`timescale 1ns/1ps
// ana_model: IDEAL behavioural model of ONE ADC's analog side (comparator + switch checks), driven by the digital block outputs.  No analog accuracy: it only gives the right 1-bit decisions
// and flags protocol/timing violations: crowbar (gp low and gn high), driver/TG contention, DAC edge to comparator rise < TMIN, DAC change while the comparator evaluates, comparator window cut by the next DAC edge.
module ana_model #(parameter TMIN = 24.0) (
    input         tg_on, rst_sw, cmp_clk,
    input  [11:0] gp, gn,
    input  [11:0] vin,            // input code (the voltage is vin + 0.5 LSB)
    output reg    cmp_q,
    output reg [31:0] e_crowbar, e_cont, e_tmin, e_chg, e_order, e_z,
    output reg [11:0] vs,         // sampled value
    output reg [31:0] n_dec
);
    reg [11:0] dacv;
    real t_dac, t_rise, t_rst_fall;
    reg  win;
    integer b;
    reg [11:0] hi, lo;
    initial begin cmp_q = 1'b1; e_crowbar = 0; e_cont = 0; e_tmin = 0; e_chg = 0; e_order = 0; e_z = 0; vs = 0; n_dec = 0; t_dac = 0; win = 0; dacv = 0; end

    always @(*) begin
        hi = ~gp & ~gn;    // driven high
        lo =  gp &  gn;    // driven low
    end
    // DAC edge bookkeeping
    always @(gp or gn) begin
        t_dac = $realtime;
        if (|(~gp & gn)) e_crowbar = e_crowbar + 1;
        if (win) e_chg = e_chg + 1;
        if (tg_on && (|(~gp) || |gn)) e_cont = e_cont + 1;
    end
    always @(posedge tg_on) if (|(~gp) || |gn) e_cont = e_cont + 1;
    // sampling: reset switches must open before the TG
    always @(negedge rst_sw) t_rst_fall = $realtime;
    always @(negedge tg_on) begin
        vs = vin;
        if (rst_sw) e_order = e_order + 1;       // TG opened while reset switches still closed
    end
    always @(posedge cmp_clk) begin
        t_rise = $realtime;
        win = 1;
        if (($realtime - t_dac) < TMIN) e_tmin = e_tmin + 1;
        if (|(gp & ~gn)) e_z = e_z + 1;           // some bit is tri-state during a trial
        dacv = hi;
        n_dec = n_dec + 1;
        #1.5 cmp_q = (vs >= dacv);
    end
    always @(negedge cmp_clk) begin win = 0; #0.6 cmp_q = 1'b1; end
endmodule
