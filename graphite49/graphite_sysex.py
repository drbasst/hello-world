#!/usr/bin/env python3
"""Programmiert das Samson Graphite 49 per SysEx (Firmware 1.42, "Version 1").

Protokoll aus dem Reverse-Engineering-Projekt alxwk/samson_sysex abgeleitet.
Siehe protocol.md. Die Lese- und Identity-Befehle sind dort dokumentiert; die
Schreib-Operationen (set/save) sind teils rekonstruiert, deshalb liest dieses
Werkzeug nach jedem Schreiben zur Kontrolle zurueck.

 WICHTIG vor dem ersten Einsatz:
  1. Firmware-Version am Geraet pruefen (beide TRANSPOSE beim Einschalten).
     Ist es nicht "Version 1" (1.xx), kann das Protokoll abweichen.
  2. Vorhandene User-Presets zuerst sichern: `dump` fuer jedes Preset 11..30.
  3. Immer in ein USER-Preset (11..30) schreiben, nie ueber ein Werk-Preset.
  4. Nach dem Programmieren das Geraet ORDENTLICH ueber den Schalter ausschalten,
     sonst wird nichts gespeichert.

Abhaengigkeit:  pip install mido python-rtmidi
Beispiele:
  python3 graphite_sysex.py ports
  python3 graphite_sysex.py identity
  python3 graphite_sysex.py dump 11
  python3 graphite_sysex.py set --preset 11 --control E1b1 --cc 1 --channel 1
  python3 graphite_sysex.py set --preset 11 --control P1 --cc 0 --channel 1 --note --momentary
  python3 graphite_sysex.py save 11
"""
import argparse
import sys
import time

import mido

ARTURIA = [0x00, 0x20, 0x6B]
MACKIE = [0x00, 0x00, 0x66]

# Hardware-Control-IDs (dezimal). Siehe protocol.md.
CONTROLS = {
    "S1b1": 2, "S2b1": 1, "S3b1": 0, "S4b1": 3, "S5b1": 5, "S6b1": 7,
    "S7b1": 6, "S8b1": 4, "S9": 10,
    "S1b2": 20, "S2b2": 21, "S3b2": 22, "S4b2": 23, "S5b2": 24, "S6b2": 25,
    "S7b2": 26, "S8b2": 27,
    "E1b1": 131, "E2b1": 135, "E3b1": 130, "E4b1": 134, "E5b1": 129,
    "E6b1": 133, "E7b1": 128, "E8b1": 132,
    "E1b2": 136, "E2b2": 137, "E3b2": 138, "E4b2": 139, "E5b2": 140,
    "E6b2": 141, "E7b2": 142, "E8b2": 143,
    "F1": 295, "F2": 294, "F3": 293, "F4": 292, "F5": 291, "F6": 290,
    "F7": 289, "F8": 288, "F9": 280, "F10": 281, "F11": 282, "F12": 283,
    "F13": 284, "F14": 285, "F15": 286, "F16": 287,
    "REW": 299, "FF": 300, "STOP": 301, "PLAY": 302, "REC": 303,
    "P1": 304, "P2": 305, "P3": 306, "P4": 307,
    "P5": 308, "P6": 309, "P7": 310, "P8": 311,
}
ID_TO_NAME = {v: k for k, v in CONTROLS.items()}

OP = {"cc": 0x01, "channel": 0x02, "port": 0x03, "flags": 0x04}


def hw_bytes(dec_id: int) -> tuple[int, int]:
    return dec_id // 128, dec_id % 128


def cc_write_bytes(cc: int) -> tuple[int, int]:
    """CC-Nummer in die beim SCHREIBEN erwarteten MSB/LSB (ohne +1-Shift)."""
    if 0 <= cc <= 127:
        return 0x00, cc
    if 128 <= cc <= 171:
        return 0x01, cc - 128
    raise ValueError(f"CC {cc} ausserhalb 0..171")


def find_ports() -> tuple[str, str]:
    outs = [p for p in mido.get_output_names() if "graphite" in p.lower()]
    ins = [p for p in mido.get_input_names() if "graphite" in p.lower()]
    # Anfrage-Port ":1" (In Port B), Antwort-Port ":4" (Out Port 5)
    out = next((p for p in outs if ":1" in p), outs[0] if outs else None)
    inp = next((p for p in ins if ":4" in p), ins[0] if ins else None)
    if not out or not inp:
        sys.exit("Graphite-Ports nicht gefunden. 'ports' zeigt alle Ports.")
    return out, inp


def send_sysex(out_name: str, data: list[int]) -> None:
    with mido.open_output(out_name) as out:
        out.send(mido.Message("sysex", data=data))


def read_preset(out_name: str, in_name: str, preset_1based: int,
                timeout: float = 2.0) -> list[dict]:
    """Liest ein Preset und gibt die Control-Records zurueck."""
    controls = []
    with mido.open_input(in_name) as inp, mido.open_output(out_name) as out:
        for _ in inp.iter_pending():
            pass
        nn = 0x7F if preset_1based is None else preset_1based - 1
        out.send(mido.Message("sysex", data=ARTURIA + [0x02, 0x05, nn, 0x00]))
        end = time.time() + timeout
        while time.time() < end:
            for msg in inp.iter_pending():
                if msg.type != "sysex":
                    continue
                d = list(msg.data)
                if d and d[0] < 4 and len(d) >= 7:
                    hw = d[0] * 128 + d[1]
                    cc = d[2] * 128 + d[3]
                    if cc > 127:
                        cc -= 1  # Lese-Shift der virtuellen CCs
                    controls.append({
                        "id": hw, "name": ID_TO_NAME.get(hw, f"id{hw}"),
                        "cc": cc, "channel": d[4], "port": d[5],
                        "flags": d[6] if len(d) > 6 else None,
                    })
                elif d and d[0] == 5:
                    return controls
            time.sleep(0.01)
    return controls


def cmd_ports(_):
    print("Ausgaenge (Anfragen -> ':1'):")
    for p in mido.get_output_names():
        print("  ", p)
    print("Eingaenge (Antworten <- ':4'):")
    for p in mido.get_input_names():
        print("  ", p)


def cmd_identity(_):
    out, inp = find_ports()
    with mido.open_input(inp) as i, mido.open_output(out) as o:
        for _m in i.iter_pending():
            pass
        o.send(mido.Message("sysex", data=MACKIE + [0x14, 0x1A, 0x00]))
        end = time.time() + 2.0
        while time.time() < end:
            for msg in i.iter_pending():
                if msg.type == "sysex":
                    print("Antwort:", " ".join(f"{b:02X}" for b in msg.data))
                    return
            time.sleep(0.01)
    print("Keine Antwort. Firmware-Version evtl. nicht 'Version 1'?")


def cmd_dump(args):
    out, inp = find_ports()
    controls = read_preset(out, inp, args.preset)
    if not controls:
        print("Nichts empfangen.")
        return
    for c in controls:
        f = "" if c["flags"] is None else f" flags=0x{c['flags']:02X}"
        print(f"{c['name']:<6} CC={c['cc']:<3} ch={c['channel']:<2} "
              f"port={c['port']}{f}")


def cmd_set(args):
    out, inp = find_ports()
    if args.control not in CONTROLS:
        sys.exit(f"Unbekanntes Control '{args.control}'. "
                 f"Moeglich: {', '.join(CONTROLS)}")
    n1, n2 = hw_bytes(CONTROLS[args.control])

    def write(op_name, v1, v2):
        send_sysex(out, ARTURIA + [0x02, OP[op_name], n1, n2, v1, v2])
        time.sleep(0.05)

    if args.cc is not None:
        v1, v2 = cc_write_bytes(args.cc)
        write("cc", v1, v2)
    if args.channel is not None:
        write("channel", 0, args.channel)
    if args.port is not None:
        write("port", 0, args.port)
    if args.note or args.controller or args.momentary or args.toggle \
            or args.relative or args.absolute:
        flags = 0
        if args.note:
            flags |= 1
        if args.momentary:
            flags |= 2
        if args.relative:
            flags |= 1  # Encoder: Bit0 = relativ
        write("flags", 0, flags)

    print("Geschrieben. Ruecklesen zur Kontrolle:")
    for c in read_preset(out, inp, args.preset):
        if c["name"] == args.control:
            print(f"  {c['name']}: CC={c['cc']} ch={c['channel']} "
                  f"port={c['port']} flags={c['flags']}")


def cmd_save(args):
    out, _ = find_ports()
    nn = args.preset - 1
    send_sysex(out, ARTURIA + [0x02, 0x07, nn, 0x00])
    print(f"Speichern in Preset {args.preset} gesendet. "
          f"Geraet anschliessend ORDENTLICH ausschalten.")


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("ports").set_defaults(func=cmd_ports)
    sub.add_parser("identity").set_defaults(func=cmd_identity)

    p = sub.add_parser("dump", help="Preset lesen (1-basiert; leer = aktuell)")
    p.add_argument("preset", nargs="?", type=int, default=None)
    p.set_defaults(func=cmd_dump)

    p = sub.add_parser("set", help="Ein Bedienelement setzen")
    p.add_argument("--preset", type=int, required=True,
                   help="nur zum Ruecklesen; geschrieben wird ins AKTUELLE Preset")
    p.add_argument("--control", required=True)
    p.add_argument("--cc", type=int)
    p.add_argument("--channel", type=int)
    p.add_argument("--port", type=int)
    p.add_argument("--note", action="store_true")
    p.add_argument("--controller", action="store_true")
    p.add_argument("--momentary", action="store_true")
    p.add_argument("--toggle", action="store_true")
    p.add_argument("--relative", action="store_true")
    p.add_argument("--absolute", action="store_true")
    p.set_defaults(func=cmd_set)

    p = sub.add_parser("save", help="Aktuelle Einstellungen in Preset speichern")
    p.add_argument("preset", type=int)
    p.set_defaults(func=cmd_save)

    args = ap.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
