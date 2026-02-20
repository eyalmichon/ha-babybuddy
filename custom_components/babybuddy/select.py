"""Support for babybuddy selects."""

from __future__ import annotations

from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .coordinator import BabyBuddyConfigEntry
from .discovery import select_description_from_metadata
from .entity import BabyBuddySelect


# For a platform to support config entries, it will need to add a setup entry function
async def async_setup_entry(
    hass: HomeAssistant,
    entry: BabyBuddyConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up babybuddy select entities for feeding and diaper change."""
    coordinator = entry.runtime_data.coordinator
    select_descriptions = [
        select_description_from_metadata(m)
        for m in coordinator.metadata.get("selects", [])
        if m.get("entity", True)
    ]
    async_add_entities(
        [BabyBuddySelect(coordinator, desc) for desc in select_descriptions]
    )
