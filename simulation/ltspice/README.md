# Simulation — LTspice port

Port of the [ngspice simulation](../ngspice/README.md): same circuit, same behavioral models, same scenarios and assertions ([`../scenarios.py`](../scenarios.py)).
Optionally runs with **vendor models** for U1 (LM317) and U2 (LM358) instead of the behavioral ones.

## Prerequisites
- LTspice 26 at `%LOCALAPPDATA%\Programs\ADI\LTspice\LTspice.exe`
- Python 3 with `numpy`, `pandas`, `matplotlib`

## Running
```bash
cd simulation/ltspice
python run_sim.py --all            # behavioral models → results/RESULTS.md
python run_sim.py --all --vendor   # onsemi LM358 + ADI LT317A → results_vendor/RESULTS.md
python run_sim.py A_nominal_40C    # one scenario
python run_sim.py --list
```
Per scenario, `results[_vendor]/<name>/`: `sim.net` (rendered netlist), `sim.log`, `out.csv`, `plot.png`, `summary.txt`.
The `.raw` file is read and then deleted; open `sim.net` in LTspice and press Run to get the waveforms interactively.

## Differences from the ngspice version
- `fan_ctrl.net.tmpl`: the ngspice `.control` block is replaced by `.save` + a plain `.dc` / `.tran` directive.
- `.options numdgt=16 plotwinsize=0`: double-precision, uncompressed `.raw`, so crossings are interpolated on the same grid as ngspice.
- `models.lib` is a verbatim copy — the B-source syntax (`V=`, `I=`, `min`/`max`) and `params:` subcircuits are accepted by both simulators.
- C2 has 1 Ω ESR (`Rser=1`, aluminium electrolytic); the ngspice netlist has an ideal C2. See the stability note below.
- Plots reuse `plot()` from `../ngspice/run_sim.py`.

Behavioral DC sweeps are identical to ngspice (V_fan and I_out differ by < 1 µV / 1 µA at every point). Transients differ slightly around the 0.1 ms input ramp (time-step control and C2 ESR): E power-up peak 4.74 V vs 4.82 V, G cold peak 1.68 V vs 1.62 V; all well inside the limits.

## Vendor models (`--vendor`)
[`models_vendor.lib`](models_vendor.lib) wraps the files in [`../vendor/`](../vendor/README.md) with the behavioral pin order and `VOS`/`IB` params, so the template only swaps subcircuit names:
- **U2 LM358** → onsemi LM358 (transistor level). `VOS`/`IB` add the difference to the model's built-in −0.42 mV / 9.6 nA, so H/J/K keep their worst-case meaning.
- **U1 LM317** → ADI LT317A (bundled with LTspice, encrypted).

How it is simulated: with these models an operating point is only easy to find with everything unpowered, and `.dc` sweeps stall for minutes. So each `.dc` scenario becomes a quasi-static `.tran`: V_in steps up from 0 at 1 ms, settles, then from 10 ms the swept source ramps at 1 °C/ms (or 1 V/ms). Halving the ramp rate gives identical results. `method=gear` is used because trap stalls in the 0→30 V power-up (F). All 11 run in ~23 s.

### Findings
| Scenario | Behavioral | Vendor | Why |
|---|---|---|---|
| A fan start (40 °C setting) | 40.1 °C | 40.0 °C | — |
| A fan "off" at 25 °C | 1.25 V | 1.47 V | U2A can't pull ADJ fully to 0 V while sinking the LT317A ADJ current |
| Fan maximum | 4.74 V | 4.90 V | real LM358 swings higher than the V_cc − 1.5 V behavioral limit |
| **B** pot at minimum | 14.7 °C | **22.7 °C — FAIL (≤ 15 °C)** | U2B follower must *sink* ~10 µA from R2 near 0 V; a class-B LM358 can't (datasheet: 12 µA min at V_O = 200 mV), so V_ref sits at 40…140 mV instead of 5 mV |
| **H** wiper open, 250 nA bias | 16.6 °C | **23.0 °C — FAIL (≤ 20 °C)** | same V_ref floor; fail-safe still turns the fan on, just later |
| LM317 dissipation @ 30 V | 5.33 W | 5.48 W | LT317A input/quiescent current |

**Stability:** with an ideal (0 Ω ESR) C2, the LT317A + onsemi LM358 driving ADJ oscillates at mid-range (V_fan 0.8…3.2 V, 2.3 A current-limit bursts). 0.2 Ω ESR is already stable, and the BOM's aluminium electrolytic has far more — **don't replace C2 with a ceramic.**
