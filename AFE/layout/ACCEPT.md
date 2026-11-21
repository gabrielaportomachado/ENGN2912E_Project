# Acceptance limits and pre-approved decisions for the layout phases (LP, 2026-11-20)

**STATUS: IN FORCE (user, 2026-11-20); reviewed after the fact, changes arrive through AFE/layout/REVIEW.md.** No phase waits for an approval: every phase decides with this file.
Written by phase LP so that one person can run L1a, L1d, L2b, L1b, L3a, L3b, L4 without asking anyone. Every number has its source; baselines are in `AFE/layout/baseline/`.

How it is used: a phase ends with `python3 AFE/layout/scripts/gate.py <phase>`. The gate reads the DRC / LVS / PEX reports of `flow.py`, the results of the golden testbenches
(`AFE/layout/tb/tb_*.py`) through `compare.py`, and the limits of `AFE/layout/accept_limits.json` (section 3 below is the same table). PASS = commit, push, start the next phase.
FAIL = find the failing line in section 4 (the decision ladder) and do exactly what it says. Only if no entry applies: section 6 (BLOCKED.md).

## 1. What the layout agent may and may not do by itself

MAY (layout-only, no approval needed): move, rotate, mirror, re-shape and re-route anything; change finger counts and unit pieces as long as netgen still matches the reference within the
property tolerance; add dummies, taps, guard rings, shields, decap units beyond the required number; choose metal layers and widths; regenerate the LVS references with the options of
`mk_lvs_netlists.py` that describe what was DRAWN (`--cin N,W,L`, `--decap W,L`, `--decap-n NMAIN,NDAC`, `--rstrap MODEL,W,L`, `--dig-netlist FILE`, `--cin-top` only as check_env.sh C3 dictates);
change floorplan parameters with `floorplan.py build --set key=value` inside the outline; apply every entry of section 4 marked PRE-APPROVED.

MAY NOT: edit a simulation netlist, the RTL (`rtl/`, `AFE/adc/rtl/`, `AFE/top/dbs_afe_top.v`), a file under `AFE/layout/lvs/` by hand, `accept_limits.json`, a baseline, or this file; change a device
size, a capacitor value or a bias tap; write a numbered Decision; edit AFE/layout/REVIEW.md; skip a gate; use a raw `ext2spice` netlist for a post-layout number; exceed the 1000 x 1000 um outline.

## 2. NEEDS THE USER'S EYE: two conventions for the pseudo-resistor transistors (found in LP)

Finding (`AFE/layout/sim/lp_prdiff_study.log`, baselines `*_junction.json`): the six pseudo-resistor transistors (pfet_03v3 0.22u/0.5u) have NO junction area / perimeter in the design netlists
(`AFE/amp/spice/pseudoR.spice`); every extracted netlist has them. With area on them (W x 0.18 um, the DIFF formula of all other devices) the simulated pseudo-resistance rises far above the
leakage resistance of the MIM capacitors (both are model floors, audit risk R1), and:

| typ 27 / ff 85 / ss -40 C | DESIGN convention (no area; every Decision was made with it) | JUNCTION convention (area present) |
|---|---|---|
| high-pass corner f_lo | 0.202 / 0.226 / 0.237 Hz | < 0.001 / 0.053 / < 0.001 Hz |
| output DC level, no electrode offset | 1.6506 / 1.6510 / 1.6502 V | 1.658 / 1.652 / 1.646 V |
| static output shift for a 10 mV electrode offset | +0.01 mV | +969 mV (railed) / +0.9 mV / +1250 mV (railed) |
| record start with a 10 mV offset: output after 12 s | 1.6507 V (within 1 mV after 4.7 / 4.6 / 3.5 s) | 1.759 / 1.677 / 1.750 V, still drifting (9.5 / 2.4 / 8.7 mV/s) |
| same with a 100 mV offset, after 40 s | 1.6508 V (8.9 / 8.6 / 8.2 s) | 2.74 / 1.99 / 2.93 V |
| holding RST_AMP for 100 ms at the record start | not needed | does not cure it: after the release the output drifts at about 1 mV/s per mV of offset |
| gain, f_hi, noise, THD, PSRR, power-up with RST_AMP | - | unchanged within 1 % (noise +0.6 .. +1.0 %) |
| moving the gate taps VTT1 / VTT2 (bias cell only) | no effect at typ / ss -40; f_lo 0.6 .. 4.4 Hz at ff 85 for VTT1 <= 0.1 V | still +58 / +129 mV (typ) and +407 mV (ss -40) at VTT1 = VTT2 = 0: no tap setting cures the cold corner |

Meaning: in the junction convention the capacitor leakage, not the pseudo-resistor, sets the DC state, so the amplifier is DC coupled with gain 1000 for slow electrode offsets; after each reset the
output is at mid-scale and then drifts by about (electrode offset) x 1 /s. Which convention silicon follows is not knowable from the models.

**Pre-decided handling (in force; the user reviews it after the fact through AFE/layout/REVIEW.md; the alternatives are in AFE/NOTES.md "LP findings"):**
1. The GATES of L2b and L3b use the DESIGN convention: `tb_amp_*.py` strip the junction area of exactly these six devices from the extracted netlist (lptb.strip_pr), so post-layout numbers are
   comparable with every approved number. Each amplifier check is ALSO run with `--junction` (the netlist as extracted) and reported next to it; of those only the rows of section 3 marked
   `junction` are limits (gain, f_hi, output level after RST_AMP), the rest is the risk view.
2. Layout rule (SPEC.md 3.2 item 4): the six devices are drawn with minimum, identical junction area.
3. Host rules added to the README (step 7): (a) after every record start the host also sets RST_AMP for >= 100 ms (it costs 100 ms and removes the dependence on the 3 ms one-shot);
   (b) the host watches the running mean of every channel and repeats RST_AMP when it leaves mid-scale +- 200 LSB (the power-up rule of Decision 44c, now also during recording); expect that every
   0.5 V / (offset x 1 /s), i.e. every 5 .. 50 s for 100 .. 10 mV of electrode offset, IF silicon follows the junction convention; (c) test plan: measure f_lo and the drift after RST_AMP with a
   known DC offset on every channel first.
4. No circuit change before tapeout. A cure (a defined DC path that does not rely on a leakage floor) is a redesign of the feedback network: after 2026-11-25.

## 3. Limits

DRC, LVS, PEX, floorplan (all phases):

| item | limit | why |
|---|---|---|
| KLayout DRC, official gf180mcuD deck, --variant=D, `flow.py drc` (FEOL + BEOL + connectivity + off-grid; antenna added for afe_dig and the top) | 0 violations | sign-off deck (common rule 3). No waiver is pre-approved |
| density rules (`flow.py drc --density`) | reported for the top only, not a gate | the organizer fills the frame; metal fill of our macro is their step (Integration README); if they ask for it: section 5 |
| netgen LVS, `flow.py lvs`, against `AFE/layout/lvs/<cell>` | final result exactly "Circuits match uniquely.", no property error | property tolerance = the PDK setup: 1 % on w, l, c_width, c_length, r_width, r_length. Enough for the 5 nm grid rounding (largest 0.04 %, SPEC.md section 6); a real mis-size (> 1 %) fails |
| LVS pins | every pin of the reference, no extra pin | extra labels become ports in Magic: label only pins |
| PEX, `flow.py pex` | device census equal to the LVS extraction, no unknown device, MIM correction applied (`mim_fix` in the JSON) | mode `c` (capacitance) is the gate; `rc` is optional: use it only if its census also passes |
| floorplan, `floorplan.py check` with the as-built GDS | 0 FAIL: inside the outline, cells inside their slots, every pin once | SPEC.md |
| chip static power (L3a estimate, L3b) | within +-10 % of 2.09 / 3.26 / 1.37 mW (AFE/review/sim/f1_power_total.log) | no target exists; a larger change means a device or a short |
| area | outline 1000 x 1000 um never exceeded | Decision 45 |

Post-layout values (baseline = schematic, post = extracted; the same script and settings for both):

Changed 2026-11-21 by REVIEW.md R8 / R9 (user / team: as-built amp_ch / adc_ch post-layout numbers accepted); the limits before that change are in AFE/layout/accept_limits_pre_R8R9.json.

<!-- LIMITS BEGIN (written by compare.py --write-accept from accept_limits.json; do not edit by hand) -->
| check | phase | value | corners | limit | soft | why |
|---|---|---|---|---|---|---|
| amp_ac | L2b | g_mid_db | all | 59 .. 61 |  | Decision 1: 60 +-1 dB |
| amp_ac | L2b | g_mid_db | all | |change| <= 0.3 | WARN only | more than 0.3 dB from the baseline = the Cin : Cf1 ratio moved by more than 3 %: check the capacitor pieces |
| amp_ac | L2b | f_lo_hz | all | <= 0.5 |  | Decisions 1, 2: f_lo <= 0.5 Hz (nan = no corner above 1 mHz) |
| amp_ac | L2b | f_hi_hz | all | >= 300 |  | Decision 1: f_hi >= 300 Hz (baseline 653 / 998 / 422 Hz) |
| amp_ac | L2b | idd_ua | all | x / baseline 0.95 .. 1.05 |  | a layout does not change the bias current: more than 5 % means a device or extraction error |
| amp_ac | L2b | vout_v | all | 1.6 .. 1.7 |  | mid-scale +-50 mV (62 LSB; the host accepts +-200 LSB, Decision 44c) |
| amp_ac | L2b | hf_dev_db | all | <= 2 |  | port-level stand-in for the stage-1 loop margin: 2 dB = about 8 deg (calibration in baseline/amp_loop.json); baseline 76-81 deg, Decision 12 wants >= 60 deg |
| amp_noise | L2b | noise_d8_post_uv | typ / ss-40 / ff85 | <= 2 / <= 2 / <= 2.2 |  | Decisions 1, 4, 8, 50: <= 2 uV rms in 0.5-300 Hz at typical flicker (ff 85 C <= 2.2 uV, Decision 50), pseudo-resistor noise as ideal resistors. = baseline noise_d8 x (post / pre of noise_real). Baseline (Cin 15 pF) 1.890 / 2.139 / 1.732 uV (typ / ff 85 / ss -40) |
| amp_loop | L2b | pm_deg | all | >= 60 |  | Decision 12 / 21b: stage-1 loop phase margin >= 60 deg with the real stage-2 load (baseline 79.2 / 76.4 / 81.1); nan = no anchor, then hf_dev_db of amp_ac decides |
| amp_psrr | L2b | supply_gain_50hz | all | 0.32 .. 0.68 |  | the ADC is ratiometric (0.5): |gain - 0.5| <= 0.12 keeps the board-ripple requirement of 1 mV rms (D4b; baseline 0.566-0.579) | R8 2026-11-21: was 0.38 .. 0.62 (accept_limits_pre_R8R9.json) |
| amp_thd | L2b | thd_pct | typ / ss-40 / ff85 | <= 0.5 / <= 0.5 / <= 4.5 |  | no target; typ / ss -40 baseline 0.04-0.05 %; ff 85 C clips at the bottom, accepted by Decision 28 (baseline of this script 2.5-3.7 %) |
| amp_thd | L2b | out_max_v | all | >= 2.13 |  | output reaches the top of the 1.15-2.15 V range (baseline 2.149-2.167 V) |
| amp_thd | L2b | out_min_v | typ / ss-40 / ff85 | <= 1.19 / <= 1.19 / <= 1.25 |  | bottom of the range; ff 85 C 1.21-1.22 V accepted (Decision 28) | R8 2026-11-21: was {"typ": 1.17, "ss-40": 1.17, "ff85": 1.25} (accept_limits_pre_R8R9.json) |
| amp_thd | L2b | gain_db | all | 58.8 .. 61 |  | Decision 1 with the ff 85 compression (baseline 59.82) |
| amp_pwrup | L2b | err_1s_mv | all | <= 50 |  | L3b item 5 / Decision 44c: 1 s after RST_AMP every output within 10 mV of 1.65 V (baseline 0.07-0.62 mV) | R8 / ladder R-6 2026-11-21: was 10.0 (accept_limits_pre_R8R9.json) |
| amp_reset | L2b | t_fs_ms_os10m | all | x / baseline 0.7 .. 1.4 |  | one-shot pulse: C_T x threshold / mirror current; baseline 3.0 / 1.6 / 5.8 ms (A4c 3.56 / 1.90 / 6.86 with its own threshold); 3 ms clears every step at typ and ss -40, 1 ms at ff 85 |
| amp_reset | L2b | t_1mv_s_os0 | all | <= 6.75 |  | baseline 1.5 / 3.2 / 0.7 s | R8 / ladder R-7 (x 1.5) 2026-11-21: was 4.5 (accept_limits_pre_R8R9.json) |
| amp_reset | L2b | t_1mv_s_os1m | all | <= 6.75 |  | baseline 0.004 / 1.4 / 0.5 s | R8 / ladder R-7 (x 1.5) 2026-11-21: was 4.5 (accept_limits_pre_R8R9.json) |
| amp_reset | L2b | t_1mv_s_os10m | all | <= 9.75 |  | Decision 38b accepted 3.4-4.7 s (baseline 4.7 / 4.6 / 3.5 s) | R8 / ladder R-7 (x 1.5) 2026-11-21: was 6.5 (accept_limits_pre_R8R9.json) |
| amp_reset | L2b | t_1mv_s_os100m | all | <= 12 |  | Decision 38b accepted 7.3-9.0 s (baseline 8.9 / 8.6 / 8.2 s) |
| amp_reset | L2b | final_v_os100m | all | 1.6 .. 1.7 |  | returns to mid-scale |
| amp_reset | L2b | final_v_os10m | all | 1.6 .. 1.7 |  | returns to mid-scale |
| amp_reset_host | L2b | t_1mv_s_os10m | all | <= 9.75 |  | as amp_reset, with the host's 100 ms RST_AMP at the record start | R8 / ladder R-7 (x 1.5) 2026-11-21: was 6.5 (accept_limits_pre_R8R9.json) |
| amp_reset_host | L2b | t_1mv_s_os100m | all | <= 12 |  | as amp_reset |
| amp_reset_host | L2b | final_v_os100m | all | 1.6 .. 1.7 |  | returns to mid-scale |
| amp_ac_junction | L2b | g_mid_db | all | 59 .. 61 |  | Decision 1 holds in both conventions |
| amp_ac_junction | L2b | f_hi_hz | all | >= 300 |  | Decision 1 |
| amp_ac_junction | L2b | vout_v | all | 1.5 .. 1.8 |  | with junction area the output DC level moves (baseline of this convention 1.658 / 1.652 / 1.646 V); +-150 mV keeps it inside the host's +-200 LSB check |
| amp_ac_junction | L2b | f_lo_hz | all | <= 0.5 |  | any corner below 0.5 Hz passes (Decision 2); in this convention it is below 1 mHz at typ and -40 C: report |
| amp_reset_host_junction | L2b | drift_mv_s_os10m | all | |x| <= 30 | WARN only | RISK VIEW, not a gate: with junction area the capacitor leakage sets the DC state and the output drifts by about 1 mV/s per mV of electrode offset after every reset (baseline of this convention about 10 mV/s at 10 mV); the host re-issues RST_AMP when a channel leaves +-200 LSB (ACCEPT.md section 2) |
| adc_codes | L1b | code_offset_lsb | all | |change| <= 15 |  | a pure code shift (AC-coupled signal); F1 expects several LSB from junction and wiring capacitance (Decision 46d: L1b restates it); 15 LSB keeps the inputs of tb_adc_steps on their boundary |
| adc_codes | L1b | inl_lo_lsb | typ / ss-40 / ff-40 / ss125 / ff85 | <= 1 / <= 1 / <= 1.2 / <= 1.2 / <= 3.1 |  | Decision 43c: INL <= 1 LSB beyond the offset for inputs <= 2.0 V (typ); at ff 85 C the claim ends at 1.9 V (baseline 1.57 LSB up to 2.05 V, accepted) | R9 2026-11-21: was {"typ": 1.0, "ss-40": 1.0, "ff-40": 1.0, "ss125": 1.0, "ff85": 2.5} (accept_limits_pre_R8R9.json) |
| adc_codes | L1b | inl_code_lo_lsb | typ / ss-40 / ff-40 / ss125 / ff85 | <= 1.5 / <= 1.5 / <= 1.5 / <= 1.5 / <= 3 |  | code-based INL less the quantisation: contains the code-dependent threshold accepted by Decision 43b (baseline 0.25-1.07) | R9 2026-11-21: was {"typ": 1.5, "ss-40": 1.5, "ff-40": 1.5, "ss125": 1.5, "ff85": 2.0} (accept_limits_pre_R8R9.json) |
| adc_codes | L1b | top_2v15_lsb | all | change <= +1.5 |  | top-of-range plate error accepted by Decision 43c (+2.1 typ / +4.4 ff 85); L1b reports the change; more than +1.5 LSB on top needs the ladder |
| adc_codes | L1b | alpha | all | |change| <= 0.02 |  | plate attenuation: -0.02 = about 70 fF of extra capacitance on the 3.49 pF DAC top plate |
| adc_codes | L1b | gain_err_pct | all | -0.5 .. 0.5 |  | ADC gain error (baseline -0.002 .. -0.11 %) |
| adc_codes | L1b | unresolved | all | <= 0 |  | no metastable decision |
| adc_codes | L1b | failed | all | <= 0 |  | every conversion converges |
| adc_steps | L1b | step_1536_lsb | all | |x| <= 2 |  | Decision 43b accepted -1.1 LSB (typ / ff 85): static, below the 2.3 LSB rms of amplifier noise at the ADC input |
| adc_steps | L1b | step_2048_lsb | typ / ss-40 / ff85 | |x| <= 2 / |x| <= 2 / |x| <= 2.5 |  | Decision 43b accepted +1.3 / +1.55 LSB; with the MIM preamp capacitors F1 expects +0.8 / +1.3 | R9 / ladder Q-2 (ff 85 C only) 2026-11-21: was 2.0 (accept_limits_pre_R8R9.json) |
| adc_steps | L1b | step_2112_lsb | all | |x| <= 0.5 |  | roll-over of the LSB array: bridge capacitor and bridge-node parasitic (Decision 40a; 0.018 LSB per fF, baseline 0.05 LSB) |
| adc_timing | L1b | settle_worst_lsb | typ / ff-40 / ss125 / ss-40x | <= 0.5 / <= 0.5 / <= 0.5 / <= 1 |  | DAC settled to 0.5 LSB when the comparator fires, inputs up to 2.0 V, matched corners; the mixed corner misses by 0.65-0.75 LSB pre-layout, accepted by Decision 44f |
| adc_timing | L1b | late | all | <= 0 |  | every decision inside the window of the clock chain |
| adc_timing | L1b | failed | all | <= 0 |  | every run converges |
| adc_timing | L1b | settle_top_lsb | all | change <= +0.5 |  | inputs above 2.0 V: slow tail of the top-of-range error accepted by Decision 43c (baseline up to 1.45 LSB at ff -40); L1b reports the change |
| adc_overlap | L1b | dt_max_lsb | all | <= 0.2 |  | the 0.21 ns driver-gate overlap of the gate-level timing (audit m3) must not move a transition (baseline 0.004 LSB) |
| adc_overlap | L1b | dcode_max | all | <= 1 |  | codes unchanged |
| bias_startup | L3b | t90_n8_ms | all | <= 4500 |  | the host waits >= 5 s before RST_AMP (Decision 44c); baseline 3.7 / 1.0 / 3565 ms |
| bias_startup | L3b | settled_n8 | all | >= 1 |  | the bias reaches its final state |
| bias_startup | L3b | vcm_v | all | |change| <= 0.005 |  | ladder tap (ratio of matched ppolyf_u_1k segments): 5 mV = 6 LSB |
| bias_startup | L3b | vrs_v | all | |change| <= 0.03 |  | reset level of the replica |
| bias_startup | L3b | i_sink_n8_ua | all | x / baseline 0.9 .. 1.1 |  | master current (beta multiplier, Rb 60 kOhm) |
| tgate | L3a | ron_max_kohm | all | <= 133 |  | A4b: more than 133 kOhm in series breaks the 2 uV noise budget (baseline 21 / 16 / 34 kOhm) |
| tgate | L3a | ron_max_kohm | all | x / baseline 0.9 .. 1.1 |  | same devices: 10 % |
| tgate | L3a | i_off_pa | all | <= 1 |  | off leakage below 1 pA inside the rails (audit i4) |
| top_e2e | L3b | offset_lsb | all | |change| <= 15 |  | pure code shift (Decisions 43e, 46d); same limit as adc_codes |
| top_e2e | L3b | inl_lo_lsb | typ / ss-40 / ff85 | <= 1 / <= 1 / <= 3.1 |  | Decision 43c: INL <= 1 LSB beyond the offset below 2.05 V; ff 85 C 1.99 LSB accepted (claim ends at 1.9 V) | R9 (same ff 85 C ADC INL as adc_codes) 2026-11-21: was {"typ": 1.0, "ss-40": 1.0, "ff85": 2.5} (accept_limits_pre_R8R9.json) |
| top_e2e | L3b | amp_minus_adc_lsb | all | <= 0.5 |  | settling of amplifier + TGATE into the ADC within T_ACQ: <= 0.5 LSB (pre-layout 0.08 LSB without the TGATE) |
| top_e2e | L3b | gain_sine_code_db | typ / ss-40 / ff85 | 59 .. 61 / 59 .. 61 / 58.8 .. 61 |  | Decision 1 end to end (pre-layout 60.007 / 59.865 / 59.990 dB) |
| top_e2e | L3b | unresolved | all | <= 0 |  | no metastable decision |
| top_supply | L3b | dt_max_lsb | all | <= 0.5 |  | shift of a transition level by the supply: <= 0.5 LSB (Decision 40e / 43f; pre-layout <= 0.03 LSB at the last trial, 0.25 LSB by input sweep at ff -40) |
| top_supply | L3b | dres_max_lsb | typ / ss125 / ff-40 | <= 0.5 / <= 0.5 / <= 0.8 |  | plate residue change at any decision instant; ff -40 C 3.6 V was AT 0.5 LSB pre-layout (an inductance item, Decision 43f): up to 0.8 is the pre-approved degradation, above it the ladder applies |
| top_supply | L3b | dres_max_lsb | ff-40 | <= 0.5 | WARN only | ff -40: more than the pre-layout 0.5 LSB: report and state the pad inductance used |
| top_supply | L3b | failed | all | <= 0 |  | every case converges |
| top_xtalk | L3b | victim_conv_lsb | all | <= 0.5 |  | what the neighbour's conversions add at the victim's next samples: <= 0.5 LSB (pre-layout 0.002 LSB; the kick only matters within 5 us of a resume) |
| top_pwrup8 | L3b | err_max_mv | all | <= 10 |  | L3b item 5: every output within 10 mV of 1.65 V 1 s after the common RST_AMP |
| top_pwrup8 | L3b | vrs_dip_mv | all | change <= +30 | WARN only | dip of the shared reset level while 8 channels reset together; baseline 15 / 14 / 137 mV (typ / ff85 / ss-40, the cold bias is still settling at 5 s); a larger dip = more load on vrs: report |
| top_stim | L3b | rec_dev_mv | all | <= 5 |  | the parked amplifier input stays on vcm_in while the IPG path carries 2.9 V pp |
| top_stim | L3b | out_dev_mv | all | <= 50 |  | the parked amplifier stays out of the rails during stimulation (baseline 0.02 mV) |
| top_stim | L3b | rec_dev_mv_leak | all | <= 5 |  | same with 200 pA of pad leakage on E and REF |
| top_stim | L3b | out_dev_mv_leak | all | <= 50 |  | same with 200 pA of pad leakage |
| top_stim | L3b | final_v | all | 1.6 .. 1.7 |  | record start 0.3 s after the stimulation: back at mid-scale |
| top_stim | L3b | final_v_leak | all | 1.6 .. 1.7 |  | same with pad leakage |
| top_stim | L3b | t_1mv_s | all | <= 4.5 |  | as amp_reset without offset (baseline 0.8 s) |
<!-- LIMITS END -->

Digital macro afe_dig (L1d; numbers of the LP trial: AFE/dig/LP_STEP5.md, AFE/dig/reports/flow_summary.rpt, sta_audit_dig.log, klayout_drc.log, AFE/dig/sim/tb_audit_dig_summary.log):

| item | limit | trial | why |
|---|---|---|---|
| setup / hold at the 5 corners, 2 MHz clock (500 ns), 0.5 ns uncertainty | 0 violations | 0 / 0 (setup ws 91.69 ns ss_125, hold ws 0.229 ns ff_n40) | STA sign-off |
| max-slew / max-cap violations | 0 | 0 / 0 (D3 macro: 16 / 3) | audit M6 |
| DAC edge -> comparator clock of ADC 0, ff_n40C_3v60 (worst SPEF) | >= 21.0 ns | 22.14 ns | DAC settling at the fast corner 15.1 ns + margin (AUDIT 4.4.3) |
| last comparator window end -> next SCLK edge at the register clock pins, ss_125C_3v00, 3 MHz | >= 20.0 ns | 22.39 ns | the next DAC edge is launched through the same clock buffer, so this is the physical margin (AUDIT 4.4.5). Against the SCLK PIN the trial has 20.59 ns: reported, not a limit |
| captured decision -> code register slack at 3 MHz, ss_125 | >= 10 ns | 13.75 ns (D3: 14.25) | STA |
| sw_rec / sw_rec_b skew at the macro pins | <= 3 ns | <= 0.78 ns (ss_125) | harmless (<= 8 fC for 100 mV, AUDIT 4.4.3); a larger value means a missing buffer |
| gate-level testbench `run_tb_audit.sh` on the hardened netlist, 5 matched corners + MIXED, 2 and 3 MHz, 3 scenarios | failing assertions only X1.contention, X5.word0, X5.after33d, T11.crowbar, and T2.settle at MIXED | as required | audit 4.4.6; Decision 44f |
| KLayout DRC variant D on the macro GDS | 0 | 0 (3:36 wall, 645 MB) | the D3 flow skipped it (M6) |
| pins | `floorplan.py check --dig-pins`: side and position per floorplan.json | PASS | SPEC.md 3.5 |
| die | <= 820 x 110 um | 819.84 x 109.76 um | floorplan slot |

## 4. Decision ladder (find the failing item; apply the first entry that fits; each entry says how often to try before the next one)

**G. General**
- G-1 A step fails the same way twice: stop trying variations of the same fix; take the next entry of the matching ladder. If the ladder is exhausted: section 6.
- G-2 A tool crashes, runs out of memory or disk: delete `AFE/layout/.ptmp` (and old LibreLane run directories), set `AFE_SLOTS=2`, re-run once. Still failing: run `check_env.sh`; a FAIL there is
  the cause, follow its "DO" line.
- G-3 `check_env.sh` C3 says MIM terminal 1 is the BOTTOM plate on this machine: PRE-APPROVED: regenerate every reference with `--cin-top rec`, re-run check_lvs_netlists.py, report it at the top of
  the phase findings. (On the LP machine terminal 1 = top plate.)
- G-4 A baseline cannot be reproduced on the layout machine (`tb_selftest.sh` fails): re-run `bash AFE/layout/tb/run_baselines.sh`; if a value differs from the committed baseline by more than 1 %
  of its limit, write BLOCKED.md (the two machines do not simulate alike).
- G-5 A cell does not follow a pin side / position of SPEC.md: PRE-APPROVED: add the wrap-around wire in the slot margin or re-run the cell's generator with the pin side as a parameter. No device change.
- G-6 The organizer's DEF or an answer arrives during a phase: finish the phase with the defaults of section 5, then apply the answer at the start of the next phase (pins are re-placed in L3a).

**D. DRC** (limit 0)
- D-1 Off-grid (`*_OFFGRID`): snap the generator to 5 nm (`round(v / 0.005) * 0.005`); sizes from the references are rounded as SPEC.md section 6.
- D-2 DF.13 / DF.14 (tap distance): add a tap cell or P+ / N+ tap within 15 um (5 V / 6 V devices) or 20 um (3.3 V devices). The TGATE always gets a filltie cell.
- D-3 MIMTM.x: bottom plate 0.6 um beyond the top plate, 1.2 um to other Metal4, top plates 0.6 um apart, no Via3 on a bottom plate (connect through Via4 / Metal5), <= 10,000 um2 of MIM per
  Metal4 polygon (split the polygon, join on Metal5).
- D-4 Metal / via spacing, width, enclosure: widen or move; never shrink a device.
- D-5 Antenna (macro and top): add a diode cell (macro: LibreLane's antenna repair) or jump to a higher metal near the gate.
- D-6 A rule that cannot be met after three different fixes: BLOCKED.md with the rule, the coordinates and the three attempts. No waiver is pre-approved.

**L. LVS** (limit: unique match)
- L-1 Property error on a capacitor / resistor / MOS size: the drawing is wrong by more than 1 %: fix the drawing. If the drawn size is intentional (other Cin pieces, other decap unit, other strap
  resistor): PRE-APPROVED: regenerate the reference with the matching option of `mk_lvs_netlists.py` and say so in the findings.
- L-2 Pin mismatch: a label is missing, misspelled or on the wrong layer; or an extra label makes an extra port. Fix the labels.
- L-3 Device count: a pcell that Magic does not recognise (metal resistor: use `kpdk.metal_res`), a missing marker layer, a device split by a well / diffusion error, an unconnected finger.
- L-4 Net mismatch: follow netgen's first reported net; typical causes are a short through a guard ring or a missing via stack.
- L-5 MIM terminals swapped (netgen does not permute them): the plate order of SPEC.md section 6 is wrong in the drawing: swap the drawing, never the reference.
- L-6 netgen runs out of time (1800 s) on the top: flatten the channel cells in the extraction (`flow.py lvs --flatten`), or compare cell by cell (amp_ch, adc_ch, bias_genc, afe_ch) and then the top
  with those cells as black boxes. Three different attempts, then BLOCKED.md.

**P. PEX**
- P-1 `rc` mode fails or its census differs: PRE-APPROVED: use mode `c`; for the supply check of L3b take the strap resistances from geometry (squares x 0.09 ohm/sq Metal1-4, 0.04 ohm/sq Metal5;
  write them into the supply model file of tb_top_supply.py) and say so.
- P-2 Anchor capacitor not found (lptb warns): the cell has another capacitor size than SPEC.md section 6: fix the drawing, or (other Cin pieces by L-1) pass the netlist anyway: the checks that
  need the node report `nan` and compare.py uses the stand-in (hf_dev_db for the loop margin).
- P-3 `VSUBS` warning: the cell has no substrate tap on vss: add it.

**R. Amplifier post-layout (L2b), design convention**
- R-1 Gain outside 60 +- 1 dB, or more than 0.3 dB from the baseline (WARN): the Cin : Cf1 ratio. Layout fix: same unit orientation and surroundings for Cin and Cf1, remove Metal5 / Metal4 wiring
  over or beside the Cf1 plates; the top-plate wiring of vn / vp adds to Cf if it runs along v1.
- R-2 f_hi < 300 Hz (baseline ss -40: 422 Hz): parasitic on o2 / vn2 of stage 2. Layout fix: shorten those nets. If f_hi(ss -40) is 280 .. 300 Hz after the fix: PRE-APPROVED degradation (gain at
  300 Hz is then -3.0 .. -3.3 dB instead of -1.8 dB; same class as the accepted f_hi spread of Decision 22). Below 280 Hz: BLOCKED.md.
- R-3 Noise (noise_d8_post_uv) > limit (2.0 uV typ / ss -40, 2.2 uV ff 85 C, Decision 50): parasitic capacitance on the summing nodes (each 1 % of 15 pF adds about 1 %). Layout fix: shorter vn / vp wiring, keep the top plates as the summing node,
  no shield plane under vn wiring other than the Cin bottom plates. The ff 85 C limit 2.2 uV replaces the former 2.05 uV R-3 allowance (REVIEW.md R6; the 15 pF schematic is already at 2.139 uV, so only about 3 % remain for layout parasitics); no other degradation is pre-approved
  (the audit already has 2.04 .. 2.23 uV for unfiltered codes, m5). Above: BLOCKED.md.
- R-4 Loop margin: pm_deg < 60 or hf_dev_db > 2 dB: parasitic on v1 or o1. Layout fix: shorten v1 (stage 1 to stage 2 Cin), keep Cc1 next to the OTA. PRE-APPROVED: pm_deg 55 .. 60 with hf_dev_db
  <= 3 dB (A3 measured 54 deg at 10 pF of stage-2 input capacitance as still stable). Below 55: BLOCKED.md.
- R-5 THD / swing: out_min above the limit at typ or ss -40: the follower or its sink is wrong (LVS should have caught it): re-check the extraction. ff 85 C up to 4.5 % / 1.25 V is accepted
  (Decision 28).
- R-6 Power-up error > 10 mV after RST_AMP: leakage on a summing node (a missing guard, a diode-connected dummy on vn). Layout fix: isolate the node. If it stays between 10 and 50 mV: PRE-APPROVED
  (the host accepts +-200 LSB = 161 mV, Decision 44c). Above 50 mV: BLOCKED.md.
- R-7 Reset recovery slower than the limits, or the pulse width outside 0.7 .. 1.4 x baseline: C_T or the mirror leg. PRE-APPROVED degradation: t_1mv up to 1.5 x the limit of section 3
  (Decision 38b accepted seconds); the host RST_AMP rule of section 2 covers the rest. A pulse shorter than 0.7 x baseline: BLOCKED.md.
- R-8 Junction-convention rows fail (output level after RST_AMP outside 1.50 .. 1.80 V, or after-reset error > 50 mV): layout fix: reduce and equalise the junction area of the six pseudo-resistor
  transistors and of anything else on vn / vp / vn2. If it still fails: BLOCKED.md (this is the item of section 2: the user decides).

**Q. ADC post-layout (L1b)**
- Q-1 Code offset moved by more than 15 LSB: PRE-APPROVED as long as inl / steps pass: re-centre the inputs of tb_adc_steps.py (`X2_OFF` environment variable) and restate the offset in the README
  (Decision 46d). More than 60 LSB: BLOCKED.md.
- Q-2 Steps at 1536 / 2048 above 2.0 LSB: the comparator kick against the driver resistance (Decision 43b). Layout fix: lower the resistance of the bottom-plate wiring of bits 9-11 (wider,
  shorter). PRE-APPROVED degradation up to 2.5 LSB (static, below the 2.3 LSB rms of amplifier noise). Above: BLOCKED.md.
- Q-3 step_2112 (bridge / bridge-node parasitic) above 0.5 LSB: layout fix: shorten node `m`, remove overlaps of other nets with `m` and with the bridge. PRE-APPROVED degradation up to 1.0 LSB
  (Decision 40a accepts |DNL| > 1 LSB in 4 % of chips). The bridge capacitor size is NOT changed. Above 1.0: BLOCKED.md.
- Q-4 alpha lower by more than 0.02, gain error outside +-0.5 %: capacitance on the DAC top plate (after the MIM correction of flow.py pex it is real): shorten `t`, remove Metal5 over the array.
  PRE-APPROVED up to -0.04 (a gain error of the ADC, no linearity effect).
- Q-5 Settling (adc_timing) above 0.5 LSB at a matched corner: resistance of the bottom-plate wiring or of the sampling path. Layout fix: wider bottom-plate wires, more contacts on the drivers.
  PRE-APPROVED degradation: up to 0.65 LSB at ONE matched corner (the class accepted for the mixed corner by Decision 44f). Mixed corner up to 1.0 LSB is the limit itself.
- Q-6 Top-of-range error grows by more than 1.5 LSB: PRE-APPROVED: narrow the INL claim of the README from 2.0 V (typ) to the highest input that still passes 1 LSB, state it (Decision 43c
  already limits the claim).
- Q-7 Unresolved decisions or failed conversions: re-run once (common rule 8). Still there: look at the comparator supply and clock wiring; BLOCKED.md after three layout attempts.

**C. Digital macro (L1d)**
- C-1 CTS (DPL-0036 or any CTS failure): PRE-APPROVED (Decision 44h), already taken in the LP trial: no CTS + ONE clock buffer `ck.u_ckbuf` in front of the register clock pins, the delay chain
  branching from the same buffered node. Re-run the LP recipe (`bash AFE/dig/run_dig.sh`); do not try to repair CTS.
- C-2 Tap limits of section 3 missed after the final run: PRE-APPROVED retune WITHOUT an RTL edit is not possible (the chain length is in `AFE/adc/rtl/adc_clkgen.v`): first re-run with the
  placement seed / density of the trial; if (a) is 20.0 .. 21.0 ns or (c) is 15 .. 20 ns: PRE-APPROVED degradation (the DAC settles in 15.1 ns at that corner; the window still ends before the next
  DAC edge), state it. Outside: BLOCKED.md.
- C-3 Routing congestion or DRC of the macro at 820 x 110: lower the utilisation by raising the height in 3.92 um steps up to 120 um (`floorplan.py build --set dig_h=...`, the channel slots
  shrink by half of it: check the amplifier margin stays >= 8 %).
- C-4 Gate-level testbench shows another failing assertion than the five allowed: BLOCKED.md with the assertion name and the log.

**A. Area** (amp_ch slot 220 x 263 um = +12 % over the estimate; everything else has more)
Ranked, cheapest first; apply in this order, re-run `floorplan.py check` after each:
- A-1 Rotate amp_ch by 90 degrees (all 8 the same way) if it fits that way. Cost: none.
- A-2 Corridor and macro parameters: `strap_corr` 26 -> 25, `bias_corr` 14 -> 12, `ring` 30 -> 26, `adc_h` 104 -> 100 (if adc_ch allows), `dig_h` -> the final macro height. Gain: up to +14 um of
  amplifier height (+5 %). Cost: tighter top-level routing.
- A-3 Re-run the amplifier generator with another aspect ratio (Cin block 2 x 2 or 1 x 4, OTA beside or below it). Cost: one L2a-type iteration (DRC + LVS + L2b again).
- A-4 Digital macro at higher utilisation (up to 60 %): -0.019 mm2 (AUDIT 4.5 lever 3). Cost: routing effort in L1d.
- A-5 (AUDIT 4.5 lever 1 = Decision 46c) decap under the Cin plates: already not needed for area in this floorplan (decap has no area of its own); it is the reserve for the supply ladder S.
- A-6 N = 4 (channels 0-3 only, one row; the south row stays empty; the unused ADC inputs `cmp_q[7:4]` of afe_dig tied to vss at the top, same SPI frame, words 6-9 read 0): -0.33 mm2.
  Cost: 4 channels. PRE-APPROVED only if A-1 .. A-4 are exhausted AND the amplifier still does not fit.
- A-7 N = 2 (Decision 45 fallback: E[1:0], IPG[1:0], REF; 700 x 600 um): PRE-APPROVED only if the organizer REFUSES the 1000 x 1000 um slot or the 24 pads in writing (then also update
  info.yaml and the README by the same rule). Never by the agent's own judgment of area.
- Not available before tapeout: Cin 20 -> 10 pF (noise, full re-simulation), a shared ADC (Decision 34).

**S. Supply (L3b tb_top_supply)**
- S-1 dres_max_lsb above 0.5 at typ / ss 125, or above 0.8 at ff -40: layout fix 1: more decap on the ADC-main strap from the reserve (up to 16 units per channel under the Cin plates, SPEC.md
  section 4), re-run. Fix 2: series resistance of the decap banks towards 3 ohm (wider or narrower strap spurs; D4: 3 ohm is the best value).
- S-2 Still above: PRE-APPROVED: state "two bond wires per supply pad are required for the 0.5 LSB supply error at ff -40 C 3.6 V" in the README board needs (X2: 1 nH instead of 2 nH takes the
  error from 0.48 to 0.06 LSB) and re-run with Lp = 1e-9, Rp = 0.125 to show it; the transition shift dt_max_lsb must still be <= 0.5 with the default 2 nH. If dt_max_lsb > 0.5: BLOCKED.md.

**X. Crosstalk (L3b tb_top_xtalk)**
- X-1 victim_conv_lsb above 0.5: layout fix: a vss line between the vcmo / vg2 lines and everything else in the bias corridor, shorter stubs; then one 5 x 5 um MIM unit (54.5 fF) from vcmo to vss
  at each channel input is NOT pre-approved (a device change): BLOCKED.md if the layout fix is not enough.

**N. Native-Vt device (audit M7; LP step 6: AFE/amp/sim/lp_rvt_summary.md)**
- N-1 Trigger: the organizer refuses `nfet_06v0_nvt`, or their precheck rejects it. (While there is no answer the layout keeps the native device: it passes the open-source DRC / LVS decks.)
- N-2 PRE-APPROVED swap: use `AFE/amp/spice/ota2_rvt.spice` + `afe_chc_rvt.spice` in place of `ota2.spice` + `afe_chc.spice` (follower = nfet_03v3 8 x 10u/1u in an isolated p-well in a deep
  n-well, bulk on its source, deep n-well on vdd; pins unchanged; +575 um2 per channel); regenerate the LVS references from them (`python3 AFE/layout/scripts/mk_lvs_netlists.py --follower rvt` + the options of the current references, see the header of AFE/layout/lvs/dbs_afe_top.spice; exactly one reference line changes: `Xs2_xota2_xmf vdd xs2_xota2_o2 out out nfet_03v3 w=10u l=1u m=8`, tested in LP); the testbenches take the variant by `AFE_AMP_VARIANT=rvt` (lptb.py);
  replace the follower in amp_ch; re-run DRC, LVS, PEX and every L2b check against the variant numbers of `AFE/amp/sim/lp_rvt_result.json` (same limits; THD <= 0.25 % at all three corners because
  the variant removes the ff 85 clipping), and tb_top_e2e.py typ.
- N-3 If the deep n-well is refused too: `AFE/amp/spice/ota2_rvt_nodnw.spice` (`--follower nodnw`, `AFE_AMP_VARIANT=nodnw`) (10 x 10u/0.28u, bulk on vss): top margin 32 mV at ss -40 C, VDD >= 3.3 V required, f_hi 602 / 925 / 386 Hz: state
  both in the README. If neither is allowed: BLOCKED.md.

**O. Organizer silent**: section 5.

## 5. Organizer defaults (used when no answer has arrived at the start of the phase that needs it)

| item | default | source | phase | if the answer differs |
|---|---|---|---|---|
| macro / top cell name | `dbs_afe_top` | our PR boundary GDS `gds/dbs_afe_top.gds` that the organizer has (Decision 45); template placeholder `A01_topcell`, examples A44_A / A02_A are organizer-assigned | L3a, L4 | rename the top cell, `TOP_SOURCE` in lvs_config.json, the GDS file and the SPICE top by `sed` + regenerate; no layout change |
| DEF / pin positions | floorplan.json `pins` (SPEC.md section 2) | no DEF in the repo on 2026-11-20 | L3a | re-place the pins in the ring lanes, blocks stay (G-6) |
| slot | 1000 x 1000 um | Decision 45; organizer README: 2040 x 2040 um design area for all projects | L3a | smaller slot refused in writing: ladder A-7 |
| pad allocation | 24 pads in the perimeter order of info.yaml: 17 analog (asig_5p0), CS / DIN input_cmos, SCLK / RSTN input_schmitt, DOUT bidirectional (bi_t, 4 mA, fast, input off), VDD (dvdd), VSS (dvss) | resources/info.yaml template (copy in AFE/review/sim/organizer); Decision 45 | L4 | fewer pads: drop nothing by yourself: BLOCKED.md (the pad list is a Decision) |
| supply pads | ONE dvdd and ONE dvss, ours alone, single bond | template comment "subsequent power/ground cells cause a break in the I/O power rails"; padring fork: 4 + 4 for the whole frame | L3b | a shared pair: re-run tb_top_supply.py with the shared current of the other projects unknown: state it as a risk, no change |
| bond wire / pad model | 2 nH + 0.25 ohm per supply pad, 1 pF pad capacitance (ASSUMED) | X2 S4 (Decision 43f); QFN-88 of the organizer README | L3b | other values: put them into the supply model file and re-run; ladder S |
| native-Vt nfet_06v0_nvt | allowed (it is a device of the open-source decks) | organizer checklist lists it as optional | L2b | refused: ladder N |
| deep n-well | available | organizer process table ("Deep nwell transistor option: It is available") | (ladder N only) | - |
| high-resistance poly | ppolyf_u_1k only | organizer process table; PDK decks (Decision 44a) | all | - |
| DRC variant | D (5 metals, 11 kA top metal, MIM option B) | organizer process table; Decision 44a | all | another variant: re-run every DRC with it; BLOCKED.md if a rule set differs |
| metal fill / density | not ours | organizer integration flow | L4 | asked for: run `flow.py drc --density`, add fill with the PDK filler script (libs.tech/klayout/tech/drc/filler_generation), re-run DRC + LVS |
| export-control form | technical answers filled, signature blank | resources/documents | L4 | the signature is a human step |

## 6. Last resort: BLOCKED.md

Write `AFE/layout/BLOCKED.md` only when no ladder entry applies or the ladder says so. Content: phase, the gate line that failed (copied), what was tried (commands, each result), the evidence
files, the smallest decision that would unblock it (one question with 2-3 options and what each costs), and what can continue meanwhile. Commit it, push, stop that phase; the phases that do not
depend on it continue (RUNBOOK.md table "what blocks what"). Nobody is waited for: the user / monitoring session answers through AFE/layout/REVIEW.md, and the next phase applies the answer.

## 7. Feedback: AFE/layout/REVIEW.md

Written only by the user / monitoring session; a phase never edits it. Every phase starts with `git pull`, reads it and applies every open item addressed to it or to an earlier phase
BEFORE its own work (a fix to a finished phase is redone and that phase's gate re-run first), and lists the items in section 9 of its report AFE/layout/reports/<phase>.md. An item may change
this file or a protected file; then the phase follows the item, and gate.py accepts the change when section 9 of the report names the item and the file.
