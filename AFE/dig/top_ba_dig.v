`timescale 1ns/1ps
// top_ba_dig.v (LP step 5 / L1d): the top wrapper `dbs_afe_top_ba` of the audit testbench (AFE/review/tb/tb_audit.v) for the hardened macro afe_dig.
// Same ports and the same internal names that tb_audit.v reads (dut.sw_rec, dut.mode_o, dut.en_o, dut.sw_rec_r, dut.ch[i].u ...) as AFE/review/tb/top_ba.v, but the digital part is ONE
// instance of the gate-level netlist of afe_dig (delay-annotated copy written by AFE/review/scripts/gen_gl.py <corner> <out> <final dir> afe_dig): dbs_ctrl, the clock buffer, the
// switch output pairs and the 15 pad-control tie cells are inside, so no estimated delay element is added here (top_ba.v adds T_SWB / T_SWI estimates for dbs_ctrl).
// The instance is called u_adc because tb_audit.v names `dut.u_adc` in its (unused) $sdf_annotate line.  Module afe_ch comes UNCHANGED from AFE/top/dbs_afe_top.v.
// mode_o / en_o are internal nets of the macro: they are read here by hierarchical name (the netlist keeps the names `mode_o` and `\en_o[i] `; AFE/dig/scripts/run_gls_dig.sh checks that).
module dbs_afe_top_ba (
    inout  [3:0] E, IPG,
    inout  [3:0] REC,
    inout        REF,
    input        CS, DIN, SCLK, RSTN,
    output       DOUT_OUT,
    input        DOUT_IN,
    output       DOUT_OE, DOUT_IE, DOUT_PD, DOUT_PU, DOUT_CS, DOUT_SL, DOUT_PDRV0, DOUT_PDRV1,
    output       CS_PU, CS_PD, DIN_PU, DIN_PD, SCLK_PU, SCLK_PD, RSTN_PU, RSTN_PD,
    inout        VDD, VSS
);
    wire        rst_amp_o;
    wire [3:0]  cmp_q, cmp_clk, rst_sw, tg_on, dac_gdn;
    wire [47:0] dac_gp, dac_gn;
    wire [3:0]  sw_rec, sw_rec_b, sw_ipg, sw_ipg_b;
    afe_dig u_adc (.CS(CS), .SCLK(SCLK), .DIN(DIN), .RSTN(RSTN), .DOUT(DOUT_OUT), .DOUT_OE(DOUT_OE), .rst_amp_o(rst_amp_o),
                   .sw_rec(sw_rec), .sw_rec_b(sw_rec_b), .sw_ipg(sw_ipg), .sw_ipg_b(sw_ipg_b),
                   .cmp_q(cmp_q), .cmp_clk(cmp_clk), .rst_sw(rst_sw), .tg_on(tg_on), .dac_gp(dac_gp), .dac_gn(dac_gn), .dac_gdn(dac_gdn),
                   .DOUT_IE(DOUT_IE), .DOUT_PD(DOUT_PD), .DOUT_PU(DOUT_PU), .DOUT_CS(DOUT_CS), .DOUT_SL(DOUT_SL), .DOUT_PDRV0(DOUT_PDRV0), .DOUT_PDRV1(DOUT_PDRV1),
                   .CS_PU(CS_PU), .CS_PD(CS_PD), .DIN_PU(DIN_PU), .DIN_PD(DIN_PD), .SCLK_PU(SCLK_PU), .SCLK_PD(SCLK_PD), .RSTN_PU(RSTN_PU), .RSTN_PD(RSTN_PD));
    // names that tb_audit.v reads
    wire       mode_o = u_adc.mode_o;
    wire [3:0] en_o   = {u_adc.\en_o[3] , u_adc.\en_o[2] , u_adc.\en_o[1] , u_adc.\en_o[0] };
    wire [3:0] sw_rec_r = sw_rec, sw_ipg_r = sw_ipg;        // "raw" switch controls of top_ba.v: here the macro pins themselves (the hazard counter then sees the real gate-level outputs)

    wire vbn, vcm, vg1, vcmo, vg2, vrs;
    bias_genc u_bias (.vbn(vbn), .vcm_in(vcm), .vg1(vg1), .vcm_out(vcmo), .vg2(vg2), .vrs(vrs), .vdd(VDD), .vss(VSS));

    wire vdd_dac;
    afe_rstrap                u_rstrap (.a(VDD), .b(vdd_dac), .vss(VSS));
    afe_decap #(.C_NF(0.125)) u_dcm    (.p(VDD), .n(VSS));
    afe_decap #(.C_NF(0.0475)) u_dcd    (.p(vdd_dac), .n(VSS));

    genvar i;
    generate for (i = 0; i < 4; i = i + 1) begin : ch
        afe_ch u (.e(E[i]), .ipg(IPG[i]), .rec(REC[i]),
                  .sw_rec(sw_rec[i]), .sw_rec_b(sw_rec_b[i]), .sw_ipg(sw_ipg[i]), .sw_ipg_b(sw_ipg_b[i]),
                  .rst_amp(rst_amp_o),
                  .rst_sw(rst_sw[i]), .tg_on(tg_on[i]), .cmp_clk(cmp_clk[i]), .dac_gdn(dac_gdn[i]),
                  .dac_gp(dac_gp[12*i +: 12]), .dac_gn(dac_gn[12*i +: 12]), .cmp_q(cmp_q[i]),
                  .vbn(vbn), .vcm(vcm), .vg1(vg1), .vcmo(vcmo), .vg2(vg2), .vrs(vrs), .ref(REF), .vdd(VDD), .vdd_cmp(VDD), .vdd_dac(vdd_dac), .vss(VSS));
    end endgenerate
endmodule
