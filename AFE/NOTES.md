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

## Open questions
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

## Results log
One row per phase. The user fills in Cost from the OpenRouter Activity page.
| Date | Phase | Model / effort | Cost (USD) | Result (with path to log) |
|------|-------|----------------|------------|---------------------------|
| 2026-11-12 | A0 plan | Claude Opus 5.5 / — | | Plan only, no sim: AFE/amp/PLAN.md (layout, tb list, .meas per target, critique) |
| 2026-11-12 | A1 device char | Claude Sonnet 5.5 / default | | gm/Id, noise, ICMR typ/27C only; see "A1 findings"; AFE/amp/sim/a1_summary.txt, sim/char_*.log/csv |
