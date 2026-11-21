# BLOCKED: phase L2b (amp_ch post-layout), 2026-11-21

Gate line that failed (copied): `GATE L2b: FAIL` because `compare.py --phase L2b: FAIL (71 PASS, 0 WARN, 22 FAIL, 0 missing)` (AFE/layout/sim/post/compare_L2b.md). Layout: AFE/layout/amp/amp_ch.gds (lay=6, 220.75 x 273.25 um), DRC 0, LVS match, PEX census equal.

## What passes
Gain 59.82 / 59.84 / 59.84 dB (typ / ff 85 / ss -40; -0.21 .. -0.24 dB from the baseline), f_lo 0.24 / 0.28 / 0.28 Hz, f_hi 634 / 973 / 408 Hz, idd unchanged, noise_d8 1.902 / 2.153 / 1.742 uV (limits 2.0 / 2.2 / 2.0), PM >= 76.9 deg (hf_dev_db ok), THD 0.04 / 0.94 / 0.05 %, one-shot pulse width within 1 % of the baseline, junction convention: gain, f_hi, output level, f_lo, host drift all PASS.

## What fails, and the ladder entry that covers it
| check (corners) | post / limit | ladder entry | status |
|---|---|---|---|
| amp_pwrup err_1s_mv (typ / ff 85 / ss -40) | 30.3 / 18.2 / 19.8 mV, limit 10 | R-6: 10 .. 50 mV is PRE-APPROVED | covered, but gate.py cannot see it (compare.py reads accept_limits.json, protected) |
| amp_reset t_1mv os0 / os1m / os10m, amp_reset_host os10m (all corners) | 5.5 / 5.5 / 8.6 s vs 4.5 / 4.5 / 6.5 s (1.22 x .. 1.32 x); host ss -40 6.514 vs 6.5 | R-7: up to 1.5 x the limit is PRE-APPROVED | covered, same gate problem |
| amp_thd out_min_v (typ, ss -40) | 1.1803 / 1.1783 V, limit 1.17 (baseline 1.1449 / 1.1450) | R-5 says "check the extraction": done (LVS match, census equal); cause is the 0.21 .. 0.23 dB gain loss (compresses the swing, out_max +14 mV, out_min +35 mV) | NO pre-approved degradation |
| amp_psrr supply_gain_50hz (typ, ff 85) | 0.636 / 0.665, limit 0.38 .. 0.62 (baseline 0.572 / 0.580; ss -40 0.617 passes by 0.003) | NONE in section 4 | NO entry |
| amp_pwrup_junction err_1s_mv (typ / ff 85 / ss -40) | 181 / 96 / 182 mV (stable offset, output sits at 1.468 V), limit 50 | R-8: layout fix, else BLOCKED.md | open |

## What was tried (each with its result)
1. flow.py drc / lvs / pex on the L2a GDS: DRC 0, LVS match, PEX census equal (log AFE/layout/sim/flow/amp_ch.{drc,lvs,pex}.json).
2. FIRST full run: 37 FAIL with output at 0.39 V and idd 4.9 uA. Cause: six capacitor-only nodes in the PEX netlist (the poly dummy lines `dummy_l=2.0` of `ota_p` x4 and `mir` x2 in AFE/layout/amp/amplib.py compose(): poly over field, tied to nothing) make the DC operating point singular; ngspice falls back to a transient start in which the bias cell stays in its low state. Fix (kit, not layout): `flow.py pex` now adds `Rfloat_<n> node 0 1e12` for every node that has only capacitors (listed in amp_ch.pex.json "floating_nodes"; no effect on signals, gmin is 1e-16 S). Re-run: 37 -> 22 FAIL. ALSO: lptb.py ANCHORS had the 20 pF Cin size 70.65 um for the summing-node probes (left over from before R6); changed to 61.15 um (so pm_deg, t_fs are measured, not nan).
3. R-8 what-if (ESTIMATE, not a gate number): the six pseudo-R transistors drawn with ad / as 0.2166p (W x 0.98 um strips) were edited in a COPY of the PEX netlist to the DIFF formula area 0.0396p: amp_pwrup_junction err_1s = 182 / 116 / 178 mV, i.e. the junction area of the six devices is NOT the lever. (copy in the job scratch only.)
4. Parasitics read from the PEX netlist (fF): vn (w_5020) - v1 1.89, vn - vp 13.5, vn - vdd 13.0 / vss 11.1 / rec 9.3; vp (w_28620) - vdd 12.0 / vss 14.8 / ref 18.1 / rec 2.3. So vn and vp see unequal vdd / vss / rec-ref coupling (1.0 / 3.7 fF): that is the likely origin of the PSRR rise (a 1 fF vdd mismatch between the two 15 pF summing nodes is of the size of the +0.064 seen, ESTIMATE) and the 1.9 fF vn - v1 coupling in parallel with Cf1 = 150 fF (1.3 %) of the gain loss. The reset gate nodes a_5238 / a_5338 / a_28938 couple 0.6 .. 1.9 fF into vn, vp and v1 (charge injection after RST_AMP, probable origin of the slower recovery, same time at all corners = temperature independent). Not yet verified by a layout change.
No layout change was made: the cell has already used the R1 checkpoint's extra re-pack attempt (REVIEW.md R1), and every cure listed above moves the vn / vp / reset-gate wiring of a cell that fits its slot by 1.25 um in width and 0.8 um in height.

## Smallest decisions that would unblock it (one question)
Q: How should L2b close for the as-built amp_ch (lay=6)?
- (A) Accept the as-built numbers: REVIEW.md item to L2b that (i) applies R-6 and R-7 to accept_limits.json / ACCEPT.md (err_1s <= 50 mV, t_1mv limits x 1.5), (ii) sets out_min <= 1.19 V at typ / ss -40, PSRR <= 0.68 (gain 0.32 .. 0.68 still keeps the 1 mV board-ripple requirement: ESTIMATE |0.68 - 0.5| = 0.18 vs 0.12 now), (iii) accepts the junction-convention power-up error up to 190 mV (the host's +-200 LSB = 161 mV rule fails by 20 mV at ss -40 / typ, so (iii) needs README rule 3(a) RST_AMP repeat). Cost: none in layout; L1b / L3a continue on this GDS.
- (B) One more amp_ch re-layout (symmetric vn / vp environment, vn - v1 coupling removed, reset-gate wiring away from the summing nodes). Cost: a full L2a-type iteration + L2b again, and the slot has 0.8 um of height margin.
- (C) Accept (A)(i) and (A)(ii) only and treat the junction convention as the risk view of ACCEPT.md section 2 (its pre-decided handling lets that convention NOT gate; R-8 contradicts it).

## What can continue meanwhile
L1b (adc_ch post-layout) and L3a (top assembly with the as-built cells) do not depend on L2b's numbers. L3b needs this decision before its top_pwrup8 / top_e2e checks.

Evidence: AFE/layout/sim/post/compare_L2b.md, AFE/layout/sim/post/*.log, AFE/layout/sim/flow/amp_ch.pex.json, AFE/layout/reports/L2b.md.
