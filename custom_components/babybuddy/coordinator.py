"""Initialization for babybuddy integration."""

from __future__ import annotations

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
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .client import BabyBuddyClient
from .const import (
    ATTR_CHILDREN,
    ATTR_COUNT,
    ATTR_FIRST_NAME,
    ATTR_LAST_NAME,
    ATTR_RESULTS,
    ATTR_SLUG,
    CONF_MQTT_ENABLED,
    CONF_MQTT_TOPIC_PREFIX,
    DEFAULT_MQTT_TOPIC_PREFIX,
    DEFAULT_SCAN_INTERVAL,
    DOMAIN,
    LOGGER,
    MQTT_TOPIC_KEYS,
    MQTT_TOPIC_TO_DATA_KEY,
    SENSOR_TYPES,
)
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
    def _slug_to_child_id(self) -> dict[str, int]:
        """Build a slug -> child_id mapping from current data."""
        if not self.data or not self.data[0]:
            return {}
        return {child[ATTR_SLUG]: child[ATTR_ID] for child in self.data[0]}

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
        for child in self.data[0]:
            child_slug = child[ATTR_SLUG]

            # Subscribe to each data type topic
            for topic_key in MQTT_TOPIC_KEYS:
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

    async def _handle_mqtt_message(self, msg) -> None:
        """Handle incoming MQTT state message."""
        # Parse topic: {prefix}/{child_slug}/{data_type}/state
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

        # Map MQTT data_type to coordinator data key
        coordinator_key = MQTT_TOPIC_TO_DATA_KEY.get(data_type)
        if not coordinator_key:
            LOGGER.debug("Unknown MQTT data type: %s", data_type)
            return

        # Find child ID from slug
        child_id = self._slug_to_child_id.get(child_slug)
        if child_id is None:
            LOGGER.debug(
                "MQTT message for unknown child slug: %s", child_slug
            )
            return

        # Update coordinator data in-place and notify entities
        children_list, child_data = self.data
        if child_id in child_data:
            child_data[child_id][coordinator_key] = payload
            self.async_set_updated_data((children_list, child_data))

    async def _handle_stats_message(self, msg) -> None:
        """Handle incoming MQTT stats message."""
        parts = msg.topic.split("/")
        if len(parts) < 4:
            return

        child_slug = parts[1]

        try:
            payload = json.loads(msg.payload)
        except (json.JSONDecodeError, TypeError):
            LOGGER.warning("Invalid MQTT stats payload on topic %s", msg.topic)
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

        try:
            children_list = await self.client.async_get(ATTR_CHILDREN)
        except ClientResponseError as error:
            if error.status == HTTPStatus.FORBIDDEN:
                raise ConfigEntryAuthFailed from error
        except (AsyncIOTimeoutError, ClientError) as error:
            raise UpdateFailed(error) from error

        if children_list[ATTR_COUNT] < len(self.child_ids):
            self.child_ids = [child[ATTR_ID] for child in children_list[ATTR_RESULTS]]
            await self._async_remove_deleted_children()
        if children_list[ATTR_COUNT] == 0:
            raise UpdateFailed("No children found. Please add at least one child.")
        if children_list[ATTR_COUNT] > len(self.child_ids):
            self.child_ids = [child[ATTR_ID] for child in children_list[ATTR_RESULTS]]

        for child in children_list[ATTR_RESULTS]:
            child_data.setdefault(child[ATTR_ID], {})
            for endpoint in SENSOR_TYPES:
                endpoint_data: dict = {}
                try:
                    endpoint_data = await self.client.async_get(
                        endpoint.key, f"?child={child[ATTR_ID]}&limit=1"
                    )
                except ClientResponseError as error:
                    LOGGER.debug(
                        f"No {endpoint} found for {child[ATTR_FIRST_NAME]} {child[ATTR_LAST_NAME]}. Skipping. error: {error}.)"
                    )
                    continue
                except (AsyncIOTimeoutError, ClientError) as error:
                    LOGGER.error(error)
                    continue
                data: list[dict[str, str]] = endpoint_data[ATTR_RESULTS]
                child_data[child[ATTR_ID]][endpoint.key] = data[0] if data else {}

            # Fetch stats (medication overdue, daily aggregates)
            try:
                stats = await self.client.async_get_stats(child[ATTR_SLUG])
                child_data[child[ATTR_ID]]["stats"] = stats
            except ClientResponseError as error:
                LOGGER.debug(
                    "Could not fetch stats for %s: %s",
                    child[ATTR_SLUG],
                    error,
                )
            except (AsyncIOTimeoutError, ClientError) as error:
                LOGGER.debug("Stats fetch error for %s: %s", child[ATTR_SLUG], error)

        return (children_list[ATTR_RESULTS], child_data)
