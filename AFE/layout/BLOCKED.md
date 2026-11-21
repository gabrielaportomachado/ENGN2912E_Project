# BLOCKED: phase L1b (adc_ch post-layout), 2026-11-21

**Gate line that failed:** `FAIL  compare.py --phase L1b: FAIL (64 PASS, 0 WARN, 5 FAIL, 0 missing)`, plus the report / Results-log lines until written (now written).
The 5 FAIL (AFE/layout/sim/post/compare_L1b.md): adc_codes inl_lo_lsb ff-40 1.096 and ss125 1.053 (limit 1), ff85 3.079 (limit 2.5); adc_codes inl_code_lo_lsb ff85 2.970 (limit 2); adc_steps step_2048_lsb ff85 2.295 (limit 2.0; Q-2 pre-approves up to 2.5, but compare.py / gate.py have no waiver).

**What was tried:** (1) PEX of the L1a layout, 4 testbenches, all corners: 7 FAIL (step_2048 2.92 / 3.92 / 2.17; inl_lo 1.15 / 1.19 / 1.26 / 1.32; logs in AFE/layout/sim/post/attempt1/). (2) Diagnosis from the PEX netlist: coupling of the bit bottom-plate wiring to the top plate t is 0.53 fF per unit for b9 / b10 / b11 but b6 1.28, b7 1.35, b8 2.25 fF: the excess of the small bits, summed (+1.4 fF), is what adds +1.6 LSB at the 2048 step (0.85 fF = 1 LSB). (3) Layout fix: Metal4 strips of b11 under the t trunk (dac_lib.py TRIM_*; +1.45 fF on b11): DRC 0, LVS match, PEX; second run 5 FAIL (above). The strip length is limited by the gaps between the other tabs under the trunk.
**Why it stops here:** the remaining dips come from the excess coupling of b6 / b7 (their pads sit in the 6 um channel between rows 3 and 4, 0.7 / 0.3 fF above binary); fixing it needs a different pad / exit arrangement of the single-unit bits (a re-pack of the DAC exits), not a small fix; the ff 85 C items are the 1.99 V point beyond the ff 85 claim (1.9 V) plus the Q-2 step.

**Smallest decision that unblocks (answer through REVIEW.md):**
1. Accept the as-built adc_ch of this commit (INL <= 1.1 LSB at all corners below 2.0 V except ff 85 C, steps <= 2.3 LSB) and set the compare limits to: inl_lo ff-40 / ss125 <= 1.2, ff 85 <= 3.1 (inl_code <= 3.0), step_2048 ff85 <= 2.5 (Q-2). Cost: Decision 43c claim becomes INL <= 1.1 LSB (typ 0.95); nothing else changes.
2. One more adc_ch layout iteration (DAC exits of b6 / b7 / b8 moved so that their coupling to t is binary, or compensating strips on the channel side). Cost: about one L1a-type session, then L1b again (30 min PEX simulations).
3. Narrow the README claim at ff 85 C to inputs <= 1.9 V (Q-6) and accept 2 only.
**What can continue meanwhile:** L2b (amp_ch), L1d, L3a do not depend on adc_ch linearity; L3b waits.
