# KiCad project — ZK-4KX fan controller

KiCad 10. Open `SursaTensiune.kicad_pro`.

## Status
- **Schematic** — complete, ERC 0 violations. Generated from `gen/gen_sch.py` + `../bom.py`.
- **PCB** — 90 × 66 mm, **routed single-sided** (B.Cu only, no vias, no jumpers) for home etching (toner transfer),
  GND = copper pour on B.Cu. DRC clean, 0 unconnected. Previews: `board.pdf`, `board_top.png`, `board_bottom.png`,
  `board_3d.png`. **Etching print:** `toner_B.Cu_1to1.pdf`. **Fab files:** `gerber/SursaTensiune_gerbers.zip`.

## Regenerating
```bash
cd gen
python check.py         # schematic from bom.py → ERC → netlist → PDF → DRC on the existing board
python check.py --pcb   # ALSO rebuilds the PCB placement — refuses while the board is routed (--force)
```
The board is routed, so it is the master now: edit the schematic in KiCad (or keep using `check.py` without
`--pcb`) and use *Tools → Update PCB from Schematic* — footprints are linked to the symbols by UUID.
`gen_pcb.py` still holds the placement (`PLACE`), so an unrouted board can always be rebuilt from it.

Gerbers (Protel extensions, F/B.Cu, F/B.Mask, F.Silkscreen, Edge.Cuts + Excellon PTH/NPTH), zipped into `gerber/`:
```bash
kicad-cli pcb export gerbers --layers F.Cu,B.Cu,F.Mask,B.Mask,F.Silkscreen,Edge.Cuts --subtract-soldermask -o out/ SursaTensiune.kicad_pcb
kicad-cli pcb export drill --format excellon --excellon-separate-th -o out/ SursaTensiune.kicad_pcb
```

## Board vs off-board
Parts with `on_board = no` are in the schematic and BOM but not on the PCB:

| Ref | Part | Connects to |
|---|---|---|
| J5 | DC jack 5.5×2.1 (panel) | VIN/GND → PS1 IN and board **J1** |
| PS1 | ZK-4KX panel module | IN+/IN− from J5; OUT+/OUT− → J6/J7 |
| J6 / J7 | Banana red / black | PS1 OUT+ / OUT− (**not** tied to GND) |
| U4 | LM35DZ on the ZK-4KX rear heatsink (fin root) | board **J2** (1 +5V, 2 OUT, 3 GND) |
| M1 | Fan 5 V 0.2 A | board **J3** (1 +, 2 −) |

## RV1 trimmer (start temperature)
Bourns 3386P 10k on the board (footprint: stock `Potentiometer_Bourns_3386P_Vertical`). Its 3D model is the
SamacSys STEP `vendor/3386P-1-103LF.stp` — **not included** (SamacSys licence: no redistribution). Download it from
[SamacSys / Component Search Engine](https://componentsearchengine.com) (part 3386P-1-103LF) and save it under that name, otherwise KiCad just shows RV1 without a 3D body. Clockwise = hotter.
Place the board so the trimmer is reachable with a screwdriver (and a multimeter probe on U2 pin 7).

## Home-etching rules (toner transfer)
- **Tracks 1.0 mm, clearance 0.5 mm** (net class Default in the project), copper 1 mm from the board edge.
- **Pads enlarged** by `gen_pcb.py` (`toner_pads`): copper ring ≥ 0.5 mm per side; where the pitch is too tight
  (TO-220, XH, 2 mm electrolytics) the pad becomes oval, keeping ≥ 0.6 mm between pads. That is why DRC's
  *footprint differs from library* and *silkscreen clipped by pad* checks are set to ignore.
- **U3 on `TO-92_Inline_Wide`** (2.54 mm pitch instead of 1.27 mm) — room for real pads; splay the leads slightly.
- **No track between IC pins** (1.8 mm pads at 2.54 mm leave 0.74 mm).
- **GND pour:** 0.8 mm clearance, 0.5 mm minimum width, thermal reliefs 0.6 mm gap / 0.8 mm spokes.
- Drills: **0.8 mm** R, C, U2, U3, RV1 · **0.95 / 1.0 mm** J2 / J1, J3 · **1.1 mm** U1, D1 · **2.2 mm** HS1 pins ·
  **3.2 mm** mounting holes.
- Print `toner_B.Cu_1to1.pdf` at **100 % (no "fit to page")**, **not mirrored** — the bottom layer is shown as seen
  from the top, which is what toner transfer needs (the paper goes face-down on the copper). Check the 90 × 66 mm
  outline with a ruler before transferring.
- The PDF is **A4 portrait**, everything at the top of the page (boards 11–77 mm from the top edge, left one at
  11–101 mm, right one at 111–201 mm), so the rest of the sheet can be cut off and reused.
- Page 1 has B.Cu (left) and, next to it, the **F.SilkS mirrored** (right) for toner transfer onto the
  component side (align on the drill holes). Page 2: F.SilkS as seen from the top — assembly reference.
  Page 3: **B.Mask twice** (+ outline), same orientation as B.Cu — black = pad openings, i.e. the film for a
  UV-cured solder mask (opaque pads block the UV, the rest cures). The two copies are cut apart and stacked.
- Page layout: layers plotted with `kicad-cli pcb export pdf --black-and-white` (+ `--mirror` for the silk,
  `--drill-shape-opt 0` for the mask), cropped to the outline ± 1 mm and placed 1:1 with PyMuPDF.

## Layout (single-sided)
Made in `gen/route_trial.py` — 5 rounds, each placement routed with both **Freerouting 2.4.1** and
**KiCadRoutingTools** (`gen/freeroute.py`: B.Cu only; for Freerouting F.Cu is declared a plane layer in the DSN).
HS1/U1 and the mounting holes are fixed (airflow, enclosure). Main ideas:
- Front strip: VFAN runs from U1 under the heatsink to C2 / R4 / D1 / J3 (J3 near the fan); VIN from U1 to C3 / U3 / J1.
- U2 (LM358) is behind R2 (10k): R2 bridges N_INV (pin 2) and VREF (pins 6/7), and VADJ, LM35_OUT and +5V pass
  under its body. LM35_OUT uses the channel between the socket's pin rows.
- C5 and R1 hang off the +5V track; WIPER runs between RV1's GND and POT_TOP pads; R1-2 sits right next to RV1's
  POT_TOP pad and C3 right next to U3's input so no track can split them.
- Op-amp and its resistors are at the back, ≈ 20 mm from HS1 and away from the ZK-4KX heatsink side.
- **GND is only the pour** — routing it as tracks first made both routers wall off other nets.

| Round | Change | Freerouting | KiCadRoutingTools |
|---|---|---|---|
| 1 | first single-sided placement | 3 unconnected | 6 |
| 2 | C5 / R1 below the +5V track, RV1 upright | 2 | 2 |
| 3 | R1 over RV1, C3 moved | 5 | 7 |
| 4 | round 2 + tight pad pairs (R1–RV1, C3–U3) | 3 | 4 |
| 5 | round 4, GND as pour only | 4 | **0** ← used |

The board is the KiCadRoutingTools result of round 5 (166 tracks, all 1.0 mm; a 0.02 mm stub removed).
Freerouting kept failing a few very short hops (U2 pin 6↔7, R1↔RV1, C3↔U3). The trial boards are written to
`trial/` (not in git).

## Check against the real parts before ordering the PCB
- **HS1 RAD-DY-KY/3** — footprint `SursaTensiune.pretty/Heatsink_Stonecold_RAD-DY-KY-3_40x20mm_P34mm` and 3D model
  `SursaTensiune.3dshapes/RAD-DY-KY-3.step` (black solid, fillets, pin grooves — built in FreeCAD by `gen/gen_heatsink_step.py`), footprint by `gen/gen_heatsink.py`, both from the Stonecold RAD-DY-KY datasheet ([TME](https://www.tme.eu/en/katalog/?search=RAD-DY-KY%2F3))
  (40×20 mm profile, 4 mm base, 30 mm tall, 2 PCB pins at 34 mm, M3 thread). Measure and correct in `gen_heatsink.py`:
  pin Ø (hole is 2.2 mm), pin position in the plate (y = −1.5 mm), fin gap on the mounting side (19.6 mm), fin heights.
  U1 sits in the fin gap, tab 0.2 mm (insulating pad) from the mounting face.
  **U1 height:** if the heatsink's M3 hole is at mid-height (15 mm), the TO-220 body must stand ≈ 2 mm above the PCB
  for the tab hole to line up — check before soldering U1.
- **C1/C3/C5** (K104K10X7RF5UH5) — footprint assumes 5.0 mm lead pitch; measure.
- **C2/C4** (EEAGA1E100H, 5 mm Ø) — 2.0 mm pitch footprint.
- **U3 UA78L05** (TO-92 on the wide 2.54 mm footprint) / **U4 LM35** pinouts verified against the KiCad symbols (TO-92: OUT-GND-IN / +Vs-OUT-GND).
