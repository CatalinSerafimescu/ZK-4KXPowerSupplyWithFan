# Simulation — fan temperature controller

DC sweeps and transients (ngspice 46) verifying every operating regime and fault before PCB.

## Prerequisites
- ngspice 46 at `E:\Catalin\Work\Electronics\NGSpice_46\bin\ngspice_con.exe` (console build; `ngspice.exe` opens a GUI)
- Python 3 with `numpy`, `pandas`, `matplotlib`

## Running
```bash
cd simulation/ngspice
python run_sim.py --all          # all scenarios → results/RESULTS.md
python run_sim.py A_nominal_40C  # one scenario
python run_sim.py --list
```
Per scenario, `results/<name>/`: `sim.cir` (rendered netlist), `out.csv`, `ngspice.log`, `plot.png`, `summary.txt`.

## Scenarios
Defined in [`../scenarios.py`](../scenarios.py), shared with the [LTspice port](../ltspice/README.md).

| Name | What it checks |
|---|---|
| `A_nominal_40C` | Temperature sweep, pot set for 40 °C: off at 25 °C, start at 40 ± 1 °C, full ≥ 62 °C, V_fan ≤ 5.25 V |
| `B_pot_min` / `C_pot_max` | Adjustment range of the start temperature (≈ 12 / 49 °C) |
| `D_vin_sweep_hot` | V_in 6–30 V at 70 °C: V_fan constant; LM317 dissipation at 9 V and 30 V |
| `E/F_powerup_*_hot` | Power-up at 9 V / 30 V when hot: no overshoot above 5.25 V |
| `G_powerup_9V_cold` | Power-up when cold: fan does not kick on |
| `H_wiper_open` | Fault: pot wiper open with worst-case LM358 bias (250 nA) → fan still runs (fail-safe) |
| `I_sensor_open` | Fault: LM35 disconnected → fan full speed (fail-safe) |
| `J/K_offset_worst_*` | LM358 offset ±7 mV on both halves in opposite directions → start shift ≤ 1.5 °C (uncalibrated) |

## Key nodes
| Node | Meaning |
|---|---|
| `V(t)` | Stimulus: voltage = temperature in °C |
| `V(n_vref)` | U2B output (pin 7) — calibration point |
| `V(n_adj)` | U2A output (pin 1) = LM317 ADJ |
| `V(vfan)` | Fan voltage |
| `I(V_i317)` | LM317 output current (fan + R4) |

## Model notes
All ICs are **behavioral** stand-ins in `models.lib` (no vendor models):
- **LM317** — V_out = V_adj + 1.25 V, 1.7 V dropout, 50 µA ADJ current; input current not modeled, dissipation = (V_in − V_fan) · I_out.
- **78L05** — 5.00 V, 1.7 V dropout, 3 mA quiescent.
- **LM358** — 100 dB, 1 MHz GBW, output 5 mV … V_cc − 1.5 V, params `VOS` and `IB` (bias flows out of the inputs, pulls a floating input high).
  The V_cc − 1.5 V high swing sets the fan maximum (≈ 4.75 V); a real part at light load may swing ~0.2 V higher → ≈ 5.0 V, still in spec.
- **LM35** — 10 mV/°C, needs V_s ≥ 4 V.
- **Fan** — 25 Ω resistor (5 V / 0.2 A). A real brushless fan draws less at 1.25 V ("off") than this model shows.
