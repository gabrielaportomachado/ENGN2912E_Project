`timescale 1ns/1ps
// --------------- FSM module --------------- 
module fsm(
    input clk,
    input rstn,         // async active-low reset (matches RSTn on the dffrnq/dffsnq cells)
    input mode,
    output rec_en,
    output treat_en
);

    reg s0, s1;
    // s0 is a dffsnq (set to 1 on reset), s1 is a dffrnq (cleared on reset), as in FSM2.sch
    always @(posedge clk or negedge rstn) begin
        if (!rstn) begin
            s0 <= 1;
            s1 <= 0;
        end else begin
            s0 <= s1 | mode;
            s1 <= s0 & mode;
        end
    end

    assign rec_en = s1;
    assign treat_en = ~(s0 | s1);

endmodule

// --------------- Digital control block (synthesizable, hardened with LibreLane) ---------------
// Everything except the analog switches: FSM, enable registers and the
// switch-control signals that drive the transmission gates.
module dbs_ctrl #(
    parameter N = 16
)(
    input clk,
    input rstn,                 // async active-low reset
    input mode,                 // mode input
    input [N-1:0] en,           // enable signals
    input ready,                // ready signal
    output reg [N-1:0] sw_rec,  // switch controls for the rec transmission gates
    output reg [N-1:0] sw_rec_b,
    output reg [N-1:0] sw_ipg,  // switch controls for the ipg transmission gates
    output reg [N-1:0] sw_ipg_b
);

    // instantiate FSM module
    wire rec_en, treat_en;
    fsm fsm_inst(.clk(clk), .rstn(rstn), .mode(mode), .rec_en(rec_en), .treat_en(treat_en));

    // register the enable signals twice
    reg [N-1:0] en_reg_1, en_reg_2;
    always @(posedge clk or negedge rstn) begin
        if (!rstn) begin
            en_reg_1 <= {N{1'b0}};
            en_reg_2 <= {N{1'b0}};
        end else begin
            en_reg_1 <= en;
            en_reg_2 <= en_reg_1;
        end
    end

    // combinationally generate the SW signals
    // should we skip the for loop and generate the whole bus at once?
    integer i;
    always @(*) begin
        for (i = 0; i < N; i = i + 1) begin
            // can we save gates here?
            sw_rec_b[i] = ~(ready & rec_en & en_reg_2[i]);
            sw_ipg_b[i] = ~(ready & treat_en & en_reg_2[i]);

            sw_rec[i] = ~sw_rec_b[i];
            sw_ipg[i] = ~sw_ipg_b[i];
        end
    end

endmodule

// --------------- Top level DBS module --------------- 
// Digital control plus the analog transmission gates
// Can be synthesized using the TGATE macro
module dbs #(
    parameter N = 16
)(
    input clk,
    input rstn,         // async active-low reset
    input mode,         // mode input
    input [N-1:0] en,   // enable signals
    input [N-1:0] vals, // the signals to be routed
    input ready,        // ready signal
    output [N-1:0] rec, // the rec channels
    output [N-1:0] ipg  // the ipg channels
);

    wire [N-1:0] sw_rec, sw_rec_b, sw_ipg, sw_ipg_b;
    dbs_ctrl #(.N(N)) ctrl (
        .clk(clk), .rstn(rstn), .mode(mode), .en(en), .ready(ready),
        .sw_rec(sw_rec), .sw_rec_b(sw_rec_b), .sw_ipg(sw_ipg), .sw_ipg_b(sw_ipg_b)
    );

    // we use a generate loop and the CMOS primitive to instantiate the transmission gates
    genvar j;
    generate
        for (j = 0; j < N; j = j + 1) begin : transmission_gates
            TGATE rec_tg (.OUT(rec[j]), .IN(vals[j]), .C(sw_rec[j]), .CBAR(sw_rec_b[j]));
            TGATE ipg_tg (.OUT(ipg[j]), .IN(vals[j]), .C(sw_ipg[j]), .CBAR(sw_ipg_b[j]));
        end
    endgenerate
endmodule
