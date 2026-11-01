#!/usr/bin/env python3
"""Logs every MIDI message from the Samson Graphite 49 to the console and to a CSV.

Usage:
    pip install mido python-rtmidi
    python3 midi_monitor.py --list          # list input ports
    python3 midi_monitor.py [--port NAME]   # log (Ctrl+C to stop)
"""
import argparse
import csv
import time
from pathlib import Path

import mido

NOTE_NAMES = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]


def note_name(n: int) -> str:
    return f"{NOTE_NAMES[n % 12]}{n // 12 - 2}"  # Yamaha/Apple: 60 = C3


def describe(msg) -> tuple[str, str, str, str]:
    ch = str(msg.channel + 1) if hasattr(msg, "channel") else ""
    if msg.type in ("note_on", "note_off"):
        return msg.type, ch, f"{msg.note} ({note_name(msg.note)})", str(msg.velocity)
    if msg.type == "control_change":
        return "cc", ch, str(msg.control), str(msg.value)
    if msg.type == "pitchwheel":
        return "pitchbend", ch, "", str(msg.pitch)
    if msg.type == "program_change":
        return "program", ch, str(msg.program + 1), ""
    if msg.type == "aftertouch":
        return "aftertouch", ch, "", str(msg.value)
    if msg.type == "sysex":
        return "sysex", "", " ".join(f"{b:02X}" for b in msg.data), ""
    return msg.type, ch, "", str(msg)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--list", action="store_true")
    ap.add_argument("--port", help="Input port name (default: first containing 'Graphite')")
    ap.add_argument("--out", default=str(Path(__file__).with_name("capture.csv")))
    ap.add_argument("--all", action="store_true", help="also log clock/active sensing")
    args = ap.parse_args()

    ports = mido.get_input_names()
    if args.list or not ports:
        print("\n".join(ports) or "No MIDI input ports found.")
        return
    port = args.port or next((p for p in ports if "graphite" in p.lower()), ports[0])
    print(f"Listening on: {port}  ->  {args.out}  (Ctrl+C to stop)")

    with mido.open_input(port) as inp, open(args.out, "a", newline="") as f:
        w = csv.writer(f)
        if f.tell() == 0:
            w.writerow(["time", "type", "channel", "number", "value"])
        try:
            for msg in inp:
                if not args.all and msg.type in ("clock", "active_sensing"):
                    continue
                row = describe(msg)
                print(f"{row[0]:<11} ch={row[1]:<3} nr={row[2]:<14} val={row[3]}")
                w.writerow([f"{time.time():.3f}", *row])
                f.flush()
        except KeyboardInterrupt:
            print("\nStopped.")


if __name__ == "__main__":
    main()
