"""Initialization for babybuddy integration."""

from __future__ import annotations

import asyncio
import json
from asyncio import TimeoutError as AsyncIOTimeoutError
from collections.abc import Callable
from dataclasses import dataclass
from datetime import timedelta
from http import HTTPStatus
from typing import Any

from aiohttp.client_exceptions import ClientError, ClientResponseError

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    ATTR_ID,
    CONF_API_KEY,
    CONF_HOST,
    CONF_PATH,
    CONF_PORT,
    CONF_SCAN_INTERVAL,
)
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed, ConfigEntryNotReady
from homeassistant.helpers.aiohttp_client import async_get_clientsession
import homeassistant.helpers.device_registry as dr
from homeassistant.helpers import issue_registry as ir
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .client import BabyBuddyClient
from .const import (
    CONF_MQTT_TOPIC_PREFIX,
    DEFAULT_MQTT_TOPIC_PREFIX,
    DEFAULT_SCAN_INTERVAL,
    DOMAIN,
    LOGGER,
)
from .discovery import sensor_description_from_metadata
from .errors import AuthorizationError, ConnectError

type BabyBuddyConfigEntry = ConfigEntry[BabyBuddyData]


@dataclass
class BabyBuddyData:
    """Data retrieved from babybuddy."""

    coordinator: BabyBuddyCoordinator
    entities: dict[str, str]


class BabyBuddyCoordinator(DataUpdateCoordinator):
    """Coordinate retrieving and updating data from babybuddy."""

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        """Initialize the BabyBuddyCoordinator."""
        LOGGER.debug("Initializing BabyBuddyCoordinator")
        super().__init__(
            hass,
            LOGGER,
            name=DOMAIN,
            config_entry=entry,
            update_interval=timedelta(
                seconds=entry.options.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL)
            ),
        )
        self.client: BabyBuddyClient = BabyBuddyClient(
            entry.data[CONF_HOST],
            entry.data[CONF_PORT],
            entry.data[CONF_PATH],
            entry.data[CONF_API_KEY],
            async_get_clientsession(hass),
        )
        self.device_registry: dr.DeviceRegistry = dr.async_get(hass)
        self.child_ids: list[str] = []
        self._mqtt_unsubscribes: list[Callable] = []
        self.metadata: dict[str, Any] = {}

    async def _async_setup(self) -> None:
        """Set up the coordinator.

        Called automatically during async_config_entry_first_refresh.
        """
        try:
            await self.client.async_connect()
        except AuthorizationError as error:
            raise ConfigEntryAuthFailed from error
        except ConnectError as error:
            raise ConfigEntryNotReady(error) from error

        # Require discovery v2 from Baby Buddy
        try:
            self.metadata = await self.client.async_get_discovery()
            LOGGER.info("Loaded entity metadata from Baby Buddy discovery endpoint")
        except (ClientResponseError, AsyncIOTimeoutError, ClientError) as err:
            raise ConfigEntryNotReady(
                "Baby Buddy discovery endpoint not available. "
                "Ensure Baby Buddy is updated and reachable."
            ) from err

        await self._async_set_children_from_db()

    async def _async_set_children_from_db(self) -> None:
        """Set child_ids from HA database."""
        self.child_ids = [
            next(iter(device.identifiers))[1]
            for device in dr.async_entries_for_config_entry(
                self.device_registry, self.config_entry.entry_id
            )
        ]

    @property
    def sensor_descriptions(self) -> list:
        """Build BabyBuddyEntityDescription list from metadata."""
        return [
            sensor_description_from_metadata(m)
            for m in self.metadata.get("sensors", [])
        ]

    def get_select_options(self, key: str) -> list[str]:
        """Return options for a select key from metadata."""
        for s in self.metadata.get("selects", []):
            if s["key"] == key:
                return s.get("options", [])
        return []

    @property
    def _slug_to_child_id(self) -> dict[str, int]:
        """Build a slug -> child_id mapping from current data."""
        if not self.data or not self.data[0]:
            return {}
        return {child["slug"]: child[ATTR_ID] for child in self.data[0]}

    async def _setup_mqtt_subscriptions(self) -> None:
        """Subscribe to Baby Buddy MQTT state topics."""
        # Check if MQTT integration is available
        if not self.hass.config_entries.async_loaded_entries("mqtt"):
            LOGGER.warning(
                "MQTT enabled in Baby Buddy options but MQTT integration "
                "is not set up. Falling back to REST polling only."
            )
            return

        from homeassistant.components.mqtt import (
            async_subscribe,
            async_wait_for_mqtt_client,
        )

        # Wait for MQTT client to be ready (per HA docs)
        if not await async_wait_for_mqtt_client(self.hass):
            LOGGER.warning(
                "MQTT client not available, falling back to REST polling."
            )
            return

        prefix = self.config_entry.options.get(
            CONF_MQTT_TOPIC_PREFIX, DEFAULT_MQTT_TOPIC_PREFIX
        )

        # Subscribe after first REST poll so child slugs are available
        mqtt_topics = self.metadata.get("mqtt", {}).get("topics", {})
        for child in self.data[0]:
            child_slug = child["slug"]

            # Subscribe to each data type topic
            for topic_key in mqtt_topics:
                topic = f"{prefix}/{child_slug}/{topic_key}/state"
                unsub = await async_subscribe(
                    self.hass,
                    topic,
                    self._handle_mqtt_message,
                    qos=1,
                )
                self._mqtt_unsubscribes.append(unsub)

            # Subscribe to stats topic
            stats_topic = f"{prefix}/{child_slug}/stats/state"
            unsub = await async_subscribe(
                self.hass,
                stats_topic,
                self._handle_stats_message,
                qos=1,
            )
            self._mqtt_unsubscribes.append(unsub)

        LOGGER.info(
            "Subscribed to Baby Buddy MQTT topics under prefix '%s'", prefix
        )

    @property
    def mqtt_discovery_enabled_in_bb(self) -> bool | None:
        """Return whether BB has MQTT auto-discovery enabled, or None if unknown."""
        settings = self.metadata.get("settings")
        if settings is None:
            return None
        return settings.get("mqtt_discovery_enabled")

    async def cleanup_mqtt_discovery(self) -> None:
        """Detect and handle Baby Buddy MQTT auto-discovered entities.

        When Baby Buddy has its "Publish Home Assistant MQTT discovery configs"
        toggle enabled, it publishes retained config messages to
        ``homeassistant/sensor/...`` and ``homeassistant/binary_sensor/...``.
        These cause duplicate entities when our native integration is also
        installed.

        **New BB (has ``settings`` in metadata):** We only check the flag and
        raise/clear a fixable repair.  The user clicks "Fix", which calls the
        BB API — BB itself disables the toggle AND publishes empty retained
        messages to clean up all its discovery topics.

        **Old BB (no ``settings``):** We fall back to cleaning the topics
        ourselves as a best-effort approach.
        """
        if self.mqtt_discovery_enabled_in_bb is False:
            ir.async_delete_issue(self.hass, DOMAIN, "mqtt_discovery_conflict")
            return

        if not self.hass.config_entries.async_loaded_entries("mqtt"):
            return

        from homeassistant.components.mqtt import async_wait_for_mqtt_client

        if not await async_wait_for_mqtt_client(self.hass):
            return

        # New BB versions expose `settings` in metadata — BB handles its own
        # cleanup when the user clicks the repair "Fix" button.  We just need
        # to detect retained topics so we know whether to show the repair.
        if self.mqtt_discovery_enabled_in_bb is True:
            detected = await self._detect_bb_discovery_topics()
            if detected:
                LOGGER.warning(
                    "Detected %d Baby Buddy MQTT auto-discovery topics. "
                    "Use the repair in Settings → Repairs to disable them.",
                    len(detected),
                )
                ir.async_create_issue(
                    self.hass,
                    DOMAIN,
                    "mqtt_discovery_conflict",
                    is_fixable=True,
                    severity=ir.IssueSeverity.WARNING,
                    translation_key="mqtt_discovery_conflict",
                    translation_placeholders={"count": str(len(detected))},
                )
            else:
                ir.async_delete_issue(self.hass, DOMAIN, "mqtt_discovery_conflict")
            return

        # Fallback for old BB without `settings` — clean up ourselves.
        cleaned = await self._legacy_cleanup_discovery_topics()

        if cleaned:
            LOGGER.warning(
                "Published empty retained messages to %d MQTT discovery "
                "topics to remove duplicate Baby Buddy entities. "
                "Disable 'Publish Home Assistant MQTT discovery configs' "
                "in Baby Buddy settings to prevent this on every restart.",
                len(cleaned),
            )
            ir.async_create_issue(
                self.hass,
                DOMAIN,
                "mqtt_discovery_conflict",
                is_fixable=False,
                severity=ir.IssueSeverity.WARNING,
                translation_key="mqtt_discovery_conflict",
                translation_placeholders={"count": str(len(cleaned))},
            )
        else:
            ir.async_delete_issue(self.hass, DOMAIN, "mqtt_discovery_conflict")

    async def _detect_bb_discovery_topics(self) -> list[str]:
        """Subscribe briefly to detect retained BB discovery topics."""
        from homeassistant.components.mqtt import async_subscribe

        found: list[str] = []

        def _on_msg(msg) -> None:
            topic_lower = msg.topic.lower()
            if "babybuddy" not in topic_lower and "baby_buddy" not in topic_lower:
                return
            if msg.payload:
                found.append(msg.topic)

        unsubs: list[Callable] = []
        for component in ("sensor", "binary_sensor"):
            unsubs.append(
                await async_subscribe(
                    self.hass,
                    f"homeassistant/{component}/+/+/config",
                    _on_msg,
                    qos=0,
                )
            )

        await asyncio.sleep(2)

        for unsub in unsubs:
            unsub()

        return found

    async def _legacy_cleanup_discovery_topics(self) -> list[str]:
        """Best-effort cleanup for old BB without the settings API."""
        from homeassistant.components.mqtt import async_publish, async_subscribe

        cleaned: list[str] = []
        discovery_prefix = "homeassistant"

        # Subscribe to find retained BB discovery topics.
        extra: set[str] = set()

        def _on_discovery(msg) -> None:
            topic_lower = msg.topic.lower()
            if "babybuddy" not in topic_lower and "baby_buddy" not in topic_lower:
                return
            if msg.payload:
                extra.add(msg.topic)

        unsubs: list[Callable] = []
        for component in ("sensor", "binary_sensor"):
            unsubs.append(
                await async_subscribe(
                    self.hass,
                    f"{discovery_prefix}/{component}/+/+/config",
                    _on_discovery,
                    qos=0,
                )
            )

        await asyncio.sleep(2)

        for unsub in unsubs:
            unsub()

        for topic in extra:
            await async_publish(self.hass, topic, "", retain=True)
            cleaned.append(topic)

        return cleaned

    async def _handle_mqtt_message(self, msg) -> None:
        """Handle incoming MQTT state message."""
        if not self.data:
            return

        parts = msg.topic.split("/")
        if len(parts) < 4:
            LOGGER.warning("Unexpected MQTT topic format: %s", msg.topic)
            return

        child_slug = parts[1]
        data_type = parts[2]

        try:
            payload = json.loads(msg.payload)
        except (json.JSONDecodeError, TypeError):
            LOGGER.warning("Invalid MQTT payload on topic %s", msg.topic)
            return

        if not isinstance(payload, dict):
            LOGGER.debug("Ignoring non-dict MQTT payload on %s", msg.topic)
            return

        mqtt_topics = self.metadata.get("mqtt", {}).get("topics", {})
        coordinator_key = mqtt_topics.get(data_type)
        if not coordinator_key:
            LOGGER.debug("Unknown MQTT data type: %s", data_type)
            return

        child_id = self._slug_to_child_id.get(child_slug)
        if child_id is None:
            LOGGER.debug(
                "MQTT message for unknown child slug: %s", child_slug
            )
            return

        children_list, child_data = self.data
        if child_id in child_data:
            child_data[child_id][coordinator_key] = payload
            self.async_set_updated_data((children_list, child_data))

    async def _handle_stats_message(self, msg) -> None:
        """Handle incoming MQTT stats message."""
        if not self.data:
            return

        parts = msg.topic.split("/")
        if len(parts) < 4:
            return

        child_slug = parts[1]

        try:
            payload = json.loads(msg.payload)
        except (json.JSONDecodeError, TypeError):
            LOGGER.warning("Invalid MQTT stats payload on topic %s", msg.topic)
            return

        if not isinstance(payload, dict):
            return

        child_id = self._slug_to_child_id.get(child_slug)
        if child_id is None:
            return

        children_list, child_data = self.data
        if child_id in child_data:
            child_data[child_id]["stats"] = payload
            self.async_set_updated_data((children_list, child_data))

    async def _async_remove_deleted_children(self) -> None:
        """Remove child device if child is removed from babybuddy."""
        for device in dr.async_entries_for_config_entry(
            self.device_registry, self.config_entry.entry_id
        ):
            if next(iter(device.identifiers))[1] not in self.child_ids:
                self.device_registry.async_remove_device(device.id)

    async def _async_update_data(
        self,
    ) -> tuple[list[dict[str, str]], dict[int, dict[str, dict[str, str]]]]:
        """Fetch data from API endpoint."""
        children_list: dict[str, Any] = {}
        child_data: dict[int, dict[str, dict[str, str]]] = {}

        count_field = self.metadata["api"]["list_response_format"]["count_field"]
        results_field = self.metadata["api"]["list_response_format"]["results_field"]

        try:
            children_list = await self.client.async_get("children")
        except ClientResponseError as error:
            if error.status == HTTPStatus.FORBIDDEN:
                raise ConfigEntryAuthFailed from error
        except (AsyncIOTimeoutError, ClientError) as error:
            raise UpdateFailed(error) from error

        if children_list[count_field] < len(self.child_ids):
            self.child_ids = [child[ATTR_ID] for child in children_list[results_field]]
            await self._async_remove_deleted_children()
        if children_list[count_field] == 0:
            raise UpdateFailed("No children found. Please add at least one child.")
        if children_list[count_field] > len(self.child_ids):
            self.child_ids = [child[ATTR_ID] for child in children_list[results_field]]

        last_activities_ep = self.metadata.get("api", {}).get(
            "last_activities_endpoint"
        )

        for child in children_list[results_field]:
            child_data.setdefault(child[ATTR_ID], {})

            if last_activities_ep:
                await self._fetch_bulk(child, child_data, last_activities_ep)
            else:
                await self._fetch_individual(
                    child, child_data, results_field
                )

        return (children_list[results_field], child_data)

    async def _fetch_bulk(
        self,
        child: dict[str, Any],
        child_data: dict[int, dict],
        endpoint_template: str,
    ) -> None:
        """Fetch all sensor data + stats in one call per child."""
        try:
            data = await self.client.async_get_last_activities(
                child["slug"], endpoint_template
            )
        except (ClientResponseError, AsyncIOTimeoutError, ClientError) as error:
            LOGGER.error(
                "Failed to fetch last-activities for %s: %s",
                child["slug"],
                error,
            )
            return

        for sensor_meta in self.metadata.get("sensors", []):
            key = sensor_meta["key"]
            child_data[child[ATTR_ID]][key] = data.get(key) or {}

        if data.get("stats"):
            child_data[child[ATTR_ID]]["stats"] = data["stats"]

    async def _fetch_individual(
        self,
        child: dict[str, Any],
        child_data: dict[int, dict],
        results_field: str,
    ) -> None:
        """Fallback: fetch each sensor type individually (old BB)."""
        child_filter = self.metadata["api"]["child_filter_param"]
        limit_param = self.metadata["api"]["limit_param"]
        stats_endpoint = self.metadata["api"]["stats_endpoint"]

        for sensor_meta in self.metadata.get("sensors", []):
            endpoint_key = sensor_meta["key"]
            try:
                endpoint_data = await self.client.async_get(
                    endpoint_key,
                    f"?{child_filter}={child[ATTR_ID]}&{limit_param}=1",
                )
            except ClientResponseError as error:
                LOGGER.debug(
                    "No %s found for %s %s. Skipping. error: %s",
                    endpoint_key,
                    child["first_name"],
                    child["last_name"],
                    error,
                )
                continue
            except (AsyncIOTimeoutError, ClientError) as error:
                LOGGER.error(error)
                continue
            data: list[dict[str, str]] = endpoint_data[results_field]
            child_data[child[ATTR_ID]][endpoint_key] = data[0] if data else {}

        try:
            stats = await self.client.async_get_stats(
                child["slug"], stats_endpoint
            )
            child_data[child[ATTR_ID]]["stats"] = stats
        except (ClientResponseError, AsyncIOTimeoutError, ClientError) as error:
            LOGGER.debug("Stats fetch error for %s: %s", child["slug"], error)
