"""Config flow, entities and a real playback on 5 input_boolean "lamps"."""

import asyncio

from homeassistant import config_entries
from homeassistant.setup import async_setup_component
from pytest_homeassistant_custom_component.common import MockConfigEntry

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
        "button.esp32_devkitv1_start",
        "button.esp32_devkitv1_stop",
        "sensor.esp32_devkitv1_progres",
    ):
        assert hass.states.get(e) is not None, e


async def test_play_stop_and_finish(hass):
    await async_setup_component(hass, "homeassistant", {})
    await async_setup_component(hass, "input_boolean", {"input_boolean": {f"l{i}": {} for i in range(1, 6)}})
    entry = MockConfigEntry(domain=DOMAIN, title="Test", data={"lights": LAMPS})
    entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    await _call(hass, "text", "set_value", "text.test_mesaj", value="vq.")  # Q is skipped
    await _call(hass, "number", "set_value", "number.test_interval", value=1)
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
