# L1d report (2026-11-20; Claude Sonnet 5.5 / high)

## 1. Summary and verdict
**R3 update (2026-11-20, REVIEW.md item R3): afe_dig re-hardened for the tightened floorplan. 80 um does NOT route; the smallest clean height is 101.92 um (die 819.84 x 101.92 um, 46.4 % utilisation).** Gate L1d: PASS (0 FAIL) on the R3 run. The R3 run follows the frozen recipe with only `--h` changed (`bash AFE/dig/run_dig.sh final --h 101.92`); the pins are the R2 floorplan.json pins (286 / 286 at the planned place). The floorplan was rebuilt with `floorplan.py build --set dig_h=101.92` (ACCEPT.md C-3): the channel slot becomes 237 x 386.04 um, **amp_ch <= 222 x 274.04 um (was 285; R4 must now fit this)**, adc_ch stays 222 x 104 um (R5 unchanged), bias_genc region 108 x 131.92 um; `floorplan.py check --dig-pins` 18 PASS, 0 FAIL. The text below describes the first (109.76 um) run unless it says R3; the R3 numbers are in section 4b.
Phase L1d (final hardening of the digital macro afe_dig) is a re-run of LP's recipe and reproduces the LP trial exactly (the flow is deterministic). **Gate L1d: PASS (0 FAIL).** Die 819.84 x 109.76 um (limit 820 x 110), 43.0 % utilisation, 167 flops, clock = no CTS + one clock buffer (Decision 44h). STA met at all 5 corners, 0 slew / cap violations, route / Magic DRC 0, LVS 0, KLayout DRC 0 on the committed GDS; tap limits (a) 22.14 ns, (c) 20.59 ns (22.39 ns at the flop pins), captured-decision slack 13.75 ns all PASS; gate-level test bench shows only the accepted assertion failures; EQUIV PASS; LVS reference netlists regenerated from the final netlist (A / B / C PASS); floorplan check 18 PASS, 0 FAIL. No ladder entry was needed. Next phases: L1b reads AFE/dig/reports/sta_taps.json, L3a places AFE/dig/final/afe_dig.{gds,lef,pnl.v,_pins.json}, L3b uses 33.7 pC per SCLK cycle (tt) / 38.4 pC (ff -40).

## 2. What was built
Nothing new was designed; LP's files were re-run unchanged (AFE/dig/afe_dig.v, mk_dig_cfg.py, run_dig.sh, scripts/; rtl/, AFE/adc/rtl/ and afe_dig.v not edited).
- Macro afe_dig: dbs_ctrl #(.N(8)) + adc8_top + `ck.u_ckbuf` (clkbuf_20) + 16 switch output pairs (clkinv_4 + clkbuf_8) + 15 pad-control ties + DOUT_OE driver; 286 signal pins (N 132 / S 132 on Metal2, W 22 on Metal3), VDD / VSS straps on Metal4. Die 819.84 x 109.76 um, core 806.40 x 101.92 um, 1706 std cells = 35,365 um2 (43.0 %).
- Frozen deliverables in AFE/dig/final/: afe_dig.gds (1,948,280 bytes), afe_dig.pnl.v (powered netlist), afe_dig.lef, afe_dig_pins.json.
- Regenerated reports in AFE/dig/reports/ (flow_summary.rpt, klayout_drc.log, sta_audit_dig.log, sta_taps.json, power_dig.log, metrics.json, sta/ ...), AFE/dig/trial/ (run_dir.txt etc.), AFE/dig/sim/ (tb_audit_dig_*.log, top_dig.log), AFE/layout/lvs/ (dbs_afe_top.spice header + the check logs).

## 3. Commands run
All from the repo root (worktree), in this order; none failed.
1. `git pull` (up to date), AFE/layout/REVIEW.md read: "(none yet)".
2. `(cd AFE/top && bash run_top_sim.sh dig)` -> EQUIV PASS.
3. `bash AFE/dig/run_dig.sh final` -> librelane exit 0, wall 0:53.8, VERDICT all PASS.
4. `bash AFE/dig/scripts/drc_dig.sh` -> PASS (0 violations).
5. `python3 AFE/review/scripts/sta_audit.py AFE/dig/reports/sta_audit_dig.log --dig /tmp/lp_dig/design/runs/final/final`
6. `python3 AFE/dig/scripts/sta_taps.py`
7. `python3 AFE/dig/scripts/power_dig.py`
8. `bash AFE/review/scripts/run_tb_audit.sh dig /tmp/lp_dig/design/runs/final/final`
9. `mkdir -p AFE/dig/final && cp /tmp/lp_dig/design/runs/final/final/gds/afe_dig.gds AFE/dig/trial/afe_dig.pnl.v AFE/dig/trial/afe_dig.lef AFE/dig/trial/afe_dig_pins.json AFE/dig/final/` ; `bash AFE/dig/scripts/drc_dig.sh AFE/dig/final/afe_dig.gds` -> PASS (0 violations)
10. `python3 AFE/layout/scripts/mk_lvs_netlists.py --decap-n 74,64 --dig-netlist AFE/dig/final/afe_dig.pnl.v` (the previous header had only these two options); `python3 AFE/layout/scripts/check_lvs_netlists.py` -> SUMMARY: A PASS, B PASS, C PASS
11. `python3 AFE/layout/scripts/floorplan.py check --dig-pins AFE/dig/final/afe_dig_pins.json` -> 18 PASS, 0 FAIL
12. `python3 AFE/layout/scripts/gate.py L1d`

## 4. Results
| check | value | limit | PASS / WARN / FAIL | source log |
|---|---|---|---|---|
| RTL equivalence (afe_dig vs reference top) | EQUIV PASS | PASS | PASS | AFE/dig/sim/top_dig.log |
| die W x H | 819.84 x 109.76 um | <= 820 x 110 | PASS | AFE/dig/reports/flow_summary.rpt |
| utilisation | 43.0 % (35,365 um2 / 1706 cells) | 30 .. 60 % | PASS | flow_summary.rpt |
| flow VERDICT | structure, timing / route / Magic DRC / LVS, slew / cap all PASS | all PASS | PASS | flow_summary.rpt |
| route DRC / antenna / Magic DRC / LVS / XOR | 0 / 0 / 0 / 0 / 0 | 0 | PASS | flow_summary.rpt |
| STA setup ws (ff-40 / ff125 / tt / ss-40 / ss125) | 96.965 / 96.046 / 95.361 / 93.778 / 91.689 ns | >= 0 | PASS | flow_summary.rpt |
| STA hold ws (same order) | 0.229 / 0.519 / 0.760 / 1.305 / 2.010 ns | >= 0 | PASS | flow_summary.rpt |
| max-slew / max-cap violations | 0 / 0 | 0 | PASS | flow_summary.rpt |
| KLayout DRC variant D on AFE/dig/final/afe_dig.gds | 0 violations (660 rules) | 0 | PASS | AFE/dig/reports/klayout_drc.log |
| tap (a) DAC edge -> comparator clock, ff -40 | 22.14 ns | >= 21.0 | PASS | AFE/dig/reports/sta_audit_dig.log (L1D_LIMITS) |
| tap (c) window end -> next SCLK edge, flop pins, ss 125 | 22.39 ns (pin: 20.59 ns) | >= 20.0 | PASS | sta_audit_dig.log |
| captured decision -> code register, 3 MHz, ss 125 | 13.75 ns | >= 10 | PASS | sta_audit_dig.log |
| switch-pair skew at the macro pins (worst) | 0.775 ns (ss 125, rec close) | <= 3 ns | PASS | sta_audit_dig.log section 7 |
| sampling skew between channels (worst) | 0.572 ns (ss 125) | info | PASS | sta_audit_dig.log |
| digital charge per SCLK cycle tt / ff-40 / ff125 / ss-40 / ss125 | 33.7 / 38.4 / 42.1 / 28.6 / 30.6 pC | info (X2 S4 assumed 12 pC) | PASS | AFE/dig/reports/power_dig.log |
| gate-level test bench (36 runs) | only X1.contention, X5.word0, X5.after33d, T11.crowbar, T2.settle (MIXED only) | accepted set | PASS | AFE/dig/sim/tb_audit_dig_summary.log |
| LVS reference netlists A / B / C | PASS / PASS / PASS (2493 cell instances in afe_dig) | PASS | PASS | AFE/layout/lvs/check_lvs_netlists.log |
| floorplan.py check --dig-pins | 18 PASS, 0 FAIL | 0 FAIL | PASS | stdout, section 5 |

### 4b. R3 re-harden results (die height search and final run at 101.92 um)
| check | value | limit | PASS / WARN / FAIL | source log |
|---|---|---|---|---|
| die height 80.00 (78.40 um = 20 rows) | GRT-0116 global-routing congestion, flow stops after 22 s | routes | FAIL | /tmp/lp_dig/librelane_r3_80.log (scratch, deleted) |
| die height 82.32 / 86.24 / 90.16 / 94.08 um | GRT-0116 at each (22-25 s) | routes | FAIL | same, tags r3_82.32 / r3_86.24 / r3_90.16 / r3_94.08 |
| die height 98.00 um | routes, STA / DRC / LVS clean, but `repair_antennas` (step 41) put ANTENNA_2 on the dont-touch net u_adc.ch[0].u.cap_clk: structure check FAIL | structure PASS | FAIL | tag r3_98.0 (collect_dig.py output) |
| die height 101.92 um (final) | structure PASS; timing / route / Magic DRC / LVS PASS; slew / cap PASS | all PASS | PASS | AFE/dig/reports/flow_summary.rpt |
| die / utilisation | 819.84 x 101.92 um, 46.4 % (35,167 um2, 1661 cells, 167 flops, 18 repair buffers) | <= 820 x slot, 30-60 % | PASS | flow_summary.rpt |
| route DRC / antenna / Magic DRC / LVS / XOR | 0 / 0 / 0 / 0 / 0 | 0 | PASS | flow_summary.rpt |
| STA setup ws (ff-40 / ff125 / tt / ss-40 / ss125) | 96.917 / 95.958 / 95.239 / 93.594 / 91.406 ns | >= 0 | PASS | flow_summary.rpt |
| STA hold ws (same order) | 0.245 / 0.553 / 0.803 / 1.356 / 2.137 ns | >= 0 | PASS | flow_summary.rpt |
| max-slew / max-cap violations | 0 / 0 | 0 | PASS | flow_summary.rpt |
| KLayout DRC variant D on AFE/dig/final/afe_dig.gds | 0 violations (660 rules) | 0 | PASS | AFE/dig/reports/klayout_drc.log |
| tap (a) DAC edge -> comparator clock, ff -40 | 21.99 ns | >= 21.0 | PASS | sta_audit_dig.log (L1D_LIMITS) |
| tap (b) window end -> next SCLK, SCLK pin, ss 125 | 20.23 ns | >= 20.0 | PASS (0.23 ns margin) | sta_audit_dig.log |
| tap (c) same, flop clock pins, ss 125 | 22.05 ns | >= 20.0 | PASS | sta_audit_dig.log |
| captured decision -> code register, 3 MHz, ss 125 | 13.69 ns | >= 10 | PASS | sta_audit_dig.log |
| switch-pair skew at the macro pins (worst) | 0.776 ns | <= 3 ns | PASS | gate_L1d.log |
| digital charge per SCLK cycle tt / ff-40 | 34.0 / 38.8 pC | info | PASS | AFE/dig/reports/power_dig.log |
| gate-level test bench (36 runs) | only the accepted assertion set (T2.settle / T11.crowbar MIXED, X1.contention, X5.word0, X5.after33d) | accepted set | PASS | AFE/dig/sim/tb_audit_dig_summary.log |
| EQUIV (afe_dig vs reference top) | EQUIV PASS | PASS | PASS | AFE/dig/sim/top_dig.log |
| LVS references A / B / C (regenerated from the new netlist) | PASS / PASS / PASS | PASS | PASS | AFE/layout/lvs/check_lvs_netlists.log |
| floorplan.py check --dig-pins (floorplan rebuilt with dig_h=101.92) | 18 PASS, 0 FAIL | 0 FAIL | PASS | stdout |

## 5. Gate output
```
gate.py L1d  (L1d)
--- common
PASS  ACCEPT.md limits table equals AFE/layout/accept_limits.json
PASS  AFE/layout/REVIEW.md not edited by this phase
PASS  protected files (limits, ACCEPT.md, design netlists, RTL) unchanged since the last REVIEW.md commit a611164
PASS  open REVIEW.md items for L1d or an earlier phase (R1 R3 R5) are listed as handled in section 9 of a phase report
PASS  phase report AFE/layout/reports/L1d.md with all 10 sections
PASS  "## L1d findings" section in AFE/NOTES.md
PASS  Results-log row for L1d in AFE/NOTES.md
PASS  L2a findings of AFE/layout/NOTES_L2.md are merged into AFE/NOTES.md
PASS  L2a report AFE/layout/reports/L2a.md (converted from NOTES_L2.md) with all 10 sections
--- afe_dig
PASS  AFE/dig/final/ has afe_dig.gds, afe_dig.pnl.v, afe_dig.lef, afe_dig_pins.json
PASS  AFE/dig/reports/flow_summary.rpt VERDICT all PASS
PASS  die 819.84 x 101.92 um <= the slot 820 x 110 um
PASS  KLayout DRC variant D of afe_dig PASS on the GDS in AFE/dig/final (1931994 bytes in the log, 1931994 committed)
PASS  (a) DAC edge -> comparator clock of ADC 0 at ff_n40: 21.99 ns >= 21.0
PASS  (c) last window end -> next SCLK edge at the flop clock pins, ss_125: 22.05 ns >= 20.0 (against the pin: 20.23 ns, reported)
PASS  captured decision -> code register slack at 3 MHz, ss_125: 13.69 ns >= 10
PASS  sw_rec / sw_ipg pair skew at the macro pins <= 3 ns: worst 0.776 ns
PASS  gate-level testbench on the hardened netlist: only accepted assertion failures
PASS  run_top_sim.sh dig: EQUIV PASS (afe_dig equals the two RTL instances + ties)
PASS  check_lvs_netlists.py SUMMARY A, B, C PASS
PASS  the LVS top was written from AFE/dig/final/afe_dig.pnl.v (header of AFE/layout/lvs/dbs_afe_top.spice)
PASS  floorplan.py check --dig-pins /foss/designs/ENGN2912E_Project/.claude/worktrees/r3-dig/AFE/dig/final/afe_dig_pins.json: floorplan.py check: 18 PASS, 0 FAIL
GATE L1d: PASS  (0 FAIL)
```

## 6. Ladder decisions
**R3 / C-3 (routing congestion of the macro; ACCEPT.md section 4):** the macro does not route at the R2 height 80 um (flow stops with GRT-0116 at 80.00, 82.32, 86.24, 90.16 and 94.08 um: the same failure, so the ladder applies instead of a third attempt), the die height was therefore raised by whole rows: 98.00 um routes but fails the structure check (antenna diode on the dont-touch comparator-clock net cap_clk of channel 0), 101.92 um is clean. The floorplan was rebuilt with `floorplan.py build --set dig_h=101.92`; the channel slots shrink by half of the 21.92 um each (237 x 397 -> 237 x 386.04). Cost: amp_ch budget 285 -> 274.04 um (margin over the estimate still +18 %, C-3 asks >= 8 %), adc_ch 104 unchanged, bias_genc region +21.92 um in y. Metal5 routing inside the macro (`--m5`, 94.08 um) was not tried: Metal5 is reserved for the top level (mk_dig_cfg.py). Not tried: RUN_ANTENNA_REPAIR off at 98.0 um (it changes the frozen recipe; 3.92 um gain).

Earlier (first L1d run): None. C-1 (CTS) not tried by design (Decision 44h); C-2 (tap limits) met on the first run; C-3 (die > 820 x 110 / routing) not needed; C-4 (other failing assertion) not triggered.

## 7. Deviations
R3: the die is 101.92 um high, not the 80 um of R2 / REVIEW R3 (and not 85 / 90 um): nothing below 98 um routes in this recipe. This is the change of floorplan.json / SPEC.md described in section 6 (dig_h 80 -> 101.92; amp_ch <= 222 x 274.04). `mk_dig_cfg.py --h` was used (kept below MIN_H on purpose for the search); no other file of the recipe was changed. Nothing in rtl/, AFE/adc/rtl/ or afe_dig.v was edited. First run: None from the prompt, SPEC.md or floorplan.json. Notes: the utilisation is 43.0 % (flow, 1706 cells in the 806 x 102 um core) against the 37 % that floorplan.py estimates before hardening, both inside the 30-60 % band; the directory AFE/dig/trial/ keeps its name as the prompt says (it now holds the final run's files, run_dir.txt points to /tmp/lp_dig/design/runs/final).

## 8. Open issues and risks
R3 additions:
- **R4 must fit amp_ch in 222 x 274.04 um** (was 285). If that cannot be met, 10 um may move from adc_h to amp_h (R2 allows +-10 um; adc_ch has +55 % margin on the estimate, but R5's target is 104). R5: adc_h unchanged at 104.
- Window (b) at the SCLK pin is 20.23 ns against 20.0 (0.23 ns margin; 20.59 ns in the 109.76 um run). Window (c) at the flop pins is 22.05 ns.
- The 98.00 um die would save 3.92 um but needs the antenna diode kept off the comparator-clock net (not tried).
- The 101.92 um macro leaves bias_genc a region of 108 x 131.92 um.
Earlier items (first run):
1. The run directory lives in /tmp/lp_dig (scratch, not in git); the frozen GDS / netlist / LEF / pin table are in AFE/dig/final/. Regenerate with `bash AFE/dig/run_dig.sh final`.
2. Window (b) against the SCLK pin at ss 125 is 20.59 ns (limit 20.0): only 0.59 ns of margin at the worst SPEF; the physical margin (c) at the flop pins is 22.39 ns. Insertion-delay changes by L3a (e.g. a different SCLK pin load) are not modelled.
3. The macro has no pad ring / top-level wiring yet: the STA uses the SDC loads. The 3 MHz SCLK path through the pad and the top-level SCLK wire is L3a / L3b territory.
4. Digital charge 33.7 pC per cycle (ff -40: 38.4 pC) is about 3x the X2 S4 assumption of 12 pC; L3b must use these numbers (power_dig.log). It is drawn from the ADC-main strap.
5. Only the accepted gate-level assertion failures remain (X1.contention, X5.word0, X5.after33d, T11.crowbar, and T2.settle at the mixed corner); they are the set listed in the F1 / LP findings of AFE/NOTES.md and unchanged from the trial.

## 9. REVIEW.md items handled
- **R1** (8-channel closure plan, order of work): read; R3 is the second step (floorplan R2 -> afe_dig R3 -> R4 -> R5). R3 hands the new amp_ch budget (274.04 um) to R4; no L2b / L1b / L3a run was started.
- **R3** (re-harden afe_dig at 820 x 80 um): done as far as the circuit allows: 80 um fails routing (GRT-0116, also at 82.3 / 86.2 / 90.2 / 94.1 um); the clean height is 101.92 um. All L1d checks re-run: STA at 5 corners, tap limits (a) 21.99 / (b) 20.23 / (c) 22.05 ns, slew / cap 0, KLayout DRC variant D 0, `run_tb_audit.sh dig` (only the accepted assertions), LVS references A / B / C, LVS top regenerated with --dig-netlist. The merge of worktree-l1d-dig into main was already done (c18ea08).

## 10. Files changed and commit
R3 changes: AFE/dig/{final/*, trial/{afe_dig.lef, afe_dig.pnl.v, afe_dig_pins.json}, config.json, afe_dig_template.def, pins_plan.json, reports/*, sim/tb_audit_dig_*.log}, AFE/layout/{floorplan.json (dig_h 101.92), SPEC.md, reports/L1d.md, sim/gate_L1d.log, lvs/check_*.log}, AFE/NOTES.md (L1d findings + Results-log row). Branch worktree-r3-dig; commit 4981e6b on branch worktree-r3-dig (pushed to origin/worktree-r3-dig; main untouched).

First-run files:
New: AFE/dig/final/{afe_dig.gds, afe_dig.pnl.v, afe_dig.lef, afe_dig_pins.json}, AFE/layout/reports/L1d.md, AFE/layout/sim/gate_L1d.log.
Changed (regenerated by the final run / checks): AFE/dig/reports/{flow_summary.rpt, klayout_drc.log, sta_audit_dig.log}, AFE/dig/trial/run_dir.txt, AFE/dig/sim/tb_audit_dig_*.log (36 runs; content equal to the trial's except the path line), AFE/layout/lvs/{dbs_afe_top.spice (header only), mk_lvs_netlists.log, check_lvs_netlists.log, check_x2_adc_lvs.log}, AFE/NOTES.md ("L1d findings" before "## Open questions" + one Results-log row).
Not touched: rtl/, AFE/adc/rtl/, AFE/dig/afe_dig.v, AFE/layout/REVIEW.md.
Commit: f0fe660 on branch worktree-l1d-dig (rebased onto origin/main b6f6987; pushed to origin/worktree-l1d-dig; main untouched). Gate re-run after the rebase: GATE L1d: PASS (0 FAIL).
