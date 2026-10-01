# Enclosure — 3D-printable case

Parametric FreeCAD script: [`gen_enclosure.py`](gen_enclosure.py) (all dimensions at the top).
[`assembly.py`](assembly.py) places the real part models (ZK-4KX, board, fan, banana sockets, power switch, DC jack) for checking;
the result is saved as [`Enclosure_assembly.FCStd`](Enclosure_assembly.FCStd).

Outside **98 W × 128 D × 68 H mm**. Two printed parts:

| Part | What | Print |
|---|---|---|
| `Enclosure_base` (.step / .stl) | Open box: floor + all 4 walls, board standoffs, 4 corner magnet bosses | Floor down, no slicer supports (built-in breakaway pane in the ZK-4KX cutout, see below) |
| `Enclosure_cover` (.step / .stl) | Top only (the chamfered cap, split at Z 65): lip inside the walls, 4 corner magnet blocks | **Upside down** (top on the bed), no supports |

Style: rounded vertical corners (R6), 45° chamfer on the top edges (3 mm), 1.2 mm chamfer on the bottom edges
(bed adhesion / elephant foot). Front and rear panels can be printed in a second colour.

## Layout
- **Front:** ZK-4KX on top (cutout 77.4 × 39.6, 6 mm wider than the datasheet so the side clips pass, panel thinned to **1.3 mm** around it — the clips grip 1.4 mm behind
  the bezel). **Below it, one row:** power switch SW1 (DS-431, 12.7 × 11.0 mm hole) on the left, then the banana
  sockets side by side, 19.05 mm apart (fits dual banana plugs), red **+** left, black **−** right (engraved beside them).
  Output leads leave the middle of the front, not the side — fine for right- and left-handed use.
- **Rear:** DC jack Ø12.2 (M12 body) on the left, labelled "9-30V"; exhaust slots.
- **Left side:** fan 30×30×10 on the full 2.4 mm wall (Ø28.5 grille, 4× Ø3.4 holes at 24 mm). Its axis is 11 mm
  behind the ZK-4KX rear heatsink centre, so that heatsink sits under the **blades** (an axial fan blows almost nothing
  behind its Ø17 hub) and the jet (Y 24–54) also reaches the front of the board heatsink (Y 47–67). Air then leaves
  through the right-side, rear and top vents — the board heatsink's fins run front-to-back, along that path.
- **Right side:** exhaust slots.
- **Top (cover):** vents above the board heatsink, **Ø5 hole above trimmer RV1** (set the start temperature with the lid on).
- **Inside:** fan board on 4 × 6 mm standoffs behind the ZK-4KX, rotated 180°, 1.5 mm from the left wall — its front
  edge runs under the fan (the parts there, J3 and C2, stay below it), J3 right under the fan.

## Assembly
| Joint | Hardware |
|---|---|
| Fan board → base | 4× **M3×10** from the top, M3 nuts pushed into the hex pockets under the floor |
| Cover → base | 4 pairs of **Ø5×3 neodymium magnets** (comp_193) in the corners; the lip inside the walls locates it |
| Fan → base | 4× **M3×16** + nuts through the 2.4 mm left wall |
| ZK-4KX | snaps into the front cutout from the front |
| Banana sockets, DC jack | their own nuts, from inside (lid off) |
| Power switch SW1 | snaps in from the front (wire it before, or push it out from inside to rewire) |

Order: ZK-4KX, banana sockets, switch, DC jack into the base → wire them → board on the standoffs → plug J1/J2 →
fan on the left wall → plug J3 → put the cover on (it snaps down on the magnets, lift to open). Stick-on rubber feet
recommended.

**Magnets:** pockets are Ø5.3 × 3.3 deep (0.3 mm glue room; the magnet ends 0.3 mm below the face). Glue them with
a drop of CA. Mind the polarity: snap each pair together, mark the two touching faces with a
marker, pull them apart, and glue each one with the marked face out (base magnet in its boss, partner in the cover
block above it). Boss tops sit 0.2 mm below the cover blocks, so the cover rests on
the wall rim, not on the magnets.

## Fit check (done in FreeCAD with the real models)
- No collisions between the base/cover and the board, fan, banana sockets, power switch or DC jack. The only
  overlaps are the switch's snap clips (0.6 mm wedges behind the panel edge — that is how it holds) and the LM317's
  uncut 3D-model leads (see below).
- ZK-4KX (STL mesh) clear of all walls and of the fan (closest ZK part 2.9 mm from the fan face — the fan follows
  the ZK-4KX heatsink height). Banana sockets ≥ 4.5 mm and the switch ≥ 2.7 mm below the ZK-4KX body.
- Board front edge under the fan: tallest part there (C2, J3) tops out at Z 17, fan bottom at Z 26.5.
- Cover lip (Z 61.5–65) and the corner magnet bosses (Z ≥ 49, 8 × 8 mm in the corners): clear of the ZK-4KX
  (body X 14.5–85.5, top Z 60.5; its clips reach X 11–89 only at Z 35–47), of the fan (top Z 57.8) and of the
  board (Y 43–109). No overlap between base and cover.
- Trimmer hole in the lid centred on RV1's adjuster (checked on the board STEP).
- Under the board: 6 mm standoffs. **Trim all leads to ≤ 3 mm** below the PCB (the KiCad LM317 model shows uncut
  leads that would touch the floor).

## Check before printing
- Banana sockets: the model is a stand-in (Hirschmann 930176100, M6) — measure your Sigmanortec sockets' thread.
- Power switch: hole 12.7 × 11.0 mm (DS-431 model 11.7, +1 mm after the first fit test; body 11.5 × 10.8, clips on the 11.5 sides);
  change `SW_CUT` if needed. The front panel is 2.4 mm there; the clips suit 1–3 mm panels.
- ZK-4KX clip grip (1.4 mm) is from the STL model; the panel is 1.3 mm there — if the clips don't catch, reduce `ZK_PANEL`.
- The 77 mm top edge of the ZK-4KX cutout is a print bridge. The base carries its own **breakaway window pane**
  there: a 0.8 mm plate flush with the front face, standing on 7 posts (0.8 × 0.6 × 0.6 mm) on the cutout's bottom
  edge, held by 3 sprues per side across a 0.5 mm gap, its top one layer (0.2 mm) below the edge. Tuned for
  **0.2 mm layers / 0.4 mm nozzle** (cutout edges, pane and sprues on the 0.2 mm grid; cutout Z 21.2 / 60.8).
  Slicer supports off. After printing, push the pane out from inside and trim the sprue nubs on the side edges
  flush (the ZK-4KX clips run along those edges). Other layer heights: set `PANE_GAP_Z` to one layer and keep the
  cutout edges on the layer grid.
