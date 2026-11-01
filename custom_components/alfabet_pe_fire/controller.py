"""Per-entry state shared by the entities, and the playback task."""

from __future__ import annotations

import asyncio
import logging
from collections.abc import Callable

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import ATTR_ENTITY_ID
from homeassistant.core import CALLBACK_TYPE, HomeAssistant, callback

from . import morse
from .const import (
    CONF_BUZZER,
    CONF_LIGHTS,
    CONF_RTTTL_PLAY,
    CONF_RTTTL_STOP,
    DEFAULT_BUZZER,
    DEFAULT_GAP_MS,
    DEFAULT_INTERVALS,
    DEFAULT_MORSE_COLOR,
    DEFAULT_REPEAT,
    DEFAULT_RTTTL_PLAY,
    DEFAULT_RTTTL_STOP,
    MODE_COLORS,
    MODE_MORSE,
    MORSE_COLORS,
    MORSE_TONE,
    SOUND_BUZZER,
    SOUND_NONE,
    SOUND_RTTTL,
    STATE_ERROR,
    STATE_DONE,
    STATE_STOPPED,
    STATE_WAITING,
)
from .encoding import OFF, encode
from .player import Progress, play, play_morse

_LOGGER = logging.getLogger(__name__)


class AlfabetController:
    """Holds the message, the settings and the progress; starts and stops playback."""

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        self.hass = hass
        self.entry = entry
        self.message = ""
        self.mode = MODE_COLORS
        self.intervals = dict(DEFAULT_INTERVALS)  # ms, per mode
        self.morse_color = DEFAULT_MORSE_COLOR
        self.repeat = DEFAULT_REPEAT  # ms, 0 = play once
        self.gap = DEFAULT_GAP_MS  # ms dark between colored letters
        self.sound = SOUND_NONE  # how Morse sounds while its lamp is lit
        self._warned: set[str] = set()  # missing RTTTL actions already logged
        self.progress = Progress()
        self._task: asyncio.Task | None = None
        self._listeners: set[Callable[[], None]] = set()

    @property
    def _settings(self) -> dict:
        """The config entry data; the options override it."""
        return {**self.entry.data, **self.entry.options}

    @property
    def lights(self) -> list[str]:
        """The 5 lamp entities, wire 1 first."""
        return list(self._settings[CONF_LIGHTS])

    @property
    def buzzer(self) -> str:
        return self._settings.get(CONF_BUZZER) or DEFAULT_BUZZER

    @property
    def rtttl_play(self) -> str:
        return self._settings.get(CONF_RTTTL_PLAY) or DEFAULT_RTTTL_PLAY

    @property
    def rtttl_stop(self) -> str:
        return self._settings.get(CONF_RTTTL_STOP) or DEFAULT_RTTTL_STOP

    @property
    def interval(self) -> int:
        """Interval of the current mode, in ms."""
        return self.intervals[self.mode]

    @interval.setter
    def interval(self, value: int) -> None:
        self.intervals[self.mode] = value

    @callback
    def add_listener(self, listener: Callable[[], None]) -> CALLBACK_TYPE:
        """Get called whenever the progress or the mode changes."""
        self._listeners.add(listener)
        return lambda: self._listeners.discard(listener)

    @callback
    def _notify(self) -> None:
        for listener in list(self._listeners):
            listener()

    @callback
    def set_mode(self, mode: str) -> None:
        """Switch the message type; the Interval entity then shows that mode's value."""
        self.mode = mode
        self._notify()

    @callback
    def _set_progress(self, progress: Progress) -> None:
        self.progress = progress
        self._notify()

    async def _set_lights(self, bits: tuple[bool, ...]) -> None:
        lights = self.lights
        off = [e for e, on in zip(lights, bits) if not on]
        on = [e for e, on in zip(lights, bits) if on]
        # on first, then off: going from code to code without a dark gap, the
        # lamps hand over instead of all blinking dark between the two calls
        if on:
            await self.hass.services.async_call(
                "homeassistant", "turn_on", {ATTR_ENTITY_ID: on}, blocking=True
            )
        if off:
            await self.hass.services.async_call(
                "homeassistant", "turn_off", {ATTR_ENTITY_ID: off}, blocking=True
            )

    async def _set_sound(self, on: bool, sound: str | None = None) -> None:
        """Start or stop the Morse sound (``sound``, the selected one by default)."""
        sound = sound or self.sound
        if sound == SOUND_BUZZER:
            await self.hass.services.async_call(
                "homeassistant",
                "turn_on" if on else "turn_off",
                {ATTR_ENTITY_ID: self.buzzer},
                blocking=True,
            )
        elif sound == SOUND_RTTTL and self._has_rtttl():
            domain, service = (self.rtttl_play if on else self.rtttl_stop).split(".", 1)
            data = {"song_str": MORSE_TONE} if on else {}
            await self.hass.services.async_call(domain, service, data, blocking=True)

    def _has_rtttl(self) -> bool:
        """Both RTTTL actions exist: a tone that cannot be stopped would ring 8 s.

        Without them (e.g. firmware not reinstalled with ``stop_rtttl``) Morse
        plays silently instead of failing, with one warning per missing action.
        """
        missing = [
            a for a in (self.rtttl_play, self.rtttl_stop)
            if not self.hass.services.has_service(*a.split(".", 1))
        ]
        for action in missing:
            if action not in self._warned:
                self._warned.add(action)
                _LOGGER.warning(
                    "Sunet Morse RTTTL is off: action %s not found (add it to the "
                    "ESPHome config and reinstall, or change it in the options)",
                    action,
                )
        return not missing

    async def _set_morse(self, bits: tuple[bool, ...]) -> None:
        # the lamp and the sound together, so the sound lasts exactly as the lamp
        await asyncio.gather(self._set_lights(bits), self._set_sound(any(bits)))

    async def async_set_sound(self, sound: str) -> None:
        """Change the Morse sound; silence the old one, it may be in the middle of a dash."""
        old, self.sound = self.sound, sound
        if old != sound and self._task and not self._task.done():
            await self._set_sound(False, old)

    async def _play_once(self) -> None:
        if self.mode == MODE_MORSE:
            await play_morse(
                morse.encode(self.message),
                self.interval / 1000,
                MORSE_COLORS.index(self.morse_color),
                self._set_morse,
                self._set_progress,
                clock=self.hass.loop.time,
            )
        else:
            await play(
                encode(self.message),
                self.interval / 1000,
                self._set_lights,
                self._set_progress,
                gap=self.gap / 1000,
            )

    async def _run(self) -> None:
        """Play, then, while Repeat is > 0, pause that long and play again.

        Every repetition reads the settings again, so the message, the type,
        the interval and the pause can be changed while it repeats.
        """
        try:
            await self._play_once()
            while self.repeat > 0:
                p = self.progress
                self._set_progress(Progress(STATE_WAITING, p.index, p.total))
                await asyncio.sleep(self.repeat / 1000)
                if self.repeat <= 0:  # turned off during the pause
                    self._set_progress(Progress(STATE_DONE, p.index, p.total))
                    break
                await self._play_once()
        except asyncio.CancelledError:
            raise
        except Exception:  # noqa: BLE001 - a missing lamp must not leave it half-lit silently
            _LOGGER.exception("Playback of %r failed", self.message)
            self._set_progress(Progress(STATE_ERROR))
            await self._silence()

    async def _silence(self) -> None:
        """After a failure, try once to turn the lamps and the sound off.

        The link may be the one that failed (e.g. WiFi lost), so each part is
        tried on its own and errors are only logged.
        """
        parts = [self._set_lights(OFF)]
        if self.mode == MODE_MORSE:
            parts.append(self._set_sound(False))
        for result in await asyncio.gather(*parts, return_exceptions=True):
            if isinstance(result, Exception):
                _LOGGER.warning("Could not turn off after the failure: %s", result)

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
        """Stop and turn all lamps off, so the last code does not stay lit (nor sound)."""
        self._cancel()
        await self._set_lights(OFF)
        self._set_progress(
            Progress(STATE_STOPPED, self.progress.index, self.progress.total)
        )
        if self.mode == MODE_MORSE:
            await self._set_sound(False)

    @callback
    def async_unload(self) -> None:
        self._cancel()
        self._listeners.clear()
