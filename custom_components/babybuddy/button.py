"""Platform for babybuddy button integration."""

from __future__ import annotations

from homeassistant.const import ATTR_ID
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .coordinator import BabyBuddyConfigEntry, BabyBuddyCoordinator
from .entity import BabyBuddyStartTimerButton


async def async_setup_entry(
    hass: HomeAssistant,
    entry: BabyBuddyConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Baby Buddy button entities."""
    coordinator = entry.runtime_data.coordinator
    tracked: set[int] = set()

    @callback
    def _add_buttons() -> None:
        if not coordinator.data:
            return
        new: list[BabyBuddyStartTimerButton] = []
        for child in coordinator.data.children:
            child_id = child[ATTR_ID]
            if child_id not in tracked:
                tracked.add(child_id)
                new.append(BabyBuddyStartTimerButton(coordinator, child))
        if new:
            async_add_entities(new)

    entry.async_on_unload(coordinator.async_add_listener(_add_buttons))
    _add_buttons()
