"""Solder-mask jig: holds the etched PCB flush with a flat frame so the mask film lies flat on paste + frame.

Run inside the FreeCAD GUI (Python console or MCP):
    exec(open(r"<repo>/mechanical/mask_jig/gen_mask_jig.py", encoding="utf-8").read())
Creates document "MaskJig" with object Jig, exports Mask_jig.step / .stl next to this script.

Coordinates (mm): origin = bottom-left outer corner, X along the 90 mm board edge, Z = up.
- Pocket 1.4 deep for 1.5–1.6 mm board: the copper sits 0.1–0.2 mm PROUD of the frame, so the film is pressed onto
  the board, never left hanging over a recessed board. Too low → a paper shim under the board.
- 4 × Ø3.2 through holes at the board's M3 mounting holes (4 mm in from each corner): pins (Ø3 drill-bit shanks)
  pushed up from below register board + punched film; pull them out downwards before the glass goes on.
- Corner reliefs so the square board corners fit in an FDM pocket; 2 push-out holes to lift the board from below.
Print floor-down, no supports, 0.2 mm layers (all Z heights on the 0.2 grid).
"""
import os

import FreeCAD as App
import Part

V = App.Vector
OUT = r"E:\Catalin\Work\Electronics\SursaTensiune\mechanical\mask_jig"   # exec() under the MCP sees its own __file__

BW, BH = 90.0, 66.0            # board outline (KiCad Edge.Cuts)
GAP = 0.4                      # clearance per side (board is hand-cut; the pins do the registering)
BORDER = 10.0                  # flat frame around the pocket, for the film
FLOOR = 3.0                    # floor under the board — also guides the pins
POCKET = 1.4                   # pocket depth, < board thickness
PIN_D = 3.2                    # board mounting holes are 3.2 mm
PINS = [(4, 4), (86, 4), (4, 62), (86, 62)]   # board coords from the bottom-left corner
RELIEF_D = 2.0                 # pocket corner reliefs
PUSH_D = 12.0                  # push-out holes
PUSH = [(30, 33), (60, 33)]

PX0 = PY0 = BORDER             # pocket corner
PW, PH = BW + 2 * GAP, BH + 2 * GAP
BX0, BY0 = PX0 + GAP, PY0 + GAP  # board corner
W, H, T = PW + 2 * BORDER, PH + 2 * BORDER, FLOOR + POCKET


def cyl(x, y, d, z0=-1, h=None):
    return Part.makeCylinder(d / 2, (h or T + 2), V(x, y, z0))


def build():
    jig = Part.makeBox(W, H, T)
    cut = [Part.makeBox(PW, PH, POCKET + 1, V(PX0, PY0, FLOOR))]
    cut += [cyl(x, y, RELIEF_D, FLOOR) for x in (PX0, PX0 + PW) for y in (PY0, PY0 + PH)]
    cut += [cyl(BX0 + x, BY0 + y, PIN_D) for x, y in PINS]
    cut += [cyl(BX0 + x, BY0 + y, PUSH_D) for x, y in PUSH]
    return jig.cut(Part.makeCompound(cut)).removeSplitter()


doc = App.newDocument("MaskJig") if "MaskJig" not in App.listDocuments() else App.getDocument("MaskJig")
for o in doc.Objects:
    doc.removeObject(o.Name)
shape = build()
obj = doc.addObject("Part::Feature", "Jig")
obj.Shape = shape
doc.recompute()
shape.exportStep(os.path.join(OUT, "Mask_jig.step"))
shape.exportStl(os.path.join(OUT, "Mask_jig.stl"))
print("Jig %.1f x %.1f x %.1f mm, pocket %.1f x %.1f x %.1f, valid=%s, volume=%.0f mm3"
      % (W, H, T, PW, PH, POCKET, shape.isValid(), shape.Volume))
