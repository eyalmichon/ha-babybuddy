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


@dataclass
class BabyBuddyEntityDescription(SensorEntityDescription):
    """Describe Baby Buddy sensor entity."""

    state_key: Callable[[dict], int] | str = ""


@dataclass
class BabyBuddySelectDescription(SelectEntityDescription):
    """Describe Baby Buddy select entity."""


ERR_TIME_FUTURE: Final[str] = "Time cannot be in the future."
ERR_TIMER_NOT_FOUND: Final[str] = "Timer not found or stopped. Timer must be active."

PLATFORMS: Final = ["binary_sensor", "sensor", "select", "switch"]
