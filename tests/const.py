"""Constants for babybuddy tests."""

from __future__ import annotations

import json
import os
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Final
from zoneinfo import ZoneInfo

from homeassistant.const import (
    ATTR_DATE,
    ATTR_TEMPERATURE,
    ATTR_TIME,
    CONF_API_KEY,
    CONF_HOST,
    CONF_PATH,
    CONF_PORT,
    CONF_SCAN_INTERVAL,
    TEMPERATURE,
    UnitOfMass,
    UnitOfTemperature,
    UnitOfVolume,
)
from homeassistant.util import dt as dt_util

from custom_components.babybuddy.const import (
    CONF_FEEDING_UNIT,
    CONF_MQTT_ENABLED,
    CONF_MQTT_TOPIC_PREFIX,
    CONF_WEIGHT_UNIT,
    DEFAULT_MQTT_TOPIC_PREFIX,
    DEFAULT_PATH,
    DEFAULT_PORT,
    DEFAULT_SCAN_INTERVAL,
)

ATTR_INT_10: Final[int] = 10
ATTR_STEP_ID_USER: Final[str] = "user"


def _resolve_bb_config() -> dict[str, Any]:
    """Read BB connection from HA's .storage, falling back to env vars."""
    storage = (
        Path(__file__).resolve().parents[1]
        / ".dev"
        / "ha"
        / ".storage"
        / "core.config_entries"
    )
    try:
        data = json.loads(storage.read_text())
        for entry in data["data"]["entries"]:
            if entry.get("domain") == "babybuddy":
                d = entry["data"]
                return {
                    CONF_HOST: d["host"],
                    CONF_PORT: d["port"],
                    CONF_PATH: d.get("path") or DEFAULT_PATH,
                    CONF_API_KEY: d["api_key"],
                }
    except (FileNotFoundError, KeyError, json.JSONDecodeError):
        pass
    return {
        CONF_HOST: os.environ.get("BABY_BUDDY_HOST", ""),
        CONF_PORT: int(os.environ.get("BABY_BUDDY_PORT", str(DEFAULT_PORT))),
        CONF_PATH: DEFAULT_PATH,
        CONF_API_KEY: os.environ.get("API_KEY", ""),
    }


MOCK_CONFIG = _resolve_bb_config()
INVALID_CONFIG_CONNECTERROR = {
    **MOCK_CONFIG,
    CONF_PATH: "lorem",
}
INVALID_CONFIG_AUTHORIZATIONERROR = {
    **MOCK_CONFIG,
    CONF_API_KEY: "lorem",
}
MOCK_OPTIONS = {
    TEMPERATURE: UnitOfTemperature.CELSIUS,
    CONF_WEIGHT_UNIT: UnitOfMass.GRAMS,
    CONF_FEEDING_UNIT: UnitOfVolume.MILLILITERS,
    CONF_SCAN_INTERVAL: DEFAULT_SCAN_INTERVAL,
    CONF_MQTT_ENABLED: False,
    CONF_MQTT_TOPIC_PREFIX: DEFAULT_MQTT_TOPIC_PREFIX,
}

MOCK_DATE_NOW: Final = dt_util.now().date()
MOCK_DATETIME_NOW: Final = datetime(2003, 1, 2, 1, 23, tzinfo=ZoneInfo("UTC"))
MOCK_DURATION: Final[timedelta] = timedelta(minutes=12, seconds=3)
MOCK_TEXT: Final[str] = "Lorem ipsum dolor sit amet, consectetur adipiscing elit."
MOCK_NUMBER: Final = 123.0

MOCK_SERVICE_ADD_CHILD_SCHEMA = {
    "birth_date": MOCK_DATE_NOW,
    "first_name": "lorem",
    "last_name": "ipsum",
}
MOCK_SERVICE_ADD_BMI_SCHEMA = {
    "bmi": MOCK_NUMBER,
    ATTR_DATE: MOCK_DATE_NOW,
    "notes": MOCK_TEXT,
    "tags": [MOCK_TEXT],
}
MOCK_SERVICE_ADD_DIAPER_CHANGE = {
    ATTR_TIME: MOCK_DATETIME_NOW,
    "notes": MOCK_TEXT,
    "type": "Wet and Solid",
    "color": "Black",
    "amount": MOCK_NUMBER,
    "tags": [MOCK_TEXT],
}
MOCK_SERVICE_ADD_HEAD_CIRCUMFERENCE = {
    "head_circumference": MOCK_NUMBER,
    ATTR_DATE: MOCK_DATE_NOW,
    "notes": MOCK_TEXT,
    "tags": [MOCK_TEXT],
}
MOCK_SERVICE_ADD_HEIGHT = {
    "height": MOCK_NUMBER,
    ATTR_DATE: MOCK_DATE_NOW,
    "notes": MOCK_TEXT,
    "tags": [MOCK_TEXT],
}
MOCK_SERVICE_ADD_NOTE = {
    ATTR_TIME: MOCK_DATETIME_NOW,
    "note": MOCK_TEXT,
    "tags": [MOCK_TEXT],
}
MOCK_SERVICE_ADD_PUMPING = {
    "amount": MOCK_NUMBER,
    ATTR_TIME: MOCK_DATETIME_NOW,
    "notes": MOCK_TEXT,
    "tags": [MOCK_TEXT],
}
MOCK_SERVICE_ADD_TEMPERATURE = {
    ATTR_TEMPERATURE: 102.3,
    ATTR_TIME: MOCK_DATETIME_NOW,
    "notes": MOCK_TEXT,
    "tags": [MOCK_TEXT],
}
MOCK_SERVICE_ADD_WEIGHT = {
    ATTR_DATE: MOCK_DATE_NOW,
    "notes": MOCK_TEXT,
    "weight": MOCK_NUMBER,
    "tags": [MOCK_TEXT],
}
MOCK_SERVICE_ADD_FEEDING = {
    "type": "Breast milk",
    "method": "Bottle",
    "amount": MOCK_NUMBER,
    "notes": MOCK_TEXT,
    "tags": [MOCK_TEXT],
}
MOCK_SERVICE_ADD_FEEDING_START_STOP = {
    **MOCK_SERVICE_ADD_FEEDING,
    "start": MOCK_DATETIME_NOW - MOCK_DURATION,
    "end": MOCK_DATETIME_NOW,
}
MOCK_SERVICE_ADD_FEEDING_TIMER = {
    **MOCK_SERVICE_ADD_FEEDING,
    "timer": True,
}
MOCK_SERVICE_ADD_PUMPING = {
    "amount": MOCK_NUMBER,
    "notes": MOCK_TEXT,
    "tags": [MOCK_TEXT],
}
MOCK_SERVICE_ADD_PUMPING_START_STOP = {
    **MOCK_SERVICE_ADD_PUMPING,
    "start": MOCK_DATETIME_NOW - MOCK_DURATION,
    "end": MOCK_DATETIME_NOW,
}
MOCK_SERVICE_ADD_PUMPING_TIMER = {
    **MOCK_SERVICE_ADD_PUMPING,
    "timer": True,
}
MOCK_SERVICE_ADD_SLEEP = {
    "nap": True,
    "notes": MOCK_TEXT,
    "tags": [MOCK_TEXT],
}
MOCK_SERVICE_ADD_SLEEP_START_STOP = {
    **MOCK_SERVICE_ADD_SLEEP,
    "start": MOCK_DATETIME_NOW - MOCK_DURATION,
    "end": MOCK_DATETIME_NOW,
}
MOCK_SERVICE_ADD_SLEEP_TIMER = {
    **MOCK_SERVICE_ADD_SLEEP,
    "timer": True,
}
MOCK_SERVICE_ADD_TUMMY_TIME = {
    "milestone": MOCK_TEXT,
    "tags": [MOCK_TEXT],
}
MOCK_SERVICE_ADD_TUMMY_TIME_START_STOP = {
    **MOCK_SERVICE_ADD_TUMMY_TIME,
    "start": MOCK_DATETIME_NOW - MOCK_DURATION,
    "end": MOCK_DATETIME_NOW,
}
MOCK_SERVICE_ADD_TUMMY_TIME_TIMER = {
    **MOCK_SERVICE_ADD_TUMMY_TIME,
    "timer": True,
}

