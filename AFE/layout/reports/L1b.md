# L1b report (2026-11-21; Claude Sonnet 5.5 / default)

## 1. Summary and verdict
Verdict: **gate L1b FAIL; AFE/layout/BLOCKED.md written** (ACCEPT.md Q-2 above its pre-approval for the ff 85 step in compare.py terms, no ladder entry for inl_lo). PEX of adc_ch (L1a layout plus one L1b fix) simulated in all corners: offsets -32.6 / -42.2 / -23.4 LSB (typ / ff 85 / ss -40), settling, overlap, alpha, gain error PASS; 64 PASS / 5 FAIL (INL ff-40 1.10, ss125 1.05, ff 85 3.08 / 2.97, step_2048 ff 85 2.30). First run on the unmodified L1a GDS had 7 FAIL (step_2048 up to 3.92 LSB); the fix (Metal4 trim strips on b11) removed the step failures at typ / ss-40. Cause: non-binary coupling of the bit wiring to the top plate t (section 6). Decision options in BLOCKED.md.

## 2. What was built
adc_ch re-generated with `trim` (dac_lib.py TRIM_NET / TRIM_LEN / TRIM_W = b11 / 100 / 1.6 um): 219.50 x 103.67 um, slot 222 x 104, floorplan.py check 17 PASS. DRC 0, LVS match, PEX (c mode, census equal). Files: AFE/layout/adc/{dac_lib.py, mk_adc_ch.py, adc_ch.gds, adc_ch.build.json, dac_sites.log, keepout.log}.

## 3. Commands run
`python3 AFE/layout/scripts/flow.py drc|lvs|pex --gds AFE/layout/adc/adc_ch.gds --top adc_ch [--ref AFE/layout/lvs/adc_ch.spice]`; `python3 AFE/layout/tb/tb_adc_{codes,steps,overlap}.py --netlist AFE/layout/sim/flow/adc_ch.pex.spice --corner all`; `tb_adc_timing.py ... --sta AFE/dig/reports/sta_taps.json`; `compare.py --phase L1b`; diagnosis: coupling-cap sums of the PEX netlist per bit net (script in the job tmp, not committed); fix: `bash AFE/layout/scripts/kl.sh AFE/layout/adc/mk_adc_ch.py out=AFE/layout/adc/adc_ch.gds` (trim defaults); then the same flow + testbenches again (first-run results kept in AFE/layout/sim/post/attempt1/).

## 4. Results
| check | value (typ / ff85 / ss-40 unless noted) | limit | result | source |
|---|---|---|---|---|
| code offset | -32.6 / -42.2 / -23.4 LSB (ff-40 -37.8, ss125 -28.6) | change <= 15 | PASS | sim/post/adc_codes.json |
| inl_lo | 0.95 / 3.08 / 0.76 (ff-40 1.10, ss125 1.05) | 1 / 2.5 / 1 (1, 1) | typ, ss-40 PASS; ff85, ff-40, ss125 FAIL | adc_codes_*.log |
| inl_code_lo | 0.86 / 2.97 / 1.06 | 1.5 / 2 / 1.5 | ff85 FAIL | adc_codes_*.log |
| alpha, gain error | 0.9768 / 0.9752 / 0.9779; -0.01 / -0.22 / -0.04 % | -0.02, +-0.5 % | PASS | compare_L1b.md |
| step_1536 | +1.05 / +1.42 / +1.05 | 2 | PASS | adc_steps.json |
| step_2048 | +1.26 / +2.30 / +0.85 | 2 | ff85 FAIL | adc_steps.json |
| step_2112 | -0.20 / -0.45 / -0.20 | 0.5 | PASS | adc_steps.json |
| settle_worst | 0.10 (typ), 0.14 (ff-40), 0.11 (ss125), 0.80 (ss-40x) | 0.5 / 1 | PASS | adc_timing.json |
| overlap dt_max | 0.0024 / 0.0064 LSB | 0.2 | PASS | adc_overlap.json |
| unresolved, failed | 0 | 0 | PASS | all |
First run (unmodified L1a GDS): step_2048 2.92 / 3.92 / 2.17, inl_lo 1.15 / - / 1.19 (ff-40 1.32, ss125 1.26): sim/post/attempt1/.

## 5. Gate output
Last gate run (FAIL), before this report: `GATE L1b: FAIL (4 FAIL)`: compare.py 5 FAIL; report / Results-log lines (now written); see BLOCKED.md. Gate not PASS, so no PASS output exists.

## 6. Ladder decisions
- Q-1: offset change <= 2.4 LSB: not triggered; offsets restated in AFE/adc/README.md (Decision 46d).
- Q-2: step_2048 above 2.0: layout fix applied (b11 trim strips, +1.45 fF coupling to t; found because the PEX coupling per unit is 0.53 fF on b9 - b11 but b6 1.28 / b7 1.35 / b8 2.25 fF, whose sum exceeds b11 by about 1.4 fF = 1.6 LSB). Cost: none in area. Result 2.92 -> 1.26 (typ), 3.92 -> 2.30 (ff 85, inside the pre-approved 2.5 but the compare has no waiver), 2.17 -> 0.85 (ss-40).
- No entry covers inl_lo above 1 beyond Q-6 (top of range); G-1 / section 6: BLOCKED.md.

## 7. Deviations
adc_ch GDS changed after L1a (trim strips) with a new `trim` parameter in the generator; LVS reference unchanged.

## 8. Open issues and risks
Binary coupling of b6 / b7 / b8 to t (BLOCKED.md options). Since step_1536 +2.1 above the schematic, the codes just above 1536 dip by about 1 LSB in all corners. ff 85 C INL is set by the 1.99 V point, beyond the 1.9 V claim. L3a should keep all of this adc_ch geometry.

## 9. REVIEW.md items handled
R1 (to all, plan of order): L1b run on the R5 re-packed adc_ch (current GDS), after R3 / R4 / R6; no wasted PEX. R7 is addressed to L3a: not touched.

## 10. Files changed and commit
AFE/layout/adc/{dac_lib.py, mk_adc_ch.py, adc_ch.gds, adc_ch.build.json, dac_sites.log, keepout.log}, AFE/adc/README.md, AFE/NOTES.md, AFE/layout/BLOCKED.md, AFE/layout/reports/L1b.md. Commit: see git log (branch worktree-l1b-adc-post).
