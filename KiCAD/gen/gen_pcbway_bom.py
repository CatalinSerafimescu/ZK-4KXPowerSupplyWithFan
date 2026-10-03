"""PCBWay assembly BOM (their Sample_BOM_PCBWay.xlsx template) for the parts soldered on the board.

Refs, quantities and descriptions come from bom.py; footprints from the routed board; manufacturer part
numbers from MPN below (bom.py holds shop names for some parts). Off-board parts and mounting holes are left out.
Run: python gen_pcbway_bom.py  →  ../SursaTensiune_BOM_PCBWay.xlsx
"""
import io
import re
import sys
import urllib.request
from pathlib import Path

import openpyxl
from openpyxl.styles import Alignment, Font

PRJ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PRJ.parent))
from bom import BOM  # noqa: E402

TEMPLATE = "https://www.pcbway.com/img/images/pcbway/Sample_BOM_PCBWay.xlsx?v=1.1"
OUT = PRJ / "SursaTensiune_BOM_PCBWay.xlsx"

# value → (manufacturer, MPN, notes); "or equivalent" where bom.py names no exact part
MPN = {
    "LM317T": ("Texas Instruments", "LM317T/NOPB",
               "Mount on HS1 with the TO-220 insulating kit (pad + shoulder bushing) and an M3 screw before soldering: "
               "the tab is OUT and must be isolated from the heatsink (check: open circuit tab-heatsink)."),
    "LM358AP": ("Texas Instruments", "LM358AP", "Insert into the DIP-8 socket (XU2), do not solder."),
    "UA78L05": ("Texas Instruments", "UA78L05AILP",
                "Pin 1 (square pad) = OUTPUT; pinout reversed vs 7805. Pads 2.54 mm apart: splay the legs."),
    "100 kΩ": ("Yageo", "MFR-25FBF52-100K", "1/4 W 1 % metal film, or equivalent."),
    "10 kΩ": ("Yageo", "MFR-25FBF52-10K", "1/4 W 1 % metal film, or equivalent."),
    "220 Ω": ("Yageo", "MFR-25FBF52-220R", "1/4 W 1 % metal film, or equivalent."),
    "10k": ("Bourns", "3386P-1-103LF", ""),
    "100 nF": ("Vishay", "K104K10X7RF5UH5", "5 mm lead pitch."),
    "10 µF": ("Panasonic", "EEA-GA1E100H", "Polarised: + on the square pad."),
    "1N4007": ("Any", "1N4007", "Band (cathode) on the square pad K."),
    "XH 2-pin": ("JST", "B2B-XH-A", "Header only; latch side as on the silkscreen."),
    "XH 3-pin": ("JST", "B3B-XH-A", "Header only; latch side as on the silkscreen."),
    "DIP-8 socket": ("Any", "DIP-8 socket, 300 mil", "At U2; notch towards pin 1."),
    "RAD-DY-KY/3": ("Stonecold", "RAD-DY-KY/3", "Heatsink, 2 solder pins; stands 30 mm tall."),
    "TO220-SET": ("Stonecold", "TO220-SET", "Insulating kit for U1 on HS1, plus an M3 screw if not in the set."),
}

# board footprints by reference
pcb = (PRJ / "SursaTensiune.kicad_pcb").read_text(encoding="utf-8")
FP = {m.group(2): m.group(1).split(":")[1]
      for m in re.finditer(r'\(footprint "([^"]+)".*?\(property "Reference" "([^"]+)"', pcb, re.S)}
FP["XU2"] = FP["U2"]                     # the socket sits on U2's footprint
FP["U1/HS1"] = FP["HS1"]

rows = []
for it in BOM:
    if it.get("offboard") or it["value"] not in MPN:
        continue
    refs = it["refs"] or (["U1/HS1"] if it["value"] == "TO220-SET" else [])
    mfr, mpn, note = MPN[it["value"]]
    desc = it["description"].replace("carbon film, ", "")      # MPNs below are metal film
    rows.append((",".join(refs), it["qty"], mfr, mpn, desc, FP[refs[0]], "thru-hole", note))

wb = openpyxl.load_workbook(io.BytesIO(urllib.request.urlopen(
    urllib.request.Request(TEMPLATE, headers={"User-Agent": "Mozilla/5.0"})).read()))
ws = wb["Sheet1"]
ws["D2"] = f"ZK-4KX fan controller rev 1.1 — {len(rows)} lines BOM (through-hole, single-sided)"
for r in range(7, 22):                   # clear the template's sample rows
    for c in range(1, 10):
        ws.cell(r, c).value = None
assert len(rows) <= 17, "template has rows 7–23 free above its footer notes (merged cells at row 24)"
font = Font(name="Arial", size=10)
for i, row in enumerate(rows):
    r = 7 + i
    for c, v in enumerate((i + 1,) + row, start=1):
        cell = ws.cell(r, c, v)
        cell.font = font
        cell.alignment = Alignment(vertical="top", wrap_text=c in (6, 9))
wb.save(OUT)
print(f"{len(rows)} lines → {OUT}")
