"""Platform for babybuddy binary sensor integration."""

from __future__ import annotations

from typing import Any

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
)
from homeassistant.const import ATTR_ID, CONF_API_KEY
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import (
    ATTR_FIRST_NAME,
    ATTR_LAST_NAME,
    DOMAIN,
)
from .coordinator import BabyBuddyConfigEntry, BabyBuddyCoordinator


async def async_setup_entry(
    hass: HomeAssistant,
    entry: BabyBuddyConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the babybuddy binary sensors."""
    coordinator = entry.runtime_data.coordinator
    tracked: dict = {}

    @callback
    def update_entities() -> None:
        """Update entities."""
        update_items(coordinator, tracked, async_add_entities)

    entry.async_on_unload(coordinator.async_add_listener(update_entities))

    update_entities()


@callback
def update_items(
    coordinator: BabyBuddyCoordinator,
    tracked: dict,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Add binary sensors for children that have stats data."""
    new_entities: list[BabyBuddyMedicationOverdueSensor] = []
    if coordinator.data:
        for child in coordinator.data[0]:
            key = f"{child[ATTR_ID]}_medication_overdue"
            if key not in tracked:
                tracked[key] = BabyBuddyMedicationOverdueSensor(coordinator, child)
                new_entities.append(tracked[key])
        if new_entities:
            async_add_entities(new_entities)


class BabyBuddyMedicationOverdueSensor(CoordinatorEntity, BinarySensorEntity):
    """Binary sensor for medication overdue status."""

    _attr_device_class = BinarySensorDeviceClass.PROBLEM
    _attr_has_entity_name = True

    coordinator: BabyBuddyCoordinator

    def __init__(
        self,
        coordinator: BabyBuddyCoordinator,
        child: dict,
    ) -> None:
        """Initialize the binary sensor."""
        super().__init__(coordinator)
        self.child = child
        self._attr_unique_id = (
            f"{coordinator.config_entry.data[CONF_API_KEY]}"
            f"-{child[ATTR_ID]}-medication_overdue"
        )
        self._attr_device_info = {
            "identifiers": {(DOMAIN, child[ATTR_ID])},
            "name": f"{child[ATTR_FIRST_NAME]} {child[ATTR_LAST_NAME]}",
        }

    @property
    def name(self) -> str:
        """Return the name of the binary sensor."""
        return f"{self.child[ATTR_FIRST_NAME]} {self.child[ATTR_LAST_NAME]} medication overdue"

    @property
    def available(self) -> bool:
        """Return True if stats data is available."""
        if not self.coordinator.data:
            return False
        child_data = self.coordinator.data[1].get(self.child[ATTR_ID], {})
        return "stats" in child_data

    @property
    def is_on(self) -> bool | None:
        """Return True if any medication is overdue."""
        if not self.available:
            return None
        child_data = self.coordinator.data[1].get(self.child[ATTR_ID], {})
        stats = child_data.get("stats", {})
        return stats.get("medications_overdue_count", 0) > 0

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return entity specific state attributes."""
        if not self.available:
            return {}
        child_data = self.coordinator.data[1].get(self.child[ATTR_ID], {})
        stats = child_data.get("stats", {})
        return {
            "overdue_names": stats.get("medications_overdue", []),
            "overdue_count": stats.get("medications_overdue_count", 0),
        }
