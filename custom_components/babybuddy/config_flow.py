"""Config flow for babybuddy integration."""

from __future__ import annotations

from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.config_entries import ConfigFlowResult, OptionsFlowWithReload
from homeassistant.const import (
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
from homeassistant.core import callback
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .client import BabyBuddyClient
from .const import (
    CONF_FEEDING_UNIT,
    CONF_MQTT_ENABLED,
    CONF_MQTT_TOPIC_PREFIX,
    CONF_WEIGHT_UNIT,
    CONFIG_FLOW_MINOR_VERSION,
    CONFIG_FLOW_VERSION,
    DEFAULT_MQTT_TOPIC_PREFIX,
    DEFAULT_NAME,
    DEFAULT_PATH,
    DEFAULT_PORT,
    DEFAULT_SCAN_INTERVAL,
    DOMAIN,
)
from .errors import AuthorizationError, ConnectError

DATA_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_HOST): str,
        vol.Required(CONF_PORT, default=DEFAULT_PORT): cv.port,
        vol.Optional(CONF_PATH, default=DEFAULT_PATH): str,
        vol.Required(CONF_API_KEY): str,
    }
)


class BabyBuddyFlowHandler(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle babybuddy config flow."""

    VERSION = CONFIG_FLOW_VERSION
    MINOR_VERSION = CONFIG_FLOW_MINOR_VERSION

    @staticmethod
    @callback
    def async_get_options_flow(
        entry: config_entries.ConfigEntry,
    ) -> BabyBuddyOptionsFlowHandler:
        """Get the options flow for this handler."""
        return BabyBuddyOptionsFlowHandler()

    def __init__(self) -> None:
        """Initiate config flow."""
        self._reauth_unique_id = None

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle a flow initialized by the user."""
        errors: dict[str, str] = {}

        if user_input is not None:
            await self.async_set_unique_id(
                f"{user_input[CONF_HOST]}-{user_input[CONF_API_KEY]}"
            )
            self._abort_if_unique_id_configured()

            try:
                client: BabyBuddyClient = BabyBuddyClient(
                    user_input[CONF_HOST],
                    user_input[CONF_PORT],
                    user_input[CONF_PATH],
                    user_input[CONF_API_KEY],
                    async_get_clientsession(self.hass),
                )
                await client.async_connect()
            except AuthorizationError:
                errors["api_key"] = "invalid_auth"
            except ConnectError:
                errors["base"] = "cannot_connect"

            if not errors:
                return self.async_create_entry(
                    title=f"{DEFAULT_NAME} ({user_input[CONF_HOST]})", data=user_input
                )

        return self.async_show_form(
            step_id="user",
            data_schema=DATA_SCHEMA,
            errors=errors,
        )

    async def async_step_reconfigure(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle reconfiguration of connection settings."""
        errors: dict[str, str] = {}
        entry = self.hass.config_entries.async_get_entry(self.context["entry_id"])
        assert entry is not None

        if user_input is not None:
            try:
                client = BabyBuddyClient(
                    user_input[CONF_HOST],
                    user_input[CONF_PORT],
                    user_input.get(CONF_PATH, DEFAULT_PATH),
                    user_input[CONF_API_KEY],
                    async_get_clientsession(self.hass),
                )
                await client.async_connect()
            except AuthorizationError:
                errors["api_key"] = "invalid_auth"
            except ConnectError:
                errors["base"] = "cannot_connect"

            if not errors:
                new_data = {**entry.data, **user_input}
                new_data.setdefault(CONF_PATH, DEFAULT_PATH)
                return self.async_update_reload_and_abort(
                    entry,
                    unique_id=f"{user_input[CONF_HOST]}-{user_input[CONF_API_KEY]}",
                    data=new_data,
                    title=f"{DEFAULT_NAME} ({user_input[CONF_HOST]})",
                )

        reconfigure_schema = vol.Schema(
            {
                vol.Required(CONF_HOST, default=entry.data.get(CONF_HOST, "")): str,
                vol.Required(
                    CONF_PORT, default=entry.data.get(CONF_PORT, DEFAULT_PORT)
                ): cv.port,
                vol.Optional(
                    CONF_PATH, default=entry.data.get(CONF_PATH, DEFAULT_PATH)
                ): str,
                vol.Required(
                    CONF_API_KEY, default=entry.data.get(CONF_API_KEY, "")
                ): str,
            }
        )

        return self.async_show_form(
            step_id="reconfigure",
            data_schema=reconfigure_schema,
            errors=errors,
        )

    async def async_step_reauth(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Perform reauth upon an API authentication error."""
        self._reauth_unique_id = self.context["unique_id"]
        return await self.async_step_reauth_confirm()

    async def async_step_reauth_confirm(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Dialog that informs the user that reauth is required."""
        errors: dict[str, str] = {}

        existing_entry = await self.async_set_unique_id(self._reauth_unique_id)
        if user_input is not None and existing_entry is not None:
            user_input[CONF_HOST] = existing_entry.data[CONF_HOST]
            user_input[CONF_PORT] = existing_entry.data[CONF_PORT]
            user_input[CONF_PATH] = existing_entry.data[CONF_PATH]
            try:
                client: BabyBuddyClient = BabyBuddyClient(
                    user_input[CONF_HOST],
                    user_input[CONF_PORT],
                    user_input[CONF_PATH],
                    user_input[CONF_API_KEY],
                    async_get_clientsession(self.hass),
                )
                await client.async_connect()
            except ConnectError:
                errors["base"] = "cannot_connect"

            if not errors:
                self.hass.config_entries.async_update_entry(
                    existing_entry,
                    data={**existing_entry.data, **user_input},
                )
                await self.hass.config_entries.async_reload(existing_entry.entry_id)
                return self.async_abort(reason="reauth_successful")

        return self.async_show_form(
            step_id="reauth_confirm",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_API_KEY): str,
                }
            ),
            errors=errors,
        )


class BabyBuddyOptionsFlowHandler(OptionsFlowWithReload):
    """Handle babybuddy options.

    Extends OptionsFlowWithReload so the config entry is automatically
    reloaded when options change (no manual update listener needed).
    """

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Manage babybuddy options."""
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        options_schema = vol.Schema(
            {
                vol.Optional(TEMPERATURE): vol.In(
                    [UnitOfTemperature.CELSIUS, UnitOfTemperature.FAHRENHEIT]
                ),
                vol.Optional(CONF_WEIGHT_UNIT): vol.In(
                    [
                        UnitOfMass.KILOGRAMS,
                        UnitOfMass.GRAMS,
                        UnitOfMass.POUNDS,
                        UnitOfMass.OUNCES,
                    ]
                ),
                vol.Optional(CONF_FEEDING_UNIT): vol.In(
                    [UnitOfVolume.MILLILITERS, UnitOfVolume.FLUID_OUNCES]
                ),
                vol.Optional(
                    CONF_SCAN_INTERVAL, default=DEFAULT_SCAN_INTERVAL
                ): cv.positive_int,
                vol.Optional(
                    CONF_MQTT_ENABLED, default=False
                ): cv.boolean,
                vol.Optional(
                    CONF_MQTT_TOPIC_PREFIX, default=DEFAULT_MQTT_TOPIC_PREFIX
                ): cv.string,
            }
        )

        return self.async_show_form(
            step_id="init",
            data_schema=self.add_suggested_values_to_schema(
                options_schema, self.config_entry.options
            ),
        )
