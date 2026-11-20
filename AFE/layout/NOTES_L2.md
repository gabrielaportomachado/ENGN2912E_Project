# NOTES_L2.md: findings and Results-log row of phase L2a (written here, not in AFE/NOTES.md, because another machine edits that file)

The first phase after L2a copies the "L2a findings" section and the Results-log row below into AFE/NOTES.md unchanged and converts them into AFE/layout/reports/L2a.md (common rule 7).
Flow notes: AFE/layout/FLOW.md. Everything lives in AFE/layout/amp/ (branch `worktree-l2a-amp`, one session, Claude Sonnet 5.5 / high, 2026-11-20).

## L2a findings

### Rework (A-3), 2026-11-20 (second pass, ACCEPT.md ladder A-3; user request; Sonnet 5.5 / high). Two steps: packing (commit f1472dd, 217.50 x 327.25 um) and tail-group merge (this commit, 218.75 x 309.25 um)
**Top lines**
- **gate.py L2a (`python3 AFE/layout/scripts/gate.py L2a --gds AFE/layout/amp/amp_ch.gds --run`, log `AFE/layout/amp/gate_L2a.log`): `GATE L2a: FAIL  (1 FAIL)`**: only `FAIL  5  as-built amp_ch 218.75 x 309.25 um fits its slot 220.00 x 263.00 um` (floorplan.py check 16 PASS, 1 FAIL); DRC 0, LVS match, findings and Results-log row PASS.
- **amp_ch still does NOT fit: 218.75 x 309.25 um = 67,648 um2 (first pass 219.25 x 385.25 = 84,466, -20 %; step 1 71,177) against the slot 220 x 263 = 57,860 (+17 %) and F1's 51,626 (+31 %).** DRC (official deck, variant D) **0 violations**, LVS **"Circuits match uniquely."** against `AFE/layout/lvs/afe_chc.spice` (default `--cin-top sum`, nothing regenerated; no W / L / m change, same device and pin counts).
  `check_amp.json`: `under_cin_clean: true` (nothing under the Cin plates).
- Native-Vt follower, MIM terminal order, LVS reference: unchanged from the first pass (below): `nfet_06v0_nvt` passes DRC + LVS, organizer silent (ladder N); terminal 1 = TOP plate; reference = default `mk_lvs_netlists.py`.
- **Packing alone cannot reach the slot: the sum of the blocks is 59,871 um2 (first pass 62,361), still above the slot area 57,860 at 100 % packing; the bbox has 11.5 % white space (first pass 26 %).** The slot this cell would need is about 220 x 310 um (+18 % in height).
  **8 channels: amp_ch alone 8 x 67,648 = 0.541 mm2 = 54 % of the 1000 x 1000 um outline (first pass 0.676 mm2). A channel is 309 + 104 + 8 = 421 um tall against 375 (+46 um per row): floorplan height about 1000 + 2 x 46 = 1,092 um (ESTIMATE, all other items unchanged).**
  Ladder A (ESTIMATE): A-2 (-14 um per row) and A-4 (-23 um, once) would take it to about 1,041 um: about 20 um per row are still missing. **The east-column rotation of mir was built and measured (`lay=4`, FLOW.md 7.2): 218.75 x 305.31 um, DRC 0 / LVS match, only -4 um (1.3 %) and a worse stage 2 (vn2 wire 290 um instead of 124, o2 479 instead of 337): NOT adopted, the committed GDS is `lay=3`.** A-6 / A-7 were NOT applied (instructions), `floorplan.json` not edited.

**What changed** (generator only: `AFE/layout/amp/mk_amp_ch.py` placement section `lay=3`, `amplib.py` ring-gap knobs and `dev_block(multi=True)`, `blocks_amp.py` tail merge; commands, knobs and limits found in FLOW.md section 7 / 7.1; GDS sha1 6a348da57ba1a40ff7098f5fda5d26f669120eda)
1. Step 1 (f1472dd): rows of 50 um devices under the Cin block, Cf1 strip 15 um, ONE column of stage-2 capacitors east of the Cin block (stage-2 nets short), ring gaps 2.5 / 2.5 / 3.0 -> 1.5 um, block gaps 2 -> 1.5 um, row gaps 3 -> 1 um, margin above the Cin lanes 8 -> 2 um: 217.50 x 327.25 um.
2. **Step 2, tail-group merge (asked for after step 1)**: xmb / xmt / xm7 (2 fingers 50u/4u each, common gate ibias1 and source vdd) drawn as ONE 6-finger pfet array with three drain strips (ibias1 / tail1 / v1) instead of three blocks: `ota_p` 150.6 -> 142.6 um wide (8,976 -> 8,499 um2), so the input pair and xm6 now share one row and the 24 um bottom row of step 1 is gone.
   Matching note: the three tail devices are now adjacent pairs of fingers in one diffusion row (same order mb, mt, m7 as before, shared source strips between them); not interleaved, as before.
   The new placement: bottom row = mirror xm3 / xm4 + a column (xms / fol / Cc1 / s2p with the `out` pin, sink1 above it); then the `ota_p` + xm6 row directly under the Cin block; the strip (24 um) holds OR2, pseudo-R 1, Cf1, the sp / sn gate-mux stack, Cf1', pseudo-R 2; the east column starts with s2tail, s2pair.
   vdd / vss pins moved to the east edge, Metal4 3 x 3 um at (W - 4, 14) and (W - 4, 30) (inner half, free of blocks); rec / ref (Metal5) and vbn vcm vg1 vcmo vg2 vrs (Metal3) on the top edge, sw_rec sw_rec_b rst_amp (Metal2) on the west edge within 60 um of the top, out (Metal3) at the bottom edge, as SPEC.md 3.2 (labels in `check_amp.json`). The Metal2 / Metal3 pins are still 0.5 um wide (L3a re-places them, ACCEPT.md G-5).
3. **A trap found and written down**: with the strip at 22 or 23 um DRC and LVS were clean but the ring of the sn block lay under the 0.6 um margin of the Cin bottom plates (`check_amp.py`: `under_cin_clean: false`). Decision 46c is not a rule of the deck, so DRC / LVS cannot see it; the strip is 24 um. FLOW.md 7.1: run check_amp.py after every repack.
4. Lever (1) of the prompt (25 um fingers) was NOT used: the area of a finger array does not shrink with finger width (ESTIMATE in FLOW.md section 7) and it would change the extracted `w` against the reference; not tried with netgen.

**Area (W x H = 218.75 x 309.25 um; `check_amp.json`, `amp_ch.build.json`)**
| block | first pass um2 | step 1 um2 | final um2 | F1 / PLAN estimate |
|---|---|---|---|---|
| Cin block incl. lanes and pad strip (164.7 x 167.3) | 27,554 | 27,554 | 27,554 (cannot shrink) | 2 x Cin drawn 20,005, footprint 21,036 |
| input pair + tail group `ota_p` (142.6 x 59.6) | 9,705 | 8,976 | 8,499 | 9,601 |
| xm3 / xm4 mirror + xm6 | 10,244 | 9,628 | 9,628 | 10,364 |
| stage 2, follower, sink arrays | 7,018 | 6,589 | 6,589 | 3,780 + stage 2 |
| MIM outside Cin (C_T, Cin2, Cc2, Cc1, Cf2, 2 x Cf1) | 6,416 | 6,416 | 6,416 | 5,912 |
| small devices (muxes, park, one-shot, OR2, 3 pseudo-R pairs) | 1,423 | 1,185 | 1,185 | x 2.5 on 350 |
| **sum of the blocks** | **62,361** | **60,348** | **59,871** | **51,626** |
| **cell bbox** | **84,466 (219.25 x 385.25)** | **71,177 (217.50 x 327.25)** | **67,648 (218.75 x 309.25)** | slot 57,860 |
Routed wire length of the sensitive nets (grid nodes x 1 um, ESTIMATE; first pass in brackets): vn 131 um (290), vp 157 (280), vn2 124 (550), **rec 21 (280)**, v1 401 (540), o1 320, o2 337, tail1 155. Achieved edge-to-edge clearance of the summing-node wires: vn 0.5 um minimum with **26 of 67 nodes closer than 2 um** (step 1: 4 of 65; first pass 2.5 um, 0 of 227; a larger halo 2.5 / 3.0 um did not change it),
vp 1.5 um (10 of 99), vn2 2.5 um (0 of 69), rec has no interior node (21 um of wire). The Metal1 vss guard around the summing-node connections is still NOT drawn: **the vn clearance is the first suspect for L2b** (ACCEPT.md R-2, R-3, R-6, R-8).
`AFE/layout/amp/pex_feasibility/` (PEX of the first-pass GDS) was NOT re-run: PEX is L2b's, on this GDS. The first-pass findings follow unchanged (their sizes and wire lengths are superseded by the numbers above; the plate order, rules and Step 1 results still hold).

### First pass (commit 1b3076a)

**Summary (top lines, as the prompt asks)**
- **Native-Vt follower `nfet_06v0_nvt` (10u / 2u): status UNCONFIRMED by the organizer (Decision 44k, ACCEPT.md ladder N applies if they refuse).** It passes the open-source decks: Step 1 test cell lp_flow: DRC 0, netgen match
  (`AFE/layout/amp/flowtest/flow/lp_flow.drc.json`, `.lvs.json`); in amp_ch it sits inside its own P+ ring (device `fol`, PDK pcell with its native / dual-gate markers) and DRC / LVS are clean with it. The layout keeps the native device.
- **MIM terminal order: terminal 1 of `cap_mim_2f0_m4m5_noshield` = TOP plate (Metal5 / FuseTop)**, same as F1 and check_env C3: extracted `X1 TOPNET BOTNET cap_mim_2f0_m4m5_noshield` (`AFE/layout/amp/flowtest/flow/lp_flow.pex.spice`),
  netgen matches TOPNET first and the full cell matches with vn / vp / vn2 on the top plates. No `--cin-top rec` needed.
- **LVS reference used: `AFE/layout/lvs/afe_chc.spice` subckt amp_ch, the default of `python3 AFE/layout/scripts/mk_lvs_netlists.py` (`--cin-top sum`), NOT regenerated** (the Cin pieces are drawn 70.65 um squares against 70.649028 in the
  reference, +0.0014 %, inside the 1 % tolerance); command of the run: `python3 AFE/layout/scripts/flow.py lvs --gds AFE/layout/amp/amp_ch.gds --top amp_ch --ref AFE/layout/lvs/afe_chc.spice --out AFE/layout/amp/flow`.
- **DRC (official gf180mcuD deck, `--variant=D`, `flow.py drc`): 0 violations. LVS: "Circuits match uniquely." (46 devices, 35 nets, 14 pins = the pins of AFE/layout/lvs/afe_chc.spice, no extra pin).** Logs: `AFE/layout/amp/flow/amp_ch.drc.json`, `amp_ch.lvs.json`, `amp_ch.lvs.out`.
- **Does NOT fit its slot: amp_ch as built is 219.25 x 385.25 um = 84,466 um2 against the slot 220 x 263 = 57,860 um2 (+46 %) and the F1 estimate 51,626 um2 (+64 %).** gate.py last line: see the end of this section ("gate.py L2a").
  ACCEPT.md ladder A (area) applies in the next phase; the numbers it needs are below.

**What was built** (all generated, nothing drawn by hand; `AFE/layout/amp/mk_amp_ch.py`, `amplib.py`, `blocks_amp.py`, `router.py`; GDS `AFE/layout/amp/amp_ch.gds`, sha1 b9407198f235d12f32265702ff358816556814b0, 3.0 MB)
- Cin: 2 x 2 checkerboard of four 70.65 x 70.65 um MIM pieces (4,991 um2 each, 5.5 um corridors), Cin1 (rec / vn) on the diagonal A1 / A2, Cin2 (ref / vp) on B1 / B2. **Plate order of Decision 46a: summing nodes vn / vp on the TOP plate
  (Metal5), rec / ref on the bottom plate (Metal4) of every piece**, also for stage 2 (vn2 on the top plate of Cin and Cf2) and for Cf1 / Cf1'. Wiring of the block: vn through the centre of the corridors on Metal5, rec as a 0.9 um Metal4 strap
  in the vertical corridor (A1 - A2) leaving south (router pad) and north (Metal5 pin), vp on an inner Metal5 lane around the east / north side, ref on Metal4 tabs + outer Metal5 lanes. **Nothing under the four plates but the MIM:
  no comp / poly / contact / Metal1-3 / via1-3 / well / implant inside the plate footprints (`AFE/layout/amp/check_amp.json`, `under_cin_clean: true`; Decision 46c reserve intact).** Cin : Cf1 = 99.972 (formula of the netlists, ESTIMATE;
  reference 100.0000): Cf1 / Cf1' (9.79 um) lie in a strip directly below the block next to the vn / vp descenders, same orientation.
- OTA 1: input pair 2 x (16 x 50u/2u) as ABBA, four units of 8 fingers each (A = vn, B = vp, drains d1 / o1 by Metal2 rails, common source tail), with the tail / mirror group (xmb, xmt, xm7: 3 units of 2 x 50u/4u, gate ibias1) in the SAME
  n-well and N+ ring (vdd); poly-only dummy lines at both ends of both groups. Loads xm3 / xm4 (50u/16u, 2 each) as ABBA of single-finger units with the P+ ring (vss) and dummies; xm6 (4 x 50u/16u) and the two sink arrays (24 and 6 fingers 16u/4u)
  in their own P+ rings. Stage 2: diff pair xm1 / xm2 (1u/40u as 4 units of 0.5u/40u, ABBA, stacked), tail 1u/20u, loads 1u/20u, follower nfet_06v0_nvt in a P+ ring. Park TGATE (nfet 1u/0.5u + pfet 2u/0.5u), the four gate-mux transistors,
  the one-shot (8 small transistors + 0.28u/40u + C_T 44.6 um) and the OR2 with a filltie abutted (n-well + tap): single-finger tiles in two rings (P+ / N+).
- **Pseudo-resistors: 6 x pfet_03v3 0.22u/0.5u, drawn identically (block `pr_block`), minimum junction area (one 0.22 x ~0.4 um diffusion pair), EACH with its own n-well tied to its source net (vn, v1, vp, vcm, vn2, out) by an N+ tie of 0.42 x 0.5 um**
  (SPEC.md 3.2 item 4; design convention of ACCEPT.md section 2 is the gate of L2b). Pairs `pr1` (vn / v1), `pr2` (vp / vcm), `pr3` (vn2 / out), wells 3.4 um apart.
- P+ guard rings (vss) around every NMOS block, N+ / n-well rings (vdd) around every PMOS block; every device has a tap in its ring (DF.13 / DF.14 clean).
- Pins (labels, `check_amp.json`): rec / ref Metal5 on the top edge; vbn vcm vg1 vcmo vg2 vrs Metal3 at the top-left corner (1 um pitch); sw_rec sw_rec_b rst_amp Metal2 on the west edge (within 60 um of the top); vdd vss Metal4 3 x 3 um at the
  top-right; out Metal3 on the bottom (inner) edge. A deviation from SPEC.md 3.2: the Metal2 / Metal3 pins are 0.5 um wide, the channel is wider than the slot (see below), so L3a re-places the pin wires anyway (ACCEPT.md G-5).

**Area, W x H** (`AFE/layout/amp/amp_ch.build.json`, `check_amp.json`; F1 numbers from AFE/review/sim/f1_area.log, which contain block factors 1.5 / 2.5)
| block | as built (bbox um2) | F1 / PLAN estimate |
|---|---|---|
| Cin block: 4 pieces + corridors + Metal5 lanes (164.7 x 167.3) | 27,554 | 2 x Cin drawn 20,005, footprint 21,036 |
| input pair + tail group `ota_p` (152.6 x 63.6) | 9,705 | (pfet 50/2 m32 4,877 + 50/4 m6 1,524) x 1.5 = 9,601 |
| xm3 / xm4 mirror + xm6 (96 x 62 + 74 x 58) | 10,244 | nfet 50/16 m8 6,909 x 1.5 = 10,364 |
| stage 2, follower, two sink arrays | 7,018 | nfet 16/4 m30 2,520 x 1.5 + stage-2 devices |
| MIM outside Cin (C_T, Cin2, Cc2, Cc1, Cf2, 2 x Cf1) | 6,416 | 5,912 |
| small devices (muxes, park, one-shot, OR2, 3 pseudo-R pairs) | 1,423 | x 2.5 on 285 + 65 |
| **sum of the blocks** | **62,361** | **afe_chc 49,312 + fs_oneshot_c 2,314 = 51,626** |
| **cell bbox 219.25 x 385.25** | **84,466** | slot 220 x 263 = 57,860 |
So every block is within +/- 5 % of F1's estimate except the Cin block (+31 %: the 5.5 um corridors, the Metal5 / Metal4 lanes and the pad strip are inside it), the sum of the blocks is +21 % and the remaining 22,100 um2 (26 %) is white space of the
row packing (4 rows of different heights, 3 um gaps, the landing-pad / ring overhead of every block is already inside the bbox). The same finger counts and widths were used for every device (no sizing change).
**8-channel extrapolation (ESTIMATE): 8 x 84,466 = 0.676 mm2 for amp_ch alone = 68 % of the 1000 x 1000 um outline (Decision 45); at the slot area 8 x 57,860 = 0.463 mm2.** With the ADC slots (8 x 22,880 = 0.183 mm2), afe_dig (0.090 mm2) and
bias_genc (0.014 mm2) the chip is about 0.96 mm2 BEFORE corridors, rings and the 30 um pin ring: it does not fit as built; a channel would be 385 + 104 + 8 = 497 um tall against the 375 um of floorplan.json, two rows 994 um + macro 110 um.
**Ladder A (next phase) with numbers: A-1 (rotate) does not help (the cell is 385 tall, 219 wide: rotated 385 x 219 breaks the 235 um channel pitch). A-3 is the way: the cell must lose 31 % of its area; the Cin block + MIM column (34,000 um2 = 59 % of
the slot) cannot shrink, so the devices + wiring (now 28,300 um2 of blocks + 22,100 um2 of white space) must fit in about 24,000 um2. Levers that are NOT used yet: (1) finger width 25 um instead of 50 um for xm3 / xm4 / xm6 / the pair (halves the
height of rows 3 and 4, 62 / 64 um -> about 35 um; the width of the rows doubles, the pair + tail must then go to two rows); (2) the gate landing pad (3 um) of each of the 11 array units and the rings (about 15 % of the device area); (3) the white space right of
row 4 (60 um) and above the short blocks of row 2; (4) the stage-2 MIM column next to the Cin block holds only 6,400 of 8,500 um2.**

**Rules from PLAN.md section 5 / SPEC.md 3.2** (what was done, what was not)
- Common-centroid pair + dummies: ABBA of four 8-finger units (each device 16 x 50u/2u), poly-only dummies (a shorted dummy transistor is NOT dropped by netgen: tested, FLOW.md section 4.3). Two-dimensional centroid (ABBA / BAAB rows) was not drawn.
- P+ guard ring on analog NMOS: yes, every NMOS block. Park switch and gate muxes: inside their own rings (small-device tiles).
- Summing node / pseudo-R / REC leakage: pseudo-resistors have minimum identical junction area and own wells; the long wires of vn / vp / vn2 / rec / the pseudo-R nodes carry a SOFT 2 um clearance (router cost); achieved edge-to-edge clearance to
  other nets on the same layer over the middle of the wire (ends excluded): vn 2.5 um minimum (0 of 227 nodes closer than 2 um), vp 1.5 um (10 of 218), vn2 0.5 um (22 of 493), rec 0.5 um (47 of 245); the pseudo-R S nodes are Metal1 links 2 um
  from the neighbouring pads of the same block. **The Metal1 vss guard around the summing-node connections was NOT drawn** (the router has no guard feature); wire lengths (ESTIMATE, grid nodes x 1 um): vn about 290 um, vp 280, **vn2 550 (the
  s2pair block is on the other side of the cell from the stage-2 capacitor column)**, rec 280, v1 540. These are the first suspects if L2b misses f_hi / noise / PSRR (ACCEPT.md R-2, R-3, R-6, R-8).
- Metal1-3 never run over Cin pieces; the vn / vp / rec connections to the Cin pieces are Metal5 / Metal4 only.
- Supply: vdd / vss are routed like signals (0.5 um wires, vdd about 560 um, vss about 860 um of wire in total, ESTIMATE): resistance of a long branch about 70 - 140 ohm. L2b should look at the IR drop (amp_ac idd / vout limits) and L3a replaces them
  by straps; the cell is on the analog strap only (no vdd_cmp / vdd_dac).

**Native-Vt / OR2 / other facts that matter later**
- The 7t5v0 OR2 (5 V devices, dual-gate marker) is in the channel with its own filltie; netgen matches pfet_05v0 / nfet_05v0 with VNW = vdd, VPW = vss.
- PEX is L2b's, but it runs: `flow.py pex` on the final GDS: 121 devices (the OR2 is flat: 3 + 3 5 V devices), 383 C (2,993 fF), 0 R (mode c), MIM correction moved 8.9 / 16.4 / 3.8 / 78.1 / 78.2 / 13.8 fF from top-plate nets to the bottom plates;
  the netlist loads in ngspice and gives a .op with guessed bias levels (`AFE/layout/amp/pex_feasibility/`, PORT ORDER of the PEX subckt: rec ref vbn vcm vg1 vcmo vg2 vrs out sw_rec sw_rec_b rst_amp vdd vss: connect by name).
- Findings that cost time and are written down in FLOW.md for L1a: the pcells' off-grid shapes (snapped copies in amplib), `Bulk Tie` unusable, dummy transistors are devices for netgen, MIM spacing rules measured with the deck, labels of library cells.
- Ladder entries used: D-1 (off-grid, snapped in the generator), L-1 (property error, fixed in the drawing: W of the stage-2 pair 2 u -> four 0.5u units, the 0.28u one-shot device via `con_bet_fin=0`), none of A (area FAIL is left for the next phase), none of G-3 (terminal order is as F1 assumed).

**gate.py L2a** (`python3 AFE/layout/scripts/gate.py L2a --gds AFE/layout/amp/amp_ch.gds --run`; copy of its last line, run on the final GDS): `GATE L2a: FAIL  (1 FAIL)`. The one FAIL is the slot: `FAIL  5  as-built amp_ch 219.25 x 385.25 um fits its slot 220.00 x 263.00 um` (floorplan.py check: 16 PASS, 1 FAIL); DRC 0 violations, LVS match, the findings section and the Results-log row PASS. Per the prompt this does not stop L2a: the next phase handles it with ACCEPT.md ladder A.

## Results-log row (for AFE/NOTES.md)
| Date | Phase | Model / effort | Cost (USD) | Result (with path to log) |
|------|-------|----------------|------------|---------------------------|
| 2026-11-20 | L2a amplifier layout amp_ch (DRC + LVS) | Claude Sonnet 5.5 / high | | amp_ch.gds: DRC variant D 0 violations, LVS "Circuits match uniquely." against AFE/layout/lvs/afe_chc.spice (46 devices, 14 pins, nothing regenerated); MIM terminal 1 = top plate (Step 1 test cell, flowtest); native-Vt follower passes DRC + LVS (organizer still silent, ladder N); Cin 2 x 2 checkerboard of four 70.65 um pieces, summing nodes on the top plates, nothing under the plates; input pair ABBA + poly dummies, rings, own wells for the 6 pseudo-resistors. NOT in the slot: 219.25 x 385.25 um = 84,466 um2 vs 57,860 (+46 %), blocks sum 62,361 vs F1 51,626: ladder A next (8 channels 0.68 mm2 of the 1.0 mm2 outline for amp_ch alone). Flow notes AFE/layout/FLOW.md; logs AFE/layout/amp/ (flow/, flowtest/, pex_feasibility/, check_amp.json, amp_ch.build.json) |
| 2026-11-20 | L2a rework (ladder A-3: new packing + tail-group merge of amp_ch) | Claude Sonnet 5.5 / high | | amp_ch.gds 218.75 x 309.25 um = 67,648 um2 (first pass 84,466, -20 %; step 1 71,177), still NOT in the slot 220 x 263 = 57,860 (+17 %); DRC variant D 0 violations, LVS "Circuits match uniquely." against AFE/layout/lvs/afe_chc.spice (unchanged reference, no device change), nothing under the Cin plates; gate.py L2a: FAIL (1 FAIL: the slot); sum of blocks 59,871 um2 is already above the slot area, white space 26 % -> 11.5 %; wires vn / vp / vn2 / rec 131 / 157 / 124 / 21 um (were 290 / 280 / 550 / 280) but vn has 26 of 67 nodes closer than 2 um to other nets; a channel would be 421 um tall (floorplan height about 1,092 um, ESTIMATE; about 1,041 um with A-2 + A-4); A-6 / A-7 not applied. Flow notes AFE/layout/FLOW.md sections 7 / 7.1; logs AFE/layout/amp/ (flow/, check_amp.json, amp_ch.build.json, gate_L2a.log) |
