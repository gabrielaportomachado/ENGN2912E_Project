# Layout specification of dbs_afe_top (LP, 2026-11-20; R2 / R3 / Decision 48 numbers; section 1 rewritten for Decision 52: 605 x 1110 um, 4 channels; section 1 numbers updated by R14 for the 86.24 um macro. Sections 2-6 still describe 8 channels where they name channel counts or pads: updated by the Decision 52 work items)

Single source of the numbers: `AFE/layout/floorplan.json` (built and checked by `AFE/layout/scripts/floorplan.py`). This file explains them. Where the two differ, floorplan.json wins.
Every layout phase reads both before drawing and runs `python3 AFE/layout/scripts/floorplan.py check` (must print 0 FAIL) before it stops.
Units um; origin = SW corner of the outline; "inner" = towards the digital macro, "outer" = towards the chip edge. Sources are given in brackets.

## 1. Outline and floorplan (Decision 52: 605 x 1110 um, 4 channels; the 8-channel 1000 x 1000 um version is tag checkpoint-n8-final)

- Outline 605 x 1110 um (W x H) = the PR boundary of `gds/dbs_afe_top.gds` (organizer revision, Decision 52; supersedes the 1000 x 1000 um of Decision 45). Never exceed it. `floorplan.py check --gds dbs_afe_top=<file>` tests it.
- Two rows of two channel slots with the digital macro as a strip between them and the bias cell at the east end of that strip. The channel slot, amp_ch, adc_ch and the TGATE zone are the same as in the 8-channel plan (only taller: 448.88 um after R14); the cells of L2a / L1a are reused unchanged.

```
 y
1110 +-------------------------------------------+
     | pin ring N: E0 REC0 IPG0  E1 REC1 IPG1      |
1084 |  +-------------------------------------+   |
     |  | bias corridor N (12): bias lines REF|   |
1072 |  +-----------+-----------+-------------+   |
     |  | ch0 (R0)  | ch1 (R0)  | spare_ne    |   |
     |W |  amp end  |           | (79 x 449)  | E |
     |  |  TGATE / amp_ch 222 x 336.88 / adc_ch 222 x 104 |   REF pin (y 555)
     |  |  ADC end  |           |             |   |
 623 |  +-----------+-----------+------+------+   |
     |  | strap corridor N (25) + decap | bias |   |
 598 |  +-------------------------------+ genc |   |
     |  | afe_dig 425 x 86.24           | 108 x|   |
     |  | (pins N: ch0-1, S: ch2-3,     |  116 |   |
     |  |  W: SPI / pad control)        |      |   |
 512 |  +-------------------------------+      |   |
     |  | strap corridor S (25)         |      |   |
 487 |  +-----------+-----------+------+------+   |
     |  | ch2 (MX)  | ch3 (MX)  | spare_se    |   |
  38 |  +-----------+-----------+-------------+   |
     |  | bias corridor S (12)                |   |
  26 |  +-------------------------------------+   |
     | pin ring S: E2 REC2 IPG2  E3 REC3 IPG3      |
   0 +-------------------------------------------+
     0 26        263         500         579 605  x
   W edge: VSS (y 497.9), 21 digital / pad-control pins (y 514.9 .. 584.9, 3.5 um pitch) + DOUT_IN (588.4), VDD (y 612.1)
   N / S edges per channel slot (x from the slot's west edge): E at 70, REC at 118 (Decision 53), IPG at 165 um
```

| block | x | y | W x H | orientation | source |
|---|---|---|---|---|---|
| ch0, ch1 (`afe_ch` slot) | 26 + 237 k | 623.12 | 237 x 448.88 | R0: ADC end at y = 623.12, amplifier end at y = 1072 | floorplan.json placements |
| ch2, ch3 | 26 + 237 (k - 2) | 38 | 237 x 448.88 | MX (mirrored about x): ADC end at y = 486.88, amplifier end at y = 38 | |
| afe_dig | 26 | 511.88 | 425 x 86.24 (slot) | R0 | Decision 54 / R14: dbs_ctrl #(.N(4)) + adc_top #(.N(4)), hardened at 424.48 x 86.24 um (the smallest height that routes AND stays <= 60 % utilisation; 78.4 um also routes, at 64.7 %) |
| bias_genc region | 471 | 496.88 | <= 108 x 116.24 | R0, pins towards the east ring | 20 um from the macro, 10 um from the ADC ends of ch1 / ch3 |
| spare_ne / spare_se | 500 | 623.12 / 38 | 79 x 448.88 | - | not assigned: REF / bias trunk widening, decap or wiring (L3a) |

Why this shape: as in the 8-channel plan, every channel's 29 ADC control pins face the macro directly, the amplifier inputs are at the far end (> 100 um from any SCLK-rate wire) and the bias lines never cross a digital wire.
A single column of 4 channels does not fit (4 x 449 um > 1110 um).

**Area and margin** [floorplan.json `area`; estimates from AFE/review/sim/f1_area.log]:

| cell | slot | estimate | slot / estimate - 1 | as built |
|---|---|---|---|---|
| amp_ch | 222 x 336.88 = 74,787 um2 | 51,626 um2 (20 pF Cin; Cin is 15 pF since Decision 50) | +45 % | 220.75 x 273.25 um (R6b): fits with 1.25 / 63.6 um margin (the height freed by the smaller macro, R14) |
| adc_ch | 222 x 104 = 23,088 um2 | 14,911 um2 | +55 % | 219.50 x 103.67 um (R5 + L1b trim): fits with 2.5 / 0.33 um margin |
| bias_genc | 108 x 116.24 = 12,554 um2 | 9,966 um2 | +26 % | not drawn yet (L3a) |
| afe_dig | 425 x 86.24 = 36,652 um2 | 18,879 um2 of std cells (AS BUILT, 855 cells, 4 channels; the N = 8 estimate was 33,661) | 52 % (floorplan.py check 4b) | 424.48 x 86.24 um, flow utilisation 58.6 % (R14) |

The outline allows a top-level factor of about 2.17 on the 4-channel share of the F1 block sum (ESTIMATE: 618,660 um2 x 4 / 8).

## 2. Chip pins (41 port bits = 24 pads, Decision 45)

`floorplan.json pins` lists every port bit of module `dbs_afe_top` once, with pad, side, position, layer and target; `floorplan.py check` tests it against `AFE/top/dbs_afe_top.v` and `info.yaml`
(organizer rule: an input pad `X` has ports X, X_PU, X_PD; the bidirectional pad DOUT has DOUT_IN, DOUT_OUT and 8 control ports).

- **These positions are a DEFAULT** (no organizer DEF existed on 2026-11-20). They are chosen so that no pin wire crosses another: E[k] / IPG[k] above (below) channel k's TGATE zone, REF at the
  middle of the east edge next to the bias cell, the 21 digital / pad-control pins on the west edge at the same y and in the same order as the west pins of afe_dig (straight Metal3 wires across the
  ring), VDD and VSS just above and below them (the star point). `info.yaml` lists the pads in this perimeter order (clockwise from the NW corner).
- **When the organizer's DEF arrives:** copy it to `AFE/layout/organizer/` and re-place only the pins: every pin keeps its target, the wires run in the ring lanes (section 5). No block moves.
  If a pin lands more than 300 um from its default, say so in the phase findings (longer E / IPG wires only add capacitance on a 1-50 kOhm node; a long VDD / VSS wire must be >= 20 um wide).
- Pin shapes: Metal5 2 um for the analog pins, Metal3 0.6 um for the digital ones, Metal5 / Metal4 20 um for VDD / VSS, each touching the outline edge, labelled with the port name on the label
  datatype of its metal (kpdk.label). Bus bits are written `E[0]` (organizer examples use bracketed names).

## 3. Cell contracts

Common to all cells: generated by a script (common rule 2) run through `bash AFE/layout/scripts/kl.sh`; devices from the PDK pcells (`kpdk.pcell`), except the metal resistor (`kpdk.metal_res`);
every coordinate a multiple of 5 nm; pins = labels on the label datatype of the pin metal, names exactly as the LVS reference; one substrate tap within 15 um of every 5 V / 6 V device and 20 um of
every 3.3 V device (DRC DF.13 / DF.14); DRC / LVS / PEX only with `AFE/layout/scripts/flow.py`. LVS references: `AFE/layout/lvs/` (never edited by hand).

### 3.1 afe_ch = one channel slot, 237 x 386.04 um (assembled by L3a; not a separately extracted cell unless L3a wants one)

Tiling of the slot (north-row orientation, y = 0 at the ADC end) [floorplan.json `cells.afe_ch.sub`]:

| part | x | y | what |
|---|---|---|---|
| control corridor | 0 .. 8 | 0 .. 386.04 | sw_rec, sw_rec_b, sw_ipg, sw_ipg_b, rst_amp from the macro side to the amplifier end: 5 lines Metal2, 0.5 um wide, 1.4 um pitch, a vss line (Metal2) on the cell side. Quasi-static nets (they move only at a mode change). |
| adc_ch | 8 .. 230 | 0 .. 104 | section 3.3 |
| amp_ch | 8 .. 230 | 104 .. 378.04 | section 3.2 |
| TGATE zone | 8 .. 230 | 378.04 .. 386.04 | rec_tg and ipg_tg (TGATE/TGATE.gds), EACH with one `gf180mcu_fd_sc_mcu7t5v0__filltie` abutted (well + substrate tap: without it the TGATE fails DRC DF.13_MV / DF.14_MV and its PMOS bulk floats; test cell lp_tgate_tap). Next to amp_ch's `rec` pin; the net `rec` (TGATE OUT to amp_ch.rec) shorter than 30 um, no other net within 2 um of it. TGATE VDD / VSS = analog strap. |
| spur corridor | 230 .. 237 | 0 .. 386.04 | analog vdd (Metal4, 3 um) over vss (Metal3, 3 um) from the bias corridor to adc_ch.vdd; amp_ch may tap it |

Internal nets of afe_ch: `rec`, `amp_out` (amp_ch.out to adc_ch.vin: one Metal3 wire, shorter than 20 um, vss on both sides). Nothing of the top level crosses amp_ch or adc_ch.

### 3.2 amp_ch (L2a / L2b), slot 222 x 274.04 um, reference `AFE/layout/lvs/afe_chc.spice` subckt amp_ch

Pins: ref sw_rec sw_rec_b rst_amp vbn vcm vg1 vcmo vg2 vrs rec out vdd vss. Rail: analog strap only.

| pin | preferred side (north-row orientation) | layer | connects to |
|---|---|---|---|
| rec | outer edge | Metal5 (the Cin1 bottom plates leave through Via4, MIMTM.10) | TGATE zone |
| ref | outer edge | Metal5 (same reason; the REF net must not join the plates of several channels on Metal4, MIMTM.11) | REF line of the bias corridor |
| vbn vcm vg1 vcmo vg2 vrs | outer edge | Metal2 or Metal3 | bias corridor |
| sw_rec sw_rec_b rst_amp | west edge, within 60 um of the outer edge | Metal2 | control corridor |
| out | inner edge | Metal3 | adc_ch.vin |
| vdd vss | outer edge and / or east edge | Metal3 / Metal4, >= 2 um | analog strap |

L2a ran before this file existed. If its cell has a pin on another side, L2b or L3a adds the wrap-around wire inside the 2 um margin of the slot or re-runs the amplifier generator with the
pin side as a parameter; no device changes (ACCEPT.md ladder G-5).

Matching and leakage rules (PLAN.md sections 1.2 and 5; Decisions 39, 46a, 46c; LP findings):
1. Input capacitors: Cin1 (rec to vn) and Cin2 (ref to vp) = 2 pieces each of 61.15 x 61.15 um = 7.4995 pF (15 pF per input, Decision 50; the 20 pF layout had 70.65 um, the reference of that time 70.649028: off grid; the 1 % LVS tolerance covers the rounding), placed as a
   2 x 2 checkerboard (Cin1 / Cin2 on the diagonals) so that both inputs see the same gradient. **Top plate (FuseTop / Metal5) = summing node, bottom plate (Metal4) = rec / ref** (Decision 46a;
   Magic terminal 1 = top plate, check_env.sh C3). Cf1 pieces (8.45 um = 150.15 fF; 9.79 um at 20 pF) next to the Cin block, same orientation; ratio Cin : Cf1 = 100 (as drawn 99.90).
2. Under the four Cin pieces: no device, no poly, no Metal1-3 of amp_ch (Decision 46c). The baseline floorplan does NOT put decap there (section 4); the area is the reserve.
3. OTA-1 input pair 2 x 16 x 50u/2u: common centroid (ABBA rows) with dummies at both ends; loads 8 x 50u/16u next to it.
4. **Pseudo-resistor transistors (6 x pfet_03v3 0.22u/0.5u): minimum drain / source area (no shared or extended diffusion), all six drawn identically, their n-wells as small as the rules allow.**
   The simulated DC state and the high-pass corner depend on their junction area (LP findings: with area on them the corner drops below 1 mHz and electrode offsets rail the output; ACCEPT.md section 2).
5. Summing nodes vn / vp / vn2 and the pseudo-resistor nodes: Metal1 guard (vss) around the connection, no other net within 2 um, not under any MIM plate other than their own, more than 20 um from
   any digital wire (section 5). P+ guard ring (vss) around the analog NMOS; the park switch and gate muxes inside their own ring.
6. The follower is `nfet_06v0_nvt`. If the organizer refuses the native device: ACCEPT.md ladder N (drop-in follower in an isolated p-well, `AFE/amp/spice/ota2_rvt.spice`).

### 3.3 adc_ch (L1a / L1b), slot 222 x 104 um, reference `AFE/layout/lvs/adc_ch.spice` subckt adc_ch

Pins: rst_sw tg_on cmp_clk dac_gdn dac_gp[11..0] dac_gn[11..0] cmp_q vin vdd vdd_cmp vdd_dac vss.

| pin | side | x in the cell (y = 0 at the inner edge) | layer |
|---|---|---|---|
| rst_sw, tg_on, dac_gdn, cmp_clk, cmp_q | inner edge | 12, 15, 18, 21, 24 | Metal2, 0.5 um wide, at the cell edge |
| dac_gp[11], dac_gn[11], dac_gp[10], dac_gn[10], ..., dac_gp[0], dac_gn[0] | inner edge | 27, 30, 33, 36, ..., 93, 96 (3.0 um pitch) | Metal2 |
| vdd_cmp | inner edge | 110 .. 130 | Metal4, >= 5 um |
| vdd_dac | inner edge | 140 .. 160 | Metal4, >= 5 um |
| vss | inner edge and east edge | 170 .. 210 | Metal4 / Metal3, >= 5 um |
| vin | outer edge | any | Metal3 |
| vdd (analog strap: vhalf, Cref switch, samb inverter, sampling-TG n-wells) | east edge (R5 as built: SOUTH edge, x 215 .. 221, Metal4, because the Cref plate fills the east edge; L3a wraps it to the spur corridor, ladder G-5) | - | Metal4, >= 2 um |

These x values are the pin positions of the afe_dig pin group of the channel (floorplan.json `cells.afe_dig.pins`, group start 8 um + 3.0 um x index, the cell starts at 8 um): the 29 wires
cross the strap corridor as straight Metal2 lines. A pin may be up to 1.5 um off; then L3a jogs it on Metal3 inside the corridor.

As built by R5 (219.5 x 103.67 um; AFE/layout/adc/FLOW_ADC.md section 6): drivers x 6 .. 112 / y 2.5 .. 26 (three rows), the keep-out band y 26 .. 44 with the vhalf serpentine (8 rows of 62.5 um) and the reset switches, the DAC array without dummy bars x 13 .. 118 / y 44 .. 102 above it, the comparator under Cref (x 111 .. 217 / y 5 .. 41.6, t on the west and vref on the east side), the vhalf capacitor + Cref switch + inverter in the column x 129 .. 157, Cref x 161 .. 220 / y 44 .. 103.

Original recommendation of LP (fits 220 x 102, superseded): driver row y 0 .. 14 (13 bottom-plate drivers, 13 sampling TGs, 2 reset switches, INV, all within x 10 .. 100); keep-out band y 14 .. 34 with only
bottom-plate wires, vin, the vhalf resistor pair and its 1 pF capacitor; above it, left to right: DAC unit array 16 x 8 sites on a 6.8 um pitch with one dummy ring (122.4 x 68 um), Cref
(59.07 um plate), comparator column (pair 2 x 80u/0.5u mirrored about the column axis, the two 5 x 5 um preamp MIM units symmetric).

Matching rules:
1. **DAC unit-to-bit map** (127 units 5 x 5 um + bridge 5.085 x 5 um; the reference says 5.082993). MSB array on the top-plate node `t`: b11 32 units, b10 16, b9 8, b8 4, b7 2, b6 1 (63).
   LSB array on node `m`: b5 32, b4 16, b3 8, b2 4, b1 2, b0 1, dummy `bd` 1 (64). Sites: MSB array = columns 0-7, LSB array = columns 8-15 of the 16 x 8 grid, each half filled common
   centroid about its own centre: place the units of a bit in point-symmetric pairs, largest bit first on the outermost free pairs, smallest in the centre; the one free site of the MSB half and
   the bridge capacitor sit on the boundary between the halves; a ring of dummy units (both plates on vss) around all 128 sites (L1a / R5: impossible, netgen counts dummy MIM units; the first build had two plain-metal bars, R5 draws none). **Top plate (FuseTop / Metal5) = `t` (MSB half) or `m` (LSB half);
   bottom plates (Metal4) = the driver nets.** Units of one bit may share a bottom-plate polygon. Record the site of every unit in the generator log (L1b needs it for the bridge check).
2. Bridge: top plate on `t`, bottom plate on `m`; the Metal5 / Metal4 of nodes `t` and `m` as short as possible, no wire of another net over or under the bridge node.
3. Cref: ONE plate 59.07 x 59.07 um, top plate = the floating node `vref` (to cmp_p.inp, shorter than 30 um, Metal5, vss guard), bottom plate = vss. **Inside the Cref bottom-plate footprint
   adc_ch draws nothing below Metal4** (no comp, poly, contact, Metal1-3): L3a places 4 decap units there (section 4). gate.py tests it.
4. vhalf: the two 250 um x 1 um ppolyf_u_1k resistors as ONE interdigitated serpentine (segments of equal length, ABAB), dummy segments outside, same orientation; tap `vcmd` in the middle.
5. Comparator: fully mirror-symmetric about its axis including the two clocked wires; `t` and `vref` enter from opposite sides with equal length.
6. Keep-outs: cmp_clk, dac_gp / dac_gn, dac_gdn, rst_sw, tg_on end at their devices in the driver row / comparator and never run within 20 um of the DAC top plates `t` / `m`, of `vref` or of
   Cref, except the last 10 um of cmp_clk at the comparator.

### 3.4 bias_genc (L3a), region 108 x 131.92 um at (866, 434.04), reference `AFE/layout/lvs/bias_genc.spice`

Pins vbn vcm_in vg1 vcm_out vg2 vrs vdd vss, towards the east ring (the bias trunk runs in the east ring to both bias corridors). Rail: analog strap.
- Ladders A (725 / 100 / 825 um) and B (375 / 450 / 825 um), 1 um wide ppolyf_u_1k: ONE serpentine block of unit segments of equal length (25 um suggested: 29 + 4 + 33 and 15 + 18 + 33
  segments), the segments of the three resistors of a ladder interleaved so that each has the same centre of gravity, dummy segments at both ends, all in the same orientation. The taps are
  ratios, so matching inside each ladder is what counts. Rb (2 x 120 um) separate.
- Reset-level replica (pfet 0.22u/0.5u, the same drawing as the pseudo-resistor transistors of amp_ch, same orientation) and C_VRS (49.885 um MIM, top plate = vrs) away from the east edge
  wiring; P+ guard ring around the cell; the cell is 20 um from the digital macro and its N-well ring.
- The pseudo-resistor gate taps vg1 / vg2 are set by the ladder segment counts: if a REVIEW.md item (or a later decision) changes VTT1 / VTT2 (ACCEPT.md section 2), only this cell changes.

### 3.5 afe_dig (L1d / R3), slot 820 x 101.92 um at (26, 449.04) (L1d: 819.84 x 109.76 um): see AFE/dig/LP_STEP5.md and floorplan.json `cells.afe_dig`

Pins: north edge = channels 0-3, south edge = channels 4-7, per channel 33 pins at 3.0 um pitch from x = 237 k' + 8 (order: sw_rec sw_rec_b sw_ipg sw_ipg_b rst_sw tg_on dac_gdn cmp_clk cmp_q,
then dac_gp / dac_gn pairs from bit 11 down to bit 0); west edge, south to north at 3.5 um pitch from y = 3 um above the macro's south edge (22 pins, the last at 76.5 um of the 101.92 um height): RSTN_PD RSTN_PU RSTN SCLK_PD SCLK_PU SCLK DIN_PD DIN_PU DIN CS_PD CS_PU CS DOUT DOUT_OE DOUT_IE
DOUT_PD DOUT_PU DOUT_CS DOUT_SL DOUT_PDRV0 DOUT_PDRV1 rst_amp_o. Rail: ADC-main strap (net VDD) and vss. `floorplan.py check --dig-pins AFE/dig/final/afe_dig_pins.json` tests the hardened macro.
Guard: P+ substrate ring (vss) and N-well ring (VDD) around the macro inside the strap corridors; >= 20 um to any analog device (the corridor is 25 um).

## 4. Supply (Decision 44d = AUDIT 4.9.2) and decap (Decision 46c)

One VDD pad, one VSS pad, star point in the west ring where the pins enter. In the netlist the analog and the ADC-main strap are the same net VDD; keep them separate metal down to the star point.

| strap | net | feeds | route | decap |
|---|---|---|---|---|
| analog | VDD | bias_genc, 8 x amp_ch.vdd, 8 x adc_ch.vdd, TGATE wells | west ring -> both bias corridors (Metal4, 12 um, over vss Metal3) -> spur corridor of every channel | none required |
| ADC-main | VDD | 8 x adc_ch.vdd_cmp, afe_dig | both strap corridors, Metal5 8 um over vss Metal4 | 74 units = 117.9 pF |
| ADC-DAC | vdd_dac | 8 x adc_ch.vdd_dac | behind the strap resistor, both strap corridors, Metal5 5 um | 64 units = 102.0 pF |

- **Strap resistor**: `rm3` 2 um x 222.2 um = 10.0 ohm typ (Decision 46e), drawn with `kpdk.metal_res(cell, 3, x, y, 222.2, 2.0)` (NOT the PDK pcell, which Magic does not extract), in the north
  strap corridor from x = 26 to 248, one end on the ADC-main strap at the star side, the other end = vdd_dac.
- **Decap unit**: cap_nmos_03v3 20 x 20 um (pcell `cap_nmos`, footprint 22.16 x 22.41 um, 1.593 pF at 3.3 V; gate = the rail, source / drain / bulk = vss; about 270 ohm of channel resistance per
  unit, ESTIMATE, i.e. 3-4 ohm per bank). One P+ tap column per two units.
- **Where** (no area of its own, nothing under the amplifier):
  1. one row of 34 units under the straps in EACH strap corridor (x = 26 + 24 j, j = 0 .. 33): 32 on vdd_dac (the DAC-strap bank sits right at the drivers), 2 at the west end on VDD;
  2. 38 units in a column in the west ring (x = 4, y = 44 + 24 j) on VDD, next to the star point and the macro's west end; the pin wires pass over them on Metal3;
  3. 4 units (2 x 2, 26 um pitch) under the Cref plate of every ADC on VDD (the Cref bottom plate is vss: it shields its top plate; the units sit next to each comparator).
  The LVS reference must have the drawn counts: `python3 AFE/layout/scripts/mk_lvs_netlists.py --decap 20,20 --decap-n 74,64 --rstrap rm3,2,222.2 --dig-netlist <powered afe_dig netlist>`.
  Limits: ADC-main >= 115 pF, ADC-DAC >= 95 pF (ACCEPT.md; X2 what-if: 0.125 -> 0.25 nF on the main rail changes the error from 0.48 to 0.49 LSB, the item is inductance, not capacitance).
- **Reserve = the lever of Decision 46c**: up to 16 more units per channel under the four Cin pieces (top-level overlap, a Metal3 shield on vss between the units and the bottom plates, on the
  ADC-main strap through the spur corridor). Proven on test cell lp_cin_decap (check_env.sh C2 / C4): DRC 0, LVS match with 1 MIM + 4 cap_nmos_03v3 on the right nets; after the MIM correction of
  `flow.py pex` the summing-node top plate sees 10.7 fF to the shield, the bottom plate 322 fF. Use it only through ACCEPT.md ladder S (supply error) or A (area).
- vss: one net; a vss strap under / beside every VDD strap; every cell ties its substrate to vss locally.

## 5. Top-level routing resources and keep-outs

| zone | Metal1 | Metal2 | Metal3 | Metal4 | Metal5 |
|---|---|---|---|---|---|
| pin ring (26 um), outline inward: 0-2 pin shapes, 2-12 digital lane, 12-14 vss stack, 14-26 analog lane (R2: lanes narrowed by 4 um, the analog lane is 12 um) | decap (west) | digital lane | digital lane | analog lane, VSS trunk | analog lane, VDD trunk |
| bias corridor (12 um) | - | 7 lines vbn vcm vg1 vcmo vg2 vrs REF, 0.4 um wide, each between two vss lines (0.75 um pitch, R2: 15 lines x 0.9 um no longer fit in 12 um; 0.35 um space is above the Metal2 minimum) | vss plate (shield + analog vss strap) | analog vdd strap | E / IPG crossings (N-S only) |
| strap corridor (25 um) | decap row | macro-to-ADC control wires (N-S), sw_* fan-in | rm3 (north), rst_amp trunk, jogs | vss strap | VDD(main) 8 um, vdd_dac 5 um |
| control corridor (8 um) / spur corridor (7 um) | - | 5 control lines + vss / - | - / vss | - / analog vdd | - |

Keep-outs (floorplan.json `rules`; L3a reports the smallest distances it achieved):
1. No SCLK, CS, DIN, DOUT, cmp_clk, dac_gp / dac_gn, dac_gdn, rst_sw, tg_on wire and no part of afe_dig within **20 um** of a summing node (vn, vp, vn2), a pseudo-resistor node, `rec`,
   the Cref node `vref` or a DAC top plate (`t`, `m`). Exceptions: the last 10 um of a control net at the device it drives; the quasi-static nets sw_rec, sw_rec_b, sw_ipg, sw_ipg_b, rst_amp, fs.
2. ADC supply straps (VDD main, vdd_dac) stay >= 5 um from those nodes and never cross over them (they carry tens of mV, not logic swings).
3. Nothing of the top level crosses amp_ch or adc_ch (their Metal4 / Metal5 are MIM plates).
4. MIM: no Via3 on a bottom plate (MIMTM.10); at most 10,000 um2 of MIM on one Metal4 polygon (MIMTM.11): `REF` and `rec` leave the Cin plates through Via4 / Metal5; the REF line of the bias
   corridor is Metal2.
5. vcm_in / vcm_out / vg / vrs daisy chain: one line per tap in the bias corridor, from bias_genc (east) along the east ring to both corridors, passing channels 3, 2, 1, 0 and 7, 6, 5, 4; a
   stub of at most 20 um into each amp_ch. No per-channel decoupling capacitor (X2 S5: conversion-induced crosstalk 0.002 LSB; tb_top_xtalk.py re-checks it; ACCEPT.md ladder X if it fails).
6. Guard rings: P+ (vss) around the analog NMOS of every amp_ch (L2a), around bias_genc and around each adc_ch driver row; P+ and N-well ring around afe_dig; no deep n-well by default
   (PLAN.md section 5), except the follower of the native-Vt fallback.

## 6. Drawn MIM and resistor sizes (5 nm grid; the LVS references carry the unrounded values, netgen tolerance 1 %)

| capacitor | reference um | draw um | top plate (terminal 1) | bottom plate |
|---|---|---|---|---|
| Cin1 / Cin2 pieces (4) | 70.649028 | 70.65 | vn / vp | rec / ref |
| stage-2 Cin | 38.588264 | 38.59 | vn2 | v1 |
| Cc2 | 31.463538 | 31.465 | o2 | vss |
| Cc1 | 22 | 22.0 | o1 | v1 |
| Cf2 | 11.917642 | 11.92 | vn2 | out |
| Cf1 (2) | 9.788457 | 9.79 | vn / vp | v1 / vcm |
| C_T (one-shot) | 44.594726 | 44.595 | t | vss |
| C_VRS (bias) | 49.886545 | 49.885 | vrs | vss |
| DAC units (127) | 5 | 5.0 | t or m | b0 .. b11, bd |
| bridge | 5.082993 x 5 | 5.085 x 5.0 | t | m |
| comparator preamp (2) | 5 | 5.0 | a1 / a2 | vss |
| vhalf decap | 22.178574 | 22.18 | vcmd | vss |
| Cref | 59.070243 | 59.07 | vref | vss |

Poly resistors ppolyf_u_1k (the only high-resistance poly of gf180mcuD, Decision 44a): bias ladders 1 um wide, 725 / 100 / 825 and 375 / 450 / 825 um; Rb 2 um x 120 um; vhalf 2 x 250 um x 1 um.
netgen adds series segments of equal width (`series {r_length add}`), so a serpentine of segments matches one long resistor.

## 7. Facts every phase needs (evidence: AFE/layout/sim/check_env_ref.log, AFE/NOTES.md "LP findings")

1. `bash AFE/layout/scripts/kl.sh <generator.py>` gives the PDK pcells in batch mode (it sets USER). `kpdk.py` has the helpers and the rule notes.
2. Magic terminal 1 of cap_mim_2f0_m4m5_noshield = top plate; netgen does not swap MIM terminals.
3. The PDK pcell `metal_resistor` does not extract in Magic; `kpdk.metal_res` does.
4. **PEX only with `python3 AFE/layout/scripts/flow.py pex`**: it corrects Magic's attachment of the capacitor-to-below capacitance to the MIM top plate. A raw `ext2spice` netlist shows a false
   parasitic of about 60 aF/um2 on every node that sits on a MIM top plate (summing nodes, DAC plate, bridge node, Cref node).
5. Post-layout numbers only with the scripts of `AFE/layout/tb/` and `compare.py`; their baselines are `AFE/layout/baseline/`. Amplifier checks run in the DESIGN convention by default (no junction
   area on the pseudo-resistor transistors) and, with `--junction`, as extracted (ACCEPT.md section 2).
6. Scratch: `AFE/layout/.ptmp` (or `$AFE_SCRATCH`); heavy jobs go through the job slots automatically (flow.py, lptb.py) or by `bash AFE/layout/scripts/slot.sh <command>`.
