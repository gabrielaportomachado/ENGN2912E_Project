# L1d report (2026-11-20; Claude Sonnet 5.5 / high)

## 1. Summary and verdict
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

## 5. Gate output
```
gate.py L1d  (L1d)
--- common
PASS  ACCEPT.md limits table equals AFE/layout/accept_limits.json
PASS  AFE/layout/REVIEW.md not edited by this phase
PASS  protected files (limits, ACCEPT.md, design netlists, RTL) unchanged since the last REVIEW.md commit 5f5e1fa
INFO  no open REVIEW.md item for L1d or an earlier phase
PASS  phase report AFE/layout/reports/L1d.md with all 10 sections
PASS  "## L1d findings" section in AFE/NOTES.md
PASS  Results-log row for L1d in AFE/NOTES.md
PASS  L2a findings of AFE/layout/NOTES_L2.md are merged into AFE/NOTES.md
PASS  L2a report AFE/layout/reports/L2a.md (converted from NOTES_L2.md) with all 10 sections
--- afe_dig
PASS  AFE/dig/final/ has afe_dig.gds, afe_dig.pnl.v, afe_dig.lef, afe_dig_pins.json
PASS  AFE/dig/reports/flow_summary.rpt VERDICT all PASS
PASS  die 819.84 x 109.76 um <= the slot 820 x 110 um
PASS  KLayout DRC variant D of afe_dig PASS on the GDS in AFE/dig/final (1948280 bytes in the log, 1948280 committed)
PASS  (a) DAC edge -> comparator clock of ADC 0 at ff_n40: 22.14 ns >= 21.0
PASS  (c) last window end -> next SCLK edge at the flop clock pins, ss_125: 22.39 ns >= 20.0 (against the pin: 20.59 ns, reported)
PASS  captured decision -> code register slack at 3 MHz, ss_125: 13.75 ns >= 10
PASS  sw_rec / sw_ipg pair skew at the macro pins <= 3 ns: worst 0.775 ns
PASS  gate-level testbench on the hardened netlist: only accepted assertion failures
PASS  run_top_sim.sh dig: EQUIV PASS (afe_dig equals the two RTL instances + ties)
PASS  check_lvs_netlists.py SUMMARY A, B, C PASS
PASS  the LVS top was written from AFE/dig/final/afe_dig.pnl.v (header of AFE/layout/lvs/dbs_afe_top.spice)
PASS  floorplan.py check --dig-pins /foss/designs/ENGN2912E_Project/.claude/worktrees/l1d-dig/AFE/dig/final/afe_dig_pins.json: floorplan.py check: 18 PASS, 0 FAIL
GATE L1d: PASS  (0 FAIL)
```

## 6. Ladder decisions
None. C-1 (CTS) not tried by design (Decision 44h); C-2 (tap limits) met on the first run; C-3 (die > 820 x 110 / routing) not needed; C-4 (other failing assertion) not triggered.

## 7. Deviations
None from the prompt, SPEC.md or floorplan.json. Notes: the utilisation is 43.0 % (flow, 1706 cells in the 806 x 102 um core) against the 37 % that floorplan.py estimates before hardening, both inside the 30-60 % band; the directory AFE/dig/trial/ keeps its name as the prompt says (it now holds the final run's files, run_dir.txt points to /tmp/lp_dig/design/runs/final).

## 8. Open issues and risks
1. The run directory lives in /tmp/lp_dig (scratch, not in git); the frozen GDS / netlist / LEF / pin table are in AFE/dig/final/. Regenerate with `bash AFE/dig/run_dig.sh final`.
2. Window (b) against the SCLK pin at ss 125 is 20.59 ns (limit 20.0): only 0.59 ns of margin at the worst SPEF; the physical margin (c) at the flop pins is 22.39 ns. Insertion-delay changes by L3a (e.g. a different SCLK pin load) are not modelled.
3. The macro has no pad ring / top-level wiring yet: the STA uses the SDC loads. The 3 MHz SCLK path through the pad and the top-level SCLK wire is L3a / L3b territory.
4. Digital charge 33.7 pC per cycle (ff -40: 38.4 pC) is about 3x the X2 S4 assumption of 12 pC; L3b must use these numbers (power_dig.log). It is drawn from the ADC-main strap.
5. Only the accepted gate-level assertion failures remain (X1.contention, X5.word0, X5.after33d, T11.crowbar, and T2.settle at the mixed corner); they are the set listed in the F1 / LP findings of AFE/NOTES.md and unchanged from the trial.

## 9. REVIEW.md items handled
None: AFE/layout/REVIEW.md contains "(none yet)"; `git pull` brought nothing new.

## 10. Files changed and commit
New: AFE/dig/final/{afe_dig.gds, afe_dig.pnl.v, afe_dig.lef, afe_dig_pins.json}, AFE/layout/reports/L1d.md, AFE/layout/sim/gate_L1d.log.
Changed (regenerated by the final run / checks): AFE/dig/reports/{flow_summary.rpt, klayout_drc.log, sta_audit_dig.log}, AFE/dig/trial/run_dir.txt, AFE/dig/sim/tb_audit_dig_*.log (36 runs; content equal to the trial's except the path line), AFE/layout/lvs/{dbs_afe_top.spice (header only), mk_lvs_netlists.log, check_lvs_netlists.log, check_x2_adc_lvs.log}, AFE/NOTES.md ("L1d findings" before "## Open questions" + one Results-log row).
Not touched: rtl/, AFE/adc/rtl/, AFE/dig/afe_dig.v, AFE/layout/REVIEW.md.
Commit: f0fe660 on branch worktree-l1d-dig (rebased onto origin/main b6f6987; pushed to origin/worktree-l1d-dig; main untouched). Gate re-run after the rebase: GATE L1d: PASS (0 FAIL).
