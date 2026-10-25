"""Interval in ms, one value per message type; the repeat pause; the letter gap.

Colored letters: the time per symbol (dark gap included). Morse: the length of
a dot. The entity shows the current mode's value and keeps both in its
attributes, which is also how both survive a restart.
"""

from __future__ import annotations

from typing import Any

from homeassistant.components.number import NumberMode, RestoreNumber
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import ATTR_UNIT_OF_MEASUREMENT, UnitOfTime
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import (
    GAP_STEP,
    MAX_GAP_MS,
    INTERVAL_STEP,
    MAX_INTERVAL,
    MAX_REPEAT,
    MIN_INTERVAL,
    MODE_COLORS,
    MODES,
    REPEAT_STEP,
)
from .entity import AlfabetEntity


def _attr(mode: str) -> str:
    """``Litere colorate`` -> ``interval_litere_colorate``."""
    return "interval_" + mode.lower().replace(" ", "_")


def _to_step(
    ms: float, step: int = INTERVAL_STEP, low: int = MIN_INTERVAL, high: int = MAX_INTERVAL
) -> int:
    """Round to the step (half up) and clamp to the limits."""
    ms = int(ms / step + 0.5) * step
    return min(max(ms, low), high)


def _repeat_step(ms: float) -> int:
    return _to_step(ms, REPEAT_STEP, 0, MAX_REPEAT)


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    controller = entry.runtime_data
    async_add_entities(
        [
            IntervalNumber(controller, "interval", "Interval"),
            RepeatNumber(controller, "repeta_dupa", "Repetă după"),
            GapNumber(controller, "pauza_intre_litere", "Pauză între litere"),
        ]
    )


class IntervalNumber(AlfabetEntity, RestoreNumber):
    _attr_icon = "mdi:timer-outline"
    _attr_mode = NumberMode.BOX
    _attr_native_min_value = MIN_INTERVAL
    _attr_native_max_value = MAX_INTERVAL
    _attr_native_step = INTERVAL_STEP
    _attr_native_unit_of_measurement = UnitOfTime.MILLISECONDS

    async def async_added_to_hass(self) -> None:
        await super().async_added_to_hass()
        last = await self.async_get_last_state()
        if last:
            restored = {
                mode: last.attributes[_attr(mode)]
                for mode in MODES
                if isinstance(last.attributes.get(_attr(mode)), (int, float))
            }
            if restored:
                for mode, ms in restored.items():
                    self.controller.intervals[mode] = _to_step(ms)
            elif last.attributes.get(ATTR_UNIT_OF_MEASUREMENT) == UnitOfTime.SECONDS:
                # 0.1.0 had one interval, in seconds, for colored letters only
                try:
                    self.controller.intervals[MODE_COLORS] = _to_step(float(last.state) * 1000)
                except ValueError:
                    pass
        # the shown value follows the message type
        self.async_on_remove(self.controller.add_listener(self.async_write_ha_state))

    @property
    def native_value(self) -> int:
        return self.controller.interval

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        return {_attr(mode): self.controller.intervals[mode] for mode in MODES}

    async def async_set_native_value(self, value: float) -> None:
        self.controller.interval = _to_step(value)
        self.async_write_ha_state()


class RepeatNumber(AlfabetEntity, RestoreNumber):
    """Pause in ms before the message starts again; 0 = play once."""

    _attr_icon = "mdi:repeat"
    _attr_mode = NumberMode.BOX
    _attr_native_min_value = 0
    _attr_native_max_value = MAX_REPEAT
    _attr_native_step = REPEAT_STEP
    _attr_native_unit_of_measurement = UnitOfTime.MILLISECONDS

    async def async_added_to_hass(self) -> None:
        await super().async_added_to_hass()
        last = await self.async_get_last_number_data()
        if last and last.native_value is not None:
            ms = last.native_value
            if last.native_unit_of_measurement == UnitOfTime.SECONDS:
                ms *= 1000  # 0.2.3 had it in seconds
            self.controller.repeat = _repeat_step(ms)

    @property
    def native_value(self) -> int:
        return self.controller.repeat

    async def async_set_native_value(self, value: float) -> None:
        self.controller.repeat = _repeat_step(value)
        self.async_write_ha_state()


class GapNumber(AlfabetEntity, RestoreNumber):
    """Colored letters: ms all lamps stay dark before each letter; 0 = none."""

    _attr_icon = "mdi:timer-pause-outline"
    _attr_mode = NumberMode.BOX
    _attr_native_min_value = 0
    _attr_native_max_value = MAX_GAP_MS
    _attr_native_step = GAP_STEP
    _attr_native_unit_of_measurement = UnitOfTime.MILLISECONDS

    async def async_added_to_hass(self) -> None:
        await super().async_added_to_hass()
        last = await self.async_get_last_number_data()
        if last and last.native_value is not None:
            self.controller.gap = _to_step(last.native_value, GAP_STEP, 0, MAX_GAP_MS)

    @property
    def native_value(self) -> int:
        return self.controller.gap

    async def async_set_native_value(self, value: float) -> None:
        self.controller.gap = _to_step(value, GAP_STEP, 0, MAX_GAP_MS)
        self.async_write_ha_state()
