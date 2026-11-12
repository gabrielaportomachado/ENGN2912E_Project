# AFE handoff notes (read this first, every session)

Simulation-only course project (ENGN2912E). Not a medical device; never connect to a person.

This file is the shared context for every agent session working on the amplifier
(AFE/amp/) and the ADC (AFE/adc/). Keep it short. At the end of every phase, update
the "Results log" and "Open questions" sections below with verified numbers only.

## Environment (verified 2026-11-12)
- Run inside container `iic-osic-tools_chipathon_xvnc_uid_501`
  (image hpretl/iic-osic-tools:chipathon26). Repo at /foss/designs/ENGN2912E_Project.
- ngspice-46 and xschem are on PATH. LibreLane is at /usr/local/bin/librelane.
  ngspice ships the Icarus co-simulation bridge (ivlng.so / ivlng.vpi): check it works
  before relying on it.
- PDK_ROOT=/foss/pdks, PDK=gf180mcuD.
- Model setup:
  .include /foss/pdks/gf180mcuD/libs.tech/ngspice/design.ngspice
  .lib /foss/pdks/gf180mcuD/libs.tech/ngspice/sm141064.ngspice typical
  Corners: typical ff ss fs sf. MIM caps come from sm141064_mim.ngspice (section
  cap_mim_new); find which .lib section of sm141064.ngspice pulls them in and include it.
  Statistical sections exist: nfet_03v3_stat, pfet_03v3_stat, mimcap_statistical.
- design.ngspice defaults: sw_stat_global=0, sw_stat_mismatch=0, fnoicor=0.
  Use fnoicor=1 for a worst-case flicker-noise run.

- xschem batch (A3): it HANGS if DISPLAY points at an unreachable X server (DISPLAY=:20 here). Use
  `(unset DISPLAY; cd AFE/amp/xschem && xschem --rcfile xschemrc --tcl 'set top_is_subckt 1' -n -s -q --no_x -o netlist ota1.sch </dev/null)`.
  Headless SVG/PNG export draws nothing. PDK symbols are referenced as `symbols/pfet_03v3.sym`; the MIM symbol's default model name
  (cap_mim_2f0fF) is overridden with model=cap_mim_2f0_m2m3_noshield.
- ngspice (A3): nonzero ad/as/pd/ps on the PDK MOSFETs make `.tran` fail ("timestep too small" at ~1 us, UNEXPLAINED): set them to 0 explicitly
  (the xschem symbols pass them by default). Vectors: `@m.xota.xm1.m0[vds]`, `v.xs1.vbrk#branch`; `.dc` sweeps need explicit `save` of device
  parameters; `meas` results and `.param` names are not visible after `setplot` / inside `.control` (carry them with `set v = $&x`); use `cph()`
  for unwrapped phase. A failed `.tran` prints one enormous line: always pipe ngspice output through `cut -c1-200 | head`.

## PDK facts (verified)
- 3.3 V devices: nfet_03v3 / pfet_03v3 (default L=0.28u). Xschem symbols
  pfet_03v3.sym / nfet_03v3.sym; netlist format `X... d g s b pfet_03v3 L= W= nf= m=`.
- The existing TGATE uses 5 V devices (pfet_05v0/nfet_05v0). Do not copy them.
- MIM: cap_mim_2f0_m2m3_noshield (~2 fF/um^2; also 1f0, 1f5 variants), symbol
  cap_mim_2f0fF.sym (params W, L). The model includes r_leak = 1/(gleak*area), which
  matters next to TΩ pseudo-resistors and for the ADC hold node.
- Std cells gf180mcu_fd_sc_mcu7t5v0 / mcu9t5v0 have 3.3 V liberty corners
  (e.g. ss_125C_3v00, ff_n40C_3v60; confirm the tt file name). The existing digital
  chip (rtl/dbs.v) was hardened at 5 V corners.

## Source signal / electrode (verified, ENGN 1600 report Fig. 4)
- Randles: source -> Rs 1k -> (Cdl 300n || Rct 50k) -> E_pin. The report used a
  single-ended 100 uV sine on a 1.65 V bias.
- This project uses TWO networks (recording + reference electrode) sharing a 1.65 V
  tissue node, driven by +VD/2 and -VD/2 (differential, zero-centred, VD up to 500 uV pk).
- Hand estimate (confirm in sim): electrode thermal noise ≈ 0.13 uV rms per electrode
  over 0.5–300 Hz, so nearly all of the 2 uV budget belongs to the amplifier.

## Targets (simulation targets, not verified requirements)
Amplifier: 3.3 V; gain 1000x (60 dB); passband 0.5–300 Hz; input-referred noise
≤ 2 uV rms integrated over 0.5–300 Hz; output biased for the ADC (VOUT_CM parameter,
default 1.5 V, also check 1.65 V; ±500 uV x 1000 → 1.0–2.0 V around 1.5 V).
ADC: 12-bit SAR, 3.3 V, serial output, 4 kS/s PER CHANNEL × 16 channels (ASSUMPTION:
confirm with team; 4 kS/s total would be only 250 S/s per channel, below the 600 S/s
that 300 Hz needs). Stretch goal: 14–16 bit.
Unspecified (parameterize, never claim tolerance): electrode DC offset, input
common-mode range, stimulation artifact amplitude/duration, recovery time, power, area.

## ADS7953 (external benchmark only, not a GF180 macro)
Product page only: 16-ch single-ended, 12-bit SAR, 1 MSPS, SPI, AVDD 2.7–5.25 V,
ranges 0–VREF / 0–2xVREF. VREF limits, input capacitance and acquisition time are
UNVERIFIED: read the datasheet before using them.

## Rules for every session
1. Write new files only under AFE/. Never edit rtl/, ROW/, TGATE/, FSM*/, MODE+FSM/,
   RDY/, config.json, flow_out/ or the std-cell folders. Including them read-only is OK.
2. Never open *.raw, flow_out/**, **/PEX/**, *_extracted.cir (large; wastes budget).
3. Every reported number must come from a log saved under AFE/<block>/sim/. Hand
   calculations are estimates; label them as such.
4. Every target has an explicit .meas (or script check) in a testbench. List any target
   you could not measure.
5. Size from simulated gm/Id and noise characterization, not rules of thumb. A pass at
   one corner proves nothing about the others.
6. Ideal sources/references are allowed in a first pass; label them IDEAL in the
   netlist and in this file.
7. Use relative includes for your own files. No hard-coded /foss/designs/DBSchip paths.
8. Xschem: author .sch files, netlist in batch (xschem -n -s -q ...), and confirm the
   xschem netlist simulates the same as the hand netlist.
9. Stop at the end of each phase and wait for approval.

## Architecture hypotheses (to confirm or reject with simulation)
Amp: stage 1 = AC-coupled capacitive-feedback amp, gain Cin/Cf ≈ 100, PMOS-input
two-stage Miller OTA, pseudo-resistor feedback for the ~0.5 Hz HPF; input caps block
electrode DC; the gates are biased on chip at VCM_IN. Stage 2 = capacitive gain ≈ 10
referenced to VOUT_CM (the level shift), with a low-gm OTA so that closed-loop
bandwidth sets the ~300 Hz LPF; it drives the ADC load. Fallback if 1/f noise can't
reach the target: chopper (transient-noise sim).
ADC: charge-redistribution SAR (binary or split MIM cap DAC), dynamic comparator with
preamp, SAR logic + serial shift-out in Verilog. One ADC behind a 16:1 mux needs
≥64 kS/s aggregate; alternatively one ADC per channel. That is a team decision.

## Planning-session hand estimates (ESTIMATES ONLY; verify each in simulation)
From the 2026-11-12 planning session; the reasoning behind the hypotheses above.
- Gain split 40 dB + 20 dB: stage-1 output stays small (±50 mV nominal), stage-2
  noise referred to the input is divided by 100 (≈0.1 uV estimate), and the remaining
  swing is headroom for the unspecified offsets and artifacts.
- Stage-1 feedback factor β ≈ Cf/(Cin+Cf+Cgs) ≈ 0.01, so the loop is easy to
  stabilize, but OTA open-loop gain must be ≥ ~70 dB (loop gain ≥ ~30) to keep the
  gain error to a few percent. A 5-transistor OTA is likely too low; use two-stage Miller.
- Stage 1 should not set the 300 Hz LPF: fH ≈ gm·Cf/(2π·CL·Cin) with gm ≈ 50 uS would
  need CL ≈ 265 pF. So the LPF goes in stage 2.
- Stage 2: β ≈ 1/11, so fH = 300 Hz needs a closed-loop GBW ≈ 3.3 kHz (e.g. Cc = 5 pF,
  gm ≈ 100 nS, a few nA). Slew needed for 0.5 V pk at 300 Hz ≈ 940 V/s; a weak-inversion
  pair gives SR ≈ ω_GBW·2nUT ≈ 1500 V/s, only ~1.6x margin. Lower gm/Id (long L or
  degeneration) buys slew. fH tracks the bias current and temperature: check at corners.
- HPF: Cf = 200 fF at 0.5 Hz needs ~1.6 TΩ, so pseudo-resistors are the only option
  (strongly PVT dependent: consider a tunable one or a DC servo). τ ≈ 0.32 s, so
  power-up/recovery settling takes seconds of simulated time.
- Cin ≈ 20 pF of MIM ≈ 10,000 um² each, 2 per channel, 32 for 16 channels: large area.
  MIM r_leak for 20 pF ≈ 50 TΩ (≈3% DC leak path versus a 1.6 TΩ pseudo-R); Cf leak
  is negligible.
- Electrode loading: |Z_e| ≈ 51 kΩ at 0.5 Hz versus 1/(ωCin) ≈ 16 GΩ, so negligible.
- Input bias: the ±500 uV never touches a gate; it sits on the electrode side of Cin.
  Gate DC = VCM_IN through the pseudo-resistors. The tissue/reference node is at 1.65 V
  in the testbench (as in the report), so pads stay inside the rails.
- Flicker noise dominates 0.5–300 Hz; meeting 2 uV is mainly an input-pair W·L (area)
  question. ngspice has no PSS/pnoise, so a chopper fallback needs transient noise.
- Anti-aliasing: a 1st/2nd-order roll-off at 300 Hz gives only ~15/33 dB at a 2 kHz
  Nyquist frequency (4 kS/s), which is weak for 12 bits.
- ADC: with VREF = 3.0 V and the 0–VREF range, mid-scale is 1.5 V (not 1.65 V). At
  12 bits over 3 V, the LSB ≈ 0.73 mV.
- Supply domains: the existing digital and TGATE are 5 V; the amp is 3.3 V. The REC node
  can see IPG (step-up) excursions and switch charge injection; the amp input
  protection is undefined.

## Decisions
Approved by the user after A0 (2026-11-12).
1. Targets accepted as proposed in AFE/amp/PLAN.md: gain within ±1 dB of 60 dB; passband
   f_lo ≤ 0.5 Hz and f_hi ≥ 300 Hz (-3 dB corners); noise = integrated output noise ÷
   midband gain, 0.5–300 Hz, ≤ 2 uV rms (the ngspice input-referred total is also reported).
2. The HPF corner may go below 0.5 Hz if A2 shows pseudo-resistor noise requires it; report
   the recovery-time cost (longer tau_HPF) alongside.
3. A4 must include an output buffer or reservoir-cap option for the ADC drive.

Approved by the user after A1 (2026-11-12).
4. The 2 uV noise target applies at typical flicker (fnoicor=0, tt, 27 C). Always also report the
   fnoicor=1 result as a risk (A1: about 3.4x worse). The chopper option stays open for after A3.
5. A3 starts from the A1 table (AFE/amp/sim/a1_summary.txt) rows with PMOS pair 16x50u/2u and NMOS
   load 1-2 x 50u / 16u (rows 10-11), not the 8u load. Subject to an .op headroom check of the load
   Vgs versus the input pair at VCM_IN.
6. A2 must find the HPF corner that keeps the in-band pseudo-resistor noise low enough that it plus
   the OTA noise (1.39-1.46 uV) is <= 2 uV, and report the recovery-time cost (tau_HPF) of that corner.

Approved by the user after A2 (2026-11-12).
7. The simulated pseudo-resistor value is not trusted (the 4-6 TOhm floor is unexplained, A2). A3/A4 must sweep the
   feedback resistance as a parameter over 0.5-50 TOhm and report f_lo, in-band noise and recovery time across that range,
   alongside the as-simulated pseudo-resistor device.
8. Every noise simulation replaces the pseudo-resistor with an ideal resistor of the same value (noise-conservative, since
   the PDK pfet noise is ~3x below 4kT/R). Label it IDEAL RESISTOR (noise) in the netlist.
9. The vt = +0.2 V gate shift may stay IDEAL in A3. A4 must replace it with a real bias circuit and report it.

Approved by the user after A3 (2026-11-12).
10. fnoicor=1 noise (4.2-5.2 uV, A3) is accepted as a documented risk. Keep the continuous-time architecture through A5; a chopper version is
    optional follow-up work after A5.
11. Keep the m=2 NMOS load (50u/16u, gate area 9200 um^2; the m=1 load is not used).
12. A4 constraints: stage-2 input capacitance <= 5 pF (A3: PM 64 deg at 5 pF, 54 deg at 10 pF); the fast-settle switch is REQUIRED, not optional; the vt
    shift and the bias (IBIAS, VCM_IN) must be real circuits.
13. The zeroed ad/as/pd/ps (A3 workaround) must be fixed in A4. First check whether the transient failure is caused by a .param NF clash with the PDK's nf
    (A3 status, verified by grep: no .param named NF/nf exists in AFE/amp/spice or tb; nf=1 appears only as an instance parameter, so a clash there is not
    the cause in the A3 files; the cause remains UNEXPLAINED). At minimum, rerun op/ac/noise with real diffusion parameters and report the change.
14. A4 is split. A4a = stage 2 + output buffer + real vt-shift/bias + fast-settle switch circuit + diffusion fix, with op/ac/noise only. A4b = all transient
    tests (THD/swing, slew, power-up, offset/artifact recovery with and without fast-settle, TGATE, ADC load) and the corner table. Each sub-phase stops for approval.

## A1 findings (typical corner, 27 C only; logs in AFE/amp/sim/, plots in AFE/amp/figs/)
- ngspice facts: inoise_total / onoise_total are rms volts, in plot noise2 (spectra are in
  noise1); checked on 1 Mohm: 2.207 uV vs hand 2.2 uV (sim/char_noise_check_R.log).
  `nf=` does NOT scale W in these models (bin max W = 100u per device): use m= for wide
  devices. Do not name a .param NF/LN/LP/MP... (clashes with subckt params / ln()). Plain
  `alterparam` after `alter`/`noise` fails, so sweeps use scripts/run_*.sh (sed on .param).
  Use `bash script.sh` (scripts are not executable here).
- gm/Id (char_gmid_{n,p}, figs/gmid_{n,p}.png): peak 27.7 (n) / 26.8 (p), independent of L;
  pfet at Id/(W/L)=1e-7 A: 16.6, at 1e-6 A: 7.1 (L=2u).
- Single-device noise (sim/char_noise_{p,n}.csv, 0.5-300 Hz, rms input-referred, typ):
  pfet 800u/2u 10 uA: 0.64 uV; nfet 800u/2u: 0.81 uV; fnoicor=1 is ~3.4x worse (pfet), same
  trend nfet. Flicker dominates; noise ~ 1/sqrt(W*L).
- ICMR (char_icmr_p, 5T follower, pair 4x50u/2u, tail 2x50u/2u, 20 uA IDEAL Iref, margin
  50 mV, follower error < 5 mV): 0.12 V to 2.21 V (sim/char_icmr_p.log). VCM_IN of 1.0-1.65 V
  is inside; the upper limit is the tail's headroom.
- Whole-OTA noise (5T OTA as follower, real pair+tail+NMOS mirror load; sim/char_ota5t_*.csv,
  sim/a1_summary.txt): the NMOS mirror load is as important as the pair, so it needs a long L
  (low gm) and area. First recommendation: PMOS pair W=800u (16x50u) L=2u, 10 uA per side
  (gm/Id about 20); NMOS load 4x50u/8u: 1.33 uV (OTA input), x1.21 for (Cin+Cf+Cgg)/Cin
  with Cgg=4.0 pF and the ESTIMATED Cin=20 pF, Cf=0.2 pF -> 1.61 uV, area about 6400 um^2.
  Superseded by Decision 5: A3 starts from load 1-2x50u/16u (1.20/1.15 uV OTA, 1.46/1.39 uV
  with the Cgg factor, 4800/6400 um^2). A larger-L pair (4u, Cgg 7.8 pF) buys little.
- WORST CASE NOT MET: with fnoicor=1 the 4x50u/8u sizing gives 4.44 uV (5.4 uV with the Cgg
  factor); the 16u loads give 3.9/3.7 uV. Reaching 1.8 uV there needs roughly 10x the area
  (ESTIMATE from 1/sqrt(WL)) or a chopper (Decision 4).
- OTA 1.4-1.5 uV plus the ESTIMATED 1.4 uV pseudo-R kT/C noise (A0) is about 2.0-2.1 uV: A2
  must settle this (Decision 6).
- Not done in A1: other corners/temperatures; thermal-vs-flicker split of the pair; mismatch/offset;
  only one tail current (20 uA) and one pair current (10 uA per side) for the OTA check.

## A2 findings (pseudo-resistor; 1u/2u PMOS pair, 3 corners x -40/27/85 C; logs in AFE/amp/sim/, plots in AFE/amp/figs/)
- Cell (spice/pseudoR.spice): `pseudo_r` = two diode-connected pfet_03v3 back to back (bulk=source);
  `pseudo_r_tune` shifts the shared gate by vt relative to the mid node (vt>0 weaker, vt<0 stronger). vt is an IDEAL
  level shifter (B-source): no circuit for it yet. Corner models: spice/models_{typical,ff,ss}.spice (MOS + mimcap_<corner>).
- ngspice facts: for TOhm devices use `.options gmin=1e-16 abstol=1e-20` plus a .nodeset on the mid node (default gmin 1e-12
  gives 1.4 TOhm, a wrong answer); `noisy=0` on a resistor removes its noise; scripts/run_pseudoR.sh, run_pseudoR_iv.sh, run_hpf_cf.sh.
- R0 (small-signal at 0 V, sim/char_pseudoR.csv; I-V sim/char_pseudoR_iv.csv, figs/pseudoR_iv.png): typ 27 C vt=0:
  5.2 TOhm (+-100 mV chord 10 TOhm). It is NOT channel conduction: it sits on a floor of 4.1 TOhm (-40 C) to ~6 TOhm (85 C)
  that does not depend on W, L, gate bias or gmin. A single off pfet shows the same ~10 fA at 0.1 V, so it is probably (UNCONFIRMED) the
  PDK model's source/drain-bulk junction leakage, but its temperature trend is unphysical. Not GMIN (see GMIN CHECK). Below it the channel takes over only when hot/fast: ff 85 C vt=0: 0.42 TOhm
  (typ 85 C: 3.1 TOhm; ss 85 C: 5.8 TOhm); vt=-0.1 gives 0.04 TOhm (ff 85 C). Longer L (4u) only helps hot corners slightly.
  I-V is symmetric (checked: +-100 mV chord resistances equal to <0.01 %).
- GMIN CHECK (sim/gmin_check.csv, scripts/run_gmin_check.sh): the floor is NOT ngspice's GMIN. With .options gmin=1e-15 and 1e-18
  (earlier 1e-16/1e-20 gave the same) R0, f_lo and noise are unchanged: typ 27 C vt=0: R0 5.18/5.20 TOhm, f_lo 0.149 Hz, noise PDK
  0.301 uV vs IDEAL 4kT/R 0.943/0.941 uV; typ 27 C vt=0.2: 5.22/5.24 TOhm, 0.148/0.147 Hz, 0.284 vs 0.939/0.938 uV; ff 85 C vt=0:
  0.415 TOhm (both), f_lo 1.99 Hz, 4.04 vs 3.81 uV; ff 85 C vt=0.2: 5.44/5.45 TOhm, 0.156 Hz, 0.589/0.587 vs 1.119/1.117 uV. Only
  gmin=1e-12 (the default) changes the answer (1.4 TOhm). Reason: gmin 1e-15 S x 0.1 V = 1e-16 A, 100x below the ~1e-14 A seen.
  Decision 6 recommendation UNCHANGED (vt=+0.2 V, Cf=200f, f_lo 0.11-0.21 Hz). The floor's origin and its odd T trend (R rises
  with T, constant to 6 digits across W/L/vt>=0.1) remain UNEXPLAINED: do not rely on a TOhm value as silicon fact; one more check
  would be the model's diode/junction parameters or an op-point dump of the off pfet currents. A1 re-check with the new
  models_typical.spice: pfet 16x50u/2u, 10 uA, typ 27 C, fnoicor=0 -> Vsg 0.742691, gm 2.04975e-4, vn 0.637587 uV, identical to
  sim/char_noise_p.csv.
- NOISE MODEL WARNING: the PDK pfet's .noise in this cell is far below 4kT/R: with the same R, in-band input-referred
  noise 0.30 uV (pfet pseudo-R) vs 0.94 uV (IDEAL 5.2 TOhm resistor, electrodes noiseless; sim/hpf_check.csv). Output
  kT/C-type total (R||Cf, both sides) of the ideal resistor 208 uV vs the hand value sqrt(2)*144 = 204 uV (A0 estimate: checks).
  So all noise numbers below use an IDEAL 4kT/R resistor at the simulated R0 (conservative; the equilibrium noise of a
  conducting diode/channel is 4kTG).
- HPF corner (hpf_*.csv, a2_summary.txt; IDEAL op-amp, Harrison both sides, Randles electrodes, Cin = 100 Cf, MIM incl.
  r_leak): Cf = 200 fF / Cin 20 pF: 5.2 TOhm gives f_lo = 0.148 Hz (tau = 1/(2 pi f_lo) = 1.1 s); the MIM capacitors measure
  ~1 % low/high in ratio (gain 39.6 dB, not 40: perimeter term), so the CF values above are nominal.
- Noise vs corner (feedback R + electrodes, input-referred, 0.5-300 Hz; figs/hpf_noise_vs_flo.png, ideal-R sweep
  sim/hpf_rsweep.csv): Cf=200f: R=1 / 1.6 / 2.5 / 5.2 / 10 TOhm -> f_lo 0.77 / 0.48 / 0.31 / 0.148 / 0.077 Hz,
  noise 2.06 / 1.65 / 1.34 / 0.96 / 0.73 uV. Cf=400f (Cin 40 pF): 0.5 / 1 / 2.5 TOhm -> 1.46 / 1.06 / 0.70 uV. Electrodes add
  only ~0.2 uV (0.96 vs 0.94 uV).
- DECISION 6 ANSWER. Budget: sqrt(2^2 - 1.46^2) = 1.37 uV for everything except the OTA (1.44 uV for the 1.39 uV OTA row).
  For Cf=200f that needs R >= ~2.4 TOhm, i.e. f_lo <= ~0.3 Hz (tau >= 0.5 s). The plain pseudo_r at vt=0 FAILS at hot/fast
  corners (ff 85 C: 3.8 uV, typ 85 C: 1.33 uV only just passes; ff 27 C vt=-0.1: 1.92 uV). With vt = +0.2 V (weaker device) Cf=200f
  passes at every corner/temperature: f_lo 0.109-0.208 Hz, noise 0.86-1.14 uV (worst ff 85 C 1.136 uV), tau 0.78-1.47 s,
  total with the OTA sqrt(1.136^2+1.46^2) = 1.85 uV (typical 27 C: 0.957 -> 1.75 uV), all at typical flicker. So the HPF corner
  should be about 0.1-0.2 Hz, not 0.5 Hz; recovery-time cost: tau 0.8-1.5 s instead of 0.32 s (to settle to 1 %: ~4.6 tau = 3.6-6.8 s).
  With Cf=400f (Cin 40 pF, 2x area) the noise drops to 0.47-0.62 uV (worst: ff 85 C vt=+0.2) and tau 1.7-3.2 s.
  The tuning voltage is the real design variable (vt = +0.1 at ff 85 C only gives 1.59 uV): A3 needs a vt generator or a fixed
  longer/series device; the junction floor (4-6 TOhm) means that even vt >> 0.2 buys nothing.
- DC leakage (MIM r_leak vs pseudo-R, sim/hpf_pvt.csv, REC side offset 0.1 V): vout shifts by 0.08-0.12 V per V at 5 TOhm
  (Cf 200f, Cin 20 pF: 7.8 mV per 100 mV offset at -40 C, 9.9 mV at 27 C, 11.8 mV at ss 85 C); 0.16-0.25 per V at Cf=400f
  (r_leak scales with 1/area). Larger than the A0 estimate (3 %) because the pseudo-R is 5 TOhm, not 1.6. Stage 2 must block
  this DC (A0 4.5) or it eats headroom: 300 mV electrode offset -> ~30 mV at stage-1 output.
- Not done in A2: xschem cell, mismatch (pseudo-R pair), tuning-voltage generator, a real op-amp (noise with the OTA is only
  quadrature-added from A1), fnoicor=1 (the pseudo-R model has no flicker term that matters here), L other than 2u/4u, W other than 1u.

## A3 findings (stage-1 OTA + closed loop; typical/ff/ss x -40/27/85 C; logs sim/a3_*.log, tables sim/a3_summary.txt, plots figs/a3_*.png)
- Design (spice/ota1.spice + ota1_params.spice + xschem/ota1.sch/.sym; xschem == hand netlist: 9 devices identical, 51+ simulated values equal,
  sim/a3_equiv_xschem.log): PMOS pair 16x50u/2u (10 uA/side), tail/bias/M7 PMOS 50u/4u m=2 each (IBIAS 20 uA IDEAL), NMOS mirror load m=2 x 50u/16u
  (Decision 5 row 11), 2nd stage NMOS m=4 x 50u/16u (same L/Vgs as the load; |output offset| <= 15 uV at all 9 PVT), Miller Cc ~1 pF MIM (22x22 um, hand calc), VCM_IN = 1.5 V
  (IDEAL), Cf = 200 fF, Cin = 20 pF (MIM sized from the PDK area+perimeter formula, so the ratio is exactly 100). 60 uA from 3.3 V. Gate area 9200 um^2
  (load m=1: 6000 um^2, noise +3 %: 1.728 vs 1.675 uV, PM 77 vs 73 deg). The pair bulk is on VDD (Vsg 1.05 V at VCM_IN 1.5 V; a pair in its own n-well was not tried).
- .op / headroom (Decision 5): at VCM_IN 1.5 V load Vgs = 0.782 V, pair Vsd 1.77 V vs Vdsat 0.057 V. Every transistor has |Vds|-|Vdsat| >= 0.427 V at all 9
  PVT points (criterion 0.05 V). Follower range with all margins >= 50 mV: 0.19-2.21 V; low end set by M6 (output), high end by the tail; pair/load never limit.
- Open loop A(s) (DC servo, load Cf + 2 pF PLACEHOLDER stage-2 input C): A0 117.4-118.8 dB (>= 70 OK), dominant pole 32-51 Hz, GBW 4.0-6.0 MHz. A(s) alone is NOT
  unity-gain stable (PM -45..-50 deg at feedback factor 1): never use this OTA as a unity buffer.
- Real loop (Tian two-injection, validated against an analytic loop to 1e-13 dB, sim/a3_tian_check.log): PM 70.4-75.7 deg at all 9 PVT (>= 60 OK), fu 197-339 kHz,
  T(100 Hz) 60.1-61.5 dB. T is flat at ~62 dB below 100 Hz, not A0-42 = 76 dB: M2's Cgd feeds the high-gain o1 node back onto the REF-side gate (anchored only by Cin2)
  and divides the forward gain (CONFIRMED: with vp AC-grounded by an IDEAL 1 F, T(100 Hz) = 68.07 dB vs 60.79 dB, PM 72.3 vs 73.4 deg; sim/a3_diag.log).
  Harmless (0.1 % gain error) but it means the REF-side network impedance matters. Stage-2 input C (CL_NEXT): PM 79 / 73 / 64 / 54 deg at
  0.5 / 2 / 5 / 10 pF, so keep it <= ~5 pF.
- Closed loop with the simulated pseudo-R devices (vt = +0.2 V IDEAL, Decision 9): gain 39.85-39.88 dB, f_lo 0.110-0.205 Hz (<= 0.5 OK), f_hi 270-522 kHz (stage 1 does not set
  the 300 Hz LPF). The ideal-R bench gives 39.992 dB, so the 0.12 dB deficit is the pseudo-R devices' parasitic C added to Cf (~2.9 fF per side, derived from 39.992 vs 39.869 dB; sim/a3_diag.log): size Cf ~ 197 fF.
  REC-only and REF-only gains are identical (39.869 dB); common-mode gain -69.5 dB at 12 Hz (sim/a3_diag.log) (ideal matched caps: CMRR 109 dB; MIM mismatch NOT modelled).
- Noise 0.5-300 Hz, input-referred = integrated output / midband gain, IDEAL RESISTOR (noise) = R0 per corner (Decisions 4, 8): typical flicker 1.52-1.84 uV at all 9 PVT
  points (<= 2 OK; worst ff 85 C 1.838 uV, typ 27 C 1.675 uV). fnoicor=1: 4.20-5.25 uV (2.7-3.0x), NOT met (Decision 4 risk). Noise to 2 kHz: 1.77-2.18 uV (> 2 at 85 C);
  to 1 MHz: 10.8-14.9 uV (stage-1 wideband; the stage-2 LPF / anti-alias must handle it, see 4.4).
- Feedback-R sweep, ideal R, typ 27 C, Cf 200 fF (Decision 7; sim/a3_summary.txt section 5): R = 0.5 / 1 / 1.6 / 2.5 / 5 / 10 / 20 / 50 TOhm -> f_lo 1.60 / 0.80 / 0.50 / 0.32 / 0.16 /
  0.080 / 0.040 / 0.016 Hz; total noise 2.24 / 2.12 / 1.995 / 1.86 / 1.69 / 1.57 / 1.50 / 1.46 uV (OTA+electrodes floor 1.27-1.43 uV, R alone 1.84 -> 0.29 uV); fnoicor=1 total
  4.56-4.78 uV for every R. Noise 2 uV and f_lo 0.5 Hz are the same limit: R >= ~1.6 TOhm. Recovery (time to within 10 mV of the final value at the stage-1 output after a 1 mV REC offset
  step = 100 mV excursion; ~2.3 R*Cf): 0.23 / 0.45 / 0.74 / 1.15 / 2.30 / 4.58 / 9.14 / 22.7 s, to 1 mV 0.46 ... 45.4 s. MIM r_leak leaves a DC shift of 0.011 / 0.020 / 0.032 / 0.049 / 0.11 / 0.20 / 0.39 / 0.96
  mV per mV of step (R/r_leak; at 50 TOhm the DC path is nearly 1:1).
- Recovery with the simulated pseudo-R device (typical 27 C): 1 mV step 3.7 s to 10 mV (6.3 s to 1 mV); 5 mV / 10 mV steps (0.5 / 1 V excursion, no clipping, vout_min 0.50 V) 11.7 / 12.0 s; worst
  ss -40 C 10 mV: 22.5 s; fastest ff 85 C: 2.6-3.6 s. Larger steps are SLOWER than an ideal 5.2 TOhm (4.6 s): the device current saturates near 10 fA (A2 floor), a ~0.05 V/s discharge rate
  at 200 fF (ESTIMATE; depends on the unverified model floor).
- Not done in A3: fs/sf corners; mismatch/offset/CMRR with cap mismatch (no Monte Carlo); real bias circuit and vt generator (both IDEAL, Decision 9: A4); large-signal swing/THD/slew,
  power-up, input protection, TGATE (A4); junction/diffusion parasitics (ad/as/pd/ps = 0) and layout/Cin bottom-plate parasitics; the xschem drawing was not viewed (no display).

## Open questions
- (A2) After each TREAT->REC switch the amp needs ~5 x tau_HPF (about 4-7 s at tau 0.8-1.5 s) to settle. A4 should evaluate a fast-settle switch (shorting the pseudo-resistors for a few ms, driven by REC_EN/READY): charge injection, residual offset, and the settling time versus switch duration.
- (A2) Is the PDK-model junction floor (4-6 TOhm, T-independent) trustworthy? And a vt generator (+0.2 V gate shift) is needed in A3; PDK pfet noise in the pseudo-R is below 4kT/R: confirm the model with the instructor/PDK docs if the pseudo-R noise is to be claimed.
- Per-channel vs total sample rate; one muxed ADC vs 16 ADCs.
- Is a teammate designing the ADC? (Avoid duplicate work.)
- ADC reference: external VREF (3.0 V?) or on chip?
- 3.3 V amp input vs the 5 V TGATE REC node: input protection, charge injection when
  the switch toggles, IPG step-up excursions.
- Anti-aliasing order vs ADC sample rate.
- (A0) Pseudo-R kT/C noise: ESTIMATE ≈1.4 uV rms input-referred (both sides, Cf=200 fF,
  0.5 Hz HPF) before any OTA noise. Lower the HPF, raise Cf, or redefine the band? Measure in A2.
- (A0) Who drives the SAR sampling cap? A few-nA stage-2 OTA cannot settle it; need a buffer
  or a reservoir cap. Needs the ADC input model from the ADC side.
- (A0) Gain/passband tolerances are not given; A0 proposes ±1 dB and f_lo ≤ 0.5, f_hi ≥ 300.

- (A3, settled by Decision 10) fnoicor=1 is 4.2-5.2 uV: accepted as a documented risk; chopper (transient noise sim) or ~10x input-pair area only as optional work after A5. Typical flicker meets 2 uV with 8-24 % margin (1.52-1.84 uV).
- (A3) HPF choice: R >= ~1.6 TOhm meets both f_lo <= 0.5 Hz and 2 uV; R0 of the device (4.1-6.2 TOhm) gives 0.11-0.2 Hz and ~1.7 uV but 2.6-4.0 s recovery (to 10 mV) for a 1 mV step and up to 22 s for 5-10 mV
  steps. A4a (Decisions 12, 14): fast-settle switch circuit (required) and a real vt generator; consider Cf ~197 fF to absorb the pseudo-R parasitic C. A4b: recovery with and without fast-settle.
- (A3, Decision 12) Stage-2 input capacitance must stay <= 5 pF for PM >= 60 deg (placeholder CL_NEXT = 2 pF); stage-1 wideband noise 10.8-14.9 uV (0.5 Hz-1 MHz) must be filtered by stage 2.
- (A3) The OTA is over-designed on gain (A0 118 dB vs 70 needed) and bandwidth (fu ~250 kHz): current/area could be traded for noise, but only the noise (pair/load area) is a binding target.

## Results log
One row per phase. The user fills in Cost from the OpenRouter Activity page.
| Date | Phase | Model / effort | Cost (USD) | Result (with path to log) |
|------|-------|----------------|------------|---------------------------|
| 2026-11-12 | A0 plan | Claude Opus 5.5 / — | | Plan only, no sim: AFE/amp/PLAN.md (layout, tb list, .meas per target, critique) |
| 2026-11-12 | A1 device char | Claude Sonnet 5.5 / default | | gm/Id, noise, ICMR typ/27C only; see "A1 findings"; AFE/amp/sim/a1_summary.txt, sim/char_*.log/csv |
| 2026-11-12 | A2 pseudo-R | Claude Sonnet 5.5 / default | | R0 4-6 TOhm on a model junction-leak floor; HPF 0.11-0.21 Hz with Cf=200f and vt=+0.2 V passes noise at all PVT; see "A2 findings"; AFE/amp/sim/a2_summary.txt, sim/char_pseudoR*.csv, sim/hpf_*.csv |
| 2026-11-12 | A3 stage-1 OTA | Claude Sonnet 5.5 / xhigh | | PMOS-input two-stage Miller OTA + closed loop; noise 1.52-1.84 uV (typ flicker, 9 PVT), fnoicor=1 4.2-5.2 uV, PM 70-76 deg, A0 118 dB, f_lo 0.11-0.2 Hz; R sweep and recovery; xschem == hand netlist; see "A3 findings"; AFE/amp/sim/a3_summary.txt, sim/a3_*.log |
