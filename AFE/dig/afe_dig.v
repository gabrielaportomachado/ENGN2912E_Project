`timescale 1ns/1ps
// afe_dig: the chip's ONE digital macro (LP step 5 / phase L1d, Decisions 44h, 46e).  It is exactly the digital part of AFE/top/dbs_afe_top.v:
//   u_adc  = adc8_top (AFE/adc/rtl, not edited): SPI frame, config word, 8 SAR logics, staggered comparator clocks
//   u_dbs  = dbs_ctrl #(.N(8)) (rtl/dbs.v, not edited): routing FSM + enable registers; clk = the SCLK net of u_adc, ready = 1'b1, mode / en = u_adc.mode_o / en_o (they stay inside)
//   plus three things that exist only here:
//   (1) CLOCK ROOT (Decision 44h fallback, parameter CLKBUF = 1): ONE hand-instantiated, hand-placed clock buffer u_ckbuf (clkbuf_20) between the pin SCLK and the single net `sclk_i`
//       that feeds every flop clock pin of u_adc / u_dbs AND the input of the comparator delay chain (adc_clkgen is inside adc8_top and takes the same net).  The buffer delay is therefore
//       common to the DAC edge and to the comparator clock: the margins of AFE/review/AUDIT.md 4.4.3 do not move against the flop clock.  Measured against the SCLK PIN every comparator
//       window ends later by the buffer delay (1.7 ns at ss 125 C 3.0 V with 1 pF on sclk_i; clkbuf_16 would be 2.1 ns: the largest clock buffer is used for that reason).
//       CLKBUF = 0 connects the pin directly (for a flow with clock tree synthesis).
//   (2) ROUTING-SWITCH OUTPUT PAIRS (I0 mismatch 8): sw_rec[i] / sw_rec_b[i] (and sw_ipg[i] / sw_ipg_b[i]) are both driven from ONE node, the NAND output of dbs_ctrl (its sw_*_b),
//       through a clkinv_4 (true) and a clkbuf_8 (complement): the pair with the smallest skew over load 0.05-0.2 pF and corners that the library offers (<= 0.31 ns, OpenSTA, AFE/dig/reports/sw_pair_cells.log).
//       dbs_ctrl's own sw_rec / sw_ipg outputs (an inverter behind the same NAND) are left open and disappear in synthesis.
//   (3) PAD-CONTROL CONSTANTS (Decision 46e): the 15 constant pad-control pins of the top are OUTPUT PINS of this macro, each driven by its own tie cell (gf180mcu_fd_sc_mcu7t5v0__tiel pin ZN = 0,
//       __tieh pin Z = 1), instantiated by hand with (* keep *) so that the final netlist has real tie cells whatever the synthesis settings.  Values = AFE/top/dbs_afe_top.v (checked by
//       AFE/dig/mk_top_dig.py, which stops if they differ): all 0 except RSTN_PD = 1.  DOUT_OE is not a constant: it is adc8_top.dout_oe = ~CS.
//   (4) DOUT_OE DRIVER: DOUT_OE = ~CS comes from its OWN inverter u_oe (clkinv_20) on the CS pin, not from adc8_top.dout_oe (the same function, `assign dout_oe = ~cs_n`, checked by
//       AFE/dig/mk_top_dig.py; that output is left open).  Reason: in adc8_top the net ~cs_n also feeds the frame reset and two of the eight sampling paths (cs_n | done); with the
//       pad-enable wire (0.3 pF ESTIMATE) on the same net the eight ADCs sampled 1 ns apart at ss 125 C and DOUT_OE followed CS only after 1.06 ns (audit assertions S2, D2).
// Pin names = table DIG_PINS of AFE/layout/scripts/mk_lvs_netlists.py + the 15 tie pins.  No TGATE here (they are in afe_ch).  Simulation models of the hand-instantiated cells: AFE/dig/cells_dig_sim.v.
module afe_dig #(
    parameter CLKBUF = 1
) (
    input         CS,          // SPI chip select, active low (adc8_top.cs_n); falling edge = sampling instant
    input         SCLK,
    input         DIN,
    input         RSTN,
    output        DOUT,        // -> top port DOUT_OUT (pad A)
    output        DOUT_OE,     // = ~CS
    output        rst_amp_o,   // RST_AMP level to the 8 channels
    output [7:0]  sw_rec, sw_rec_b, sw_ipg, sw_ipg_b,
    input  [7:0]  cmp_q,
    output [7:0]  cmp_clk, rst_sw, tg_on,
    output [95:0] dac_gp, dac_gn,
    output [7:0]  dac_gdn,
    // pad-control constants (tie cells)
    output        DOUT_IE, DOUT_PD, DOUT_PU, DOUT_CS, DOUT_SL, DOUT_PDRV0, DOUT_PDRV1,
    output        CS_PU, CS_PD, DIN_PU, DIN_PD, SCLK_PU, SCLK_PD, RSTN_PU, RSTN_PD
);
    // ---- (1) clock root ----
    wire sclk_i;
    generate if (CLKBUF) begin : ck
        (* keep *) gf180mcu_fd_sc_mcu7t5v0__clkbuf_20 u_ckbuf (.I(SCLK), .Z(sclk_i));
    end else begin : nock
        assign sclk_i = SCLK;
    end endgenerate

    // ---- serial interface, config word, 8 SARs ----
    wire       mode_o;
    wire [7:0] en_o;
    /* verilator lint_off PINCONNECTEMPTY */
    adc8_top u_adc (.cs_n(CS), .sclk(sclk_i), .din(DIN), .rstn(RSTN), .dout(DOUT), .dout_oe(),
                    .rst_amp_o(rst_amp_o), .mode_o(mode_o), .en_o(en_o),
                    .cmp_q(cmp_q), .cmp_clk(cmp_clk), .rst_sw(rst_sw), .tg_on(tg_on), .dac_gp(dac_gp), .dac_gn(dac_gn), .dac_gdn(dac_gdn));
    /* verilator lint_on PINCONNECTEMPTY */
    // ---- (4) DOUT_OE = ~CS, own driver ----
    (* keep *) gf180mcu_fd_sc_mcu7t5v0__clkinv_20 u_oe (.I(CS), .ZN(DOUT_OE));

    // ---- routing control, clocked by the same SCLK net, READY tied high ----
    wire [7:0] rec_b_raw, ipg_b_raw;
    /* verilator lint_off PINCONNECTEMPTY */
    dbs_ctrl #(.N(8)) u_dbs (.clk(sclk_i), .rstn(RSTN), .mode(mode_o), .en(en_o), .ready(1'b1),
                             .sw_rec(), .sw_rec_b(rec_b_raw), .sw_ipg(), .sw_ipg_b(ipg_b_raw));
    /* verilator lint_on PINCONNECTEMPTY */

    // ---- (2) complementary output pairs from one node ----
    genvar i;
    generate for (i = 0; i < 8; i = i + 1) begin : sw
        (* keep *) gf180mcu_fd_sc_mcu7t5v0__clkinv_4 u_rec   (.I(rec_b_raw[i]), .ZN(sw_rec[i]));
        (* keep *) gf180mcu_fd_sc_mcu7t5v0__clkbuf_8 u_rec_b (.I(rec_b_raw[i]), .Z(sw_rec_b[i]));
        (* keep *) gf180mcu_fd_sc_mcu7t5v0__clkinv_4 u_ipg   (.I(ipg_b_raw[i]), .ZN(sw_ipg[i]));
        (* keep *) gf180mcu_fd_sc_mcu7t5v0__clkbuf_8 u_ipg_b (.I(ipg_b_raw[i]), .Z(sw_ipg_b[i]));
    end endgenerate

    // ---- (3) pad-control constants: one tie cell per pin ----
    (* keep *) gf180mcu_fd_sc_mcu7t5v0__tiel u_tie_DOUT_IE    (.ZN(DOUT_IE));
    (* keep *) gf180mcu_fd_sc_mcu7t5v0__tiel u_tie_DOUT_PD    (.ZN(DOUT_PD));
    (* keep *) gf180mcu_fd_sc_mcu7t5v0__tiel u_tie_DOUT_PU    (.ZN(DOUT_PU));
    (* keep *) gf180mcu_fd_sc_mcu7t5v0__tiel u_tie_DOUT_CS    (.ZN(DOUT_CS));
    (* keep *) gf180mcu_fd_sc_mcu7t5v0__tiel u_tie_DOUT_SL    (.ZN(DOUT_SL));
    (* keep *) gf180mcu_fd_sc_mcu7t5v0__tiel u_tie_DOUT_PDRV0 (.ZN(DOUT_PDRV0));
    (* keep *) gf180mcu_fd_sc_mcu7t5v0__tiel u_tie_DOUT_PDRV1 (.ZN(DOUT_PDRV1));
    (* keep *) gf180mcu_fd_sc_mcu7t5v0__tiel u_tie_CS_PU      (.ZN(CS_PU));
    (* keep *) gf180mcu_fd_sc_mcu7t5v0__tiel u_tie_CS_PD      (.ZN(CS_PD));
    (* keep *) gf180mcu_fd_sc_mcu7t5v0__tiel u_tie_DIN_PU     (.ZN(DIN_PU));
    (* keep *) gf180mcu_fd_sc_mcu7t5v0__tiel u_tie_DIN_PD     (.ZN(DIN_PD));
    (* keep *) gf180mcu_fd_sc_mcu7t5v0__tiel u_tie_SCLK_PU    (.ZN(SCLK_PU));
    (* keep *) gf180mcu_fd_sc_mcu7t5v0__tiel u_tie_SCLK_PD    (.ZN(SCLK_PD));
    (* keep *) gf180mcu_fd_sc_mcu7t5v0__tiel u_tie_RSTN_PU    (.ZN(RSTN_PU));
    (* keep *) gf180mcu_fd_sc_mcu7t5v0__tieh u_tie_RSTN_PD    (.Z(RSTN_PD));      // RSTN pull-down ON (Decision 41e)
endmodule
