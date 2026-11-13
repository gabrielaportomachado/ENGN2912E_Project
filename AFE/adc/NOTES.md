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
| 2026-11-13 | D0b re-plan, one ADC per channel | Claude Sonnet 5.5 / default | | Plan only, all ESTIMATE: 8 staggered SARs, 160-clock / 10-word frame, config in word 0, no reset, supply risk (decap 0.16-0.47 mm2); see "D0b findings" below; AFE/adc/PLAN.md section D0b, sim/d0b_estimates.log |

## D0b findings (2026-11-13; hand estimates only, no circuit files; PLAN.md section D0b has the detail and the "Choices I made" table)
- ARCHITECTURE: N = 8 x (amplifier + 12-bit SAR), no mux, simultaneous sampling at CS falling, 4 kS/s per channel, one DOUT behind a digital serializer (the 8 SAR result registers chained into one 96-bit shift register, reused, +12 mux2 per ADC), config on DIN.
- FRAME: 160 SCLK = 10 x 16-bit words. SCLK 1-16 (word 0): DIN = {7 x 0, MODE, EN[7:0]}; SCLK 1-19: the 8 conversions, staggered one SCLK per channel (ADC i does trial k - i at SCLK k); SCLK 33-160: 8 words {0, ID[2:0], code[11:0]}, channel 0 first, same-frame data (no latency).
  Config hold register loads at SCLK 33 (after all conversions; frames with < 33 clocks change nothing); dbs is clocked by SCLK (no CLK pad); DOUT driven only while CS is low (pad _OE = ~CS). Pins: CS, SCLK, DIN, DOUT, RSTN (no new pad vs the 31-pad list).
- CLOCK: SCLK 0.64 MHz minimum (frame = 250 us), 1-5 MHz recommended; T_ACQ = 250 us - 19/f_SCLK = 220-246 us because each ADC reconnects to its amplifier right after its own last trial; CS from an MCU hardware timer, jitter <= 85 ns rms (0.1 LSB at 300 Hz full scale).
- ACQUISITION: no reset to 1.65 V (removed). At reconnect the amplifier output has moved <= 3.6-17.9 mV (5-1 MHz) from the held value; SIMULATED A4b no-reset case (+-0.24 V, 245 us) <= 0.26 LSB is therefore a conservative bound; follower sink stays BM_KSF 6.
  Power-up / large step: ESTIMATE 4-22 mV at 240 us for a 1.65 V step, discard ~10 frames.
- SUPPLY: MSB trial draws 13.55 pC (not 27 pC), 36.1 pC per conversion; 8 simultaneous ADCs draw 108 pC in one SCLK cycle, staggered 35.9 pC (3.0x less). Decap for a 50 mV peak: 2.17 nF (0.47 mm2) vs 0.72 nF (0.16 mm2) (MOS density 4.6 fF/um2 ESTIMATE, unchecked).
  Ring-down with L = 2 nH (ASSUMED) needs series R >= ~0.25 ohm; at 0.1 ohm nothing settles. First-order supply charge per trial is data-independent (repeats every frame).
- AREA / POWER: 0.136 mm2 for 8 ADCs + shared digital (decap excluded); ~28 uW (1.4 % of the amplifiers). Error budget RSS 0.44 LSB (two new crosstalk lines).

## Hand-back to the amplifier / NOTES.md (D0b; for the user or monitoring session to merge)
- Proposed Decision (D0b outcome): one ADC per channel, staggered conversions (ADC i starts at SCLK i+1), 160-clock / 10-word frame with config in word 0 (commit at SCLK 33), tracking resumes after each ADC's own last trial, no 1.65 V reset, dbs clocked by SCLK. Overrule points are listed in PLAN.md D0b.1/D0b.2.
- Decision 24 (SCLK >= 3.5 MHz): relaxed to 0.64 MHz minimum, 1-5 MHz recommended; T_ACQ 220-246 us. Decision 28: reset removed, kick criterion met by A4b adc245; KSF 6 kept (consistent with Decision 36). Decision 18: DIN added, readout of the same frame.
- Decision 27: the 27 pC MSB charge is an upper bound; corrected 13.6 pC per MSB trial, 36 pC per conversion, 8 ADCs => 108 pC (simultaneous) / 36 pC (staggered) per SCLK cycle. Supply droop remains OPEN and is now a floorplan item (decap 0.16-0.47 mm2, not in the TAPEOUT.md area).
- TAPEOUT.md: ADC area ~0.136 mm2 confirmed; ADC + interface power ~28 uW (not 17-20 uW). L0/L3: dbs/fsm clock = SCLK (check that nothing depends on a free-running clock); the config wrapper = 9-bit shift + 9-bit hold as in PLAN.md D0b.2 row 6.
- Amplifier: no change requested.
- Open for D1/D2/D4: monotonic DAC switching to cut supply charge (not analysed); L-C-R supply model; shared vcm_out tap vs local divider; MIM minimum size (Decision 25) and mismatch model (26).
