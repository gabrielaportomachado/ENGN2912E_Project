# REVIEW.md: feedback to the layout phases

Written ONLY by the user / the monitoring session. A phase never edits this file. Every phase starts with `git pull`, reads this file and applies every open item addressed to it or to
an earlier phase BEFORE its own work (a fix to a finished phase is redone and that phase's gate re-run first), then lists the items it handled in section 9 of its report
AFE/layout/reports/<phase>.md. `gate.py` fails while an open item for the phase (or an earlier one) is not listed in a report's section 9.
ACCEPT.md is IN FORCE (user, 2026-11-20) and is reviewed after the fact: changes to it, to the limits or to a protected file arrive here as items.

Item format (one per heading; the target is a phase, several phases separated by commas, or `all`):

    ### R1 (2026-11-21) to L2b: <short title>
    Status: open
    <what to do, why, evidence>

The monitoring session sets `Status: closed` once it has seen the item handled.

## Items

### R1 (2026-11-20) to all: 8-channel closure plan (Decision 48), order of work
Status: open
The as-built cells do not fit 8 channels in the 1000 x 1000 um outline (L1a report section 8: amp_ch 218.75 x 309.25, adc_ch 265.85 x 126.25 against the 235 x 375 um channel slot). The user keeps N = 8 (Decision 48). Do the items in this order, one phase session each, gate + report + push after each: R2 (floorplan) -> R3 (afe_dig re-harden) -> R4 (Cin 15 pF, then amp_ch rework) -> R5 (adc_ch re-pack) -> then L2b and L1b on the NEW cells -> L3a. Do not run L2b / L1b / L3a on the current cells (wasted PEX). CHECKPOINT (deadline now 2026-11-30, Decision 49): a cell that misses its budget by more than 3 % in either dimension gets ONE more re-pack attempt in a fresh session; if it still misses after that, or R4's simulations fail a Decision 1 target, write AFE/layout/BLOCKED.md with the as-built sizes / numbers and stop that line (the user decides between more rework and N = 4, ladder A-6); the other items may continue.

### R2 (2026-11-20) to L3a: tightened floorplan for 8 channels
Status: closed (monitoring 2026-11-20: handled, merged in c18ea08, floorplan.py check 16 PASS)
Run `python3 AFE/layout/scripts/floorplan.py build --set ring=26 bias_corr=12 strap_corr=25 dig_h=80 ch_pitch=237 adc_h=104` (checked by the monitoring session: channel slot 237 x 397 um, amp_ch <= 222 x 285, adc_ch <= 222 x 104, afe_dig 820 x 80 at 51 % utilisation, bias_genc <= 108 x 110; `floorplan.py check` gives 15 PASS and ONE FAIL: 3e, pins DOUT_IN / VDD touch on the west edge). Fix 3e by changing only the west pin parameters (pin_pitch_w / pin_y0_w or the pin order inside the organizer template rules) until `floorplan.py check` is all PASS; update SPEC.md to the new numbers; commit floorplan.json + SPEC.md. The amp / adc split of the 389 um (amp_h + adc_h) may be moved by up to 10 um between the two cells (`adc_h`) once R4 / R5 know their real heights; the outline stays 1000 x 1000 um.

### R3 (2026-11-20) to L1d: re-harden afe_dig at 820 x 80 um
Status: closed (monitoring 2026-11-21: handled on branch worktree-r3-dig; 80 um does not route, afe_dig 819.84 x 101.92 um, gate L1d PASS; the height conflict goes to R7)
Re-run the frozen L1d recipe with the macro height 80 um (die 820 x 80, pins per the new floorplan.json from R2). All L1d checks again: STA at 5 corners, tap-delay limits (a) >= 21.0 ns, (b)/(c) >= 20.0 ns, max-slew / max-cap 0, KLayout DRC variant D 0, run_tb_audit.sh gls (only the 4 known assertions), LVS, regenerate the LVS top with --dig-netlist. If the routing fails at 80 um, try 85 / 90 um and report; each 10 um above 80 must come out of adc_h or amp_h (tell R5 / R4 in the report). Merge branch worktree-l1d-dig into main first if it is not merged.

### R4 (2026-11-20) to L2a (then L2b): Cin 20 pF -> 15 pF, then amp_ch to <= 222 x 285 um
Status: closed (monitoring 2026-11-21: step 1 on worktree-r4-amp-cin15, finished by R6)
Decision 48 (circuit change approved by the user): in AFE/amp/spice/afe_params.spice set `.param CF1V=150f` (was 200f); CIN_RATIO stays 100, so Cin1 = Cin2 = 15 pF and the stage-1 gain stays 100 (60 dB channel). Nothing else in the circuit changes. Step 1, simulate BEFORE any layout (schematic, typ 27 / ff 85 / ss -40, common rule 8, the golden testbenches AFE/layout/tb/tb_amp_*.py with --netlist schematic): gain (60 +- 1 dB; if the parasitic absorbed by CF1V moves it by more than 0.3 dB, trim CF1V in 5 fF steps and say so), f_lo <= 0.5 Hz, f_hi >= 300 Hz, noise <= 2 uV (0.5-300 Hz), PM, THD, PSRR, reset recovery with the one-shot, power-up with RST_AMP 100 ms, and AFE/adc/scripts/x2_s1.py typ (amp -> ADC). Write the new numbers next to the 20 pF baselines; then REPLACE the amp baselines in AFE/layout/baseline/ with the 15 pF ones (keep the old files as *_cin20.json) so that compare.py / gate.py use them. Update the noise / f_lo statements in AFE/adc/README.md and info.yaml / README.md if they quote them. If any Decision 1 target fails: stop, BLOCKED.md (checkpoint of R1). Step 2: regenerate the LVS reference with `mk_lvs_netlists.py --cin 2,W,L` for two pieces of 7.5 pF each on the 5 nm grid (W = L chosen for capacitance, as F1 did; state it), re-run check_lvs_netlists.py. Step 3: re-run the amp_ch generator with the smaller Cin block and the full cell width 222 um (ladder A-3), target <= 222 x 285 um, DRC 0, LVS match; keep all L2a rules (summing nodes on the top plates, nothing under the plates, identical minimum-area pseudo-R devices, ABBA pair with dummies). Report the block table vs the old one.

### R5 (2026-11-20) to L1a: adc_ch re-pack to <= 222 x 104 um
Status: closed (monitoring 2026-11-20: handled on branch worktree-r5-adc-repack 46a9ada, adc_ch 219.50 x 103.67 um, DRC 0, LVS match)
Re-pack adc_ch (no circuit change) to the budget of the new floorplan (R2; 222 x 104 um, or the adc_h that R2 / R3 / R4 report). The DAC array (about 8.5k um2) and Cref (about 3.6-3.8k um2) are at their estimate; the overshoot is in the driver rows (3,567 um2 vs F1 391), the comparator (4,791 vs 877) and vhalf (2,813 vs 1,415), plus packing: use the L1a report's own proposals (multi-finger driver rows, the column below Cref, vhalf pitch 2.2 um instead of 3 um, cell width = 222 um) and keep the comparator symmetric. DRC 0, LVS match against AFE/layout/lvs/adc_ch.spice, all L1a keep-outs. Report the block table vs the L1a one.

### R6 (2026-11-20) to L2a (R4), then L2b: Cin 15 pF adopted, ff 85 C noise allowance 2.2 uV (Decision 50)
Status: closed (monitoring 2026-11-21: handled on branch worktree-r6-amp-cin15; amp_ch 220.25 x 284.25 um at Cin 15 pF, gate L2a PASS against the R2 budget 285 um)
Unblocks R4 (BLOCKED.md of branch worktree-r4-amp-cin15). The user accepts Cin = 15 pF with the hot-corner noise miss. Do, on top of main (merge worktree-r5-adc-repack into main first if it is not merged):
1. Merge branch worktree-r4-amp-cin15; set `.param CF1V=150f` in AFE/amp/spice/afe_params.spice; move the 20 pF amp baselines to AFE/layout/baseline/*_cin20.json and copy AFE/layout/baseline_cin15/* into AFE/layout/baseline/ (fix the `log` paths inside); remove AFE/layout/BLOCKED.md (its content goes into report L2a.md section 6).
2. Limits (ACCEPT.md and accept_limits.json together, the gate checks they agree): amplifier noise (noise_d8, 0.5-300 Hz) <= 2.0 uV at typ 27 C and ss -40 C as before; at ff 85 C <= 2.2 uV, for the schematic AND post-layout (L2b), replacing the 2.05 uV R-3 allowance for that corner. Every other limit unchanged.
3. Continue R4 at its step 2 (LVS reference with `mk_lvs_netlists.py --cin 2,61.15,61.15` or the exact grid value R4 computed, check_lvs_netlists.py) and step 3 (amp_ch re-layout, target <= 222 x 285 um; first lever the shorter Cf1 strip R4 named). The adc_ch of R5 uses all 104 um, so amp_h must stay <= 285 um unless R3 frees height.
4. Update the noise statements (AFE/adc/README.md, README.md, info.yaml if quoted): Cin 15 pF, 1.89 / 2.14 / 1.73 uV (typ / ff 85 / ss -40, Decision-8 figure), the ff 85 C miss accepted by Decision 50.
List R6 and R4 in report L2a.md section 9; run `python3 AFE/layout/scripts/gate.py L2a` until PASS; commit and push.

### R7 (2026-11-21) to L3a: close the 8-channel floorplan with the as-built cells
Status: open
Problem: the as-built cells do not fit together. afe_dig 819.84 x 101.92 um (R3: nothing below 98 um routes, GRT-0116), amp_ch 220.25 x 284.25 um (R6, built against the R2 budget 285), adc_ch 219.50 x 103.67 um (R5, budget 104, no slack). With dig_h 101.92 the channel slot loses ~11 um per row (R3 set amp_h <= 274.04): about 10.2 um per row (~22 um in total) is missing. Do NOT re-lay out amp_ch, adc_ch or afe_dig unless every floorplan lever below fails.
First: merge worktree-r3-dig and worktree-r6-amp-cin15 into main (both regenerated AFE/layout/lvs/: the second merge re-runs `mk_lvs_netlists.py` with BOTH the --dig-netlist of R3 and the --cin of R6 plus --decap-n, then check_lvs_netlists.py PASS). Expect `floorplan.py check --gds amp_ch=... adc_ch=... afe_dig=...` to FAIL on height until this item is done.
Levers, in this order, pre-approved (ACCEPT.md A-2 / A-4 / A-5 and Decision 46c), until `floorplan.py check --gds` with all three as-built cells is ALL PASS with >= 0.5 um margin in every slot:
(a) DECAP UNDER THE Cin PLATES (Decision 46c, LP test cell lp_cin_decap): move decap units out of the strap corridors into the area under the Cin pieces of each amp_ch (kept free of devices and Metal1-3 by L2a / R6; check that it still is), over a continuous vss Metal3 shield between the decap and the Cin bottom plates (the driven rec / ref / v1 side, Decision 46a). The decap there belongs to the strap that L3a can reach without crossing a 20 um keep-out; the totals of Decision 44d (>= 0.125 nF ADC-main, >= 0.1 nF ADC-DAC, 4c of floorplan.py check) must still hold, and the DAC-strap share must stay within ~150 um of its adc_ch; shrink strap_corr by what the decap row no longer needs (keep the straps, the control wires and their spacing). Prove on a test cell that Magic extracts one amp_ch Cin block + shield + decap with the right devices (flow.py lvs) before using it.
(b) Corridor trims: bias_corr 12 -> 10, strap_corr further if (a) leaves room; ring stays 26 (pins, west decap bank).
(c) WIDER, FLATTER MACRO: relocate bias_genc (108 x 110) out of the middle band (e.g. into the space freed by (a) at the east end of a strap corridor, or the east ring lane if the bias trunk allows) and re-harden afe_dig wider (up to the 948 um core width) and lower with the frozen recipe (`mk_dig_cfg.py --w/--h`); all L1d checks again, gate L1d PASS.
(d) Only if (a)-(c) fail: 10 um of height may move to amp_ch with an amp_ch re-pack, or write BLOCKED.md with the as-built numbers and the best floorplan found (R1 checkpoint; the user decides vs N = 4).
Record the final floorplan in floorplan.json / SPEC.md (floorplan.py build only), say which levers were used and their cost in report sections 6 / 7 (AFE/layout/reports/R7.md), and what L3a / L3b must verify (decap coupling into the Cin bottom plates: L3b supply / crosstalk runs; strap IR drop). Commit and push.

(An earlier R6 with extra adc_ch levers was withdrawn unused on 2026-11-20 - R5 fit without it - and its number reused for the Cin 15 pF item above; see git history 1a1c17a.)

## DRAFT for team review (2026-11-21): L2b and L1b post-layout results - NOT yet items
Written by the monitoring session for the team; nothing below is an instruction to a phase yet (no `### R<n>` heading, so gate.py and the phases ignore it).
Once the team agrees, it becomes items R8 / R9 (and the R7 correction) with `Status: open`, and one session applies them; then L3a starts.
Both phases are DRC 0 / LVS match / PEX clean and both cells WORK after layout; each misses a few limits by small margins and wrote BLOCKED.md on its branch
(worktree-l2b 12f8be4, worktree-l1b-adc-post c636acf; not merged). Full evidence: AFE/layout/BLOCKED.md, AFE/layout/reports/{L2b,L1b}.md and AFE/layout/sim/post/compare_{L2b,L1b}.md on those branches.
Proposal: accept the as-built cells, loosen the limits below, and move on to L3a (another re-layout would cost a full phase cycle each, and both cells fit their slots with < 1 um to spare).

#### Draft R8 to L2b: accept the as-built amp_ch post-layout numbers (L2b option C)
Passes: gain 59.82 / 59.84 / 59.84 dB (typ / ff 85 / ss -40), f_lo 0.24-0.28 Hz, f_hi 408-973 Hz, noise_d8 1.902 / 2.153 / 1.742 uV (limits 2.0 / 2.2 / 2.0), PM >= 76.9 deg, THD 0.04 / 0.94 / 0.05 %.
| check | post-layout | current limit | proposed |
|---|---|---|---|
| amp_pwrup err_1s_mv | 30.3 / 18.2 / 19.8 mV | <= 10 | <= 50 (ladder R-6, already pre-approved) |
| amp_reset t_1mv (os0 / os1m / os10m), amp_reset_host os10m | 1.22-1.32 x the limit | 4.5 / 4.5 / 6.5 s | x 1.5 (ladder R-7, already pre-approved) |
| amp_thd out_min_v (typ, ss -40) | 1.1803 / 1.1783 V | <= 1.17 | <= 1.19 (cause: the 0.2 dB gain loss compresses the swing) |
| amp_psrr supply_gain_50hz (typ, ff 85) | 0.636 / 0.665 | 0.38 .. 0.62 | 0.32 .. 0.68 (cause: 1-4 fF unequal vdd / vss coupling of vn / vp; ESTIMATE: board-ripple requirement still met) |
| amp_pwrup_junction err_1s_mv | 181 / 96 / 182 mV | <= 50 | not gating: junction convention = risk view of ACCEPT.md section 2; covered by host rule 6 (repeat RST_AMP when a channel leaves mid-scale +-200 LSB) and first-silicon test 4 |
Keep L2b's kit fixes (flow.py pex 1 TOhm bleeders on capacitor-only nodes; lptb.py Cin probe anchors 61.15 um).

#### Draft R9 to L1b: accept the as-built adc_ch post-layout numbers (L1b option 1)
Everything passes except linearity at three corners (cause: uneven coupling of the b6 / b7 / b8 exits to the DAC top plate; L1b already trimmed b11, 7 -> 5 FAIL).
| check | post-layout | current limit | proposed |
|---|---|---|---|
| adc_codes inl_lo_lsb ff -40 / ss 125 | 1.096 / 1.053 LSB | <= 1 | <= 1.2 |
| adc_codes inl_lo_lsb ff 85 | 3.079 LSB | <= 2.5 | <= 3.1 |
| adc_codes inl_code_lo_lsb ff 85 | 2.970 LSB | <= 2 | <= 3.0 |
| adc_steps step_2048_lsb ff 85 | 2.295 LSB | <= 2.0 | <= 2.5 (ladder Q-2, already pre-approved) |
README / Decision 43c claim becomes INL <= 1.1 LSB (typ 0.95) below 2.0 V, ff 85 C noted separately.

#### Draft correction to R7 (L3a): the cells now fit
R7 was written before the merges of R3 / R6 / R6b. On main 6a969a0: amp_ch 220.75 x 273.25 in 222 x 274.04, adc_ch 219.50 x 103.67 in 222 x 104, afe_dig 819.84 x 101.92;
`floorplan.py check --gds amp_ch=... adc_ch=... --dig-pins ...` 20 PASS, 0 FAIL. Levers (a)-(d) are not needed. Only open point: R7's ">= 0.5 um margin in every slot" (adc_ch has 0.33 um height):
proposed: accept 0.3 um, or use lever (b) bias_corr 12 -> 10 to give adc_h the room. (The paused 98 um macro attempt, worktree r3-dig98, uncommitted, would free 3.92 um but is not needed.)

#### When the team agrees
One session: merge worktree-l2b and worktree-l1b-adc-post into main, apply R8 / R9 to AFE/layout/accept_limits.json and ACCEPT.md together, remove BLOCKED.md (content into the reports, section 6), restate the claims in README.md / AFE/adc/README.md, re-run `gate.py L2b` and `gate.py L1b` to PASS, commit, push. Then L3a.
