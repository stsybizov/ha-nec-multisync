"""Config and options flow for NEC MultiSync."""

from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol

from homeassistant.config_entries import (
    ConfigEntry,
    ConfigFlow,
    ConfigFlowResult,
    OptionsFlow,
)
from homeassistant.const import CONF_HOST, CONF_NAME, CONF_PORT
from homeassistant.core import callback
import homeassistant.helpers.config_validation as cv

from .api import NecApiError, NecMultisyncApi
from .const import (
    CONF_MONITOR_ID,
    CONF_SOURCES,
    DEFAULT_MONITOR_ID,
    DEFAULT_NAME,
    DEFAULT_PORT,
    DEFAULT_SCAN_INTERVAL,
    DOMAIN,
    INPUT_SOURCES,
)

_LOGGER = logging.getLogger(__name__)

USER_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_HOST): str,
        vol.Optional(CONF_NAME, default=DEFAULT_NAME): str,
        vol.Optional(CONF_MONITOR_ID, default=DEFAULT_MONITOR_ID): vol.All(
            int, vol.Range(min=1, max=100)
        ),
        vol.Optional(CONF_PORT, default=DEFAULT_PORT): cv.port,
    }
)


async def _validate(hass, data: dict[str, Any]) -> dict[str, str | None]:
    """Try to connect and read identity. Returns model/serial or raises."""
    api = NecMultisyncApi(
        host=data[CONF_HOST],
        monitor_id=data.get(CONF_MONITOR_ID, DEFAULT_MONITOR_ID),
        port=data.get(CONF_PORT, DEFAULT_PORT),
    )
    try:
        await hass.async_add_executor_job(api.connect)
        await hass.async_add_executor_job(api.read_device_info)
    finally:
        await hass.async_add_executor_job(api.disconnect)
    return {"model": api.model, "serial": api.serial}


class NecMultisyncConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle a config flow for NEC MultiSync."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        errors: dict[str, str] = {}
        if user_input is not None:
            try:
                info = await _validate(self.hass, user_input)
            except NecApiError:
                errors["base"] = "cannot_connect"
            except Exception:  # noqa: BLE001
                _LOGGER.exception("Unexpected error validating NEC display")
                errors["base"] = "unknown"
            else:
                unique_id = info["serial"] or user_input[CONF_HOST]
                await self.async_set_unique_id(unique_id)
                self._abort_if_unique_id_configured()
                title = user_input.get(CONF_NAME) or info["model"] or DEFAULT_NAME
                return self.async_create_entry(title=title, data=user_input)

        return self.async_show_form(
            step_id="user", data_schema=USER_SCHEMA, errors=errors
        )

    @staticmethod
    @callback
    def async_get_options_flow(config_entry: ConfigEntry) -> OptionsFlow:
        return NecMultisyncOptionsFlow()


class NecMultisyncOptionsFlow(OptionsFlow):
    """Options: poll interval and which inputs to expose as sources."""

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        options = self.config_entry.options
        schema = vol.Schema(
            {
                vol.Optional(
                    "scan_interval",
                    default=options.get("scan_interval", DEFAULT_SCAN_INTERVAL),
                ): vol.All(int, vol.Range(min=10, max=600)),
                vol.Optional(
                    CONF_SOURCES,
                    default=options.get(CONF_SOURCES, list(INPUT_SOURCES)),
                ): cv.multi_select(list(INPUT_SOURCES)),
            }
        )
        return self.async_show_form(step_id="init", data_schema=schema)
