"""
run_sim.py — LTspice port: render the netlist template, run LTspice in batch mode,
check the same assertions as the ngspice runner, plot.

Usage:
  python run_sim.py --all          # run every scenario, write results/RESULTS.md
  python run_sim.py A_nominal_40C  # run one scenario
  python run_sim.py --list
"""
import argparse
import importlib.util
import os
import re
import subprocess
import sys
from pathlib import Path

if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

import numpy as np
import pandas as pd

SIM_DIR = Path(__file__).parent
sys.path.insert(0, str(SIM_DIR.parent))  # shared scenarios.py
from scenarios import SCENARIOS

# reuse plot() from ../ngspice/run_sim.py (same module name, so load it by path)
_spec = importlib.util.spec_from_file_location("ngspice_run_sim", SIM_DIR.parent / "ngspice" / "run_sim.py")
_ngspice = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_ngspice)
plot = _ngspice.plot

LTSPICE = Path(os.environ["LOCALAPPDATA"]) / "Programs" / "ADI" / "LTspice" / "LTspice.exe"
# --vendor swaps the behavioral LM317/LM358 for vendor models (models_vendor.lib)
# With the vendor models the operating point is only easy to find with V_in = 0 (everything
# unpowered); at other points LTspice's .op/.dc stalls for minutes. So vendor runs replace each
# .dc sweep by a quasi-static .tran: power up, settle, then ramp slowly (see quasi_static()).
# method=gear: with trap, the 0→30 V power-up (F) stalls on the time step at ~1.016 ms.
MODELS = {"behavioral": dict(OPAMP="LM358B", REG317="LM317B", results=SIM_DIR / "results",
                             quasi_static=False, EXTRA_OPTIONS=""),
          "vendor": dict(OPAMP="LM358V", REG317="LM317V", results=SIM_DIR / "results_vendor",
                         quasi_static=True, EXTRA_OPTIONS="method=gear")}
# swept source -> DataFrame column that becomes the x axis
DC_SOURCES = {"V_T": "t", "V_IN": "vin"}
RAMP_START = 10e-3  # s: power-up at 1 ms, settled well before the ramp starts
RAMP_RATE = 1e3     # swept units per second (1 °C/ms, 1 V/ms)
TEMPLATE = SIM_DIR / "fan_ctrl.net.tmpl"
# DataFrame column -> LTspice trace name (x axis is always column 0 of the .raw)
TRACES = {"vin": "V(vin)", "t": "V(t)", "v5": "V(v5)", "vref": "V(n_vref)", "vadj": "V(n_adj)",
          "vfan": "V(vfan)", "i317": "I(V_i317)", "ifan": "I(V_ifan)"}


def quasi_static(sc: dict) -> tuple[dict, str | None]:
    """Turn 'dc SRC start stop step' into a .tran that powers up from V_in = 0 at 1 ms,
    holds until RAMP_START, then ramps SRC slowly from start to stop.
    Returns the modified scenario and the column to use as sweep axis (None if not a .dc)."""
    m = re.fullmatch(r"dc (\S+) (\S+) (\S+) \S+", sc["analysis"])
    if not m:
        return sc, None
    col = DC_SOURCES[m.group(1)]
    start, stop = float(m.group(2)), float(m.group(3))
    t_end = RAMP_START + (stop - start) / RAMP_RATE
    ramp = f"{RAMP_START:g} {start} {t_end:g} {stop}"
    subs = dict(sc["subs"])
    if col == "t":
        vin = float(re.fullmatch(r"DC (\S+)", subs["VIN_SRC"]).group(1))
        subs.update(VIN_SRC=f"PWL(0 0 1m 0 1.1m {vin})", TEMP_C=f"PWL(0 {start} {ramp})")
    else:
        subs.update(VIN_SRC=f"PWL(0 0 1m 0 1.1m {start} {ramp})")
    return dict(sc, subs=subs, analysis=f"tran 0 {t_end:g} 0 20u"), col


def render(sc: dict, models: dict) -> str:
    text = TEMPLATE.read_text(encoding="utf-8")
    subs = dict(sc["subs"], NAME=sc["name"], ANALYSIS=sc["analysis"],
                MODELSLIB=(SIM_DIR / "models.lib").as_posix(),
                VENDORLIB=(SIM_DIR / "models_vendor.lib").as_posix(),
                OPAMP=models["OPAMP"], REG317=models["REG317"], EXTRA_OPTIONS=models["EXTRA_OPTIONS"])
    for k, v in subs.items():
        text = text.replace("{{" + k + "}}", str(v))
    if "{{" in text:
        raise ValueError(f"unresolved placeholder in {sc['name']}")
    return text


def read_raw(path: Path) -> pd.DataFrame:
    """Minimal reader for an LTspice binary .raw file (real data, not stepped)."""
    blob = path.read_bytes()
    marker = "Binary:\n".encode("utf-16-le")
    head_end = blob.index(marker) + len(marker)
    header = blob[:head_end].decode("utf-16-le")
    n_vars = int(re.search(r"No\. Variables:\s*(\d+)", header).group(1))
    n_pts = int(re.search(r"No\. Points:\s*(\d+)", header).group(1))
    flags = re.search(r"Flags:(.*)", header).group(1)
    names = re.findall(r"^\s+\d+\s+(\S+)\s+\S+", header.split("\nVariables:")[1], re.M)[:n_vars]

    body = blob[head_end:]
    if "double" in flags:   # .options numdgt>6: every value is float64
        data = np.frombuffer(body, dtype="<f8", count=n_pts * n_vars).reshape(n_pts, n_vars)
    else:                   # x axis float64, the rest float32
        rec = np.dtype([("x", "<f8")] + [(f"v{i}", "<f4") for i in range(1, n_vars)])
        arr = np.frombuffer(body, dtype=rec, count=n_pts)
        data = np.column_stack([arr[n].astype(float) for n in rec.names])
    df = pd.DataFrame(data, columns=[n.lower() for n in names])
    df.iloc[:, 0] = df.iloc[:, 0].abs()   # transient time may carry a sign flag
    return df


def run(sc: dict, models: dict) -> tuple[bool, list[str]]:
    out = models["results"] / sc["name"]
    out.mkdir(parents=True, exist_ok=True)
    net = out / "sim.net"
    raw, log = net.with_suffix(".raw"), net.with_suffix(".log")
    sim_sc, sweep_col = quasi_static(sc) if models["quasi_static"] else (sc, None)
    net.write_text(render(sim_sc, models), encoding="utf-8")
    raw.unlink(missing_ok=True)

    r = subprocess.run([str(LTSPICE), "-b", str(net)], capture_output=True, text=True,
                       timeout=300, cwd=str(out))
    log_text = log.read_text(encoding="utf-8", errors="replace") if log.exists() else ""
    # "Direct Newton iteration failed" is informational when Gmin stepping then succeeds;
    # a run that really fails never reaches "Total elapsed time".
    if (r.returncode != 0 or not raw.exists() or "Total elapsed time" not in log_text
            or re.search(r"error|singular|too small", log_text, re.I)):
        return False, [f"LTspice failed (exit {r.returncode}), see sim.log"]

    rdf = read_raw(raw)
    if sweep_col:   # drop the power-up part of a quasi-static sweep
        rdf = rdf[rdf["time"] >= RAMP_START].reset_index(drop=True)
    df = pd.DataFrame({"sweep": rdf[TRACES[sweep_col].lower()] if sweep_col else rdf.iloc[:, 0]})
    for col, trace in TRACES.items():
        df[col] = rdf[trace.lower()]
    df.to_csv(out / "out.csv", index=False)
    raw.unlink()   # large binary; out.csv keeps the traces

    results = sc["assertions"](df)
    plot(df, sc, out / "plot.png")

    lines = [f"{'PASS' if ok else 'FAIL'}  {msg}" for ok, msg in results]
    (out / "summary.txt").write_text(f"{sc['name']}: {sc['desc']}\n" + "\n".join(lines) + "\n",
                                     encoding="utf-8")
    return all(ok for ok, _ in results), lines


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("names", nargs="*")
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--list", action="store_true")
    ap.add_argument("--vendor", action="store_true", help="TI LM358 + ADI LT317A instead of behavioral models")
    args = ap.parse_args()

    if args.list:
        for s in SCENARIOS:
            print(f"{s['name']:24s} {s['desc']}")
        return

    chosen = SCENARIOS if args.all else [s for s in SCENARIOS if s["name"] in args.names]
    if not chosen:
        ap.error("give scenario names, --all or --list")

    kind = "vendor" if args.vendor else "behavioral"
    models = MODELS[kind]
    flag = " --vendor" if args.vendor else ""
    report = [f"# Simulation results — LTspice, {kind} models\n", f"> Generated by `ltspice/run_sim.py --all{flag}`.\n",
              "| Scenario | Description | Result |", "|---|---|---|"]
    details = []
    for s in chosen:
        ok, lines = run(s, models)
        print(f"{'PASS' if ok else 'FAIL'}  {s['name']}")
        for ln in lines:
            print(f"      {ln}")
        report.append(f"| [{s['name']}]({s['name']}/plot.png) | {s['desc']} | {'✅ PASS' if ok else '❌ FAIL'} |")
        details += [f"\n### {s['name']}\n", *[f"- {ln}" for ln in lines]]

    if args.all:
        (models["results"] / "RESULTS.md").write_text("\n".join(report + ["\n## Details"] + details) + "\n",
                                                encoding="utf-8")


if __name__ == "__main__":
    main()
