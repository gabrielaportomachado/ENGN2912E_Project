`timescale 1ns/1ps
// Simulation models of the 6 std cells used in adc_dlychain / adc_clkgen / adc8_top (gf180mcu 7t5v0).  Delay-cell delays = per-cell averages inside the extracted chain (OpenSTA on the LibreLane netlist + SPEF, sim/d3_taps.log; dlyb is not in the chain: scaled estimate).
// Pick the corner with -DCORNER_TT (default) / -DCORNER_SS125 / -DCORNER_SSN40 / -DCORNER_FFN40 / -DCORNER_FF125.  Gate delays (and3, inv) are ESTIMATES scaled with the delay-cell ratio.
`ifdef CORNER_SS125
  `define DA 1.317
  `define DB 2.9
  `define DC 5.124
  `define DD 7.16
  `define DG 1.15
  `define DI 0.23
`elsif CORNER_SSN40
  `define DA 0.95
  `define DB 2.1
  `define DC 3.506
  `define DD 4.892
  `define DG 0.8
  `define DI 0.16
`elsif CORNER_FFN40
  `define DA 0.386
  `define DB 0.75
  `define DC 1.333
  `define DD 1.846
  `define DG 0.3
  `define DI 0.06
`elsif CORNER_FF125
  `define DA 0.534
  `define DB 1.1
  `define DC 1.962
  `define DD 2.729
  `define DG 0.4
  `define DI 0.08
`else
  `define DA 0.666
  `define DB 1.45
  `define DC 2.454
  `define DD 3.42
  `define DG 0.55
  `define DI 0.11
`endif
module gf180mcu_fd_sc_mcu7t5v0__dlya_1(I, Z); input I; output Z; assign #(`DA) Z = I; endmodule
module gf180mcu_fd_sc_mcu7t5v0__dlyb_1(I, Z); input I; output Z; assign #(`DB) Z = I; endmodule
module gf180mcu_fd_sc_mcu7t5v0__dlyc_1(I, Z); input I; output Z; assign #(`DC) Z = I; endmodule
module gf180mcu_fd_sc_mcu7t5v0__dlyd_1(I, Z); input I; output Z; assign #(`DD) Z = I; endmodule
module gf180mcu_fd_sc_mcu7t5v0__inv_1(I, ZN); input I; output ZN; assign #(`DI) ZN = ~I; endmodule
module gf180mcu_fd_sc_mcu7t5v0__and3_1(A1, A2, A3, Z); input A1, A2, A3; output Z; assign #(`DG) Z = A1 & A2 & A3; endmodule
