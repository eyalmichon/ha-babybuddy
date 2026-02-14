"""Platform for babybuddy sensor integration."""

from __future__ import annotations

from homeassistant.const import ATTR_ID
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .coordinator import BabyBuddyConfigEntry, BabyBuddyCoordinator
from .entity import BabyBuddyChildDataSensor, BabyBuddyChildSensor, BabyBuddyStatsSensor


# For a platform to support config entries, it will need to add a setup entry function
async def async_setup_entry(
    hass: HomeAssistant,
    entry: BabyBuddyConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the babybuddy sensors."""
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
    """Add new sensors for new endpoint entries."""
    if coordinator.data is None:
        return

    new_entities = []
    for child in coordinator.data[0]:
        # Child info sensor
        if child[ATTR_ID] not in tracked:
            tracked[child[ATTR_ID]] = BabyBuddyChildSensor(coordinator, child)
            new_entities.append(tracked[child[ATTR_ID]])

        # Data sensors (from metadata "sensors")
        for description in coordinator.sensor_descriptions:
            track_key = f"{child[ATTR_ID]}_{description.key}"
            if (
                coordinator.data[1][child[ATTR_ID]].get(description.key)
                and track_key not in tracked
            ):
                tracked[track_key] = BabyBuddyChildDataSensor(
                    coordinator, child, description
                )
                new_entities.append(tracked[track_key])

        # Stats sensors (from metadata "stats_sensors")
        for stats_meta in coordinator.metadata.get("stats_sensors", []):
            track_key = f"{child[ATTR_ID]}_stats_{stats_meta['key']}"
            if track_key not in tracked:
                tracked[track_key] = BabyBuddyStatsSensor(
                    coordinator, child, stats_meta
                )
                new_entities.append(tracked[track_key])

    if new_entities:
        async_add_entities(new_entities)
