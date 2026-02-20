"""Test babybuddy timer switch and timer-based services (metadata-aware)."""

import asyncio
from datetime import timedelta

import pytest
from homeassistant.components.sensor.const import (
    ATTR_STATE_CLASS,
    SensorDeviceClass,
    SensorStateClass,
)
from homeassistant.components.switch import DOMAIN as SWITCH_DOMAIN
from homeassistant.const import (
    ATTR_DEVICE_CLASS,
    ATTR_ENTITY_ID,
    ATTR_ICON,
    SERVICE_TURN_ON,
    STATE_OFF,
    STATE_ON,
)
from homeassistant.core import HomeAssistant
from homeassistant.util import dt as dt_util

from custom_components.babybuddy.const import DOMAIN
from custom_components.babybuddy.coordinator import BabyBuddyCoordinator

from .conftest import find_sensor_meta, sensor_entity_id, switch_entity_id
from .const import (
    ATTR_INT_10,
    MOCK_DURATION,
    MOCK_SERVICE_ADD_CHILD_SCHEMA,
    MOCK_SERVICE_ADD_FEEDING_START_STOP,
    MOCK_SERVICE_ADD_FEEDING_TIMER,
    MOCK_SERVICE_ADD_PUMPING_START_STOP,
    MOCK_SERVICE_ADD_PUMPING_TIMER,
    MOCK_SERVICE_ADD_SLEEP_START_STOP,
    MOCK_SERVICE_ADD_SLEEP_TIMER,
    MOCK_SERVICE_ADD_TUMMY_TIME_START_STOP,
    MOCK_SERVICE_ADD_TUMMY_TIME_TIMER,
)

_CHILD = MOCK_SERVICE_ADD_CHILD_SCHEMA

_DEVICE_CLASS_MAP = {
    "timestamp": SensorDeviceClass.TIMESTAMP,
    "temperature": SensorDeviceClass.TEMPERATURE,
}
_STATE_CLASS_MAP = {
    "measurement": SensorStateClass.MEASUREMENT,
    "total": SensorStateClass.TOTAL,
    "total_increasing": SensorStateClass.TOTAL_INCREASING,
}


def _assert_sensor_meta(state, meta: dict) -> None:
    """Assert icon, device_class, and state_class match metadata."""
    assert state.attributes[ATTR_ICON] == meta["icon"]

    dc = meta.get("device_class")
    if dc and dc in _DEVICE_CLASS_MAP:
        assert state.attributes[ATTR_DEVICE_CLASS] == _DEVICE_CLASS_MAP[dc]

    sc = meta.get("state_class")
    if sc and sc in _STATE_CLASS_MAP:
        assert state.attributes[ATTR_STATE_CLASS] == _STATE_CLASS_MAP[sc]


def _find_child_id(coordinator: BabyBuddyCoordinator, child_schema: dict) -> int:
    """Find the BB child ID matching the given first/last name."""
    for child in coordinator.data[0]:
        if (
            child["first_name"] == child_schema["first_name"]
            and child["last_name"] == child_schema["last_name"]
        ):
            return child["id"]
    msg = f"Child {child_schema['first_name']} {child_schema['last_name']} not found"
    raise ValueError(msg)


async def _clear_entries(
    coordinator: BabyBuddyCoordinator, endpoint: str, child_id: int
) -> None:
    """Delete all entries for a child on the given endpoint to avoid overlap conflicts."""
    try:
        resp = await coordinator.client.async_get(endpoint, f"?child={child_id}")
        for entry in resp.get("results", []):
            await coordinator.client.async_delete(endpoint, str(entry["id"]))
    except Exception:  # noqa: BLE001, S110
        pass


@pytest.fixture
async def test_timer(
    hass: HomeAssistant, bb_coordinator: BabyBuddyCoordinator
) -> None:
    """Turn on the timer switch, yield, then verify cleanup."""
    meta = bb_coordinator.metadata
    timer_icon = meta.get("timer", {}).get("icon", "mdi:timer-sand")
    baby_switch_eid = switch_entity_id(meta, _CHILD)

    await hass.services.async_call(
        SWITCH_DOMAIN,
        SERVICE_TURN_ON,
        target={ATTR_ENTITY_ID: baby_switch_eid},
        blocking=True,
    )
    switch_state = hass.states.get(baby_switch_eid)

    assert switch_state
    assert switch_state.attributes[ATTR_ICON] == timer_icon
    assert switch_state.state == STATE_ON

    await asyncio.sleep(ATTR_INT_10)

    yield

    await asyncio.sleep(ATTR_INT_10)
    switch_state = hass.states.get(baby_switch_eid)

    assert switch_state
    assert switch_state.attributes[ATTR_ICON] == timer_icon
    assert switch_state.state == STATE_OFF


async def test_service_add_feeding_start_stop(
    hass: HomeAssistant,
    bb_coordinator: BabyBuddyCoordinator,
) -> None:
    """Test the "add feeding" service call via start/stop."""
    meta = bb_coordinator.metadata
    smeta = find_sensor_meta(meta, "feedings")
    eid = sensor_entity_id(meta, _CHILD, "feedings")
    sw_eid = switch_entity_id(meta, _CHILD)

    await hass.services.async_call(
        DOMAIN,
        "add_feeding",
        MOCK_SERVICE_ADD_FEEDING_START_STOP,
        target={ATTR_ENTITY_ID: sw_eid},
        blocking=True,
    )
    state = hass.states.get(eid)

    assert state
    _assert_sensor_meta(state, smeta)
    assert (
        state.attributes["notes"] == MOCK_SERVICE_ADD_FEEDING_START_STOP["notes"]
    )
    assert state.attributes["tags"] == MOCK_SERVICE_ADD_FEEDING_START_STOP["tags"]
    assert dt_util.parse_datetime(state.state) is not None


@pytest.mark.usefixtures("test_timer")
async def test_service_add_feeding_timer(
    hass: HomeAssistant,
    bb_coordinator: BabyBuddyCoordinator,
) -> None:
    """Test the "add feeding" service call via timer."""
    meta = bb_coordinator.metadata
    smeta = find_sensor_meta(meta, "feedings")
    eid = sensor_entity_id(meta, _CHILD, "feedings")
    sw_eid = switch_entity_id(meta, _CHILD)

    await hass.services.async_call(
        DOMAIN,
        "add_feeding",
        MOCK_SERVICE_ADD_FEEDING_TIMER,
        target={ATTR_ENTITY_ID: sw_eid},
        blocking=True,
    )
    state = hass.states.get(eid)

    assert state
    assert dt_util.parse_duration(state.attributes["duration"]) >= timedelta(
        seconds=ATTR_INT_10
    )
    _assert_sensor_meta(state, smeta)
    assert state.attributes["notes"] == MOCK_SERVICE_ADD_FEEDING_TIMER["notes"]
    assert state.attributes["tags"] == MOCK_SERVICE_ADD_FEEDING_TIMER["tags"]


async def test_service_add_pumping_start_stop(
    hass: HomeAssistant,
    bb_coordinator: BabyBuddyCoordinator,
) -> None:
    """Test the "add pumping" service call via start/stop."""
    meta = bb_coordinator.metadata
    smeta = find_sensor_meta(meta, "pumping")
    eid = sensor_entity_id(meta, _CHILD, "pumping")
    sw_eid = switch_entity_id(meta, _CHILD)

    await hass.services.async_call(
        DOMAIN,
        "add_pumping",
        MOCK_SERVICE_ADD_PUMPING_START_STOP,
        target={ATTR_ENTITY_ID: sw_eid},
        blocking=True,
    )
    state = hass.states.get(eid)

    assert state
    _assert_sensor_meta(state, smeta)
    assert (
        state.attributes["notes"] == MOCK_SERVICE_ADD_PUMPING_START_STOP["notes"]
    )
    assert state.attributes["tags"] == MOCK_SERVICE_ADD_PUMPING_START_STOP["tags"]
    assert state.state == str(MOCK_SERVICE_ADD_PUMPING_START_STOP["amount"])


@pytest.mark.usefixtures("test_timer")
async def test_service_add_pumping_timer(
    hass: HomeAssistant,
    bb_coordinator: BabyBuddyCoordinator,
) -> None:
    """Test the "add pumping" service call via timer."""
    meta = bb_coordinator.metadata
    smeta = find_sensor_meta(meta, "pumping")
    eid = sensor_entity_id(meta, _CHILD, "pumping")
    sw_eid = switch_entity_id(meta, _CHILD)

    await hass.services.async_call(
        DOMAIN,
        "add_pumping",
        MOCK_SERVICE_ADD_PUMPING_TIMER,
        target={ATTR_ENTITY_ID: sw_eid},
        blocking=True,
    )
    state = hass.states.get(eid)

    assert state
    assert dt_util.parse_duration(state.attributes["duration"]) >= timedelta(
        seconds=ATTR_INT_10
    )
    _assert_sensor_meta(state, smeta)
    assert state.attributes["notes"] == MOCK_SERVICE_ADD_PUMPING_TIMER["notes"]
    assert state.attributes["tags"] == MOCK_SERVICE_ADD_PUMPING_TIMER["tags"]
    assert state.state == str(MOCK_SERVICE_ADD_PUMPING_TIMER["amount"])


async def test_service_add_sleep_start_stop(
    hass: HomeAssistant,
    bb_coordinator: BabyBuddyCoordinator,
) -> None:
    """Test the "add sleep" service call via start/stop."""
    meta = bb_coordinator.metadata
    smeta = find_sensor_meta(meta, "sleep")
    eid = sensor_entity_id(meta, _CHILD, "sleep")
    sw_eid = switch_entity_id(meta, _CHILD)

    child_id = _find_child_id(bb_coordinator, _CHILD)
    await _clear_entries(bb_coordinator, "sleep", child_id)

    end = dt_util.now() - timedelta(seconds=5)
    service_data = {
        **MOCK_SERVICE_ADD_SLEEP_START_STOP,
        "start": end - MOCK_DURATION,
        "end": end,
    }
    await hass.services.async_call(
        DOMAIN,
        "add_sleep",
        service_data,
        target={ATTR_ENTITY_ID: sw_eid},
        blocking=True,
    )
    state = hass.states.get(eid)

    assert state
    _assert_sensor_meta(state, smeta)
    assert state.attributes["notes"] == service_data["notes"]
    assert state.attributes["tags"] == service_data["tags"]
    assert state.state == str(int(MOCK_DURATION.total_seconds() / 60))


@pytest.mark.usefixtures("test_timer")
async def test_service_add_sleep_timer(
    hass: HomeAssistant,
    bb_coordinator: BabyBuddyCoordinator,
) -> None:
    """Test the "add sleep" service call via timer."""
    meta = bb_coordinator.metadata
    smeta = find_sensor_meta(meta, "sleep")
    eid = sensor_entity_id(meta, _CHILD, "sleep")
    sw_eid = switch_entity_id(meta, _CHILD)

    await hass.services.async_call(
        DOMAIN,
        "add_sleep",
        MOCK_SERVICE_ADD_SLEEP_TIMER,
        target={ATTR_ENTITY_ID: sw_eid},
        blocking=True,
    )
    state = hass.states.get(eid)

    assert state
    assert dt_util.parse_duration(state.attributes["duration"]) >= timedelta(
        seconds=ATTR_INT_10
    )
    _assert_sensor_meta(state, smeta)
    assert state.attributes["notes"] == MOCK_SERVICE_ADD_SLEEP_TIMER["notes"]
    assert state.attributes["tags"] == MOCK_SERVICE_ADD_SLEEP_TIMER["tags"]
    assert state.state == "0"  # int() on ~10 sec == 0


async def test_service_add_tummy_time_start_stop(
    hass: HomeAssistant,
    bb_coordinator: BabyBuddyCoordinator,
) -> None:
    """Test the "add tummy time" service call via start/stop."""
    meta = bb_coordinator.metadata
    smeta = find_sensor_meta(meta, "tummy-times")
    eid = sensor_entity_id(meta, _CHILD, "tummy-times")
    sw_eid = switch_entity_id(meta, _CHILD)

    child_id = _find_child_id(bb_coordinator, _CHILD)
    await _clear_entries(bb_coordinator, "tummy-times", child_id)

    end = dt_util.now() - timedelta(seconds=5)
    service_data = {
        **MOCK_SERVICE_ADD_TUMMY_TIME_START_STOP,
        "start": end - MOCK_DURATION,
        "end": end,
    }
    await hass.services.async_call(
        DOMAIN,
        "add_tummy_time",
        service_data,
        target={ATTR_ENTITY_ID: sw_eid},
        blocking=True,
    )
    state = hass.states.get(eid)

    assert state
    _assert_sensor_meta(state, smeta)
    assert (
        state.attributes["milestone"]
        == service_data["milestone"]
    )
    assert (
        state.attributes["tags"] == service_data["tags"]
    )
    assert state.state == str(int(MOCK_DURATION.total_seconds() / 60))


@pytest.mark.usefixtures("test_timer")
async def test_service_add_tummy_time_timer(
    hass: HomeAssistant,
    bb_coordinator: BabyBuddyCoordinator,
) -> None:
    """Test the "add tummy time" service call via timer."""
    meta = bb_coordinator.metadata
    smeta = find_sensor_meta(meta, "tummy-times")
    eid = sensor_entity_id(meta, _CHILD, "tummy-times")
    sw_eid = switch_entity_id(meta, _CHILD)

    await hass.services.async_call(
        DOMAIN,
        "add_tummy_time",
        MOCK_SERVICE_ADD_TUMMY_TIME_TIMER,
        target={ATTR_ENTITY_ID: sw_eid},
        blocking=True,
    )
    state = hass.states.get(eid)

    assert state
    assert dt_util.parse_duration(state.attributes["duration"]) >= timedelta(
        seconds=ATTR_INT_10
    )
    _assert_sensor_meta(state, smeta)
    assert (
        state.attributes["milestone"]
        == MOCK_SERVICE_ADD_TUMMY_TIME_TIMER["milestone"]
    )
    assert state.attributes["tags"] == MOCK_SERVICE_ADD_TUMMY_TIME_TIMER["tags"]
    assert state.state == "0"  # int() on ~10 sec == 0
