"""UI setup: a name and the 5 lamps, wire 1 (yellow) to wire 5 (white)."""

from __future__ import annotations

from collections.abc import Sequence
from typing import Any

import voluptuous as vol

from homeassistant.config_entries import ConfigFlow, ConfigFlowResult, OptionsFlow
from homeassistant.core import callback
from homeassistant.helpers import selector

from .const import (
    CONF_LIGHTS,
    CONF_NAME,
    DEFAULT_LIGHTS,
    DEFAULT_NAME,
    DOMAIN,
    WIRE_COUNT,
)

_LAMP = selector.EntitySelector(selector.EntitySelectorConfig(domain=["light", "switch"]))
WIRE_KEYS = tuple(f"fir_{i}" for i in range(1, WIRE_COUNT + 1))


def _wires_schema(lights: Sequence[str]) -> dict:
    return {vol.Required(key, default=e): _LAMP for key, e in zip(WIRE_KEYS, lights)}


def _lights_from(user_input: dict[str, Any]) -> list[str]:
    return [user_input[key] for key in WIRE_KEYS]


class AlfabetConfigFlow(ConfigFlow, domain=DOMAIN):
    VERSION = 1

    async def async_step_user(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        if user_input is not None:
            return self.async_create_entry(
                title=user_input[CONF_NAME], data={CONF_LIGHTS: _lights_from(user_input)}
            )
        schema = vol.Schema(
            {vol.Required(CONF_NAME, default=DEFAULT_NAME): str, **_wires_schema(DEFAULT_LIGHTS)}
        )
        return self.async_show_form(step_id="user", data_schema=schema)

    @staticmethod
    @callback
    def async_get_options_flow(config_entry) -> OptionsFlow:
        return AlfabetOptionsFlow()


class AlfabetOptionsFlow(OptionsFlow):
    """Change the lamps later (e.g. the church rows instead of the ESP32 LEDs)."""

    async def async_step_init(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        if user_input is not None:
            return self.async_create_entry(data={CONF_LIGHTS: _lights_from(user_input)})
        current = {**self.config_entry.data, **self.config_entry.options}[CONF_LIGHTS]
        return self.async_show_form(step_id="init", data_schema=vol.Schema(_wires_schema(current)))
