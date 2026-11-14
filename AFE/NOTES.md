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
38. After A4c (2026-11-13): user APPROVED the power-up fix (RST_AMP bit); the 100 mV-tail acceptance is my recommendation, not yet explicitly approved. A4c design accepted as built (replica-biased gate-switched pseudo-R reset 0.22u/0.5u, REC park on the routing C/CBAR nets, current-starved one-shot 1.9-6.9 ms, release step <= 0.14 mV).
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

## Open questions
- (A4c) POWER-UP LATCH: without a reset stage 1 latches at a rail after the VDD ramp (not within 10 mV after 40 s at typ 27 / ff 85 / ss -40; A4b recovered in 10-17 s) and the 2-7 ms one-shot does not clear it (needs >= 30 ms, 100 ms for margin; the bias at ss -40 C takes ~0.6 s). A longer power-up reset is not implemented (options: re-trigger the record start about 10 times, a second slower timer, a digital counter, a larger C_T).
- (A4c) 100 mV electrode offset: output within 1 mV only after 7.3-9.0 s (target 100 ms not met); the MIM r_leak DC path (v1 static -9.9 mV per 100 mV) sets it, not the reset. 10 mV: 3.4-4.7 s, 1 mV: 0.13-0.27 s.
- (A4c) The park level vcm_in (1.6484 V) differs from the electrode DC level by an arbitrary amount: the amplifier sees that difference as an offset step at every unpark (1.6 mV in the testbench), which the reset pulse handles.
- (A4c) Not done: park-injection result at ss -40, all-9-PVT tables of the reset, TGATE + real one-shot in one netlist (aborts), xschem for the changed cells, the replica / mirror mismatch (I_REF spread from device mismatch), an r_leak = 0 counterfactual, area/layout of C_T (~2,000 um2 per channel) and C_VRS (~2,500 um2 once; ESTIMATES).
- (A4b -> ANSWERED by A4c / Decision 36: the gate-switched reset keeps Cf in the loop, PM 72-76 deg, no ringing; open parts: power-up latch, 100 mV tail, below) Fast-settle as designed (a transmission gate across the feedback elements) makes OTA1 a unity-gain follower, which oscillates after ~1.5 us and leaves stage 1 latched at a rail on release. Options (not implemented): a pulse < 300 ns (works for the pulse alone, probably too short to charge Cin to a 10-100 mV offset); extra compensation
  switched in with the pulse; a gate-switched pseudo-resistor reset (R >~ 20 MOhm keeps the loop stable); or accept recovery times of tens of seconds to minutes. Needs a decision.
- (A4b, A4c: with the park the open-switch state is benign and a reset pulse leaves the railed state; whether silicon latches is still unknown) The bistable railed state of stage 1 (a DC state held by fA leakage) can be entered by any DC disturbance; with the record-path TGATE attached it is the DC operating point at ff 85 C / ss -40 C in the simulator. Does silicon behave the same? The TGATE-attached recovery / pad-leakage transients could not be simulated reliably.
- (A4b, A4c: with the park ON leaks of 1 and 10 pA and 10 pF pad capacitance change nothing at typ 27 C; without the park 1 pA rails stage 1) Pad leakage above ~10 fA on the floating REC node rails the amplifier (hand ESTIMATE); the ESD / pad leakage at REC[7:0] (Decision 35) is unknown and must stay below this or the routing switch must never float REC for long.
- (A4b) Decisions 24 and 28 are provisional (Decision 34); the follower-sink sweep (KSF 24: +0.41 mW at N = 8) is only needed if the 1.65 V reset and a short acquisition window are kept.
- (A4b) DBS stimulation artifacts of several volts: out of scope here (user, 2026-11-13); recovery from them is the open item.
- (D0, ANSWERED by Decision 23) No out-of-band interference requirement exists; the 13-20 dB interferer attenuation at 3.7 kHz is a documented risk. Reopen only if a requirement appears (cure: analog second pole, PLAN.md 5.2).
- (Decision 27) The ADC's ~27 pC MSB-trial charge draw from VDD (VREF = VDD: 8.2 pF x 3.3 V; on-chip decoupling would need ~336 nF for 0.1 LSB) is a board decoupling and bond-wire inductance risk. Who owns the board decoupling and package, and what supply-pin L/C is realistic? D2/D4 report the supply droop at the decision instants.
- (Decisions 25-26) Minimum legal MIM unit size/spacing in the GF180 design rules is unknown (D2 must find it); the MIM matching constant is an assumption (0.5 %*um) until a model or silicon data exists.
- (D0) Is the external MCU 3.3 V (assumed)? Which supply pins and board decoupling will the 3.3 V ADC/amp rail have (VREF = VDD makes the ADC code depend on it)?
- (A4a status) The fast-settle transmission gates exist in the netlists and their DC/AC behaviour is verified (A4a findings); settling time versus pulse width, charge injection and residual offset are A4b.
- (A2) After each TREAT->REC switch the amp needs ~5 x tau_HPF (about 4-7 s at tau 0.8-1.5 s) to settle. A4 should evaluate a fast-settle switch (shorting the pseudo-resistors for a few ms, driven by REC_EN/READY): charge injection, residual offset, and the settling time versus switch duration.
- (A2) Is the PDK-model junction floor (4-6 TOhm, T-independent) trustworthy? And a vt generator (+0.2 V gate shift) is needed in A3; PDK pfet noise in the pseudo-R is below 4kT/R: confirm the model with the instructor/PDK docs if the pseudo-R noise is to be claimed.
- One muxed ADC vs 16 ADCs: OPEN, decided after D0 (Decision 19). (Sample rate, ownership and
  reference are settled: Decisions 15–17.)
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
| 2026-11-12 | A4a stage 2 + real bias | Claude Sonnet 5.5 / default | | Stage 2 (gain 10, f_hi 359-867 Hz) + follower buffer + real bias/ladders + fixed-gate vt + transmission-gate fast-settle + real diffusion; gain 59.9-60.0 dB, f_lo 0.15-0.28 Hz, noise 1.54-1.80 uV (fnoicor=0), fnoicor=1 4.2-5.2 uV (risk), 47-119 uA; xschem == hand netlists; see "A4a findings"; AFE/amp/sim/a4a_summary.txt, sim/a4a_*.log |
| 2026-11-12 | D0 ADC plan | Claude Sonnet 5.5 / default | | Plan only, no circuit files: 1 SAR + 16:1 mux (Decision 19 outcome), binary 4096 x 4 fF DAC, SPI mode 0 with SCLK-clocked conversion; aliasing quantified from the A4a spectra (noise aliasing <= 0.14 uV; interferer 13-20 dB at 3.7 kHz, +6 dB/octave of oversampling); A4b ADC input model C_s 17 pF / 1 kOhm / T_ACQ 12.4 us; see "D0 findings"; AFE/adc/PLAN.md, AFE/adc/sim/d0_estimates.log |
| 2026-11-13 | A4b transients | Claude Sonnet 5.5 / default | | Found and fixed: output clipped at 1.94 V (native-Vt follower), stage-2 pseudo-R rectification (VTT2 0.9 V), supply gain 1.02 -> 0.57 V/V (VCM_IN = 1.65 V); fast-settle release is an OTA1 unity-gain oscillation (works only for < 300 ns pulses), real one-shot designed; TGATE Ron at 3.3 V 8-34 kOhm (max for 2 uV: 133 kOhm); recovery 8-13 s (1 mV), latches at 10 mV, 500 s at 100 mV; ADC kick -2.25 LSB after a 1.65 V reset (KSF 24 passes), 245 us no-reset case <= 0.26 LSB; power-up OK; TGATE-attached transients unreliable (bistable stage 1); see "A4b findings"; sim/a4b_*.log, sim/a4b_corner_table.txt |
| 2026-11-13 | A4c fast-settle redesign + REC park | Claude Sonnet 5.5 / default | | Gate-switched pseudo-R reset (replica-set R_reset 17-39 MOhm over 9 PVT, PM 72-76 deg, no ringing at 6 PVT) + REC park + current-starved one-shot (3.6 / 1.9 / 6.9 ms): 3 ms+ clears 1/10/100 mV steps, release step <= 0.14 mV, 1 mV step settles in 0.13-0.27 s (A4b 10-13 s); 100 mV in 7-9 s (target 0.1 s NOT met: MIM leak); park keeps stage 1 out of the rail with 1-10 pA leakage; power-up latch NOT cured (needs >= 30 ms reset); tables unchanged; see "A4c findings"; sim/a4c_*.log |
| 2026-11-13 | L0 layout plan | Claude Sonnet 5.5 / default | | Plan only: MIM min 25 um2 (1.2 um unit illegal, Decision 25 answered), Cin >= 2 pieces, m4m5 MIM LVS name, tool flow, star-routed supplies, schedule to 2026-11-25; DAC style split 6+6 approved; see Decision 39 and AFE/layout/PLAN.md | |
