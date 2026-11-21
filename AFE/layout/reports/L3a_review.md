# L3a review notes (2026-11-21; monitoring session, Claude Opus 5.5): what was built, what to watch, and the REC buffer options

Companion to AFE/layout/reports/L3a.md (the phase report, gate PASS). Written at the user's request after the L3a merge (main 136e489). Every number comes from L3a.md, AFE/layout/top/check_top.log,
AFE/layout/reports/R13.md or floorplan.json; "ESTIMATE" marks what nobody simulated. Headings are lettered on purpose (gate.py parses the numbered sections of reports/*.md).

## A. Verdict
First complete chip layout: `AFE/layout/top/dbs_afe_top.gds`, 605.000 x 1110.000 um (the outline), 4 x afe_ch (adc_ch + amp_ch + 2 TGATE with filltie), afe_dig 424.48 x 86.24 um, bias_genc 107.25 x 115.10 um (slot 108 x 116.24),
strap corridors with the rm3 strap resistor, the pin ring with the 37 pin bits of the 20 pads, 104 decap units.
| check | result | source |
|---|---|---|
| full-chip DRC, deck variant D, antenna ON | 0 violations (90 s, 655 MB) | AFE/layout/sim/flow/dbs_afe_top.drc.json |
| full-chip LVS vs AFE/layout/lvs/dbs_afe_top.spice | Circuits match uniquely (39 s) | dbs_afe_top.lvs.json |
| bias_genc DRC / LVS | 0 / match | bias_genc.{drc,lvs}.json |
| routing TGATE + tap, PEX: Ron max typ / ff 85 / ss -40 | 21.0 / 15.6 / 34.2 kOhm (limit <= 133); off leakage 0.010 / 0.011 / 0.008 pA (limit <= 1) | AFE/layout/sim/post/tgate.json |
| keep-outs (rule >= 20 um unless stated) | macro -> any MIM top plate 61.0; ADC control wires -> MIM top plate 36.0; ADC straps -> MIM top plate 39.7 (rule 5); pad wires -> digital 448; bias_genc -> macro 21.0 | check_top.log |
| sw_rec / sw_rec_b length difference per channel | 8.6 um (limit 100); computed from drawn constants, not extracted | check_top.log |
| gates L2a, L1a, L1d, L2b, L1b, L3a after the merge | all PASS; floorplan check 20 PASS, 0 FAIL | gate logs |
| static power, 4 channels | 306 uA = 1.01 mW typ (ESTIMATE; the N = 8 total was 2.003 mW) | L3a.md section 8 item 5 |

## B. A finished cell changed: amp_ch (antenna fix)
The antenna rule had never been run on a cell before L3a. `flow.py drc --antenna` found ONE violation per amp_ch (ANT.16 / ANT.3: Metal2 perimeter 85.3 um on a 0.11 um2 gate, ratio 775 > 400), the gate of pseudo-resistor 3 (net gm2) reaching a 158 um Metal2 cluster
through one via. Fix (ACCEPT.md ladder D-5): the gate leaves on Metal3 (`gup` knob of amplib.pr_block, only pr3). Evidence: amp_ch.gds is NEW but the same 220.75 x 273.25 um, DRC (with antenna) 0, LVS match, `under_cin_clean` true; the full L2b post-layout set was re-run on the
new PEX: compare L2b 90 PASS, 0 WARN, 0 FAIL, gates L2a / L2b PASS (the L2b result files were overwritten, the old ones are in git). Cost: wire gm2 213 -> 245 um, `t` 156 -> 163 um, and the clearance of the stage-2 summing node vn2 to the nearest other net 2.5 -> 1.5 um
(2 nodes closer than 2 um; the stage-1 nodes vn / vp already had 0.5 / 1.5 um since L2a). L1b is unaffected (adc_ch not changed). L3b should look at the vn2 neighbourhood in the top PEX.

## C. Decap: the counts match, the nets do not (the main open point)
LVS sees ONE net VDD (analog strap and ADC-main strap are the same net, Decision 44d), so the gate (74 + 30 units) passes. Physically they are separate straps joined at the pad star point, and the units were placed as follows (L3a.md section 7 item 2):
| rail | planned (Decisions 44d / 52e) | drawn | where |
|---|---|---|---|
| ADC-main strap (comparators + macro) | 74 units = 117.9 pF | **42 units = 66.9 pF** | west bank 38 + 2 at the east end of each strap corridor |
| analog strap (VDD) | none required (AUDIT 4.9.2) | 32 units = 51.0 pF | 4 under each Cref (16) + 16 in the two spare regions east of the channels |
| ADC-DAC strap (vdd_dac) | 30 units = 47.8 pF | 30 units = 47.8 pF | 15 per strap corridor |
Why: the comparator supply pad is 40 um behind the comparator, so the Cref units went on the analog spur; the 16 units meant for "under the Cin pieces" were NOT drawn there (Metal1-3 over amp_ch would cross the cell, SPEC.md 5 item 3), they sit in the spare regions on the analog trunk.
Consequence: the supply-noise numbers of the baselines (top_supply: plate residue 0.559 LSB at ff -40 C, soft 0.5, hard 0.8; typ 0.174) assumed 117.9 pF on the ADC-main strap; with 66.9 pF it can be worse. The L3b supply run must use the as-drawn split (supply_model.json from the top PEX), not the LVS count.
If it fails (options, top-level changes only, cells unchanged): (1) connect the 16 spare-region units (503 .. 577 um) to the ADC-main strap instead of the analog trunk, which needs the ADC-main Metal5 strap extended east from the corridor ends (about 40 um); (2) add units in the spare regions (79 x 448.88 um each = about 35,000 um2 per region, floorplan.json zones spare_ne / spare_se; a unit needs about 22.2 x 22.4 um = 497 um2, so about 100 more units fit in the two regions, ESTIMATE from the free area, wiring not counted);
(3) more units under Cref. The decap total (104 units) is already in the LVS reference: changing the number needs `mk_lvs_netlists.py --decap-n` and a new LVS.

## D. The amplifier output wire is unshielded
amp_out (amp_ch.out -> adc_ch.vin) is a **200 um Metal3 wire** without vss shield lines; SPEC.md 3.1 asked for < 20 um with shields, impossible here because the two pins are 144 um apart in x. It runs in the 52 um band between adc_ch and amp_ch, more than 25 um from every other wire (L3a.md section 7 item 6). It carries the amplified signal the ADC samples, so L3b's crosstalk and noise checks should include it (the X2-style crosstalk bench in L3b simulates cells, not the top wiring: use the top PEX). Moving amp_ch down in its slot (section F) would shorten the vertical part.

## E. Other deviations (all in L3a.md section 7; none changes a result above)
TGATE zone 15 um instead of 8 um (amp_ch sits 15 um below the slot top; the slot has 63.6 um spare height: amp_ch 273.25 of 336.88 um); three Metal5 straps side by side (VSS 5.5, VDD-main 8, vdd_dac 5 um) instead of "VDD over vss"; no vss Metal3 plate in the bias corridors;
no P+ / N-well ring around the macro (it has its own taps; no analog device within 61 um); the TGATE + filltie are copied flat into one cell for correct bulk labels; DOUT_IN is a stub connected to nothing (the pad input is off); kit change `flow.py lvs --ref-verilog / --blackbox` (reads the macro Verilog named in the reference header).
Not done in L3a: full-chip PEX (L3b), metal density / fill (the organizer adds fill, ACCEPT.md section 5), the organizer's DEF (the floorplan.json default positions are used).

## F. REC buffers (question deferred by the user until a first layout exists; this is the layout evidence)
Background: Decision 53 put 4 analog REC pads on the amplifier input. R13 (AFE/layout/reports/R13.md): pad OPEN = harmless (87 / 87 limit rows PASS; pad adds 2.8 - 2.9 pF and <= 1.9 pA); a DC 10 MOhm / 10 pF scope probe breaks reset recovery (15 rows FAIL, ~164 nA drawn from rec); 1 GOhm probe PASSES; series resistors do not help.
**What the layout leaves (L3a.md section 8 item 4):** per channel three free strips about 38 um long (x 80 .. 117 um of the slot, between the REC riser at x 78.9 and the REC pad wire at x 118), 3.9 / 2.8 / 5.6 um high (z 0.5 .. 4.4, 5.6 .. 8.4, 9.4 .. 15 um above the amp_ch top); the Metal1 VDD / VSS rails of the TGATE row run between them;
only Metal3 tracks and the Metal5 REC horizontal cross them. The REC pad wire is 90 um of Metal5 (about 12 fF to its neighbours, ESTIMATE). The slot has 63.6 um of spare height: moving amp_ch 20 .. 40 um down opens up to the 57 um band (a top-level placement change; amp_ch.gds is unchanged).
| option | what it is | layout room | what it needs | covers | cost / risk |
|---|---|---|---|---|---|
| **1. Board buffer** | electrometer-grade follower (femtoamp-class input bias) on the PCB right at the REC pad, guard ring on the board | none | board rule + part choice; the chip keeps the open pad (R13: harmless) | any probe after the buffer; ordinary scopes work | PCB leakage / contamination at pA level must be controlled; nothing on the chip changes |
| **2. On-chip follower per channel** | source follower with its gate on rec, output to the pad wire, own current sink (about a few uA, ESTIMATE) from the bias line | the strips are too small for a cell of about 25 x 10 um (ESTIMATE); lower amp_ch by about 10 .. 25 um (top level only) | a new cell (schematic, sim with the R13 `--rec-load` infrastructure instead of the pad: gain, noise, f_lo, PSRR, power-up, park, the 87 rows), DRC / LVS, a new LVS reference, a new design netlist (protected-file change), top re-run (mk_top.py), then L3b | the pad never touches rec; works with any probe; the pad ESD / leakage sees the follower output | gate capacitance and leakage on rec (tens of fF and fA, ESTIMATE; a thick-oxide device keeps leakage lowest; the native-Vt variant reuses the amplifier's follower but depends on the unanswered organizer question, Decision 44k); lowering amp_ch lengthens the high-impedance E / rec wires by the same amount (about 0.13 fF per um, derived from 12 fF / 90 um, ESTIMATE) and shortens amp_out; amp_ch's own PEX does not contain the follower: an afe_ch-level extraction is needed |
| 3. REC_EN switch (see the saved note) | a TGATE between rec and the pad, closed only on request by a config bit | the strips fit a small TGATE (4.2 x 4.8 um + tap) | one config bit (the 80-SCLK word 0 has reserved bits [12:4]; a small RTL change and a macro re-harden), a control pin from the macro | the pad is isolated during normal recording | extra tap on rec; no help once enabled with a 10 MOhm probe |
Recommendation (monitoring session's view, not a decision): do option 1 regardless (zero chip risk; it is a board rule + part). Decide option 2 AFTER L3b: L3b may force other top-level edits (decap relocation of section C, the amp_out wire of section D), and the amp_ch shift that option 2 needs is also a top-level change, so one "top re-spin" can carry all three. Effort of option 2: ESTIMATE half a day to a day of agent time in about three sessions (cell + simulations, top re-spin, re-verification) plus review; L3a itself took about an hour and R13 about an hour and a half.

## G. What L3b has to check on the real layout
1. Full-chip PEX (flow.py pex on the top) and the supply run with the AS-DRAWN decap split (section C); plate residue at ff -40 C 3.6 V (0.559 LSB, soft 0.5, hard 0.8) and the DAC strap with its 5 um x 440 um Metal5 resistance.
2. Crosstalk and noise on amp_out (200 um Metal3, section D), the Metal2 control lines past the amp / adc cells, the bias lines (vcmo / vg2 / vrs coupling to neighbours; ladder X-1 if > 10 fF), the vn2 clearance of 1.5 um (section B).
3. The sw_rec / sw_rec_b skew from the extraction (8.6 um is a calculation), the REC wire coupling (about 12 fF, ESTIMATE), the 4-channel power-up (the 5 s bias wait is still the 8-channel number: README rule 2 / SPI_FRAME.md section 4).

## H. Open with the organizer (unchanged by L3a)
DEF and pin positions (the floorplan.json defaults are used; the pad wires leave at those positions), the 20-pad allotment (Decision 53), the native-Vt device (nfet_06v0_nvt in the follower; ladder N applies if refused), metal fill (theirs), the top cell name.
