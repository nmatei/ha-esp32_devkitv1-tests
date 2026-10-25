"""International Morse (ITU-R M.1677-1): table, encoding and real timing."""

import asyncio

from alfabet_pe_fire.const import STATE_DONE, STATE_PLAYING
from alfabet_pe_fire.encoding import OFF
from alfabet_pe_fire.morse import MORSE, WORD_BREAK, MorseSymbol, encode
from alfabet_pe_fire.player import play_morse


def test_itu_table():
    letters = ".- -... -.-. -.. . ..-. --. .... .. .--- -.- .-.. -- -. --- .--. --.- .-. ... - ..- ...- .-- -..- -.-- --.."
    assert [MORSE[c] for c in "ABCDEFGHIJKLMNOPQRSTUVWXYZ"] == letters.split()
    digits = "----- .---- ..--- ...-- ....- ..... -.... --... ---.. ----."
    assert [MORSE[c] for c in "0123456789"] == digits.split()
    assert MORSE["."] == ".-.-.-" and MORSE[","] == "--..--" and MORSE["?"] == "..--.."
    assert MORSE["@"] == ".--.-." and MORSE["!"] == "-.-.--"


def test_all_codes_are_distinct():
    assert len(set(MORSE.values())) == len(MORSE)


def test_words_lowercase_and_romanian_letters():
    assert [s.code for s in encode("sos")] == ["...", "---", "..."]
    assert encode("Ăâîșțşţ") == encode("AAISTST")
    assert encode("„Da”") == encode('"DA"')


def test_one_word_break_between_words_only():
    symbols = encode("  e   t  ")
    assert symbols == [MorseSymbol("E", "."), WORD_BREAK, MorseSymbol("T", "-")]
    assert WORD_BREAK.label == "␣" and WORD_BREAK.is_word_break


def test_unknown_signs_are_skipped_and_empty_words_dropped():
    assert encode("a € b") == encode("a b")
    assert encode("€ ~") == []


def _run(message, unit=1.0, wire=4):
    """Returns [(time, lamp on?)] and the progress, on a fake clock."""
    now = [0.0]
    log, progress = [], []

    async def set_lights(bits):
        log.append((round(now[0], 3), any(bits)))
        assert bits in (OFF, tuple(i == wire for i in range(5)))

    async def sleep(seconds):
        now[0] += seconds

    asyncio.run(play_morse(encode(message), unit, wire, set_lights, progress.append, sleep, lambda: now[0]))
    return log, progress


def _on_times(log):
    """[(start, end)] of every lamp-on period."""
    starts = [t for t, on in log if on]
    ends = [t for t, on in log[1:] if not on]
    return list(zip(starts, ends))


def test_timing_dot_dash_and_gaps():
    log, _ = _run("ab c")
    # A = .-   gap 3   B = -...   word gap 7   C = -.-.
    assert _on_times(log) == [
        (0, 1), (2, 5),  # A: dot, 1 off, dash
        (8, 11), (12, 13), (14, 15), (16, 17),  # 3 off, B
        (24, 27), (28, 29), (30, 33), (34, 35),  # 7 off, C
    ]


def test_unit_scales_everything():
    log, _ = _run("et", unit=0.2)
    assert _on_times(log) == [(0, 0.2), (0.8, 1.4)]


def test_lamp_latency_does_not_stretch_the_rhythm():
    now = [0.0]
    log = []

    async def slow_lights(bits):
        now[0] += 0.05  # each switch takes 50 ms
        log.append((round(now[0], 3), any(bits)))

    async def sleep(seconds):
        now[0] += seconds

    asyncio.run(play_morse(encode("ee"), 1.0, 0, slow_lights, lambda p: None, sleep, lambda: now[0]))
    # every switch is 50 ms late, but the lateness does not add up: the two dots
    # are still exactly dot 1 + letter gap 3 = 4 units apart (4.15 without deadlines)
    assert [t for t, on in log if on] == [0.1, 4.1]


def test_progress_counts_word_breaks():
    _, progress = _run("e t")
    assert [(p.state, p.index, p.total) for p in progress] == [
        (STATE_PLAYING, 1, 3), (STATE_PLAYING, 2, 3), (STATE_PLAYING, 3, 3), (STATE_DONE, 3, 3)
    ]
    assert progress[0].symbol.code == "."
