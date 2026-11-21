# L2b report (2026-11-21; Claude Sonnet 5.5, default effort)

## 1. Summary and verdict
**Update 2026-11-21 (R8, REVIEW.md; accepted by the user / team): the as-built amp_ch is accepted with loosened limits (old limits: AFE/layout/accept_limits_pre_R8R9.json); `compare.py --phase L2b` now PASS; BLOCKED.md removed (its text is in section 6). Gate: section 5.**
**Verdict: GATE L2b FAIL (BLOCKED, AFE/layout/BLOCKED.md).** amp_ch (lay=6, 220.75 x 273.25 um) on the Cin 15 pF baselines: DRC 0, LVS match, PEX census equal. Post-layout: gain 59.84 / 59.82 / 59.84 dB (typ / ff 85 / ss -40), f_lo <= 0.28 Hz, f_hi 634 / 973 / 408 Hz, noise_d8 1.902 / 2.153 / 1.742 uV, PM >= 76.9 deg, THD <= 0.94 %: all PASS. 22 of 93 compare rows FAIL: power-up error 18 .. 30 mV (R-6, pre-approved <= 50 mV), reset recovery 1.2 .. 1.3 x the limits (R-7, pre-approved <= 1.5 x) - both covered by the ladder but gate.py cannot see it (limits are protected); out_min 1.180 V at typ / ss -40 (limit 1.17; cause: gain -0.21 dB), PSRR 0.636 / 0.665 at typ / ff 85 (limit 0.62; no ladder entry), junction-convention power-up error 96 .. 182 mV (R-8: layout fix or BLOCKED). Decision needed from the user: BLOCKED.md options A / B / C. Native-Vt (ladder N): no organizer answer in the repo (AFE/NOTES.md), default of ACCEPT.md section 5 (allowed), device kept.
Two kit fixes were needed first (section 6): floating dummy-poly nodes made the extracted netlist's DC point singular (37 -> 22 FAIL) and the Cin anchor size in lptb.py was still 70.65 um.

## 2. What was built
Nothing in layout (no GDS change; AFE/layout/amp/amp_ch.gds is the R6 / re-pack-2 cell, sha in the flow JSONs). Kit changes: `flow.py pex` adds Rfloat resistors (1 Tohm to ground) to capacitor-only nodes; `lptb.py` ANCHORS vn / vp 70.65 -> 61.15 um. PEX netlist AFE/layout/sim/flow/amp_ch.pex.spice: 121 devices, 347 C (2608.5 fF), 6 R (the Rfloat), MIM correction moved 8.7 / 16.2 / 4.2 / 59.3 / 14.0 / 59.8 fF (nodes a_28022_1954#, a_40238_24600#, a_6838_13302#, w_28620_25696#, w_39820_39896#, w_5020_25696#).

## 3. Commands run
```
git pull   (already up to date; REVIEW.md: R1 open, handled see section 9)
python3 AFE/layout/scripts/flow.py drc --gds AFE/layout/amp/amp_ch.gds --top amp_ch        -> 0 violations
python3 AFE/layout/scripts/flow.py lvs --gds AFE/layout/amp/amp_ch.gds --top amp_ch --ref AFE/layout/lvs/afe_chc.spice   -> match
python3 AFE/layout/scripts/flow.py pex --gds AFE/layout/amp/amp_ch.gds --top amp_ch        (twice: before / after the Rfloat fix)
for t in amp_ac amp_noise amp_psrr amp_thd amp_loop amp_pwrup amp_reset: tb_$t.py --netlist AFE/layout/sim/flow/amp_ch.pex.spice --corner all   (twice)
tb_amp_reset.py ... --os 10m,100m --host-rst 0.1 ; tb_amp_ac / tb_amp_pwrup / tb_amp_reset (+ --os 10m,100m --host-rst 0.1) / tb_amp_noise / tb_amp_psrr / tb_amp_thd with --junction
python3 AFE/layout/tb/compare.py --phase L2b      (first run 37 FAIL, after the fixes 22 FAIL)
tb_amp_pwrup.py --netlist <copy with ad/as 0.0396p on the six pseudo-R devices> --junction --corner all   (what-if, ESTIMATE, scratch only)
python3 AFE/layout/scripts/gate.py L2b
```
The first full run failed because of the singular DC point (log AFE/layout/.ptmp/tb/amp_ac/ac_pex10a0a8e3943f_typ.log: "singular matrix: check node xch.xpex.a_856_1244#", gmin / source stepping failed, transient op).

## 4. Results (design convention unless "junction"; full table AFE/layout/sim/post/compare_L2b.md)
| check | value typ / ff 85 / ss -40 | limit | result | log |
|---|---|---|---|---|
| gain g_mid_db (baseline 60.05 / 60.06 / 60.04) | 59.84 / 59.82 / 59.84 | 59 .. 61, change <= 0.3 | PASS | sim/post/amp_ac_*.log |
| f_lo / f_hi (Hz) | 0.241 / 0.276 / 0.284 ; 634 / 973 / 408 | <= 0.5 ; >= 300 | PASS | amp_ac_*.log |
| idd (uA) | 74.43 / 118.81 / 47.13 | baseline +-5 % | PASS (+0 %) | amp_ac_*.log |
| noise_d8 (uV) | 1.902 / 2.153 / 1.742 | 2.0 / 2.2 / 2.0 | PASS | amp_noise_*.log |
| pm_deg (compare shows 439 / 437 / 441 = 79 / 77 / 81 + 360, unwrapped by the script) | 79.3 / 76.6 / 81.1 | >= 60 | PASS | amp_loop_*.log |
| THD % / out_max | 0.040 / 0.94 / 0.052 ; 2.165 / 2.205 / 2.163 V | <= 0.5 / 4.5 / 0.5 ; >= 2.13 | PASS | amp_thd_*.log |
| out_min_v (baseline 1.145 / 1.220 / 1.145) | 1.180 / 1.237 / 1.178 | <= 1.17 / 1.25 / 1.17 | FAIL typ, ss -40 | amp_thd_*.log |
| PSRR 50 Hz (baseline 0.572 / 0.580 / 0.567) | 0.636 / 0.665 / 0.617 | 0.38 .. 0.62 | FAIL typ, ff 85 | amp_psrr_*.log |
| power-up err_1s (mV) | 30.3 / 18.2 / 19.8 | <= 10 | FAIL (R-6 covers <= 50) | amp_pwrup_*.log |
| reset one-shot pulse t_fs (ms) | 3.02 / 1.64 / 5.85 | 0.7 .. 1.4 x baseline | PASS (1.0 x) | amp_reset_*.log |
| reset t_1mv os0 / os1m / os10m (s) | typ 5.59 / 5.58 / 8.57 ; ff 5.52 / 5.54 / 8.51 ; ss 5.46 / 5.43 / 7.33 | 4.5 / 4.5 / 6.5 | FAIL (R-7 covers <= 1.5 x) | amp_reset_*.log |
| reset os100m t_1mv, final V | 9.47 / 7.52 / 8.26 s ; 1.651 / 1.651 / 1.650 V | 12 s ; 1.6 .. 1.7 | PASS | amp_reset_*.log |
| host reset os10m t_1mv | 7.63 / 7.42 / 6.514 | 6.5 | FAIL (R-7 covers) | amp_reset_host_*.log |
| junction: g_mid, f_hi, vout | 59.81 / 59.79 / 59.82 dB ; 636 / 975 / 409 Hz ; 1.664 / 1.651 / 1.659 V | 59 .. 61 ; >= 300 ; 1.5 .. 1.8 | PASS | amp_ac_junction_*.log |
| junction: f_lo | below 1 mHz (typ, ss -40), 0.095 Hz (ff 85) | <= 0.5 | PASS | amp_ac_junction_*.log |
| junction: host drift os10m (mV/s) | 9.6 / 11.3 / 8.6 | WARN-only 30 | PASS | amp_reset_host_junction_*.log |
| junction: power-up err_1s (mV) | 181.2 / 95.8 / 181.7 | <= 50 | FAIL (R-8) | amp_pwrup_junction_*.log |

## 5. Gate output
```
gate.py L2b  (L2b)
--- common
PASS  ACCEPT.md limits table equals AFE/layout/accept_limits.json
PASS  AFE/layout/REVIEW.md not edited by this phase
PASS  protected files (limits, ACCEPT.md, design netlists, RTL) unchanged since the last REVIEW.md commit e94677f
PASS  open REVIEW.md items for L2b or an earlier phase (R1) are listed as handled in section 9 of a phase report
INFO  AFE/layout/BLOCKED.md exists: # BLOCKED: phase L2b (amp_ch post-layout), 2026-11-21
FAIL  AFE/layout/BLOCKED.md does not block L2b (its first lines do not name it)
      -> DO: this phase is blocked: continue with a phase that does not depend on it (RUNBOOK.md "what blocks what"); the answer arrives through REVIEW.md
PASS  phase report AFE/layout/reports/L2b.md with all 10 sections
PASS  "## L2b findings" section in AFE/NOTES.md
PASS  Results-log row for L2b in AFE/NOTES.md
PASS  L2a findings of AFE/layout/NOTES_L2.md are merged into AFE/NOTES.md
PASS  L2a report AFE/layout/reports/L2a.md (converted from NOTES_L2.md) with all 10 sections
WARN  scratch AFE/layout/.ptmp is not empty: delete it at the end of the phase (common rule 4)
--- amp_ch layout: AFE/layout/amp/amp_ch.gds
--- layout still clean (the PEX is of the layout that passed DRC / LVS)
PASS  DRC report belongs to the current GDS (sha1)
PASS  DRC ran with the official deck, variant D
PASS  DRC amp_ch: 0 violations
PASS  LVS report belongs to the current GDS (sha1)
PASS  LVS reference AFE/layout/lvs/afe_chc.spice is a generated reference of AFE/layout/lvs or the phase's own AFE/layout/<cell dir>/lvs
PASS  LVS amp_ch: Circuits match uniquely.
PASS  the reference was written by mk_lvs_netlists.py (header)
--- PEX
PASS  PEX report belongs to the current GDS (sha1)
PASS  PEX ran (c mode)
PASS  PEX device census equals the LVS extraction
PASS  MIM top-plate correction applied (moved a_28022_1954# 8.7 fF, a_40238_24600# 16.2 fF, a_6838_13302# 4.2 fF, w_28620_25696# 59.3 fF)
PASS  no unknown device model in the PEX netlist 
--- post-layout limits
FAIL  compare.py --phase L2b: FAIL (71 PASS, 0 WARN, 22 FAIL, 0 missing)
      -> DO: AFE/layout/sim/post/compare_L2b.md lists every FAIL; apply the ACCEPT.md ladder entry of that check (R amplifier, Q ADC, S supply, X crosstalk)
PASS  post-layout results were simulated on extracted netlists
GATE L2b: FAIL  (2 FAIL)
```
The two FAIL lines are the compare.py result and the gate rule that a BLOCKED.md naming L2b blocks it (intended). Full output: AFE/layout/sim/post/gate_L2b.log.


**Gate re-run after R8 / R9 (2026-11-21, `python3 AFE/layout/scripts/gate.py L2b`, log AFE/layout/sim/gate_L2b.log):**
```
gate.py L2b  (L2b)
--- common
PASS  ACCEPT.md limits table equals AFE/layout/accept_limits.json
PASS  AFE/layout/REVIEW.md not edited by this phase
PASS  protected files (limits, ACCEPT.md, design netlists, RTL) unchanged since the last REVIEW.md commit b6c91de
WARN  protected files changed by REVIEW.md items (named in report section 9): AFE/layout/ACCEPT.md AFE/layout/accept_limits.json
PASS  open REVIEW.md items for L2b or an earlier phase (R1 R8) are listed as handled in section 9 of a phase report
PASS  phase report AFE/layout/reports/L2b.md with all 10 sections
PASS  "## L2b findings" section in AFE/NOTES.md
PASS  Results-log row for L2b in AFE/NOTES.md
PASS  L2a findings of AFE/layout/NOTES_L2.md are merged into AFE/NOTES.md
PASS  L2a report AFE/layout/reports/L2a.md (converted from NOTES_L2.md) with all 10 sections
WARN  scratch AFE/layout/.ptmp is not empty: delete it at the end of the phase (common rule 4)
--- amp_ch layout: AFE/layout/amp/amp_ch.gds
--- layout still clean (the PEX is of the layout that passed DRC / LVS)
PASS  DRC report belongs to the current GDS (sha1)
PASS  DRC ran with the official deck, variant D
PASS  DRC amp_ch: 0 violations
PASS  LVS report belongs to the current GDS (sha1)
PASS  LVS reference AFE/layout/lvs/afe_chc.spice is a generated reference of AFE/layout/lvs or the phase's own AFE/layout/<cell dir>/lvs
PASS  LVS amp_ch: Circuits match uniquely.
PASS  the reference was written by mk_lvs_netlists.py (header)
--- PEX
PASS  PEX report belongs to the current GDS (sha1)
PASS  PEX ran (c mode)
PASS  PEX device census equals the LVS extraction
PASS  MIM top-plate correction applied (moved a_28022_1954# 8.7 fF, a_40238_24600# 16.2 fF, a_6838_13302# 4.2 fF, w_28620_25696# 59.3 fF)
PASS  no unknown device model in the PEX netlist 
--- post-layout limits
PASS  compare.py --phase L2b: PASS (90 PASS, 0 WARN, 0 FAIL, 0 missing)
PASS  post-layout results were simulated on extracted netlists
GATE L2b: PASS  (0 FAIL)
```

## 6. Ladder decisions
- P-1 / G-1 neighbourhood (no entry): floating capacitor-only nodes (six dummy poly lines) made the DC operating point singular. Not a layout defect for LVS or DRC; fixed in the kit (flow.py pex Rfloat 1 Tohm, listed in amp_ch.pex.json). Cost: n_res = 6 in the PEX report. Evidence: 37 FAIL -> 22 FAIL, idd 4.9 uA -> 74.43 uA (= baseline), vout 0.39 -> 1.6506 V.
- P-2: anchors for vn / vp missing (lptb.py still had the 20 pF size): lptb.py ANCHORS vn / vp 61.15 um. The loop margin and t_fs are now measured.
- R-5: out_min 1.18 V: extraction checked (LVS match, census equal); cause is the gain loss of 0.21 dB. No relief available -> BLOCKED.md.
- R-6 (10 .. 50 mV pre-approved): applies to 18 .. 30 mV, not applied to the gate (limits are protected).
- R-7 (<= 1.5 x pre-approved): applies to t_1mv rows, not applied to the gate.
- R-8: junction area of the six pseudo-R devices is not the lever (what-if ad / as 0.0396p: 182 / 116 / 178 mV, ESTIMATE). Layout cure not attempted: see BLOCKED.md for why.
- PSRR: no ladder entry. BLOCKED.md.
- N: unchanged (default allowed).


**BLOCKED.md of this phase (2026-11-21, removed after R8; kept here verbatim, headings demoted):**

#### BLOCKED: phase L2b (amp_ch post-layout), 2026-11-21

Gate line that failed (copied): `GATE L2b: FAIL` because `compare.py --phase L2b: FAIL (71 PASS, 0 WARN, 22 FAIL, 0 missing)` (AFE/layout/sim/post/compare_L2b.md). Layout: AFE/layout/amp/amp_ch.gds (lay=6, 220.75 x 273.25 um), DRC 0, LVS match, PEX census equal.

#### What passes
Gain 59.82 / 59.84 / 59.84 dB (typ / ff 85 / ss -40; -0.21 .. -0.24 dB from the baseline), f_lo 0.24 / 0.28 / 0.28 Hz, f_hi 634 / 973 / 408 Hz, idd unchanged, noise_d8 1.902 / 2.153 / 1.742 uV (limits 2.0 / 2.2 / 2.0), PM >= 76.9 deg (hf_dev_db ok), THD 0.04 / 0.94 / 0.05 %, one-shot pulse width within 1 % of the baseline, junction convention: gain, f_hi, output level, f_lo, host drift all PASS.

#### What fails, and the ladder entry that covers it
| check (corners) | post / limit | ladder entry | status |
|---|---|---|---|
| amp_pwrup err_1s_mv (typ / ff 85 / ss -40) | 30.3 / 18.2 / 19.8 mV, limit 10 | R-6: 10 .. 50 mV is PRE-APPROVED | covered, but gate.py cannot see it (compare.py reads accept_limits.json, protected) |
| amp_reset t_1mv os0 / os1m / os10m, amp_reset_host os10m (all corners) | 5.5 / 5.5 / 8.6 s vs 4.5 / 4.5 / 6.5 s (1.22 x .. 1.32 x); host ss -40 6.514 vs 6.5 | R-7: up to 1.5 x the limit is PRE-APPROVED | covered, same gate problem |
| amp_thd out_min_v (typ, ss -40) | 1.1803 / 1.1783 V, limit 1.17 (baseline 1.1449 / 1.1450) | R-5 says "check the extraction": done (LVS match, census equal); cause is the 0.21 .. 0.23 dB gain loss (compresses the swing, out_max +14 mV, out_min +35 mV) | NO pre-approved degradation |
| amp_psrr supply_gain_50hz (typ, ff 85) | 0.636 / 0.665, limit 0.38 .. 0.62 (baseline 0.572 / 0.580; ss -40 0.617 passes by 0.003) | NONE in section 4 | NO entry |
| amp_pwrup_junction err_1s_mv (typ / ff 85 / ss -40) | 181 / 96 / 182 mV (stable offset, output sits at 1.468 V), limit 50 | R-8: layout fix, else BLOCKED.md | open |

#### What was tried (each with its result)
1. flow.py drc / lvs / pex on the L2a GDS: DRC 0, LVS match, PEX census equal (log AFE/layout/sim/flow/amp_ch.{drc,lvs,pex}.json).
2. FIRST full run: 37 FAIL with output at 0.39 V and idd 4.9 uA. Cause: six capacitor-only nodes in the PEX netlist (the poly dummy lines `dummy_l=2.0` of `ota_p` x4 and `mir` x2 in AFE/layout/amp/amplib.py compose(): poly over field, tied to nothing) make the DC operating point singular; ngspice falls back to a transient start in which the bias cell stays in its low state. Fix (kit, not layout): `flow.py pex` now adds `Rfloat_<n> node 0 1e12` for every node that has only capacitors (listed in amp_ch.pex.json "floating_nodes"; no effect on signals, gmin is 1e-16 S). Re-run: 37 -> 22 FAIL. ALSO: lptb.py ANCHORS had the 20 pF Cin size 70.65 um for the summing-node probes (left over from before R6); changed to 61.15 um (so pm_deg, t_fs are measured, not nan).
3. R-8 what-if (ESTIMATE, not a gate number): the six pseudo-R transistors drawn with ad / as 0.2166p (W x 0.98 um strips) were edited in a COPY of the PEX netlist to the DIFF formula area 0.0396p: amp_pwrup_junction err_1s = 182 / 116 / 178 mV, i.e. the junction area of the six devices is NOT the lever. (copy in the job scratch only.)
4. Parasitics read from the PEX netlist (fF): vn (w_5020) - v1 1.89, vn - vp 13.5, vn - vdd 13.0 / vss 11.1 / rec 9.3; vp (w_28620) - vdd 12.0 / vss 14.8 / ref 18.1 / rec 2.3. So vn and vp see unequal vdd / vss / rec-ref coupling (1.0 / 3.7 fF): that is the likely origin of the PSRR rise (a 1 fF vdd mismatch between the two 15 pF summing nodes is of the size of the +0.064 seen, ESTIMATE) and the 1.9 fF vn - v1 coupling in parallel with Cf1 = 150 fF (1.3 %) of the gain loss. The reset gate nodes a_5238 / a_5338 / a_28938 couple 0.6 .. 1.9 fF into vn, vp and v1 (charge injection after RST_AMP, probable origin of the slower recovery, same time at all corners = temperature independent). Not yet verified by a layout change.
No layout change was made: the cell has already used the R1 checkpoint's extra re-pack attempt (REVIEW.md R1), and every cure listed above moves the vn / vp / reset-gate wiring of a cell that fits its slot by 1.25 um in width and 0.8 um in height.

#### Smallest decisions that would unblock it (one question)
Q: How should L2b close for the as-built amp_ch (lay=6)?
- (A) Accept the as-built numbers: REVIEW.md item to L2b that (i) applies R-6 and R-7 to accept_limits.json / ACCEPT.md (err_1s <= 50 mV, t_1mv limits x 1.5), (ii) sets out_min <= 1.19 V at typ / ss -40, PSRR <= 0.68 (gain 0.32 .. 0.68 still keeps the 1 mV board-ripple requirement: ESTIMATE |0.68 - 0.5| = 0.18 vs 0.12 now), (iii) accepts the junction-convention power-up error up to 190 mV (the host's +-200 LSB = 161 mV rule fails by 20 mV at ss -40 / typ, so (iii) needs README rule 3(a) RST_AMP repeat). Cost: none in layout; L1b / L3a continue on this GDS.
- (B) One more amp_ch re-layout (symmetric vn / vp environment, vn - v1 coupling removed, reset-gate wiring away from the summing nodes). Cost: a full L2a-type iteration + L2b again, and the slot has 0.8 um of height margin.
- (C) Accept (A)(i) and (A)(ii) only and treat the junction convention as the risk view of ACCEPT.md section 2 (its pre-decided handling lets that convention NOT gate; R-8 contradicts it).

#### What can continue meanwhile
L1b (adc_ch post-layout) and L3a (top assembly with the as-built cells) do not depend on L2b's numbers. L3b needs this decision before its top_pwrup8 / top_e2e checks.

Evidence: AFE/layout/sim/post/compare_L2b.md, AFE/layout/sim/post/*.log, AFE/layout/sim/flow/amp_ch.pex.json, AFE/layout/reports/L2b.md.

**Resolution: R8** (REVIEW.md): the user / team accepted the as-built numbers; the limits were changed in AFE/layout/accept_limits.json and the ACCEPT.md table (compare.py --write-accept) together; the old values are in AFE/layout/accept_limits_pre_R8R9.json and in the REVIEW.md item.

## 7. Deviations
Kit files edited by this phase: AFE/layout/scripts/flow.py (bleed_floating) and AFE/layout/tb/lptb.py (ANCHORS); neither is protected (ACCEPT.md section 1 protects limits, baselines, design netlists, RTL, REVIEW.md); they change every later PEX of the kit (L1b, L3b see 1 Tohm resistors on capacitor-only nodes: harmless). The baselines were not touched.

## 8. Open issues and risks
- Decision on BLOCKED.md options A / B / C (user via REVIEW.md).
- The six floating dummy-poly lines (`dummy_l=2.0` in amplib.compose, ota_p x4, mir x2) are untied poly in silicon; tying them to vdd / vss is a layout hygiene item for any re-layout.
- vn / vp environment mismatch (vdd 13.0 vs 12.0 fF, vss 11.1 vs 14.8 fF, rec 9.3 vs ref 18.1 fF) and vn - v1 coupling 1.89 fF (1.3 % of Cf1) are the likely origins of the PSRR rise and the gain loss; reset gate nodes couple 0.6 .. 1.9 fF into vn / vp / v1 (probable origin of the slower recovery). All ESTIMATE, not verified by a layout change.
- Junction convention: -180 mV power-up offset is a leakage-floor effect that the schematic baseline (1 mV) does not show; ACCEPT.md section 2 says that convention is the risk view, the gate row contradicts it.
- 8 channels: the power-up row with a common RST_AMP (L3b top_pwrup8) will inherit the 18 .. 30 mV.

## 9. REVIEW.md items handled
- R1 (open, to all): order of work respected: L2b was run on the NEW amp_ch (R6 + re-pack 2, merged as 6a969a0), after R4 / R6; not run on the old cell. The R1 checkpoint rule (a further failure after the extra re-pack attempt -> BLOCKED.md and the user decides) is what BLOCKED.md applies.
- R2 .. R7: not addressed to L2b (R7 is for L3a, still open, not touched).

- R8 (to L2b): applied by the monitoring session 2026-11-21 at the user's request: protected files changed for R8: AFE/layout/accept_limits.json and AFE/layout/ACCEPT.md (err_1s_mv 10 -> 50 (R-6), t_1mv x 1.5 (R-7), out_min_v typ / ss-40 1.17 -> 1.19, supply_gain_50hz 0.38..0.62 -> 0.32..0.68, amp_pwrup_junction err_1s_mv not gating (report)); copy of the old file AFE/layout/accept_limits_pre_R8R9.json; BLOCKED.md removed; compare L2b PASS.
- R9 (to L1b): see AFE/layout/reports/L1b.md section 9.

## 10. Files changed and commit
AFE/layout/scripts/flow.py, AFE/layout/tb/lptb.py, AFE/layout/sim/flow/amp_ch.{drc,lvs,pex}.json and logs, AFE/layout/sim/post/*, AFE/layout/BLOCKED.md, AFE/layout/reports/L2b.md, AFE/NOTES.md (L2b findings + Results-log row). Commit hash: 88260bc (branch worktree-l2b).
