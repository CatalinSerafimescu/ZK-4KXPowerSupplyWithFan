"""Regenerate the schematic from bom.py and verify it; optionally regenerate the PCB.

  python check.py         # gen_sch → ERC → netlist (→ PCB DRC if a board exists)
  python check.py --pcb   # also regenerate the PCB placement — refuses if the board is routed
  python check.py --pcb --force   # … and overwrite the routing anyway
"""
import subprocess
import sys
from pathlib import Path

KICAD_BIN = Path(r"C:\Program Files\KiCad\10.0\bin")
CLI = str(KICAD_BIN / "kicad-cli.exe")
GEN = Path(__file__).parent
PRJ = GEN.parent
NAME = "SursaTensiune"


def run(cmd, **kw):
    r = subprocess.run(cmd, capture_output=True, text=True, **kw)
    if r.returncode != 0:
        sys.exit(f"FAILED: {' '.join(map(str, cmd))}\n{r.stdout}{r.stderr}")
    return r.stdout


def summary(report: Path, ignore=()):
    counts = {}
    for line in report.read_text(encoding="utf-8").splitlines():
        if line.startswith("["):
            k = line[1:line.index("]")]
            counts[k] = counts.get(k, 0) + 1
    shown = {k: v for k, v in counts.items() if k not in ignore}
    return shown, counts


def main():
    run([sys.executable, GEN / "gen_sch.py"])
    run([CLI, "sch", "erc", "--severity-all", "-o", PRJ / "erc.rpt", PRJ / f"{NAME}.kicad_sch"])
    shown, _ = summary(PRJ / "erc.rpt")
    print("ERC:", shown or "0 violations")
    run([CLI, "sch", "export", "netlist", "--format", "kicadsexpr", "-o", PRJ / f"{NAME}.net",
         PRJ / f"{NAME}.kicad_sch"])
    run([CLI, "sch", "export", "pdf", "-o", PRJ / f"{NAME}_sch.pdf", PRJ / f"{NAME}.kicad_sch"])

    if "--pcb" in sys.argv:
        pcb = PRJ / f"{NAME}.kicad_pcb"
        if pcb.exists() and "(segment" in pcb.read_text(encoding="utf-8") and "--force" not in sys.argv:
            sys.exit(f"{pcb.name} is routed: --pcb would delete the tracks. Add --force to do it anyway.")
        run([str(KICAD_BIN / "python.exe"), GEN / "gen_pcb.py"], cwd=GEN)
    if (PRJ / f"{NAME}.kicad_pcb").exists():
        run([CLI, "pcb", "drc", "--severity-all", "-o", PRJ / "drc.rpt", PRJ / f"{NAME}.kicad_pcb"])
        shown, counts = summary(PRJ / "drc.rpt", ignore=("unconnected_items",))
        print("DRC:", shown or "clean", f"(+ {counts.get('unconnected_items', 0)} unrouted)")
    sys.exit(1 if shown else 0)


if __name__ == "__main__":
    main()
