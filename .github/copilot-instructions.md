# Alfabetul pe fire — project guide

## IDE rules sync

This file is kept in sync with the Copilot instructions:

| File | IDE |
|---|---|
| `CLAUDE.md` | Claude Code |
| `.github/copilot-instructions.md` | GitHub Copilot |

A `PostToolUse` hook (`.claude/settings.json` → `.claude/sync-rules-hook.sh`)
copies whichever of these two files was just edited over the other, so they
stay identical automatically. If you edit one outside Claude Code, run:

```bash
bash .claude/sync-rules.sh <path-to-the-file-you-edited>
```

## What this is

A Home Assistant **custom integration** (HACS-compatible), domain
`alfabet_pe_fire`. It plays a text message on 5 lamps (the ESP32 devkitv1 LEDs
by default) using the 5-wire alphabet of the **bible-ai-preado** lessons
(`../bible-ai-preado`), like the "Redare automată" panel of its browser app.
Personal study project: no CI, no GitHub Actions.

## Sync with bible-ai-preado (important)

The code is copied from `../bible-ai-preado/src/shared/wires.js` (`SETS[5]`,
`FALLBACK`, `CEDILLA`), which is the **source of truth**: the same code is on
sheets already printed for the kids. Never change `SYMBOLS` here on its own.
`tests/test_sync_with_wires.py` compares both when the checkout sits next to
this one; `tests/test_encoding.py` pins codes produced by `wires.js`.

## Architecture (`custom_components/alfabet_pe_fire/`)

- `encoding.py` — **pure**, HA-free: `SYMBOLS`, `REPLACEMENTS`, `Symbol`
  (`code`, `binary`, `bits` wire 1 first), `encode()`.
- `morse.py` — **pure**, HA-free: international Morse (ITU-R M.1677-1)
  `MORSE` table, `MorseSymbol`, `encode()` (one `WORD_BREAK` between words;
  Ă Â Î Ș Ț fold to A A I S T), unit counts `DOT` 1, `DASH` 3, `ELEMENT_GAP` 1,
  `LETTER_GAP` 3, `WORD_GAP` 7, `LEAD_IN` 3, `MIN_PART` 0.5.
- `player.py` — **pure**, HA-free: `play()` (per symbol: all off, `GAP` 0.4 s,
  code, hold `interval - GAP`), `play_morse()` (one lamp, waits to deadlines on
  an injected clock so lamp latency doesn't stretch the rhythm; `LEAD_IN` 3
  units off before the first letter; a late switch never cuts an element
  below `MIN_PART` = half — without that the slow first ESP32 call swallowed
  the first dot of SOS), `Progress`.
  Lamps / progress / sleep / clock are injected, so it is tested with a fake
  clock. Stop = cancel the task.
- `controller.py` — `AlfabetController`, one per config entry
  (`entry.runtime_data`): message, mode, `intervals` (ms, one per mode;
  `interval` is the current mode's), Morse color, `repeat` (ms, step 200, 0 = once), progress
  listeners, runs `play()` or `play_morse()` (by mode) as a background task,
  looping with a `STATE_WAITING` pause while `repeat` > 0 (settings re-read each time),
  drives lamps with `homeassistant.turn_on/turn_off` (works for `light` and
  `switch`).
- `text.py` / `number.py` / `select.py` / `button.py` / `sensor.py` — Mesaj,
  Interval (ms, follows the mode; both values in its attributes, restored), Repetă după (ms; a seconds value from 0.2.3 is restored ×1000),
  Tip mesaj + Culoare Morse, Start/Stop,
  Progres. Names are hardcoded Romanian on purpose: they make the entity ids
  used by `examples/dashboard-card.yaml`, whatever HA's language.
- `config_flow.py` — name + 5 entity selectors (`fir_1` … `fir_5`); the options
  flow changes the lamps. `translations/` has `en` and `ro`.
- `const.py` — keys, defaults (`DEFAULT_LIGHTS`), interval limits, `GAP`,
  `MODES` (select options), `MORSE_COLORS`, `DEFAULT_INTERVALS` per mode.
- `brand/` — icons (`icon.png` 256, `icon@2x.png` 512, + `dark_` variants).

## Development

- Pure tests: `.venv/bin/python -m pytest` (`pytest.ini` limits to `tests/`;
  `conftest.py` loads `const`/`encoding`/`morse`/`player` without HA).
- HA tests: `.venv-ha/bin/python -m pytest tests_ha` (real HA core via
  `pytest-homeassistant-custom-component`; lamps are `input_boolean`s).
  `tests_ha/conftest.py` must import our `custom_components` **before** the
  plugin, or HA finds the plugin's own `testing_config` package and reports
  "Integration not found".
- Bump `manifest.json` `version` for releases (HACS updates).

## Conventions

- Keep `encoding.py` and `player.py` free of HA imports.
- Update `tests/` and this guide when behavior changes.
