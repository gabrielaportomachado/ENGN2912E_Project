// AUDIT step 4: per-corner delays for the back-annotated testbench.  Sources:
//   digital (T_*): AFE/review/sim/sta_audit.log (OpenSTA on the hardened adc8_top, nom SPEF): T_GPGN = latest gp/gn arrival; T_RST / T_TG / T_GDN = CS -> rst_sw, OR2 part of tg_on, dac_gdn;
//                  T_DOUT = SCLK fall -> dout (max).  T_SWB / T_SWI (dbs_ctrl clk->Q + NAND3, inverter) are ESTIMATES scaled with the corner (dbs_ctrl is not hardened yet).
//   analog requirements: TSET  = DAC settling to 0.5 LSB needed before the comparator clock [AFE/adc/NOTES.md D4: 15.1 ns ff -40 3.6 V, 22.6 typ, 35.8 ss 125 3.0 V; D2: 24.0 ss -40;
//                                ff 125 3.6 V is an ESTIMATE between ff -40 and typ]
//                        TDEC  = comparator decision time at small overdrive [AFE/review/sim/mixcorner.log: 0.99 ff -40 3.6 V, 1.58 typ, 2.02 ss 125 3.6 V; ss 125 3.0 V ESTIMATE 2.6;
//                                ss -40: D1 1.8], TCRST = comparator output back to the reset value after cmp_clk falls [D4 race: tapw -> outp 0.79 / 1.14 / 1.83 ns less inv + and3]
//   MIXED = fastest std-cell timing (ff_n40) with SLOW 3.3 V analog (ss -40 C 3.6 V): TSET 24.0 (D2 ss -40 at 3.3 V; mixcorner.log shows 0.65 LSB left at 21.4 ns), TDEC 1.63
`ifndef AUDIT_DELAYS_VH
`define AUDIT_DELAYS_VH
`ifdef CORNER_FFN40
  `define T_GPGN 3.62
  `define T_RST  0.63
  `define T_TG   0.40
  `define T_GDN  0.55
  `define T_DOUT 0.90
  `define T_SWB  0.60
  `define T_SWI  0.08
  `ifdef MIXED
    `define TSET  24.0
    `define TDEC  1.63
    `define TCRST 0.55
  `else
    `define TSET  15.1
    `define TDEC  0.99
    `define TCRST 0.46
  `endif
`elsif CORNER_FF125
  `define T_GPGN 5.02
  `define T_RST  0.87
  `define T_TG   0.55
  `define T_GDN  0.75
  `define T_DOUT 1.26
  `define T_SWB  0.85
  `define T_SWI  0.11
  `define TSET  20.0
  `define TDEC  1.40
  `define TCRST 0.50
`elsif CORNER_SSN40
  `define T_GPGN 8.28
  `define T_RST  1.47
  `define T_TG   0.95
  `define T_GDN  1.30
  `define T_DOUT 2.12
  `define T_SWB  1.40
  `define T_SWI  0.20
  `define TSET  24.0
  `define TDEC  1.80
  `define TCRST 0.60
`elsif CORNER_SS125
  `define T_GPGN 11.48
  `define T_RST  2.06
  `define T_TG   1.35
  `define T_GDN  1.85
  `define T_DOUT 2.97
  `define T_SWB  2.00
  `define T_SWI  0.28
  `define TSET  35.8
  `define TDEC  2.60
  `define TCRST 0.74
`else
  `define T_GPGN 6.01
  `define T_RST  1.06
  `define T_TG   0.68
  `define T_GDN  0.90
  `define T_DOUT 1.51
  `define T_SWB  1.00
  `define T_SWI  0.14
  `define TSET  22.6
  `define TDEC  1.58
  `define TCRST 0.57
`endif
`endif
