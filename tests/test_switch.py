"""Test babybuddy timer-based (button) services (metadata-aware)."""

import asyncio
from datetime import timedelta

import pytest
from homeassistant.const import ATTR_ENTITY_ID
from homeassistant.core import HomeAssistant
from homeassistant.util import dt as dt_util

from custom_components.babybuddy.const import ACTIVE_TIMERS_KEY, DOMAIN
from custom_components.babybuddy.coordinator import BabyBuddyCoordinator

from .conftest import assert_sensor_meta, button_entity_id, child_entity_id, find_sensor_meta, sensor_entity_id
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


def _find_child_id(coordinator: BabyBuddyCoordinator, child_schema: dict) -> int:
    """Find the BB child ID matching the given first/last name."""
    for child in coordinator.data.children:
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
    """Start a timer via the start_timer service, yield, then verify cleanup."""
    meta = bb_coordinator.metadata
    baby_eid = child_entity_id(meta, _CHILD)
    child_id = _find_child_id(bb_coordinator, _CHILD)
    timer_ep = meta.get("timer", {}).get("endpoint", "timers")

    # Clear any stale timers from previous runs
    await _clear_entries(bb_coordinator, timer_ep, child_id)
    await bb_coordinator.async_refresh()

    await hass.services.async_call(
        DOMAIN,
        "start_timer",
        {"child": baby_eid},
        blocking=True,
    )

    # start_timer calls async_request_refresh; force a full blocking refresh
    await bb_coordinator.async_refresh()
    timers = bb_coordinator.data.child_data.get(child_id, {}).get(ACTIVE_TIMERS_KEY, [])
    assert len(timers) > 0, "Timer was not created"

    await asyncio.sleep(ATTR_INT_10)

    yield

    await bb_coordinator.async_refresh()


async def test_service_add_feeding_start_stop(
    hass: HomeAssistant,
    bb_coordinator: BabyBuddyCoordinator,
) -> None:
    """Test the "add feeding" service call via start/stop."""
    meta = bb_coordinator.metadata
    smeta = find_sensor_meta(meta, "feedings")
    eid = sensor_entity_id(meta, _CHILD, "feedings")
    baby_eid = child_entity_id(meta, _CHILD)

    child_id = _find_child_id(bb_coordinator, _CHILD)
    await _clear_entries(bb_coordinator, "feedings", child_id)

    end = dt_util.now() - timedelta(seconds=5)
    service_data = {
        **MOCK_SERVICE_ADD_FEEDING_START_STOP,
        "start": end - MOCK_DURATION,
        "end": end,
    }

    await hass.services.async_call(
        DOMAIN,
        "add_feeding",
        service_data,
        target={ATTR_ENTITY_ID: baby_eid},
        blocking=True,
    )
    state = hass.states.get(eid)

    assert state
    assert_sensor_meta(state, smeta)
    assert (
        state.attributes["notes"] == service_data["notes"]
    )
    assert state.attributes["tags"] == service_data["tags"]
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
    baby_eid = child_entity_id(meta, _CHILD)

    await hass.services.async_call(
        DOMAIN,
        "add_feeding",
        MOCK_SERVICE_ADD_FEEDING_TIMER,
        target={ATTR_ENTITY_ID: baby_eid},
        blocking=True,
    )
    state = hass.states.get(eid)

    assert state
    assert dt_util.parse_duration(state.attributes["duration"]) >= timedelta(
        seconds=ATTR_INT_10
    )
    assert_sensor_meta(state, smeta)
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
    baby_eid = child_entity_id(meta, _CHILD)

    child_id = _find_child_id(bb_coordinator, _CHILD)
    await _clear_entries(bb_coordinator, "pumping", child_id)

    end = dt_util.now() - timedelta(seconds=5)
    service_data = {
        **MOCK_SERVICE_ADD_PUMPING_START_STOP,
        "start": end - MOCK_DURATION,
        "end": end,
    }

    await hass.services.async_call(
        DOMAIN,
        "add_pumping",
        service_data,
        target={ATTR_ENTITY_ID: baby_eid},
        blocking=True,
    )
    state = hass.states.get(eid)

    assert state
    assert_sensor_meta(state, smeta)
    assert (
        state.attributes["notes"] == service_data["notes"]
    )
    assert state.attributes["tags"] == service_data["tags"]
    assert state.state == str(service_data["amount"])


@pytest.mark.usefixtures("test_timer")
async def test_service_add_pumping_timer(
    hass: HomeAssistant,
    bb_coordinator: BabyBuddyCoordinator,
) -> None:
    """Test the "add pumping" service call via timer."""
    meta = bb_coordinator.metadata
    smeta = find_sensor_meta(meta, "pumping")
    eid = sensor_entity_id(meta, _CHILD, "pumping")
    baby_eid = child_entity_id(meta, _CHILD)

    await hass.services.async_call(
        DOMAIN,
        "add_pumping",
        MOCK_SERVICE_ADD_PUMPING_TIMER,
        target={ATTR_ENTITY_ID: baby_eid},
        blocking=True,
    )
    state = hass.states.get(eid)

    assert state
    assert dt_util.parse_duration(state.attributes["duration"]) >= timedelta(
        seconds=ATTR_INT_10
    )
    assert_sensor_meta(state, smeta)
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
    baby_eid = child_entity_id(meta, _CHILD)

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
        target={ATTR_ENTITY_ID: baby_eid},
        blocking=True,
    )
    state = hass.states.get(eid)

    assert state
    assert_sensor_meta(state, smeta)
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
    baby_eid = child_entity_id(meta, _CHILD)

    await hass.services.async_call(
        DOMAIN,
        "add_sleep",
        MOCK_SERVICE_ADD_SLEEP_TIMER,
        target={ATTR_ENTITY_ID: baby_eid},
        blocking=True,
    )
    state = hass.states.get(eid)

    assert state
    assert dt_util.parse_duration(state.attributes["duration"]) >= timedelta(
        seconds=ATTR_INT_10
    )
    assert_sensor_meta(state, smeta)
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
    baby_eid = child_entity_id(meta, _CHILD)

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
        target={ATTR_ENTITY_ID: baby_eid},
        blocking=True,
    )
    state = hass.states.get(eid)

    assert state
    assert_sensor_meta(state, smeta)
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
    baby_eid = child_entity_id(meta, _CHILD)

    await hass.services.async_call(
        DOMAIN,
        "add_tummy_time",
        MOCK_SERVICE_ADD_TUMMY_TIME_TIMER,
        target={ATTR_ENTITY_ID: baby_eid},
        blocking=True,
    )
    state = hass.states.get(eid)

    assert state
    assert dt_util.parse_duration(state.attributes["duration"]) >= timedelta(
        seconds=ATTR_INT_10
    )
    assert_sensor_meta(state, smeta)
    assert (
        state.attributes["milestone"]
        == MOCK_SERVICE_ADD_TUMMY_TIME_TIMER["milestone"]
    )
    assert state.attributes["tags"] == MOCK_SERVICE_ADD_TUMMY_TIME_TIMER["tags"]
    assert state.state == "0"  # int() on ~10 sec == 0
