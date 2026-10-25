"""The 5-wire alphabet: message -> codes -> lamp bits.

Pure and HA-free, so it is unit-testable without Home Assistant.

The code is copied from bible-ai-preado ``src/shared/wires.js`` (``SETS[5]``),
which stays the source of truth: the same code is on the printed sheets the
kids decode with. ``tests/test_sync_with_wires.py`` compares the two when the
bible-ai-preado checkout sits next to this one.
"""

from __future__ import annotations

from dataclasses import dataclass

from .const import WIRE_COUNT

# The symbol with code ``c`` is ``SYMBOLS[c - 1]``; code 0 (all off) means nothing.
# 28 letters without Q, W, Y (A–Z, then Ă Â Î Ș Ț), then space = 11101,
# comma = 11110, full stop = 11111 = STOP.
SYMBOLS = "ABCDEFGHIJKLMNOPRSTUVXZĂÂÎȘȚ ,."

# Signs that are not in the code fall back to their closest neighbour (FALLBACK
# and CEDILLA in wires.js); anything else that is not in the code is skipped.
REPLACEMENTS = {
    "Ş": "Ș",
    "Ţ": "Ț",
    "!": ".",
    "?": ".",
    ":": ",",
    ";": ",",
    "-": " ",
    "\n": " ",
}


@dataclass(frozen=True)
class Symbol:
    """One transmitted symbol."""

    char: str
    code: int

    @property
    def binary(self) -> str:
        """The code as wire 1 … wire 5, e.g. ``10101``."""
        return format(self.code, f"0{WIRE_COUNT}b")

    @property
    def bits(self) -> tuple[bool, ...]:
        """Which lamps are on, wire 1 (most significant bit) first."""
        return tuple(b == "1" for b in self.binary)

    @property
    def label(self) -> str:
        """Readable form; the space is shown as ␣."""
        return "␣" if self.char == " " else self.char

    @property
    def detail(self) -> str:
        """Binary and decimal code, e.g. ``01100 · 12``."""
        return f"{self.binary} · {self.code}"


def encode_char(ch: str) -> Symbol | None:
    """Encode one character, or ``None`` if it is skipped."""
    upper = ch.upper()
    upper = REPLACEMENTS.get(upper, upper)
    # len check: some characters upper-case to two letters (ß -> SS)
    if len(upper) != 1 or upper not in SYMBOLS:
        return None
    return Symbol(upper, SYMBOLS.index(upper) + 1)


def encode(message: str) -> list[Symbol]:
    """Encode a message, skipping what does not exist on 5 wires."""
    return [s for s in map(encode_char, message) if s is not None]


OFF: tuple[bool, ...] = (False,) * WIRE_COUNT
