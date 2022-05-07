"""Config flow for Wyze Home Assistant Integration integration."""
from __future__ import annotations

import logging
from typing import Any, Dict

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.const import CONF_USERNAME, CONF_PASSWORD
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError
from wyzeapy.base_client import NetClient

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

STEP_USER_DATA_SCHEMA = vol.Schema({CONF_USERNAME: str, CONF_PASSWORD: str})


async def validate_input(hass: HomeAssistant, data: Dict[str, Any]) -> Dict[str, Any]:
    """Validate the user input allows us to connect.

    Data has the keys from STEP_USER_DATA_SCHEMA with values provided by the user.
    """

    base_client = NetClient()

    if not await hass.async_add_executor_job(
        base_client.can_login, data[CONF_USERNAME], data[CONF_PASSWORD]
    ):
        raise InvalidAuth

    # If you cannot connect:
    # throw CannotConnect
    # If the authentication is wrong:
    # InvalidAuth

    # Return info that you want to store in the config entry.
    return {"title": "Wyze Home Assistant Integration"}


class ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Wyze Home Assistant Integration."""

    VERSION = 1
    CONNECTION_CLASS = config_entries.CONN_CLASS_CLOUD_POLL

    async def async_step_user(
        self, user_input: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """Handle the initial step."""
        if user_input is None:
            return self.async_show_form(
                step_id="user", data_schema=STEP_USER_DATA_SCHEMA
            )

        errors = {}

        # noinspection PyBroadException
        try:
            info = await validate_input(self.hass, user_input)
        except CannotConnect:
            errors["base"] = "cannot_connect"
        except InvalidAuth:
            errors["base"] = "invalid_auth"
        except Exception:
            _LOGGER.exception("Unexpected exception")
            errors["base"] = "unknown"
        else:
            return self.async_create_entry(title=info["title"], data=user_input)

        return self.async_show_form(
            step_id="user", data_schema=STEP_USER_DATA_SCHEMA, errors=errors
        )

    async def async_step_import(self, import_config):
        """Import a config entry from configuration.yaml."""
        return await self.async_step_user(import_config)


class CannotConnect(HomeAssistantError):
    """Error to indicate we cannot connect."""


class InvalidAuth(HomeAssistantError):
    """Error to indicate there is invalid auth."""
