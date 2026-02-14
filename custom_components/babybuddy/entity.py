"""Platform for babybuddy sensor integration."""

from __future__ import annotations

from typing import Any

from homeassistant.components.select import SelectEntity
from homeassistant.components.sensor import SensorEntity
from homeassistant.components.sensor.const import SensorDeviceClass, SensorStateClass
from homeassistant.components.switch import SwitchEntity
from homeassistant.const import ATTR_ID, CONF_API_KEY, CONF_HOST, CONF_PATH, CONF_PORT
from homeassistant.helpers.restore_state import RestoreEntity
from homeassistant.helpers.typing import StateType
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.util import dt as dt_util

from .client import get_datetime_from_time
from .const import (
    ATTR_BABYBUDDY_CHILD,
    ATTR_BIRTH_DATE,
    ATTR_CHANGES,
    ATTR_CHILD,
    ATTR_DESCRIPTIVE,
    ATTR_FIRST_NAME,
    ATTR_ICON_CHILD_SENSOR,
    ATTR_ICON_TIMER_SAND,
    ATTR_LAST_NAME,
    ATTR_PICTURE,
    ATTR_SLUG,
    ATTR_SOLID,
    ATTR_START,
    ATTR_TIMER,
    ATTR_TIMERS,
    ATTR_WET,
    DIAPER_TYPES,
    DOMAIN,
    BabyBuddyEntityDescription,
    BabyBuddySelectDescription,
)
from .coordinator import BabyBuddyCoordinator


class BabyBuddySensor(CoordinatorEntity, SensorEntity):
    """Base class for babybuddy sensors."""

    _attr_has_entity_name = True
    coordinator: BabyBuddyCoordinator

    def __init__(self, coordinator: BabyBuddyCoordinator, child: dict) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self.child = child
        self._attr_device_info = {
            "configuration_url": f"{coordinator.config_entry.data[CONF_HOST]}:{coordinator.config_entry.data[CONF_PORT]}{coordinator.config_entry.data[CONF_PATH]}/children/{child[ATTR_SLUG]}/dashboard/",
            "identifiers": {(DOMAIN, child[ATTR_ID])},
            "name": f"{child[ATTR_FIRST_NAME]} {child[ATTR_LAST_NAME]}",
        }


class BabyBuddyChildSensor(BabyBuddySensor):
    """Representation of a babybuddy child sensor."""

    def __init__(self, coordinator: BabyBuddyCoordinator, child: dict) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator, child)

        self._attr_name = None  # Primary device entity: uses device name
        self._attr_unique_id = (
            f"{coordinator.config_entry.data[CONF_API_KEY]}-{child[ATTR_ID]}"
        )
        self._attr_native_value = child[ATTR_BIRTH_DATE]
        self._attr_icon = ATTR_ICON_CHILD_SENSOR
        self._attr_device_class = ATTR_BABYBUDDY_CHILD

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return entity specific state attributes for babybuddy."""
        return self.child

    @property
    def entity_picture(self) -> str | None:
        """Return babybuddy picture."""
        image: str | None = self.child[ATTR_PICTURE]
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
        self._attr_unique_id = f"{self.coordinator.config_entry.data[CONF_API_KEY]}-{child[ATTR_ID]}-{description.key}"

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
        if self.child[ATTR_ID] not in self.coordinator.data[1]:
            return None
        data: dict[str, str] = self.coordinator.data[1][self.child[ATTR_ID]][
            self.entity_description.key
        ]
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
        if self.child[ATTR_ID] in self.coordinator.data[1]:
            attrs = self.coordinator.data[1][self.child[ATTR_ID]][
                self.entity_description.key
            ]
            if self.entity_description.key == ATTR_CHANGES:
                wet_and_solid: tuple[bool, bool] = (
                    self.coordinator.data[1][self.child[ATTR_ID]][
                        self.entity_description.key
                    ].get(ATTR_WET, False),
                    self.coordinator.data[1][self.child[ATTR_ID]][
                        self.entity_description.key
                    ].get(ATTR_SOLID, False),
                )
                if wet_and_solid == (True, False):
                    attrs[ATTR_DESCRIPTIVE] = DIAPER_TYPES[0]
                if wet_and_solid == (False, True):
                    attrs[ATTR_DESCRIPTIVE] = DIAPER_TYPES[1]
                if wet_and_solid == (True, True):
                    attrs[ATTR_DESCRIPTIVE] = DIAPER_TYPES[2]

        return attrs

    @property
    def native_unit_of_measurement(self) -> str | None:
        """Return entity unit of measurement."""
        return self.coordinator.config_entry.options.get(
            self.entity_description.key,
            self.entity_description.native_unit_of_measurement,
        )


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
            f"{coordinator.config_entry.data[CONF_API_KEY]}"
            f"-{child[ATTR_ID]}-stats-{stats_meta['key']}"
        )
        self._attr_icon = stats_meta.get("icon")
        if stats_meta.get("unit_of_measurement"):
            self._attr_native_unit_of_measurement = stats_meta["unit_of_measurement"]

        # Map string state_class to HA enum
        _sc_map = {
            "measurement": SensorStateClass.MEASUREMENT,
            "total": SensorStateClass.TOTAL,
            "total_increasing": SensorStateClass.TOTAL_INCREASING,
        }
        sc = stats_meta.get("state_class")
        if sc and sc in _sc_map:
            self._attr_state_class = _sc_map[sc]

    @property
    def name(self) -> str:
        """Return the name of the sensor."""
        return self._stats_meta["name"]

    @property
    def _stats(self) -> dict[str, Any]:
        """Return the stats dict for this child, or empty dict."""
        if not self.coordinator.data:
            return {}
        child_data = self.coordinator.data[1].get(self.child[ATTR_ID], {})
        return child_data.get("stats", {})

    @property
    def native_value(self) -> StateType:
        """Return the stats field value."""
        field = self._stats_meta.get("stats_field", self._stats_meta["key"])
        return self._stats.get(field)

    @property
    def available(self) -> bool:
        """Return True if coordinator data is available."""
        return bool(self.coordinator.data)


class BabyBuddyChildTimerSwitch(CoordinatorEntity, SwitchEntity):
    """Representation of a babybuddy timer switch."""

    _attr_has_entity_name = True
    coordinator: BabyBuddyCoordinator

    def __init__(
        self,
        coordinator: BabyBuddyCoordinator,
        child: dict,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self.child = child
        self._attr_name = "Timer"
        self._attr_unique_id = (
            f"{self.coordinator.config_entry.data[CONF_API_KEY]}-{child[ATTR_ID]}-{ATTR_TIMER}"
        )
        self._attr_icon = ATTR_ICON_TIMER_SAND
        self._attr_device_info = {
            "identifiers": {(DOMAIN, child[ATTR_ID])},
            "name": f"{child[ATTR_FIRST_NAME]} {child[ATTR_LAST_NAME]}",
        }

    @property
    def _timer_data(self) -> dict[str, Any]:
        """Return the current timer data dict, or empty dict if unavailable."""
        child_data = self.coordinator.data[1].get(self.child[ATTR_ID], {})
        timer_data = child_data.get(ATTR_TIMERS)
        return timer_data if isinstance(timer_data, dict) else {}

    @property
    def is_on(self) -> bool:
        """Return entity state."""
        timer_data = self._timer_data
        if not timer_data:
            return False
        # In Babybuddy 2.0 'active' is not in the JSON response, so return
        # True if any timers are returned, as only active timers are
        # returned.
        return timer_data.get("active", True)

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return entity specific state attributes for babybuddy."""
        if self.is_on:
            return self._timer_data
        return {}

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Start a new timer."""
        data = {
            ATTR_CHILD: self.child[ATTR_ID],
            ATTR_START: get_datetime_from_time(dt_util.now()),
        }
        await self.coordinator.client.async_post(ATTR_TIMERS, data)
        await self.coordinator.async_request_refresh()

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Delete active timer."""
        timer_data = self._timer_data
        timer_id = timer_data.get(ATTR_ID)
        if timer_id is None:
            return
        await self.coordinator.client.async_delete(ATTR_TIMERS, timer_id)
        await self.coordinator.async_request_refresh()


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
            f"{self.coordinator.config_entry.data[CONF_API_KEY]}-{entity_description.key}"
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
            raise ValueError(f"Invalid option for {self.entity_id}: {option}")

        self._attr_current_option = option
        self.async_write_ha_state()
