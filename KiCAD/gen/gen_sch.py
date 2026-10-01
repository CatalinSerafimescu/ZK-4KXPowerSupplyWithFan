"""Generate SursaTensiune.kicad_sch from stock KiCad symbols + bom.py.

Every pin gets a short wire stub ending in a net label (no long wires), so the
netlist is defined entirely by the NET tables below. Values, descriptions and
inventory IDs come from bom.py; symbols/footprints are assigned here.

Run:  python gen_sch.py   (then kicad-cli ERC / netlist check, see check.py)
"""
import sys
import uuid
from pathlib import Path

from sexp import Q, dump, find, first, lib_symbol, outward, pins

ROOT = Path(__file__).resolve().parents[2]
PRJ = ROOT / "KiCAD"
sys.path.insert(0, str(ROOT))
from bom import BOM  # noqa: E402

NAME = "SursaTensiune"
LOCAL_LIB = PRJ / f"{NAME}.kicad_sym"
ROOT_UUID = "5a000000-0000-4000-8000-000000000001"
STUB = 2.54

BOMREF = {r: item for item in BOM for r in item["refs"]}

FP = {
    "R": "Resistor_THT:R_Axial_DIN0207_L6.3mm_D2.5mm_P10.16mm_Horizontal",
    "C": "Capacitor_THT:C_Disc_D5.0mm_W2.5mm_P5.00mm",
    "CP": "Capacitor_THT:CP_Radial_D5.0mm_P2.00mm",
    "XH2": "Connector_JST:JST_XH_B2B-XH-A_1x02_P2.50mm_Vertical",
    "XH3": "Connector_JST:JST_XH_B3B-XH-A_1x03_P2.50mm_Vertical",
}

# ── Parts: (ref, lib_id, unit, (x, y), {pin: net}, footprint | None=off-board) ──
# Nets: VJACK VIN GND +5V VREF N_INV VADJ VFAN LM35_OUT POT_TOP WIPER VOUT_P VOUT_N
P = []


def part(ref, lib_id, at, nets, fp=None, unit=1, value=None, bom=True, sim=True):
    P.append(dict(ref=ref, lib_id=lib_id, unit=unit, at=at, nets=nets, fp=fp,
                  value=value, bom=bom))


# Block A — enclosure wiring (off-board)
part("J5", "Connector:Barrel_Jack", (40.64, 60.96), {"1": "VJACK", "2": "GND"})
part("SW1", "Switch:SW_SPST", (66.04, 50.8), {"1": "VJACK", "2": "VIN"})
part("PS1", f"{NAME}:ZK-4KX", (93.98, 60.96), {"1": "VIN", "2": "GND", "3": "VOUT_P", "4": "VOUT_N"})
part("J6", "Connector:Conn_01x01_Socket", (137.16, 58.42), {"1": "VOUT_P"})
part("J7", "Connector:Conn_01x01_Socket", (137.16, 71.12), {"1": "VOUT_N"})
part("#FLG01", "power:PWR_FLAG", (40.64, 81.28), {"1": "VIN"}, bom=False, value="PWR_FLAG")
part("#FLG02", "power:PWR_FLAG", (55.88, 81.28), {"1": "GND"}, bom=False, value="PWR_FLAG")

# Block B — board connectors + the off-board parts plugged into them
part("J1", "Connector:Conn_01x02_Pin", (111.76, 111.76), {"1": "VIN", "2": "GND"}, FP["XH2"])
part("J2", "Connector:Conn_01x03_Pin", (111.76, 129.54), {"1": "+5V", "2": "LM35_OUT", "3": "GND"}, FP["XH3"])
part("J3", "Connector:Conn_01x02_Pin", (111.76, 167.64), {"1": "VFAN", "2": "GND"}, FP["XH2"])
part("U4", "Sensor_Temperature:LM35-LP", (45.72, 129.54), {"1": "+5V", "2": "LM35_OUT", "3": "GND"})
part("M1", "Motor:Fan", (45.72, 167.64), {"1": "VFAN", "2": "GND"})

# Block C — 5 V aux rail
part("C3", "Device:C", (190.5, 60.96), {"1": "VIN", "2": "GND"}, FP["C"])
part("U3", "Regulator_Linear:L78L05_TO92", (213.36, 55.88), {"3": "VIN", "1": "+5V", "2": "GND"},
     "Package_TO_SOT_THT:TO-92_Inline_Wide")
part("C4", "Device:C_Polarized", (238.76, 60.96), {"1": "+5V", "2": "GND"}, FP["CP"])
part("C5", "Device:C", (254.0, 60.96), {"1": "+5V", "2": "GND"}, FP["C"])
part("U2", "Amplifier_Operational:LM358", (294.64, 60.96), {"8": "+5V", "4": "GND"},
     "Package_DIP:DIP-8_W7.62mm_Socket", unit=3)

# Block D — start temperature (threshold) + U2B buffer
part("R1", "Device:R", (190.5, 116.84), {"1": "+5V", "2": "POT_TOP"}, FP["R"])
part("RV1", "Device:R_Potentiometer", (205.74, 129.54), {"3": "POT_TOP", "2": "WIPER", "1": "GND"},
     "Potentiometer_THT:Potentiometer_Bourns_3386P_Vertical")
part("R5", "Device:R", (220.98, 142.24), {"1": "WIPER", "2": "GND"}, FP["R"])
part("U2", "Amplifier_Operational:LM358", (246.38, 129.54), {"5": "WIPER", "6": "VREF", "7": "VREF"},
     "Package_DIP:DIP-8_W7.62mm_Socket", unit=2)

# Block E — amplifier U2A (gain 11)
part("R2", "Device:R", (287.02, 116.84), {"1": "VREF", "2": "N_INV"}, FP["R"])
part("R3", "Device:R", (304.8, 116.84), {"1": "N_INV", "2": "VADJ"}, FP["R"])
part("U2", "Amplifier_Operational:LM358", (332.74, 129.54), {"3": "LM35_OUT", "2": "N_INV", "1": "VADJ"},
     "Package_DIP:DIP-8_W7.62mm_Socket", unit=1)

# Block F — fan supply
part("C1", "Device:C", (190.5, 195.58), {"1": "VIN", "2": "GND"}, FP["C"])
part("U1", "Regulator_Linear:LM317_TO-220", (213.36, 190.5), {"3": "VIN", "1": "VADJ", "2": "VFAN"},
     "Package_TO_SOT_THT:TO-220-3_Vertical")
part("C2", "Device:C_Polarized", (238.76, 195.58), {"1": "VFAN", "2": "GND"}, FP["CP"])
part("R4", "Device:R", (254.0, 195.58), {"1": "VFAN", "2": "GND"}, FP["R"])
part("D1", "Diode:1N4007", (274.32, 195.58), {"1": "VFAN", "2": "GND"},
     "Diode_THT:D_DO-41_SOD81_P10.16mm_Horizontal")

# Mechanical
part("HS1", "Mechanical:Heatsink", (213.36, 226.06), {}, f"{NAME}:Heatsink_Stonecold_RAD-DY-KY-3_40x20mm_P34mm")
for i, x in enumerate((304.8, 320.04, 335.28, 350.52), 1):
    part(f"H{i}", "Mechanical:MountingHole", (x, 226.06), {}, "MountingHole:MountingHole_3.2mm_M3", bom=False)

TEXTS = [
    ((27.94, 38.1), "A · ENCLOSURE WIRING (off-board)", 2.0),
    ((27.94, 43.18), "DC jack → SW1 (power switch) → ZK-4KX input + fan board J1;  ZK-4KX output → banana sockets", 1.5),
    ((27.94, 96.52), "B · OFF-BOARD PARTS → BOARD CONNECTORS J1–J3 (JST XH)", 2.0),
    ((177.8, 38.1), "C · 5 V AUX RAIL (U2, LM35)", 2.0),
    ((177.8, 96.52), "D · START TEMPERATURE", 2.0),
    ((177.8, 157.48), "V_REF [mV] = 11·T_start − 155  (measure U2 pin 7)", 1.5),
    ((276.86, 96.52), "E · AMPLIFIER (gain 11)", 2.0),
    ((276.86, 157.48), "V_ADJ = 11·V_LM35 − 10·V_REF  (0 … ~3.5 V)", 1.5),
    ((177.8, 172.72), "F · FAN SUPPLY", 2.0),
    ((177.8, 213.36), "V_FAN = V_ADJ + 1.25 V  (1.25 … 4.75 V)", 1.5),
    ((27.94, 88.9), "J5: centre = + (check adapter).  Do NOT tie ZK-4KX OUT− to IN−.", 1.5),
    ((27.94, 190.5), "LM35 on the ZK-4KX rear heatsink (fin root). Check heatsink potential; insulate the legs.", 1.5),
    ((177.8, 162.56), "RV1 trimmer: pin 3 = POT_TOP → clockwise = higher start temperature.", 1.5),
    ((177.8, 238.76), "HS1: U1 on RAD-DY-KY/3 (2 PCB pins, M3) with TO220-SET insulator (U1 tab = V_FAN!).  "
                      "0.9 W @ 9 V in, 5.3 W @ 30 V in.", 1.5),
    ((27.94, 254.0), "Simulation: ../simulation (ngspice 46, 11 scenarios PASS).  BOM: ../bom.md "
                     "(generated from ../bom.py).", 1.5),
]


# ── Helpers ───────────────────────────────────────────────────────────────────
def U():
    return Q(str(uuid.uuid4()))


def eff(size=1.27, justify=None, hide=False):
    e = ["effects", ["font", ["size", size, size]]]
    if justify:
        e.append(["justify", *justify.split()])
    return e


def prop(name, value, at, hide=False):
    p = ["property", Q(name), Q(value), ["at", *at], ["show_name", "no"], ["do_not_autoplace", "no"]]
    if hide:
        p.append(["hide", "yes"])
    p.append(eff())
    return p


def r2(v):
    return round(v, 2)


def label(net, xy, d):
    ang, just = {(1, 0): (0, "left"), (-1, 0): (180, "right"),
                 (0, -1): (90, "left"), (0, 1): (270, "right")}[d]
    return ["label", Q(net), ["at", r2(xy[0]), r2(xy[1]), ang],
            ["effects", ["font", ["size", 1.27, 1.27]], ["justify", just]], ["uuid", U()]]


def wire(a, b):
    return ["wire", ["pts", ["xy", r2(a[0]), r2(a[1])], ["xy", r2(b[0]), r2(b[1])]],
            ["stroke", ["width", 0], ["type", "default"]], ["uuid", U()]]


def main():
    lib_syms, body = {}, []
    for p in P:
        lid = p["lib_id"]
        if lid not in lib_syms:
            lib_syms[lid] = lib_symbol(lid, LOCAL_LIB if lid.startswith(NAME + ":") else None)
        sym = lib_syms[lid]
        x, y = p["at"]
        b = BOMREF.get(p["ref"])
        offboard = p["fp"] is None and not p["ref"].startswith("#")
        value = p["value"] or (b["value"] if b else first(sym, "property")[2])

        lprops = {q[1]: q for q in find(sym, "property")}

        def lat(name, default=(0, 0)):
            q = lprops.get(name)
            a = first(q, "at") if q else ["at", *default, 0]
            return (r2(x + float(a[1])), r2(y - float(a[2])), float(a[3]) if len(a) > 3 else 0)

        power = p["ref"].startswith("#")
        inst = ["symbol", ["lib_id", Q(lid)], ["at", x, y, 0], ["unit", p["unit"]], ["body_style", 1],
                ["exclude_from_sim", "no"], ["in_bom", "yes" if p["bom"] else "no"],
                ["on_board", "no" if (offboard or power) else "yes"], ["in_pos_files", "yes"],
                ["dnp", "no"], ["uuid", U()],
                prop("Reference", p["ref"], lat("Reference"), hide=power),
                prop("Value", value, lat("Value"), hide=power),
                prop("Footprint", p["fp"] or "", lat("Footprint"), hide=True),
                prop("Datasheet", str(lprops["Datasheet"][2]) if "Datasheet" in lprops else "", lat("Datasheet"), hide=True),
                prop("Description", b["description"] if b else str(lprops.get("Description", [0, 0, ""])[2]),
                     lat("Description"), hide=True)]
        if b:
            inst.append(prop("Part", b["part_number"], (x, y, 0), hide=True))
            inst.append(prop("Status", b["status"] + (" (off-board)" if b.get("offboard") else ""), (x, y, 0), hide=True))
            if b.get("inv"):
                inst.append(prop("Inventory", b["inv"], (x, y, 0), hide=True))

        for num, name, px, py, ang in pins(sym, p["unit"]):
            inst.append(["pin", Q(num), ["uuid", U()]])
            pt = (x + px, y - py)
            net = p["nets"].get(num)
            d = outward(ang)
            end = (pt[0] + d[0] * STUB, pt[1] + d[1] * STUB)
            if net is None:
                body.append(["no_connect", ["at", r2(pt[0]), r2(pt[1])], ["uuid", U()]])
                continue
            body.append(wire(pt, end))
            body.append(label(net, end, d))
        inst.append(["instances", ["project", Q(NAME), ["path", Q("/" + ROOT_UUID),
                                                        ["reference", Q(p["ref"])], ["unit", p["unit"]]]]])
        body.insert(0, inst)

    for (tx, ty), txt, size in TEXTS:
        body.append(["text", Q(txt), ["exclude_from_sim", "no"], ["at", tx, ty, 0],
                     ["effects", ["font", ["size", size, size]], ["justify", "left", "bottom"]], ["uuid", U()]])

    sch = ["kicad_sch", ["version", 20260306], ["generator", Q("eeschema")], ["generator_version", Q("10.0")],
           ["uuid", Q(ROOT_UUID)], ["paper", Q("A3")],
           ["title_block", ["title", Q("ZK-4KX fan temperature controller")], ["date", Q("2026-09-21")],
            ["rev", Q("1.0")], ["company", Q("DIY")],
            ["comment", 1, Q("Generated by KiCAD/gen/gen_sch.py from bom.py — edit there, not here")],
            ["comment", 2, Q("Nets by labels; off-board parts have on_board=no")]],
           ["lib_symbols", *lib_syms.values()],
           *body,
           ["sheet_instances", ["path", Q("/"), ["page", Q("1")]]],
           ["embedded_fonts", "no"]]
    out = PRJ / f"{NAME}.kicad_sch"
    out.write_text(dump(sch) + "\n", encoding="utf-8")
    print(f"Saved: {out}")


if __name__ == "__main__":
    main()
