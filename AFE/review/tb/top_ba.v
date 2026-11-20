`timescale 1ns/1ps
// AUDIT step 4: back-annotated COPY of the top wrapper AFE/top/dbs_afe_top.v (module dbs_afe_top).  The original file is not edited; it is still compiled for its module
// afe_ch (the channel cell, used here UNCHANGED).  Differences to dbs_afe_top:
//   * the outputs of adc8_top and dbs_ctrl pass through `assign #delay` elements that carry the STA-derived delays the RTL abstracts (values per corner in audit_delays.vh,
//     source AFE/review/sim/sta_audit.log).  With +define+GLS adc8_top is the HARDENED gate-level netlist with its SDF, so no delay is added on its outputs.
//   * dbs_ctrl is RTL in both builds (it is not in the hardened netlist): its NAND3 / inverter delays are ESTIMATES (T_SWB, T_SWI).
`include "audit_delays.vh"
module dbs_afe_top_ba (
    inout  [7:0] E, IPG, REC,
    inout        REF,
    input        CS, DIN, SCLK, RSTN,
    output       DOUT,
    output       DOUT_OE, DOUT_IE, DOUT_PD, DOUT_PU, DOUT_CS, DOUT_SL, DOUT_PDRV0, DOUT_PDRV1,
    output       CS_PU, CS_PD, DIN_PU, DIN_PD, SCLK_PU, SCLK_PD, RSTN_PU, RSTN_PD,
    inout        VDD, VSS
);
    wire dout_oe;
    assign DOUT_OE = dout_oe;
    assign DOUT_IE = 1'b0; assign DOUT_PD = 1'b0; assign DOUT_PU = 1'b0; assign DOUT_CS = 1'b0; assign DOUT_SL = 1'b0; assign DOUT_PDRV0 = 1'b0; assign DOUT_PDRV1 = 1'b0;
    assign CS_PU = 1'b0; assign CS_PD = 1'b0; assign DIN_PU = 1'b0; assign DIN_PD = 1'b0; assign SCLK_PU = 1'b0; assign SCLK_PD = 1'b0; assign RSTN_PU = 1'b0; assign RSTN_PD = 1'b1;

    wire        mode_o, rst_amp_o, dout_r;
    wire [7:0]  en_o, cmp_q, cmp_clk, rst_sw, tg_on, dac_gdn;
    wire [95:0] dac_gp, dac_gn;
    wire [7:0]  cmp_clk_r, rst_sw_r, tg_on_r, dac_gdn_r;
    wire [95:0] dac_gp_r, dac_gn_r;
    adc8_top u_adc (.cs_n(CS), .sclk(SCLK), .din(DIN), .rstn(RSTN), .dout(dout_r), .dout_oe(dout_oe),
                    .rst_amp_o(rst_amp_o), .mode_o(mode_o), .en_o(en_o),
                    .cmp_q(cmp_q), .cmp_clk(cmp_clk_r), .rst_sw(rst_sw_r), .tg_on(tg_on_r), .dac_gp(dac_gp_r), .dac_gn(dac_gn_r), .dac_gdn(dac_gdn_r));
`ifdef GLS
    assign DOUT = dout_r; assign cmp_clk = cmp_clk_r; assign rst_sw = rst_sw_r; assign tg_on = tg_on_r; assign dac_gdn = dac_gdn_r; assign dac_gp = dac_gp_r; assign dac_gn = dac_gn_r;
`else
    assign #(`T_DOUT) DOUT = dout_r;
    assign cmp_clk = cmp_clk_r;                              // chain delays are in the per-corner cell models (cells_sim.v, calibrated on the STA taps)
    assign #(`T_RST)  rst_sw  = rst_sw_r;                    // OR2 + buffer after trk
    assign #(`T_TG)   tg_on   = tg_on_r;                     // OR2 (the dlyd cell itself is modelled in the RTL)
    assign #(`T_GDN)  dac_gdn = dac_gdn_r;                   // OR2 + inverter
    assign #(`T_GPGN) dac_gp  = dac_gp_r;                    // latest clk->Q + gate arrival (worst case for the DAC -> comparator time)
    assign #(`T_GPGN) dac_gn  = dac_gn_r;
`endif

    wire [7:0] sw_rec, sw_rec_b, sw_ipg, sw_ipg_b;
    wire [7:0] sw_rec_r, sw_rec_b_r, sw_ipg_r, sw_ipg_b_r;
    dbs_ctrl #(.N(8)) u_dbs (.clk(SCLK), .rstn(RSTN), .mode(mode_o), .en(en_o), .ready(1'b1),
                             .sw_rec(sw_rec_r), .sw_rec_b(sw_rec_b_r), .sw_ipg(sw_ipg_r), .sw_ipg_b(sw_ipg_b_r));
    assign #(`T_SWB)          sw_rec_b = sw_rec_b_r;         // clk->Q + NAND3 (ESTIMATE)
    assign #(`T_SWB + `T_SWI) sw_rec   = sw_rec_r;           // + inverter (ESTIMATE): sw_rec lags sw_rec_b (I0 mismatch 8)
    assign #(`T_SWB)          sw_ipg_b = sw_ipg_b_r;
    assign #(`T_SWB + `T_SWI) sw_ipg   = sw_ipg_r;

    wire vbn, vcm, vg1, vcmo, vg2, vrs;
    bias_genc u_bias (.vbn(vbn), .vcm_in(vcm), .vg1(vg1), .vcm_out(vcmo), .vg2(vg2), .vrs(vrs), .vdd(VDD), .vss(VSS));

    genvar i;
    generate for (i = 0; i < 8; i = i + 1) begin : ch
        afe_ch u (.e(E[i]), .ipg(IPG[i]), .rec(REC[i]),
                  .sw_rec(sw_rec[i]), .sw_rec_b(sw_rec_b[i]), .sw_ipg(sw_ipg[i]), .sw_ipg_b(sw_ipg_b[i]),
                  .rst_amp(rst_amp_o),
                  .rst_sw(rst_sw[i]), .tg_on(tg_on[i]), .cmp_clk(cmp_clk[i]), .dac_gdn(dac_gdn[i]),
                  .dac_gp(dac_gp[12*i +: 12]), .dac_gn(dac_gn[12*i +: 12]), .cmp_q(cmp_q[i]),
                  .vbn(vbn), .vcm(vcm), .vg1(vg1), .vcmo(vcmo), .vg2(vg2), .vrs(vrs), .ref(REF), .vdd(VDD), .vss(VSS));
    end endgenerate
endmodule
