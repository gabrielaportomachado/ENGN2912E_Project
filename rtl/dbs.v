// --------------- FSM module --------------- 
module fsm(
    input clk,
    input reset,
    input mode,
    output rec_en,
    output treat_en
);

    reg s0, s1;
    always @(posedge clk) begin
        if (reset) begin // TODO: need to decide active high or low reset, and sync or async reset
            s0 <= 0;
            s1 <= 0;
        end else begin
            s0 <= s1 | mode;
            s1 <= s0 & mode;
        end
    end

    assign rec_en = s1;
    assign treat_en = ~(s0 | s1);

endmodule

// --------------- Top level DBS module --------------- 
module dbs(
    parameter N = 16    
)(
    input clk,
    input reset,
    input mode,         // mode input
    input [N-1:0] en,   // enable signals
    input [N-1:0] vals, // the signals to be routed
    input ready,        // ready signal
    output [N-1:0] rec, // the rec channels
    output [N-1:0] ipg  // the ipg channels
);

    // instantiate FSM module
    wire rec_en, treat_en;
    fsm fsm_inst(.clk(clk), .reset(reset), .mode(mode), .rec_en(rec_en), .treat_en(treat_en);

    // register the enable signals twice
    reg [N-1:0] en_reg_1, en_reg_2;
    always @(posedge clk) begin
        if (!reset) begin // TODO: see reset note above
            en_reg_1 <= '0;
            en_reg_2 <= '0;
        end else begin
            en_reg_1 <= en;
            en_reg_2 <= en_reg_1;
        end
    end

    // combinationally generate the SW signals
    // should we skip the for loop and generate the whole bus at once?
    integer i;
    rec [N-1:0] sw_rec, sw_rec_b, sw_ipg, sw_ipg_b;
    always @(*) begin
        for (i = 0; i < N; i = i + 1) begin
            // can we save gates here?
            sw_rec_b[i] = ~(ready & rec_en & en_reg_2[i]);
            sw_ipg_b[i] = ~(ready & treat_en & en_reg_2[i]);

            sw_rec[i] = ~sw_rec_b[i];
            sw_ipg[i] = ~sw_ipg_b[i];
        end
    end
    
    // we use a generate loop and the CMOS primitive to instantiate the transmission gates
    genvar j;
    generate
        for (j = 0; j < N; j = j + 1) begin : transmission_gates
            // cmos inst_name (out, in, ctrl, ctrl_bar)
            cmos rec_tg (rec[i], vals[i], sw_rec[i], sw_rec_b[i]);
            cmos ipg_tg (ipg[i], vals[i], sw_ipg[i], sw_ipg_b[i]);
        end
    endgenerate
endmodule
