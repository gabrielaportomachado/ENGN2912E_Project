# Tapeout plan (Chipathon 2026, GF180MCU) - DRAFT, written 2026-11-12 by the monitoring session

Not yet reviewed by the user. Numbers marked ESTIMATE are not simulated. This file is separate
from NOTES.md on purpose (the A4b agent is editing NOTES.md); merge the decisions below into
NOTES.md "Decisions" after the user approves them.

## Requirements received (from the course/Chipathon organizer)
- Three groups share one frame: 2935 x 2935 um, core 2235 x 2235 um, 88 IO pads (22/side).
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
- Official deadline unconfirmed; aim to be ready before Thanksgiving (2026-11-26).

## Proposed Decision 29 (needs user approval): N = 4 channels
Reason: simplest plan that is still robust. The routing RTL is already parametric (rtl/dbs.v, parameter N),
so a 4-channel routing block needs no redesign. Pins, area, mux size, bias loading and layout effort all drop ~4x.
Keep everything parametric in N so 8 or 16 is a re-run, not a redesign. 16 channels stays the documented architecture
(ENGN 1600 design); N = 4 is the taped-out instance. Fallback if layout goes well: 8 (pin cost: +8 analog, +4 EN).
Consequences (ESTIMATES from existing numbers): aggregate rate 4 ch x 4 kS/s = 16 kS/s, frame period 62.5 us;
amplifier power ~4 x 245 uW ~ 1 mW (A4a typical); ADC mux 4:1 (4-bit frame ID kept, upper 2 bits 0);
follower-sink cost in the ADC-kick sweep: BM_KSF 24 = ~0.21 mW total, BM_KSF 36 = ~0.35 mW total (was 0.83 / 1.65 mW at 16 channels),
so the larger sink (36, worst error 0.317 LSB) becomes affordable. The A4b sweep still has nan corners: confirm all 9 before choosing.

## Draft pin list (N = 4) - io_type names to be mapped to the info.yaml template
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
Everything above that says 4 channels now reads 8. 8-channel numbers (ESTIMATES from existing simulated per-channel numbers, not new simulation):
- Area: 8 x 35-45k um2 = 0.28-0.36 mm2, + ADC ~0.017 mm2 + 8:1 mux + routing block + overhead -> ~0.4-0.55 mm2, report ~700 x 700 um (650-750). Still inside a ~1110 x 1110 um slot.
- Amplifier power ~8 x 245 uW ~ 2 mW (A4a typical, 74.4 uA x 3.3 V per channel). Aggregate 8 x 4 kS/s = 32 kS/s, frame period 31.25 us, T_ACQ = 31.25 us - 16/f_SCLK (26.7 us at 3.5 MHz).
- ADC-kick follower sink (extra over BM_KSF 6, 0.87 uA per unit typ): BM_KSF 24 -> ~0.41 mW total (worst error 0.499 LSB, no margin); BM_KSF 36 -> ~0.69 mW (0.317 LSB). Still pending: the sweep's nan corners.
- Mux 8:1, frame ID 4 bits kept (3 used). Layout: one replicated channel cell x 8 (about twice the placement/routing/PEX of N = 4, same cell work).

### Pins at N = 8 (io_type per the templates)
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
34. ONE 12-bit SAR ADC PER CHANNEL (N = 8), no analog mux: supersedes Decision 19's outcome (one SAR + mux). Each channel = amplifier + ADC; simultaneous sampling; 4 kS/s per channel; frame period 250 us per channel.
    ESTIMATE (scaled from D0: 0.017 mm2 per muxed ADC, ~0.27 mm2 for 16): ~0.13 mm2 for 8 ADCs, total block ~0.5-0.65 mm2 (a bit over 700 x 700 um, report ~750 x 750). ADC power ~ unchanged (D0 ~17 uW total).
    Interface needs a rework (8 converters on one DOUT): D0b in prompts/adc.md. The ADC-kick check in A4b is NOT removed: the acquisition window gets much longer (T_ACQ up to ~245 us) and the step is smaller if the ADC skips the 1.65 V reset,
    but A4b data still showed 0.4-2 mV (0.5-2.4 LSB) output displacement at 240 us at some ss/ff corners, so the follower-sink choice stays relevant at lower priority.
35. READY is tied to VDD inside the macro (rtl/dbs.v only uses it to gate the switch controls): no READY pad. REC[7:0] (the node after the routing switch, before the amplifier) are analog pads, all 8 simultaneously.
    Caution for L0: a REC pad adds ESD leakage/capacitance; with the routing switch open the REC node floats, so leakage can drift it and create an offset step to recover from.
Final pad list (31 pads; ~2 over a third of the budget; no spare for extra supply pairs: ask the organizer. Fallback if forced: REC on 4 channels = 27 pads):
 analog (24): E[7:0], IPG[7:0], REC[7:0]; input_cmos (2): CS, DIN; input_schmitt (2): SCLK, RSTN; bidirectional (1): DOUT; power VDD; ground VSS.
