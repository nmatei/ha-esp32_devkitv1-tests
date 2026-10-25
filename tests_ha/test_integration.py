"""Config flow, entities and a real playback on 5 input_boolean "lamps"."""

import asyncio

from homeassistant import config_entries
from homeassistant.setup import async_setup_component
from homeassistant.core import State
from pytest_homeassistant_custom_component.common import (
    MockConfigEntry,
    mock_restore_cache,
    mock_restore_cache_with_extra_data,
)

DOMAIN = "alfabet_pe_fire"
LAMPS = [f"input_boolean.l{i}" for i in range(1, 6)]


def _lamps(hass):
    return [hass.states.get(e).state == "on" for e in LAMPS]


async def _call(hass, domain, service, entity_id, **data):
    await hass.services.async_call(domain, service, {"entity_id": entity_id, **data}, blocking=True)


async def test_flow_defaults_create_the_card_entities(hass):
    r = await hass.config_entries.flow.async_init(DOMAIN, context={"source": config_entries.SOURCE_USER})
    r = await hass.config_entries.flow.async_configure(r["flow_id"], {})
    assert r["type"] == "create_entry"
    assert r["title"] == "ESP32 devkitv1"
    assert r["data"]["lights"][4] == "light.office_esphome_esp32_devkitv1_led_alb"
    await hass.async_block_till_done()
    # the ids used by examples/dashboard-card.yaml
    for e in (
        "text.esp32_devkitv1_mesaj",
        "number.esp32_devkitv1_interval",
        "number.esp32_devkitv1_repeta_dupa",
        "number.esp32_devkitv1_pauza_intre_litere",
        "select.esp32_devkitv1_tip_mesaj",
        "select.esp32_devkitv1_culoare_morse",
        "button.esp32_devkitv1_start",
        "button.esp32_devkitv1_stop",
        "sensor.esp32_devkitv1_progres",
    ):
        assert hass.states.get(e) is not None, e


async def _setup(hass):
    await async_setup_component(hass, "homeassistant", {})
    await async_setup_component(hass, "input_boolean", {"input_boolean": {f"l{i}": {} for i in range(1, 6)}})
    entry = MockConfigEntry(domain=DOMAIN, title="Test", data={"lights": LAMPS})
    entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    return entry


async def test_play_stop_and_finish(hass):
    entry = await _setup(hass)

    await _call(hass, "text", "set_value", "text.test_mesaj", value="vq.")  # Q is skipped
    await _call(hass, "number", "set_value", "number.test_interval", value=1000)
    await _call(hass, "button", "press", "button.test_start")
    await asyncio.sleep(0.6)  # past the 0.4 s gap
    assert _lamps(hass) == [True, False, True, False, True]  # V = 21 = 10101
    assert hass.states.get("sensor.test_progres").state == "1 / 2 · V (10101 · 21)"
    await asyncio.sleep(1.0)
    assert _lamps(hass) == [True] * 5  # . = 31

    await _call(hass, "button", "press", "button.test_stop")
    await hass.async_block_till_done()
    assert _lamps(hass) == [False] * 5
    assert hass.states.get("sensor.test_progres").state == "oprit"

    await _call(hass, "button", "press", "button.test_start")
    await asyncio.sleep(2.3)
    await hass.async_block_till_done()
    assert hass.states.get("sensor.test_progres").state == "gata"
    assert _lamps(hass) == [False] * 5

    assert await hass.config_entries.async_unload(entry.entry_id)


async def test_morse_on_the_chosen_lamp(hass):
    entry = await _setup(hass)
    assert hass.states.get("select.test_tip_mesaj").state == "Litere colorate"

    await _call(hass, "text", "set_value", "text.test_mesaj", value="et")
    await _call(hass, "select", "select_option", "select.test_tip_mesaj", option="Morse")
    await _call(hass, "select", "select_option", "select.test_culoare_morse", option="alb")
    await _call(hass, "number", "set_value", "number.test_interval", value=200)
    await _call(hass, "button", "press", "button.test_start")

    # lead-in 3 units (0-0.6 s), E = . (0.6-0.8 s), letter gap (0.8-1.4 s), T = - (1.4-2.0 s)
    await asyncio.sleep(0.3)
    assert _lamps(hass) == [False] * 5
    await asyncio.sleep(0.4)
    assert _lamps(hass) == [False, False, False, False, True]
    assert hass.states.get("sensor.test_progres").attributes["code"] == "."
    await asyncio.sleep(0.4)
    assert _lamps(hass) == [False] * 5
    await asyncio.sleep(0.5)
    assert _lamps(hass) == [False, False, False, False, True]
    assert hass.states.get("sensor.test_progres").state == "2 / 2 · T (-)"
    await asyncio.sleep(0.7)
    await hass.async_block_till_done()
    assert _lamps(hass) == [False] * 5
    assert hass.states.get("sensor.test_progres").state == "gata"

    assert await hass.config_entries.async_unload(entry.entry_id)


async def test_interval_is_remembered_per_mode(hass):
    entry = await _setup(hass)
    interval = lambda: hass.states.get("number.test_interval")  # noqa: E731
    assert float(interval().state) == 5000

    await _call(hass, "number", "set_value", "number.test_interval", value=3000)
    await _call(hass, "select", "select_option", "select.test_tip_mesaj", option="Morse")
    assert float(interval().state) == 400
    await _call(hass, "number", "set_value", "number.test_interval", value=600)
    await _call(hass, "select", "select_option", "select.test_tip_mesaj", option="Litere colorate")
    assert float(interval().state) == 3000
    assert interval().attributes["interval_morse"] == 600
    assert interval().attributes["interval_litere_colorate"] == 3000

    assert await hass.config_entries.async_unload(entry.entry_id)


async def test_restore_keeps_both_intervals_and_migrates_seconds(hass):
    mock_restore_cache(hass, [
        State("select.test_tip_mesaj", "Morse"),
        State("number.test_interval", "600", {"interval_litere_colorate": 3000, "interval_morse": 600}),
    ])
    entry = await _setup(hass)
    state = hass.states.get("number.test_interval")
    assert float(state.state) == 600  # Morse is the restored mode
    assert state.attributes["interval_litere_colorate"] == 3000
    assert await hass.config_entries.async_unload(entry.entry_id)


async def test_restore_migrates_the_old_seconds_interval(hass):
    mock_restore_cache(hass, [State("number.test_interval", "2.5", {"unit_of_measurement": "s"})])
    entry = await _setup(hass)
    assert float(hass.states.get("number.test_interval").state) == 2500  # 2.5 s → 2500 ms (step 100)
    assert await hass.config_entries.async_unload(entry.entry_id)


async def test_repeat_plays_again_until_turned_off(hass):
    entry = await _setup(hass)
    assert float(hass.states.get("number.test_repeta_dupa").state) == 0

    await _call(hass, "text", "set_value", "text.test_mesaj", value="e")
    await _call(hass, "select", "select_option", "select.test_tip_mesaj", option="Morse")
    await _call(hass, "number", "set_value", "number.test_interval", value=200)
    await _call(hass, "number", "set_value", "number.test_repeta_dupa", value=1000)
    await _call(hass, "button", "press", "button.test_start")

    # each play: lead-in 0.6 s, E = . (0.6-0.8 s); then 1 s pause
    await asyncio.sleep(0.7)
    assert _lamps(hass)[0]
    await asyncio.sleep(0.5)  # 1.2 s: in the pause
    assert hass.states.get("sensor.test_progres").state == "pauză, reia după 1000 ms"
    assert not any(_lamps(hass))
    await asyncio.sleep(1.3)  # 2.5 s: second play, 1.8 + 0.6 lead-in -> dot at 2.4-2.6
    assert _lamps(hass)[0]
    assert hass.states.get("sensor.test_progres").state == "1 / 1 · E (·)"

    # 0 stops the repeating after the current play
    await _call(hass, "number", "set_value", "number.test_repeta_dupa", value=0)
    await asyncio.sleep(0.5)
    await hass.async_block_till_done()
    assert hass.states.get("sensor.test_progres").state == "gata"
    assert not any(_lamps(hass))

    assert await hass.config_entries.async_unload(entry.entry_id)


async def test_stop_during_the_repeat_pause(hass):
    entry = await _setup(hass)
    await _call(hass, "text", "set_value", "text.test_mesaj", value="e")
    await _call(hass, "select", "select_option", "select.test_tip_mesaj", option="Morse")
    await _call(hass, "number", "set_value", "number.test_interval", value=200)
    await _call(hass, "number", "set_value", "number.test_repeta_dupa", value=5000)
    await _call(hass, "button", "press", "button.test_start")
    await asyncio.sleep(1.2)
    assert hass.states.get("sensor.test_progres").state == "pauză, reia după 5000 ms"

    await _call(hass, "button", "press", "button.test_stop")
    await hass.async_block_till_done()
    assert hass.states.get("sensor.test_progres").state == "oprit"
    assert not any(_lamps(hass))
    assert await hass.config_entries.async_unload(entry.entry_id)


async def test_repeat_restores_the_old_seconds_value_as_ms(hass):
    mock_restore_cache_with_extra_data(hass, [(
        State("number.test_repeta_dupa", "3"),
        {"native_value": 3, "native_unit_of_measurement": "s",
         "native_min_value": 0, "native_max_value": 3600, "native_step": 1},
    )])
    entry = await _setup(hass)
    assert float(hass.states.get("number.test_repeta_dupa").state) == 3000
    assert await hass.config_entries.async_unload(entry.entry_id)


async def test_chaser_animation_loops(hass):
    """README example: one lamp at a time, left to right, forever."""
    entry = await _setup(hass)
    await _call(hass, "text", "set_value", "text.test_mesaj", value="PHDBA")
    await _call(hass, "number", "set_value", "number.test_interval", value=800)
    await _call(hass, "number", "set_value", "number.test_repeta_dupa", value=200)
    seen = []
    await _call(hass, "button", "press", "button.test_start")
    for _ in range(26):  # 0.8 s per letter, 4 s per round + 0.2 s pause
        await asyncio.sleep(0.25)
        lamps = _lamps(hass)
        if any(lamps) and (not seen or seen[-1] != lamps):
            seen.append(lamps)
    one_hot = [[i == n for i in range(5)] for n in range(5)]
    assert seen[:6] == one_hot + one_hot[:1]  # second round starts again on the left
    await _call(hass, "button", "press", "button.test_stop")
    assert await hass.config_entries.async_unload(entry.entry_id)


async def test_fast_chaser_without_letter_gap(hass):
    """Pauză între litere = 0 and Interval 300 ms: a lamp moves every 0.3 s, never all dark."""
    entry = await _setup(hass)
    assert float(hass.states.get("number.test_pauza_intre_litere").state) == 400
    await _call(hass, "text", "set_value", "text.test_mesaj", value="PHDBA")
    await _call(hass, "number", "set_value", "number.test_interval", value=300)
    await _call(hass, "number", "set_value", "number.test_pauza_intre_litere", value=0)
    await _call(hass, "button", "press", "button.test_start")
    seen = []
    for _ in range(14):  # 1.5 s per round, sampled every 0.1 s
        await asyncio.sleep(0.1)
        lamps = _lamps(hass)
        assert any(lamps)  # never all dark (on goes before off, so a hand-over may show 2)
        if sum(lamps) == 1 and (not seen or seen[-1] != lamps):
            seen.append(lamps)
    assert seen[:5] == [[i == n for i in range(5)] for n in range(5)]
    await _call(hass, "button", "press", "button.test_stop")
    assert await hass.config_entries.async_unload(entry.entry_id)
