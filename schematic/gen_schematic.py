"""Fan temperature controller schematic — schemdraw → fan_controller.svg / .png

Blocks (left → right):
  1. Input J1 + 5 V aux rail (U3 78L05)
  2. Threshold: R1 + RV1 (3386P trimmer) + R5 fail-safe → U2B follower → V_REF
  3. Amplifier: LM35 (J2) → U2A, gain 11, V_ADJ = 11·V_LM35 − 10·V_REF
  4. Fan regulator: U1 LM317 → V_FAN → J3 fan, R4 min load, D1 clamp
Nets shared between blocks use labels (VIN, +5V, V_REF, V_ADJ) instead of wires.
"""
import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import schemdraw
import schemdraw.elements as elm
from bom import LABEL

HERE = os.path.dirname(__file__)


def lbl(d, xy, text, **kw):
    d.add(elm.Label().at(xy).label(text, **kw))


def net(d, xy, name, loc="right"):
    """Open-dot net label."""
    d.add(elm.Dot(open=True).at(xy).label(name, loc=loc, fontsize=9, color="navy"))


def draw(path: str) -> None:
    with schemdraw.Drawing(show=False) as d:
        d.config(fontsize=8, unit=2.2)

        # ═══ 1. INPUT + 5 V AUX RAIL ═════════════════════════════════════════
        d.add(elm.Label().at((0, 11.2)).label("1 · INPUT + 5 V AUX", fontsize=10, halign="left"))
        j1 = d.add(elm.Ic(pins=[elm.IcPin(name="GND", side="right", pin="2"),
                                elm.IcPin(name="VIN", side="right", pin="1")],
                          edgepadW=0.8, pinspacing=1.2, leadlen=0.5, lsize=8, plblsize=7, label="J1\nINPUT\n9–30 V").at((0, 6)))
        d.add(elm.Line().right(1.2).at(j1.VIN))
        vin_node = d.here
        net(d, vin_node, "VIN", loc="top")
        d.add(elm.Line().right(1.2).at(vin_node))
        u3_in = d.here
        d.add(elm.Line().at(j1.GND).right(0.6))
        d.add(elm.Ground())

        # C3 at U3 input
        d.add(elm.Dot().at(u3_in))
        d.add(elm.Capacitor().down().at(u3_in).length(2.2))
        lbl(d, (u3_in[0] + 0.5, u3_in[1] - 1.1), "C3\n100n", halign="left")
        d.add(elm.Ground())

        u3 = d.add(elm.Ic(pins=[elm.IcPin(name="IN", side="left", pin="3"),
                                elm.IcPin(name="OUT", side="right", pin="1"),
                                elm.IcPin(name="GND", side="bottom", pin="2")],
                          size=(2.6, 1.6), lsize=8, plblsize=7, label="U3\n78L05").right().anchor("IN").at((u3_in[0] + 1.5, u3_in[1])))
        d.add(elm.Line().at(u3_in).to(u3.IN))
        d.add(elm.Line().down(0.6).at(u3.GND))
        d.add(elm.Ground())

        d.add(elm.Line().right(1.0).at(u3.OUT))
        v5 = d.here
        d.add(elm.Dot())
        d.add(elm.Capacitor(polar=True).down().at(v5).length(2.2))
        lbl(d, (v5[0] + 0.5, v5[1] - 1.1), "C4\n10µ/25V", halign="left")
        d.add(elm.Ground())
        d.add(elm.Line().right(2.2).at(v5))
        c5 = d.here
        d.add(elm.Dot())
        d.add(elm.Capacitor().down().at(c5).length(2.2))
        lbl(d, (c5[0] + 0.5, c5[1] - 1.1), "C5\n100n\n(at U2 pin 8)", halign="left")
        d.add(elm.Ground())
        d.add(elm.Line().up(1.0).at(c5))
        net(d, d.here, "+5V", loc="top")

        # U2 power pins note
        lbl(d, (0, 1.2), "U2 (LM358AP): pin 8 = +5V, pin 4 = GND", halign="left")

        # ═══ 2. THRESHOLD (start temperature) ════════════════════════════════
        X2 = 18.5
        d.add(elm.Label().at((X2, 11.2)).label("2 · START TEMPERATURE", fontsize=10, halign="left"))
        net(d, (X2, 10), "+5V", loc="left")
        d.add(elm.Resistor().down().at((X2, 10)).length(2.2))
        lbl(d, (X2 + 0.5, 8.9), LABEL["R1"], halign="left")
        pot = d.add(elm.Potentiometer().down().length(2.4))
        lbl(d, (X2 - 0.6, pot.center[1]), "RV1\n10k\ntrimmer", halign="right")
        d.add(elm.Ground())
        wiper = pot.tap
        d.add(elm.Line().right(1.4).at(wiper))
        w = d.here
        d.add(elm.Dot())
        d.add(elm.Resistor().down().at(w).length(2.2))
        lbl(d, (w[0] + 0.5, w[1] - 1.1), LABEL["R5"] + "\nfail-safe", halign="left")
        d.add(elm.Ground())

        u2b = d.add(elm.Opamp(leads=True).right().anchor("in2").at((w[0] + 1.6, w[1])))
        d.add(elm.Line().at(w).to(u2b.in2))
        lbl(d, (u2b.in2[0] + 0.1, u2b.in2[1] - 0.35), "5", halign="left", fontsize=7)
        lbl(d, (u2b.in1[0] + 0.1, u2b.in1[1] + 0.35), "6", halign="left", fontsize=7)
        lbl(d, (u2b.out[0] - 0.1, u2b.out[1] + 0.35), "7", halign="right", fontsize=7)
        lbl(d, (u2b.center[0] - 0.2, u2b.center[1] - 1.5), "U2B\nLM358AP\nfollower", halign="center")
        # follower feedback: out → in1
        d.add(elm.Line().up(1.0).at(u2b.out))
        top = d.here
        d.add(elm.Line().left(u2b.out[0] - u2b.in1[0] + 0.3).at(top))
        d.add(elm.Line().toy(u2b.in1[1]))
        d.add(elm.Line().to(u2b.in1))
        d.add(elm.Dot().at(u2b.out))
        d.add(elm.Line().right(1.0).at(u2b.out))
        net(d, d.here, "V_REF")
        lbl(d, (X2, 2.1), "V_REF [mV] = 11·T_start − 155\n(measure at U2 pin 7)",
            halign="left", fontsize=8, color="darkred")

        # ═══ 3. AMPLIFIER ════════════════════════════════════════════════════
        X3 = 31.5
        d.add(elm.Label().at((X3, 11.2)).label("3 · AMPLIFIER  (gain 11)", fontsize=10, halign="left"))
        j2 = d.add(elm.Ic(pins=[elm.IcPin(name="GND", side="right", pin="3"),
                                elm.IcPin(name="OUT", side="right", pin="2"),
                                elm.IcPin(name="VS", side="right", pin="1")],
                          edgepadW=0.8, pinspacing=1.0, leadlen=0.5, lsize=8, plblsize=7,
                          label="J2\nLM35DZ\n(U4,\noff-board)").at((X3, 3.6)))
        d.add(elm.Line().right(0.8).at(j2.VS))
        net(d, d.here, "+5V", loc="top")
        d.add(elm.Line().right(0.8).at(j2.GND))
        d.add(elm.Ground())

        u2a = d.add(elm.Opamp(leads=True).right().anchor("in2").at((X3 + 7, j2.OUT[1])))
        d.add(elm.Line().at(j2.OUT).to(u2a.in2))
        lbl(d, (u2a.in2[0] + 0.1, u2a.in2[1] - 0.35), "3", halign="left", fontsize=7)
        lbl(d, (u2a.in1[0] + 0.1, u2a.in1[1] + 0.35), "2", halign="left", fontsize=7)
        lbl(d, (u2a.out[0] - 0.1, u2a.out[1] + 0.35), "1", halign="right", fontsize=7)
        lbl(d, (u2a.center[0] - 0.2, u2a.center[1] - 1.4), "U2A\nLM358AP", halign="center")

        # inverting node: R2 from V_REF, R3 to output
        d.add(elm.Line().left(0.6).at(u2a.in1))
        n_inv = d.here
        d.add(elm.Dot())
        d.add(elm.Line().up(1.6).at(n_inv))
        fb = d.here
        d.add(elm.Resistor().right().at(fb).tox(u2a.out[0] + 0.6))
        lbl(d, ((fb[0] + u2a.out[0]) / 2, fb[1] + 0.55), LABEL["R3"].replace("\n", " "), halign="center")
        d.add(elm.Line().toy(u2a.out[1]))
        d.add(elm.Dot())
        d.add(elm.Line().at(u2a.out).right(0.6))
        d.add(elm.Resistor().left().at(fb).length(2.4))
        lbl(d, (fb[0] - 1.2, fb[1] + 0.55), LABEL["R2"].replace("\n", " "), halign="center")
        net(d, d.here, "V_REF", loc="left")
        d.add(elm.Line().right(1.2).at((u2a.out[0] + 0.6, u2a.out[1])))
        net(d, d.here, "V_ADJ")
        lbl(d, (X3, 1.2), "V_ADJ = 11·V_LM35 − 10·V_REF   (0 … ~3.5 V)", halign="left", fontsize=8,
            color="darkred")

        # ═══ 4. FAN REGULATOR ════════════════════════════════════════════════
        X4 = 45.5
        d.add(elm.Label().at((X4, 11.2)).label("4 · FAN SUPPLY", fontsize=10, halign="left"))
        net(d, (X4, 8), "VIN", loc="left")
        d.add(elm.Line().right(1.2).at((X4, 8)))
        c1 = d.here
        d.add(elm.Dot())
        d.add(elm.Capacitor().down().at(c1).length(2.2))
        lbl(d, (c1[0] + 0.4, c1[1] - 1.1), "C1\n100n", halign="left")
        d.add(elm.Ground())
        u1 = d.add(elm.Ic(pins=[elm.IcPin(name="IN", side="left", pin="3"),
                                elm.IcPin(name="OUT", side="right", pin="2"),
                                elm.IcPin(name="ADJ", side="bottom", pin="1")],
                          size=(2.6, 1.6), lsize=8, plblsize=7, label="U1\nLM317T").right().anchor("IN").at((c1[0] + 1.6, c1[1])))
        d.add(elm.Line().at(c1).to(u1.IN))
        d.add(elm.Line().down(2.4).at(u1.ADJ))
        net(d, d.here, "V_ADJ", loc="bottom")

        d.add(elm.Line().right(1.2).at(u1.OUT))
        vf = d.here
        d.add(elm.Dot())
        lbl(d, (vf[0] + 1.0, vf[1] + 0.9), "V_FAN 1.25–4.75 V", halign="center", color="darkred")
        cols = [("C2\n10µ/25V", elm.Capacitor(polar=True)), (LABEL["R4"] + "\nmin load", elm.Resistor()),
                ("D1\n1N4007", elm.Diode().reverse())]
        x = vf[0]
        for i, (txt, e) in enumerate(cols):
            if i:
                d.add(elm.Line().right(1.9).at((x, vf[1])))
                x += 1.9
                d.add(elm.Dot().at((x, vf[1])))
            el = d.add(e.down().at((x, vf[1])).length(2.4))
            d.add(elm.Ground().at(el.end))
            lbl(d, (x + 0.45, vf[1] - 1.2), txt, halign="left")
        d.add(elm.Line().right(2.2).at((x, vf[1])))
        j3 = d.add(elm.Ic(pins=[elm.IcPin(name="M", side="left", pin="2"),
                                elm.IcPin(name="P", side="left", pin="1")],
                          edgepadW=0.8, pinspacing=1.2, leadlen=0.5, lsize=8, plblsize=7, label="J3\nFAN\n5V 0.2A")
                   .right().anchor("P").at(d.here))
        d.add(elm.Line().left(0.6).at(j3.M))
        d.add(elm.Ground())
        lbl(d, (X4, 1.2), "U1 heat: 0.9 W @ 9 V in — HS1 heatsink above ~12 V in (tab = OUT!)",
            halign="left", fontsize=8, color="darkred")

        d.save(path)


if __name__ == "__main__":
    schemdraw.use("svg")
    draw(os.path.join(HERE, "fan_controller.svg"))
    schemdraw.use("matplotlib")
    draw(os.path.join(HERE, "fan_controller.png"))
    print("Saved: fan_controller.svg / .png")
