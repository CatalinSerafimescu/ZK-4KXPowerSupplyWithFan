# Solder-mask jig

`Mask_jig.step` / `.stl`, made by `gen_mask_jig.py` (run in the FreeCAD GUI). 110.8 × 86.8 × 4.4 mm, print
floor-down, no supports.

- **Pocket** 90.8 × 66.8 mm (0.4 mm per side around the 90 × 66 board), **1.4 mm deep**: a 1.5–1.6 mm board sits
  0.1–0.2 mm proud, so the film is pressed onto the board and then lies flat on the 10 mm frame. If your board
  is thinner than 1.4 mm, put a paper shim under it.
- **4 × Ø3.2 through holes** at the board's mounting holes (4 mm in from each corner) for registration pins —
  Ø3 drill-bit shanks or M3 screws pushed up from below.
- Corner reliefs (square board corners in an FDM pocket) and 2 × Ø12 holes to push the board out from below.

## Use (UV solder mask)
1. Etched board **drilled**, cleaned, copper side up in the pocket. Pins up through the mounting holes.
2. Film: the two B.Mask copies from page 3 of `KiCAD/toner_B.Cu_1to1.pdf`, stacked, **toner side down**. Punch/drill
   Ø3.2 through the 4 black corner dots (the mounting-hole openings) with the stack taped together.
   The mounting holes are symmetric, so the pins alone don't fix the orientation: check the two big HS1 dots and
   the pad rows line up with the board before the paste goes on.
3. Paste on the board, film down over the pins, squeegee from the centre outwards (excess goes into the gap and
   onto the frame). Tape the film edges to the frame.
4. Pull the pins out **downwards**, lay a sheet of glass on top for even pressure, expose. Ordinary picture-frame
   glass passes 395–405 nm LEDs well but cuts a lot at 365 nm — expose longer, or skip the glass with a 365 nm lamp.
5. Paste squeezed onto the frame cures there too: cover the frame with one layer of packing tape before step 3 and
   peel it off afterwards, so the frame stays flat for the next board.
