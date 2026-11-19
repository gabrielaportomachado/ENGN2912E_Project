# AFE ADC (8 x 12-bit SAR, one per channel)

Status after D0b-D5. Source of every number: `NOTES.md` (this directory) and `../NOTES.md` Decision 40; logs in `sim/`. Nothing was re-run for this page.

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
```
Comparator reference = VDD/2 tap, inn = plate. Supply: two straps from one pad pair (DAC drivers via ~10 ohm + local decap; comparators and logic on the main rail), about 0.23 nF total.

## Interface
Pins: `CS`, `SCLK`, `DIN`, `DOUT`, `RSTN`. Frame = 160 SCLK = 10 x 16-bit words.

| SCLK | Content |
|---|---|
| 1-16 (word 0) | DIN = {6 x 0, RST_AMP, MODE, EN[7:0]} (RST_AMP added in I0, Decision 38); config commits at SCLK 33 (frames < 33 clocks change nothing); RST_AMP is a level, held until the next config frame or RSTN |
| 1-19 | the 8 conversions, ADC i runs trial k-i at SCLK k (CS falling = simultaneous sample) |
| 17-32 (word 1) | DOUT = held config {6 x 0, RST_AMP, MODE, EN[7:0]} of the PREVIOUS frame (committed at its SCLK 33; 0 after RSTN); DIN ignored |
| 33-160 (words 2-9) | channel 0..7, `{0, ID[2:0], code[11:0]}`, same-frame data |

SCLK 2 MHz nominal, 3 MHz max (0.64 MHz min). T_ACQ = 240-244 us. Input range claimed 1.15-2.15 V.

## How to run (from `AFE/adc/`; scripts need `bash`, not executable)
| Phase | Command |
|---|---|
| D1 | `bash scripts/run_d1.sh <delay\|offset\|noise\|icmr\|conv\|kick\|tbl>` -> `sim/d1_<case>.log` (`NMC=`, `NCYC=` env overrides) |
| D2 cap DAC / switch | `bash scripts/run_d2_conv.sh` (settle, samp, idd npz); `bash scripts/d2_ktc.sh`; `python3 scripts/d2_acweights.py <mode>`; `python3 scripts/d2_dnl.py` |
| D2 supply | `bash scripts/run_d2_supply.sh`, `bash scripts/run_d2_supply3.sh` (stagger) |
| D3 RTL | `bash scripts/run_d3_sim.sh` (Icarus: exhaustive, edge, corner x f matrix) |
| D3 synthesis | `bash scripts/run_d3_synth.sh` (LibreLane in `lg/`; CTS fails, run with `--skip OpenROAD.CTS --skip OpenROAD.ResizerTimingPostCTS`) |
| D3 STA taps | `python3 scripts/d3_taps.py sim/d3_taps.log` (runs `d3_sta.tcl`, 5 corners) |
| D4 settle / race | `python3 scripts/d4_settle.py <corner> <T> <VDD> <vins>`; `python3 scripts/d4_race.py <corner> <T> <VDD> <slew ns> <W ns> [dly]` |
| D4 supply | `python3 scripts/d4_idd.py ...` (currents), `python3 scripts/d4_supply.py 3` -> `sim/d4_supply_3MHz.log` |
| D4 hybrid | `python3 scripts/d4_hybrid.py dnl` / `enob` / `track` |
| D4b replay | `python3 scripts/d4_replay.py <corner> <T> <VDD> <dt_c ns> <W ns> <slew ns> <vins> [T_ns]` -> `sim/d4_replay.log` |
| D5 settling | `bash scripts/run_d5_settle.sh` -> `sim/d5_settle.log` |
| X2 (2026-11-19) | closed-loop PWL replay, one ngspice thread: `python3 scripts/x2_adc.py <corner> <n>` (ADC alone); `python3 scripts/x2_s1.py <typ\|ff85\|ss-40> <TPRE ms> all` then `python3 scripts/x2_s1_report.py`; `python3 scripts/x2_s3.py <corner> <N> <M> <TPRE ms>`; `python3 scripts/x2_s4.py <ff-40\|typ\|ss125> all 3`, `python3 scripts/x2_s4_sweep.py <corner> <case>`; `python3 scripts/x2_s5.py typ`; abort study `bash scripts/run_x2_s2_stats.sh`, `python3 scripts/x2_s2_trace.py`; what-ifs `bash scripts/run_x2_whatif*.sh` |
| D5 SNDR / noise | `python3 scripts/d5_hybrid_amp.py` (hybrid SNDR, `sim/d5_sndr.log`); `python3 scripts/d5_noise.py` (`sim/d5_noise.log`); transistor-level `bash scripts/run_d5_sndr.sh` ABORTS (see open items) |

## Host power-up sequence and test plan (Decisions 38, 41)
1. Hold RSTN LOW while VDD ramps (the chip has no power-on reset: config and routing flops are cleared only by RSTN; the RSTN pad has its pull-down enabled, so an undriven RSTN also means "in reset"). All routing switches stay open, every REC node is parked at VCM_IN.
2. Release RSTN. Wait >= 1 s after VDD is stable (the amplifier master bias needs up to ~0.6 s at ss -40 C).
3. Write a config frame with RST_AMP = 1 (word 0 = 0x0200, MODE = 0, EN = 0); keep it set for >= 100 ms (>= 30 ms needed); write a config frame with RST_AMP = 0.
4. Write the working config (word 0 = {RST_AMP 0, MODE, EN}); read it back in word 1 of the NEXT frame. After a record start each enabled channel takes a reset pulse (about 3.6 ms typ, up to 7 ms) and the amplifier then needs 0.13-0.27 s (1 mV step) to 9 s (100 mV step) to settle: discard those frames.
Pad controls: DOUT drives only while CS is low; RSTN pull-down on; other pad-control names/values are placeholders until checked against the organizer template (L4).

## Results
Corners are typ 27 / ff 85 / ss -40 C unless noted. Types: SIM = transistor/ngspice or Icarus/OpenSTA, HYBRID = Python model fed with SIM numbers, ESTIMATE = hand/analytic.

| Item | Target | Measured | Corner | P/F | Type | Log |
|---|---|---|---|---|---|---|
| Comparator decision time (0.1 mV) | < half cycle | 1.5 / 1.3 / 1.8 ns | typ / ff / ss | PASS | SIM | `sim/d1_delay.log` |
| Comparator offset sigma | <= 2 LSB | 1.27 / 1.31 / 1.23 mV = 1.57 / 1.63 / 1.53 LSB | typ / ff / ss | PASS (code shift) | SIM | `sim/d1_offset.log` |
| Comparator noise (pair) | 0.25 LSB | 118 / 168 / 108 uV = 0.15 / 0.21 / 0.13 LSB | typ / ff / ss | PASS (latch open) | SIM | `sim/d1_noise.log` |
| Fixed evaluate shift | code shift only | 11.4 / 13.8 / 9.5 LSB (D1 fit 12.7-24.4 LSB, upper bound). X2 closed loop: the CODE OFFSET of the converter is -30 / -40 / -22 LSB (typ / ff 85 / ss -40) and the threshold is code dependent (steps -1.1 / +1.3 LSB at codes 1536 / 2048), see NOTES "X2 findings" S1 | typ / ff / ss | ACCEPTED | SIM | `sim/d2_float.log` |
| kT/C (plate 3.49 pF) | negligible | 34.1 / 37.3 / 30.1 uV = 0.042 / 0.046 / 0.037 LSB | 27 / 85 / -40 C | PASS | SIM | `sim/d2_ktc.log` |
| DAC DNL / INL, A_C 0.5 %*um | \|DNL\| <= 1, INL <= 1 | \|DNL\| > 1 LSB in 4.05 % of chips (1.7 % missing code); INL max 0.99 (2000 runs). With real SAR + supply: 1-3 % / 0-0.95 LSB | typ | ACCEPTED (Decision 40a) | HYBRID | `sim/d2_dnl.log`, `sim/d4_hybrid_dnl.log` |
| DAC settling to 1/2 LSB | < T/2 = 167 ns at 3 MHz | <= 24 ns (Vin <= 2.0 V); 98-103 ns tail at 2.1 V | typ/ff/ss | PASS (tail: see top of range) | SIM | `sim/d2_settle.log`, `sim/d4_settle.log` |
| Sampling-switch nonlinearity | 0.15 LSB | 0.046 / 0.408 / 0.001 LSB | typ / ff / ss | ff ACCEPTED (Decision 40d) | SIM | `sim/d2_samp.log` |
| Top-of-range plate error | within 1 LSB | within 1 LSB to 1.9 V; +4.3 (ff 85) / +5.0 (ss 125) LSB at 2.15 V | ff 85 / ss 125 | ACCEPTED (0.1 % FS) | SIM | `sim/d4_replay.log` |
| Supply error, stagger, Rd 3 ohm | <= 0.5 LSB | 0.15 (0.16 at f=1) ff -40; Rd 0.25-10 ohm: 0.18-0.28 (<= 0.50) | ff -40 3.6 V, 3 MHz | PASS | HYBRID (superposed) | `sim/d4_supply_3MHz.log` |
| Capture vs reset race | > 0.3 ns | >= 0.8 ns (0.79 ff -40, 1.04 ff 85, 1.14 typ, 1.83 ss 125) | 4 corners | PASS | SIM | NOTES D4 (`d4_race.py` output not saved as a log) |
| T0 vs DAC settling | > 0 | 5.9 ns (ff -40, T0 24.8 ns less 3.78 ns edge), 16.4 (typ), 48 (ss 125) | STA-matched | PASS | SIM + STA | `sim/d4_settle.log`, `sim/d3_taps.log` |
| Settling with real amplifier (A4c) | <= 0.5 LSB | <= 0.086 / 0.114 / 0.070 LSB (57 runs, max 0.114) | typ / ff / ss | PASS | SIM | `sim/d5_settle.log` |
| Input-referred noise 0.5-300 Hz | <= 2 uV | 1.68 / 1.86 / 1.55 uV (fnoicor=1: 4.4-4.9, miss) | typ / ff / ss | PASS | ESTIMATE | `sim/d5_noise.log` |
| SNDR, ADC alone (0.49 V pk) | - | 61.3 / 60.5 / 61.5 dB, ENOB raw 9.89 / 9.75 / 9.93 | typ / ff / ss | - | HYBRID | `sim/d4_hybrid_enob.log` |
| SNDR end-to-end (0.45 V pk, amp noise) | - | 44.7 / 31.7 / 45.6 dB, ENOB raw 7.13 / 4.97 / 7.28; amplifier-noise limited (ff: 2.5 % amp THD) | typ / ff / ss | INFO | HYBRID | `sim/d5_sndr.log` |
| Digital area | - | 0.028 mm2 (28,272 um2 Yosys, 1062 cells); die 93,933 um2 at 39 % util.; all 5 STA corners meet setup/hold | 5 libs | PASS | SIM | `sim/d3_signoff_summary.rpt`, `sim/d3_yosys_stat.rpt` |
| Power | - | ADC + interface about 28 uW (D0b); comparators +3-4 uW (D1); flow power NOT used | - | - | ESTIMATE | NOTES D0b, D1 |

Note on end-to-end ENOB: NOTES gives raw ENOB 7.13 (typ); with the NOTES FS convention (+1.74 bit) that is about 8.9 bit FS, not 9.1. The 9.1 figure is not in NOTES, so it is not used here.

## Board requirements
| Item | Requirement |
|---|---|
| 3.3 V supply ripple | <= about 1 mV rms (RSS of all bands, uses whole 1.15-2.15 V range); ADC is ratiometric, 0.6 LSB/mV. Use a dedicated low-noise LDO, not a switching rail |
| SCLK | 2 MHz nominal, <= 3 MHz (0.64 MHz min) |
| CS | from an MCU hardware timer, jitter <= 85 ns rms |
| Power-up | discard about 10 frames (ESTIMATE: 4-22 mV left at 240 us for a 1.65 V step) |

## IDEAL / ASSUMED / HYBRID / ESTIMATE
| Item | Status |
|---|---|
| MIM matching constant A_C = 0.5 %*um | ASSUMPTION (PDK `mimcap_statistical` is a global skew, gives no ratio error); DNL fails at 1.0 (47 % of chips) |
| Supply L = 2 nH, R = 0.25 ohm | ASSUMED (re-check when package known; R 0.1 ohm needs about 40 ns ring-down) |
| MOS decap density 4.6 fF/um2 | ESTIMATE, unchecked (0.23 nF = about 0.05 mm2) |
| Latch noise 50 uV | ESTIMATE only, never measured |
| DNL/INL/SNDR | HYBRID Python SAR (D2 network + D1/D2 comparator numbers + D4b supply table); 100 / 20 chips |
| 8-ADC supply currents | superposition of single-ADC transistor waveforms, not a full netlist; digital charge 1.5 pC/ADC/edge ESTIMATE |
| SAR controls in D2/D4b/D5 | scripted, not the synthesized logic |

## Open items for L1 / L3
1. Re-synthesize the netlist with `dac_gdn` (RTL has it, `spice/dig/` netlists and SDF do not); then rerun `scripts/d4_sdf.tcl`, `d4_gen_dig.py`.
2. LibreLane CTS fails (DPL-0036): keep the delay-chain taps out of CTS; SCLK tree must not run through the chain.
3. XSPICE / ivlng unusable in this ngspice-46 build: use the replay method post-layout.
4. Transistor-level amp -> ADC run aborts at t = 28.8 ms with the amplifier attached (4 configurations): try slower switch edges or a series R in the testbench. -> ANSWERED by X2 (NOTES "X2 findings" S2): a tolerance abort (abstol 1e-15 on gate-source branch currents) at a switching event; "28.8 ms" was a log artifact of `cut -c1-300`; use `.options abstol=1e-12` and one ngspice thread per job.
5. Crosstalk of the 0.2-0.36 V amplifier-output kick spike across 8 channels via shared vcm / bias / supply (not simulated). -> X2 S5 (2 channels, typ): the neighbour output moves 0.87 mV for < 0.5 us (through vcm_out / vg2) and <= 0.022 LSB at its next sample.
6. Full 8-ADC transistor-level supply run (D2/D4 superposition unconfirmed). -> X2 S4: done (8 ADC cells, pad L on VDD and VSS): <= 0.11 LSB at typ and ss 125 C, 0.33-0.50 LSB of plate error at ff -40 C 3.6 V (at the limit; an inductance item).
7. Latch noise measurement.
8. Top-of-range plate error (+4-5 LSB at 2.15 V) and bridge-cap / LSB-node parasitics (0.018 LSB DNL per fF; lengthen bridge 0.016 fF per fF) in PEX.
9. Two supply straps: DAC drivers via about 10 ohm + local decap, comparators/logic on the main rail, about 0.23 nF total; about 3 ohm in series with each decap.
