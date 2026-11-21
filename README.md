# dbs_afe_top: 8-channel neural recording front end with per-channel 12-bit SAR ADC (GF180MCU, Chipathon 2026, team GAJT)

Brown University ENGN 2912E. Process GF180MCU variant D (gf180mcuD: 5 metals, MIM option B, 3.3 V devices; the routing switches use 5 V devices on 3.3 V).
Status: layout in progress (scaffold written 2026-11-20 by phase LP; L4 replaces every `<L4: ...>` placeholder). Design record: `AFE/NOTES.md` (Decisions 1-47), `AFE/TAPEOUT.md`,
`AFE/adc/README.md` (ADC, SPI frame, every host rule in detail), `AFE/review/AUDIT.md`.
Academic demonstrator: the stimulation path is a bench demonstration (tens of uA), **not for real stimulation or connection to a person**.

| item | value |
|---|---|
| top cell / GDS | `dbs_afe_top` (macro name pending the organizer) / `gds/dbs_afe_top.gds` `<L4: final GDS, sha1>` |
| size | PR boundary 1000 x 1000 um (Decision 45); drawn `<L4: W x H from flow.py info>` |
| pads | 24: 17 analog, 5 digital, VDD, VSS (`info.yaml`) |
| supply | one 3.3 V pad pair (3.0 .. 3.6 V); about 2.0 mW in every mode (`AFE/review/sim/f1_power_total.log`: 2.09 / 3.26 / 1.37 mW typ / ff 85 / ss -40) |
| channels | 8 x (electrode routing switch -> AC-coupled amplifier, 60 dB, 0.2 Hz .. 0.42-1.0 kHz -> 12-bit SAR ADC); all 8 sampled at the same instant |
| output | SPI-like frame of 160 SCLK (2 MHz nominal, 3 MHz max), 4 kS/s per channel set by the host |

## Block diagram
```
 E[k] ──┬── rec TGATE (sw_rec) ──> rec ─[Cin 15 pF]─ OTA1 ─ stage 2 ─ follower ─> out ─> sampling TG ─> split 6+6 MIM DAC ─> cmp_p ─> SAR ─┐
        └── ipg TGATE (sw_ipg) ──> IPG[k]            (feedback Cf, pseudo-resistors, RST_AMP one-shot reset)      vhalf + Cref 7 pF  │   x 8 (k = 0..7)
 REF ───────────────────────────> ref (all 8 amplifiers)                                                                              │
 bias_genc (one, shared): vbn, vcm_in, vg1, vcm_out, vg2, vrs ──> all 8 channels                                                      │
 afe_dig (one hardened macro): dbs_ctrl (routing FSM, EN, MODE, RST_AMP) + adc8_top (SPI frame, 8 SAR logics, staggered comparator clocks) <┘
 CS, SCLK, DIN, RSTN ──> afe_dig ──> DOUT (driven only while CS is low)
```
Floorplan: two rows of four channels, the digital macro between them, the bias cell at the east end (`AFE/layout/SPEC.md`, `AFE/layout/floorplan.json`).

## Pins (pad order clockwise from the NW corner; `info.yaml`)
| pad | type | function |
|---|---|---|
| E[0] .. E[7] | analog | electrode k: to the amplifier (record) or to IPG[k] (stimulate) through 5 V transmission gates; keep inside 0..VDD |
| IPG[0] .. IPG[7] | analog | stimulator input k (bench IPG), connected to E[k] in stimulation mode |
| REF | analog | reference electrode, common to all 8 amplifiers; MUST be connected (to the reference electrode or mid-supply) |
| CS | input (CMOS) | frame select, active low; its falling edge samples all 8 channels |
| SCLK | input (Schmitt) | serial clock, 2 MHz nominal, <= 3 MHz |
| DIN | input (CMOS) | config word 0 = {6 x 0, RST_AMP, MODE, EN[7:0]}, committed at SCLK 33 |
| RSTN | input (Schmitt) | reset, active low, pad pull-down on (an undriven RSTN = reset) |
| DOUT | bidirectional (used as output, 4 mA, fast) | word 1 = read-back of the config, words 2-9 = channel 0..7 `{0, ID[2:0], code[11:0]}` |
| VDD / VSS | power / ground | 3.3 V; dedicated low-noise LDO |

The 15 pad-control pins (`<pad>_PU/_PD`, `DOUT_*`) are constants driven by tie cells inside afe_dig (Decision 46e): all 0 except RSTN_PD = 1; DOUT_OE = ~CS.

## Host rules (Decisions 43d, 44c, 44g; ACCEPT.md section 2; details and reasons in `AFE/adc/README.md`)
Power-up:
1. Hold RSTN low while VDD ramps; release it while CS is high.
2. Wait >= 5 s (the shared bias starts in 3.7 ms typ but 3.6 s at ss -40 C with 8 channels; `AFE/layout/baseline/bias_startup.json`).
3. Config frame with RST_AMP = 1 for >= 100 ms, then RST_AMP = 0.
4. Read for 1 s: every channel within mid-scale +-200 LSB (codes 1848-2248), else repeat step 3.
Recording:
5. After every record start (MODE / EN change) also send RST_AMP = 1 for >= 100 ms, then RST_AMP = 0; discard the frames until the channel is within 1 mV (seconds).
6. Watch the running mean of every channel; when it leaves mid-scale +-200 LSB, repeat RST_AMP (step 5). (LP finding: if the silicon pseudo-resistors behave like the junction-area model, a DC electrode offset makes the output drift by about offset x 1 /s after each reset; ACCEPT.md section 2.)
7. After stimulation, wait >= 0.3 s before recording on that channel (the electrode recovers; `AFE/layout/baseline/top_stim.json`).
Protocol:
8. RSTN changes only while CS is high; every frame has exactly 160 SCLK; never raise CS early; let CS fall >= 100 ns before the first SCLK edge; CS from a hardware timer (jitter <= 85 ns rms).
9. Discard the first frame after any pause. Low-pass the codes to 300 Hz for the noise figure (1.89 / 2.14 / 1.73 uV rms at 27 / 85 / -40 C, Cin 15 pF, Decision 50). There is no power-down.

## Board needs
Dedicated 3.3 V LDO with <= about 1 mV rms ripple (the ADC is ratiometric, 0.6 LSB/mV); MCU with a hardware timer for CS and an SPI master (mode: data out on SCLK falling, sampled on rising); REF connected; E / IPG signals within 0..VDD; one bond wire per supply pad assumed (2 nH; two bond wires per supply pad if offered: ACCEPT.md ladder S-2 `<L4: say whether L3b needed it>`).

## Test plan (first silicon)
1. Supply current at 3.3 V after power-up (expect 0.6 mA typ; `f1_power_total.log`); RSTN / CS / SCLK / DIN / DOUT frame read-back (word 1 = config).
2. Short E[k] and REF to a mid-supply source: every channel near code 2018 (= 2048 + code offset -30 typ); noise of the codes in 0.5-300 Hz (expect <= 2 uV rms at the electrode at 27 C and -40 C, 2.14 uV at 85 C: Cin = 15 pF, Decision 50).
3. Gain and bandwidth: 0.45 mV pk sine from 0.1 Hz to 2 kHz on E[k]: 60 dB, high-pass corner (design 0.25-0.29 Hz at Cin 15 pF), low-pass corner (0.42-1.0 kHz).
4. **Measure first on every channel**: the high-pass corner and the drift after RST_AMP with a known DC offset (10 mV and 100 mV) on E[k]: this decides between the two pseudo-resistor models of ACCEPT.md section 2 and the RST_AMP repeat interval of rule 6.
5. ADC linearity with a slow ramp (amplifier output 1.15-2.0 V): INL <= 1.1 LSB beyond the fixed offset (Decision 43c as restated by REVIEW R9: post-layout 0.95 LSB typ, 1.10 / 1.05 LSB at ff -40 / ss 125, 3.1 LSB at ff 85 C near 2.0 V); crosstalk: one channel driven to full scale, the neighbours quiet.
6. Routing: stimulation mode with a bench IPG (tens of uA) on IPG[k]; record mode afterwards (rule 7).

## Files of the submission
`info.yaml`, `lvs_config.json`, `gds/dbs_afe_top.gds`, `spice/dbs_afe_top.spice` (= `AFE/layout/lvs/dbs_afe_top.spice`, copied by L4), `verilog/gl/afe_dig.v`
(= `AFE/dig/final/afe_dig.pnl.v`, copied by L4), `documents/Export_Control_GF_Rev8.2.docx` (technical answers: `documents/export_control_answers.md`; signature by a person).
Check: `python3 AFE/layout/scripts/check_submission.py` (and `python3 AFE/layout/scripts/gate.py L4`).
