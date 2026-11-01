# Graphite 49: SysEx-Protokoll (Referenz)

Quelle: reverse-engineertes Protokoll aus dem GitHub-Projekt
`alxwk/samson_sysex` (<https://github.com/alxwk/samson_sysex>), abgerufen am
01.11.2026. Bezieht sich auf **Firmware 1.42 ("Version 1")**. Geräte mit der
"Version 2"-Firmware (anderes LCD) können abweichen — **vor allem zuerst die
Firmware-Version am Gerät prüfen** (beide TRANSPOSE-Tasten beim Einschalten
halten).

Damit lässt sich das Graphite **vom Rechner aus per USB programmieren** — ohne
Ghidra. Ghidra wäre nur nötig, falls die Version-2-Firmware anders ist und man
die Unterschiede aus dem offiziellen Editor-Binary ableiten müsste.

## Zwei Wege, dasselbe zu erreichen

1. **Offizieller Graphite Editor** (Windows V1.92, Mac v1.3.0) von samsontech.com.
   Fertiges GUI, lädt Presets herunter/hoch. Sicherster Weg. (Der Editor kann
   systemweite Parameter wie Kurven/Aftertouch NICHT exportieren — die gehen nur
   per SysEx, siehe Register.)
2. **Direkt per SysEx** mit dem Skript `graphite_sysex.py` hier im Ordner.
   Mächtiger (auch Register), aber teils rekonstruiert — immer per Rücklesen
   prüfen.

## MIDI-Ports

- Anfragen gehen an den Port **`:1`** ("In Port B" im Handbuch).
- Antworten kommen vom Port **`:4`** ("Out Port 5").

## Framing

Jede Nachricht: `F0 ... F7`. Zwei Hersteller-IDs:
- **Mackie** `00 00 66` — nur für die Geräte-ID-Abfrage.
- **Arturia** `00 20 6b` — für alles andere (lesen, schreiben, speichern).

## Nachrichten

### Geräte-ID abfragen
```
Senden:   F0 00 00 66 14 1A 00 F7
Antwort:  F0 00 00 66 14 1B 58 59 5A 74 13 2C 64 F7
```

### Preset lesen ("Get Settings")
```
Senden:   F0 00 20 6B 02 05 nn 00 F7
          nn = Preset-Nr. (0-basiert; 7F = aktuelles Preset)
```
Antwort pro Bedienelement (Typ 1):
```
F0 n1 n2 rr rr cc pp ff F7
  n1 n2 = Hardware-Control-ID (siehe Tabelle unten)
  rr rr = zugewiesener CC# (MSB/LSB; beim LESEN sind virtuelle CCs um +1
          verschoben, daher Skript: cc-1 wenn >127)
  cc    = Kanal (10 = aktueller)
  pp    = Port (05 = aktueller)
  ff    = Flags
```
Flags: Encoder Bit0: 0=Absolut(0..127), 1=Relativ(links=65,rechts=1).
Taster/Pads Bit0: 0=Controller, 1=Note. Bit1: 0=Toggle, 1=Momentary.

Antwort für systemweite Register (Typ 2): `F0 04 rr nn .. .. F7`
(rr = Startregister, nn = Anzahl; siehe Register-Tabelle).

### Ein Bedienelement setzen
```
Senden:   F0 00 20 6B 02 op  n1 n2  v1 v2  F7
  op: 01=CC# setzen  02=Kanal setzen  03=Port setzen  04=Flags setzen
  n1 n2 = Hardware-Control-ID
  v1 v2 = Wert (14-bit, MSB/LSB)
```
Wichtig: Beim SCHREIBEN wird der CC-Wert direkt aus den MSB/LSB-Spalten der
CC-Tabelle genommen, NICHT um +1 verschoben. Beispiel Master Volume (CC 152):
Lesen liefert `01 19`, Schreiben erwartet `01 18`.
- CC 0..127:  MSB=00, LSB=CC
- CC 128..171: MSB=01, LSB=CC-128

### Systemweites Register setzen
```
Senden:   F0 00 20 6B 02 06 nn vv vv F7   (Wert vv ins Register nn)
```

### Aktuelle Einstellungen in ein Preset speichern
```
Senden:   F0 00 20 6B 02 07 nn 00 F7      (nn = Ziel-Preset, 0-basiert)
```

## Hardware-Control-IDs (dezimal = MSB*128 + LSB)

Schieber: S1b1=2 S2b1=1 S3b1=0 S4b1=3 S5b1=5 S6b1=7 S7b1=6 S8b1=4 · S9=10
          S1b2=20 S2b2=21 S3b2=22 S4b2=23 S5b2=24 S6b2=25 S7b2=26 S8b2=27
Encoder:  E1b1=131 E2b1=135 E3b1=130 E4b1=134 E5b1=129 E6b1=133 E7b1=128 E8b1=132
          E1b2=136 E2b2=137 E3b2=138 E4b2=139 E5b2=140 E6b2=141 E7b2=142 E8b2=143
Taster:   F1=295 F2=294 F3=293 F4=292 F5=291 F6=290 F7=289 F8=288
          F9=280 F10=281 F11=282 F12=283 F13=284 F14=285 F15=286 F16=287
Transport: REW=299 FF=300 STOP=301 PLAY=302 REC=303
Pads:     P1=304 P2=305 P3=306 P4=307 (Bank A) · P5=308 P6=309 P7=310 P8=311 (Bank B)

(Die Schieber haben zwei Bänke, die Encoder auch. Die Pads liegen in zwei
Bänken A/B zu je 4. Also 8 Pads gesamt, nicht 4.)

## CC-Nummern (Auszug)

Standard-MIDI 0..127 wie üblich (1=Modulation, 7=Volume, 10=Pan, 11=Expression,
64=Sustain). Darüber "virtuelle" CCs, die das Gerät andere MIDI-Nachrichten
senden lassen:
- 144 = Channel Pressure (Aftertouch)
- 145 = Program Change
- 152 = Master Volume (SysEx) · 153 = Master Balance
- 159..170 = MMC (Stop/Play/… — aber fehlerhaft, siehe quirks)
- 171 = Pitch Bend

Die vollständige Tabelle (alle 0..171, mit MSB/LSB und Read-Shift) steht in der
Quelle unter `cc_table.md`. MMC ist durch einen Firmware-Bug um -1 verschoben
(MMC RESET nicht erreichbar).

## Register (systemweite / Zonen-Einstellungen)

Wichtige Register (0-basiert): 00=Preset# · 12=Pedal CC# · 14=aktive Zonen-Maske
· 15..18=Zonen-Ports · 19..1C=Zonen-Kanäle · 1D..20=Zonen-Oktave (04=0) ·
21..24=Zonen-Transpose (0C=0) · 2D..34=Zonen-Tastaturbereiche. Volle Liste in der
Quelle unter `registers.md`.

## Remote-Control-Presets (Nr. 02..16)

Vorbelegt für DAWs (Logic, Pro Tools, Cubase, Ableton, …), meist Mackie Control,
Pro Tools per (unvollständigem) HUI. Für GarageBand auf dem iPad **irrelevant**,
weil GarageBand weder Mackie noch HUI versteht. Details in der Quelle unter
`rc_presets.md`.

## Macken (Firmware 1.42)

- Kurven und Aftertouch sind **systemweit**, gehören zu keinem Preset, und
  überleben "Preset Reset". Nicht über den Editor exportierbar, teils per SysEx.
- Aftertouch "Off" (172) wird nicht im NVRAM gespeichert und fällt nach dem
  Ausschalten auf 144 zurück. Empfehlung: auf 3 (ungenutzt) setzen.
- Der Power-Schalter schaltet nicht hart ab, sondern fährt sauber herunter und
  **speichert dabei**. Zieht man stattdessen das Kabel, gehen Änderungen
  verloren. Also immer ordentlich über den Schalter ausschalten.
- Bank-Wechsel: nach Bank-Änderung muss ENTER **zweimal** gedrückt werden.

## Service-Modi (Tasten beim Einschalten halten)

- beide OCTAVE → Init (Werksreset?)
- beide TRANSPOSE → zeigt Firmware-Version / Update-Modus
- OCTAVE- & TRANSPOSE- → Test-Modus (alle Bedienelemente prüfen)

**Achtung:** Diese Modi können alle Einstellungen auf Werk zurücksetzen. Vorher
eigene User-Presets per SysEx/Editor auf den Rechner sichern.
