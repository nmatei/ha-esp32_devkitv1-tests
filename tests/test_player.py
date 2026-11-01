"""Timing of the playback, driven with a fake clock."""

import asyncio

from alfabet_pe_fire.const import STATE_DONE, STATE_PLAYING
from alfabet_pe_fire.encoding import OFF, encode
from alfabet_pe_fire.player import hold_time, play


def _run(message, interval):
    log, progress = [], []

    async def set_lights(bits):
        log.append(("lights", bits))

    async def sleep(seconds):
        log.append(("sleep", round(seconds, 3)))

    asyncio.run(play(encode(message), interval, set_lights, progress.append, sleep))
    return log, progress


def test_each_symbol_is_gap_then_code():
    log, _ = _run("AB", 5)
    a, b = encode("AB")
    assert log == [
        ("lights", OFF), ("sleep", 0.4), ("lights", a.bits), ("sleep", 4.6),
        ("lights", OFF), ("sleep", 0.4), ("lights", b.bits), ("sleep", 4.6),
        ("lights", OFF),
    ]


def test_progress_counts_and_ends_done():
    _, progress = _run("A?", 2)
    assert [(p.state, p.index, p.total) for p in progress if not p.pause] == [
        (STATE_PLAYING, 1, 2), (STATE_PLAYING, 2, 2), (STATE_DONE, 2, 2)
    ]
    assert progress[-2].symbol.char == "."


def test_the_dark_gap_is_reported_as_a_pause():
    log = []
    a = encode("A")[0]

    async def set_lights(bits):
        log.append(("lights", bits))

    async def sleep(seconds):
        log.append(("sleep", round(seconds, 3)))

    def on_progress(p):
        log.append(("pause", p.pause))

    asyncio.run(play([a], 5, set_lights, on_progress, sleep))
    assert log == [
        ("pause", True), ("lights", OFF), ("sleep", 0.4),
        ("pause", False), ("lights", a.bits), ("sleep", 4.6),
        ("lights", OFF), ("pause", False),
    ]


def test_empty_message_only_turns_off():
    log, progress = _run("qwy", 5)
    assert log == [("lights", OFF)]
    assert progress[-1].state == STATE_DONE


def test_interval_includes_the_gap_and_hold_has_a_floor():
    assert hold_time(1.0) == 0.6
    assert hold_time(0.5) == 0.1
    assert hold_time(0.3, gap=0) == 0.3
    assert hold_time(0.1, gap=0.4) == 0.1  # MIN_HOLD


def test_no_gap_goes_straight_from_code_to_code():
    log, progress = [], []
    a, b = encode("AB")

    async def set_lights(bits):
        log.append(("lights", bits))

    async def sleep(seconds):
        log.append(("sleep", round(seconds, 3)))

    asyncio.run(play(encode("AB"), 0.3, set_lights, progress.append, sleep, gap=0))
    assert log == [
        ("lights", a.bits), ("sleep", 0.3),
        ("lights", b.bits), ("sleep", 0.3),
        ("lights", OFF),
    ]


def test_no_gap_means_no_pause_signal():
    progress = []

    async def set_lights(bits):
        pass

    async def sleep(seconds):
        pass

    asyncio.run(play(encode("AB"), 0.3, set_lights, progress.append, sleep, gap=0))
    assert not any(p.pause for p in progress)
