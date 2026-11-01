# Graphite 49: Reverse Engineering (rea + Ghidra)

Ziel: Herausfinden, ob und wie sich das Graphite 49 per USB vom Rechner aus
programmieren lässt. Samson liefert kein Editor-Tool und keine dokumentierte
SysEx-Schnittstelle, also muss das Protokoll selbst ermittelt werden. Es geht um
eigene Hardware zum Zweck der Interoperabilität.

## Was wahrscheinlich geht und was nicht

Das Graphite ist ein class-compliant USB-MIDI-Gerät. Die Einstellungen (Presets,
CC-Belegung) liegen im Flash des internen Mikrocontrollers. Zwei Fragen:

1. **Gibt es einen USB-Weg, Presets zu schreiben?** Möglich über SysEx oder ein
   Vendor-spezifisches USB-Interface. Wenn ja, lässt sich ein eigener Editor bauen.
2. **Lässt sich die Firmware lesen/ändern?** Nur sinnvoll, wenn 1 nichts ergibt.
   Deutlich aufwendiger und meist nicht nötig.

Realistische Erwartung: Entweder das Gerät nimmt SysEx-Dumps entgegen (dann ist
ein Editor machbar), oder es gibt gar keinen Schreibweg per USB (dann bleibt nur
die Bedienung am Gerät, und Ghidra hilft nicht weiter).

## Reihenfolge (billigste zuerst)

### Stufe 1 — MIDI/SysEx beobachten (kein Ghidra nötig)
- Mit `midi_monitor.py` (siehe README) auf SysEx achten (`F0 ... F7`).
  Beim Preset-Wechsel, Speichern und Umschalten am Gerät mitschneiden.
- Sendet das Gerät beim Speichern selbst SysEx? Dann ist das Format direkt sichtbar.
- Universal SysEx Identity Request senden: `F0 7E 7F 06 01 F7`. Antwort notieren
  (Hersteller-ID, Family, Member, Version). Samson-Hersteller-ID identifizieren.
- Test: einen SysEx-Block zurücksenden und sehen, ob sich ein Preset ändert.

### Stufe 2 — USB-Verkehr aufzeichnen
- Falls doch irgendeine Samson/Windows-Editor- oder Firmware-Update-Software
  existiert: diese in einer VM starten und den USB-Verkehr mit **Wireshark +
  USBPcap** (Windows) bzw. **usbmon/Wireshark** (Linux) mitschneiden, während man
  im Editor ein Preset ändert. Das zeigt die echten Schreibbefehle, ohne
  Disassembly.
- Ohne Editor-Software entfällt diese Stufe, weil es nichts zu beobachten gibt.

### Stufe 3 — Ghidra: Updater/Editor disassemblieren
- Nur wenn es ein Windows-/Mac-Binary von Samson gibt (Editor oder
  Firmware-Updater). Das ist der Punkt, an dem Ghidra greift:
  1. Binary in Ghidra importieren, auto-analyze.
  2. Nach USB/MIDI-Strings suchen (`SysEx`, `F0`, `winmm`, `midiOutLongMsg`,
     `hid`, `libusb`, Preset-Dateiendungen).
  3. Von diesen API-Aufrufen rückwärts die Funktionen finden, die den
     Preset-Puffer zusammenbauen. Daraus das Byte-Layout eines Presets ableiten.
  4. Ergebnis: Dokumentation des SysEx-/USB-Formats, dann eigener Python-Editor.

### Stufe 4 — Firmware vom Chip (letzte Option)
- Nur wenn kein USB-Schreibweg existiert und das wirklich nötig ist.
- MCU identifizieren (Gehäuse öffnen, Chip-Aufdruck lesen). Wenn Lese-Schutz aus:
  per SWD/JTAG/ISP auslesen, sonst nicht praktikabel.
- Firmware-Dump in Ghidra mit passendem Prozessor laden (Cortex-M / 8051 / o.ä.),
  SysEx-Parser suchen, Protokoll ableiten. Firmware verändern wird hier
  ausdrücklich NICHT empfohlen (Gerät leicht unbrauchbar).

## Werkzeuge

- `midi_monitor.py` (im Repo) — SysEx mitschneiden, Stufe 1.
- Wireshark + USBPcap/usbmon — Stufe 2.
- Ghidra — Stufe 3 und 4.
- Für einen späteren eigenen Editor: Python `mido` zum Senden von SysEx.

## Nächster konkreter Schritt (in der USB-Sitzung)

1. Prüfen, ob überhaupt irgendeine Samson-Software für das Graphite existiert
   (sonst entfallen Stufe 2 und 3, und Ghidra bringt nichts).
2. Stufe 1 durchführen: Identity Request senden, Antwort und jeglichen SysEx beim
   Speichern mitschneiden. Das entscheidet, ob ein Schreibweg überhaupt existiert.
