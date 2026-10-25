# Alfabetul pe fire

A Home Assistant custom integration (HACS-compatible) that transmits a text
message on **5 lamps** — the 5 LEDs of an ESP32 devkitv1, or any 5
lights/switches — using the 5-wire alphabet from the
[bible-tech](https://github.com/nmatei/bible-tech) lessons, or in **international Morse
code** on one lamp of your choice. It is the "Redare automată"
panel of the browser app, running in Home Assistant: type a message, set the
time per symbol, press **Start**.

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

### Morse

With **Tip mesaj = Morse** the message is sent in international Morse code
(ITU-R M.1677-1) on the lamp chosen in **Culoare Morse**. The timing is the real
one, in units of **Interval** (the length of a dot, default 400 ms):

| Element                              | Lamp | Units |
| ------------------------------------ | ---- | ----- |
| dot `.`                              | on   | 1     |
| dash `-`                             | on   | 3     |
| between the dots/dashes of a letter  | off  | 1     |
| between letters                      | off  | 3     |
| between words                        | off  | 7     |

Letters A–Z, digits 0–9 and `. , : ? ' - / ( ) " = + @` (ITU), plus the common
`! ; & _ $`. Ă Â Î Ș Ț have no Morse code and are sent as A A I S T; anything
else is skipped. Waits run to deadlines, so the time a lamp takes to switch
does not stretch the rhythm; a very late switch never cuts a dot, dash or gap
below half its length. The lamps stay off for 3 units before the first letter,
while the link to the ESP32 wakes up.

> If dots still go missing (often the first one), set
> `wifi: power_save_mode: none` on the ESP32 — see
> [examples/esphome-leds.yaml](examples/esphome-leds.yaml). With the default
> power saving, commands can be delayed and arrive bunched together.

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
| `select.<name>_tip_mesaj`       | `Litere colorate` (5 wires) or `Morse`            |
| `number.<name>_interval`        | ms, 200–60000, step 200; **one value per message type**: time per symbol for colored letters (default 5000), dot length for Morse (default 400). Switching the type shows its value. |
| `select.<name>_culoare_morse`   | Morse: the lamp (`galben` … `alb`, wire 1 … 5)    |
| `number.<name>_repeta_dupa`     | ms, 0–3600000, step 200: **0 = play once**; above 0 the message starts again after that pause, forever, until Stop (or until set back to 0). Each repetition reads the settings again, so they can be changed while it repeats. |
| `button.<name>_start`           | plays from the beginning (restarts if running)    |
| `button.<name>_stop`            | stops and turns all lamps off                     |
| `sensor.<name>_progres`         | `2 / 3 · L (01100 · 12)`, in Morse `2 / 3 · L (· - · ·)`, `pauză, reia după 1000 ms` between repetitions, then `gata` / `oprit`; attributes `index`, `total`, `symbol`, `code` (`21`, or `.-` in Morse), `binary` (colored letters only) |

A ready dashboard card: [examples/dashboard-card.yaml](examples/dashboard-card.yaml)
(Edit dashboard → Add card → Manual).

## 🔁 Looping animations

With **Repetă după** above 0 the message plays forever, so a few chosen letters
make the lamps "move". In **Litere colorate** every letter lights its 5-bit
code, so pick the letters whose codes have the lamps you want:

| Code | 16 | 8 | 4 | 2 | 1 | 24 (16+8) | 12 (8+4) | 6 (4+2) | 3 (2+1) |
| ---- | -- | - | - | - | - | --------- | -------- | ------- | ------- |
| Letter | P | H | D | B | A | Ă | L | F | C |
| Lamps | `10000` | `01000` | `00100` | `00010` | `00001` | `11000` | `01100` | `00110` | `00011` |

**One lamp at a time, left to right, forever** (yellow → white), set on the card:

| Entity | Value |
| ------ | ----- |
| Mesaj | `PHDBA` |
| Tip mesaj | `Litere colorate` |
| Interval | `800` ms |
| Repetă după | `200` ms |

Right to left: `ABDHP`. Back and forth: `PHDBABDH`.

**Two lamps at a time, left to right, forever** (yellow+red → green+white):
the same settings with Mesaj = `ĂLFC`. Right to left: `CFLĂ`.

As an automation action (e.g. on a button or at a given time):

```yaml
- action: text.set_value
  target: { entity_id: text.esp32_devkitv1_mesaj }
  data: { value: PHDBA }
- action: select.select_option
  target: { entity_id: select.esp32_devkitv1_tip_mesaj }
  data: { option: Litere colorate }
- action: number.set_value
  target: { entity_id: number.esp32_devkitv1_interval }
  data: { value: 800 }
- action: number.set_value
  target: { entity_id: number.esp32_devkitv1_repeta_dupa }
  data: { value: 200 }
- action: button.press
  target: { entity_id: button.esp32_devkitv1_start }
```

Timing: every letter starts with all lamps off for 0.4 s, then its code stays
lit for the rest of the Interval (at least 0.4 s), so 800 ms = 0.4 s off +
0.4 s on — the fastest step; a smaller Interval does not go faster. Between two rounds there is also the Repetă după pause (200 ms is the
shortest above 0). **Stop** ends the animation.

## 🧪 Development

```bash
# pure logic (encoding + timing), fast, no HA
python3 -m venv .venv && .venv/bin/pip install pytest
.venv/bin/python -m pytest

# integration tests against a real HA core (Python ≥ 3.13, big install)
python3.14 -m venv .venv-ha && .venv-ha/bin/pip install pytest-homeassistant-custom-component
.venv-ha/bin/python -m pytest tests_ha
```
