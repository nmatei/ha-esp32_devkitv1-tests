"""International Morse code (ITU-R M.1677-1): message -> dots and dashes.

Pure and HA-free, so it is unit-testable without Home Assistant. Timing is in
units (the length of a dot); :func:`player.play_morse` turns them into seconds.
"""

from __future__ import annotations

from dataclasses import dataclass

# Timing, in units ------------------------------------------------------------
DOT = 1  # lamp on
DASH = 3  # lamp on
ELEMENT_GAP = 1  # off, between the dots/dashes of one letter
LETTER_GAP = 3  # off, between letters
WORD_GAP = 7  # off, between words

MORSE = {
    # letters
    "A": ".-",
    "B": "-...",
    "C": "-.-.",
    "D": "-..",
    "E": ".",
    "F": "..-.",
    "G": "--.",
    "H": "....",
    "I": "..",
    "J": ".---",
    "K": "-.-",
    "L": ".-..",
    "M": "--",
    "N": "-.",
    "O": "---",
    "P": ".--.",
    "Q": "--.-",
    "R": ".-.",
    "S": "...",
    "T": "-",
    "U": "..-",
    "V": "...-",
    "W": ".--",
    "X": "-..-",
    "Y": "-.--",
    "Z": "--..",
    # digits
    "1": ".----",
    "2": "..---",
    "3": "...--",
    "4": "....-",
    "5": ".....",
    "6": "-....",
    "7": "--...",
    "8": "---..",
    "9": "----.",
    "0": "-----",
    # punctuation (ITU)
    ".": ".-.-.-",
    ",": "--..--",
    ":": "---...",
    "?": "..--..",
    "'": ".----.",
    "-": "-....-",
    "/": "-..-.",
    "(": "-.--.",
    ")": "-.--.-",
    '"': ".-..-.",
    "=": "-...-",
    "+": ".-.-.",
    "@": ".--.-.",
    # not ITU, but in common use
    "!": "-.-.--",
    ";": "-.-.-.",
    "&": ".-...",
    "_": "..--.-",
    "$": "...-..-",
}

# Romanian letters have no Morse code: send the base letter. Typographic
# quotes and apostrophes become the plain ones.
FOLD = {
    "Ă": "A",
    "Â": "A",
    "Î": "I",
    "Ș": "S",
    "Ş": "S",
    "Ț": "T",
    "Ţ": "T",
    "„": '"',
    "”": '"',
    "“": '"',
    "«": '"',
    "»": '"',
    "’": "'",
    "‘": "'",
}


@dataclass(frozen=True)
class MorseSymbol:
    """One letter, or the break between two words (``char`` = space, no code)."""

    char: str
    code: str

    @property
    def is_word_break(self) -> bool:
        return not self.code

    @property
    def label(self) -> str:
        """Readable form; the word break is shown as ␣."""
        return "␣" if self.is_word_break else self.char


WORD_BREAK = MorseSymbol(" ", "")


def encode_char(ch: str) -> MorseSymbol | None:
    """Encode one character, or ``None`` if it has no Morse code."""
    upper = ch.upper()
    upper = FOLD.get(upper, upper)
    code = MORSE.get(upper)
    return MorseSymbol(upper, code) if code else None


def encode(message: str) -> list[MorseSymbol]:
    """Encode a message: one ``WORD_BREAK`` between words, unknown signs skipped."""
    words = [[s for s in map(encode_char, word) if s] for word in message.split()]
    symbols: list[MorseSymbol] = []
    for word in filter(None, words):
        if symbols:
            symbols.append(WORD_BREAK)
        symbols.extend(word)
    return symbols
