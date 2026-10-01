"""Place the real part models into the "Enclosure" document (run gen_enclosure.py first).

Run with the FreeCAD MCP execute_code_async (loads heavy STEP files off the GUI thread) or
from the Python console (then commit() is not available — call place(load()) directly).
Placements follow gen_enclosure.py parameters.
"""
import os

import FreeCAD as App
import Mesh
import Part

V, Rot, Pl = App.Vector, App.Rotation, App.Placement
M = r"E:\Catalin\Work\Electronics\SursaTensiune\mechanical"
g = {}
exec(open(os.path.join(M, "enclosure", "gen_enclosure.py"), encoding="utf-8").read().split("# ── Helpers")[0], g)


def load():
    return {
        "ZK": Mesh.Mesh(os.path.join(M, "stl", "ZK-4KX Buck Boost Converter.STL")),
        "Board": Part.read(os.path.join(M, "pcb", "SursaTensiune_board.step")),
        "Fan": Part.read(os.path.join(M, "fan", "Fan_30x30x10_5V_2pin.step")),
        "Banana": Part.read(os.path.join(M, "banana", "930176100.stp")),
        "Jack": Part.read(os.path.join(M, "dc_jack", "DC_jack_5.5x2.1_panel_10A.step")),
        "Switch": Part.read(os.path.join(M, "button", "DS-431_square_push_button_red.step")),
    }


def board_placement(shape):
    """Rotate 180° about Z and put the PCB (90×66×1.6 solid) on the standoffs."""
    pcb = max(shape.Solids, key=lambda s: s.BoundBox.XLength * s.BoundBox.YLength
              if abs(s.BoundBox.ZLength - 1.6) < 0.2 else 0)
    s = pcb.copy()
    s.rotate(V(0, 0, 0), V(0, 0, 1), 180)
    b = s.BoundBox
    return Pl(V(g["BX0"] - b.XMin, g["BY0"] - b.YMin, g["T"] + g["STANDOFF_H"] - b.ZMin), Rot(V(0, 0, 1), 180))


def place(parts, doc_name="Enclosure"):
    doc = App.getDocument(doc_name)
    # breakaway print pane is removed before the ZK-4KX goes in: re-cut the cutout (only the pane is left in it)
    base = doc.getObject("Base")
    cx, cz = g["ZK_CUT"]
    base.Shape = base.Shape.cut(Part.makeBox(cx, g["T"] + 2, cz, V(g["ZK_X"] - cx / 2, -1, g["ZK_Z"] - cz / 2)))
    for n in ("ZK4KX", "Board", "Fan", "Banana_red", "Banana_black", "DC_jack", "Switch"):
        if doc.getObject(n):
            doc.removeObject(n)
    zk = doc.addObject("Mesh::Feature", "ZK4KX")
    zk.Mesh = parts["ZK"]
    zk.Placement = Pl(V(g["ZK_X"] - 2.34, 15.375, g["ZK_Z"] - 23.13), Rot(V(0, 0, 1), 90))
    bd = doc.addObject("Part::Feature", "Board")
    bd.Shape = parts["Board"]
    bd.Placement = board_placement(parts["Board"])
    fan = doc.addObject("Part::Feature", "Fan")
    fan.Shape = parts["Fan"]
    # fan axis → +X (blows into the box); turned 180° on its axis so the wire corner is at the
    # rear-bottom (free space behind the ZK-4KX), not against the ZK-4KX body
    fan.Placement = Pl(V(g["T"], g["FAN_Y"], g["FAN_Z"]), Rot(V(0, 1, 0), 90).multiply(Rot(V(0, 0, 1), 180)))
    for name, dx in (("Banana_red", 0.0), ("Banana_black", g["BANANA_P"])):
        b = doc.addObject("Part::Feature", name)
        b.Shape = parts["Banana"]
        # model axis x: Ø10.5 flange ends at x = 11.0 → on the front face (Y = 0), M6 thread through the panel
        b.Placement = Pl(V(g["BANANA_X"] + dx, -11.0, g["ROW_Z"]), Rot(V(0, 0, 1), 90))
    j = doc.addObject("Part::Feature", "DC_jack")
    j.Shape = parts["Jack"]
    # model axis y: Ø13.8 flange ends at y = 1.8 → on the rear face (Y = D), M12 thread through the panel
    j.Placement = Pl(V(g["JACK_X"], g["D"] + 1.8, g["JACK_Z"]), Rot(V(0, 0, 1), 180))
    sw = doc.addObject("Part::Feature", "Switch")
    sw.Shape = parts["Switch"]
    # model axis z: rim underside at z = 0 → on the front face, body into the box; snap clips (model y) along X
    sw.Placement = Pl(V(g["SW_X"], 0, g["ROW_Z"]), Rot(V(1, 0, 0), 90).multiply(Rot(V(0, 0, 1), 90)))
    doc.recompute()
    if App.GuiUp:
        # solids: 0 = movable cap (red), 1 = housing + rim (black), 2-3 = solder tabs (metal)
        cols = {0: (0.85, 0.1, 0.1), 1: (0.08, 0.08, 0.08)}
        sw.ViewObject.DiffuseColor = [cols.get(i, (0.75, 0.75, 0.75))
                                      for i, so in enumerate(sw.Shape.Solids) for _ in so.Faces]
        zk.ViewObject.ShapeColor = (0.55, 0.60, 0.70)
        bd.ViewObject.ShapeColor = (0.10, 0.45, 0.20)
        fan.ViewObject.ShapeColor = (0.25, 0.25, 0.25)
        doc.getObject("Banana_red").ViewObject.ShapeColor = (0.8, 0.1, 0.1)
        doc.getObject("Banana_black").ViewObject.ShapeColor = (0.1, 0.1, 0.1)
        j.ViewObject.ShapeColor = (0.6, 0.6, 0.6)
    return doc
