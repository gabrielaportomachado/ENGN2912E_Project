# LP step 6: native-Vt fallback of the follower (audit M7)

2026-11-20, fork of the LP session (Claude Fable 5.2 / max). Corners typ 27 / ff 85 / ss -40 C, 3.3 V unless stated. Every number is from a log named in the text
(`AFE/amp/sim/lp_rvt_*.log`, `AFE/adc/sim/lp_rvt_x2_s1_*.log`); ESTIMATE = not simulated. The original netlist was run by the same scripts in the same session.
Machine-readable: `AFE/amp/sim/lp_rvt_result.json`. No design netlist, RTL, testbench or NOTES file was edited; nothing was committed.

## 1. Verdict

**WORKS, with no loss.** A drop-in variant without `nfet_06v0_nvt` meets every amplifier target at the three corners (42 scripted checks, 0 failed, `lp_rvt_report.log`):
the follower becomes a regular `nfet_03v3`, 8 x 10u/1u, in an isolated p-well (LVPWELL in DNWELL) with its bulk on its source. Files `AFE/amp/spice/ota2_rvt.spice` + `afe_chc_rvt.spice`.

Needs your attention:
1. **The variant needs the deep n-well** instead of the native-Vt layer. The organizer table says "Deep nwell transistor option: It is available" (`AFE/review/sim/organizer/Integration_README.md`, under a "2025 Chipathon" heading); it does not mention native Vt. Ask both in one question. Drawn without a real DNWELL the p-well (tied to `out`) would be shorted to the substrate.
2. **Side effect: the accepted Decision-28 miss disappears.** The native device clips the bottom at ff (Vgs -0.23 V); the variant has Vgs +0.46 V. THD at +-0.5 mV, ff 85: 2.505 % -> 0.078 %; output bottom 1.220 -> 1.179 V (= full swing around the drifted mean); X2 S1 ff 85: amplifier output 1.213..2.153 -> 1.149..2.153 V, sine-fit residual of the codes 8.98 -> 0.87 LSB rms, DC-level gain -3.50 % -> +0.07 %. DC swing passes at all 9 PVT (the original fails at ff 27 and ff 85). Adopting the variant regardless of the organizer's answer is therefore an option; NOT applied, your decision.
3. **f_hi rises 5.6 / 6.7 / 4.4 %** (653 / 998 / 422 -> 690 / 1065 / 441 Hz): the follower gate is bootstrapped (bulk = source), so o2 carries less capacitance (GBW 7.33 -> 7.75 kHz). Target >= 300 Hz met; in-band noise unchanged; noise to 2 kHz +0.4 %; alias attenuation at 3.7 kHz about 0.5 dB lower (ESTIMATE, first-order roll-off; Decision 23 risk). Cc2 was not retuned.
4. **Settling metric trap (for the golden testbenches):** the D5 number "L - U at the end of T_ACQ" contains a DC-solve difference between the two amplifier copies of up to 0.15 LSB at reltol 1e-4 (it vanishes at reltol 1e-6, vntol 1e-9, abstol 1e-12; `lp_rvt_settle.log` NOTE, `lp_rvt_settle_tight.log`). Use "end minus before" or the tighter tolerances for an acceptance limit. abstol 1e-15 aborts at the first switching event, as X2 found.
5. `AFE/adc/scripts/x2lib.py` got the additive options `X2_AMP_INC` / `X2_AMP_SUBCKT` (default output byte-identical to the previous file for 5 corners: checked).
6. A third netlist was added beyond the two requested: `ota2_rvt_nodnw.spice`, the second fallback if neither native Vt nor DNWELL is offered (section 2, row B).

## 2. Candidates

Screen = stage-2 OTA + follower + sink on the real bias, inverting gain -1 loop of two IDEAL 100 MOhm resistors, DC sweep: output range in which |d out / d in| >= 0.99 (`lp_rvt_screen.log`, 31 candidates; `scripts/lp_rvt_screen.py`). Needed 1.15 .. 2.15 V. "Input left" = (top - 1.65 V) / 1000 where the top is short.

| candidate | follows [V] typ / ff 85 / ss -40 | margin to 2.15 V [mV] | margin to 1.15 V [mV] | kept / dropped |
|---|---|---|---|---|
| original, nfet_06v0_nvt 10u/2u, bulk vss | 0.90-2.97 / 1.29-3.15 / 0.50-2.76 | +818 / +999 / +612 | +252 / **-138** / +651 | reference; bottom fails at ff 85 (Decision 28) |
| **A: nfet_03v3 8 x 10u/1u, isolated p-well, bulk = source** | 0.27-2.48 / 0.57-2.59 / 0.10-2.34 | +328 / +443 / +192 | +877 / +582 / +1047 | **CHOSEN** (`ota2_rvt.spice`) |
| A: same device 10u/2u (the original W / L) | 0.13-2.33 / 0.39-2.41 / 0.10-2.23 | +183 / +263 / +82 | >= +762 | works, but only 82 mV at ss -40 and fails at VDD 3.0 V ss -40 (-68 mV) |
| A: 4 x 10u/1u; 10 x 10u/0.5u; 40u/0.28u | - | ss -40: +162; +207; +282 | >= +422 | work; 4 x: 17 mV left at 3.0 V; 0.5u / 0.28u: shorter than needed |
| B: nfet_03v3 10u/2u, bulk vss (the A4a follower) | 0.10-1.80 / 0.30-1.88 / 0.10-1.70 | -352 / -271 / -452 | > +850 | dropped: input left +148 / +228 / +47 uV of +500 |
| B: 100u/0.5u, bulk vss (weak inversion); 4 x 100u/0.5u | 0.24-2.01 / 0.48-2.13 / 0.10-1.87 | -142 / -21 / -282; -102 / +29 / -247 | > +620 | dropped: input left +358 / +478 / +217 uV; 4x the width buys 40 mV |
| **B: nfet_03v3 10 x 10u/0.28u (minimum L), bulk vss, no DNWELL** | 0.40-2.32 / 0.67-2.44 / 0.11-2.18 | +168 / +289 / **+32** | +752 / +482 / +1036 | **RUNNER-UP** (`ota2_rvt_nodnw.spice`): passes, thin; L 0.30u fails at ss -40 (-23 mV), i.e. 55 mV per 0.02 um of L; fails at ss -40 for VDD <= 3.15 V |
| C: nfet_05v0 40u/0.6u; nfet_06v0 40u/0.7u, bulk vss | 0.22-1.95 / 0.47-2.08 / 0.10-1.79; 0.18-1.86 / 0.42-1.97 / 0.10-1.73 | -197 / -71 / -357; -287 / -176 / -417 | > +670 | dropped: higher Vt than the 3.3 V device |
| C: nfet_05v0 40u/0.6u, isolated p-well | 0.29-2.45 / 0.62-2.59 / 0.10-2.28 | +298 / +443 / +132 | > +520 | works, no gain over A (same DNWELL, thicker oxide) |
| D: PMOS follower / extra buffer | - | - | - | dropped without a netlist: o2 cannot go below the pair's tail (o2 >= 0.90 / 1.02 / 0.77 V at the original's lower limit, screen log), a PMOS follower adds Vsg >= about 0.7 V, so the output bottom would be >= 1.6 V (ESTIMATE); it needs a PMOS-input stage-2 OTA and a PMOS bias = a redesign |
| E: VOUT_CM 1.65 -> 1.15 V with the plain 10u/2u follower | 0.02-1.79 / 0.05-1.88 / 0.02-1.69 (needed 0.65-1.65) | +143 / +229 / +43 to 1.65 V | > +590 to 0.65 V | documented last resort (`lp_rvt_screen_vocm1p15.log`, IDEAL 1.15 V reference): new vcm_out / vg2 taps in bias_genc (and vcm_in, or the supply gain goes back to about 1 V/V, A4b), ADC centred at code 1427, the ADC was never verified at 0.65-1.15 V, README checks change |

Sizing of A (rule 10): L = 1u (not at minimum length), W = 8 x 10u = the finger width of the original: gm 116 / 159 / 90 uS (original 100 / 147 / 72), top margin 192 mV at ss -40 C and still +42 mV at VDD 3.0 V (`lp_rvt_screen_vdd.log`: variant +178 / +293 / +42 mV at 3.0 V, +473 / +583 / +337 mV at 3.6 V; the original's ff 85 bottom fails at every VDD). 9 PVT at 3.3 V (`lp_rvt_screen_pvt9.log`): variant top margin 192-443 mV, bottom margin 582-1047 mV, all PASS.

## 3. The chosen variant

Diff (`lp_rvt_report.log` section 1; one device line, 10 / 10 non-comment lines otherwise identical; `afe_chc_rvt.spice` has the device lines of `afe_chc.spice`, checked by script):
```
- Xmf vdd o2 out vss nfet_06v0_nvt L={OTA2_LF} W={OTA2_WF} nf=1 ... m={1}      (10u/2u, bulk vss)
+ Xmf vdd o2 out out nfet_03v3     L=1u        W=10u       nf=1 ... m={8}      (8 x 10u/1u, bulk = source)
```
Same subckt names (`ota2`, `afe_chc`) and pins, same parameter files, bias_genc untouched. Use: include `ota2_rvt.spice` instead of `ota2.spice` and `afe_chc_rvt.spice` instead of `afe_chc.spice`; never both. No testbench or script edit is needed (the existing testbenches ran unchanged with the two paths swapped).

Layout consequence (amplifier cell of L2a, one device): replace the follower by 8 fingers of 10u/1u `nfet_03v3` in an LVPWELL inside a DNWELL; p-well tap ring -> `out`, an N+ tap in the DNWELL -> `vdd`, P+ ring around the DNWELL -> `vss`. Pins of `amp_ch` unchanged. Drawn with the PDK pcell (`nfet`, volt 3.3V, nf 8, deepnwell = 1, pcmpgr = 1, bulk "Guard Ring"; `scripts/lp_rvt_dnw_cell.sh` -> `lp_rvt_dnw_cell.log`):
27.00 x 25.14 um = 679 um2 with both rings, against 7.34 x 14.20 um = 104 um2 for the native device with its ring: **+575 um2 per channel** (0.9 % of the 66,736 um2 channel estimate of `f1_area.log`). Magic extracts 8 x `nfet_03v3 w=10u l=1u` with a bulk net of its own (the LVPWELL), so bulk = source is LVS-able. KLayout DRC variant D: no well / diffusion / poly / implant violation; 286 x CO.6 only, because the pcell draws its two ring contacts without Metal1 (the layout adds the Metal1 rings) and it draws NO N+ tap for the DNWELL (the layout adds one in the 2.5 um LPW.3 band). The pcell library needs the environment variable `USER` in this container. Rules to keep: DN.1 1.7 um, LPW.3 2.5 um, LPW.11 1.5 um, DNWELL to other n-wells 3.1 um.
Tech-file evidence that the device stays `nfet_03v3`: Magic `gf180mcuD.tech` line 4086 `device msubcircuit nfet_03v3 nfet ndiff,ndc ndiff,ndc allpsub` with line 254 `allpsub = space/w,pwell,pbase` and line 3304 `substrate ... -dnwell,isosub`; KLayout `mos_extraction.lvs` lines 111-119 "3.3V NMOS transistor inside DNWELL as regular, non dw device", bulk = `lvpwell_con` (the `_dn` name only with `consider_dn_dw_features`, default false).

LVS consequence: `AFE/layout/scripts/mk_lvs_netlists.py` needs one switch that substitutes two entries of `SIM_FILES`: `AFE/amp/spice/ota2.spice` -> `AFE/amp/spice/ota2_rvt.spice` and `AFE/amp/spice/afe_chc.spice` -> `AFE/amp/spice/afe_chc_rvt.spice` (second fallback: only `ota2.spice` -> `ota2_rvt_nodnw.spice`). Tested without editing the script (loaded in memory, output to /tmp; `scripts/lp_rvt_lvs_check.py` -> `lp_rvt_lvs_check.log`, PASS): the reference changes in exactly one device line, in `afe_chc.spice` and in the copy inside `dbs_afe_top.spice`; `adc_ch` and `bias_genc` are unchanged:
```
- Xs2_xota2_xmf vdd xs2_xota2_o2 out vss nfet_06v0_nvt w=10u l=2u
+ Xs2_xota2_xmf vdd xs2_xota2_o2 out out nfet_03v3 w=10u l=1u m=8
```
`AFE/review/scripts/xcheck.py` reads the same two files and needs the same substitution. The LVPWELL / DNWELL junction (out to vdd, reverse biased) is a parasitic, not a netlist device; as a what-if (`diode_pw2dw`, 400 um2 / 80 um, ESTIMATE of the well, 172 fF at zero bias) it changes nothing in op / ac / noise / loop / PSRR / THD (`lp_rvt_tables.log`, `lp_rvt_swing.log`, columns `rvt+dio`).

## 4. Results, original vs variant

| quantity | target | original | variant `rvt` | runner-up (no deep n-well) | log (AFE/amp/sim) |
|---|---|---|---|---|---|
| mid-band gain [dB] | 60 +- 1 | 60.056 / 60.060 / 60.041 | 60.062 / 60.071 / 60.046 | 60.049 / 60.059 / 60.030 | lp_rvt_tables.log |
| f_lo [Hz] | <= 0.5 | 0.202 / 0.226 / 0.237 | 0.203 / 0.226 / 0.238 | 0.202 / 0.226 / 0.237 | lp_rvt_tables.log |
| f_hi [Hz] | >= 300 | 653.5 / 997.6 / 422.0 | 689.9 / 1064.6 / 440.7 | 601.9 / 925.3 / 386.3 | lp_rvt_tables.log |
| noise 0.5-300 Hz, typical flicker [uV] | <= 2 | 1.668 / 1.847 / 1.540 | 1.668 / 1.847 / 1.541 | 1.666 / 1.846 / 1.537 | lp_rvt_tables.log |
| noise, fnoicor = 1 [uV] | report | 4.720 / 4.933 / 4.393 | 4.722 / 4.935 / 4.397 | 4.715 / 4.931 / 4.384 | lp_rvt_tables.log |
| supply current, bias + channel [uA] | = original | 74.43 / 118.81 / 47.13 | 74.43 / 118.81 / 47.13 | 74.43 / 118.81 / 47.13 | lp_rvt_tables.log |
| output DC error [mV] | - | 0.805 / 1.112 / 0.425 | 0.382 / 0.493 / -0.141 | 0.155 / 0.434 / -0.169 | lp_rvt_tables.log |
| stage-2 OTA output o2 [V] | - | 1.681 / 1.417 / 1.946 | 2.262 / 2.112 / 2.430 | 2.332 / 2.159 / 2.520 | lp_rvt_tables.log |
| follower Vgs [V] | - | 0.030 / -0.234 / 0.296 | 0.612 / 0.462 / 0.780 | 0.682 / 0.509 / 0.871 | lp_rvt_tables.log |
| follower gm [uS] | - | 100.4 / 147.5 / 72.1 | 115.8 / 158.6 / 89.5 | 138.6 / 189.0 / 108.4 | lp_rvt_tables.log |
| stage-2 OTA + follower: PM at beta = 1 [deg] | >= 60 | 87.7 / 87.1 / 88.3 | 87.6 / 86.9 / 88.2 | 88.0 / 87.4 / 88.5 | lp_rvt_tables.log |
| stage-2: PM at the real beta 0.294 / 3.294 [deg] | >= 60 | 90.5 / 90.4 / 90.6 | 90.4 / 90.3 / 90.6 | 90.5 / 90.4 / 90.7 | lp_rvt_tables.log |
| stage-1 loop PM, real stage 2 as load [deg] | >= 60 | 79.2 / 76.4 / 81.1 | 79.2 / 76.4 / 81.1 | 79.2 / 76.4 / 81.1 | lp_rvt_tables.log |
| supply -> output gain at 50 Hz [V/V] | ideal 0.5 | 0.5710 / 0.5786 / 0.5658 | 0.5720 / 0.5797 / 0.5669 | 0.5713 / 0.5792 / 0.5655 | lp_rvt_tables.log |
| DC swing: follows down to / up to [V] | 1.15 / 2.15 | 0.898 / 1.288 / 0.498; 2.968 / 3.148 / 2.762 | 0.273 / 0.568 / 0.103; 2.478 / 2.593 / 2.342 | 0.398 / 0.668 / 0.113; 2.318 / 2.438 / 2.182 | lp_rvt_screen.log |
| +-0.5 mV, 12.25 Hz: THD [%] | D28 accepts ff 85 | 0.034 / 2.505 / 0.044 | 0.035 / 0.078 / 0.050 | 0.044 / 0.074 / 0.100 | lp_rvt_swing.log |
| +-0.5 mV, 12.25 Hz: out max; out min [V] | 2.15; 1.15 | 2.154 / 2.186 / 2.152; 1.148 / 1.220 / 1.148 | 2.154 / 2.186 / 2.152; 1.147 / 1.179 / 1.147 | 2.152 / 2.186 / 2.150; 1.148 / 1.180 / 1.149 | lp_rvt_swing.log |
| +-0.6 mV, 12.25 Hz: THD [%] | margin | 0.038 / 6.126 / 0.048 | 0.041 / 0.098 / 0.068 | 0.068 / 0.096 / 0.422 | lp_rvt_swing.log |
| +-0.5 mV, 300 Hz: THD [%] | - | 0.043 / 0.406 / 0.165 | 0.050 / 0.022 / 0.162 | 0.128 / 0.083 / 0.222 | lp_rvt_swing.log |
| slew, +-0.5 mV step, slower direction [V/s] | >= 942 | 1936 / 2980 / 1221 | 2042 / 3178 / 1276 | 1782 / 2769 / 1118 | lp_rvt_slew.log |
| ADC load, IDEAL 17 pF behind 1 kOhm, no reset, 245 us [LSB] | <= 0.5 | 0.180 / 0.102 / 0.264 | 0.183 / 0.102 / 0.263 | 0.172 / 0.101 / 0.242 | lp_rvt_adc245.log |
| REAL TG + split DAC (D5 method, 19 cases): what the kick leaves at the end of T_ACQ [LSB] | <= 0.5 | 0.090 / 0.089 / 0.075 | 0.022 / 0.010 / 0.026 | 0.005 / 0.006 / 0.005 | lp_rvt_settle.log |
| same, raw L - U at the end (the D5 number; attention 4) [LSB] | <= 0.5 | 0.083 / 0.101 / 0.067 | 0.015 / 0.156 / 0.043 | 0.006 / 0.009 / 0.010 | lp_rvt_settle.log |
| same, raw, 100x tighter tolerances, 4 cases [LSB] | <= 0.5 | 0.086 / 0.094 / 0.064 | 0.023 / 0.011 / 0.026 | n/a | lp_rvt_settle_tight.log |
| kick spike on the output, L - U peak [mV] | report | 278 / 292 / 254 | 207 / 222 / 200 | 192 / 205 / 210 | lp_rvt_settle.log |
| reset recovery, 10 mV step, ideal 3 ms pulse: time to within 1 mV [s] | as original | 4.97 / 4.48 / 4.14 | 5.07 / 4.55 / 3.79 | 5.12 / 4.03 / 4.29 | lp_rvt_rec.log |
| power-up from 0 V + RST_AMP 100 ms at 3 s: final error [mV]; time to within 10 mV [s] | within 10 mV | 0.64 / 0.99 / 0.21; 0 / 0 / 0 | 0.05 / 0.30 / -0.37; 0 / 0 / 0.26 | n/a | lp_rvt_pur.log |

Reproduction of the old logs by the original in this session: THD 0.034 / 2.505 / 0.044 % (a4c_thd.log 0.040 / 2.527 / 0.051; here abstol 1e-12), adc245 0.180 / 0.102 / 0.264 LSB (a4b_adc245.log 0.178 / 0.102 / 0.260), real-DAC settle 0.083 / 0.101 / 0.067 LSB (d5_settle.log 0.086 / 0.114 / 0.070), slew 1949 / 3007 / 1231 V/s (A4b 1937 / 2985 / 1227), supply 74.43 / 118.81 / 47.13 uA (F1). The 68.86 / 111.01 / 43.07 uA of the directive is the channel alone; the follower current is unchanged (5.214 / 8.412 / 3.260 uA).

X2 S1, transistor-level amplifier -> ADC, closed loop, `AFE/adc/scripts/x2_s1.py` unchanged, full set (9 levels + 8 sine points, 3 frames) at all three corners, X2_NCAL = 12 calibration inputs (X2 used 24), both netlists (`AFE/adc/sim/lp_rvt_x2_s1_report.log`, driver `AFE/amp/scripts/lp_rvt_x2.py`):

| corner | netlist | code offset [LSB] | INL beyond the offset, below 2.05 V [LSB] | whole range [LSB] | amplifier -> ADC minus ADC alone [LSB] | kick spike at the resume [mV] | sine gain of the codes [dB]; residual [LSB rms] | amplifier output [V] |
|---|---|---|---|---|---|---|---|---|
| typ | original | -30.22 | 0.76 PASS | 2.94 | -0.013 (-0.072..+0.024) | 172..515 | 60.006; 0.67 | 1.1492..2.1522 |
| typ | variant | -30.27 | 0.54 PASS | 2.44 | -0.012 (-0.068..+0.031) | 120..340 | 60.013; 0.64 | 1.1482..2.1517 |
| typ | second fallback | -30.35 | 0.68 PASS | 2.07 | -0.012 (-0.067..+0.032) | 126..277 | 59.998; 0.59 | 1.1489..2.1506 |
| ff 85 | original | -40.37 | 1.99 FAIL (ADC, Decision 43c) | 4.82 | -0.011 (-0.076..+0.042) | 106..481 | 59.862; 8.98 | 1.2133..2.1529 |
| ff 85 | variant | -40.47 | 2.00 FAIL (ADC, Decision 43c) | 4.40 | -0.012 (-0.078..+0.044) | 84..319 | 60.004; 0.87 | 1.1486..2.1526 |
| ss -40 | original | -22.02 | 0.30 PASS | 0.85 | -0.002 (-0.027..+0.052) | 104..407 | 59.990; 0.38 | 1.1488..2.1502 |
| ss -40 | variant | -22.05 | 0.44 PASS | 0.91 | -0.001 (-0.030..+0.056) | 83..279 | 59.993; 0.44 | 1.1486..2.1502 |

The INL numbers are set by the ADC (sampling + DAC side identical for both netlists, e.g. -0.05..+0.26 LSB typ); the code-based part moves with where the 34 inputs fall inside a code. The amplifier adds <= 0.08 LSB in both. 0 unresolved comparator decisions, 1-3 passes per run.

## 5. Proposed ACCEPT.md paragraph

**Native-Vt fallback (M7), pre-approved swap.**
- Trigger: (a) the organizer answers that `nfet_06v0_nvt` / the native-Vt layer is not offered, or a precheck or DRC deck of the organizer rejects it; or (b) no answer on native Vt has arrived when L2b starts. In case (b) the swap is the default, because the organizer's process table lists the deep n-well as available and does not list native Vt (`AFE/review/sim/organizer/Integration_README.md`). If the organizer confirms native Vt, keep the original.
- Swap: use `AFE/amp/spice/ota2_rvt.spice` and `AFE/amp/spice/afe_chc_rvt.spice` wherever `ota2.spice` / `afe_chc.spice` are named (simulation include lists; `X2_AMP_INC` of x2lib.py; the `SIM_FILES` substitution of mk_lvs_netlists.py, then regenerate `AFE/layout/lvs/`). In the amplifier cell replace the follower by `nfet_03v3`, 8 fingers x 10 um, L 1 um, in LVPWELL inside DNWELL: p-well tap -> `out`, DNWELL N+ tap -> `vdd`, outer P+ ring -> `vss`, Metal1 on every ring contact; budget 27 x 25 um (+575 um2 per channel). Nothing else changes (pins, bias_genc, ADC, digital).
- Re-run: DRC and LVS of `amp_ch`; every L2b check on the extracted cell, compared with the VARIANT baselines (`AFE/amp/sim/lp_rvt_result.json`, key `variant_results`), not the original's; X2 S1 typ.
- Pass limits for the variant, typ / ff 85 / ss -40: the limits of the original (gain 60 +- 1 dB, f_lo <= 0.5 Hz, f_hi >= 300 Hz, noise <= 2 uV, PM >= 60 deg, settling <= 0.5 LSB, supply current within 2 % of 74.4 / 118.8 / 47.1 uA), plus two that replace the Decision-28 exception: THD at +-0.5 mV 12.25 Hz <= 0.25 % at all three corners (schematic 0.035 / 0.078 / 0.050 %), and the output follows up to >= 2.20 V at ss -40 C (schematic 2.34 V; this is the one margin layout can eat, through the well resistance or a lower o2 ceiling). If THD at ff 85 is between 0.25 % and 2.6 %, accept it under Decision 28 and report.
- If the organizer ALSO refuses the deep n-well: use `AFE/amp/spice/ota2_rvt_nodnw.spice` (regular `nfet_03v3` 10 x 10u/0.28u, bulk vss; substitute only `ota2.spice`). Accepted degradations: top of the output 2.18 V at ss -40 C (32 mV of margin; below 2.15 V for VDD <= 3.15 V at ss -40 C, so the README states VDD >= 3.3 V), THD <= 0.10 % at +-0.5 mV, f_hi 602 / 925 / 386 Hz. Before use run `python3 AFE/amp/scripts/lp_rvt_x2.py run nodnw ff85` and `... ss-40` (only typ was run) and require the amplifier to add <= 0.1 LSB.
- BLOCKED only if the organizer refuses native Vt, the deep n-well AND a minimum-length 3.3 V NMOS, which cannot happen for a standard device.

## 6. Choices I made (rule 10)

1. Isolated p-well (A) over minimum-length bulk-vss (B). Both meet the targets; A has 192 mV of top margin at ss -40 C against 32 mV, works down to 3.0 V, and does not rest on the minimum-length threshold roll-off. Cost: +575 um2 per channel against +36 um2 (679 / 141 / 104 um2), and the DNWELL layer. Priority 1 (meets the targets with margin) decided before priority 2 (area).
2. Size 8 x 10u/1u: see section 2.
3. Same subckt names and pins, new files only: a variant is selected by swapping two include paths; no testbench, script or Verilog change. `afe_chc_rvt.spice` is a copy of the `afe_chc` subckt (nothing changes at that level), kept honest by the check in `lp_rvt_report.py`.
4. Cc2 not retuned for the 5.6 % f_hi shift (one changed device instead of two; every target met).
5. The well junction is not a netlist device (not extracted without a diode marker); simulated as a what-if.
6. Transients run with `abstol=1e-12` for both netlists (Decision 43a), not the 1e-20 of the A4c testbench; op / ac / noise keep the testbench options.
7. X2 S1 with 12 calibration inputs instead of 24, for both netlists.
8. Settling reported as "end minus before" plus the raw D5 number (attention 4).
9. The second fallback was written as a file and taken through the same tables and X2 S1 typ.

## 7. Not done / open

- Layout and PEX of the DNWELL follower inside `amp_ch`, netgen LVS of the wired device, the DNWELL tap; only the bare pcell was extracted and DRC-checked.
- ac / noise / THD at 9 PVT (3 corners; the DC swing was run at 9 PVT), fs / sf, Monte Carlo, other supply voltages than 3.3 V (DC swing only at 3.0 / 3.15 / 3.6 V).
- xschem schematic of the variant and its equivalence run.
- X2 S3 / S4 / S5 and the TGATE-attached runs with the variant; X2 S1 of the second fallback at ff 85 / ss -40.
- Noise with the PDK well-diode model (`.noise` returns NaN with that model card in ngspice-46; its capacitance was used instead).
- The reset-recovery and power-up numbers are a same-script comparison; they differ from the A4c log values (other tolerance set, other read-out instants) and are not a re-qualification of Decision 38.
- The organizer's confirmation of the deep n-well.

## Files

- Netlists: `AFE/amp/spice/ota2_rvt.spice`, `afe_chc_rvt.spice`, `ota2_rvt_nodnw.spice` (new). Edited: `AFE/adc/scripts/x2lib.py` (additive option only).
- Scripts (new): `AFE/amp/scripts/lp_rvt_lib.py`, `lp_rvt_screen.py`, `lp_rvt_run.py`, `lp_rvt_x2.py`, `lp_rvt_report.py`, `lp_rvt_lvs_check.py`, `lp_rvt_dnw_cell.sh`.
- Logs: `AFE/amp/sim/lp_rvt_{screen,screen_vdd,screen_pvt9,screen_vocm1p15,tables,swing,adc245,settle,settle_tight,slew,rec,pur,dnw_cell,lvs_check,report}.log` (+ `.json`, + `_nglogs.tgz` = the complete ngspice outputs), `lp_rvt_result.json`; `AFE/adc/sim/lp_rvt_x2_s1_{orig,rvt}_{typ,ff85,ss-40}.{log,npz}`, `lp_rvt_x2_s1_nodnw_typ.{log,npz}`, `lp_rvt_x2_s1_report.{log,json}`.
- Re-run everything: `python3 AFE/amp/scripts/lp_rvt_screen.py all 3.3`; `python3 AFE/amp/scripts/lp_rvt_run.py <tables|swing|adc245|settle|settle_tight|slew|rec|pur> orig,rvt,B_10x10_0p28`; `python3 AFE/amp/scripts/lp_rvt_x2.py run <orig|rvt|nodnw> <typ|ff85|ss-40>` then `... report`; `python3 AFE/amp/scripts/lp_rvt_report.py`. Jobs go through `AFE/layout/scripts/slot.sh`, two at a time, scratch in /tmp/lp_rvt.
