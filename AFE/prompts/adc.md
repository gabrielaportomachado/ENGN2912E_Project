# ADC phase prompts (AFE/adc/)

Start only after the amplifier's A4 results exist (the ADC input range and sample rate
depend on them), and after the team has confirmed who designs the ADC.
Start each session with:
"Read AFE/NOTES.md, then do phase D<n> from AFE/prompts/adc.md."
Review the result and /clear between phases.

---

## D0: Plan (no simulation)
From NOTES.md, derive the ADC requirements: input range, sample rate (state the
per-channel vs muxed assumption), resolution, LSB size, and an error budget (kT/C,
comparator noise and offset, DAC mismatch, reference). Compare architectures: one muxed
SAR vs one SAR per channel; binary vs split cap DAC; sampling switch type (TG vs
bootstrapped). Recommend one, list the assumptions, define the .meas/scripts for each
spec (DNL/INL from a ramp or histogram, SNDR/ENOB from a coherent-sampled sine FFT,
conversion time, power). Propose the folder layout under AFE/adc/
(rtl/, spice/, xschem/, tb/, sim/, figs/). Stop.

## D1: Comparator
Design a dynamic comparator (preamp + latch) on 3.3 V. Measure: decision time vs input
difference at the planned clock, input-referred offset (Monte Carlo with
sw_stat_mismatch=1, ≥100 runs), input-referred noise (transient noise or a
probability-vs-Vin sweep), kickback, energy per comparison. Corners. Update NOTES.md. Stop.

## D2: Cap DAC and sampling switch
Choose the unit MIM cap from kT/C and mismatch (use mimcap_statistical). Build the DAC
and switch network with ideal switches first, then transistor switches. Measure DAC
settling within ½ LSB per bit-cycle, sampling-switch distortion and charge injection
over the input range, and the DAC's DNL from mismatch (Monte Carlo). Update NOTES.md.
Stop.

## D3: SAR logic and serial output (Verilog)
Write AFE/adc/rtl/sar_ctrl.v (synchronous SAR state machine, start/done, 12-bit result)
and a serial shift-out (SPI-like: CS, SCLK, DOUT), plus an Icarus testbench with an
ideal comparator model that checks every code. Synthesize with LibreLane at a 3.3 V
corner as a separate design (do not touch config.json or rtl/dbs.v). Stop.

## D4: Mixed-signal top level
Combine the comparator, DAC and SAR logic in ngspice. Use the Icarus co-simulation
bridge (ivlng) or the synthesized gate netlist; say which you used and why. Measure
DNL/INL (ramp/histogram) and SNDR/ENOB (coherent sine, FFT) at typical, then corners.
Update NOTES.md. Stop.

## D5: Amp + ADC
Drive the ADC from the one-channel amplifier testbench (AFE/amp) with the Randles source.
Check that the amplifier output settles to ½ LSB within the acquisition window, and
report end-to-end SNDR with the neural-band input. Update NOTES.md. Stop.

## D6: Report
Write AFE/adc/README.md in the same format as AFE/amp/README.md. Stop.
