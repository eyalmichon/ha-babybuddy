"""Initialization for babybuddy integration."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import voluptuous as vol
from packaging.version import Version

from homeassistant.components import websocket_api
from homeassistant.config_entries import ConfigEntry, ConfigEntryError
from homeassistant.const import (
    CONF_API_KEY,
    CONF_HOST,
    CONF_PATH,
    CONF_PORT,
    EVENT_HOMEASSISTANT_STARTED,
)
from homeassistant.core import CoreState, HomeAssistant, callback
import homeassistant.helpers.entity_registry as er
from homeassistant.helpers.typing import ConfigType

from .const import (
    CONFIG_FLOW_VERSION,
    DEFAULT_PATH,
    DEFAULT_PORT,
    DOMAIN,
    LOGGER,
    MIN_BB_VERSION,
    PLATFORMS,
)
from .coordinator import BabyBuddyConfigEntry, BabyBuddyCoordinator, BabyBuddyData
from .frontend import JSModuleRegistration
from .services import async_setup_services

_MANIFEST = json.loads((Path(__file__).parent / "manifest.json").read_text())
_INTEGRATION_VERSION: str = _MANIFEST.get("version", "0.0.0")


@websocket_api.websocket_command({vol.Required("type"): f"{DOMAIN}/card_config"})
@websocket_api.async_response
async def _websocket_card_config(
    hass: HomeAssistant,
    connection: websocket_api.ActiveConnection,
    msg: dict,
) -> None:
    """Return card configuration: version + UI metadata from discovery.

    The ``ready`` flag lets the frontend distinguish "integration not loaded
    yet, please retry" from "no groups configured". Without it, an early
    card render would get ``sensor_groups: []`` and wrongly place every
    entity into the catch-all "Other" bucket forever.
    """
    result: dict[str, Any] = {"version": _INTEGRATION_VERSION}

    entries = hass.config_entries.async_loaded_entries(DOMAIN)
    if entries:
        coordinator = entries[0].runtime_data.coordinator
        result["ready"] = True
        result["sensor_groups"] = coordinator.metadata.get("sensor_groups", [])
    else:
        result["ready"] = False
        result["sensor_groups"] = []

    connection.send_result(msg["id"], result)


async def _async_register_frontend(hass: HomeAssistant) -> None:
    """Register the Baby Buddy card with the HA frontend."""
    registrar = JSModuleRegistration(hass, _INTEGRATION_VERSION)
    await registrar.async_register()


async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    """Set up babybuddy."""
    websocket_api.async_register_command(hass, _websocket_card_config)

    async def _setup_frontend(_event: object = None) -> None:
        await _async_register_frontend(hass)

    if hass.state == CoreState.running:
        await _setup_frontend()
    else:
        hass.bus.async_listen_once(EVENT_HOMEASSISTANT_STARTED, _setup_frontend)

    return True


# async_setup_entry handles the setup of individual configuration
# entries created by users via the UI (i.e., Config Entry)
async def async_setup_entry(hass: HomeAssistant, entry: BabyBuddyConfigEntry) -> bool:
    """Set up the babybuddy component."""

    coordinator = BabyBuddyCoordinator(hass, entry)
    entry.runtime_data = BabyBuddyData(coordinator=coordinator, entities={})

    # Fetch initial data so we have data when entities subscribe
    #
    # If the refresh fails, async_config_entry_first_refresh will
    # raise ConfigEntryNotReady and setup will try again later
    #
    # If you do not want to retry setup on failure, use
    # coordinator.async_refresh() instead

    await coordinator.async_config_entry_first_refresh()

    bb_version_str = coordinator.metadata.get("babybuddy_version")
    if bb_version_str is None:
        raise ConfigEntryError(
            f"This integration requires Baby Buddy {MIN_BB_VERSION} or later. "
            "Please update your Baby Buddy server."
        )
    bb_version = Version(bb_version_str)
    if bb_version < MIN_BB_VERSION:
        raise ConfigEntryError(
            f"Baby Buddy {bb_version} is too old. "
            f"This integration requires {MIN_BB_VERSION} or later."
        )
    LOGGER.info("Baby Buddy version %s (minimum: %s)", bb_version, MIN_BB_VERSION)

    # Register services dynamically from discovery metadata
    entry.runtime_data.service_keys = await async_setup_services(hass, coordinator)

    # Clean up any MQTT auto-discovered entities that BB may have created,
    # then set up our own MQTT subscriptions for real-time data updates.
    try:
        await coordinator.cleanup_mqtt_discovery()
    except Exception:
        LOGGER.exception("Failed to clean up MQTT discovery topics")

    if entry.options.get("mqtt_enabled", False):
        try:
            await coordinator._setup_mqtt_subscriptions()
        except Exception:
            LOGGER.exception("Failed to set up MQTT subscriptions")

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    return True


async def async_unload_entry(hass: HomeAssistant, entry: BabyBuddyConfigEntry) -> bool:
    """Unload babybuddy config entry."""
    coordinator = entry.runtime_data.coordinator

    # Clean up MQTT subscriptions
    for unsub in coordinator._mqtt_unsubscribes:
        unsub()
    coordinator._mqtt_unsubscribes.clear()

    result = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)

    if result:
        remaining = [
            e for e in hass.config_entries.async_loaded_entries(DOMAIN)
            if e.entry_id != entry.entry_id
        ]
        if not remaining:
            for key in entry.runtime_data.service_keys or []:
                hass.services.async_remove(DOMAIN, key)

    return result


async def async_migrate_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Handle migration of config entries."""

    LOGGER.debug(
        "Migrating from ConfigFlow version %s.%s",
        entry.version,
        entry.minor_version,
    )

    if entry.version == 1:
        new = {**entry.data}
        new[CONF_PATH] = DEFAULT_PATH
        hass.config_entries.async_update_entry(
            entry, version=2, minor_version=1, data=new
        )

    if entry.version == 2 and entry.minor_version < 2:
        _migrate_unique_ids(hass, entry)
        new_unique_id = (
            f"{entry.data[CONF_HOST]}:{entry.data.get(CONF_PORT, DEFAULT_PORT)}"
        )
        hass.config_entries.async_update_entry(
            entry, minor_version=2, unique_id=new_unique_id,
        )

    LOGGER.info(
        "Migration to ConfigFlow version %s.%s successful",
        entry.version,
        entry.minor_version,
    )

    return True


@callback
def _migrate_unique_ids(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Rewrite entity unique_ids from API-key prefix to entry_id prefix.

    Also removes orphaned switch entities left behind after the switch
    platform was replaced by the button platform.
    """
    api_key: str | None = entry.data.get(CONF_API_KEY)

    if api_key:
        old_prefix = f"{api_key}-"
        new_prefix = f"{entry.entry_id}-"

        @callback
        def _update_unique_id(
            entity_entry: er.RegistryEntry,
        ) -> dict[str, Any] | None:
            if entity_entry.unique_id.startswith(old_prefix):
                new_uid = f"{new_prefix}{entity_entry.unique_id[len(old_prefix):]}"
                LOGGER.debug(
                    "Migrating unique_id %s → %s",
                    entity_entry.unique_id,
                    new_uid,
                )
                return {"new_unique_id": new_uid}
            return None

        er.async_migrate_entries(hass, entry.entry_id, _update_unique_id)

    ent_reg = er.async_get(hass)
    for ent in er.async_entries_for_config_entry(ent_reg, entry.entry_id):
        if ent.domain == "switch":
            LOGGER.debug("Removing orphaned switch entity %s", ent.entity_id)
            ent_reg.async_remove(ent.entity_id)
