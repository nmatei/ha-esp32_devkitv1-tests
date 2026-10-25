"""Start and Stop."""

from __future__ import annotations

from homeassistant.components.button import ButtonEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .entity import AlfabetEntity


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    controller = entry.runtime_data
    async_add_entities(
        [StartButton(controller, "start", "Start"), StopButton(controller, "stop", "Stop")]
    )


class StartButton(AlfabetEntity, ButtonEntity):
    _attr_icon = "mdi:play"

    async def async_press(self) -> None:
        self.controller.start()


class StopButton(AlfabetEntity, ButtonEntity):
    _attr_icon = "mdi:stop"

    async def async_press(self) -> None:
        await self.controller.async_stop()
