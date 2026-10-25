"""Config flow, entities and a real playback on 5 input_boolean "lamps"."""

import asyncio

from homeassistant import config_entries
from homeassistant.setup import async_setup_component
from homeassistant.core import State
from pytest_homeassistant_custom_component.common import MockConfigEntry, mock_restore_cache

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
    assert hass.states.get("sensor.test_progres").state == "1 / 2 · V"
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

    # E = . (0-0.2 s), letter gap 3 units (0.2-0.8 s), T = - (0.8-1.4 s)
    await asyncio.sleep(0.1)
    assert _lamps(hass) == [False, False, False, False, True]
    assert hass.states.get("sensor.test_progres").attributes["code"] == "."
    await asyncio.sleep(0.4)
    assert _lamps(hass) == [False] * 5
    await asyncio.sleep(0.5)
    assert _lamps(hass) == [False, False, False, False, True]
    assert hass.states.get("sensor.test_progres").state == "2 / 2 · T"
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
    assert float(hass.states.get("number.test_interval").state) == 2600  # 2500 → step 200
    assert await hass.config_entries.async_unload(entry.entry_id)
