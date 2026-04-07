"""JavaScript module registration for the Baby Buddy card."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

from homeassistant.components.http import StaticPathConfig
from homeassistant.core import HomeAssistant
from homeassistant.helpers.event import async_call_later

_LOGGER = logging.getLogger(__name__)

URL_BASE = "/babybuddy-card"
JS_FILENAME = "babybuddy-card.js"


class JSModuleRegistration:
    """Registers the Baby Buddy card JS module with Home Assistant."""

    def __init__(self, hass: HomeAssistant, version: str) -> None:
        self.hass = hass
        self.version = version
        self.lovelace = hass.data.get("lovelace")

    async def async_register(self) -> None:
        """Register static path and Lovelace resource."""
        await self._async_register_path()
        if self.lovelace is None:
            _LOGGER.debug("Lovelace not available, skipping resource registration")
            return
        mode = getattr(
            self.lovelace,
            "mode",
            getattr(self.lovelace, "resource_mode", "yaml"),
        )
        if mode == "storage":
            await self._async_wait_for_lovelace_resources()

    async def _async_register_path(self) -> None:
        frontend_dir = str(Path(__file__).parent)
        try:
            await self.hass.http.async_register_static_paths(
                [StaticPathConfig(URL_BASE, frontend_dir, False)]
            )
            _LOGGER.debug("Registered static path: %s -> %s", URL_BASE, frontend_dir)
        except RuntimeError:
            _LOGGER.debug("Static path already registered: %s", URL_BASE)

    async def _async_wait_for_lovelace_resources(self) -> None:
        async def _check_loaded(_now: Any) -> None:
            if self.lovelace.resources.loaded:
                await self._async_register_module()
                return

            # Force-load the resource collection if the method is available.
            # This works around the lazy-load issue where resources stay
            # unloaded until the frontend is opened (core issue #165767).
            if hasattr(self.lovelace.resources, "async_load"):
                _LOGGER.debug("Force-loading Lovelace resource collection")
                try:
                    await self.lovelace.resources.async_load()
                    await self._async_register_module()
                    return
                except Exception:
                    _LOGGER.debug("Could not force-load resources, retrying in 5s")

            _LOGGER.debug("Lovelace resources not loaded yet, retrying in 5s")
            async_call_later(self.hass, 5, _check_loaded)

        await _check_loaded(0)

    async def _async_register_module(self) -> None:
        url = f"{URL_BASE}/{JS_FILENAME}"
        versioned_url = f"{url}?v={self.version}"

        existing = [
            r
            for r in self.lovelace.resources.async_items()
            if r["url"].split("?")[0] == url
        ]

        if existing:
            resource = existing[0]
            if self._get_version(resource["url"]) != self.version:
                _LOGGER.info("Updating Baby Buddy card to v%s", self.version)
                await self.lovelace.resources.async_update_item(
                    resource["id"],
                    {"res_type": "module", "url": versioned_url},
                )
        else:
            _LOGGER.info("Registering Baby Buddy card v%s", self.version)
            await self.lovelace.resources.async_create_item(
                {"res_type": "module", "url": versioned_url}
            )

    @staticmethod
    def _get_version(url: str) -> str:
        parts = url.split("?")
        if len(parts) > 1 and parts[1].startswith("v="):
            return parts[1].removeprefix("v=")
        return "0"

    async def async_unregister(self) -> None:
        """Remove Lovelace resources registered by this integration."""
        if self.lovelace is None:
            return
        mode = getattr(
            self.lovelace,
            "mode",
            getattr(self.lovelace, "resource_mode", "yaml"),
        )
        if mode != "storage":
            return
        url = f"{URL_BASE}/{JS_FILENAME}"
        for resource in self.lovelace.resources.async_items():
            if resource["url"].split("?")[0] == url:
                await self.lovelace.resources.async_delete_item(resource["id"])
