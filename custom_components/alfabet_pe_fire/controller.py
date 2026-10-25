"""Per-entry state shared by the entities, and the playback task."""

from __future__ import annotations

import asyncio
import logging
from collections.abc import Callable

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import ATTR_ENTITY_ID
from homeassistant.core import CALLBACK_TYPE, HomeAssistant, callback

from .const import CONF_LIGHTS, DEFAULT_INTERVAL, STATE_ERROR, STATE_STOPPED
from .encoding import OFF, encode
from .player import Progress, play

_LOGGER = logging.getLogger(__name__)


class AlfabetController:
    """Holds the message, the interval and the progress; starts and stops playback."""

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        self.hass = hass
        self.entry = entry
        self.message = ""
        self.interval = DEFAULT_INTERVAL
        self.progress = Progress()
        self._task: asyncio.Task | None = None
        self._listeners: set[Callable[[], None]] = set()

    @property
    def lights(self) -> list[str]:
        """The 5 lamp entities, wire 1 first (options override the initial data)."""
        return list({**self.entry.data, **self.entry.options}[CONF_LIGHTS])

    @callback
    def add_listener(self, listener: Callable[[], None]) -> CALLBACK_TYPE:
        """Get called whenever the progress changes."""
        self._listeners.add(listener)
        return lambda: self._listeners.discard(listener)

    @callback
    def _set_progress(self, progress: Progress) -> None:
        self.progress = progress
        for listener in list(self._listeners):
            listener()

    async def _set_lights(self, bits: tuple[bool, ...]) -> None:
        lights = self.lights
        off = [e for e, on in zip(lights, bits) if not on]
        on = [e for e, on in zip(lights, bits) if on]
        if off:
            await self.hass.services.async_call(
                "homeassistant", "turn_off", {ATTR_ENTITY_ID: off}, blocking=True
            )
        if on:
            await self.hass.services.async_call(
                "homeassistant", "turn_on", {ATTR_ENTITY_ID: on}, blocking=True
            )

    async def _run(self) -> None:
        symbols = encode(self.message)
        try:
            await play(symbols, self.interval, self._set_lights, self._set_progress)
        except asyncio.CancelledError:
            raise
        except Exception:  # noqa: BLE001 - a missing lamp must not leave it half-lit silently
            _LOGGER.exception("Playback of %r failed", self.message)
            self._set_progress(Progress(STATE_ERROR))

    def _cancel(self) -> None:
        if self._task and not self._task.done():
            self._task.cancel()
        self._task = None

    @callback
    def start(self) -> None:
        """Play the current message from the beginning (restarts a running one)."""
        self._cancel()
        self._task = self.entry.async_create_background_task(
            self.hass, self._run(), f"{self.entry.domain}_play_{self.entry.entry_id}"
        )

    async def async_stop(self) -> None:
        """Stop and turn all lamps off, so the last code does not stay lit."""
        self._cancel()
        await self._set_lights(OFF)
        self._set_progress(
            Progress(STATE_STOPPED, self.progress.index, self.progress.total)
        )

    @callback
    def async_unload(self) -> None:
        self._cancel()
        self._listeners.clear()
