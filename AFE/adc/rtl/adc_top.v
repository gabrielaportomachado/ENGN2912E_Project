`timescale 1ns/1ps
// adc_top: serial interface + SAR logic for the N per-channel 12-bit SAR ADCs, N = 4 (Decision 54, REVIEW R14).  3.3 V digital, SPI mode 0 slave, ONE DOUT.
// Replaces adc8_top (160-SCLK frame, 8 channels; kept untouched as history).  The per-channel SAR logic (adc_sar_ch) and the comparator-clock chain (adc_clkgen, N = 4) are the same as before.
//
// FRAME (normative = Decision 54 = AFE/adc/SPI_FRAME.md).  CS low ... CS high, EXACTLY 16 * (N + 1) = 80 SCLK rising edges (N = 4), 5 words of 16 bits, MSB first; edge number k = 1..80:
//   CS falling edge           : all N ADCs sample at once (plate reset switches open at the buffered CS, sampling TGs open a few ns later); SCLK must be low and silent before it.
//   k = 1..16   (word 0)      : DIN = config word {WR[15], RST_AMP[14], MODE[13], reserved 0 [12:4] (ignored), EN[3:0] [3:0]} sampled on SCLK rising.
//                               DOUT = status word {SYNC 1010 [15:12], RST_AMP [11], MODE [10], EN[3:0] [9:6], 0 [5:0]} = the HELD config of before this frame.  DOUT changes on SCLK FALLING edges;
//                               bit 15 (the first 1 of the sync pattern) is already on DOUT at edge 1: dout_q is SET while CS is high (DOUT is tri-state then, dout_oe = ~cs_n).
//   k = 1..16                 : conversions, staggered one SCLK per channel: ADC i does trial t at edge t + i (t = 1..12); ADC i is done at edge 13 + i (ADC 3: edge 16), tracking resumes at edge 14 + i
//   k = 17                    : COMMIT: if WR = 1 the config shifted in on edges 1..16 is copied into the hold register (rst_amp_o, mode_o, en_o); WR = 0 keeps it; a frame with fewer than 17 edges changes nothing
//   k = 17..80  (words 1..4)  : DIN ignored; DOUT = {ID[1:0], 2'b00, code[11:0]} of channel 0 .. 3 (ID = channel number; the two zero bits are reserved flags), same-frame data (the codes are complete at edge 16;
//                               the first code bit goes out after edge 20, i.e. it is read at edge 21)
//   edges beyond 80           : ignored, DOUT = 0.  CS rising (any time) asynchronously clears the frame counter and the ADC drivers (tri-state), presets DOUT to 1 (the sync MSB, DOUT_OE is low) and re-enables tracking.
// RSTN (async) also clears the config shift register, rst_amp_o, mode_o and en_o (all routing switches open, amplifier reset released).
// rst_amp_o is a LEVEL held in the hold register between frames (SCLK stops while CS is high): the host sets it with one frame (WR = 1), waits >= 100 ms, clears it with another frame.
// N = 1..4 (EN[3:0] and ID[1:0] are fixed fields of the 16-bit word; for N < 4 the unused EN bits are ignored).
module adc_top #(
    parameter N = 4
) (
    input            cs_n,
    input            sclk,
    input            din,
    input            rstn,
    output           dout,
    output           dout_oe,
    output           rst_amp_o,  // amplifier reset hold, OR-ed into every channel's fs: 1 while the RST_AMP config bit is held set
    output           mode_o,
    output [N-1:0]   en_o,
    // analog side, per ADC i (bit i of the N-bit vectors, bits 12*i+11..12*i of the DAC vectors)
    input  [N-1:0]   cmp_q,      // comparator outputs (1 = Vin >= trial value)
    output [N-1:0]   cmp_clk,    // staggered comparator evaluate clocks (high = evaluate)
    output [N-1:0]   rst_sw,     // 1 = plate and LSB-node reset switches closed (tracking); falls first at CS falling
    output [N-1:0]   tg_on,      // 1 = sampling transmission gate on; the delayed copy of rst_sw (opens AFTER the reset switches, closes after the drivers are released)
    output [12*N-1:0] dac_gp,    // tri-state inverter PMOS gates, 12 per ADC
    output [12*N-1:0] dac_gn,    // tri-state inverter NMOS gates, 12 per ADC
    output [N-1:0]   dac_gdn     // dummy-unit bottom driver NMOS gate: 1 = dummy bottom grounded; = ~tg_on
);
    // N outside 1..4 does not fit the 16-bit word (EN[3:0], ID[1:0]): elaboration stops on an undefined module
    generate if (N < 1 || N > 4) begin : bad_n
        adc_top_N_must_be_1_to_4 stop_here ();
    end endgenerate

    localparam [6:0] LAST = 16 * (N + 1);        // number of edges of the frame (80)

    wire frame_rn = rstn & ~cs_n;

    // ---- frame edge counter (m = edges taken so far; stops at 16 * (N + 1) = 80, so every edge beyond the frame is ignored) ----
    reg [6:0] cnt;
    always @(posedge sclk or negedge frame_rn)
        if (!frame_rn) cnt <= 7'd0;
        else if (cnt != LAST) cnt <= cnt + 7'd1;

    wire [20:0] tok;
    genvar k, i;
    generate for (k = 0; k < 21; k = k + 1) begin : tk
        assign tok[k] = (cnt == k);
    end endgenerate

    // ---- config word: shift register {WR, RST_AMP, MODE, EN[3:0]} (bits of word 0 at m = 0, 1, 2 and 12..15; the reserved bits m = 3..11 are not stored),
    //      hold register {RST_AMP, MODE, EN[3:0]} written at edge 17 (m = 16) if WR = 1 ----
    reg [6:0] cfg_sr;
    reg [5:0] cfg_hold;
    wire cfg_shift = (cnt < 7'd3) || (cnt >= 7'd12 && cnt < 7'd16);
    always @(posedge sclk or negedge rstn)
        if (!rstn) begin cfg_sr <= 7'd0; cfg_hold <= 6'd0; end
        else begin
            if (cfg_shift) cfg_sr <= {cfg_sr[5:0], din};
            if (cnt == 7'd16 && cfg_sr[6]) cfg_hold <= cfg_sr[5:0];
        end
    assign rst_amp_o = cfg_hold[5];
    assign mode_o    = cfg_hold[4];
    assign en_o      = cfg_hold[N-1:0];

    // ---- readout: stream position m (= edges taken at the falling edge that updates DOUT): word w = m / 16, bit p = m % 16 of that word, MSB first ----
    wire [2:0] w = cnt[6:4];
    wire [3:0] p = cnt[3:0];
    wire       in_status = (w == 3'd0);
    wire       in_words  = (w >= 3'd1) && (w <= N);     // words 1..N: ID + code of channel w - 1
    wire       shift     = in_words && (p >= 4'd4);      // consumed a code bit of the head channel: all channels shift
    wire [2:0] chn       = w - 3'd1;
    wire [11:0] code [0:N-1];
    reg  dout_q;
    reg  dbit;
    always @(*) begin
        dbit = 1'b0;
        if (in_status) begin
            case (p)
                4'd0: dbit = 1'b1;               // SYNC 1010
                4'd1: dbit = 1'b0;
                4'd2: dbit = 1'b1;
                4'd3: dbit = 1'b0;
                4'd4: dbit = cfg_hold[5];        // RST_AMP
                4'd5: dbit = cfg_hold[4];        // MODE
                4'd6: dbit = cfg_hold[3];        // EN[3]
                4'd7: dbit = cfg_hold[2];
                4'd8: dbit = cfg_hold[1];
                4'd9: dbit = cfg_hold[0];        // EN[0]
                default: dbit = 1'b0;
            endcase
        end
        if (in_words) begin
            case (p)
                4'd0: dbit = chn[1];             // ID[1]
                4'd1: dbit = chn[0];             // ID[0]
                4'd2: dbit = 1'b0;               // reserved flags
                4'd3: dbit = 1'b0;
                default: dbit = code[0][11];
            endcase
        end
    end
    // DOUT is tri-state while CS is high: it is preset to 1 (= bit 15 of the status word, the first sync bit) so that it is valid at edge 1
    always @(negedge sclk or negedge frame_rn)
        if (!frame_rn) dout_q <= 1'b1; else dout_q <= dbit;
    assign dout    = dout_q;
    assign dout_oe = ~cs_n;

    // ---- the N SARs ----
    wire [N-1:0] drv_en, done, tapw;
    wire [N-1:0] code_next;                 // bit shifted into code[i] while reading out: the MSB of the next channel (0 for the last)
    generate for (i = 0; i < N - 1; i = i + 1) begin : cn
        assign code_next[i] = code[i + 1][11];
    end endgenerate
    assign code_next[N-1] = 1'b0;
    generate for (i = 0; i < N; i = i + 1) begin : ch
        wire [11:0] gp, gn;
        adc_sar_ch #(.IDX(i)) u (
            .sclk(sclk), .rstn(rstn), .frame_rn(frame_rn), .tok(tok), .cap_clk(tapw[i]), .cmp_q(cmp_q[i]),
            .shift(shift), .shift_in(code_next[i]),
            .code(code[i]), .gp(gp), .gn(gn), .drv_en(drv_en[i]), .done(done[i]));
        assign dac_gp[12*i +: 12] = gp;
        assign dac_gn[12*i +: 12] = gn;
        wire trk = cs_n | done[i];
        assign rst_sw[i] = trk;
        // sampling TG: delayed copy of trk (opens after the reset switches; closes after the drivers have released, drv_en clears asynchronously on CS rising)
        (* keep *) gf180mcu_fd_sc_mcu7t5v0__dlyd_1 utg (.I(trk), .Z(tg_on[i]));
        assign dac_gdn[i] = ~tg_on[i];
    end endgenerate

    // ---- staggered comparator clocks ----
    adc_clkgen #(.N(N)) ckg (.sclk(sclk), .act(drv_en), .cmp_clk(cmp_clk), .tapw(tapw));
endmodule
