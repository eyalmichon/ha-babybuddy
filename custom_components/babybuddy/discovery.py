"""Dynamic entity discovery for Baby Buddy.

Defines the metadata contract between Baby Buddy and this integration.
Baby Buddy can serve this via ``GET /api/ha/discovery/``.  When that
endpoint is unavailable (older BB versions), ``FALLBACK_METADATA`` is
used instead -- it replicates the hardcoded entity definitions that
existed before this dynamic system.
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


# ---------------------------------------------------------------------------
# Fallback metadata  (used when BB lacks ``/api/ha/discovery/``)
# ---------------------------------------------------------------------------
# This exactly replicates the previously-hardcoded entity definitions so
# the integration works identically with older Baby Buddy versions.

FALLBACK_METADATA: dict[str, Any] = {
    "version": 1,
    "stats_endpoint": "/api/children/{slug}/stats/",
    "mqtt": {
        "default_topic_prefix": "babybuddy",
        "topics": {
            "feeding": "feedings",
            "diaper_change": "changes",
            "sleep": "sleep",
            "pumping": "pumping",
            "tummy_time": "tummy-times",
            "temperature": "temperature",
            "weight": "weight",
            "height": "height",
            "head_circumference": "head-circumference",
            "bmi": "bmi",
            "note": "notes",
            "medication": "medications",
            "medication_schedule": "medication_schedules",
            "timer": "timers",
        },
    },
    "sensors": [
        {
            "key": "bmi",
            "name": "Last BMI",
            "state_key": "bmi",
            "state_class": "measurement",
            "icon": "mdi:scale-bathroom",
        },
        {
            "key": "changes",
            "name": "Last Diaper Change",
            "state_key": "time",
            "device_class": "timestamp",
            "icon": "mdi:paper-roll-outline",
        },
        {
            "key": "feedings",
            "name": "Last Feeding",
            "state_key": "start",
            "device_class": "timestamp",
            "icon": "mdi:baby-bottle-outline",
        },
        {
            "key": "head-circumference",
            "name": "Last Head Circumference",
            "state_key": "head_circumference",
            "state_class": "measurement",
            "icon": "mdi:head-outline",
        },
        {
            "key": "height",
            "name": "Last Height",
            "state_key": "height",
            "state_class": "measurement",
            "icon": "mdi:human-male-height",
        },
        {
            "key": "medications",
            "name": "Last Medication",
            "state_key": "time",
            "device_class": "timestamp",
            "icon": "mdi:pill",
        },
        {
            "key": "notes",
            "name": "Last Note",
            "state_key": "time",
            "device_class": "timestamp",
            "icon": "mdi:note-multiple-outline",
        },
        {
            "key": "pumping",
            "name": "Last Pumping",
            "state_key": "amount",
            "state_class": "measurement",
            "icon": "mdi:mother-nurse",
        },
        {
            "key": "sleep",
            "name": "Last Sleep",
            "state_key": "duration",
            "transform": "duration_to_minutes",
            "state_class": "measurement",
            "unit_of_measurement": "min",
            "icon": "mdi:sleep",
        },
        {
            "key": "temperature",
            "name": "Temperature",
            "state_key": "temperature",
            "device_class": "temperature",
            "state_class": "measurement",
            "icon": "mdi:thermometer",
        },
        {
            "key": "timers",
            "name": "Last Timer",
            "state_key": "start",
            "device_class": "timestamp",
            "icon": "mdi:timer-sand",
        },
        {
            "key": "tummy-times",
            "name": "Last Tummy Time",
            "state_key": "duration",
            "transform": "duration_to_minutes",
            "state_class": "measurement",
            "unit_of_measurement": "min",
            "icon": "mdi:baby",
        },
        {
            "key": "weight",
            "name": "Last Weight",
            "state_key": "weight",
            "state_class": "measurement",
            "icon": "mdi:scale-bathroom",
        },
    ],
    "stats_sensors": [],
    "binary_sensors": [
        {
            "key": "medication_overdue",
            "name": "Medication Overdue",
            "device_class": "problem",
            "stats_field": "medications_overdue_count",
            "condition": "greater_than_zero",
            "attributes": {
                "overdue_names": "medications_overdue",
                "overdue_count": "medications_overdue_count",
            },
        },
    ],
    "selects": [
        {
            "key": "diaper_color",
            "name": "Diaper Color",
            "icon": "mdi:paper-roll-outline",
            "options": ["Black", "Brown", "Green", "Yellow"],
        },
        {
            "key": "change_type",
            "name": "Diaper Type",
            "icon": "mdi:paper-roll-outline",
            "options": ["Wet", "Solid", "Wet and Solid"],
        },
        {
            "key": "feeding_method",
            "name": "Feeding Method",
            "icon": "mdi:baby-bottle-outline",
            "options": [
                "Bottle",
                "Left breast",
                "Right breast",
                "Both breasts",
                "Parent fed",
                "Self fed",
            ],
        },
        {
            "key": "feeding_type",
            "name": "Feeding Type",
            "icon": "mdi:baby-bottle-outline",
            "options": [
                "Breast milk",
                "Formula",
                "Fortified breast milk",
                "Solid food",
            ],
        },
    ],
}
