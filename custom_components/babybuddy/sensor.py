"""Platform for babybuddy sensor integration."""

from __future__ import annotations

from homeassistant.const import ATTR_ID
from homeassistant.core import HomeAssistant, callback
import homeassistant.helpers.entity_registry as er
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import ACTIVE_TIMERS_KEY, DOMAIN
from .coordinator import BabyBuddyConfigEntry, BabyBuddyCoordinator
from .entity import (
    BabyBuddyChildDataSensor,
    BabyBuddyChildSensor,
    BabyBuddyStatsSensor,
    BabyBuddyTimerSensor,
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: BabyBuddyConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the babybuddy sensors."""
    coordinator = entry.runtime_data.coordinator
    tracked: dict = {}
    tracked_timers: dict[int, BabyBuddyTimerSensor] = {}

    @callback
    def update_entities() -> None:
        """Update entities — add new sensors and manage dynamic timer sensors."""
        _update_static_sensors(coordinator, tracked, async_add_entities)
        _update_timer_sensors(
            hass, coordinator, tracked_timers, async_add_entities
        )

    entry.async_on_unload(coordinator.async_add_listener(update_entities))

    update_entities()


@callback
def _update_static_sensors(
    coordinator: BabyBuddyCoordinator,
    tracked: dict,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Add new child / data / stats sensors for new endpoint entries."""
    if coordinator.data is None:
        return

    new_entities = []
    for child in coordinator.data.children:
        if child[ATTR_ID] not in tracked:
            tracked[child[ATTR_ID]] = BabyBuddyChildSensor(coordinator, child)
            new_entities.append(tracked[child[ATTR_ID]])

        for description in coordinator.sensor_descriptions:
            track_key = f"{child[ATTR_ID]}_{description.key}"
            if (
                coordinator.data.child_data[child[ATTR_ID]].get(description.key)
                and track_key not in tracked
            ):
                tracked[track_key] = BabyBuddyChildDataSensor(
                    coordinator, child, description
                )
                new_entities.append(tracked[track_key])

        for stats_meta in coordinator.metadata.get("stats_sensors", []):
            track_key = f"{child[ATTR_ID]}_stats_{stats_meta['key']}"
            if track_key not in tracked:
                tracked[track_key] = BabyBuddyStatsSensor(
                    coordinator, child, stats_meta
                )
                new_entities.append(tracked[track_key])

    if new_entities:
        async_add_entities(new_entities)


@callback
def _update_timer_sensors(
    hass: HomeAssistant,
    coordinator: BabyBuddyCoordinator,
    tracked_timers: dict[int, BabyBuddyTimerSensor],
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Dynamically create / remove timer sensor entities.

    Follows the HA ``dynamic-devices`` pattern: diff active timer IDs
    against the set we already track, add new ones, and remove stale ones
    from the entity registry.
    """
    if coordinator.data is None:
        return

    current_timer_ids: set[int] = set()
    child_by_id: dict[int, dict] = {c[ATTR_ID]: c for c in coordinator.data.children}
    new_entities: list[BabyBuddyTimerSensor] = []

    for child_id, data in coordinator.data.child_data.items():
        child = child_by_id.get(child_id)
        if child is None:
            continue
        for timer in data.get(ACTIVE_TIMERS_KEY, []):
            tid = timer.get(ATTR_ID)
            if tid is None:
                continue
            current_timer_ids.add(tid)
            if tid not in tracked_timers:
                entity = BabyBuddyTimerSensor(coordinator, child, timer)
                tracked_timers[tid] = entity
                new_entities.append(entity)

    if new_entities:
        async_add_entities(new_entities)

    stale = set(tracked_timers) - current_timer_ids
    if stale:
        ent_reg = er.async_get(hass)
        for tid in stale:
            entity = tracked_timers.pop(tid)
            entry = ent_reg.async_get(entity.entity_id)
            if entry:
                ent_reg.async_remove(entry.entity_id)
