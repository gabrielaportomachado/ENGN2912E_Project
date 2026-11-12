# AFE ADC: phase D0 plan (no circuit files)

Simulation-only course project (ENGN2912E). Not a medical device.
Status: PROPOSAL (D0). Every number is a hand ESTIMATE unless it says SIMULATED. SIMULATED numbers come from the A4a amplifier
logs (AFE/amp/sim/a4a_*) and, for the aliasing budget, from the amplifier output-noise spectra
(AFE/amp/sim/a4a_nspec_*.csv) processed by scripts/d0_estimates.py. All estimates are reproduced in sim/d0_estimates.log.

## 0. Choices I made (rule 10) and what needs the user's attention

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

## 2. Decision 19: one SAR + 16:1 mux versus 16 SARs (ESTIMATE; sim/d0_estimates.log section 4)
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

## 4. Clocking and interface (Decision 18)
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
