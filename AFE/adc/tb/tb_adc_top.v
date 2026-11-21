`timescale 1ns/1ps
// tb_adc_top: self-checking Icarus testbench of adc_top #(N = 4), the 80-SCLK frame of Decision 54 (AFE/adc/SPI_FRAME.md), with IDEAL comparator models (ana_model).
// Plusargs: +PER=<SCLK period ns> +MODE=exh|rand|edge +NF=<frames> .   exh: every code on every channel (channel c sees code (f + 1024 c) mod 4096 in frame f: NF = 4096 covers all codes on all 4 channels);
// rand: random codes incl. 0 / 4095 and random config words; edge: the protocol corner cases (runt frames, commit at edge 17, WR = 0 / 1, edges beyond 80, CS rising mid-frame, RSTN mid-frame, DOUT preload ...).
// Every frame is compared bit by bit against an expected 80-bit stream built from the HELD config before the frame, the channel numbers and the input codes (function exp_stream), independent of the RTL.
module tb_adc_top;
    localparam N = 4;
    reg cs_n = 1, sclk = 0, din = 0, rstn = 0;
    wire dout, dout_oe, mode_o, rst_amp_o;
    wire [N-1:0] en_o, cmp_clk, rst_sw, tg_on, gdn;
    wire [12*N-1:0] gp, gn;
    wire [N-1:0] cmp_q;
    reg  [12*N-1:0] vin_all = 0;
    real PER = 500.0;
    integer NF = 16;
    reg [255:0] MODE_S;
    integer errs = 0, nfr = 0;

    adc_top #(.N(N)) dut (.cs_n(cs_n), .sclk(sclk), .din(din), .rstn(rstn), .dout(dout), .dout_oe(dout_oe), .rst_amp_o(rst_amp_o), .mode_o(mode_o), .en_o(en_o),
                          .cmp_q(cmp_q), .cmp_clk(cmp_clk), .rst_sw(rst_sw), .tg_on(tg_on), .dac_gp(gp), .dac_gn(gn), .dac_gdn(gdn));

    // dummy-unit bottom must be grounded whenever the sampling TG is off (gdn = ~tg_on at every instant; TG off and gdn high at every comparator evaluation)
    integer egd = 0;
    always @(gdn or tg_on) #0.001 if (gdn !== ~tg_on) egd = egd + 1;
    genvar g;
    generate for (g = 0; g < N; g = g + 1) begin : gdchk
        always @(posedge cmp_clk[g]) if (gdn[g] !== 1'b1 || tg_on[g] !== 1'b0) egd = egd + 1;
    end endgenerate

    wire [31:0] ecb [0:N-1], eco [0:N-1], etm [0:N-1], ech [0:N-1], eor [0:N-1], ez [0:N-1], nd [0:N-1];
    wire [11:0] vs [0:N-1];
    generate for (g = 0; g < N; g = g + 1) begin : an
        ana_model m (.tg_on(tg_on[g]), .rst_sw(rst_sw[g]), .cmp_clk(cmp_clk[g]), .gp(gp[12*g +: 12]), .gn(gn[12*g +: 12]), .vin(vin_all[12*g +: 12]),
                     .cmp_q(cmp_q[g]), .e_crowbar(ecb[g]), .e_cont(eco[g]), .e_tmin(etm[g]), .e_chg(ech[g]), .e_order(eor[g]), .e_z(ez[g]), .vs(vs[g]), .n_dec(nd[g]));
    end endgenerate
    function integer esum(input integer dummy);
        integer c; begin esum = 0; for (c = 0; c < N; c = c + 1) esum = esum + ecb[c] + eco[c] + etm[c] + ech[c] + eor[c] + ez[c]; end
    endfunction

    // DOUT may only change on SCLK falling edges (or asynchronously to the preload value when CS rises)
    integer e_dout = 0;
    always @(dout) if (sclk && !cs_n && rstn) e_dout = e_dout + 1;
    // pad OE = ~CS
    integer e_oe = 0;
    always @(cs_n or dout_oe) #1 if (dout_oe !== ~cs_n) e_oe = e_oe + 1;
    // the held config may only change on an SCLK rising edge (never while SCLK is low) or by RSTN
    integer e_cfgt = 0;
    always @({rst_amp_o, mode_o, en_o}) if (rstn && !sclk && $time > 0) e_cfgt = e_cfgt + 1;

    // ---- expected stream (independent of the RTL): position j = 0..79 is the bit read at edge j + 1 ----
    reg [5:0]       cfg_exp = 6'd0;                 // {RST_AMP, MODE, EN[3:0]}: the config the DUT must hold
    reg [5:0]       pre_cfg = 6'd0;                 // held config at the start of the frame
    reg [12*N-1:0]  vin_frame;                      // codes at the start of the frame (CS falling = sampling instant)
    function exp_bit(input integer j);
        integer w, p;
        reg [15:0] wd;
        begin
            w = j / 16; p = j % 16;
            if (w == 0)      wd = {4'b1010, pre_cfg[5], pre_cfg[4], pre_cfg[3:0], 6'd0};
            else if (w <= N) wd = {w[1:0] - 2'd1, 2'b00, vin_frame[12*(w-1) +: 12]};
            else             wd = 16'd0;
            exp_bit = wd[15 - p];
        end
    endfunction

    // ---- SPI master ----
    reg [95:0] rx;                                   // rx[95 - (k-1)] = bit read at edge k (k = 1..80); bits 81.. go to rx_tail
    reg [15:0] rx_tail;
    integer    ntail;
    reg        pre_ok;                               // DOUT = 1 and DOUT_OE = 1 right after CS falls (before any SCLK edge)
    task frame(input integer nclk, input [15:0] w0, input integer ncs_hold);
        integer k;
        begin
            rx = 0; rx_tail = 0; ntail = 0; pre_cfg = {rst_amp_o, mode_o, en_o};
            #(PER);                                  // CS high setup
            cs_n = 0; vin_frame = vin_all;
            #(1.0); pre_ok = (dout === 1'b1) && (dout_oe === 1'b1);
            #(99.0);                                 // CS falling -> first SCLK >= 100 ns (the sampling instant is the CS edge)
            for (k = 1; k <= nclk; k = k + 1) begin
                din = (k <= 16) ? w0[16 - k] : $random;
                #(PER/2); sclk = 1;
                if (k <= 80) rx[95 - (k - 1)] = dout;
                else begin rx_tail = {rx_tail[14:0], dout}; ntail = ntail + 1; end
                #(PER/2); sclk = 0;
            end
            #(PER/2 + ncs_hold);
            cs_n = 1;
            // commit rule: edge 17 with WR = 1 (the config bits come from word 0)
            if (nclk >= 17 && w0[15]) cfg_exp = {w0[14], w0[13], w0[3:0]};
        end
    endtask

    // compare the frame bit by bit (first nbits stream positions); returns the number of wrong bits
    integer bad_bits;
    task check_stream(input integer nbits, input [255:0] what);
        integer j, nb;
        begin
            nb = 0;
            for (j = 0; j < nbits; j = j + 1)
                if (rx[95 - j] !== exp_bit(j)) begin
                    nb = nb + 1;
                    if (errs + nb < 30) $display("  ERR %0s frame %0d: edge %0d (word %0d bit %0d) read %b expected %b", what, nfr, j + 1, j / 16, 15 - (j % 16), rx[95 - j], exp_bit(j));
                end
            bad_bits = nb; errs = errs + nb;
        end
    endtask
    task check_cfg(input [255:0] what);
        begin
            if (pre_ok !== 1'b1) begin errs = errs + 1; $display("  ERR %0s: DOUT not preloaded to 1 with OE high at CS falling", what); end
            if ({rst_amp_o, mode_o, en_o} !== cfg_exp) begin errs = errs + 1; $display("  ERR %0s: held config %b expected %b", what, {rst_amp_o, mode_o, en_o}, cfg_exp); end
        end
    endtask
    task idle_check(input [255:0] what);   // after CS rises: all ADC drivers released, tracking on
        begin
            #20;
            if (rst_sw !== {N{1'b1}}) begin errs = errs + 1; $display("  ERR %0s: rst_sw=%b after CS rising", what, rst_sw); end
            if (gp !== {(12*N){1'b1}} || gn !== {(12*N){1'b0}}) begin errs = errs + 1; $display("  ERR %0s: drivers not tri-state after CS rising", what); end
            #30;
            if (tg_on !== {N{1'b1}}) begin errs = errs + 1; $display("  ERR %0s: tg_on=%b", what, tg_on); end
            if (dout_oe !== 1'b0) begin errs = errs + 1; $display("  ERR %0s: DOUT_OE high while CS high", what); end
        end
    endtask
    // full 80-edge frame + all checks
    task full(input [15:0] w0, input [255:0] what);
        begin
            frame(80, w0, 0);
            check_stream(80, what);
            check_cfg(what);
            idle_check(what);
            nfr = nfr + 1;
        end
    endtask
    task new_codes_fixed; integer c2; begin for (c2 = 0; c2 < N; c2 = c2 + 1) vin_all[12*c2 +: 12] = 100 + 37 * c2; end endtask
    task new_codes_rand;  integer c2; begin for (c2 = 0; c2 < N; c2 = c2 + 1) vin_all[12*c2 +: 12] = $random; end endtask

    integer f, c, nbitsum;
    reg [15:0] w0;
    reg [11:0] vv;
    initial begin
        if (!$value$plusargs("PER=%f", PER)) PER = 500.0;
        if (!$value$plusargs("NF=%d", NF)) NF = 16;
        if (!$value$plusargs("MODE=%s", MODE_S)) MODE_S = "rand";
        #50 rstn = 1; #50;
        if (MODE_S == "exh" || MODE_S == "rand") begin
            for (f = 0; f < NF; f = f + 1) begin
                for (c = 0; c < N; c = c + 1) begin
                    if (MODE_S == "exh") vv = (f + 1024 * c) % 4096;
                    else vv = (f < 4) ? (f == 0 ? 12'd0 : f == 1 ? 12'd4095 : f == 2 ? 12'd2048 : 12'd2047) : $random;
                    vin_all[12*c +: 12] = vv;
                end
                w0 = $random;
                if (f % 7 == 3) w0[15] = 1'b0;     // some frames with WR = 0
                if (f % 7 == 5) w0[15] = 1'b1;
                full(w0, "rand/exh");
            end
        end else begin
            // ---- edge cases ----
            // 1. reset state: nothing configured, DOUT idle
            if ({rst_amp_o, mode_o, en_o} !== 6'd0) begin errs = errs + 1; $display("ERR reset cfg"); end
            if (dout_oe !== 1'b0) begin errs = errs + 1; $display("ERR DOUT_OE after reset"); end
            // 2. first frame, status word of the empty config, WR = 0 (nothing committed)
            new_codes_fixed;
            full(16'h4003, "wr0_first");                              // WR = 0, RST_AMP = 1, EN = 3: ignored, cfg stays 0
            // 3. WR = 1 commits at edge 17: runt frames of 16 edges change nothing, 17 edges commit
            frame(16, 16'hC003, 0); check_cfg("wr1_16edges"); idle_check("wr1_16edges");         // WR = 1, RST_AMP = 1, EN = 3, but only 16 edges: no commit
            frame(17, 16'h8015, 0); check_cfg("wr1_17edges"); idle_check("wr1_17edges");        // WR = 1: commit at edge 17 -> MODE = 0, RST_AMP = 0, EN = 5
            if ({rst_amp_o, mode_o, en_o} !== 6'b00_0101) begin errs = errs + 1; $display("ERR 17-edge frame did not commit: %b", {rst_amp_o, mode_o, en_o}); end
            frame(20, 16'h4002, 0);   check_cfg("wr0_20edges"); idle_check("wr0_20edges");     // WR = 0: no change
            frame(79, 16'hE00F, 0);   check_cfg("wr1_79edges"); idle_check("wr1_79edges");     // WR = 1, RST_AMP = 1, MODE = 1, EN = F: commits (>= 17 edges)
            check_stream(79, "wr1_79edges");                           // the first 79 bits of that frame are the held config of before
            // 4. every field of the config word, one at a time (WR = 1) and the status word read back by the next frame
            new_codes_fixed;
            full(16'h8000, "cfg_none");
            full(16'h8001, "cfg_en0");  full(16'h8002, "cfg_en1");  full(16'h8004, "cfg_en2");  full(16'h8008, "cfg_en3");
            full(16'hA000, "cfg_mode"); full(16'hC000, "cfg_rst");  full(16'hE00F, "cfg_all");  full(16'h8000, "cfg_clr");
            full(16'h8000, "cfg_clr2");
            // 5. WR = 0 keeps the old config whatever the other bits say
            full(16'h800A, "wr_set");   full(16'h7FFF, "wr0_all_ones"); full(16'h0000, "wr0_zero"); full(16'h0000, "wr0_zero2");
            // 6. reserved bits [12:4] are ignored (host sends 0; a 1 there must not matter)
            full(16'h9FF3, "reserved_ones");  full(16'h8000 | 16'h0ff0, "reserved_ones2");  full(16'h8000, "cfg_clr3");
            // 7. aborted frames (CS rises mid-frame): no commit; the next full frame is clean; zero- and one-clock frames
            new_codes_fixed;
            frame(0, 16'hFFFF, 0);  check_cfg("zero_clk");  idle_check("zero_clk");
            frame(1, 16'hFFFF, 0);  check_cfg("one_clk");   idle_check("one_clk");
            for (c = 0; c < N; c = c + 1) vin_all[12*c +: 12] = 4095 - 511 * c;
            frame(5, 16'hFFFF, 0);  check_cfg("abort5");    idle_check("abort5");
            frame(13, 16'hFFFF, 0); check_cfg("abort13");   idle_check("abort13");
            frame(16, 16'hFFFF, 0); check_cfg("abort16");   idle_check("abort16");
            frame(21, 16'h0000, 0); check_cfg("abort21");   idle_check("abort21");
            frame(40, 16'h8000, 0); check_cfg("abort40");   idle_check("abort40");           // 40 edges with WR = 1: commits (cfg 0)
            full(16'h80A5, "after_abort");
            // 8. more than 80 edges: DOUT = 0 after edge 80, nothing else happens (config word of edges 1-16 only)
            new_codes_rand;
            frame(95, 16'h8033, 0);
            check_stream(80, "c95"); check_cfg("c95"); idle_check("c95");
            if (rx_tail !== 16'd0 || ntail !== 15) begin errs = errs + 1; $display("ERR c95: DOUT after edge 80 = %b (%0d edges), expected 0", rx_tail, ntail); end
            nfr = nfr + 1;
            // 9. SCLK toggles while CS is high: nothing moves
            repeat (50) begin #(PER/2) sclk = 1; #(PER/2) sclk = 0; end
            idle_check("sclk_cs_high");
            if (dout_oe !== 1'b0) begin errs = errs + 1; $display("ERR dout_oe while CS high"); end
            full(16'h0000, "after_sclk_idle");
            // 10. RSTN in the middle of a frame (after 40 edges) clears the config; DOUT is preset to 1 while reset is low
            full(16'h80FF, "pre_rstn");
            cs_n = 0; #100;
            repeat (40) begin #(PER/2) sclk = 1; #(PER/2) sclk = 0; end
            rstn = 0; #20; rstn = 1; #20;
            cfg_exp = 6'd0;
            if ({rst_amp_o, mode_o, en_o} !== 6'd0) begin errs = errs + 1; $display("ERR rstn cfg"); end
            #(PER); cs_n = 1; idle_check("rstn_mid");
            full(16'h0000, "after_rstn");
            // 11. RST_AMP is a LEVEL: set by a WR frame, kept across a 100 ms idle gap and runt frames, cleared by a WR frame or RSTN
            full(16'hC000, "rst_set");
            if (rst_amp_o !== 1'b1) begin errs = errs + 1; $display("ERR rst_amp not set"); end
            frame(10, 16'h0000, 0); check_cfg("rst_runt"); idle_check("rst_runt");
            if (rst_amp_o !== 1'b1) begin errs = errs + 1; $display("ERR rst_amp cleared by a runt frame"); end
            #(100_000_000.0);
            if (rst_amp_o !== 1'b1) begin errs = errs + 1; $display("ERR rst_amp dropped during 100 ms idle"); end
            full(16'hE000, "rst_mode");
            full(16'hA000, "rst_clr");
            if (rst_amp_o !== 1'b0) begin errs = errs + 1; $display("ERR rst_amp not cleared"); end
            full(16'hC0FF, "rst_set2");
            rstn = 0; #20; rstn = 1; #20; cfg_exp = 6'd0;
            if ({rst_amp_o, mode_o, en_o} !== 6'd0) begin errs = errs + 1; $display("ERR rstn did not clear rst_amp"); end
            // 12. back-to-back frames at the minimum CS-high time (1 SCLK period) with changing codes
            for (f = 0; f < 6; f = f + 1) begin new_codes_rand; full(16'h8000 + f * 16'h0111 + 1, "b2b"); end
            // 13. a frame whose DIN is all ones / all zeros / alternating (the data words 1..4 of DIN are ignored)
            new_codes_fixed;
            full(16'hFFFF, "din_ones"); full(16'h0000, "din_zero"); full(16'hAAAA, "din_alt");
            // 14. codes 0 and 4095 on every channel
            for (c = 0; c < N; c = c + 1) vin_all[12*c +: 12] = (c % 2) ? 12'd4095 : 12'd0;
            full(16'h8000, "extreme_codes");
            for (c = 0; c < N; c = c + 1) vin_all[12*c +: 12] = (c % 2) ? 12'd0 : 12'd4095;
            full(16'h8000, "extreme_codes2");
        end
        if (esum(0) != 0) errs = errs + 1;
        $display("EVENTS frames %0d decisions %0d %0d %0d %0d", nfr, nd[0], nd[1], nd[2], nd[3]);
        $display("RESULT %0s PER %0.2f frames %0d errors %0d e_dout %0d e_oe %0d e_cfgt %0d  crowbar %0d contention %0d dac->cmp<TMIN %0d dac-change-in-window %0d order %0d Zbit %0d dummy-driver errors %0d",
                 (errs == 0 && egd == 0 && e_dout == 0 && e_oe == 0 && e_cfgt == 0 && esum(0) == 0) ? "PASS" : "FAIL", PER, nfr, errs, e_dout, e_oe, e_cfgt,
                 ecb[0]+ecb[1]+ecb[2]+ecb[3], eco[0]+eco[1]+eco[2]+eco[3], etm[0]+etm[1]+etm[2]+etm[3], ech[0]+ech[1]+ech[2]+ech[3], eor[0]+eor[1]+eor[2]+eor[3], ez[0]+ez[1]+ez[2]+ez[3], egd);
        $finish;
    end
endmodule
