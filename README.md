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

# Full letter transmission

`ABCDEFGHIJKLMNOPQRSTUVWXYZĂÂÎȘȚ ,.`

For every symbol: all lamps off for **Pauză între litere** (default 400 ms),
then the code stays lit until the next one. The Interval includes that pause;
a code stays lit at least 100 ms. Lowercase becomes uppercase,
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
`light.esphome_esp32_devkitv1_led_{galben,rosu,albastru,verde,alb}`.
**Configure** changes the lamps later (e.g. `light.sanctuar_randul1…5`).

The ESPHome side (5 GPIO outputs as binary lights) is in
[examples/esphome-leds.yaml](examples/esphome-leds.yaml).

## 🎛️ Entities

One device per entry, with:

| Entity                          | What                                              |
| ------------------------------- | ------------------------------------------------- |
| `text.<name>_mesaj`             | the message (max 255 characters), kept on restart |
| `select.<name>_tip_mesaj`       | `Litere colorate` (5 wires) or `Morse`            |
| `number.<name>_interval`        | ms, 100–60000, step 10; **one value per message type**: time per symbol for colored letters (default 5000), dot length for Morse (default 400). Switching the type shows its value. |
| `select.<name>_culoare_morse`   | Morse: the lamp (`galben` … `alb`, wire 1 … 5)    |
| `select.<name>_sunet_morse`     | Morse sound, exactly as long as the lamp is lit: `Fără` (none, default), `Buzzer activ` (a switch on/off with the lamp), `RTTTL` (a long tone started on lit, stopped on dark). The buzzer and the two RTTTL actions (`play_rtttl` with `song_str`, `stop_rtttl`) are set in the integration options. |
| `number.<name>_pauza_intre_litere` | colored letters: ms all lamps stay dark before each letter, 0–5000, step 10, default 400. **0 = no dark gap** (smooth, fast animations; two equal letters in a row then look like one). |
| `number.<name>_repeta_dupa`     | ms, 0–3600000, step 10: **0 = play once**; above 0 the message starts again after that pause, forever, until Stop (or until set back to 0). Each repetition reads the settings again, so they can be changed while it repeats. |
| `binary_sensor.<name>_pauza`   | colored letters: `on` while all lamps are dark before a letter (Pauză între litere), to react to it (stays `off` with Pauză între litere = 0). For a sound on every letter, gap or not, see [sunet-pauza.yaml](examples/automations/sunet-pauza.yaml) |
| `button.<name>_start`           | plays from the beginning (restarts if running)    |
| `button.<name>_stop`            | stops and turns all lamps off                     |
| `sensor.<name>_progres`         | `2 / 3 · L (01100 · 12)`, in Morse `2 / 3 · L (· - · ·)`, `pauză, reia după 1000 ms` between repetitions, then `gata` / `oprit`; attributes `index`, `total`, `symbol`, `code` (`21`, or `.-` in Morse), `binary` (colored letters only) |

Ready dashboard cards (Edit dashboard → Add card → Manual):
[examples/dashboard/dashboard-leds.yaml](examples/dashboard/dashboard-leds.yaml) (the lamps,
Start/Stop, Mesaj and Progres; needs `button-card` and `card-mod` from HACS) and
[examples/dashboard/dashboard-card.yaml](examples/dashboard/dashboard-card.yaml) (the settings).

The full device setup (ESPHome, wiring, dashboard, automations), in Romanian:
[examples/](examples/README.md); the modules and parts on the board: [examples/componente.md](examples/componente.md).

## 🔁 Looping animations

With **Repetă după** above 0 the message plays forever, so a few chosen letters
make the lamps "move". Every letter lights its 5-bit code (wire 1 yellow on the
left … wire 5 white on the right).

**1. Set once** (same for every animation below):

| Entity      | Value             |
| ----------- | ----------------- |
| Tip mesaj   | `Litere colorate` |
| Interval    | `800` ms          |
| Pauză între litere | `400` ms   |
| Repetă după | `100` ms          |

Faster and smooth, without the dark blink between steps: Interval `300` ms,
Pauză între litere `0` ms (a lamp moves every 0.3 s).

**2. Copy a message** into **Mesaj**, then press **Start** (**Stop** ends it):

| Animation                         | Mesaj      | Lamps, step by step                                                   |
| --------------------------------- | ---------- | --------------------------------------------------------------------- |
| One lamp, left → right            | `PHDBA`    | `10000` → `01000` → `00100` → `00010` → `00001`                       |
| One lamp, right → left            | `ABDHP`    | `00001` → `00010` → `00100` → `01000` → `10000`                       |
| One lamp, back and forth          | `PHDBABDH` | `10000` → `01000` → `00100` → `00010` → `00001` → `00010` → `00100` → `01000` |
| Two lamps, left → right           | `ĂLFC`     | `11000` → `01100` → `00110` → `00011`                                 |
| Two lamps, right → left           | `CFLĂ`     | `00011` → `00110` → `01100` → `11000`                                 |
| Two lamps, back and forth         | `ĂLFCFL`   | `11000` → `01100` → `00110` → `00011` → `00110` → `01100`             |
| Edges → center                    | `RJD`      | `10001` → `01010` → `00100`                                           |
| Center → edges                    | `DJR`      | `00100` → `01010` → `10001`                                           |
| Center ↔ edges, back and forth    | `DJRJ`     | `00100` → `01010` → `10001` → `01010`                                 |
| All blink                         | `.`        | `11111`                                                               |

The letters behind the codes, to make your own:

| Code   | 16      | 8       | 4       | 2       | 1       | 24 (16+8) | 12 (8+4) | 6 (4+2) | 3 (2+1) | 17 (16+1) | 10 (8+2) | 31 (all) |
| ------ | ------- | ------- | ------- | ------- | ------- | --------- | -------- | ------- | ------- | --------- | -------- | -------- |
| Letter | `P`     | `H`     | `D`     | `B`     | `A`     | `Ă`       | `L`      | `F`     | `C`     | `R`       | `J`      | `.`      |
| Lamps  | `10000` | `01000` | `00100` | `00010` | `00001` | `11000`   | `01100`  | `00110` | `00011` | `10001`   | `01010`  | `11111`  |

The same as an automation action (e.g. on a button or at a given time); change
`value: PHDBA` to any message from the table:

```yaml
- action: select.select_option
  target: { entity_id: select.esp32_devkitv1_tip_mesaj }
  data: { option: Litere colorate }
- action: number.set_value
  target: { entity_id: number.esp32_devkitv1_interval }
  data: { value: 800 }
- action: number.set_value
  target: { entity_id: number.esp32_devkitv1_pauza_intre_litere }
  data: { value: 400 }
- action: number.set_value
  target: { entity_id: number.esp32_devkitv1_repeta_dupa }
  data: { value: 100 }
- action: text.set_value
  target: { entity_id: text.esp32_devkitv1_mesaj }
  data: { value: PHDBA }
- action: button.press
  target: { entity_id: button.esp32_devkitv1_start }
```

Timing: every letter starts with all lamps off for Pauză între litere, then
its code stays lit for the rest of the Interval (at least 100 ms), so 800 ms
with a 400 ms pause = 0.4 s off + 0.4 s on. With pause 0 each step is just the
Interval (from 100 ms). When going from code to code, lamps are turned on
before the others go off, so they hand over instead of all blinking dark.
Between two rounds there is also the Repetă după pause.

## 🧪 Development

```bash
# pure logic (encoding + timing), fast, no HA
python3 -m venv .venv && .venv/bin/pip install pytest
.venv/bin/python -m pytest

# integration tests against a real HA core (Python ≥ 3.13, big install)
python3.14 -m venv .venv-ha && .venv-ha/bin/pip install pytest-homeassistant-custom-component
.venv-ha/bin/python -m pytest tests_ha
```
