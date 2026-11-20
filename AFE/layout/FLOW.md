# FLOW.md: the layout flow as it was run in phase L2a (2026-11-20, Atharv's machine, one session)

Written by L2a for the later phases (L1a, L2b, L1b, L3a ...). Everything here was run, the evidence is in `AFE/layout/amp/` (logs, JSON reports, test cells).

## 1. Tool versions (python3 AFE/layout/scripts/flow.py versions)
KLayout 0.30.8, Magic 8.3.636, netgen 1.5.318, ngspice 46, python 3.12.3, image IIC-OSIC-TOOLS 2026.04, PDK gf180mcuD (variant D: 5 metals, 11 kA top metal, MIM option B). Host: aarch64 container,
8 cores, 7 GB RAM. Timings of this cell: generation 10 s, KLayout DRC 8 s (490 MB), Magic extraction + netgen LVS 1.2 s, PEX 1 s.

## 2. Commands (exactly as run; repository root, no wrapper)
| step | command | result |
|---|---|---|
| test cells (Step 1) | `bash AFE/layout/scripts/kl.sh AFE/layout/amp/mk_flowtest.py out=AFE/layout/amp/flowtest` | lp_flow.gds, lp_dummy.gds + .ref.spice |
| DRC | `python3 AFE/layout/scripts/flow.py drc --gds AFE/layout/amp/flowtest/lp_flow.gds --top lp_flow --out AFE/layout/amp/flowtest/flow` | 0 violations (also lp_dummy) |
| LVS | `python3 AFE/layout/scripts/flow.py lvs --gds .../lp_flow.gds --top lp_flow --ref .../lp_flow.ref.spice --out .../flow` | Circuits match uniquely (also lp_dummy) |
| PEX | `python3 AFE/layout/scripts/flow.py pex --gds .../lp_flow.gds --top lp_flow --out .../flow` | 5 devices, 25 C, MIM correction moved 0.2 fF |
| ngspice | `cd AFE/layout/amp/flowtest/ng && bash ../../../scripts/slot.sh ngspice -b op.spice` (job-local .spiceinit `set num_threads=1`) | .op runs, op.log |
| amp_ch generation | `bash AFE/layout/scripts/kl.sh AFE/layout/amp/mk_amp_ch.py out=AFE/layout/amp gds=amp_ch.gds` | amp_ch.gds, amp_ch.build.json, mk_amp_ch.log |
| amp_ch DRC | `python3 AFE/layout/scripts/flow.py drc --gds AFE/layout/amp/amp_ch.gds --top amp_ch --out AFE/layout/amp/flow` | 0 violations |
| amp_ch LVS | `python3 AFE/layout/scripts/flow.py lvs --gds AFE/layout/amp/amp_ch.gds --top amp_ch --ref AFE/layout/lvs/afe_chc.spice --out AFE/layout/amp/flow` | Circuits match uniquely. |
| facts DRC / LVS do not test | `bash AFE/layout/scripts/kl.sh AFE/layout/amp/check_amp.py gds=AFE/layout/amp/amp_ch.gds build=AFE/layout/amp/amp_ch.build.json outjson=AFE/layout/amp/check_amp.json` | W x H, areas, nothing under the Cin plates, pin labels |
| PEX feasibility (L2b owns the real run) | `python3 AFE/layout/scripts/flow.py pex --gds AFE/layout/amp/amp_ch.gds --top amp_ch --out AFE/layout/amp/pex_feasibility` and `ngspice -b` of `pex_feasibility/ng/op.spice` | 121 devices, 383 C, loads and runs one .op |
| gate | `python3 AFE/layout/scripts/gate.py L2a --gds AFE/layout/amp/amp_ch.gds --run` | see NOTES_L2.md |

LVS reference used: `AFE/layout/lvs/afe_chc.spice` (subckt amp_ch), the default of `mk_lvs_netlists.py` (`--cin-top sum`, no other option): it was NOT regenerated. The MIM terminal check says terminal 1 = top plate, and the drawn Cin
pieces are 70.65 um squares (reference 70.649028 um, +0.0014 %), inside the 1 % property tolerance. No `AFE/layout/amp/lvs/` exists.

## 3. MIM terminal check (Decision 46a, Step 1)
Cell lp_flow, one 5 x 5 um unit, top plate (Metal5 / FuseTop) labelled TOPNET, bottom plate (Metal4 lead) labelled BOTNET. Magic extracts
`X1 TOPNET BOTNET cap_mim_2f0_m4m5_noshield c_width=5u c_length=5u` (AFE/layout/amp/flowtest/flow/lp_flow.pex.spice, line "X1 TOPNET BOTNET") and netgen matches the reference `X3 TOPNET BOTNET cap_mim_2f0_m4m5_noshield`:
**terminal 1 = TOP plate on this machine too**, the references of AFE/layout/lvs/ (summing nodes listed first) are right as they are. The full cell confirms it: all 4 Cin pieces have vn / vp on the Metal5 plate and LVS matches.

## 4. Substitutions and things that differ from the prompts / SPEC (all deliberate, all in the generator)
1. **The PDK pcells have off-grid shapes** (DRC `*_OFFGRID`, 5 nm grid): the transistor pcells draw Metal1 gate pads with 1 nm coordinates (y = 2.289 um); `cap_mim` rounds sizes to 2 nm (44.595 -> 44.596) and places its Via4 sea on a
   1 nm grid (about 20,000 off-grid vias in the six big pieces). `amplib.snapped_copy` / `mim_snapped_copy` copy a pcell into a plain cell and grow the Metal1 / Metal2 boxes outward to 5 nm (never shrink), round FuseTop / CAP_MK / MIM_L_MK / Metal4 /
   Metal5 to the nearest 5 nm and shift each Via4 as a whole (its size must stay 0.26 um). Every device then has DRC 0 and the LVS sizes stay inside 1 %.
2. **pcell `bulk='Bulk Tie'` is unusable here**: it coerces W to >= 0.42 um, and in the first Step-1 run Magic put the drain port of the two devices on the well net (cause not investigated; the drawing with our own tie matched at once). The pseudo-resistor transistors (W 0.22) use `con_bet_fin=0` and their own N+ tie (0.42 x 0.5 um comp, DF.9 area 0.2025 um2,
   NP.3a / NP.5di: N+ at least 0.16 um from the P+ comp and 0.16 um beyond the N+ comp). `con_bet_fin=0` is also what gives W = 0.28 for the one-shot's 0.28u/40u transistor (default coerces to 0.36).
3. **A dummy transistor is a device for netgen** (lp_dummy: a transistor with gate = source = drain on one net stays an unmatched device; `nf=2` against `m=2` merges fine, "Merged 1 parallel devices"). Dummies are therefore
   POLY-ONLY lines on field oxide (min(L, 2 um) wide, 0.3 um beyond the comp, at both ends of the matched groups of amp_ch: input pair, tail mirror group, xm3 / xm4 mirror): they are no device in Magic and not in the reference. Diffusion dummies were not drawn.
4. **No `Bulk Tie` / `Guard Ring` pcell options anywhere**: `amplib.ring_cl` draws a P+ (substrate) or N+ ring with its own n-well (centre line on integer um, Metal1 ring 1 um wide, contacts, 0.16 um implant overlap).
5. Labels inside imported library cells (the 7t5v0 OR2 and filltie) would become ports of amp_ch in Magic: `amplib.or2_block` deletes them; pins are labelled exactly once, on the top cell (14 labels = the 14 pins of the reference).
6. Net names inside blocks are NOT labelled (a label becomes a pin); netgen's net-mismatch report names nets by their fan-out, which was enough (the first LVS of the full cell already matched uniquely, only 3 W property errors).

## 5. MIM design rules measured with the deck (DRC variant D), AFE/layout/amp/mk_mimtest.py and flowtest/mimsp_*.gds / mimst_*.gds
- two pieces with unrelated bottom plates: top plates 2.4 um apart are legal (bottom plates 1.2 um apart); 1.8 um is not (MIMTM.1).
- an UNRELATED Metal4 strap between two pieces must be >= 1.8 um from each top plate edge (= 1.2 um from the bottom plate edge): 1.5 um fails, 1.8 um passes.
- Metal4 that is part of a bottom plate polygon (tab, strap, pad) must be >= 1.2 um from the "virtual" region = FuseTop sized by 1.06 um clipped to that polygon, i.e. **>= 2.26 um from the top plate edge**: a pad 2.21 um away fails (MIMTM.1, corner
  case). The corridor between two pieces of one Cin block therefore needs 2.26 + 0.9 (strap) + 1.8 = 4.96 -> drawn 5.5 um.
- Via3 may not touch the bottom plate under FuseTop (MIMTM.10), a Metal4 tab outside the plate with Via4 -> Metal5 pad is legal (tested: tab 3 um, pad 1.2 x 1.2 um). Every piece has a sea of Via4 (0.26 um, 0.5 um spacing) over the top plate.

## 6. Generator structure (AFE/layout/amp/)
- `amplib.py` helpers: `Dev` (pcell instance + terminal rectangles found from the pcell geometry), `dev_block` (multi-finger array: S rail Metal1 below, gate bus Metal1 above with a 1 um landing pad, drains Via1 + Metal2 stubs to ONE Metal2 rail,
  ring), `add_tile` / `group_block` (single-finger devices with three 0.5 um Metal1 landing pads on integer coordinates), `pr_block` (pseudo-resistor pair, own wells), `mim_block` (MIM + tabs + 2 x 2 um Metal4 pads), `or2_block`,
  `compose`, `ring_cl`. **Every landing pad is on an integer um coordinate** so that the router grid (1.0 um pitch) meets it: the origin of every block is an integer.
- `router.py`: 1 um grid router, Metal2 / Metal3 / Metal4, 0.5 um wires and pads, Via1 only at Metal1 terminals; A* from the tree built so far; obstacles with the net they belong to; terminals with few access nodes are reserved; "halo" = soft clearance of
  about 2 um around the long wires of sensitive nets (cost, not a hard block); `hard` = extra clearance that only keeps other nets away (MIMTM.1). Wires of one net near (not overlapping) a fixed shape of the same net are blocked too (spacing).
- `blocks_amp.py`: the circuit as blocks with their nets (flattened net names of the reference); `mk_amp_ch.py`: Cin block (manual Metal5 / Metal4 geometry), rows, column, router, pins, GDS.
- Tool order for the next cell generator (L1a): write the blocks with integer-aligned landing pads, run the router for everything that is not a plate, run DRC, then LVS; the debug aid that saved most time was `AFE/layout/amp/drcsum.py <drc dir>`
  (rule, coordinates) and `shapes_at.py` (what is at x, y).
