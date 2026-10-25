"""The message to transmit."""

from __future__ import annotations

from homeassistant.components.text import TextEntity, TextMode
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import STATE_UNAVAILABLE, STATE_UNKNOWN
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.restore_state import RestoreEntity

from .const import MAX_MESSAGE
from .entity import AlfabetEntity


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    async_add_entities([MessageText(entry.runtime_data, "mesaj", "Mesaj")])


class MessageText(AlfabetEntity, TextEntity, RestoreEntity):
    _attr_icon = "mdi:message-text"
    _attr_mode = TextMode.TEXT
    _attr_native_min = 0
    _attr_native_max = MAX_MESSAGE

    async def async_added_to_hass(self) -> None:
        await super().async_added_to_hass()
        last = await self.async_get_last_state()
        if last and last.state not in (STATE_UNKNOWN, STATE_UNAVAILABLE):
            self.controller.message = last.state

    @property
    def native_value(self) -> str:
        return self.controller.message

    async def async_set_value(self, value: str) -> None:
        self.controller.message = value
        self.async_write_ha_state()
