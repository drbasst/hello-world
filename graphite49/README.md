# Samson Graphite 49 mit GarageBand (iPad): Vorbereitung

Stand: 01.11.2026. Diese Notizen bereiten eine spätere Sitzung vor, in der das Keyboard per USB an einem Computer hängt.

> **Hinweis zur Quellenlage:** Die Handbuch-PDFs ließen sich aus der Cloud-Umgebung nicht abrufen (Netzwerksperre). Alles unten stammt aus Suchergebnis-Auszügen von Handbuch-Kopien und Testberichten. Punkte mit **(prüfen)** sind nicht bestätigt und müssen am Gerät oder im Handbuch nachgesehen werden.

## 1. Das Kernproblem

GarageBand auf dem iPad kann **keine** Hardware-Regler frei zuweisen (kein „MIDI Learn“ für Smart Controls). Laut Berichten reagiert es nur auf:

| MIDI-Befehl | Wirkung in GarageBand iPad | Verlässlichkeit |
|---|---|---|
| Noten und Anschlagstärke | spielt das Instrument | sicher |
| Pitch Bend | Tonhöhe | sicher |
| CC 1 (Modulation) | Modulation, je nach Instrument | sicher |
| CC 64 (Sustain) | Haltepedal | sicher |
| CC 7 (Volume), CC 10 (Pan) | Spur-Lautstärke bzw. Panorama, evtl. nur im Instrument-Modus | unsicher (prüfen) |
| CC 11 (Expression), Aftertouch | teils gemeldet | unsicher (prüfen) |
| Transport, MMC, Mackie/HUI | nicht unterstützt | sicher |

**Folge:** Egal wie das Graphite programmiert wird, die meisten Drehknöpfe und Schieber können in GarageBand nichts steuern. Erreichbar ist nur: Pads spielen Noten, ein Regler als Modulation (CC 1), eventuell ein Schieber als Lautstärke (CC 7).

## 2. Was über das Graphite 49 bekannt ist

- **Bedienelemente:** 49 Tasten, 8 Drehregler (E1 bis E8), 9 Schieber (S1 bis S9), 16 Taster, Transport-Tasten. Die Pads werden je nach Quelle mit 4 oder 8 angegeben (2 Bänke) (prüfen).
- **Programmierung:** Nur am Gerät. Es gibt keinen offiziellen Software-Editor und keine dokumentierte SysEx-Schnittstelle. Per USB kann man also auslesen, was das Gerät sendet, aber nicht von außen umprogrammieren.
- **Presets:** Es gibt 30 Presets:
  - Preset 1 ist das „Graphite“-Grundpreset: Drehregler senden CC 10 (Pan) und Schieber CC 7 (Volume), auf den Kanälen 1 bis 8 (je Regler ein Kanal).
  - Presets 2 bis 10 sind für bestimmte DAWs (Logic, Cubase, Pro Tools usw., Mackie Control oder HUI). Diese Programme gibt es auf dem iPad nicht.
  - Presets 11 bis 30 sind User-Presets. **Nur diese sind frei programmierbar.**
  - Ältere Testberichte nennen eine andere Aufteilung, das hängt vermutlich von der Firmware ab (prüfen).
- **Pads:** Werksseitig spielen die Pads Drum-Noten auf **MIDI-Kanal 10**. Die genauen Notennummern sind unbekannt (prüfen).
- **Setup-Modus:**
  - Starten mit der Taste **SETUP**. Das Keyboard sendet dann kein MIDI, und die ersten 17 Tasten werden zu Funktions- und Zifferntasten (Beschriftung über den Tasten).
  - Je Regler, Pad oder Taster stellt man Port, Kanal, Typ, Modus und Control-Code (CC-Nummer) ein.
  - **ENTER** bestätigt und speichert ins aktuelle Preset.
  - Weitere Funktionen: K.Curve (Anschlagskurve Tastatur), P.Curve (Anschlagskurve Pads), Aftertouch-Zuweisung. Kurve 0 ist „Normal“ (Standard), Kurve 7 ist fest auf Anschlagstärke 64.
- **MIDI-Kanal im Hauptmodus:** Pfeiltaste rechts unter dem Display drücken, bis „Ch“ erscheint, Kanal mit den Data-Tasten einstellen, dann ENTER.
- **Stromversorgung am iPad:** Über den Lightning-USB-Kamera-Adapter bzw. USB-C. Mit Pads und Display kann der Strom knapp werden, dann einen aktiven USB-Hub verwenden.

## 3. Warum die Pads wohl nichts tun (Hypothesen)

1. Auf der aktuellen GarageBand-Spur ist kein Schlagzeug ausgewählt. GarageBand ignoriert den MIDI-Kanal, also spielen Pads auf Kanal 10 einfach Noten auf der gewählten Spur. Bei einem Keyboard-Instrument liegen diese Noten tief und fallen vielleicht nicht auf.
2. Ein DAW-Preset (2 bis 10) ist aktiv, in dem die Pads oder Regler Mackie- oder HUI-Befehle senden. **Erster Test:** Preset 1 laden.
3. Die Pad-Anschlagskurve oder der Pad-Typ ist verstellt.
4. Die Stromversorgung reicht nicht aus.

## 4. Zielbelegung (in einem User-Preset, z. B. **Preset 11**)

| Element | Senden als | Effekt in GarageBand |
|---|---|---|
| Tasten | Noten, Kanal 1 | spielen |
| Pads 1 bis 8 | Noten 36, 38, 42, 46, 49, 51, 45, 48 (Kick, Snare, HH zu, HH offen, Crash, Ride, Tom tief, Tom hoch), Kanal 1 | Schlagzeug auf Drum-Spur |
| Drehregler E1 | CC 1 | Modulation |
| Schieber S9 (Master) | CC 7, Kanal 1 | Lautstärke (prüfen) |
| Drehregler E2 | CC 10, Kanal 1 | Panorama (prüfen) |
| Sustain-Buchse | CC 64 | Haltepedal |
| übrige Regler | ohne Wirkung | (Einschränkung von GarageBand) |

Die Drum-Notennummern folgen dem General-MIDI-Standard, den die GarageBand-Drum-Kits weitgehend nutzen (im Test prüfen).

## 5. Ablauf für die USB-Sitzung

Voraussetzung: Das Graphite hängt per USB an einem Mac oder Linux-Rechner, der über Remote Control mit dieser Claude-Sitzung verbunden ist. Das iPad hilft hier nicht, weil Claude darauf keine Befehle ausführen kann.

1. `python3 -m pip install mido python-rtmidi` installieren.
2. `python3 graphite49/midi_monitor.py --list` zeigt die MIDI-Ports.
3. `python3 graphite49/midi_monitor.py` starten. Dann jeden Regler, Schieber, jedes Pad und jeden Taster einmal bewegen. Das Skript protokolliert Typ, Kanal und Nummer in `graphite49/capture.csv`.
4. Mit dieser Liste wird die echte Ist-Belegung im Abschnitt 2 eingetragen, und die (prüfen)-Punkte werden geklärt.
5. Am Gerät im Setup-Modus Preset 11 nach Abschnitt 4 programmieren (Claude führt Schritt für Schritt). Mit dem Monitor prüfen, ob jedes Element jetzt das Richtige sendet.
6. Am iPad in GarageBand testen.

## 6. Alternative ohne Umprogrammieren (auf dem iPad)

- **MidiFire oder StreamByter** (iOS-Apps von Audeonic) können CC-Befehle in Echtzeit umbiegen, bevor sie in GarageBand ankommen. Die Regeln liegen in `streambyter_rules.txt`. Das ändert aber nichts an der Grenze aus Abschnitt 1.
- **Logic Pro für iPad** (Abo) hat „Learn“ für Controller-Zuweisungen. Damit wären alle Regler nutzbar. **Cubasis** und **AUM** bieten ebenfalls MIDI Learn.

## Quellen

- Samson-Handbuch (Kopien): <https://storage.googleapis.com/samson-production/uploads/documents/Graphite49_OM_5L_v4.pdf>, <https://www.fullcompass.com/common/files/22432-SamsonGraphite49OwnersManual.pdf>, <https://www.manualslib.com/manual/515709/Samson-Graphite-49.html>
- Sound On Sound, Testbericht: <https://www.soundonsound.com/reviews/samson-graphite-49>
- FL-Studio-Tutorial (Kanal einstellen): <https://forum.image-line.com/viewtopic.php?t=123327>
- Apple, GarageBand iPad und MIDI: <https://support.apple.com/guide/garageband-ipad/chs39282dbe/ipados>
- Apple Community, unterstützte CCs: <https://discussions.apple.com/thread/4666875>
- StreamByter: <https://apps.apple.com/app/streambyter/id1398712641>
