"""The Alfabetul pe fire integration.

Transmits a text message on 5 lamps (ESP32 LEDs, relays…) using the 5-wire
alphabet from the bible-ai-preado lessons, one symbol every few seconds, like
the "Redare automată" panel of the browser app.
"""

from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant

from .controller import AlfabetController

PLATFORMS = [Platform.TEXT, Platform.NUMBER, Platform.BUTTON, Platform.SENSOR]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    entry.runtime_data = AlfabetController(hass, entry)
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    entry.runtime_data.async_unload()
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
