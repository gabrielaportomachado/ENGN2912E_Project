# Tapeout plan (Chipathon 2026, GF180MCU)

Written from 2026-11-12 on by the monitoring session as a running log. The decisions in it were approved by the user and are recorded in AFE/NOTES.md
(Decisions 29-45), which is the reference. Numbers marked ESTIMATE are not simulated. F1 (2026-11-20) added the CURRENT STATE section below and marked every
older section that no longer holds as SUPERSEDED (the old text is kept as history; do not take numbers from a SUPERSEDED section).

## CURRENT STATE (2026-11-20, after Decisions 44 and 45; kept up to date by the phases)
- Chip: N = 8 channels (Decision 29); per channel: routing TGATEs, LFP amplifier (60 dB, 0.2-650 Hz), its own 12-bit SAR ADC (Decision 34), simultaneous sampling at CS falling, 4 kS/s per channel
  (host timed), one SPI port: 160-clock frame, word 0 = config {RST_AMP, MODE, EN[7:0]} on DIN, word 1 = config readback, words 2-9 = {ID, code} of channel 0-7 on DOUT (Decisions 37, 38, 41).
  Single 3.3 V supply (Decision 30), no CLK / READY / MODE / EN pads (routing control clocked by SCLK, READY tied high inside), no 5 V domain, no analog mux.
- Pads: 24 (Decision 45; the TA asked for fewer pads and a smaller block: REC pads dropped, fallback N = 2). Pin list for info.yaml:

| Pad | io_type | Top-cell ports (AFE/top/dbs_afe_top.v) | Note |
|---|---|---|---|
| E[7:0] | analog (8) | E[7:0] | electrode contacts (to the record and IPG routing TGATEs) |
| IPG[7:0] | analog (8) | IPG[7:0] | stimulation side; signals must stay inside 0..VDD |
| REF | analog (1) | REF | shared reference electrode -> amplifier `ref` input of all 8 channels (Decision 41) |
| CS | input_cmos | CS, CS_PU = 0, CS_PD = 0 | SPI chip select; falling edge = sampling instant of all 8 channels |
| DIN | input_cmos | DIN, DIN_PU = 0, DIN_PD = 0 | config word 0 |
| SCLK | input_schmitt | SCLK, SCLK_PU = 0, SCLK_PD = 0 | 2 MHz nominal, 3 MHz maximum; the only clock of the chip |
| RSTN | input_schmitt | RSTN, RSTN_PU = 0, RSTN_PD = 1 | asynchronous reset, pad pull-down ON |
| DOUT | bidirectional | DOUT_OUT (to pad A), DOUT_IN (from pad Y, unused), DOUT_OE = ~CS, DOUT_IE = DOUT_PD = DOUT_PU = DOUT_CS = DOUT_SL = DOUT_PDRV0 = DOUT_PDRV1 = 0 | serial data out; drives only while CS is low (Decisions 41d, 44b) |
| VDD | power | VDD | one 3.3 V pad |
| VSS | ground | VSS | one ground pad |

  17 analog + 5 digital + 2 supply = 24. REC[7:0] are NOT pads (REC = record TGATE output = amplifier input is an internal net; the ADC data shows the same signal).
  The port names follow the organizer template (resources/info.yaml: `<name>_OUT` / `<name>_IN` and 8 control pins for a bidirectional pad, `<name>_PU` / `<name>_PD` for an input pad; every control pin driven).
- Block outline given to the organizer: 1000 x 1000 um (gds/dbs_afe_top.gds, top cell dbs_afe_top, PR boundary only until L3a replaces it with the layout of the same outline).
  Area ESTIMATE 0.87 mm2 (935 x 935 um; pessimistic 1.00 mm2 = 998 x 998 um, i.e. no margin against the outline in the pessimistic case), AFE/review/sim/f1_area.log (the audit had 0.86 / 0.98 mm2 before the 1 kOhm/sq poly made the ladders and dividers 3x longer).
- Power: 2.09 mW typ in record mode (3.26 mW ff 85 C, 1.37 mW ss -40 C), 0.63 mA; no power-down (AFE/review/sim/f1_power_total.log).
- Supply: one pad pair, three straps (analog; ADC-main with 0.125 nF MOS decap; ADC-DAC behind 10 ohm with 0.1 nF), 0.225 nF = 0.057-0.071 mm2 (Decision 44d). SCLK 0.64 MHz minimum, 2 MHz nominal, 3 MHz maximum (Decision 40c).
- Layout / LVS inputs: AFE/layout/PLAN.md section 9 (pins), AFE/layout/lvs/ (LVS references written by AFE/layout/scripts/mk_lvs_netlists.py), AFE/prompts/layout_run.md (phases).
- Host rules, power-up sequence, test plan: AFE/adc/README.md.
- OPEN with the organizer (Decision 44k): macro name and DEF, slot size and pad positions, whether the VDD / VSS pair is ours alone and can be double bonded, native-Vt nfet_06v0_nvt allowed
  (the follower uses it), high-resistance poly 1 kOhm/sq only (the netlists use only ppolyf_u_1k since F1), bond-wire inductance. Fallback if 8 channels are refused: N = 2 (Decision 45).

## Requirements received (from the course/Chipathon organizer)
- Three groups share one frame: 2935 x 2935 um, core 2235 x 2235 um, 88 IO pads (22/side). (Later information: the organizer README states a 2040 x 2040 um design area and the TA plans 5 projects per frame; our outline is 1000 x 1000 um, 24 pads, Decision 45.)
  Plan for ONE THIRD: about 29 pads and about 1.66 mm2 (equal share, unconfirmed). Unknown: whether power pads count in the 88.
- Repo (public GitHub, one per group, submission pulled from main): info.yaml (title, team, description,
  path to lvs_config.json, path to export-control doc, pin list name + io_type), lvs_config.json (top cell,
  GDS path, LVS netlist path), gds/<top_cell>.gds (core only), LVS netlist (gate-level Verilog for digital,
  SPICE for analog), documents/Export_Control_GF_Rev8.2.docx (technical answers, signature blank),
  README (block diagram, pin description, short test plan).
- Templates: github.com/sscs-ose/sscs-chipathon-2026/blob/main/resources/{info.yaml,lvs_config.json,documents/Export_Control_GF_Rev8.2.docx};
  fork from github.com/Mauricio-xx/chipathon-2026-gf180mcu-padring; examples chipathon-2026-AI_Byte (digital),
  chipathon-2026-A44-SAR-ADC (analog). The comments at the end of info.yaml define the port names each pad type needs
  (for example <name>_OE, <name>_IE, <name>_PU for bidirectional): READ THEM before fixing top-level ports; drive every control pin.
- Due Fri 2026-11-13: repo link, pin list (name + type) and total count, estimated block size (W x H, um).
- Official deadline: 2026-11-30 (organizer, told to the user 2026-11-20; Decision 49). Thanksgiving 2026-11-26 is in the middle: plan no human step for 11-26 / 11-27.

## Proposed Decision 29 (needs user approval): N = 4 channels
**SUPERSEDED** (2026-11-12): N = 8 was approved (Decision 29); the mux, MODE / EN / CLK / READY pads and the 5 V domain below no longer exist. History only.
Reason: simplest plan that is still robust. The routing RTL is already parametric (rtl/dbs.v, parameter N),
so a 4-channel routing block needs no redesign. Pins, area, mux size, bias loading and layout effort all drop ~4x.
Keep everything parametric in N so 8 or 16 is a re-run, not a redesign. 16 channels stays the documented architecture
(ENGN 1600 design); N = 4 is the taped-out instance. Fallback if layout goes well: 8 (pin cost: +8 analog, +4 EN).
Consequences (ESTIMATES from existing numbers): aggregate rate 4 ch x 4 kS/s = 16 kS/s, frame period 62.5 us;
amplifier power ~4 x 245 uW ~ 1 mW (A4a typical); ADC mux 4:1 (4-bit frame ID kept, upper 2 bits 0);
follower-sink cost in the ADC-kick sweep: BM_KSF 24 = ~0.21 mW total, BM_KSF 36 = ~0.35 mW total (was 0.83 / 1.65 mW at 16 channels),
so the larger sink (36, worst error 0.317 LSB) becomes affordable. The A4b sweep still has nan corners: confirm all 9 before choosing.

## Draft pin list (N = 4) - io_type names to be mapped to the info.yaml template
**SUPERSEDED**: the pin list is the 24-pad table in CURRENT STATE (Decisions 32, 35, 41, 45).
| Pin | Dir | Type | Note |
|---|---|---|---|
| E[3:0] | in/out | analog | electrode contacts (to amp inputs via TGATE REC path) |
| IPG[3:0] | in/out | analog | stimulation side |
| CS | in | digital | SPI chip select (CS falling = sample) |
| SCLK | in | digital | SPI clock, mode 0, also clocks the conversion |
| DOUT | out | digital | 16-bit frame {ID, 12-bit code}, MSB first |
| RSTN | in | digital | async active-low reset |
| MODE | in | digital | 0 = treat (IPG), 1 = record |
| EN[3:0] | in | digital | per-channel enable |
| CLK | in | digital | routing config clock (config DFFs use it) |
| READY | in | digital | routing FSM ready input (rtl/dbs.v) |
| VDD3 | pwr | power | 3.3 V amp + ADC |
| VDD5 | pwr | power | 5 V routing/TGATE domain |
| VSS | pwr | power | ground |
Signal pins 4+4+1+1+1+1+1+4+1+1 = 19; with 3 supply pads 22 (of ~29). ~7 spare: reserve for 2-3 analog test points
(e.g. channel-0 amp output, VCM_OUT tap, bias monitor) and a second VSS. Decide the test points after L2.
Open: is REC an internal node (assumed yes: amp inputs connect to the routing block, no REC pads)?

## Block size estimate (ESTIMATE, not simulated)
**SUPERSEDED** by AFE/review/AUDIT.md 4.5: 0.86 mm2 for N = 8 with one ADC per channel.
Per channel ~35-45k um2 (2 x 10,000 um2 Cin MIM + ~3k other MIM + OTA/bias gate area ~13k um2 drawn x layout overhead).
4 channels ~0.14-0.18 mm2; ADC ~0.017 mm2 (D0) plus 4:1 mux; routing block small; routing/guard overhead 30-50 %.
Total ~0.25-0.35 mm2, report as roughly 600 x 600 um (range 500-700 per side). Replace with the extracted number after L3.

## Layout-phase prompts: AFE/prompts/layout.md (L0-L4)
Run after the amp A4b and ADC D1-D4 results exist; L1/L2 may start in parallel with the end of A4b if their inputs are frozen.
Known layout risks to plan for (from NOTES.md): 4-6 TOhm pseudo-R is a PDK-model floor (unverified in silicon); MIM matching is
an ASSUMPTION; shared vcm_in/vcm_out taps couple channels; ADC VDD = VREF needs board decoupling; amp 3.3 V vs routing 5 V crossings.

## UPDATE 2026-11-12 after fetching the templates (user approved: N = 4, no REC pads)
Source: a fetch subagent's PARAPHRASED report of sscs-ose resources/info.yaml + lvs_config.json, the Mauricio-xx padring fork, and the two example repos.
Re-read the raw files before submission; do not copy values from this summary.

### What the templates say
- io_type has exactly 7 values: ground, power, input_cmos, input_schmitt, bidirectional, bidirectional_24ma, analog. There is NO output-only type: outputs are `bidirectional`.
  Every bidirectional pad needs its control pins tied (_PD, _PU, _CS, _SL, _IE, _OE, _PDRV0/1; the 24 mA type has no PDRV). input pads have optional _PD/_PU controls that must also be driven.
  `analog` pads connect to ASIG5V (5 V-rated ESD pad, a signal pad, not a power pad). Pad control glue lives inside the macro wrapper (AI_Byte example).
- Examples are MACROS, not whole chips: A44_A and A02_A are 1110 x 1110 um user macros with an organizer-supplied DEF (89 / 146 abutment pins), top cell name = macro name,
  and info.yaml lists only the pad cells (15 and 22 entries). So "a third of 88 pads" and a ~1110 um square slot per group are consistent with 3 x 1110^2 in the core.
  We need OUR macro name and OUR organizer DEF: ask the organizer. (Template placeholder top cell: A01_topcell.)
- lvs_config.json: STD_CELL_LIBRARY gf180mcu_fd_sc_mcu7t5v0; analog example gives LVS_SPICE_FILES, digital example gives LVS_VERILOG_FILES; a mixed design (ours) fills both, as A44 does.
- Padring fork: die 2935 um, but its core is 2051 x 2051 um (442..2493), not 2235 as in the announcement; 8 supply pads in total (4 DVDD, 4 DVSS) for the whole frame; 60 analog + 20 bidir pads; the
  fork's "88" only matches if the 8 supply pads are counted. Ask the organizer which core number and which pad allocation are right.

### Revised draft pin list for info.yaml (21 pads; replaces the table above)
**SUPERSEDED**: see CURRENT STATE. In particular DOUT_OE is NOT tied to 1: DOUT_OE = ~CS (Decision 41d), and the pad DOUT needs the two ports DOUT_OUT / DOUT_IN (Decision 44b).
| Pin | io_type | Note |
|---|---|---|
| E[3:0] (4 entries) | analog | electrode contacts |
| IPG[3:0] (4 entries) | analog | stimulation side |
| CS, MODE, CLK, READY, EN[3:0] (8 entries) | input_cmos | |
| SCLK, RSTN | input_schmitt | clock and reset want hysteresis |
| DOUT | bidirectional | only way to get an output; tie _OE=1, _IE=0, _PD=_PU=0, set _PDRV/_SL/_CS in the wrapper |
| VDD | power | |
| VSS | ground | |
Spare: ~8 of ~29. More supply pads are likely needed for 16 kS/s-class mixed-signal noise isolation; ask how many DVDD/DVSS pads our slot gets.

### NEW DECISION NEEDED (Decision 30): supply voltage
**DECIDED**: option (a), single 3.3 V (Decision 30). TGATE at 3.3 V: Ron 4-21 kOhm typ, 34 kOhm at ss -40 C (AFE/review/sim/tgate_ron.log); the digital macro is hardened at 3.3 V corners.
The pad ring offers one power and one ground type (DVDD / DVSS), with no separate 3.3 V and 5 V rails. The amp and ADC are 3.3 V designs; the routing block (TGATE, std cells 7t5v0) was
verified at 5 V. Options: (a) run the whole chip from a single 3.3 V DVDD (A44 does this): re-check TGATE Ron and the FSM at 3.3 V and drop the 5 V -> 3.3 V crossing logic (simplest, rule 10);
(b) 5 V DVDD plus an on-chip regulator for 3.3 V (extra block, noise, area); (c) a 3.3 V supply on an analog pad (not a power pad: unsuitable for the current). Recommendation: (a), then simulate the
routing block and TGATE at 3.3 V in L0/L3. Note the IPG stimulation swing is set by the external generator; the pad is rated 5 V.

## APPROVED by the user, 2026-11-12 (merge into NOTES.md "Decisions" when the A4b agent is idle)
29. N = 4 channels, all blocks parametric in N; 16 channels remains the documented architecture. No REC pads (amp inputs connect internally to the routing block).
30. Single 3.3 V DVDD for the whole chip (amp, ADC, routing block, pads); no 5 V domain and no on-chip regulator. Consequences to verify (L0/L3): TGATE Ron and the dbs FSM/std cells (7t5v0)
    at 3.3 V; drop the 5 V -> 3.3 V level crossings (rstn, fast-settle); IPG stimulation amplitude is set externally (analog pad is 5 V-rated).
31. Planning frame: core 2235 x 2235 um (announcement figure; the padring fork says 2051 - unresolved, plan with 2235, keep the block small enough for either). Pad plan: ~29 per group, 21 used.
OPEN with the organizer (user does not know): our macro name / DEF / slot size; whether power pads count in the 88 and how many DVDD/DVSS pads our slot gets.

## REVISION 2026-11-12 (user): N = 8 channels (supersedes N = 4 in Decision 29; Decisions 30-31 unchanged)
**PARTLY SUPERSEDED**: N = 8 stands. The 8:1 mux, the 31.25 us frame, T_ACQ = 31.25 us - 16/f_SCLK and the follower-sink sweep below belong to the one-shared-ADC plan, replaced by one ADC per channel (Decisions 34, 37: no mux, 250 us frame, T_ACQ 240-244 us, sink stays at BM_KSF 6).
Everything above that says 4 channels now reads 8. 8-channel numbers (ESTIMATES from existing simulated per-channel numbers, not new simulation):
- Area: 8 x 35-45k um2 = 0.28-0.36 mm2, + ADC ~0.017 mm2 + 8:1 mux + routing block + overhead -> ~0.4-0.55 mm2, report ~700 x 700 um (650-750). Still inside a ~1110 x 1110 um slot.
- Amplifier power ~8 x 245 uW ~ 2 mW (A4a typical, 74.4 uA x 3.3 V per channel). Aggregate 8 x 4 kS/s = 32 kS/s, frame period 31.25 us, T_ACQ = 31.25 us - 16/f_SCLK (26.7 us at 3.5 MHz).
- ADC-kick follower sink (extra over BM_KSF 6, 0.87 uA per unit typ): BM_KSF 24 -> ~0.41 mW total (worst error 0.499 LSB, no margin); BM_KSF 36 -> ~0.69 mW (0.317 LSB). Still pending: the sweep's nan corners.
- Mux 8:1, frame ID 4 bits kept (3 used). Layout: one replicated channel cell x 8 (about twice the placement/routing/PEX of N = 4, same cell work).

### Pins at N = 8 (io_type per the templates)
**SUPERSEDED**: option C was taken (Decision 32) and then changed by Decisions 35, 37, 41, 45; READY and CLK are not pads. See CURRENT STATE.
| Group | Pins | io_type | Count |
|---|---|---|---|
| Electrodes, stimulation | E[7:0], IPG[7:0] | analog | 16 |
| Control, parallel enables | CS, MODE, CLK, READY, EN[7:0] | input_cmos | 12 |
| Clock/reset | SCLK, RSTN | input_schmitt | 2 |
| Data out | DOUT | bidirectional | 1 |
| Supplies | VDD, VSS | power / ground | 2 |
Option A (baseline, no routing change): 33 pads = 4 over the ~29 plan; no spare for extra supply pads or test points.
Option B: use SCLK as the routing clock (drop CLK; config registers and FSM clocked while the MCU clocks SCLK): 32 pads. Still over.
Option C (RECOMMENDED, needs user approval; reverses Decision 18's "no DIN"): serial configuration on the same SPI port. Add DIN; a 9-bit shift register (MODE + EN[7:0]) in a NEW wrapper under AFE/
  (rtl/ stays untouched) loaded in a CS-framed write, then fed to dbs as mode/en. Pads: 16 analog + CS, SCLK, RSTN, DIN, DOUT, READY (tied or pad) + VDD, VSS = 24, leaving ~5 for extra supply pairs and test points.
  Cost: ~9 flops + a few gates of new digital, one new SPI write frame (D-phase, spec in L0). Pin count stays 24 if the user later asks for N = 16 (only analog pads grow: +16 -> 40, over budget; so 8 is the ceiling for a third).

## APPROVED by the user, 2026-11-12 (second batch; merge with 29-31 into NOTES.md when the A4b agent is idle)
29 (revised). N = 8 channels (supersedes N = 4); 30. single 3.3 V DVDD; 31. 2235 um core planning frame.
32. Option C: serial configuration on the SPI port. New DIN pin; MODE + EN[7:0] loaded through a 9-bit shift register in a NEW wrapper under AFE/ (rtl/ untouched), framed by CS.
    Reverses Decision 18's "no DIN" (user approved). Pad count 24: analog E[7:0], IPG[7:0]; CS, SCLK, RSTN, DIN, READY (input), DOUT (bidirectional); VDD, VSS. L0 specifies the write-frame format.

## REVISION 2026-11-12 (user, from group): per-channel ADC; raw recording pins on all 8 channels simultaneously; READY tied high
**PARTLY SUPERSEDED**: Decision 34 (one ADC per channel) and READY tied high stand. The REC[7:0] pads of Decision 35 were DROPPED on 2026-11-20 (Decision 45); the 31-pad list below is history.
34. ONE 12-bit SAR ADC PER CHANNEL (N = 8), no analog mux: supersedes Decision 19's outcome (one SAR + mux). Each channel = amplifier + ADC; simultaneous sampling; 4 kS/s per channel; frame period 250 us per channel.
    ESTIMATE (scaled from D0: 0.017 mm2 per muxed ADC, ~0.27 mm2 for 16): ~0.13 mm2 for 8 ADCs, total block ~0.5-0.65 mm2 (a bit over 700 x 700 um, report ~750 x 750). ADC power ~ unchanged (D0 ~17 uW total).
    Interface needs a rework (8 converters on one DOUT): D0b in prompts/adc.md. The ADC-kick check in A4b is NOT removed: the acquisition window gets much longer (T_ACQ up to ~245 us) and the step is smaller if the ADC skips the 1.65 V reset,
    but A4b data still showed 0.4-2 mV (0.5-2.4 LSB) output displacement at 240 us at some ss/ff corners, so the follower-sink choice stays relevant at lower priority.
35. READY is tied to VDD inside the macro (rtl/dbs.v only uses it to gate the switch controls): no READY pad. REC[7:0] (the node after the routing switch, before the amplifier) are analog pads, all 8 simultaneously.
    Caution for L0: a REC pad adds ESD leakage/capacitance; with the routing switch open the REC node floats, so leakage can drift it and create an offset step to recover from.
Final pad list (31 pads; ~2 over a third of the budget; no spare for extra supply pairs: ask the organizer. Fallback if forced: REC on 4 channels = 27 pads):
 analog (24): E[7:0], IPG[7:0], REC[7:0]; input_cmos (2): CS, DIN; input_schmitt (2): SCLK, RSTN; bidirectional (1): DOUT; power VDD; ground VSS.

Group sketch (2026-11-12, confirms Decision 35): E[i] -> routing TGATE (record path) -> node REC[i] (analog pad) that also feeds amp[i] + ADC[i]; all channels' digital outputs go to one DOUT.
Implement the shared DOUT as a digital serializer (daisy-chained capture/shift registers or a channel mux into one output flop), not a tri-state/wired bus. The IPG (stimulation) path is not drawn; it stays as in the routing block.

Stimulation amplitude (group, 2026-11-12): the chip is simulation/bench only and does not handle real IPG signals, so the IPG test amplitude is free to choose. Planning value: keep IPG test signals within 0-3.3 V (<= VDD) so the 3.3 V
routing switch passes them without body-diode conduction. Closes the "IPG amplitude" question under Decision 30; Decision 30 stands. State "not for real stimulation or connection to a person" in the README (NOTES.md already says this).

## RE-ESTIMATE 2026-11-12/13 (N = 8, one ADC per channel, 31 pads). ALL AREA NUMBERS ARE ESTIMATES (not layout).
**SUPERSEDED** by AFE/review/AUDIT.md 4.5 / 4.6 (area 0.86 mm2, power 2.1 mW) and by the 24-pad list.
Per amplifier channel (from NOTES.md A3/A4a drawn-area figures): MIM 2 x 10,000 (Cin1) + 1,490 (Cin2) + 990 (Cc2) + 142 (Cf2) + Cf1 ~ 22.8k um2 (MIM not overlaid on circuits);
transistor gate area OTA1 ~12.4k (pair 2 x 1.6k, load 9.2k) + bias sink 1.5k + stage 2 0.5k + OTA1 stage-2/Cc1 ~1-2k = ~16k, x 1.5-2 layout overhead = 24-32k.  -> 47-55k um2 per amplifier channel.
Per ADC (D0 estimate 0.017 mm2 for one SAR incl. 16.4 pF cap DAC, comparator, logic): ~15-20k um2.  Per channel (amp + ADC): ~62-75k um2.  x 8 = 0.50-0.60 mm2.
Add routing block + TGATEs + DIN shift register + serializer + shared bias ~0.02-0.04 mm2, then guard rings, decoupling, routing channels, whitespace 25-40 % -> 0.65-0.85 mm2.
=> report ~900 x 900 um (range 800-950 per side). The earlier "750 x 750" was optimistic: it undercounted the amplifier gate area and layout overhead. Fits a 1110 x 1110 um slot (1.23 mm2) at ~55-70 % utilization.
If the organizer's slot is smaller, levers (in order): overlay MIM caps above circuits, trade Cin (noise vs gain), cut to N = 4 (~0.35-0.45 mm2, ~600 x 600 um).
Power (ESTIMATE): amplifiers ~8 x 245 uW = 2 mW typical; ADCs ~17-20 uW total (D0, ADC power ~independent of mux vs per-channel at the same total sample rate).
Pads: 31 (24 analog E/IPG/REC, 2 input_cmos CS/DIN, 2 input_schmitt SCLK/RSTN, 1 bidirectional DOUT, VDD, VSS). With one more supply pair (VDD+VSS x 2, advisable for mixed-signal noise) 33.

## RE-ESTIMATE 2 (after D0b, 2026-11-13): the supply decap changes the block size. ESTIMATES.
**SUPERSEDED**: decap is 0.225 nF = 0.057-0.071 mm2 at the PDK density of 3.98 fF/um2 (Decisions 40e, 44d; not 0.72 nF / 0.16 mm2 at 4.6 fF/um2), block total 0.86 mm2; SCLK is 2 MHz nominal and 3 MHz maximum (Decision 40c; not 1-5 MHz); 24 pads.
D0b (AFE/adc/PLAN.md section D0b): 8 ADCs + shared digital = 0.136 mm2 (agrees with the 0.13 mm2 above); on-chip supply decap for staggered conversions 0.72 nF = ~0.16 mm2 (simultaneous: 0.47 mm2);
the decap density 4.6 fF/um2 is NOT checked in the PDK, the 2 nH package inductance is ASSUMED. Block total with decap: ~0.8-1.0 mm2 (0.65-0.85 above + 0.16) -> report ~1000 x 1000 um (range 900-1150) against a ~1110 x 1110 um slot (1.23 mm2): TIGHT.
Levers for L0 (in order of cost): (1) place the MOS decap UNDER the MIM capacitors (the MIM sits in upper metal; ~0.16 mm2 of Cin MIM exists), check the GF180 MIM/decap stacking rules and the noise coupling; (2) monotonic / energy-saving DAC switching
(2-4x less supply charge, ESTIMATE from the literature, evaluate first in D2); (3) N = 4 (~0.45-0.6 mm2, ~700 x 700 um); (4) a bigger slot from the organizer.
Frame/pin consequences from D0b: DIN carries config in word 0 of a 160-SCLK frame; DOUT carries 8 x 16-bit words; dbs is clocked by SCLK (no CLK pad), SCLK 1-5 MHz recommended (0.64 MHz minimum); CS from an MCU hardware timer (jitter <= 85 ns rms). Pad list unchanged (31).

## UPDATE 2026-11-14 (phase I1, Decision 41): 32 pads
**PARTLY SUPERSEDED**: the REF pad and the RSTN pull-down stand; the count is 24 since Decision 45 (no REC pads), so the REC fallbacks below are moot.
One shared analog pad REF (reference electrode) is added and wired to the `ref` input of all 8 amplifier channels (afe_chc.ref). Final list: analog (25): E[7:0], IPG[7:0], REC[7:0], REF; input_cmos (2): CS, DIN; input_schmitt (2): SCLK, RSTN;
bidirectional (1): DOUT; power VDD; ground VSS = 32 pads. 32 EXCEEDS the ~29 planning share (one third of 88) by 3; it is subject to the organizer's pad allocation (still unanswered: macro name/DEF, whether power pads count).
FALLBACK if the organizer cannot give 32: drop REF and tie every afe_ch `ref` to vcm (the shared VCM_IN tap): single-ended recording, no reference-electrode common-mode rejection (A3: REC-only gain identical, 39.869 dB), documented as such;
the second fallback of the earlier plan (REC pads on 4 channels only) is unchanged. RSTN pad: pull-down enabled (pad-control tie RSTN_PD = 1) so the chip stays in reset until the host drives RSTN.

