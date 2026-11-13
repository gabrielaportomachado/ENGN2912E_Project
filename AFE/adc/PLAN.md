# AFE ADC: phase D0 plan (no circuit files)

Simulation-only course project (ENGN2912E). Not a medical device.
Status: PROPOSAL (D0), re-planned in D0b (section D0b below wins). Every number is a hand ESTIMATE unless it says SIMULATED. SIMULATED numbers come from the A4a amplifier
logs (AFE/amp/sim/a4a_*) and, for the aliasing budget, from the amplifier output-noise spectra
(AFE/amp/sim/a4a_nspec_*.csv) processed by scripts/d0_estimates.py. All estimates are reproduced in sim/d0_estimates.log.

## D0b. RE-PLAN for ONE ADC PER CHANNEL (Decisions 29-36; written 2026-11-13; this section WINS over the D0 text below wherever they differ)

Every number is a hand ESTIMATE (ideal charge algebra / arithmetic) unless marked SIMULATED (amplifier logs); all reproduced in sim/d0b_estimates.log (scripts/d0b_estimates.py). No circuit files.
Architecture now: N = 8 channels, each = amplifier + its own 12-bit SAR (no analog mux), all 8 sample at the same instant (CS falling), 4 kS/s per channel (250 us period), single 3.3 V DVDD, VREF = VDD,
ONE DOUT shared by a digital serializer (no tri-state bus), config on DIN. Signal path (group sketch): E[i] -> routing TGATE -> REC[i] (pad) -> amp[i] -> ADC[i].

### D0b.1 Needs your attention
1. SUPPLY IS THE BIGGEST ADC RISK (D0b.5). VREF = VDD and 8 ADCs trial at once. Corrected charge (ideal charge conservation, not D0's upper bound): MSB trial 13.6 pC (D0/Decision 27 said 27 pC), 36.1 pC per conversion.
   Simultaneous trials draw 108 pC in the first SCLK cycle; staggering the 8 SARs by one SCLK each cuts that to 35.9 pC (3.0x). To keep the on-chip droop <= 50 mV the decap needs 0.72 nF (staggered) vs 2.17 nF (simultaneous)
   = 0.16 mm2 vs 0.47 mm2 of MOS decap (ESTIMATE, density 4.6 fF/um2 NOT checked in the PDK; the ADCs themselves are 0.136 mm2). And the ring-down after each trial needs >= ~0.25 ohm of series damping with L = 2 nH (ASSUMED, package unknown):
   at R = 0.1 ohm the ring does not settle in a bit time. Nothing in the plan can remove this risk; D2/D4 must simulate an L-C-R supply (Decision 27) and L2/L3 must budget the decap area (0.16-0.47 mm2 is a floorplan item).
2. No CLK pad: the routing block (rtl/dbs.v: FSM + 2-stage enable registers, so 2-3 clock edges after a config change) must be clocked by SCLK. I commit config at SCLK 33 (after all conversions), so its switch outputs change at SCLK ~35 of the same frame, never during a conversion.
   dbs then only advances while SCLK runs (frames of >= 32 clocks, every 250 us). L0/L3 must check that nothing in dbs/fsm depends on a free-running clock.
3. Frame = 160 SCLK = 10 x 16-bit words (D0b.3), CS must come from an MCU HARDWARE TIMER every 250 us: aperture jitter limit 0.1 LSB = 85 ns rms at 300 Hz full scale (software-polled CS would cost SNR).
4. Decision 24 (SCLK >= 3.5 MHz) is no longer needed and is relaxed to SCLK 1-5 MHz recommended (absolute minimum 0.64 MHz). Decision 28: the 1.65 V reset is dropped altogether (D0b.4). Decision 18 changes: DIN exists, the readout is of the SAME conversion (no one-frame latency).
5. ADC area 0.136 mm2 (8 ADCs + shared digital) and ADC + interface power ~28 uW (1.4 % of the amplifiers; D0's 17 uW was for 64 kS/s DAC energy only: the 128-clock readout chain and the clock tree now dominate). No amplifier change is required (D0b.7).
6. I did not model monotonic / energy-saving DAC switching (it would cut the supply charge, 2-4x, ESTIMATE from the literature, not checked here); it is the first option to evaluate in D2 if the decap area is too large. Not chosen now because it changes the DAC design (D2) and the comparator ICMR (D1).

### D0b.2 Choices I made (rule 10)
| # | Choice | Options (numbers) | Why |
|---|--------|-------------------|-----|
| 1 | Per-channel ADC cell = D0 cell (binary 12 bit, 4.01 fF unit, TG bottom-plate sampling, dynamic comparator, SAR logic); no analog mux | D0 per-ADC area 15,975 um2; +300 um2 for the readout chain mux | Decision 34; nothing in D0 depended on the mux except the 16:1 TGs (removed) |
| 2 | Conversions STAGGERED by one SCLK per channel (ADC i starts trial 1 at SCLK i+1; 7-flop token chain; conversions end at SCLK 19) | simultaneous: 108 pC first cycle, 2.17 nF decap (0.47 mm2); staggered: 35.9 pC, 0.72 nF (0.16 mm2) | (2) least area: saves ~0.31 mm2 of decap for 7 flops; sampling stays simultaneous (CS falling), only the bit trials are offset; the extra hold time is <= 19 clocks (3.8-30 us, leakage <= 0.02 LSB) |
| 3 | Readout = the 8 SAR result registers chained into ONE 96-bit shift register (reused, +12 mux2 per ADC) behind a 16-bit word former {4-bit ID, 12-bit code} (ID = channel index, ID MSB = 0), channel 0 first | (a) reuse (+2,400 um2 total); (b) 96 separate capture flops + load/shift mux (+9,600 um2); (c) 96-bit stream without ID (-3 flops, breaks the Decision 18 word, MCU words not 16-bit aligned) | (1) keeps the Decision 18 word; (2) smallest area; the result registers are free after their conversion, tracking does not need them |
| 4 | Tracking resumes right after each ADC's own last trial (SCLK 12+i), not at CS rising; NO reset to 1.65 V; ADC input node sees only its own amplifier | resume at CS rising: T_ACQ = 250 - 160/f (90-218 us); resume after trials: 220-246 us; reset: one more switch + a 1.65 V source, -0.74..-2.25 LSB kick (A4b) | (4) fewest switches/signals; also minimises the amplifier step: at reconnect the output has moved <= 5.1 mV (3.5 MHz) from the held value (D0b.4) |
| 5 | Frame = 160 SCLK = 10 x 16-bit words: word 0 (SCLK 1-16) DIN = {7 x 0, MODE, EN[7:0]}, DOUT = 0; word 1 (17-32) idle (DIN ignored, DOUT 0); words 2-9 (33-160) = channels 0-7 on DOUT | 147 clocks (19 + 128, not 16-aligned); separate config frame (needs a clock-count / mode decode); echo of the committed config in word 1 (+~20 gates) | 16-bit aligned DMA transfers on any MCU; one frame type; no mode decode. The config echo would give a readback of EN/MODE for bring-up (there are no EN pads): NOT chosen by rule 10, recommended as optional, your call |
| 6 | Config: 9-bit shift register takes DIN on SCLK rising edges 1-16 (the last 9 bits stay), 9-bit hold register loads at SCLK 33 (a frame with fewer than 33 clocks changes nothing); hold -> dbs mode/en. Reset: EN = 0 (all switches open), MODE = 0 | commit at CS rising (dbs would then switch during the next conversion window); commit mid-frame | commit between conversion and readout: no routing-switch activity near a decision instant; runt frames are harmless |
| 7 | DOUT: pad _OE = NOT CS (driven only while CS is low), data from one output flop clocked on SCLK falling edge (mode 0); no internal tri-state or wired bus | always driven | standard SPI sharing at no cost; internal bus avoided as the group asked |
| 8 | ADC top-plate reset / comparator threshold: reuse the amplifier's vcm_out tap (VDD/2) per channel, comparator threshold = the SAME node as the reset (any VDD/2 error cancels, only matching of reset and threshold matters) | local per-ADC divider (2 resistors per ADC, extra static current) | (4) reuse. Charge pulled from the shared tap per frame <= 17 pF x 1 LSB = 14 fC per ADC (ESTIMATE), 8 ADCs 0.11 pC into a ~0.75 MOhm node: small; D1/D4 verify, the divider is the fallback |
| 9 | dbs clock = SCLK (no CLK pad, TAPEOUT.md final list of 31 pads unchanged) | CLK pad (+1 pad, over budget) | pad budget; item 2 of D0b.1 |

### D0b.3 Interface and frame timing (replaces section 4 below; all ESTIMATE, sim/d0b_estimates.log section 1)
- Pins used by the ADC/interface (all in the 31-pad list, TAPEOUT.md): CS, SCLK, DIN (input_cmos / input_schmitt as listed), DOUT (bidirectional, _OE = ~CS, _IE = 0), RSTN (async, clears counters, EN = 0, results). No other pad.
- SPI mode 0: CS active low, DIN sampled on SCLK rising, DOUT changes on SCLK falling, MSB first. SCLK idles low; the sampling instant is the CS FALLING EDGE itself (asynchronous: the top-plate switches of all 8 ADCs open from the buffered CS, skew < ~1 ns), SCLK is silent for >= 90 us before it (frame <= 160 us at SCLK >= 1 MHz).
- Timeline: CS falls = all 8 sample. SCLK k (k = 1..): ADC i performs trial k - i (i = 0..7, 12 trials MSB first), so ADC 0 finishes at SCLK 12 and ADC 7 at SCLK 19; each ADC reconnects its sampling network to its amplifier right after its last trial. SCLK 1-16 shift DIN in (word 0). SCLK 32 end of word 1.
  At SCLK 33 the config hold register loads and the readout starts: SCLK 33-160 shift out 8 words {0, ID[2:0], code[11:0]}, channel 0 first. CS rises after exactly 160 SCLK. A frame aborted early (CS rising before SCLK 160) gives incomplete data and no config change if it had < 33 clocks; the counters restart at the next CS falling.
- Master clock budget (SCLK, MCU 3.3 V assumed):
  | SCLK | frame | silent time before next CS falling | T_ACQ (resume after own trials) |
  |---|---|---|---|
  | 0.64 MHz (minimum, frame = 250 us) | 250 us | 0 | 220.3 us |
  | 1 MHz | 160 us | 90 us | 231.0 |
  | 3.5 MHz | 45.7 | 204 | 244.6 |
  | 5 MHz (maximum, D0; D1/D2 confirm) | 32 | 218 | 246.2 |
  Recommended 1-5 MHz. The MCU needs: a hardware timer for CS at 4 kHz (jitter <= 85 ns rms), 10 x 16-bit DMA words per frame, DIN stable during word 0 (it carries the 9-bit config every frame, so config is refreshed every 250 us), 3.3 V logic.
  First valid data: the first frame after reset is a valid conversion (readout is of the same frame), but the amplifier needs seconds to settle after power-up (A4b: 17 s to 10 mV, SIMULATED) and the ADC kick after a 0 V start needs ~10 frames (D0b.4).
- Latency and throughput: zero frame latency; aggregate 32 kS/s; SCLK clocks the SAR logic directly (no internal clock) and the 96-bit chain shifts for 128 clocks per frame.

### D0b.4 Acquisition window, reset, and what stays of Decisions 24 and 28 (ESTIMATE + SIMULATED A4b)
- T_ACQ = 250 us - 19/f_SCLK = 220-246 us (table above). The ADC cap reconnects to its amplifier 3.8-30 us after the sample instant, when the output has moved at most 942 V/s x t = 3.6 mV (5 MHz) / 5.1 mV (3.5 MHz) / 17.9 mV (1 MHz) from the held value,
  so the step the amplifier sees is ~5-20 mV plus the code residual (<= ~2 LSB, D1/D2), NOT the 0.24 V of a sample-to-sample step and NOT the +-0.5 V of the reset case.
- SIMULATED (sim/a4b_adc245.log, no reset, C_s 17 pF behind 1 kOhm, +-0.24 V): |error| at 245 us <= 0.26 LSB (0.21 uV input-referred) at typ 27 C, ff 85 C, ss -40 C; <= 0.48 LSB even at 11 us. The reconnect step is 13-67x smaller than the tested one (1-5 MHz; 47x at 3.5 MHz), so this is a conservative bound.
- DECISION 24 re-derived: its purpose (T_ACQ >= 11.05 us in a 15.625 us period) is moot: T_ACQ is >= 220 us for any SCLK >= 0.64 MHz. The D0 settling arithmetic (SIMULATED A4a follower: 1 V down worst 7.68 us, 3.3 V down worst 20.05 us at ss -40 C) is met 29x (1 V) / 11x (3.3 V) over (220 us window); the full-rail step settling that was "report only" now also fits the window (settling only; the stage-2 loop kick below is separate).
  New SCLK requirement: 0.64 MHz minimum (frame fits), 1-5 MHz recommended; no MCU constraint beyond that.
- DECISION 28 re-derived: the 1.65 V reset is REMOVED (not just rejected): no extra switch; the amplifier follower sink stays BM_KSF 6 (Decision 36); the 4 mW sink and the KSF sweep are not needed; the ff 85 C swing miss is unaffected.
  Kick criterion for the new frame: output within 0.5 LSB of final value at the sample instant for steps up to the 0.24 V sample-to-sample bound: SIMULATED met (<= 0.26 LSB).
- Large one-time steps (ADC power-up with C_s at 0 V, or an artifact): follower settling to 0.5 LSB takes 11.2 us for 1.65 V (worst corner, D0 formula with SIMULATED sink 3.26 uA), inside T_ACQ; the stage-2 loop kick (error ~ step^2 from A4b) is ESTIMATED at 4-22 mV at 240 us for a 1.65 V step,
  decaying with the 0.3-0.5 ms loop constant: discard the first ~10 frames (2.5 ms) after reset. D5 measures it. DBS artifacts of several volts remain out of scope.
- A4b ADC load model (C_s 17 pF, R_ADC 1 kOhm, 20 fF off-load) is unchanged; "ADC input model" of section 5.3 below stays valid, the T_ACQ column is superseded by the table above.

### D0b.5 Supply: 8 simultaneous VREF = VDD ADCs (ESTIMATE; sim/d0b_estimates.log sections 2-3 and 7)
- Charge from VDD per trial (ideal charge conservation; bottom-plate sampling, top plate at VDD/2; a failing trial bit returns its charge to GND, not to VDD): trials MSB..LSB mean 13.55 / 10.16 / 5.93 / 3.18 / 1.64 / 0.83 / 0.42 / 0.21 / 0.11 / 0.05 / 0.03 / 0.01 pC; 36.1 pC per conversion (119 pJ; D0's 233 pJ is conservative).
  The charge per trial is INDEPENDENT of Vin to first order, so the supply bounce repeats every frame (an offset/INL term); only second-order effects (finite switch Ron, parasitics) make it data-dependent = inter-channel crosstalk.
- Charge per SCLK cycle summed over 8 ADCs: simultaneous 108.4 pC (cycle 1); staggered 35.9 pC (cycle 8). L-C-R model (ASSUMED L = 2 nH, series R, on-chip decap C, residual at the decision instant T = half an SCLK period): need <= 0.1 LSB = 81 uV.
  Examples (residual in LSB, simultaneous | staggered): C = 1 nF, R = 0.25 ohm: 100 ns 0.26 | 0.086, 143 ns 0.018 | 0.006; R = 0.1 ohm: 11 | 3.7 and 3.8 | 1.3 (fails); C = 2 nF, R = 0.25 ohm: 0.13 | 0.043. So at 5 MHz and R = 0.25 ohm only the staggered scheme passes at 1 nF; R below ~0.2 ohm fails everywhere.
- Budget in LSB (RSS 0.44 of 0.5): kT/C 0.02, comparator 0.25, DAC 0.25, external VDD 0.20, switch 0.15, NEW on-chip supply bounce crosstalk 0.07, NEW shared-tap/digital activity 0.05. External VDD with the SIMULATED supply gain (sim/a4b_vddbudget.log): rms noise allowed for 0.2 LSB = 10.35 mV (DC), 2.29 mV (50 Hz), 3.46 mV (300 Hz), 0.58 mV (1 kHz), 0.35 mV (10 kHz, aliased: no anti-alias filter).
- Rules for D2/D4: model the supply as source -> L-R -> on-chip C with all 8 ADCs in the testbench and the stagger schedule; report the residual at every decision instant in LSB for both schedules; the stagger stays unless the simultaneous schedule passes with the same decap.

### D0b.6 Area, power (ESTIMATE; sim/d0b_estimates.log sections 4-5)
- Per ADC 16,275 um2 (DAC 9,400, comparator 2,000, SAR logic 3,075, switches 1,500, chain mux 300). Shared digital 6,175 um2 (frame counter 8, ID counter 3, stagger token 7, config shift 9 + hold 9, control 3 flops; ~150 gates; buffers).
  8 ADCs + shared = 136,375 um2 = 0.136 mm2 (TAPEOUT.md ~0.13 mm2). Decap not included: 0.16-0.47 mm2 (D0b.1 item 1).
- Power at 32 kS/s total: DAC 7.4 uW + comparator/logic 0.7 + readout chain 9.8 + clock tree 10.5 = 28 uW (8.6 uA at 3.3 V) = 1.4 % of the amplifiers (1.96 mW, SIMULATED A4a). Assumptions: 0.2 pJ per flop-clock, 1.5 pF clock tree.

### D0b.7 What stays valid from D0 and what changes
| D0 section | Status |
|---|---|
| 1 requirements, 1.2 error budget | valid; budget gets two new lines (D0b.5); rate now 4 kS/s x 8 = 32 kS/s aggregate |
| 1.3 VDD noise | valid; the 27 pC / 336 nF figure is superseded by D0b.5 (13.6 pC MSB, 36 pC per conversion, 8 ADCs) |
| 2 Decision 19 (mux vs 16 SARs) | SUPERSEDED by Decision 34 (one SAR per channel, no mux) |
| 3 DAC, comparator, switches | valid, except "mux = 16 TG pairs" (removed); D2 must still check the minimum MIM size (Decision 25) and run the mismatch model (26) |
| 4 clocking / interface | SUPERSEDED by D0b.3 (DIN, 160-clock frame, no 5 V -> 3.3 V crossings: single 3.3 V, Decision 30) |
| 5 aliasing | valid unchanged (4 kS/s per channel, no oversampling, Decision 23 keeps the documented risk) |
| 5.3 A4b input model | model valid; T_ACQ superseded by D0b.4 |
| 6-8 folder layout, tests | valid; D3 adds the 8-ADC stagger/serializer/config testbenches; D2/D4 add the L-C-R supply; D5 stays one channel; the mux tests are dropped |
| Amplifier | no change requested (follower sink KSF 6 stays, Decision 36); A4b adc245 no-reset case is the load check |

### D0b.8 Things I think are wrong or missing elsewhere
1. Decision 27 / PLAN.md 1.3 "27 pC MSB trial": upper bound; the floating top plate gives 13.6 pC (D0b.5). The risk is larger than that figure suggested only because there are now 8 ADCs.
2. TAPEOUT.md "ADC power ~17-20 uW" and "ADC ~0.13 mm2": the area holds (0.136 mm2); power is ~28 uW because of the readout chain and clock tree. Neither matters against 2 mW of amplifiers.
3. The tapeout plan lists no CLK pad but dbs needs a clock: resolved here by SCLK (D0b.1 item 2) but L0 must check it.
4. The decap area (0.16-0.47 mm2) is not in the TAPEOUT.md area re-estimate (0.65-0.85 mm2); adding it brings the block to ~0.8-1.3 mm2 against the ~1.23 mm2 slot. This needs a decision at L0 (monotonic switching, lower criterion, or bigger slot).
5. The 4 kS/s per channel rate is fixed by the MCU timer; if the MCU cannot provide a 85 ns-jitter CS, the aperture jitter dominates the noise of 300 Hz components before the ADC does.

Stop here for review. D1 (comparator) can start after you review D0b.

---

## 0. Choices I made (rule 10) and what needs the user's attention  [D0 text; see D0b above for what is superseded]

Priorities used, in order: meets targets and Decisions, least area, least power, least added hardware/complexity.

UPDATE after D0 review (NOTES.md Decisions 23-27): interferer attenuation is a documented risk (no analog second pole); SCLK >= 3.5 MHz => T_ACQ >= 11.05 us for A4b; D2 must check the minimum legal MIM size before any DAC design and
build/sweep its own mismatch model (A_C 0.25-1 %*um); the 27 pC supply draw is an open board risk. The sections below are the D0 plan as written; where they differ (e.g. T_ACQ 12.4 us default, section 5.2) the Decisions win.

| # | Choice | Options considered (numbers in sections below) | Why |
|---|--------|-------------------------------------------------|-----|
| 1 | Decision 19 OUTCOME: ONE 12-bit SAR behind a 16:1 analog mux | (a) 1 SAR + mux: 0.017 mm2. (b) 16 SARs: 0.256 mm2 (14.7x), + own clock + 16x12 result flops. (c) not quantified: 4 SARs x 4:1 mux ~ 0.064 mm2 (ESTIMATE, 3.7x), same power | Both meet the targets; power is equal (ADC < 1 % of the 3.9 mW of amplifiers); area decides |
| 2 | Decision 22: convert each channel at 4 kS/s (no oversampling, no on-chip filter); noise aliasing quantified as negligible; interferer aliasing quantified and handed back as an ANALOG issue | 1x, 2x, 4x, 8x oversampling with sinc^3/sinc^4 decimation (section 5) | Oversampling buys only ~6 dB per octave against a first-order analog filter and needs a stronger amplifier output stage; 1x is least power and complexity and still meets Decision 22 ("or quantify the aliasing") |
| 3 | Binary-weighted 12-bit cap DAC, unit 1.2 x 1.2 um (4.0 fF), C_total 16.4 pF | Units 1.0 / 1.2 / 1.5 / 2.0 um; split 6+6 with bridge | MSB-carry DNL sigma 0.27 LSB under the ASSUMED A_C = 0.5 %*um; split needs 64x larger units for the same accuracy (same total C, worse parasitics) |
| 4 | SPI mode 0, SCLK clocks the conversion (ADS7953-style), no DIN (channel auto-increments, 4-bit ID in every frame), 3 new pins CS/SCLK/DOUT; the existing 10 MHz `clk` is NOT used | separate conversion clock + 16-word result array; DIN channel select | no extra clock, no result memory, no crossing of `clk`; fewest pins |
| 5 | Transmission-gate sampling switch with bottom-plate sampling (top-plate switch opens first); no bootstrapping | bootstrapped NMOS | the settling is complete (section 4), so Ron variation does not distort; fewer devices |
| 6 | A4b ADC input model: C_s = 17 pF, Ron = 1 kOhm, t_acq = 12.4 us default (SCLK 5 MHz, 64 kS/s) and 7.8 us as the stress case | t_acq 3 / 4.6 / 7.8 / 12.4 us | simulated follower: 1 V downward step needs 7.7 us at the slowest corner (section 5.3) |

Needs your attention (details in the sections named):
1. Decision 19 outcome (one SAR + mux) is a choice you can overrule at D0 review (section 2).
2. Interferer aliasing is weak and is NOT fixed by oversampling plus a digital filter: first-order analog roll-off gives 13-20 dB at 3.7 kHz (fast corner 13 dB) and only +6 dB per octave of
   oversampling (section 5). If out-of-band interference matters, the cure is a higher-order analog low-pass in the amplifier (not defined: there is no interference spec; I propose one in section 5.2).
3. The A4a output follower sinks only 3.3-8.4 uA with 1/gm_f = 11.6-17.5 kOhm (SIMULATED); into the 17 pF sampling cap a DOWNWARD 1 V step takes 3.7-7.7 us to settle to 0.5 LSB (3.3 V: 8.6-20 us). That is met with
   t_acq = 12.4 us (SCLK 5 MHz), only just met at 7.8 us (0.12 us margin at ss -40 C) and NOT met at 4.6 us or 3 us. So SCLK should be >= ~3.5 MHz at 1x, any oversampling needs a stronger follower, and full-rail artifact
   steps are not covered. A4b must test this with the model below and size the follower sink (section 5.3).
4. The PDK has NO local MIM mismatch (mimcap_statistical is one global skew) and no active voltage-coefficient term in cap_mim_2f0. The DAC linearity numbers rest on an ASSUMED A_C = 0.5 %*um; D2 must
   add a per-unit mismatch model (section 3) and the result is only as good as that assumption.
5. VREF = VDD means the ADC reference moves with the supply. With the A4a amplifier (supply-to-output 1.0 V/V at 50-60 Hz vs the ideal 0.5) the in-band VDD noise must be <= 0.31 mV rms for 0.2 LSB (section 1.3);
   Decision 21(c) in A4b may relax that to 1.6 mV.
6. The amplifier, not the ADC, limits the SNR (section 1.1): ENOB of the channel at full +-500 uV input is ~7.3 bit. The 12 bits are for headroom (offsets, artifacts); the "14-16 bit stretch goal" in NOTES.md buys nothing.
7. Assumed: the external MCU is a 3.3 V device. ADS7953 datasheet values are still unverified; only its protocol shape is used.

## 1. Requirements and error budget

### 1.1 Derived requirements
- Input range 0-3.3 V (VREF = VDD), LSB = 3.3/4096 = 0.8057 mV. Amplifier output 1.15-2.15 V nominal (+-500 uV x 1000 around 1.65 V); offsets/artifacts may use the rest.
- Rates (Decision 16): 4 kS/s per channel x 16 = 64 kS/s aggregate. Per-channel Nyquist 2 kHz; the 300 Hz band is oversampled 6.7x.
- SIMULATED (amp/sim/a4a_summary.txt): amplifier output noise = input-referred 1.54-1.80 uV x 1000 = 1.91-2.23 LSB rms. The ADC may add <= 0.5 LSB rms (RSS +3 %: sqrt(2.1^2+0.5^2) = 2.16).
  Quantisation alone is 0.289 LSB rms. At the full +-500 uV input the channel SNR is 20log(354 uV/1.8 uV) = 46 dB (7.3 bit): the amplifier sets the ENOB.
- Conversion budget: one conversion per 15.6 us (64 kS/s). One frame = 16 SCLK. SCLK max 5 MHz (3.2 us frame, 12 bit trials of 200 ns), min 100 kHz (leakage droop ESTIMATE 9 uV over 160 us).
  With SCLK 5 MHz the frame is 3.2 us and the acquisition window (CS high) 12.4 us; with SCLK 2.048 MHz both are 7.8 us. Lower bound with t_acq >= 3 us: SCLK >= 1.27 MHz; with the A4a follower: SCLK >= ~3.5 MHz (section 5.3).

### 1.2 Error budget (ESTIMATE; input-referred LSB rms; RSS limit 0.5 excluding quantisation)
| source | allocation | basis |
|---|---|---|
| kT/C of C_s = 16.4 pF | 0.020 | computed (15.6 uV) |
| comparator noise | 0.25 | allocation (D1: probability-vs-Vin sweep or transient noise) |
| DAC mismatch (random DNL/INL) | 0.25 | allocation (D2: Monte Carlo) |
| VDD noise / ripple at the decision instants | 0.20 | allocation (D4) |
| sampling-switch distortion + charge injection | 0.15 | allocation (D2) |
| RSS | 0.43 | limit 0.5 |
Static specs (ASSUMPTION, justified by the 2 LSB amplifier noise that dithers the code): |DNL| <= 1 LSB, no missing codes (3 sigma); |INL| <= 2 LSB (3 sigma); offset error <= 2 LSB; gain error <= 0.5 % FS.
Dynamic: ADC-alone SNDR >= 68 dB (11.0 bit) at typical, >= 64 dB (10.4 bit) at corners (full-scale coherent sine).

### 1.3 VDD noise (Decision 17b), using the SIMULATED A4a PSRR (|v(out)/v(vdd)| V/V, 9 PVT)
Code error per mV of VDD ripple = (|A - 0.5|) x 1 mV / 0.806 mV, because the ADC is ratiometric (mid-scale = VDD/2). A4a: DC 0.58-0.69, 50/60 Hz 1.00-1.03, 300 Hz 0.78-0.97, 1 kHz 0.35-0.68, 10 kHz 0.04-0.09.
In the neural band the worst |A-0.5| = 0.53, i.e. 0.65 LSB per mV. For the 0.2 LSB allocation: in-band (0.5-300 Hz) VDD noise <= 0.31 mV rms; if Decision 21(c) brings |A-0.5| to <= 0.1: <= 1.6 mV rms.
Inside the ADC the DAC bottom plates switch to VDD/GND: the MSB trial draws Q = 8.2 pF x 3.3 V = 27 pC. On-chip decoupling cannot supply that to 0.1 LSB (would need 336 nF), so the board decoupling plus bond-wire
inductance must let the supply settle to < 0.08 mV before each decision. RISK for D2/D4 (not solvable by the plan alone); D4 simulates a rippled VDD with an L-C supply model.

## 2. Decision 19: one SAR + 16:1 mux versus 16 SARs (ESTIMATE; sim/d0_estimates.log section 4)  [SUPERSEDED by Decision 34 / D0b: one SAR per channel, no mux; kept for history]
| item | (a) 1 SAR + mux | (b) 16 SARs |
|---|---|---|
| DAC array (4096 x 4 fF, x1.6 spacing) | 9,400 um2 | 150,400 |
| comparator + preamp | 2,000 | 32,000 |
| SAR/control logic (25 flops + 80 gates) | 3,075 | 49,200 |
| switches/drivers | 1,500 | 24,000 |
| mux (16 TG pairs + decoder) | 1,360 | - |
| result storage for SPI (16 x 12 flops) | not needed (one result register) | ~14,400 |
| total | 17,335 um2 = 0.017 mm2 | ~270,000 um2 = 0.27 mm2 (15x) |
| conversion energy (1.3 C V^2 = 232 pJ) | 14.8 uW at 64 kS/s | 14.8 uW (same conversions/s) |
| clocking | SCLK clocks it | needs an internal clock per ADC or a shared one |
| mux settling | t_acq >= 2 us for 0.1 LSB (section 5.3) | none (each SAR has its own amplifier, window >> 100 us) |
| crosstalk | memory of the previous channel in C_s: residual exp(-t_acq/tau) = 1e-7 of the step at 3 us (< 0.001 LSB); 16 off-TG leakage 0.009 LSB (silicon-like ESTIMATE; this PDK model ~0) | none |
| what the amplifier must drive | 17 pF through 1 kOhm for t_acq, once per 250 us per channel (see 5.3) | its own 17 pF at 4 kHz per channel (same charge kick, long window) |
OUTCOME: (a). The extra constraint of (a) is the acquisition window, handled in 5.3.
Power does not discriminate (ADC ~17 uW vs 3.9 mW for the 16 amplifiers, A4a); area (15x) does.

## 3. Cap DAC, comparator, sampling switch
- DAC: binary-weighted, bits 11..0 = 2048..1 unit caps + 1 dummy unit. Unit = 1.2 x 1.2 um MIM (cap_mim_2f0_m2m3_noshield): Cu = 1.99e-3*L*W + 2.383e-10*2*(L+W) = 4.01 fF (PDK area+perimeter formula, same as AFE/amp).
  C_total = 16.4 pF; C_s = 17 pF with ~0.6 pF parasitics; array ~ 9,400 um2 with 1.6x spacing/dummies (ESTIMATE).
- Matching (ASSUMPTION, NOT in the PDK): sigma(dC/C) = A_C/sqrt(area), A_C = 0.5 %*um -> 0.42 % per unit; binary MSB-carry DNL sigma = sqrt(4096) x 0.42 % = 0.27 LSB (3 sigma 0.8 LSB).
  Table (sim/d0_estimates.log section 3): unit 1.0 um 0.32 LSB / 12.1 pF; 1.2 um 0.27 / 16.4; 1.5 um 0.21 / 24.2; 2.0 um 0.16 / 40.4.
  PDK reality: mimcap_statistical is `agauss(0,0.025,3)` per cap type, applied globally (sw_stat_global): all caps move together, DNL cannot be derived from it. D2 builds the array with a per-unit
  `agauss(0, sigma_u, 1)` multiplier (own netlist) and sweeps A_C = 0.25-1.0 %*um. Also no voltage coefficient is active in the 2f0 model, so VCR-induced INL cannot be simulated (state in D2).
- kT/C = 15.6 uV (0.019 LSB): irrelevant; the DAC is matching-limited, not noise-limited. Split-cap 6+6: sigma(MSB carry) = 512 sigma_u LSB, so the same accuracy needs 64x larger units: no gain.
- Comparator (D1): dynamic latch with a preamp, decision < 20 ns, input-referred noise <= 0.25 LSB rms (0.2 mV), offset removed by calibration-free design only if sigma <= 2 LSB (offset is a code shift, not an INL error).
  Threshold = VDD/2 (single-ended, top plate reset to VDD/2 during sampling).
- Switches: sampling = transmission gate (NMOS 10u/0.5u + PMOS 20u/0.5u, Ron ~ 0.6 kOhm mid-range, ESTIMATE) with bottom-plate sampling (top-plate switch opens first => signal-independent injection); DAC bit switches Ron <= 1.3 kOhm
  for 9 tau in half a 5 MHz cycle (W/L ~ 5-10); mux = 16 TG pairs, Ron ~ 1 kOhm.
- Reference: DAC bottom plates switch to VDD / GND (VREF = VDD, Decision 17). Energy 232 pJ/conversion (conventional switching).

## 4. Clocking and interface (Decision 18)  [SUPERSEDED by D0b.3 (DIN, 160-clock frame, 8 ADCs on one DOUT, single 3.3 V); kept for history]
- Protocol (ADS7953-shaped, own definition): SPI mode 0 (CPOL 0, CPHA 0), CS active low, MSB first, DOUT driven on SCLK falling edges and sampled by the master on rising edges, tri-state when CS is high.
  CS falling = sample instant (top-plate switch opens, aperture ~ns). SCLK 1-12 = 12 bit trials MSB first. SCLK 1-16 shift out the PREVIOUS conversion as {4-bit channel ID, 12-bit code}. CS rising after exactly 16 SCLK =
  end of frame, mux pointer increments, tracking of the next channel starts (t_acq = CS-high time, >= 3 us). A frame aborted before 16 SCLK discards the conversion and holds the pointer. The first frame after reset returns ID 0 / code 0.
- SCLK: max 5 MHz (D1/D2 confirm; fallback 2.5 MHz), min 100 kHz. 64 kS/s aggregate needs frame + t_acq <= 15.6 us. SCLK clocks the SAR logic directly (no internal clock).
- No DIN: the mux visits channels 0..15 in order and the ID in every frame lets the MCU detect a missed frame. Reset: existing `rstn` (level-shifted) clears the pointer.
- New pins: CS, SCLK, DOUT (+ VDD3/GND for the ADC). Reused: `rstn`. NOT used: `clk` (5 V, 10 MHz).
- Crossings between the 5 V chip (rtl/dbs.v: clk, rstn, mode, en[15:0], ready, sw_rec/sw_rec_b/sw_ipg/sw_ipg_b[15:0]; TGATE uses nfet_05v0/pfet_05v0) and the 3.3 V analog/ADC (nothing designed in rtl/):
  1. rstn -> ADC reset (5 V -> 3.3 V). 2. Fast-settle control fs (amplifier A4a/A4b), derived from `ready`/`rec_en`/`sw_rec[i]` edges: 1 shared or 16 per-channel signals (5 V -> 3.3 V).
  3. None from the 3.3 V domain into the 5 V domain. 4. CS/SCLK/DOUT go to an external MCU assumed to be 3.3 V (if 5 V: down-shifters on CS/SCLK, a 5 V-capable output stage on DOUT).
  Down-shift = an inverter built from 5 V devices (nfet_05v0/pfet_05v0) powered from VDD3: its input may swing 0-5 V, its output swings 0-3.3 V; no dedicated shifter cell is needed (ESTIMATE; device ratings from the PDK TGATE use).
  The REC node from the 5 V TGATE into the 3.3 V amplifier input is AC-coupled by Cin (A3); its overvoltage/IPG excursions remain an open question (NOTES).

## 5. Aliasing (Decision 22) and the ADC input model for A4b
### 5.1 Quantified aliasing (SIMULATED amplifier, sim/d0_estimates.log section 6; fout = 4 kS/s, band 0.5-300 Hz)
Noise: aliased noise power from the bands k*fout +- 300 Hz (all replicas to 1 MHz, amplifier output PSD weighted by the digital filter), input-referred:
| corner | in-band | 1x | 2x sinc^3 | 4x sinc^3 | 8x sinc^3 |
|---|---|---|---|---|---|
| ff 85 C (f_hi 867 Hz, worst) | 1.807 uV | 0.144 uV (0.63 % of the power; total 1.813) | 0.072 | 0.037 | 0.020 |
| typical 27 C | 1.670 | 0.102 (0.37 %) | 0.052 | 0.027 | 0.015 |
| ss -40 C (f_hi 359 Hz) | 1.538 | 0.070 (0.21 %) | 0.037 | 0.020 | 0.012 |
=> noise aliasing is negligible (+0.3 % on the total at worst); no hardware is needed for noise.
Interferers (attenuation in dB of a component that lands in the band; first-order amplifier response + digital filter), ff 85 C / ss -40 C:
| interferer frequency | 1x | 2x s3 | 4x s3 | 8x s3 |
|---|---|---|---|---|
| 3.7 kHz | 13 / 20 | 69 / 76 | 76 / 84 | 78 / 85 |
| 7.7 kHz | 19 / 27 | 19 / 27 (not filtered: it is an ADC image) | 93 / 101 | 101 / 109 |
| 15.7 kHz | 25 / 33 | 25 / 33 | 25 / 33 | 117 / 125 |
| 31.7 kHz | 31 / 39 | 32 / 39 | 32 / 39 | 32 / 39 |
In-band droop of the sinc^3 filter at 300 Hz: 2x -0.18 dB, 4x -0.23 dB, 8x -0.24 dB.
Worst-case figure (nearest unfiltered alias band): 1x 12.8-20.3 dB; 2x 19-27 dB; 4x 25-33 dB. Oversampling moves the worst alias band up one octave (+6 dB) per doubling because the analog filter is first order;
the digital filter only removes the bands near multiples of 4 kHz that are not ADC images.

### 5.2 Interference requirement (ASSUMPTION: no spec exists)
Out-of-band interference (kHz-range stimulation harmonics, EMI) of 100 uV pk at the amplifier input must alias below 0.5 uV (a quarter of the 2 uV noise budget): 46 dB. Not reachable by oversampling alone
(the 4x + sinc^3 option reaches 25-33 dB in the worst band; 46 dB would need ~16-32x oversampling, i.e. >1 MS/s aggregate). Reachable by an analog second pole: a 2nd-order response at the same f_hi gives 40log(f/f_hi):
at 3.7 kHz 25 dB (ff) / 40 dB (ss), combined with 2x + sinc^3 for the 4 kHz band the worst band moves to 7.7 kHz where 2nd-order gives 38 dB (ff) / 53 dB (ss) (ESTIMATE). Hand-back to the amplifier work (A4b/A5), only if the
interference requirement is real; the user decides.

### 5.3 ADC input model for A4b and what it asks of the amplifier (sim/d0_estimates.log section 5b)
- Model (AFE/amp/spice/adc_load.spice, to be written in A4b): amplifier out -> mux TG (Ron = 1 kOhm) -> C_s = 17 pF (starts at the previous channel's voltage), connected for t_acq then disconnected;
  off-channel load on each amplifier output 20 fF (ESTIMATE); parameters R_ADC = 1k, C_ADC = 17p, T_ACQ = 12.4u (default) and 7.8u (stress), V_PREV = V_OUT_CM +- 1 V and +- 3.3 V (steps), frame period 15.6 us (64 kS/s aggregate).
- SIMULATED A4a follower (a4a_op.log, 9 PVT): sink current 3.26-8.41 uA, 1/gm_f = 11.6-17.5 kOhm (typical 14.6). The follower is class A: it sources strongly but sinks only its bias.
  tau = (1/gm_f + Ron) C_s = 215-315 ns. A DOWNWARD step of dV settles to 0.5 LSB (0.40 mV) in t = C_s dV / I_sink + ln(dV/0.5 LSB) tau:
  | corner | I_sink | tau | 1 V down | 3.3 V down |
  |---|---|---|---|---|
  | ss -40 C (worst) | 3.26 uA | 315 ns | 7.68 us | 20.05 us |
  | typical 27 C | 5.21 | 265 | 5.33 | 13.15 |
  | ff 85 C (best) | 8.41 | 217 | 3.72 | 8.63 |
  (all 9 corners in the log). Windows: t_acq = 12.4 us (SCLK 5 MHz, 1x), 7.8 us (SCLK 2.048 MHz, 1x), 4.6 us (2x oversampling at 5 MHz), 3 us (minimum for the mux).
  => 1 V steps: met at 12.4 us (4.7 us margin); only just met at 7.8 us (0.12 us margin, ss -40 C); NOT met at 4.6 us or 3 us. 3.3 V (full-rail artifact) steps: not met below 20 us.
  Sink needed at the worst tau for a 1 V step: 3 us 31 uA, 4.6 us 7.9 uA, 7.8 us 3.2 uA (A4a has 3.26 uA at ss -40 C), 12.4 us 1.7 uA; for 3.3 V: 338 / 32 / 11.3 / 5.9 uA.
- Consequence (A4b decides, rule 10): at 1x with SCLK >= 3.5 MHz nothing changes in the amplifier; raising the follower sink (BM_KSF 6 -> 12 or more; ESTIMATE +5 uA = +17 uW per channel) is only needed for faster frames, for oversampling or if
  full-rail steps must be covered. An alternative that costs one switch per ADC (not per channel) is to precharge C_s to VDD/2 before each channel, which cuts the typical step to the signal amplitude; not chosen now.
- A4b pass criteria (derived, not requirements): output within 0.5 LSB of its final value at the end of T_ACQ for +-1 V steps at 12.4 us (and report 7.8 / 4.6 / 3 us), and the stage-2 loop recovers without ringing after the C_s connect/disconnect kick.

## 6. Folder layout (AFE/adc/)
```
AFE/adc/
  PLAN.md  README.md (D6)
  rtl/       sar_ctrl.v, spi_slave.v, adc_top.v, tb_*.v   (separate LibreLane design, not rtl/dbs.v)
  spice/     models_<corner>.spice (copy of the amp ones), comparator.spice, cap_dac.spice, samp_switch.spice, mux16.spice, adc_core.spice, adc_ivlng.spice
  xschem/    comparator, dac_switch, mux16, adc_core (.sch/.sym) + xschemrc
  tb/        see section 7
  sim/       logs and csv only (*.raw never opened)
  figs/      png
  scripts/   d0_estimates.py (this phase), run_d*.sh, dnl_inl.py, fft_enob.py, equiv_xschem_adc.sh, plots_d*.py
```

## 7. Testbench list
| phase | testbench | analysis | purpose |
|---|---|---|---|
| D1 | tb_cmp_delay, tb_cmp_offset_mc, tb_cmp_noise, tb_cmp_kick | .tran, MC (sw_stat_mismatch=1, >=100), prob-vs-Vin | decision time, offset sigma, noise, kickback, energy/decision, ICMR |
| D2 | tb_dac_settle (per bit), tb_dac_mc (per-unit agauss, python static model checked against SPICE at 16 codes), tb_samp_dist, tb_samp_inj, tb_mux_settle, tb_mux_xtalk | .tran, python | settling to 0.5 LSB, DNL/INL MC (>= 1000 draws), THD, charge injection, mux Ron/settling/crosstalk |
| D3 | sar_tb.v, spi_tb.v | Icarus | every code with an ideal comparator model, SPI framing, CS edge cases, reset |
| D4 | tb_adc_ramp, tb_adc_sine, tb_adc_vddnoise | ngspice + ivlng (or synthesized netlist) | DNL/INL (code transitions at selected codes + python full-array model), SNDR/ENOB, VDD sensitivity |
| D5 | tb_amp_adc | .tran | amplifier -> mux -> ADC with the Randles source: settling in t_acq, end-to-end SNDR/noise |

## 8. Exact measurements per spec (ngspice `.control` / python; syntax confirmed on first use)
- Transfer/DNL/INL: static DAC levels from cap-array charge algebra in python (4096 codes, N draws of per-unit mismatch), cross-checked against SPICE .op at 16 codes (|difference| < 0.01 LSB);
  `DNL_k = (T_{k+1}-T_k)/LSB - 1`, `INL_k = (T_k - ideal_k)/LSB` after best-fit gain/offset removal; report 3-sigma max over draws. Full-converter check: ramp with 4 inputs per code in ivlng at selected codes (0, 1, 2047, 2048, 4094, 4095 and 64 random).
- SNDR/ENOB: coherent sine, N = 1024 points, M = 127 cycles (gcd(M,N)=1), amplitude 0.99 FS and 0.3 V pk around 1.65 V; `fft_enob.py` computes SNDR = 10log10(P_signal/P_rest), ENOB = (SNDR-1.76)/6.02. Typical then 9 PVT. Repeat with a 10 mV sine and 1 mV rms noise on VDD: report ENOB loss and code shift.
- Conversion time and throughput: from the Verilog/SPICE timeline, CS falling to the 12th decision latched: meas `trig`/`targ` on the comparator output and SAR done; target <= 12 SCLK periods (2.4 us at 5 MHz).
- Power: `meas tran iavg avg i(Vdd3)` over >= 64 conversions at 64 kS/s; target <= 100 uW (ESTIMATE 17 uW).
- Mux: Ron from .dc of the closed TG at 0.3/1.65/3.0 V; settling = |v(Cs)-v(in)| at T_ACQ end after +-1 V and +-3.3 V steps (<= 0.5 LSB); crosstalk = in-band spectral line of a 1 V pk, 1 kHz sine on the adjacent unselected channel in the selected channel's code (<= 0.1 LSB).
- Sampling-switch THD of a 0.5 V pk sine (<= -74 dB) and charge injection (code shift vs input level, <= 0.5 LSB, signal-dependent part <= 0.15 LSB).
- Comparator: offset sigma, noise, decision time vs overdrive, kickback on the DAC top plate, energy (D1 list). SPI: Icarus checks for every code and frame edge case.
- Targets I cannot measure in simulation: VCR-induced INL (no active VCR in the model), real MIM mismatch (assumption), supply-pin inductance (board).

## 9. Things I think are wrong or missing in NOTES.md / the prompts
1. D2 says "use mimcap_statistical": that section is a single global skew, not local mismatch; the DAC DNL needs an own per-unit agauss model (section 3).
2. "Stretch goal 14-16 bit" (NOTES targets): the amplifier noise (~2 LSB rms at 12 bit, SNR 46 dB at full input) makes more bits useless.
3. Anti-aliasing: oversampling does not fix interferer aliasing with a first-order analog filter (section 5); no interference spec exists.
4. VREF = VDD makes the amplifier's supply gain (1.0 V/V at 50-60 Hz, A4a) a code error of 0.65 LSB/mV; Decision 21(c) in A4b addresses it.
5. The A4a follower sink (3.3-8.4 uA) is too weak for oversampling, for t_acq below ~8 us, or for full-rail artifact steps (section 5.3).
6. D4 says "SNDR from a coherent sine at typical, then corners" at conversion rate 64 kS/s; per-channel decimated metrics (4 kS/s) must be derived by sampling every 16th conversion of one channel.

## 10. Assumptions
- A_C = 0.5 %*um; Ron(TG) 0.6-1 kOhm; follower R_out 10-14 kOhm; std-cell areas 75 um2/flop, 15 um2/gate (7-track 5 V library scaled; confirm at D3 with the 3.3 V synthesis).
- External MCU at 3.3 V; SCLK <= 5 MHz; ADS7953 only as protocol reference (datasheet values unverified).
- Conversion energy 1.3 C V^2 (conventional switching); no calibration; no oversampling in hardware.
- 16 channels visited in fixed order 0..15 at 64 kS/s aggregate.
