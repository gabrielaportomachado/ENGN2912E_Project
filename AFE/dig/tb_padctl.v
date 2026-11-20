`timescale 1ns/1ps
// tb_padctl: second top-level module of `bash AFE/top/run_top_sim.sh dig`.  tb_top.v checks only 3 of the 15 constant pad-control pins; this checks all 15 at the ports of the
// device under test (tb_top.dut) against the values of AFE/top/dbs_afe_top.v / info.yaml (all 0 except RSTN_PD = 1), once at 1 us and at every later change.  One line: PADCTL PASS / PADCTL FAIL.
module tb_padctl;
    wire [14:0] v = {tb_top.dut.DOUT_IE, tb_top.dut.DOUT_PD, tb_top.dut.DOUT_PU, tb_top.dut.DOUT_CS, tb_top.dut.DOUT_SL, tb_top.dut.DOUT_PDRV0, tb_top.dut.DOUT_PDRV1,
                     tb_top.dut.CS_PU, tb_top.dut.CS_PD, tb_top.dut.DIN_PU, tb_top.dut.DIN_PD, tb_top.dut.SCLK_PU, tb_top.dut.SCLK_PD, tb_top.dut.RSTN_PU, tb_top.dut.RSTN_PD};
    localparam [14:0] WANT = 15'b000000000000001;
    reg armed = 0;
    initial begin
        #1000;
        if (v === WANT) $display("PADCTL PASS: DOUT_IE DOUT_PD DOUT_PU DOUT_CS DOUT_SL DOUT_PDRV0 DOUT_PDRV1 CS_PU CS_PD DIN_PU DIN_PD SCLK_PU SCLK_PD RSTN_PU = 0, RSTN_PD = 1 (read %b)", v);
        else            $display("PADCTL FAIL: read %b, want %b", v, WANT);
        armed = 1;
    end
    always @(v) if (armed && v !== WANT) $display("PADCTL FAIL at %0t: read %b, want %b", $time, v, WANT);
endmodule
