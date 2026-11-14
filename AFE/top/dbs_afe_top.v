`timescale 1ns/1ps
// dbs_afe_top: chip top level for the Chipathon macro (I0, 2026-11-14).  Digital part = rtl/dbs.v (dbs_ctrl, N = 8, read only) + AFE/adc/rtl/adc8_top (SPI frame, config word, 8 SAR logics);
// analog part = 8 x afe_ch (routing TGATEs + REC park + amplifier + fs one-shot + ADC DAC/comparator) + 1 x bias_genc.  Single 3.3 V supply (Decision 30).  READY is tied high (Decision 35).
//
// WHY dbs_ctrl + TGATE and not the dbs module: dbs wraps dbs_ctrl + the 2N TGATEs but does not bring sw_rec / sw_rec_b out, and the amplifier reset trigger and the REC park need exactly those two nets.
// The TGATEs therefore sit inside afe_ch; the wiring is the same as dbs.v lines 99-106 (rec_tg: C = sw_rec, CBAR = sw_rec_b; ipg_tg: C = sw_ipg, CBAR = sw_ipg_b).  tb_top.v compares REC / IPG against a real `dbs #(8)` instance.
//
// Pads (31, as AFE/TAPEOUT.md / info.yaml): analog E[7:0] IPG[7:0] REC[7:0]; input_cmos CS DIN; input_schmitt SCLK RSTN; bidirectional DOUT; power VDD; ground VSS.
// The pad control pins below (DOUT_*, *_PU, *_PD) follow the NAMING in info.yaml's header comment; the exact names / polarities come from the organizer's template and are NOT verified (template not re-read in this phase).
module dbs_afe_top (
    inout  [7:0] E, IPG, REC,
    input        CS, DIN, SCLK, RSTN,
    output       DOUT,
    output       DOUT_OE, DOUT_IE, DOUT_PD, DOUT_PU, DOUT_CS, DOUT_SL, DOUT_PDRV0, DOUT_PDRV1,
    output       CS_PU, CS_PD, DIN_PU, DIN_PD, SCLK_PU, SCLK_PD, RSTN_PU, RSTN_PD,
    inout        VDD, VSS
);
    // ---- pad glue: DOUT drives only while CS is low (adc8_top dout_oe); input pads get no pull ----
    wire dout_oe;
    assign DOUT_OE = dout_oe;                       // tri-state while CS is high (the MCU may share the MISO line); info.yaml draft said OE = 1: see NOTES I0 finding
    assign DOUT_IE = 1'b0; assign DOUT_PD = 1'b0; assign DOUT_PU = 1'b0; assign DOUT_CS = 1'b0; assign DOUT_SL = 1'b0; assign DOUT_PDRV0 = 1'b0; assign DOUT_PDRV1 = 1'b0;   // values: PLACEHOLDERS
    assign CS_PU = 1'b0; assign CS_PD = 1'b0; assign DIN_PU = 1'b0; assign DIN_PD = 1'b0; assign SCLK_PU = 1'b0; assign SCLK_PD = 1'b0; assign RSTN_PU = 1'b0; assign RSTN_PD = 1'b0;

    // ---- serial interface, config word, 8 SARs ----
    wire        mode_o, rst_amp_o;
    wire [7:0]  en_o, cmp_q, cmp_clk, rst_sw, tg_on, dac_gdn;
    wire [95:0] dac_gp, dac_gn;
    adc8_top u_adc (.cs_n(CS), .sclk(SCLK), .din(DIN), .rstn(RSTN), .dout(DOUT), .dout_oe(dout_oe),
                    .rst_amp_o(rst_amp_o), .mode_o(mode_o), .en_o(en_o),
                    .cmp_q(cmp_q), .cmp_clk(cmp_clk), .rst_sw(rst_sw), .tg_on(tg_on), .dac_gp(dac_gp), .dac_gn(dac_gn), .dac_gdn(dac_gdn));

    // ---- routing control (rtl/dbs.v), clocked by SCLK (no CLK pad, Decision 37), READY tied high ----
    wire [7:0] sw_rec, sw_rec_b, sw_ipg, sw_ipg_b;
    dbs_ctrl #(.N(8)) u_dbs (.clk(SCLK), .rstn(RSTN), .mode(mode_o), .en(en_o), .ready(1'b1),
                             .sw_rec(sw_rec), .sw_rec_b(sw_rec_b), .sw_ipg(sw_ipg), .sw_ipg_b(sw_ipg_b));

    // ---- shared bias (one per chip): vcmd = ADC DAC reset level + comparator reference (VDD/2) ----
    wire vbn, vcm, vg1, vcmo, vg2, vrs, vcmd;
    bias_genc u_bias (.vbn(vbn), .vcm_in(vcm), .vg1(vg1), .vcm_out(vcmo), .vg2(vg2), .vrs(vrs), .vdd(VDD), .vss(VSS));
    assign vcmd = vcmo;     // PLACEHOLDER (I0 finding): no VDD/2 tap for the ADC exists in bias_genc; every ADC sim used an IDEAL source.  Same net as vcm_out only until L2 decides.

    // ---- 8 channels ----
    genvar i;
    generate for (i = 0; i < 8; i = i + 1) begin : ch
        afe_ch u (.e(E[i]), .ipg(IPG[i]), .rec(REC[i]),
                  .sw_rec(sw_rec[i]), .sw_rec_b(sw_rec_b[i]), .sw_ipg(sw_ipg[i]), .sw_ipg_b(sw_ipg_b[i]),
                  .rst_amp(rst_amp_o),
                  .rst_sw(rst_sw[i]), .tg_on(tg_on[i]), .cmp_clk(cmp_clk[i]), .dac_gdn(dac_gdn[i]),
                  .dac_gp(dac_gp[12*i +: 12]), .dac_gn(dac_gn[12*i +: 12]), .cmp_q(cmp_q[i]),
                  .vbn(vbn), .vcm(vcm), .vg1(vg1), .vcmo(vcmo), .vg2(vg2), .vrs(vrs), .vcmd(vcmd), .vdd(VDD), .vss(VSS));
    end endgenerate
endmodule

// afe_ch: ONE channel = the cell L2 lays out (amplifier + park + routing TGATEs + one-shot + ADC analog).  Pin list: AFE/layout/PLAN.md section 9.
module afe_ch (
    inout        e, ipg, rec,                       // electrode pad, IPG pad, REC pad (= amplifier input node)
    input        sw_rec, sw_rec_b, sw_ipg, sw_ipg_b,// routing switch controls from dbs_ctrl (C / CBAR of the two TGATEs)
    input        rst_amp,                           // RST_AMP config bit level (adc8_top rst_amp_o), common to all channels
    input        rst_sw, tg_on, cmp_clk, dac_gdn,   // adc8_top bit i
    input  [11:0] dac_gp, dac_gn,                   // adc8_top bits 12*i+11 .. 12*i
    output       cmp_q,
    input        vbn, vcm, vg1, vcmo, vg2, vrs, vcmd, vdd, vss
);
    // routing switches (5 V-device TGATE macro, TGATE/TGATE.v; dbs.v wiring)
    TGATE rec_tg (.OUT(rec), .IN(e), .C(sw_rec), .CBAR(sw_rec_b));
    TGATE ipg_tg (.OUT(ipg), .IN(e), .C(sw_ipg), .CBAR(sw_ipg_b));

    // amplifier reset: one-shot started by the edge that closes the record switch (C net), OR-ed with RST_AMP
    wire fs_os, fs;
    fs_oneshot_c u_os (.trig(sw_rec), .fs(fs_os), .vbn(vbn), .vdd(vdd), .vss(vss));
    (* keep *) gf180mcu_fd_sc_mcu7t5v0__or2_1 u_or (.A1(fs_os), .A2(rst_amp), .Z(fs));

    // amplifier with REC park (pkc = CBAR = HIGH while the record switch is open = park ON; pkcb = C)
    wire amp_out;
    // ref: the amplifier's second input has NO pad (I0 finding); tied to the shared vcm_in tap
`ifdef SIM_STUBS
    wire [11:0] sim_amp_out, sim_vs, sim_dacv;
`endif
    afe_chc u_amp (.rec(rec), .ref(vcm), .out(amp_out), .vdd(vdd), .vss(vss), .vbn(vbn), .vcm(vcm), .vg1(vg1), .vcmo(vcmo), .vg2(vg2), .vrs(vrs),
                   .fs(fs), .pkc(sw_rec_b), .pkcb(sw_rec)
`ifdef SIM_STUBS
                   , .sim_out(sim_amp_out)
`endif
    );

    // ADC analog: split-cap DAC + switches, comparator.  rstm = rst = rst_sw (D4 wiring); samb = ~tg_on (local inverter); gdp tied high (Decision 37 / D4)
    wire samb, t, m;
    (* keep *) gf180mcu_fd_sc_mcu7t5v0__inv_1 u_samb (.I(tg_on), .ZN(samb));
    dac_sw u_dac (.vin(amp_out), .t(t), .m(m), .vcm(vcmd), .vdd(vdd), .vss(vss), .rst(rst_sw), .rstm(rst_sw), .sam(tg_on), .samb(samb),
                  .gp0(dac_gp[0]), .gp1(dac_gp[1]), .gp2(dac_gp[2]), .gp3(dac_gp[3]), .gp4(dac_gp[4]), .gp5(dac_gp[5]), .gp6(dac_gp[6]), .gp7(dac_gp[7]), .gp8(dac_gp[8]), .gp9(dac_gp[9]), .gp10(dac_gp[10]), .gp11(dac_gp[11]),
                  .gdp(vdd),
                  .gn0(dac_gn[0]), .gn1(dac_gn[1]), .gn2(dac_gn[2]), .gn3(dac_gn[3]), .gn4(dac_gn[4]), .gn5(dac_gn[5]), .gn6(dac_gn[6]), .gn7(dac_gn[7]), .gn8(dac_gn[8]), .gn9(dac_gn[9]), .gn10(dac_gn[10]), .gn11(dac_gn[11]),
                  .gdn(dac_gdn)
`ifdef SIM_STUBS
                  , .sim_vin(sim_amp_out), .sim_vs(sim_vs), .sim_dacv(sim_dacv)
`endif
    );
    wire cmp_qn;
    cmp_p u_cmp (.inp(vcmd), .inn(t), .clk(cmp_clk), .outp(cmp_q), .outn(cmp_qn), .vdd(vdd), .vss(vss)
`ifdef SIM_STUBS
                 , .sim_vs(sim_vs), .sim_dacv(sim_dacv)
`endif
    );
endmodule
