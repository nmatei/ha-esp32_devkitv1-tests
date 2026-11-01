"""Pauză: on while all lamps are dark before a colored letter, to react to it (e.g. a sound)."""

from __future__ import annotations

from homeassistant.components.binary_sensor import BinarySensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import STATE_PLAYING
from .entity import AlfabetEntity


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    async_add_entities([PauseSensor(entry.runtime_data, "pauza", "Pauză")])


class PauseSensor(AlfabetEntity, BinarySensorEntity):
    _attr_icon = "mdi:timer-pause"

    async def async_added_to_hass(self) -> None:
        await super().async_added_to_hass()
        self.async_on_remove(self.controller.add_listener(self.async_write_ha_state))

    @property
    def is_on(self) -> bool:
        p = self.controller.progress
        return p.state == STATE_PLAYING and p.pause
