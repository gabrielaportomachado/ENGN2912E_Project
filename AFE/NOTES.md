# AFE handoff notes (read this first, every session)

Simulation-only course project (ENGN2912E). Not a medical device; never connect to a person.

This file is the shared context for every agent session working on the amplifier
(AFE/amp/) and the ADC (AFE/adc/). Keep it short. At the end of every phase, update
the "Results log" and "Open questions" sections below with verified numbers only.

## Environment (verified 2026-11-12)
- Run inside container `iic-osic-tools_chipathon_xvnc_uid_501`
  (image hpretl/iic-osic-tools:chipathon26). Repo at /foss/designs/ENGN2912E_Project.
- ngspice-46 and xschem are on PATH. LibreLane is at /usr/local/bin/librelane.
  ngspice ships the Icarus co-simulation bridge (ivlng.so / ivlng.vpi), but it does NOT work here (D4: no Cosim setup)
  and the XSPICE gate-level co-simulation gives wrong codes: for any ADC transient use the closed-loop PWL replay
  of AFE/adc/scripts/x2lib.py (X2; `X2_ADC_INC=<netlist>` swaps in an extracted ADC cell).
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
- ngspice (A3, corrected by the Decision 13 answer in A4a): the early `.tran` failure ("timestep too small" at ~1 us) was NOT caused by ad/as/pd/ps. It is nrd / nrs != 0
  (the xschem symbol default 0.18u/W) together with gmin = 1e-16: keep the real diffusion parameters (`.param DIFF=1`: ad = as = W*0.18u, pd = ps = 2*(W+0.18u)) and set nrd = nrs = 0.
  Vectors: `@m.xota.xm1.m0[vds]`, `v.xs1.vbrk#branch`; `.dc` sweeps need explicit `save` of device
  parameters; `meas` results and `.param` names are not visible after `setplot` / inside `.control` (carry them with `set v = $&x`); use `cph()`
  for unwrapped phase. NEVER pipe ngspice through `cut` or truncate its log (Decision 43a): the abort message is on the same carriage-return separated line as the
  progress values and gets lost (this is how the D5 "abort at 28.8 ms" artifact arose). Keep the whole log and read its "doAnalyses:" line.
- Simulation rules since X2 (Decision 43a; AFE/prompts/layout_run.md common rule 8): `.options abstol=1e-12` in every transient with switching (keep gmin 1e-16, reltol 1e-4, vntol 1e-7,
  chgtol 1e-17; abstol 1e-15 or smaller makes ngspice abort on the pA currents of gate-only sources); ONE ngspice thread per job through a job-local `.spiceinit` containing
  `set num_threads=1` (ngspice reads its working directory first; the system default in this container is 8 threads, 5-35x slower for these netlists. The A4b findings below say
  "ngspice ignores num_threads": that is true for `.options`, ~/.spiceinit and OMP_NUM_THREADS, which is what was tried then); every supply model with pad inductance gets ~1 pF per pad
  to the board ground; a driver script re-runs an aborted job once with a slightly different step cap. Runners that do all this: AFE/adc/scripts/x2lib.py, AFE/review/scripts/ngjob.py.
- Process option (Decision 44a, verified in the PDK decks): gf180mcuD = 5 metals, MIM option B. High-resistance poly is `ppolyf_u_1k` ONLY: `ppolyf_u_3k` has an ngspice model but is not
  a device of this variant (no LVS, netgen or Magic support): never use it. Layout / LVS MIM device is `cap_mim_2f0_m4m5_noshield`; the simulation netlists keep the m2m3 name (same model)
  and AFE/layout/scripts/mk_lvs_netlists.py writes the LVS references (AFE/layout/lvs/). Never edit a simulation netlist for LVS.

## PDK facts (verified)
- 3.3 V devices: nfet_03v3 / pfet_03v3 (default L=0.28u). Xschem symbols
  pfet_03v3.sym / nfet_03v3.sym; netlist format `X... d g s b pfet_03v3 L= W= nf= m=`.
- The existing TGATE uses 5 V devices (pfet_05v0/nfet_05v0). Do not copy them.
- MIM: cap_mim_2f0_m2m3_noshield (~2 fF/um^2; also 1f0, 1f5 variants), symbol
  cap_mim_2f0fF.sym (params W, L). The model includes r_leak = 1/(gleak*area), which
  matters next to TΩ pseudo-resistors and for the ADC hold node.
  Rules (Decision 39): minimum 25 um2 (5 x 5 um = 54.5 fF), maximum 10,000 um2 per plate. In the layout device (cap_mim_2f0_m4m5_noshield, Metal4 / Metal5)
  terminal 1 is the TOP plate and terminal 2 the bottom plate; LVS does not swap them (F1).
- Resistors: the only high-resistance poly of gf180mcuD is ppolyf_u_1k (1 kOhm/sq typ, 800 / 1200 at ff / ss, tc1 -9.4e-4 per K); MOS decap cap_nmos_03v3 is 3.98 fF/um2 at 3.3 V.
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
default 1.65 V = ADC mid-scale since VREF = VDD (Decision 17); ±500 uV x 1000 → 1.15–2.15 V).
ADC: 12-bit SAR PER CHANNEL (Decision 34), 3.3 V, serial output, 4 kS/s PER CHANNEL × N = 8 channels (Decision 29; 16 was the original architecture) (confirmed by the
user, Decision 16), VREF = VDD = 3.3 V (input range 0–3.3 V, 1 LSB ≈ 0.806 mV).
Stretch goal: 14–16 bit.
Unspecified (parameterize, never claim tolerance): electrode DC offset, input
common-mode range, stimulation artifact amplitude/duration, recovery time, power, area.

## ADS7953 (external benchmark only, not a GF180 macro)
The ADC is designed on chip in this project (Decision 15), so the ADS7953 is only a
comparison point (its SPI framing inspired Decision 18). Product page only: 16-ch
single-ended, 12-bit SAR, 1 MSPS, SPI. Its datasheet values are not needed.

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
10. Decision points: decide yourself, do not stop to ask. At every design choice, consider
   2–3 options and pick one using these priorities in order:
   (1) meets the targets and the recorded Decisions;
   (2) least area;
   (3) least power;
   (4) least additional hardware and complexity: fewest extra blocks, bias lines, clocks,
       control signals and pins; reuse what already exists.
   Base the pick on simulated numbers where you have them, otherwise labelled ESTIMATEs. In
   the phase summary, list each choice under "Choices I made": the options considered,
   their numbers, what you picked and why, so the user can overrule it at review. If no
   option meets a target, or the best option would change a recorded Decision, still pick
   the closest one and continue, but flag it at the top of the summary under "Needs your
   attention". Rule 9 still applies: stop at the end of each phase.

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
- (SUPERSEDED by Decision 17: VREF = VDD = 3.3 V, mid-scale 1.65 V, LSB ≈ 0.806 mV.)
  ADC: with VREF = 3.0 V and the 0–VREF range, mid-scale is 1.5 V. At 12 bits over 3 V,
  the LSB ≈ 0.73 mV.
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

ADC decisions, set by the user (2026-11-12), before D0.
15. The user designs the ADC in this project (the partner agreed): run the full D0–D6 in AFE/prompts/adc.md, files under AFE/adc/.
16. Sample rate: 4 kS/s PER CHANNEL, 16 channels (64 kS/s aggregate if one ADC is shared).
17. Reference: VREF = VDD = 3.3 V (no separate reference). Input range 0–3.3 V, 1 LSB ≈ 0.806 mV, mid-scale 1.65 V.
    Consequences: (a) the amplifier's VOUT_CM default becomes 1.65 V (output 1.15–2.15 V for ±500 uV), and A4a/A4b use it;
    (b) supply noise/ripple appears directly in every conversion, so D0 must budget VDD noise (in LSB) and the amplifier's
    PSRR, and D4 must simulate with a noisy/rippled VDD as well as a clean one.
18. Serial interface: SPI-style with an EXTERNAL master (an MCU drives CS and SCLK; the chip drives DOUT). Frame: 16 bits =
    4-bit channel ID + 12-bit code, MSB first. D0 specifies the SPI mode, max SCLK, whether a DIN pin selects channels, and
    whether SCLK also clocks the conversion (as the ADS7953 does) or a separate clock is needed.
19. ADC count: D0 compares one SAR behind a 16:1 analog mux versus 16 SARs (area incl. cap DACs, power, mux and
    buffer settling between channels, crosstalk) with numbers and CHOOSES one by rule 10; the user can overrule at D0 review.
    OUTCOME (D0, 2026-11-12, by rule 10): ONE 12-bit SAR behind a 16:1 analog mux. ESTIMATE: 0.017 mm2 vs ~0.27 mm2 for 16 SARs (15x), equal ADC power (~17 uW, < 1 % of the 3.9 mW of the amplifiers). See AFE/adc/PLAN.md.

Approved by the user after A4a (2026-11-12).
20. The transmission-gate fast-settle switch (NMOS+PMOS, fs/fsb, one inverter per channel) is accepted. A4b must measure its charge injection and the residual offset it leaves
    after release (output step and decay, versus switch pulse width).
21. A4b must also: (a) ramp VDD from 0 V and show the beta-multiplier bias (bias_gen) reaches its intended current (master ~0.85 uA typ, OTA1 IBIAS ~21 uA), adding the smallest start-up
    circuit if the existing diode-stack start-up is not enough (rule 10); (b) re-measure the stage-1 loop phase margin with the real stage-2 load (Cin2 = 3 pF through the real stage 2, not
    the A3 CL_NEXT placeholder); (c) find the path that makes the supply-to-output gain ~1.0 V/V at 50-60 Hz instead of the ideal-ratiometric 0.5 V/V (A4a PSRR table) and fix it if a small
    change does (then re-run the A4a PSRR/ac/noise at 9 PVT).
22. The f_hi spread (359-867 Hz over 9 PVT, only ~15 dB / ~8 dB of first-order attenuation at the 2 kHz Nyquist frequency) and its weak anti-aliasing are handed to the ADC: D0 must address
    them (oversampling + digital filtering, or a quantified aliasing budget). D0 runs BEFORE A4b so that A4b uses D0's ADC input model (R_ADC / C_ADC / acquisition window).
    OUTCOME (D0, by rule 10): convert at 4 kS/s per channel with NO oversampling and no on-chip filter. Noise aliasing is negligible (SIMULATED: <= 0.144 uV, 0.63 % of the in-band power, +0.3 % on the total at ff 85 C).
    Interferer aliasing is weak (1x: 13-20 dB at 3.7 kHz) and oversampling + sinc^3 only moves the worst alias band up 6 dB per octave (2x 19-27 dB, 4x 25-33 dB) because the analog roll-off is first order: the fix, if out-of-band
    interference matters, is an analog second pole in the amplifier (no spec exists; PLAN.md 5.2 proposes 100 uV pk -> <= 0.5 uV). Resolved by Decision 23.

Approved by the user after D0 (2026-11-12).
23. No out-of-band interference requirement exists. Keep the first-order amplifier roll-off; the interferer attenuation of the 4 kS/s conversion (13-20 dB at 3.7 kHz, SIMULATED, D0) is a DOCUMENTED RISK, not a target.
    No analog second pole is added for it. (Supersedes the D0 suggestion in PLAN.md 5.2, which stays as information.)
24. SCLK must be >= 3.5 MHz (MCU-side requirement, no extra hardware). With the 15.625 us frame period (64 kS/s aggregate) the 16-clock frame is <= 4.57 us, so the acquisition window is T_ACQ >= 11.05 us
    (arithmetic: 15.625 - 16/3.5 MHz). A4b verifies the follower settles to 1/2 LSB with the D0 ADC input model (C_s 17 pF, Ron 1 kOhm) at that T_ACQ (and may also report 12.4 us), for +-1 V steps
    (D0: worst 7.68 us at ss -40 C, so expected met). Full-rail (+-3.3 V) step settling (D0: 8.6-20 us) is REPORT-ONLY, no pass claim. Sizing the follower sink is allowed only if the +-1 V check fails (rule 10).
25. Before any DAC design, D2 must find the minimum MIM dimension (and spacing) in the GF180 PDK design rules. If 1.2 um units are illegal, redo the binary-vs-split DAC choice by rule 10 with legal units
    (D0 assumed 1.2 x 1.2 um = 4.0 fF; total C and matching change with the unit).
26. D2 builds its own per-unit MIM mismatch model (the PDK has none), labelled ASSUMPTION in the netlist and the log, and sweeps the matching constant A_C = 0.25-1 %*um (D0 assumed 0.5) to show the DNL/INL sensitivity.
27. The ADC's ~27 pC MSB-trial charge draw from VDD (VREF = VDD, D0) is a board-decoupling and bond-wire risk: recorded under Open questions; D2/D4 report the supply droop with an L-C supply model.

Approved by the user during A4b (2026-11-13).
28. ADC kick (A4b finding, see "A4b findings (partial)"): the 4 mW sink option (x16 channels) and an acquisition-time boost (new control signal) are REJECTED. The ADC resets its sampling capacitor to VOUT_CM = 1.65 V between
    conversions (one switch, existing node, existing SAR reset phase), so the step seen by the amplifier is the signal itself (+-0.5 V max), not +-1 V. A4b models this in spice/adc_load.spice and re-runs the settling check with
    +-0.5 V steps from 1.65 V, reporting the residual in LSB and as input-referred crosstalk in uV. If it still misses 0.5 LSB: report the smallest extra follower sink current that passes and the gain from a higher SCLK
    (T_ACQ = 15.625 us - 16/f_SCLK), without implementing either. The ff 85 C swing limit (1.20 V vs the 1.15 V target) is accepted as a documented miss. A4b scope: recovery steps of 1, 10 and 100 mV; recovery, TGATE and
    power-up at typical 27 C, ff 85 C and ss -40 C (all 9 corners only for a test that fails or is within 10 % of its limit at one of those three); fast-settle asserted 10 us before the TGATE closes and released after
    T_FS (sweep 0.1/1/10 ms). DBS stimulation artifacts of several volts are OUT OF SCOPE (open item).
    PROVISIONAL (Decision 34): Decisions 24 and 28 stay provisional until D0b re-derives the ADC interface for one ADC per channel (acquisition window ~245 us, reset optional); A4b adds a no-reset 245 us case (sim/a4b_adc245.log).

Approved by the user for the Chipathon tapeout (2026-11-12; full text, pin list and estimates in AFE/TAPEOUT.md; layout phases L0-L4 in AFE/prompts/layout.md).
29. N = 8 channels are taped out (all blocks parametric in N). Wherever this file says "16 channels" / "x16" / "16:1 mux" it is the original architecture: the TAPEOUT numbers are x8, an 8:1 mux, aggregate 32 kS/s,
    frame period 31.25 us, T_ACQ = 31.25 us - 16/f_SCLK (Decisions 16, 19, 24 read with N = 8). 16 channels does not fit a third of the pad budget (about 40 pads).
30. Single 3.3 V DVDD for the whole chip (amplifier, ADC, routing block, pads). No 5 V domain, no on-chip regulator. Still to verify (L0/L3): TGATE Ron and the dbs FSM / 7t5v0 std cells at 3.3 V; the 5 V -> 3.3 V level
    crossings (rstn, fast-settle control) are dropped. The IPG stimulation amplitude is set externally (analog pads are 5 V rated). Supersedes the 5 V/3.3 V split in "Planning-session hand estimates".
31. Planning frame: 2235 x 2235 um core (announcement; the padring fork says 2051, unresolved), one third of the pads (~29) per group; macro name, DEF and supply-pad count are with the organizer.
32. Serial configuration (reverses Decision 18's "no DIN"): new DIN pin; MODE + EN[7:0] loaded through a 9-bit shift register in a NEW wrapper under AFE/ (rtl/ untouched), CS-framed. 24 pads: E[7:0], IPG[7:0] (analog),
    CS, DIN, READY (input_cmos), SCLK, RSTN (input_schmitt), DOUT (bidirectional), VDD, VSS. No REC pads (amplifier inputs connect internally to the routing block).
33. ADC sessions (D1-D6) write to AFE/adc/NOTES.md and do not edit this file, so ADC and amplifier sessions may run side by side (one ADC session at a time). Hand-backs go in AFE/adc/NOTES.md "Hand-back" and are merged here by the user.
34. ONE 12-bit SAR ADC PER CHANNEL (N = 8), no analog mux, simultaneous sampling (group requirement, 2026-11-12); supersedes the Decision 19 outcome (one SAR + 16:1 mux). Decisions 24, 28 and the A4b ADC input model
    (C_s 17 pF, R_ADC 1 kOhm) still describe the ADC load, but the acquisition window is now far longer (frame period 250 us per channel) and the ADC may skip the 1.65 V reset; the follower-sink choice stays open at lower priority
    (A4b still showed 0.4-2 mV output displacement at 240 us at some corners). D0b (prompts/adc.md) re-plans the interface for 8 converters on one DOUT.
35. READY tied to VDD inside the macro (no pad). REC[7:0] (after the routing switch, before the amplifier) are analog pads, all 8 simultaneously. Final list: 31 pads (see AFE/TAPEOUT.md); Decision 32's list is amended accordingly.

36. Approved by the user after A4b (2026-11-13): fast-settle redesign = (A) gate-switched pseudo-resistor reset that keeps Cf in the loop (no unity-gain follower; the A4b Cf-shorting switch oscillates and rails stage 1) plus
    (B) a REC park switch tying the REC node to VCM_IN while the routing switch is open (no floating node). Executed as phase A4c (prompts/amp.md). Keep the follower sink at BM_KSF 6 (per-channel ADC with no reset, Decision 34, passes the ADC-kick check);
    the ff 85 C swing miss stays accepted (Decision 28). Fallback if A4c fails twice: ship the <= 300 ns short pulse and document the slow recovery.
37. Approved by the user after D0b (2026-11-13; detail in AFE/adc/PLAN.md section D0b and AFE/adc/NOTES.md): one ADC per channel with STAGGERED conversions (all 8 sample at CS falling; ADC i starts its bit trials i SCLK cycles later; 7-flop token chain);
    160-SCLK / 10-word frame: word 0 carries {MODE, EN[7:0]} on DIN (committed at SCLK 33, after all conversions), words 2-9 carry the 8 channels on DOUT as {ID, code}, channel 0 first, word 1 = config readback (user-approved); the 8 SAR result registers are chained
    and reused as the shift register; dbs/fsm clocked by SCLK (no CLK pad; L0/L3 must check nothing needs a free-running clock); each ADC reconnects to its amplifier right after its own last trial, NO 1.65 V reset (T_ACQ 220-246 us). Decision 24 relaxed to SCLK >= 0.64 MHz (1-5 MHz
    recommended); Decision 28 met by sim/a4b_adc245.log (<= 0.26 LSB), follower sink stays at BM_KSF 6; Decision 18 gains DIN; Decision 27 corrected: 13.6 pC per MSB trial, 36 pC per conversion, 8 ADCs = 108 pC simultaneous / 36 pC staggered per SCLK cycle.
    Supply droop remains OPEN and is a floorplan item: on-chip decap ~0.72 nF (~0.16 mm2 staggered, ESTIMATE, MOS-cap density 4.6 fF/um2 unchecked, 2 nH ASSUMED) must be budgeted in L0; CS must come from an MCU hardware timer (jitter <= 85 ns rms).
    ADC + interface power ~28 uW; 8 ADCs + shared digital 0.136 mm2. Open for D1/D2/D4: monotonic DAC switching, L-C-R supply model, shared vcm_out tap, MIM minimum size (25) and mismatch model (26).
38. After A4c (2026-11-13): user APPROVED the power-up fix (RST_AMP bit); the 100 mV-tail acceptance (output within 1 mV only after 7.3-9.0 s for a 100 mV electrode offset; 10 mV 3.4-4.7 s; 1 mV 0.13-0.27 s; the 100 ms target is NOT met, cause the MIM r_leak DC path) was APPROVED by the user on 2026-11-14. NOTE (2026-11-14): RST_AMP was not in the RTL when this was written; integration phase I0 (2026-11-14) added it (see "I0 findings"). A4c design accepted as built (replica-biased gate-switched pseudo-R reset 0.22u/0.5u, REC park on the routing C/CBAR nets, current-starved one-shot 1.9-6.9 ms, release step <= 0.14 mV).
    (a) POWER-UP LATCH (approved fix): 1-bit RST_AMP in the DIN config word, ORed into fs, held by the MCU >= 100 ms and issued >= 1 s after VDD (master bias up at ss -40 C); no analog change; D3/L3 implement it; pin list unchanged.
    (b) 100 mV electrode offset recovers in 7-9 s (1 mV 0.13-0.27 s, 10 mV 3.4-4.7 s) via the MIM r_leak DC path: documented, 100 ms target dropped (pending user confirmation). Open, re-check post-layout (L2): replica/mirror mismatch, park injection at ss -40, TGATE + real one-shot in one netlist, xschem update, 9-PVT reset tables.
39. L0 facts (2026-11-13, AFE/layout/PLAN.md; ANSWERS Decision 25): minimum legal MIM = 25 um2 (5x5 um, ~54.5 fF); the 1.2 um / 4 fF unit of D0/D0b is ILLEGAL (binary 12-bit with legal units ~223 pF, ~102,000 um2 per ADC, 0.82 mm2 for 8: rejected). Max single MIM 10,000 um2 -> each 20 pF Cin is built from >= 2 parallel pieces.
    Metal stack 5 metals, MIM between Metal4 and Metal5: LVS device cap_mim_2f0_m4m5_noshield (sims used m2m3, same C). Tools: KLayout Python generation + official KLayout DRC, Magic extraction/PEX, netgen LVS (always -batch with timeout; --version hangs), LibreLane digital; gdsfactory does not import here.
    ADC DAC style: APPROVED by the user 2026-11-13 (conditional on D2 MC DNL/INL proof; fallbacks 7+5 split or 8x8 um units): split 6+6, 5x5 um units, C_s ~7 pF (replaces 17 pF in D0/D0b numbers). Agent recommendation was split 6+6 with 5x5 um units, ~7 pF, ~3,300 um2/ADC; my caveat: the MSB-array error is ~8x larger in LSB than a full binary of the same units, DNL ~0.4 LSB 1-sigma at A_C 0.5 %*um: D2 MC must prove it, fallback 7+5 split or larger units). Power-pad count and L0's untested items (padring fork, example repos not read) remain open.
40. After D1/D2 (2026-11-14; approved by the user on the monitoring session's recommendation; detail in AFE/adc/NOTES.md "D1 findings", "D2 findings", "D2 decisions"). ANSWERS the Decision 39 condition and UPDATES Decisions 24, 26, 27:
    (a) DAC: split 6+6, 5x5 um units KEPT; planning A_C = 0.5 %*um (Decision 26 value; mimcap_statistical is a global skew only). Accepted cost: |DNL| > 1 LSB in ~4 % of chips (1.7 % with a missing code), INL < 1 LSB; harmless here because the amplifier noise at the ADC input is ~2.3 LSB rms. 7+5 split is the fallback only. Comparator plate = 3.49 pF (7 pF is the bottom-plate total). L1 PEX must check the bridge cap (64/63 unit, non-integer) and the bridge-node parasitic.
    (b) Comparator: cmp_p (PMOS double-tail, 80u/0.5u pair) as built in D1; NO D1b. Its fixed evaluate-phase shift (+12.7..+24.4 LSB) plus offset (sigma ~1.6 LSB) is a pure code shift (AC-coupled input). Latch noise unmeasured (open for D4); comparator noise is not binding at system level (1.855 uV vs 2 uV at ff 85).
    (c) SCLK: maximum 3 MHz, nominal 2 MHz (Decision 24 UPDATE; 5 MHz misses MSB settling by 0.6 LSB at Vin 2.15 V, ff 85). T_ACQ 240-244 us.
    (d) Sampling switch: ff 85 C nonlinearity 0.41 LSB (~-70 dB) ACCEPTED (far below the amplifier's 2.5 % THD at ff 85, Decision 28). Input range claimed: 1.15-2.15 V only.
    (e) SUPPLY (Decision 27 UPDATE): the dominant decision-instant error is the 8 comparators firing on one edge (~2.6 pC each), not the DAC. Plan: two straps from the one pad pair (DAC bottom-plate drivers via ~10 ohm with ~0.1-0.25 nF local decap; comparators + SAR logic on the main rail, >= ~0.125 nF) and comparator clocks STAGGERED per ADC (first ~30 ns after the DAC edge, then +i*Delta; Delta <= ~36 ns to fit 3 MHz). Total decap ~0.23 nF (~0.05 mm2, ESTIMATE; L 2 nH / R 0.25 ohm ASSUMED). Supersedes 0.72 nF (D0b) and 3.6 nF (D1). Superposition of per-ADC currents only: D4 or L3 must confirm with one full 8-ADC run. D3 generates the 8 clock phases (delay chain); L1/L3 route the two straps.
41. After I0 (2026-11-14; approved by the user; answers the "I0 findings" mismatches 1, 2, 5, 6, 9): (a) [mismatch 1] ONE shared REF analog pad is added (32 pads), wired to afe_chc.ref of all 8 channels; 32 exceeds the ~29 planning share and is subject to the organizer's allocation, fallback = ref tied to vcm (single-ended), documented in TAPEOUT.md.
    (b) [mismatch 2] the ADC's VDD/2 (dac_sw.vcm plate/M reset level and cmp_p.inp) comes from a dedicated per-ADC divider, cell `vhalf` (two equal poly resistors + local MIM decap, placed in afe_ch), not from vcm_out. Acceptance targets (set by the monitoring session's I1 prompt, not by the user): back within 0.1 LSB (80 uV) before the comparator decisions, comparator kickback <= 0.1 LSB, <= ~10 uA static per ADC (results: "I1 findings": NOT met).
    (c) [mismatch 5] word 1 on DOUT = the held config {6 x 0, RST_AMP, MODE, EN[7:0]} as committed at the previous SCLK 33 (readback). (d) [mismatch 6] dout_oe = ~cs_n is kept; pad-control names/values stay placeholders until L4 checks them against the organizer template.
    (e) [mismatch 9] RSTN pad pull-down enabled (RSTN_PD = 1); "hold RSTN low during the VDD ramp" is part of the README host power-up sequence (AFE/adc/README.md).
42. After I2 (2026-11-14; approved by the user on the monitoring session's recommendation; detail in "I2 findings"). ANSWERS Decision 41(b) (vhalf alone missed the target by 20-100x):
    (a) SAMPLED FLOATING REFERENCE adopted: cmp_p.inp sits on Cref = 7 pF (128 x 5x5 um MIM units, ~3,490 um2), connected to vhalf through a TGATE closed while tg_on = 1 (driven by tg_on and the local samb inverter); no RTL change (gating with rst as well made no difference, <= 0.01 LSB).
    (b) vhalf = 2 x 250 kOhm ppolyf_u_3k + 1 pF local decap (was 20 pF; 20 pF = 10,002 um2 also broke the 10,000 um2 single-MIM limit: I1 area figure corrected). Total ~4,200 um2 per ADC, ~6-7 uA static.
    (c) Result (true-SAR PWL replay, one ADC, 6 Vin per corner): worst threshold error beyond the fixed offset 0.25 / 0.23 / 0.47 LSB (typ / ss 125 / ff -40) vs the 0.5 LSB target; fixed offset -9.3 / -7.6 / -12.4 LSB (clock kick on the floating node; a pure code shift, accepted; partly cancels the +12.7..+24.4 LSB evaluate shift). Cref 10 pF not pursued (3.5 -> 7 pF only took ff from 0.65 to 0.47 LSB).
    (d) OPEN for L1/L3: ff -40 C margin (0.03 LSB) re-check after PEX; the 3072 transition and fs/sf corners not run; no Monte Carlo of the TGATE / Cref; staggered 8-ADC supply interaction not covered.
43. After X2 (2026-11-20; approved by the user on the monitoring session's recommendation; detail in AFE/adc/NOTES.md "X2 findings", commit b258669). CORRECTS Decisions 40b / 42c and ANSWERS 40e (8-ADC run) and README open items 4-6:
    (a) P1 APPROVED (testbench rules, no circuit change): every transient testbench with switching uses `.options abstol=1e-12` (keep gmin 1e-16, reltol 1e-4, vntol 1e-7, chgtol 1e-17); one ngspice thread per job (job-local .spiceinit `set num_threads=1`; `.options num_threads` is not an ngspice option); never pipe ngspice through `cut` (read the "doAnalyses:" line); every L-C-R supply model has ~1 pF per pad to board ground (or a loss R across the pad L); a driver script re-runs an aborted job once with a slightly different step cap (residual abort rate ~1 per 10^5 switching events).
    (b) P2 NOT TAKEN for this tapeout: DAC driver sizing is unchanged. The code-dependent comparator threshold (steps -1.1 / +1.3 LSB at codes 1536 / 2048 at typ, up to +1.55 LSB at ff 85, nominal devices) is static and deterministic, below the amplifier noise at the ADC input (~2.3 LSB rms), and leaves ENOB FS with noise unchanged (8.96 / 7.23 / 9.15 vs hybrid 9.0 / 6.85 / 9.15). A uniform widening moves the step to the MSB; a real cure needs per-bit driver sizing and an S4 re-run (no time before 2026-11-25). Documented as a known limitation; correctable by a per-chip lookup after measurement.
    (c) P3: top-of-range error ACCEPTED as in Decision 40c; INL claim stated as <= 1 LSB beyond a fixed offset for amplifier outputs 1.15-2.0 V (typ) / 1.15-1.9 V (ff 85); +2.1 / +4.4 LSB at 2.15 V (typ / ff 85) documented.
    (d) P4 APPROVED: the host discards the first frame after any pause in conversions (README).
    (e) FIXED CODE OFFSET is -30 / -40 / -22 LSB (typ / ff 85 / ss -40) = -24 / -33 / -18 uV at the electrode; the +11..+24 (40b) and -9 (42c) figures do not describe the closed-loop converter. Pure code shift, harmless (AC-coupled). README numbers to be corrected.
    (f) 8-ADC supply (40e): PASS at typ / ss 125 (<= 0.11 LSB); ff -40 C 3.6 V transition shift <= 0.25 LSB (half the 0.5 LSB margin) with 2 nH + 0.25 ohm on EACH of VDD and VSS (ASSUMED). OPTIONAL: two bond wires per supply pad (1 nH, 0.125 ohm) takes the plate error from 0.48 to 0.06 LSB: ask the organizer whether double bonding is possible. Crosstalk between channels PASS (0.022 LSB). Both to be confirmed after PEX in L3b.
44. After the pre-layout AUDIT (2026-11-20; approved by the user on the monitoring session's recommendation; detail in AFE/review/AUDIT.md, commit be40b54). Implemented by phase F1:
    (a) P-A1 (B1): high-resistance poly is ppolyf_u_1k ONLY in gf180mcuD (LVS variant D: poly_res = 1k; checked in the PDK). bias_genc ladders and vhalf use ppolyf_u_1k with 3x the squares (same resistance; every simulated number stays valid).
    (b) P-A2 (B2): top ports DOUT_OUT (was DOUT) and DOUT_IN (unused input), per the organizer bidirectional-pad template; the 8 pad-control pins kept.
    (c) P-A3 (M1): host power-up = RSTN low during the VDD ramp, release RSTN while CS is high, wait >= 5 s (8-channel bias start-up 3.6 s at ss -40 C), RST_AMP >= 100 ms, then every channel within 200 LSB of mid-scale, else repeat RST_AMP. Supersedes "wait >= 1 s" (Decision 38a / README).
    (d) P-A4 (M2): supply rail table of AUDIT 4.9.2 frozen: analog strap (bias, amplifiers, one-shots, vhalf, Cref switch, TGATE wells); ADC-main strap (cmp_p + digital macro, 0.125 nF decap ~3 ohm); ADC-DAC strap (bottom-plate drivers via ~10 ohm, 0.1 nF decap). New pins vdd_cmp and vdd_dac on the ADC cell and afe_ch; decap and strap resistor are devices in the LVS top netlist. Supersedes the "two straps" / "three straps" wording of Decision 40e and PLAN section 5.
    (e) P-A5 (M3): LVS reference netlists are generated by script from the simulation netlists with the rules of AUDIT 4.9.3 (m4m5 MIM; remove Rbrk / Rt / Rmm / Cpb* / Cpm; comparator Cxa = one 5x5 um MIM unit each; Cin as 2 pieces); simulation netlists are never edited for LVS.
    (f) P-A6 (M4): the mixed-corner MSB-trial error (slow 3.3 V devices with fast standard cells: 0.65 LSB) is ACCEPTED, same class as Decision 43b; no delay-chain retune.
    (g) P-A7 (M5) and m4: host protocol rules in the README: RSTN changes only while CS is high, frames are always 160 clocks, CS is never raised early.
    (h) P-A8 (M6): L1d fallback = no CTS + one hand-placed clock buffer if CTS cannot be fixed; KLayout DRC variant D on the macro; tap delays checked with AFE/review/scripts/sta_audit.py.
    (i) P-A10 (m7): Cref is ONE MIM plate (59.07 um side, as in vhalf.spice), not 128 units (corrects Decision 42a wording); Cin is built from 2 pieces.
    (j) Minor items m1-m8, i1-i4: documentation clean-up and the layout_run.md edits of AUDIT 4.9.4 are done in F1; m8 open items accepted as documented.
    (k) OPEN with the organizer (P-A9, user asks): macro name / DEF, slot size, 32-pad allocation, own VDD/VSS pair and double bonding, native-Vt nfet_06v0_nvt allowed (M7: if not, the follower needs a redesign), 1k poly only, bond-wire inductance.
45. Pad budget after the TA feedback (2026-11-20; decided by the user): KEEP N = 8 channels, at most 24 pads total. The 8 REC pads are DROPPED (REC stays an internal net: record TGATE OUT = afe_chc.rec; it was an observation point only, the ADC data shows the same signal, and removing the pad removes pad leakage / ESD current from the high-impedance amplifier input). Pads: E[7:0], IPG[7:0], REF (17 analog) + CS, SCLK, DIN, RSTN, DOUT_OUT/DOUT_IN (5 digital, Decision 44b) + VDD, VSS = 24. Supersedes the 32-pad count of Decision 41a. Block outline for the organizer's DEF template: 1000 x 1000 um PR boundary (gds/dbs_afe_top.gds, top cell dbs_afe_top, PR_bndry 0/0; AUDIT area 0.86-0.98 mm2). The TA asked for 6 analog pins and a smaller area (5 projects per frame): if the organizer refuses, the pre-studied fallback is N = 2 (E[1:0], IPG[1:0], REF; ~0.23-0.33 mm2, 700 x 600 um; unused ADCs tied off, same SPI frame).
46. After phase F1 (2026-11-20; approved by the user on the monitoring session's recommendation; "F1 findings", commit e3b04a2):
    (a) MIM plate order: the amplifier summing nodes are on the TOP plate of the input capacitors (stage 1 Cin1 -> vn, Cin2 -> vp; stage 2 Cin -> vn2), the driven side (rec, ref, v1) on the BOTTOM plate. Reason: the bottom plate carries the substrate / underlying-layer parasitic; on a low-impedance driven node it is harmless, on a summing node it adds noise gain and couples substrate or decap noise into the most sensitive node. AFE/layout/scripts/mk_lvs_netlists.py now defaults to --cin-top sum and AFE/layout/lvs/ was regenerated (check_lvs_netlists.py A / B / C PASS, only the 5 Cin lines changed). The simulation netlists keep their node order (no effect in simulation; PEX shows the real parasitic). L2a confirms on its first extracted MIM unit which Magic terminal is the top plate (F1: terminal 1 per the tech file) and regenerates with the other flag only if the tech file reading was wrong.
    (b) ppolyf_u_1k branch currents +1.6 / -8.5 / +11.2 % (typ / ff 85 / ss -40) ACCEPTED: device behaviour predicted by the audit; taps <= 0.49 mV, ADC codes identical, vhalf <= 8.4 uA (Decision 41b). Bias start-up with 8 channels and amplifier ac / noise at the 3 corners are re-run with the 1k poly as LP baselines.
    (c) Area 0.874 mm2 (0.997 mm2 pessimistic) ACCEPTED as an estimate; the floorplan must fit the 1000 x 1000 um outline with a stated margin. First lever: decap under the Cin plates (AUDIT 4.5), facing only the bottom (driven) plate (a); L2a keeps the area under the Cin pieces free of its own devices and Metal1-3 wiring so this stays possible; LP decides how (top-level overlap or cells inside amp_ch, which strap) and proves it extracts cleanly in Magic.
    (d) Comparator Cxa = one 5 x 5 um MIM unit (54.5 fF instead of 40 fF) ACCEPTED: code offset about +1.5 / +1.9 LSB (typ / ff 85), step at 2048 +1.30 -> +0.80 LSB typ. The offsets of Decision 43e are pre-layout; L1b restates them in AFE/adc/README.md.
    (e) F1 choices ACCEPTED: sampling-TG n-wells on vdd (analog strap); strap resistor rm3 2 x 222.2 um (LP confirms rm3 is an LVS device of variant D); MOS decap units 20 x 20 um; gdp on vdd_dac; cmp_p pin renamed vdd_cmp. CHANGED: the 15 pad-control ties are driven by tie-high / tie-low standard cells (gf180mcu_fd_sc_mcu7t5v0__tieh / __tiel) inside afe_dig as macro output pins, not 0-ohm resistors (a wire in the layout would not match a resistor in LVS); LP step 5 / L1d add them and update mk_lvs_netlists.py accordingly.
    (f) F1's extra edits ACCEPTED (no `cut` pipe in dgrun.sh / run_a4a.sh, X2_ADC_INC option in x2lib.py).
    (g) The approval of AFE/layout/ACCEPT.md (from LP) will be Decision 47.
47. Layout process after LP (2026-11-20; decided by the user; LP commit 5f5e1fa): NO approval gate. AFE/layout/ACCEPT.md is IN FORCE as LP wrote it (limits, decision ladder, organizer defaults, native-Vt fallback pre-approved only if the organizer refuses nfet_06v0_nvt) and is reviewed after the fact. Atharv runs every layout phase in the order of AFE/layout/RUNBOOK.md without waiting; each phase writes AFE/layout/reports/<phase>.md (10 fixed sections, checked by gate.py) + its findings and Results-log row in AFE/NOTES.md, and commits and pushes. Feedback goes only through AFE/layout/REVIEW.md (written by the user / monitoring session; every phase applies its open items first). Supersedes Decision 46g. OPEN for the user's review: the pseudo-resistor junction-area finding (ACCEPT.md section 2: with junction area the high-pass corner falls below 1 mHz and slow electrode offsets drift the output; handled for now by host reset rules, design-convention gates and a first-silicon test; a cure is a redesign). The user ACCEPTS this handling for the tapeout; a bounded pre-tapeout study of the pseudo-resistor n-well tie was considered and SKIPPED (fA-level model floors cannot prove a cure, and a bulk change would re-open LVS references and amplifier verification during L2a); kept: minimum identical junction area (SPEC.md 3.2), host reset rules, first-silicon f_lo / drift test.
48. 8-channel closure after L2a / L1a (2026-11-20; decided by the user on the monitoring session's analysis): KEEP N = 8 in the 1000 x 1000 um outline. As built, amp_ch 218.75 x 309.25 um and adc_ch 265.85 x 126.25 um do not fit the 235 x 375 um channel slot; a tightened floorplan (ring 26, bias corridor 12, strap corridor 25, afe_dig 820 x 80 um, channel slot 237 x 397 um) leaves amp_ch <= 222 x 285 and adc_ch <= 222 x 104 um. The amplifier's blocks alone fill 98.6 % of that, so the user approved a CIRCUIT CHANGE: stage-1 Cin 20 pF -> 15 pF with Cf1 200 fF -> 150 fF (CF1V, afe_params.spice; gain unchanged; ESTIMATED: noise up a few %, f_lo about 0.2 -> 0.27 Hz; to be verified by simulation before layout). Devices under the Cin plates were NOT chosen. Work items R1-R5 in AFE/layout/REVIEW.md (floorplan, afe_dig re-harden, Cin + amp rework, adc re-pack, then L2b / L1b / L3a on the new cells), with a checkpoint: a cell more than 3 % over budget or a failed Decision 1 target -> BLOCKED.md and the user decides (more rework or N = 4, ladder A-6). Supersedes the "no circuit resizing" rule for this one parameter only.
49. Deadline (2026-11-20; organizer, told to the user): the official submission deadline is 2026-11-30 (was assumed 11-25). New targets in AFE/prompts/layout_run.md: R2/R3 11-21, R4/R5 11-22, L2b 11-23, L1b 11-24, L3a 11-26, L3b 11-28, L4 11-29, one day of reserve. The REVIEW R1 checkpoint allows one more re-pack attempt per cell before BLOCKED.md. The late-cut order (L2b/L1b typ only, skip the deep n-well) is kept only as a reserve, not planned.
50. Cin after R4 (2026-11-20; decided by the user on the monitoring session's recommendation): Cin = 15 pF (CF1V 150 fF) is adopted. R4's schematic simulation (branch worktree-r4-amp-cin15, AFE/layout/baseline_cin15/) passes every Decision 1 target except the noise at ff 85 C: Decision-8 figure 1.89 / 2.14 / 1.73 uV (typ / ff 85 / ss -40; 20 pF: 1.67 / 1.85 / 1.54), with the real pseudo-R devices 1.50 / 1.73 / 1.39 uV; f_lo 0.25-0.29 Hz; gain, f_hi, PM, THD, power-up, reset, amp -> ADC unchanged or PASS. The ff 85 C noise limit becomes <= 2.2 uV (schematic and post-layout; typ and ss -40 stay <= 2.0 uV), same class as the accepted ff 85 THD miss (Decision 28). The Decision 48 estimate ("noise up a few %") was wrong: noise scales about as 1/sqrt(Cin) (+15.5 %); a Cin meeting 2.0 uV (~17.5 pF, amp ~300 um tall) does not fit the 8-channel floorplan because adc_ch (R5: 219.50 x 103.67 um) uses its whole 104 um. Implemented by REVIEW.md R6 (first written as R7; renumbered after the unused adc_ch-lever item R6 was withdrawn).

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

## A4a findings (stage 2 + follower buffer + real bias/vt/fast-settle + diffusion fix; op/ac/noise only; typical/ff/ss x -40/27/85 C; logs sim/a4a_*.log, tables sim/a4a_summary.txt + a4a_diff_summary.txt, plots figs/a4a_*.png, driver scripts/run_a4a.sh)
- Design (spice/: afe_params, bias_gen, ota2, stage1r, stage2, afe_ch; xschem/: ota1, ota2, bias_gen). VOUT_CM = 1.65 V (Decision 17), VCM_IN = 1.5 V. REAL, no IDEAL source left except the electrode source, VDD and the fast-settle control `fs`:
  * bias_gen: self-biased NMOS beta-multiplier (16u/4u, K=4, 60 kOhm poly, PMOS mirror, 3-diode start-up; master 0.85 uA typ) + two 2 uA ladders (3k/sq poly) giving vcm_in 1.5 V, vg1 = vcm_in+0.2 V
    (stage-1 pseudo-R gate), vcm_out 1.65 V, vg2 = vcm_out+0.2 V. All taps scale with VDD (ratiometric to the ADC mid-scale). OTA1 IBIAS = mirror leg 24x16u/4u (21 uA typ, 13-34 uA over 9 PVT).
  * Pseudo-R gate = fixed ladder tap (pseudo_r_fg), not the A2/A3 IDEAL tracking shifter. Fast-settle = transmission gate (NMOS+PMOS, fs/fsb, 0.5u|1u / 0.5u) across each of the 3 feedback elements + one inverter per channel.
  * Stage 2: Cin2 3 pF / Cf2 0.294 pF (gain 10), NMOS pair 2 x 1u/40u at ~5.5 nA/side (gm ~100 nS), tail 1u/20u (11 nA typ, 1/77 of the master), PMOS mirror load 1u/20u, Cc2 2.0 pF on the o2 node,
    NMOS follower 10u/2u + sink 6x unit (5.2 uA typ) INSIDE the stage-2 loop (Zout ~ 1/gm_f; its Vgs of ~1.25 V is absorbed by the loop, o2 sits at 2.90 V).
  * MIM area (drawn side^2, ESTIMATE): Cin2 1490, Cc2 990, Cf2 142 um2 (stage 1 unchanged: Cin 2 x 10,000); stage-2 transistor gate area ~545 um2 (+ 1,540 for the OTA1 bias sink).
- TARGETS over all 9 PVT (sim/a4a_summary.txt): gain @12.25 Hz 59.88-60.02 dB (stage 1 39.98-39.99, stage 2 19.89-20.04; target 60 +-1), f_lo 0.147-0.276 Hz (<= 0.5), f_hi 359-867 Hz (>= 300; slow corner
  ss -40 C 359 Hz, fast ff 85 C 867 Hz), channel is non-inverting (phase -0.7..+0.6 deg). Noise 0.5-300 Hz (typical flicker, IDEAL R = R0 in both stages): 1.535-1.803 uV (<= 2 OK, worst ff 85 C);
  stage 1 alone (measured at the stage-1 output) 1.552-1.805 uV: the channel total is within 0.02 uV of it and slightly BELOW it, because the stage-2 low-pass trims the band-edge noise by about as much as stage 2 adds; to 2 kHz 1.61-1.95 uV; to 1 MHz 1.62-1.99 uV (A3's 10.8-14.9 uV wideband is now filtered by stage 2).
  fnoicor=1: 4.18-5.20 uV (2.7-2.95x), NOT met = the Decision-10 risk, unchanged. Output DC error vs VOUT_CM 0.7-2.3 mV. Supply current 46.9-119 uA (typ 74.4 uA; 245 uW). Saturation margin of every analog
  transistor >= 0.19 V (criterion 0.05). OTA2 open loop: A0 51.1-57.6 dB, GBW 3.9-9.7 kHz, PM(beta=1) 87.4-88.7 deg (first-order loop; PM stays 87.7 deg with a 50 pF load). Supply sanity (typ 27 C, ladders fixed):
  VDD 3.0/3.6 V gives VOUT_CM 1.50/1.80 V (tracks VDD/2), gain 59.90/60.02 dB, f_lo 0.17/0.20, f_hi 554/572 Hz.
- Switch closed (acfs, AC only): gain at 12 Hz collapses to < -146 dB with no peaking (|H| max -4..-38 dB), i.e. the input is blanked; time-domain settling, charge injection, residual offset and loop stability with the
  switch closed are A4b.
- PSRR (Decision 17b, sim/a4a_psrr.log; |v(out)/v(vdd)|): DC 0.58-0.69, 50/60 Hz 1.00-1.03, 300 Hz 0.78-0.97, 1 kHz 0.35-0.68, 10 kHz 0.04-0.09 V/V; ideal ratiometric tracking of mid-scale (VREF = VDD) would be 0.5.
  So a 1 mV ripple on VDD at 50-60 Hz appears as ~1 mV at the output (1 uV input-referred) and, after the ADC's own VREF = VDD scaling, a net code error of about (1.02-0.5)*1 mV/0.806 mV = 0.65 LSB (ESTIMATE from the V/V figures).
- DECISION 13 ANSWER (diffusion / .tran failure; sim/a4a_diag_tran.log, sim/a4a_diff_summary.txt). It is NOT an NF clash and NOT ad/as/pd/ps: with the A3 options (gmin=1e-16 abstol=1e-20 chgtol=1e-19) the stage-1
  .tran runs with ad/as only, pd/ps only, or both, and FAILS (t = 0.24 ns, "timestep too small") as soon as nrd/nrs != 0 (the xschem symbol default 0.18u/W gives mOhm-level BSIM4 internal resistances, which with
  gmin=1e-16 break the solver); gmin=1e-14 does not help; default options (gmin=1e-12) run but give the wrong TOhm physics (dc_shift -35 mV vs -87.5 mV). FIX: .param DIFF in ota1/ota2/bias_gen (1 = ad=as=W*0.18u,
  pd=ps=2*(W+0.18u), nrd=nrs=0). Effect on the A3 op/ol/loop/cl/noise at 9 PVT (A3 environment otherwise unchanged): noise identical to 4 digits (typ 1.6752 uV fn0, 4.7535 fn1), A0 and gain identical, loop PM
  73.36 -> 72.73 deg (typ27; worst change 1.0 %), fu -0.4 %, GBW up to -3.4 %, f_hi +1.1 %, OTA output offset up to 16.5 uV (was <= 15.3). NOT yet exercised: a full-channel .tran with these options (A4b).
- Real vt (fixed gate), sim/a4a_prfg.csv: R0 at vt = +0.2 V over 9 PVT = 4.10 / 5.24 / 6.16 TOhm (typ -40/27/85), ff 4.10 / 5.23 / 5.45, ss 4.10 / 5.24 / 6.22: identical to A2's IDEAL tracking shifter (<= 0.1 %), also at a node
  DC of 1.65 V. vt = +0.1 V fails at ff 85 C (2.57 TOhm).
- FAST-SETTLE SWITCH: in this PDK model every reverse-biased junction leaks ~1e-14 A (the A2 "floor"), not W-dependent. An NMOS-only switch (bulk vss) leaks ~1e-14 A out of the summing node: that is more than the
  pseudo-R can supply (its current saturates near 1e-14 A), so stage 2's DC point railed (out 1.92 V, o2 3.23 V instead of 1.65 V) and stage 1 sat 41 mV off. A bulk-tied PMOS has no DC leak but a forward diode: R0 5.24 -> 1.70 TOhm.
  The NMOS+PMOS transmission gate cancels the leak (i(+-100 mV) = +9.59e-15 / -9.65e-15 A as with no switch; R0 5.230 vs 5.236 TOhm typ 27; ff 85 and ss -40 also unchanged). Residual summing-node DC shift with it: 11-16 mV (stage 1, 9 PVT).
  This ~1e-14 A leakage is a property of the PDK model (and is not W-dependent, A2); whether silicon behaves the same is UNVERIFIED (ESTIMATE: real junction leakage is smaller at 27 C but grows steeply with temperature, which this model does not show). The TG cancellation relies on matched NMOS/PMOS leaks, so treat it as a model-level result.
- xschem (sim/a4a_equiv_xschem.log): ota1/ota2/bias_gen netlisted in batch, structure identical to the hand netlists (9/8/14 devices, pin order identical); op, ac (typ 27 and ss -40), OTA2 open loop and noise with the xschem
  netlists swapped in agree to <= 0.05 % (device quantities; the only visible difference is a 0.12 mV shift of the stage-2 DC output at typ 27, a 0.9 % difference in the -0.1 deg mid-band phase). ota2/bias_gen .sch are written
  by scripts/gen_a4a_sch.py from tables typed separately from the hand netlists; the drawings were not viewed (no display).
- Not done in A4a (by Decision 14 or by choice): all transients (A4b); fs/sf corners; mismatch/offset/CMRR (no Monte Carlo); VOUT_CM = 1.5 V alternative (superseded by Decision 17); a startup transient of bias_gen (only the DC
  solution, found without nodesets); a trim for f_hi (spread 359-867 Hz = 2.4x); PSRR improvement; xschem drawings of stage1r/stage2/afe_ch (these stay hand netlists, as stage1 did in A3).

## D0 findings (ADC plan, no circuit files; AFE/adc/PLAN.md, hand estimates in AFE/adc/sim/d0_estimates.log, script AFE/adc/scripts/d0_estimates.py)
- Numbers marked SIMULATED come from the A4a amplifier logs; everything else is a labelled ESTIMATE. LSB = 0.806 mV. Amplifier output noise = 1.91-2.23 LSB rms (SIMULATED), channel SNR at full +-500 uV input 46 dB (7.3 bit):
  the amplifier limits the ENOB; 12 bits are headroom, the 14-16 bit stretch goal buys nothing. ADC budget <= 0.5 LSB rms (RSS allocation 0.43).
- Architecture: one SAR + 16:1 mux (Decision 19 outcome); binary 12-bit cap DAC, unit 1.2 x 1.2 um MIM = 4.0 fF, C_total 16.4 pF (C_s ~ 17 pF), transmission-gate sampling switch with bottom-plate sampling, dynamic-latch comparator.
- PDK limits found: no local MIM mismatch (mimcap_statistical is one global agauss(0,0.025,3) skew) and no active voltage-coefficient term in cap_mim_2f0 -> D2 must add its own per-unit mismatch model (ASSUMED A_C = 0.5 %*um); VCR-INL cannot be simulated.
- Interface (Decision 18): SPI mode 0, SCLK clocks the conversion (CS falling = sample, 12 bit trials, 16-bit frame {4-bit ID, 12-bit code} of the PREVIOUS conversion), SCLK 0.1-5 MHz, no DIN (channel auto-increments), new pins CS/SCLK/DOUT; existing `clk` unused;
  5 V -> 3.3 V crossings: rstn and the amplifier fast-settle control (down-shift with a 5 V-device inverter on VDD3); nothing from 3.3 V into the 5 V domain.
- A4b ADC INPUT MODEL (use this): C_ADC = C_s = 17 pF behind R_ADC = 1 kOhm (TG), connected for T_ACQ then disconnected, starting at the previous channel's voltage (step +-1 V and +-3.3 V); T_ACQ = 11.05 us (Decision 24: SCLK = 3.5 MHz, the slowest allowed; 12.4 us at 5 MHz also reported),
  7.8 / 4.6 / 3 us reported as stress; frame period 15.6 us; off-channel load 20 fF per amplifier output. SIMULATED A4a follower: sink 3.26-8.41 uA, 1/gm_f 11.6-17.5 kOhm -> a 1 V DOWNWARD step settles to 0.5 LSB in 3.7-7.7 us (3.3 V: 8.6-20 us):
  met at 12.4 us, 0.12 us margin at 7.8 us (ss -40 C), not met at 4.6/3 us. A4b measures it with the real stage 2 and sizes the follower sink if needed (rule 10).
- VDD noise (Decision 17b): code error = |A-0.5| x dVDD / 0.806 mV with A the A4a supply-to-output gain; in-band worst |A-0.5| = 0.53 -> 0.65 LSB per mV; allocation 0.2 LSB -> in-band VDD noise <= 0.31 mV rms (<= 1.6 mV if Decision 21(c) gets |A-0.5| <= 0.1).
  The ADC's own MSB trial draws 27 pC from VDD: board decoupling / bond-wire inductance is a risk for D2/D4.

## A4b findings, part 1 (sim/a4b_*.log, sim/a4b_summary.txt; scripts/run_a4b.sh, run_a4a.sh with TAG=a4b, run_a4b_*.sh, a4b_analyze.py; tb/tb_afe_1ch_tran.spice is the master transient testbench)
Only results from valid runs are listed (an early batch was discarded: stray 12.25 Hz 500 uV source left on, S-switch ADC model aborting).
- FIRST TRANSIENT FINDING: the A4a output could NOT reach the target swing. The A4a follower (3.3 V NMOS 10u/2u, Vgs ~1.25 V with its body effect at out = 1.65 V) clips the output at ~1.94 V: +-0.5 mV at 12.25 Hz gives 20 % THD
  and 57.7 dB at typical 27 C (sim/a4b_follower.log, variant a4a). FIX (rule 10, 1 device swap, same W/L, no area/power): follower = PDK native-Vt 6 V NMOS nfet_06v0_nvt 10u/2u (vth0 -0.04 typ / -0.22 ff / +0.14 ss; lmin 1.8u, wmin 0.8u met by L = 2u, W = 10u).
  Not done: W/L other than 10u/2u was only tried for THD (a smaller W/L removes the ff 85 C limit, below) and its ADC-kick cost was NOT measured with a valid ADC model.
- STAGE-2 PSEUDO-R RECTIFICATION (found as a slow DC drift of the output during a large sine): with the A4a gate offset VTT2 = 0.2 V the pseudo-R conducts on the positive output peaks, so the output mean drifts by -226..+83 mV (12.25 Hz, 0.5 mV, 8 s)
  and THD at full scale is up to 27.5 % (ff 85 C) (sim/a4b_thd_vtt0.2.log, run at VCM_IN 1.5); with an IDEAL resistor the drift is +3.5..+5.1 mV (sim/a4b_follower.log, nvtidealR). FIX: VTT2 = 0.9 V (same ladder, only the tap ratio: vg2 = 1.65 + 0.9 V);
  R0 stays on the model floor at all 9 PVT (4.10/5.24/6.22 TOhm typ -40/27/85; sim/a4b_prfg.csv, ff 85 C 6.22 instead of 5.45 TOhm), so f_lo and noise do not change. VTT2 = 0.6: THD <= 0.22 % except ff 85 C 3.7 % (sim/a4b_thd_vtt0.6.log). The remaining positive drift
  (+15..+37 mV at 12.25 Hz, +94..+105 mV at 300 Hz after 8 s of full-scale sine) is the model's ~10 fA junction floor (UNEXPLAINED origin, A2), not channel conduction.
- Baseline now (spice/afe_params.spice): VCM_IN = 1.65 V (was 1.5), VTT2 = 0.9 V (was 0.2), native-Vt follower. Re-run tables (9 PVT, sim/a4b_summary.txt): gain 60.035-60.053 dB, f_lo 0.154-0.290 Hz, f_hi 421-996 Hz (A4a 359-867), phase -0.4..+0.85 deg,
  noise 1.540-1.803 uV (typical flicker, <= 2 OK), fnoicor=1 4.18-5.20 uV (unchanged risk), supply 46.8-119 uA (typ 74.4), output DC error 0.4-1.1 mV, worst saturation margin 0.359 V (ss -40 C, xs1.xota.xmt; criterion 0.05),
  OTA2 open loop A0 58.5-60.3 dB, PM(beta=1) 87.1-88.3 deg, fast-settle closed: gain < -141 dB.
- SWING / THD (sim/a4b_thd.log, sim/a4b_thd_1pct.log; 9 PVT, 12.25 Hz and 300 Hz, 0.25-1.0 mV pk, 8 s): at +-0.5 mV THD is 0.030-0.247 % at 8 of 9 corners and 0.025-0.165 % at 300 Hz; the exception is ff 85 C at 12.25 Hz: 2.43 %
  (output bottom limit 1.20 V = o2 minimum 0.95 V + the follower's negative Vgs -0.27 V at ff; the target bottom is 1.15 V). Accepted as a documented miss (Decision 28). Output extremes at 0.5 mV: ymax 2.157-2.228 V, ymin 1.163-1.272 V (ff 85 C 1.220 V at 12.25 Hz).
  First amplitude with THD > 1 %: ss and typical -40: > 1.0 mV; typical 27: 1.0 mV (12.25 Hz); ff 27: 0.6 mV; ff 85: 0.5 mV. Gain at 300 Hz 58.19-59.64 dB (the LPF edge). DC drift: see above.
- DECISION 21(b), stage-1 loop with the REAL stage 2 (Cin2 3 pF through ota2 + follower), Tian two-injection, 9 PVT (sim/a4b_loop.log): T(100 Hz) 60.05-61.50 dB, fu 199-386 kHz, PM 76.3-81.0 deg (A3 with the 2 pF placeholder: 70.4-75.7 deg). The two injection copies
  needed their own zero-impedance copies of the bias references: through the shared ladder taps (~0.75 MOhm nodes) they talk to each other. Side observation (not studied): the shared vcm_in / vcm_out taps are a channel-to-channel coupling path (Cf2 = 200 fF per channel into the tap).
- DECISION 21(c), supply-to-output path (sim/a4b_psrrpath.log, typical 27 C, 50 Hz): the 1.02 V/V is the DIFFERENCE of two large terms: stage-2 reference vcm_out (T = 11.18 V/V x ripple 0.4998 = 5.587) minus the stage-1 reference vcm_in
  (T = 10.04 V/V x ripple 0.4544 = 4.561, because VCM_IN = 1.5 V is 0.4545 VDD, not 0.5 VDD); vbn, vg1, vg2 and the direct supply path contribute < 0.02. FIX: VCM_IN = 1.65 V = VOUT_CM (one tap voltage, zero hardware). Result at 9 PVT (sim/a4b_summary.txt section 5):
  |out/vdd| DC 0.507-0.516, 50/60 Hz 0.557-0.570, 300 Hz 0.459-0.547, 1 kHz 0.22-0.40, 10 kHz 0.035-0.063 V/V (ratiometric ideal 0.5). |A-0.5| in band: <= 0.07 (was 0.51-0.53). VCM_IN = 1.67 V would give 0.508 at typical 27 only (not tuned: PVT spread).
  Re-run at the new baseline: ac, op (all margins >= 0.359 V), noise, psrr, ol2, acfs at 9 PVT: tabulated above.
- Threads: ngspice -b ignores num_threads=1 (.spiceinit, .options, OMP_NUM_THREADS all checked: 8 threads either way); pinning each job to one core with taskset and running nproc-1 jobs in parallel is what works (scripts/run_a4b.sh). tb/.spiceinit holds num_threads=1 anyway.
- Files: spice/adc_load.spice (ADC input model: IDEAL behavioural switches, C_s 17 pF, R_ADC 1 kOhm, C_OFF 20 fF), tb/tb_afe_1ch_tran.spice, tb_afe_1ch_loop.spice, tb_afe_1ch_psrrpath.spice; spice/afe_ch.spice passes BRKV/BRKI to stage 1;
  xschem/ota2.sch regenerated with the native-Vt follower (scripts/gen_a4a_sch.py; equivalence re-run still to do).

## A4b findings, part 2 (checkpoint 2026-11-13; same logs/scripts; Decisions 34-35 apply: N = 8, one ADC per channel, READY tied high, REC pads)
- FAST-SETTLE RELEASE (sim/a4b_fscharge.log, sim/a4b_fsfix.log, figs/a4b_fs_release.png; sine and signals OFF): NOT charge injection. With the switch closed OTA1 is a unity-gain follower (A3: PM -45 deg at beta = 1) and OSCILLATES: starts ~1.5 us after
  the edge, grows to +-0.5 V on v1 / vn1 within ~5 us, period 1.8 us (557 kHz) (typical 27 C, 100 us pulse). At the release the summing node is wherever the oscillation left it (0.6 V from vp), the capacitive loop (beta 0.01) cannot pull it back and
  v1 goes to 0.006 V (typical, ss -40) or 0.84 V rising ~0.05 V/s (ff 85 C): 'stuck', recovering only through the ~10 fA saturating pseudo-R (tens of s to minutes). The 300 fC 'injected charge' of the first table was this swing x Cf1.
  Tried (typical 27, 12 s window): softer edges 0.1 / 3 us (stuck), 4x wider transmission gate (still oscillates, pk-pk 0.95 V), extra switched Miller capacitor 2 / 9 pF across OTA1 (stuck), series resistor in the reset path (runs abort at start-up, inconclusive;
  theory: stable only for R >~ 20 MOhm). WHAT WORKS: a fast-settle pulse SHORTER than the oscillation growth time. IDEAL 100 ns / 300 ns pulses, 3 corners: release step dout@10us <= 0.4 mV, dv1@10us <= 0.94 mV (injected charge Cf1 x dv1 <= 0.19 fC),
  output within 1 mV of the final value after 0 .. 4.2 s (typ 27: 4.2 / 1.4 s for 100 / 300 ns, ff 85: 3.3 / 1.3 s, ss -40: 0 / 0.65 s); a 1 us pulse already leaves 56 mV at 1 ms (t < 1 mV: 6.7 s), 3 us leaves a rail-to-rail error. The user's sequence 'assert 10 us before the TGATE closes, release 0.1-10 ms later'
  therefore cannot work with this OTA (see tg runs).
- REAL fast-settle source (item 3; spice/fs_oneshot.spice, tb/tb_fsos_gate.spice, scripts/fs_pwl.py; sim/a4b_fsos.log): one-shot = poly RC delay (145 kOhm, ppolyf_u_1k) + NAND2 + inverter, 3.3 V gates, programmable width by one NMOS-switched MIM (sel): fs pulse width 82 / 252 ns (typ 27),
  57 / 173 ns (ff 85), 117 / 359 ns (ss -40) for sel = 0 / 1 (all inside the stable window). Trigger = the edge that closes the record-path TGATE (FSM entering record mode), load ~10 fF (3 TGs + inverter, ESTIMATE). Release with the played-back real waveform (edges ~30 ps): dout@10us <= 0.1 mV,
  dv1 <= 0.4 mV, out - pre at 1 s: -0.4 .. -1.1 mV, at the end <= 0.15 mV; settles within 1 mV in 0 .. 2.5 s. Co-simulation by PWL playback (the one-shot inside the channel netlist aborted .tran: cause below).
- TGATE AT 3.3 V (item 1; sim/a4b_tg33_ron.log): Ron (10 mV across, gate drive C = VDD, CBAR = 0) at 1.15 / 1.65 / 2.15 V: typical 27 C 8.3 / 12.7 / 21.0 kOhm, ff 85 C 7.2 / 9.3 / 13.9, ss -40 C 9.6 / 20.7 / 25.3 kOhm; maximum over 1.15-2.15 V 20.8 / 13.1 / 34.2 kOhm (5 V: 4.1-6.1 kOhm).
  Noise (sim/a4b_tg33_noise_summary.log, IDEAL series resistor in place of the switch, Randles source, typical flicker): base 1.668 / 1.803 / 1.540 uV (typ / ff 85 / ss -40); +30 kOhm -> 1.708 / 1.849 / 1.572; +100 kOhm -> 1.800 / 1.953 / 1.644.
  The resistor's own thermal noise (0.39 uV at 30 kOhm in 0.5-300 Hz, matches the hand estimate 0.5-0.7 uV for a few tens of kOhm) adds in quadrature: +0.04 uV at 30 kOhm. MAX Ron for total <= 2 uV: 133 kOhm (ff 85 C, the worst), 266 kOhm typ, 493 kOhm ss -40.
  The real TGATE at 3.3 V (max 34 kOhm) therefore costs <= 0.05 uV. The TGATE devices themselves could not be put into the noise netlist: with them attached the DC operating point of stage 1 lands in a BISTABLE railed state (v1 0.3 V, vn1 1.79 V; ff 85 C also in the transient): the
  summing node is held by fA leakage, so any DC disturbance can latch stage 1 for tens of seconds (noise 9-170 uV in those runs: discarded). A start-up aid (IDEAL 100 MOhm tie of vn1/vp1/vn2 to the references for t < 50 ms, INIT_G) did not help (it pushed typical 27 C into the railed state too): see part 3.
- PAD LOADING (item 2): C_PAD on the REC node: noise unchanged (1.668 / 1.803 / 1.540 uV at 0, 2, 10 pF: the node is driven by a 1 kOhm source or the switch). Floating-node results (switch open, I_LEAK): NOT simulated reliably, see part 3 (hand ESTIMATE only).
- ADC LOAD (sim/a4b_adc.log, a4b_adc2.log, a4b_adcks.log; spice/adc_load.spice is unchanged; Decisions 24 and 28 are PROVISIONAL until D0b, Decision 34): with the 1.65 V reset the +0.5 V step (amplifier above 1.65 V, easy direction) passes (|err| <= 0.26 LSB, input-referred 0.21 uV);
  the -0.5 V step (amplifier output below 1.65 V: the follower must SINK C_s's charge) leaves -0.74 .. -2.25 LSB at 11.05 us (1.8 uV input-referred at the worst corner, ff -40 C), 2.2 LSB at 14.6 us (a higher SCLK gains nothing: the error is the stage-2 loop integrating the kick, error ~ omega_H x (kick area ~ C Vstep^2 / 2 I_sink),
  decays with the 0.3-0.5 ms loop time constant; residual at the next frame 240 us later: 0.4-2 mV). Without reset the +-1 V reference: +7.1 LSB (sink limited direction), -0.29 LSB. Follower sink sweep (hard step -0.5 V, 11.05 us): error ~ 1/BM_KSF: 6: 2.254 LSB worst, 9: 1.467, 12: 1.076, 18: 0.689, 24: 0.499 (passes by 1 milli-LSB), 36: 0.317;
  extra sink per channel (KSF - 6) x 0.87 uA typ: KSF 24 +15.7 uA = 0.41 mW for N = 8 (typ), KSF 36 +26 uA = 0.69 mW. NAN CORNERS explained: the missing entries are .tran runs that aborted with 'timestep too small' in the quiet pre-roll (random; see the cause below) or were killed when I stopped jobs;
  all but typical 85 C ksf 12/18 and ff 85 C ksf 18 were re-run (retry with TMAXS x 0.9 / TSTEP x 3) and fit the same 1/KSF law.
- CAUSE OF THE RANDOM .tran ABORTS ('timestep too small ... trouble with node v.xch.xs2.vbrk#branch', also A3's UNEXPLAINED failure class): the 0 V loop-break sources Vbrk in stage1r/stage2 carry ~1e-20 A branch currents that cannot meet abstol = 1e-20. FIX (A4b): the break is a 100 Ohm noiseless resistor (1 mOhm made .tran ~100x slower) unless
  .param LOOPTEST=1 (tb_afe_1ch_loop.spice); the Tian result is identical (typical 27: 60.8063 dB, 268588 Hz, 79.1197 deg). ngspice -b ignores num_threads / OMP_NUM_THREADS (8 threads regardless; nproc honours OMP_NUM_THREADS, so use `nproc --all`).
- Reported items: (a) the VTT2 = 0.9 V shift is REAL hardware, no IDEAL source: ladder B of bias_gen (poly 3k/sq, 2 uA): RB1 = 375 kOhm, RB2 = 450 kOhm, RB3 = 825 kOhm, tap vg2 = 2.55 V = 0.77 VDD (ratiometric); (b) the native NMOS nfet_06v0_nvt has typical/ff/ss parameter sets (vth0 -0.039 / -0.216 / +0.142 V) but NO mismatch/statistical
  terms (its _stat section has no mc_/agauss entries), model limits lmin 1.8 um, wmin 0.8 um (met: 10u/2u); (c) ADC VDD-noise budget at the measured supply gain (sim/a4b_vddbudget.log, 0.2 LSB allocation): in band worst |A-0.5| = 0.070 -> dVDD <= 2.3 mV rms at 50-60 Hz (3.5 mV at 300 Hz, 10 mV at DC); out of band (aliased, no anti-alias filter): 0.58 mV rms at 1 kHz, 0.35 mV at 10 kHz;
  (d) stage-1 margins at VCM_IN = 1.65 V (sim/a4b_stage1_margin.log): minimum 0.359 V (tail, ss -40 C), pair 1.76 V, load 0.50 V, 2nd stage 1.40 V, bias 0.65 V; criterion 0.05 V.
- Checks done: xschem == hand netlists for ota1 / ota2 (native-Vt follower) / bias_gen at the new baseline: structure PASS, op/ac/ol2/noise values identical (sim/a4b_equiv_xschem.log).

## A4b findings, part 3 (end of A4b; stopped for review)
- SLEW (sim/a4b_slew.log; typical 27 / ff 85 / ss -40, +-0.25 and +-0.5 mV steps): max |dv/dt| for the +-0.5 V output step 1227 / 1219 V/s up/down at ss -40 (worst), 1937 / 1930 typical, 2985 / 2972 ff 85, all >= 942 V/s (ESTIMATE 2 pi 300 x 0.5);
  max-slope / step ratio changes by only 0.94-0.98 between 0.25 and 0.5 mV: no slewing; 10-90 % rise 0.49 ms typ, 0.76 ms ss -40, 0.31 ms ff 85. (ff 85 C, -0.5 mV: the step reaches only -0.434 V: the 1.20 V bottom limit.)
- RECOVERY after an electrode offset step, no TGATE, no fast-settle (sim/a4b_recov.log, 80 s / 1500 s windows): 1 mV (output +-1.0 V, no clip): within 10 mV after 8.1 / 9.1 / 7.2 s (typ 27 / ff 85 / ss -40), within 1 mV after 11.8 / 12.9 / 10.4 s, 0.5 LSB after 13.2 / 14.4 / 11.7 s.
  10 mV: stage 1 LATCHES at a rail and stays there for the whole 80 s (output -871 mV, -507 mV, +1282 mV from rest at the end). 100 mV: back within 1 mV only after 500 / 265 / 489 s (8 min typical). This is the problem the fast-settle switch exists for.
- FAST-SETTLE IN THE TGATE SCENARIO: with the IDEAL pulse any width >= 10 us latches (above); the sequence 'assert fs 10 us before the TGATE closes, release 0.1-10 ms later' cannot work with this OTA. With the REAL one-shot at the typical corner (played back, triggered at the closing edge, 252 ns),
  a 1 / 10 / 100 mV electrode step is NOT reliably cleared: those runs are INVALID (see the next bullet). Pulse-alone behaviour (no offset) is valid and is in a4b_fscharge.log / a4b_fsos.log. What is still open: does a 100-300 ns pulse also charge Cin to a 10-100 mV offset fast enough?
  (Cin charges through Rs + TGATE Ron: tau ~ 1 kOhm + 12 kOhm times 20 pF ~ 0.26 us, so 300 ns is only ~1 tau: probably NOT, a fundamental conflict with the < 1 us stability window; a stable OTA1 at beta = 1 (more compensation switched in, or a gate-switched pseudo-R in the reset path) would remove it.)
- TGATE-ATTACHED TRANSIENTS (offset step while the switch is open, pad loading with the REC node floating, fast-settle from the one-shot): NOT RELIABLE, logs deleted. With the record-path TGATE in the netlist the DC operating point of stage 1 lands in the bistable railed state at ff 85 C and ss -40 C
  and, depending on netlist details (0 V vs 100 Ohm loop-break element, start-up aid, extra pad elements) also at typical 27 C; the aid I tried (tie to the reference) does not cure it. HAND ESTIMATE (not simulated) for the floating REC node: a leakage I on C_PAD + Cin||Cn = 11 pF + C_PAD moves REC at I / C = 0.9 V/s per 10 pA;
  the pseudo-resistors can only return ~10 fA (their current saturates), so any leakage above ~10 fA drives the output to a rail within the 0.3 s switch-open time and the recovery is then tens of seconds to minutes (as the 10 mV / 100 mV recovery above). C_PAD alone (no leakage): no effect on noise (a4b_tg33_noise_summary.log).
- POWER-UP (Decision 21a; sim/a4b_pwrup.log, a4b_pwrfs.log; VDD ramp from the all-zero state, no nodesets): the beta-multiplier reaches EXACTLY its DC operating point in all runs: master 0.847 uA typ / 1.370 ff 85 / 0.527 ss -40 and OTA1 IBIAS 21.19 / 34.12 / 13.27 uA, supply 74.5 / 119 / 46.9 uA.
  The existing 3-diode start-up is enough, no extra circuit added (rule 10); time for the master current to reach 90 %: 0.55 / 1.4 / 9.8 ms for ramps of 0.1 / 1 / 10 ms at typical 27 C, 0.75 ms at ff 85 C, but 611 ms at ss -40 C (the stack only kicks at leakage level when cold/slow: it starts, late).
  Output within 10 mV of 1.65 V after 17.3 / 9.5 / 15.9 s and within 1 mV after 20.8 / 17.5 / 18.6 s (typ / ff 85 / ss -40). A fast-settle pulse at power-up makes it WORSE: an ideal 1 ms pulse latches (+322 / -508 / +1282 mV at 40 s), a 300 ns pulse after the ramp too (-868 / -509 / +1282 mV): do not fire fs at power-up.
- ADC, ONE ADC PER CHANNEL (Decision 34; sim/a4b_adc245.log; PROVISIONAL): no reset, T_ACQ = 245 us, C_s starts +-0.24 V from the amplifier output (300 Hz full-scale sample-to-sample step): |err| at 245 us <= 0.26 LSB (0.21 uV input-referred) at all three corners (typ -0.178 / +0.045, ff 85 -0.102 / +0.028, ss -40 -0.260 / +0.055 LSB);
  even at 11 us the error is <= 0.48 LSB, so the follower sink does not have to change (with one ADC per channel the +-0.5 V reset case of a4b_adc.log and the sink sweep are not needed unless a 1.65 V reset is kept).
- CORNER TABLE (sim/a4b_corner_table.txt, from the saved logs, 9 PVT): gain 60.04-60.05 dB, f_lo 0.154-0.290 Hz, f_hi 421-996 Hz, noise 1.540-1.803 uV (fnoicor=1 4.18-5.20), supply 46.8-119 uA, PSRR(50 Hz) 0.559-0.570 V/V, stage-1 loop PM 76-81 deg, THD at +-0.5 mV 0.025-0.247 % (ff 85 C 12.25 Hz 2.43 %).
  Fast-settle columns exist at the three corners only (100 ns pulse: dout 0.25 / 0.20 / 0.01 mV, dv1 -0.94 / -0.62 / -0.15 mV).
- SCRIPTS: scripts/run_a4b.sh <case> (thd slew adc adc2 adcks adc245 fscharge fsshort fsos recov pwrup pwrfs; tg tgos padfloat exist but are not reliable), run_a4b_fsfix.sh, run_a4b_tgate.sh, run_a4b_tgnoise.sh, run_a4b_loop.sh, run_a4b_psrrpath.sh, run_a4b_follower.sh, run_a4b_prfg.sh,
  a4b_analyze.py, a4b_corner_table.py, a4b_report_misc.py, plots_a4b.py, fs_pwl.py; testbenches tb_afe_1ch_tran.spice (master), tb_afe_1ch_loop.spice, tb_afe_1ch_psrrpath.spice, tb_tgate_ron.spice, tb_fsos_gate.spice; figures figs/a4b_*.png.

## A4c findings (fast-settle redesign + REC park, Decision 36; typical 27 C / ff 85 C / ss -40 C; logs sim/a4c_*.log, plots figs/a4c_reset.png)
Files: spice/{a4c_params,bias_genc,stage1c,stage2c,afe_chc,fs_oneshot_c}.spice (A4b files untouched); tb/tb_a4c_{tran,loop,bias,ac,noise,op}.spice, tb_fsos_c.spice, char_prst.spice; scripts/run_a4c.sh, run_a4c_b.sh, run_a4c_loop.sh,
run_a4c_tbl.sh, run_a4c_prsize.sh, a4c_analyze.py, a4c_lib.py, a4c_ring.py, fs_pwl_c.py, plots_a4c.py. The HAND netlists are the source of truth: xschem bias_gen.sch / afe_ch were NOT updated (ota1/ota2 unchanged, A4b equivalence still holds).
- WHAT IS BUILT. (A) Per channel the gate of each stage's pseudo-resistor pair goes through a 2-device mux (PMOS gate fs = normal tap vg1/vg2, NMOS gate fs = reset level vrs): Cf stays in the loop, no unity-gain state, no inverter; the 3 fast-settle TGs and the fsb inverter are removed.
  vrs is generated ONCE per chip in bias_genc by a REPLICA: a diode-connected PMOS the same size as the pseudo-R, source on vcm_in, carrying I_REF from a narrow/long NMOS mirror leg of the master (0.28u/40u, same current density); vrs = vcm_in - Vsg(I_REF), C_VRS = 5 pF (~2,500 um2, ESTIMATE) holds it.
  (B) REC park: NMOS 1u/0.5u + PMOS 2u/0.5u transmission gate rec <-> vcm_in per channel, gates = the routing switch's CBAR and C nets (existing control nets, NO new control signal). Reset control: fs_oneshot_c (current-starved timer, trigger = the C net edge that closes the routing switch).
- WHY A REPLICA (the ladder tap of the prompt does not work). R_reset of the pseudo-R pair at one gate level spans 100x over the corners (sim/a4c_prst.log, 1u/2u, nodes at 1.65 V: gate 0.85 V gives 2.2 MOhm typ 27, 0.61 MOhm ff 85, 187 MOhm ss -40; 1.20 V gives 3.6 GOhm / 23 MOhm / 3.5 TOhm),
  while the stage-1 loop in the reset state needs R_reset >~ 20 MOhm for PM >= 60 deg (sim/a4c_loop_t1_ladder_tap_REJECTED.log: typ 27 R 26 MOhm PM 72.7 deg, R 1.3 MOhm PM 18.9 deg; ss -40 R 42 MOhm PM 76 deg; ff 85 R 1.6 MOhm PM 24 deg; strong inversion R ~0.2 MOhm: PM -4 .. -23 deg).
  With the replica R0_reset = 17.3-38.5 MOhm over all 9 PVT (I_REF 1.22-3.84 nA, vrs 0.81-1.22 V, sim/a4c_reset_replica.log): R ~ 2 Ut / I_REF tracks the master current.
- RESET-STATE STABILITY. AC loop (Tian, final sizes, sim/a4c_loop_final.log): PM 73.0 deg typ 27, 76.1 ss -40, 72.2 ff -40, 73.9 ss 85. The AC DC-solve of the reset state landed in a NON-PHYSICAL operating point at ff 85 (no unity-gain crossing) and typ 85 (PM -12.5 deg, vrs pulled to 0.8 V with ~45 nA unaccounted: a solver artifact,
  the same branch as in sim/a4c_loop_rsl_1u2u.log), so stability is checked in the TIME domain (sim/a4c_ring.log): reset held ON, 1 mV REC step -> v1 decays monotonically (one extremum, no ringing) at typ 27, typ 85, ff -40, ff 85, ss -40, ss 85. I_REF choice (1u/2u sweep, sim/a4c_loop_rsl_1u2u.log typ 27): RSL 10u PM 56.7 / 20u 65.6 / 40u 71.6 deg.
- PSEUDO-R SIZE 1u/2u -> 0.22u/0.5u (both stages, replica too). The release charge scales with W*L (sim/a4c_release_size_edge.log, typ 27, 100 mV step, 10 ms pulse; out - rest at +1 ms): 1u/2u -18.4 mV, 0.5u/1u -5.0, 0.22u/1u -2.1, 0.22u/0.5u -1.0, 0.22u/0.28u -0.6 mV.
  Slower release edges do NOT help (1u/2u: edge 100 ns / 10 us / 100 us: -18.4 / -22.8 / -23.1 mV at +1 ms). Normal-state R0 stays on the model floor (sim/a4c_prsize.csv, 9 PVT, VTT 0.2 and 0.9): 4.10-6.22 TOhm for every size down to 0.22u/0.5u (ff 85 stage 1: 4.68 TOhm vs 5.45 for 1u/2u, hence ff 85 f_lo 0.204 -> 0.225 Hz);
  0.22u/0.28u at VTT 0.2 drops to 1.72 TOhm (ff 85): rejected. Side effect: the full-scale 12.25 Hz output DC drift of A4b (+15..+37 mV after 8 s) is +0.8 mV typ 27 and +0.4 mV ss -40 (still +36 mV at ff 85).
- RESET PULSE WIDTH AND RECOVERY (sim/a4c_rec.log, ideal pulse from 10 us before the REC step, no TGATE; 1/10/100 mV x 1/3/10/30 ms x 3 corners). 3 ms and longer clear all steps at all 3 corners; 1 ms fails at typ 27 (100 mV: release step +81.6 mV, out +395 mV at +1 ms) and ss -40 (100 mV: stage 1 railed, out -1.24 V; 10 mV: +10 mV).
  With 3-10 ms: output error at the pulse end <= 0.05 mV (ss -40, 100 mV 3 ms: 0.55 mV), RELEASE STEP out -0.05 .. -0.14 mV, v1 -0.03 .. -0.07 mV at every corner (target <= 1 mV: met). A residual of -0.8 .. -1.4 mV (1.0-1.7 LSB) is present 1 ms after release for the 1 and 10 mV steps.
  Time from release until the output stays within 1 mV of its final value: 1 mV step 0.13-0.27 s, 10 mV step 3.4-4.7 s, 100 mV step 7.3-9.0 s (within 10 mV: 0 / 0 / 4.0-5.3 s). A4b without fast-settle: 1 mV 10-13 s, 10 mV latched, 100 mV 265-500 s.
  TARGET NOT MET: "within 1 mV after a 100 mV step in <= 100 ms". Cause (not the reset): the 100 mV DC level on REC leaks through the MIM r_leak of Cin into the summing node; v1 settles to a STATIC -9.9 mV (A2: ~10 % per V of offset) with the ~1.1 s stage-1 time constant, and stage 2 passes the slow change as a +36..47 mV output bump
  decaying with its 1.5 s HPF (v1 and out vs time: typ 27 100 mV 10 ms run, v1 -5.8 mV at 1 s, -8.3 at 2 s, -9.9 at 8 s; out +43 mV at 1 s, +2 mV at 8 s). Inferred from A2 and the static v1 value; an r_leak = 0 counterfactual could not be run (a `.param gleak` override from the testbench changed nothing; unlogged attempt).
- ONE-SHOT (spice/fs_oneshot_c.spice; sim/a4c_oneshot.log): PMOS holds timer node t at VDD, trigger turns it off and a mirror leg of the master (0.28u/40u) discharges C_T = 4 pF (MIM, ~1,970 um2 per channel, ESTIMATE); fs = trig AND t (NAND + inverter, 11 small devices). Pulse width 3.56 ms typ 27 / 1.90 ms ff 85 / 6.86 ms ss -40:
  >= the 3 ms that clears everything at typ and ss -40, and > the 1 ms that suffices at ff 85; it scales with 1/I like the time the reset needs. In the channel netlist with the real gate (no TGATE, typ 27, sim/a4c_oneshot_inchannel.log): 100 mV step -> out -0.014 mV at 3 ms, -1.1 mV 0.4 ms after the pulse end, within 1 mV later. With the TGATE attached
  the in-netlist one-shot aborts .tran, so the TGATE runs play back its waveform (fs_pwl_c.py: real plateau and falling edge, rising edge replaced by 100 ns because ns edges abort the run). The timer leg adds ~2 nA from VDD while the routing switch is open (7 nW/channel); supply current unchanged (below).
- (B) PARK + TGATE (3.3 V drive, sim/a4c_tg.log; routing switch OPEN + park ON from t = 0, electrode offset step at 0.3 s on the OPEN electrode, switch closes at 0.5 s and the real one-shot waveform resets). Open phase: v1 and the summing node do not move (|v1 - rest| <= 0.01 mV, |vn1 - rest| < 0.001 mV; output within 0.01 / 0.04 / 0.16 mV of rest at typ / ff 85 / ss -40, including a 100 mV electrode step).
  After the close, out - rest at +10 ms: -1.0 .. -1.8 mV for 0/1/10 mV steps (0 mV gives -1.5 mV only because the testbench tissue level 1.65 V differs from vcm_in 1.6484 V by 1.6 mV = the offset the amplifier sees at the unpark), 100 mV: -1.4 / +0.3 / -1.0 mV (typ / ff 85 / ss -40); time to within 1 mV of the final value:
  0 mV 0.77 / 0.70 / 0.08 s, 1 mV 0.31 / 0.25 / 0.01 s, 10 mV 4.6 / 4.5 / 3.5 s, 100 mV 8.9 / 8.9 / 7.3 s (typ / ff 85 / ss -40); the final value is within 0.16 mV of rest at typ and ff 85 and -0.66 .. -0.75 mV at ss -40.
  PURE charge injection of the park and the switch (tissue level set to vcm_in, no offset, no reset pulse, sim/a4c_inj.log): nothing visible at the park assert (<= 0.002 mV); at the close v1 steps +0.172 mV (typ) / -0.316 mV (ff 85) = 1.7 / 3.2 uV input-referred (out -1.7 / +3.2 mV, back within 0.4 mV by 3 s). ss -40: run stalled (not obtained).
  Pad assumptions (sim/a4c_leak.log, typ 27, 10 mV step while open): with park ON, I_LEAK 0 / 1 / 10 pA and C_PAD 0 / 10 pF leave the open phase and the recovery unchanged (5 of the 6 combinations completed; C_PAD 10 pF with no leak aborted at 0.504 s, numerical). With park OFF (the A4b condition) the floating REC rails stage 1 (v1 0.01 V with zero leak, 2.03 V with 1 pA) and the output does not return
  (-26 mV at 20 s with 0 leak, +5.7 mV with 1 pA); the 10 pA and 10 pF park-OFF cases do not even find a DC operating point. Noise with the park devices and gate muxes in the netlist (off): unchanged (below), i.e. +0.000 uV.
  BISTABLE RAILED STATE: with the TGATE closed at t = 0 and no initialisation, the DC solution is solver-path dependent: railed in A4b and in earlier (unlogged) A4c runs, normal in the final-netlist run of sim/a4c_rescue.log. In that run the park step at 0.2 s (1.6 mV level mismatch x1000) drives out to 0.80 V and v1 to 1.80 V, and the reset at 0.5 s restores out 1.6502 V within 5 ms.
  A uic start (no TGATE) also fell into the railed state (unlogged run): the state is a real attractor of the circuit, a reset pulse takes the channel out of it. The tests therefore start with the switch OPEN and the park ON (benign DC point), which is also the treat/power-up state of the system.
- POWER-UP (item 3; sim/a4c_pu.log, sim/a4c_pur.log): REGRESSION versus A4b. VDD ramp 1 ms, no reset: stage 1 latches at a rail at all three corners (v1 0.007 V) and the output is NOT within 10 mV of 1.65 V after 40 s (typ 1.929 V decaying, ff 85 1.143 V, ss -40 2.932 V); A4b self-recovered in 17.3 / 9.5 / 15.9 s.
  A reset derived from the VDD ramp (ideal, 10 ms) does not clear it (bias not up yet: master needs 0.55-1.4 ms typ/ff and ~0.6 s at ss -40, A4b). An ideal reset applied at 3 s (bias up at every corner): 4 ms (the one-shot's size) does NOT clear the latch (+26 / +31 / +20 mV at 40 s, typ / ff 85 / ss -40); 30 ms does (within 10 mV at once, within 1 mV after 2.6 / 0.66 / 3.3 s);
  100 and 300 ms: within 1 mV after 0.14 / 0 / 0.92 s (100 ms). The record-start one-shot at 0.5 s with the TGATE (sim/a4c_pu.log): ss -40 stays latched (the one-shot timer runs from the same slow master), typ and ff 85 runs aborted numerically (no result).
- TABLES (item 5; ac/noise/op/loop sim/a4c_ac.log, a4c_noise.log, a4c_op.log, a4c_loop.log, a4c_thd.log; A4b = sim/a4b_corner_table.txt; typ 27 / ff 85 / ss -40): gain 60.050/60.051/60.035 -> 60.056/60.061/60.041 dB; f_lo 0.203/0.204/0.237 -> 0.202/0.225/0.237 Hz; f_hi 652.1/995.6/421.2 -> 653.5/997.6/422.0 Hz;
  noise (typical flicker, IDEAL R = this netlist's R0) 1.668/1.803/1.540 -> 1.668/1.847/1.540 uV (<= 2 OK), fnoicor=1 4.720/4.922/4.393 -> 4.720/4.933/4.393 uV (the Decision-10 risk, unchanged); stage-1 loop PM (normal state) 79.1/76.3/81.0 -> 79.2/76.4/81.1 deg;
  THD at +-0.5 mV, 12.25 Hz 0.044/2.425/0.053 -> 0.040/2.527/0.051 % (ff 85 C keeps the accepted Decision-28 miss, bottom 1.220 V; output 1.148-2.154 V typ 27 and 1.148-2.153 V ss -40); supply 74.4/119.3/46.8 -> 74.4/119.3/46.8 uA; output DC error 0.4-1.1 -> 0.80/1.14/0.43 mV. Not re-run (not affected): PSRR, 9-PVT tables, slew, ADC load.
- NUMERICS: (1) ngspice's DC solve lands in non-physical states in the reset state (AC), with the TGATE closed at t = 0, and at the TGATE ss -40 start (cured by taking the park controls from the routing nets directly instead of B-sources, and by TSTEP = 1n); .tran aborts are random ("timestep too small"): scripts retry with TSTEP x3 / TMAXS x0.9;
  pulse edges below ~100 ns and 1 us electrode edges while the TGATE is open make the TGATE runs abort, so TG_TR = 100 ns, OS_TR = 100 us (offset edge, open switch), INIT edges 1 us. (2) scripts/run_a4c.sh must not be edited while it runs.

## I0 findings (integration phase, 2026-11-14; no layout, no analog simulation; Claude Sonnet 5.5; files AFE/top/{dbs_afe_top.v, stubs_analog.v, tb_top.v, run_top_sim.sh}, log AFE/top/sim/i0_top.log; edited: AFE/adc/rtl/adc8_top.v, AFE/adc/tb/tb_adc8.v, AFE/adc/README.md; rtl/dbs.v untouched)
- RST_AMP (Decision 38) is in the RTL. Config word 0 = {6 x 0, RST_AMP (bit 9), MODE (bit 8), EN[7:0]}: 10-bit shift register on SCLK 1-16, hold register at SCLK 33, new output `rst_amp_o` (adc8_top). It is a LEVEL in the hold register: SCLK stops while CS is high, so no clock exists to time it and there is NO on-chip timer;
  the host sets the bit (one config frame), waits >= 100 ms (>= 30 ms needed by A4c), clears it (another config frame). RSTN clears it; frames of < 33 clocks leave it unchanged; word-0 bits 15..10 are ignored. rst_amp_o is ORed with each channel's one-shot output (OR2 per channel) into afe_chc.fs. Not self-clearing: if the host forgets, all 8 amplifiers stay in reset.
  Host power-up sequence (from Decision 38a): RSTN low during VDD ramp, release, wait >= 1 s after VDD (ss -40 C bias), set RST_AMP, hold >= 100 ms, clear.
  Simulated (sim/i0_top.log, tb_top.v T2): bit set -> fs high on all 8 channels (+0.2 ns, OR2 delay is an ESTIMATE), still high after 30 ms and 105 ms with no clock; cleared by a frame; fs[0] high 105.500 ms. Runt frame (20 clocks) does not clear it; RSTN does (tb_adc8.v edge mode).
  D3 regression with the 10-bit config (sim/d3_exh_tt_2MHz.log: every code on every channel, 4096 frames PASS; sim/d3_edge.log: 4 SCLK rates PASS incl. the new RST_AMP cases; sim/d3_matrix.log: 19 PASS, 1 FAIL = ss 125 C at 4 MHz, the same FAIL as at HEAD, 4 MHz is above the 3 MHz maximum of Decision 40c).
  STALE (not re-run): the hardened D3 netlist / area / STA (AFE/adc/lg, sim/d3_signoff_summary.rpt, d3_yosys_stat.rpt) was built from the 9-bit RTL; +2 flops (cfg_sr, cfg_hold) and one output. Re-run bash AFE/adc/scripts/run_d3_synth.sh before sign-off.
- RESET TRIGGER AND PARK from the routing state (all from dbs_ctrl in rtl/dbs.v, no new logic): one-shot trig (fs_oneshot_c.trig) = sw_rec[i] (the C net of the record TGATE, = ready & rec_en & en_reg_2[i]); park pkc (afe_chc) = sw_rec_b[i] (the CBAR net, HIGH = routing switch open = park ON); pkcb = sw_rec[i].
  So the pulse starts when the record switch closes, in every channel that is enabled, and also for every enable of a channel while already in record mode; nothing starts in treat mode. Timing from the config frame (measured, 2 MHz): commit at SCLK 33, treat -> record: sw_ipg falls after SCLK 34, sw_rec rises after SCLK 35 (500 ns = one SCLK apart, break-before-make), fs rises 0.2 ns later.
  (Record -> treat: sw_rec falls after edge 34, sw_ipg rises after edge 35: from reading the FSM, not measured.) The ADC conversions end by SCLK 20, so the reset pulse (about SCLK 35) never overlaps a conversion; the amplifier output is invalid for the one-shot width (3.56 ms typ, 1.9-6.9 ms over corners = about 14 frames at 250 us) plus the electrode-offset recovery (A4c: 0.13-0.27 s to 1 mV for 1 mV, 7-9 s for 100 mV).
  With the stub amplifier (output code 0xAAA while fs = 1): 14 of 30 frames read 0xAAA in all 8 channels, all later frames read the input codes; every DOUT word = {0, ID, code}.
- TOP NETLIST AFE/top/dbs_afe_top.v: dbs_ctrl (N = 8, clk = SCLK, ready = 1) + adc8_top + bias_genc + 8 x afe_ch; 31 pads (24 analog E/IPG/REC, CS DIN SCLK RSTN, DOUT, VDD, VSS) plus pad-control outputs. dbs_ctrl + TGATE is used instead of module dbs because dbs does not export sw_rec / sw_rec_b (needed for the trigger and the park);
  the wiring is dbs.v's and tb_top.v compares REC / IPG with a real `dbs #(8)` instance: 0 differences. Stub modules afe_chc, fs_oneshot_c, bias_genc, dac_sw, cmp_p have exactly the SPICE pin names (sim-only ports sim_* behind `SIM_STUBS`). Channel cell pins and the crossing-net list: AFE/layout/PLAN.md section 9 (281 digital <-> analog nets).
  RESULT PASS, 0 errors: reset state (switches open, park ON), RST_AMP set/hold/clear, record start, 8 ADC words, treat mode (IPG closed, REC floating), record on channels 0-3 only (one-shot fires again on those only), RST_AMP during record, RSTN; DOUT_OE = ~CS, DOUT changes only on SCLK falling edges, no crowbar / contention / sam-samb error in the DAC stub.
- MISMATCHES between dbs.v, the amplifier netlist (afe_chc and bias_genc), the ADC netlist and adc8_top (needs your decision unless noted):
  1. afe_chc has a `ref` pin (second input, Cin2 on the REF side; A3/A4 used a Randles pair around a 1.65 V tissue node) but there is no REF pad (Decisions 32/35, 31 pads). The top ties ref to vcm (1.6484 V): single-ended recording, no reference-electrode common-mode rejection. REC-only gain is identical (A3). A REF pad costs +1 pad (32).
  2. The ADC needs a VDD/2 net (dac_sw.vcm = plate reset level, cmp_p.inp): every D1-D5 simulation used an IDEAL source `vcmd`; bias_genc has only vcm_out (1.65 V, the amplifier stage-2 reference). The top uses vcm_out as a PLACEHOLDER, which would put the 8 reset-switch kicks on the stage-2 references of all amplifiers (the A4b side observation: shared taps couple channels). Needs its own divider/buffer or a decision to share. Also the comparator threshold moves 0.19 LSB per 10 mV of VDD/2 (D1).
  3. dac_sw needs samb = ~sam; adc8_top has no such output (only dac_gdn = ~tg_on). The top adds a local inv_1 per channel (D4 modelled samb with a delayed ideal inverter). Choice, not a conflict.
  4. dac_sw has two reset gates rst (plate T) and rstm (mid node M): D2/D5 sequenced rstm 0.5-1 ns BEFORE rst; adc8_top has one rst_sw and D4 tied both together (the top does the same). The one-net case was not re-simulated at transistor level for D5 timing; a one-run replay (rstm = rst) is worth doing at L1/PEX.
  5. Decision 37 says word 1 = config readback (user-approved); the RTL, README and D3 testbench have word 1 = 0 and PLAN.md D0b says the echo was NOT chosen (rule 10, "your call"). With RST_AMP the readback would be the only way to see rst_amp / mode / en from the board. Cost ~20 gates, one more D3 case. Not implemented here.
  6. info.yaml draft comment (written before D0b) says DOUT_OE = 1; adc8_top gives dout_oe = ~cs_n (DOUT tri-state while CS is high, the MCU may share the MISO line). The top follows adc8_top. All pad-control names/values (DOUT_*, *_PU/PD) are PLACEHOLDERS: the organizer template was not re-read in this phase.
  7. The hardened `dbs` macro (config.json, DESIGN_NAME dbs, clock port `clk`) does not export sw_rec / sw_rec_b and contains the TGATE blackboxes. For the chip, harden dbs_ctrl (or a wrapper that exports sw_*, clocked by SCLK) and place the 16 TGATEs in the 8 afe_ch cells; rtl/dbs.v itself needs no change.
  8. sw_rec_b and sw_rec in dbs_ctrl come from two separate gates (sw_rec = ~sw_rec_b): they are complementary only up to one inverter delay. The record TGATE, the park TGATE and the one-shot trigger all see that skew (the park and the routing switch overlap for ~0.1-0.3 ns, E to vcm through the TGATE); A4c simulated ideal complementary edges. Check at L3 (gate-level sim / STA) and, if needed, buffer both nets from one driver.
  9. No power-on reset: all config and FSM flops reset only through RSTN. If RSTN is not held low while VDD ramps, the routing switches (and RST_AMP) can power up in a random state: README test plan must say "hold RSTN low during power-up".
  10. Name collision for L2: afe_chc.vcm (= bias_genc.vcm_in, 1.6484 V) and dac_sw.vcm (= VDD/2) are different nets; afe_ch calls them vcm and vcmd.
  11. FSM timing (dbs.v): clocked by SCLK only, so a routing change completes at SCLK 35 of a frame; a frame of 33-34 clocks commits the config but the routing (and the one-shot trigger) waits for the next frame's first edges. RST_AMP acts at SCLK 33. No change needed (the interface uses 160-clock frames).
  12. Simulation only: TGATE.v is a one-way `cmos` primitive (E -> REC, E -> IPG as in dbs.v); the real TGATE conducts both ways (IPG pad drives the electrode). Not an RTL mismatch.
- Choices I made (rule 10): (a) RST_AMP as a held level, no timer: an on-chip timer needs a free-running clock (none: dbs/adc are clocked by SCLK, Decision 37) or a ~100 ms RC (area, corner spread); the host already has to wait 1 s after VDD. (b) OR2 AFTER the one-shot, not into trig: ORing RST_AMP into the trigger would give only the 3.6 ms pulse (the timer discharges while trig stays high).
  (c) RST_AMP at word-0 bit 9 (next to MODE) rather than a separate frame. (d) TGATEs inside afe_ch, dbs_ctrl at the top (see 7). (e) samb by a local inverter (3), ref tied to vcm (1), vcmd = vcm_out placeholder (2), DOUT_OE = ~CS (6).
- Not done: no synthesis / STA / gate-level simulation of the top (only RTL with std-cell delay models); D3 hardened results stale (above); pad template not re-read; the stubs carry no analog behaviour (amplifier output code is a testbench value); xschem not touched; amplifier/ADC netlists unchanged.

## I1 findings (2026-11-14; Claude Sonnet 5.5; implements Decision 41; files: AFE/top/{dbs_afe_top.v, stubs_analog.v, tb_top.v}, AFE/adc/{rtl/adc8_top.v, tb/tb_adc8.v, spice/vhalf.spice, scripts/i1_vhalf.py, run_i1_vhalf.sh, README.md}, AFE/{TAPEOUT.md, layout/PLAN.md section 9}, info.yaml)
- DONE: (1) REF pad: dbs_afe_top has the port REF, wired to afe_ch.ref -> afe_chc.ref of all 8 channels (32 pads); info.yaml, TAPEOUT.md (32 > ~29 share, fallback), PLAN.md section 9 updated. (3) word-1 readback in adc8_top.v: DOUT word 1 (SCLK 17-32) = {6 x 0, RST_AMP, MODE, EN[7:0]} of the config held BEFORE this frame (0 after RSTN); tb_adc8.v checks every full frame against the config held at its start
  (exh 4096 frames, the edge cases incl. runt frames and RSTN mid-frame, the 4 b2b frames) and tb_top.v checks all 8 words per frame the same way; (5) RSTN_PD = 1 and the README host power-up sequence / test plan; (4) dout_oe unchanged. Regression: sim/d3_exh_tt_2MHz.log PASS (4096 frames), sim/d3_edge.log PASS (4 SCLK rates), sim/d3_matrix.log 19 PASS + the same 1 FAIL as before (ss 125 C at 4 MHz > the 3 MHz maximum); AFE/top/sim/i0_top.log (now the I1 run) PASS, 0 errors, REC/IPG == dbs.
- D3 SYNTHESIS RE-RUN (bash scripts/run_d3_synth.sh --skip OpenROAD.CTS --skip OpenROAD.ResizerTimingPostCTS; CTS DPL-0036 is the known L3 item, not touched), 10-bit config + word-1 mux, vs the old sim/d3_signoff_summary.rpt / d3_yosys_stat.rpt (git HEAD):
  Yosys cell area 28,272 -> 28,799 um2 (+527, +1.9 %), cells 998 -> 1008 (+10); placed std cells 31,279 -> 31,872 um2 (+593), die 93,933 um2 unchanged-class (bbox 300.3 x 318.2 um), utilization 38.8 %, 0 magic DRC, 0 antenna violations.
  STA (5 corners): setup and hold met everywhere, hold WS (ff_n40C) +0.2567 -> +0.2358 ns, setup WS (ss_125C) +96.77 -> +96.53 ns, tt hold +0.820 -> +0.787. Max-cap / max-slew violations (unbuffered SCLK net, no CTS): overall 3 / 31 -> 3 / 16 (counts differ per corner and per run; not analysed, an L3 item with the CTS problem).
- (2) VHALF, TRANSISTOR LEVEL (sim/i1_vhalf.log; scripts/i1_vhalf.py: dac_sw + cmp_p + vhalf, 3.3 V, D5 timing, frame 1 converts 1.15 V, frame 2 samples 2.15 V (1 V step), 12 comparator pulses from 130 ns after CS falling; R = 250 kOhm each (ppolyf_u_3k, 1 um x 83 um), C swept 10 / 20 / 40 pF; typ 27 C / ss 125 C / ff -40 C; run by PID, scratch sim/.ptmp):
  (c) STATIC CURRENT MET: 6.29 / 5.83 / 7.44 uA (typ / ss 125 / ff -40), independent of C. VDD/2 static = 1.65000 V (ideal resistor match; a real x % pair mismatch moves it by x/4 % of VDD = a code shift, not a sampling error since plate and comparator share the node).
  (a) AND (b) NOT MET at any size tried. Worst of the decisions in 12 trials, |v(vhalf) - v(just before the plate switch opens)|, in LSB (80 uV = 0.1 LSB), (a) = just before a decision / (b) = within 3 ns after a comparator rise:
    C = 10 pF: (a) 5.3 / 4.4 / 9.8, (b) 12.4 / 7.0 / 19.7   (typ / ss 125 / ff -40)
    C = 20 pF: (a) 2.75 / 2.26 / 5.16, (b) 6.17 / 3.29 / 9.71
    C = 40 pF: (a) 1.41 / 1.15 / 2.66, (b) 2.76 / 1.48 / 4.34
  The error scales as 1/C (ESTIMATE from the three points): 0.1 LSB would need about 0.5 nF (ss 125 C, (a)) to 1.7 nF (ff -40 C, (b)) per ADC = 0.25-0.85 mm2 of MIM per ADC: impossible. The resume kick itself (TG closing with the bottoms at the old code) is 377 / 245 / 143 mV peak at 10 / 20 / 40 pF (typ) but it decays with tau = R_out x C = 125 kOhm x C (1.25-5 us), far inside the 240 us acquisition window: not the problem.
  CAUSE (waveform of the 40 pF typ run, sim/.ptmp/i1_raw_C40_typical_27.csv): the comparator's input pair couples the PLATE swing onto the reference node (about 2.3 mV per V of plate displacement, i.e. ~90 fF of gate coupling through the common source), and the comparator clock edge kicks it by +2.9 mV (40 pF) at 8 ns. The part proportional to the instantaneous plate-to-vhalf voltage only scales the comparison and does not change its sign (harmless);
  the part that matters is the MEMORY: after the large early trials vhalf recovers with tau = R_out x C (5 us at 40 pF, 125 kOhm output) while the later trials (plate within +-1 LSB of balance) need 80 uV: residual -1.1 mV at 100 ns, -0.76 mV at 1.1 us, -0.25 mV at 8 us in that run. The hybrid frame (MSB trial, then the final-code pattern, 12 identical evaluations) is not the real SAR sequence: the real trial swings are binary-weighted and the
  residue is smaller in the late trials, so the table is an UPPER bound for (a); (b) is the comparator's own clock kick and does not depend on the sequence. A real-SAR transistor run (12 true trials, all 8 ADCs staggered) was NOT done.
  CHOICE (rule 10: no option meets the target, so the closest affordable): vhalf default C = 20 pF (a single MIM, 9,900 um2 drawn, < the 10,000 um2 MIMTM.8b limit; 40 pF = 19,900 um2 needs 2 pieces and 0.16 mm2 for 8 ADCs), poly pair about 170 um2 drawn (1 um x 83 um each, ~500 um2 with spacing/contacts, ESTIMATE). With it the vhalf error is a few LSB (2.3-5.2 LSB (a), 3.3-9.7 LSB (b)) = signal-/clock-dependent code error comparable to the amplifier noise (2.3 LSB rms at the ADC input),
  so it adds INL/noise, not a hard failure; but it violates the 0.1 LSB target by 20-100x.
  NEEDS YOUR ATTENTION. Options (none implemented): (i) lower the impedance at the decision instants: a unity-gain buffer or source follower for vhalf (cost: tens of uA per ADC, above the 10 uA budget; a follower's own kickback is lower by ~its gm/C) ; (ii) cut the coupling: smaller comparator input pair or a PMOS pair with its tail decoupled (D1 re-sizing: the pair is 80u/0.5u for noise, 0.15 LSB);
  (iii) only the comparator reference noisy, plate reset on its own quiet node: does not help (the kick on inp still adds to the comparison); (iv) accept as a code error and measure it with the full 12-trial real-SAR run (what I did not do). Time box: stopped here as instructed.
- afe_ch now contains vhalf (u_vh) and has no vcmd pin; bias_genc/vcm_out are no longer used by the ADC. The stub vhalf outputs a constant; the digital sim is unaffected.
- Not done: gate-level sim of the top; real-SAR vhalf run; pad template (L4); vhalf area from layout.

## I2 findings (2026-11-14; Claude Sonnet 5.5; follow-up to I1; files: AFE/adc/{spice/vhalf.spice (vrefs added), scripts/i2_replay.py, i2_analyze.py, i1_vhalf.py (VR option)}, AFE/top/{dbs_afe_top.v, stubs_analog.v}, AFE/layout/PLAN.md section 9; logs AFE/adc/sim/{i2_replay.log, i2_summary.txt, i2_twoframe.log}; no Decision written, as asked)
- WHAT WAS BUILT: sampled floating reference. `vrefs` (in vhalf.spice) = transmission gate (NMOS 1u/0.28u + PMOS 2u/0.28u, the DAC sampling-TG sizes) from vhalf to cmp_p.inp + Cref (MIM) on cmp_p.inp. Gates: c = tg_on, cb = samb (the afe_ch local inverter): NO new RTL output.
  dac_sw.vcm (plate / M reset level) stays on vhalf. Instance u_vr in afe_ch (dbs_afe_top.v), stub vrefs in stubs_analog.v; top sim PASS (0 errors). Timing: the TG opens with tg_on, 2 ns after the first DAC driver edge (the plate switch rst opens 1 ns before the drivers). Variant `crefr` = TG gated by rst (opens WITH the plate switch, before the drivers): results are identical
  to the tg_on version at every corner (within 0.01 LSB), so the ref switch does NOT have to open earlier than the sampling TG and the RTL is unchanged. (crefr needs a complement of rst, i.e. an extra inverter: not proposed.)
- METHOD (D4b replay, true binary SAR): scripts/i2_replay.py = scripts/d2_conv.control() (ideal 12-trial decision sequence as PWL into transistor-level dac_sw) + cmp_p with the clock pulses at the D3 STA instants per corner (DAC edge -> rise 21.0 / 39.6 / 83.8 ns, width 3.2 / 5.9 / 12.3 ns at ff -40 / typ 27 / ss 125), SCLK 2 MHz (T = 500 ns), 3.3 V, typ 27 / ss 125 / ff -40.
  Six Vin per corner: 1.15, 2.15 V and 0.3 LSB above the code levels 1024 (0.8252 V, MSB-1), 1536 (1.2377 V), 2048 (1.6502 V, MSB), 2560 (2.0627 V): the trial that tests that level has a ~0.3 LSB margin, so its error is that bit's threshold error. 1024 / 3072 are outside the claimed 1.15-2.15 V range (1024 is included, 3072 not run).
  Reference run = the same netlist with an IDEAL 1.65 V on dac_sw.vcm and cmp_p.inp. Metric d_k = (plate - ref node) 1.5 ns after the comparator rise (it contains the comparator's own evaluate shift, identical in both runs); delta_k = d_k(variant) - d_k(ideal) = code error in LSB (1 LSB = 0.806 mV). offset = delta_12 (final trial, every code); threshold error of a bit = delta at its transition trial MINUS the corner's offset.
- RESULT (sim/i2_summary.txt; 90 + 54 runs): [offset / its spread over the 6 Vin / worst threshold error beyond the offset, LSB]
    I2 Cref 3.5 pF (vhalf 20 pF):  typ -18.2 / 0.06 / 0.39,  ss -14.9 / 0.06 / 0.44,  ff -23.8 / 0.35 / 0.65   (ff -40 FAILS 0.5)
    I2 Cref 7 pF  (vhalf 20 pF):   typ  -9.3 / 0.02 / 0.25,  ss  -7.6 / 0.02 / 0.23,  ff -12.4 / 0.25 / 0.47   (MEETS <= 0.5 at all three corners; ff has 0.03 LSB margin)
    I2 Cref 7 pF, vhalf 10 pF:     typ -9.3 / 0.03 / 0.24,  ss -7.6 / 0.03 / 0.22,  ff -12.4 / 0.27 / 0.46
    I2 Cref 7 pF, vhalf 1 pF:      typ -9.3 / 0.03 / 0.24,  ss -7.6 / 0.03 / 0.23,  ff -12.4 / 0.26 / 0.46   (same as 20 pF: the divider decap is no longer needed for the conversion)
    (iv) I1 vhalf 20 pF alone, same replay: typ -2.1 / 3.75 / 1.0 (bit 2560: +1.55),  ss -1.0 / 5.31 / 1.5 (+2.04),  ff -3.6 / 2.28 / 0.6 (+2.80): spread over Vin 2.3-5.3 LSB, threshold errors up to 2.8 LSB, trials 9-12 vary by 2.7-3.2 LSB: FAILS 0.5 (better than the I1 hybrid estimate of 1.2-5 LSB, same conclusion).
  Per trial, typ 27 C, Vin 1.6502 V (MSB transition), Cref 7 pF / vhalf 1 pF: reference-node error vs its value just before the plate switch opens, measured just before each of the 12 clock rises: -0.24 +1.01 +0.59 +0.66 +0.70 +0.72 +0.71 +0.69 +0.68 +0.67 +0.67 +0.67 LSB (the vhalf-alone run: -0.16 +0.23 +0.03 ... -0.10, i.e. smaller before the clock, but 12.4 LSB peak
  over all runs because the divider node follows the plate swing; I1's quantities); 1.5 ns after the rise (the decision instant): +9.5 +13.8 +13.4 +12.4 +11.2 +10.5 +10.2 +10.0 +9.9 +9.8 +9.8 +9.8 LSB (vhalf alone: +3.3 +4.8 ... +3.1). Resulting code error delta_k = d_k - d_k(ideal): -9.0 -13.8 -13.2 -12.0 -10.7 -9.9 -9.6 -9.4 -9.3 -9.3 -9.3 -9.3 LSB (the same fixed offset, plus the proportional plate coupling in the early trials, which does not change a sign decision).
  Why it works: the floating Cref holds charge, the plate swing couples onto it once (k ~ 1 %, proportional to plate - ref, harmless for the sign), nothing recovers slowly (no R*C memory), and the comparator's own clock kick (a common-mode shift: +9.8 LSB at 7 pF, +19.2 at 3.5 pF = 1/Cref) is the SAME every trial and every code = the fixed offset. That fixed offset (-7.6 to -12.4 LSB with 7 pF) partly cancels the comparator's +11..14 LSB evaluate shift (D2); the net code shift moves between corners by about 5 LSB (ESTIMATE of the net: not re-derived), an offset, not a gain error.
- CHECKS REQUESTED: (1) switch charge-injection offset = ref-node step 20 ns after the plate switch opens: -0.18 LSB (7 pF, vhalf 20 pF), -0.25 / -0.30 (vhalf 1 pF, typ / ff), -0.35 (3.5 pF): a fixed code shift, already inside the offsets above. (2) kT/C on Cref (ESTIMATE, sqrt(kT/C)): 7 pF 21 / 24 / 28 uV rms = 0.027 / 0.030 / 0.035 LSB at -40 / 27 / 125 C (3.5 pF: 30 / 34 / 40 uV = 0.04-0.05 LSB); the plate samples the same vhalf 1-2 ns earlier, so most of it is common.
  (3) Cref settling within T_ACQ (sim/i2_twoframe.log, two frames 250 us apart, 1 V step, TG closing with the bottoms at the old code, Cref 7 pF, vhalf 1 pF; and Cref 3.5 pF / vhalf 20 pF): at the next sample the ref node minus vhalf is 0.0 uV and vhalf minus 1.65 V is 0.0 uV (resolution 0.1 uV, limit 80 uV) at typ, ss 125, ff -40; the vhalf node swings 416 / 399 / 426 mV after the resume (1 pF) and settles with R_out*(C+Cref) = 125 kOhm x 8 pF = 1 us (ESTIMATE) inside the 240 us window.
  (4) static current unchanged: 5.8 / 6.4 / 7.4 uA (Cref adds none). (5) AREA per ADC (ESTIMATE from the PDK area+perimeter formula, drawn): Cref 7 pF 59.1 x 59.1 um = 3,490 um2 (128 units of the 5 x 5 um cell, 54.5 fF), vhalf decap 1 pF 492 um2 (I1's 20 pF is 10,002 um2: the I1 number "9,900" was wrong and breaks MIMTM.8b by 2 um2), poly pair ~170 um2 drawn, TG ~ 10 um2:
  ~4,200 um2 per ADC (8 ADCs 0.034 mm2) versus 10,500 um2 for the I1 vhalf (0.084 mm2): saves 0.05 mm2 and meets the target.
- ADOPTED in the netlists (vhalf.spice defaults VR_C = 7 pF, VH_C = 1 pF; afe_ch has u_vr; PLAN.md section 9): Cref 7 pF behind the TG on tg_on / samb, divider 2 x 250 kOhm + 1 pF. The monitoring session decides; the I1 20 pF values stay reproducible with `.param`.
- CAVEATS / NOT DONE: ff -40 C is the corner with the least margin (0.46 vs 0.5 LSB; spread over Vin 0.26 LSB). The replay forces the ideal decisions (as D4b), so it measures threshold error per bit, not a code histogram; the comparator's evaluate shift flips the last trials against the ideal decisions (flag in the last column of i2_summary.txt, also for the ideal-ref run). Only 6 Vin per corner, 3 bit transitions plus the two range ends; MSB-1 at 3072 V and the fs / sf corners not run;
  one ADC at a time (no neighbour-ADC supply interaction, so D4's supply result stands only by superposition); no Monte Carlo of the TG / Cref mismatch (the plate and ref samples are 2-3 ns apart; a systematic difference is the fixed offset). Floating-node leakage on vref over the ~10 us conversion (hand ESTIMATE with the PDK-model ~10 fA junction floor: 10 fA x 10 us / 7 pF = 14 nV) is negligible.
  The 9-job memory limit of this container (ngspice aborts with "memory required ... more than available" above ~6 parallel jobs): scripts save only 4 vectors and pin one job per core.

## F1 findings (2026-11-20; audit fixes of Decision 44 and the 24-pad list of Decision 45; Claude Fable 5.2 / max; NO circuit was resized; logs AFE/review/sim/f1_*.log, AFE/adc/sim/f1_*.log, AFE/{amp,adc}/sim/f1_equiv_xschem.log, AFE/layout/lvs/*.log)
- NEEDS YOUR ATTENTION.
  (1) NEW, layout-relevant NOW (L2a draws Cin): the MIM terminals are NOT interchangeable in LVS (the netgen setup has no `permute` for MIM; Magic's tech file defines the device as `csubcircuit cap_mim_2f0_m4m5_noshield *mimcap *m4`, i.e. the top plate is
      terminal 1: read from the tech file, to be CONFIRMED by the first MIM unit that L2a extracts in its flow check).
      The simulation netlists put the TOP plate of the input capacitors on the driven side and the BOTTOM plate (the one with the capacitance to the substrate) on the high-impedance summing nodes: stage 1 `Xcin1 rec vn`, `Xcin2 ref vp`,
      stage 2 `Xcin in vn2` (Cf1, Cf2, Cc, the DAC units, Cref, C_T, C_VRS already have their top plate on the sensitive node). The simulations cannot tell (the MIM model is a symmetric two-terminal C + r_leak).
      The LVS reference keeps the netlist order by default (nothing was decided); `mk_lvs_netlists.py --cin-top sum` writes the summing nodes on the top plates (stage 1 and stage 2). RECOMMENDED: decide "summing node on the top plate" and regenerate
      before L2a runs its LVS; otherwise LVS will force the bottom plate onto vn / vp / vn2.
  (2) Item 1 criterion "currents within 1 %": MET for the supply current (bias + channel: +0.08 / -0.40 / +0.65 % at typ / ff 85 / ss -40), the channel and the master; NOT met for the resistor branches themselves: ladders +1.6 / -8.6 / +11.2 %,
      vhalf +1.7 / -8.5 / +11.2 %. This is the device, not the edit: ppolyf_u_1k has corners 800 / 1200 ohm/sq (the 3k: 2250 / 3750) and tc1 -9.4e-4 /K (the 3k: -1.67e-3), and is 1.6 % lower at 25 C for 3x the squares. The numbers equal the audit's
      prediction (power_op.log rows 1k_3L) to the printed digit. No consequence found: taps move <= 0.49 mV, ADC codes identical at typ and ff 85, vhalf <= 8.4 uA (Decision 41b: <= ~10 uA).
  (3) AREA: the 3x longer resistors add 0.008 mm2 of blocks: 0.874 mm2 = 935 x 935 um at x1.30 (was 0.863), 0.997 mm2 = 998 x 998 um in the pessimistic x1.50 case (was 0.984): NO margin against the 1000 x 1000 um outline given to the organizer
      in the pessimistic case (review/sim/f1_area.log). First lever: decap under the Cin plates (-0.092 mm2, AUDIT 4.5).
  (4) LVS rule 3 changes the circuit that is built: the comparator's two ideal 40 fF capacitors become 5 x 5 um MIM units of 54.52 fF. Measured on the design netlists (adc/sim/f1_x2_inl_step.log): code offset +1.5 LSB (typ) / +1.9 LSB (ff 85)
      (so about -28.5 / -38 LSB instead of the -30 / -40 of Decision 43e), step at code 2048 +1.30 -> +0.80 LSB (typ), +1.55 -> +1.30 LSB (ff 85), step at 1536 -1.08 -> -1.08 (typ), -1.08 -> -0.95 (ff 85): neutral to slightly better. NOT applied to the
      simulation netlists (CMP_CA stays 40f; L1b extracts the real value).
  (5) The code offset and the steps depend on junction capacitance: the cells of the LVS reference (same devices, but no ad / as / pd / ps) read another -3.3 LSB (typ) / -5.2 LSB (ff 85) and the 2048 step becomes +0.92 / +1.80 LSB.
      Expect the offset (and the Decision 43b steps by a few 0.1 LSB) to move after PEX in L1b; the README numbers are pre-layout numbers.
  (6) Choices that L3a / L1d inherit and may change by re-running the script: strap resistor = Metal3 resistor rm3 2 um x 222 um (10.0 ohm typ, +-13 % corner; the salicided poly ppolyf_s would be 7.3 -> 15 ohm/sq at the slow corner);
      decap unit 20 x 20 um cap_nmos_03v3 (79 + 63 units; a 20 um gate gives about 3-4 ohm of series resistance per bank, ESTIMATE, the value X2 S4 assumed); the 15 pad-control ties are 0-ohm resistors in the LVS top (or tie cells inside afe_dig, L1d);
      the afe_dig black box has the L1d pin list in a PROVISIONAL order until `--dig-netlist` is used.
- ITEM 1, P-A1 / B1 (Decision 44a): ppolyf_u_3k -> ppolyf_u_1k, 3x the squares at 1 um width, in amp/spice/bias_genc.spice, bias_gen.spice and adc/spice/vhalf.spice. Check: review/scripts/f1_bias_op.py -> review/sim/f1_bias_op.log (the pre-F1 netlist is
  rebuilt from the new files and run again, so the differences have full resolution; it reproduces the audit rows `3k`); adc/scripts/x2_adc.py -> adc/sim/f1_x2_adc.log, f1_x2_compare.log. [typ 27 / ff 85 / ss -40 C, 3.3 V]

  | quantity | before (ppolyf_u_3k) | after (ppolyf_u_1k) | limit | verdict |
  |---|---|---|---|---|
  | lengths, 1 um wide | ladder A 241.7 / 33.3 / 275 um, ladder B 125 / 150 / 275 um, vhalf 2 x 83.3 um | A 725 / 100 / 825 um, B 375 / 450 / 825 um (2 x 1650 um), vhalf 2 x 250 um per ADC | - | an LVS device now |
  | taps vcm_in / vg1 / vcm_out / vg2, change | (typ 1.64842 / 1.84956 / 1.64938 / 2.54960 V) | typ +0.47 / -0.28 / +0.45 / +0.29 mV; ff 85 +0.38 / -0.41 / +0.49 / +0.31 mV; ss -40 +0.47 / -0.19 / +0.39 / +0.25 mV | 0.5 mV | PASS (worst 0.49 mV) |
  | reset level vrs, mirror bias vbn, amplifier output DC | - | vrs +0.47 / +0.37 / +0.47 mV; vbn 0.000; output +0.46 / +0.46 / +0.39 mV | - | follow the taps |
  | supply current, bias + one channel | 74.37 / 119.29 / 46.83 uA | 74.43 / 118.81 / 47.13 uA (+0.08 / -0.40 / +0.65 %) | 1 % | PASS |
  | channel; master | 68.86 / 111.01 / 43.07; 1.683 / 2.683 / 1.049 uA | unchanged (0.00 %) | 1 % | PASS |
  | ladder current A + B | 3.83 / 5.59 / 2.72 uA | 3.89 / 5.11 / 3.02 uA (+1.6 / -8.6 / +11.2 %) | 1 % | NOT MET (attention 2) |
  | vhalf current per ADC | 6.31 / 9.18 / 4.47 uA | 6.41 / 8.40 / 4.98 uA (+1.7 / -8.5 / +11.2 %) | 1 % | NOT MET (attention 2) |
  | audit prediction (power_op.log rows 1k_3L), 5 corners | - | same to the printed digit (0.01 uA, 0.1 mV) | - | PASS |
  | ADC alone, closed loop, 12 inputs typ | codes 1436 .. 2571, code - ideal -30.33, T +30.05 LSB | the same 12 codes in both frames, -30.33, +30.05 LSB (max change of T 0.003 LSB); ff 85, 8 inputs: same codes (-41.62) | same codes | PASS |
  | chip static power / record mode | 2.003 / 3.200 / 1.267 mW; 2.084 / 3.283 / 1.351 mW | 2.006 / 3.178 / 1.282 mW; 2.087 / 3.261 / 1.365 mW (review/sim/f1_power_total.log) | - | - |
  | poly footprint (area.py model) | ladders + Rb 2,194 um2; vhalf pair 280 um2 per ADC | 5,890 um2; 840 um2 per ADC | - | attention 3 |

  Every other reference to the 3k device was updated: xschem bias_gen.sch regenerated by scripts/gen_a4a_sch.py and re-netlisted (xschem == hand netlist: structure PASS for ota1 / ota2 / bias_gen, op / ac / ol2 / noise within 0.0024 %, amp/sim/f1_equiv_xschem.log),
  the comment of the three models_*.spice, a4a_collect.py, review/scripts/power_op.py (its three variants are now built from the new netlists), area.py, xcheck.py. Left on purpose: the Decisions / findings above and saved logs.
  Not re-run: bias start-up (the ladders are not in the start-up path; Rb was 1k already), amplifier ac / noise at corners (taps move < 0.5 mV; the typ gain was re-measured in item 4: 60.0559 dB).
- ITEM 2, P-A2 / B2 + Decision 45 (top/dbs_afe_top.v, stubs_analog.v, tb_top.v, info.yaml, TAPEOUT.md, layout/PLAN.md section 9, adc/README.md; review/tb/{top_ba.v, tb_audit.v, stubs_audit.v}):

  | | before | after |
  |---|---|---|
  | pads (info.yaml entries) | 32: 25 analog (E, IPG, REC, REF), CS, DIN, SCLK, RSTN, DOUT, VDD, VSS | 24: 17 analog (E[7:0], IPG[7:0], REF), CS, DIN, SCLK, RSTN, DOUT, VDD, VSS |
  | data pad on the top | port DOUT | ports DOUT_OUT (= adc8_top.dout, to pad A) and DOUT_IN (from pad Y, unused: DOUT_IE = 0), as the organizer template requires for a bidirectional pad |
  | pad-control pins | 16, names not verified | the same 16; names checked against review/sim/organizer/template_info.yaml lines 26-66 (_PD _PU _CS _SL _IE _OE _PDRV0 _PDRV1; _PD _PU for inputs): all match, all driven |
  | REC | top port REC[7:0], afe_ch port rec | internal net `rec` of afe_ch (record TGATE OUT = afe_chc.rec) |
  | top port bits | 48 | 41 |
  | info.yaml comment | "tie DOUT_OE=1" | DOUT_OE = ~CS, the values of every control pin |
  | gds/dbs_afe_top.gds | 1000 x 1000 um PR boundary | untouched |
  | top simulation top/sim/i0_top.log | PASS, 0 errors | PASS, 0 errors; same log except the line number of $finish; REC is read from the internal nets, one check of the strap nets added |

- ITEM 3, P-A4 / M2 (Decision 44d; adc/spice/dac_sw.spice, comparator.spice; top/dbs_afe_top.v, stubs; adc/scripts/{x2lib, d4lib, d5lib, i1_vhalf, i2_replay}.py, adc/tb/tb_dac_{conv,replay}.spice; adc/xschem/cmp_p):

  | | before | after |
  |---|---|---|
  | dac_sw pins | 36: ... vcm vdd vss ... | 37: ... vcm vdd vdd_dac vss ...; vdd_dac = source + n-well of the 13 bottom-plate driver PMOS (26 terminals), vdd = n-well of the 13 sampling-TG PMOS (13 terminals) |
  | cmp_p supply pin | vdd | vdd_cmp, same position (22 device terminals); cmp_inv and the unused cmp_n unchanged; xschem cmp_p regenerated: structure PASS, 4 simulations within 1.4 % (adc/sim/f1_equiv_xschem.log) |
  | afe_ch supply ports | vdd, vss | vdd (afe_chc, one-shot, OR2, vhalf, Cref switch, samb inverter, sampling-TG wells, routing-TGATE wells), vdd_cmp (cmp_p), vdd_dac (drivers + the gdp tie), vss |
  | top netlist | one net VDD, no decap, no strap | VDD = analog strap + ADC-main strap (afe_ch.vdd and .vdd_cmp), vdd_dac behind the cell afe_rstrap; cells afe_decap 0.125 nF (VDD) and 0.1 nF (vdd_dac); stubs for the digital simulation |
  | devices in the LVS top | none | rm3 2 um x 222.2 um = 10.0 ohm typ between VDD and vdd_dac; cap_nmos_03v3 79 units (125.9 pF) on VDD, 63 units (100.4 pF) on vdd_dac, 20 x 20 um each, 3.98 fF/um2 (56,800 um2) |
  | S1 ADC alone, typ, 12 inputs | X2 codes | the same 12 codes (run after item 3 and again on the final state) |
  | X2 S4, 8 ADCs, typ, full scale, 3 MHz | 0 code changes; dT 0.018 LSB; residue 0.113 LSB; droop 0.13 / 2.92 mV | 0; 0.019; 0.113; 0.13 / 2.92 mV (adc/sim/f1_x2_s4_summary.log) |

  x2lib.adc_cell keeps the X2 S4 / S5 partition by default (cmp_p, vhalf and the Cref switch on the main rail; the whole dac_sw incl. the TG wells and gdp on the DAC strap) so that every X2 number stays reproducible; `vana=` / `vtg=` give the chip partition for L3b.
  Every single-rail testbench ties both dac_sw supplies to its one supply (7 instantiations, each checked for 37 nodes). The untracked scratch testbenches adc/tb/d5_65*.spice (not in git) still have the old pin list.
- ITEM 4, P-A5 / M3 (Decision 44e): layout/scripts/mk_lvs_netlists.py -> layout/lvs/{afe_chc.spice (afe_chc, fs_oneshot_c, OR2, amp_ch), adc_ch.spice (dac_sw, cmp_p, vhalf, vrefs, INV, adc_ch), bias_genc.spice, dbs_afe_top.spice, mk_lvs_netlists.log}.
  It reads the simulation netlists and module afe_ch / dbs_afe_top of the Verilog top (no connection is typed twice), evaluates every parameter to a number, writes the analog cells flat (names = the simulation hierarchy with `_`), and STOPS if a rule
  does not find its elements, if an ideal element is left or if a device is not an LVS device. Options: `--cin N[,W,L]`, `--cin-top rec|sum`, `--decap W,L`, `--rstrap MODEL,W,L`, `--dig-netlist <afe_dig powered netlist>`.

  | rule of AUDIT 4.9.3 | simulation netlist | LVS reference |
  |---|---|---|
  | 1 MIM name | cap_mim_2f0_m2m3_noshield (139 per channel + 1 in bias_genc) | cap_mim_2f0_m4m5_noshield; terminal 1 = top plate |
  | 2 ideal elements | Rbrk x 2 (100 ohm), Rt, Rmm (10 TOhm), Cpm, Cpb0-11, Cpbd (2 fF) | removed; vng joined with vn, vng2 with vn2 |
  | 3 comparator Cxa1, Cxa2 | ideal 40 fF | one 5 x 5 um MIM unit each, 54.52 fF (attention 4) |
  | 4 Cin1, Cin2 | one plate 100.012 um = 10,002 um2 each (above the 10,000 um2 limit) | 2 pieces of 70.649 x 70.649 um = 4,991 um2 each, 20.0000 pF per capacitor (ratio to Cf1 stays 100). The audit's 70.72 um keeps the AREA and gives +0.20 % of capacitance (the perimeter term doubles), outside its own 0.1 % |
  | 5 Cref | one plate 59.07 um | the same, 3,489 um2 (P-A10) |
  | 6 resistors | ppolyf_u_1k after item 1 | 7 in bias_genc (60 + 2 x 1650 squares), 2 per vhalf (250 squares); ppolyf_u_3k is refused |
  | 7 top | Verilog: adc8_top + dbs_ctrl + bias_genc + 8 x afe_ch | SPICE: afe_dig black box (273 pins: the L1d list + VDD VSS) + bias_genc + 8 x afe_ch + 3 supply devices + 15 pad-control ties (0-ohm resistors); DOUT_IN is the one unconnected pin |
  | 8 TGATE, standard cells | no power pins in the Verilog | TGATE VDD / VSS and the OR2 / INV VDD / VNW on the analog strap vdd, VSS / VPW on vss |

  Device lines: afe_chc 38, fs_oneshot_c 9, bias_genc 17, dac_sw 182, cmp_p 25, vhalf 3, vrefs 3; amp_ch 53, adc_ch 215, afe_ch 272; chip without the digital macro 8 x 272 + 17 + 3 = 2196. Checks (layout/scripts/check_lvs_netlists.py -> layout/lvs/check_lvs_netlists.log, and review/scripts/xcheck.py):
  A. the LVS reference of bias_genc + afe_chc SIMULATES like the design netlists (typ, tb_a4c_op / tb_a4c_ac): against the design netlists without diffusion parameters every DC node within 10 uV, all 20 device currents identical, gain 60.0559 dB,
     f_lo 0.2023 Hz, f_hi 653.66 Hz identical (with diffusion parameters f_hi is 653.47 Hz): PASS. B. the flat ADC cells convert in the X2 replay (12 inputs, typ): one uniform shift of -1 .. -3 LSB, spread 0.16 LSB: PASS (the shift = Cxa + no Cpb + no
     diffusion parameters, attention 4 / 5). C. netgen 1.5.318 reads all four files (each top cell matched against a copy): PASS; it keeps the 15 ties as devices of class r. D. xcheck, with its own parser: each LVS cell equals the flattened simulation
     netlist device by device and terminal by terminal under the rules (38 / 9 / 17 / 182 / 25 / 3 / 3 devices, 0 differences); afe_ch of the LVS top equals module afe_ch net by net (57 nets, 85 connections); the 8 channel instances, the 273 afe_dig pins and
     the 15 ties equal the Verilog top.
- ITEM 5, documentation: adc/README.md (supply and reference description, DOUT_OUT / DOUT_IN, accuracy claim of Decision 43c, code offset of 43e, nine protocol rules incl. RSTN only while CS is high / 160-clock frames / first frame after a pause / 300 Hz host filter /
  no power-down / E and IPG inside 0..VDD with the TGATE Ron / REF connected, power-up with the >= 5 s wait and the 200 LSB check, results rows for offset, steps, INL, top of range, supply, power, board table, decap density, open items 1 / 8 / 9 + LVS + X2_ADC_INC);
  TAPEOUT.md (CURRENT STATE section with the 24-pad list; 10 older sections marked SUPERSEDED or PARTLY SUPERSEDED, the Decision-30 question marked DECIDED; title no longer "DRAFT"); layout/PLAN.md (section 9 rewritten, the stale lines of sections 4 and 5); adc/NOTES.md header (mux / 31.25 us / 9 bits);
  this file: Environment (ad/as/pd/ps, `cut`, the X2 simulation rules, the thread statement, the process option), PDK facts (MIM rules and plate order, 1k poly, decap density), Open questions (11 older entries marked answered, accepted or moot; 5 F1 entries added). Also (Decision 43a): the `cut` pipe was
  removed from adc/scripts/dgrun.sh and amp/scripts/run_a4a.sh (carriage returns become newlines instead). NOT touched: Decisions and findings (Decision 23 still says 13-20 dB: 11.7-18.9 dB today; Decision 42a "128 units": one plate, Decision 44i),
  the README digital-area row (pre-I1 numbers), other `cut` pipes that only filter .op / .ac logs (amp/scripts/run_a4b_loop.sh, run_a4c_tbl.sh, run_a3_diag.sh), AFE/prompts/*.
- ITEM 6, regression:

  | run | result |
  |---|---|
  | D3 RTL testbench (adc/scripts/run_d3_sim.sh) | exhaustive 4096 frames PASS; 4 edge-case runs PASS; matrix 19 PASS + 1 FAIL = ss 125 C at 4 MHz (known, above the 3 MHz maximum); logs unchanged in git |
  | top/run_top_sim.sh | RESULT PASS, 0 errors, REC / IPG == dbs |
  | review/scripts/run_tb_audit.sh (rtl AND gls, 72 runs) | all 72 logs and the summary are byte-identical to the audit's. Failing assertions: X1.contention, X5.word0, X5.after33d (every build), T11.crowbar (gate level), and T2.settle at the MIXED corner only (= M4, accepted by Decision 44f) |
  | review/scripts/xcheck.py -> review/sim/f1_xcheck.log | 114 checks, 93 OK, 3 MISMATCH, 18 NOTE; rows B1 (2), B2 (2), M2 (6), M3 (10), m7 (2), m1 (1): all OK |
  | remaining MISMATCH | lvs_config.json LVS_SPICE_FILES and LVS_VERILOG_FILES name spice/<top>.spice and verilog/gl/<top>.v, which do not exist (L4 fills lvs_config.json; the SPICE top is layout/lvs/dbs_afe_top.spice); module afe_dig does not exist yet (L1d) |
  | remaining NOTEs worth a look | TGATE: the extracted view TGATE_extracted.cir has only a SUB pin and the PMOS bulk on an unnamed net: not pin-compatible with TGATE.spice (L3a); bracketed pad names; pad-control values; the four *_ready flags are false |

- Choices I made (rule 10): (a) the new dac_sw pin sits right after vdd; the sampling-TG n-wells stay on `vdd` = the analog strap, as the L1a pin list implies (X2 S4 had them on the DAC strap: no DC current either way; alternative: one well row with the
  drivers on vdd_dac, simpler to draw); gdp is tied to vdd_dac, the source rail of the dummy PMOS. (b) cmp_p's pin is RENAMED to vdd_cmp (the alternative, keeping `vdd` and connecting it to vdd_cmp one level up, changes fewer files but leaves the cell pin
  ambiguous). (c) strap resistor and decap are cells of the Verilog top (afe_rstrap, afe_decap with a capacitance parameter) so that the SPICE top can be generated from the Verilog; in the LVS top they are devices. (d) LVS references flat per analog cell,
  with the two layout cells amp_ch / adc_ch cut out of module afe_ch by a table (names from PLAN section 3); their pins `out` / `vin` are the net amp_out. (e) Cin pieces sized for equal CAPACITANCE, not equal area. (f) rm3 for the strap, 20 x 20 um decap units,
  0-ohm ties (attention 6). (g) F1 logs have the prefix f1_ and the audit / X2 logs are left as evidence (x2_adc.py, x2_inl_step.py, x2_s4.py and power_total.py got a log-name option); the tb_audit logs were regenerated in place and did not change.
  (h) the default plate order of Cin follows the netlists (attention 1).
- Suggested edits to AFE/prompts/layout_run.md (not made; the monitoring session owns the prompts): L2a / L1a: name the cells amp_ch (file afe_chc.spice) and adc_ch, state the plate order once decided, "re-run mk_lvs_netlists.py --cin N,W,L with the drawn
  pieces"; L1b: "X2_ADC_INC=<extracted netlist>" and "compare offset and steps with adc/sim/f1_x2_inl_step.log"; L1d: "then run mk_lvs_netlists.py --dig-netlist <powered netlist>; decide whether the 15 pad-control ties live in afe_dig";
  L3a: "--decap and --rstrap with the drawn sizes; the TGATE extracted view".
- Not done: ss -40 for the Cxa what-if; the S4 / S5 runs with the chip rail partition (vana / vtg); netgen against a layout (none exists); bias start-up and corner ac / noise re-runs with the 1k poly; nothing under AFE/layout/amp/ or FLOW.md was touched.

## LP findings (2026-11-20; layout preparation: the kit that lets ONE person run L1a, L1d, L2b, L1b, L3a, L3b, L4 without asking anyone; Claude Fable 5.2 / max; files AFE/layout/{SPEC.md, floorplan.json, ACCEPT.md, RUNBOOK.md, scripts/, tb/, baseline/, sim/}, AFE/dig/, AFE/prompts/layout_run.md; NO design netlist or RTL was changed)
(written step by step; the summary "ready per phase / still needs a human / risks" is at the end of this section)
- STEP 1, ENVIRONMENT CHECK: `bash AFE/layout/scripts/check_env.sh` (1-2 min; PASS / WARN / FAIL per line with the action on FAIL); reference run of this machine AFE/layout/sim/check_env_ref.log.
  New kit commands used by every later phase: `AFE/layout/scripts/flow.py drc | lvs | pex | info | versions` (official KLayout deck --variant=D, Magic, netgen -batch; JSON reports that gate.py reads),
  `kl.sh` + `kpdk.py` (KLayout-Python generators with the PDK pcells), `slot.sh` (machine-wide limit of 3 heavy jobs, common rule 4), `mk_testcells.py` (the five test cells below).
  Facts established with evidence in that log (all on generated test cells, DRC variant D = 0 violations, netgen LVS = match):
  (a) rm3 IS an LVS-extractable resistor of variant D (Decision 46e): 2 x 222.2 um extracts as `rm3 r_width=2u r_length=0.2222m` and matches. BUT the PDK pcell `metal_resistor` draws only layer 110/13; Magic builds the
      device from Metal3 AND RES_MK (110/5) AND 110/13 in ONE cell, so the pcell extracts as two open Metal3 stubs and NO device. Use `kpdk.metal_res()` (draws all three shapes; DRC clean).
  (b) cap_nmos_03v3 (20 x 20 um unit) extracts as a device, also when it lies UNDER a MIM plate (Decision 46c, test cell lp_cin_decap: one 70.65 um Cin piece over 4 decap units + a Metal3 shield: 1 MIM + 4 cap_nmos_03v3 on the right nets).
  (c) MIM terminal order (Decision 46a): terminal 1 of cap_mim_2f0_m4m5_noshield = TOP plate (FuseTop / Metal5 side). A 5 x 5 um unit with plates labelled TOPNET / BOTNET extracts as `X0 TOPNET BOTNET ...`; LVS matches `X1 TOPNET BOTNET`
      and does NOT match the swapped reference. F1's reading of the tech file was right; the `--cin-top sum` references are correct. (L2a's FLOW.md was not on origin: check_env.sh compares with it once it exists.)
  (d) NEW, a trap for every post-layout number: Magic treats the MIM top-plate tile as Metal4 of the TOP-plate node, so a stock `ext2spice` attaches the capacitance between the capacitor and whatever lies below it (substrate, wells,
      Metal1-3) to terminal 1. With the summing nodes on the top plates (Decision 46a) every PEX run would show a false parasitic on vn / vp / vn2, the DAC plate, the bridge node and the Cref node (test cell: 305.3 fF from the top plate
      to the shield, 59-61 aF/um2 = the Metal4-to-Metal3 value of the tech file; in silicon the bottom plate shields it). `flow.py pex` extracts twice (stock, and with the MIM tile removed from the parasitic rules) and moves the
      difference to the bottom-plate net(s): 10.7 fF left on the top plate, 294.6 fF moved to the bottom plate. Post-layout phases must use `flow.py pex`, never a raw ext2spice.
  (e) The PDK pcells (nfet, pfet, nfet_06v0_nvt, cap_mim, cap_nmos, resistors, vias) DO work in KLayout batch mode once the environment variable USER exists (the container has none; draw_efuse.py reads it): `kl.sh` sets it.
      This corrects AFE/layout/PLAN.md section 2 ("gdsfactory fails at import").
  (f) Grid: every drawn dimension must be a multiple of 5 nm. The F1 default Cin piece 70.649 um is off grid (DRC *_OFFGRID): draw 70.65 um (20.0006 pF, +0.003 %); no regeneration is needed: netgen's 1 % property tolerance covers every grid rounding (largest 0.04 %, SPEC.md section 6).
  (g) The routing switch TGATE/TGATE.gds alone fails DRC (DF.13_MV / DF.14_MV: no well / substrate tap within 15 um) and extracts with its PMOS bulk on an unnamed net and the NMOS bulk on the bare substrate (the F1 note). With ONE filltie
      standard cell abutted (test cell lp_tgate_tap) it is DRC clean and matches TGATE.spice: L3a places every TGATE with a tap cell.
  (h) MIM rules that constrain the top-level wiring (KLayout deck mim_b.drc; design manual 10.4.2 fetched 2026-11-20): MIMTM.10 no Via3 on the bottom plate, the bottom plate is contacted only from above (Via4 / Metal5) or by a Metal4 wire;
      MIMTM.11 capacitors may share one bottom-plate polygon only up to 10,000 um2 of MIM, so the REF net (16 pieces) must leave each plate pair through Via4 / Metal5 and must not be one Metal4 polygon; guideline "no sensitive matching analog
      circuitry underneath MIM" (decap and wiring are allowed).
  (i) ngspice here starts 8 threads per job unless the job directory has a .spiceinit (confirmed again); the PEX device lines (r_width / r_length, c_width / c_length, ad / as / pd / ps) load in ngspice with the PDK libraries
      (add `.lib ... moscap_typical` for cap_nmos_03v3: the amplifier model files do not include it).
- CHANGE OF PLAN (user, 2026-11-20, during LP-finish): NO approval gate. ACCEPT.md is IN FORCE as written (status line "IN FORCE (user, 2026-11-20); reviewed after the fact, changes
  arrive through AFE/layout/REVIEW.md"); no phase waits for a human; every phase writes AFE/layout/reports/<phase>.md (10 fixed sections, checked by gate.py) besides its findings + Results-log
  row, commits AND pushes (checkpoint push after ~2 h); AFE/layout/REVIEW.md (created empty, written only by the user / monitoring session) is read and applied at the start of every phase.
  No numbered Decision was written for it (the monitoring session records it).
- INTEGRITY (LP-finish, `git diff a6aff2f 4e7f30f`): no pre-LP evidence log changed except AFE/layout/lvs/*.log and the regenerated AFE/layout/lvs/dbs_afe_top.spice. Three X2 logs
  (adc/sim/x2_done.txt, x2_s5_summary.log, x2_s5_typ.log) had been overwritten by the LP crosstalk / end-to-end wrappers before the commit; they were restored from git and the cause fixed
  (x2_s1.py / x2_s5.py got the X2_LOG_PREFIX option that x2_s4.py already had; the wrappers use prefix lp_top and move the logs into their output directory, lptb.x2_collect). One stray log
  (adc/sim/lp_top_s4_ff-40.log) was moved to layout/baseline/top_supply_x2_s4_ff-40.log. What LP changed in tracked scripts, old default behaviour unchanged in every case:
  x2lib.py: options X2_ADC_CELL (one layout cell instead of the four ADC cells), X2_AMP_INC / X2_AMP_SUBCKT / X2_AMP_NODESET (foreign amplifier cell); all empty by default (step 6 checked the
  default output byte-identical at 5 corners). x2_s1.py: X2_LOG_PREFIX for x2_done.txt (default x2). x2_s4.py: X2_QDIG (default 1.5e-12 = the old constant). x2_s5.py: X2_LOG_PREFIX and
  X2_CAL_NPZ (defaults = the old file names). sta_audit.py / .tcl: `--dig <LibreLane final dir>` (+ --load / --intran); without it the log is identical (re-run in LP-finish: no line differs
  from review/sim/sta_audit.log). run_tb_audit.sh: mode `dig <final dir>` with its own log directory; other modes unchanged. run_top_sim.sh: mode `dig` (afe_dig equivalence); default unchanged.
  gen_gl.py: two optional arguments (run dir, top module); without them unchanged. check_lvs_netlists.py: tie-cell form recognised, C2 hierarchical read when the top names a macro netlist,
  LVSCHK_NPAR (default 3 = old). mk_lvs_netlists.py: --ties (default dig = Decision 46e), --dig-netlist, --decap-n, --follower (default native); the F1 options behave as before.
- STEP 2, FLOORPLAN AND CELL CONTRACTS: AFE/layout/SPEC.md + AFE/layout/floorplan.json (written by `python3 AFE/layout/scripts/floorplan.py build`; `check` tests fit, slots, pins, decap rows,
  macro pins). Outline 1000 x 1000 um, 30 um pin ring; two rows of four channel slots 235 x 375 um (north R0, south MX), afe_dig 820 x 110 um between them at (30, 445), bias_genc <= 100 x 142 um
  at (870, 429); bias corridors 14 um at the amplifier ends, strap corridors 26 um at the ADC ends, an 8 um control corridor and a 7 um spur corridor per channel. Slots vs the F1 estimates
  (review/sim/f1_area.log, which already contain block factors): amp_ch 220 x 263 um = +12 % (the tight item), adc_ch 220 x 104 = +53 %, bias_genc +42 %, afe_dig 43 % utilisation as built.
  41 port bits / 24 pads with side, position, layer and target (default positions, no organizer DEF yet). Decap: 74 units on the ADC-main strap (117.9 pF) and 64 on the DAC strap (102.0 pF),
  20 x 20 um cap_nmos_03v3, in the strap corridors, the west ring and under each Cref: no area of its own and nothing under the amplifier; the decap-under-Cin lever of Decision 46c is
  proven on test cell lp_cin_decap (check_env.sh C2 / C4) and kept as reserve. `floorplan.py check --dig-pins AFE/dig/trial/afe_dig_pins.json`: 18 PASS, 0 FAIL (layout/sim/floorplan_check.log).
- STEP 3, GOLDEN TESTBENCHES: AFE/layout/tb/ (lptb.py library + 17 tb_*.py checks, compare.py, mk_fake_pex.py, run_baselines.sh). Every check takes `--netlist schematic|<PEX>` and `--corner`,
  writes JSON + log; a PEX netlist is adapted by port NAME, internal nodes are found through their MIM anchor capacitors, the operating point comes from a power-up transient. The PEX path is
  proven end to end: tb_tgate on the Magic PEX of lp_tgate_tap gives 21.019 / 15.603 / 34.232 kOhm vs 21.021 / 15.605 / 34.233 schematic; amp_ac, amp_noise, amp_loop (PM 79.07 vs 79.17 deg)
  and adc_codes (offset -29 vs -30 LSB) on synthetic Magic-style netlists. 25 baselines in AFE/layout/baseline/ reproduce the history: gain 60.056 / 60.061 / 60.041 dB, f_lo 0.202 / 0.226 /
  0.237 Hz, f_hi 653 / 998 / 422 Hz, noise D8 1.668 / 1.847 / 1.540 uV, PM 79.2 / 76.4 / 81.1 deg, PSRR 0.571 / 0.579 / 0.566, THD 0.035 / 2.63 / 0.046 % (typ / ff 85 / ss -40); bias start-up
  with 8 channels and 1k poly 3.7 ms / 1.0 ms / 3565 ms (the 5 s wait holds); ADC offset -30.2 / -40.1 / -22.0 LSB, steps at 2048 +1.30 / +1.55 / +0.42 LSB, settling of the MSB trials 0.07 /
  0.10 / 0.11 LSB (matched), 0.65 LSB at the mixed corner; end to end (amplifier -> its ADC) offset -30.2 / -40.4 / -22.1 LSB, INL below 2.05 V 0.76 / 1.99 / 0.32 LSB, the amplifier adds
  <= 0.08 LSB, sine gain 60.007 / 59.866 / 59.990 dB; 8-channel power-up error <= 0.70 / 0.42 / 1.21 mV (vrs dip 15 / 14 / 137 mV); crosstalk induced by conversions 0.001 LSB; 8-ADC supply
  run residue 0.113 LSB typ, 0.496 LSB ff -40 C 3.6 V (with the D3 digital charge; L3b uses the afe_dig charge 33.7 / 38.4 pC per cycle, dig/reports/power_dig.log). `compare.py --phase
  L2b | L1b | L3a | L3b --selftest`: all PASS (93 / 69 / 9 / 65 rows). Two limits were corrected in LP-finish to match the baselines: top_xtalk dcode_conv is reported, not a limit (the victim
  sits 0.28 LSB from a code edge, so 1 code toggles with a 0.001 LSB effect); top_pwrup8 vrs_dip = change <= +30 mV against the baseline (ss -40 has 137 mV pre-layout).
  MAJOR FINDING (ACCEPT.md section 2): the 0.2 Hz high-pass corner and the offset tolerance rest on the six pseudo-resistor transistors having NO junction area in the design netlists. With the
  area every extracted netlist will have (the "junction convention"), f_lo is < 1 mHz (typ, ss -40) / 0.053 Hz (ff 85), a 10 mV electrode offset shifts the output by +969 / +0.9 / +1250 mV
  (railed at typ and ss -40), and after a reset the output drifts by about 1 mV/s per mV of offset; RST_AMP does not cure it, the gate taps cannot either (layout/sim/lp_prdiff_study.log,
  baseline/*_junction.json). Handling in force: gates use the design convention (lptb strips the area of exactly these six devices), the junction convention is run and reported, layout
  draws the six devices with minimum identical area, host rules (record-start RST_AMP, repeat RST_AMP when a channel leaves +-200 LSB), and the test plan measures f_lo and the drift first.
- STEP 4, ACCEPT.md (IN FORCE): limits per phase (DRC 0, LVS unique match with the 1 % property tolerance, PEX census + MIM correction, 75 post-layout limit rows generated from
  accept_limits.json, the digital limits (a) >= 21.0 ns, (c) >= 20.0 ns, slack >= 10 ns, skew <= 3 ns, accepted test-bench failures), a decision ladder of 53 entries (G, D, L, P, R, Q, C, A,
  S, X, N, O) with pre-approved degradations, organizer defaults for every open question (macro name, DEF, slot, pads, supply pads, bond model, native Vt, metal fill), BLOCKED.md format.
- STEP 5, DIGITAL MACRO (AFE/dig/LP_STEP5.md): afe_dig.v + LibreLane recipe (run_dig.sh), trial hardened: 819.84 x 109.76 um, 1706 cells, 43 %, no CTS + one clock buffer (Decision 44h),
  STA met at 5 corners (setup ws >= 91.7 ns, hold ws >= 0.229 ns), 0 slew / cap violations, Magic DRC / LVS / antenna 0, KLayout DRC variant D 0 (dig/reports/klayout_drc.log); limits (a)
  22.14 ns, (c) 22.39 ns (20.59 ns against the SCLK pin), slack 13.75 ns, switch-pair skew <= 0.78 ns (dig/reports/sta_audit_dig.log); gate-level testbench at 5 corners + MIXED, 2 / 3 MHz:
  only X1.contention, X5.word0, X5.after33d, T11.crowbar (+ T2.settle at MIXED) (dig/sim/tb_audit_dig_summary.log); equivalence EQUIV PASS (dig/sim/top_dig.log, re-run in LP-finish).
  LVS references regenerated with `mk_lvs_netlists.py --decap-n 74,64 --dig-netlist AFE/dig/trial/afe_dig.pnl.v` (tie cells are macro pins, no 0-ohm device); check_lvs_netlists.py A, B, C
  PASS (C2: netgen reads the SPICE top plus the Verilog macro, 2493 instances). New: dig/scripts/sta_taps.py writes the tap timing for tb_adc_timing.py (dig/reports/sta_taps.json).
- STEP 6, NATIVE-Vt FALLBACK (AFE/amp/sim/lp_rvt_summary.md, lp_rvt_result.json): 31 follower candidates screened. CHOSEN variant `rvt` (AFE/amp/spice/ota2_rvt.spice + afe_chc_rvt.spice):
  nfet_03v3 8 x 10u/1u in an isolated p-well (deep n-well on vdd), bulk on its source; one device line changes, +575 um2 per channel. Against the original (typ / ff 85 / ss -40): gain
  60.062 / 60.071 / 60.046 dB, f_hi 690 / 1065 / 441 Hz (+4-7 %), noise 1.668 / 1.847 / 1.541 uV (unchanged), PM unchanged, swing follows 0.27-2.48 / 0.57-2.59 / 0.10-2.34 V, THD at ff 85
  2.505 -> 0.078 % (the Decision-28 miss disappears), real-DAC settling 0.022 / 0.010 / 0.026 LSB, X2 S1 end to end offset -30.27 / -40.47 / -22.05 LSB and amplifier contribution <= 0.08 LSB
  as the original (adc/sim/lp_rvt_x2_s1_report.log). Runner-up without deep n-well `ota2_rvt_nodnw.spice` (10 x 10u/0.28u): passes with 32 mV margin at ss -40 C, f_hi 602 / 925 / 386 Hz.
  Pre-approved in ACCEPT.md ladder N, triggered only by the organizer refusing the native device (or their precheck rejecting it); executable without an edit: `mk_lvs_netlists.py --follower rvt`
  (one reference line changes, tested) and `AFE_AMP_VARIANT=rvt` for the testbenches (tb_amp_ac typ reproduces 60.0625 dB).
- STEP 7, SUBMISSION SCAFFOLD: info.yaml (24 pads in the floorplan perimeter order, template keys), lvs_config.json (SPICE top + the macro netlist verilog/gl/afe_dig.v), README.md (block diagram,
  pins, host rules incl. the new record-start / RST_AMP-repeat / 0.3 s-after-stimulation rules, board needs, test plan; `<L4: ...>` placeholders only for GDS, W x H, ladder S-2),
  documents/export_control_answers.md (technical answers; the .docx stays for the signer: python-docx is not installed). `python3 AFE/layout/scripts/check_submission.py --pre`: PASS (13 PASS,
  6 PENDING = files L3a / L4 produce; layout/sim/check_submission_pre.log). Padring fork (review/sim/organizer/padring_fork_README.md): the organizer builds the frame with
  `SLOT=workshop make librelane` (nix-shell, about 2 h 15 min); we only deliver the block (RUNBOOK.md "L4 and after").
- STEP 8, PROMPTS: AFE/prompts/layout_run.md rewritten for one person (run order with the pairs that may run together: L1a + L1d, L2b + L1b; self-contained phase blocks with inputs, steps,
  gate, ladder, crash recovery rule 11, REVIEW.md rule 12, report rule 7, commit + push); the L2a block is unchanged except for one line pointing at gate.py. AFE/layout/RUNBOOK.md (plain
  language). AFE/layout/scripts/gate.py <phase> (common checks, DRC / LVS / PEX reports bound to the GDS by sha1, Cref keep-out, decap count, compare.py, macro checks, submission check,
  report sections, REVIEW items), tested: L1d gate on a frozen copy of the trial passes every technical line; DRC / LVS / PEX readers on test cells; the Cref keep-out finds a Metal3 shape
  inside the footprint. `python3 AFE/layout/scripts/check_prompts.py`: every one of 154 paths in layout_run.md, RUNBOOK.md, ACCEPT.md, SPEC.md exists or is made by a named phase (PASS).
  check_env.sh: 32 PASS, 0 FAIL (layout/sim/check_env_ref.log; the disk check now separates the repository disk, >= 3 GB, from the scratch disk, >= 10 GB).
- REPORT.
  (1) READY per phase: L2a (running): gate.py L2a re-checks its DRC / LVS and the slot. L1a: contract (SPEC.md 3.3), reference, flow.py, gate with the Cref keep-out. L1d: the full recipe
  passed every limit in the trial; L1d re-runs it and freezes AFE/dig/final/. L2b: PEX with MIM correction, 11 amplifier checks in both conventions with baselines and limits. L1b: 4 ADC checks
  with baselines, tap timing of the macro. L3a: floorplan, pins, straps, decap counts, LVS top with the macro, TGATE + tap check; the top generator itself is L3a's work. L3b: 6 system checks
  with baselines, supply model fed from the layout and the macro power report. L4: info.yaml, lvs_config.json, README, export answers, check_submission.py.
  (2) STILL NEEDS A HUMAN: only organizer answers (macro name / DEF, slot, pad allocation, supply pads and bonding, native-Vt device, bond-wire model; each has a default in ACCEPT.md section 5),
  the export-control signature and the party questions, and the creation of / push to the submission repository. ACCEPT.md is in force; the user reviews afterwards through REVIEW.md.
  (3) RISKS NOT REMOVED: (a) the pseudo-resistor junction-area effect above (silicon may follow either model; the host rules limit the damage, the cure is a redesign); (b) amp_ch has only
  12 % slot margin over an estimate (ladder A); (c) the full-chip top generator, routing and full-chip DRC / LVS run time are untested (L3a; netgen timeout ladder L-6); (d) the PEX of the
  full chip may be slow (ladder P-1); (e) the organizer's integrated LVS tool is unknown (lvs_config.json follows the template; our sign-off is netgen); (f) no organizer answer yet on the
  native-Vt device and the macro name (defaults + ladder N / O); (g) the 8-ADC supply error at ff -40 C 3.6 V was already at 0.5 LSB pre-layout and the hardened macro draws 40 % more charge
  per cycle than the D3 macro the baseline used (ladder S: more decap, two bond wires); (h) the trial macro is in /tmp of this machine: L1d regenerates it (2 minutes).

## L2a findings

**Summary (top lines, as the prompt asks)**
- **Native-Vt follower `nfet_06v0_nvt` (10u / 2u): status UNCONFIRMED by the organizer (Decision 44k, ACCEPT.md ladder N applies if they refuse).** It passes the open-source decks: Step 1 test cell lp_flow: DRC 0, netgen match
  (`AFE/layout/amp/flowtest/flow/lp_flow.drc.json`, `.lvs.json`); in amp_ch it sits inside its own P+ ring (device `fol`, PDK pcell with its native / dual-gate markers) and DRC / LVS are clean with it. The layout keeps the native device.
- **MIM terminal order: terminal 1 of `cap_mim_2f0_m4m5_noshield` = TOP plate (Metal5 / FuseTop)**, same as F1 and check_env C3: extracted `X1 TOPNET BOTNET cap_mim_2f0_m4m5_noshield` (`AFE/layout/amp/flowtest/flow/lp_flow.pex.spice`),
  netgen matches TOPNET first and the full cell matches with vn / vp / vn2 on the top plates. No `--cin-top rec` needed.
- **LVS reference used: `AFE/layout/lvs/afe_chc.spice` subckt amp_ch, the default of `python3 AFE/layout/scripts/mk_lvs_netlists.py` (`--cin-top sum`), NOT regenerated** (the Cin pieces are drawn 70.65 um squares against 70.649028 in the
  reference, +0.0014 %, inside the 1 % tolerance); command of the run: `python3 AFE/layout/scripts/flow.py lvs --gds AFE/layout/amp/amp_ch.gds --top amp_ch --ref AFE/layout/lvs/afe_chc.spice --out AFE/layout/amp/flow`.
- **DRC (official gf180mcuD deck, `--variant=D`, `flow.py drc`): 0 violations. LVS: "Circuits match uniquely." (46 devices, 35 nets, 14 pins = the pins of AFE/layout/lvs/afe_chc.spice, no extra pin).** Logs: `AFE/layout/amp/flow/amp_ch.drc.json`, `amp_ch.lvs.json`, `amp_ch.lvs.out`.
- **Does NOT fit its slot: amp_ch as built is 219.25 x 385.25 um = 84,466 um2 against the slot 220 x 263 = 57,860 um2 (+46 %) and the F1 estimate 51,626 um2 (+64 %).** gate.py last line: see the end of this section ("gate.py L2a").
  ACCEPT.md ladder A (area) applies in the next phase; the numbers it needs are below.

**What was built** (all generated, nothing drawn by hand; `AFE/layout/amp/mk_amp_ch.py`, `amplib.py`, `blocks_amp.py`, `router.py`; GDS `AFE/layout/amp/amp_ch.gds`, sha1 b9407198f235d12f32265702ff358816556814b0, 3.0 MB)
- Cin: 2 x 2 checkerboard of four 70.65 x 70.65 um MIM pieces (4,991 um2 each, 5.5 um corridors), Cin1 (rec / vn) on the diagonal A1 / A2, Cin2 (ref / vp) on B1 / B2. **Plate order of Decision 46a: summing nodes vn / vp on the TOP plate
  (Metal5), rec / ref on the bottom plate (Metal4) of every piece**, also for stage 2 (vn2 on the top plate of Cin and Cf2) and for Cf1 / Cf1'. Wiring of the block: vn through the centre of the corridors on Metal5, rec as a 0.9 um Metal4 strap
  in the vertical corridor (A1 - A2) leaving south (router pad) and north (Metal5 pin), vp on an inner Metal5 lane around the east / north side, ref on Metal4 tabs + outer Metal5 lanes. **Nothing under the four plates but the MIM:
  no comp / poly / contact / Metal1-3 / via1-3 / well / implant inside the plate footprints (`AFE/layout/amp/check_amp.json`, `under_cin_clean: true`; Decision 46c reserve intact).** Cin : Cf1 = 99.972 (formula of the netlists, ESTIMATE;
  reference 100.0000): Cf1 / Cf1' (9.79 um) lie in a strip directly below the block next to the vn / vp descenders, same orientation.
- OTA 1: input pair 2 x (16 x 50u/2u) as ABBA, four units of 8 fingers each (A = vn, B = vp, drains d1 / o1 by Metal2 rails, common source tail), with the tail / mirror group (xmb, xmt, xm7: 3 units of 2 x 50u/4u, gate ibias1) in the SAME
  n-well and N+ ring (vdd); poly-only dummy lines at both ends of both groups. Loads xm3 / xm4 (50u/16u, 2 each) as ABBA of single-finger units with the P+ ring (vss) and dummies; xm6 (4 x 50u/16u) and the two sink arrays (24 and 6 fingers 16u/4u)
  in their own P+ rings. Stage 2: diff pair xm1 / xm2 (1u/40u as 4 units of 0.5u/40u, ABBA, stacked), tail 1u/20u, loads 1u/20u, follower nfet_06v0_nvt in a P+ ring. Park TGATE (nfet 1u/0.5u + pfet 2u/0.5u), the four gate-mux transistors,
  the one-shot (8 small transistors + 0.28u/40u + C_T 44.6 um) and the OR2 with a filltie abutted (n-well + tap): single-finger tiles in two rings (P+ / N+).
- **Pseudo-resistors: 6 x pfet_03v3 0.22u/0.5u, drawn identically (block `pr_block`), minimum junction area (one 0.22 x ~0.4 um diffusion pair), EACH with its own n-well tied to its source net (vn, v1, vp, vcm, vn2, out) by an N+ tie of 0.42 x 0.5 um**
  (SPEC.md 3.2 item 4; design convention of ACCEPT.md section 2 is the gate of L2b). Pairs `pr1` (vn / v1), `pr2` (vp / vcm), `pr3` (vn2 / out), wells 3.4 um apart.
- P+ guard rings (vss) around every NMOS block, N+ / n-well rings (vdd) around every PMOS block; every device has a tap in its ring (DF.13 / DF.14 clean).
- Pins (labels, `check_amp.json`): rec / ref Metal5 on the top edge; vbn vcm vg1 vcmo vg2 vrs Metal3 at the top-left corner (1 um pitch); sw_rec sw_rec_b rst_amp Metal2 on the west edge (within 60 um of the top); vdd vss Metal4 3 x 3 um at the
  top-right; out Metal3 on the bottom (inner) edge. A deviation from SPEC.md 3.2: the Metal2 / Metal3 pins are 0.5 um wide, the channel is wider than the slot (see below), so L3a re-places the pin wires anyway (ACCEPT.md G-5).

**Area, W x H** (`AFE/layout/amp/amp_ch.build.json`, `check_amp.json`; F1 numbers from AFE/review/sim/f1_area.log, which contain block factors 1.5 / 2.5)
| block | as built (bbox um2) | F1 / PLAN estimate |
|---|---|---|
| Cin block: 4 pieces + corridors + Metal5 lanes (164.7 x 167.3) | 27,554 | 2 x Cin drawn 20,005, footprint 21,036 |
| input pair + tail group `ota_p` (152.6 x 63.6) | 9,705 | (pfet 50/2 m32 4,877 + 50/4 m6 1,524) x 1.5 = 9,601 |
| xm3 / xm4 mirror + xm6 (96 x 62 + 74 x 58) | 10,244 | nfet 50/16 m8 6,909 x 1.5 = 10,364 |
| stage 2, follower, two sink arrays | 7,018 | nfet 16/4 m30 2,520 x 1.5 + stage-2 devices |
| MIM outside Cin (C_T, Cin2, Cc2, Cc1, Cf2, 2 x Cf1) | 6,416 | 5,912 |
| small devices (muxes, park, one-shot, OR2, 3 pseudo-R pairs) | 1,423 | x 2.5 on 285 + 65 |
| **sum of the blocks** | **62,361** | **afe_chc 49,312 + fs_oneshot_c 2,314 = 51,626** |
| **cell bbox 219.25 x 385.25** | **84,466** | slot 220 x 263 = 57,860 |
So every block is within +/- 5 % of F1's estimate except the Cin block (+31 %: the 5.5 um corridors, the Metal5 / Metal4 lanes and the pad strip are inside it), the sum of the blocks is +21 % and the remaining 22,100 um2 (26 %) is white space of the
row packing (4 rows of different heights, 3 um gaps, the landing-pad / ring overhead of every block is already inside the bbox). The same finger counts and widths were used for every device (no sizing change).
**8-channel extrapolation (ESTIMATE): 8 x 84,466 = 0.676 mm2 for amp_ch alone = 68 % of the 1000 x 1000 um outline (Decision 45); at the slot area 8 x 57,860 = 0.463 mm2.** With the ADC slots (8 x 22,880 = 0.183 mm2), afe_dig (0.090 mm2) and
bias_genc (0.014 mm2) the chip is about 0.96 mm2 BEFORE corridors, rings and the 30 um pin ring: it does not fit as built; a channel would be 385 + 104 + 8 = 497 um tall against the 375 um of floorplan.json, two rows 994 um + macro 110 um.
**Ladder A (next phase) with numbers: A-1 (rotate) does not help (the cell is 385 tall, 219 wide: rotated 385 x 219 breaks the 235 um channel pitch). A-3 is the way: the cell must lose 31 % of its area; the Cin block + MIM column (34,000 um2 = 59 % of
the slot) cannot shrink, so the devices + wiring (now 28,300 um2 of blocks + 22,100 um2 of white space) must fit in about 24,000 um2. Levers that are NOT used yet: (1) finger width 25 um instead of 50 um for xm3 / xm4 / xm6 / the pair (halves the
height of rows 3 and 4, 62 / 64 um -> about 35 um; the width of the rows doubles, the pair + tail must then go to two rows); (2) the gate landing pad (3 um) of each of the 11 array units and the rings (about 15 % of the device area); (3) the white space right of
row 4 (60 um) and above the short blocks of row 2; (4) the stage-2 MIM column next to the Cin block holds only 6,400 of 8,500 um2.**

**Rules from PLAN.md section 5 / SPEC.md 3.2** (what was done, what was not)
- Common-centroid pair + dummies: ABBA of four 8-finger units (each device 16 x 50u/2u), poly-only dummies (a shorted dummy transistor is NOT dropped by netgen: tested, FLOW.md section 4.3). Two-dimensional centroid (ABBA / BAAB rows) was not drawn.
- P+ guard ring on analog NMOS: yes, every NMOS block. Park switch and gate muxes: inside their own rings (small-device tiles).
- Summing node / pseudo-R / REC leakage: pseudo-resistors have minimum identical junction area and own wells; the long wires of vn / vp / vn2 / rec / the pseudo-R nodes carry a SOFT 2 um clearance (router cost); achieved edge-to-edge clearance to
  other nets on the same layer over the middle of the wire (ends excluded): vn 2.5 um minimum (0 of 227 nodes closer than 2 um), vp 1.5 um (10 of 218), vn2 0.5 um (22 of 493), rec 0.5 um (47 of 245); the pseudo-R S nodes are Metal1 links 2 um
  from the neighbouring pads of the same block. **The Metal1 vss guard around the summing-node connections was NOT drawn** (the router has no guard feature); wire lengths (ESTIMATE, grid nodes x 1 um): vn about 290 um, vp 280, **vn2 550 (the
  s2pair block is on the other side of the cell from the stage-2 capacitor column)**, rec 280, v1 540. These are the first suspects if L2b misses f_hi / noise / PSRR (ACCEPT.md R-2, R-3, R-6, R-8).
- Metal1-3 never run over Cin pieces; the vn / vp / rec connections to the Cin pieces are Metal5 / Metal4 only.
- Supply: vdd / vss are routed like signals (0.5 um wires, vdd about 560 um, vss about 860 um of wire in total, ESTIMATE): resistance of a long branch about 70 - 140 ohm. L2b should look at the IR drop (amp_ac idd / vout limits) and L3a replaces them
  by straps; the cell is on the analog strap only (no vdd_cmp / vdd_dac).

**Native-Vt / OR2 / other facts that matter later**
- The 7t5v0 OR2 (5 V devices, dual-gate marker) is in the channel with its own filltie; netgen matches pfet_05v0 / nfet_05v0 with VNW = vdd, VPW = vss.
- PEX is L2b's, but it runs: `flow.py pex` on the final GDS: 121 devices (the OR2 is flat: 3 + 3 5 V devices), 383 C (2,993 fF), 0 R (mode c), MIM correction moved 8.9 / 16.4 / 3.8 / 78.1 / 78.2 / 13.8 fF from top-plate nets to the bottom plates;
  the netlist loads in ngspice and gives a .op with guessed bias levels (`AFE/layout/amp/pex_feasibility/`, PORT ORDER of the PEX subckt: rec ref vbn vcm vg1 vcmo vg2 vrs out sw_rec sw_rec_b rst_amp vdd vss: connect by name).
- Findings that cost time and are written down in FLOW.md for L1a: the pcells' off-grid shapes (snapped copies in amplib), `Bulk Tie` unusable, dummy transistors are devices for netgen, MIM spacing rules measured with the deck, labels of library cells.
- Ladder entries used: D-1 (off-grid, snapped in the generator), L-1 (property error, fixed in the drawing: W of the stage-2 pair 2 u -> four 0.5u units, the 0.28u one-shot device via `con_bet_fin=0`), none of A (area FAIL is left for the next phase), none of G-3 (terminal order is as F1 assumed).

**gate.py L2a** (`python3 AFE/layout/scripts/gate.py L2a --gds AFE/layout/amp/amp_ch.gds --run`; copy of its last line, run on the final GDS): `GATE L2a: FAIL  (1 FAIL)`. The one FAIL is the slot: `FAIL  5  as-built amp_ch 219.25 x 385.25 um fits its slot 220.00 x 263.00 um` (floorplan.py check: 16 PASS, 1 FAIL); DRC 0 violations, LVS match, the findings section and the Results-log row PASS. Per the prompt this does not stop L2a: the next phase handles it with ACCEPT.md ladder A.

## L1a findings (2026-11-20; adc_ch layout up to DRC + LVS; Claude Sonnet 5.5 / high; files AFE/layout/adc/{mk_adc_ch.py, dac_lib.py, cmp_lib.py, cmp_top.py, vhalf_lib.py, rlib.py, adclib.py, router.py, adc_ch.gds, adc_ch.build.json, dac_sites.log, keepout.log, FLOW_ADC.md, test/}; reports AFE/layout/reports/{L1a,L2a}.md; logs AFE/layout/sim/flow/adc_ch.{drc,lvs}.json)

**Summary**
- **adc_ch: DRC 0 violations (official gf180mcuD deck, variant D), LVS "Circuits match uniquely." against subckt adc_ch of AFE/layout/lvs/adc_ch.spice (reference NOT regenerated; 34 pins, all by name; netgen flattens the hierarchical cmp_p / dac_sw / vhalf / vrefs / inv_1 of the reference against the flat layout).** GDS AFE/layout/adc/adc_ch.gds, sha1 in the report. Cref keep-out PASS (nothing below Metal4 inside the 59.07 um plate footprint).
- **Gate L1a: FAIL, one line: the slot. adc_ch as built is 265.85 x 126.25 um = 33,564 um2 against the slot 220 x 104 = 22,880 um2 (+47 %) and the F1 estimate 14,911 um2 (+125 %).** adc_ch is also wider than the 235 um channel pitch. The size is the sum of the parts (table below), see "Area". ACCEPT.md ladder A has no entry that helps an ADC of this size (A-2 `adc_h` 104 -> 100 goes the wrong way); the decision belongs to the floorplan (section "What the next phase must know").
- The L2a FAIL (amp_ch 84,466 um2 against 57,860 um2) was merged with this report (reports/L2a.md, "L2a findings" above).
- Three facts of SPEC.md 3.3 that do not hold (details in AFE/layout/adc/FLOW_ADC.md section 3): (1) the DAC unit pitch of 6.8 um is not legal: neighbours of different nets need top plates 2.4 um apart (MIMTM.1, bottom plates 1.2 um apart) = pitch 7.4 um; same-net neighbours can be 1.0 um apart (pitch 6.0 um, one merged bottom plate);
  (2) a dummy MIM with both plates on vss is extracted as a shorted cap_mim device that netgen does not drop: the dummy rows are plain Metal4 / Metal5 bars; (3) the 20 um keep-out band between the driver row and the DAC array cannot hold the driver rows of a real layout (two rows of 11 and 14 um + routing = 29 um).

**What was built** (generated, nothing drawn by hand; run `bash AFE/layout/scripts/kl.sh AFE/layout/adc/mk_adc_ch.py out=AFE/layout/adc/adc_ch.gds`)
- DAC: 127 units 5 x 5 um + bridge 5.085 x 5 um on two halves of 8 rows (LSB half west, node m; MSB half east, node t), every bit in point-symmetric pairs about the centre of its half (rows 0, 1, 6, 7 = the largest bit, rows 2 and 5 the next, rows 3 and 4 the small bits, row 4 = point reflection of row 3);
  units of one run are 6.0 um apart and share ONE Metal4 bottom-plate polygon, different nets 7.4 um; a 6 um channel between rows 3 and 4 carries the pads of the small bits; one plain-metal dummy row (vss) south and north of the array; Metal5 top-plate bars per row joined by a trunk outside the array
  (t east, m west), the bridge's bottom plate (m) leaves through a Via4 pad in the channel and a short (about 10 um) Metal5 strap to the east end of the LSB row 4 bar. Site of every unit: AFE/layout/adc/dac_sites.log (128 units: b11 32, b10 16, b9 8, b8 4, b7 2, b6 1, bridge 1, b5 32, b4 16, b3 8, b2 4, b1 2, b0 1, bd 1).
  Centroids: every bit with more than one unit has its centroid within 0.02 um of the centre of its half; the single units b0 / bd and b6 / bridge sit at the row ends (+-23.1 um, +-5.5 um: they are each other's point-symmetric partner, ESTIMATE of the effect: 1 unit x 0.02 % per 23 um at 1 %/mm gradient, negligible).
- Drivers: 13 bottom-plate drivers (pfet 2u/0.28u + nfet 1u/0.28u, bd driver with its pfet gate tied to vdd_dac) and 13 sampling TGs in three rows of single-finger tiles (nfet row 110 x 11 um in a P+ ring, driver pfets 60 x 14 um in the vdd_dac well, TG pfets in the vdd well), sources tied to the rings in Metal1;
  the two reset switches (nfet 0.5u/0.28u) sit next to the lower ends of the t / m trunks, rst_sw and rstm are one net. Supplies as SPEC.md 3.3: vdd analog (TG / Cref switch / inverter wells), vdd_dac (driver wells), vdd_cmp (comparator wells), one vss.
- Comparator cmp_p: two MIRROR-IMAGE halves (one routed cell of 51 x 39 um, the second instance placed with a mirror about the axis x = 0: pair 4 x 20u/0.5u = 80u/0.5u each, preamp MIM units Cxa (5 x 5 um, top a1 / a2, bottom vss), reset and mc devices, latch halves, output inverters) + a centre column (tail pfet mt1, clock inverter ic);
  vref enters on the east edge, t on the west edge, both on Metal5 over a Metal3-Metal5 via stack; routed centre nets: tl 38 um, clkb 61 um, cmp_clk 66 um, o1 / o2 24 um each (equal), vss 54, vdd_cmp 57 um (ESTIMATE, grid nodes x 1 um). The two latch nets cross in the centre column on different tracks (exact mirror symmetry of that crossing is impossible).
- vhalf: the two 250 um x 1 um ppolyf_u_1k resistors as ONE serpentine of 20 segments of 25 um in the order A B A B ... (chain A rows 0, 2, .. 18: vdd to vcmd, chain B rows 19, 17, .. 1: vcmd to vss), same orientation, plain poly dummy lines at both ends, jumpers on Metal2 lanes (A at the head, B one um further out via a Metal1 strip), the 22.18 um MIM (top vcmd, bottom vss).
  netgen sums the series segments: 2 ppolyf_u_1k devices after flattening, W = 1.0, L = 250 each.
- Cref: ONE 59.07 um MIM, top plate = vref (Metal5 strap 23.5 um to the comparator pad), bottom plate vss through a Metal4 tab and pad; nothing below Metal4 in its footprint (no Metal1-Metal3 of this cell, the router is kept out; gate.py: PASS). Cref switch (nfet 1u + pfet 2u) and the inverter samb = not tg_on (inv_1 drawn from the 5 V pcells, netgen flattens the reference to the same two devices) sit between the comparator and Cref.
- Pins: control pins Metal2 at the inner edge at x = 12 15 18 21 24 (rst_sw tg_on dac_gdn cmp_clk cmp_q), dac_gp / dac_gn from x = 27 at 3 um pitch (dac_gp[11] 27, dac_gn[11] 30, .., dac_gn[0] 96), vdd_cmp 110-130, vdd_dac 140-160, vss 170-210 (Metal4, inner edge), vin Metal3 at the outer (top) edge x = 4, vdd Metal4 at the east edge (y 48-54).

**Area, W x H (as built, bounding boxes; F1 numbers from AFE/review/sim/f1_area.log)**
| block | as built W x H (um) | um2 | F1 estimate (um2) |
|---|---|---|---|
| DAC array + trunks + pads (core 104.9 x 72.4 um) | 116.2 x 73.6 | 8,553 | 8,416 (12 x 11 sites at 6.8 um) |
| driver rows (13 drivers + 13 TG + 2 resets, with the routing space between the rows) | 123 x 29 | 3,567 | 391 (MOS footprint x 2.5) |
| comparator cmp_p | 118.0 x 40.6 | 4,791 | 877 |
| vhalf serpentine + 22.18 um capacitor | 34 x 64 + 27 x 23 | 2,176 + 637 | 1,415 |
| Cref (plate 59.07 um + tab / pad) | 63.2 x 60.3 | 3,811 | 3,720 |
| Cref switch + inverter (four small blocks) | 4 x about 11 x 12 | 563 | 6 |
| **adc_ch bounding box** | **265.85 x 126.25** | **33,564** | **14,911 (slot 22,880)** |
The array and Cref match F1; the rest does not: the F1 factor 2.5 on small devices missed the real overhead of rings, landing pads and routing (the comparator is 5.5 x its estimate, the driver rows 9 x), and the poly resistors and the capacitor of vhalf need 2 x. The sum of the block bounding boxes alone (24.1k um2) already exceeds the slot (22.9k um2).
**8-channel extrapolation (ESTIMATE): 8 x 33,564 = 0.269 mm2 for adc_ch + 8 x 84,466 = 0.676 mm2 for amp_ch (L2a) + afe_dig slot 0.090 mm2 + bias_genc slot 0.014 mm2 = 1.049 mm2 BEFORE corridors, rings and the 30 um pin ring, against the 1.000 mm2 outline: eight channels do not fit with the two cells as built.**

**Keep-outs and wire lengths** (AFE/layout/adc/keepout.log, adc_ch.build.json; ESTIMATES from grid nodes x 1 um)
- control wires to DAC top plates / vref / Cref (limit 20 um, SPEC.md 3.3 rule 6): cmp_clk 44.0 um, dac_gn[*] 43 um, dac_gdn 43.2 um, dac_gp[*] 26.0 um; **tg_on 5.2 um (at the Cref switch it drives: allowed as "the last 10 um at the device") and rst_sw 12.0 um (at the reset switch next to the t trunk: same exception)**.
- t node: Metal5 trunk + row straps + strap to the comparator pad about 114 um, m node about 94 um, vref strap 23.5 um (Metal5, < 30 um) + 36 um of Metal2-Metal4 router wire to the Cref switch drains; the bottom-plate nets b0 .. b11 / bd are 164 - 379 um of Metal2 / Metal3 / Metal4 (about 40 ohm for 220 um of 0.5 um wire: negligible against the driver, but check in L1b: Q-2 / Q-5).
- Over / under the DAC: Metal2 / Metal3 only in the 6 um channel strip; Metal4 keeps 1.2 um from every plate; the t / m trunks cross the Metal4 exit tabs of the rows (about 1 um2 each).

**Rules / deviations** (all in the generator)
1. DAC unit pitch 7.4 um (different nets) / 6.0 um (same net) instead of 6.8 um; array 104.9 x 72.4 um core instead of 122.4 x 68 um; the ring of dummy units is a plain-metal row south and north only (the west / east sides carry the exits); no dummy MIM units (netgen would count them).
2. bd driver: its pfet gate is tied to vdd_dac (reference: gdp = vdd_dac); b0 / bd and b6 / bridge at the row ends (see above).
3. Reset switches next to the trunks, Cref switch next to Cref (the SPEC keeps all switches in the driver row; vref < 30 um needs the switch at Cref).
4. Power: the driver sources are tied to their rings in Metal1; the rings are joined by the router (supplies routed like signals, 77 - 506 um of wire per rail; L3a replaces them by straps).
5. Cell outline 265.85 x 126.25 um; origin of the GDS bbox x = 3.75 um (the vin pin and the margin wires start at x = 3.75): the slot test uses width and height.

**Ladder entries used**: D-1 / D-4 style fixes inside the generator (M1.2a stub spacing of narrow devices, Via4 sea pitch, 5 V marker snapping, plain-metal dummies: FLOW_ADC.md sections 3 and 4); L: none needed (pin matching failed once because the comparator block was named cmp_p: renamed); A (area): A-1 (rotate) does not help (126 um wide x 266 um tall in a channel that is 375 um tall for amp_ch + adc_ch), A-2 gains nothing; the rest of ladder A belongs to the amplifier or to the whole floorplan.

**What the next phase must know**
- L1b (PEX + post-layout simulations of the ADC) can start on this GDS: DRC / LVS clean, PEX port order by name. The sites of the units for the bridge check are in dac_sites.log.
- **The floorplan needs a decision before L3a**: the two cells together are 1.049 mm2 (with 8 channels) in a 1.000 mm2 outline. Options with their cost: (A-6) N = 4 channels in one row: adc_ch (266 um wide) is wider than the 235 um pitch, so adc_ch must be re-packed to <= 235 um (taller; there is room in the 4-channel floorplan) or the pitch widened; (re-pack for 8) amp_ch to about 60 % of its area (the levers in the L2a findings) and adc_ch to about 70 %
  (comparator in one column with Cref above it, drivers in one row of multi-finger devices, vhalf pitch 2.2 um): needs about one more L2a-type and L1a-type iteration each, and is still on the edge; (A-7) N = 2.

## L1d findings (2026-11-20; afe_dig final hardening = re-run of the LP recipe, nothing in rtl/, AFE/adc/rtl/ or AFE/dig/afe_dig.v edited; Claude Sonnet 5.5 / high; run `bash AFE/dig/run_dig.sh final`, scratch run directory /tmp/lp_dig/design/runs/final; report AFE/layout/reports/L1d.md; frozen files AFE/dig/final/)

**Summary**
- **Gate L1d: PASS (0 FAIL).** The final run reproduces the LP trial: same structure, same numbers (the flow is deterministic: only the run tag / path lines of flow_summary.rpt, klayout_drc.log, sta_audit_dig.log, trial/run_dir.txt differ from the trial; sta_taps.json and power_dig.log are byte-identical).
- Equivalence `(cd AFE/top && bash run_top_sim.sh dig)`: EQUIV PASS (AFE/dig/sim/top_dig.log).
- Die 819.84 x 109.76 um (limit 820 x 110), core 806.4 x 101.92 um, 1706 std cells = 35,365 um2 = **43.0 % utilisation** of the core (flow_summary.rpt; floorplan.py's pre-hardening estimate was 37 %), 167 flops (159 on sclk_i + 8 capture flops), 18 repair buffers, routing up to Metal4, wirelength 82,705 um, route DRC 0, antenna 0, Magic DRC 0, LVS 0, XOR 0, 286 / 286 pins at the planned place. Clock = no CTS + `ck.u_ckbuf` (Decision 44h; ladder C-1 not touched). LibreLane v3.0.2, wall 54 s, peak RSS 548 MB.
- **STA after route (extracted SPEF, 500 ns period, 0.5 ns uncertainty; AFE/dig/reports/flow_summary.rpt):** 0 setup / hold / max-slew / max-cap violations at every corner:

  | corner | setup ws (ns) | hold ws (ns) |
  |---|---|---|
  | ff -40 C 3.6 V | 96.965 | 0.229 |
  | ff 125 C 3.6 V | 96.046 | 0.519 |
  | tt 25 C 3.3 V | 95.361 | 0.760 |
  | ss -40 C 3.0 V | 93.778 | 1.305 |
  | ss 125 C 3.0 V | 91.689 | 2.010 |

- **Tap limits (AFE/dig/reports/sta_audit_dig.log, line L1D_LIMITS, worst of the three SPEF sets):** (a) DAC edge -> comparator clock of ADC 0 at ff -40: 22.14 ns >= 21.0 PASS; (c) last window end -> next SCLK edge at the flop clock pins, ss 125: 22.39 ns >= 20.0 PASS (against the SCLK pin, (b): 20.59 ns >= 20.0 PASS); captured decision -> code register at 3 MHz, ss 125: slack 13.75 ns >= 10 PASS. Ladder C-2 not needed. AFE/dig/reports/sta_taps.json (L1b's timing input) regenerated: first comparator-clock tap T0 26.53 / 38.97 / 48.72 / 69.50 / 101.30 ns at ff -40 / ff 125 / tt / ss -40 / ss 125.
- **Skew of the 16 switch output pairs** (same channel, |sw_x edge - sw_x_b opposite edge| at the macro pins, sta_audit_dig.log section 7), closing edge: rec 0.23 / 0.33 / 0.39 / 0.56 / 0.78 ns, ipg 0.22 / 0.32 / 0.38 / 0.54 / 0.76 ns (ff -40 / ff 125 / tt / ss -40 / ss 125), worst 0.775 ns <= 3 ns. Sampling skew between the 8 channels (rst_sw fall spread) 0.20 .. 0.57 ns. Clock latency SCLK pin -> flops 0.54 .. 1.33 ns (ff -40 .. ss -40 min / max), spread 0.10 ns.
- **Power (AFE/dig/reports/power_dig.log):** pC per SCLK cycle 33.7 (tt 3.3 V), 38.4 (ff -40, 3.6 V), 42.1 (ff 125), 28.6 (ss -40), 30.6 (ss 125); tt = 111.1 pJ per cycle = 71.1 uW average (160 SCLK cycles per frame, 4 kS/s per channel); the clock network is 48 .. 50 %. L3b uses 33.7 pC (tt) and 38.4 pC (ff -40).
- **DRC:** KLayout official deck variant D on AFE/dig/final/afe_dig.gds: "PASS (0 violations)" (660 rules; AFE/dig/reports/klayout_drc.log names the committed GDS, 1,948,280 bytes).
- **Gate-level test bench on the hardened netlist** (run_tb_audit.sh dig, AFE/dig/sim/tb_audit_dig_summary.log; 36 runs = 6 corners x 2 / 3 MHz x 3 tests): only the accepted failing assertions X1.contention (12 lines), X5.word0 (12), X5.after33d (12), T11.crowbar (96) and T2.settle at the mixed corner FFN40_MIXED only (16, none elsewhere). Ladder C-4 not needed.
- **LVS references:** `python3 AFE/layout/scripts/mk_lvs_netlists.py --decap-n 74,64 --dig-netlist AFE/dig/final/afe_dig.pnl.v` (the old header had exactly these two options, with the netlist AFE/dig/trial/afe_dig.pnl.v); `check_lvs_netlists.py`: "SUMMARY: A PASS, B PASS, C PASS" (C: 2493 cell instances in afe_dig, hierarchical read matches its copy). AFE/layout/lvs/dbs_afe_top.spice changed only in its header line.
- `floorplan.py check --dig-pins AFE/dig/final/afe_dig_pins.json`: 18 PASS, 0 FAIL.
- Ladder entries used: none. No deviation from the prompt.

## R2 findings (2026-11-20; REVIEW.md item R2 = tightened floorplan for 8 channels, Decision 48; Claude Sonnet 5.5; files AFE/layout/{floorplan.json, SPEC.md}; report AFE/layout/reports/R2.md; no simulation, no layout)
- **Command:** `python3 AFE/layout/scripts/floorplan.py build --set ring=26 bias_corr=12 strap_corr=25 dig_h=80 ch_pitch=237 adc_h=104 pin_pitch_w=3.5 pin_y0_w=3.0`; `floorplan.py check`: 16 PASS, 0 FAIL (log AFE/layout/reports/R2.md section 5).
- **New floorplan** (outline 1000 x 1000 um): channel slot 237 x 397 um (ctl 8 | cell 222 | spur 7; adc 104 + amp 285 + TGATE zone 8); amp_ch <= 222 x 285 (+23 % over the F1 estimate), adc_ch <= 222 x 104 (+55 %), bias_genc <= 108 x 110 at (866, 445) (+19 %), afe_dig 820 x 80 at (26, 460) (51 % utilisation, estimate). Rows: ch0-3 at y = 565 (R0), ch4-7 at y = 38 (MX); strap corridors 25 um, bias corridors 12 um, ring 26 um.
- **Check 3e** (the only FAIL of the item's recipe: DOUT_IN / VDD touch): the 22 west pins at 4.0 um pitch from y = 4 reached 88 um, above the 80 um macro, and DOUT_IN landed on VDD. Fixed with the west pin parameters only: pitch 3.5 um from y = 3 um (last pin 76.5 um); VDD at y = 554, VSS at y = 446 unchanged in rule. R3 must harden afe_dig with these west pins (floorplan.json cells.afe_dig.pins.W).
- **Expected FAILs until later items:** `check --dig-pins AFE/dig/final/afe_dig_pins.json` (die 819.84 x 109.76, channel pin x for the 237 um pitch: R3); `check --gds amp_ch=... adc_ch=...` (218.75 x 309.25 / 265.85 x 126.25: R4 / R5).
- **Risks:** the ring analog lane is now 12 um (was 16) and the bias corridor 12 um: its 15 lines (7 signals + 8 vss) were 0.9 um pitch = 13.5 um, now 0.75 um pitch (SPEC.md section 5); L3a must check Metal2 spacing and the VDD / REF trunk widths. No numbered Decision written.

## R5 findings (2026-11-20; REVIEW.md item R5 = adc_ch re-pack to <= 222 x 104 um, Decision 48; Claude Sonnet 5.5; files AFE/layout/adc/{mk_adc_ch.py, dac_lib.py, cmp_lib.py, cmp_top.py, vhalf_lib.py, rlib.py, adclib.py, router.py, adc_ch.gds, adc_ch.build.json, dac_sites.log, keepout.log, FLOW_ADC.md, test/}; report AFE/layout/reports/L1a.md; no circuit change, LVS reference AFE/layout/lvs/adc_ch.spice not regenerated)
- **Result: adc_ch 219.50 x 103.67 um = 22,755 um2 (was 265.85 x 126.25 = 33,564, -32 %), slot 222 x 104 = 23,088 um2 (margin 1.4 %); DRC variant D 0 violations, LVS "Circuits match uniquely." (34 pins), Cref keep-out PASS, `floorplan.py check --gds adc_ch=...` 17 PASS 0 FAIL, `gate.py L1a` PASS.** First re-pack attempt, so the checkpoint rule of R1 did not trigger.
- **Where the 10.8k um2 came from:** DAC 8,553 -> 6,833 (the two plain-metal dummy bars of 7.4 um each are not drawn); driver rows 3,567 -> 2,540 (rings 1.0 um from the tiles instead of 2.5 um, DRC 0 in test/mk_drvtest.py; a tile with a tied source needs no pad column: pitch 3 um instead of 4 um for the pull-down and driver pfets); comparator 4,791 -> 3,880 (pair as 5 fingers x 16u instead of 4 x 20u, blocks 3 um apart, margin 2 um, centre +-8 um; tile pitch 3.5 um shorted vdd_cmp to vss, so it stays 4 um); vhalf 2,813 -> 1,894 (8 rows of 62.5 um at pitch 2.2 um instead of 20 rows of 25 um at 3 um, no end dummies; it now sits in the 20 um keep-out band under the DAC where SPEC.md 3.3 put it); Cref 3,811 unchanged; switch / inverter / reset switch blocks 563 -> 486. The packing: drivers bottom left, DAC above them (first plate row 20.9 um above the highest gate pad), comparator bottom right under Cref (t enters on the west side, vref on the east side under the plate: vref strap 6.5 um), Cref top right with its bottom-plate pad on the west side, switch / inverter / vhalf capacitor in the column between the DAC and Cref.
- **Deviations (details report section 7):** no dummy bars; vhalf folded without end dummies; `vdd` pin moved to the south edge x 215 .. 221 (the Cref plate fills the east edge; ladder G-5 wrap by L3a); rst_sw runs 5.0 um from the t trunk at its two reset switches (38 nodes) and tg_on 14.8 um from it over about 24 um at the Cref switch / inverter (26 of 28 control nets keep >= 21 um; both are quasi-static, to be confirmed in L1b); the t strap runs between the comparator top and the first plate row (Metal5, 79 um incl. the trunk; m 87 um).
- **For the other items:** the cell is full (103.67 of 104 um): R3 / R4 must not ask adc_ch for height (a taller afe_dig comes out of amp_h). Metal-only debug `test/probe_short.py` (KLayout connectivity, vias inside CAP_MK are not Metal4-Metal5 contacts) found three real shorts that only LVS reported as "failed pin matching"; two rules for tiles in this generator: a source stub column collides with the neighbour's drain column below 4 um pitch, and the serpentine of vhalf needs an even number of segment pairs.
- **L1b should look at:** bit-net wires 144 - 213 um, t 79 um / m 87 um of Metal5 (Q-3 step 2112, Q-4 alpha), the Cref switch strap (about 30 um on the vref node), the comparator input pair 2 .. 5 um from the lowest plate row, the missing dummy bars at the b11 / b5 edge rows (INL), tg_on / rst_sw coupling.

## R4 findings (2026-11-20; REVIEW.md item R4 = Cin 20 -> 15 pF, step 1 only: schematic simulations; STOPPED by the checkpoint of R1: a Decision 1 target fails; Claude Sonnet 5.5; files AFE/layout/{BLOCKED.md, baseline_cin15/}, AFE/layout/reports/L2a.md section 9; no layout, no LVS reference, no GDS change)
- **Result: BLOCKED.** With CF1V = 150f (Cin1 = Cin2 = 15 pF, ratio 100) the Decision-8 noise is **1.890 / 2.139 / 1.732 uV (typ / ff 85 / ss -40)** against 1.668 / 1.847 / 1.540 at 20 pF: the limit 2.0 uV (accept_limits.json amp_noise, ALL corners) FAILS at ff 85 (+7 %); ladder R-3 pre-approves only 2.05 uV at ff 85 and only for layout parasitics. `compare.py --phase L2b --selftest` on the 15 pF baseline: 92 PASS, 1 FAIL (this one).
- **Everything else passes** (design convention, typ / ff 85 / ss -40): gain 60.05 / 60.06 / 60.04 dB (no CF1V trim needed), f_lo 0.246 / 0.281 / 0.288 Hz (was 0.202 / 0.226 / 0.237), f_hi 653 / 998 / 422 Hz (unchanged), PM 79.6 / 76.9 / 81.4 deg, THD 0.042 / 2.40 (the accepted Decision-28 miss, was 2.63) / 0.057 %, supply gain 0.572 / 0.580 / 0.567, power-up error 0.24 / 0.10 / 0.62 mV, reset recovery unchanged. Junction convention likewise. Full tables: AFE/layout/BLOCKED.md.
- **Why more than the "few %" of Decision 48:** noise_d8^2 = b / Cin (b = 69.8 uV^2 pF at ff 85) so noise goes with 1 / sqrt(Cin): +15.5 % for 20 -> 15 pF (measured +15.8 % at ff 85). ESTIMATE: 2.0 uV at ff 85 needs Cin >= 17.1 pF (about 17.5 - 18 pF with layout parasitics); 2.05 uV needs 16.3 pF.
- **Files / state:** the 15 pF results are in AFE/layout/baseline_cin15/ (amp_*.json + logs); AFE/layout/baseline/ (20 pF) and AFE/amp/spice/afe_params.spice (CF1V = 200f) were NOT changed, so main stays consistent with the 20 pF layout until the user decides. Amp -> ADC at 15 pF: run done, log AFE/adc/sim/x2_s1_typ_cin15.log: end-to-end gain 59.994 dB, amp->ADC vs ADC alone +0.07 LSB mean (max 0.57), INL below 2.05 V 0.75 LSB PASS, whole range 2.78 LSB (top-of-range effect of Decision 43, not like-for-like with the earlier 2.14 LSB run; 20 pF not re-run).
- **Area (ESTIMATE, `mk_amp_ch.py` block sizes, no layout run):** the Cin block shrinks 164.7 x 167.3 -> 145.7 x 148.3 um (pieces 61.15 um = 7.4995 pF, Cf1 8.45 um = 150.1 fF); the committed packing would give about 218.75 x 290 um (+1.8 % over 285); at 17.5 pF about 300 um (+5 %).
- **Decision needed (BLOCKED.md):** (1) keep 15 pF and accept ff 85 noise 2.14 uV, (2) Cin about 17.5 pF (CF1V = 175f) with a second re-pack and up to 10 um from adc_h, (3) keep 20 pF and N = 4 (ladder A-6). R3 and R5 are not blocked. No numbered Decision written.

## Open questions
- (F1, DECIDED by Decision 46a: summing nodes on the top plate) Plate order of the input MIM capacitors (Cin1 / Cin2 of stage 1, Cin of stage 2): the netlists have the summing nodes on the BOTTOM plates and LVS does not swap MIM terminals. Decide before L2a's LVS; `mk_lvs_netlists.py --cin-top sum` puts them on top ("F1 findings", attention 1).
- (F1) After layout the comparator's preamp capacitors are 54.5 fF MIM units, not 40 fF: code offset about +1.5 / +1.9 LSB (typ / ff 85), and the offset is sensitive to junction capacitance by several LSB: the offsets of Decision 43e are pre-layout numbers, to be restated after L1b.
- (F1) Area: 0.874 mm2 at x1.30, 0.997 mm2 (998 x 998 um) at the pessimistic x1.50 against the 1000 x 1000 um outline given to the organizer.
- (F1) For L3a / L1d: strap-resistor device (rm3 in the reference), decap unit, where the 15 pad-control ties live (0-ohm resistors in the LVS top, or tie cells in afe_dig), the afe_dig port order (`--dig-netlist`), the TGATE extracted view without power pins.
- (Decision 44k, unchanged) Organizer: macro name / DEF, slot and pad positions, own VDD / VSS pair and double bonding, native-Vt nfet_06v0_nvt, 1k poly only, bond inductance.
- (I2, ANSWERED by Decision 42: adopted) The I1 vhalf question is answered by the sampled floating reference (Cref 7 pF + TG, vhalf decap 1 pF): code error <= 0.47 LSB beyond a fixed offset at typ / ss 125 / ff -40 (I2 findings; the offset itself was corrected by Decision 43e). The I1 text below is superseded:
- (I1, ANSWERED by Decision 42) vhalf misses the 0.1 LSB targets by 20-100x at any affordable C (a: 1.2-5 LSB, b: 1.5-9.7 LSB at 20-40 pF); options in "I1 findings". Pick one before L2 (the cell area and the comparator sizing depend on it).
- (I0, ANSWERED by Decision 41; REC pads later dropped by Decision 45) Five items need a decision before L2/L3: REF input of afe_chc (mismatch 1: pad or tie to vcm), source of the ADC VDD/2 net (2), word-1 config readback (5), DOUT_OE policy and the pad-control names (6), RSTN held low at power-up (9). The rest of the I0 list is information for L2/L3.
- (A4c, ANSWERED by Decisions 38a / 44c: RST_AMP config bit, host sequence with a >= 5 s wait and a mid-scale check) POWER-UP LATCH: without a reset stage 1 latches at a rail after the VDD ramp (not within 10 mV after 40 s at typ 27 / ff 85 / ss -40; A4b recovered in 10-17 s) and the 2-7 ms one-shot does not clear it (needs >= 30 ms, 100 ms for margin; the bias at ss -40 C takes ~0.6 s). A longer power-up reset is not implemented (options: re-trigger the record start about 10 times, a second slower timer, a digital counter, a larger C_T).
- (A4c, ACCEPTED by Decision 38b) 100 mV electrode offset: output within 1 mV only after 7.3-9.0 s (target 100 ms not met); the MIM r_leak DC path (v1 static -9.9 mV per 100 mV) sets it, not the reset. 10 mV: 3.4-4.7 s, 1 mV: 0.13-0.27 s.
- (A4c) The park level vcm_in (1.6484 V) differs from the electrode DC level by an arbitrary amount: the amplifier sees that difference as an offset step at every unpark (1.6 mV in the testbench), which the reset pulse handles.
- (A4c) Not done: park-injection result at ss -40, all-9-PVT tables of the reset, TGATE + real one-shot in one netlist (aborts), xschem for the changed cells, the replica / mirror mismatch (I_REF spread from device mismatch), an r_leak = 0 counterfactual, area/layout of C_T (~2,000 um2 per channel) and C_VRS (~2,500 um2 once; ESTIMATES).
- (A4b -> ANSWERED by A4c / Decision 36: the gate-switched reset keeps Cf in the loop, PM 72-76 deg, no ringing; open parts: power-up latch, 100 mV tail, below) Fast-settle as designed (a transmission gate across the feedback elements) makes OTA1 a unity-gain follower, which oscillates after ~1.5 us and leaves stage 1 latched at a rail on release. Options (not implemented): a pulse < 300 ns (works for the pulse alone, probably too short to charge Cin to a 10-100 mV offset); extra compensation
  switched in with the pulse; a gate-switched pseudo-resistor reset (R >~ 20 MOhm keeps the loop stable); or accept recovery times of tens of seconds to minutes. Needs a decision.
- (A4b, A4c: with the park the open-switch state is benign and a reset pulse leaves the railed state; whether silicon latches is still unknown) The bistable railed state of stage 1 (a DC state held by fA leakage) can be entered by any DC disturbance; with the record-path TGATE attached it is the DC operating point at ff 85 C / ss -40 C in the simulator. Does silicon behave the same? The TGATE-attached recovery / pad-leakage transients could not be simulated reliably.
- (A4b, A4c: with the park ON leaks of 1 and 10 pA and 10 pF pad capacitance change nothing at typ 27 C; without the park 1 pA rails stage 1. MOOT for the pads since Decision 45: there are no REC pads any more; the E pad leakage (about 200 pA, organizer README) acts through the routing TGATE only in record mode) Pad leakage above ~10 fA on the floating REC node rails the amplifier (hand ESTIMATE); the ESD / pad leakage at REC[7:0] (Decision 35) is unknown and must stay below this or the routing switch must never float REC for long.
- (A4b) Decisions 24 and 28 are provisional (Decision 34); the follower-sink sweep (KSF 24: +0.41 mW at N = 8) is only needed if the 1.65 V reset and a short acquisition window are kept.
- (A4b) DBS stimulation artifacts of several volts: out of scope here (user, 2026-11-13); recovery from them is the open item.
- (D0, ANSWERED by Decision 23) No out-of-band interference requirement exists; the 13-20 dB interferer attenuation at 3.7 kHz (11.7-18.9 dB with the A4b / A4c amplifier, AFE/review/AUDIT.md 4.7) is a documented risk. Reopen only if a requirement appears (cure: analog second pole, PLAN.md 5.2).
- (Decision 27; numbers CORRECTED and the question ANSWERED pre-layout by Decisions 37, 40e, 43f, 44d: 13.6 pC per MSB trial, staggered comparator clocks, three straps with 0.225 nF, 8-ADC run PASS; pad L / R still ASSUMED) The ADC's ~27 pC MSB-trial charge draw from VDD (VREF = VDD: 8.2 pF x 3.3 V; on-chip decoupling would need ~336 nF for 0.1 LSB) is a board decoupling and bond-wire inductance risk. Who owns the board decoupling and package, and what supply-pin L/C is realistic? D2/D4 report the supply droop at the decision instants.
- (Decisions 25-26; the size part is ANSWERED by Decision 39: 25 um2 minimum, 5 x 5 um units) Minimum legal MIM unit size/spacing in the GF180 design rules is unknown (D2 must find it); the MIM matching constant is an assumption (0.5 %*um) until a model or silicon data exists.
- (D0) Is the external MCU 3.3 V (assumed)? Which supply pins and board decoupling will the 3.3 V ADC/amp rail have (VREF = VDD makes the ADC code depend on it)?
- (A4a status) The fast-settle transmission gates exist in the netlists and their DC/AC behaviour is verified (A4a findings); settling time versus pulse width, charge injection and residual offset are A4b.
- (A2) After each TREAT->REC switch the amp needs ~5 x tau_HPF (about 4-7 s at tau 0.8-1.5 s) to settle. A4 should evaluate a fast-settle switch (shorting the pseudo-resistors for a few ms, driven by REC_EN/READY): charge injection, residual offset, and the settling time versus switch duration.
- (A2) Is the PDK-model junction floor (4-6 TOhm, T-independent) trustworthy? And a vt generator (+0.2 V gate shift) is needed in A3; PDK pfet noise in the pseudo-R is below 4kT/R: confirm the model with the instructor/PDK docs if the pseudo-R noise is to be claimed.
- (ANSWERED by Decision 34: one SAR ADC per channel, N = 8, no mux) One muxed ADC vs 16 ADCs: OPEN, decided after D0 (Decision 19). (Sample rate, ownership and
  reference are settled: Decisions 15–17.)
- (PARTLY ANSWERED: single 3.3 V supply, Decision 30; park switch and reset, Decision 36; signals must stay inside 0..VDD, AUDIT i4) 3.3 V amp input vs the 5 V TGATE REC node: input protection, charge injection when
  the switch toggles, IPG step-up excursions.
- (ANSWERED by Decisions 22 / 23: no oversampling, first-order roll-off accepted as a documented risk) Anti-aliasing order vs ADC sample rate.
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
| 2026-11-12 | A4a stage 2 + real bias | Claude Sonnet 5.5 / default | | Stage 2 (gain 10, f_hi 359-867 Hz) + follower buffer + real bias/ladders + fixed-gate vt + transmission-gate fast-settle + real diffusion; gain 59.9-60.0 dB, f_lo 0.15-0.28 Hz, noise 1.54-1.80 uV (fnoicor=0), fnoicor=1 4.2-5.2 uV (risk), 47-119 uA; xschem == hand netlists; see "A4a findings"; AFE/amp/sim/a4a_summary.txt, sim/a4a_*.log |
| 2026-11-12 | D0 ADC plan | Claude Sonnet 5.5 / default | | Plan only, no circuit files: 1 SAR + 16:1 mux (Decision 19 outcome), binary 4096 x 4 fF DAC, SPI mode 0 with SCLK-clocked conversion; aliasing quantified from the A4a spectra (noise aliasing <= 0.14 uV; interferer 13-20 dB at 3.7 kHz, +6 dB/octave of oversampling); A4b ADC input model C_s 17 pF / 1 kOhm / T_ACQ 12.4 us; see "D0 findings"; AFE/adc/PLAN.md, AFE/adc/sim/d0_estimates.log |
| 2026-11-13 | A4b transients | Claude Sonnet 5.5 / default | | Found and fixed: output clipped at 1.94 V (native-Vt follower), stage-2 pseudo-R rectification (VTT2 0.9 V), supply gain 1.02 -> 0.57 V/V (VCM_IN = 1.65 V); fast-settle release is an OTA1 unity-gain oscillation (works only for < 300 ns pulses), real one-shot designed; TGATE Ron at 3.3 V 8-34 kOhm (max for 2 uV: 133 kOhm); recovery 8-13 s (1 mV), latches at 10 mV, 500 s at 100 mV; ADC kick -2.25 LSB after a 1.65 V reset (KSF 24 passes), 245 us no-reset case <= 0.26 LSB; power-up OK; TGATE-attached transients unreliable (bistable stage 1); see "A4b findings"; sim/a4b_*.log, sim/a4b_corner_table.txt |
| 2026-11-13 | A4c fast-settle redesign + REC park | Claude Sonnet 5.5 / default | | Gate-switched pseudo-R reset (replica-set R_reset 17-39 MOhm over 9 PVT, PM 72-76 deg, no ringing at 6 PVT) + REC park + current-starved one-shot (3.6 / 1.9 / 6.9 ms): 3 ms+ clears 1/10/100 mV steps, release step <= 0.14 mV, 1 mV step settles in 0.13-0.27 s (A4b 10-13 s); 100 mV in 7-9 s (target 0.1 s NOT met: MIM leak); park keeps stage 1 out of the rail with 1-10 pA leakage; power-up latch NOT cured (needs >= 30 ms reset); tables unchanged; see "A4c findings"; sim/a4c_*.log |
| 2026-11-13 | L0 layout plan | Claude Sonnet 5.5 / default | | Plan only: MIM min 25 um2 (1.2 um unit illegal, Decision 25 answered), Cin >= 2 pieces, m4m5 MIM LVS name, tool flow, star-routed supplies, schedule to 2026-11-25; DAC style split 6+6 approved; see Decision 39 and AFE/layout/PLAN.md | |
| 2026-11-14 | I0 integration (RST_AMP, top netlist, digital sim) | Claude Sonnet 5.5 / medium | | RST_AMP bit 9 of word 0 + rst_amp_o level in adc8_top; trigger = sw_rec, park = sw_rec_b / sw_rec; AFE/top/dbs_afe_top.v + stubs; whole-digital sim PASS (0 errors, REC/IPG == dbs); D3 regression PASS (hardened netlist stale); channel pin list in layout/PLAN.md section 9; 12 mismatches listed, 5 need a decision; see "I0 findings"; AFE/top/sim/i0_top.log | 
| 2026-11-14 | I1 (Decision 41: REF pad, vhalf, word-1 readback, RSTN pull-down) | Claude Sonnet 5.5 / medium | | REF pad (32 pads) wired in top/info.yaml/TAPEOUT/PLAN; word-1 config readback in RTL + tb (D3 regression PASS, top sim PASS); D3 re-synthesised: +527 um2 (+1.9 %), setup/hold met at 5 corners; vhalf (2 x 250k poly + 20 pF MIM): static 5.8-7.4 uA OK, but decision-time error 1.2-5.2 LSB and kickback 1.5-9.7 LSB (target 0.1) at 20-40 pF, NOT met; see "I1 findings"; sim/i1_vhalf.log, AFE/top/sim/i0_top.log | 
| 2026-11-14 | I2 (sampled floating reference, true-SAR replay) | Claude Sonnet 5.5 / medium | | Cref 7 pF + TG (tg_on/samb, no RTL change) on cmp_p.inp, vhalf decap 20 -> 1 pF: threshold error <= 0.47 LSB at typ/ss125/ff-40 beyond a fixed -7.6..-12.4 LSB offset (3.5 pF: 0.65 at ff FAILS; I1 vhalf alone: up to 2.8 LSB, 2.3-5.3 LSB spread); Cref settles to 0.0 uV in T_ACQ; ~4,200 um2 per ADC vs 10,500; netlists updated; see "I2 findings"; sim/i2_replay.log, i2_summary.txt, i2_twoframe.log |
| 2026-11-19 | X2 transistor-level amp -> ADC + 8-ADC run (pre-layout) | Claude Fable 5.2 / max | | Amp->ADC works at transistor level (adds <= 0.08 LSB); D5 abort = abstol 1e-15 (fixed with 1e-12); ENOB FS with amp noise 8.96 / 7.23 / 9.15; 8-ADC supply PASS (<= 0.25 LSB ff -40); crosstalk 0.022 LSB; INL FAIL at ff 85 / top of range, code-dependent threshold steps at 1536 / 2048; Decision 43. See AFE/adc/NOTES.md "X2 findings" |
| 2026-11-20 | AUDIT pre-layout | Claude Fable 5.2 / max | | Layout GO WITH CONDITIONS, tapeout 11-25 at risk. BLOCKERS: B1 ppolyf_u_3k (6 bias-ladder and 16 vhalf resistors) does not exist in gf180mcuD (only the 1 kOhm/sq HRES poly: LVS / netgen / Magic decks, organizer table); B2 the bidirectional pad needs top ports DOUT_OUT / DOUT_IN (organizer template); B3 organizer macro name / DEF / slot / pad allocation still missing. MAJOR: bias start-up 3.6 s at ss -40 C with 8 channels (README says 1 s); supply straps and decap are in no netlist (2 vs 3 straps); ideal elements in the LVS-reference netlists (the 40 fF comparator capacitors are below the MIM minimum); DAC settling misses by 0.65 LSB when 3.3 V devices are slow and std cells fast; RSTN changed during a frame commits a wrong config; digital macro not sign-off clean (CTS, no KLayout DRC); native-Vt follower device unconfirmed. Area 0.86 mm2 (70 % of the ASSUMED 1110 um slot), power 2.08 mW typ, timing PASS at 5 matched corners at 2 and 3 MHz (RTL + gate level, 72 runs), in-band noise 1.71 / 1.89 / 1.59 uV. Report AFE/review/AUDIT.md (10 proposals P-A1..P-A10), logs AFE/review/sim, scripts AFE/review/scripts |
| 2026-11-20 | F1 audit fixes (Decision 44) + 24 pads (Decision 45) | Claude Fable 5.2 / max | | No circuit resized. (1) ppolyf_u_3k -> ppolyf_u_1k, 3x the squares (bias_genc, bias_gen, vhalf): taps move <= 0.49 mV, supply / channel / master currents within 0.65 %, ladder and vhalf branch currents +1.6 / -8.5 / +11.2 % (typ / ff 85 / ss -40: the 1k poly's own corner and temperature behaviour, as the audit predicted), ADC codes identical (12 inputs typ, 8 at ff 85). (2) top ports DOUT_OUT / DOUT_IN, REC ports and pads removed (rec internal), 24 pads in info.yaml / TAPEOUT.md / PLAN section 9; pad-control names equal the organizer template. (3) supply pins vdd / vdd_cmp / vdd_dac on dac_sw, cmp_p, afe_ch; strap resistor + MOS decap as cells of the top and devices of the LVS top; X2 scripts updated: S1 ADC-alone codes identical, S4 typ reproduced. (4) layout/scripts/mk_lvs_netlists.py -> layout/lvs/ (afe_chc + fs_oneshot_c + amp_ch, adc_ch, bias_genc, dbs_afe_top with afe_dig as a black box); the generated amplifier / bias reference simulates identically to the design netlists, the ADC cells convert, netgen reads all files, xcheck finds every cell equal to the simulation netlist device by device. (5) adc/README.md, TAPEOUT.md, PLAN.md, NOTES Environment cleaned. (6) D3 RTL PASS, top sim PASS, 72 audit testbench runs byte-identical (only X1.contention, X5.word0, X5.after33d, T11.crowbar and the accepted MIXED-corner T2.settle fail), xcheck rows B1 B2 M2 M3 m7 OK, 3 MISMATCH left (lvs_config paths: L4; afe_dig: L1d). NEW: MIM plate order of Cin is on the wrong plate for the summing nodes in the netlists and LVS will not swap it (decide before L2a's LVS); Cxa as a MIM unit moves the code offset +1.5 / +1.9 LSB; area 0.874 mm2 (0.997 pessimistic). See "F1 findings"; review/sim/f1_bias_op.log, f1_xcheck.log, f1_area.log, f1_power_total.log; adc/sim/f1_x2_compare.log, f1_x2_inl_step.log, f1_x2_s4_summary.log; layout/lvs/mk_lvs_netlists.log, check_lvs_netlists.log |
| 2026-11-20 | LP layout preparation (+ LP-finish) | Claude Fable 5.2 / max; finish Claude Opus 5.5 / high | | One-person layout kit: check_env.sh 32 PASS (layout/sim/check_env_ref.log); SPEC.md + floorplan.json (18 PASS, amp_ch slot +12 %); flow.py DRC / LVS / PEX with MIM top-plate correction; 17 golden testbenches + compare.py, 25 baselines, selftest all PASS; ACCEPT.md IN FORCE (user change of plan: no approval gate, reports + REVIEW.md); afe_dig trial hardened, all L1d limits PASS (dig/LP_STEP5.md); native-Vt fallback rvt pre-approved (amp/sim/lp_rvt_summary.md); info.yaml / lvs_config / README / export answers (check_submission --pre PASS); layout_run.md + RUNBOOK.md + gate.py + check_prompts.py (PASS). MAJOR: pseudo-R junction area -> f_lo < 1 mHz and offset railing in the junction convention (ACCEPT.md section 2). See "LP findings" |
| 2026-11-20 | L2a amplifier layout amp_ch (DRC + LVS) | Claude Sonnet 5.5 / high | | amp_ch.gds: DRC variant D 0 violations, LVS "Circuits match uniquely." against AFE/layout/lvs/afe_chc.spice (46 devices, 14 pins, nothing regenerated); MIM terminal 1 = top plate (Step 1 test cell, flowtest); native-Vt follower passes DRC + LVS (organizer still silent, ladder N); Cin 2 x 2 checkerboard of four 70.65 um pieces, summing nodes on the top plates, nothing under the plates; input pair ABBA + poly dummies, rings, own wells for the 6 pseudo-resistors. NOT in the slot: 219.25 x 385.25 um = 84,466 um2 vs 57,860 (+46 %), blocks sum 62,361 vs F1 51,626: ladder A next (8 channels 0.68 mm2 of the 1.0 mm2 outline for amp_ch alone). Flow notes AFE/layout/FLOW.md; logs AFE/layout/amp/ (flow/, flowtest/, pex_feasibility/, check_amp.json, amp_ch.build.json) |
| 2026-11-20 | L1a ADC layout adc_ch (DRC + LVS) | Claude Sonnet 5.5 / high | | adc_ch.gds: DRC variant D 0 violations, LVS "Circuits match uniquely." against AFE/layout/lvs/adc_ch.spice (34 pins, reference not regenerated); Cref keep-out PASS; split 6+6 DAC (127 units + bridge, point-symmetric pairs, site map in AFE/layout/adc/dac_sites.log), 13 drivers + 13 TGs, mirror-image comparator, interdigitated vhalf serpentine, Cref one 59.07 um plate. NOT in the slot: 265.85 x 126.25 um = 33,564 um2 vs 22,880 (+47 %, F1 estimate 14,911): the 6.8 um DAC pitch of SPEC.md is illegal (MIMTM.1: 7.4 um), driver rows and comparator are 9 x / 5.5 x their F1 estimates; with amp_ch (L2a) 8 channels need 1.049 mm2 of the 1.000 mm2 outline (ladder A open: floorplan decision). Notes AFE/layout/adc/FLOW_ADC.md; logs AFE/layout/adc/ (adc_ch.build.json, keepout.log, dac_sites.log), AFE/layout/sim/flow/adc_ch.*.json; report AFE/layout/reports/L1a.md |
| 2026-11-20 | L1d digital macro afe_dig, final hardening | Claude Sonnet 5.5 / high | | Re-run of the LP recipe reproduces the trial (deterministic): die 819.84 x 109.76 um, 43.0 % utilisation, STA met at 5 corners (setup ws >= 91.7 ns, hold ws >= 0.229 ns), 0 slew / cap violations, route / Magic DRC 0, LVS 0, KLayout DRC 0 on AFE/dig/final/afe_dig.gds; tap limits (a) 22.14 / (c) 20.59 (flop pins 22.39) / slack 13.75 ns PASS; switch-pair skew <= 0.78 ns; 33.7 pC per SCLK cycle at tt (38.4 pC ff -40); gate-level tb only accepted failures; EQUIV PASS; mk_lvs_netlists --decap-n 74,64 --dig-netlist AFE/dig/final/afe_dig.pnl.v, check_lvs_netlists A / B / C PASS; floorplan.py check 18 PASS 0 FAIL; no ladder entry. Logs AFE/dig/reports/, AFE/dig/sim/; report AFE/layout/reports/L1d.md |
| 2026-11-20 | R2 tightened floorplan (Decision 48) | Claude Sonnet 5.5 | | floorplan.py build ring 26 / bias_corr 12 / strap_corr 25 / dig_h 80 / ch_pitch 237 / adc_h 104 (+ west pins 3.5 um pitch from y = 3 to fix check 3e): channel slot 237 x 397 um, amp_ch <= 222 x 285, adc_ch <= 222 x 104, bias_genc <= 108 x 110, afe_dig 820 x 80; floorplan.py check 16 PASS 0 FAIL; SPEC.md updated. As-built cells and the L1d macro still fail their slot checks until R3 / R4 / R5. Report AFE/layout/reports/R2.md |
| 2026-11-20 | R5 adc_ch re-pack (REVIEW item R5, Decision 48) | Claude Sonnet 5.5 | | adc_ch 219.50 x 103.67 um = 22,755 um2 (was 265.85 x 126.25 = 33,564, -32 %) in the 222 x 104 um slot; DRC variant D 0 violations, LVS match against AFE/layout/lvs/adc_ch.spice (not regenerated), Cref keep-out PASS, floorplan.py check 17 PASS, gate L1a PASS; no circuit change. Levers: no dummy bars around the DAC, driver rings 1.0 um and tile pitch 3 / 4 um, comparator 106 x 36.6 under Cref, vhalf folded (8 rows of 62.5 um) in the keep-out band, Cref pad on its west side, `vdd` pin on the south edge; rst_sw 5.0 um / tg_on 14.8 um from the t trunk at their devices (26 of 28 control nets >= 21 um). The cell is full: no height to give to R3 / R4. Notes AFE/layout/adc/FLOW_ADC.md section 6; report AFE/layout/reports/L1a.md |
| 2026-11-20 | R4 Cin 15 pF simulations (Decision 48), STOPPED | Claude Sonnet 5.5 | | CF1V = 150f: amp testbenches at 3 corners x 2 conventions: all PASS except Decision-8 noise 1.890 / 2.139 / 1.732 uV (limit 2.0: FAIL at ff 85, R-3 allows 2.05); gain 60.05 dB, f_lo <= 0.288 Hz, PM >= 76.9 deg. BLOCKED.md written, no layout; results in AFE/layout/baseline_cin15/, baselines and afe_params unchanged. Report AFE/layout/reports/L2a.md section 9 |
