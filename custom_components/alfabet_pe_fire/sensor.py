"""Playback progress: ``7 / 42 · L``, with the code in the attributes."""

from __future__ import annotations

from typing import Any

from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import STATE_DONE, STATE_ERROR, STATE_PLAYING, STATE_STOPPED
from .entity import AlfabetEntity

STATE_TEXT = {
    STATE_DONE: "gata",
    STATE_STOPPED: "oprit",
    STATE_ERROR: "eroare (vezi log-ul)",
}


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    async_add_entities([ProgressSensor(entry.runtime_data, "progres", "Progres")])


class ProgressSensor(AlfabetEntity, SensorEntity):
    _attr_icon = "mdi:progress-clock"

    async def async_added_to_hass(self) -> None:
        await super().async_added_to_hass()
        self.async_on_remove(self.controller.add_listener(self.async_write_ha_state))

    @property
    def native_value(self) -> str:
        p = self.controller.progress
        if p.state == STATE_PLAYING and p.symbol:
            return f"{p.index} / {p.total} · {p.symbol.label}"
        return STATE_TEXT.get(p.state, "—")

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        p = self.controller.progress
        return {
            "state": p.state,
            "index": p.index,
            "total": p.total,
            "symbol": p.symbol.char if p.symbol else None,
            "code": p.symbol.code if p.symbol else None,  # 21, or ".-" in Morse
            "binary": getattr(p.symbol, "binary", None),  # 5-wire alphabet only
        }
