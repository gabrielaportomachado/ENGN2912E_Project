`timescale 1ns/1ps
// Level 2: the REAL digital macro (afe_dig, gate-level AFE/dig/final/afe_dig.pnl.v) with a behavioural comparator per channel.
// Same port names as hdl/afe_frame_model.v, so tb/test_frames.py and tb/test_neural.py run unchanged.
//
// code_in[12*i +: 12] = the code the analog side of channel i "presents" at the CS falling edge (as at level 0).
//
// COMPARATOR MODEL (ideal): ADC i's n-th comparator evaluation after CS falls (n = 1..12, one rising edge of cmp_clk[i] each)
// answers  code_in bit (12 - n)  - exactly what an ideal comparator against a binary-search DAC returns (MSB first; 1 = Vin >= trial,
// adc_top.v).  So a correct SAR logic must reproduce code_in on DOUT.  It does NOT model the DAC, comparator offset, noise or timing
// margins (that is what the transistor-level analog tests are for).  The answer appears 0.4 ns after the cmp_clk rising edge.
//
// SHADOW OF THE HELD CONFIG (mode_o, en_o): afe_dig keeps mode_o / en_o inside, so this wrapper tracks them from the SPI word format
// of SPI_FRAME.md (16 bits on edges 1..16, commit at edge 17 if WR, RSTN clears).  It is written from the spec, NOT copied from the RTL.
// tb/test_neural.py compares the DUT's own status word (DOUT, word 0) with it on every frame, so a wrong DUT fails there.
// rst_amp_o is taken from the DUT.
module afe_dig_wrap (
    input         cs_n,
    input         sclk,
    input         din,
    input         rstn,
    input  [47:0] code_in,
    output        dout,
    output        dout_oe,
    output        rst_amp_o,
    output        mode_o,
    output [3:0]  en_o
);
    wire [3:0]  cmp_q, cmp_clk, rst_sw, tg_on, dac_gdn, sw_rec, sw_rec_b, sw_ipg, sw_ipg_b;
    wire [47:0] dac_gp, dac_gn;
    wire        ie, pd, pu, csp, sl, pdrv0, pdrv1, cs_pu, cs_pd, din_pu, din_pd, sclk_pu, sclk_pd, rstn_pu, rstn_pd;

    afe_dig dut (
        .CS(cs_n), .SCLK(sclk), .DIN(din), .RSTN(rstn),
        .DOUT(dout), .DOUT_OE(dout_oe), .rst_amp_o(rst_amp_o),
        .sw_rec(sw_rec), .sw_rec_b(sw_rec_b), .sw_ipg(sw_ipg), .sw_ipg_b(sw_ipg_b),
        .cmp_q(cmp_q), .cmp_clk(cmp_clk), .rst_sw(rst_sw), .tg_on(tg_on),
        .dac_gp(dac_gp), .dac_gn(dac_gn), .dac_gdn(dac_gdn),
        .DOUT_IE(ie), .DOUT_PD(pd), .DOUT_PU(pu), .DOUT_CS(csp), .DOUT_SL(sl), .DOUT_PDRV0(pdrv0), .DOUT_PDRV1(pdrv1),
        .CS_PU(cs_pu), .CS_PD(cs_pd), .DIN_PU(din_pu), .DIN_PD(din_pd), .SCLK_PU(sclk_pu), .SCLK_PD(sclk_pd),
        .RSTN_PU(rstn_pu), .RSTN_PD(rstn_pd)
    );

    // ---- ideal comparators ----
    genvar i;
    generate for (i = 0; i < 4; i = i + 1) begin : cmp
        integer n;
        reg q;
        initial begin n = 0; q = 1'b0; end
        always @(posedge cmp_clk[i] or posedge cs_n) begin
            if (cs_n) begin
                n <= 0;
                q <= 1'b0;
            end else begin
                q <= #0.4 (n < 12) ? code_in[12*i + 11 - n] : 1'b0;
                n <= n + 1;
            end
        end
        assign cmp_q[i] = q;
    end endgenerate

    // ---- shadow of the held config, from the spec ----
    integer     ne;
    reg [15:0]  w;
    reg [5:0]   hold;                       // {RST_AMP, MODE, EN[3:0]}
    initial begin ne = 0; w = 16'd0; hold = 6'd0; end
    always @(posedge sclk or negedge rstn or posedge cs_n) begin
        if (!rstn) begin
            hold <= 6'd0; ne <= 0; w <= 16'd0;
        end else if (cs_n) begin
            ne <= 0;
        end else begin
            ne <= ne + 1;                   // ne = edges taken before this one
            if (ne < 16) w <= {w[14:0], din};
            if (ne == 16 && w[15]) hold <= {w[14], w[13], w[3:0]};   // edge 17: commit if WR
        end
    end
    assign mode_o = hold[4];
    assign en_o   = hold[3:0];
endmodule