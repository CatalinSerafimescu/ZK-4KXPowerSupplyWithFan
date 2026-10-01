"""Single-sided (B.Cu) autorouting of a copy of the board: Freerouting or KiCadRoutingTools, + GND pour.

Run with KiCad's python (Freerouting needs Java 25 on PATH):
    "C:/Program Files/KiCad/10.0/bin/python.exe" freeroute.py [src.kicad_pcb dst.kicad_pcb]
Default: SursaTensiune.kicad_pcb (only read) → SursaTensiune_freerouting.kicad_pcb.
Rules (toner transfer): 1.0 mm tracks, 0.5 mm clearance, no vias; pour 0.8 mm clearance.
"""
import os
import glob
import re
import shutil
import subprocess
import sys

import pcbnew

HERE = os.path.dirname(os.path.abspath(__file__))
KI = os.path.dirname(HERE)
WORK = os.path.join(os.environ["TEMP"], "freerouting_run")
JAR = max(glob.glob(os.path.expanduser(
    r"~\Documents\KiCad\10.0\3rdparty\plugins\app_freerouting_kicad-plugin\jar\freerouting-*.jar")))
KRT = r"E:\Catalin\Work\Programming\KiCadRoutingTools\route.py"
WIDTH, CLEARANCE, EDGE = 1.0, 0.5, 1.0
MM = pcbnew.FromMM


def add_gnd_pour(board):
    """GND pour on B.Cu over the whole board (GND is routed with tracks, the pour only adds copper)."""
    zone = pcbnew.ZONE(board)
    zone.SetLayer(pcbnew.B_Cu)
    zone.SetNetCode(board.FindNet("/GND").GetNetCode())
    zone.SetLocalClearance(MM(0.8))
    zone.SetMinThickness(MM(0.5))
    zone.SetPadConnection(pcbnew.ZONE_CONNECTION_THERMAL)
    zone.SetThermalReliefGap(MM(0.6))
    zone.SetThermalReliefSpokeWidth(MM(0.8))
    bb = board.GetBoardEdgesBoundingBox()
    ol = zone.Outline()
    ol.NewOutline()
    for x, y in ((bb.GetLeft(), bb.GetTop()), (bb.GetRight(), bb.GetTop()),
                 (bb.GetRight(), bb.GetBottom()), (bb.GetLeft(), bb.GetBottom())):
        ol.Append(x, y)
    board.Add(zone)
    pcbnew.ZONE_FILLER(board).Fill(board.Zones())


def freeroute(src, dst, log=None, pour_nets=("/GND",)):
    """Freerouting on B.Cu only (F.Cu declared a plane layer in the DSN, so nothing is routed on it).
    pour_nets are left to the pour: removed from the DSN netlist, so their pads are only obstacles."""
    os.makedirs(WORK, exist_ok=True)
    dsn, ses = os.path.join(WORK, "board.dsn"), os.path.join(WORK, "board.ses")
    if os.path.exists(ses):
        os.remove(ses)
    shutil.copyfile(src, dst)
    board = pcbnew.LoadBoard(dst)
    assert pcbnew.ExportSpecctraDSN(board, dsn)
    t = open(dsn, encoding="utf-8").read()
    t = re.sub(r"\(layer F\.Cu\s*\(type signal\)", "(layer F.Cu\n      (type power)", t, count=1)
    t = re.sub(r"\(width \d+\)", f"(width {WIDTH * 1000:.0f})", t)
    t = re.sub(r"\(clearance \d+\)", f"(clearance {CLEARANCE * 1000:.0f})", t)
    for n in pour_nets:
        t = re.sub(r"\(net " + re.escape(n) + r"\s*\(pins[^)]*\)\s*\)", "", t)
        t = re.sub(r"(\(class \S+[^()]*?)\s" + re.escape(n) + r"(?=[\s)])", r"\1", t)
    open(dsn, "w", encoding="utf-8").write(t)
    r = subprocess.run(["java", "-jar", JAR, "-de", dsn, "-do", ses, "-mp", "100", "--gui.enabled=false"],
                       capture_output=True, text=True)
    if log:
        open(log, "w", encoding="utf-8").write(r.stdout + r.stderr)
    if not os.path.exists(ses):
        sys.exit(f"Freerouting produced no session file:\n{r.stdout[-2000:]}{r.stderr[-2000:]}")
    assert pcbnew.ImportSpecctraSES(board, ses)
    add_gnd_pour(board)
    board.Save(dst)


def kicad_routing_tools(src, dst, log=None, pour_nets=("/GND",)):
    """KiCadRoutingTools (Rust A*) on B.Cu only; pour_nets are left to the pour."""
    nets = sorted({p.GetNetname() for f in pcbnew.LoadBoard(src).GetFootprints() for p in f.Pads()
                   if p.GetNetname() and p.GetNetname() not in pour_nets})
    r = subprocess.run([sys.executable, KRT, src, dst, "--layers", "B.Cu", "--track-width", str(WIDTH),
                        "--clearance", str(CLEARANCE), "--board-edge-clearance", str(EDGE),
                        "--nets", *nets], capture_output=True, text=True, cwd=os.path.dirname(KRT))
    if log:
        open(log, "w", encoding="utf-8").write(r.stdout + r.stderr)
    board = pcbnew.LoadBoard(dst)
    add_gnd_pour(board)
    board.Save(dst)


if __name__ == "__main__":
    src, dst = (sys.argv[1:3] if len(sys.argv) > 2 else
                (os.path.join(KI, "SursaTensiune.kicad_pcb"), os.path.join(KI, "SursaTensiune_freerouting.kicad_pcb")))
    freeroute(src, dst)
