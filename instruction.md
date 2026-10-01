# Assembly instructions — ZK-4KX bench supply with temperature-controlled fan

Everything needed to build, wire, test and calibrate the unit. Part data: [bom.md](bom.md).
Design details: [README.md](README.md), [KiCAD/PCB_info.md](KiCAD/PCB_info.md), [simulation/](simulation/README.md).

---

## 1. What you are building

```
 9 V adapter ─► DC jack J5 ─► SW1 ──┬─► ZK-4KX  IN+/IN−   ZK-4KX OUT+/OUT− ─► banana J6 (red) / J7 (black)
 (5.5×2.1, centre +)   (on/off, + wire) │
                                    └─► fan board J1 ─► 78L05 (+5 V) ─► LM358 + LM35 ─► LM317 ─► J3 ─► fan M1
                                                  LM35 (on the ZK-4KX heatsink) ─► J2
```

- The fan is **off** below a start temperature **T_start** (set with trimmer RV1, ≈ 15–52 °C).
- Above it, fan speed rises **proportionally**: starts at T_start (≈ 2.8 V), full speed at ≈ T_start + 18 °C (≈ 4.75 V).
- Fail-safes: LM35 disconnected → fan full speed; trimmer wiper open → fan runs from ≈ 17 °C.
- The fan voltage can never exceed ≈ 4.75–5.0 V, whatever the input voltage.

**Input voltage:** 9–28 V (limit set by the 78L05, max ≈ 30 V). The ZK-4KX itself accepts 5–30 V.
With the 9 V / 2 A adapter the ZK-4KX can deliver about 15 W (it draws ≈ 3× the output current when boosting).

---

## 2. Parts and tools

All parts are in [bom.md](bom.md) with inventory IDs. **Still to buy:** 4× M3 standoffs + screws for the board.
Check before starting: the JST XH kit shows **qty −5** in the inventory — make sure you have 2× 2-pin and 1× 3-pin headers + housings + crimps.

| Board parts | Off-board parts |
|---|---|
| U1 LM317T/NOPB, U2 LM358AP (+ DIP-8 socket), U3 UA78L05, R1 100k, R2 10k, R3 100k, R4 220 Ω, R5 100k, RV1 3386P 10k trimmer, C1/C3/C5 100 nF, C2/C4 10 µF 25 V, D1 1N4007, J1 XH-2, J2 XH-3, J3 XH-2, HS1 RAD-DY-KY/3 + Stonecold TO220-SET insulating kit | PS1 ZK-4KX, M1 fan 30×30 5 V 0.2 A, U4 LM35DZ, J5 DC jack 5.5×2.1 panel, SW1 DS-431 latching push switch, J6/J7 4 mm banana sockets red/black, Kapton tape, thermal paste |

Tools: soldering iron, multimeter, JST XH crimp tool, screwdriver for the trimmer, M3 screwdriver/nut driver, heat-shrink.
Wire: **0.75–1 mm² (AWG 18)** for input and ZK-4KX output (up to 4 A); thin wire (AWG 24–26) for fan and LM35.

---

## 3. Before you build

1. **The PCB is single-sided** (copper on the bottom only, no vias, no wire jumpers), 1.0 mm tracks, GND pour — made
   for toner transfer. Print [KiCAD/toner_B.Cu_1to1.pdf](KiCAD/toner_B.Cu_1to1.pdf) at **100 %** (no fit-to-page),
   **not mirrored**, and check the 90 × 66 mm outline with a ruler. Drills: 0.8 mm (R, C, U2, U3, RV1),
   1.0 mm (J1, J2, J3), 1.1 mm (U1, D1), 2.2 mm (HS1 pins), 3.2 mm (mounting holes). Details:
   [KiCAD/PCB_info.md](KiCAD/PCB_info.md).

   **Printing the films (Canon LBP6020).** Print from the PDF viewer at **Actual size / 100 %**, **A4 portrait**,
   one page at a time: page 1 (B.Cu + mirrored F.SilkS) on thermal transfer paper, page 3 (B.Mask, two copies) on the
   transparency, page 2 on plain paper (assembly reference). Everything is in the top 77 mm of the page — the rest of
   the sheet can be cut off and used for the next print. Driver settings (*Printing Preferences*):

   | Driver setting | Page 1 → thermal transfer paper | Page 3 → Xerox Premium Transparency (003R98198) |
   |---|---|---|
   | Page Setup → Output Size | A4 | A4 (*Transparency* is only offered for A4 / Letter) |
   | Paper Source → Paper Type | **Plain Paper**; switch to **Heavy Paper** (then **Heavy Paper H**) only if the toner rubs off with a fingernail | **Transparency** — never Plain: the fuser runs too hot/fast for film and can melt it onto the roller |
   | Quality → Advanced Settings → Toner Save | **Off** | **Off** |
   | Quality → Advanced Settings → Toner Density | **maximum** | **maximum** |
   | Quality → Advanced Settings → Halftones | **None [Solid]** (no dither in the GND pour) | **None [Solid]** |
   | Finishing → Advanced Settings → Special Print Mode A/B, Special Print Adjustment A/B | Off (they all lower density) | Off |
   | Finishing → Advanced Settings → Output Adjustment Mode | On (higher resolution for the 0.5 mm clearances) | On |

   - **Which side prints:** on the LBP6020 load the sheet with the side to print **facing up**. Check once with a plain
     sheet marked with an X before wasting a transfer sheet or a film.
   - **Feed one sheet at a time**, holding it by the edges (fingerprints stop toner from sticking). Transfer paper:
     print on the **glossy/coated side**. Transparency: laser-grade film, fan it first. The removable stripe must not
     lie under a board (boards: 11–77 mm from the top edge, 11–201 mm across) — if it runs along a short edge, feed
     that edge last so it ends up at the bottom of the page.
   - Take each sheet out as soon as it comes out, let it cool flat, don't touch the toner. Check for pinholes against
     a lamp: a pinhole in the GND pour becomes a pit in the copper.
   - **Solder mask film:** laser toner does not fully block UV, so page 3 has **two copies**. Cut them apart and stack
     them exactly on top of each other (align on the pads over a lamp, a drop of superglue or tape at the corners). Expose with the
     toner side towards the board — less parallax. Black = pad openings; the rest of the UV mask hardens.
2. **Measure the real parts** and correct the footprints if needed (then re-run `KiCAD/gen/gen_heatsink.py`):
   - Heatsink RAD-DY-KY/3: pin diameter (hole is 2.2 mm), pin spacing (34 mm), fin gap on the flat side (≈ 19.6 mm), **height of the M3 hole**.
   - 100 nF capacitors: lead pitch (footprint 5.0 mm).
3. **Adapter polarity:** the design assumes a **centre-positive** 9 V adapter — check its label.

---

## 4. Board assembly (low parts first)

Pin 1 of every part is the **square pad**.

| Step | Part | Notes |
|---|---|---|
| 1 | R1–R5 | Not polarised. R1, R3, R5 = 100 kΩ, R2 = 10 kΩ, R4 = 220 Ω. |
| 2 | D1 1N4007 | **Band (cathode) on the square pad "K"** — cathode goes to V_FAN. |
| 3 | DIP-8 socket | Notch towards pin 1. Do **not** insert U2 yet. |
| 4 | C1, C3, C5 100 nF | Not polarised. C1 at U1, C3 at U3, C5 beside U2 (on its +5 V track). |
| 5 | RV1 trimmer 3386P | Only fits one way. |
| 6 | U3 UA78L05 (TO-92) | Pads are 2.54 mm apart (wider than the TO-92 legs, for home etching) — splay the legs slightly. Pin 1 (square pad) = **OUTPUT**, 2 = GND, 3 = INPUT. Its pinout is reversed vs a 7805 — follow the pad numbers, not the 7805 habit. |
| 7 | C2, C4 10 µF | **+ on the square pad.** Stripe (−) away from it. |
| 8 | J1, J2, J3 JST XH | Latch side as printed on the silkscreen. |
| 9 | HS1 heatsink | Solder its two pins. It stands 30 mm tall. |
| 10 | U1 LM317T | See below. |

### Mounting U1 on the heatsink
The LM317 tab is connected to its **OUT** pin (= V_FAN), so it **must be insulated** from the heatsink.

1. Put U1's legs through the board **without soldering**.
2. Stack: heatsink ← insulating pad (from the TO220-SET) ← U1 tab ← shoulder bushing ← M3 screw (+ washer/nut if the set has none).
   The screw goes into the heatsink's **M3 thread**.
3. Adjust U1's height so the tab hole lines up with the heatsink hole — if the hole is at mid-height (15 mm),
   the TO-220 body stands **≈ 2 mm above the PCB**.
4. Tighten moderately (soft pad — do not crush it).
5. **Check isolation:** multimeter on Ω between the heatsink and U1's tab/middle pin → must read **open (OL)**.
6. Only now solder U1's three legs. Pin 1 (square pad) = ADJ, 2 = OUT, 3 = IN.

At 9 V input U1 dissipates ≈ 0.9 W; at 30 V ≈ 5.3 W (Tj ≈ ambient + 58 °C with this heatsink).

---

## 5. Enclosure and wiring

Printed case: [mechanical/enclosure/](mechanical/enclosure/README.md) — base (floor + front + rear panels) and a U-shaped cover.
Front panel: ZK-4KX on top; below it, left to right: power switch SW1, red **+**, black **−**. DC jack on the rear.
Board on 4 × 6 mm standoffs (M3×10 + nuts under the floor), cover held by 4 × M3×10 from below, fan on the cover's left wall.
**Trim all board leads to ≤ 3 mm** below the PCB (6 mm standoffs).

### ZK-4KX (PS1)
- Panel cutout **71 × 39 mm**; body 79 × 43 × 26 mm (model: `mechanical/stl/`).
- Terminal block on the back: **IN+, IN−, OUT+, OUT−**.
- **Never connect OUT− to IN−** (the module measures current between them). Never short IN to OUT.

### DC jack J5 (panel, 3 tabs)
The jack has three tabs: **centre pin**, **sleeve**, and a **switch** contact (touches the sleeve only when no plug is inserted).
Identify them with the multimeter (continuity) before soldering: plug in the adapter's connector and see which tab
connects to the plug's barrel — that is the sleeve; the switch tab loses contact when the plug goes in. Leave the switch tab unconnected.

### Power switch SW1 (DS-431, front panel)
Latching push switch with 2 pins: pressed in = **on**, pressed again = **off**. It sits in the **+ wire**, before the
split to the ZK-4KX and the fan board, so it switches both (off = no fan either). It snaps into an ≈ 11.7 × 11.0 mm
hole from the front. Before soldering, check with the multimeter which state is "on" (continuity when latched in).
**Current rating:** read the rating on the switch body — it must be ≥ 2 A DC for the 9 V / 2 A adapter. With a 30 V
supply and the ZK-4KX at its full 30 V / 4 A, the input current is ≈ 5 A; a small switch is not rated for that.

### Wiring table
| From | To | Wire |
|---|---|---|
| J5 DC jack centre (+) | **SW1** pin 1 | 0.75–1 mm² |
| **SW1** pin 2 | ZK-4KX **IN+** and board **J1 pin 1** | 0.75–1 mm² to the ZK-4KX, thin to J1 |
| J5 DC jack sleeve (−) | ZK-4KX **IN−** and board **J1 pin 2** | same (not switched) |
| ZK-4KX **OUT+** | J6 red banana | 0.75–1 mm² |
| ZK-4KX **OUT−** | J7 black banana | 0.75–1 mm² |
| Fan red (+) / black (−) | board **J3 pin 1 / pin 2** | fan leads |
| LM35 +Vs / Vout / GND | board **J2 pin 1 / 2 / 3** | 3 thin wires |

### LM35 (U4) on the ZK-4KX heatsink
The ZK-4KX has a finned aluminium heatsink in the middle of its back PCB, above the terminal block
(the switching MOSFETs are under it) — that is the hot spot to measure.

1. **Measure the heatsink potential first:** multimeter between the heatsink and IN− with the module powered.
   If it is not 0 V (it may be tied to a MOSFET / switching node), the LM35 legs must not touch it.
2. Flat face of the LM35 against the heatsink base at the fin root, with a little thermal paste; fix with Kapton
   (or thermally conductive epoxy).
3. Insulate the three legs (Kapton or heat-shrink). Check the LM35 pinout (+Vs, Vout, GND) against the TI datasheet
   drawing before soldering the wires — a reversed LM35 heats up and reads nonsense.
4. Route the wires away from the toroid inductor. If they are **longer than ≈ 20 cm**, add a 75–100 Ω resistor in series
   with 1 µF from Vout to GND at the sensor (datasheet damper).

### Fan (M1) and board
- Place the fan so it blows **onto the ZK-4KX's rear heatsink**; give the enclosure inlet and outlet vents.
  The fan is **10 mm** thick (STEP model: `mechanical/fan/Fan_30x30x10_5V_2pin.step`).
- Mount the board on 4 M3 standoffs; keep the **trimmer RV1 reachable** with a screwdriver and U2 pin 7 reachable
  with a probe (for calibration).
- HS1 is not connected to any net (U1's tab is insulated from it) — still keep it clear of other metal.

---

## 6. First power-up

Use the 9 V adapter (or a bench supply with current limit ≈ 200 mA for the board alone).

1. **U2 out of its socket and the fan unplugged.** Do **not** power the board with the fan connected while U2 is
   missing: the LM317's ADJ pin would float and V_FAN would rise towards V_in.
2. Power on (SW1 latched in). Measure to GND:
   - J1 pin 1 (VIN): ≈ 9 V
   - C4 + (or U2 socket pin 8): **4.75–5.25 V**. If not, check U3's orientation.
3. Power off. Insert **U2 LM358AP** (notch to pin 1). Plug in the fan (J3) and the LM35 (J2).
4. Power on. At room temperature with T_start set above it, V_FAN (C2 +) ≈ **1.25 V** and the fan does not spin.

---

## 7. Calibration — setting the start temperature

Measure **U2 pin 7 to GND** (V_REF) and turn RV1 (clockwise = hotter):

> **V_REF [mV] = 11 × T_start − 155**

| Fan starts at | V_REF (U2 pin 7) |
|---|---|
| 35 °C | 230 mV |
| 40 °C | 285 mV |
| 45 °C | 340 mV |
| 50 °C | 395 mV |
| 52 °C (≈ max) | 417 mV |

Recommended start: **40–45 °C** on the ZK-4KX heatsink. The fan reaches full speed ≈ 18 °C higher,
well before the ZK-4KX's own over-temperature protection (settable 80–110 °C).

**Check:** warm the LM35 (fingers, hair dryer). LM35 output (J2 pin 2) = 10 mV/°C. The fan should start near T_start
and V_FAN should rise ≈ 0.11 V/°C up to ≈ 4.75 V.

Narrower ramp (≈ 9.5 °C instead of 18 °C): replace R2 with 5.1 kΩ (then V_REF = (20.6·T_start/100 − 1.55) / 19.6 V).

---

## 8. Troubleshooting

| Symptom | Check |
|---|---|
| Nothing works | SW1 off (latched out), or its rating/contacts — measure VIN on both SW1 pins |
| No +5 V | U3 reversed (pin 1 = OUTPUT), C3/C4 shorted, VIN missing on J1 |
| Fan always full speed | LM35 disconnected or wrongly wired (fail-safe → full), J2 pinout |
| Fan never starts | V_REF too high (turn RV1 anticlockwise); LM35 reading low; fan needs > 2.8 V to start — lower T_start a little |
| Fan starts at ≈ 17 °C regardless of RV1 | RV1 wiper not contacting (R5 fail-safe active) |
| V_FAN > 5 V | U2 missing or ADJ (U1 pin 1) not connected to U2 pin 1 |
| Heatsink shorts / fan voltage wrong | U1 tab not insulated — check the TO220-SET pad and bushing |
| U1 very hot | Input voltage high: 5.3 W at 30 V is normal for this design; make sure HS1 gets airflow |

---

## 9. Reference values

| Point | Value |
|---|---|
| +5 V rail (U3 out) | 4.75–5.25 V |
| V_REF (U2 pin 7) | 0 … ≈ 0.42 V (sets T_start) |
| LM35 out (J2 pin 2) | 10 mV/°C (e.g. 0.40 V at 40 °C) |
| V_ADJ (U2 pin 1) | 11·V_LM35 − 10·V_REF, 0 … ≈ 3.5 V |
| V_FAN (J3 pin 1) | V_ADJ + 1.25 V → 1.25 V (off) … ≈ 4.75 V (full) |
| U1 dissipation | 0.9 W @ 9 V in, 5.3 W @ 30 V in |

Simulated in ngspice and LTspice (11 scenarios, all pass in both): [ngspice](simulation/ngspice/results/RESULTS.md), [LTspice](simulation/ltspice/results/RESULTS.md).
