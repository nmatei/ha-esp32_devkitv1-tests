"""Interval in ms, one value per message type.

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
    INTERVAL_STEP,
    MAX_INTERVAL,
    MIN_INTERVAL,
    MODE_COLORS,
    MODES,
)
from .entity import AlfabetEntity


def _attr(mode: str) -> str:
    """``Litere colorate`` -> ``interval_litere_colorate``."""
    return "interval_" + mode.lower().replace(" ", "_")


def _to_step(ms: float) -> int:
    """Round to the step (half up) and clamp to the limits."""
    ms = int(ms / INTERVAL_STEP + 0.5) * INTERVAL_STEP
    return min(max(ms, MIN_INTERVAL), MAX_INTERVAL)


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
