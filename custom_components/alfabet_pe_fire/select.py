"""Message type (colored letters / Morse) and the lamp Morse is sent on."""

from __future__ import annotations

from homeassistant.components.select import SelectEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.restore_state import RestoreEntity

from .const import MODES, MORSE_COLORS
from .entity import AlfabetEntity


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    controller = entry.runtime_data
    async_add_entities(
        [
            ModeSelect(controller, "tip_mesaj", "Tip mesaj"),
            MorseColorSelect(controller, "culoare_morse", "Culoare Morse"),
        ]
    )


class ModeSelect(AlfabetEntity, SelectEntity, RestoreEntity):
    _attr_icon = "mdi:format-list-bulleted-type"
    _attr_options = list(MODES)

    async def async_added_to_hass(self) -> None:
        await super().async_added_to_hass()
        last = await self.async_get_last_state()
        if last and last.state in MODES:
            self.controller.set_mode(last.state)

    @property
    def current_option(self) -> str:
        return self.controller.mode

    async def async_select_option(self, option: str) -> None:
        self.controller.set_mode(option)
        self.async_write_ha_state()


class MorseColorSelect(AlfabetEntity, SelectEntity, RestoreEntity):
    _attr_icon = "mdi:lightbulb-on"
    _attr_options = list(MORSE_COLORS)

    async def async_added_to_hass(self) -> None:
        await super().async_added_to_hass()
        last = await self.async_get_last_state()
        if last and last.state in MORSE_COLORS:
            self.controller.morse_color = last.state

    @property
    def current_option(self) -> str:
        return self.controller.morse_color

    async def async_select_option(self, option: str) -> None:
        self.controller.morse_color = option
        self.async_write_ha_state()
