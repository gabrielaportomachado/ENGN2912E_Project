# L3a report (2026-11-21; Claude Sonnet 5.5 / high; branch worktree-l3a)

Phase L3a: top assembly of dbs_afe_top (4 channels, 20 pads, 605 x 1110 um), full-chip DRC (with antenna) + LVS, TGATE with its tap as placed. Prompt: AFE/prompts/layout_run.md "L3a". Inputs read first: SPEC.md, floorplan.json, ACCEPT.md, FLOW.md, REVIEW.md (no open item), the cells amp_ch / adc_ch / afe_dig / TGATE, the LVS references.

## 1. Summary and verdict
dbs_afe_top.gds is 605.000 x 1110.000 um (the outline, PR boundary drawn): 4 x afe_ch (adc_ch + amp_ch + 2 TGATE with filltie + corridors), afe_dig, bias_genc, the strap corridors with the rm3 strap resistor, the pin ring with all 37 pin bits of the 20 pads, 74 decap units on VDD and 30 on vdd_dac. **Official `flow.py drc --antenna` (deck variant D): 0 violations (90 s, 655 MB). `flow.py lvs` against AFE/layout/lvs/dbs_afe_top.spice: "Circuits match uniquely." (39 s).** bias_genc (107.25 x 115.10 um, region 108 x 116.24) DRC 0 / LVS match. TGATE + tap PEX: Ron max 21.0 / 15.6 / 34.2 kOhm (typ / ff 85 / ss -40), off leakage 0.01 pA: compare L3a PASS (9 / 9).
Two things the next phases must know: (1) the antenna check (never run on the cells before L3a) found ONE violation per amp_ch (ANT.16 / ANT.3, the gate of pseudo-R 3); fixed in the amp_ch generator by ladder D-5 (the gate leaves on Metal3), amp_ch.gds is therefore NEW (same size, DRC 0, LVS match): see section 6 and the L2b re-run in section 8. (2) The top LVS needs the Verilog of the macro: `flow.py lvs` now reads `--dig-netlist` from the reference header by itself (kit change, section 7).
Verdict: gate L3a PASS (section 5).

## 2. What was built
| item | result | file |
|---|---|---|
| top | 605.000 x 1110.000 um, 6.37 MB GDS, sha1 edb9d93e468e495d65b427870c73d2952ec73098 | AFE/layout/top/dbs_afe_top.gds, generator mk_top.py (+ mk_afe_ch.py, toplib.py, mk_bias_genc.py, biaslib.py) |
| afe_ch (one channel slot, 237 x 448.88 um) | adc_ch at (8, 0), amp_ch at (8, 158.88) (its top 15 um below the slot top), TGATE rec_tg / ipg_tg (flattened TGATE.gds + one filltie abutted each, labels VDD VSS IN OUT C CBAR), control corridor (5 Metal2 lines 0.5 um, 1.4 um pitch + a vss line), spur corridor (vdd Metal4 3 um, vss Metal3 2.8 um), amp_out (Metal3, 200 um), Metal3 tracks for sw_rec / sw_rec_b / sw_ipg / sw_ipg_b, Metal5 pad wires E / REC / IPG; cell test: DRC 0, LVS vs subckt afe_ch match | mk_afe_ch.py |
| bias_genc | 107.25 x 115.10 um (12,344 um2; slot 108 x 116.24), ladders A / B 22 rows x 3 units of 25 um at 2.0 um pitch, C_VRS over ladder B, 8 pins Metal3 on the east edge; DRC 0, LVS match | mk_bias_genc.py (written by a sub-agent of this session, re-run and checked by me), biaslib.py, bias_genc.build.json |
| strap corridors N / S (25 um) | Metal5 straps VSS (5.5 um) / VDD-main (8 um) / vdd_dac (5 um) side by side, macro VDD / VSS stripes and the adc supply pads tied by Metal4 stubs + via4 boxes, 116 adc control wires Metal2 (macro pin -> adc pin, straight), 4 x 4 sw jogs Metal3, rst_amp trunk Metal3 (y_c 10.5), rm3 2 x 222.2 um (kpdk.metal_res) north only, vdd_dac N <-> S link at x 460 .. 465 | mk_top.py |
| west ring | 21 pad-control wires Metal3 straight to the macro, DOUT_IN stub (not connected inside), VDD pad Metal5 (x 0..21, y 602.12 .. 622.12), VSS pad Metal4 (y 487.88 .. 507.88), VDD-main trunk Metal5 x 3..11, analog VDD trunk Metal5 x 13..21, VSS trunk Metal4 x 12.5..20.5, rst_amp Metal2 at x 22.9, decap bank 38 units | mk_top.py |
| bias corridors N / S (12 um), east ring | 15 Metal2 lines per corridor (7 signals vbn vcm vg1 vcmo vg2 vrs REF between 8 vss lines, 0.4 um wide, 0.75 um pitch), analog vdd Metal4 strap u 0.3..8.8, stubs Metal3 from the 6 bias pins of each amp_ch, REF Metal5 stack at u 10.15, east ring: VDD Metal5 x 581..588, VSS Metal5 x 589.5..596.5, 7 Metal3 bias lines x 598.25 .. 604.25, REF pad stub at (605, 555) | mk_top.py |
| decap | 104 cap_nmos_03v3 units 20 x 20 um (pcell + a P+ tap strip each): see section 7 for where | mk_top.py |
| facts check | pins, keep-outs, skew, decap instances | check_top.py -> check_top.log, check_top.json |
| kit | `flow.py lvs --ref-verilog / --blackbox`, automatic when the reference header names `--dig-netlist` | AFE/layout/scripts/flow.py |
| amp_ch (changed) | gate of pr3 leaves on Metal3 (knob `gup`, default 1 in mk_amp_ch.py): 220.75 x 273.25 um as before, DRC (also antenna) 0, LVS match, under_cin_clean true | AFE/layout/amp/{mk_amp_ch.py, amplib.py, blocks_amp.py, amp_ch.gds, amp_ch.build.json} |

**Pin list (37 port bits of 20 pads; name (side, layer, x, y of the pin shape on the outline), all verified as labels by check_top.py)**: E[0] (N, M5, 96, 1110); IPG[0] (N, M5, 191, 1110); REC[0] (N, M5, 144, 1110); E[1] (N, M5, 333, 1110); IPG[1] (N, M5, 428, 1110); REC[1] (N, M5, 381, 1110); E[2] (S, M5, 96, 0); IPG[2] (S, M5, 191, 0); REC[2] (S, M5, 144, 0); E[3] (S, M5, 333, 0); IPG[3] (S, M5, 428, 0); REC[3] (S, M5, 381, 0); REF (E, M5, 605, 555); RSTN_PD (W, M3, 0, 514.88); RSTN_PU (W, M3, 0, 518.38); RSTN (W, M3, 0, 521.88); SCLK_PD (W, M3, 0, 525.38); SCLK_PU (W, M3, 0, 528.88); SCLK (W, M3, 0, 532.38); DIN_PD (W, M3, 0, 535.88); DIN_PU (W, M3, 0, 539.38); DIN (W, M3, 0, 542.88); CS_PD (W, M3, 0, 546.38); CS_PU (W, M3, 0, 549.88); CS (W, M3, 0, 553.38); DOUT_OUT (W, M3, 0, 556.88); DOUT_OE (W, M3, 0, 560.38); DOUT_IE (W, M3, 0, 563.88); DOUT_PD (W, M3, 0, 567.38); DOUT_PU (W, M3, 0, 570.88); DOUT_CS (W, M3, 0, 574.38); DOUT_SL (W, M3, 0, 577.88); DOUT_PDRV0 (W, M3, 0, 581.38); DOUT_PDRV1 (W, M3, 0, 584.88); DOUT_IN (W, M3, 0, 588.38); VDD (W, M5, 0, 612.12); VSS (W, M4, 0, 497.88).

Area: chip 671,550 um2; afe_dig 424.48 x 86.24; the 4 slots 4 x 106,385 um2; bias_genc 12,344 um2.

## 3. Commands run
```
bash AFE/layout/scripts/kl.sh AFE/layout/top/mk_bias_genc.py out=AFE/layout/top/bias_genc.gds        (sub-agent; I re-ran the two checks below)
python3 AFE/layout/scripts/flow.py drc --gds AFE/layout/top/bias_genc.gds --top bias_genc            -> 0
python3 AFE/layout/scripts/flow.py lvs --gds AFE/layout/top/bias_genc.gds --top bias_genc --ref AFE/layout/lvs/bias_genc.spice   -> match
bash AFE/layout/scripts/kl.sh AFE/layout/top/mk_afe_ch.py out=AFE/layout/top/afe_ch.gds             (cell test; 3 DRC rounds 16 -> 1 -> 0, LVS: 3 failures found and fixed: TGATE labels, vdd / vss short through amp_ch's vdd Metal3 wire, vcmo / vg2 / vrs short through amp_ch's Metal2 feeder at y 272)
python3 AFE/layout/scripts/flow.py lvs --gds AFE/layout/top/afe_ch.gds --top afe_ch --ref AFE/layout/lvs/dbs_afe_top.spice --refcell afe_ch
bash AFE/layout/scripts/kl.sh AFE/layout/top/mk_top.py out=AFE/layout/top/dbs_afe_top.gds > AFE/layout/top/mk_top.log
python3 AFE/layout/scripts/flow.py drc --gds AFE/layout/top/dbs_afe_top.gds --top dbs_afe_top --antenna     (first run 84 violations: ANT.16 x4, M2.2a x64, V3.2a x16 -> 0 after the fixes of section 6)
python3 AFE/layout/scripts/flow.py lvs --gds AFE/layout/top/dbs_afe_top.gds --top dbs_afe_top --ref AFE/layout/lvs/dbs_afe_top.spice
python3 AFE/layout/scripts/flow.py pex --gds AFE/layout/top/dbs_afe_top.gds --top TGATE                  (the TGATE + filltie cell is named TGATE in the top GDS)
python3 AFE/layout/tb/tb_tgate.py --netlist AFE/layout/sim/flow/TGATE.pex.spice --corner all
python3 AFE/layout/tb/compare.py --phase L3a
python3 AFE/layout/top/check_top.py > AFE/layout/top/check_top.log
amp_ch after the antenna fix: bash AFE/layout/scripts/kl.sh AFE/layout/amp/mk_amp_ch.py out=AFE/layout/amp gds=amp_ch.gds ; flow.py drc / lvs / pex of amp_ch ; check_amp.py ; the L2b testbench set of the L2b prompt (script in section 8)
python3 AFE/layout/scripts/gate.py L3a
```
Timing: mk_top 3.4 s, DRC top 90 s (655 MB), LVS top 39 s (507 MB), PEX of TGATE 1 s.

## 4. Results
| check | value | limit | PASS / WARN / FAIL | source |
|---|---|---|---|---|
| outline | 605.000 x 1110.000 um | <= 605 x 1110 | PASS | check_top.log, floorplan.py check |
| DRC top, variant D, antenna on | 0 violations | 0 | PASS | AFE/layout/sim/flow/dbs_afe_top.drc.json |
| LVS top (afe_dig from AFE/dig/final/afe_dig.pnl.v) | Circuits match uniquely | match | PASS | AFE/layout/sim/flow/dbs_afe_top.lvs.json |
| DRC / LVS bias_genc | 0 / match | 0 / match | PASS | AFE/layout/sim/flow/bias_genc.{drc,lvs}.json |
| DRC (antenna) / LVS amp_ch after the fix | 0 / match | 0 / match | PASS | AFE/layout/sim/flow/amp_ch.{drc,lvs}.json |
| decap in the LVS top | ADC-main 74 units = 117.9 pF, ADC-DAC 30 units = 47.8 pF | >= 115 / >= 47.5 pF | PASS | gate.py, floorplan.json params |
| decap pcell instances in the GDS | 104 | 74 + 30 | PASS | check_top.log |
| pin bits | 37 / 37 labels, each once, at the floorplan.json position | 37 | PASS | check_top.log |
| floorplan.py check with the as-built top and macro pins | 19 PASS, 0 FAIL | 0 FAIL | PASS | gate.py |
| TGATE + tap, PEX: ron_max (typ / ff 85 / ss -40) | 21.0 / 15.6 / 34.2 kOhm | <= 133 kOhm, within 0.9 .. 1.1 x baseline 21 / 16 / 34 | PASS | AFE/layout/sim/post/tgate.json |
| TGATE off leakage | 0.010 / 0.011 / 0.008 pA | <= 1 pA | PASS | same |
| compare.py --phase L3a | 9 PASS, 0 WARN, 0 FAIL | 0 FAIL | PASS | AFE/layout/sim/post/compare_L3a.md |
| keep-out: macro -> any MIM top plate (summing nodes, DAC / Cref plates; superset) | 61.0 um | >= 20 | PASS | check_top.log |
| keep-out: adc control wires of the top (Metal2) -> any MIM top plate | 36.0 um | >= 20 | PASS | same |
| keep-out: ADC supply straps -> any MIM top plate | 39.7 um | >= 5 | PASS | same |
| keep-out: E / REC / IPG pad wires -> digital side | 448 um | >= 20 | PASS | same |
| bias_genc -> macro | 21.0 um | >= 20 | PASS | same |
| sw_rec / sw_rec_b length (macro pin -> TGATE pin), ch 0 / 1 / 2 / 3 | 550.6 / 559.2, 550.4 / 559.0, 550.6 / 559.2, 550.4 / 559.0 um; difference 8.6 um | < 100 um | PASS | check_top.log (computed from the drawn constants) |
| static power, 4 channels | 306 uA = 1.01 mW typ (ESTIMATE, section 8) | AUDIT 4.6 N = 8: 606.8 uA = 2.003 mW | consistent | AUDIT 4.6, TAPEOUT.md |

## 5. Gate output
```
gate.py L3a  (L3a)
--- common
PASS  ACCEPT.md limits table equals AFE/layout/accept_limits.json
PASS  AFE/layout/REVIEW.md not edited by this phase
PASS  protected files (limits, ACCEPT.md, design netlists, RTL) unchanged since the last REVIEW.md commit cec9f71
INFO  no open REVIEW.md item for L3a or an earlier phase
PASS  phase report AFE/layout/reports/L3a.md with all 10 sections
PASS  "## L3a findings" section in AFE/NOTES.md
PASS  Results-log row for L3a in AFE/NOTES.md
PASS  L2a findings of AFE/layout/NOTES_L2.md are merged into AFE/NOTES.md
PASS  L2a report AFE/layout/reports/L2a.md (converted from NOTES_L2.md) with all 10 sections
--- dbs_afe_top layout: AFE/layout/top/dbs_afe_top.gds
PASS  DRC report belongs to the current GDS (sha1)
PASS  DRC ran with the official deck, variant D
PASS  DRC included the antenna rules
PASS  DRC dbs_afe_top: 0 violations
PASS  LVS report belongs to the current GDS (sha1)
PASS  LVS reference AFE/layout/lvs/dbs_afe_top.spice is a generated reference of AFE/layout/lvs or the phase's own AFE/layout/<cell dir>/lvs
PASS  LVS dbs_afe_top: Circuits match uniquely.
PASS  the reference was written by mk_lvs_netlists.py (header)
PASS  decap in the LVS top (= drawn, LVS matched): ADC-main 74 units = 117.9 pF >= 115, ADC-DAC 30 units = 47.8 pF >= 47.5 (floorplan.json params)
PASS  compare.py --phase L3a: PASS (9 PASS, 0 WARN, 0 FAIL, 0 missing)
PASS  post-layout results were simulated on extracted netlists
PASS  floorplan.py check --gds dbs_afe_top=/foss/designs/ENGN2912E_Project/.claude/worktrees/l3a/AFE/layout/top/dbs_afe_top.gds --dig-pins /foss/designs/ENGN2912E_Project/.claude/worktrees/l3a/AFE/dig/final/afe_dig_pins.json: floorplan.py check: 19 PASS, 0 FAIL
GATE L3a: PASS  (0 FAIL)
```

## 6. Ladder decisions
- **D-5 (antenna)**. Trigger: `flow.py drc --antenna` on the top: ANT.16_i_ANT.3 x 4 (one per amp_ch: Metal2 perimeter 85.3 um on a 0.11 um2 gate, ratio 775 > 400). The same violation exists in amp_ch alone (L2a never ran the antenna check): `flow.py drc --gds AFE/layout/amp/amp_ch.gds --top amp_ch --antenna` -> 1. Cause: gate of pseudo-resistor 3 (net gm2) reaches a 158 um Metal2 cluster through one via1. Fix (the entry says "jump to a higher metal near the gate"): amplib.pr_block(gup=True) draws via1 + a 0.5 x 0.5 um Metal2 pad + via2 + a Metal3 pad at the gate pad and the router starts the net on Metal3 (the Metal2 pad is an obstacle of its own net name, otherwise the router ran Metal2 from it); knob `gup`, default 1; only pr3 uses it. Evidence: amp_ch DRC (with antenna) 0, LVS match, same 220.75 x 273.25 um, `under_cin_clean` true, 34 nets routed, 0 failed. Cost: gm2 wire 213 -> 245 um, `t` 156 -> 163 um, and the clearance of the stage-2 summing node vn2 to the nearest other net went from 2.5 um (0 nodes closer than 2 um) to 1.5 um (2 nodes; the stage-1 nodes vn / vp already had 0.5 / 1.5 um since L2a). The L2b post-layout set was re-run on the new PEX (section 8).
- D-1 .. D-4 (M2.2a x 64: via pads of 0.6 / 0.7 um on the 0.75 um pitch bias lines -> 0.46 um; V3.2a x 16: my via3 next to bias_genc's own via3 at two pads -> the Metal4 feeder continues the cell's wire end): no ladder entry needed beyond "widen / move" (D-4).
- L-6 (netgen time-out): not needed, the top LVS takes 39 s.
- Macro in the LVS: no ladder entry; the hardened macro is compared as in the LibreLane netgen step (Verilog + PDK standard-cell SPICE, `-blackbox`), see section 7.

## 7. Deviations
1. **TGATE zone 15 um instead of 8 um**: amp_ch sits 15 um below the slot top (the slot has 63.6 um of spare height: amp_ch 273.25 of 336.88 um) so that the 4 control tracks, the E track and the Metal5 pad wires fit; the 52 um free band between adc_ch and amp_ch carries amp_out only. The bias pins of amp_ch are 17.8 um from the slot edge (+ up to 11 um of corridor line distance), SPEC 5 item 5 says a stub of at most 20 um.
2. **Decap placement** (counts as specified, 74 / 30): west bank 38 units on VDD (x = 4, y = 44 + 24 j, j = 0 .. 39 without 18 and 19 which would sit on the VSS pad; gates on the VDD-main Metal5 trunk, S/D on a Metal1 rail to the VSS Metal4 trunk); corridors: 15 units on vdd_dac (x = 26 + 24 j, j = 0 .. 14) and 2 on VDD (j = 15, 16: the EAST end, not the west end, because the control wires of channel 0 cross the west end) per corridor; **Cref: 4 units per ADC under the Cref plate, on the analog VDD spur (Metal2 rails to the spur Metal4), not on the ADC-main strap**: the comparator supply pad is 40 um away behind the comparator; **Cin: NOT drawn (16 units)**: leaving the Cin area on Metal1-3 would cross amp_ch (SPEC 5 item 3); the 16 units sit in the two spare regions east of the channels (x 503 .. 577, 8 + 8 units, gates on the analog VDD east trunk, S/D on the VSS east trunk). Consequence for L3b: the 32 Cref / spare units are on the analog net, the ADC-main net has 42 units (38 + 4) = 66.9 pF and the analog net 32 units (51 pF) in the layout; in the netlist both are one net VDD (LVS cannot tell), the supply run of L3b (tb_top_supply with supply_model.json) must use the as-drawn split.
3. **Straps**: VSS, VDD-main and vdd_dac are three Metal5 straps side by side (5.5 / 8 / 5 um), not "VDD over vss Metal4" (Metal4 carries the stubs and the 8 + 8 macro stripe stubs); the rm3 body is on Metal3 between them, leads via3 / via4.
4. **Bias corridors**: no Metal3 vss plate; the 8 vss Metal2 lines are tied at both ends and to the vss Metal3 spur of every channel; the analog vdd Metal4 strap covers u 0.3 .. 8.8 only (the REF stack at u 10.15 needs no hole); REF is Metal2 in the corridor and Metal3 in the east ring.
5. **No P+ / N-well ring around the macro** (SPEC 3.5 / 5 item 6): the hardened macro has its own tap and endcap cells; no analog device is within 61 um.
6. **amp_out** (amp_ch.out -> adc_ch.vin) is a 200 um Metal3 wire without vss shield lines (SPEC 3.1 asks < 20 um with shields: the two pins are 144 um apart in x); it runs through the free band, > 25 um from every other wire.
7. **bias_genc** (sub-agent report, verified): no P+ ring around the whole cell (107.25 of 108 um wide; each NMOS group has its own P+ ring, each pfet group its N-well ring); ra1 / ra2 (rb1 / rb2) are consecutive chain sections, only ra3 / rb3 are interleaved with them; resistor pitch 2.0 um with two merge fills the pcell does not draw (P+ between facing heads, resistor marker between rows); Rb = 2 rows of 60 um; mn2 5 fingers of 12.8 um; C_VRS (49.885 um) over ladder B.
8. **amp_ch changed** (D-5, section 6), a finished-phase artifact: the L2a gate and the L2b post-layout set are re-run (section 8).
9. **Kit change**: AFE/layout/scripts/flow.py `lvs` takes `--ref-verilog` and `--blackbox` and reads the macro Verilog from the `--dig-netlist` option in the header of the reference (the default call of the prompt works unchanged; the JSON report lists `ref_verilog`).
10. **TGATE wrapper**: the TGATE of TGATE/TGATE.gds and the filltie are copied flat into one cell named TGATE with the six labels (an instance of the library cells next to each other did not name the PMOS bulk).
11. DOUT_IN: a Metal3 stub at (0, 588.38) that is connected to nothing inside (the pad input buffer is off); rst_amp_o of the macro leaves on the west edge at the same y: its wire turns north / south at x = 22.9 on Metal2.
12. Pin shapes: the 20 pad wires are Metal5 2 um wide ending at the outline (E / REC / IPG), Metal3 0.56 um for the 21 pad-control pins, VDD pad Metal5 21 x 20 um, VSS pad Metal4 21 x 20 um (floorplan.json gives only the position and the 20 um width).

## 8. Open issues and risks
1. **L2b re-run after the amp_ch change: done.** The full L2b testbench set (design and junction conventions, all corners, reset with --os 10m,100m --host-rst 0.1) was re-run on the new amp_ch PEX: `compare.py --phase L2b` 90 PASS, 0 WARN, 0 FAIL (AFE/layout/sim/post/compare_L2b.md), `gate.py L2b` PASS, `gate.py L2a` PASS. The files AFE/layout/sim/post/amp_*.json were overwritten with the new numbers (the old ones are in git). L1b is unaffected (adc_ch not changed).
2. L3b must check: coupling of the Metal2 control lines past the amp / adc cells; the bias lines (coupling of vcmo / vg2 / vrs to neighbours from the top PEX, ladder X-1 if > 10 fF); the supply with the as-drawn decap split (section 7 item 2) and the strap resistance of the vdd_dac strap (Metal5 5 um, 440 um long); the vn2 clearance 1.5 um of amp_ch.
3. Not done in this phase: the full-chip PEX (L3b), metal density / fill (the organizer adds fill, ACCEPT.md section 5), the organizer DEF (positions are the floorplan.json defaults; the pad wires leave at the floorplan positions, none moved).
4. **REC pad / buffer question (REVIEW R13 / R16, not decided here)**: the layout leaves, per channel, three free strips of about 38 um length (x 80 .. 117, between the REC riser at x 78.9 and the REC pad wire at x 118) and 3.9 / 2.8 / 5.6 um height (z 0.5 .. 4.4, 5.6 .. 8.4, 9.4 .. 15 above the amp_ch top; the Metal1 VDD / VSS rails of the TGATE row run between them and could supply a small follower; only Metal3 tracks and the Metal5 REC horizontal cross them above Metal2) and, if the amp_ch is moved 20 .. 40 um down in its slot, up to the 57 um band between adc_ch and amp_ch; a follower on the rec node would sit within 40 um of the amplifier input, the rec wire to the pad is 90 um of Metal5 (about 12 fF to the neighbours, ESTIMATE). A board buffer needs no layout room. The REC pad itself: open pad harmless, 10 MOhm probe fails (R13).
5. ESTIMATE of the static power: 4 x 68.86 uA (amplifier) + 5.51 uA (bias) + 4 x 6.31 uA (vhalf) = 306 uA = 1.01 mW at 3.3 V typ (AUDIT 4.6 per-block numbers, the N = 8 total was 606.8 uA = 2.003 mW; TAPEOUT.md: record mode 1.05 mW with the dynamic terms). The ladders drawn equal the reference (LVS match within 1 %), so the 3.83 uA of the ladders is unchanged. The decap gate leakage (104 units, 41,600 um2) is not simulated here (ESTIMATE: far below 1 uA).
6. The sw_rec / sw_rec_b length difference of 8.6 um is a calculation from the drawn constants, not an extracted number (L3b PEX can confirm).
7. amp_ch Cref decap units are drawn inside the adc_ch footprint (under the Cref plate, Metal1 / Metal2 only); the gate rule "nothing below Metal4 inside the Cref footprint" belongs to adc_ch alone (L1a gate) and still passes.

## 9. REVIEW.md items handled
No open item for L3a or an earlier phase at the start (R1 .. R17 closed by the monitoring session on 2026-11-21; `gate.py` prints "no open REVIEW.md item"). R10 (host offset rule) and R13 (REC pad) are closed items: their numbers are used, nothing is changed here. Files that REVIEW protects were not touched (accept_limits.json, ACCEPT.md, RTL, design netlists).

## 10. Files changed and commit
New: AFE/layout/top/{mk_top.py, mk_afe_ch.py, toplib.py, mk_bias_genc.py, biaslib.py, dbs_afe_top.gds, bias_genc.gds, *.build.json, check_top.{py,log,json}, mk_*.log}, AFE/layout/reports/L3a.md, AFE/layout/sim/flow/{dbs_afe_top,bias_genc,TGATE}.*, AFE/layout/sim/post/{tgate,compare_L3a}.*. Changed: AFE/layout/amp/{mk_amp_ch.py, amplib.py, blocks_amp.py, amp_ch.gds, build / check files, flow reports}, AFE/layout/scripts/flow.py, AFE/layout/sim/flow/amp_ch.*, AFE/layout/sim/post/amp_*.json (L2b re-run), AFE/NOTES.md, AFE/layout/FLOW.md (section 10). Branch worktree-l3a; commit hash: see the next line (written by a second small commit).
Commit of the phase: e241753
