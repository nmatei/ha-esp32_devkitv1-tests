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
    assert [(p.state, p.index, p.total) for p in progress] == [
        (STATE_PLAYING, 1, 2), (STATE_PLAYING, 2, 2), (STATE_DONE, 2, 2)
    ]
    assert progress[1].symbol.char == "."


def test_empty_message_only_turns_off():
    log, progress = _run("qwy", 5)
    assert log == [("lights", OFF)]
    assert progress[-1].state == STATE_DONE


def test_hold_never_shorter_than_gap():
    assert hold_time(1.0) == 0.6
    assert hold_time(0.5) == 0.4
