"""Constants for the Alfabetul pe fire integration."""

from __future__ import annotations

from typing import Final

DOMAIN: Final = "alfabet_pe_fire"

# Config keys -----------------------------------------------------------------
CONF_NAME: Final = "name"
CONF_LIGHTS: Final = "lights"  # 5 entity ids, wire 1 (MSB) … wire 5 (LSB)
CONF_BUZZER: Final = "buzzer"  # switch that beeps while on (active buzzer)
CONF_RTTTL_PLAY: Final = "rtttl_play"  # action "domain.service", takes song_str
CONF_RTTTL_STOP: Final = "rtttl_stop"

# Wires -----------------------------------------------------------------------
# Same order and colors as the physical board and the printed code sheet.
WIRE_COUNT: Final = 5
WIRE_NAMES: Final = ("galben", "rosu", "albastru", "verde", "alb")

# Defaults --------------------------------------------------------------------
DEFAULT_NAME: Final = "ESP32 devkitv1"
DEFAULT_LIGHTS: Final = tuple(
    f"light.esphome_esp32_devkitv1_led_{color}" for color in WIRE_NAMES
)

# The board's buzzers (examples/esphome-full.yaml); the actions are named
# after the ESPHome device's API name.
DEFAULT_BUZZER: Final = "switch.esphome_esp32_devkitv1_buzzer_hw_512"
DEFAULT_RTTTL_PLAY: Final = "esphome.esphome_web_3053a0_play_rtttl"
DEFAULT_RTTTL_STOP: Final = "esphome.esphome_web_3053a0_stop_rtttl"

# All lights go dark for this long between two symbols, so a repeated letter
# is still visible as two letters (GAP_MS in the browser app). Colored letters
# can change it with "Pauză între litere" (0 = no dark gap, for fast animations).
GAP: Final = 0.4  # seconds
DEFAULT_GAP_MS: Final = 400
MAX_GAP_MS: Final = 5000
GAP_STEP: Final = 10
# the shortest time a symbol stays lit, whatever the Interval
MIN_HOLD: Final = 0.1  # seconds

# Message type -----------------------------------------------------------------
# The options of the "Tip mesaj" select (shown as they are).
MODE_COLORS: Final = "Litere colorate"  # 5-wire alphabet, all lamps
MODE_MORSE: Final = "Morse"  # international Morse on one lamp
MODES: Final = (MODE_COLORS, MODE_MORSE)

# The options of the "Culoare Morse" select: the lamp Morse is sent on, by wire.
MORSE_COLORS: Final = ("galben", "roșu", "albastru", "verde", "alb")
DEFAULT_MORSE_COLOR: Final = "galben"

# The options of the "Sunet Morse" select: how Morse sounds while its lamp is lit.
SOUND_NONE: Final = "Fără"
SOUND_BUZZER: Final = "Buzzer activ"  # CONF_BUZZER on / off with the lamp
SOUND_RTTTL: Final = "RTTTL"  # MORSE_TONE on lit, stopped on dark
SOUNDS: Final = (SOUND_NONE, SOUND_BUZZER, SOUND_RTTTL)
# one whole note at 30 bpm (8 s), longer than any dash; stopped when the lamp goes dark
MORSE_TONE: Final = "morse:d=1,o=6,b=30:a"

# Interval, in ms, kept separately for each message type:
# colored letters = time per symbol (dark gap included),
# Morse = the length of a dot (dash 3, letter gap 3, word gap 7).
DEFAULT_INTERVALS: Final = {MODE_COLORS: 5000, MODE_MORSE: 400}
MIN_INTERVAL: Final = 100
MAX_INTERVAL: Final = 60000
INTERVAL_STEP: Final = 10

MAX_MESSAGE: Final = 255  # HA state length limit

# Repeat: ms of pause before the message starts again; 0 = play once.
# Short pauses make looping animations (see README).
DEFAULT_REPEAT: Final = 0
MAX_REPEAT: Final = 3_600_000  # 1 hour
REPEAT_STEP: Final = 10

# Progress states -------------------------------------------------------------
STATE_IDLE: Final = "idle"
STATE_PLAYING: Final = "playing"
STATE_DONE: Final = "done"
STATE_WAITING: Final = "waiting"  # pause before the next repetition
STATE_STOPPED: Final = "stopped"
STATE_ERROR: Final = "error"
