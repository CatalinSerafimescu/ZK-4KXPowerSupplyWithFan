"""Parametric 3D-printable enclosure for the ZK-4KX bench supply + fan controller.

Run inside the FreeCAD GUI (Python console or MCP):
    exec(open(r"<repo>/mechanical/enclosure/gen_enclosure.py", encoding="utf-8").read())
Creates document "Enclosure" with objects Base and Cover, and exports
Enclosure_base / Enclosure_cover as .step and .stl next to this script.

Coordinates (mm): X = left→right seen from the front, Y = front→back, Z = up.
Origin = front-left-bottom outer corner.

Parts
- Base  = open box: floor + all 4 walls (+ standoffs, magnet bosses). Everything that is screwed/snapped
          (ZK-4KX, banana sockets, DC jack, fan board, fan) sits on it — full access from the top.
- Cover = top only (the 45° chamfered cap), located by a lip inside the walls, held by 4 magnet pairs.
Print: Base floor-down; Cover upside-down (top on the bed). No slicer supports: the base carries its own
breakaway pane in the ZK-4KX cutout (push it out before fitting the ZK-4KX).
"""
import math
import os

import FreeCAD as App
import Part

V = App.Vector
HERE = os.path.dirname(os.path.abspath(globals().get("__file__", "")))
if not os.path.exists(os.path.join(HERE, "gen_enclosure.py")):
    HERE = r"E:\Catalin\Work\Electronics\SursaTensiune\mechanical\enclosure"

# ── Main dimensions ───────────────────────────────────────────────────────────
W, D, H = 98.0, 128.0, 68.0      # outside
T = 2.4                          # wall / floor / top thickness
R = 6.0                          # vertical corner radius (= depth of the front/rear caps)
CT, CB = 3.0, 1.2                # top-edge chamfer (style + upside-down printing), bottom chamfer (bed)
ZS = H - CT                      # base / cover split, where the top chamfer starts

# ── ZK-4KX (from mechanical/stl model) ───────────────────────────────────────
ZK_X, ZK_Z = 50.0, 41.0          # centre of bezel / cutout on the front (outputs + switch in a row below)
ZK_CUT = (77.4, 39.6)            # datasheet 71×39 + clearance, +6 on width (fit test: the side clips must pass);
                                 # edges at Z 21.2 / 60.8 (on the 0.2 mm layer grid)
ZK_PANEL = 1.3                   # clips grip 1.4 mm behind the bezel (STL) → 1.3 local panel = 0.1 play
ZK_POCKET = (81.0, 45.0)         # thinned area (clips stand 3.4 mm out on the left/right)
ZK_HS_Y, ZK_HS_Z = 27.9, ZK_Z + 1.77   # ZK rear heatsink centre (depth behind front face, height)
# Breakaway "window pane" for the 77 mm top edge of the cutout (a bridge when the base prints floor-down).
# A thin plate in the plane of the front face stands on short posts on the cutout's bottom edge, is held at the
# sides by small sprues across a gap, and stops one layer below the top edge (like a slicer's support Z distance),
# so the top edge prints on it but hardly fuses. Push it out from inside after printing.
PANE_T = 0.8                     # plate thickness, flush with the front face (2 lines of a 0.4 nozzle)
PANE_GAP_X, PANE_GAP_Z = 0.5, 0.2   # side gap (wide enough that the slicer keeps it open), top gap = 1 layer
PANE_POSTS, PANE_POST = 7, (0.8, 0.6, 0.6)   # posts on the bottom edge: count, X, Y, height (Z)
PANE_SPRUES, PANE_SPRUE_H = (1 / 4, 1 / 2, 3 / 4), 0.6   # side sprues at these fractions of the height, 3 layers

# ── Front / rear hardware ────────────────────────────────────────────────────
ROW_Z = 10.0                     # row under the ZK-4KX: power switch, red +, black − (clear of floor and bezel)
BANANA_X, BANANA_P, BANANA_D = 58.0, 19.05, 6.4    # red at BANANA_X, black 19.05 mm to its right
SW_X, SW_CUT = 23.0, (12.7, 11.0)                   # DS-431 latching switch, rim 14×14, snap clips left/right
                                                    # (+1 on width after the fit test)
JACK_X, JACK_Z, JACK_D = 17.0, 34.0, 12.2                           # DC jack M12 body

# ── Fan (left wall), 30×30, holes 24 mm, bore 28.5 ───────────────────────────
# Axis 11 mm behind the ZK heatsink centre: the heatsink sits under the blades (not in the dead zone behind
# the Ø17 hub) and the jet (Y 24…54) also reaches the front of the board heatsink (Y 47…67, fins along Y).
FAN_Y, FAN_Z = ZK_HS_Y + 11.0, ZK_HS_Z
FAN_HOLE_P, FAN_HOLE_D, FAN_BORE = 24.0, 3.4, 28.5

# ── Fan-controller board (90×66, M3 holes 4 mm from the corners), rotated 180° ─
BX0, BY0 = T + 1.5, 43.0                 # board outline X 3.9…93.9, Y 43…109 (its front edge runs under the fan)
STANDOFF_H, STANDOFF_D = 6.0, 7.0
BOARD_HOLES = [(BX0 + 4, BY0 + 4), (BX0 + 86, BY0 + 4), (BX0 + 4, BY0 + 62), (BX0 + 86, BY0 + 62)]
TRIM_XY = (BX0 + 90 - 57.32, BY0 + 56.64)             # RV1 adjuster seen from the top (RV1 at 58, 59)
HS_BOARD = (BX0 + 90 - 50, BX0 + 90 - 10, BY0 + 4, BY0 + 24)   # board heatsink area (x0,x1,y0,y1)

M3_CLR, M3_NUT_F, M3_NUT_T = 3.4, 5.8, 2.6

# ── Cover: lip inside the walls + 4 magnet pairs (Ø5×3 neodymium, comp_193) in the corners ─
LIP_GAP, LIP_W, LIP_H = 0.2, 1.6, 3.5    # clearance to the walls, lip width, depth below ZS
MAG_D, MAG_H = 5.0, 3.0
MAG_CLR = 0.3                            # pocket Ø+0.3 and 0.3 deeper: glue room, magnet ends below the face
BOSS = 8.0                               # corner boss footprint (clear of the ZK-4KX body X 14.5…85.5)
BOSS_GAP = 0.2                           # between base boss top and cover block → the cover seats on the rim


# ── Helpers ───────────────────────────────────────────────────────────────────
def rounded_box(w, d, h, r, ct, cb, origin=V(0, 0, 0)):
    s = Part.makeBox(w, d, h)
    s = s.makeFillet(r, [e for e in s.Edges if abs(e.Vertexes[0].Point.z - e.Vertexes[1].Point.z) > h - 1e-6])
    top = [e for e in s.Edges if all(abs(v.Point.z - h) < 1e-6 for v in e.Vertexes)]
    s = s.makeChamfer(ct, top)
    bot = [e for e in s.Edges if all(abs(v.Point.z) < 1e-6 for v in e.Vertexes)]
    s = s.makeChamfer(cb, bot)
    s.translate(origin)
    return s


def box(x0, x1, y0, y1, z0, z1):
    return Part.makeBox(x1 - x0, y1 - y0, z1 - z0, V(x0, y0, z0))


def cyl(d, p, axis, length):
    return Part.makeCylinder(d / 2, length, p, axis)


def slot_y(y, z0, z1, x0, x1, w):          # vertical slot in a wall normal to X (width along Y)
    r = w / 2
    s = box(x0, x1, y - r, y + r, z0 + r, z1 - r)
    s = s.fuse([cyl(w, V(x0, y, z0 + r), V(1, 0, 0), x1 - x0), cyl(w, V(x0, y, z1 - r), V(1, 0, 0), x1 - x0)])
    return s


def slot_x(x, z0, z1, y0, y1, w):          # vertical slot in a wall normal to Y (width along X)
    r = w / 2
    s = box(x - r, x + r, y0, y1, z0 + r, z1 - r)
    return s.fuse([cyl(w, V(x, y0, z0 + r), V(0, 1, 0), y1 - y0), cyl(w, V(x, y0, z1 - r), V(0, 1, 0), y1 - y0)])


def slot_top(x, y0, y1, w):                # slot through the top, long along Y
    r = w / 2
    s = box(x - r, x + r, y0 + r, y1 - r, H - T - 1, H + 1)
    return s.fuse([cyl(w, V(x, y0 + r, H - T - 1), V(0, 0, 1), T + 2), cyl(w, V(x, y1 - r, H - T - 1), V(0, 0, 1), T + 2)])


def hex_prism(cx, cy, flats, z0, z1):
    rc = flats / math.sqrt(3)
    pts = [V(cx + rc * math.cos(math.radians(60 * i)), cy + rc * math.sin(math.radians(60 * i)), z0) for i in range(6)]
    return Part.Face(Part.makePolygon(pts + [pts[0]])).extrude(V(0, 0, z1 - z0))


def rrect(x0, x1, y0, y1, r, z0, z1):     # box with rounded vertical edges
    s = box(x0, x1, y0, y1, z0, z1)
    return s.makeFillet(r, [e for e in s.Edges if abs(e.Vertexes[0].Point.z - e.Vertexes[1].Point.z) > 1e-6])


def corners(shape):                        # a front-left corner feature copied to all 4 corners
    fr = shape.mirror(V(W / 2, 0, 0), V(1, 0, 0))
    return [shape, fr, shape.mirror(V(0, D / 2, 0), V(0, 1, 0)), fr.mirror(V(0, D / 2, 0), V(0, 1, 0))]


def text(s, size, font=r"C:\Windows\Fonts\arialbd.ttf"):
    """Flat text faces in the XY plane (FreeCAD ShapeString helper); None if unavailable."""
    try:
        import Part as _P
        wires = _P.makeWireString(s, font, size, 0)
        faces = []
        for ch in wires:
            if ch:
                faces.append(_P.Face(_P.Compound(ch), "Part::FaceMakerBullseye") if len(ch) > 1 else _P.Face(ch[0]))
        return _P.Compound(faces) if faces else None
    except Exception as exc:
        print("text skipped:", s, exc)
        return None


def engrave_front(shape, s, x, z, size, depth=0.6):
    t = text(s, size)
    if t is None:
        return shape
    bb = t.BoundBox
    t.translate(V(-bb.Center.x, -bb.Center.y, 0))
    t.rotate(V(0, 0, 0), V(1, 0, 0), 90)            # XY → XZ, readable from the front
    t.translate(V(x, 0, z))
    return shape.cut(t.extrude(V(0, depth, 0)).translated(V(0, -0.01, 0)))


def engrave_rear(shape, s, x, z, size, depth=0.6):
    t = text(s, size)
    if t is None:
        return shape
    bb = t.BoundBox
    t.translate(V(-bb.Center.x, -bb.Center.y, 0))
    t.rotate(V(0, 0, 0), V(1, 0, 0), 90)
    t.rotate(V(0, 0, 0), V(0, 0, 1), 180)           # readable from behind
    t.translate(V(x, D, z))
    return shape.cut(t.extrude(V(0, -depth, 0)).translated(V(0, 0.01, 0)))


# ── Shell ─────────────────────────────────────────────────────────────────────
outer = rounded_box(W, D, H, R, CT, CB)
k = math.sqrt(2) - 1
inner = rounded_box(W - 2 * T, D - 2 * T, H - 2 * T, R - T, CT - k * T, max(CB - k * T, 0.2), V(T, T, T))
shell = outer.cut(inner)

cuts = []
# front: ZK cutout + thinned clip pocket, banana holes
cuts.append(box(ZK_X - ZK_CUT[0] / 2, ZK_X + ZK_CUT[0] / 2, -1, T + 1, ZK_Z - ZK_CUT[1] / 2, ZK_Z + ZK_CUT[1] / 2))
cuts.append(box(ZK_X - ZK_POCKET[0] / 2, ZK_X + ZK_POCKET[0] / 2, ZK_PANEL, T + 0.5, ZK_Z - ZK_POCKET[1] / 2, ZK_Z + ZK_POCKET[1] / 2))
for dx in (0.0, BANANA_P):
    cuts.append(cyl(BANANA_D, V(BANANA_X + dx, -1, ROW_Z), V(0, 1, 0), T + 2))
cuts.append(box(SW_X - SW_CUT[0] / 2, SW_X + SW_CUT[0] / 2, -1, T + 1, ROW_Z - SW_CUT[1] / 2, ROW_Z + SW_CUT[1] / 2))
# rear: DC jack + exhaust slots
cuts.append(cyl(JACK_D, V(JACK_X, D - T - 1, JACK_Z), V(0, 1, 0), T + 2))
for i in range(9):
    cuts.append(slot_x(JACK_X + 13 + i * 6, 12, 48, D - T - 1, D + 1, 3.0))
# left wall: fan grille, screw holes (full wall: M3×16 + nuts for the fan)
grille = cyl(FAN_BORE, V(-1, FAN_Y, FAN_Z), V(1, 0, 0), T + 2)
bars = [box(-2, T + 2, FAN_Y + y - 1.1, FAN_Y + y + 1.1, FAN_Z - 20, FAN_Z + 20) for y in [i * 3.4 - 13.6 for i in range(9)]]
cuts.append(grille.common(bars[0].fuse(bars[1:])))
for dy in (-FAN_HOLE_P / 2, FAN_HOLE_P / 2):
    for dz in (-FAN_HOLE_P / 2, FAN_HOLE_P / 2):
        cuts.append(cyl(FAN_HOLE_D, V(-1, FAN_Y + dy, FAN_Z + dz), V(1, 0, 0), T + 2))
# right wall: exhaust slots
for i in range(10):
    cuts.append(slot_y(50 + i * 6, 16, 44, W - T - 1, W + 1, 3.0))
# top: vents over the board heatsink, trimmer access
for i in range(8):
    cuts.append(slot_top(HS_BOARD[0] + 2.5 + i * 5, HS_BOARD[2] + 1, HS_BOARD[3] - 1, 2.5))
cuts.append(cyl(5.0, V(TRIM_XY[0], TRIM_XY[1], H - T - 1), V(0, 0, 1), T + 2))
shell = shell.cut(cuts[0].fuse(cuts[1:]))

# ── Split: cover = the chamfered top cap, base = the rest (walls straight up to ZS for the lip) ─
cover = shell.common(box(-1, W + 1, -1, D + 1, ZS, H + 1))
base = shell.cut(box(-1, W + 1, -1, D + 1, ZS, H + 1)).cut(rrect(T, W - T, T, D - T, R - T, ZS - LIP_H - 1, ZS + 1))

# ── Base additions ────────────────────────────────────────────────────────────
adds = []
for (x, y) in BOARD_HOLES:
    adds.append(cyl(STANDOFF_D, V(x, y, T - 0.1), V(0, 0, 1), STANDOFF_H + 0.1))
# magnet bosses in the corners: 45° underside towards both walls (prints without supports)
bz1 = ZS - LIP_H - BOSS_GAP                                         # boss top
mz0 = bz1 - MAG_H - MAG_CLR                                         # magnet pocket bottom
bz0 = mz0 - 1.0 - BOSS                                              # underside meets the walls here
prof_x = Part.Face(Part.makePolygon([V(T - 0.3, 0, bz0), V(T + BOSS, 0, bz0 + BOSS + 0.3), V(T + BOSS, 0, bz1),
                                     V(T - 0.3, 0, bz1), V(T - 0.3, 0, bz0)])).extrude(V(0, BOSS + 0.3, 0))
prof_x.translate(V(0, T - 0.3, 0))
prof_y = prof_x.mirror(V(0, 0, 0), V(1, -1, 0))                     # same profile along the other wall
mag = cyl(MAG_D + MAG_CLR, V(T + BOSS / 2, T + BOSS / 2, mz0), V(0, 0, 1), BOSS)
adds += corners(prof_x.common(prof_y))
zb, zt = ZK_Z - ZK_CUT[1] / 2, ZK_Z + ZK_CUT[1] / 2 - PANE_GAP_Z   # breakaway window pane (see PANE_*)
px0, px1 = ZK_X - ZK_CUT[0] / 2 + PANE_GAP_X, ZK_X + ZK_CUT[0] / 2 - PANE_GAP_X
pw, pd, ph = PANE_POST
adds.append(box(px0, px1, 0, PANE_T, zb + ph, zt))
for i in range(PANE_POSTS):                                        # posts, first/last at the pane corners
    x = px0 + i * (px1 - px0 - pw) / (PANE_POSTS - 1)
    adds.append(box(x, x + pw, (PANE_T - pd) / 2, (PANE_T + pd) / 2, zb - 0.1, zb + ph + 0.1))
for f in PANE_SPRUES:
    z = round((zb + ph + f * (zt - zb - ph)) / 0.2) * 0.2            # on the layer grid
    for x0, x1 in ((px0 - PANE_GAP_X - 0.1, px0 + 0.1), (px1 - 0.1, px1 + PANE_GAP_X + 0.1)):
        adds.append(box(x0, x1, 0, PANE_T, z, z + PANE_SPRUE_H))
base = base.fuse(adds)
bcuts = []
for (x, y) in BOARD_HOLES:
    bcuts.append(cyl(M3_CLR, V(x, y, -1), V(0, 0, 1), T + STANDOFF_H + 2))
    bcuts.append(hex_prism(x, y, M3_NUT_F, -1, M3_NUT_T))
bcuts += corners(mag)
base = base.cut(bcuts[0].fuse(bcuts[1:]))
# labels
base = engrave_front(base, "+", BANANA_X - 10, ROW_Z, 6)
base = engrave_front(base, "\u2212", BANANA_X + BANANA_P + 10, ROW_Z, 6)
base = engrave_rear(base, "9-30V", JACK_X, JACK_Z + 12, 4.5)

# ── Cover additions: lip inside the walls, magnet blocks in the corners ──────
lz0 = ZS - LIP_H
lip_out = rrect(T + LIP_GAP, W - T - LIP_GAP, T + LIP_GAP, D - T - LIP_GAP, R - T - LIP_GAP, lz0, ZS + 0.1)
lip = lip_out.cut(rrect(T + LIP_GAP + LIP_W, W - T - LIP_GAP - LIP_W, T + LIP_GAP + LIP_W, D - T - LIP_GAP - LIP_W,
                        R - T - LIP_GAP - LIP_W, lz0 - 1, ZS + 1))
blocks = [b.common(lip_out) for b in corners(box(T, T + BOSS, T, T + BOSS, lz0, ZS + 0.1))]
mag_c = cyl(MAG_D + MAG_CLR, V(T + BOSS / 2, T + BOSS / 2, lz0 - 1), V(0, 0, 1), 1 + MAG_H + MAG_CLR)
cover = cover.fuse([lip] + blocks).cut(corners(mag_c)[0].fuse(corners(mag_c)[1:]))

base, cover = base.removeSplitter(), cover.removeSplitter()

# ── Document + export ─────────────────────────────────────────────────────────
if "Enclosure" in App.listDocuments():
    App.closeDocument("Enclosure")
doc = App.newDocument("Enclosure")
ob = doc.addObject("Part::Feature", "Base"); ob.Shape = base
oc = doc.addObject("Part::Feature", "Cover"); oc.Shape = cover
doc.recompute()
if App.GuiUp:
    ob.ViewObject.ShapeColor = (0.20, 0.20, 0.22)
    oc.ViewObject.ShapeColor = (0.80, 0.45, 0.10)
    oc.ViewObject.Transparency = 60
    import ImportGui
    ImportGui.export([ob], os.path.join(HERE, "Enclosure_base.step"))
    ImportGui.export([oc], os.path.join(HERE, "Enclosure_cover.step"))
else:
    base.exportStep(os.path.join(HERE, "Enclosure_base.step"))
    cover.exportStep(os.path.join(HERE, "Enclosure_cover.step"))
import MeshPart  # noqa: E402
for name, shp in (("Enclosure_base", base), ("Enclosure_cover", cover)):
    MeshPart.meshFromShape(Shape=shp, LinearDeflection=0.05, AngularDeflection=0.2).write(os.path.join(HERE, name + ".stl"))
# 3MF in print orientation, on the bed at the origin: base floor-down, cover upside down (top on the bed)
for name, shp, flip in (("Enclosure_base", base, False), ("Enclosure_cover", cover, True)):
    p = shp.copy()
    if flip:
        p.rotate(V(0, 0, 0), V(1, 0, 0), 180)
    bb = p.BoundBox
    p.translate(V(-bb.XMin, -bb.YMin, -bb.ZMin))
    MeshPart.meshFromShape(Shape=p, LinearDeflection=0.05, AngularDeflection=0.2).write(os.path.join(HERE, name + ".3mf"))
print("Base valid", base.isValid(), "vol %.0f" % base.Volume, "| Cover valid", cover.isValid(), "vol %.0f" % cover.Volume)
