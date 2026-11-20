`timescale 1ns/1ps
// Zero-delay FUNCTIONAL models of the standard cells that AFE/dig/afe_dig.v instantiates by hand (clock buffer, routing-switch output pairs, DOUT_OE inverter, tie cells), for the RTL simulations
// (AFE/top/run_top_sim.sh dig).  Zero delay on purpose: tb_top.v compares REC / IPG with a zero-delay `dbs` reference 0.05 ns after every change.  The other hand-instantiated cells
// (dlya / dlyb / dlyc / dlyd, inv_1, and3_1 of the comparator clock chain) are modelled in AFE/adc/tb/cells_sim.v; the OR2 of afe_ch in AFE/top/stubs_analog.v.
// Gate-level simulations use the PDK models (-DFUNCTIONAL) with the SDF-derived delays of AFE/review/scripts/gen_gl.py instead of this file.
module gf180mcu_fd_sc_mcu7t5v0__clkbuf_20 (I, Z);  input I; output Z;  assign Z = I;     endmodule
module gf180mcu_fd_sc_mcu7t5v0__clkbuf_8  (I, Z);  input I; output Z;  assign Z = I;     endmodule
module gf180mcu_fd_sc_mcu7t5v0__clkinv_4  (I, ZN); input I; output ZN; assign ZN = ~I;   endmodule
module gf180mcu_fd_sc_mcu7t5v0__clkinv_20 (I, ZN); input I; output ZN; assign ZN = ~I;   endmodule
module gf180mcu_fd_sc_mcu7t5v0__tieh      (Z);     output Z;           assign Z = 1'b1;  endmodule
module gf180mcu_fd_sc_mcu7t5v0__tiel      (ZN);    output ZN;          assign ZN = 1'b0; endmodule
