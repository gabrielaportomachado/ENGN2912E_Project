`timescale 1ns/1ps
// dbs_afe_top: chip top level for the Chipathon macro (I0, 2026-11-14; Decision 52, 2026-11-21: 4 channels).  Digital part = rtl/dbs.v (dbs_ctrl, N = 8, read only) + AFE/adc/rtl/adc8_top
// (SPI frame, config word, 8 SAR logics): the 8-channel LOGIC is kept unchanged (Decision 52c); only channels 0-3 exist; the comparator inputs cmp_q[7:4] of the unused SAR logics are tied low
// and their outputs are left open (in silicon both happen inside the afe_dig wrapper).  Words 6-9 of the 160-SCLK frame carry IDs 4-7 with a constant code; EN[7:4] has no effect.
// analog part = 4 x afe_ch (routing TGATEs + REC park + amplifier + fs one-shot + ADC DAC/comparator) + 1 x bias_genc.  Single 3.3 V supply (Decision 30).  READY is tied high (Decision 35).
// The 8-channel version of this file is in git tag checkpoint-n8-final.
//
// WHY dbs_ctrl + TGATE and not the dbs module: dbs wraps dbs_ctrl + the 2N TGATEs but does not bring sw_rec / sw_rec_b out, and the amplifier reset trigger and the REC park need exactly those two nets.
// The TGATEs therefore sit inside afe_ch; the wiring is the same as dbs.v lines 99-106 (rec_tg: C = sw_rec, CBAR = sw_rec_b; ipg_tg: C = sw_ipg, CBAR = sw_ipg_b).  tb_top.v compares REC / IPG against a real `dbs #(8)` instance.
//
// Pads (16, Decision 52; was 24, Decision 45): analog E[3:0] IPG[3:0] REF (9); input_cmos CS DIN; input_schmitt SCLK RSTN; bidirectional DOUT (5 digital); power VDD; ground VSS.
// REF = shared reference electrode, wired to afe_chc.ref of all 4 channels.  NO REC pads (Decision 45): rec is an internal net of afe_ch (record TGATE OUT = afe_chc.rec).
// Fallback (organizer pad share): N = 2 channels (Decision 45, A-7); the older fallback "drop the REF pad and tie every afe_ch `ref` to vcm" stays possible.
// Pad-pin names (F1, Decision 44b; checked against the organizer template, copy in AFE/review/sim/organizer/template_info.yaml lines 26-66): a bidirectional pad <name> needs the ports
// <name>_OUT (to the pad's A) and <name>_IN (from the pad's Y) plus the 8 control pins <name>_PD _PU _CS _SL _IE _OE _PDRV0 _PDRV1; an input pad <name> needs <name> (from Y), <name>_PD, <name>_PU.
// "All control signals must be connected" (template line 27): every one is driven below.  The VALUES (drive strength, slew, input type) are still to be confirmed in L4 (Decision 41d).
module dbs_afe_top (
    inout  [3:0] E, IPG,
    inout        REF,
    input        CS, DIN, SCLK, RSTN,
    output       DOUT_OUT,                          // serial data to the bidirectional pad DOUT (pad pin A)
    input        DOUT_IN,                           // from the same pad (pad pin Y): NOT USED (the pad's input buffer is off, DOUT_IE = 0); exists because the template requires the port
    output       DOUT_OE, DOUT_IE, DOUT_PD, DOUT_PU, DOUT_CS, DOUT_SL, DOUT_PDRV0, DOUT_PDRV1,
    output       CS_PU, CS_PD, DIN_PU, DIN_PD, SCLK_PU, SCLK_PD, RSTN_PU, RSTN_PD,
    inout        VDD, VSS
);
    // ---- pad glue: DOUT drives only while CS is low (adc8_top dout_oe); input pads get no pull ----
    wire dout_oe;
    assign DOUT_OE = dout_oe;                       // = ~CS: tri-state while CS is high (the MCU may share the MISO line), Decision 41d
    assign DOUT_IE = 1'b0; assign DOUT_PD = 1'b0; assign DOUT_PU = 1'b0; assign DOUT_CS = 1'b0; assign DOUT_SL = 1'b0; assign DOUT_PDRV0 = 1'b0; assign DOUT_PDRV1 = 1'b0;   // input off, no pull, CMOS, fast, 4 mA: values to be confirmed in L4
    assign CS_PU = 1'b0; assign CS_PD = 1'b0; assign DIN_PU = 1'b0; assign DIN_PD = 1'b0; assign SCLK_PU = 1'b0; assign SCLK_PD = 1'b0; assign RSTN_PU = 1'b0; assign RSTN_PD = 1'b1;   // RSTN pull-down ON (Decision 41, mismatch 9): the chip comes up in reset if the host does not drive RSTN

    // ---- serial interface, config word, 8 SAR logics (channels 4-7 unused, Decision 52c) ----
    wire        mode_o, rst_amp_o;
    wire [7:0]  en_o, cmp_q, cmp_clk, rst_sw, tg_on, dac_gdn;
    wire [95:0] dac_gp, dac_gn;
    assign cmp_q[7:4] = 4'b0000;                   // unused SAR logics 4-7: comparator input tied low (inside the afe_dig wrapper in silicon); their outputs stay open
    adc8_top u_adc (.cs_n(CS), .sclk(SCLK), .din(DIN), .rstn(RSTN), .dout(DOUT_OUT), .dout_oe(dout_oe),
                    .rst_amp_o(rst_amp_o), .mode_o(mode_o), .en_o(en_o),
                    .cmp_q(cmp_q), .cmp_clk(cmp_clk), .rst_sw(rst_sw), .tg_on(tg_on), .dac_gp(dac_gp), .dac_gn(dac_gn), .dac_gdn(dac_gdn));

    // ---- routing control (rtl/dbs.v), clocked by SCLK (no CLK pad, Decision 37), READY tied high ----
    wire [7:0] sw_rec, sw_rec_b, sw_ipg, sw_ipg_b;
    dbs_ctrl #(.N(8)) u_dbs (.clk(SCLK), .rstn(RSTN), .mode(mode_o), .en(en_o), .ready(1'b1),
                             .sw_rec(sw_rec), .sw_rec_b(sw_rec_b), .sw_ipg(sw_ipg), .sw_ipg_b(sw_ipg_b));

    // ---- shared bias (one per chip) ----
    wire vbn, vcm, vg1, vcmo, vg2, vrs;
    bias_genc u_bias (.vbn(vbn), .vcm_in(vcm), .vg1(vg1), .vcm_out(vcmo), .vg2(vg2), .vrs(vrs), .vdd(VDD), .vss(VSS));

    // ---- supply straps (F1, Decision 44d = the rail table of AFE/review/AUDIT.md 4.9.2).  ONE pad pair VDD / VSS, three metal straps star-connected at the pad:
    //        analog strap   -> net VDD     : bias_genc, 4 x (afe_chc, fs_oneshot_c, OR2, vhalf, Cref switch, samb inverter, sampling-TG n-wells, routing-TGATE wells)   [afe_ch.vdd]
    //        ADC-main strap -> net VDD     : 4 x cmp_p [afe_ch.vdd_cmp] + the digital macro; decap 0.125 nF (MOS capacitors, about 3 ohm in series; kept for 4 channels, Decision 52e)
    //        ADC-DAC strap  -> net vdd_dac : the 13 bottom-plate drivers of each dac_sw [afe_ch.vdd_dac]; behind ONE 10 ohm strap resistor from the ADC-main strap; decap 0.05 nF (0.1 nF for 8 ADCs, Decision 52e)
    //      The analog and the ADC-main strap are the same NET (VDD): they differ only in the layout (separate metal from the pad).  The strap resistor and the two decap banks are DEVICES of the
    //      LVS top reference (AFE/layout/lvs/dbs_afe_top.spice, written by AFE/layout/scripts/mk_lvs_netlists.py from this file); here they are the cells afe_rstrap / afe_decap (stubs_analog.v).
    wire vdd_dac;
    afe_rstrap                u_rstrap (.a(VDD), .b(vdd_dac), .vss(VSS));     // 10 ohm, ADC-main strap -> ADC-DAC strap (X2 S4: Rs = 10 ohm)
    afe_decap #(.C_NF(0.125)) u_dcm    (.p(VDD), .n(VSS));                    // ADC-main strap decap 0.125 nF (cap_nmos_03v3, 3.98 fF/um2 in the PDK model)
    afe_decap #(.C_NF(0.0475)) u_dcd   (.p(vdd_dac), .n(VSS));                // ADC-DAC strap decap >= 47.5 pF for 4 ADCs (Decision 52e; 0.1 nF for 8)

    // ---- 4 channels (Decision 52) ----
    genvar i;
    generate for (i = 0; i < 4; i = i + 1) begin : ch
        afe_ch u (.e(E[i]), .ipg(IPG[i]),
                  .sw_rec(sw_rec[i]), .sw_rec_b(sw_rec_b[i]), .sw_ipg(sw_ipg[i]), .sw_ipg_b(sw_ipg_b[i]),
                  .rst_amp(rst_amp_o),
                  .rst_sw(rst_sw[i]), .tg_on(tg_on[i]), .cmp_clk(cmp_clk[i]), .dac_gdn(dac_gdn[i]),
                  .dac_gp(dac_gp[12*i +: 12]), .dac_gn(dac_gn[12*i +: 12]), .cmp_q(cmp_q[i]),
                  .vbn(vbn), .vcm(vcm), .vg1(vg1), .vcmo(vcmo), .vg2(vg2), .vrs(vrs), .ref(REF), .vdd(VDD), .vdd_cmp(VDD), .vdd_dac(vdd_dac), .vss(VSS));
    end endgenerate
endmodule

// afe_ch: ONE channel = amplifier part (L2: afe_chc + fs_oneshot_c + OR2) + ADC analog part (L1: vhalf, samb inverter, dac_sw, vrefs, cmp_p) + the 2 routing TGATEs (L3).  Pin list: AFE/layout/PLAN.md section 9.
module afe_ch (
    inout        e, ipg,                            // electrode pad, IPG pad
    inout        ref,                               // REF pad: shared reference electrode (afe_chc.ref)
    input        sw_rec, sw_rec_b, sw_ipg, sw_ipg_b,// routing switch controls from dbs_ctrl (C / CBAR of the two TGATEs)
    input        rst_amp,                           // RST_AMP config bit level (adc8_top rst_amp_o), common to all channels
    input        rst_sw, tg_on, cmp_clk, dac_gdn,   // adc8_top bit i
    input  [11:0] dac_gp, dac_gn,                   // adc8_top bits 12*i+11 .. 12*i
    output       cmp_q,
    input        vbn, vcm, vg1, vcmo, vg2, vrs,
    input        vdd, vdd_cmp, vdd_dac, vss         // vdd = analog strap; vdd_cmp = ADC-main strap (cmp_p); vdd_dac = ADC-DAC strap (the 13 bottom-plate drivers); AUDIT 4.9.2
);
    // rec = record TGATE OUT = amplifier input (afe_chc.rec) = park node.  INTERNAL net since Decision 45 (no REC pad: one pad leakage / ESD path less on the high-impedance input)
    wire rec;
    // routing switches (5 V-device TGATE macro, TGATE/TGATE.v; dbs.v wiring).  Their VDD / VSS (wells) are on the analog strap in the LVS reference (TGATE.v has no power pins)
    TGATE rec_tg (.OUT(rec), .IN(e), .C(sw_rec), .CBAR(sw_rec_b));
    TGATE ipg_tg (.OUT(ipg), .IN(e), .C(sw_ipg), .CBAR(sw_ipg_b));

    // amplifier reset: one-shot started by the edge that closes the record switch (C net), OR-ed with RST_AMP
    wire fs_os, fs;
    fs_oneshot_c u_os (.trig(sw_rec), .fs(fs_os), .vbn(vbn), .vdd(vdd), .vss(vss));
    (* keep *) gf180mcu_fd_sc_mcu7t5v0__or2_1 u_or (.A1(fs_os), .A2(rst_amp), .Z(fs));

    // amplifier with REC park (pkc = CBAR = HIGH while the record switch is open = park ON; pkcb = C)
    wire amp_out;
`ifdef SIM_STUBS
    wire [11:0] sim_amp_out, sim_vs, sim_dacv;
`endif
    afe_chc u_amp (.rec(rec), .ref(ref), .out(amp_out), .vdd(vdd), .vss(vss), .vbn(vbn), .vcm(vcm), .vg1(vg1), .vcmo(vcmo), .vg2(vg2), .vrs(vrs),
                   .fs(fs), .pkc(sw_rec_b), .pkcb(sw_rec)
`ifdef SIM_STUBS
                   , .sim_out(sim_amp_out)
`endif
    );

    // ADC analog: split-cap DAC + switches, comparator.  rstm = rst = rst_sw (D4 wiring); samb = ~tg_on (local inverter, analog strap); gdp tied high = to vdd_dac, the source rail of the dummy driver PMOS (Decision 37 / D4)
    // VDD/2 for this ADC: own resistive divider + MIM decap (cell vhalf, Decision 41)
    wire vcmd;
    vhalf u_vh (.out(vcmd), .vdd(vdd), .vss(vss));
    wire samb, t, m;
    (* keep *) gf180mcu_fd_sc_mcu7t5v0__inv_1 u_samb (.I(tg_on), .ZN(samb));
    dac_sw u_dac (.vin(amp_out), .t(t), .m(m), .vcm(vcmd), .vdd(vdd), .vdd_dac(vdd_dac), .vss(vss), .rst(rst_sw), .rstm(rst_sw), .sam(tg_on), .samb(samb),
                  .gp0(dac_gp[0]), .gp1(dac_gp[1]), .gp2(dac_gp[2]), .gp3(dac_gp[3]), .gp4(dac_gp[4]), .gp5(dac_gp[5]), .gp6(dac_gp[6]), .gp7(dac_gp[7]), .gp8(dac_gp[8]), .gp9(dac_gp[9]), .gp10(dac_gp[10]), .gp11(dac_gp[11]),
                  .gdp(vdd_dac),
                  .gn0(dac_gn[0]), .gn1(dac_gn[1]), .gn2(dac_gn[2]), .gn3(dac_gn[3]), .gn4(dac_gn[4]), .gn5(dac_gn[5]), .gn6(dac_gn[6]), .gn7(dac_gn[7]), .gn8(dac_gn[8]), .gn9(dac_gn[9]), .gn10(dac_gn[10]), .gn11(dac_gn[11]),
                  .gdn(dac_gdn)
`ifdef SIM_STUBS
                  , .sim_vin(sim_amp_out), .sim_vs(sim_vs), .sim_dacv(sim_dacv)
`endif
    );
    wire cmp_qn;
    // sampled floating comparator reference (I2): Cref behind a TG closed while tg_on = 1, open during the conversion
    wire vref;
    vrefs u_vr (.in(vcmd), .out(vref), .c(tg_on), .cb(samb), .vdd(vdd), .vss(vss));
    cmp_p u_cmp (.inp(vref), .inn(t), .clk(cmp_clk), .outp(cmp_q), .outn(cmp_qn), .vdd_cmp(vdd_cmp), .vss(vss)
`ifdef SIM_STUBS
                 , .sim_vs(sim_vs), .sim_dacv(sim_dacv)
`endif
    );
endmodule
