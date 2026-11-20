# Pre-layout design audit (2026-11-20)

Auditor: Claude Fable 5.2, max effort, fresh session. Repo at 24e6141 (= origin/main). No design file was changed. Everything new is under `AFE/review/`
(`scripts/`, `tb/`, `sim/`). Source tags: [log] = saved log, [file:line], [calc script], ESTIMATE, ASSUMED, ORGANIZER (public organizer files fetched today, copies in `sim/organizer/`).

## 1. Executive summary

- **Layout: GO WITH CONDITIONS.** L2a (amplifier cell) and L1d (digital macro) can continue. L1a must not draw the VDD/2 divider, and nobody should draw the bias ladders, before issue B1 is decided. L3a cannot start before B2 and B3.
- **Tapeout 2026-11-25: AT RISK, GO only if B1-B3 are closed by 11-22.** No analog GDS exists yet and the organizer's macro name, DEF and slot are still unknown.
- **Biggest risks:** (1) schedule and organizer inputs (B3); (2) two process-option mismatches found today: the 3 kOhm/sq poly resistor used in 22 places does not exist in gf180mcuD (B1), and the native-Vt follower device is unconfirmed (M7); (3) the amplifier's DC state is held by fA-level leakage that only the model defines: bistable stage 1, power-up needs a host reset, and the shared bias needs 3.6 s to start at ss -40 C with 8 channels (M1).
- **Area: FITS.** 0.86 mm2 (929 x 929 um) = 70 % of the ASSUMED 1110 x 1110 um slot, 30 % margin (20 % with a 1.5x overhead) [sim/area.log].
- **Power: OK, no target exists.** 2.08 mW typ in record mode (2.00 mW static; 3.28 mW ff 85 C, 1.35 mW ss -40 C), 0.63 mA from one pad pair [sim/power_total.log].
- **Timing / synchrony: PASS at all five matched corners at 2 and 3 MHz**, RTL and gate level (72 testbench runs, 202 assertions in each main run). Tightest numbers: 22.4 ns between the last comparator window and the next SCLK edge (ss 125 C 3.0 V, 3 MHz); 6.8 ns of DAC-settling margin (ff -40 C 3.6 V) [sim/tb_audit_summary.log]. One uncorrelated corner (slow 3.3 V devices with fast standard cells) misses by 2 ns = 0.65 LSB on the MSB trial (M4).
- **Noise: PASS.** 1.71 / 1.89 / 1.59 uV in 0.5-300 Hz at the electrode including aliasing, switch resistance and the ADC (limit 2.0); 2.04 / 2.23 / 1.92 uV if the host does not low-pass [sim/freq_noise.log]. ENOB referred to full scale 8.9 / 6.7 / 9.0 bit (amplifier limited).
- Connectivity check: 105 scripted checks, 13 mismatches (all in the issue list) [sim/xcheck.log]. Single clock domain (SCLK), no crossing. The sample rate is set only by the host.

## 2. Issue list

Severity: BLOCKER = chip will not work or cannot be submitted; MAJOR = spec or robustness miss that a decision should accept or fix; MINOR = documentation or consistency; INFO.
"Before layout" = must be settled before the named layout phase continues.

| id | sev | step | what | evidence | consequence | proposed fix | h | who | before layout |
|---|---|---|---|---|---|---|---|---|---|
| B1 | BLOCKER | 3, 9 | `ppolyf_u_3k` is used for the 6 bias-ladder resistors and the 2 x 8 vhalf resistors, but gf180mcuD has only the 1 kOhm/sq high-resistance poly | [AFE/amp/spice/bias_genc.spice:19-21,29-31], [AFE/adc/spice/vhalf.spice:9-10]; KLayout LVS variant D sets poly_res = 1k [libs.tech/klayout/tech/lvs/run_lvs.py:219-224, rule_decks/res_extraction.lvs:180-186]; netgen and Magic know only ppolyf_u_1k [netgen/gf180mcuD_setup.tcl:40, magic/gf180mcuD.tech:4156]; ORGANIZER table "Resistor HRES 1k (ppolyf_u_1k)" | LVS cannot match. Drawn with the 3k dimensions the silicon value is 1/3: ratios hold, static current +111 uA (+0.37 mW) [sim/power_op.log] | P-A1: switch to ppolyf_u_1k, either 3x the squares (same R, +0.004 mm2) or the same squares (R/3). Then re-run the bias .op and one ADC replay | 1 | user decides, agent edits | YES: L1a (vhalf), L3a (bias) |
| B2 | BLOCKER | 3 | The top has port `DOUT`; the organizer template requires `<name>_OUT` (to pad A) and `<name>_IN` (from pad Y) for a bidirectional pad | [AFE/top/dbs_afe_top.v:15]; ORGANIZER [sim/organizer/template_info.yaml:42-45]; [sim/xcheck.log C9] | the organizer's pad-frame generation cannot connect DOUT | P-A2: rename to `DOUT_OUT`, add an unused input `DOUT_IN`; keep the 8 control pins | 0.5 | agent | YES: L3a |
| B3 | BLOCKER | 5, 9 | Organizer inputs still missing 5 days before the date: macro name, DEF / pin positions, slot size, pad allocation for 32 pads, number of supply pads | [AFE/TAPEOUT.md:100,163], [AFE/layout/PLAN.md:85]; ORGANIZER README states a 2040 x 2040 um design area, not 2235 | L3a cannot place pins; the 1110 x 1110 um slot and "one pad pair" are assumptions | user asks the organizer today (question list in P-A9) | - | user, organizer | YES: L3a, L4 |
| M1 | MAJOR | 4, 8 | The shared bias starts 6x slower with 8 channels on `vbn`: 3.6 s at ss -40 C (0.6 s with one channel, which is the basis of "wait >= 1 s"); 23 s at ss -40 C 3.0 V | [sim/bias_startup.log]; Decision 38a, [AFE/adc/README.md:49] | at the cold slow corner the documented sequence fires RST_AMP before the bias is up: all amplifiers stay latched until RST_AMP is repeated | P-A3: README / L4 text: wait >= 5 s, then RST_AMP, then check that all codes are within +-200 LSB of mid-scale, else repeat | 0.3 | agent | no |
| M2 | MAJOR | 3, 9 | The supply network of Decision 40e / 43f (two straps, ~10 ohm, 0.125 + 0.1 nF, ~3 ohm ESR) exists only in prose and in a testbench script; the top netlist has one VDD net and no decap; PLAN section 5 and L3a say three straps, Decision 40e and L1a say two; `afe_ch` has one `vdd` pin | [AFE/top/dbs_afe_top.v:18,51], [AFE/adc/scripts/x2lib.py:179-191], [AFE/layout/PLAN.md:59], [AFE/prompts/layout_run.md:54,85] | each layout session must guess the rail of every block; LVS reference has no decap devices | P-A4: freeze the rail table of 4.9.2, add pins `vdd_cmp` and `vdd_dac` to the ADC cell and `afe_ch`, add decap and the strap resistor to the LVS top netlist | 1.5 | agent | YES: L1a pins |
| M3 | MAJOR | 3, 9 | The netlists that serve as LVS reference contain ideal elements and one unrealisable device: `Rbrk` 100 ohm in series with each OTA input, `Rt` / `Rmm` 10 TOhm, 14 x 2 fF `Cpb*` / `Cpm`, and 2 x 40 fF ideal `Cxa` in the comparator (40 fF is below the smallest legal MIM, 54.5 fF) | [AFE/amp/spice/stage1c.spice:11, stage2c.spice:10, fs_oneshot_c.spice:18-19], [AFE/adc/spice/dac_sw.spice:29-42, comparator.spice:14-15]; [sim/xcheck.log C12] | LVS mismatch in L2a and L1a; the comparator capacitor has no layout definition | P-A5: one script writes the LVS netlists (rules in 4.9.3); `Cxa` = one 5 x 5 um MIM unit (checked: decision time +0.05 ns, code +1..2 LSB) [sim/mixcorner.log] | 1 | agent | YES: L2a, L1a LVS |
| M4 | MAJOR | 4 | With slow 3.3 V devices and the fastest standard cells (-40 C, 3.6 V) the comparator fires 21.9 ns after the DAC edge but the MSB trial needs about 24 ns: 0.65 LSB unsettled (0.41 LSB on the next bit) for every input | [sim/mixcorner.log ss-40x], [sim/tb_audit_summary.log *_MIXED: T2.settle FAIL] | a static step of up to 0.65 LSB at the major carries on such a die; same class and size as the steps accepted in Decision 43b | P-A6: accept, or retune the chain in L1d (T0 +4 dlyd, Delta 4 -> 3 dlyd) and re-run X2 S4 at ff -40 C | 0 or 3 | user decides | L1d if retuned |
| M5 | MAJOR | 4 | RSTN released or pulsed while CS is low restarts the frame counter in mid-frame: the 16 DIN bits that follow the release are taken as word 0 and committed 33 edges later (testbench: host sent 0x1FF, the chip committed RST_AMP = 1, MODE = 1, EN = 0x4C) | [sim/tb_audit_*_main.log X5.word0, X5.after33d]; [AFE/adc/rtl/adc8_top.v:33,49-54] | a wrong routing state (record, stimulate or amplifier reset on arbitrary channels) until the next complete frame (250 us) after a badly timed reset | P-A7: README rule "change RSTN only while CS is high; send only 160-clock frames; never raise CS early" | 0.2 | agent | no |
| M6 | MAJOR | 4, 9 | The digital macro is not sign-off clean: CTS fails (DPL-0036), the flow skipped KLayout DRC (runset unset), 16 max-slew and 3 max-cap violations on the unbuffered SCLK net; `afe_dig` does not exist yet | [AFE/adc/lg/runs/d3/warning.log], [final/metrics.json], [AFE/adc/NOTES.md:144] | L1d may not converge in its 2 h box; an unverified macro in the top | P-A8: fallback = no CTS + one hand-placed clock buffer, chain taken from the SCLK root; KLayout DRC variant D on the macro; re-check the table of 4.3 after P&R | 2-4 | agent (L1d) | L1d |
| M7 | MAJOR | 8 | The follower is the native-Vt 6 V NMOS `nfet_06v0_nvt`; the organizer checklist lists native-Vt as an optional module and their process table does not mention it | [AFE/amp/spice/ota2.spice:14]; ORGANIZER [gf180mcu_tapeout_checklist.md section 1] | if the option is not offered the output clips at 1.94 V (A4b) and the amplifier needs a redesign | ask the organizer today (P-A9) | - | user, organizer | L2a (follower) |
| m1 | MINOR | 1 | Statements that still carry superseded numbers or rules (list in 4.1.3): e.g. NOTES Environment "always pipe ngspice through cut" against Decision 43a; TAPEOUT.md N = 4, mux, 5 V domain, 0.72 nF; README power 28 uW, "wait >= 1 s" | 4.1.3 | a new session follows the wrong rule | one clean-up commit by the monitoring session | 1 | monitoring session | no |
| m2 | MINOR | 4 | `AFE/adc/sim/d3_taps.log` predates the hardened netlist by 7 hours; the values differ by 0.2-0.6 ns | file times; [sim/sta_audit.log] | none (all margins hold) | cite sim/sta_audit.log from now on | 0 | - | no |
| m3 | MINOR | 4 | Gate-level simulation shows short crowbar overlaps at the DAC driver gates (PMOS and NMOS of one bit both on): about 6000 per run, longest 0.06-0.21 ns; D2-X2 assumed 0.3 ns break-before-make | [sim/tb_audit_summary.log crowb column] | <= 0.2 pC extra supply charge per edge at the DAC edge, not at a decision | add to L1b (4.9.4) | 0.5 | agent (L1b) | no |
| m4 | MINOR | 4 | On an aborted frame (CS raised during a conversion) the sampling switch closes 2.4-5.6 ns before the drivers release; the RTL comment says it cannot | [sim/sta_audit.log section 4], [AFE/adc/rtl/adc8_top.v:100] | a short kick on the amplifier output on host errors only | README: do not abort frames | 0 | - | no |
| m5 | MINOR | 2, 7 | Without a host low-pass the code stream carries 2.04 / 2.23 / 1.92 uV; the 2 uV target is met only in 0.5-300 Hz | [sim/freq_noise.log] | a user who reads raw codes sees > 2 uV at typ and ff | README sentence | 0.1 | agent | no |
| m6 | MINOR | 5, 6 | MOS decap density is 3.98 fF/um2 in the PDK model, not the 4.6 assumed; the X2 S4 digital charge (1.5 pC per ADC per edge, 12 pC at most) is about half of what the hardened macro draws (24 pC per SCLK cycle typ, 27 pC ff -40 C) | [sm141064.ngspice:39263-39268], [lg/runs/d3/53-openroad-stapostpnr/*/power.rpt] | decap 0.057-0.071 mm2 instead of 0.049; S4 margin at ff -40 C (half used) is a little optimistic | L3b uses the macro's charge (4.9.4) | 0 | agent (L3b) | no |
| m7 | MINOR | 9 | Decision 42a says Cref = 128 x 5 x 5 um units, the netlist has one 59.07 um plate; Cin is one 100.01 um plate (> 10,000 um2) | [AFE/adc/spice/vhalf.spice:23], [AFE/amp/spice/stage1c.spice:14-15], [sim/area.log] | LVS property mismatch unless stated | Cref as ONE plate (saves 0.018 mm2), Cin as 2 pieces; say so in L1a / L2a | 0 | agent | L1a, L2a |
| m8 | MINOR | 8 | Open items that no layout prompt covers: replica / mirror mismatch of the reset level, latch noise, fs/sf and Monte Carlo of the Cref switch, 9-PVT reset tables, xschem update | Decisions 38b, 40b, 42d against layout_run.md | stay unverified at tapeout | accept as documented, or add the sentences of 4.9.4 | 0 | user | no |
| i1 | INFO | 4 | One clock domain: every flop is clocked by SCLK (the capture flops by a delayed copy). The routing FSM only moves while SCLK runs; nothing needs a free-running clock | [AFE/top/dbs_afe_top.v:30,36], [rtl/dbs.v:13,51] | - | - | - | - | - |
| i2 | INFO | 4 | 4 kS/s is enforced only by the host's CS timer; the chip accepts up to 12.4 kS/s (2 MHz) or about 18.5 kS/s (3 MHz) back to back | [sim/tb_audit X4] | - | - | - | - | - |
| i3 | INFO | 6 | There is no power-down: EN only gates the routing switches; 2.0 mW flows in every mode | [rtl/dbs.v:67-68], [sim/power_op.log] | - | - | - | - | - |
| i4 | INFO | 8 | TGATE at 3.3 V: Ron 4-21 kOhm typ over 0-3.3 V (34 kOhm ss -40 C; 65 kOhm at 3.0 V); signals must stay inside 0..VDD | [sim/tgate_ron.log] | stimulation path is a bench demonstration only (tens of uA) | README sentence | - | - | - |

## 3. Proposed decisions for the user (not written as Decisions)

- **P-A1 (B1).** Replace `ppolyf_u_3k` by `ppolyf_u_1k` in `bias_genc.spice` and `vhalf.spice`. Recommended: keep the resistance (3x the squares: ladders 2 x 1650 um, vhalf 2 x 250 um per ADC at 1 um width). It leaves every simulated number valid (taps move < 0.5 mV, currents unchanged [sim/power_op.log, variant 1k_3L]) and costs about 0.004 mm2 for the ladders and 560 um2 per ADC. The alternative (same squares, R/3) costs no area but +0.37 mW and needs an ADC replay with the 83 kOhm divider.
- **P-A2 (B2).** Top-level ports `DOUT_OUT` (was `DOUT`) and `DOUT_IN` (new, unused input). Update info.yaml line 20 (stale "tie DOUT_OE=1").
- **P-A3 (M1).** Host power-up text: RSTN low during the VDD ramp; release RSTN while CS is high; wait >= 5 s (>= 30 s only if the board runs below 3.1 V at -40 C); RST_AMP = 1 for >= 100 ms; RST_AMP = 0; read frames; if any channel is more than 200 LSB away from mid-scale after 1 s, repeat RST_AMP. No circuit change.
- **P-A4 (M2).** Adopt the rail table of section 4.9.2: three straps from the one pad pair (analog: amplifiers, bias, vhalf, Cref switch; ADC-main: comparators and the digital macro; ADC-DAC: bottom-plate drivers through about 10 ohm), new pins `vdd_cmp` and `vdd_dac` on the ADC cell and on `afe_ch`.
- **P-A5 (M3).** Adopt the LVS-netlist rules of section 4.9.3, with the comparator preamp capacitor as one 5 x 5 um MIM unit (54.5 fF) per node.
- **P-A6 (M4).** Accept the mixed-corner 0.65 LSB as documented (recommended: it is a static error of the size already accepted in Decision 43b, and a retune needs the 8-ADC supply run again), or retune in L1d.
- **P-A7 (M5).** README protocol rules: RSTN changes only while CS is high; frames are always 160 clocks; the host does not raise CS early; SCLK may run while CS is high.
- **P-A8 (M6).** L1d fallback and checks as in section 4.9.4, edit 7.
- **P-A9 (B3, M7).** Questions for the organizer, today: (1) macro name and DEF; (2) slot size and shape (1110 x 1110 um assumed; your README says 2040 x 2040 um for all); (3) may we have 32 pads (25 analog, 2 input_cmos, 2 input_schmitt, 1 bidirectional, 1 power, 1 ground), and where do they land relative to the slot; (4) is the VDD / VSS pair ours alone (the template says further power / ground cells break the I/O rails) and can it be double bonded; (5) is the native-Vt NMOS `nfet_06v0_nvt` allowed; (6) confirm high-resistance poly = 1 kOhm/sq only; (7) the package / bond-wire inductance to assume.
- **P-A10 (m7).** Cref is one MIM plate (as in the netlist), not 128 units.

## 4. Per-step results

### 4.1 Step 1: decision ledger

Status: A = active, S(n) = superseded by Decision n, P = partly superseded. "Who" = who set the target: U = user, M = monitoring session, G = agent (rule 10).
"Implemented" names the file and line that carries the decision today.

#### 4.1.1 Ledger

| # | content | status | implemented where | evidence | consistent with later findings? | who |
|---|---|---|---|---|---|---|
| 1 | gain 60 +-1 dB, f_lo <= 0.5 Hz, f_hi >= 300 Hz, noise <= 2 uV in 0.5-300 Hz | A | afe_chc + afe_params (CIN_RATIO 100 [afe_params.spice:33], CIN2 / CF2V [28-29]) | [amp/sim/a4c_ac.log], [a4c_noise.log], [review/sim/freq_noise.log] | yes | U |
| 2 | HPF corner may go below 0.5 Hz | A | pseudo-R on the model floor, f_lo 0.20-0.24 Hz | [a4c_ac.log] | yes; cost is the recovery time (Decision 38) | U |
| 3 | A4 must include an output buffer | A | native-Vt follower [ota2.spice:14-15] | [a4b_follower.log] | yes; device availability open (M7) | U |
| 4 | 2 uV applies at typical flicker; report fnoicor = 1 | A | testbench parameter FN | [a4c_noise.log]: 4.72 / 4.93 / 4.39 uV at fnoicor = 1 | yes (documented risk) | U |
| 5 | A3 sizing start (pair 16 x 50u/2u, load 50u/16u) | A | [ota1_params.spice:5-18] | [a3_summary.txt] | yes | U |
| 6 | find the HPF corner that keeps pseudo-R noise in budget | A (answered in A2) | VTT 0.2 V [afe_params.spice:7] | [a2_summary.txt] | yes | U |
| 7 | pseudo-R value not trusted: sweep 0.5-50 TOhm | A | reports only | [a3_summary.txt section 5] | yes; the floor is still unexplained (risk R1) | U |
| 8 | noise sims use an IDEAL resistor of the same value | A | RMODE = 1 in the noise testbench [stage1c.spice:3,22-24] | [a4c_noise.log] | yes | U |
| 9 | vt shift may be ideal in A3, real in A4 | A | ladder taps vg1 / vg2 [bias_genc.spice:19-20,29-30] | [a4a_prfg.csv] | yes, but the ladder device is not available (B1) | U |
| 10 | fnoicor = 1 noise accepted as a risk | A | - | [a4c_noise.log] | yes | U |
| 11 | keep the m = 2 NMOS load | A | [ota1_params.spice:15] | [a3_summary.txt] | yes | U |
| 12 | stage-2 input C <= 5 pF; fast-settle required; real bias | P: fast-settle switch S(36) | CIN2 3 pF [afe_params.spice:28] | [a4b_loop.log] | yes | U |
| 13 | fix the zeroed diffusion parameters | A (answered) | DIFF = 1 [ota1_params.spice:22] | [a4a_diff_summary.txt] | yes; NOTES Environment line 29 still says the old workaround (m1) | U |
| 14 | A4 split into A4a / A4b | A (process) | - | - | - | U |
| 15 | the ADC is designed in this project | A | AFE/adc | - | yes | U |
| 16 | 4 kS/s per channel, 16 channels | P: 16 -> 8 by 29 | host timer only (i2) | [review/sim/tb_audit: T_ACQ] | rate is not enforced on chip | U |
| 17 | VREF = VDD, mid-scale 1.65 V; budget VDD noise | A | VOCM, VCM_IN [afe_params.spice:5-6]; DAC drivers to vdd [dac_sw.spice:14] | [a4b_psrrpath.log], [adc/sim/d4_hybrid_track.log] | yes; board ripple <= 1 mV rms is a host requirement | U |
| 18 | SPI with external master, 16-bit word, no DIN | P: DIN by 32, frame by 37 | [adc8_top.v:60-85] | [adc/sim/d3_exh_tt_2MHz.log] | yes | U |
| 19 | one SAR + 16:1 mux (D0 outcome) | S(34) | - | - | - | G, then U |
| 20 | transmission-gate fast-settle switch | S(36) | removed (afe_chc has gate muxes) | [a4b_fscharge.log] | - | U |
| 21 | (a) bias start-up from a VDD ramp, (b) loop PM with real stage 2, (c) supply gain | A | (a) 3-diode start-up [bias_genc.spice:15-17]; (c) VCM_IN = 1.65 V | [a4b_pwrup.log], [a4b_loop.log], [a4b_psrrpath.log] | (a) NO: measured with one channel; with 8 channels 3.6 s at ss -40 C [review/sim/bias_startup.log] (M1) | U |
| 22 | weak anti-aliasing handed to the ADC; D0: no oversampling | A | - | [adc/sim/d0_estimates.log] | numbers moved: see 23 | U / G |
| 23 | interferer attenuation 13-20 dB at 3.7 kHz is a documented risk | A | - | [review/sim/freq_noise.log]: 11.7 (ff 85) / 15.2 / 18.9 dB today (f_hi rose from 867 to 998 Hz in A4b) | number stale by 1.3 dB; decision stands | U |
| 24 | SCLK >= 3.5 MHz, T_ACQ >= 11.05 us | S(37, 40c) | - | - | contradicts 40c (max 3 MHz) unless read in order | U |
| 25 | find the minimum legal MIM | A (answered by 39) | 5 x 5 um units [dac_units.spice] | [layout/PLAN.md:11] | yes; the comparator's 40 fF ideal C is below it (M3) | U |
| 26 | own MIM mismatch model, A_C 0.25-1 %*um | A | [adc/scripts/d2_dnl.py] | [adc/sim/d2_dnl.log] | A_C is still an assumption | U |
| 27 | DAC charge draw is a board / bond-wire risk | P: numbers by 37, 40e, 43f | - | [adc/sim/x2_s4_summary.log] | yes | U |
| 28 | no 4 mW sink; reset C_s to 1.65 V; ff 85 C swing miss accepted | P: reset removed by 37 | BM_KSF 6 [afe_params.spice:15] | [a4b_adc245.log], [a4c_thd.log] | yes | U |
| 29 | N = 8 channels | A | N = 8 [dbs_afe_top.v:36,45] | [sim/xcheck.log C5] | yes; TAPEOUT.md still opens with N = 4 (m1) | U |
| 30 | single 3.3 V supply; verify TGATE and FSM at 3.3 V | A | one VDD port [dbs_afe_top.v:18] | TGATE: [a4b_tg33_ron.log] (1.15-2.15 V) and [review/sim/tgate_ron.log] (0-VDD); FSM: 3.3 V libraries in [lg/config.json] | open part: dbs_ctrl is not hardened at 3.3 V yet (L1d) | U |
| 31 | planning frame 2235 um core, ~29 pads | A (assumption) | - | ORGANIZER README: 2040 x 2040 um; fork: 2051 | NO: 2235 has no source in the organizer files (B3) | U |
| 32 | serial config on DIN, 9-bit shift register in a new wrapper, 24 pads | P: 10 bits by 38, pads by 35 / 41 | 10-bit `cfg_sr` inside adc8_top, not a wrapper [adc8_top.v:48-57] | [adc/sim/d3_edge.log] | implemented differently from the text (no separate wrapper); harmless | U |
| 33 | ADC sessions write to AFE/adc/NOTES.md | A (process) | - | - | - | U |
| 34 | one SAR per channel, simultaneous sampling | A | [adc8_top.v:98-99] (rst_sw = cs_n OR done) | channel spread <= 0.075 ns [review/sim/tb_audit_summary.log] | yes | U (group) |
| 35 | READY tied high; REC pads; 31 pads | P: 32 pads by 41 | `.ready(1'b1)` [dbs_afe_top.v:36]; REC ports [12] | [sim/xcheck.log C11] | yes | U |
| 36 | gate-switched pseudo-R reset + REC park | A | [afe_chc.spice:9-15], [bias_genc.spice:25-27], [fs_oneshot_c.spice] | [a4c_rec.log], [a4c_tg.log] | yes | U |
| 37 | staggered conversions, 160-clock frame, word 1 readback, dbs clocked by SCLK, no 1.65 V reset | P: numbers by 38-40 | [adc_sar_ch.v:31-53], [adc8_top.v:36-45,60-85], [dbs_afe_top.v:36] | [review/sim/tb_audit_*] | text says "7-flop token chain", the RTL decodes one counter (`tok`): harmless. "L0/L3 must check nothing needs a free-running clock": no prompt asks; checked here (i1) | U |
| 38 | A4c accepted; (a) RST_AMP bit, held >= 100 ms, issued >= 1 s after VDD; (b) 100 mV recovery 7-9 s accepted | A | bit 9 [adc8_top.v:55]; OR2 [dbs_afe_top.v:73] | [top/sim/i0_top.log], [a4c_pur.log] | (a) "1 s" is wrong for 8 channels (M1). (b) open items (replica mismatch, 9-PVT tables, TGATE + one-shot in one netlist, xschem) are not in any prompt except park injection (m8) | U |
| 39 | MIM minimum 25 um2, m4m5 MIM, split 6+6 with 5 x 5 um units | A | [dac_units.spice] 127 units + bridge 5 x 5.083 + dummy | [layout/PLAN.md:11-17]; model m4m5 = m2m3 [sm141064_mim.ngspice:68-73, 252-257] | yes | U |
| 40a | keep 6+6, A_C 0.5 planning, accept DNL > 1 in ~4 % | A | - | [adc/sim/d2_dnl.log] | yes | U on M |
| 40b | cmp_p as built; evaluate shift +12.7..+24.4 LSB | P: offset numbers S(43e) | [comparator_params.spice:2-18] | [adc/sim/x2_s1_report.log] | corrected by 43e; latch noise never measured (m8) | U on M |
| 40c | SCLK max 3 MHz, nominal 2 MHz | A | chain parameters [adc_clkgen.v:7-9]; SDC 500 ns [lg/config.json] | [review/sim/sta_audit.log]: 23.1 ns left at ss 125 C | yes | U on M |
| 40d | sampling-switch nonlinearity at ff 85 C accepted; range 1.15-2.15 V | P: INL claim narrowed by 43c | - | [adc/sim/d2_samp.log] | README still says "input range claimed 1.15-2.15 V" (m1) | U on M |
| 40e | two straps, staggered comparator clocks, 0.23 nF | A (not in a netlist) | chain in RTL; straps and decap nowhere (M2) | [adc/sim/x2_s4_summary.log] | PLAN section 5 and L3a say three straps; density 3.98 not 4.6 fF/um2 (m6) | U on M |
| 41a | REF pad, 32 pads | A | [dbs_afe_top.v:13,51] | [sim/xcheck.log C7] | subject to allocation (B3) | U |
| 41b | per-ADC vhalf divider; 0.1 LSB targets | A (targets missed, answered by 42) | [vhalf.spice:8-12], [dbs_afe_top.v:90] | [adc/sim/i1_vhalf.log] | resistor type not available (B1) | M (targets) |
| 41c | word 1 = config readback | A | [adc8_top.v:63,71] | [review/sim/tb_audit check_data] | yes | U |
| 41d | dout_oe = ~cs_n; pad-control names until L4 | A | [adc8_top.v:85], [dbs_afe_top.v:22-24] | [sim/xcheck.log C9] | names checked today: control pins match, `DOUT` itself does not (B2) | U |
| 41e | RSTN pull-down | A | RSTN_PD = 1 [dbs_afe_top.v:24] | [sim/xcheck.log C9] | yes | U |
| 42a | sampled floating reference Cref 7 pF "128 units" | A | one MIM [vhalf.spice:23], [dbs_afe_top.v:105] | [adc/sim/i2_summary.txt] | netlist is one plate, text says 128 units (m7) | U on M |
| 42b | vhalf 2 x 250 kOhm ppolyf_u_3k + 1 pF | A | [vhalf.spice:6,9-10] | [review/sim/power_op.log]: 6.31 uA | B1 | U on M |
| 42c | threshold error <= 0.47 LSB, offset -7.6..-12.4 LSB | P: offset S(43e) | - | [adc/sim/i2_summary.txt] | corrected by 43e | U on M |
| 42d | open: ff -40 margin after PEX, 3072 transition, fs/sf, Monte Carlo, 8-ADC supply | A (open) | L1b covers PEX and 3072; X2 S4 covers supply | - | fs/sf and Monte Carlo of the Cref switch are in no prompt (m8); fs/sf timing checked here [mixcorner.log] | M |
| 43a | simulation rules (abstol 1e-12, 1 thread, no cut, pad C, retry) | A | layout_run.md rule 8; x2lib | [adc/sim/x2_s2_repro.log] | `adc/scripts/dgrun.sh:18` and `amp/scripts/run_a4a.sh:68` still pipe through `cut`; NOTES Environment line 32 still says to (m1) | U on M |
| 43b | driver resize not taken; steps -1.1 / +1.3 LSB accepted | A | DSW_WN 1u, DSW_WP 2u [dac_sw.spice:6-7] | [adc/sim/x2_inl_step.log] | yes | U on M |
| 43c | INL claim 1.15-2.0 V typ / 1.9 V ff 85 | A | - | [adc/sim/x2_s1_report.log]; settling tail confirmed [review/sim/mixcorner.log] | yes | U on M |
| 43d | host discards the first frame after a pause | A | README | [adc/sim/x2_adc.log] | README says "about 10 frames" at power-up; the "first frame after any pause" sentence is missing (m1) | U on M |
| 43e | code offset -30 / -40 / -22 LSB | A | - | reproduced: -29..-33 typ [review/sim/mixcorner.log tt27m] | yes | U on M |
| 43f | 8-ADC supply PASS; double bonding optional | A | - | [adc/sim/x2_s4_sweep.log] | digital charge under-estimated about 2x (m6) | U on M |

#### 4.1.2 Contradicting or differently implemented decisions

1. **24 vs 40c**: "SCLK >= 3.5 MHz" against "maximum 3 MHz". Resolved only through the text of 37; Decision 24 is not marked superseded where it stands.
2. **40e vs PLAN section 5 / L3a prompt**: two straps against three straps; neither is in a netlist (M2).
3. **21a / 38a vs the 8-channel chip**: bias start-up and the ">= 1 s" wait were measured with one channel on `vbn` (M1).
4. **31 vs the organizer files**: 2235 um core against 2040 um (README) and 2051 um (padring fork).
5. **42a vs the netlist**: "128 units" against one plate. **39 vs stage1c**: Cin drawn as one 10,002 um2 plate (known; L2a splits it).
6. **32 / 37 vs the RTL**: no separate wrapper, no token-flop chain. Function is as decided.
7. **43a vs old scripts and NOTES Environment**: the `cut` pipe is still in two run scripts and in the Environment section.
8. **42b / 9 / 41b vs the PDK**: the decided resistor type does not exist in this PDK variant (B1).

#### 4.1.3 Open or "to be confirmed" items without a layout prompt, and stale statements

Not covered by any prompt in layout_run.md: replica / mirror mismatch of `vrs` (38b); 9-PVT reset tables (38b); TGATE + real one-shot in one netlist (38b; L3b item 1 has the TGATE but not the one-shot); xschem update (38b); latch noise (40b, README open item 7); fs / sf corners and Monte Carlo for the Cref switch (42d); the question to the organizer about double bonding (43f); "nothing needs a free-running clock" (37; checked here).

Stale statements (file: what it still says -> what holds today):
- AFE/NOTES.md:32 "always pipe ngspice output through `cut -c1-200`" -> forbidden by Decision 43a.
- AFE/NOTES.md:29 "set ad/as/pd/ps to 0" -> Decision 13 answer: only nrd / nrs must be 0.
- AFE/NOTES.md:462,489 "ngspice ignores num_threads" -> a job-local `.spiceinit` works (X2).
- AFE/NOTES.md "Open questions": MIM minimum size, mux vs 16 ADCs, vhalf option list are answered (Decisions 39, 34, 42) but still listed as open.
- AFE/TAPEOUT.md: title "DRAFT, not yet reviewed"; lines 22-55 N = 4 with MODE / EN / CLK / READY pads and VDD5; 104-107 "8:1 mux, 31.25 us frame"; 117-121 pad options; 155-159 decap 0.72 nF / 0.16 mm2 and "SCLK 1-5 MHz". None is marked superseded.
- AFE/adc/NOTES.md:8-9 "8:1 input mux, frame period 31.25 us, 9-bit shift register" -> no mux, 250 us, 10 bits.
- AFE/adc/README.md: line 16 "comparator reference = VDD/2 tap" -> floating Cref; line 28 and the table "input range claimed 1.15-2.15 V" -> INL claim to 2.0 / 1.9 V (43c); line 49 "wait >= 1 s" (M1); line 67 top-of-range numbers are the D4b ones; line 76 "ADC + interface about 28 uW" -> about 54 uW digital + 167 uW of vhalf dividers (section 4.6); line 100 open item 1 (re-synthesis with dac_gdn) is done; the 43d sentence is missing.
- AFE/layout/PLAN.md:59 decap 0.72 nF at 4.6 fF/um2 -> 0.225 nF at 3.98 fF/um2.
- info.yaml:20 "tie DOUT_OE=1" -> DOUT_OE = ~CS.
- Decision 23 "13-20 dB at 3.7 kHz" -> 11.7-18.9 dB.
- AFE/adc/sim/d3_taps.log -> superseded by AFE/review/sim/sta_audit.log (m2).

### 4.2 Step 2: requirements traceability

Corners: amplifier typ 27 / ff 85 / ss -40 C at 3.3 V (9 PVT where A4b did them); ADC typ 27 / ff -40 3.6 V / ss 125 3.0 V. Status: PASS, FAIL, ACCEPTED-FAIL (Decision n), ESTIMATE, NOT VERIFIED.

| target | required | best evidence (typ / ff 85 / ss -40 unless stated) | corners | margin | status |
|---|---|---|---|---|---|
| gain | 60 +-1 dB (D1) | 60.056 / 60.061 / 60.041 dB [amp/sim/a4c_ac.log]; reproduced 60.058 / 60.063 / 60.043 [review/sim/freq_noise.log]; end to end from codes 60.007 / 59.865 / 59.990 dB [adc/sim/x2_s1_report.log] | 3 (9 in A4b) | 0.9 dB | PASS |
| f_lo | <= 0.5 Hz (D1, D2) | 0.202 / 0.225 / 0.237 Hz [a4c_ac.log] | 3 | 2.1x | PASS (set by a model leakage floor: risk R1) |
| f_hi | >= 300 Hz | 653 / 998 / 422 Hz [a4c_ac.log]; gain at 300 Hz -0.8 / -0.4 / -1.8 dB [freq_noise.log] | 3 | 122 Hz at ss -40 | PASS |
| input-referred noise | <= 2 uV rms, 0.5-300 Hz, typical flicker (D1, D4) | amplifier 1.669 / 1.849 / 1.541; with aliasing, TGATE Ron and ADC: 1.709 / 1.886 / 1.591 uV [freq_noise.log] | 3 | 14.5 / 5.7 / 20.5 % | PASS (ff 85 is inside 10 % of the limit; A4b's 9-PVT table shows it is the worst corner) |
| noise, fnoicor = 1 | report (D4, D10) | 4.72 / 4.93 / 4.39 uV [a4c_noise.log] | 3 | - | ACCEPTED-FAIL (Decision 10) |
| noise, unfiltered codes | none stated | 2.04 / 2.23 / 1.92 uV [freq_noise.log] | 3 | - | INFO: needs a host low-pass (m5) |
| CMRR | none stated | common-mode gain -69.5 dB at 12 Hz, ideal matched caps (CMRR 109 dB) [a3_diag.log]; no cap mismatch run | typ | - | NOT VERIFIED with mismatch |
| PSRR (supply to output) | none; ideal 0.5 V/V | 0.557-0.570 V/V at 50 Hz, 9 PVT [a4b_summary.txt]; board ripple <= ~1 mV rms [adc/sim/d4_hybrid_track.log] | 9 | - | INFO: host requirement |
| THD at +-0.5 mV | none; D28 accepts ff 85 | 0.040 / 2.527 / 0.051 % at 12.25 Hz [a4c_thd.log] | 3 | - | ACCEPTED-FAIL at ff 85 (Decision 28) |
| output range | 1.15-2.15 V | 1.148-2.154 V typ, bottom 1.220 V at ff 85 [a4c_thd.log]; 1.1486-2.1515 / 1.2129-2.1524 / 1.1491-2.1505 V [x2_s1_report.log] | 3 | - | PASS typ, ss; ACCEPTED-FAIL ff 85 (Decision 28) |
| resolution | 12 bit, no missing code (D0 criterion) | DNL > 1 LSB in ~4 % of chips at the ASSUMED A_C 0.5 [d2_dnl.log]; nominal devices: steps -1.1 / +1.3 LSB at codes 1536 / 2048 [x2_inl_step.log] | 3 | - | ACCEPTED-FAIL (Decisions 40a, 43b) |
| INL beyond the offset | <= 1 LSB | 0.63 / 1.99 / 0.61 LSB below 2.05 V; 2.2 / 5.1 / 0.6 LSB to 2.15 V [x2_s1_report.log] | 3 | - | PASS typ, ss below 2.0 V; ACCEPTED-FAIL ff 85 and top of range (Decision 43c) |
| ENOB, full-scale referred | none (information) | 8.96 / 7.23 / 9.15 [x2_s3_summary.log]; own budget 8.87 / 6.69 / 8.95 [freq_noise.log] | 3 | - | INFO: amplifier-noise limited |
| sample rate | 4 kS/s per channel x 8 (D16, D29) | frame 80.1 us at 2 MHz, 53.4 us at 3 MHz of the 250 us period; minimum SCLK 0.64 MHz [calc 4.4.4] | - | 3.1x / 4.7x | PASS (host-enforced only) |
| simultaneous sampling (D34) | all 8 at CS falling | spread of the 8 sampling switches <= 0.075 ns [tb_audit_summary.log, gate level] | 5 | - | PASS |
| settling in T_ACQ | <= 0.5 LSB | <= 0.114 LSB at 240.5 us with the real DAC [adc/sim/d5_settle.log]; amplifier adds <= 0.08 LSB to the codes [x2_s1_report.log]; T_ACQ of ADC 7: 239.65 us (2 MHz), 243.07 us (3 MHz) [tb_audit_summary.log] | 3 | 4x | PASS |
| supply error at decisions | <= 0.5 LSB | <= 0.11 LSB typ / ss 125; <= 0.25 LSB ff -40 3.6 V [x2_s4_sweep.log]; pad L / R ASSUMED | 3 | 2x at ff -40 | PASS (ESTIMATE inputs; m6) |
| channel crosstalk | <= 0.5 LSB | 0.022 LSB, 2 channels [x2_s5_summary.log] | typ | 20x | PASS (typ only; 8 channels not run) |
| power | none stated | 2.08 / 3.28 / 1.35 mW [power_total.log] | 3 | - | INFO |
| area | fit the slot | 0.86 mm2 vs 1.23 mm2 ASSUMED [area.log] | - | 30 % | PASS against an assumption (B3) |
| pads | ~29 share | 32 [info.yaml], [xcheck.log C9] | - | -3 | NOT VERIFIED (organizer) |
| recovery after an electrode step | 100 ms for 100 mV (dropped) | 1 mV 0.13-0.27 s, 10 mV 3.4-4.7 s, 100 mV 7.3-9.0 s [a4c_rec.log] | 3 | - | ACCEPTED-FAIL (Decision 38b) |
| power-up | defined state | needs RST_AMP >= 30 ms after the bias is up [a4c_pur.log]; bias up after 3.7 ms / 1.0 ms / 3.6 s with 8 channels [bias_startup.log] | 3 (+ 3.0 V) | - | PASS with the host sequence of P-A3; README value FAILS at ss -40 (M1) |
| stimulation range through the TGATE | 0-3.3 V (TAPEOUT.md:141) | Ron 4.3-21.0 / 4.1-15.6 / 4.5-34.2 kOhm over 0-3.3 V; 65 kOhm at 3.0 V ss -40; leakage < 1 pA inside the rails, 0.55 nA at VDD + 0.4 V [tgate_ron.log] | 6 | - | PASS for bench signals inside 0..VDD (i4) |
| serial interface | SPI mode 0, 160-clock frame | 72 testbench runs, 202 assertions in each main run [tb_audit_summary.log]; every code on every channel [adc/sim/d3_exh_tt_2MHz.log] | 5 | - | PASS |

**End-to-end chain** (own calculation, [review/scripts/freq_noise.py], log [review/sim/freq_noise.log]), at the electrode, typ 27 / ff 85 / ss -40:

| term | value | source |
|---|---|---|
| amplifier + electrodes, 0.5-300 Hz | 1.669 / 1.849 / 1.541 uV | new .noise run of the frozen netlist; equals a4c_noise.log within 0.002 uV |
| amplifier noise aliased into the band (k x 4 kHz +- 300 Hz) | 0.116 / 0.161 / 0.080 uV | same run (D5 estimate: 0.13 / 0.18 / 0.09) |
| routing TGATE thermal noise (max Ron) | 0.32 / 0.30 / 0.36 uV | [tgate_ron.log], 4kTR x 299.5 Hz |
| ADC at its input, 0-2 kHz: kT/C 34 / 37 / 30 uV, Cref 24 / 28 / 21, comparator pair 118 / 168 / 108, latch 50 (ESTIMATE), quantisation 233, DNL 201 (ESTIMATE 0.25 LSB) | 336 / 357 / 332 uV = 0.42 / 0.44 / 0.41 LSB | [d2_ktc.log], [d1_noise.log], I2 estimate |
| ADC share inside 0-300 Hz, at the electrode | 0.13 / 0.14 / 0.13 uV | / 1000 x sqrt(300 / 2000) |
| **total in band** | **1.709 / 1.886 / 1.591 uV** | limit 2.0 |
| total in the unfiltered code stream | 2.036 / 2.229 / 1.920 uV | |
| SNR for +-500 uV / SINAD with amplifier THD | 44.8 / 44.0 / 45.3 dB; 44.8 / 31.7 / 45.3 dB | [a4c_thd.log] |
| ENOB referred to 3.3 V full scale | 8.87 / 6.69 / 8.95 bit | (SINAD - 1.76) / 6.02 + log2(1.65 / 0.5) |

Not in the sum because they are static or host-side: code offset -22..-40 LSB (43e), threshold steps at codes 1536 / 2048 (43b), top-of-range error (43c), supply ripple (0.6 LSB per mV), CS jitter (85 ns rms for 0.1 LSB at 300 Hz full scale).

### 4.3 Step 3: connectivity and interface consistency

Script [review/scripts/xcheck.py], log [review/sim/xcheck.log]: 105 checks, 68 OK, 13 MISMATCH, 24 NOTE. It parses the Verilog top and stubs, the RTL, every SPICE subckt (flattened to device terminals), info.yaml, lvs_config.json, PLAN.md section 9 and the organizer template.

What passed (all scripted):
- Stub ports equal the SPICE subckt ports in name and order for afe_chc, fs_oneshot_c, bias_genc, dac_sw, cmp_p, vhalf, vrefs (C1). Every SPICE pin of every analog instance in `afe_ch` is connected by name (C3).
- Net census of `afe_ch` (57 nets): every pin that only touches MOS gates has exactly one driver; no net has two digital drivers; two open nets, both intended (`cmp_qn`, `m`) (C4).
- All 14 per-channel buses use every bit exactly once for i = 0..7 (C5). `dbs_ctrl #(8)` exports the four switch buses and all are consumed (C11).
- Polarity of 17 control pins, derived from the device type at each gate and compared with the RTL expression (C6): sw_rec (NMOS of the TGATE, the park PMOS and the one-shot trigger), sw_rec_b (PMOS of the TGATE, park NMOS: HIGH = park on), fs (PMOS normal tap / NMOS reset level: active high), rst and rstm on one net (NMOS, high = tracking), sam / samb, gp (PMOS, low = drive high) = ~(en & code), gn (NMOS) = en & ~code, gdp tied to VDD, gdn = ~tg_on, Cref switch on tg_on / samb, comparator clock high = evaluate, comparator inp = reference, inn = plate, outp -> cmp_q.
- REF reaches `afe_chc.ref` of all 8 channels (C7). One vhalf per ADC, its node `vcmd` is local (C8). `vcm_out` no longer feeds the ADC.
- info.yaml has 32 pins; every input pad has `_PU` / `_PD` driven; DOUT has its 8 control pins driven; DOUT_OE = dout_oe = ~cs_n; RSTN_PD = 1; no top port is left over (C9).
- PLAN.md section 9 pin table equals the `afe_ch` port list; 281 crossing nets confirmed (C14). The 6 hand-instantiated standard cells exist in the 7t5v0 library (C15).
- No internal net of any analog cell is without a DC path or has a single terminal (C13).

Mismatch table:

| id | what | detail | issue |
|---|---|---|---|
| C9 | DOUT port naming | template wants `DOUT_OUT` and `DOUT_IN`; the top has `DOUT` | B2 |
| C9 | stale comment | info.yaml line 20 "tie DOUT_OE=1" | m1 |
| C10 | lvs_config paths | `spice/dbs_afe_top.spice`, `verilog/gl/dbs_afe_top.v`, `gds/dbs_afe_top.gds` do not exist yet (expected before L3a) | - |
| C10 | LVS structure | both file lists name the top; L1d hardens `afe_dig`, which is not a module of the top netlist. The mixed-signal example of the organizer uses a SPICE top reference plus the powered netlist of its digital block (github.com/tritone4801/chipathon-2026-A44-SAR-ADC lvs_config.json, read 2026-11-20; see sim/organizer/README.txt) | 4.9.3 |
| C10 | top name | `dbs_afe_top` is our name; examples use organizer-assigned names (A44_A, A02_A) | B3 |
| C12 | ideal primitives | afe_chc: Rbrk x 2; fs_oneshot_c: Rt, Rmm; dac_sw: Cpb0-11, Cpbd, Cpm; cmp_p: Cxa1, Cxa2 | M3 |
| C12 | device not in the PDK variant | ppolyf_u_3k: bias_genc x 6, vhalf x 2 (x 8 ADCs) | B1 |
| C12 | MIM name | 141 MIM instances are `cap_mim_2f0_m2m3_noshield`; layout device is `..._m4m5_...` (same model) | 4.9.3 |
| C2 | TGATE views | signal pins agree in .v / .spice / .lef / extracted .cir; power pins exist only in .spice and .lef; the extracted view has the PMOS bulk on an unnamed net | 4.9.3 |

Notes: bracketed pad names are used by both organizer examples ("DOUT[7]", "data[7]"), so `E[0]` is acceptable (ORGANIZER). `gf_def_ready`, `ws_def_ready`, `drc_ready`, `lvs_ready` are all false in info.yaml.

### 4.4 Step 4: analog-digital synchrony

Sources: the RTL [AFE/adc/rtl/*.v, rtl/dbs.v, AFE/top/dbs_afe_top.v]; OpenSTA on the current hardened netlist [review/scripts/sta_audit.tcl, .py -> review/sim/sta_audit.log];
the assertion testbench [review/tb/tb_audit.v, top_ba.v, stubs_audit.v, audit_delays.vh; review/scripts/run_tb_audit.sh, gen_gl.py -> review/sim/tb_audit_*.log, tb_audit_summary.log];
analog needs from saved logs and from [review/sim/mixcorner.log], [bias_startup.log].
Notation: edge k = k-th SCLK rising edge after CS fell; ADC i = 0..7; T = SCLK period (500 ns at 2 MHz, 333.3 ns at 3 MHz).

#### 4.4.1 Timeline of a full operating cycle (from the RTL)

**Power-up.**
1. VDD ramps. RSTN is low through the pad pull-down (RSTN_PD = 1 [dbs_afe_top.v:24]). All flops with a reset are cleared asynchronously: `cfg_hold` = 0 so RST_AMP = MODE = 0, EN = 0 [adc8_top.v:50]; FSM s0 = 1, s1 = 0 so rec_en = treat_en = 0 [dbs.v:13-24]: every routing switch open, every REC node parked on vcm_in (sw_rec_b = 1 -> park NMOS on).
2. With CS high: `frame_rn` = 0, counter 0, drivers tri-state, `trk` = 1: plate reset closed, sampling switch and Cref switch closed, comparator in reset (no static current), DOUT pad off.
3. Bias: ladders are up with VDD; the master current needs 3.7 ms (typ), 1.0 ms (ff 85), 3.6 s (ss -40), 23 s (ss -40, 3.0 V) with 8 channels [bias_startup.log].
4. Stage 1 of every amplifier comes up latched at a rail [amp/sim/a4c_pu.log]. The host must write RST_AMP = 1, hold >= 30 ms (100 ms decided), write RST_AMP = 0. RST_AMP is a level in `cfg_hold`; it needs no clock while held [tb C1.hold].
5. If RSTN is never driven low, the routing and RST_AMP are undefined until two complete frames have been sent, after which the chip is in the defined all-open state [tb P3]. In silicon the pull-down makes this case unlikely.

**Configuration write** (every frame carries it): DIN is shifted into the 10-bit `cfg_sr` on edges 1-16 (the last 10 bits stay: RST_AMP, MODE, EN[7:0]) [adc8_top.v:52]. At edge 33 `cfg_hold` <= `cfg_sr` [53]. Frames with fewer than 33 edges commit nothing. The outputs change 1.0-3.2 ns after edge 33 [sta_audit.log section 5].

**Record frame.**

| event | when (RTL) | delay from STA, ff -40 / tt / ss 125 |
|---|---|---|
| CS falls = sample: plate reset switch `rst_sw` opens for all 8 ADCs | combinational from the pad: `trk = cs_n OR done` [adc8_top.v:98-99] | 0.51-0.63 / 0.92-1.06 / 1.88-2.06 ns; spread over the 8 channels 0.12-0.18 ns |
| sampling switch and Cref switch (`tg_on`) open, dummy bottom grounded (`dac_gdn`) | one dlyd cell after `trk` [101-102] | 2.26-2.40 / 4.18-4.36 / 8.74-9.01 ns; after the reset switch by >= 1.63 / 3.12 / 6.68 ns |
| frame counter released | `frame_rn` = rstn AND ~cs_n [33] | CS must fall >= 4.1 / 6.8 / 13.0 ns before edge 1 |
| ADC i, trial t: DAC bits set | edge t + i (t = 1..12) [adc_sar_ch.v:35-43,58-59] | gate edges 0.80-3.62 / 1.35-6.01 / 2.64-11.48 ns after the edge |
| comparator clock of ADC i | T0 + i x Delta after the same edge, width W [adc_clkgen.v:22-28] | T0 25.0 / 46.2 / 96.5 ns; Delta 7.4 / 13.8 / 28.8 ns; W 3.2 / 5.9 / 12.3 ns; ADC 7 ends at 80.2 / 148.4 / 310.3 ns |
| decision captured | rising edge of `tapw` [adc_sar_ch.v:29] | 0.33 / 0.57 / 1.09 ns before the window ends |
| decision written into the code bit | next SCLK edge [36,41] | slack at 3 MHz 250.6 / 180.6 / 14.3 ns |
| drivers released | edge 13 + i [49] | |
| tracking resumes (reset switch closes, sampling and Cref switches one dlyd later) | edge 14 + i [53] | reset switch 1.1-4.7 ns after the edge, sampling switch 2.9-11.4 ns |
| DOUT word 0 = 0; word 1 (sampled at edges 17-32) = config held before this frame; words 2-9 (edges 33-160) = {0, ID, code} of channel 0..7 | `dout_q` on SCLK falling [82-83] | DOUT 0.6-3.0 ns after the falling edge; host samples half a period later |
| CS rises | counter, drivers, DOUT cleared; `trk` = 1 | DOUT pad off |

ADC 7 finishes its last decision after edge 19 and tracks again from edge 21. The first DOUT bit that can be 1 changes after edge 22. No DOUT edge falls inside a conversion.

**Mode switch.** After the commit at edge 33 the routing controller needs two more SCLK edges (enable double register, FSM) [dbs.v:18-19,56-57]:
- treat -> record: sw_ipg falls after edge 34, sw_rec rises after edge 35 (one SCLK period of break-before-make). sw_rec is the one-shot trigger: fs rises with it; the park switch opens on the same nets.
- record -> treat: sw_rec falls after edge 34 (park closes), sw_ipg rises after edge 35.
- The reset pulse lasts 3.56 / 1.90 / 6.86 ms (typ / ff 85 / ss -40) [amp/sim/a4c_oneshot.log] = 15 / 8 / 28 frames at 4 kS/s; then the amplifier settles: 0.13-0.27 s for a 1 mV electrode step, 3.4-4.7 s for 10 mV, 7.3-9.0 s for 100 mV [a4c_rec.log]. The host may use data after that.
- A config frame of only 33 or 34 clocks commits the config but leaves the FSM unfinished; the routing then moves at edges 1-2 of the next frame, while the ADCs convert [tb M2].

**CS high / idle, SCLK stopped.** Comparator in reset, no static current. DAC bottoms follow the amplifier, plate and Cref on vhalf. vhalf dividers draw 6.3 uA each all the time. Nothing in the chip needs a clock. If SCLK runs while CS is high (shared bus) only the delay chain, the capture flops and `cfg_sr` toggle; no analog control moves and the garbage in `cfg_sr` is overwritten by the next word 0 [tb X3].
**SCLK stopped in mid-conversion (CS low).** The digital state waits and continues correctly [tb X2]. Plate and Cref float meanwhile: a 3.49 pF plate droops 0.29 mV per ms per pA of leakage (ESTIMATE), so only that frame is affected.

#### 4.4.2 Clock domains

One clock: SCLK. All adc8_top flops, the FSM and the enable registers are clocked by the SCLK pad net [dbs_afe_top.v:30,36]; the 8 capture flops by `tapw[i]`, a delayed SCLK. CS and RSTN act only as asynchronous resets. There is no clock-domain crossing; the former `clk` of rtl/dbs.v is SCLK. When the host does not clock SCLK the routing state and RST_AMP hold; a mode change needs a frame of at least 35 clocks.

#### 4.4.3 Required versus available

"Available" is from STA / gate-level simulation of the hardened netlist at the digital corner; "needed" from the analog log at the paired analog corner (ff -40 C 3.6 V / ff 125 / typ / ss -40 / ss 125 C 3.0 V).

| pair | analog needs | digital gives | margin | status |
|---|---|---|---|---|
| sampling order: plate reset before sampling / Cref switch | > 0 (wrong order costs 0.4 LSB nonlinearity, [adc/sim/d2_samp.log]) | 1.72 / 2.54 / 3.22 / 4.64 / 6.79 ns [tb gls] | >= 1.7 ns | PASS |
| simultaneous sampling of the 8 channels | << 85 ns (jitter budget) | <= 0.075 ns spread [tb gls] | 1000x | PASS |
| acquisition: sampling switch closed before the next sample, incl. the kick (spikes 0.10-0.49 V [x2_s1_report.log]) | <= 0.114 LSB left at 240.5 us [d5_settle.log]; <= 0.48 LSB already at 11 us [a4b_adc245.log]; codes equal the ADC alone within 0.08 LSB [x2_s1] | 239.65 us at 2 MHz, 243.07 us at 3 MHz (ADC 7); 70.5 us back to back [tb F1, X4] | >= 20x in time | PASS |
| DAC settling before the comparator clock (trial 1 is the slowest) | 15.1 / ~20 / 22.6 / 24.0 / 35.8 ns to 0.5 LSB [adc/NOTES D4, D2] | 21.88 / 32.54 / 40.97 / 58.91 / 86.49 ns [tb gls] | 6.8 / 12.5 / 18.4 / 34.9 / 50.7 ns | PASS (top of range excepted: Decision 43c) |
| same, uncorrelated corner: slow 3.3 V devices, ff -40 standard cells | about 24 ns | 21.9 ns | -2 ns = 0.65 LSB on trial 1, 0.41 LSB on trial 2; ss 125 C 3.6 V with ff 125 cells: 0.32-0.44 LSB [mixcorner.log] | FAIL at that corner (M4) |
| comparator decision inside the window | 0.99 / 1.58 / 2.02 ns at small overdrive; 1.63 ns for slow analog at -40 C [mixcorner.log] | W minus capture lead minus setup: 2.66 / 5.11 / 10.97 ns | >= 1.0 ns even at the mixed corner | PASS |
| window T0 + 7 Delta + W inside the SCLK period | ends before the next edge | last end 80.2 / 118.4 / 148.4 / 212.2 / 310.3 ns | at 3 MHz: 253 / 215 / 185 / 121 / 22.4 ns; at 2 MHz: 420 / 381 / 351 / 287 / 189 ns | PASS (4 MHz fails at ss 125: [adc/sim/d3_matrix.log]) |
| capture of cmp_q against the comparator reset (hold) | comparator output leaves its decision 0.79 / 1.14 / 1.83 ns after tapw [adc/NOTES D4] | flop hold | >= 0.8 ns [D4 race] | PASS (not re-simulated; unchanged netlist path) |
| captured decision to the code register | setup | slack 250.6 / 211.2 / 180.6 / 115.0 / 14.25 ns at 3 MHz [sta_audit.log] | 14 ns | PASS |
| Cref switch open before the first decision | open at the first comparator clock | opens 2.3-9.0 ns after CS; first clock >= T0 after edge 1 | > 100 ns | PASS [tb T6] |
| rst / rstm on one net (I0 mismatch 4) | D2 opened rstm 0.5-1 ns before rst | same instant | X2 ran rstm = rst in closed loop: codes consistent [adc/scripts/x2lib.py:211]; PEX re-check is in L1b | PASS pre-layout |
| sw_rec / sw_rec_b skew | A4c used ideal complementary edges; during the skew E, REC and vcm are joined through two PMOS for the skew time: <= 8 fC for 100 mV (ESTIMATE) | 0.16-0.89 ns at closing, 0.07-2.25 ns at opening (ESTIMATE: yosys netlist, 0.05-0.2 pF load) [dbs_ctrl_skew.log] | - | PASS (harmless); L1d / L3a report the real value |
| reset pulse versus first valid data | 3 ms clears every step at typ and ss -40, 1 ms at ff 85 [a4c_rec.log] | 3.56 / 1.90 / 6.86 ms | 1.2x / 1.9x / 2.3x | PASS; host discards 15 / 8 / 28 frames plus the settling time |
| RST_AMP at power-up | >= 30 ms, after the bias is up | host-timed level | bias up after 3.6 s at ss -40 with 8 channels, README says 1 s | FAIL of the documented sequence at ss -40 (M1) |
| CS falling before the first SCLK edge | recovery of the frame flops | - | host must give >= 4.1 / 6.8 / 13.0 ns (README says 100 ns) | PASS |
| DOUT to the host | host samples on the rising edge | 0.6-3.0 ns after the falling edge at the macro pin; + pad (4 mA setting, ASSUMED <= 15 ns into 20 pF) | >= 148 ns at 3 MHz | PASS |
| frame rate | 250 us period | 80.1 us (2 MHz), 53.4 us (3 MHz) | idle 170 / 197 us | PASS |
| delay-chain spread | T0 >= settling at ff, end <= T at ss | ratio ss 125 / ff -40 = 3.86 | both ends are used up: +1 dlyd on T0 costs 7.2 ns at ss 125 (22 ns left) | PASS, no spare |

#### 4.4.4 Frame-rate arithmetic

- One frame = 160 SCLK + CS lead (>= 13 ns) = 80.0 us at 2 MHz, 53.3 us at 3 MHz. At 4 kS/s the period is 250 us: 68 % / 79 % of it is idle.
- Minimum SCLK for 4 kS/s x 8 with a 160-clock frame: 160 / 250 us = 0.64 MHz with no gap; 0.65 MHz with 1.5 clocks of CS-high time. Plate hold at that speed: 21 clocks = 32 us (9 uV droop per pA, ESTIMATE).
- Maximum sample rate (back to back, 1.5 clocks CS high): 12.4 kS/s at 2 MHz with T_ACQ 70.5 us [tb X4]; about 18.5 kS/s at 3 MHz.
- Maximum SCLK: 3 MHz, set by the last comparator window at ss 125 C 3.0 V (310.3 ns of 333.3 ns) and by the top-of-range DAC settling. Nominal 2 MHz leaves 189 ns.
- 4 kS/s is not enforced on chip: the sampling instant is the CS falling edge of the host timer (jitter <= 85 ns rms for 0.1 LSB at 300 Hz full scale, [adc/PLAN.md D0b.1]).

#### 4.4.5 Delay chain and the open CTS item

- What is at stake: T0 and Delta come from 57 dlyd + 8 dlyc + 2 dlya cells kept by `(* keep *)` and RSZ_DONT_TOUCH_RX [adc_dlychain.v, lg/config.json]. If CTS buffers or resizes them, or adds insertion delay only on the flop branch, the DAC edge moves relative to the comparator clock: each ns of clock-tree insertion delay on the flops takes one ns from the DAC-to-comparator margin (6.8 ns at ff -40) and gives it to the window-end margin (22.4 ns at ss 125).
- The run without CTS is a workable fallback: one net with 143 pins, hold slack +0.24 ns at ff -40 including 0.5 ns uncertainty, but 16 max-slew violations at ss 125 [metrics.json]. One hand-placed clock buffer in front of the flops fixes the slew; the chain must branch from the same buffered node.
- The 2 h box in L1d is enough for the fallback, not for a general CTS fix. Either way L1d must re-run [review/scripts/sta_audit.py] on the new netlist and re-check the table of 4.4.3 (exact sentence in 4.9.4, edit 7).

#### 4.4.6 Testbench results

Builds: RTL + per-corner cell models + STA port delays (6 corner settings), and gate level = the hardened netlist with the worst SDF arc on every cell output (6 settings). Icarus cannot read this SDF (it aborts in `$sdf_annotate`, tried with and without `-ginterconnect`), so [review/scripts/gen_gl.py] writes the delays as `assign #`; the gate-level DAC-to-comparator time equals STA within 0.02 ns. Each build runs at 2 and 3 MHz with three scenarios: main, late reset, no reset. 72 runs; one line per run in [review/sim/tb_audit_summary.log].

Scenarios in `main`: power-up with RSTN released before SCLK (P1); RST_AMP set, held 100 ms without a clock, cleared (C1); record start, one-shot, 41 frames at 250 us with corner codes (F1); record -> treat -> record on 4 channels and the two cases where an EN bit falls in the frame that changes MODE (M1); a 33-clock config frame (M2); CS raised after 5, 13, 20, 40 clocks (X1); SCLK stopped 1 ms after edge 6 (X2); 100 SCLK cycles with CS high (X3); back-to-back frames (X4); RSTN pulses in mid-frame (X5). `rstlate`: frames running while RSTN is low, release between frames (P2). `noreset`: RSTN never low (P3).

Standing assertions, evaluated after every scenario (ids as in the logs):

| id | assertion | 5 matched corners, 2 and 3 MHz, RTL and gate level |
|---|---|---|
| S1 | plate reset opens before the sampling / Cref switch | PASS |
| S2 | 8 channels sample within 1 ns | PASS |
| S3 | dac_gdn = ~tg_on | PASS |
| T1 | trial t of ADC i is evaluated between edges t + i and t + i + 1 | PASS |
| T2 | DAC edge to comparator clock >= settling time of the corner | PASS; FAIL at the MIXED setting (M4) |
| T3 | no DAC edge while a comparator evaluates | PASS |
| T4 | every window ends before the next SCLK edge | PASS |
| T5 | window >= decision time | PASS |
| T6 | sampling switch, Cref switch, plate reset open and dummy grounded at every comparator clock | PASS |
| T7 | no tri-state bottom at a comparator clock | PASS |
| T8 | 12 comparator pulses per ADC per frame | PASS |
| T9 / T10 | drivers released at edge 13 + i, tracking at 14 + i | PASS |
| T11 | no crowbar at the driver gates | PASS in RTL; FAIL at gate level: overlaps of 0.06-0.21 ns (m3) |
| T12 | sampling switch never on while a driver is on | PASS in complete frames |
| T13 | no comparator clock while CS is high | PASS |
| R1 | record and IPG switch never on together | PASS |
| R2 | no routing edge while an ADC converts | PASS with 160-clock frames |
| R3 | no pulse shorter than one SCLK period on sw_rec / sw_ipg, no zero-width hazard | PASS, also in the two EN-falls-with-MODE cases |
| D1 / D2 | DOUT changes only after the falling edge; DOUT_OE = ~CS; DOUT = 0 while CS is high | PASS |

Scenario assertions: all PASS (P1.*, C1.*, F1.*, M1.*, M2.*, X1.a5-a40, X1.recover, X2.digital, X3.*, X4.data, X5.after33, X5.next, P2.*, P3.*) except three that state a property the design does not have:

| id | result | meaning |
|---|---|---|
| X1.contention | FAIL in all builds | on an aborted frame the sampling switch closes before the drivers release: 1.4-3.0 ns (RTL build), 2.4-5.6 ns (gate level) (m4) |
| X5.word0 | FAIL in all builds | RSTN pulsed during word 0: the same frame commits a word assembled from the DIN bits after the release, not the word the host sent (M5) |
| X5.after33d | FAIL in all builds | RSTN pulsed after edge 33 while DIN carries data: the rest of the frame is decoded as a new frame and commits that data; with DIN idle low (X5.after33) nothing wrong is committed (M5) |

Measured at gate level, ff -40 / ff 125 / tt / ss -40 / ss 125: DAC edge to comparator 21.88 / 32.54 / 40.97 / 58.91 / 86.49 ns; window width 3.37 / 4.91 / 6.16 / 8.79 / 12.79 ns; window end to the next edge at 3 MHz 253.0 / 214.7 / 184.7 / 120.7 / 22.4 ns; DOUT 0.84 / 1.20 / 1.45 / 2.06 / 2.91 ns after the falling edge.

### 4.5 Step 5: area and floorplan

Script [review/scripts/area.py], log [review/sim/area.log]. Every device size is evaluated from the netlist parameters. The layout model (ESTIMATE) is stated at the top of the log:
MOS footprint m (W + 0.8 um)(L + 1.0 um), x1.2 for 5 V / 6 V devices; MIM footprint (side + 1.8 um)^2 per piece (0.6 um bottom-plate overlap, 0.6 um spacing);
HRES poly length x (width + 0.4 um) x 1.2; block factor 1.5 for blocks of large analog devices and 2.5 for blocks of small devices (wells, guard ring, dummies, local wiring);
top-level factor 1.30 on everything except the hardened digital macro. The factor 1.30 is taken from the only layout data in the repo: the digital macro places 31,872 um2 of cells
on 82,048 um2 of core (39 %) [lg/runs/d3/final/metrics.json], and analog blocks made of a few large rectangles (MIM plates, long-L devices) pack much better than that; 1.50 is shown as the pessimistic case.

| block | gate area um2 | MIM drawn um2 | poly R um2 | ESTIMATE um2 | note |
|---|---|---|---|---|---|
| afe_chc (stage 1, stage 2, follower, muxes, park) | 12,883 | 23,301 | - | 49,312 | Cin 2 x 100.01 x 100.01 um = 10,002 um2 each: above the 10,000 um2 limit, 2 pieces each; OTA1 load 8 x 50u/16u is the largest device group |
| fs_oneshot_c | 15 | 1,989 (C_T 4 pF) | - | 2,314 | |
| 2 routing TGATEs + OR2 + INV | - | - | - | 199 | TGATE 3.36 x 3.92 um [TGATE.lef], x3 for rails and taps |
| **amplifier part of a channel** | 12,898 | 25,290 | - | **51,825** | |
| dac_sw | 22 | 3,200 (127 units + bridge 5 x 5.083 + dummy) | - | 8,807 | unit array 12 x 11 sites + one dummy ring on a 6.8 um pitch = 8,416 um2 |
| cmp_p | 102 | 0 (2 x 40 fF are ideal) | - | 877 + 92 | + two 5 x 5 um MIM units (M3) |
| vhalf | 0 | 492 (1 pF) | 280 | 855 | 2 x 83.3 um x 1 um; with ppolyf_u_1k and the same R: + 560 um2 |
| vrefs (Cref 7 pF, one plate 59.07 um) | 1 | 3,489 | - | 3,720 | as 128 units: 5,919 um2 |
| **ADC analog part of a channel** | 125 | 7,182 | 280 | **14,351** | |
| **one channel `afe_ch`** | | | | **66,176** | e.g. 203 x 325 um |
| bias_genc (once) | 657 | 2,489 (C_VRS 5 pF) | 2,194 | 6,270 | ladders 2 x 550 um of 1 um poly; with ppolyf_u_1k and the same R: 5,890 um2 of poly |
| digital macro (adc8_top hardened + dbs_ctrl 1,998 um2 synthesized) | - | - | - | 74,802 at 45 % utilization | die today 300.3 x 318.2 um = 95,555 um2 at 38.8 %, 1,684 cells, 149 flops |
| decap 0.225 nF as MOS capacitors (3.98 fF/um2) | - | - | - | 70,666 | 56,533 um2 drawn x 1.25; as MIM 129,375 um2; under the Cin plates: 0 |

MIM rule check (all 141 MIM instances): none below 25 um2; two above 10,000 um2 per channel (Cin, known since Decision 39). The comparator's 40 fF capacitors would be 18 um2 as MIM, below the minimum (M3).

Totals:

| | um2 / mm2 |
|---|---|
| 8 channels | 529,411 |
| + bias + digital macro + decap | 681,150 = 0.681 mm2 |
| x1.30 top-level factor | **0.863 mm2 = 929 x 929 um** |
| x1.50 | 0.984 mm2 = 992 x 992 um |
| with the decap under the Cin plates, x1.30 | 0.771 mm2 |

| slot | area | utilization at x1.30 / x1.50 | margin |
|---|---|---|---|
| 1110 x 1110 um (ASSUMED, TAPEOUT.md) | 1.232 mm2 | 70 % / 80 % | 30 % / 20 % |
| one third of 2040 x 2040 um (ORGANIZER README) | 1.387 mm2 | 62 % / 71 % | 38 % / 29 % |
| one third of 2235 x 2235 um (Decision 31) | 1.665 mm2 | 52 % / 59 % | 48 % / 41 % |

**Verdict: FITS with 30 % margin in the assumed slot (20 % in the pessimistic case).** The slot itself is an assumption (B3).

Comparison with earlier estimates: 8 amplifier parts 0.415 mm2 (earlier 0.40-0.45: agrees). 8 ADC analog parts 0.115 mm2 + digital 0.075 mm2 = 0.190 mm2 (earlier 0.08-0.12 and 0.136): higher, because the unit array needs a 6.8 um pitch plus a dummy ring (8,416 um2, not 3,300 drawn), Cref and vhalf were added after the estimate (4,575 um2 per ADC), and the digital part is counted as placed (45 %), not as cell area (0.028 mm2). Block total 0.86-0.98 mm2 against the earlier 0.8-1.0: agrees; the decap is now 0.07 mm2 instead of 0.16.

Plausible floorplan for a 1110 x 1110 um slot (ESTIMATE; pad positions are ASSUMED until the DEF exists):
- Two rows of four channel cells, each cell 240 x 400 um including its share of routing: 960 x 800 um. In each cell the two Cin pieces of each input (4 x 70.7 x 70.7 um) sit at the pad-side end with REC and the routing TGATEs, then OTA1 (pair and loads about 110 x 110 um), stage 2 and the one-shot, and the ADC part (unit array 95 x 88 um, Cref 61 x 61 um, comparator, vhalf) at the inner end next to the digital macro.
- A centre strip 1110 x 150 um between the rows: bias_genc (about 80 x 80 um) in the middle so the six bias lines run at most 480 um to each side, the vcm daisy chain, the three supply straps and the DAC-strap decap.
- Digital macro 275 x 275 um in one corner next to CS, DIN, SCLK, RSTN, DOUT, VDD, VSS, with its guard ring and a 20 um decap strip towards the channels; its control pins face the centre strip.
- Pads: 25 analog pads (E, IPG, REC of a channel adjacent, REF in the middle) on the two edges along the channel rows, 3 per channel = 12 per edge plus REF; 7 digital / supply pads on a third edge. A 1110 um edge holds about 9 pads at the pad pitch of an 88-pad frame (22 per 2935 um side), so 32 pads need more than three slot edges or organizer routing from farther pads. This is the main floorplan unknown (P-A9 question 3). Long REC routes add capacitance (harmless: [amp/sim/a4b_tg33_noise_summary.log]) and pad leakage paths (see 4.8).

Levers if the slot turns out smaller, ranked by cost:
1. Decap under the Cin MIM plates (allowed by PLAN section 4): -0.092 mm2, costs a Metal3 shield and one coupling check.
2. Cref as one plate instead of 128 units: -0.018 mm2, no cost (P-A10).
3. Digital macro at 60 % utilization: -0.019 mm2, costs routing effort.
4. Cin 20 -> 10 pF with Cf 100 fF: -0.084 mm2, costs noise (OTA noise gain and kT/C rise) and a full amplifier re-simulation: not before tapeout.
5. N = 4: -0.265 mm2 of blocks.
6. 11-bit DAC: -0.012 mm2: not worth it. A shared ADC would save about 0.10 mm2 and lose Decision 34.

### 4.6 Step 6: power

Static currents from new .op runs [review/scripts/power_op.py -> review/sim/power_op.log] (they reproduce the saved totals 74.37 / 119.29 / 46.83 uA of [amp/sim/a4c_op.log]); totals [review/scripts/power_total.py -> review/sim/power_total.log].

Per block, uA, typ 27 / ff 85 / ss -40 at 3.3 V:

| block | typ | ff 85 | ss -40 | source |
|---|---|---|---|---|
| OTA1 (bias diode, tail, second stage: 3 x IBIAS) | 63.6 | 102.6 | 39.8 | [power_op.log] |
| stage-2 tail | 0.011 | 0.019 | 0.006 | |
| follower | 5.21 | 8.41 | 3.26 | |
| **one amplifier channel** | **68.86** | **111.01** | **43.07** | |
| bias_genc (master 1.68 uA, ladders 3.83 uA at typ) | 5.51 | 8.28 | 3.76 | |
| vhalf, per ADC | 6.31 | 9.18 | 4.47 | (I1 log: 6.29 typ, 5.83 ss 125, 7.44 ff -40) |
| **chip static: 8 channels + bias + 8 vhalf** | **606.8 uA = 2.003 mW** | 969.8 uA = 3.200 mW | 384.1 uA = 1.267 mW | ff -40 C 3.6 V: 662 uA, 2.38 mW; ss 125 C 3.0 V: 638 uA, 1.91 mW |

Dynamic terms, uW at 4 kS/s per channel:

| term | typ | how |
|---|---|---|
| digital macro (SAR logic, delay chain, SPI) + dbs_ctrl | 54.0 | LibreLane power.rpt 159.3 uW with SCLK free-running at 2 MHz = 79.6 pJ per SCLK cycle, x 160 cycles x 4000 frames, x 1.06 for dbs_ctrl. 97 % of it is clock and flop clock-pin power, so the default data activity of the report matters little |
| comparators | 2.3 | 6.0 pJ per decision [adc/sim/d1_delay.log] x 12 x 8 x 4000 |
| DAC switching | 1.9 | 17.8 pC per conversion, worst code [adc/sim/d2_settle.log] x 3.3 V x 32,000 |
| Cref and sampling switch gates | < 0.01 | about 100 fF x V^2 x 4000 per ADC (ESTIMATE) |
| DOUT pad into 15 pF (ASSUMED) | 23.5 | 36 rising edges per frame x C V^2; 15.7 / 31.4 uW at 10 / 20 pF |
| routing block | 0 | static CMOS; one-shot legs 8 x 2 nA while a switch is open |

Totals per mode, mW:

| mode | typ 27 | ff 85 | ss -40 | ff -40 C 3.6 V | ss 125 C 3.0 V |
|---|---|---|---|---|---|
| record (frames at 4 kS/s) | 2.084 | 3.283 | 1.351 | 2.482 | 1.984 |
| stimulate (frames still read) | 2.084 | 3.283 | 1.351 | 2.482 | 1.984 |
| reset (RST_AMP held) | same static current; + frames if read | | | | |
| idle, SCLK stopped | 2.003 | 3.200 | 1.268 | 2.384 | 1.915 |

SCLK 2 MHz and 3 MHz give the same average because a frame has 160 clocks at both. If the host leaves SCLK running the digital part is 159 uW (2 MHz) or 239 uW (3 MHz).
There is no power-down: EN gates only the routing switches (i3). The amplifiers are 87 % of the chip; the eight vhalf dividers (0.167 mW) are 8 % and two thirds of everything on the ADC side.

Consequences:
- Average current from the pad pair 0.63 mA typ, 0.99 mA at ff 85 C. A dvdd / dvss pad cell is rated 60 mA DC (ORGANIZER): one pair is enough for DC.
- Peak (ESTIMATE): 24 pC per SCLK cycle for the digital macro (27 pC at ff -40 C 3.6 V), 1.8-2.6 pC per comparator decision, 50 pC per DOUT edge into 15 pF (5-10 mA for 5-10 ns, only during read-out). X2 S4 assumed 12 pC of digital charge at most: the 8-ADC supply result at ff -40 C (half the margin used) should be repeated in L3b with the macro's own number (m6).
- Static IR drop with a 1000 um x 10 um strap: 2.4 mV on the top metal (0.04 ohm/sq), 5.5 mV on Metal3 (0.09 ohm/sq); 3.9 mV at ff 85 C. All references are ratiometric and generated once in bias_genc, so this is harmless.
- Electromigration: 0.06-0.10 mA per um on a 10 um strap, 0.04 mA per um on a 2 um channel branch, against 2.09 mA per um at 85 C for Metal1-4 (ORGANIZER table): more than 20x margin.
- No power target exists (Targets: "unspecified"). ADS7953 comparison: its datasheet power is not in the repo and was not fetched; NOT VERIFIED. For orientation only: everything on the ADC side here is 0.25 mW for 32 kS/s = 7.8 nJ per conversion, dominated by the static dividers.
- Never simulated before this audit: the per-block split, the bias and vhalf currents at ff -40 / ss 125, the digital power at the real frame activity. Still not simulated: the pad cells' own supply current, the comparator and DAC energy at ff -40 3.6 V / ss 125 3.0 V (values above are the 3.3 V ones).

### 4.7 Step 7: frequency plan

[review/scripts/freq_noise.py -> review/sim/freq_noise.log], new .ac / .noise run of the frozen channel.

- **Signal band.** f_lo 0.20 / 0.23 / 0.24 Hz, f_hi 662 / 1001 / 427 Hz (typ / ff 85 / ss -40; a4c_ac.log: 653 / 998 / 422). Gain at 300 Hz -0.8 / -0.4 / -1.8 dB.
- **Roll-off order.** First order: -20.1 / -19.9 / -20.3 dB per decade from 4 kHz to 40 kHz, -23..-25 dB per decade from 40 to 400 kHz (stage 1 starts to help above about 300 kHz).

| relative gain, dB | 1 kHz | 2 kHz (Nyquist) | 3.7 kHz | 4.3 kHz | 7.7 kHz | 16 kHz | 100 kHz | 1 MHz |
|---|---|---|---|---|---|---|---|---|
| typ 27 | -5.2 | -10.1 | -15.2 | -16.4 | -21.4 | -27.8 | -45.0 | -66.3 |
| ff 85 | -3.0 | -7.0 | -11.7 | -12.9 | -17.8 | -24.1 | -40.9 | -65.0 |
| ss -40 | -8.2 | -13.7 | -18.9 | -20.2 | -25.2 | -31.6 | -49.3 | -66.3 |

- **Aliasing of amplifier noise** into 0.5-300 Hz at 4 kS/s: 0.116 / 0.161 / 0.080 uV; it raises the in-band noise by 0.004-0.007 uV. Negligible, as D0 said.
- **Aliasing of interference.** A tone at 3.7 or 4.3 kHz lands at 300 Hz attenuated by only 15 / 12 / 19 dB; at the ff 85 corner a 2 kHz tone is down 7 dB. Decision 23 accepts this as a documented risk; its figure "13-20 dB" is now 11.7-18.9 dB. Is the 998 Hz corner with a first-order roll-off acceptable? For noise yes (budget above). For interferers it is the weakest point of the chain: anything between 2 and 20 kHz at the electrode (switching supplies, stimulation harmonics) appears in band with 7-28 dB of attenuation. No requirement exists, so this stays ACCEPTED (Decision 23); the cure after tapeout is a host that samples faster (the chip allows 12-18 kS/s, i2) and filters digitally: 12 kS/s moves the first alias band to 11.7 kHz (-25 dB typ).
- **SCLK range.** Maximum 3 MHz: set by the comparator chain at ss 125 C 3.0 V (last window ends at 310.3 ns of 333.3 ns) and by the top-of-range DAC settling. Nominal 2 MHz: 189 ns left. Minimum for 4 kS/s x 8: 0.64 MHz. Below that the sample rate drops; the plate hold time (21 clocks) limits SCLK to roughly 15 kHz for 0.5 LSB of droop at 1 pA of leakage (ESTIMATE).
- **Stagger versus SCLK.** T0 + 7 Delta + W = 80 / 148 / 310 ns; the chain does not scale with SCLK, so the same windows are used at 2 and 3 MHz. A slower SCLK only adds idle time.
- **Internal frequencies.** The chip has no oscillator. Activity is locked to the frame: comparator and DAC bursts of 12 pulses per ADC at the SCLK rate during the first 20 clocks, read-out activity for 128 clocks, all repeating at the 4 kHz frame rate. Every harmonic of 4 kHz aliases to DC when sampled at 4 kS/s: it becomes a fixed offset per channel, not a tone. The data-dependent part of the read-out current (DOUT bits) is first-order independent of the input (X2 S5: neighbour moves 0.022 LSB). The reset one-shot (1.9-6.9 ms) fires only at a record start.
- **Time constants versus the stimulation duty cycle.** HPF time constant 0.66-0.79 s; reset pulse 1.9-6.9 ms; settling after a record start 0.13-0.27 s for a 1 mV electrode step and 3.4-9 s for 10-100 mV. In the original use of the dbs FSM (alternating treat and record) a record window is useful only after about 0.3 s, so the mode cannot alternate faster than about 1 Hz, and electrode offsets of 10 mV or more between the parked level (1.648 V) and the tissue need seconds. Recording between stimulation pulses of a 130 Hz train (7.7 ms period) is not possible with this amplifier.

### 4.8 Step 8: robustness gaps and risk register

L = likelihood that silicon differs from the simulation in a way that matters, I = impact on a working chip. "Check now" = done in this audit where a cheap check existed.

| id | item | never simulated / only estimated | L | I | check now | covered by a prompt? sentence to add |
|---|---|---|---|---|---|---|
| R1 | fA-level leakage that sets the pseudo-R value, f_lo, the bistable DC state of stage 1, recovery times and the cold bias start-up | the 4-6 TOhm "floor" is a model property of unexplained origin (A2); every result that depends on it is a model result | high | medium: f_lo and recovery may be off by a large factor; a latched amplifier is recovered by RST_AMP | not possible in simulation | none can. L4 README test plan: "measure f_lo, the output DC level after RST_AMP and the time to recover from a 10 mV electrode step on every channel" |
| R2 | bias start-up with 8 channels | was measured with one channel | high at cold | medium (M1) | DONE: 3.7 ms typ, 3.6 s ss -40 C, 23 s at 3.0 V [bias_startup.log] | L2b has "power-up with RST_AMP held 100 ms": add "with the vbn load of 8 channels (AFE/review/scripts/bias_startup.py), and state the wait time for the README" |
| R3 | fs / sf corners | amplifier and ADC were never run there | low | low | DONE: amplifier gain 60.06 dB, f_hi 677 / 647 Hz, noise 1.685 / 1.653 uV, 74.1 / 74.9 uA [amp_fssf.log]; ADC timing: settled within 0.18 LSB, decision <= 1.38 ns [mixcorner.log] | not needed; Cref threshold error at fs / sf stays open (42d) |
| R4 | uncorrelated 3.3 V and 5 V device corners (analog slow, standard cells fast) | every earlier run paired ff with ff, ss with ss | low to medium | low: 0.65 LSB static step (M4) | DONE [mixcorner.log] | L1b: "also run the ADC replay with ss analog models and the ff_n40 timing (AFE/review/scripts/mixcorner.py)" |
| R5 | Monte Carlo: DAC units (A_C assumed 0.5 %*um, the PDK has no local MIM mismatch), Cref switch, pseudo-R pair, reset-level replica, Cin / Cf ratio (CMRR) | comparator offset only (D1: sigma 1.6 LSB) | medium | low for the ADC (code shift, DNL below the noise); medium for the replica (sets the reset resistance and the loop stability in reset, stable only above ~20 MOhm) | not cheap: the pseudo-R sits on a model floor and the replica current is nA; no meaningful mismatch model | no prompt. Add to L2b: "Monte Carlo (sw_stat_mismatch = 1, 20 seeds, typ) of the reset state: R_reset and the reset-state step response" |
| R6 | substrate and supply coupling of the 2-3 MHz digital activity into the TOhm nodes, latch-up | not simulatable before layout | medium | medium: frame-synchronous coupling aliases to DC (offset), rectification at the summing node could shift the DC state; RST_AMP recovers | no | PLAN section 5 has the guard-ring rules; L3a does not name the summing node. Add to L3a: "no SCLK / CS / DIN / DOUT / cmp_clk / dac_g* wire within 20 um of a summing node, a pseudo-R, REC or the Cref node; report the minimum distances" |
| R7 | ESD / pad leakage on E, REC, REF | A4c tested 1 and 10 pA with the park on; ORGANIZER README reports about 200 pA for the asig pad | medium | low: with the park on 8 x 200 pA into the vcm tap (412 kOhm) shifts it 0.66 mV (ESTIMATE); in record mode it flows into the electrode; REF connects only to MIM plates, so an unconnected REF pad drifts to a rail | estimate only | L3b item 2: add "with 200 pA of pad leakage on E, REC and REF". README: "REF must be connected to the reference electrode or to mid-supply" |
| R8 | routing TGATE (5 V devices) at 3.3 V over the full range | A4b: 1.15-2.15 V only | - | low | DONE: 4-21 kOhm typ, 34 kOhm ss -40, 65 kOhm at 3.0 V, leakage < 1 pA inside the rails [tgate_ron.log] | L3a already asks for it; replace by "cite AFE/review/sim/tgate_ron.log and re-check on the extracted view" |
| R9 | PEX of the bridge capacitor and the LSB node | D2 sensitivity only (0.018 LSB per fF) | medium | low | no (needs layout) | L1b covers it |
| R10 | 8-channel amplifier + ADC run; all 8 channels resetting together on one `vrs` (16 gate nodes dumped on the 5 pF hold capacitor, about 12 mV, ESTIMATE) | X2 S5 had 2 channels, no reset | medium | medium for the common reset (RST_AMP is the power-up path) | not done: an 8-channel transistor run from power-up is a long run; left for L3b | L3b: add item (5) below |
| R11 | residual abort rate of about 1 per 1e5 switching events | - | certain | none with the retry | - | common rule 8 covers it |
| R12 | comparator latch noise | never measured (two methods failed in D1) | - | none at system level: even 646 uV gives 1.96 uV | no | none; accept (m8) |
| R13 | native-Vt follower device available in the shuttle | - | low to medium | high (M7) | not possible here | organizer question |
| R14 | one VDD / VSS pad pair: bond inductance 2 nH ASSUMED, shared with the DOUT driver; whether the I/O rails are shared with the other groups | X2 S4 with assumed values | medium | low to medium: 0.25 LSB at ff -40 C with half the margin; DOUT edges fall after the conversions | - | L3b item 3 covers the re-run; organizer question 4 |
| R15 | CS is the sampling clock and an `input_cmos` pad without hysteresis | - | low | low: a glitch on CS aborts the frame | - | option: declare CS as `input_schmitt` in info.yaml (no pad cost; adds about 1 ns of delay) |
| R16 | amplifier CMRR with capacitor mismatch | ideal matched capacitors only (109 dB) | medium | low (bench noise pickup) | no | none; README test plan |
| R17 | hold of the floating plate / Cref during the conversion | model leakage 10 fA | low | low: 9.5 us hold at 2 MHz gives 2.7 uV per pA | estimate | none needed |

### 4.9 Step 9: layout readiness

#### 4.9.1 Are the inputs frozen and unambiguous?

| phase | input | state |
|---|---|---|
| L2a | cell list, pins | frozen: afe_chc + fs_oneshot_c + OR2; pin table = `afe_ch` ports (checked by script, C14) |
| L2a | MIM sizes | from the parameters: Cin 20 pF (2 pieces each), Cf1 2 x 9.79 um, Cin2 38.59 um, Cf2 11.92 um, Cc1 22 um, Cc2 31.46 um, C_T 44.59 um [area.log]. NOT stated: Cin : Cf1 matching (ratio 100 exactly: build Cin from pieces with the perimeter-to-area ratio in mind, PLAN section 1.2) |
| L2a | devices | native-Vt follower unconfirmed (M7); `Rbrk`, `Rt`, `Rmm` must be removed for LVS (M3) |
| L2a | shielding | PLAN section 5 names the summing node, pseudo-R and REC; no numeric rule for digital lines (R6) |
| L1a | cell list, pins | frozen except the supply pins (M2) |
| L1a | MIM | DAC 127 units 5 x 5 um + dummy + bridge 5 x 5.083 um; common centroid required but no placement is specified (which unit belongs to which bit is free: say so); Cref one plate or 128 units (m7); comparator capacitors undefined (M3) |
| L1a | resistors | vhalf type not available (B1) |
| L1d | RTL, pins | frozen; the wrapper `afe_dig` is to be created; CTS open (M6) |
| L3a | bias_genc | ladder type not available (B1); no layout phase owns its matching rules (ladder as one serpentine, replica next to nothing noisy) |
| L3a | top ports | DOUT naming (B2); macro name, DEF, slot (B3) |
| L3a | supply | rail table missing (M2); decap devices not in a netlist |
| all | LVS netlists | no rule set (M3) |

#### 4.9.2 Proposed rail table (P-A4)

| strap from the pad pair | blocks | decap | in the netlist as |
|---|---|---|---|
| analog | bias_genc, 8 x afe_chc, 8 x fs_oneshot_c + OR2, 8 x vhalf, Cref switch, samb inverter, TGATE wells | none required | net VDD |
| ADC main | 8 x cmp_p, digital macro | 0.125 nF, about 3 ohm in series | net VDD; decap = cap_nmos_03v3 instances at the top level |
| ADC DAC | bottom-plate drivers of 8 x dac_sw (pin `vdd_dac`) | 0.1 nF, about 3 ohm in series | net VDD_DAC behind one 10 ohm resistor device from the ADC main strap |

X2 S4 / S5 simulated exactly this split with the amplifiers on the main rail (the less favourable case) [adc/scripts/x2lib.py:179-191, x2_s5.py].

#### 4.9.3 Proposed LVS-netlist rules (P-A5)

One script (for example AFE/layout/scripts/mk_lvs_netlists.py) reads the simulation netlists and writes the LVS references; no hand edits.
1. `cap_mim_2f0_m2m3_noshield` -> `cap_mim_2f0_m4m5_noshield`.
2. Remove `Rbrk` (join vng with vn, vng2 with vn2), `Rt`, `Rmm`, `Cpb0-11`, `Cpbd`, `Cpm`.
3. `Cxa1`, `Cxa2` -> one `cap_mim_2f0_m4m5_noshield` 5 x 5 um each.
4. Cin: 2 pieces of 70.72 x 70.72 um per capacitor (or whatever L2a draws, as long as area and perimeter sum to the simulated value within 0.1 %).
5. Cref: one plate 59.07 x 59.07 um.
6. Resistors per P-A1.
7. Top: a SPICE top reference that instantiates the 8 channel cells, bias_genc, the decap and strap devices and the digital macro as a black box; the macro's powered gate-level netlist goes into LVS_VERILOG_FILES (the organizer's mixed-signal example does the same).
8. TGATE: use TGATE/TGATE.spice with VDD / VSS connected to the analog strap; standard cells inside `afe_ch` get VDD / VSS / VNW / VPW.

#### 4.9.4 Edits to AFE/prompts/layout_run.md (exact text)

1. Common rules, rule 1: replace "Decisions 1-43" by "Decisions 1-43 and AFE/review/AUDIT.md sections 2, 3 and 4.9".
2. Common rules, add: "9. Process option (verified in the PDK decks and the organizer table): variant D = 5 metals, 11 kA top metal, MIM option B (cap_mim_2f0_m4m5_noshield), high-resistance poly 1 kOhm/sq ONLY: `ppolyf_u_3k` does not exist in this variant. Run KLayout DRC and LVS with --variant=D."
3. Common rules, add: "10. LVS reference netlists are written by a script from the simulation netlists with the substitutions of AFE/review/AUDIT.md 4.9.3; never edit a simulation netlist for LVS."
4. L2a, after "from AFE/amp/spice/afe_chc.spice and fs_oneshot_c.spice.": add "The follower is the native-Vt 6 V NMOS nfet_06v0_nvt: in Step 1 take one such device through DRC and LVS; if the organizer has not confirmed the native-Vt option, report it at the top of the summary."
5. L1a: replace "vhalf (2 x 250 kOhm ppolyf_u_3k + 1 pF) and the floating reference Cref 7 pF (128 units) with its TGATE (Decision 42)" by "vhalf (2 x 250 kOhm in ppolyf_u_1k, drawn as one matched pair, + 1 pF) and the floating reference Cref 7 pF as ONE MIM plate (59.07 um side, as in vhalf.spice) with its TGATE (Decision 42); the two 40 fF preamp capacitors of cmp_p as one 5 x 5 um MIM unit each".
6. L1a: replace "two supply straps per Decision 40(e) (DAC drivers vs comparator+logic)" by "supply pins per AFE/review/AUDIT.md 4.9.2: `vdd` (vhalf, Cref switch, inverter), `vdd_cmp` (cmp_p), `vdd_dac` (the 13 bottom-plate drivers), one `vss`".
7. L1d, after "verify the tap delays at 5 corners after P&R.": add "Use AFE/review/scripts/sta_audit.py on the new netlist and compare with AFE/review/sim/sta_audit.log: the DAC-edge to comparator-clock time of ADC 0 must stay >= 21 ns at ff_n40 and the last window must end >= 20 ns before 333.3 ns at ss_125. The chain must branch from the same node that feeds the flop clock pins. If CTS cannot be made to work in the time box: no CTS, one hand-placed clock buffer. Run KLayout DRC (variant D) on the macro; the D3 flow skipped it. Then run AFE/review/scripts/run_tb_audit.sh gls with the new netlist: the failing assertions must be only X1.contention, X5.word0, X5.after33d, T11.crowbar."
8. L1b: add "and (g) the driver-gate overlap: the gate-level timing shows the PMOS and NMOS gate of one bit both on for up to 0.21 ns (AFE/review/sim/tb_audit_summary.log), not the 0.3 ns break-before-make of the D2-X2 testbenches: repeat one replay with that overlap; (h) one replay with ss analog models and the ff_n40 timing (AFE/review/scripts/mixcorner.py: 0.65 LSB on trial 1 pre-layout)."
9. L3a: replace "the three supply straps and guard rings of PLAN.md section 5" by "the supply straps of AFE/review/AUDIT.md 4.9.2 (decap and the 10 ohm strap resistor are devices in the LVS netlist) and the guard rings of PLAN.md section 5; no SCLK / CS / DIN / DOUT / cmp_clk / dac_g* wire within 20 um of a summing node, a pseudo-R, REC or the Cref node". Replace "pins on the edges per the organizer template (32 pads incl. REF" by "pins on the edges per the organizer template (32 pads incl. REF; the bidirectional pad needs the ports DOUT_OUT and DOUT_IN plus its 8 control pins".
10. L3b: replace "(3) the X2 S4 8-ADC staggered supply run (x2_s4.py) re-run on the extracted straps and the real pad/bond values" by "(3) the X2 S4 8-ADC staggered supply run (x2_s4.py) re-run on the extracted straps and the real pad/bond values, with the digital charge taken from the afe_dig power report (D3 macro: 24 pC per SCLK cycle typ, 27 pC at ff -40 C 3.6 V), not 1.5 pC per ADC per edge". Add "(5) all 8 amplifier channels on the one bias_genc: VDD ramp, RST_AMP for 100 ms after the bias is up, release: every output within 10 mV of 1.65 V; report the dip on vrs when the 8 channels reset together; (6) item 2 with 200 pA of pad leakage on E, REC and REF."
11. L4: replace "host power-up sequence from AFE/adc/README.md: RSTN low during the VDD ramp, wait >= 1 s, RST_AMP >= 100 ms" by "host power-up sequence: RSTN low during the VDD ramp, release RSTN while CS is high, wait >= 5 s (bias start-up with 8 channels is 3.6 s at ss -40 C), RST_AMP >= 100 ms, then check that every channel reads within 200 LSB of mid-scale, else repeat; protocol rules: RSTN changes only while CS is high, frames are always 160 clocks, CS is not raised early; the 2 uV noise figure needs a host low-pass to 300 Hz; REF must be connected; E and IPG signals stay inside 0..VDD; there is no power-down".

## 5. What was NOT verified, and why

- Anything that needs a layout: PEX, DRC, LVS, substrate coupling, the real strap resistances, the bridge-node parasitic. No analog layout exists.
- Monte Carlo of the DAC, the Cref switch, the pseudo-R pair, the reset replica and the Cin / Cf ratio (R5): the PDK has no local MIM mismatch model, and the pseudo-R sits on an unexplained model floor, so a mismatch run would not be evidence.
- An 8-channel amplifier + ADC transistor run and the 8-channel common reset (R10): a long run from power-up; proposed for L3b.
- The ADC replay with the vhalf divider at one third of its resistance (only needed if P-A1 is decided that way).
- The Cref threshold error at fs / sf and at the 3072 transition (42d); only ADC timing was run at fs / sf.
- Gate-level timing with the exact SDF: Icarus aborts in `$sdf_annotate` on this file (tried twice); replaced by the worst arc per cell output, no interconnect delays (<= 0.11 ns), no setup / hold checks. The capture-flop hold race was therefore not re-simulated; the D4 result (>= 0.8 ns) stands.
- dbs_ctrl timing and area after place and route (not hardened); its skew numbers are estimates.
- The pad cells: delay, leakage, supply current, and how the organizer connects the pad ring's core rails. The organizer's DEF, macro name and slot.
- The organizer statements are taken from public files fetched today; the process table sits under a heading that says "2025 Chipathon". They need the organizer's confirmation.
- Comparator and DAC energy at ff -40 C 3.6 V and ss 125 C 3.0 V (the 3.3 V values were used for power).
- ADS7953 power (no datasheet value in the repo).
- TGATE + real one-shot + amplifier in one netlist (aborted in A4c with the old tolerances; not retried here).
- Latch noise of the comparator.
- X2 was not repeated.
