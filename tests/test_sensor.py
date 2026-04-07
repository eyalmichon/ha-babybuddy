"""Test babybuddy sensors (metadata-aware)."""

from homeassistant.const import (
    ATTR_ENTITY_ID,
    ATTR_TEMPERATURE,
    ATTR_TIME,
)
from homeassistant.core import HomeAssistant
from homeassistant.util import dt as dt_util

from custom_components.babybuddy.const import DOMAIN
from custom_components.babybuddy.coordinator import BabyBuddyCoordinator

from .conftest import assert_sensor_meta, child_entity_id, find_sensor_meta, sensor_entity_id
from .const import (
    MOCK_SERVICE_ADD_BMI_SCHEMA,
    MOCK_SERVICE_ADD_CHILD_SCHEMA,
    MOCK_SERVICE_ADD_DIAPER_CHANGE,
    MOCK_SERVICE_ADD_HEAD_CIRCUMFERENCE,
    MOCK_SERVICE_ADD_HEIGHT,
    MOCK_SERVICE_ADD_NOTE,
    MOCK_SERVICE_ADD_TEMPERATURE,
    MOCK_SERVICE_ADD_WEIGHT,
)

_CHILD = MOCK_SERVICE_ADD_CHILD_SCHEMA


async def test_service_add_bmi(
    hass: HomeAssistant,
    bb_coordinator: BabyBuddyCoordinator,
) -> None:
    """Test the "add bmi" service call."""
    meta = bb_coordinator.metadata
    smeta = find_sensor_meta(meta, "bmi")
    baby_eid = child_entity_id(meta, _CHILD)
    eid = sensor_entity_id(meta, _CHILD, "bmi")

    await hass.services.async_call(
        DOMAIN,
        "add_bmi",
        MOCK_SERVICE_ADD_BMI_SCHEMA,
        target={ATTR_ENTITY_ID: baby_eid},
        blocking=True,
    )
    state = hass.states.get(eid)

    assert state
    assert_sensor_meta(state, smeta)
    assert state.attributes["notes"] == MOCK_SERVICE_ADD_BMI_SCHEMA["notes"]
    assert state.attributes["tags"] == MOCK_SERVICE_ADD_BMI_SCHEMA["tags"]
    assert state.state == str(MOCK_SERVICE_ADD_BMI_SCHEMA["bmi"])


async def test_service_add_diaper_change(
    hass: HomeAssistant,
    bb_coordinator: BabyBuddyCoordinator,
) -> None:
    """Test the "add diaper change" service call."""
    meta = bb_coordinator.metadata
    smeta = find_sensor_meta(meta, "changes")
    baby_eid = child_entity_id(meta, _CHILD)
    eid = sensor_entity_id(meta, _CHILD, "changes")

    await hass.services.async_call(
        DOMAIN,
        "add_diaper_change",
        MOCK_SERVICE_ADD_DIAPER_CHANGE,
        target={ATTR_ENTITY_ID: baby_eid},
        blocking=True,
    )
    state = hass.states.get(eid)

    assert state
    assert_sensor_meta(state, smeta)
    assert state.attributes["notes"] == MOCK_SERVICE_ADD_DIAPER_CHANGE["notes"]
    assert state.attributes["tags"] == MOCK_SERVICE_ADD_DIAPER_CHANGE["tags"]
    assert (
        dt_util.parse_datetime(state.state) == MOCK_SERVICE_ADD_DIAPER_CHANGE[ATTR_TIME]
    )


async def test_service_add_head_circumference(
    hass: HomeAssistant,
    bb_coordinator: BabyBuddyCoordinator,
) -> None:
    """Test the "add head circumference" service call."""
    meta = bb_coordinator.metadata
    smeta = find_sensor_meta(meta, "head-circumference")
    baby_eid = child_entity_id(meta, _CHILD)
    eid = sensor_entity_id(meta, _CHILD, "head-circumference")

    await hass.services.async_call(
        DOMAIN,
        "add_head_circumference",
        MOCK_SERVICE_ADD_HEAD_CIRCUMFERENCE,
        target={ATTR_ENTITY_ID: baby_eid},
        blocking=True,
    )
    state = hass.states.get(eid)

    assert state
    assert_sensor_meta(state, smeta)
    assert (
        state.attributes["notes"] == MOCK_SERVICE_ADD_HEAD_CIRCUMFERENCE["notes"]
    )
    assert state.attributes["tags"] == MOCK_SERVICE_ADD_HEAD_CIRCUMFERENCE["tags"]
    assert state.state == str(
        MOCK_SERVICE_ADD_HEAD_CIRCUMFERENCE["head_circumference"]
    )


async def test_service_add_height(
    hass: HomeAssistant,
    bb_coordinator: BabyBuddyCoordinator,
) -> None:
    """Test the "add height" service call."""
    meta = bb_coordinator.metadata
    smeta = find_sensor_meta(meta, "height")
    baby_eid = child_entity_id(meta, _CHILD)
    eid = sensor_entity_id(meta, _CHILD, "height")

    await hass.services.async_call(
        DOMAIN,
        "add_height",
        MOCK_SERVICE_ADD_HEIGHT,
        target={ATTR_ENTITY_ID: baby_eid},
        blocking=True,
    )
    state = hass.states.get(eid)

    assert state
    assert_sensor_meta(state, smeta)
    assert state.attributes["notes"] == MOCK_SERVICE_ADD_HEIGHT["notes"]
    assert state.attributes["tags"] == MOCK_SERVICE_ADD_HEIGHT["tags"]
    assert state.state == str(MOCK_SERVICE_ADD_HEIGHT["height"])


async def test_service_add_note(
    hass: HomeAssistant,
    bb_coordinator: BabyBuddyCoordinator,
) -> None:
    """Test the "add note" service call."""
    meta = bb_coordinator.metadata
    smeta = find_sensor_meta(meta, "notes")
    baby_eid = child_entity_id(meta, _CHILD)
    eid = sensor_entity_id(meta, _CHILD, "notes")

    await hass.services.async_call(
        DOMAIN,
        "add_note",
        MOCK_SERVICE_ADD_NOTE,
        target={ATTR_ENTITY_ID: baby_eid},
        blocking=True,
    )
    state = hass.states.get(eid)

    assert state
    assert_sensor_meta(state, smeta)
    assert state.attributes["note"] == MOCK_SERVICE_ADD_NOTE["note"]
    assert state.attributes["tags"] == MOCK_SERVICE_ADD_NOTE["tags"]
    assert dt_util.parse_datetime(state.state) == MOCK_SERVICE_ADD_NOTE[ATTR_TIME]


async def test_service_add_temperature(
    hass: HomeAssistant,
    bb_coordinator: BabyBuddyCoordinator,
) -> None:
    """Test the "add temperature" service call."""
    meta = bb_coordinator.metadata
    smeta = find_sensor_meta(meta, "temperature")
    baby_eid = child_entity_id(meta, _CHILD)
    eid = sensor_entity_id(meta, _CHILD, "temperature")

    await hass.services.async_call(
        DOMAIN,
        "add_temperature",
        MOCK_SERVICE_ADD_TEMPERATURE,
        target={ATTR_ENTITY_ID: baby_eid},
        blocking=True,
    )
    state = hass.states.get(eid)

    assert state
    assert_sensor_meta(state, smeta)
    assert state.attributes["notes"] == MOCK_SERVICE_ADD_TEMPERATURE["notes"]
    assert state.attributes["tags"] == MOCK_SERVICE_ADD_TEMPERATURE["tags"]
    assert state.state == str(MOCK_SERVICE_ADD_TEMPERATURE[ATTR_TEMPERATURE])


async def test_service_add_weight(
    hass: HomeAssistant,
    bb_coordinator: BabyBuddyCoordinator,
) -> None:
    """Test the "add weight" service call."""
    meta = bb_coordinator.metadata
    smeta = find_sensor_meta(meta, "weight")
    baby_eid = child_entity_id(meta, _CHILD)
    eid = sensor_entity_id(meta, _CHILD, "weight")

    await hass.services.async_call(
        DOMAIN,
        "add_weight",
        MOCK_SERVICE_ADD_WEIGHT,
        target={ATTR_ENTITY_ID: baby_eid},
        blocking=True,
    )
    state = hass.states.get(eid)

    assert state
    assert_sensor_meta(state, smeta)
    assert state.attributes["notes"] == MOCK_SERVICE_ADD_WEIGHT["notes"]
    assert state.attributes["tags"] == MOCK_SERVICE_ADD_WEIGHT["tags"]
    assert state.state == str(MOCK_SERVICE_ADD_WEIGHT["weight"])
