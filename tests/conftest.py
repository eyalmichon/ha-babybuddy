"""Global fixtures for babybuddy integration."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

import pytest
from homeassistant import config_entries
from homeassistant.util import slugify
from pytest_socket import _remove_restrictions

from custom_components.babybuddy.const import DOMAIN

from .const import MOCK_CONFIG

if TYPE_CHECKING:
    from homeassistant.core import HomeAssistant

    from custom_components.babybuddy.coordinator import BabyBuddyCoordinator

pytest_plugins = "pytest_homeassistant_custom_component"


# ---------------------------------------------------------------------------
# Metadata lookup helpers
# ---------------------------------------------------------------------------


def find_sensor_meta(metadata: dict[str, Any], key: str) -> dict[str, Any]:
    """Find sensor metadata entry by its endpoint key (e.g. ``"bmi"``)."""
    return next(s for s in metadata["sensors"] if s["key"] == key)


def sensor_entity_id(
    metadata: dict[str, Any], child: dict[str, Any], sensor_key: str
) -> str:
    """Derive a sensor entity_id from metadata and child info."""
    tmpl = metadata.get("child", {}).get(
        "name_template", "{first_name} {last_name}"
    )
    device_name = tmpl.replace(
        "{first_name}", child["first_name"]
    ).replace("{last_name}", child["last_name"])
    sensor_meta = find_sensor_meta(metadata, sensor_key)
    slug = slugify(f"{device_name} {sensor_meta['name']}")
    return f"sensor.{slug}"


def switch_entity_id(metadata: dict[str, Any], child: dict[str, Any]) -> str:
    """Derive the timer switch entity_id from metadata and child info."""
    tmpl = metadata.get("child", {}).get(
        "name_template", "{first_name} {last_name}"
    )
    device_name = tmpl.replace(
        "{first_name}", child["first_name"]
    ).replace("{last_name}", child["last_name"])
    timer_name = metadata.get("timer", {}).get("name", "Timer")
    slug = slugify(f"{device_name} {timer_name}")
    return f"switch.{slug}"


def child_entity_id(metadata: dict[str, Any], child: dict[str, Any]) -> str:
    """Derive the primary child sensor entity_id from metadata."""
    tmpl = metadata.get("child", {}).get(
        "name_template", "{first_name} {last_name}"
    )
    device_name = tmpl.replace(
        "{first_name}", child["first_name"]
    ).replace("{last_name}", child["last_name"])
    return f"sensor.{slugify(device_name)}"


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture(autouse=True)
def enable_socket_fixture():
    """Remove all socket restrictions so tests can reach the live BB instance."""
    _remove_restrictions()


@pytest.fixture(autouse=True)
def auto_enable_custom_integrations(enable_custom_integrations):
    """Enable loading custom integrations."""
    return


@pytest.fixture
async def setup_baby_buddy_entry_live(hass: HomeAssistant):
    """Create a live config entry via the user flow and return it."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], user_input=MOCK_CONFIG
    )
    return result["result"]


@pytest.fixture
async def bb_coordinator(
    hass: HomeAssistant, setup_baby_buddy_entry_live
) -> BabyBuddyCoordinator:
    """Return the BabyBuddyCoordinator from the loaded entry."""
    entry = setup_baby_buddy_entry_live
    return entry.runtime_data.coordinator
