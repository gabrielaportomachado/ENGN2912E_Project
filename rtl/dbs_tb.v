// Testbench for dbs.v, recreating the stimulus of ROW/ROW_tb.sch (FSM2 + ROW):
//   fclk = 100 kHz, CLK period 0.95*tper_clk, MODE period 16*tper_clk,
//   RSTn released at 2*tper_clk, READY = 1, ENi = 1, tstop = 24*tper_clk.
// Edges are placed at the 50% point of the SPICE PULSE sources.
`timescale 1ns/1ps

module dbs_tb;

    localparam N = 16;

    // same quantities as the .control block in ROW_tb.sch (in ns)
    localparam real TPER_CLK = 1e9 / 1e5;               // 10 us
    localparam real TFR      = 0.01 * TPER_CLK;          // rise/fall
    localparam real TON_CLK  = 0.5 * TPER_CLK - 2 * TFR;
    localparam real TPER2CLK = 0.95 * TPER_CLK;          // actual CLK period
    localparam real TSTOP    = 24 * TPER_CLK;
    localparam real TPER_D   = 16 * TPER_CLK;            // MODE period
    localparam real TON_D    = 0.5 * TPER_D - 2 * TFR;
    localparam real TD_R     = 2 * TPER_CLK;             // RSTn release

    reg clk = 0, rstn = 0, mode = 0, ready = 1;
    reg [N-1:0] en   = {N{1'b1}};
    reg [N-1:0] vals = 16'hA5C3;
    wire [N-1:0] rec, ipg;

    dbs #(.N(N)) dut (
        .clk(clk), .rstn(rstn), .mode(mode), .en(en),
        .vals(vals), .ready(ready), .rec(rec), .ipg(ipg)
    );

    // V4: PULSE(0 5 0 tfr tfr ton_clk tper2clk)
    initial begin
        #(TFR / 2);
        forever begin
            clk = 1; #(TON_CLK + TFR);
            clk = 0; #(TPER2CLK - TON_CLK - TFR);
        end
    end

    // V3: PULSE(0 5 0 tfr tfr ton_D tper_D)
    initial begin
        #(TFR / 2);
        forever begin
            mode = 1; #(TON_D + TFR);
            mode = 0; #(TPER_D - TON_D - TFR);
        end
    end

    // V5: PULSE(0 5 td_R ...) -> RSTn held low until td_R
    initial begin
        #(TD_R + TFR / 2);
        rstn = 1;
    end

    // ---------------- checks ----------------
    integer errors = 0;
    integer k;

    always @(*) begin
        #1; // let combinational logic settle
        if (|(dut.sw_rec & dut.sw_ipg)) begin
            $display("ERROR %0t: SW_REC and SW_IPG both on (%h)", $time, dut.sw_rec & dut.sw_ipg);
            errors = errors + 1;
        end
        if ((dut.sw_rec !== ~dut.sw_rec_b) || (dut.sw_ipg !== ~dut.sw_ipg_b)) begin
            $display("ERROR %0t: switch outputs not complementary", $time);
            errors = errors + 1;
        end
        for (k = 0; k < N; k = k + 1) begin
            if (rec[k] !== (dut.sw_rec[k] ? vals[k] : 1'bz)) begin
                $display("ERROR %0t: rec[%0d]=%b, expected %b", $time, k, rec[k], dut.sw_rec[k] ? vals[k] : 1'bz);
                errors = errors + 1;
            end
            if (ipg[k] !== (dut.sw_ipg[k] ? vals[k] : 1'bz)) begin
                $display("ERROR %0t: ipg[%0d]=%b, expected %b", $time, k, ipg[k], dut.sw_ipg[k] ? vals[k] : 1'bz);
                errors = errors + 1;
            end
        end
    end

    // same signals as the wrdata line in ROW_tb.sch (channel 0), sampled every 100 ns
    integer fd;
    initial begin
        $dumpfile("sim/dbs_tb.vcd");
        $dumpvars(0, dbs_tb);
        fd = $fopen("sim/dbs_tb_transitions.txt", "w");
        $fdisplay(fd, "# time_s clk mode rstn eni_q2 rec_en treat_en sw_rec sw_ipg sw_recb sw_ipgb");
        while ($realtime < TSTOP) begin
            $fdisplay(fd, "%e %b %b %b %b %b %b %b %b %b %b", $realtime * 1e-9,
                      clk, mode, rstn, dut.ctrl.en_reg_2[0], dut.ctrl.rec_en, dut.ctrl.treat_en,
                      dut.sw_rec[0], dut.sw_ipg[0], dut.sw_rec_b[0], dut.sw_ipg_b[0]);
            #100;
        end
        $fclose(fd);
        if (errors == 0) $display("PASS: no errors");
        else             $display("FAIL: %0d errors", errors);
        $finish;
    end

endmodule
