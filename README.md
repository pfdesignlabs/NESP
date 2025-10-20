# NESP Hardware (Atopile Workspace)

Deze repository bevat de Atopile-definitie van de NESP-hardware. In plaats van losse handmatige scripts gebruiken we nu één Atopile-project (`nesp-ato/`) dat alle componenten, verbindingen en CAD-referenties beschrijft. Via Atopile genereer je rechtstreeks de KiCad6‐bestanden (symbolen, footprints, netlist) en downstream export (Gerbers/STEP) wanneer gewenst.

## Structuur

```
nesp-ato/
  ├─ ato.toml                  # projectmetadata en build-target
  ├─ libs/                     # herbruikbare atoms en componentblokken
  │   ├─ passives.ato          # generieke R/C/L/ESD atoms
  │   ├─ power.ato             # USB-C front-end, charger en buckregulator
  │   ├─ mcu_esp32s3_wroom1.ato
  │   ├─ display_ili9341_sd.ato
  │   ├─ audio_max98357a.ato
  │   ├─ input_buttons.ato
  │   └─ indicators.ato
  ├─ cad/                      # samengevoegde vendor symbolen/footprints/3D
  │   ├─ nesp_symbols.kicad_sym
  │   ├─ footprints.pretty/
  │   └─ 3d/
  └─ nesp_top.ato              # top-level design dat alle blokken verbindt
```

De vendor ZIPs/datasheets zijn nog steeds te vinden onder `electronics/components/` zodat je KiCad-modellen en datasheets snel terugvindt, maar de flow draait nu volledig via Atopile.

## Atopile gebruiken

1. **Afhankelijkheden installeren**

   ```bash
   pip install atopile
   ```

   (of gebruik je bestaande Atopile‐omgeving, minimaal versie 0.12.)

2. **Build uitvoeren**

   ```bash
   cd /Users/pfdesignlabs/Documents/Projects/NESP
   ato build --entry nesp-ato/nesp_top.ato --target kicad6
   ```

   Dit genereert in `build/kicad/nesp_top/` de KiCad6-projectbestanden inclusief:
   - Samengevoegde symbol library & footprint tables
   - Netlist en schema
   - Mapping naar de gebruikte 3D-modellen

   Kopieer aansluitend de map `nesp-ato/cad/` naar `build/kicad/nesp_top/cad/`
   (of voeg deze paden toe aan de KiCad library tables) zodat alle vendor
   symbolen/footprints/3D-bestanden beschikbaar zijn in het gegenereerde project.

   De atoms verwijzen naar de bibliotheken:

   - `NESP_Symbols` → `cad/nesp_symbols.kicad_sym`
   - `NESP_Footprints` → `cad/footprints.pretty`
   - 3D-modellen → `${KIPRJMOD}/cad/3d/*.step`

3. **KiCad openen**

   Open het gegenereerde `.kicad_pro` bestand uit de build-folder of importeer de gegenereerde netlist in een nieuw project.

## Componentblokken

- **PowerTree** – USB-C front-end (ESD, polyfuse, TVS), BQ24074 charger, MPM3610 buck (3V3), JST-PH batterijconnector, CC-pulldowns, RC enable, bulkcaps.
- **MCU_ESP32S3** – ESP32-S3-WROOM-1 module, USB D+/D-, gedeelde SPI voor TFT + SD, I²S voor audio, button-GPIO’s, LED-signalen.
- **DisplayBlock** – 3.2” ILI9341 TFT met gedeelde SD, serieweerstanden en pull-ups, backlight drive.
- **AudioBlock** – MAX98357A I²S class-D amp, Zobel netwerk, bulkcaps, speakerklemmen.
- **Buttons** – 10+ tact switches met serie-weerstanden en ESD arrays.
- **Indicators** – Power/user LEDs en charger STAT/PG indicatoren.

De top-level `nesp_top.ato` koppelt deze blokken via nette netnamen zodat Atopile de volledige netlist en PCB‐Libraries kan genereren.

## Opschoning t.o.v. vorige setup

- De oude Nexar/NESP KiCad generator scripts zijn verwijderd (`tools/`, `electronics/scripts/`, `libs/`, `hardware/schematics/`).
- Manifestgedreven downloads zijn optioneel; met Atopile bepaal je symbolen/footprints via de atoms.
- README en repo zijn opgeschoond zodat het duidelijk is dat Atopile de enige bron van waarheid is.

## Vervolg/uitbreiding

- BQ24074 STAT/PG nets zijn beschikbaar voor extra indicatorfunctionaliteit.
- Voor detailafstemming kun je per blok simpelweg de betreffende `libs/*.ato` aanpassen.
- Voor Gerbers/STEP kun je na het genereren van de KiCad6-output de standaard `kicad-cli` flow gebruiken.

Veel succes met het verder uitbouwen van de NESP-hardware! 🎮🔋🧩
