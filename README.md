# Alfabetul pe fire

A Home Assistant custom integration (HACS-compatible) that transmits a text
message on **5 lamps** — the 5 LEDs of an ESP32 devkitv1, or any 5
lights/switches — using the 5-wire alphabet from the
[bible-ai-preado](../bible-ai-preado) lessons. It is the "Redare automată"
panel of the browser app, running in Home Assistant: type a message, set the
seconds per symbol, press **Start**.

Personal study project; no CI.

## ⚙️ How it works

Each symbol is a 5-bit code, wire 1 (yellow) being the most significant bit:

| Code    | Symbols                                        |
| ------- | ---------------------------------------------- |
| 1 – 28  | A–Z without Q, W, Y (A=1 … Z=23), then Ă Â Î Ș Ț |
| 29      | space (`11101`)                                |
| 30      | comma (`11110`)                                |
| 31      | full stop = STOP (`11111`)                     |

For every symbol: all lamps off for 0.4 s, then the code stays lit until the
next one (the interval includes the 0.4 s). Lowercase becomes uppercase,
ş/ţ (cedilla) become ș/ț, `! ?` → full stop, `: ;` → comma, `-` → space;
everything else that is not in the code (Q, W, Y, quotes, digits) is skipped.

## 📥 Installation

- **Manual:** copy `custom_components/alfabet_pe_fire/` into
  `/config/custom_components/` on the HA machine, restart HA.
- **HACS (custom repository):** once the repo is on GitHub
  (`https://github.com/nmatei/ha-esp32_devkitv1-tests`, type *Integration*);
  updates then come from HACS.

Then **Settings → Devices & Services → + Add Integration → Alfabetul pe fire**:
a name (default `ESP32 devkitv1`) and the 5 lamps, prefilled with
`light.office_esphome_esp32_devkitv1_led_{galben,rosu,albastru,verde,alb}`.
**Configure** changes the lamps later (e.g. `light.sanctuar_randul1…5`).

The ESPHome side (5 GPIO outputs as binary lights) is in
[examples/esphome-leds.yaml](examples/esphome-leds.yaml).

## 🎛️ Entities

One device per entry, with:

| Entity                          | What                                              |
| ------------------------------- | ------------------------------------------------- |
| `text.<name>_mesaj`             | the message (max 255 characters), kept on restart |
| `number.<name>_interval`        | seconds per symbol, 1–60, step 0.5, default 5     |
| `button.<name>_start`           | plays from the beginning (restarts if running)    |
| `button.<name>_stop`            | stops and turns all lamps off                     |
| `sensor.<name>_progres`         | `7 / 42 · L`, `gata`, `oprit`; attributes `index`, `total`, `symbol`, `code`, `binary` |

A ready dashboard card: [examples/dashboard-card.yaml](examples/dashboard-card.yaml)
(Edit dashboard → Add card → Manual).

## 🧪 Development

```bash
# pure logic (encoding + timing), fast, no HA
python3 -m venv .venv && .venv/bin/pip install pytest
.venv/bin/python -m pytest

# integration tests against a real HA core (Python ≥ 3.13, big install)
python3.14 -m venv .venv-ha && .venv-ha/bin/pip install pytest-homeassistant-custom-component
.venv-ha/bin/python -m pytest tests_ha
```
