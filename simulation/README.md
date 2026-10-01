# Simulation — fan temperature controller

The same 11 scenarios, run in two simulators:

| Folder | Simulator | Results |
|---|---|---|
| [`ngspice/`](ngspice/README.md) | ngspice 46 (`ngspice_con.exe -b`) | [RESULTS.md](ngspice/results/RESULTS.md) |
| [`ltspice/`](ltspice/README.md) | LTspice 26 (`LTspice.exe -b`) | [RESULTS.md](ltspice/results/RESULTS.md), vendor models: [RESULTS.md](ltspice/results_vendor/RESULTS.md) |

[`scenarios.py`](scenarios.py) is shared: stimuli, parameters and pass/fail assertions are defined once.
Each folder has its own netlist template and `models.lib` (identical behavioral models today).
[`vendor/`](vendor/README.md) holds manufacturer models (onsemi LM358, ADI LT317A), used by `ltspice/run_sim.py --vendor`.
