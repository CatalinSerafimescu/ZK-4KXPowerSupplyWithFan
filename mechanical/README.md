# Mechanical files

| File | What |
|---|---|
| Heatsink datasheet | Stonecold RAD-DY-KY profile drawing (40×20 mm, 4 mm base, pins at 34 mm, M3, 6.9 K/W for L = 30 mm) — not included, see [TME](https://www.tme.eu/en/katalog/?search=RAD-DY-KY%2F3) |
| `heatsink/RAD-DY-KY.jpg`, `RAD-DY-KY_top.jpg` | TME photo and profile — source for the KiCad footprint (`../KiCAD/gen/gen_heatsink.py`) |
| `stl/ZK-4KX Buck Boost Converter.STL` | ZK-4KX panel module, 79 × 54 × 42.5 mm — by Legacy_Micro, [Printables 401707](https://www.printables.com/model/401707-basic-model-zk-4kx-buck-boost-converter), CC0 |
| `pcb/SursaTensiune_board.step` | Whole fan-controller board with all parts, **including the heatsink** (KiCad export, solids — best for FreeCAD) |
| `pcb/SursaTensiune_board.stl` | Same board as a mesh — 90 × 66 × 39.7 mm |
| `trimmer/3386P-1-103LF.stp` | Bourns 3386P trimmer — **not included** (SamacSys licence: no redistribution). Download from [SamacSys / Component Search Engine](https://componentsearchengine.com), part 3386P-1-103LF. |
| `banana/930176100.stp` | 4 mm banana panel socket (Hirschmann 930176100), ≈ 33 × 15 × 10 mm — **not included** (SamacSys licence: no redistribution). Download from [SamacSys / Component Search Engine](https://componentsearchengine.com); needed by `enclosure/assembly.py`. Stand-in for J6/J7 — the Sigmanortec sockets may differ slightly, measure. |
| `dc_jack/DC_jack_5.5x2.1_panel_10A.step` (+ 2 renders) | Panel-mount DC jack 5.5×2.1 mm, 10 A — the one on the case (J5). ≈ 14 × 24 × 20 mm, threaded body + nut, 3 solder tabs. From [GrabCAD](https://grabcad.com/library/power-jack-socket-5-5-x-2-1-mm-10a-dc-1). |
| `button/DS-431_square_push_button_red.step` | Power switch SW1: DS-431 latching push switch, 14 × 14 mm rim, 11.5 × 10.8 mm body with snap clips, 20 mm deep incl. the 2 solder tabs |
| `fan/Fan_30x30x10_5V_2pin.step` (+ `.png`) | 30×30×**10** mm 2-pin 5 V fan (M1). Made in FreeCAD from A. Kirchner's 30×30×8 model ([GrabCAD](https://grabcad.com/library/fan-30x30x8mm-5v-2-pin-1)): frame cut at mid-height, top half raised 2 mm and the gap filled (valid solid, exact planes/cylinders, holes unchanged); rotor unchanged, centred. The original rotor had broken face trims (drawn as an endless tube along the fan axis, reappearing after every STEP round trip), so it was replaced by a clean hub + 7 pitched blades. 203 KB, opens in < 1 s. FreeCAD version: `stl/Fan10.FCStd`. |

The fan mount STL that came with the ZK-4KX model is not used.

Board exports are regenerated with `kicad-cli pcb export step|stl --subst-models` after PCB changes.

KiCad cannot use STL as a 3D model (STEP/VRML only); the fan and ZK-4KX are off-board, so these models are
for the enclosure design. Heatsink 3D: `../KiCAD/SursaTensiune.3dshapes/RAD-DY-KY-3.step` — black solid with rounded fins, pin grooves and the
M3 hole, built in FreeCAD by `../KiCAD/gen/gen_heatsink_step.py` (run it inside the FreeCAD GUI to keep the colours).
Enclosure: see [`enclosure/`](enclosure/README.md). Solder-mask jig (holds the PCB flush under the mask film):
[`mask_jig/`](mask_jig/README.md).
