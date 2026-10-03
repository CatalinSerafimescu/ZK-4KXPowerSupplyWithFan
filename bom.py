"""
Bill of Materials — ZK-4KX fan temperature controller
Single source of truth for component data, schematic labels and procurement status.

To update a component:  edit the entry here, then run  python bom.py
                        (regenerates bom.md; the schematic reads LABEL from here)

status values
  'inventory'  — in hand, listed in ComponentsDB/inventory.html (inv = comp id)
  'have'       — in hand, not listed in ComponentsDB
  'buy'        — must be ordered
optional=True marks parts that are not required for the basic build.
offboard=True marks parts wired to the board, not mounted on it (excluded from PCB).
"""

BOM = [
    # ══ ICs ══════════════════════════════════════════════════════════════════
    {
        "refs": ["U1"], "value": "LM317T", "qty": 1, "status": "inventory", "inv": "comp_221",
        "description": "Adjustable linear regulator, 1.5 A, TO-220, THT",
        "part_number": "LM317T/NOPB (TI)",
        "notes": "Fan supply: V_fan = V_adj + 1.25 V. Tab = OUT (insulate from heatsink/chassis). "
                 "Dissipation 0.9 W @ 9 V in, 5.3 W @ 30 V in (sim D).",
    },
    {
        "refs": ["U2"], "value": "LM358AP", "qty": 1, "status": "inventory", "inv": "comp_218",
        "description": "Dual op-amp, single supply, A-grade (Vos ≤ 3 mV), DIP-8, THT",
        "part_number": "LM358AP (TI)",
        "notes": "U2A = gain-11 amplifier driving U1 ADJ; U2B = V_ref buffer. "
                 "Powered from +5 V, so its output (≤ ~3.5 V) caps V_fan at ~4.75 V.",
    },
    {
        "refs": ["U3"], "value": "UA78L05", "qty": 1, "status": "inventory", "inv": "comp_219",
        "description": "5 V / 100 mA linear regulator, TO-92, THT",
        "part_number": "UA78L05AILP (TI) — discontinued at TME, 2 in stock",
        "notes": "Powers U2 + U4 (~2 mA). Pinout (flat face): OUT–GND–IN, reversed vs 7805. "
                 "Input max ~30 V.",
    },
    {
        "refs": ["U4"], "value": "LM35DZ", "qty": 1, "status": "inventory", "inv": "comp_220",
        "description": "Analog temperature sensor, 10 mV/°C, 0–100 °C, TO-92, THT",
        "part_number": "LM35DZ/NOPB (TI)",
        "notes": "Off-board via J2, on the ZK-4KX rear heatsink (fin root, flat face down, paste + Kapton); "
                 "check the heatsink potential and insulate the legs. "
                 "Leads > ~20 cm: add 75–100 Ω + 1 µF damper at the sensor (datasheet).",
    },

    # ══ Resistors ════════════════════════════════════════════════════════════
    {
        "refs": ["R1"], "value": "100 kΩ", "qty": 1, "status": "inventory", "inv": "comp_117",
        "description": "Resistor, carbon film, 100 kΩ, 1/4 W, 1 %, axial THT",
        "part_number": "Rezistor 1/4W 100K 1%",
        "notes": "Top of threshold divider (R1 : RV1 ≈ 10 : 1 → V_ref 0–0.42 V).",
    },
    {
        "refs": ["R2"], "value": "10 kΩ", "qty": 1, "status": "inventory", "inv": "comp_116",
        "description": "Resistor, carbon film, 10 kΩ, 1/4 W, 1 %, axial THT",
        "part_number": "Rezistor 1/4W 10K 1%",
        "notes": "U2A gain resistor Rg. Use 5.1 kΩ for a ~9.5 °C ramp instead of ~18 °C.",
    },
    {
        "refs": ["R3"], "value": "100 kΩ", "qty": 1, "status": "inventory", "inv": "comp_117",
        "description": "Resistor, carbon film, 100 kΩ, 1/4 W, 1 %, axial THT",
        "part_number": "Rezistor 1/4W 100K 1%",
        "notes": "U2A feedback resistor Rf (gain = 1 + R3/R2 = 11).",
    },
    {
        "refs": ["R4"], "value": "220 Ω", "qty": 1, "status": "inventory", "inv": "comp_111",
        "description": "Resistor, carbon film, 220 Ω, 1/4 W, 1 %, axial THT",
        "part_number": "Rezistor 1/4W 220R 1%",
        "notes": "LM317 minimum load (5.7 mA at 1.25 V, 22 mA / 0.1 W at 4.75 V).",
    },
    {
        "refs": ["R5"], "value": "100 kΩ", "qty": 1, "status": "inventory", "inv": "comp_117",
        "description": "Resistor, carbon film, 100 kΩ, 1/4 W, 1 %, axial THT",
        "part_number": "Rezistor 1/4W 100K 1%",
        "notes": "Fail-safe: if the pot wiper loses contact, pulls V_ref low → fan starts at ~17 °C "
                 "(runs) instead of never (sim H).",
    },
    {
        "refs": ["RV1"], "value": "10k", "qty": 1, "status": "inventory", "inv": "comp_053",
        "description": "Trimmer, Bourns 3386P, 10 kΩ, single-turn, top adjust, THT",
        "part_number": "3386P-1-103LF (Bourns)",
        "notes": "Sets start temperature ~15–52 °C (clockwise = hotter). "
                 "Calibrate: V_ref(U2 pin 7) [mV] = 11·T_start − 155.",
    },

    # ══ Capacitors ═══════════════════════════════════════════════════════════
    {
        "refs": ["C1", "C3", "C5"], "value": "100 nF", "qty": 3, "status": "inventory", "inv": "comp_038",
        "description": "Capacitor, ceramic X7R, 100 nF, 100 V, THT",
        "part_number": "K104K10X7RF5UH5",
        "notes": "C1 at U1 IN, C3 at U3 IN, C5 at U2 pin 8 — each placed next to its pin.",
    },
    {
        "refs": ["C2", "C4"], "value": "10 µF", "qty": 2, "status": "inventory", "inv": "comp_037",
        "description": "Capacitor, aluminium electrolytic, 10 µF, 25 V, radial THT",
        "part_number": "EEAGA1E100H (Panasonic)",
        "notes": "C2 at U1 OUT (≤ 5 V), C4 at U3 OUT (5 V). Mind polarity.",
    },

    # ══ Diode ════════════════════════════════════════════════════════════════
    {
        "refs": ["D1"], "value": "1N4007", "qty": 1, "status": "inventory", "inv": "comp_062",
        "description": "Diode, rectifier, 1 A, 1000 V, DO-41, THT",
        "part_number": "1N4007",
        "notes": "Across the fan, cathode to +. Clamps motor spikes.",
    },

    # ══ Board connectors / mechanics ═════════════════════════════════════════
    {
        "refs": ["J1", "J3"], "value": "XH 2-pin", "qty": 2, "status": "inventory", "inv": "comp_156",
        "description": "Connector, JST XH 2.54 mm, 2-pin header + housing + crimps",
        "part_number": "B2B-XH-A (Kit Conectori XH2.54)",
        "notes": "J1 = input (wired from J5 / ZK-4KX IN), J3 = fan. Inventory shows the XH kit at qty −5 — check stock.",
    },
    {
        "refs": ["J2"], "value": "XH 3-pin", "qty": 1, "status": "inventory", "inv": "comp_156",
        "description": "Connector, JST XH 2.54 mm, 3-pin header + housing + crimps",
        "part_number": "B3B-XH-A (Kit Conectori XH2.54)",
        "notes": "J2 = LM35 (1 +5V, 2 OUT, 3 GND).",
    },
    {
        "refs": ["XU2"], "value": "DIP-8 socket", "qty": 1, "status": "inventory", "inv": "comp_235",
        "description": "IC socket, DIP-8, 300 mil",
        "part_number": "Soclu DIP 8 pini",
        "notes": "For U2 (footprint DIP-8_W7.62mm_Socket).",
    },
    {
        "refs": ["HS1"], "value": "RAD-DY-KY/3", "qty": 1, "status": "inventory", "inv": "comp_224",
        "description": "Heatsink, Stonecold RAD-DY-KY/3, TO-220/TO-3P, 40×20 mm profile, 30 mm tall, 2 PCB pins @ 34 mm, M3 thread, 6.9 K/W",
        "part_number": "RAD-DY-KY/3 (Stonecold, TME)",
        "notes": "U1 up to 5.3 W @ 30 V in → Tj ≈ Ta + 5.3·(6.9 + 3 + ~1) ≈ Ta + 58 °C. "
                 "Stands upright on its 2 solder pins; U1 sits in the fin gap, screwed to the M3 thread.",
    },
    {
        "refs": [], "value": "TO220-SET", "qty": 1, "status": "inventory", "inv": "comp_223",
        "description": "TO-220 insulating mounting set (pad + bushing), Stonecold",
        "part_number": "TO220-SET (Stonecold) — alt: Fischer MST 220 (comp_222)",
        "notes": "Required: U1 tab = V_fan, heatsink must be isolated. Add M3 screw + nut if not in the set.",
    },
    {
        "refs": ["H1", "H2", "H3", "H4"], "value": "M3", "qty": 4, "status": "buy", "inv": None,
        "description": "Board mounting: M3×10 screws + M3 nuts",
        "part_number": "any",
        "notes": "Into the 6 mm standoffs printed in the enclosure base; nuts in the hex pockets under the floor.",
    },
    {
        "refs": [], "value": "Kapton tape", "qty": 1, "status": "inventory", "inv": "comp_147",
        "description": "Kapton tape 12 mm", "part_number": "Banda Kapton 12mm",
        "notes": "Fix LM35 to the ZK-4KX rear heatsink.",
    },

    # ══ Off-board (enclosure) ════════════════════════════════════════════════
    {
        "refs": ["PS1"], "value": "ZK-4KX", "qty": 1, "status": "have", "inv": None, "offboard": True,
        "description": "Buck-boost CC/CV panel module, 5–30 V in, 0.5–30 V / 4 A out, 79×43×26 mm (cutout 71×39)",
        "part_number": "ZK-4KX (boxed panel version)",
        "notes": "35 W natural / 50 W with active cooling — the reason for this fan. Own OTP 80–110 °C. "
                 "Do not tie OUT− to IN−.",
    },
    {
        "refs": ["M1"], "value": "Fan 5V 0.2A", "qty": 1, "status": "have", "inv": None, "offboard": True,
        "description": "Fan, 30×30×10 mm, 5 V, 0.2 A, 2-wire (Raspberry Pi type)",
        "part_number": "—",
        "notes": "Runs 1.25 V (off) … ~4.75 V (full). Plug into J3.",
    },
    {
        "refs": ["J5"], "value": "DC jack 5.5×2.1", "qty": 1, "status": "inventory", "inv": "comp_231", "offboard": True,
        "description": "DC barrel jack, female, panel mount, 5.5×2.1 mm",
        "part_number": "Mufa DC mama 5.5x2.1",
        "notes": "Center = + (check the 9 V adapter). + goes to SW1; − to ZK-4KX IN− and J1 pin 2.",
    },
    {
        "refs": ["SW1"], "value": "DS-431 latching", "qty": 1, "status": "have", "inv": None, "offboard": True,
        "description": "Push switch, latching (self-locking), square 14 mm red, snap-in, 2 pins (SPST)",
        "part_number": "DS-431",
        "notes": "Power switch on the front panel, in the + wire from J5 to ZK-4KX IN+ and J1 pin 1. "
                 "Panel hole ≈ 11.7 × 11.0 mm. Check the DC current rating: ≥ 2 A for the 9 V / 2 A adapter, "
                 "≈ 5 A for a 30 V supply at the ZK-4KX's full 30 V / 4 A output.",
    },
    {
        "refs": ["J6"], "value": "Banana red", "qty": 1, "status": "inventory", "inv": "comp_226", "offboard": True,
        "description": "Banana socket 4 mm, female, red, panel", "part_number": "Mufa Banana 4mm mama rosu",
        "notes": "ZK-4KX OUT+.",
    },
    {
        "refs": ["J7"], "value": "Banana black", "qty": 1, "status": "inventory", "inv": "comp_227", "offboard": True,
        "description": "Banana socket 4 mm, female, black, panel", "part_number": "Mufa Banana 4mm mama negru",
        "notes": "ZK-4KX OUT−.",
    },
    {
        "refs": [], "value": "M3×16", "qty": 4, "status": "buy", "inv": None, "offboard": True,
        "description": "Fan mounting: M3×16 screws + M3 nuts", "part_number": "any",
        "notes": "Through the 2.4 mm left wall of the enclosure base.",
    },
    {
        "refs": [], "value": "Magnet Ø5×3", "qty": 8, "status": "inventory", "inv": "comp_193", "offboard": True,
        "description": "Neodymium magnet, Ø5 × 3 mm", "part_number": "—",
        "notes": "Lid: 4 pairs in the corner bosses of the base and cover, glued with CA. Mind the polarity.",
    },
]

STATUS_TEXT = {"inventory": "✅ inventory", "have": "✅ have", "buy": "🛒 buy"}

# ─── Schematic labels ────────────────────────────────────────────────────────
LABEL: dict[str, str] = {}
for _i in BOM:
    for _r in _i["refs"]:
        LABEL[_r] = f"{_r}\n{_i['value']}"


def write_bom_md(path: str = "bom.md") -> None:
    def row(i):
        refs = ", ".join(i["refs"]) or "—"
        status = STATUS_TEXT[i["status"]] + (" (optional)" if i.get("optional") else "")
        inv = i["inv"] or ""
        return (f"| {refs} | {i['value']} | {i['qty']} | {i['description']} | "
                f"{i['part_number']} | {status} | {inv} | {i['notes']} |")

    head = ["| Ref | Value | Qty | Description | Part number | Status | Inventory ID | Notes |",
            "|---|---|---|---|---|---|---|---|"]
    buy_req = [i for i in BOM if i["status"] == "buy" and not i.get("optional")]
    buy_opt = [i for i in BOM if i["status"] == "buy" and i.get("optional")]

    lines = ["# BOM — ZK-4KX fan temperature controller\n",
             "> Generated by `bom.py` — edit that file, then run `python bom.py`.\n",
             "## Shopping list\n", "**Required:**\n"]
    lines += [f"- {i['qty']}× **{i['value']}** — {i['description']} ({i['part_number']})" for i in buy_req]
    lines += ["", "**Optional:**\n"]
    lines += [f"- {i['qty']}× {i['value']} — {i['description']}" for i in buy_opt]
    lines += ["", "## Full BOM\n", *head, *[row(i) for i in BOM], ""]

    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    print(f"Saved: {path}")


if __name__ == "__main__":
    import sys
    sys.stdout.reconfigure(encoding="utf-8")
    write_bom_md()
