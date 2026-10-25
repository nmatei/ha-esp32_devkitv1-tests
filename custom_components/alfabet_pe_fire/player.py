"""Plays a message on the lamps, one symbol at a time.

Pure and HA-free: lamps, progress reporting and sleep are injected callables,
so the timing is unit-testable with a fake clock. Stopping is done by
cancelling the task that runs :func:`play`.
"""

from __future__ import annotations

import asyncio
from collections.abc import Awaitable, Callable
from dataclasses import dataclass

from .const import GAP, STATE_DONE, STATE_IDLE, STATE_PLAYING
from .encoding import OFF, Symbol

SetLights = Callable[[tuple[bool, ...]], Awaitable[None]]


@dataclass(frozen=True)
class Progress:
    """Where the playback is."""

    state: str = STATE_IDLE
    index: int = 0  # 1-based position of the current symbol
    total: int = 0
    symbol: Symbol | None = None


def hold_time(interval: float, gap: float = GAP) -> float:
    """How long a symbol stays lit: the interval includes the dark gap."""
    return max(interval - gap, gap)


async def play(
    symbols: list[Symbol],
    interval: float,
    set_lights: SetLights,
    on_progress: Callable[[Progress], None],
    sleep: Callable[[float], Awaitable[None]] = asyncio.sleep,
    gap: float = GAP,
) -> None:
    """For each symbol: all lamps off for ``gap``, then its code until the next one."""
    total = len(symbols)
    hold = hold_time(interval, gap)
    for index, symbol in enumerate(symbols, 1):
        on_progress(Progress(STATE_PLAYING, index, total, symbol))
        await set_lights(OFF)
        await sleep(gap)
        await set_lights(symbol.bits)
        await sleep(hold)
    await set_lights(OFF)
    on_progress(Progress(STATE_DONE, total, total))
