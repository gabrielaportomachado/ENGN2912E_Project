# Amplifier phase prompts (AFE/amp/)

Use one phase per Claude Code session. Start each session with:
"Read AFE/NOTES.md, then do phase A<n> from AFE/prompts/amp.md."
After the agent stops, review the result, then /clear before the next phase.

---

## A0: Plan (no simulation)
Read AFE/NOTES.md and skim the existing ROW/ and TGATE/ files (read-only). Propose the
folder layout under AFE/amp/ (spice/, xschem/, tb/, sim/, figs/), the testbench list,
and the exact .meas for every target in NOTES.md. List your assumptions and anything you
think is wrong in the architecture hypotheses. Write no circuit files. Stop.

## A1: Device characterization
Write AFE/amp/tb/char_*.spice to characterize pfet_03v3 and nfet_03v3 at the typical
corner, 27 °C:
- gm/Id vs Id/(W/L) (Vds ≈ 0.5 V), for a few L (e.g. 0.5u, 1u, 2u, 4u);
- input-referred noise density vs frequency (0.1 Hz–10 kHz) for a few W·L at a few Id,
  and the integrated input-referred noise over 0.5–300 Hz; repeat one point with fnoicor=1;
- valid input common-mode range of a PMOS differential pair with tail current source
  on 3.3 V.
Save logs/CSV in AFE/amp/sim/ and plots in AFE/amp/figs/. Recommend the input pair
W, L and Id needed to reach ≤ ~1.8 uV rms OTA noise, with the area cost. Update
NOTES.md. Stop.

## A2: Pseudo-resistor
Characterize a back-to-back PMOS pseudo-resistor (and one tunable variant):
I–V for ±100 mV, effective small-signal resistance, across typical/ff/ss and
-40/27/85 °C. Report the HPF corner it gives with candidate Cf values, including MIM
r_leak. Update NOTES.md. Stop.

## A3: Stage-1 OTA and closed loop
Design the stage-1 OTA (spice subckt + xschem .sch/.sym). Testbenches: .op (all devices
in their intended region), open-loop .ac (gain, GBW, phase margin, with the real
closed-loop load), closed loop with the Randles source: .ac gain and corners, .noise
integrated 0.5–300 Hz input-referred. Corners typical/ff/ss. Update NOTES.md. Stop.

## A4: Stage 2 and full one-channel testbench
Add stage 2 (gain ≈ 10, referenced to VOUT_CM, LPF ≈ 300 Hz) and a parameterized ADC
load (R_ADC, C_ADC; default values from the ADS7953 datasheet if verified, otherwise
labelled placeholders). One-channel top-level AFE/amp/xschem/afe_ch.sch and testbench
AFE/amp/tb/tb_afe_1ch with parameters VD, F_SIG, VOS_REC, VOS_REF, VCM_AC, ART_AMP,
ART_DUR, ART_T0, VOUT_CM, USE_TG (series TGATE.spice, read-only include).
Measure: midband gain, -3 dB corners, integrated input-referred noise, output swing
and THD vs amplitude (find the 1% THD point), slew at full scale, power-up settling,
recovery after an offset step and after an artifact pulse (report a sweep, no pass
claims for unspecified values), supply current. Corners typical/ff/ss, -40/27/85 °C.
Plots in AFE/amp/figs/. Update NOTES.md. Stop.

## A5: Report (SHORT, low effort)
Write AFE/amp/README.md, at most one page: how to run, a results table (target, measured, corner, pass/fail, log path), what is IDEAL, open items. Do not re-run anything. Stop.

## A4c: Fast-settle redesign (gate-switched pseudo-R reset) + REC park switch (Decision 36)
Context (NOTES.md "A4b findings", Decision 36): closing the fast-settle TG shorts Cf and makes OTA1 an unstable unity-gain follower (oscillation, stage 1 rails; only <= 300 ns pulses are clean). Recovery without fast-settle
is far too slow (1 mV: 10-13 s, 10 mV latches, 100 mV: 265-500 s; power-up ~20 s). The REC node floats when the routing switch is open, so ~10 fA of leakage rails the amplifier, and with the real TGATE attached stage 1
can sit in a bistable railed DC state. Do these, in order, at typical 27 C, ff 85 C and ss -40 C only (all 9 only if a result is within 10 % of its limit):
1. (A) Replace the Cf-shorting fast-settle with a RESET THAT KEEPS Cf IN THE LOOP: switch the gate bias of the stage-1 (and, if needed, stage-2) pseudo-resistors to a low-resistance level for the pulse, using an existing bias tap plus
   one small switch if possible (rule 10: least hardware). Sweep the reset gate level so R_reset spans ~1 MOhm-1 GOhm; for each report loop phase margin in the reset state (Tian, keep the 100 Ohm noiseless loop-break from A4b),
   recovery time to within 1 mV (1.2 LSB) after 1, 10 and 100 mV REC offset steps, pulse width needed (try 10 us, 100 us, 1 ms, 10 ms), and the release step (charge injection of the gate switch) and settling after release.
   Pick the setting by rule 10 and say why. Target: the output within 1 mV after a 100 mV offset step in <= 100 ms (state what you achieve if not met), no oscillation, release step <= 1 mV at the output.
2. (B) Add a REC PARK switch: a small transmission gate per channel tying the REC node (after the routing switch, before Cin) to VCM_IN (1.65 V) while the routing switch is open, driven by the existing sw_rec_b control (no new control
   signal; say if it needs one). Re-run the TGATE-attached scenario that was INVALID in A4b: treat (routing switch open, park ON, REC leak I_LEAK 0/1/10 pA and C_PAD 0/2/10 pF as ASSUMPTIONS) -> record (park off, routing switch closes,
   reset pulse from item 1). Report: does stage 1 stay out of the bistable railed state; charge injection at park release and routing-switch close; recovery time; added noise (park switch off-state, must keep total <= 2 uV, typical flicker).
3. Power-up with the new reset: VDD ramp 0 -> 3.3 V, reset asserted from the VDD-derived control; time to within 10 mV and 1 mV of 1.65 V.
4. Fast-settle control: keep the real one-shot circuit idea from A4b but re-size its widths to the pulse found in item 1; verify with the real gate in the channel netlist if the transient aborts allow it, otherwise PWL playback and say so.
5. Re-run the key A4b tables at the three corners that the changes can affect: ac gain/f_lo/f_hi, noise, THD at +-0.5 mV, loop PM, supply current. Report any change versus a4b_corner_table.txt.
Rules: new logs use tag a4c; do not modify a4b results; results from saved logs only; cap yourself: if a step fails the same way twice, stop and report instead of trying a third fix. Update xschem only for cells whose structure
changed and only if cheap (else label the hand netlist as the source of truth). Write findings under "A4c findings" in NOTES.md, update the Results log, keep Decisions 34-36 untouched, and finish with "Choices I made" and "Needs your attention". Stop.
