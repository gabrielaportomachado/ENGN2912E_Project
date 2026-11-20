# L2a report (2026-11-20; Claude Sonnet 5.5 / high; converted from AFE/layout/NOTES_L2.md, AFE/layout/FLOW.md and AFE/layout/amp/gate_L2a.log by phase L1a, common rule 7)

Everything below is copied or condensed from the L2a session's own notes; no number is new. The "L2a findings" section and the Results-log row were copied unchanged into AFE/NOTES.md.

## 1. Summary and verdict
- amp_ch (afe_chc + fs_oneshot_c + OR2): **DRC 0 violations (official deck, variant D), LVS "Circuits match uniquely."** against subckt amp_ch of AFE/layout/lvs/afe_chc.spice (46 devices, 35 nets, 14 pins; reference NOT regenerated).
- **Gate verdict at the end of L2a: FAIL (1 FAIL), the slot: amp_ch as built is 219.25 x 385.25 um = 84,466 um2 against the slot 220 x 263 = 57,860 um2 (+46 %) and the F1 estimate 51,626 um2 (+64 %).** ACCEPT.md ladder A applies (open, see section 8).
- Native-Vt follower nfet_06v0_nvt (10u / 2u): passes DRC and LVS in the test cell and in amp_ch; the organizer has not confirmed it (ladder N if refused).
- MIM terminal order: terminal 1 of cap_mim_2f0_m4m5_noshield = TOP plate (Metal5 / FuseTop), as F1 assumed (check_env C3 and the Step-1 test cell), no `--cin-top rec` needed.

## 2. What was built
amp_ch.gds (sha1 b9407198f235d12f32265702ff358816556814b0, 3.0 MB) by AFE/layout/amp/mk_amp_ch.py (+ amplib.py, blocks_amp.py, router.py). Cin = 2 x 2 checkerboard of four 70.65 um pieces (summing nodes vn / vp on the TOP plates, nothing under the plates);
input pair ABBA 2 x (16 x 50u/2u) with poly-only dummies; P+ / N+ rings around every NMOS / PMOS block; the six pseudo-resistor transistors (pfet_03v3 0.22u/0.5u) drawn identically, minimum junction area, each with its own n-well; stage 2, follower
(nfet_06v0_nvt in a P+ ring), park TGATE, gate muxes, one-shot with C_T and the OR2 with filltie. Area table (um2): Cin block 27,554; pair + tail 9,705; mirror + xm6 10,244; stage 2 + sinks 7,018; MIM outside Cin 6,416; small devices 1,423; sum of the blocks 62,361;
cell bbox 84,466. The flow notes are in AFE/layout/FLOW.md.

## 3. Commands run
As in AFE/layout/FLOW.md section 2 (test cells mk_flowtest.py, flow.py drc / lvs / pex on them, mk_amp_ch.py, flow.py drc --gds AFE/layout/amp/amp_ch.gds --top amp_ch --out AFE/layout/amp/flow, flow.py lvs ... --ref AFE/layout/lvs/afe_chc.spice, check_amp.py,
PEX feasibility run, gate.py L2a --gds AFE/layout/amp/amp_ch.gds --run).

## 4. Results
| check | value | limit | PASS / WARN / FAIL | source log |
|---|---|---|---|---|
| DRC amp_ch (variant D) | 0 violations | 0 | PASS | AFE/layout/amp/flow/amp_ch.drc.json |
| LVS amp_ch | Circuits match uniquely (46 devices, 14 pins) | match | PASS | AFE/layout/amp/flow/amp_ch.lvs.json |
| slot (floorplan.py check item 5) | 219.25 x 385.25 um = 84,466 um2 | 220 x 263 um | **FAIL** | AFE/layout/amp/gate_L2a.log |
| nothing under the four Cin plates | under_cin_clean true | clean | PASS | AFE/layout/amp/check_amp.json |
| Cin : Cf1 ratio (formula of the netlists, ESTIMATE) | 99.972 | 100.0000 | PASS (within 0.03 %) | AFE/layout/amp/amp_ch.build.json |
| native-Vt follower | DRC 0, LVS match | accepted by the organizer? unknown | open (ladder N) | AFE/layout/amp/flowtest/flow/lp_flow.*.json |
| MIM terminal 1 | top plate | top plate | PASS | AFE/layout/amp/flowtest/flow/lp_flow.pex.spice |
| PEX feasibility (L2b owns the real run) | 121 devices, 383 C, loads and runs one .op | runs | PASS | AFE/layout/amp/pex_feasibility.log |

## 5. Gate output
Verbatim copy of AFE/layout/amp/gate_L2a.log (run by L2a on the final GDS; the floorplan line is the only FAIL):
```
gate.py L2a  (L2a --gds AFE/layout/amp/amp_ch.gds --run)
--- common
PASS  ACCEPT.md limits table equals AFE/layout/accept_limits.json
PASS  AFE/layout/REVIEW.md not edited by this phase
INFO  no open REVIEW.md item for L2a or an earlier phase
PASS  "## L2a findings" section in AFE/layout/NOTES_L2.md
PASS  Results-log row for L2a in AFE/layout/NOTES_L2.md
--- amp_ch layout: AFE/layout/amp/amp_ch.gds
PASS  DRC report belongs to the current GDS (sha1)
PASS  DRC ran with the official deck, variant D
PASS  DRC amp_ch: 0 violations
PASS  LVS report belongs to the current GDS (sha1)
PASS  LVS reference AFE/layout/lvs/afe_chc.spice is a generated reference of AFE/layout/lvs or the phase's own AFE/layout/<cell dir>/lvs
PASS  LVS amp_ch: Circuits match uniquely.
PASS  the reference was written by mk_lvs_netlists.py (header)
FAIL  floorplan.py check --gds amp_ch=AFE/layout/amp/amp_ch.gds: floorplan.py check: 16 PASS, 1 FAIL
      -> DO: ACCEPT.md ladder A (area) or G-5 (pin side); failing lines: FAIL  5  as-built amp_ch 219.25 x 385.25 um fits its slot 220.00 x 263.00 um  see AFE/layout/ACCEPT.md ladder "area"
GATE L2a: FAIL  (1 FAIL)
```

## 6. Ladder decisions
D-1 (off-grid shapes of the PDK pcells: snapped in the generator, FLOW.md section 4.1), L-1 (property error on the stage-2 pair and the 0.28u one-shot device: fixed in the drawing, `con_bet_fin=0` and four 0.5u/40u units). A (area): NOT applied, left to the next phase (the prompt of L2a allowed the FAIL).
G-3 not needed (terminal order as F1 assumed).

## 7. Deviations
Pins: rec / ref on Metal5 at the top edge, vbn .. vrs on Metal3 at the top-left corner, sw_rec / sw_rec_b / rst_amp Metal2 on the west edge, vdd / vss Metal4 3 x 3 um at the top-right, out Metal3 on the bottom (inner) edge; Metal2 / Metal3 pins are 0.5 um wide;
the channel is wider than the slot anyway, so L3a re-places the pin wires (ACCEPT.md G-5). Not drawn: the Metal1 vss guard around the summing-node connections (the router has no guard feature), two-dimensional centroid of the input pair (ABBA rows only), diffusion dummies
(poly-only dummy lines instead: a dummy transistor is a device for netgen). `Bulk Tie` pcell option unusable (coerces W >= 0.42 um): own N+ / P+ ties. Full list: AFE/layout/FLOW.md section 4.

## 8. Open issues and risks
1. **Area**: 84,466 um2 vs the slot 57,860 um2; 8 channels of amp_ch alone = 0.676 mm2 = 68 % of the 1000 x 1000 um outline; the levers named in NOTES_L2.md (finger width 25 um instead of 50 um for xm3 / xm4 / xm6 / the pair, the 3 um gate landing pads and rings, the 60 um of white space right of row 4,
   the stage-2 MIM column that is only 75 % full) are not used yet. See also the L1a report (section 8): with adc_ch at 33,564 um2 the chip does not fit even with perfect packing.
2. Wire lengths of the summing nodes (ESTIMATE): vn about 290 um, vp 280, vn2 550 um (s2pair is on the other side of the cell from the stage-2 capacitor column), rec 280, v1 540: the first suspects if L2b misses f_hi / noise / PSRR (ladder R-2, R-3, R-6, R-8).
3. vdd / vss are routed like signals (about 560 / 860 um of 0.5 um wire): IR drop for L2b; L3a replaces them by straps.
4. The native-Vt device is unconfirmed by the organizer (ladder N).

## 9. REVIEW.md items handled
None (REVIEW.md had no item when L2a ran and none when this conversion was written).

## 10. Files changed and commit
AFE/layout/amp/ (mk_amp_ch.py, amplib.py, blocks_amp.py, router.py, amp_ch.gds, amp_ch.build.json, check_amp.py / .json / .log, mk_flowtest.py, mk_mimtest.py, drcsum.py, shapes_at.py, flow/, flowtest/, pex_feasibility/, gate_flow/, drc.log, lvs.log),
AFE/layout/FLOW.md, AFE/layout/NOTES_L2.md. Commits 16fe280 (checkpoint) and 1b3076a (L2a final) on branch worktree-l2a-amp = main at the start of L1a. This report was written by L1a (commit 36cb8d8 on branch worktree-l1a-adc).
