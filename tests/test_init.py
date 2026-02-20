"""Test babybuddy child creation."""

import pytest
from homeassistant.const import ATTR_DEVICE_CLASS, ATTR_ICON
from homeassistant.core import HomeAssistant

from custom_components.babybuddy.const import DOMAIN
from custom_components.babybuddy.coordinator import BabyBuddyCoordinator

from .conftest import child_entity_id
from .const import MOCK_SERVICE_ADD_CHILD_SCHEMA


@pytest.mark.usefixtures("setup_baby_buddy_entry_live")
async def test_service_add_child(
    hass: HomeAssistant,
    bb_coordinator: BabyBuddyCoordinator,
) -> None:
    """Test the "add child" service call."""
    meta = bb_coordinator.metadata
    child_meta = meta.get("child", {})

    entity_id = child_entity_id(meta, MOCK_SERVICE_ADD_CHILD_SCHEMA)
    await hass.services.async_call(
        DOMAIN,
        "add_child",
        MOCK_SERVICE_ADD_CHILD_SCHEMA,
        blocking=True,
    )
    state = hass.states.get(entity_id)

    assert state
    assert state.attributes[ATTR_DEVICE_CLASS] == child_meta.get(
        "device_class", "babybuddy_child"
    )
    assert (
        state.attributes["first_name"]
        == MOCK_SERVICE_ADD_CHILD_SCHEMA["first_name"]
    )
    assert state.attributes[ATTR_ICON] == child_meta.get(
        "icon", "mdi:baby-face-outline"
    )
    assert (
        state.attributes["last_name"]
        == MOCK_SERVICE_ADD_CHILD_SCHEMA["last_name"]
    )
