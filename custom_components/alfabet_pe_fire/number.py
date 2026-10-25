"""Seconds per symbol (the dark gap included)."""

from __future__ import annotations

from homeassistant.components.number import NumberMode, RestoreNumber
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import UnitOfTime
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import INTERVAL_STEP, MAX_INTERVAL, MIN_INTERVAL
from .entity import AlfabetEntity


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    async_add_entities([IntervalNumber(entry.runtime_data, "interval", "Interval")])


class IntervalNumber(AlfabetEntity, RestoreNumber):
    _attr_icon = "mdi:timer-outline"
    _attr_mode = NumberMode.BOX
    _attr_native_min_value = MIN_INTERVAL
    _attr_native_max_value = MAX_INTERVAL
    _attr_native_step = INTERVAL_STEP
    _attr_native_unit_of_measurement = UnitOfTime.SECONDS

    async def async_added_to_hass(self) -> None:
        await super().async_added_to_hass()
        last = await self.async_get_last_number_data()
        if last and last.native_value is not None:
            self.controller.interval = last.native_value

    @property
    def native_value(self) -> float:
        return self.controller.interval

    async def async_set_native_value(self, value: float) -> None:
        self.controller.interval = value
        self.async_write_ha_state()
