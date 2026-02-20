"""Dynamic entity discovery for Baby Buddy.

Defines the metadata contract between Baby Buddy and this integration.
Baby Buddy serves entity metadata via ``GET /api/ha/discovery/``.
The integration requires discovery v2 and will not load without it.
"""

from __future__ import annotations

from typing import Any

from homeassistant.components.sensor.const import SensorDeviceClass, SensorStateClass
from homeassistant.util import dt as dt_util

from .const import BabyBuddyEntityDescription, BabyBuddySelectDescription

# ---------------------------------------------------------------------------
# Known state-value transforms
# ---------------------------------------------------------------------------
# The metadata ``transform`` field references one of these by name so the
# integration knows how to derive the sensor state from the raw API entry.

KNOWN_TRANSFORMS: dict[str, Any] = {
    "duration_to_minutes": lambda value, field="duration": int(
        dt_util.parse_duration(value.get(field, "00:00:00")).total_seconds() / 60
    ),
}

# ---------------------------------------------------------------------------
# Device-class / state-class string → HA enum mappings
# ---------------------------------------------------------------------------

_DEVICE_CLASS_MAP: dict[str, SensorDeviceClass] = {
    "timestamp": SensorDeviceClass.TIMESTAMP,
    "temperature": SensorDeviceClass.TEMPERATURE,
}

_STATE_CLASS_MAP: dict[str, SensorStateClass] = {
    "measurement": SensorStateClass.MEASUREMENT,
    "total": SensorStateClass.TOTAL,
    "total_increasing": SensorStateClass.TOTAL_INCREASING,
}

# ---------------------------------------------------------------------------
# Factory helpers
# ---------------------------------------------------------------------------


def sensor_description_from_metadata(
    meta: dict[str, Any],
) -> BabyBuddyEntityDescription:
    """Create a ``BabyBuddyEntityDescription`` from a discovery dict."""
    kwargs: dict[str, Any] = {
        "key": meta["key"],
        "name": meta.get("name"),
        "icon": meta.get("icon"),
    }

    dc = meta.get("device_class")
    if dc and dc in _DEVICE_CLASS_MAP:
        kwargs["device_class"] = _DEVICE_CLASS_MAP[dc]

    sc = meta.get("state_class")
    if sc and sc in _STATE_CLASS_MAP:
        kwargs["state_class"] = _STATE_CLASS_MAP[sc]

    if meta.get("unit_of_measurement"):
        kwargs["native_unit_of_measurement"] = meta["unit_of_measurement"]

    transform_name = meta.get("transform")
    if transform_name and transform_name in KNOWN_TRANSFORMS:
        kwargs["state_key"] = KNOWN_TRANSFORMS[transform_name]
    else:
        kwargs["state_key"] = meta.get("state_key", "")

    return BabyBuddyEntityDescription(**kwargs)


def select_description_from_metadata(
    meta: dict[str, Any],
) -> BabyBuddySelectDescription:
    """Create a ``BabyBuddySelectDescription`` from a discovery dict."""
    return BabyBuddySelectDescription(
        key=meta["key"],
        name=f"Baby Buddy {meta['name']}",
        icon=meta.get("icon"),
        options=meta.get("options", []),
    )
