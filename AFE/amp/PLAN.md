# AFE amplifier: phase A0 plan (no simulation)

Simulation-only course project (ENGN2912E). Not a medical device.
Status: PROPOSAL. Every number below is a hand ESTIMATE unless it says "verified" (meaning read
from a PDK/repo file, not simulated).

## 1. Folder layout (AFE/amp/)

```
AFE/amp/
  PLAN.md                 this file
  README.md               (A5) how to run, results table
  spice/
    models_<corner>.spice   one per corner: design.ngspice + .lib sm141064.ngspice <corner>
                            + .lib sm141064.ngspice mimcap_<typical|ss|ff>  (fs/sf -> mimcap_typical)
    pseudoR.spice           (A2) subckts pseudo_r, pseudo_r_tune
    ota1.spice              (A3) stage-1 two-stage Miller OTA (PMOS input)
    ota2.spice              (A4) stage-2 low-gm OTA
    stage1.spice, stage2.spice, afe_ch.spice   (A3/A4) closed-loop cells
    src_randles.spice       Rs 1k + (Cdl 300n || Rct 50k), REC and REF networks, IDEAL VD balun
    adc_load.spice          R_ADC/C_ADC + sample switch (placeholder values, labelled)
    bias_ideal.spice        IDEAL current/voltage references (VCM_IN, VOUT_CM, IBIAS)
  xschem/                   *.sch / *.sym for ota1, ota2, pseudo_r, stage1, stage2, afe_ch, tb_*
    xschemrc                relative paths only
  tb/                       hand-written testbenches (list in section 2)
  scripts/
    run.sh                  ngspice -b wrapper: tb + corner + temp + params -> sim/<tb>_<corner>_<T>.log
    corners.py              sweeps corner x temp x param, collects .meas into sim/*.csv
    check.py                compares sim/*.csv against the target table, prints PASS/FAIL/REPORT
    plots.py                figs/*.png from csv (wrdata outputs, never *.raw)
    equiv_xschem.sh         netlists xschem/*.sch in batch, runs both netlists, diffs .meas
  sim/                      logs + csv only (*.raw git-ignored, never opened by agents)
  figs/                     png
```

Corner handling: ngspice cannot parameterize a `.lib` section name, so `run.sh` picks
`spice/models_<corner>.spice` through a single `.include models.spice` symlink/copy per run, and
sets temperature with `.temp` / `.options temp=`. Verified: MIM caps are pulled in by sections
`mimcap_typical`, `mimcap_ss`, `mimcap_ff` of sm141064.ngspice (each includes
`sm141064_mim.ngspice cap_mim_new`); the MOS corner sections (`typical`, `ff`, ...) do NOT include them.
Verified: `r_leak = 1/(gleak*c_AREA)` with `gleak = 9.51e-10/5*10000`; units of c_AREA to confirm in A2.
Verified: 3.3 V std-cell liberty tt file is `gf180mcu_fd_sc_mcu7t5v0__tt_025C_3v30.lib` (for the ADC phase).

## 2. Testbench list

| Phase | Testbench (AFE/amp/tb/) | Analysis | Purpose |
|---|---|---|---|
| A1 | char_gmid_p.spice, char_gmid_n.spice | .dc | gm/Id vs Id/(W/L), L = 0.5/1/2/4 u, Vds = 0.5 V |
| A1 | char_noise_p.spice, char_noise_n.spice | .noise | Sv,in(f) 0.1 Hz–10 kHz, several W·L, Id; integrate 0.5–300 Hz; fnoicor=1 repeat |
| A1 | char_icmr_p.spice | .dc | PMOS pair + tail ICMR on 3.3 V |
| A2 | char_pseudoR.spice | .dc, .op | I–V ±100 mV, R_eff, typ/ff/ss × −40/27/85 °C, plain + tunable |
| A2 | tb_hpf_cf.spice | .ac, .noise | HPF corner for candidate Cf incl. MIM r_leak; pseudo-R noise (see 4.1) |
| A3 | tb_ota1_op.spice | .op | region check of every device |
| A3 | tb_ota1_loop.spice | .ac (Tian, 2 runs) | loop gain, unity-gain f, PM, with the real closed-loop network as load |
| A3 | tb_ota1_ol.spice | .ac | open-loop A0, GBW (DC servo through a huge L/R so the op point is set) |
| A3 | tb_st1_ac.spice, tb_st1_noise.spice, tb_st1_tran.spice | .ac/.noise/.tran | stage-1 closed loop with Randles source |
| A4 | tb_afe_1ch_op.spice | .op | output DC vs VOUT_CM, supply current, regions |
| A4 | tb_afe_1ch_ac.spice | .ac | midband gain, fL, fH, CMRR (VCM_AC) |
| A4 | tb_afe_1ch_noise.spice | .noise | integrated noise 0.5–300 Hz; also 0.5 Hz–fs/2 and wideband |
| A4 | tb_afe_1ch_thd.spice | .tran + fourier | swing, THD vs VD, 1 % THD point |
| A4 | tb_afe_1ch_slew.spice | .tran | slew rate at full scale |
| A4 | tb_afe_1ch_pwrup.spice | .tran | power-up settling (seconds of sim time) |
| A4 | tb_afe_1ch_recov.spice | .tran | VOS_REC/VOS_REF step and ART_AMP/ART_DUR/ART_T0 pulse, sweeps |
| A4 | tb_afe_1ch_adc.spice | .tran | output error at sampling instant with ADC load (R_ADC, C_ADC) |
| A4 | tb_afe_1ch_tg.spice | .tran | USE_TG=1: series TGATE.spice (read-only include), switch charge injection |
| all | equiv_xschem.sh | — | xschem netlist vs hand netlist: same .meas within 0.1 % |

The tb_afe_1ch_* files share one parameter header (VD, F_SIG, VOS_REC, VOS_REF, VCM_AC, ART_AMP,
ART_DUR, ART_T0, VOUT_CM, USE_TG, VDD, R_ADC, C_ADC); they are split per analysis so each run is
short and its log holds one kind of measurement.

Source: one IDEAL independent source `VD` (AC 1, SIN for .tran) drives two IDEAL E-sources giving
+VD/2 and −VD/2 into the REC and REF Randles networks around the 1.65 V tissue node. A single
independent source is needed so `.noise` can refer noise to the input.

## 3. Exact measurements per target

ngspice `.control` syntax (results of one `meas` can be reused with `$&name`). Syntax to be
confirmed on the first A1/A3 run; any change gets recorded here.
`vout` = AFE output node, `F_MID = 12.25 Hz` (geometric centre of 0.5–300 Hz).

### T1 Supply 3.3 V
Netlist: `VVDD vdd 0 {VDD}` with `.param VDD=3.3`. Sanity run at 3.0/3.6 V (not a target, reported).

### T2 Gain 1000 (60 dB)
```
ac dec 50 0.01 100k
meas ac g_mid  find vdb(vout) at=12.25
meas ac g_pk   max  vdb(vout)
meas ac f_pk   when vdb(vout)=$&g_pk    (or max_at via let/vecmax)
```
check: report g_mid; proposed tolerance |g_mid − 60| ≤ 1 dB (ASSUMPTION, no tolerance given).
Sign: the Harrison topology is inverting; report the phase at F_MID too.

### T3 Passband 0.5–300 Hz (−3 dB corners)
```
let g3 = g_pk - 3
meas ac f_lo when vdb(vout)=$&g3 rise=1
meas ac f_hi when vdb(vout)=$&g3 fall=last
```
check: f_lo ≤ 0.5 Hz and f_hi ≥ 300 Hz (proposed reading of the target: the passband contains
0.5–300 Hz); also report f_lo/0.5 and f_hi/300 so over-wide bands are visible.

### T4 Input-referred noise ≤ 2 uV rms, 0.5–300 Hz
```
noise v(vout) VD dec 100 0.5 300
setplot noise2
let vn_in_int  = inoise_total            * ngspice integrates over the analysis band
let vn_out_int = onoise_total
let vn_in_mid  = vn_out_int / 10^(g_mid/20)
print vn_in_int vn_in_mid
```
check: vn_in_mid ≤ 2e-6 (primary: integrated output noise / midband gain); vn_in_int is also
reported (it divides by the reduced gain near the band edges, so it is larger).
Units of inoise_total/onoise_total (V vs V²) to confirm in A1 against a resistor (4kTR) check.
Extra runs: `fnoicor=1`; all corners; separate run with the electrode resistors made noiseless
(or the OTA ideal) to split electrode vs amplifier contributions; spectrum 0.05 Hz–100 kHz via
`wrdata` for figs. Extra (not a target, see 4.4): `noise ... 0.5 2k` and `0.5 1Meg` totals.

### T5 Output biased at VOUT_CM (1.5 V default, also 1.65 V)
```
op
let vout_dc = v(vout)
let vout_err = v(vout) - VOUT_CM
```
check: report vout_err; proposed flag if |vout_err| > 50 mV (ASSUMPTION).

### T6 Output range 1.0–2.0 V for ±500 uV (and THD)
```
tran step=20u stop={settle + 10/F_SIG}       * SIN(0 VD F_SIG), VD = 500u, F_SIG = 12.25 and 300
meas tran vout_max max v(vout) from={settle}
meas tran vout_min min v(vout) from={settle}
fourier F_SIG v(vout)                        * over the last N periods (linearize first)
```
check: vout_max ≥ 1.98 and vout_min ≤ 1.02 at gain within T2 tolerance; THD at VD = 500 uV
reported. Sweep VD (100u…2m) and interpolate the 1 % THD point.

### T7 Slew (derived target ≥ 2π·300·0.5 ≈ 942 V/s, ESTIMATE)
```
let dv = deriv(v(vout))
meas tran sr_pos max dv from={t_step} to={t_step+5m}
meas tran sr_neg min dv from={t_step} to={t_step+5m}
```
Input: 300 Hz, VD = 500 uV sine (the real worst case), plus a ±500 uV step (pessimistic).
check: min(sr_pos, −sr_neg) ≥ 942 V/s; also THD of the 300 Hz sine (T6) catches slew distortion.

### T8 Power-up settling (no target; report)
VDD PWL ramp 0→3.3 V in 100 us; `meas tran t_settle when v(vout)` enters VOUT_CM ± 10 mV and
± 1 mV (≈ 1.4 LSB at 12 bit / 3 V), last crossing, sim to ≥ 10 τ_HPF (seconds).

### T9 Recovery (no target; sweep only)
Offset step VOS_REC (and VOS_REF) at ART_T0; artifact pulse ART_AMP, ART_DUR at ART_T0.
`meas tran t_rec` = time after the event until |v(vout) − VOUT_CM| stays < 10 mV (last crossing).
Also `meas tran v_peak max v(vout)` to see rail clipping. Report a table over the sweep.

### T10 Supply current (no target; report)
`meas tran i_avg avg i(VVDD)` and `.op` value of `i(VVDD)`, per corner/temp.

### T11 ADC drive (no target; report)
With the sample switch + C_ADC (placeholder), `meas tran v_err` = v(c_adc) at end of
acquisition − v(vout) without load; report in LSB. See 4.3.

### OTA-level checks (A3, derived)
```
op: for every device: vds - vdsat ≥ 50 mV (saturation), gm/Id, region printed
    (@m.xm1.m0[vdsat] etc.; exact vector names for the PDK subckt to confirm in A1)
loop (Tian): meas ac f_u when vdb(T)=0 ; meas ac pm find vp(T) at=$&f_u  -> PM ≥ 60°
open loop:   meas ac a0 find vdb(out) at=0.01 ; check a0 ≥ 70 dB (derived)
```
Run at typical/ff/ss (× −40/27/85 °C in A4).

### Targets not measured / no pass claim
Electrode DC offset, input CM range, artifact amplitude/duration, recovery time, power, area:
unspecified; swept and reported only. Gain and passband tolerances: proposed above (ASSUMPTION).
CMRR/PSRR: not targets; CMRR reported from the VCM_AC run.

## 4. Things I think are wrong or missing in the architecture hypotheses

4.1 **Pseudo-resistor noise is missing from the budget, and it is large.** The feedback
pseudo-R and Cf form a kT/C-type noise source. Hand ESTIMATE: total output noise of R‖Cf is
√(kT/Cf) = √(4.14e-21/200f) ≈ 144 uV; referred to the input (÷100) ≈ 1.44 uV, of which about
half the power lies above the 0.5 Hz corner → ≈ 1.0 uV rms in 0.5–300 Hz per side. The
non-inverting side has its own Cin/Cf/pseudo-R, so ×√2 → ≈ 1.4 uV rms. Together with the
OTA's flicker noise that could break 2 uV before the input pair is sized. This is not
fixed by a bigger input pair. Options: a lower HPF (e.g. 0.1–0.2 Hz, so the noise bulk falls
below the band), a larger Cf (with Cin ×100 → more area), or define the integration band.
A2 must measure it.

4.2 **Input-pair Cgs vs noise.** Large W·L for flicker noise adds Cgs at the virtual ground;
OTA noise is multiplied by (Cin+Cf+Cgs)/Cin. With Cin = 20 pF a large PMOS pair can add several
pF. A1/A3 should optimize W·L with this factor included, not just the bare-device noise.

4.3 **A few-nA stage-2 OTA cannot drive a SAR sampling capacitor.** The LPF-by-GBW idea makes
the stage 2 output stage weak (gm ≈ 100 nS). A charge-redistribution SAR dumps kickback on
every sample; settling to ½ LSB (0.37 mV) in the acquisition time needs a buffer, or a large
hold/reservoir cap after the LPF (which is then the real LPF). A4 needs T11, and the ADC team
must say what the input looks like.

4.4 **Noise the ADC actually sees.** With a first-order roll-off the noise bandwidth is
≈ π/2·300 ≈ 470 Hz, and any wideband floor aliases into the band. The 0.5–300 Hz figure
under-states what is digitized; also report integrated noise to fs/2 and wideband.

4.5 **Two HPF poles.** If stage 2 is AC-coupled with its own pseudo-R, its HPF stacks with
stage 1's (two poles at 0.5 Hz give f_lo ≈ 0.78 Hz). Put stage 2's HPF well below (≤ 0.1 Hz)
or DC-couple stage 2 (stage-1 output DC = its reference, stage 2 references VOUT_CM).

4.6 **LPF by bias current is PVT-sensitive.** f_hi ∝ gm ∝ Id/(n·UT) in weak inversion:
expect large spread over corners/temperature, so the 300 Hz corner needs a trimmable bias
or an explicit RC/gm-C pole. Slew margin of ~1.6× (estimate) also shrinks at ss/cold.

4.7 **MIM leakage puts a fraction of the electrode DC offset on the gate.** r_leak(Cin) ≈ 50 TΩ
(estimate) vs a 1.6 TΩ pseudo-R gives DC gain R_pseudo/r_leak ≈ 3 % from electrode to stage-1
output; 300 mV offset → ~10 mV at stage-1 output. Fine if stage 2 blocks DC (4.5), but it varies
with temperature and with the pseudo-R (decades over PVT), so A2 should report it.

4.8 **Output range uses only 1/3 of the ADC.** 1.0–2.0 V on a 0–3 V range wastes ≈ 1.6 bits.
Not wrong, but it is a gain-vs-headroom choice for the team (offset/artifact headroom).

4.9 **Anti-aliasing** (agree with NOTES): 1st/2nd order gives 15/33 dB at 2 kHz, far from
74 dB for 12 bits. Oversampling plus digital decimation is the cheap fix; that is an ADC/system
decision.

4.10 **The 5 V TGATE in series with REC.** TGATE.spice uses pfet_05v0/nfet_05v0 with bulk tied to
its VDD/VSS. In the series case its on-resistance adds to Rs (thermal noise, small) and its
charge injection on toggling lands on the high-impedance Cin node, which with a seconds-long
τ_HPF could saturate stage 1. Measured in tb_afe_1ch_tg (no pass claim).

4.11 Agree: 5-T OTA too low gain; stage 1 should not set the LPF; flicker noise dominates the
OTA; electrode loading negligible.

## 5. Assumptions

- Stage 1 = Harrison-type: REC via Cin to the inverting input, REF via a matched Cin to the
  non-inverting input with a matched Cf/pseudo-R to VCM_IN. Gain is inverting.
- VCM_IN (gate bias) is an IDEAL source in A3/A4, value chosen from the A1 PMOS-pair ICMR
  (probably 1.0–1.65 V). VOUT_CM and all bias currents are IDEAL in the first pass.
- "Passband 0.5–300 Hz" means −3 dB corners; the check is f_lo ≤ 0.5 and f_hi ≥ 300.
- Noise target uses integrated output noise / midband gain (both definitions reported).
- Gain tolerance ±1 dB and output-CM flag 50 mV are proposals, not requirements.
- ADC load values: placeholders until the ADS7953 datasheet is read (or the team's GF180 SAR
  is defined); labelled PLACEHOLDER in the netlist.
- Typical corner MIM = mimcap_typical; ff/ss MOS → mimcap_ff/ss; fs/sf → mimcap_typical.
- Single-ended output into a single-ended ADC.
- Stage-2 gain sign/inversion does not matter to the ADC.
