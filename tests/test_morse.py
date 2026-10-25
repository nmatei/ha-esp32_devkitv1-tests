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
    # 3 off (lead-in)   A = .-   gap 3   B = -...   word gap 7   C = -.-.
    assert _on_times(log) == [
        (3, 4), (5, 8),  # A: dot, 1 off, dash
        (11, 14), (15, 16), (17, 18), (19, 20),  # 3 off, B
        (27, 30), (31, 32), (33, 36), (37, 38),  # 7 off, C
    ]


def test_unit_scales_everything():
    log, _ = _run("et", unit=0.2)
    assert _on_times(log) == [(0.6, 0.8), (1.4, 2.0)]


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
    assert [t for t, on in log if on] == [3.1, 7.1]


def test_progress_counts_word_breaks():
    _, progress = _run("e t")
    assert [(p.state, p.index, p.total) for p in progress] == [
        (STATE_PLAYING, 1, 3), (STATE_PLAYING, 2, 3), (STATE_PLAYING, 3, 3), (STATE_DONE, 3, 3)
    ]
    assert progress[0].symbol.code == "."


def _run_with_latency(message, delays, unit=0.4):
    """Like _run, but the n-th lamp switch takes delays[n] seconds (then 0)."""
    now = [0.0]
    calls = [0]
    log = []

    async def set_lights(bits):
        n = calls[0]
        calls[0] += 1
        now[0] += delays[n] if n < len(delays) else 0
        log.append((round(now[0], 3), any(bits)))

    async def sleep(seconds):
        now[0] += seconds

    asyncio.run(play_morse(encode(message), unit, 0, set_lights, lambda p: None, sleep, lambda: now[0]))
    return log


def test_a_slow_first_switch_does_not_swallow_the_first_dot():
    # the first "on" takes 450 ms (ESP32 waking up), longer than a 400 ms dot
    log = _run_with_latency("s", [0, 0.45])
    durations = [round(end - start, 3) for start, end in _on_times(log)]
    assert len(durations) == 3
    assert min(durations) >= 0.2  # every dot stays visible: at least half a unit


def test_a_slow_switch_mid_message_keeps_every_element_visible():
    # one "off" in the middle of SOS takes 700 ms, more than a whole gap
    log = _run_with_latency("sos", [0, 0, 0, 0, 0, 0, 0.7])
    on = _on_times(log)
    assert len(on) == 9
    assert all(end - start >= 0.2 for start, end in on)
    gaps = [b[0] - a[1] for a, b in zip(on, on[1:])]
    assert all(g >= 0.2 for g in gaps)
