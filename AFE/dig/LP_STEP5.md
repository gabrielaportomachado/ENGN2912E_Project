# LP step 5: digital macro afe_dig, de-risked (2026-11-20)

Summary of the LP trial (the work of the LP fork, finished and re-checked in LP-finish). Every number is from the file named. L1d re-runs this recipe and freezes the result (layout_run.md L1d).

## What exists
| file | what |
|---|---|
| AFE/dig/afe_dig.v | the macro: dbs_ctrl #(.N(8)) + adc8_top (unchanged RTL) + ONE clock buffer u_ckbuf (clkbuf_20, Decision 44h) feeding every flop clock and the comparator delay chain from one net `sclk_i` + 16 switch output pairs (clkinv_4 / clkbuf_8 from one node, I0 mismatch 8) + 15 tie cells for the pad-control pins (14 tiel, RSTN_PD tieh; Decision 46e) + DOUT_OE = ~CS (clkinv_20) |
| AFE/dig/mk_dig_cfg.py | LibreLane config.json + DEF template + pins_plan.json from AFE/layout/floorplan.json (pins snapped to the 0.56 um track grid; height >= 105.84 um with routing up to Metal4; `--clock cts` kept for experiments only) |
| AFE/dig/run_dig.sh | hardening (~1-2 min) in $AFE_DIG_RUN (default /tmp/lp_dig, never on the host disk) + collect_dig.py -> AFE/dig/reports/, AFE/dig/trial/ |
| AFE/dig/scripts/ | collect_dig.py (structure checks), drc_dig.sh (official KLayout DRC variant D: LibreLane skips it for gf180mcuD), power_dig.py, sw_pair_cells.py, sta_taps.py (timing for tb_adc_timing.py), lyrdb_count.py |
| AFE/dig/dbs_afe_top_dig.v, mk_top_dig.py, tb_padctl.v, cells_dig_sim.v, top_ba_dig.v | equivalence and gate-level benches (run_top_sim.sh dig, run_tb_audit.sh dig) |
| AFE/dig/trial/ | afe_dig.pnl.v (powered netlist, LVS port order), afe_dig.lef, afe_dig_pins.json (as built), run_dir.txt. The GDS stays in the run directory (L1d copies it to AFE/dig/final/) |

## Results of the trial
| check | result | source |
|---|---|---|
| equivalence with the RTL top (adc8_top + dbs_ctrl + 15 ties) | EQUIV PASS: 0 differing log lines, all 15 pad-control constants right | AFE/dig/sim/top_dig.log (re-run in LP-finish) |
| die / utilisation | 819.84 x 109.76 um, 1706 cells, 43.0 %, 167 flops, routing up to Metal4 (Metal5 free for the top) | reports/flow_summary.rpt |
| pins | 286 signal pins, all at the planned place; N / S Metal2 (channels 0-3 / 4-7), W Metal3 | flow_summary.rpt, floorplan.py check --dig-pins (18 PASS) |
| STA, 5 corners, 500 ns, 0.5 ns uncertainty | setup ws 91.69 ns (ss_125) .. 96.97 ns, hold ws 0.229 ns (ff_n40) .. 2.01 ns; 0 violations; max-slew / max-cap 0 / 0 (D3 macro: 16 / 3) | flow_summary.rpt |
| route / Magic DRC / LVS / antenna | 0 / 0 / 0 / 0 | flow_summary.rpt |
| KLayout DRC variant D | 0 violations in 660 rules, 3:36 wall, 645 MB | reports/klayout_drc.log |
| (a) DAC edge -> comparator clock ADC 0, ff_n40 | 22.14 ns (limit 21.0) | reports/sta_audit_dig.log |
| (c) last window end -> next SCLK edge at the flop clocks, ss_125 | 22.39 ns (limit 20.0); against the SCLK pin 20.59 ns | sta_audit_dig.log |
| decision -> code register slack at 3 MHz, ss_125 | 13.75 ns (D3: 14.25) | sta_audit_dig.log |
| clock latency SCLK pin -> flops | 0.54-0.64 ns (ff_n40) .. 1.73-1.83 ns (ss_125); chain input on the same node | sta_audit_dig.log section 8 |
| sw_rec / sw_rec_b and sw_ipg pair skew | <= 0.78 ns (ss_125) | sta_audit_dig.log section 7 |
| gate-level testbench, 5 corners + MIXED, 2 / 3 MHz, 3 scenarios | only X1.contention, X5.word0, X5.after33d, T11.crowbar (+ T2.settle at MIXED) | AFE/dig/sim/tb_audit_dig_summary.log |
| supply charge | 33.7 pC per SCLK cycle tt 3.3 V, 38.4 pC ff -40 C 3.6 V (D3: 24 / 27; X2 assumed 12) | reports/power_dig.log |
| LVS top with the macro | mk_lvs_netlists.py --decap-n 74,64 --dig-netlist AFE/dig/trial/afe_dig.pnl.v; check_lvs_netlists.py A, B, C PASS (C2: netgen reads SPICE top + Verilog macro, 2493 instances) | AFE/layout/lvs/check_lvs_netlists.log |
| run cost | LibreLane 1:02 wall, 549 MB peak, run directory 183 MB | flow_summary.rpt |

## Notes for L1d
1. CTS: not used (TritonCTS puts the comparator delay chain on the clock root net). The clock-buffer form is the pre-approved fallback (Decision 44h, ACCEPT.md C-1) and passes every limit.
2. Warnings worth one line in the L1d report (reports/warnings_summary.log): RSZ-0020 "2 floating nets" (identify them in the final run: expected = unused outputs), RSZ-0062 during
   repair (the final STA has no violation), EST-0026 for net CS (estimate only; the route has 0 errors).
3. The tie cells are inside the macro, so the LVS top has no 0-ohm devices; DOUT_IN stays the one disconnected top-level pin.
