`timescale 1ns/1ps
// tb_top: Icarus testbench of the whole digital part (dbs_afe_top) with behavioural analog stubs (stubs_analog.v).  I0, 2026-11-14.
// Scenario: reset -> RST_AMP set / held >= 100 ms / cleared -> record start (config write, mode change) -> amplifier reset pulse (fs one-shot) -> ADC frames on DOUT
//           -> treat mode -> record again on 4 channels -> RST_AMP during record -> RSTN.  The stub amplifier outputs code 0xAAA while fs = 1, else the code written to u_amp.sim_vin (here vin_all).
// Also compares REC / IPG with a real `dbs #(8)` instance (rtl/dbs.v) fed with the same mode / en / E.
module tb_top;
    supply1 vdd_n; supply0 vss_n;
    reg cs = 1, din = 0, sclk = 0, rstn = 0;
    reg [7:0] eval = 8'h5a;
    wire [7:0] E, IPG, REC;
    assign E = eval;
    wire dout, dout_oe, d_ie, d_pd, d_pu, d_cs, d_sl, d_p0, d_p1, cs_pu, cs_pd, din_pu, din_pd, sclk_pu, sclk_pd, rstn_pu, rstn_pd;
    dbs_afe_top dut (.E(E), .IPG(IPG), .REC(REC), .CS(cs), .DIN(din), .SCLK(sclk), .RSTN(rstn), .DOUT(dout),
                     .DOUT_OE(dout_oe), .DOUT_IE(d_ie), .DOUT_PD(d_pd), .DOUT_PU(d_pu), .DOUT_CS(d_cs), .DOUT_SL(d_sl), .DOUT_PDRV0(d_p0), .DOUT_PDRV1(d_p1),
                     .CS_PU(cs_pu), .CS_PD(cs_pd), .DIN_PU(din_pu), .DIN_PD(din_pd), .SCLK_PU(sclk_pu), .SCLK_PD(sclk_pd), .RSTN_PU(rstn_pu), .RSTN_PD(rstn_pd),
                     .VDD(vdd_n), .VSS(vss_n));
    // reference: the real dbs module (dbs_ctrl + 16 TGATE) with the same inputs
    wire [7:0] ref_rec, ref_ipg;
    dbs #(.N(8)) ref_dbs (.clk(sclk), .rstn(rstn), .mode(dut.mode_o), .en(dut.en_o), .vals(E), .ready(1'b1), .rec(ref_rec), .ipg(ref_ipg));
    integer e_ref = 0;
    always @(REC or IPG or ref_rec or ref_ipg) begin #0.05; if (REC !== ref_rec || IPG !== ref_ipg) e_ref = e_ref + 1; end

    reg [95:0] vin_all = 96'd0;
    // ---- observation of the 8 channels ----
    wire [7:0] fs_v, swr_v;
    wire [31:0] os_n [0:7];
    wire [31:0] epark [0:7], edac [0:7];
    real t_fs_r [0:7];
    real t_fs_f [0:7];
    real t_sw_r [0:7];
    real t_swi_f [0:7];
    genvar g;
    generate for (g = 0; g < 8; g = g + 1) begin : ob
        assign fs_v[g]   = dut.ch[g].u.fs;
        assign swr_v[g]  = dut.ch[g].u.sw_rec;
        assign os_n[g]   = dut.ch[g].u.u_os.n_pulses;
        assign epark[g]  = dut.ch[g].u.u_amp.e_park;
        assign edac[g]   = dut.ch[g].u.u_dac.e_crowbar + dut.ch[g].u.u_dac.e_cont + dut.ch[g].u.u_dac.e_order + dut.ch[g].u.u_dac.e_samb;
        initial begin t_fs_r[g] = -1.0; t_fs_f[g] = -1.0; t_sw_r[g] = -1.0; t_swi_f[g] = -1.0; end
        always @(posedge fs_v[g]) t_fs_r[g] = $realtime;
        always @(negedge fs_v[g]) t_fs_f[g] = $realtime;
        always @(posedge swr_v[g]) t_sw_r[g] = $realtime;
        always @(negedge dut.sw_ipg[g]) t_swi_f[g] = $realtime;
        always @(vin_all[12*g +: 12]) dut.ch[g].u.u_amp.sim_vin = vin_all[12*g +: 12];
    end endgenerate

    integer errs = 0;
    task chk(input cond, input [511:0] msg);
        begin if (!cond) begin errs = errs + 1; $display("  ERR t=%0t: %0s", $time, msg); end end
    endtask

    // ---- SPI master (as tb_adc8): 160 edges, SCLK 2 MHz ----
    real PER = 500.0;
    reg [159:0] rx;
    reg [7:0] fs_at_cs;
    task frame(input [15:0] w0);
        integer k;
        begin
            rx = 0;
            fs_at_cs = fs_v;                 // state of the amplifier reset at the sampling instant (CS falling)
            cs = 0; #100.0;
            for (k = 1; k <= 160; k = k + 1) begin
                din = (k <= 16) ? w0[16 - k] : $random;
                #(PER/2); sclk = 1;
                rx[160 - k] = dout;
                #(PER/2); sclk = 0;
            end
            #(PER/2); cs = 1; #(PER);
        end
    endtask
    // one 250 us frame period (4 kS/s per channel): returns with CS high at the end of the period
    task period(input [15:0] w0);
        real t0;
        begin t0 = $realtime; frame(w0); #(250000.0 - ($realtime - t0)); end
    endtask
    function [15:0] word(input integer w); word = rx[159 - 16*w -: 16]; endfunction
    integer nbad_data = 0, nfs_frames = 0, nfr = 0;
    task check_data(input integer verbose);   // words 2..9 = {0, ID, code}; code = 0xAAA if the amplifier was in reset at CS falling, else vin
        integer c; reg [11:0] ex; reg [15:0] wd;
        begin
            for (c = 0; c < 8; c = c + 1) begin
                ex = fs_at_cs[c] ? 12'hAAA : vin_all[12*c +: 12];
                wd = word(2 + c);
                if (wd !== {1'b0, c[2:0], ex}) begin nbad_data = nbad_data + 1; if (verbose) $display("  ERR frame %0d ch %0d got %h exp %h", nfr, c, wd, {1'b0, c[2:0], ex}); end
            end
            if (word(0) !== 16'd0 || word(1) !== 16'd0) begin nbad_data = nbad_data + 1; if (verbose) $display("  ERR words 0/1 not zero"); end
            nfr = nfr + 1; if (fs_at_cs != 8'd0) nfs_frames = nfs_frames + 1;
        end
    endtask

    integer DOUT_OE_ok = 1;
    always @(cs or dout_oe) #1 if (dout_oe !== ~cs) DOUT_OE_ok = 0;
    integer e_dout = 0;     // DOUT may only change on SCLK falling edges (or to 0 when CS rises)
    always @(dout) if (sclk && !cs && rstn) e_dout = e_dout + 1;

    integer c, f;
    real t_set, t_clr, w, gap, gapmin, gapmax;
    initial begin
        for (c = 0; c < 8; c = c + 1) vin_all[12*c +: 12] = 100 + 37 * c;
        #100; rstn = 1; #100;
        // ---------------- T1: after reset ----------------
        chk(dut.sw_rec === 8'h00 && dut.sw_ipg === 8'h00 && dut.sw_rec_b === 8'hff, "T1 switches open, park ON after RSTN");
        chk(dut.rst_amp_o === 1'b0 && fs_v === 8'h00, "T1 no amplifier reset after RSTN");
        chk(dout_oe === 1'b0 && dout === 1'b0, "T1 DOUT_OE low while CS high");
        // ---------------- T2: RST_AMP set (config write), held, cleared ----------------
        period(16'h0200);                      // RST_AMP = 1, MODE = 0, EN = 0
        t_set = t_fs_r[0];
        chk(dut.rst_amp_o === 1'b1 && fs_v === 8'hff, "T2 RST_AMP set -> fs high on all 8 channels");
        chk(dut.sw_rec === 8'h00 && os_n[0] === 0, "T2 RST_AMP does not touch the routing or the one-shot");
        check_data(1);                         // this frame sampled before the commit: normal codes
        period(16'h0200);   check_data(1);     // this frame sampled while fs = 1: every channel reads 0xAAA
        chk(fs_at_cs === 8'hff && nfs_frames == 1, "T2 frame sampled while fs = 1 carries the reset code");
        #30_000_000.0; chk(fs_v === 8'hff, "T2 fs still high 30 ms after set");
        #75_000_000.0; chk(fs_v === 8'hff, "T2 fs still high 105 ms after set, no clock, CS high");
        period(16'h0000);                      // clear
        t_clr = t_fs_f[0];
        chk(dut.rst_amp_o === 1'b0 && fs_v === 8'h00, "T2 RST_AMP cleared -> fs low");
        $display("T2: fs[0] high from %0.3f ms to %0.3f ms = %0.3f ms (the host holds the bit; the RTL adds no timer)", t_set/1e6, t_clr/1e6, (t_clr - t_set)/1e6);
        chk((t_clr - t_set) >= 100_000_000.0, "T2 amplifier reset held >= 100 ms");
        // ---------------- T3: record start (MODE = 1, EN = FF) ----------------
        nfs_frames = 0; nfr = 0; nbad_data = 0;
        period(16'h01ff);                      // config write; routing switches close at SCLK ~35 of this frame
        for (c = 0; c < 8; c = c + 1) chk(os_n[c] === 1, "T3 one-shot started once per channel");
        chk(dut.sw_rec === 8'hff && dut.sw_ipg === 8'h00 && dut.sw_rec_b === 8'h00, "T3 record switches closed, park OFF");
        for (c = 0; c < 8; c = c + 1) begin gap = t_fs_r[c] - t_sw_r[c]; chk(gap >= 0.0 && gap < 1.0, "T3 fs rises < 1 ns after sw_rec (one-shot trigger)"); end
        $display("T3: fs rise - sw_rec rise (ch0) = %0.3f ns", t_fs_r[0] - t_sw_r[0]);
        for (f = 0; f < 30; f = f + 1) begin period(16'h01ff); check_data(0); end
        for (c = 0; c < 8; c = c + 1) begin w = t_fs_f[c] - t_fs_r[c]; chk(w > 3.55e6 && w < 3.57e6, "T3 one-shot width (stub T_FS 3.56 ms)"); end
        $display("T3: fs pulse width ch0 %0.4f ms, ch7 %0.4f ms; %0d of %0d frames sampled during the pulse (code 0xAAA); word errors %0d", (t_fs_f[0]-t_fs_r[0])/1e6, (t_fs_f[7]-t_fs_r[7])/1e6, nfs_frames, nfr, nbad_data);
        chk(nbad_data == 0, "T3 every DOUT word = {0, ID, code}, code = 0xAAA while fs, else the input code");
        chk(nfs_frames >= 12 && nfs_frames <= 16, "T3 about 3.56 ms / 250 us = 14 frames in reset");
        chk(fs_v === 8'h00, "T3 fs low after the pulse");
        // a clean frame after the pulse: 8 ADC words with new codes
        for (c = 0; c < 8; c = c + 1) vin_all[12*c +: 12] = 4095 - 511 * c;
        nbad_data = 0;
        period(16'h01ff); check_data(1);
        chk(nbad_data == 0, "T3 8 ADC words after the reset pulse");
        for (c = 0; c < 8; c = c + 1) chk(epark[c] === 0, "T3 park gates complementary");
        // ---------------- T4: treat mode ----------------
        eval = 8'hc3; #10;
        chk(REC === 8'hc3, "T4 REC follows E (record switches closed)");
        period(16'h00ff);                      // MODE = 0
        chk(dut.sw_rec === 8'h00 && dut.sw_ipg === 8'hff && dut.sw_rec_b === 8'hff, "T4 treat: IPG closed, record open, park ON");
        chk(IPG === 8'hc3 && REC === 8'hzz, "T4 IPG follows E, REC floating (z) at the TGATE");
        for (c = 0; c < 8; c = c + 1) chk(os_n[c] === 1, "T4 no new one-shot in treat mode");
        // ---------------- T5: record again on channels 0..3 ----------------
        period(16'h010f);
        chk(dut.sw_rec === 8'h0f && dut.sw_ipg === 8'h00, "T5 record on ch0-3 only");
        for (c = 0; c < 8; c = c + 1) chk(os_n[c] === (c < 4 ? 2 : 1), "T5 one-shot fired again on ch0-3 only");
        gapmin = 1e12; gapmax = 0.0;
        for (c = 0; c < 4; c = c + 1) begin gap = t_sw_r[c] - t_swi_f[c]; if (gap < gapmin) gapmin = gap; if (gap > gapmax) gapmax = gap; end
        $display("T5: break-before-make, sw_ipg fall -> sw_rec rise (treat -> record): %0.1f .. %0.1f ns", gapmin, gapmax);
        chk(gapmin > 0.0, "T5 IPG switch opens before the record switch closes");
        // ---------------- T6: RST_AMP while recording, then RSTN ----------------
        period(16'h030f);
        chk(fs_v === 8'hff && dut.sw_rec === 8'h0f, "T6 RST_AMP set during record: fs high on all 8, routing unchanged");
        rstn = 0; #50; rstn = 1; #50;
        chk(dut.sw_rec === 8'h00 && dut.sw_ipg === 8'h00 && dut.rst_amp_o === 1'b0 && fs_v === 8'h00 && dut.sw_rec_b === 8'hff, "T6 RSTN clears RST_AMP, config and routing; park ON");
        // ---------------- summary ----------------
        chk(e_ref == 0, "REC / IPG equal the real dbs module's outputs");
        for (c = 0; c < 8; c = c + 1) chk(edac[c] === 0, "DAC stub: no crowbar / contention / samb error");
        chk(DOUT_OE_ok == 1, "DOUT_OE = ~CS at every change");
        chk(e_dout == 0, "DOUT changes only on SCLK falling edges");
        chk(d_ie === 1'b0 && cs_pu === 1'b0 && rstn_pd === 1'b0, "pad control ties");
        $display("e_ref %0d  e_dout %0d  DOUT_OE_ok %0d", e_ref, e_dout, DOUT_OE_ok);
        $display("RESULT %0s errors %0d", errs == 0 ? "PASS" : "FAIL", errs);
        $finish;
    end
endmodule
