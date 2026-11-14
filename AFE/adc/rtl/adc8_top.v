`timescale 1ns/1ps
// adc8_top: serial interface + SAR logic for the 8 per-channel 12-bit SAR ADCs (D0b frame, Decisions 32-35, 38, D2 decisions).  3.3 V digital, SPI mode 0 slave, ONE DOUT.
//
// FRAME (CS low ... CS high, exactly 160 SCLK rising edges, 10 x 16-bit words, MSB first; edge number k = 1..160):
//   CS falling edge          : all 8 ADCs sample at once (plate reset switches open at the buffered CS, sampling TGs open a few ns later); SCLK must be low and silent before it.
//   k = 1..16  (word 0)      : DIN = {6 x 0, RST_AMP, MODE, EN[7:0]} (I0, Decision 38) sampled on SCLK rising; DOUT = 0
//   k = 1..20                : conversions, staggered one SCLK per channel: ADC i does trial t at edge t + i (t = 1..12); ADC i is done at edge 13 + i, tracking resumes at edge 14 + i
//   k = 17..32 (word 1)      : idle, DIN ignored, DOUT = 0
//   k = 33                   : the 10-bit config shift register is copied into the hold register (rst_amp_o, mode_o, en_o); frames with fewer than 33 edges change nothing
//   k = 33..160 (words 2..9) : DOUT = {0, ID[2:0], code[11:0]} of channel 0 .. 7 (ID = channel number), same-frame data; DOUT changes on SCLK FALLING edges
//   edges beyond 160 : ignored, DOUT = 0.  CS rising (any time) asynchronously clears the frame counter, the ADC drivers (tri-state) and DOUT, and re-enables tracking.
// dout_oe = ~cs_n (pad _OE).  RSTN (async) also clears rst_amp_o, mode_o and en_o (all routing switches open, amplifier reset released).
// rst_amp_o is a LEVEL held in the hold register between frames (SCLK stops while CS is high): the host sets it with one frame, waits >= 100 ms, clears it with another frame.
module adc8_top (
    input          cs_n,
    input          sclk,
    input          din,
    input          rstn,
    output         dout,
    output         dout_oe,
    output         rst_amp_o,  // amplifier reset hold, OR-ed into every channel's fs: 1 while the RST_AMP config bit is set
    output         mode_o,
    output [7:0]   en_o,
    // analog side, per ADC i (bit i of the 8-bit vectors, bits 12*i+11..12*i of the DAC vectors)
    input  [7:0]   cmp_q,      // comparator outputs (1 = Vin >= trial value)
    output [7:0]   cmp_clk,    // staggered comparator evaluate clocks (high = evaluate)
    output [7:0]   rst_sw,     // 1 = plate and LSB-node reset switches closed (tracking); falls first at CS falling
    output [7:0]   tg_on,      // 1 = sampling transmission gate on; the delayed copy of rst_sw (opens AFTER the reset switches, closes after the drivers are released)
    output [95:0]  dac_gp,     // tri-state inverter PMOS gates, 12 per ADC
    output [95:0]  dac_gn,     // tri-state inverter NMOS gates, 12 per ADC
    output [7:0]   dac_gdn     // dummy-unit bottom driver NMOS gate (D4): 1 = dummy bottom grounded; = ~tg_on, so it is grounded exactly while the sampling TG is off (its PMOS gate is tied high, no pin)
);
    wire frame_rn = rstn & ~cs_n;

    // ---- frame edge counter (m = edges taken so far; saturates at 255) ----
    reg [7:0] cnt;
    always @(posedge sclk or negedge frame_rn)
        if (!frame_rn) cnt <= 8'd0;
        else if (cnt != 8'hff) cnt <= cnt + 8'd1;

    wire [20:0] tok;
    genvar k, i;
    generate for (k = 0; k < 21; k = k + 1) begin : tk
        assign tok[k] = (cnt == k);
    end endgenerate

    // ---- config: 10-bit shift register {RST_AMP, MODE, EN[7:0]} on edges 1..16, hold register at edge 33 ----
    reg [9:0] cfg_sr, cfg_hold;
    always @(posedge sclk or negedge rstn)
        if (!rstn) begin cfg_sr <= 10'd0; cfg_hold <= 10'd0; end
        else begin
            if (cnt < 8'd16) cfg_sr <= {cfg_sr[8:0], din};
            if (cnt == 8'd32) cfg_hold <= cfg_sr;
        end
    assign rst_amp_o = cfg_hold[9];
    assign mode_o = cfg_hold[8];
    assign en_o   = cfg_hold[7:0];

    // ---- readout ----
    wire [3:0] w = cnt[7:4];
    wire [3:0] p = cnt[3:0];
    wire       in_words = (w >= 4'd2) && (w <= 4'd9);
    wire       shift    = in_words && (p >= 4'd4);        // consumed a code bit of the head channel: all channels shift
    wire [3:0] ch4      = w - 4'd2;
    wire [11:0] code [0:7];
    reg  dout_q;
    reg  dbit;
    always @(*) begin
        dbit = 1'b0;
        if (in_words) begin
            case (p)
                4'd0: dbit = 1'b0;
                4'd1: dbit = ch4[2];
                4'd2: dbit = ch4[1];
                4'd3: dbit = ch4[0];
                default: dbit = code[0][11];
            endcase
        end
    end
    always @(negedge sclk or negedge frame_rn)
        if (!frame_rn) dout_q <= 1'b0; else dout_q <= dbit;
    assign dout    = dout_q;
    assign dout_oe = ~cs_n;

    // ---- the 8 SARs ----
    wire [7:0]  drv_en, done, tapw;
    wire [7:0]  code_next;
    generate for (i = 0; i < 8; i = i + 1) begin : ch
        wire [11:0] gp, gn;
        adc_sar_ch #(.IDX(i)) u (
            .sclk(sclk), .rstn(rstn), .frame_rn(frame_rn), .tok(tok), .cap_clk(tapw[i]), .cmp_q(cmp_q[i]),
            .shift(shift), .shift_in((i == 7) ? 1'b0 : code_next[i]),
            .code(code[i]), .gp(gp), .gn(gn), .drv_en(drv_en[i]), .done(done[i]));
        assign dac_gp[12*i +: 12] = gp;
        assign dac_gn[12*i +: 12] = gn;
        wire trk = cs_n | done[i];
        assign rst_sw[i] = trk;
        // sampling TG: delayed copy of trk (opens after the reset switches; closes after the drivers have released, drv_en clears asynchronously on CS rising)
        (* keep *) gf180mcu_fd_sc_mcu7t5v0__dlyd_1 utg (.I(trk), .Z(tg_on[i]));
        assign dac_gdn[i] = ~tg_on[i];
    end endgenerate
    generate for (i = 0; i < 7; i = i + 1) begin : cn
        assign code_next[i] = code[i + 1][11];
    end endgenerate
    assign code_next[7] = 1'b0;

    // ---- staggered comparator clocks ----
    adc_clkgen ckg (.sclk(sclk), .act(drv_en), .cmp_clk(cmp_clk), .tapw(tapw));
endmodule
