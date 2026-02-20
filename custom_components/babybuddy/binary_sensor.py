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

from .const import DOMAIN
from .coordinator import BabyBuddyConfigEntry, BabyBuddyCoordinator

_BINARY_DEVICE_CLASS_MAP: dict[str, BinarySensorDeviceClass] = {
    "problem": BinarySensorDeviceClass.PROBLEM,
    "safety": BinarySensorDeviceClass.SAFETY,
}


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
    """Add binary sensors for children based on metadata."""
    new_entities: list[BabyBuddyDynamicBinarySensor] = []
    if not coordinator.data:
        return

    for child in coordinator.data[0]:
        for bs_meta in coordinator.metadata.get("binary_sensors", []):
            key = f"{child[ATTR_ID]}_{bs_meta['key']}"
            if key not in tracked:
                tracked[key] = BabyBuddyDynamicBinarySensor(
                    coordinator, child, bs_meta
                )
                new_entities.append(tracked[key])

    if new_entities:
        async_add_entities(new_entities)


class BabyBuddyDynamicBinarySensor(CoordinatorEntity, BinarySensorEntity):
    """Binary sensor driven by metadata from the discovery endpoint."""

    _attr_has_entity_name = True
    coordinator: BabyBuddyCoordinator

    def __init__(
        self,
        coordinator: BabyBuddyCoordinator,
        child: dict,
        meta: dict[str, Any],
    ) -> None:
        """Initialize the binary sensor."""
        super().__init__(coordinator)
        self.child = child
        self._meta = meta
        self._attr_unique_id = (
            f"{coordinator.config_entry.data[CONF_API_KEY]}"
            f"-{child[ATTR_ID]}-{meta['key']}"
        )
        self._attr_device_info = {
            "identifiers": {(DOMAIN, child[ATTR_ID])},
            "name": f"{child['first_name']} {child['last_name']}",
        }

        dc = meta.get("device_class")
        if dc and dc in _BINARY_DEVICE_CLASS_MAP:
            self._attr_device_class = _BINARY_DEVICE_CLASS_MAP[dc]

    @property
    def name(self) -> str:
        """Return the name of the binary sensor."""
        return self._meta["name"]

    @property
    def available(self) -> bool:
        """Return True if coordinator data is available."""
        return bool(self.coordinator.data)

    @property
    def _stats(self) -> dict[str, Any]:
        """Return the stats dict for this child, or empty dict."""
        if not self.coordinator.data:
            return {}
        child_data = self.coordinator.data[1].get(self.child[ATTR_ID], {})
        return child_data.get("stats", {})

    @property
    def is_on(self) -> bool | None:
        """Evaluate the binary sensor state from metadata condition."""
        field = self._meta.get("stats_field", "")
        condition = self._meta.get("condition", "greater_than_zero")
        value = self._stats.get(field, 0)

        if condition == "greater_than_zero":
            return value > 0
        if condition == "truthy":
            return bool(value)
        # Default: treat as truthy
        return bool(value)

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return entity specific state attributes from metadata mapping."""
        stats = self._stats
        if not stats:
            return {}
        attr_map = self._meta.get("attributes", {})
        return {
            attr_name: stats.get(stats_field)
            for attr_name, stats_field in attr_map.items()
            if stats.get(stats_field) is not None
        }
