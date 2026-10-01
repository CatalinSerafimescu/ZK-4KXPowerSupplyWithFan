"""
Simulation scenarios for the fan temperature controller.

Each scenario fills the placeholders of fan_ctrl.cir.tmpl and lists assertions.
An assertion function gets a pandas DataFrame with columns:
  sweep (°C, V or s) | vin | t | v5 | vref | vadj | vfan | i317 | ifan
and returns list[(passed: bool, message: str)].
"""
import numpy as np

# ── Design constants (keep in sync with bom.py / netlist) ─────────────────────
R1, RV1, R5 = 100e3, 10e3, 100e3
V5 = 5.0
GAIN, K_REF = 11.0, 10.0       # V_adj = 11*V_lm35 - 10*V_ref
V_START = 2.8                  # fan voltage where a 5 V Pi fan starts to spin (measured on the breadboard)
V_FAN_MAX = 5.25               # 5 V fan +5 %


def vref_for_tstart(t_start: float) -> float:
    """Calibration formula: V_ref such that the fan reaches V_START at t_start."""
    return (GAIN * t_start / 100 - (V_START - 1.25)) / K_REF


def pot_for_tstart(t_start: float) -> float:
    """Pot position (0 = wiper at GND end, 1 = top) giving vref_for_tstart()."""
    target = vref_for_tstart(t_start)
    best, best_err = 0.0, 1e9
    for a in np.linspace(0, 1, 10001):
        rb = RV1 * a + 1e-3
        rb_eff = rb * R5 / (rb + R5)
        v = V5 * rb_eff / (R1 + RV1 * (1 - a) + rb_eff)
        if abs(v - target) < best_err:
            best, best_err = a, abs(v - target)
    return best


# ── Helpers for assertions ────────────────────────────────────────────────────
def crossing(x, y, level):
    """First x where y rises through level (linear interpolation), or None."""
    idx = np.where((y[:-1] < level) & (y[1:] >= level))[0]
    if len(idx) == 0:
        return None
    i = idx[0]
    return x[i] + (level - y[i]) * (x[i + 1] - x[i]) / (y[i + 1] - y[i])


def at(df, col, x):
    return float(np.interp(x, df["sweep"].values, df[col].values))


def check_start(df, expected, tol):
    t = crossing(df["sweep"].values, df["vfan"].values, V_START)
    if t is None:
        return (False, f"fan never reaches {V_START} V")
    return (abs(t - expected) <= tol,
            f"fan start ({V_START} V) at {t:.1f} °C (expected {expected:.1f} ± {tol} °C)")


def check_max(df, limit=V_FAN_MAX):
    m = df["vfan"].max()
    return (m <= limit, f"max V_fan = {m:.3f} V (limit {limit} V)")


# ── Analyses ──────────────────────────────────────────────────────────────────
DC_TEMP = "dc V_T 0 80 0.25"
DC_VIN = "dc V_IN 6 30 0.05"
TRAN = "tran 10u 30m"

BASE = dict(VIN_SRC="DC 9", TEMP_C=25, POT_A=pot_for_tstart(40),
            VOS_A=0, VOS_B=0, IB="45n", R_SENSOR_LINK="1m", R_WIPER_LINK="1m")


def sc(name, desc, kind, analysis, asserts, **over):
    subs = dict(BASE)
    subs.update(over)
    return dict(name=name, desc=desc, kind=kind, analysis=analysis,
                subs=subs, assertions=asserts)


def _a_nominal(df):
    return [
        (at(df, "vfan", 25) < 1.6, f"25 °C: V_fan = {at(df, 'vfan', 25):.2f} V (fan off, < 1.6 V)"),
        check_start(df, 40, 1.0),
        (at(df, "vfan", 62) >= 4.5, f"62 °C: V_fan = {at(df, 'vfan', 62):.2f} V (full speed, ≥ 4.5 V)"),
        check_max(df),
    ]


def _range_min(df):
    t = crossing(df["sweep"].values, df["vfan"].values, V_START)
    return [(t is not None and t <= 15, f"pot at minimum: fan start at {t:.1f} °C (≤ 15 °C)")]


def _range_max(df):
    t = crossing(df["sweep"].values, df["vfan"].values, V_START)
    return [(t is not None and 46 <= t <= 53, f"pot at maximum: fan start at {t:.1f} °C (46–53 °C)")]


def _vin_sweep(df):
    ok = df[df["sweep"] >= 8.5]
    p = (df["vin"] - df["vfan"]) * df["i317"]
    p9, p30 = float(np.interp(9, df["sweep"], p)), float(np.interp(30, df["sweep"], p))
    return [
        (ok["vfan"].between(4.5, V_FAN_MAX).all(),
         f"V_in 8.5–30 V: V_fan {ok['vfan'].min():.3f}–{ok['vfan'].max():.3f} V (4.5–{V_FAN_MAX} V)"),
        (p9 < 1.2, f"U1 (LM317) dissipation @ 9 V in: {p9:.2f} W (no heatsink needed, < 1.2 W)"),
        (True, f"U1 (LM317) dissipation @ 30 V in: {p30:.2f} W (heatsink HS1 required)"),
    ]


def _powerup(df):
    final = df["vfan"].iloc[-1]
    return [check_max(df),
            (4.5 <= final <= V_FAN_MAX, f"settled V_fan = {final:.3f} V")]


def _powerup_cold(df):
    m = df["vfan"].max()
    return [(m < 2.0, f"cold power-up: max V_fan = {m:.2f} V (no start-up kick, < 2.0 V)")]


def _wiper_open(df):
    t = crossing(df["sweep"].values, df["vfan"].values, V_START)
    return [(t is not None and t <= 20,
             f"wiper open, worst-case IB: fan start at {t:.1f} °C (fail-safe ON, ≤ 20 °C)")]


def _sensor_open(df):
    return [(df["vfan"].min() >= 4.5,
             f"sensor open: V_fan ≥ {df['vfan'].min():.2f} V at all temperatures (fail-safe full speed)")]


def _offset(df):
    return [check_start(df, 40, 1.5), check_max(df)]


SCENARIOS = [
    sc("A_nominal_40C", "Temperature sweep, threshold set for 40 °C, 9 V in", "dc_temp", DC_TEMP, _a_nominal),
    sc("B_pot_min", "Temperature sweep, pot at minimum", "dc_temp", DC_TEMP, _range_min, POT_A=0),
    sc("C_pot_max", "Temperature sweep, pot at maximum", "dc_temp", DC_TEMP, _range_max, POT_A=1),
    sc("D_vin_sweep_hot", "Input sweep 6–30 V at 70 °C (fan full)", "dc_vin", DC_VIN, _vin_sweep, TEMP_C=70),
    sc("E_powerup_9V_hot", "Power-up 0→9 V at 70 °C", "tran", TRAN, _powerup,
       VIN_SRC="PWL(0 0 1m 0 1.1m 9)", TEMP_C=70),
    sc("F_powerup_30V_hot", "Power-up 0→30 V at 70 °C", "tran", TRAN, _powerup,
       VIN_SRC="PWL(0 0 1m 0 1.1m 30)", TEMP_C=70),
    sc("G_powerup_9V_cold", "Power-up 0→9 V at 25 °C (fan should stay off)", "tran", TRAN, _powerup_cold,
       VIN_SRC="PWL(0 0 1m 0 1.1m 9)", TEMP_C=25),
    sc("H_wiper_open", "Fault: pot wiper open, worst-case LM358 bias 250 nA", "dc_temp", DC_TEMP, _wiper_open,
       R_WIPER_LINK="1T", IB="250n"),
    sc("I_sensor_open", "Fault: LM35 disconnected", "dc_temp", DC_TEMP, _sensor_open,
       R_SENSOR_LINK="1T"),
    sc("J_offset_worst_pos", "LM358 offset corner: U2A +7 mV, U2B −7 mV (uncalibrated)", "dc_temp", DC_TEMP,
       _offset, VOS_A="7m", VOS_B="-7m"),
    sc("K_offset_worst_neg", "LM358 offset corner: U2A −7 mV, U2B +7 mV (uncalibrated)", "dc_temp", DC_TEMP,
       _offset, VOS_A="-7m", VOS_B="7m"),
]
