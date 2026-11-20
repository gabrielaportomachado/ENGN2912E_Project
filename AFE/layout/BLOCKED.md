# BLOCKED: phase L2a (rework item R4 of AFE/layout/REVIEW.md), 2026-11-20

Written by the R4 session (Claude Sonnet 5.5) under AFE/layout/REVIEW.md R1 checkpoint ("if R4's simulations fail a Decision 1 target, write BLOCKED.md with the numbers and stop that line").
R4 step 1 (simulations before layout) failed ONE Decision 1 target; no layout was started. R2 (floorplan) is merged; R3 (afe_dig) and R5 (adc_ch) are independent of this and may continue.

## Failed gate line
`python3 AFE/layout/tb/compare.py --phase L2b --selftest` on the 15 pF baseline (CF1V = 150f):
```
FAIL amp_noise ff85 noise_d8_post_uv: baseline -, post 2.1392, limit <= 2   (Decisions 1, 4, 8: <= 2 uV rms in 0.5-300 Hz ...)
RESULT compare L2b: FAIL  (92 PASS, 0 WARN, 1 FAIL, 0 missing)
```
Every other metric passes at all three corners (table below). ACCEPT.md ladder R-3 pre-approves up to 2.05 uV at ff 85 C only, and only as a degradation caused by LAYOUT parasitics; the schematic itself is already at 2.139 uV, so no ladder entry applies (and the post-layout parasitics would still be added on top).

## What was done (R4 step 1, all schematic, common rule 8, golden testbenches, `--netlist schematic`)
- `AFE/amp/spice/afe_params.spice`: `.param CF1V=150f` (was 200f), CIN_RATIO = 100 unchanged: Cin1 = Cin2 = 15 pF. Gain moved by 0.00 dB, so no CF1V trim (the 0.3 dB / 5 fF rule) was needed.
- `bash`-equivalent of `AFE/layout/tb/run_baselines.sh amp` without bias_startup / tgate (they do not depend on Cin): tb_amp_{ac,noise,psrr,thd,loop,pwrup,reset} `--corner all`, the same with `--junction` (not loop), tb_amp_reset `--os 10m,100m --host-rst 0.1` with and without `--junction`.
- Amp -> ADC: `X2_SUFFIX=_cin15 X2_LOG_PREFIX=x2r4 python3 AFE/adc/scripts/x2_s1.py typ` (see "amp -> ADC" below).
- The 15 pF results are kept in **AFE/layout/baseline_cin15/** (same file names as AFE/layout/baseline/amp_*.json, logs included; the `log` paths inside point there). **AFE/layout/baseline/ and afe_params.spice are NOT changed (still 20 pF / 200f)** so that main stays consistent with the committed 20 pF layout and with L2b / L1b / L3a gates until you decide. To adopt 15 pF: `.param CF1V=150f`, copy AFE/layout/baseline_cin15/amp_* over AFE/layout/baseline/ after saving the 20 pF ones as *_cin20.json (R4 text).

## Results: 20 pF baseline -> 15 pF (design convention unless noted; typ 27 C / ff 85 C / ss -40 C)
| metric | limit | 20 pF | 15 pF | |
|---|---|---|---|---|
| gain at 12.25 Hz [dB] | 60 +- 1 | 60.06 / 60.06 / 60.04 | 60.05 / 60.06 / 60.04 | PASS |
| f_lo [Hz] | <= 0.5 | 0.202 / 0.226 / 0.237 | 0.246 / 0.281 / 0.288 | PASS |
| f_hi [Hz] | >= 300 | 653 / 998 / 422 | 653 / 998 / 422 | PASS |
| **noise, Decision-8 figure noise_d8 [uV rms 0.5-300 Hz]** | **<= 2.0** | 1.668 / 1.847 / 1.540 | **1.890 / 2.139 / 1.732** | **FAIL at ff 85** (+13 / +16 / +12.5 %) |
| noise, real pseudo-R devices (report) [uV] | - | 1.418 / 1.580 / 1.322 | 1.495 / 1.732 / 1.386 | report |
| stage-1 loop PM [deg] | >= 60 | 79.2 / 76.4 / 81.1 | 79.6 / 76.9 / 81.4 | PASS |
| THD at +-0.5 mV, 12.25 Hz [%] | typ / ss small, ff 85 accepted (Decision 28) | 0.035 / 2.63 / 0.046 | 0.042 / 2.40 / 0.057 | PASS (ff 85 = the accepted miss, slightly better) |
| supply gain 50 Hz | - | 0.571 / 0.579 / 0.566 | 0.572 / 0.580 / 0.567 | PASS |
| power-up error after 1 s [mV] (RST_AMP 100 ms) | <= 10 | 0.27 / 0.07 / 0.62 | 0.24 / 0.10 / 0.62 | PASS |
| reset recovery, t_fs [ms] / host-RST rule | as baseline | 3.11 / 1.62 / 5.83 | 2.97 / 1.72 / 5.79 | PASS |
Junction convention (same files `*_junction.json`): same picture (noise 1.510 / 1.763 / 1.404 uV real devices; gain, f_hi, PM unchanged). Full old-vs-new listing of every value: AFE/layout/baseline_cin15/ against `git show HEAD:AFE/layout/baseline/<file>`.

Why the noise rises more than the "few %" ESTIMATED in Decision 48: noise_d8 behaves as noise^2 = b / Cin with a ~ 0 (fit through the two points at ff 85: b = 69.8 uV^2 pF), i.e. noise ~ 1 / sqrt(Cin): 20 -> 15 pF is +15.5 % at ff 85 (measured +15.8 %), and the corner f_lo rises by 22 % with Cf1 so the 0.5 Hz edge of the band takes more resistor noise.
ESTIMATE from that fit (to be confirmed by simulation if you choose it): noise_d8(ff 85) = 2.0 uV needs Cin >= 17.1 pF, 2.05 uV (the R-3 allowance) Cin >= 16.3 pF; with 2 - 3 % for layout parasitics: Cin about 17.5 - 18 pF.

## Amp -> ADC (x2_s1.py typ, 15 pF)
Run completed (168 s, log AFE/adc/sim/x2_s1_typ_cin15.log): amp -> ADC works at 15 pF: end-to-end gain at 23.4 Hz 999.28 V/V (59.994 dB, -0.07 %), amplifier alone 1000.70 V/V, amp->ADC minus ADC alone T mean +0.072 LSB (max +0.572), below 2.05 V +0.040 LSB; kick spike 173..445 mV; |INL| below 2.05 V 0.75 LSB PASS, whole range 2.78 LSB FAIL (the known top-of-range effect of Decision 43; the S1 typ verdict recorded earlier in AFE/adc/sim/x2_s1_summary.log is also FAIL, 2.14 LSB, a differently configured run, so the two are NOT a like-for-like comparison and the 20 pF case was not re-run). Noise at the ADC input is the failing item, not the transfer.

## Area consequence (ESTIMATE from `mk_amp_ch.py plan=1` with a parametrised Cin block; no layout was generated)
The 2 x 2 Cin block shrinks from 164.7 x 167.3 um (4 x 70.65 um pieces) to 145.7 x 148.3 um (4 x 61.15 um pieces, 7.4995 pF each by the PDK formula, Cf1 8.45 um = 150.1 fF, ratio 99.9). With the committed lay=3 packing this is -19 um: amp_ch about 218.75 x 290 um (+1.8 % over the 285 um budget, inside the 3 % checkpoint; a shorter Cf1 strip under the Cin block, now 24 um, would be the first lever: ESTIMATE, not tried). At Cin = 17.5 pF (pieces about 66 um) the saving is only about -9 um: about 300 um, +5 % over budget: that needs a real re-pack (finger width 25 um, ADC / amp split via adc_h, which R2 allows up to 10 um) and is beyond one more attempt without the decision below.

## The decision that unblocks it (one question)
Which Cin do you want to carry into the layout?
1. **Keep 15 pF and accept the ff 85 noise miss (2.139 uV, +7 % over 2.0; typ 1.89 / ss -40 1.73 pass).** Extend the ff 85 allowance of ladder R-3 from 2.05 to about 2.2 uV (write it in REVIEW.md; post-layout parasitics add 1 - 3 %). Cost: the hot-corner noise spec of Decision 1 is missed by about 7 % (ENOB effect: see the x2_s1 line above); area closes with a small re-pack (about 290 -> 285 um). R4 steps 2 - 3 then run as written.
2. **Cin about 17.5 pF (CF1V = 175f, Cin = 17.5 pF, CIN_RATIO 100)**: meets 2.0 uV at all corners (ESTIMATE 1.97 uV at ff 85). Cost: amp_ch about 300 um tall (+5 %): needs a second re-pack session, a shift of up to 10 um from adc_h (R5 must then fit adc_ch in 94 um instead of 104), and the 5 fF-step CF1V simulations again (about 15 min).
3. **Keep Cin = 20 pF (no circuit change) and go to N = 4 channels** (ladder A-6, -0.33 mm2): no noise change; 4 channels instead of 8.
What can continue meanwhile: R3 (afe_dig 820 x 80) and R5 (adc_ch re-pack) are independent of R4; L2b / L1b / L3a wait for R4 + R5 (REVIEW.md R1).

## Evidence files
AFE/layout/baseline_cin15/ (all 15 pF results), AFE/layout/baseline/*.json (20 pF, unchanged), AFE/layout/reports/L2a.md section 9, AFE/adc/sim/x2_s1_typ_cin15.log (+ .npz).
