// Testbench for the fsm module in dbs.v, using the stimulus of FSM/FSM_tb.sch:
//   fclk = 100 kHz, CLK period 0.95*tper_clk, MODE period 16*tper_clk,
//   RSTn released at 2*tper_clk, tstop = 24*tper_clk.
// After that, MODE is driven randomly for a while so every reachable state
// transition gets exercised. Each clock edge is checked against a reference model.
`timescale 1ns/1ps

module fsm_tb;

    // same quantities as the .control block in FSM_tb.sch (in ns)
    localparam real TPER_CLK = 1e9 / 1e5;               // 10 us
    localparam real TFR      = 0.01 * TPER_CLK;          // rise/fall
    localparam real TON_CLK  = 0.5 * TPER_CLK - 2 * TFR;
    localparam real TPER2CLK = 0.95 * TPER_CLK;          // actual CLK period
    localparam real TSTOP    = 24 * TPER_CLK;
    localparam real TPER_D   = 16 * TPER_CLK;            // MODE period
    localparam real TON_D    = 0.5 * TPER_D - 2 * TFR;
    localparam real TD_R     = 2 * TPER_CLK;             // RSTn release
    localparam integer N_RANDOM = 200;                   // random-MODE clock cycles after TSTOP

    reg clk = 0, rstn = 0, mode = 0;
    wire rec_en, treat_en;

    fsm dut (.clk(clk), .rstn(rstn), .mode(mode), .rec_en(rec_en), .treat_en(treat_en));

    // V4: PULSE(0 5 0 tfr tfr ton_clk tper2clk)
    initial begin
        #(TFR / 2);
        forever begin
            clk = 1; #(TON_CLK + TFR);
            clk = 0; #(TPER2CLK - TON_CLK - TFR);
        end
    end

    // V3: PULSE(0 5 0 tfr tfr ton_D tper_D) until TSTOP, then random MODE
    // changes on the falling clock edge
    initial begin
        #(TFR / 2);
        while ($realtime < TSTOP) begin
            mode = 1; #(TON_D + TFR);
            mode = 0; #(TPER_D - TON_D - TFR);
        end
        repeat (N_RANDOM) begin
            @(negedge clk);
            mode = $random;
        end
        @(negedge clk);
        finish_sim;
    end

    // V5: PULSE(0 5 td_R ...) -> RSTn held low until td_R
    initial begin
        #(TD_R + TFR / 2);
        rstn = 1;
    end

    // ---------------- reference model + checks ----------------
    reg m_s0 = 1, m_s1 = 0;     // reset state of the model, same as the flops
    integer errors = 0;
    integer covered [0:3][0:1]; // covered[state][mode], state = {s0, s1}
    integer a, b;

    initial for (a = 0; a < 4; a = a + 1) for (b = 0; b < 2; b = b + 1) covered[a][b] = 0;

    always @(posedge clk or negedge rstn) begin
        if (!rstn) begin
            m_s0 <= 1;
            m_s1 <= 0;
        end else begin
            covered[{m_s0, m_s1}][mode] = covered[{m_s0, m_s1}][mode] + 1;
            m_s0 <= m_s1 | mode;
            m_s1 <= m_s0 & mode;
        end
    end

    always @(negedge clk) begin
        if ({dut.s0, dut.s1} !== {m_s0, m_s1}) begin
            $display("ERROR %0t: state {s0,s1}=%b%b, expected %b%b", $time, dut.s0, dut.s1, m_s0, m_s1);
            errors = errors + 1;
        end
        if (rec_en !== m_s1 || treat_en !== ~(m_s0 | m_s1)) begin
            $display("ERROR %0t: rec_en=%b treat_en=%b, expected %b %b",
                     $time, rec_en, treat_en, m_s1, ~(m_s0 | m_s1));
            errors = errors + 1;
        end
        if (rec_en && treat_en) begin
            $display("ERROR %0t: REC_EN and TREAT_EN both high", $time);
            errors = errors + 1;
        end
    end

    // same signals as the FSM SPICE runs, sampled every 100 ns up to TSTOP
    integer fd;
    initial begin
        $dumpfile("sim/fsm_tb.vcd");
        $dumpvars(0, fsm_tb);
        fd = $fopen("sim/fsm_tb_transitions.txt", "w");
        $fdisplay(fd, "# time_s clk mode rstn s0 s1 rec_en treat_en");
        while ($realtime < TSTOP) begin
            $fdisplay(fd, "%e %b %b %b %b %b %b %b", $realtime * 1e-9,
                      clk, mode, rstn, dut.s0, dut.s1, rec_en, treat_en);
            #100;
        end
        $fclose(fd);
    end

    // every transition reachable from reset: {s0,s1} = 10, 11, 00 with MODE = 0/1
    // ({s0,s1} = 01 is unreachable)
    task finish_sim;
        begin
            for (a = 0; a < 4; a = a + 1) begin
                if (a == 2'b01) begin
                    if (covered[a][0] + covered[a][1] != 0) begin
                        $display("ERROR: unreachable state 01 was entered");
                        errors = errors + 1;
                    end
                end else for (b = 0; b < 2; b = b + 1) begin
                    $display("transition {s0,s1}=%b%b mode=%0d: %0d times", a[1], a[0], b, covered[a][b]);
                    if (covered[a][b] == 0) begin
                        $display("ERROR: transition from %b%b with mode=%0d never exercised", a[1], a[0], b);
                        errors = errors + 1;
                    end
                end
            end
            if (errors == 0) $display("PASS: no errors");
            else             $display("FAIL: %0d errors", errors);
            $finish;
        end
    endtask

endmodule
