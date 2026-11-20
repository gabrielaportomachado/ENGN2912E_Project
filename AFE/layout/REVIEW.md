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
Status: open
Re-run the frozen L1d recipe with the macro height 80 um (die 820 x 80, pins per the new floorplan.json from R2). All L1d checks again: STA at 5 corners, tap-delay limits (a) >= 21.0 ns, (b)/(c) >= 20.0 ns, max-slew / max-cap 0, KLayout DRC variant D 0, run_tb_audit.sh gls (only the 4 known assertions), LVS, regenerate the LVS top with --dig-netlist. If the routing fails at 80 um, try 85 / 90 um and report; each 10 um above 80 must come out of adc_h or amp_h (tell R5 / R4 in the report). Merge branch worktree-l1d-dig into main first if it is not merged.

### R4 (2026-11-20) to L2a (then L2b): Cin 20 pF -> 15 pF, then amp_ch to <= 222 x 285 um
Status: open
Decision 48 (circuit change approved by the user): in AFE/amp/spice/afe_params.spice set `.param CF1V=150f` (was 200f); CIN_RATIO stays 100, so Cin1 = Cin2 = 15 pF and the stage-1 gain stays 100 (60 dB channel). Nothing else in the circuit changes. Step 1, simulate BEFORE any layout (schematic, typ 27 / ff 85 / ss -40, common rule 8, the golden testbenches AFE/layout/tb/tb_amp_*.py with --netlist schematic): gain (60 +- 1 dB; if the parasitic absorbed by CF1V moves it by more than 0.3 dB, trim CF1V in 5 fF steps and say so), f_lo <= 0.5 Hz, f_hi >= 300 Hz, noise <= 2 uV (0.5-300 Hz), PM, THD, PSRR, reset recovery with the one-shot, power-up with RST_AMP 100 ms, and AFE/adc/scripts/x2_s1.py typ (amp -> ADC). Write the new numbers next to the 20 pF baselines; then REPLACE the amp baselines in AFE/layout/baseline/ with the 15 pF ones (keep the old files as *_cin20.json) so that compare.py / gate.py use them. Update the noise / f_lo statements in AFE/adc/README.md and info.yaml / README.md if they quote them. If any Decision 1 target fails: stop, BLOCKED.md (checkpoint of R1). Step 2: regenerate the LVS reference with `mk_lvs_netlists.py --cin 2,W,L` for two pieces of 7.5 pF each on the 5 nm grid (W = L chosen for capacitance, as F1 did; state it), re-run check_lvs_netlists.py. Step 3: re-run the amp_ch generator with the smaller Cin block and the full cell width 222 um (ladder A-3), target <= 222 x 285 um, DRC 0, LVS match; keep all L2a rules (summing nodes on the top plates, nothing under the plates, identical minimum-area pseudo-R devices, ABBA pair with dummies). Report the block table vs the old one.

### R5 (2026-11-20) to L1a: adc_ch re-pack to <= 222 x 104 um
Status: closed (monitoring 2026-11-20: handled on branch worktree-r5-adc-repack 46a9ada, adc_ch 219.50 x 103.67 um, DRC 0, LVS match)
Re-pack adc_ch (no circuit change) to the budget of the new floorplan (R2; 222 x 104 um, or the adc_h that R2 / R3 / R4 report). The DAC array (about 8.5k um2) and Cref (about 3.6-3.8k um2) are at their estimate; the overshoot is in the driver rows (3,567 um2 vs F1 391), the comparator (4,791 vs 877) and vhalf (2,813 vs 1,415), plus packing: use the L1a report's own proposals (multi-finger driver rows, the column below Cref, vhalf pitch 2.2 um instead of 3 um, cell width = 222 um) and keep the comparator symmetric. DRC 0, LVS match against AFE/layout/lvs/adc_ch.spice, all L1a keep-outs. Report the block table vs the L1a one.

### R6 (2026-11-20) to L1a (R5): extra pre-approved levers for the adc_ch re-pack
Status: closed (monitoring 2026-11-20: NOT NEEDED, R5 fit its slot without these levers; R5 branched before R6 existed. Do not apply.)
Layout-only, no circuit change; use them in this order, as far as needed, and list which ones you used in report sections 6 / 7:
(a) HEIGHT FROM THE AMPLIFIER: the channel slot height is fixed (397 um = amp_h + 8 + adc_h), but the split is not: once R4 has its as-built amp_ch height, set adc_h = 389 - amp_h (amp_ch rounded up to 0.25 um) with `floorplan.py build --set adc_h=<value>` (this replaces R2's "up to 10 um"; the outline stays 1000 x 1000 um), then `floorplan.py check` all PASS. If R3 ends below 80 um, the gain (half per row) also goes to adc_h. If R4 is not finished when R5 needs the number, re-pack to 222 x 104 and take the extra height later only if needed.
(b) DEVICES UNDER THE GROUNDED PLATES: the bottom plates of Cref (vrefs Xc: out / vss) and of the vhalf 1 pF capacitor (vhalf Xc: out / vss) are vss, i.e. grounded shields. NON-matching devices may be placed under them: the DAC bottom-plate drivers and reset switches, the Cref switch, the inverter, their Metal1-3 wiring. Conditions: the bottom plate covers each such device and wire with >= 2 um overlap on every side; no Via3 onto the bottom plate (MIMTM.10, contact from above or by a Metal4 wire); NOT under the plates: the comparator, the vhalf resistor pair, the sampling switch, the DAC array.
(c) KEEP-OUT BAND: the 20 um band between the driver rows and the DAC top plates / Cref may shrink to >= 8 um where a continuous vss shield separates the digital wires from the sensitive node (a vss Metal4 plane over the digital wires, or a vss guard ring plus a vss Metal4 / Metal5 cover), with no digital wire on Metal4 / Metal5 there. L1b must then report from the extraction the coupling capacitance from every dac_g*, rst_sw, tg_on and cmp_clk net to t, m and the Cref top plate (out), next to the same numbers of the 20 um layout if available; the ACCEPT.md ladder decides.
(d) Only if (a)-(c) are not enough: say so in the report with the as-built size (checkpoint of R1).

### R7 (2026-11-20) to L2a (R4), then L2b: Cin 15 pF adopted, ff 85 C noise allowance 2.2 uV (Decision 50)
Status: open
Unblocks R4 (BLOCKED.md of branch worktree-r4-amp-cin15). The user accepts Cin = 15 pF with the hot-corner noise miss. Do, on top of main (merge worktree-r5-adc-repack into main first if it is not merged):
1. Merge branch worktree-r4-amp-cin15; set `.param CF1V=150f` in AFE/amp/spice/afe_params.spice; move the 20 pF amp baselines to AFE/layout/baseline/*_cin20.json and copy AFE/layout/baseline_cin15/* into AFE/layout/baseline/ (fix the `log` paths inside); remove AFE/layout/BLOCKED.md (its content goes into report L2a.md section 6).
2. Limits (ACCEPT.md and accept_limits.json together, the gate checks they agree): amplifier noise (noise_d8, 0.5-300 Hz) <= 2.0 uV at typ 27 C and ss -40 C as before; at ff 85 C <= 2.2 uV, for the schematic AND post-layout (L2b), replacing the 2.05 uV R-3 allowance for that corner. Every other limit unchanged.
3. Continue R4 at its step 2 (LVS reference with `mk_lvs_netlists.py --cin 2,61.15,61.15` or the exact grid value R4 computed, check_lvs_netlists.py) and step 3 (amp_ch re-layout, target <= 222 x 285 um; first lever the shorter Cf1 strip R4 named). The adc_ch of R5 uses all 104 um, so amp_h must stay <= 285 um unless R3 frees height.
4. Update the noise statements (AFE/adc/README.md, README.md, info.yaml if quoted): Cin 15 pF, 1.89 / 2.14 / 1.73 uV (typ / ff 85 / ss -40, Decision-8 figure), the ff 85 C miss accepted by Decision 50.
List R7 and R4 in report L2a.md section 9; run `python3 AFE/layout/scripts/gate.py L2a` until PASS; commit and push.
