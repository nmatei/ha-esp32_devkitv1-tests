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

DEFAULT_INTERVAL: Final = 5.0  # seconds per symbol, pause included
MIN_INTERVAL: Final = 1.0
MAX_INTERVAL: Final = 60.0
INTERVAL_STEP: Final = 0.5

# All lights go dark for this long between two symbols, so a repeated letter
# is still visible as two letters (GAP_MS in the browser app).
GAP: Final = 0.4  # seconds

MAX_MESSAGE: Final = 255  # HA state length limit

# Progress states -------------------------------------------------------------
STATE_IDLE: Final = "idle"
STATE_PLAYING: Final = "playing"
STATE_DONE: Final = "done"
STATE_STOPPED: Final = "stopped"
STATE_ERROR: Final = "error"
