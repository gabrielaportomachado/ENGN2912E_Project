// 16-channel demo testbench for dbs.v.
//
// Three experiments, each one full MODE period (8 cycles REC + 8 cycles TREAT):
//   A: all 16 channels enabled          -> every channel switches REC, then IPG
//   B: only even channels enabled       -> odd channels stay off the whole time
//   C: only channels 0-7 enabled       -> channels 8-15 stay off the whole time
// READY is held high throughout.
//
// Self-checks:
//   - SW_REC and SW_IPG are never on together, and the _b outputs are complements
//   - rec/ipg carry vals when their switch is on, and float (z) otherwise
//   - once settled (>= 3 cycles after a MODE or EN change), in REC mode
//     SW_REC == EN & READY and SW_IPG == 0; in TREAT mode the other way round
`timescale 1ns/1ps

module dbs_tb_16ch;

    localparam N = 16;
    localparam real TCLK = 10000.0;     // 100 kHz, as in ROW_tb.sch
    localparam SEG = 16;                // cycles per experiment
    localparam C_A = 2;                 // reset held for the first 2 cycles
    localparam C_B = C_A + SEG;
    localparam C_C = C_B + SEG;
    localparam C_END = C_C + SEG;

    reg clk = 0, rstn = 0, mode = 1, ready = 1;
    reg [N-1:0] en   = {N{1'b1}};
    reg [N-1:0] vals = 16'hA5C3;
    wire [N-1:0] rec, ipg;

    dbs #(.N(N)) dut (
        .clk(clk), .rstn(rstn), .mode(mode), .en(en),
        .vals(vals), .ready(ready), .rec(rec), .ipg(ipg)
    );

    always #(TCLK / 2) clk = ~clk;

    // ---------------- stimulus: inputs change 1 ns after each rising edge ----------------
    integer cyc = -1;           // index of the most recent rising clock edge
    integer last_change = 0;    // cycle of the last MODE or EN change
    reg mode_n, ready_n;
    reg [N-1:0] en_n;

    always @(posedge clk) begin
        cyc = cyc + 1;
        #1;
        mode_n  = mode;
        en_n    = en;
        ready_n = 1;
        if (cyc == C_A) rstn = 1;
        if (cyc >= C_A && cyc < C_END)
            mode_n = (((cyc - C_A) % SEG) < SEG / 2);
        if (cyc == C_A) en_n = {N{1'b1}};                 // A: all channels
        if (cyc == C_B) en_n = 16'h5555;                  // B: even channels only
        if (cyc == C_C) en_n = 16'h00FF;                  // C: channels 0-7 only
        if (mode_n !== mode || en_n !== en || cyc == C_A) last_change = cyc;
        mode  = mode_n;
        en    = en_n;
        ready = ready_n;
    end

    // ---------------- checks ----------------
    integer errors = 0;
    integer k;

    task fail(input [8*64-1:0] msg);
        begin
            $display("ERROR t=%0t cyc=%0d: %0s", $time, cyc, msg);
            errors = errors + 1;
        end
    endtask

    always @(*) begin
        #2;
        if (|(dut.sw_rec & dut.sw_ipg)) fail("SW_REC and SW_IPG both on");
        if ((dut.sw_rec !== ~dut.sw_rec_b) || (dut.sw_ipg !== ~dut.sw_ipg_b))
            fail("switch outputs not complementary");
        for (k = 0; k < N; k = k + 1) begin
            if (rec[k] !== (dut.sw_rec[k] ? vals[k] : 1'bz)) fail("rec != vals through switch");
            if (ipg[k] !== (dut.sw_ipg[k] ? vals[k] : 1'bz)) fail("ipg != vals through switch");
        end
    end

    // intent check at the middle of every cycle once things have settled
    always @(negedge clk) begin
        if (rstn && cyc - last_change >= 3) begin
            if (mode) begin
                if (dut.sw_rec !== (en & {N{ready}})) fail("REC mode: SW_REC != EN & READY");
                if (dut.sw_ipg !== {N{1'b0}})         fail("REC mode: SW_IPG on");
            end else begin
                if (dut.sw_ipg !== (en & {N{ready}})) fail("TREAT mode: SW_IPG != EN & READY");
                if (dut.sw_rec !== {N{1'b0}})         fail("TREAT mode: SW_REC on");
            end
        end
    end

    // ---------------- dump: 4 samples per clock cycle ----------------
    integer fd;
    initial begin
        fd = $fopen("sim/dbs_tb_16ch.txt", "w");
        $fdisplay(fd, "# cycle rstn mode ready rec_en treat_en en sw_rec sw_ipg (hex buses, bit k = channel k)");
        #(TCLK / 2 + TCLK / 8);
        while (cyc < C_END + 2) begin
            // cycle n = rising clock edge n (first edge is at TCLK/2)
            $fdisplay(fd, "%.3f %b %b %b %b %b %h %h %h", $realtime / TCLK - 0.5,
                      rstn, mode, ready, dut.ctrl.rec_en, dut.ctrl.treat_en, en, dut.sw_rec, dut.sw_ipg);
            #(TCLK / 4);
        end
        $fclose(fd);
        if (errors == 0) $display("PASS: no errors");
        else             $display("FAIL: %0d errors", errors);
        $finish;
    end

endmodule
