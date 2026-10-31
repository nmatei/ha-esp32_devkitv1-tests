# ESP32 DevKit V1 + Home Assistant (ESPHome)

Documentația completă a proiectului pentru configurarea și utilizarea ESP32 DevKit V1 cu Home Assistant prin ESPHome.
Placă: **ESP32 DevKit V1** (`esp32doit-devkit-v1`), integrare prin **ESPHome**.

---

## 1. Prezentare generală

- 5 LED-uri colorate (galben, roșu, albastru, verde, alb) pe breadboard, comandate din Home Assistant prin WiFi
- LED-ul albastru de pe placă (GPIO2) ca al șaselea LED controlabil
- Senzor de lumină **HW-486** (fotorezistor, analogic)
- Senzor de temperatură **HW-498** (termistor NTC, analogic, convertit în °C)
- Buton fizic **HW-483** cu toggle inteligent (start/stop în funcție de stare)
- Buzzer activ **HW-512** (on/off) și buzzer pasiv **HW-508** (melodii RTTTL)
- Dashboard custom cu `button-card` + `card_mod`

### Puncte cheie învățate

- **GPIO-urile ESP32 scot 3.3V, nu 5V.** LED-urile cu rezistențe calculate pentru 5V luminează mai slab la 3.3V, dar funcționează. Nu conecta niciodată 5V la un pin GPIO — pinii nu sunt toleranți la 5V.
- Pinul **VIN** dă ~5V (de la USB), dar e alimentare fixă, necontrolabilă din software.
- Notația de pe placă: **D16 = GPIO16** etc. GPIO16/17 apar pe placă drept **RX2/TX2**.
- Pini de evitat ca ieșiri: GPIO0, 2*, 12, 15 (boot/strapping), GPIO34-39 (doar intrare). (*GPIO2 e ok pentru LED-ul onboard.)
- Pentru citiri analogice cu WiFi activ: **doar ADC1** (GPIO32-39). ADC2 nu funcționează cu WiFi pornit.
- Senzorii se alimentează din **3V3**, nu din VIN — altfel ieșirea analogică poate depăși 3.3V și arde ADC-ul.
- LED-ul roșu de pe placă e LED-ul de power, legat în hardware — nu se poate stinge din software.

---

## 2. Instalare ESPHome

Două componente, cu roluri diferite:

| Componentă | Rol |
|---|---|
| **ESPHome Device Builder** (app, fost add-on) | Atelierul: editezi YAML, compilezi, instalezi firmware (OTA prin WiFi) |
| **ESPHome** (integrarea) | Puntea: HA vorbește cu placa și afișează entitățile |

### 2.1 ESPHome Device Builder (app)

Link direct (deschide pagina app-ului în Home Assistant-ul tău prin My Home Assistant; la prima folosire cere adresa instanței, ex. `http://homeassistant.local:8123`):
[Instalează ESPHome Device Builder](https://my.home-assistant.io/redirect/supervisor_addon/?addon=5c53de3b_esphome&repository_url=https%3A%2F%2Fgithub.com%2Fesphome%2Fhome-assistant-addon)

Sau manual:

1. Settings → Apps → Install app → **ESPHome Device Builder** → Install → Start → Show in sidebar.
2. Prima flash-are prin USB: **https://web.esphome.io** (Chrome, nu Safari) sau din Builder → New Device → "Plug into this computer".
3. Dacă placa a fost instalată prin web.esphome.io, în Builder apare ca *discovered* → **ADOPT** → se creează configurația editabilă.
4. Orice modificare de YAML: **SAVE + INSTALL → Wirelessly**. Save doar salvează fișierul; Install compilează și trimite firmware-ul pe placă.

App-urile există doar pe Home Assistant OS / Supervised. Pe HA Container/Core, Device Builder rulează separat (ex. Docker `ghcr.io/esphome/esphome`, port 6052).

### 2.2 ESPHome (integrarea)

Link direct (pornește adăugarea integrării):
[Adaugă integrarea ESPHome](https://my.home-assistant.io/redirect/config_flow_start/?domain=esphome)

De obicei HA găsește singur placa după prima flash-are (mDNS, aceeași rețea):

1. Settings → Devices & services → secțiunea **Discovered** → **ESPHome** (numele plăcii) → **Add** / Configure → Submit.
2. Dacă cere **encryption key**: e cheia din YAML-ul plăcii, `api:` → `encryption:` → `key:` (în Builder → placa → Edit).
3. Alege zona (Area) → Finish. Entitățile (LED-uri, senzori, buton, buzzer) apar sub dispozitiv.

Dacă placa nu apare la Discovered:

1. Settings → Devices & services → **Add integration** → caută **ESPHome**.
2. Host: IP-ul plăcii (din router sau din logurile din Builder) sau `<nume>.local`; Port: `6053`.
3. Encryption key ca mai sus → Submit.

După un Install wireless, integrarea preia automat entitățile noi la repornirea plăcii. Ca device-ul să poată apela acțiuni HA (`homeassistant.action`), activează în integrare: Configure → **Allow the device to perform Home Assistant actions**.

Notă: device-ul a rămas înregistrat în API ca `esphome-web-3053a0`, deci serviciile expuse au prefixul `esphome.esphome_web_3053a0_...` (chiar dacă entitățile au prefixul "office"). Redenumirea (`name:` din secțiunea `esphome:`) ar rupe entitățile și automatizările existente — nu merită.

---

## 3. Cablare

### LED-uri (toate pe rândul din dreapta)

| Pin placă | GPIO | LED |
|---|---|---|
| D23 | GPIO23 | galben |
| D22 | GPIO22 | roșu |
| D21 | GPIO21 | albastru |
| D19 | GPIO19 | verde |
| D18 | GPIO18 | alb |
| (onboard) | GPIO2 | LED albastru placă |

Circuit per LED: **GPIO → rezistență → anod (picior lung) → catod (picior scurt) → GND**.
Toate catozii pe linia comună (−) a breadboard-ului, legată la un GND al plăcii.
Polaritate: picior lung = + (spre pin), picior scurt = − (spre GND). Invers conectat nu se strică, doar nu luminează.

LED-urile RGB **HW-479** și **HW-478** sunt legate în paralel cu LED-urile roșu, verde și albastru: `R` → D22, `G` → D19, `B` → D21, `−` → GND. Se aprind odată cu acestea, fără configurație ESPHome proprie.

### Senzori și module (alimentare din 3V3 + GND, colțul dreapta-jos al plăcii)

| Modul | Ce e | Pin S | Note |
|---|---|---|---|
| HW-486 | Senzor lumină (fotorezistor) | **D34** (GPIO34) | 3 pini: S / mijloc=VCC / − |
| HW-498 | Senzor temperatură (termistor NTC) | **D35** (GPIO35) | idem |
| HW-483 | Buton apăsabil | **D33** (GPIO33) | pullup intern + inverted |
| HW-512 | Buzzer activ (sună singur la ON) | **D25** (GPIO25) | S + GND |
| HW-508 | Buzzer pasiv (PWM/melodii) | **D26** (GPIO26) | S + GND |

Diferența buzzere: conectat direct la 3V3+GND, **activul sună continuu**, pasivul tace (sau un "tic").

### Verificare cu multimetrul (DC, sondă neagră pe GND)

| Punct de măsură | ON | OFF |
|---|---|---|
| Pin GPIO (ex. D23) | ~3.3V | ~0V |
| Anod LED (după rezistență) | ~1.8-2.2V (roșu/galben), ~2.7-3.2V (albastru/verde/alb) | 0V |

Curent prin LED = tensiunea pe rezistență ÷ valoarea rezistenței.
La LED-urile albastre/albe tensiunea de deschidere (~3V) e aproape de 3.3V → luminează mai slab; e normal, nu e defect.

---

## 4. Configurația ESPHome completă (YAML)

> Secțiunile `esphome:`, `esp32:`, `wifi:`, `api:` (cheia de criptare), `ota:` sunt cele generate la ADOPT — mai jos e doar ce s-a adăugat peste ele. Indentarea contează: `output:`, `light:` etc. încep de la marginea din stânga.

```yaml
# ---------- API: serviciu pentru buzzer-ul pasiv ----------
api:
  # ... encryption etc. generate automat ...
  actions:
    - action: play_rtttl
      variables:
        song_str: string
      then:
        - rtttl.play: !lambda "return song_str;"

# ---------- Iesiri ----------
output:
  - platform: gpio
    pin: GPIO23
    id: out_galben
  - platform: gpio
    pin: GPIO22
    id: out_rosu
  - platform: gpio
    pin: GPIO21
    id: out_albastru
  - platform: gpio
    pin: GPIO19
    id: out_verde
  - platform: gpio
    pin: GPIO18
    id: out_alb
  - platform: gpio
    pin: GPIO2
    id: out_onboard
  # buzzer pasiv (PWM)
  - platform: ledc
    pin: GPIO26
    id: buzzer_pasiv

# ---------- LED-uri ----------
light:
  - platform: binary
    name: "LED Galben"
    output: out_galben
  - platform: binary
    name: "LED Rosu"
    output: out_rosu
  - platform: binary
    name: "LED Albastru"
    output: out_albastru
  - platform: binary
    name: "LED Verde"
    output: out_verde
  - platform: binary
    name: "LED Alb"
    output: out_alb
  - platform: binary
    name: "LED Placa"
    output: out_onboard

# ---------- Senzori analogici ----------
sensor:
  # Lumina
  - platform: adc
    pin: GPIO34
    name: "Senzor Lumina (HW-486)"
    attenuation: 12db
    update_interval: 2s

  # Temperatura - lant de 3 pasi: volti -> rezistenta -> grade
  - platform: adc
    pin: GPIO35
    id: temp_raw
    attenuation: 12db
    update_interval: 2s
    internal: true
  - platform: resistance
    sensor: temp_raw
    configuration: DOWNSTREAM   # daca valorile sunt absurde/inverse: UPSTREAM
    resistor: 10kOhm
    reference_voltage: 3.3V
    id: temp_resistance
    internal: true
  - platform: ntc
    sensor: temp_resistance
    calibration:
      b_constant: 3950
      reference_temperature: 25°C
      reference_resistance: 10kOhm
    name: "Temperatura (HW-498)"

# ---------- Buton fizic ----------
binary_sensor:
  - platform: gpio
    pin:
      number: GPIO33
      mode:
        input: true
        pullup: true
      inverted: true
    name: "Buton (HW-483)"
    filters:
      - delayed_on: 10ms    # debounce
      - delayed_off: 10ms

# ---------- Buzzer activ ----------
switch:
  - platform: gpio
    pin: GPIO25
    name: "Buzzer (HW-512)"
    icon: "mdi:bullhorn"

# ---------- Buzzer pasiv: player de melodii ----------
rtttl:
  output: buzzer_pasiv
```

Note:

- `attenuation: 12db` extinde domeniul ADC la 0-3.3V (fără el saturează la ~1.1V).
- `internal: true` ascunde senzorii intermediari (volți, ohmi) din HA — ajunge doar temperatura în °C.
- `inverted: true` la buton: modulul trage S la GND la apăsare; inversat, apăsat = ON.
- Dacă temperatura e deplasată cu 2-5°C e normal pentru termistoare ieftine (ajustabil din `b_constant` sau filtru `offset`).
- Alternativă pentru GPIO2: `status_led: { pin: GPIO2 }` ca indicator de conexiune (clipește când nu e conectat la WiFi/HA) — secțiune separată, fără `output:` pe GPIO2.
- Test rapid buzzer pasiv: Developer Tools → Actions → `esphome.esphome_web_3053a0_play_rtttl` → `song_str: "beep:d=16,o=5,b=100:c6"`.

---

## 5. Dashboard (Lovelace)

Necesită: **button-card** și **card_mod** (HACS). Entitățile au prefixul `office_esphome_esp32_devkitv1`.

Structura: o casetă cu chenar (mod-card) cu cele 5 becuri pe un rând (grid cu 5 coloane, icon 22px, înălțime 40px), plus o a doua casetă cu LED-ul plăcii pe 1/5 din lățime și senzorul de progres întins pe 3 coloane (`grid-column: span 3`).

```yaml
type: grid
square: false
columns: 1
cards:
  - type: custom:mod-card
    card_mod:
      style: |
        ha-card {
          background: var(--ha-card-background, var(--card-background-color));
          border-radius: var(--ha-card-border-radius, 12px);
          box-shadow: var(--ha-card-box-shadow, none);
          border: 1px solid var(--divider-color);
          padding: 8px;
        }
    card:
      type: grid
      columns: 5
      square: false
      cards:
        - type: custom:button-card
          entity: light.office_esphome_esp32_devkitv1_led_galben
          show_name: false
          icon: mdi:lightbulb
          tap_action:
            action: toggle
          styles:
            card:
              - background: none
              - box-shadow: none
              - border: none
              - height: 40px
            icon:
              - width: 22px
              - color: rgba(255, 200, 0, 0.3)
          state:
            - value: "on"
              styles:
                icon:
                  - color: rgb(255, 200, 0)
                  - filter: drop-shadow(0 0 8px rgb(255, 200, 0))
        - type: custom:button-card
          entity: light.office_esphome_esp32_devkitv1_led_rosu
          show_name: false
          icon: mdi:lightbulb
          tap_action:
            action: toggle
          styles:
            card:
              - background: none
              - box-shadow: none
              - border: none
              - height: 40px
            icon:
              - width: 22px
              - color: rgba(244, 67, 54, 0.3)
          state:
            - value: "on"
              styles:
                icon:
                  - color: rgb(244, 67, 54)
                  - filter: drop-shadow(0 0 8px rgb(244, 67, 54))
        - type: custom:button-card
          entity: light.office_esphome_esp32_devkitv1_led_albastru
          show_name: false
          icon: mdi:lightbulb
          tap_action:
            action: toggle
          styles:
            card:
              - background: none
              - box-shadow: none
              - border: none
              - height: 40px
            icon:
              - width: 22px
              - color: rgba(33, 150, 243, 0.3)
          state:
            - value: "on"
              styles:
                icon:
                  - color: rgb(33, 150, 243)
                  - filter: drop-shadow(0 0 8px rgb(33, 150, 243))
        - type: custom:button-card
          entity: light.office_esphome_esp32_devkitv1_led_verde
          show_name: false
          icon: mdi:lightbulb
          tap_action:
            action: toggle
          styles:
            card:
              - background: none
              - box-shadow: none
              - border: none
              - height: 40px
            icon:
              - width: 22px
              - color: rgba(76, 175, 80, 0.3)
          state:
            - value: "on"
              styles:
                icon:
                  - color: rgb(76, 175, 80)
                  - filter: drop-shadow(0 0 8px rgb(76, 175, 80))
        - type: custom:button-card
          entity: light.office_esphome_esp32_devkitv1_led_alb
          show_name: false
          icon: mdi:lightbulb
          tap_action:
            action: toggle
          styles:
            card:
              - background: none
              - box-shadow: none
              - border: none
              - height: 40px
            icon:
              - width: 22px
              - color: rgba(200, 200, 200, 0.35)
          state:
            - value: "on"
              styles:
                icon:
                  - color: rgb(255, 255, 255)
                  - filter: drop-shadow(0 0 8px rgba(255, 255, 255, 0.9))
  - type: custom:mod-card
    card_mod:
      style: |
        ha-card {
          background: var(--ha-card-background, var(--card-background-color));
          border-radius: var(--ha-card-border-radius, 12px);
          box-shadow: var(--ha-card-box-shadow, none);
          border: 1px solid var(--divider-color);
          padding: 8px;
        }
    card:
      type: grid
      columns: 5
      square: false
      cards:
        - type: custom:button-card
          entity: light.office_esphome_esp32_devkitv1_led_placa
          show_name: false
          icon: mdi:lightbulb
          tap_action:
            action: toggle
          styles:
            card:
              - background: none
              - box-shadow: none
              - border: none
              - height: 40px
            icon:
              - width: 22px
              - color: rgba(0, 150, 255, 0.3)
          state:
            - value: "on"
              styles:
                icon:
                  - color: rgb(0, 150, 255)
                  - filter: drop-shadow(0 0 8px rgb(0, 150, 255))
        - type: custom:button-card
          entity: sensor.esp32_devkitv1_progres
          show_name: false
          show_icon: false
          show_state: true
          tap_action:
            action: more-info
          card_mod:
            style: |
              :host {
                grid-column: span 3;
              }
          styles:
            card:
              - background: none
              - box-shadow: none
              - border: none
              - height: 40px
            state:
              - font-size: 13px
              - color: var(--secondary-text-color)
```

Lecții de layout (ce NU a mers):

- `width` + `margin` + `aspect_ratio` pe button-card → cardurile se restrâng la zero, totul pare gol.
- `square: true` pe grid → celule pătrate uriașe, spațiu gol imens sub iconuri.
- `button-card` singur direct sub `mod-card` cu `height` fix → uneori se randează cu înălțime zero; soluția: un `grid` între ele.
- Soluția stabilă: fără `aspect_ratio`/`square`, înălțime explicită pe card (`height: 40px`), mărimea vizuală din `icon: width`.

---

## 6. Automatizare: buton fizic → toggle start/stop cu feedback sonor

Apăsarea butonului HW-483: dacă `sensor.esp32_devkitv1_progres` e `oprit` → Start (+ 3 note ascendente), altfel → Stop (+ 3 note descendente).

```yaml
alias: Toggle LEDs
description: Toggle LEDs
triggers:
  - trigger: state
    entity_id: binary_sensor.office_esphome_esp32_devkitv1_buton_hw_483
    to: "on"
actions:
  - if:
      - condition: state
        entity_id: sensor.esp32_devkitv1_progres
        state: oprit
    then:
      - action: esphome.esphome_web_3053a0_play_rtttl
        data:
          song_str: "start:d=16,o=5,b=140:c6,e6,g6"
      - action: button.press
        target:
          entity_id: button.esp32_devkitv1_start
    else:
      - action: esphome.esphome_web_3053a0_play_rtttl
        data:
          song_str: "stop:d=16,o=5,b=140:g6,e6,c6"
      - action: button.press
        target:
          entity_id: button.esp32_devkitv1_stop
mode: single
```

Capcane evitate:

- Trigger fără `to: "on"` s-ar declanșa și la eliberarea butonului (dublă execuție).
- Logica if/else se face în `actions:` (cu `if`/`choose`), nu în `conditions:` (alea doar blochează).
- Entitățile `button.*` nu au stări utile — nu pot fi folosite în condiții.
- Valoarea `oprit` trebuie să corespundă **literal** cu ce arată senzorul în Developer Tools → States.

---

## 7. Depanare — rezumat

| Simptom | Cauză probabilă |
|---|---|
| LED nu luminează, pinul arată 3.3V | LED invers (rotește-l 180°) sau contact slab în breadboard |
| LED albastru/alb luminează slab | Normal la 3.3V: Vf (~3V) aproape de tensiunea pinului |
| Install wireless eșuează cu eroare de autentificare | Cheie/parolă OTA diferită în firmware-ul vechi → o flash-are prin USB, apoi OTA merge |
| Senzor cu valori haotice/fixe | Lipitură rece pe modul; verifică lipiturile de pe spate |
| Temperatura absurdă sau inversată | Schimbă `DOWNSTREAM` ↔ `UPSTREAM` la platforma `resistance` |
| Binary sensor inversat (ON când e liber) | `inverted: true` pe pin |
| Icon nou nu apare | Override local în HA (golește câmpul Icon al entității), Install nefăcut, cache browser (Cmd+Shift+R), sau typo în numele `mdi:` |
| Serviciul rtttl nu e găsit | Numele real e după numele API al device-ului: `esphome.esphome_web_3053a0_play_rtttl` (verifică în Developer Tools → Actions) |

## 8. Idei de continuare

- LED-uri cu intensitate variabilă: `output: platform: ledc` + `light: platform: monochromatic` (PWM).
- Alimentare reală la 5V pentru LED-uri: ULN2003 sau tranzistori NPN (2N2222 + 1kΩ pe bază), comutând linia VIN.
- Calibrare senzor de lumină în procente: filtru `calibrate_linear` pe baza valorilor măsurate întuneric/lumină plină.
- Acțiune locală pe buton (merge fără WiFi/HA): `on_press: light.toggle: <id>` direct în ESPHome.
- Alarmă cu buzzerul activ: temperatură peste prag → `switch.turn_on` până la confirmare.
