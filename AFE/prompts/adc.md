# ADC phase prompts (AFE/adc/)

The user designs the ADC (Decision 15). Settled: 12-bit SAR, 3.3 V, 4 kS/s per channel × 16
(Decision 16), VREF = VDD = 3.3 V (Decision 17), SPI with an external master and a 16-bit
frame (Decision 18). D0 chooses one muxed ADC vs 16 ADCs itself (Decision 19, rule 10).

ADC sessions write findings to AFE/adc/NOTES.md and never edit AFE/NOTES.md, so they may run
alongside an amplifier session (but only one ADC session at a time, and mind the shared CPU).
D0–D4 do not depend on the amplifier results; D5 needs A4b.
Start each session with:
"Read AFE/NOTES.md, AFE/TAPEOUT.md and AFE/adc/NOTES.md, then do phase D<n> from AFE/prompts/adc.md."
(TAPEOUT.md changes the ADC to an 8:1 mux, a DIN config frame, and a single 3.3 V supply.)
Review the result and /clear between phases.

---

## D0: Requirements and architecture plan (no circuit files)
Write AFE/adc/PLAN.md (same structure as AFE/amp/PLAN.md) covering:
1. Requirements derived from NOTES.md: input range 0–3.3 V (amp output 1.15–2.15 V nominal),
   LSB 0.806 mV, sample rate per channel and aggregate, conversion time budget, and an error
   budget in LSB: kT/C, comparator noise and offset, DAC mismatch, VDD noise/ripple (VREF = VDD),
   sampling-switch distortion and charge injection.
2. Decision 19 comparison, with numbers (hand ESTIMATES, labelled): one SAR + 16:1 analog mux
   vs 16 SARs. Area (cap DAC + comparator + logic), power, mux on-resistance and settling after
   a channel switch, what the amplifier output must drive in each case (link to Decision 3 and
   A4a), crosstalk. Choose one by rule 10 (NOTES.md) and record it as the Decision 19 outcome.
3. Cap DAC choice (binary vs split/bridge), unit cap from kT/C and MIM mismatch, total DAC
   capacitance; sampling switch (TG vs bootstrapped) over the 1.15–2.15 V input range.
4. Clocking and interface (Decision 18): SPI mode, max SCLK, frame timing (CS low → sample →
   12 bit-cycles → shift out), whether SCLK drives the conversion or a separate clock is
   needed, DIN for channel select (yes/no), pin list. The existing digital chip (rtl/dbs.v) is
   a 5 V domain: list every signal that crosses between it and the 3.3 V ADC and what level
   shifting it needs (design nothing in rtl/; just list it).
5. The verification plan: the exact .meas / script for every spec (DNL/INL from a ramp or
   code histogram, SNDR/ENOB from a coherently sampled sine + FFT, conversion time, power,
   VDD-noise sensitivity), and the folder layout under AFE/adc/ (rtl/, spice/, xschem/, tb/,
   sim/, figs/, scripts/).
6. Assumptions and anything you think is wrong in NOTES.md.
Stop.

## D0b: Re-plan for one ADC per channel (Decision 34; run before D1)
Read AFE/NOTES.md (Decisions 29-35), AFE/TAPEOUT.md, AFE/adc/PLAN.md. The architecture changed: ONE 12-bit SAR PER CHANNEL (N = 8), no analog mux, each ADC samples its own amplifier output,
simultaneous sampling, 4 kS/s per channel, single 3.3 V DVDD, VREF = VDD. Update AFE/adc/PLAN.md (and write findings to AFE/adc/NOTES.md, not AFE/NOTES.md): per-channel area/power with a
per-ADC cell (hand estimates labelled ESTIMATE), the serial interface for 8 converters on ONE DOUT (CS falling = simultaneous sample, 12 SCLK trials, then shift out 8 x 16-bit frames or another scheme: choose by rule 10;
the master clock budget; group sketch (2026-11-12): E[i] -> routing TGATE -> node REC[i] (pad) that also feeds amp[i] + ADC[i]; all ADC outputs share ONE DOUT, so build it as a digital serializer (daisy-chained 12-bit capture/shift registers, or a channel mux into one output flop), NOT a wired or tri-state bus; config write through DIN: MODE + EN[7:0] 9-bit shift register in a new wrapper, plus the pins list in TAPEOUT.md), the new acquisition window (frame period 250 us per channel, so T_ACQ can be far longer than 11 us),
whether the ADC should skip the reset to 1.65 V (sample from the previous own value: step <= ~0.24 V at 300 Hz full scale) or reset (step = the signal), and what that does to the amplifier follower load. Also re-budget the supply: 8 ADCs sampling and converting SIMULTANEOUSLY with VREF = VDD draw ~8 x 27 pC at the MSB trial (ESTIMATE, Decision 27 had one ADC),
so decide whether to stagger the conversions by channel (cost: a few clock phases) and give the VDD-droop and crosstalk budget in LSB with the amplifier PSRR table (NOTES.md "A4b findings", section 5). Re-derive
Decisions 24 and 28 (SCLK, T_ACQ, kick criterion) for the new frame and state what stays valid. Write no circuit files. Stop.

## D1: Comparator
Design a dynamic comparator (preamp + latch) on 3.3 V for the D0 clock rate. Measure: decision
time vs input difference, input-referred offset (Monte Carlo with sw_stat_mismatch=1, 30-50
runs), input-referred noise (transient noise or probability-vs-Vin sweep), kickback onto the
DAC node, energy per comparison, input common-mode range for the chosen DAC switching scheme.
Corners: typical 27 C, ff 85 C and ss -40 C only (all 9 only if a result is within 10 % of its limit). xschem cell + equivalence check (rule 8). Update NOTES.md.
Stop.

## D2: Cap DAC and sampling switch (ONE ADC PER CHANNEL, Decision 34: no mux)
Size the unit MIM cap from kT/C and mismatch (use mimcap_statistical). Build the DAC and its
switch network with ideal switches first, then transistor switches. Measure DAC settling to
½ LSB in each bit-cycle, sampling-switch distortion and charge injection over 1.15–2.15 V
(and 0–3.3 V), DAC DNL from mismatch (Monte Carlo, 30-50 runs). No mux.
Update NOTES.md. Stop.

## D3: SAR logic and SPI output (Verilog)
Write AFE/adc/rtl/sar_ctrl.v (synchronous SAR state machine, start/done, 12-bit result, channel
counter if muxed) and the serial interface from D0b / Decisions 32-35 (CS, SCLK, DIN config write of MODE + EN[7:0], one DOUT serializer for 8 per-channel ADCs; frame format as chosen in D0b). Icarus testbench with an ideal comparator
model that checks every code and the SPI framing, including CS edge cases. Synthesize with
LibreLane at a 3.3 V corner as a SEPARATE design under AFE/adc/ (do not touch config.json or
rtl/dbs.v); report area and timing at the D0 clock. Stop.

## D4: Mixed-signal top level
Combine comparator, DAC (and mux) and SAR logic in ngspice, using the Icarus co-simulation
bridge (ivlng) or the synthesized gate netlist; say which and why. Measure DNL/INL (ramp or
histogram) and SNDR/ENOB (coherent sine, FFT) at typical, then ff 85 C and ss -40 C only. Repeat with a noisy /
rippled VDD (VREF = VDD, Decision 17) and report the ENOB loss. Update NOTES.md. Stop.

## D5: Amp + ADC
Drive the ADC from the one-channel amplifier testbench (AFE/amp, after A4b) with the Randles
source. Check that the amplifier output (or its buffer) settles to ½ LSB within the
acquisition window, for ONE channel (no mux), and report end-to-end SNDR
and input-referred noise in the neural band. Update NOTES.md. Stop.

## D6: Report (SHORT, low effort)
Write AFE/adc/README.md, at most one page: how to run, a results table (target / measured / corner / pass-fail / log path), what is IDEAL, open items. Do not re-run anything. Stop.
