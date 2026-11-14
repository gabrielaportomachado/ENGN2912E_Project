`timescale 1ns/1ps
// adc_sar_ch: SAR logic of ONE ADC (index IDX = 0..7).  All flops are clocked by SCLK rising except the capture flop (clocked by tapw, see adc_clkgen).
// Token tok[k] is high while the frame edge counter m = k (the number of SCLK rising edges since CS fell, BEFORE the edge being taken; the edge is number k+1).
// Timing of this ADC (edge number = m + 1): m = IDX            : DAC trial 1 (MSB high, others low; the bottoms leave the input track-and-hold state; drivers enabled)
//                                          m = IDX + t - 1     : DAC trial t (bit 12 - t goes high), decision of trial t - 1 (captured in cap) is written into bit 12 - t + 1
//                                          m = IDX + 12        : decision of trial 12 written into bit 0, drivers released (tri-state)
//                                          m = IDX + 13        : done = 1 -> tracking resumes (plate reset switches close at once, sampling TG after its own delay)
// Comparator convention: cmp_q = 1 means Vin >= trial DAC value (keep the bit).  Wiring: inp = reference (VDD/2 tap), inn = plate (cmp_p: inp > inn -> outp = 1).
module adc_sar_ch #(parameter IDX = 0) (
    input         sclk,
    input         rstn,        // async, active low (chip reset)
    input         frame_rn,    // async, active low: low while CS is high or in reset
    input  [20:0] tok,         // one-hot decode of the frame edge counter, tok[k] = (m == k)
    input         cap_clk,     // capture clock (tapw[IDX])
    input         cmp_q,       // comparator outp
    input         shift,       // readout shift enable (all channels together)
    input         shift_in,    // bit shifted into code[0] (MSB of the next channel; 0 for channel 7)
    output [11:0] code,
    output [11:0] gp,          // per-bit tri-state inverter PMOS gate (0 = bit driven to VDD)
    output [11:0] gn,          // per-bit tri-state inverter NMOS gate (1 = bit driven to GND)
    output        drv_en,
    output        done
);
    reg [11:0] code_r;
    reg        en_r, done_r, cap_r;
    integer b;

    // capture flop: no reset (its clock is the delayed tapw, a reset would need a removal check against a clock that arrives up to ~400 ns late); the first use of cap_r is always after a capture
    always @(posedge cap_clk) cap_r <= cmp_q;

    always @(posedge sclk or negedge rstn)
        if (!rstn) begin
            code_r <= 12'h000;
        end else begin
            if (tok[IDX + 0]) code_r[11] <= 1'b1;
            else if (tok[IDX + 1]) code_r[11] <= cap_r;
            else if (shift) code_r[11] <= code_r[10];
            for (b = 0; b <= 10; b = b + 1) begin
                if (tok[IDX]) code_r[b] <= 1'b0;
                else if (tok[IDX + 11 - b]) code_r[b] <= 1'b1;
                else if (tok[IDX + 12 - b]) code_r[b] <= cap_r;
                else if (shift) code_r[b] <= (b == 0) ? shift_in : code_r[b - 1];
            end
        end

    always @(posedge sclk or negedge frame_rn)
        if (!frame_rn) en_r <= 1'b0;
        else if (tok[IDX]) en_r <= 1'b1;
        else if (tok[IDX + 12]) en_r <= 1'b0;

    always @(posedge sclk or negedge frame_rn)
        if (!frame_rn) done_r <= 1'b0;
        else if (tok[IDX + 13]) done_r <= 1'b1;

    assign code   = code_r;
    assign drv_en = en_r;
    assign done   = done_r;
    assign gp = ~({12{en_r}} & code_r);
    assign gn =   {12{en_r}} & ~code_r;
endmodule
