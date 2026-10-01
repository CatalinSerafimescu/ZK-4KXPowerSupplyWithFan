"""Placement trials for single-sided routing: build a placement, route it with Freerouting and
KiCadRoutingTools (B.Cu only, 1.0 / 0.5 mm, no vias), DRC both.

    "C:/Program Files/KiCad/10.0/bin/python.exe" route_trial.py <round>
Output: KiCAD/trial/r<round>{,_fr,_krt}.kicad_pcb + .rpt / .log (main board untouched).
"""
import os
import re
import shutil
import subprocess
import sys

import gen_pcb
from freeroute import freeroute, kicad_routing_tools

KI = gen_pcb.PRJ
OUT = KI / "trial"
CLI = r"C:\Program Files\KiCad\10.0\bin\kicad-cli.exe"
BW, BH = gen_pcb.BW, gen_pcb.BH
HS = gen_pcb.HS

FIXED = {  # heatsink + LM317 (airflow, enclosure vents) and mounting holes stay where they are
    "HS1": (*HS, 0), "U1": (HS[0] - 2.54, HS[1] + 0.2 + 3.15, 0),
    "H1": (4.0, 4.0, 0), "H2": (BW - 4.0, 4.0, 0), "H3": (4.0, BH - 4.0, 0), "H4": (BW - 4.0, BH - 4.0, 0),
}

ROUNDS = {
    # front strip (under HS1 + right): VFAN lane → C2/R4/D1/J3 hanging below it, GND row under them;
    # VIN lane under HS1 → C3, U3, J1; region under U1: C1, J2, C5 (GND); U2 behind R2, which bridges
    # N_INV ↔ VREF over VADJ / LM35 / +5V; R1/RV1/R5 right of U2, GND trunk along the rear/right edges
    1: {
        "C2": (56.0, 7.0, 270), "R4": (61.0, 6.0, 270), "D1": (67.0, 6.0, 270), "J3": (78.0, 7.0, 270),
        "C1": (35.0, 26.0, 0), "C3": (59.5, 22.5, 270), "U3": (64.0, 34.0, 90), "J1": (72.0, 28.0, 270),
        "C4": (57.0, 37.5, 0), "J2": (54.0, 30.0, 180), "C5": (46.0, 35.0, 180),
        "U2": (36.0, 45.0, 0), "R2": (44.89, 39.0, 180), "R3": (28.0, 40.0, 90),
        "R1": (50.0, 40.0, 270), "RV1": (60.0, 52.0, 90), "R5": (40.0, 59.0, 0),
    },
    # C5 and R1 hang below the +5V track (right of VREF); RV1 upright so WIPER runs between its
    # GND and POT_TOP pads; J2 moved clear of the gap; more room above R2
    2: {
        "C2": (56.0, 7.0, 270), "R4": (61.0, 6.0, 270), "D1": (67.0, 6.0, 270), "J3": (78.0, 7.0, 270),
        "C1": (35.0, 26.0, 0), "C3": (59.5, 22.5, 270), "U3": (64.0, 34.0, 90), "J1": (72.0, 28.0, 270),
        "C4": (57.0, 37.5, 0), "J2": (50.0, 30.0, 180), "C5": (49.0, 38.5, 270),
        "U2": (36.0, 45.0, 0), "R2": (44.89, 39.0, 180), "R3": (28.0, 40.0, 90),
        "R1": (53.0, 38.0, 270), "RV1": (58.0, 58.0, 0), "R5": (40.0, 60.0, 0),
    },
    # R1-2 straight above RV1 POT_TOP; C5 further right (room for VREF beside pin 8); C3 right above
    # U3 VIN, C4 below-right of U3
    3: {
        "C2": (56.0, 7.0, 270), "R4": (61.0, 6.0, 270), "D1": (67.0, 6.0, 270), "J3": (78.0, 7.0, 270),
        "C1": (35.0, 26.0, 0), "C3": (64.0, 24.0, 0), "U3": (64.0, 34.0, 90), "J1": (72.0, 28.0, 270),
        "C4": (60.0, 41.0, 0), "J2": (50.0, 30.0, 180), "C5": (50.0, 38.5, 270),
        "U2": (36.0, 45.0, 0), "R2": (44.89, 39.0, 180), "R3": (28.0, 40.0, 90),
        "R1": (56.0, 38.0, 270), "RV1": (56.0, 58.0, 0), "R5": (38.0, 61.0, 0),
    },
    # = round 2, but pad pairs that a GND track must not split are < 2 mm apart:
    # R1-2 right above RV1 POT_TOP, C3 VIN right above U3 VIN (C3 GND on the front GND row)
    4: {
        "C2": (56.0, 7.0, 270), "R4": (61.0, 6.0, 270), "D1": (68.0, 6.0, 270), "J3": (78.0, 7.0, 270),
        "C1": (35.0, 26.0, 0), "C3": (64.5, 23.9, 90), "U3": (64.0, 34.0, 90), "J1": (72.0, 28.0, 270),
        "C4": (61.5, 40.0, 0), "J2": (50.0, 30.0, 180), "C5": (49.0, 38.5, 270),
        "U2": (36.0, 45.0, 0), "R2": (44.89, 39.0, 180), "R3": (28.0, 40.0, 90),
        "R1": (57.5, 40.0, 270), "RV1": (58.0, 59.0, 0), "R5": (40.0, 60.0, 0),
    },
    # = round 4 placement; GND left to the pour (ground plane), routers do the other nets only
    5: {
        "C2": (56.0, 7.0, 270), "R4": (61.0, 6.0, 270), "D1": (68.0, 6.0, 270), "J3": (78.0, 7.0, 270),
        "C1": (35.0, 26.0, 0), "C3": (64.5, 23.9, 90), "U3": (64.0, 34.0, 90), "J1": (72.0, 28.0, 270),
        "C4": (61.5, 40.0, 0), "J2": (50.0, 30.0, 180), "C5": (49.0, 38.5, 270),
        "U2": (36.0, 45.0, 0), "R2": (44.89, 39.0, 180), "R3": (28.0, 40.0, 90),
        "R1": (57.5, 40.0, 270), "RV1": (58.0, 59.0, 0), "R5": (40.0, 60.0, 0),
    },
}


def drc(pcb):
    rpt = pcb.with_suffix(".rpt")
    subprocess.run([CLI, "pcb", "drc", "--severity-all", "-o", str(rpt), str(pcb)], capture_output=True)
    txt = rpt.read_text(encoding="utf-8")
    kinds = {}
    for k in re.findall(r"^\[(\w+)\]", txt, re.M):
        kinds[k] = kinds.get(k, 0) + 1
    # unconnected pairs: "<pad or track> <net> of <ref>" lines under each [unconnected_items]
    pairs = []
    for block in txt.split("[unconnected_items]")[1:]:
        items = re.findall(r"\[(/[^\]]+)\](?: on B\.Cu)?(?: of (\w+))?", block.split("\n[")[0])
        pairs.append(" ↔ ".join(f"{n}{'@' + r if r else ''}" for n, r in items[:2]))
    return kinds, pairs


POUR_ONLY = {5}   # rounds where GND is only the pour (not routed with tracks)


def main(rnd):
    OUT.mkdir(exist_ok=True)
    place = {**gen_pcb.PLACE, **FIXED, **ROUNDS[rnd]}
    base = OUT / f"r{rnd}.kicad_pcb"
    gen_pcb.main(place, base)
    for suffix in ("", "_fr", "_krt"):
        shutil.copyfile(KI / "SursaTensiune.kicad_pro", OUT / f"r{rnd}{suffix}.kicad_pro")
    kinds, _ = drc(base)
    print("placement DRC:", {k: v for k, v in kinds.items() if k != "unconnected_items"} or "clean")
    for tag, fn in (("fr", freeroute), ("krt", kicad_routing_tools)):
        dst = OUT / f"r{rnd}_{tag}.kicad_pcb"
        fn(str(base), str(dst), log=str(dst.with_suffix(".log")), pour_nets=("/GND",) if rnd in POUR_ONLY else ())
        kinds, pairs = drc(dst)
        print(f"{tag}: unconnected {kinds.pop('unconnected_items', 0)}, other {kinds or 'none'}")
        for p in pairs:
            print("   ", p)


if __name__ == "__main__":
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    main(int(sys.argv[1]))
