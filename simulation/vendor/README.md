# Vendor SPICE models

Manufacturer models for the two ICs the design depends on most. Both are © their vendors, so they are **not included** —
put them here under these names to run `ltspice/run_sim.py --vendor`:

| File | Part (BOM) | Source | Format | Runs in |
|---|---|---|---|---|
| `onsemi_LM358.mod` | U2 LM358AP (TI) | onsemi LM358 "next gen" model, 9/27/2018 ([model page](https://onsemi.com/support/design-resources/models?rpn=LM358)) | open, standard SPICE, transistor level | LTspice; should run in ngspice too (untested) |
| `LT317A.sub` | U1 LM317T (TI) | ADI, bundled with LTspice 26 (`lib.zip` → `lib/sub/LT317A.sub`) — Linear's LM317 equivalent | LTspice-encrypted | LTspice only |

Notes:
- **onsemi LM358** — pins `+IN -IN +V -V OUT`. Measured as a follower on 5 V (0.2…3.4 V common mode): offset −0.42 mV, input bias 9.6 nA flowing out of the inputs. Class-B output like the real part: it can sink only ~10 µA near ground, which matters in this circuit (see [../ltspice/README.md](../ltspice/README.md)).
- **LT317A** — pins `ADJ OUT IN` (different from our behavioral `LM317B`: `IN ADJ OUT`).
- Wrappers with the behavioral models' pin order and `VOS`/`IB` params: [`../ltspice/models_vendor.lib`](../ltspice/models_vendor.lib).

Tried and rejected:
- **TI LMX58_LM2904** (SNOM268C, switch-based macromodel) — has a false operating point with the output latched ~1.5 V *above* V_cc (seen in both LTspice and ngspice); in this circuit it hung or latched in most scenarios.
- **TI LM317** (SBVM440) — Cadence-encrypted, runs only in PSpice.
