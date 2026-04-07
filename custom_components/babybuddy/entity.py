"""Platform for babybuddy sensor integration."""

from __future__ import annotations

from collections.abc import Callable
from typing import TYPE_CHECKING, Any

from homeassistant.components.button import ButtonEntity
from homeassistant.components.select import SelectEntity
from homeassistant.components.sensor import SensorEntity
from homeassistant.components.sensor.const import SensorDeviceClass, SensorStateClass
from homeassistant.const import (
    ATTR_ID,
    CONF_HOST,
    CONF_PATH,
    CONF_PORT,
    UnitOfLength,
    UnitOfMass,
    UnitOfVolume,
)
from homeassistant.util.unit_system import METRIC_SYSTEM
from homeassistant.exceptions import ServiceValidationError
from homeassistant.helpers.restore_state import RestoreEntity
from homeassistant.helpers.typing import StateType
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.util import dt as dt_util

if TYPE_CHECKING:
    from homeassistant.core import HomeAssistant

from .const import (
    ACTIVE_TIMERS_KEY,
    DOMAIN,
    BabyBuddyEntityDescription,
    BabyBuddySelectDescription,
)
from .coordinator import BabyBuddyCoordinator
from .discovery import STATE_CLASS_MAP

_OPTIONS_KEY_ALIASES: dict[str, str] = {
    "pumping": "feedings",
}

def _is_metric(hass: HomeAssistant) -> bool:
    return hass.config.units is METRIC_SYSTEM

_UNIT_FALLBACKS: dict[str, Callable[[HomeAssistant], str]] = {
    "temperature": lambda hass: hass.config.units.temperature_unit,
    "weight": lambda hass: UnitOfMass.KILOGRAMS if _is_metric(hass) else UnitOfMass.POUNDS,
    "height": lambda hass: UnitOfLength.CENTIMETERS if _is_metric(hass) else UnitOfLength.INCHES,
    "head-circumference": lambda hass: UnitOfLength.CENTIMETERS if _is_metric(hass) else UnitOfLength.INCHES,
    "pumping": lambda hass: UnitOfVolume.MILLILITERS if _is_metric(hass) else UnitOfVolume.FLUID_OUNCES,
    "bmi": lambda _: "kg/m²",
}


def child_device_name(child: dict, metadata: dict) -> str:
    """Derive the HA device name for a child from metadata name_template."""
    name_template = metadata.get("child", {}).get(
        "name_template", "{first_name} {last_name}"
    )
    return name_template.replace(
        "{first_name}", child["first_name"]
    ).replace("{last_name}", child["last_name"])


def build_device_info(
    coordinator: BabyBuddyCoordinator, child: dict
) -> dict[str, Any]:
    """Build a consistent device_info dict for a child entity."""
    child_meta = coordinator.metadata.get("child", {})
    dashboard_path = child_meta.get(
        "dashboard_path", "/children/{slug}/dashboard/"
    ).replace("{slug}", child["slug"])
    device_name = child_device_name(child, coordinator.metadata)
    return {
        "configuration_url": (
            f"{coordinator.config_entry.data[CONF_HOST]}"
            f":{coordinator.config_entry.data[CONF_PORT]}"
            f"{coordinator.config_entry.data.get(CONF_PATH) or ''}"
            f"{dashboard_path}"
        ),
        "identifiers": {(DOMAIN, child[ATTR_ID])},
        "name": device_name,
    }


class BabyBuddySensor(CoordinatorEntity, SensorEntity):
    """Base class for babybuddy sensors."""

    _attr_has_entity_name = True
    coordinator: BabyBuddyCoordinator

    def __init__(self, coordinator: BabyBuddyCoordinator, child: dict) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self.child = child
        self._attr_device_info = build_device_info(coordinator, child)


class BabyBuddyChildSensor(BabyBuddySensor):
    """Representation of a babybuddy child sensor."""

    def __init__(self, coordinator: BabyBuddyCoordinator, child: dict) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator, child)

        self._attr_name = None  # Primary device entity: uses device name
        self._attr_unique_id = (
            f"{coordinator.config_entry.entry_id}-{child[ATTR_ID]}"
        )
        child_meta = coordinator.metadata.get("child", {})
        self._attr_native_value = child[child_meta.get("state_field", "birth_date")]
        self._attr_icon = child_meta.get("icon", "mdi:baby-face-outline")
        self._attr_device_class = child_meta.get("device_class", "babybuddy_child")

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return entity specific state attributes for babybuddy."""
        return self.child

    @property
    def entity_picture(self) -> str | None:
        """Return babybuddy picture."""
        picture_field = self.coordinator.metadata.get("child", {}).get(
            "picture_field", "picture"
        )
        image: str | None = self.child.get(picture_field)
        return image


class BabyBuddyChildDataSensor(BabyBuddySensor):
    """Representation of a child data sensor."""

    entity_description: BabyBuddyEntityDescription

    def __init__(
        self,
        coordinator: BabyBuddyCoordinator,
        child: dict,
        description: BabyBuddyEntityDescription,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator, child)

        self.entity_description = description
        self._attr_unique_id = f"{self.coordinator.config_entry.entry_id}-{child[ATTR_ID]}-{description.key}"

    @property
    def name(self) -> str | None:
        """Return the name of the babybuddy sensor."""
        if self.entity_description.name:
            return str(self.entity_description.name)
        # Fallback for descriptions without a name
        sensor_type = self.entity_description.key
        if sensor_type[-1] == "s":
            sensor_type = sensor_type[:-1]
        return f"Last {sensor_type}"

    @property
    def native_value(self) -> StateType:
        """Return entity state."""
        if not self.coordinator.data:
            return None
        data: dict[str, str] = (
            self.coordinator.data.child_data
            .get(self.child[ATTR_ID], {})
            .get(self.entity_description.key, {})
        )
        if not data:
            return None
        if callable(self.entity_description.state_key):
            return self.entity_description.state_key(data)
        if self.entity_description.device_class == SensorDeviceClass.TIMESTAMP:
            return dt_util.parse_datetime(data[self.entity_description.state_key])

        return data[self.entity_description.state_key]

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return entity specific state attributes."""
        attrs: dict[str, Any] = {}
        if not self.coordinator.data:
            return attrs
        data = (
            self.coordinator.data.child_data
            .get(self.child[ATTR_ID], {})
            .get(self.entity_description.key, {})
        )
        if data:
            attrs = dict(data)
            rt_name = self.entity_description.reverse_transform
            if rt_name:
                transform = self.coordinator.metadata.get("transforms", {}).get(rt_name, {})
                if transform.get("type") == "mapping":
                    mapping = transform.get("mapping", {})
                    for label, expected in mapping.items():
                        if all(attrs.get(k) == v for k, v in expected.items()):
                            attrs["descriptive"] = label
                            break

        if self.entity_description.group:
            attrs["bb_group"] = self.entity_description.group
        if self.entity_description.color:
            attrs["bb_color"] = self.entity_description.color

        return attrs

    @property
    def native_unit_of_measurement(self) -> str | None:
        """Return entity unit of measurement."""
        options = self.coordinator.config_entry.options
        key = self.entity_description.key
        from_options = options.get(key) or options.get(
            _OPTIONS_KEY_ALIASES.get(key, key)
        )
        if from_options:
            return from_options
        if self.entity_description.native_unit_of_measurement:
            return self.entity_description.native_unit_of_measurement
        fallback = _UNIT_FALLBACKS.get(key)
        if fallback:
            return fallback(self.hass)
        return None


class BabyBuddyStatsSensor(BabyBuddySensor):
    """Sensor that reads a value from the coordinator stats data."""

    def __init__(
        self,
        coordinator: BabyBuddyCoordinator,
        child: dict,
        stats_meta: dict[str, Any],
    ) -> None:
        """Initialize the stats sensor."""
        super().__init__(coordinator, child)
        self._stats_meta = stats_meta
        self._attr_unique_id = (
            f"{coordinator.config_entry.entry_id}"
            f"-{child[ATTR_ID]}-stats-{stats_meta['key']}"
        )
        self._attr_icon = stats_meta.get("icon")
        if stats_meta.get("unit_of_measurement"):
            self._attr_native_unit_of_measurement = stats_meta["unit_of_measurement"]

        sc = stats_meta.get("state_class")
        if sc and sc in STATE_CLASS_MAP:
            self._attr_state_class = STATE_CLASS_MAP[sc]

    @property
    def name(self) -> str:
        """Return the name of the sensor."""
        return self._stats_meta["name"]

    @property
    def _stats(self) -> dict[str, Any]:
        """Return the stats dict for this child, or empty dict."""
        if not self.coordinator.data:
            return {}
        return (
            self.coordinator.data.child_data
            .get(self.child[ATTR_ID], {})
            .get("stats", {})
        )

    @property
    def native_value(self) -> StateType:
        """Return the stats field value."""
        field = self._stats_meta.get("stats_field", self._stats_meta["key"])
        return self._stats.get(field)

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return stats sensor attributes including group metadata."""
        attrs: dict[str, Any] = {}
        group = self._stats_meta.get("group", "")
        if group:
            attrs["bb_group"] = group
        color = self._stats_meta.get("color", "")
        if color:
            attrs["bb_color"] = color
        return attrs

    @property
    def available(self) -> bool:
        """Return True if coordinator data is available."""
        return bool(self.coordinator.data)


class BabyBuddyStartTimerButton(CoordinatorEntity, ButtonEntity):
    """Button to start a new timer for a child."""

    _attr_has_entity_name = True
    coordinator: BabyBuddyCoordinator

    def __init__(
        self,
        coordinator: BabyBuddyCoordinator,
        child: dict,
    ) -> None:
        """Initialize the button."""
        super().__init__(coordinator)
        self.child = child
        self._attr_name = "Start timer"
        self._attr_unique_id = (
            f"{coordinator.config_entry.entry_id}"
            f"-{child[ATTR_ID]}-start-timer"
        )
        self._attr_icon = "mdi:timer-plus"
        self._attr_device_info = build_device_info(coordinator, child)

    async def async_press(self) -> None:
        """Start a new timer by calling the babybuddy.start_timer service."""
        await self.hass.services.async_call(
            DOMAIN,
            "start_timer",
            {"child": self.entity_id},
        )


class BabyBuddyTimerSensor(CoordinatorEntity, SensorEntity):
    """Sensor representing a single active Baby Buddy timer.

    State is the timer's start timestamp (device_class=TIMESTAMP) so the
    value is stable while the timer runs (no unnecessary recorder writes).
    Frontend cards derive elapsed time client-side.
    """

    _attr_has_entity_name = True
    _attr_device_class = SensorDeviceClass.TIMESTAMP
    coordinator: BabyBuddyCoordinator

    def __init__(
        self,
        coordinator: BabyBuddyCoordinator,
        child: dict,
        timer: dict,
    ) -> None:
        """Initialize the timer sensor."""
        super().__init__(coordinator)
        self.child = child
        self._timer_id: int = timer[ATTR_ID]
        timer_name = timer.get("name") or f"Timer {self._timer_id}"
        self._attr_name = timer_name
        self._attr_unique_id = (
            f"{coordinator.config_entry.entry_id}"
            f"-{child[ATTR_ID]}-timer-{self._timer_id}"
        )
        self._attr_icon = "mdi:timer-sand"
        self._attr_device_info = build_device_info(coordinator, child)

    @property
    def _timer_data(self) -> dict[str, Any] | None:
        """Find this timer in the coordinator's timer list."""
        if not self.coordinator.data:
            return None
        child_entry = self.coordinator.data.child_data.get(self.child[ATTR_ID], {})
        for t in child_entry.get(ACTIVE_TIMERS_KEY, []):
            if t.get(ATTR_ID) == self._timer_id:
                return t
        return None

    @property
    def available(self) -> bool:
        """Timer is available only while it exists in BB."""
        return self._timer_data is not None

    @property
    def native_value(self) -> StateType:
        """Return the timer start timestamp."""
        timer = self._timer_data
        if not timer:
            return None
        start = timer.get("start")
        if start is None:
            return None
        return dt_util.parse_datetime(start)

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Expose timer metadata as attributes."""
        timer = self._timer_data
        if not timer:
            return {}
        return {
            "timer_id": timer.get(ATTR_ID),
            "timer_name": timer.get("name"),
            "child": timer.get("child"),
            "duration": timer.get("duration"),
        }


class BabyBuddySelect(CoordinatorEntity, SelectEntity, RestoreEntity):
    """Babybuddy select entity for feeding and diaper change."""

    _attr_should_poll = False
    coordinator: BabyBuddyCoordinator
    entity_description: BabyBuddySelectDescription

    def __init__(
        self,
        coordinator: BabyBuddyCoordinator,
        entity_description: BabyBuddySelectDescription,
    ) -> None:
        """Initialize the Babybuddy select entity."""
        super().__init__(coordinator)
        self._attr_unique_id = (
            f"{self.coordinator.config_entry.entry_id}-{entity_description.key}"
        )
        self._attr_options = entity_description.options
        self.entity_description = entity_description
        self._attr_current_option = None

    async def async_added_to_hass(self) -> None:
        """Restore last state when added."""
        last_state = await self.async_get_last_state()
        if last_state:
            self._attr_current_option = last_state.state

    async def async_select_option(self, option: str) -> None:
        """Update the current selected option."""
        if option not in self.options:
            raise ServiceValidationError(
                translation_domain=DOMAIN,
                translation_key="invalid_select_option",
                translation_placeholders={
                    "entity_id": self.entity_id,
                    "option": option,
                },
            )

        self._attr_current_option = option
        self.async_write_ha_state()
