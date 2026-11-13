# ADC notes (AFE/adc/) - ADC sessions write findings HERE, not in AFE/NOTES.md

Created 2026-11-12 so ADC sessions (D1-D6) can run alongside amplifier sessions without both editing AFE/NOTES.md.
- Read AFE/NOTES.md (shared decisions 1-28, amplifier results) and AFE/TAPEOUT.md (decisions 29-32: N = 8, single 3.3 V DVDD, 2235 um core planning frame, serial config with DIN) first.
- Write ONLY to AFE/adc/ (including this file). Do not edit AFE/NOTES.md; if a shared decision or an amplifier hand-back is needed, put it under "Hand-back to the amplifier / NOTES.md" below
  and the user or monitoring session merges it.
- Same rules as AFE/NOTES.md "Rules for every session" (numbers from saved logs, stop at the end of each phase, rule 10 for choices).
- ADC changes from TAPEOUT.md to apply in D1-D6: 8:1 input mux (not 16:1; frame ID 4 bits, 3 used); aggregate 32 kS/s, frame period 31.25 us, T_ACQ = 31.25 us - 16/f_SCLK;
  DIN pin and a CS-framed config write (MODE + EN[7:0], 9-bit shift register in a new wrapper); single 3.3 V DVDD, so no 5 V -> 3.3 V level crossings.

## Results log (ADC)
| Date | Phase | Model / effort | Cost (USD) | Result (with path to log) |
|------|-------|----------------|------------|---------------------------|
| 2026-11-12 | D0 ADC plan | Claude Sonnet 5.5 / default | | See AFE/NOTES.md "D0 findings"; AFE/adc/PLAN.md, AFE/adc/sim/d0_estimates.log |

## Hand-back to the amplifier / NOTES.md
(empty)
