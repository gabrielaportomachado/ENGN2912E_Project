# dbs_afe_top: 4-channel neural recording front end with per-channel 12-bit SAR ADC (GF180MCU, Chipathon 2026, team GAJT)

Brown University ENGN 2912E. Process GF180MCU variant D (gf180mcuD: 5 metals, MIM option B, 3.3 V devices; the routing switches use 5 V devices on 3.3 V).
Status: layout in progress (scaffold written 2026-11-20 by phase LP; L4 replaces every `<L4: ...>` placeholder). Design record: `AFE/NOTES.md` (Decisions 1-54), `AFE/TAPEOUT.md`,
`AFE/adc/SPI_FRAME.md` (the host interface, normative), `AFE/adc/README.md` (ADC, every host rule in detail), `AFE/review/AUDIT.md`. The 8-channel design of earlier versions is the git tag `checkpoint-n8-final`.
Academic demonstrator: the stimulation path is a bench demonstration (tens of uA), **not for real stimulation or connection to a person**.

| item | value |
|---|---|
| top cell / GDS | `dbs_afe_top` (macro name pending the organizer) / `gds/dbs_afe_top.gds` `<L4: final GDS, sha1>` |
| size | outline 605 x 1110 um (Decision 52); drawn `<L4: W x H from flow.py info>` |
| pads | 20: 13 analog (E[3:0], IPG[3:0], REC[3:0], REF), 5 digital, VDD, VSS (`info.yaml`; Decisions 52, 53) |
| supply | one 3.3 V pad pair (3.0 .. 3.6 V); about 1.0 mW in every mode (re-derived for 4 channels from `AFE/review/sim/f1_power_total.log` and `AFE/dig/reports/power_dig.log`, `AFE/TAPEOUT.md`: 1.05 / 1.64 / 0.68 mW typ / ff 85 / ss -40; ESTIMATE, not measured; the 8-channel numbers were 2.09 / 3.26 / 1.37 mW) |
| channels | 4 x (electrode routing switch -> AC-coupled amplifier, 60 dB, 0.2 Hz .. 0.42-1.0 kHz -> 12-bit SAR ADC); all 4 sampled at the same instant |
| output | SPI frame of 80 SCLK = 5 words of 16 bits (config + status word, then 4 x {ID, flags, code}); 2 MHz nominal, 3 MHz max, 4 kS/s per channel set by the host; `AFE/adc/SPI_FRAME.md` (Decision 54) |

## Block diagram
```
 E[k] ──┬── rec TGATE (sw_rec) ──┬─> rec ─[Cin 15 pF]─ OTA1 ─ stage 2 ─ follower ─> out ─> sampling TG ─> split 6+6 MIM DAC ─> cmp_p ─> SAR ─┐
        │                        └─> pad REC[k]  (= the amplifier input, high-impedance probe point)                                       │   x 4 (k = 0..3)
        └── ipg TGATE (sw_ipg) ──> IPG[k]            (feedback Cf, pseudo-resistors, RST_AMP one-shot reset)      vhalf + Cref 7 pF        │
 REF ───────────────────────────> ref (all 4 amplifiers)                                                                                      │
 bias_genc (one, shared): vbn, vcm_in, vg1, vcm_out, vg2, vrs ──> all 4 channels                                                              │
 afe_dig (one hardened macro, 424.48 x 86.24 um): dbs_ctrl #(4) (routing FSM, EN, MODE, RST_AMP) + adc_top #(4) (80-SCLK SPI frame, SAR logics, staggered comparator clocks) <┘
 CS, SCLK, DIN, RSTN ──> afe_dig ──> DOUT (driven only while CS is low)
```
Floorplan: two rows of two channels, the digital macro between them, the bias cell at the east end (`AFE/layout/SPEC.md`, `AFE/layout/floorplan.json`).

## Pins (pad order clockwise from the NW corner; `info.yaml`)
| pad | type | function |
|---|---|---|
| E[0] .. E[3] | analog | electrode k: to the amplifier (record) or to IPG[k] (stimulate) through 5 V transmission gates; keep inside 0..VDD |
| IPG[0] .. IPG[3] | analog | stimulator input k (bench IPG), connected to E[k] in stimulation mode |
| REC[0] .. REC[3] | analog | the amplifier input of channel k (the electrode signal after the record switch, before amplification; Decision 53). **Board rule, PROPOSED (not decided): leave REC open, or use a probe of >= 1 GOhm DC and <= 10 pF; no 10 MOhm scope probe, no AC-coupled probe, no DC source** (AFE/layout/reports/R13.md section 8: a 10 MOhm / 10 pF probe fails the amplifier limits) |
| REF | analog | reference electrode, common to all 4 amplifiers; MUST be connected (to the reference electrode or mid-supply) |
| CS | input (CMOS) | frame select, active low; its falling edge samples all 4 channels |
| SCLK | input (Schmitt) | serial clock, 2 MHz nominal, <= 3 MHz |
| DIN | input (CMOS) | config word 0 = {WR, RST_AMP, MODE, 9 x 0, EN[3:0]}, committed at SCLK 17 only if WR = 1 |
| RSTN | input (Schmitt) | reset, active low, pad pull-down on (an undriven RSTN = reset) |
| DOUT | bidirectional (used as output, 4 mA, fast) | word 0 = status {1010, RST_AMP, MODE, EN[3:0], 0 x 6} (the held config of before the frame), words 1-4 = channel 0..3 `{ID[1:0], 00, code[11:0]}` |
| VDD / VSS | power / ground | 3.3 V; dedicated low-noise LDO |

The 15 pad-control pins (`<pad>_PU/_PD`, `DOUT_*`) are constants driven by tie cells inside afe_dig (Decision 46e): all 0 except RSTN_PD = 1; DOUT_OE = ~CS.

## Host rules (Decisions 43d, 44c, 44g; ACCEPT.md section 2; details and reasons in `AFE/adc/README.md`)
Power-up:
1. Hold RSTN low while VDD ramps; release it while CS is high.
2. Wait >= 5 s (the shared bias starts in 3.7 ms typ but 3.6 s at ss -40 C: `AFE/layout/baseline/bias_startup.json`, an 8-channel-era value that is kept and NOT re-derived for 4 channels; the 4-channel power-up run `top_pwrup8.json` waited 5 s at ss -40 C).
3. Config frame (WR = 1) with RST_AMP = 1 for >= 100 ms, then a config frame with RST_AMP = 0.
4. Read for 1 s and check every channel (host offset rule, Decision 51 addendum, REVIEW R10): a channel within +-300 LSB of mid-scale (codes 1748-2348, about +-242 mV) is accepted and its mean is subtracted in software; outside +-300 LSB, or drifting by more than 20 LSB/s, repeat step 3 (RST_AMP is a config bit written with WR = 1), at most 3 times, then flag the channel.
Recording:
5. After every record start (MODE / EN change) also send RST_AMP = 1 for >= 100 ms, then RST_AMP = 0; discard the frames until the channel is within 1 mV (seconds).
6. The same check runs during recording: watch the running mean of every channel; outside mid-scale +-300 LSB or drifting by more than 20 LSB/s, repeat RST_AMP (step 5; at most 3 times, then flag the channel). (LP finding: if the silicon pseudo-resistors behave like the junction-area model, a DC electrode offset makes the output drift by about offset x 1 /s after each reset; ACCEPT.md section 2.)
7. After stimulation, wait >= 0.3 s before recording on that channel (the electrode recovers; `AFE/layout/baseline/top_stim.json`).
Protocol:
8. RSTN changes only while CS is high; every frame has exactly 80 SCLK (SPI mode 0, <= 3 MHz); check the sync nibble 1010 of the status word and the IDs 0-3 of every frame; send WR = 1 only in a frame that changes the config; never raise CS early; let CS fall >= 100 ns before the first SCLK edge; CS from a hardware timer (jitter <= 85 ns rms).
9. Discard the first frame after any pause. Low-pass the codes to 300 Hz for the noise figure (1.89 / 2.14 / 1.73 uV rms at 27 / 85 / -40 C, Cin 15 pF, Decision 50). There is no power-down.

## Board needs
Dedicated 3.3 V LDO with <= about 1 mV rms ripple (the ADC is ratiometric, 0.6 LSB/mV); MCU with a hardware timer for CS and an SPI master (mode: data out on SCLK falling, sampled on rising); REF connected; E / IPG signals within 0..VDD; REC open or a >= 1 GOhm, <= 10 pF probe only (PROPOSED rule, see Pins); one bond wire per supply pad assumed (2 nH; two bond wires per supply pad if offered: ACCEPT.md ladder S-2 `<L4: say whether L3b needed it>`).

## Test plan (first silicon)
1. Supply current at 3.3 V after power-up (expect about 0.32 mA typ with 4 channels, ESTIMATE, `AFE/TAPEOUT.md`; it was 0.6 mA with 8); RSTN / CS / SCLK / DIN / DOUT frame read-back (status word 0xA000 after reset; after a WR = 1 frame the next status word shows the committed config).
2. Short E[k] and REF to a mid-supply source: every channel near code 2018 (= 2048 + code offset -30 typ); noise of the codes in 0.5-300 Hz (expect <= 2 uV rms at the electrode at 27 C and -40 C, 2.14 uV at 85 C: Cin = 15 pF, Decision 50).
3. Gain and bandwidth: 0.45 mV pk sine from 0.1 Hz to 2 kHz on E[k]: 60 dB, high-pass corner (design 0.25-0.29 Hz at Cin 15 pF), low-pass corner (0.42-1.0 kHz).
4. **Measure first on every channel**: the high-pass corner and the drift after RST_AMP with a known DC offset (10 mV and 100 mV) on E[k]: this decides between the two pseudo-resistor models of ACCEPT.md section 2 and the RST_AMP repeat interval of rule 6.
5. ADC linearity with a slow ramp (amplifier output 1.15-2.0 V): INL <= 1.1 LSB beyond the fixed offset (Decision 43c as restated by REVIEW R9: post-layout 0.95 LSB typ, 1.10 / 1.05 LSB at ff -40 / ss 125, 3.1 LSB at ff 85 C near 2.0 V); crosstalk: one channel driven to full scale, the neighbours quiet.
6. Routing: stimulation mode with a bench IPG (tens of uA) on IPG[k]; record mode afterwards (rule 7).
7. REC[k] (proposed board rule above): with REC open, the codes of the channel are the reference; then a >= 1 GOhm probe on REC[k] must not change gain, noise or the offset after RST_AMP beyond the numbers of AFE/layout/reports/R13.md; do not connect a 10 MOhm probe.

## Files of the submission
`info.yaml`, `lvs_config.json`, `gds/dbs_afe_top.gds`, `spice/dbs_afe_top.spice` (= `AFE/layout/lvs/dbs_afe_top.spice`, copied by L4), `verilog/gl/afe_dig.v`
(= `AFE/dig/final/afe_dig.pnl.v`, copied by L4), `documents/Export_Control_GF_Rev8.2.docx` (technical answers: `documents/export_control_answers.md`; signature by a person).
Check: `python3 AFE/layout/scripts/check_submission.py` (and `python3 AFE/layout/scripts/gate.py L4`).
