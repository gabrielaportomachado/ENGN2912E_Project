# L1b report (2026-11-21; Claude Sonnet 5.5 / default)

## 1. Summary and verdict
**Update 2026-11-21 (R9, REVIEW.md; accepted by the user / team): the as-built adc_ch is accepted with loosened limits (old limits: AFE/layout/accept_limits_pre_R8R9.json); `compare.py --phase L1b` now PASS; BLOCKED.md removed (its text is in section 6). Gate: section 5.**
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


**Gate re-run after R8 / R9 (2026-11-21, `python3 AFE/layout/scripts/gate.py L1b`, log AFE/layout/sim/gate_L1b.log):**
```
gate.py L1b  (L1b)
--- common
PASS  ACCEPT.md limits table equals AFE/layout/accept_limits.json
PASS  AFE/layout/REVIEW.md not edited by this phase
PASS  protected files (limits, ACCEPT.md, design netlists, RTL) unchanged since the last REVIEW.md commit b6c91de
WARN  protected files changed by REVIEW.md items (named in report section 9): AFE/layout/ACCEPT.md AFE/layout/accept_limits.json
PASS  open REVIEW.md items for L1b or an earlier phase (R1 R8 R9) are listed as handled in section 9 of a phase report
PASS  phase report AFE/layout/reports/L1b.md with all 10 sections
PASS  "## L1b findings" section in AFE/NOTES.md
PASS  Results-log row for L1b in AFE/NOTES.md
PASS  L2a findings of AFE/layout/NOTES_L2.md are merged into AFE/NOTES.md
PASS  L2a report AFE/layout/reports/L2a.md (converted from NOTES_L2.md) with all 10 sections
WARN  scratch AFE/layout/.ptmp is not empty: delete it at the end of the phase (common rule 4)
--- adc_ch layout: AFE/layout/adc/adc_ch.gds
--- layout still clean (the PEX is of the layout that passed DRC / LVS)
PASS  DRC report belongs to the current GDS (sha1)
PASS  DRC ran with the official deck, variant D
PASS  DRC adc_ch: 0 violations
PASS  LVS report belongs to the current GDS (sha1)
PASS  LVS reference AFE/layout/lvs/adc_ch.spice is a generated reference of AFE/layout/lvs or the phase's own AFE/layout/<cell dir>/lvs
PASS  LVS adc_ch: Circuits match uniquely.
PASS  the reference was written by mk_lvs_netlists.py (header)
--- PEX
PASS  PEX report belongs to the current GDS (sha1)
PASS  PEX ran (c mode)
PASS  PEX device census equals the LVS extraction
PASS  MIM top-plate correction applied (moved a_1094_7200# 13.2 fF, a_21494_7200# 13.5 fF, a_23316_2302# 0.3 fF, a_26694_9400# 26.7 fF)
PASS  no unknown device model in the PEX netlist 
--- post-layout limits
PASS  compare.py --phase L1b: PASS (69 PASS, 0 WARN, 0 FAIL, 0 missing)
PASS  post-layout results were simulated on extracted netlists
GATE L1b: PASS  (0 FAIL)
```

## 6. Ladder decisions
- Q-1: offset change <= 2.4 LSB: not triggered; offsets restated in AFE/adc/README.md (Decision 46d).
- Q-2: step_2048 above 2.0: layout fix applied (b11 trim strips, +1.45 fF coupling to t; found because the PEX coupling per unit is 0.53 fF on b9 - b11 but b6 1.28 / b7 1.35 / b8 2.25 fF, whose sum exceeds b11 by about 1.4 fF = 1.6 LSB). Cost: none in area. Result 2.92 -> 1.26 (typ), 3.92 -> 2.30 (ff 85, inside the pre-approved 2.5 but the compare has no waiver), 2.17 -> 0.85 (ss-40).
- No entry covers inl_lo above 1 beyond Q-6 (top of range); G-1 / section 6: BLOCKED.md.


**BLOCKED.md of this phase (2026-11-21, removed after R9; kept here verbatim, headings demoted):**

#### BLOCKED: phase L1b (adc_ch post-layout), 2026-11-21

**Gate line that failed:** `FAIL  compare.py --phase L1b: FAIL (64 PASS, 0 WARN, 5 FAIL, 0 missing)`, plus the report / Results-log lines until written (now written).
The 5 FAIL (AFE/layout/sim/post/compare_L1b.md): adc_codes inl_lo_lsb ff-40 1.096 and ss125 1.053 (limit 1), ff85 3.079 (limit 2.5); adc_codes inl_code_lo_lsb ff85 2.970 (limit 2); adc_steps step_2048_lsb ff85 2.295 (limit 2.0; Q-2 pre-approves up to 2.5, but compare.py / gate.py have no waiver).

**What was tried:** (1) PEX of the L1a layout, 4 testbenches, all corners: 7 FAIL (step_2048 2.92 / 3.92 / 2.17; inl_lo 1.15 / 1.19 / 1.26 / 1.32; logs in AFE/layout/sim/post/attempt1/). (2) Diagnosis from the PEX netlist: coupling of the bit bottom-plate wiring to the top plate t is 0.53 fF per unit for b9 / b10 / b11 but b6 1.28, b7 1.35, b8 2.25 fF: the excess of the small bits, summed (+1.4 fF), is what adds +1.6 LSB at the 2048 step (0.85 fF = 1 LSB). (3) Layout fix: Metal4 strips of b11 under the t trunk (dac_lib.py TRIM_*; +1.45 fF on b11): DRC 0, LVS match, PEX; second run 5 FAIL (above). The strip length is limited by the gaps between the other tabs under the trunk.
**Why it stops here:** the remaining dips come from the excess coupling of b6 / b7 (their pads sit in the 6 um channel between rows 3 and 4, 0.7 / 0.3 fF above binary); fixing it needs a different pad / exit arrangement of the single-unit bits (a re-pack of the DAC exits), not a small fix; the ff 85 C items are the 1.99 V point beyond the ff 85 claim (1.9 V) plus the Q-2 step.

**Smallest decision that unblocks (answer through REVIEW.md):**
1. Accept the as-built adc_ch of this commit (INL <= 1.1 LSB at all corners below 2.0 V except ff 85 C, steps <= 2.3 LSB) and set the compare limits to: inl_lo ff-40 / ss125 <= 1.2, ff 85 <= 3.1 (inl_code <= 3.0), step_2048 ff85 <= 2.5 (Q-2). Cost: Decision 43c claim becomes INL <= 1.1 LSB (typ 0.95); nothing else changes.
2. One more adc_ch layout iteration (DAC exits of b6 / b7 / b8 moved so that their coupling to t is binary, or compensating strips on the channel side). Cost: about one L1a-type session, then L1b again (30 min PEX simulations).
3. Narrow the README claim at ff 85 C to inputs <= 1.9 V (Q-6) and accept 2 only.
**What can continue meanwhile:** L2b (amp_ch), L1d, L3a do not depend on adc_ch linearity; L3b waits.

**Resolution: R9** (REVIEW.md): the user / team accepted the as-built numbers; the limits were changed in AFE/layout/accept_limits.json and the ACCEPT.md table (compare.py --write-accept) together; the old values are in AFE/layout/accept_limits_pre_R8R9.json and in the REVIEW.md item.

## 7. Deviations
adc_ch GDS changed after L1a (trim strips) with a new `trim` parameter in the generator; LVS reference unchanged.

## 8. Open issues and risks
Binary coupling of b6 / b7 / b8 to t (BLOCKED.md options). Since step_1536 +2.1 above the schematic, the codes just above 1536 dip by about 1 LSB in all corners. ff 85 C INL is set by the 1.99 V point, beyond the 1.9 V claim. L3a should keep all of this adc_ch geometry.

## 9. REVIEW.md items handled
R1 (to all, plan of order): L1b run on the R5 re-packed adc_ch (current GDS), after R3 / R4 / R6; no wasted PEX. R7 is addressed to L3a: not touched.

- R9 (to L1b): applied by the monitoring session 2026-11-21 at the user's request: protected files changed for R9: AFE/layout/accept_limits.json and AFE/layout/ACCEPT.md (adc_codes inl_lo_lsb ff-40 / ss125 1 -> 1.2, ff85 2.5 -> 3.1; inl_code_lo_lsb ff85 2 -> 3.0; step_2048_lsb ff85 2.0 -> 2.5 (Q-2); top_e2e inl_lo_lsb ff85 2.5 -> 3.1); copy of the old file AFE/layout/accept_limits_pre_R8R9.json; BLOCKED.md removed; compare L1b PASS. README.md / AFE/adc/README.md INL claim restated (<= 1.1 LSB).
- R8 (to L2b): see AFE/layout/reports/L2b.md section 9.
- PEX re-check for the L2b kit fix (flow.py bleed_floating): AFE/layout/sim/flow/adc_ch.pex.spice has 0 capacitor-only nodes, so the L1b numbers are unchanged by that fix.

## 10. Files changed and commit
AFE/layout/adc/{dac_lib.py, mk_adc_ch.py, adc_ch.gds, adc_ch.build.json, dac_sites.log, keepout.log}, AFE/adc/README.md, AFE/NOTES.md, AFE/layout/BLOCKED.md, AFE/layout/reports/L1b.md. Commit: see git log (branch worktree-l1b-adc-post).
