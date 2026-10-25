"""Constants for the Alfabetul pe fire integration."""

from __future__ import annotations

from typing import Final

DOMAIN: Final = "alfabet_pe_fire"

# Config keys -----------------------------------------------------------------
CONF_NAME: Final = "name"
CONF_LIGHTS: Final = "lights"  # 5 entity ids, wire 1 (MSB) … wire 5 (LSB)

# Wires -----------------------------------------------------------------------
# Same order and colors as the physical board and the printed code sheet.
WIRE_COUNT: Final = 5
WIRE_NAMES: Final = ("galben", "rosu", "albastru", "verde", "alb")

# Defaults --------------------------------------------------------------------
DEFAULT_NAME: Final = "ESP32 devkitv1"
DEFAULT_LIGHTS: Final = tuple(
    f"light.office_esphome_esp32_devkitv1_led_{color}" for color in WIRE_NAMES
)

# All lights go dark for this long between two symbols, so a repeated letter
# is still visible as two letters (GAP_MS in the browser app).
GAP: Final = 0.4  # seconds

# Message type -----------------------------------------------------------------
# The options of the "Tip mesaj" select (shown as they are).
MODE_COLORS: Final = "Litere colorate"  # 5-wire alphabet, all lamps
MODE_MORSE: Final = "Morse"  # international Morse on one lamp
MODES: Final = (MODE_COLORS, MODE_MORSE)

# The options of the "Culoare Morse" select: the lamp Morse is sent on, by wire.
MORSE_COLORS: Final = ("galben", "roșu", "albastru", "verde", "alb")
DEFAULT_MORSE_COLOR: Final = "galben"

# Interval, in ms, kept separately for each message type:
# colored letters = time per symbol (dark gap included),
# Morse = the length of a dot (dash 3, letter gap 3, word gap 7).
DEFAULT_INTERVALS: Final = {MODE_COLORS: 5000, MODE_MORSE: 400}
MIN_INTERVAL: Final = 200
MAX_INTERVAL: Final = 60000
INTERVAL_STEP: Final = 200

MAX_MESSAGE: Final = 255  # HA state length limit

# Progress states -------------------------------------------------------------
STATE_IDLE: Final = "idle"
STATE_PLAYING: Final = "playing"
STATE_DONE: Final = "done"
STATE_STOPPED: Final = "stopped"
STATE_ERROR: Final = "error"
