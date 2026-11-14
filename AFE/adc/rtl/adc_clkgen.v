`timescale 1ns/1ps
// adc_clkgen: the 8 staggered comparator clocks.  One chain of dont-touch delay cells from SCLK: tap[0] = SCLK + T0 (about 30 ns, typ), tap[i+1] = tap[i] + DT (about 50 ns, typ).
//   tapw[i]  = tap[i] delayed by a further W (about 6 ns typ): its RISING edge ends the comparator window and clocks the capture flop of ADC i.
//   cmp_clk[i] = tap[i] & ~tapw[i] & act[i]   (one pulse of width W per SCLK rising edge, only while ADC i is converting: act = drv_en of that ADC; act is stable long before tap rises).
// Chain lengths are parameters (counts of dlyd/dlyc/dlyb/dlya cells); defaults are tuned on the extracted STA numbers at tt/25C/3.3 V: cmp_clk[0] rises about 30 ns after SCLK, DT about 50 ns, W about 5.9 ns (sim/d3_taps.log).
module adc_clkgen #(
    parameter T0_D = 13, T0_C = 0, T0_B = 0, T0_A = 2,
    parameter DT_D = 4,  DT_C = 0, DT_B = 0, DT_A = 0,
    parameter W_D  = 1,  W_C  = 1, W_B  = 0, W_A  = 0
) (
    input        sclk,
    input  [7:0] act,
    output [7:0] cmp_clk,
    output [7:0] tapw
);
    wire [7:0] tap;
    wire [7:0] tapw_b;
    genvar i;
    generate
        for (i = 0; i < 8; i = i + 1) begin : t
            if (i == 0) begin : first
                adc_dlychain #(.NA(T0_A), .NB(T0_B), .NC(T0_C), .ND(T0_D)) ch (.I(sclk), .Z(tap[0]));
            end else begin : nxt
                adc_dlychain #(.NA(DT_A), .NB(DT_B), .NC(DT_C), .ND(DT_D)) ch (.I(tap[i-1]), .Z(tap[i]));
            end
            adc_dlychain #(.NA(W_A), .NB(W_B), .NC(W_C), .ND(W_D)) wch (.I(tap[i]), .Z(tapw[i]));
            (* keep *) gf180mcu_fd_sc_mcu7t5v0__inv_1  ui (.I(tapw[i]), .ZN(tapw_b[i]));
            (* keep *) gf180mcu_fd_sc_mcu7t5v0__and3_1 ug (.A1(tap[i]), .A2(tapw_b[i]), .A3(act[i]), .Z(cmp_clk[i]));
        end
    endgenerate
endmodule
