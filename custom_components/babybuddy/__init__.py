"""Initialization for babybuddy integration."""

from __future__ import annotations

from packaging.version import Version

from homeassistant.config_entries import ConfigEntry, ConfigEntryError
from homeassistant.const import CONF_PATH
from homeassistant.core import HomeAssistant
from homeassistant.helpers.typing import ConfigType

from .const import CONFIG_FLOW_VERSION, DEFAULT_PATH, LOGGER, MIN_BB_VERSION, PLATFORMS
from .coordinator import BabyBuddyConfigEntry, BabyBuddyCoordinator, BabyBuddyData
from .services import async_setup_services


# async_setup is for the initial setup of the integration itself
async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    """Set up babybuddy."""
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
    await async_setup_services(hass, coordinator)

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

    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)


async def async_migrate_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Handle migration of config entries."""

    LOGGER.debug(f"Migrating from ConfigFlow version {entry.version}.")

    if entry.version == 1:
        new = {**entry.data}
        new[CONF_PATH] = DEFAULT_PATH

        hass.config_entries.async_update_entry(
            entry, version=CONFIG_FLOW_VERSION, data=new
        )

    LOGGER.info(
        f"Migration to ConfigFlow version {entry.version} successful.",
    )

    return True
