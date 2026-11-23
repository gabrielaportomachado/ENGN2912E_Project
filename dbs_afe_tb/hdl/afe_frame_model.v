`timescale 1ns/1ps
// Spec-level model of the digital side of dbs_afe_top (SPI_FRAME.md), NOT the real RTL.
// The analog side is replaced by `code_in` (4 x 12 bit), sampled at the falling edge of CS = the sampling
// instant of the real chip. The cocotb testbench drives code_in from a Python amplifier/ADC model.
// Behaviour copied from adc_top.v: cnt counts SCLK edges while CS low; DOUT changes on falling edges;
// commit at edge 17 if WR; edges beyond 80 -> DOUT 0; RSTN async clears config.
module afe_frame_model (
    input         cs_n, sclk, din, rstn,
    input  [47:0] code_in,           // {ch3, ch2, ch1, ch0}, 12 bit each
    output        dout,
    output        dout_oe,
    output        rst_amp_o, mode_o,
    output [3:0]  en_o
);
    reg [6:0]  cnt;
    reg [15:0] sr;
    reg [5:0]  hold;                  // {rst_amp, mode, en[3:0]}
    reg [79:0] stream;
    reg        dout_q;

    assign rst_amp_o = hold[5];
    assign mode_o    = hold[4];
    assign en_o      = hold[3:0];
    assign dout_oe   = ~cs_n;
    assign dout      = dout_q;

    // frame start: sample the "analog" inputs, build the output stream from the config held BEFORE this frame
    always @(negedge cs_n) begin
        stream[79:64] = {4'hA, hold[5], hold[4], hold[3:0], 6'b0};
        stream[63:48] = {2'd0, 2'b00, code_in[11:0]};
        stream[47:32] = {2'd1, 2'b00, code_in[23:12]};
        stream[31:16] = {2'd2, 2'b00, code_in[35:24]};
        stream[15:0]  = {2'd3, 2'b00, code_in[47:36]};
    end

    always @(posedge sclk or posedge cs_n or negedge rstn) begin
        if (!rstn) begin
            cnt <= 0; sr <= 0; hold <= 0;
        end else if (cs_n) begin
            cnt <= 0;
        end else begin
            if (cnt < 16) sr <= {sr[14:0], din};
            if (cnt == 16 && sr[15]) hold <= {sr[14], sr[13], sr[3:0]};
            if (cnt != 80) cnt <= cnt + 1;
        end
    end

    // DOUT preset to bit 15 of the status word while CS is high / at frame start
    always @(negedge sclk or posedge cs_n or negedge rstn) begin
        if (!rstn || cs_n) dout_q <= 1'b1;
        else dout_q <= (cnt < 80) ? stream[79 - cnt] : 1'b0;
    end
endmodule