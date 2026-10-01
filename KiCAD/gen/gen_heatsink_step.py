"""STEP model of the Stonecold RAD-DY-KY/3 heatsink, built with FreeCAD from the same
dimensions as the footprint (gen_heatsink.py).

Run inside the FreeCAD GUI (colours are exported — black heatsink, silver pins), e.g. from the
Python console or the FreeCAD MCP:
  exec(open(r"<repo>/KiCAD/gen/gen_heatsink_step.py").read())
or headless (geometry only, no colours):
  "C:\\Program Files\\FreeCAD 1.1\\bin\\freecadcmd.exe" gen_heatsink_step.py
Output: KiCAD/SursaTensiune.3dshapes/RAD-DY-KY-3.step (mm; X = footprint x, Y = −footprint y, Z up).
"""
import os
import sys

import FreeCAD as App
import Part

HERE = os.path.dirname(os.path.abspath(globals().get("__file__", "")))
if not os.path.exists(os.path.join(HERE, "gen_heatsink.py")):  # exec() from the FreeCAD GUI
    HERE = r"E:\Catalin\Work\Electronics\SursaTensiune\KiCAD\gen"
sys.path.insert(0, HERE)
import importlib  # noqa: E402

import gen_heatsink as g  # noqa: E402
importlib.reload(g)

OUT = os.path.join(os.path.dirname(HERE), "SursaTensiune.3dshapes", "RAD-DY-KY-3.step")
M3_Z = g.H / 2           # M3 thread at mid-height (est. — measure)
M3_R = 1.25              # M3 tap drill Ø2.5
PIN_D = 1.5              # PCB pin Ø (est.)
PIN_BELOW, PIN_IN = 3.5, 5.0   # pin length below the board / pressed into the groove
GROOVE_R = 0.85          # pin groove in the base plate (the Ω slots in the drawing)
FIN_TIP_R = 0.5          # rounded fin tips


def box(x0, x1, y0, y1, z0, z1):
    """Box from footprint coordinates (y = footprint y); model Y = −y."""
    return Part.makeBox(x1 - x0, y1 - y0, z1 - z0, App.Vector(x0, -y1, z0))


body = box(-g.W / 2, g.W / 2, -g.PLATE, 0, 0, g.H)
for x in g.FULL_FINS:
    body = body.fuse(box(x - g.FIN_T / 2, x + g.FIN_T / 2, -g.PLATE - g.BACK_FIN, g.MOUNT_FIN, 0, g.H))
for x in g.BACK_FINS:
    body = body.fuse(box(x - g.FIN_T / 2, x + g.FIN_T / 2, -g.PLATE - g.BACK_FIN, -g.PLATE, 0, g.H))
body = body.removeSplitter()

# round the fin tips: vertical edges lying on the outer fin faces (model Y extremes)
tip_y = (g.PLATE + g.BACK_FIN, -g.MOUNT_FIN)
tips = [e for e in body.Edges
        if abs(e.Vertexes[0].Point.z - e.Vertexes[1].Point.z) > g.H - 0.01
        and all(any(abs(v.Point.y - ty) < 1e-6 for ty in tip_y) for v in e.Vertexes)]
try:
    body = body.makeFillet(FIN_TIP_R, tips)
except Exception as exc:  # keep sharp tips if OCC refuses
    print("fin fillet skipped:", exc)

# M3 thread hole through the base plate (along model Y), pin grooves along Z
body = body.cut(Part.makeCylinder(M3_R, g.PLATE + 2, App.Vector(0, -1, M3_Z), App.Vector(0, 1, 0)))
for sx in (-1, 1):
    body = body.cut(Part.makeCylinder(GROOVE_R, g.H + 2, App.Vector(sx * g.PIN_X, -g.PIN_Y, -1)))
body = body.removeSplitter()

pins = [Part.makeCylinder(PIN_D / 2, PIN_BELOW + PIN_IN, App.Vector(sx * g.PIN_X, -g.PIN_Y, -PIN_BELOW))
        for sx in (-1, 1)]

doc = App.newDocument("RAD_DY_KY_3")
hs = doc.addObject("Part::Feature", "Heatsink")
hs.Shape = body
pf = doc.addObject("Part::Feature", "Pins")
pf.Shape = Part.makeCompound(pins)
doc.recompute()

if App.GuiUp:
    import FreeCADGui as Gui
    import ImportGui
    hs.ViewObject.ShapeColor = (0.08, 0.08, 0.08)
    pf.ViewObject.ShapeColor = (0.78, 0.78, 0.80)
    ImportGui.export([hs, pf], OUT)
    Gui.SendMsgToActiveView("ViewFit")
else:
    import Import
    Import.export([hs, pf], OUT)
print("Saved:", OUT, "| fin tips rounded:", len(tips), "| colours:", App.GuiUp)
