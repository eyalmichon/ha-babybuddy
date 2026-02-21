"""Repair flows for the Baby Buddy integration."""

from __future__ import annotations

from typing import Any

import voluptuous as vol

from homeassistant.components.repairs import RepairsFlow
from homeassistant.config_entries import ConfigEntryState
from homeassistant.core import HomeAssistant

from .const import DOMAIN, LOGGER
from .coordinator import BabyBuddyConfigEntry

CONFIRM_SCHEMA = vol.Schema({vol.Required("confirm", default=False): bool})


class MqttDiscoveryRepairFlow(RepairsFlow):
    """Repair flow to disable Baby Buddy's MQTT auto-discovery via API."""

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        """Forward to the confirm step that shows the form."""
        return await self.async_step_confirm()

    async def async_step_confirm(
        self, user_input: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        """Show explanation and ask user to confirm."""
        if user_input is not None:
            if user_input.get("confirm"):
                return await self._disable_mqtt_discovery()
            return self.async_abort(reason="skipped_by_user")

        return self.async_show_form(step_id="confirm", data_schema=CONFIRM_SCHEMA)

    async def _disable_mqtt_discovery(self) -> dict[str, Any]:
        """Call BB API to disable MQTT discovery and resolve the issue."""
        entry: BabyBuddyConfigEntry | None = None
        for e in self.hass.config_entries.async_loaded_entries(DOMAIN):
            if e.state is ConfigEntryState.LOADED:
                entry = e
                break

        if not entry:
            return self.async_abort(reason="entry_not_loaded")

        coordinator = entry.runtime_data.coordinator
        try:
            await coordinator.client.async_patch_ha_settings(
                {"mqtt_discovery_enabled": False}
            )
        except Exception:
            LOGGER.exception("Failed to disable MQTT discovery on Baby Buddy")
            return self.async_abort(reason="api_call_failed")

        return self.async_create_entry(data={})


async def async_create_fix_flow(
    hass: HomeAssistant,
    issue_id: str,
    data: dict[str, str] | None,
) -> RepairsFlow:
    """Create the repair flow for a given issue."""
    if issue_id == "mqtt_discovery_conflict":
        return MqttDiscoveryRepairFlow()
    return RepairsFlow()
