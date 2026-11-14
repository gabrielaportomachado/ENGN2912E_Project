`timescale 1ns/1ps
// adc_dlychain: series chain of gf180mcu 7t5v0 delay cells (standard cells instantiated directly, marked keep / dont touch).
// Nominal (tt 25C 3.3 V, STA, no wires) delays: dlya_1 0.84 ns, dlyb_1 1.56, dlyc_1 2.64, dlyd_1 3.66 (sim/d3_dlycell.log).
module adc_dlychain #(parameter NA = 0, NB = 0, NC = 0, ND = 1) (
    input  I,
    output Z
);
    localparam N = NA + NB + NC + ND;
    wire [N:0] w;
    assign w[0] = I;
    genvar k;
    generate
        for (k = 0; k < N; k = k + 1) begin : g
            if (k < ND) begin : d
                (* keep *) gf180mcu_fd_sc_mcu7t5v0__dlyd_1 u (.I(w[k]), .Z(w[k+1]));
            end else if (k < ND + NC) begin : c
                (* keep *) gf180mcu_fd_sc_mcu7t5v0__dlyc_1 u (.I(w[k]), .Z(w[k+1]));
            end else if (k < ND + NC + NB) begin : b
                (* keep *) gf180mcu_fd_sc_mcu7t5v0__dlyb_1 u (.I(w[k]), .Z(w[k+1]));
            end else begin : a
                (* keep *) gf180mcu_fd_sc_mcu7t5v0__dlya_1 u (.I(w[k]), .Z(w[k+1]));
            end
        end
    endgenerate
    assign Z = w[N];
endmodule
