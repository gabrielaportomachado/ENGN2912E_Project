# AFE ADC (8 x 12-bit SAR, one per channel)

Status after D0b-D5, X2 (2026-11-19), the pre-layout audit and F1 (2026-11-20). Source of every number: `NOTES.md` (this directory), `../NOTES.md` Decisions 40-45 and "F1 findings", `../review/AUDIT.md`; logs in `sim/` and `../review/sim/`.
The page was brought up to date in F1 (Decisions 43c-e, 44, 45); the D-phase rows of the results table were not re-run.

## Block diagram
```
amp[i] -> sampling TG -> split 6+6 MIM DAC (127 x 5x5 um units, plate 3.49 pF, bottoms 6.92 pF)
                              |plate                                 x8 (i = 0..7)
                         cmp_p (PMOS double-tail, pair 80u/0.5u)  <- clock from adc_clkgen tap i
                              |cmp_q
                         SAR (12 code flops, shared one-hot token decode)
   adc_clkgen: one dont-touch std-cell delay chain, comparator clock of ADC i = T0 + i*Delta (staggered)
   8 code regs -> one 96-bit shift chain -> DOUT (negedge flop, driven only while CS low)
   DIN -> 10-bit shift (RST_AMP + MODE + EN[7:0]) -> hold register (commit at SCLK 33)      VREF = VDD = 3.3 V
   vhalf (2 x 250 kOhm ppolyf_u_1k + 1 pF, one per ADC) -> TG (closed while tracking) -> Cref 7 pF -> cmp_p.inp      x8
```
Comparator: inn = DAC plate, inp = the SAMPLED FLOATING REFERENCE (Decision 42): Cref 7 pF (one MIM plate) is charged to VDD/2 from the per-ADC divider `vhalf` through a transmission gate that is closed while tracking and open during the conversion. The plate reset level is the same `vhalf` node.
Supply (Decision 44d, `../review/AUDIT.md` 4.9.2): three straps from the one pad pair: analog (amplifiers, bias, vhalf, Cref switch; pin `vdd`), ADC-main (comparators `vdd_cmp` + the digital macro, 0.125 nF MOS decap), ADC-DAC (the 13 bottom-plate drivers per ADC, pin `vdd_dac`, behind a 10 ohm strap resistor, 0.1 nF MOS decap). 0.225 nF in total = 56,500 um2 at 3.98 fF/um2.

## Interface
Pins: `CS`, `SCLK`, `DIN`, `DOUT`, `RSTN` (the bidirectional pad DOUT is the top-cell port pair `DOUT_OUT` / `DOUT_IN`, Decision 44b; `DOUT_IN` is not used). Frame = 160 SCLK = 10 x 16-bit words.

| SCLK | Content |
|---|---|
| 1-16 (word 0) | DIN = {6 x 0, RST_AMP, MODE, EN[7:0]} (RST_AMP added in I0, Decision 38); config commits at SCLK 33 (frames < 33 clocks change nothing); RST_AMP is a level, held until the next config frame or RSTN |
| 1-19 | the 8 conversions, ADC i runs trial k-i at SCLK k (CS falling = simultaneous sample) |
| 17-32 (word 1) | DOUT = held config {6 x 0, RST_AMP, MODE, EN[7:0]} of the PREVIOUS frame (committed at its SCLK 33; 0 after RSTN); DIN ignored |
| 33-160 (words 2-9) | channel 0..7, `{0, ID[2:0], code[11:0]}`, same-frame data |

SCLK 2 MHz nominal, 3 MHz max (0.64 MHz min). T_ACQ = 240-244 us. Input = the amplifier output, 1.15-2.15 V.
Accuracy claim (Decision 43c; restated after the post-layout L1b run by REVIEW R9: INL <= 1.1 LSB, typ 0.95, ff -40 1.10, ss 125 1.05, ff 85 C 3.1 LSB at the 1.99 V point): INL <= 1 LSB (pre-layout) beyond a fixed code offset for amplifier outputs <= 2.0 V (typ) / <= 1.9 V (ff 85 C); above that the plate error grows to +2.1 / +4.4 LSB at 2.15 V (typ / ff 85).
Fixed code offset (Decisions 43e, 46d; restated by L1b from the extracted adc_ch, AFE/layout/sim/post/adc_codes.json): -32.6 / -42.2 / -23.4 LSB (typ 27 / ff 85 / ss -40 C; pre-layout -30.2 / -40.1 / -22.0) = -26 / -34 / -19 uV at the electrode; a pure code shift (the signal is AC coupled).

### Protocol rules for the host (Decisions 43d, 44g; `../review/AUDIT.md` M5, m4, m5, i2, i3, i4)
1. Change RSTN only while CS is HIGH. A release or a pulse of RSTN while CS is low restarts the frame counter in mid-frame: the 16 DIN bits that follow are taken as word 0 and committed 33 edges later (a wrong routing / reset state until the next complete frame).
2. Every frame has exactly 160 SCLK. Never raise CS early: a frame shorter than 33 clocks commits nothing, one of 33-34 clocks commits the config but lets the routing change during the conversions of the next frame, and on an aborted frame the sampling switch closes 2.4-5.6 ns before the DAC drivers release (a short kick on the amplifier output).
3. Discard the first frame after any pause in the conversions (it reads +0.36 / +0.03 / +0.33 LSB differently). More frames are invalid after power-up, an amplifier reset or a record start: see the power-up sequence.
4. CS falling is the sampling instant of all 8 channels: drive CS from a hardware timer (jitter <= 85 ns rms) and let it fall >= 100 ns before the first SCLK edge (the chip needs >= 13 ns). SCLK may run while CS is high (shared bus).
5. The sample rate is set only by the host: 4 kS/s = one frame every 250 us (the chip accepts back-to-back frames: 12.4 kS/s at 2 MHz, about 18.5 kS/s at 3 MHz).
6. Noise: with Cin = 15 pF (Decision 50) the amplifier noise in 0.5-300 Hz (Decision-8 figure) is 1.89 / 2.14 / 1.73 uV at the electrode (typ / ff 85 / ss -40): typ and ss -40 meet the 2 uV figure, the ff 85 C value misses it by 7 % and is accepted by Decision 50 (limit 2.2 uV at ff 85 C). The earlier 20 pF figures (1.71 / 1.89 / 1.59 uV amplifier + aliasing + switch + ADC; unfiltered codes 2.04 / 2.23 / 1.92 uV) were not re-simulated for 15 pF (ESTIMATE: about +15 %). The host must low-pass the code stream to 300 Hz.
7. There is NO power-down: EN only gates the routing switches; about 2.0 mW flows in every mode (record, stimulate, reset, idle).
8. Signals on E and IPG must stay inside 0..VDD. The routing TGATE (5 V devices on 3.3 V) has Ron 4-21 kOhm typ over 0-3.3 V, up to 34 kOhm at ss -40 C (65 kOhm at 3.0 V); leakage < 1 pA inside the rails, 0.55 nA at VDD + 0.4 V. The stimulation path is a bench demonstration (tens of uA), not for real stimulation or connection to a person.
9. REF must be connected (to the reference electrode or to mid-supply): it reaches only MIM plates inside the chip and would drift to a rail if left open.

## How to run (from `AFE/adc/`; scripts need `bash`, not executable)
| Phase | Command |
|---|---|
| D1 | `bash scripts/run_d1.sh <delay\|offset\|noise\|icmr\|conv\|kick\|tbl>` -> `sim/d1_<case>.log` (`NMC=`, `NCYC=` env overrides) |
| D2 cap DAC / switch | `bash scripts/run_d2_conv.sh` (settle, samp, idd npz); `bash scripts/d2_ktc.sh`; `python3 scripts/d2_acweights.py <mode>`; `python3 scripts/d2_dnl.py` |
| D2 supply | `bash scripts/run_d2_supply.sh`, `bash scripts/run_d2_supply3.sh` (stagger) |
| D3 RTL | `bash scripts/run_d3_sim.sh` (Icarus: exhaustive, edge, corner x f matrix) |
| D3 synthesis | `bash scripts/run_d3_synth.sh` (LibreLane in `lg/`; CTS fails, run with `--skip OpenROAD.CTS --skip OpenROAD.ResizerTimingPostCTS`) |
| D3 STA taps | `python3 scripts/d3_taps.py sim/d3_taps.log` (runs `d3_sta.tcl`, 5 corners). The saved `sim/d3_taps.log` predates the hardened netlist by 7 hours (values differ by 0.2-0.6 ns): cite `../review/sim/sta_audit.log` (`../review/scripts/sta_audit.py`) |
| D4 settle / race | `python3 scripts/d4_settle.py <corner> <T> <VDD> <vins>`; `python3 scripts/d4_race.py <corner> <T> <VDD> <slew ns> <W ns> [dly]` |
| D4 supply | `python3 scripts/d4_idd.py ...` (currents), `python3 scripts/d4_supply.py 3` -> `sim/d4_supply_3MHz.log` |
| D4 hybrid | `python3 scripts/d4_hybrid.py dnl` / `enob` / `track` |
| D4b replay | `python3 scripts/d4_replay.py <corner> <T> <VDD> <dt_c ns> <W ns> <slew ns> <vins> [T_ns]` -> `sim/d4_replay.log` |
| D5 settling | `bash scripts/run_d5_settle.sh` -> `sim/d5_settle.log` |
| X2 (2026-11-19) | closed-loop PWL replay, one ngspice thread: `python3 scripts/x2_adc.py <corner> <n>` (ADC alone); `python3 scripts/x2_s1.py <typ\|ff85\|ss-40> <TPRE ms> all` then `python3 scripts/x2_s1_report.py`; `python3 scripts/x2_s3.py <corner> <N> <M> <TPRE ms>`; `python3 scripts/x2_s4.py <ff-40\|typ\|ss125> all 3`, `python3 scripts/x2_s4_sweep.py <corner> <case>`; `python3 scripts/x2_s5.py typ`; abort study `bash scripts/run_x2_s2_stats.sh`, `python3 scripts/x2_s2_trace.py`; what-ifs `bash scripts/run_x2_whatif*.sh` |
| F1 (2026-11-20) | `bash scripts/run_f1_checks.sh [adc\|steps\|s4\|all]` (replays after the F1 netlist changes -> `sim/f1_x2_*.log`); LVS references `python3 ../layout/scripts/mk_lvs_netlists.py` -> `../layout/lvs/`, their checks `python3 ../layout/scripts/check_lvs_netlists.py`; connectivity `python3 ../review/scripts/xcheck.py ../review/sim/f1_xcheck.log` |
| D5 SNDR / noise | `python3 scripts/d5_hybrid_amp.py` (hybrid SNDR, `sim/d5_sndr.log`); `python3 scripts/d5_noise.py` (`sim/d5_noise.log`); transistor-level `bash scripts/run_d5_sndr.sh` ABORTS (see open items) |

## Host power-up sequence and test plan (Decisions 38, 41, 44c)
1. Hold RSTN LOW while VDD ramps (the chip has no power-on reset: config and routing flops are cleared only by RSTN; the RSTN pad has its pull-down enabled, so an undriven RSTN also means "in reset"). All routing switches stay open, every REC node (internal, no pad) is parked at VCM_IN.
2. Release RSTN while CS is HIGH. Wait >= 5 s after VDD is stable: the shared bias needs 3.7 ms (typ), 1.0 ms (ff 85 C) but 3.6 s (ss -40 C) to start with 8 channels on it (`../review/sim/bias_startup.log`; the earlier "1 s" was measured with one channel). Wait >= 30 s only if the board supply is below 3.1 V at -40 C (23 s at 3.0 V).
3. Write a config frame with RST_AMP = 1 (word 0 = 0x0200, MODE = 0, EN = 0); keep it set for >= 100 ms (>= 30 ms needed); write a config frame with RST_AMP = 0. RST_AMP is a level held in the chip, it needs no clock while held.
4. Read frames for 1 s. Every channel must then read within 200 LSB of mid-scale (codes 1848-2248; a settled channel reads about 2018 = 2048 minus the code offset). If one does not, its amplifier is still latched at a rail: repeat step 3.
5. Write the working config (word 0 = {RST_AMP 0, MODE, EN}); read it back in word 1 of the NEXT frame. After a record start each enabled channel takes a reset pulse (about 3.6 ms typ, 1.9-6.9 ms over corners = 8-28 frames) and the amplifier then needs 0.13-0.27 s (1 mV electrode step) to 9 s (100 mV step) to settle: discard those frames.
Pad controls: DOUT drives only while CS is low (DOUT_OE = ~CS); RSTN pull-down on; the pad-control pin NAMES are checked against the organizer template (F1, `../review/scripts/xcheck.py`), the values (4 mA, fast, CMOS input off) are confirmed in L4.

## Results
Corners are typ 27 / ff 85 / ss -40 C unless noted. Types: SIM = transistor/ngspice or Icarus/OpenSTA, HYBRID = Python model fed with SIM numbers, ESTIMATE = hand/analytic.

| Item | Target | Measured | Corner | P/F | Type | Log |
|---|---|---|---|---|---|---|
| Comparator decision time (0.1 mV) | < half cycle | 1.5 / 1.3 / 1.8 ns | typ / ff / ss | PASS | SIM | `sim/d1_delay.log` |
| Comparator offset sigma | <= 2 LSB | 1.27 / 1.31 / 1.23 mV = 1.57 / 1.63 / 1.53 LSB | typ / ff / ss | PASS (code shift) | SIM | `sim/d1_offset.log` |
| Comparator noise (pair) | 0.25 LSB | 118 / 168 / 108 uV = 0.15 / 0.21 / 0.13 LSB | typ / ff / ss | PASS (latch open) | SIM | `sim/d1_noise.log` |
| Code offset, closed loop | code shift only | -30 / -40 / -22 LSB (typ / ff 85 / ss -40) = -24 / -33 / -18 uV at the electrode (Decision 43e). The D1 / D2 single-decision shift (11.4 / 13.8 / 9.5 LSB) and the I2 figure (-9 LSB) do not describe the converter | typ / ff 85 / ss -40 | ACCEPTED | SIM | `sim/x2_s1_report.log`, `sim/x2_adc.log` |
| Transfer steps at codes 1536 / 2048 | - | -1.1 / +1.3 LSB typ, -1.1 / +1.55 LSB ff 85 (nominal devices, static: the comparator kick meets the driver on-resistance, the threshold depends on the DAC state) | typ / ff 85 | ACCEPTED (Decision 43b) | SIM | `sim/x2_inl_step.log` |
| INL beyond the fixed offset | <= 1 LSB | 0.63 / 1.99 / 0.61 LSB for inputs below 2.05 V; 2.2 / 5.1 / 0.6 LSB over 1.15-2.15 V | typ / ff 85 / ss -40 | PASS for inputs <= 2.0 V typ / 1.9 V ff 85 (the claim of Decision 43c); ACCEPTED above | SIM | `sim/x2_s1_report.log` |
| kT/C (plate 3.49 pF) | negligible | 34.1 / 37.3 / 30.1 uV = 0.042 / 0.046 / 0.037 LSB | 27 / 85 / -40 C | PASS | SIM | `sim/d2_ktc.log` |
| DAC DNL / INL, A_C 0.5 %*um | \|DNL\| <= 1, INL <= 1 | \|DNL\| > 1 LSB in 4.05 % of chips (1.7 % missing code); INL max 0.99 (2000 runs). With real SAR + supply: 1-3 % / 0-0.95 LSB | typ | ACCEPTED (Decision 40a) | HYBRID | `sim/d2_dnl.log`, `sim/d4_hybrid_dnl.log` |
| DAC settling to 1/2 LSB | < T/2 = 167 ns at 3 MHz | <= 24 ns (Vin <= 2.0 V); 98-103 ns tail at 2.1 V | typ/ff/ss | PASS (tail: see top of range) | SIM | `sim/d2_settle.log`, `sim/d4_settle.log` |
| Sampling-switch nonlinearity | 0.15 LSB | 0.046 / 0.408 / 0.001 LSB | typ / ff / ss | ff ACCEPTED (Decision 40d) | SIM | `sim/d2_samp.log` |
| Top-of-range plate error | within 1 LSB | +1.2 / +3.4 / 0.0 LSB at 2.10 V, +2.1 / +4.4 / +0.15 LSB at 2.15 V (closed loop, real reference); onset near 2.0 V typ, 1.9 V ff 85 (D4b, ideal reference: +4.3 ff 85 / +5.0 ss 125 at 2.15 V) | typ / ff 85 / ss -40 | ACCEPTED (Decision 43c, 0.1 % FS) | SIM | `sim/x2_s1_report.log`, `sim/d4_replay.log` |
| Supply error, stagger, Rd 3 ohm | <= 0.5 LSB | 8 ADC cells on the modelled pad pair (X2 S4): <= 0.11 LSB at typ and ss 125, transition shift <= 0.25 LSB at ff -40 3.6 V (D4 superposition: 0.15-0.28) | typ / ss 125 / ff -40 3.6 V, 3 MHz | PASS (half the margin used at ff -40; pad L / R ASSUMED) | SIM | `sim/x2_s4_summary.log`, `sim/x2_s4_sweep.log`, `sim/d4_supply_3MHz.log` |
| Capture vs reset race | > 0.3 ns | >= 0.8 ns (0.79 ff -40, 1.04 ff 85, 1.14 typ, 1.83 ss 125) | 4 corners | PASS | SIM | NOTES D4 (`d4_race.py` output not saved as a log) |
| T0 vs DAC settling | > 0 | 5.9 ns (ff -40, T0 24.8 ns less 3.78 ns edge), 16.4 (typ), 48 (ss 125) | STA-matched | PASS | SIM + STA | `sim/d4_settle.log`, `sim/d3_taps.log` |
| Settling with real amplifier (A4c) | <= 0.5 LSB | <= 0.086 / 0.114 / 0.070 LSB (57 runs, max 0.114) | typ / ff / ss | PASS | SIM | `sim/d5_settle.log` |
| Input-referred noise 0.5-300 Hz | <= 2 uV (ff 85 C: 2.2 uV, Decision 50) | 20 pF: 1.68 / 1.86 / 1.55 uV; 15 pF (Decision 50): 1.89 / 2.14 / 1.73 uV (fnoicor=1: 4.4-4.9, miss) | typ / ff / ss | PASS typ / ss, ff 85 C accepted miss | ESTIMATE (20 pF) / SIM (15 pF) | `sim/d5_noise.log`, `AFE/layout/baseline/amp_noise.json` |
| SNDR, ADC alone (0.49 V pk) | - | 61.3 / 60.5 / 61.5 dB, ENOB raw 9.89 / 9.75 / 9.93 | typ / ff / ss | - | HYBRID | `sim/d4_hybrid_enob.log` |
| SNDR end-to-end (0.45 V pk, amp noise) | - | 44.7 / 31.7 / 45.6 dB, ENOB raw 7.13 / 4.97 / 7.28; amplifier-noise limited (ff: 2.5 % amp THD). Transistor level (X2 S3, 64 samples, amplifier noise added analytically): 44.4 / 33.9 / 45.5 dB = ENOB referred to full scale 8.96 / 7.23 / 9.15 | typ / ff / ss | INFO | HYBRID; SIM + ESTIMATE | `sim/d5_sndr.log`, `sim/x2_s3_summary.log` |
| Digital area | - | 0.028 mm2 (28,272 um2 Yosys, 1062 cells); die 93,933 um2 at 39 % util.; all 5 STA corners meet setup/hold | 5 libs | PASS | SIM | `sim/d3_signoff_summary.rpt`, `sim/d3_yosys_stat.rpt` |
| Power, whole chip | none stated | record mode 2.09 / 3.26 / 1.37 mW, idle (SCLK stopped) 2.01 / 3.18 / 1.28 mW; 0.63 mA from the pad pair at typ. Amplifiers 1.82 mW typ (87 %). ADC side 0.25 mW typ: 8 vhalf dividers 169 uW, digital macro + routing control 54 uW, DOUT pad 23.5 uW (15 pF ASSUMED), comparators 2.3 uW, DAC 1.9 uW. No power-down. (`../review/AUDIT.md` 4.6 has 2.08 / 3.28 / 1.35 mW with the old ppolyf_u_3k dividers; the D0b figure of 28 uW was the ADC without dividers and with cell-level digital power) | typ / ff 85 / ss -40 | INFO | SIM (static) + ESTIMATE (dynamic) | `../review/sim/f1_power_total.log`, `../review/sim/f1_bias_op.log` |

Note on end-to-end ENOB: NOTES gives raw ENOB 7.13 (typ); with the NOTES FS convention (+1.74 bit) that is about 8.9 bit FS, not 9.1. The 9.1 figure is not in NOTES, so it is not used here.

## Board requirements
| Item | Requirement |
|---|---|
| 3.3 V supply ripple | <= about 1 mV rms (RSS of all bands, uses whole 1.15-2.15 V range); ADC is ratiometric, 0.6 LSB/mV. Use a dedicated low-noise LDO, not a switching rail |
| SCLK | 2 MHz nominal, <= 3 MHz (0.64 MHz min) |
| CS | from an MCU hardware timer, jitter <= 85 ns rms |
| Power-up | host sequence above: RSTN low during the VDD ramp, >= 5 s wait, RST_AMP >= 100 ms, check every channel within 200 LSB of mid-scale |
| Frames to discard | the first frame after any pause (Decision 43d); the frames during and after an amplifier reset (8-28 frames of reset pulse + settling) |
| Host filter | low-pass the codes to 300 Hz for the 2 uV noise figure |
| Protocol | RSTN changes only while CS is high; always 160 clocks per frame; CS never raised early |
| E, IPG, REF | E / IPG signals inside 0..VDD; REF connected |

## IDEAL / ASSUMED / HYBRID / ESTIMATE
| Item | Status |
|---|---|
| MIM matching constant A_C = 0.5 %*um | ASSUMPTION (PDK `mimcap_statistical` is a global skew, gives no ratio error); DNL fails at 1.0 (47 % of chips) |
| Supply L = 2 nH, R = 0.25 ohm | ASSUMED (re-check when package known; R 0.1 ohm needs about 40 ns ring-down) |
| MOS decap density | 3.98 fF/um2 from the PDK model `cap_nmos_03v3` at 3.3 V (4.6 was assumed in D0b-D2): 0.225 nF = 56,500 um2 drawn, 0.057-0.071 mm2 with spacing |
| Latch noise 50 uV | ESTIMATE only, never measured |
| DNL/INL/SNDR | HYBRID Python SAR (D2 network + D1/D2 comparator numbers + D4b supply table); 100 / 20 chips |
| 8-ADC supply currents | D2 / D4: superposition of single-ADC waveforms; X2 S4: full 8-ADC netlist. Digital charge 1.5 pC/ADC/edge is an ESTIMATE and about half of what the hardened macro draws (24 pC per SCLK cycle typ, 27 pC at ff -40 C 3.6 V): L3b repeats S4 with the macro's number |
| SAR controls in D2/D4b/D5 | scripted, not the synthesized logic |

## Open items for L1 / L3
1. DONE in I1: the hardened netlist (`lg/runs/d3`) has `dac_gdn`, the 10-bit config and the word-1 readback. (`spice/dig/` and its SDF are the old XSPICE experiment, not used.) L1d hardens the chip macro `afe_dig` = dbs_ctrl + adc8_top.
2. LibreLane CTS fails (DPL-0036): keep the delay-chain taps out of CTS; SCLK tree must not run through the chain.
3. XSPICE / ivlng unusable in this ngspice-46 build: use the replay method post-layout.
4. Transistor-level amp -> ADC run aborts at t = 28.8 ms with the amplifier attached (4 configurations): try slower switch edges or a series R in the testbench. -> ANSWERED by X2 (NOTES "X2 findings" S2): a tolerance abort (abstol 1e-15 on gate-source branch currents) at a switching event; "28.8 ms" was a log artifact of `cut -c1-300`; use `.options abstol=1e-12` and one ngspice thread per job.
5. Crosstalk of the 0.2-0.36 V amplifier-output kick spike across 8 channels via shared vcm / bias / supply (not simulated). -> X2 S5 (2 channels, typ): the neighbour output moves 0.87 mV for < 0.5 us (through vcm_out / vg2) and <= 0.022 LSB at its next sample.
6. Full 8-ADC transistor-level supply run (D2/D4 superposition unconfirmed). -> X2 S4: done (8 ADC cells, pad L on VDD and VSS): <= 0.11 LSB at typ and ss 125 C, 0.33-0.50 LSB of plate error at ff -40 C 3.6 V (at the limit; an inductance item).
7. Latch noise measurement.
8. Top-of-range plate error (+2.1 / +4.4 LSB at 2.15 V typ / ff 85, accepted by Decision 43c) and bridge-cap / LSB-node parasitics (0.018 LSB DNL per fF; lengthen bridge 0.016 fF per fF) in PEX (L1b).
9. Three supply straps (Decision 44d): pins `vdd` / `vdd_cmp` / `vdd_dac` of the ADC cell; DAC drivers behind the 10 ohm strap resistor + 0.1 nF, comparators + digital macro on the ADC-main strap + 0.125 nF, about 3 ohm in series with each decap (the MOS decap's own channel resistance: about 20 um gate length, ESTIMATE).
10. LVS references of the ADC cell: `../layout/lvs/adc_ch.spice` (written by `../layout/scripts/mk_lvs_netlists.py`; never edit a simulation netlist for LVS). The comparator's two 40 fF preamp capacitors become one 5 x 5 um MIM unit each (54.5 fF): the code offset moves by +1.5 LSB (typ) / +1.9 LSB (ff 85) and the step at code 2048 shrinks from +1.30 to +0.80 LSB (typ), +1.55 to +1.30 LSB (ff 85) (`sim/f1_x2_inl_step.log`, `../NOTES.md` "F1 findings").
11. For post-layout replays: `X2_ADC_INC=<extracted netlist>` makes the X2 scripts use it in place of the design netlists of the ADC cell (`scripts/x2lib.py`).
