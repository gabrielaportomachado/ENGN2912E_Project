`ifdef SYNTHESIS
(* blackbox *) module TGATE (input IN, input C, input CBAR, output OUT);
endmodule
`else
// cmos inst_name (out, in, ctrl, ctrl_bar)
module TGATE (input IN, input C, input CBAR, output OUT);
    cmos tgate_inst(OUT, IN, C, CBAR);
endmodule
`endif
