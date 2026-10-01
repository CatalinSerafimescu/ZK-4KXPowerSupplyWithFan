"""Generate SursaTensiune.kicad_pcb from the schematic netlist (placement only, unrouted).

Run with KiCad's Python:
  "C:\\Program Files\\KiCad\\10.0\\bin\\python.exe" gen_pcb.py
Needs SursaTensiune.net (kicad-cli sch export netlist) — check.py does both.
Footprints, nets and schematic links (paths) come from the netlist; positions from PLACE.
"""
import math
from pathlib import Path

import pcbnew

from sexp import KICAD, find, first, parse

PRJ = Path(__file__).resolve().parents[1]
NAME = "SursaTensiune"
BW, BH = 90.0, 66.0          # board size, mm
OX, OY = 100.0, 100.0        # board origin on the page, mm

# RV1: stock KiCad 3386P footprint has no 3D model; use the SamacSys STEP 3386P-1-103LF.stp in
# KiCAD/vendor/ (not in the repo — SamacSys licence: no redistribution; download it yourself). Transform = SamacSys placement
# re-expressed in the stock footprint frame (pads rotated 90°, origin at pad 1).
# Connectors: function name (printed as the value) + per-pin labels on the silkscreen:
# (name, pin labels, label offset from the pin row, name position) — footprint-local mm
CONN = {"J1": ("IN 9-30V", ["+", "-"], 4.2, (1.25, -5.4)),     # name on the free side, away from U3
        "J3": ("FAN 5V", ["+", "-"], 4.2, (1.25, 5.6)),
        # turned 180°: labels in the strip between J2 and the HS1 outline, name beside J2
        "J2": ("LM35", ["+5V", "OUT", "GND"], 4.0, (10.8, 0.0))}
XH_PITCH = 2.5
RING, GAP = 0.5, 0.6          # toner transfer: pad copper ring per side, min gap between pads of one part

LOCAL_MODELS = {"RV1": ("${KIPRJMOD}/vendor/3386P-1-103LF.stp", (4.58, 2.365, 4.76), (-180, 0, 90))}

# ref: (x, y, rotation°) — board coordinates in mm, (0,0) = top-left corner
HS = (30.0, 16.5)   # heatsink origin = centre of its mounting face
PLACE = {
    "HS1": (*HS, 0),
    # TO-220 in the fin gap: middle pin on the heatsink centre line,
    # tab face 0.2 mm (insulating pad) from the mounting face, pads 3.15 mm further
    "U1": (HS[0] - 2.54, HS[1] + 0.2 + 3.15, 0),
    # single-sided layout (see route_trial.py, round 5): front strip = VFAN lane under HS1 with C2/R4/D1/J3
    # below it; VIN lane → C3/U3/J1; under U1: C1, J2; U2 behind R2, which bridges N_INV ↔ VREF over
    # VADJ / LM35_OUT / +5V; C5 and R1 hang off the +5V track; WIPER runs between RV1's GND and POT_TOP pads
    "C2": (56.0, 7.0, 270),
    "R4": (61.0, 6.0, 270),
    "D1": (68.0, 6.0, 270),
    "J3": (78.0, 7.0, 270),
    "C1": (35.0, 26.0, 0),
    "C3": (64.5, 23.9, 90),
    "U3": (64.0, 34.0, 90),
    "J1": (72.0, 28.0, 270),
    "C4": (61.5, 40.0, 0),
    "J2": (50.0, 30.0, 180),
    "C5": (49.0, 38.5, 270),
    "U2": (36.0, 45.0, 0),
    "R2": (44.89, 39.0, 180),
    "R3": (28.0, 40.0, 90),
    "R1": (57.5, 40.0, 270),
    "RV1": (58.0, 59.0, 0),
    "R5": (40.0, 60.0, 0),
    "H1": (4.0, 4.0, 0),
    "H2": (BW - 4.0, 4.0, 0),
    "H3": (4.0, BH - 4.0, 0),
    "H4": (BW - 4.0, BH - 4.0, 0),
}


def mm(v):
    return pcbnew.FromMM(v)


def pt(x, y):
    return pcbnew.VECTOR2I(mm(OX + x), mm(OY + y))


def rel(x, y, rot, dx, dy):
    """Board point of the footprint-local offset (dx, dy) of a footprint at (x, y) rotated by rot."""
    a = math.radians(rot)
    return pt(x + dx * math.cos(a) + dy * math.sin(a), y - dx * math.sin(a) + dy * math.cos(a))


def lib_path(lib):
    if lib == NAME:
        return str(PRJ / f"{NAME}.pretty")
    return str(KICAD / "footprints" / f"{lib}.pretty")


def toner_pads(fp):
    """Home etching (toner transfer): copper ring >= RING per side; where the pitch is too tight for a
    round pad, the pad becomes oval (narrow along the row, long across it), keeping >= GAP to its neighbour."""
    pads = [p for p in fp.Pads() if p.GetAttribute() == pcbnew.PAD_ATTRIB_PTH]
    for p in pads:
        d = pcbnew.ToMM(p.GetDrillSize().x)
        target = d + 2 * RING
        size = p.GetSize(pcbnew.F_Cu)
        w, h = max(pcbnew.ToMM(size.x), target), max(pcbnew.ToMM(size.y), target)
        for q in pads:
            if q is p:
                continue
            dx = abs(pcbnew.ToMM(q.GetFPRelativePosition().x - p.GetFPRelativePosition().x))
            dy = abs(pcbnew.ToMM(q.GetFPRelativePosition().y - p.GetFPRelativePosition().y))
            if dy < 0.01 and dx < w + GAP:     # neighbour in the same row (x)
                w, h = dx - GAP, max(h, target + 0.4)
            elif dx < 0.01 and dy < h + GAP:   # neighbour in the same column (y)
                h, w = dy - GAP, max(w, target + 0.4)
        p.SetSize(pcbnew.F_Cu, pcbnew.VECTOR2I(mm(w), mm(h)))
        if abs(w - h) > 0.01 and p.GetShape(pcbnew.F_Cu) == pcbnew.PAD_SHAPE_CIRCLE:
            p.SetShape(pcbnew.F_Cu, pcbnew.PAD_SHAPE_OVAL)


def main(place=PLACE, out=None):
    net = parse((PRJ / f"{NAME}.net").read_text(encoding="utf-8"))
    board = pcbnew.BOARD()

    nets = {}
    pad_net = {}
    for n in find(first(net, "nets"), "net"):
        name = str(first(n, "name")[1])
        ni = pcbnew.NETINFO_ITEM(board, name)
        board.Add(ni)
        nets[name] = ni
        for node in find(n, "node"):
            pad_net[(str(first(node, "ref")[1]), str(first(node, "pin")[1]))] = ni

    missing = []
    for c in find(first(net, "components"), "comp"):
        ref = str(first(c, "ref")[1])
        fpid = first(c, "footprint")
        if not fpid:
            continue
        lib, fname = str(fpid[1]).split(":")
        fp = pcbnew.FootprintLoad(lib_path(lib), fname)
        fp.SetFPID(pcbnew.LIB_ID(lib, fname))
        fp.SetReference(ref)
        fp.SetValue(str(first(c, "value")[1]))
        fp.SetPath(pcbnew.KIID_PATH("/" + str(first(c, "tstamps")[1])))
        fp.SetSheetname("Root")
        fp.SetSheetfile(f"{NAME}.kicad_sch")
        toner_pads(fp)
        if ref in place:
            x, y, rot = place[ref]
        else:
            missing.append(ref)
            x, y, rot = BW + 20, 10 + 10 * len(missing), 0
        fp.SetPosition(pt(x, y))
        fp.SetOrientationDegrees(rot)
        if ref.startswith("H") and ref != "HS1":
            fp.Reference().SetVisible(False)
        if ref == "U1":  # keep the reference off the heatsink outline
            fp.Reference().SetPosition(pt(x + 2.54, y + 4.6))
        if ref in LOCAL_MODELS and fp.Models().size():
            path, off, rot3 = LOCAL_MODELS[ref]
            m = fp.Models()[0]
            m.m_Filename = path
            m.m_Offset = pcbnew.VECTOR3D(*off)
            m.m_Rotation = pcbnew.VECTOR3D(*rot3)
        # values on the silkscreen (printed + visible in 3D), except mechanical parts
        if not ref.startswith("H"):
            val = fp.Value()
            val.SetLayer(pcbnew.F_SilkS)
            val.SetVisible(True)
            val.SetTextSize(pcbnew.VECTOR2I(mm(0.8), mm(0.8)))
            val.SetTextThickness(mm(0.12))
            if (ref.startswith("R") and ref != "RV1") or ref == "D1":
                # axial parts: value beside the body (the body would cover it), opposite the reference
                val.SetPosition(rel(x, y, rot, 5.08, 2.3))
                val.SetTextAngleDegrees(rot % 180)
            if ref == "C2":  # reference left of the can, clear of R4
                fp.Reference().SetPosition(pt(x - 3.5, y + 1.0))
                fp.Reference().SetTextAngleDegrees(90)
                val.SetPosition(pt(x, y - 3.4))
                val.SetTextAngleDegrees(0)
        if ref in CONN:
            name, pin_labels, label_dy, value_at = CONN[ref]
            fp.SetValue(name)
            vertical = label_dy > 4.5                       # long labels, written across the row
            fp.Value().SetPosition(rel(x, y, rot, *value_at))
            fp.Value().SetTextAngleDegrees(0 if ref == "J2" else rot % 180)
            for i, s in enumerate(pin_labels):
                lt = pcbnew.PCB_TEXT(board)
                lt.SetText(s)
                lt.SetPosition(rel(x, y, rot, i * XH_PITCH, label_dy))
                if vertical:
                    lt.SetTextAngleDegrees((90 + rot) % 180)
                lt.SetLayer(pcbnew.F_SilkS)
                lt.SetTextSize(pcbnew.VECTOR2I(mm(0.8), mm(0.8)))
                lt.SetTextThickness(mm(0.12))
                board.Add(lt)
        for pad in fp.Pads():
            ni = pad_net.get((ref, pad.GetNumber()))
            if ni:
                pad.SetNet(ni)
        board.Add(fp)

    # board outline
    corners = [(0, 0), (BW, 0), (BW, BH), (0, BH)]
    for a, b in zip(corners, corners[1:] + corners[:1]):
        seg = pcbnew.PCB_SHAPE(board)
        seg.SetShape(pcbnew.SHAPE_T_SEGMENT)
        seg.SetStart(pt(*a))
        seg.SetEnd(pt(*b))
        seg.SetLayer(pcbnew.Edge_Cuts)
        seg.SetWidth(mm(0.1))
        board.Add(seg)

    # silkscreen notes
    for (x, y), txt in [((46, 64.2), "ZK-4KX fan controller  rev 1.1"),
                        ((77, 47),"U1 on HS1 with\nTO220-SET insulator\n(U1 tab = V_FAN)")]:
        t = pcbnew.PCB_TEXT(board)
        t.SetText(txt)
        t.SetPosition(pt(x, y))
        t.SetLayer(pcbnew.F_SilkS)
        t.SetTextSize(pcbnew.VECTOR2I(mm(1.0), mm(1.0)))
        t.SetTextThickness(mm(0.15))
        board.Add(t)

    out = out or PRJ / f"{NAME}.kicad_pcb"
    board.Save(str(out))
    print(f"Saved: {out}")
    if missing:
        print("Not placed (parked right of board):", ", ".join(missing))


if __name__ == "__main__":
    main()
