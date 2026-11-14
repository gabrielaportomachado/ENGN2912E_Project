`timescale 1ns/1ps
// tb_adc8: Icarus testbench for adc8_top with IDEAL comparator models (ana_model).  Plusargs: +PER=<SCLK period ns> +MODE=exh|rand|edge +NF=<frames> +TAG=<text>
// exh : every code on every channel (channel i sees code (f*1 + 512*i) mod 4096 in frame f, so NF = 4096 covers all codes on all 8 channels); rand: random codes incl. 0 / 4095; edge: CS / reset / runt-frame cases.
module tb_adc8;
    reg cs_n = 1, sclk = 0, din = 0, rstn = 0;
    wire dout, dout_oe, mode_o, rst_amp_o;
    wire [7:0] en_o, cmp_clk, rst_sw, tg_on, gdn;
    integer egd = 0;
    // D4: the dummy-unit bottom must be grounded whenever the sampling TG is off and floating-free (gdn = ~tg_on) at every instant
    always @(gdn or tg_on) #0.001 if (gdn !== ~tg_on) begin egd = egd + 1; end
    genvar gq; generate for (gq = 0; gq < 8; gq = gq + 1) begin : gdchk
        always @(posedge cmp_clk[gq]) if (gdn[gq] !== 1'b1 || tg_on[gq] !== 1'b0) egd = egd + 1;   // dummy bottom grounded and TG off at every comparator evaluation
    end endgenerate
    wire [95:0] gp, gn;
    wire [7:0] cmp_q;
    reg [95:0] vin_all = 0;
    real PER = 500.0;
    integer NF = 16;
    reg [255:0] MODE_S, TAG;
    integer errs = 0, nfr = 0;

    adc8_top dut (.cs_n(cs_n), .sclk(sclk), .din(din), .rstn(rstn), .dout(dout), .dout_oe(dout_oe), .rst_amp_o(rst_amp_o), .mode_o(mode_o), .en_o(en_o),
                  .cmp_q(cmp_q), .cmp_clk(cmp_clk), .rst_sw(rst_sw), .tg_on(tg_on), .dac_gp(gp), .dac_gn(gn), .dac_gdn(gdn));

    wire [31:0] ecb [0:7], eco [0:7], etm [0:7], ech [0:7], eor [0:7], ez [0:7], nd [0:7];
    wire [11:0] vs [0:7];
    genvar g;
    generate for (g = 0; g < 8; g = g + 1) begin : an
        ana_model m (.tg_on(tg_on[g]), .rst_sw(rst_sw[g]), .cmp_clk(cmp_clk[g]), .gp(gp[12*g +: 12]), .gn(gn[12*g +: 12]), .vin(vin_all[12*g +: 12]),
                     .cmp_q(cmp_q[g]), .e_crowbar(ecb[g]), .e_cont(eco[g]), .e_tmin(etm[g]), .e_chg(ech[g]), .e_order(eor[g]), .e_z(ez[g]), .vs(vs[g]), .n_dec(nd[g]));
    end endgenerate

    // DOUT may only change on SCLK falling edges (or asynchronously to 0 when CS rises)
    integer e_dout = 0;
    always @(dout) if (sclk && !cs_n && rstn) e_dout = e_dout + 1;
    // pad OE
    always @(cs_n or dout_oe) #1 if (dout_oe !== ~cs_n) errs = errs + 1;

    // ---- SPI master ----
    reg [159:0] rx;
    reg [9:0] pre_cfg = 10'd0;   // held config at the start of the frame = what word 1 must read back (I1)           // rx[159 - (k-1)] = bit sampled at edge k
    integer kk;
    task frame(input integer nclk, input [15:0] w0, input integer ncs_hold);
        integer k;
        begin
            rx = 0; pre_cfg = {rst_amp_o, mode_o, en_o};
            #(PER);            // CS high setup
            cs_n = 0;
            #(100.0);          // CS falling -> first SCLK >= 100 ns (sampling instant is the CS edge)
            for (k = 1; k <= nclk; k = k + 1) begin
                din = (k <= 16) ? w0[16 - k] : $random;
                #(PER/2); sclk = 1;
                if (k <= 160) rx[160 - k] = dout;
                #(PER/2); sclk = 0;
            end
            #(PER/2 + ncs_hold);
            cs_n = 1;
        end
    endtask

    function [11:0] code_of(input integer f, input integer ch);
        code_of = (f + 512 * ch) % 4096;
    endfunction
    function [15:0] expect_word(input integer w);   // 0..9 from rx
        expect_word = rx[159 - 16*w -: 16];
    endfunction

    integer badch [0:7];
    integer bi;
    initial for (bi = 0; bi < 8; bi = bi + 1) badch[bi] = 0;
    reg [9:0] cfg_exp = 10'd0;
    integer f, c, w, bad;
    reg [15:0] w0, ww;
    reg [11:0] vv;
    reg [95:0] vtmp;

    task check_full(input [9:0] cfg_new);
        integer c2;
        begin
            bad = 0;
            if (expect_word(0) !== 16'd0 || expect_word(1) !== {6'd0, pre_cfg}) begin bad = bad + 1; if (errs < 40) $display("  ERR word1 got %h exp %h", expect_word(1), {6'd0, pre_cfg}); end
            for (c2 = 0; c2 < 8; c2 = c2 + 1) begin
                ww = expect_word(2 + c2);
                if (ww !== {1'b0, c2[2:0], vin_all[12*c2 +: 12]}) begin
                    bad = bad + 1; badch[c2] = badch[c2] + 1;
                    if (errs < 0) $display("  ERR frame %0d ch %0d: got %h exp %h (vs %0d)", nfr, c2, ww, {1'b0, c2[2:0], vin_all[12*c2 +: 12]}, vs[c2]);
                end
            end
            if ({rst_amp_o, mode_o, en_o} !== cfg_new) begin bad = bad + 1; if (errs < 40) $display("  ERR cfg got %b exp %b", {rst_amp_o, mode_o, en_o}, cfg_new); end
            errs = errs + bad;
        end
    endtask

    task idle_check(input [255:0] what);   // after CS rises: all ADC drivers released, tracking on, no violations
        integer c2;
        begin
            #20;
            if (rst_sw !== 8'hff) begin errs = errs + 1; $display("  ERR %0s: rst_sw=%b after CS rising", what, rst_sw); end
            if (gp !== {96{1'b1}} || gn !== 96'd0) begin errs = errs + 1; $display("  ERR %0s: drivers not tri-state after CS rising", what); end
            #30;
            if (tg_on !== 8'hff) begin errs = errs + 1; $display("  ERR %0s: tg_on=%b", what, tg_on); end
        end
    endtask

    initial begin
        if (!$value$plusargs("PER=%f", PER)) PER = 500.0;
        if (!$value$plusargs("NF=%d", NF)) NF = 16;
        if (!$value$plusargs("MODE=%s", MODE_S)) MODE_S = "rand";
        #50 rstn = 1; #50;
        if (MODE_S == "exh" || MODE_S == "rand") begin
            for (f = 0; f < NF; f = f + 1) begin
                for (c = 0; c < 8; c = c + 1) begin
                    if (MODE_S == "exh") vv = code_of(f, c);
                    else vv = (f < 4) ? (f == 0 ? 12'd0 : f == 1 ? 12'd4095 : f == 2 ? 12'd2048 : 12'd2047) + c * (f < 4 ? 0 : 0) : $random;
                    vin_all[12*c +: 12] = vv;
                end
                w0 = {7'd0, $random} ; w0[15:10] = 6'd0;
                frame(160, w0, 0);
                nfr = nfr + 1;
                cfg_exp = w0[9:0];
                check_full(cfg_exp);
                idle_check("frame");
            end
        end else begin
            // ---- edge cases ----
            // 1. reset state
            if ({rst_amp_o, mode_o, en_o} !== 10'd0) begin errs = errs + 1; $display("ERR reset cfg"); end
            // 2. runt frames: 20 clocks with cfg 1FF -> no commit; 32 clocks -> none; 33 -> commit
            for (c = 0; c < 8; c = c + 1) vin_all[12*c +: 12] = 100 + 37 * c;
            frame(20, 16'h01ff, 0);  idle_check("runt20");  if ({rst_amp_o, mode_o, en_o} !== 10'd0) begin errs = errs + 1; $display("ERR runt20 committed"); end
            frame(32, 16'h01ff, 0);  idle_check("runt32");  if ({rst_amp_o, mode_o, en_o} !== 10'd0) begin errs = errs + 1; $display("ERR runt32 committed"); end
            frame(33, 16'h0155, 0);  idle_check("c33");     if ({rst_amp_o, mode_o, en_o} !== 10'h155) begin errs = errs + 1; $display("ERR 33-clock frame did not commit: %b", {rst_amp_o, mode_o, en_o}); end
            // a 16-clock frame with another config: no change; next full frame gives the new one
            frame(16, 16'h00aa, 0);  idle_check("c16");     if ({rst_amp_o, mode_o, en_o} !== 10'h155) begin errs = errs + 1; $display("ERR c16 changed cfg"); end
            frame(160, 16'h0080, 0); idle_check("full1");   check_full(10'h080);
            // 3. CS glitch with no clocks, and a 0-clock frame
            frame(0, 16'hffff, 0);   idle_check("zeroclk"); if ({rst_amp_o, mode_o, en_o} !== 10'h080) begin errs = errs + 1; $display("ERR zeroclk"); end
            frame(1, 16'hffff, 0);   idle_check("oneclk");
            // 4. abort mid conversion and mid readout, then a clean full frame
            for (c = 0; c < 8; c = c + 1) vin_all[12*c +: 12] = 4095 - 511 * c;
            frame(5, 16'h0000, 0);   idle_check("abort5");
            frame(13, 16'h0000, 0);  idle_check("abort13");
            frame(21, 16'h0000, 0);  idle_check("abort21");
            frame(40, 16'h0000, 0);  idle_check("abort40");
            frame(160, 16'h01a5, 0); idle_check("full2");   check_full(10'h1a5);
            // 5. more than 160 clocks: DOUT stays 0 after 160, config unchanged
            frame(170, 16'h0033, 0); idle_check("c170");
            if (rx[0] !== 1'b0) begin errs = errs + 1; $display("ERR c170 rx tail"); end
            if ({rst_amp_o, mode_o, en_o} !== 10'h033) begin errs = errs + 1; $display("ERR c170 cfg %b", {rst_amp_o, mode_o, en_o}); end
            // 6. SCLK toggles while CS is high: nothing moves
            repeat (50) begin #(PER/2) sclk = 1; #(PER/2) sclk = 0; end
            idle_check("sclk_cs_high");
            if (dout !== 1'b0) begin errs = errs + 1; $display("ERR dout while CS high"); end
            // 7. RSTN in the middle of a frame (after 40 clocks) clears config and ADC state
            cs_n = 0; #100;
            repeat (40) begin #(PER/2) sclk = 1; #(PER/2) sclk = 0; end
            rstn = 0; #20; rstn = 1; #20;
            if ({rst_amp_o, mode_o, en_o} !== 10'd0) begin errs = errs + 1; $display("ERR rstn cfg"); end
            #(PER); cs_n = 1; idle_check("rstn_mid");
            // 7b. RST_AMP (I0, Decision 38): DIN bit 9 of word 0.  Set in a full frame, held as a LEVEL across frames and a 100 ms idle gap, cleared by a frame, by RSTN, not by runt frames
            frame(160, 16'h0200, 0); idle_check("rst_set");   check_full(10'h200);
            if (rst_amp_o !== 1'b1) begin errs = errs + 1; $display("ERR rst_amp not set"); end
            frame(20, 16'h0000, 0);  idle_check("rst_runt");  if (rst_amp_o !== 1'b1) begin errs = errs + 1; $display("ERR rst_amp cleared by a runt frame"); end
            #(100_000_000.0);                                 // 100 ms with no clock and CS high
            if (rst_amp_o !== 1'b1) begin errs = errs + 1; $display("ERR rst_amp dropped during 100 ms idle"); end
            frame(160, 16'h0300, 0); idle_check("rst_mode");  check_full(10'h300);   // RST_AMP + MODE, EN = 0
            frame(160, 16'h0100, 0); idle_check("rst_clr");   check_full(10'h100);
            if (rst_amp_o !== 1'b0) begin errs = errs + 1; $display("ERR rst_amp not cleared"); end
            frame(160, 16'h02ff, 0); idle_check("rst_set2");  check_full(10'h2ff);
            rstn = 0; #20; rstn = 1; #20;
            if ({rst_amp_o, mode_o, en_o} !== 10'd0) begin errs = errs + 1; $display("ERR rstn did not clear rst_amp"); end
            frame(160, 16'hfc00, 0); idle_check("rst_upper"); check_full(10'h000);       // word-0 bits 15..10 are ignored
            // 8. back-to-back frames at the minimum CS-high time (1 SCLK period) with changing codes
            for (f = 0; f < 4; f = f + 1) begin
                for (c = 0; c < 8; c = c + 1) vin_all[12*c +: 12] = $random;
                frame(160, 16'h0100 + f, 0); idle_check("b2b"); check_full(10'h100 + f);
            end
        end
        $display("TMINCH %0d %0d %0d %0d %0d %0d %0d %0d  CHGCH %0d %0d %0d %0d %0d %0d %0d %0d", etm[0], etm[1], etm[2], etm[3], etm[4], etm[5], etm[6], etm[7], ech[0], ech[1], ech[2], ech[3], ech[4], ech[5], ech[6], ech[7]);
        $display("BADCH %0d %0d %0d %0d %0d %0d %0d %0d", badch[0], badch[1], badch[2], badch[3], badch[4], badch[5], badch[6], badch[7]);
        $display("RESULT %0s PER %0.2f frames %0d bad %0d e_dout %0d  crowbar %0d contention %0d dac->cmp<TMIN %0d dac-change-in-window %0d order %0d Zbit %0d decisions %0d dummy-driver errors %0d",
                 (errs == 0 && egd == 0 && e_dout == 0 && (ecb[0]+ecb[1]+ecb[2]+ecb[3]+ecb[4]+ecb[5]+ecb[6]+ecb[7]+eco[0]+eco[1]+eco[2]+eco[3]+eco[4]+eco[5]+eco[6]+eco[7]+etm[0]+etm[1]+etm[2]+etm[3]+etm[4]+etm[5]+etm[6]+etm[7]+ech[0]+ech[1]+ech[2]+ech[3]+ech[4]+ech[5]+ech[6]+ech[7]+eor[0]+eor[1]+eor[2]+eor[3]+eor[4]+eor[5]+eor[6]+eor[7]+ez[0]+ez[1]+ez[2]+ez[3]+ez[4]+ez[5]+ez[6]+ez[7]) == 0) ? "PASS" : "FAIL", PER, nfr, errs, e_dout,
                 ecb[0]+ecb[1]+ecb[2]+ecb[3]+ecb[4]+ecb[5]+ecb[6]+ecb[7], eco[0]+eco[1]+eco[2]+eco[3]+eco[4]+eco[5]+eco[6]+eco[7],
                 etm[0]+etm[1]+etm[2]+etm[3]+etm[4]+etm[5]+etm[6]+etm[7], ech[0]+ech[1]+ech[2]+ech[3]+ech[4]+ech[5]+ech[6]+ech[7],
                 eor[0]+eor[1]+eor[2]+eor[3]+eor[4]+eor[5]+eor[6]+eor[7], ez[0]+ez[1]+ez[2]+ez[3]+ez[4]+ez[5]+ez[6]+ez[7],
                 nd[0]+nd[1]+nd[2]+nd[3]+nd[4]+nd[5]+nd[6]+nd[7], egd);
        $finish;
    end
endmodule
