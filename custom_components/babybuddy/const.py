"""Constants for babybuddy integration."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import TYPE_CHECKING, Final

if TYPE_CHECKING:
    from collections.abc import Callable

from homeassistant.components.select import SelectEntityDescription
from homeassistant.components.sensor import SensorEntityDescription

LOGGER = logging.getLogger(__package__)

DOMAIN: Final[str] = "babybuddy"

CONF_FEEDING_UNIT: Final[str] = "feedings"
CONF_MQTT_ENABLED: Final[str] = "mqtt_enabled"
CONF_MQTT_TOPIC_PREFIX: Final[str] = "mqtt_topic_prefix"
CONF_WEIGHT_UNIT: Final[str] = "weight"

DEFAULT_NAME: Final[str] = "Baby Buddy"
DEFAULT_PORT: Final[int] = 8000
DEFAULT_PATH: Final[str] = ""
DEFAULT_SCAN_INTERVAL: Final[int] = 60
DEFAULT_MQTT_TOPIC_PREFIX: Final[str] = "babybuddy"

CONFIG_FLOW_VERSION: Final[int] = 2
CONFIG_FLOW_MINOR_VERSION: Final[int] = 1

ATTR_AMOUNT: Final[str] = "amount"
ATTR_BABYBUDDY_CHILD: Final[str] = "babybuddy_child"
ATTR_BIRTH_DATE: Final[str] = "birth_date"
ATTR_BMI: Final[str] = "bmi"
ATTR_CHANGES: Final[str] = "changes"
ATTR_CHILD: Final[str] = "child"
ATTR_CHILDREN: Final[str] = "children"
ATTR_COLOR: Final[str] = "color"
ATTR_COUNT: Final[str] = "count"
ATTR_DESCRIPTIVE: Final[str] = "descriptive"
ATTR_END: Final[str] = "end"
ATTR_FEEDINGS: Final[str] = "feedings"
ATTR_FIRST_NAME: Final[str] = "first_name"
ATTR_HEAD_CIRCUMFERENCE_DASH: Final[str] = "head-circumference"
ATTR_HEAD_CIRCUMFERENCE_UNDERSCORE: Final[str] = "head_circumference"
ATTR_HEIGHT: Final[str] = "height"
ATTR_LAST_NAME: Final[str] = "last_name"
ATTR_MEDICATION: Final[str] = "medications"
ATTR_METHOD: Final[str] = "method"
ATTR_MILESTONE: Final[str] = "milestone"
ATTR_NAP: Final[str] = "nap"
ATTR_NOTE: Final[str] = "note"
ATTR_NOTES: Final[str] = "notes"
ATTR_PICTURE: Final[str] = "picture"
ATTR_PUMPING: Final[str] = "pumping"
ATTR_RESULTS: Final[str] = "results"
ATTR_SLEEP: Final[str] = "sleep"
ATTR_SLUG: Final[str] = "slug"
ATTR_SOLID: Final[str] = "solid"
ATTR_START: Final[str] = "start"
ATTR_TAGS: Final[str] = "tags"
ATTR_TIMER: Final[str] = "timer"
ATTR_TIMERS: Final[str] = "timers"
ATTR_TUMMY_TIMES: Final[str] = "tummy-times"
ATTR_TYPE: Final[str] = "type"
ATTR_WEIGHT: Final[str] = "weight"
ATTR_WET: Final[str] = "wet"

ATTR_ICON_CHILD_SENSOR: Final[str] = "mdi:baby-face-outline"
ATTR_ICON_TIMER_SAND: Final[str] = "mdi:timer-sand"

ATTR_ACTION_ADD_BMI: Final[str] = "add_bmi"
ATTR_ACTION_ADD_CHILD: Final[str] = "add_child"
ATTR_ACTION_ADD_DIAPER_CHANGE: Final[str] = "add_diaper_change"
ATTR_ACTION_ADD_FEEDING: Final[str] = "add_feeding"
ATTR_ACTION_ADD_HEAD_CIRCUMFERENCE: Final[str] = "add_head_circumference"
ATTR_ACTION_ADD_HEIGHT: Final[str] = "add_height"
ATTR_ACTION_ADD_NOTE: Final[str] = "add_note"
ATTR_ACTION_ADD_PUMPING: Final[str] = "add_pumping"
ATTR_ACTION_ADD_SLEEP: Final[str] = "add_sleep"
ATTR_ACTION_ADD_TEMPERATURE: Final[str] = "add_temperature"
ATTR_ACTION_ADD_TUMMY_TIME: Final[str] = "add_tummy_time"
ATTR_ACTION_ADD_WEIGHT: Final[str] = "add_weight"
ATTR_ACTION_ADD_MEDICATION: Final[str] = "add_medication"
ATTR_ACTION_DELETE_LAST_ENTRY: Final[str] = "delete_last_entry"
ATTR_ACTION_GIVE_MEDICATION: Final[str] = "give_medication"

DIAPER_COLORS: Final = ["Black", "Brown", "Green", "Yellow"]
DIAPER_TYPES: Final = ["Wet", "Solid", "Wet and Solid"]
FEEDING_METHODS: Final = [
    "Bottle",
    "Left breast",
    "Right breast",
    "Both breasts",
    "Parent fed",
    "Self fed",
]
FEEDING_TYPES: Final = ["Breast milk", "Formula", "Fortified breast milk", "Solid food"]


@dataclass
class BabyBuddyEntityDescription(SensorEntityDescription):
    """Describe Baby Buddy sensor entity."""

    state_key: Callable[[dict], int] | str = ""


@dataclass
class BabyBuddySelectDescription(SelectEntityDescription):
    """Describe Baby Buddy select entity."""


PLATFORMS: Final = ["binary_sensor", "sensor", "select", "switch"]
