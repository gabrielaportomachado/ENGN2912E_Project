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
