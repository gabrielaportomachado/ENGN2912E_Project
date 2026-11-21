`timescale 1ns/1ps
// AUDIT step 4 testbench (2026-11-20): extension of AFE/top/tb_top.v (copied idea, original not edited) with one assertion per analog-digital ordering requirement.
// DUT = dbs_afe_top_ba (AFE/review/tb/top_ba.v: the top wrapper with STA-derived delays) + the ORIGINAL afe_ch, adc_top N = 4 (RTL, or the hardened netlist + SDF with +define+GLS), rtl/dbs.v.  R14 (Decision 54): 4 channels, the 80-SCLK frame (config word with WR, committed at edge 17; status word; 4 x {ID, 00, code}), REC pads; every item of the 8-channel testbench keeps its intent (ids unchanged except X5.after33 / X5.after33d -> X5.after17 / X5.after17d: the commit edge is 17 now).  F1 (2026-11-20): ports follow the new top (DOUT_OUT / DOUT_IN, no REC ports: REC is read from the internal nets; Decisions 44b / 45); no line added, nothing else changed.
// Plusargs: +PER=<SCLK period ns> +SCEN=main|noreset|rstlate.   Every line "ASSERT <id> PASS|FAIL | what | measured" is one assertion; SUMMARY at the end.
`include "audit_delays.vh"
module tb_audit;
    supply1 vdd_n; supply0 vss_n;
    reg cs = 1, din = 0, sclk = 0, rstn = 0;
    localparam NCH = 4;
    reg [NCH-1:0] eval = 4'ha;
    wire [NCH-1:0] E, IPG, REC;
    assign E = eval;
    wire dout, dout_oe, d_ie, d_pd, d_pu, d_cs, d_sl, d_p0, d_p1, cs_pu, cs_pd, din_pu, din_pd, sclk_pu, sclk_pd, rstn_pu, rstn_pd;
    wire refw; assign refw = 1'b1;
    dbs_afe_top_ba dut (.E(E), .IPG(IPG), .REC(REC), .REF(refw), .CS(cs), .DIN(din), .SCLK(sclk), .RSTN(rstn), .DOUT_OUT(dout), .DOUT_IN(1'b0),
                        .DOUT_OE(dout_oe), .DOUT_IE(d_ie), .DOUT_PD(d_pd), .DOUT_PU(d_pu), .DOUT_CS(d_cs), .DOUT_SL(d_sl), .DOUT_PDRV0(d_p0), .DOUT_PDRV1(d_p1),
                        .CS_PU(cs_pu), .CS_PD(cs_pd), .DIN_PU(din_pu), .DIN_PD(din_pd), .SCLK_PU(sclk_pu), .SCLK_PD(sclk_pd), .RSTN_PU(rstn_pu), .RSTN_PD(rstn_pd),
                        .VDD(vdd_n), .VSS(vss_n));
`ifdef GLS
    initial $sdf_annotate(`SDFFILE, dut.u_adc);
`endif
    real PER = 500.0;
    reg [255:0] SCEN;
    integer nass = 0, nfail = 0;
    task A(input [255:0] id, input cond, input [2047:0] what);
        begin nass = nass + 1; if (!cond) nfail = nfail + 1; $display("ASSERT %0s %0s | %0s", id, cond ? "PASS" : "FAIL", what); end
    endtask

    // ------------------------------------------------------------------ bookkeeping of the serial port
    integer ne = 0;
    real t_cs_f = 0, t_cs_r = 0, t_sr = 0, t_sf = 0;
    reg frame_clean = 1'b0;      // RSTN was high during the whole frame (a frame cut by RSTN is not a complete conversion)
    always @(negedge cs) begin t_cs_f = $realtime; ne = 0; frame_clean = (rstn === 1'b1); end
    always @(negedge rstn) frame_clean = 1'b0;
    always @(posedge cs) t_cs_r = $realtime;
    always @(posedge sclk) begin t_sr = $realtime; if (!cs) ne = ne + 1; end
    always @(negedge sclk) t_sf = $realtime;

    // ------------------------------------------------------------------ per-channel monitors (only nets at the afe_ch pins are used: valid for RTL and for the gate-level netlist)
    integer e_order[0:7], e_cont[0:7], e_tset[0:7], e_chg[0:7], e_win[0:7], e_trk[0:7], e_z[0:7], e_crow[0:7], e_gdn[0:7], e_edge[0:7], e_res[0:7], e_rel[0:7], n_ck[0:7], e_nck[0:7], e_idle[0:7];
    real m_dac2ck[0:7], m_ck2edge[0:7], m_w[0:7], m_rst2tg[0:7], x_ov[0:7], t_gp[0:7], t_ckr[0:7], t_ckf[0:7], t_rstf[0:7], t_tgr[0:7], t_c0[0:7], tacq[0:7], x_hold[0:7];
    reg [NCH-1:0] c_act = 0, pend = 0, act_d = 0, cb_act = 0;
    real t_cb0[0:7], x_cb[0:7];
    real t_swr[0:7], t_swf[0:7], t_ipr[0:7], t_ipf[0:7], t_eq[0:7], t_raw[0:7], t_raw2[0:7], t_fsr[0:7], t_fsf[0:7];
    integer e_bbm = 0, e_route_conv = 0, n_glitch = 0, n_haz = 0;
    real m_bbm = 1.0e18, x_swskew = 0.0;
    integer q;
    task clr;
        begin
            for (q = 0; q < NCH; q = q + 1) begin
                e_order[q] = 0; e_cont[q] = 0; e_tset[q] = 0; e_chg[q] = 0; e_win[q] = 0; e_trk[q] = 0; e_z[q] = 0; e_crow[q] = 0; e_gdn[q] = 0; e_edge[q] = 0; e_res[q] = 0; e_rel[q] = 0; e_nck[q] = 0; e_idle[q] = 0;
                m_dac2ck[q] = 1.0e18; m_ck2edge[q] = 1.0e18; m_w[q] = 1.0e18; m_rst2tg[q] = 1.0e18; x_ov[q] = 0.0; x_hold[q] = 0.0; x_cb[q] = 0.0;
            end
            e_bbm = 0; e_route_conv = 0; n_glitch = 0; n_haz = 0; m_bbm = 1.0e18; x_swskew = 0.0;
        end
    endtask
    initial begin
        for (q = 0; q < NCH; q = q + 1) begin n_ck[q] = 0; t_gp[q] = 0; t_ckr[q] = 0; t_ckf[q] = 0; t_rstf[q] = 0; t_tgr[q] = 0; t_c0[q] = 0; tacq[q] = 0; t_cb0[q] = 0;
            t_swr[q] = 0; t_swf[q] = 0; t_ipr[q] = 0; t_ipf[q] = 0; t_eq[q] = 0; t_raw[q] = -1; t_raw2[q] = -1; t_fsr[q] = -1; t_fsf[q] = -1; end
        clr;
    end
    function integer sum8; input integer sel; integer k; begin
        sum8 = 0;
        for (k = 0; k < NCH; k = k + 1) case (sel)
            0: sum8 = sum8 + e_order[k];  1: sum8 = sum8 + e_cont[k];  2: sum8 = sum8 + e_tset[k];  3: sum8 = sum8 + e_chg[k];  4: sum8 = sum8 + e_win[k];
            5: sum8 = sum8 + e_trk[k];    6: sum8 = sum8 + e_z[k];     7: sum8 = sum8 + e_crow[k];  8: sum8 = sum8 + e_gdn[k];  9: sum8 = sum8 + e_edge[k];
            10: sum8 = sum8 + e_res[k];   11: sum8 = sum8 + e_rel[k];  12: sum8 = sum8 + e_nck[k];  13: sum8 = sum8 + e_idle[k];
        endcase end
    endfunction
    function real min8; input integer sel; integer k; real v; begin
        min8 = 1.0e18;
        for (k = 0; k < NCH; k = k + 1) begin
            case (sel) 0: v = m_dac2ck[k]; 1: v = m_ck2edge[k]; 2: v = m_w[k]; 3: v = m_rst2tg[k]; default: v = 0; endcase
            if (v < min8) min8 = v;
        end end
    endfunction
    function real max8; input integer sel; integer k; real v; begin
        max8 = 0.0;
        for (k = 0; k < NCH; k = k + 1) begin
            case (sel) 0: v = x_ov[k]; 1: v = x_hold[k]; 2: v = x_cb[k]; default: v = 0; endcase
            if (v > max8) max8 = v;
        end end
    endfunction

    genvar g;
    generate for (g = 0; g < NCH; g = g + 1) begin : mon
        wire [11:0] gp = dut.dac_gp[12*g +: 12];
        wire [11:0] gn = dut.dac_gn[12*g +: 12];
        wire drv_any = (|(~gp)) | (|gn);
        wire tri_any = |(gp & ~gn);
        reg da;
        always @(gp or gn) begin
            da = (|(~gp)) | (|gn);
            t_gp[g] = $realtime;
            if (|(~gp & gn)) begin if (!cb_act[g]) begin e_crow[g] = e_crow[g] + 1; cb_act[g] = 1'b1; t_cb0[g] = $realtime; end end   // crowbar: PMOS and NMOS driver of one bit on together
            else if (cb_act[g]) begin if ($realtime - t_cb0[g] > x_cb[g]) x_cb[g] = $realtime - t_cb0[g]; cb_act[g] = 1'b0; end
            if (dut.cmp_clk[g] === 1'b1) e_chg[g] = e_chg[g] + 1;                                          // DAC moves while the comparator evaluates
            if (c_act[g] && !da) begin if ($realtime - t_c0[g] > x_ov[g]) x_ov[g] = $realtime - t_c0[g]; c_act[g] = 1'b0; end
            if (dut.tg_on[g] === 1'b1 && da && !c_act[g]) begin e_cont[g] = e_cont[g] + 1; c_act[g] = 1'b1; t_c0[g] = $realtime; end
            if (!da && act_d[g] && !cs && ne != 13 + g) e_rel[g] = e_rel[g] + 1;                           // drivers released at SCLK edge 13 + i
            act_d[g] = da;
        end
        always @(posedge dut.tg_on[g]) begin
            t_tgr[g] = $realtime;
            if ((|(~gp)) | (|gn)) begin e_cont[g] = e_cont[g] + 1; c_act[g] = 1'b1; t_c0[g] = $realtime; end   // sampling TG closes while a driver still holds a bottom
        end
        always @(negedge dut.rst_sw[g]) t_rstf[g] = $realtime;
        always @(posedge dut.rst_sw[g]) if (!cs && ne != 14 + g) e_res[g] = e_res[g] + 1;                 // tracking resumes at SCLK edge 14 + i
        always @(negedge dut.tg_on[g]) begin
            if (dut.rst_sw[g] !== 1'b0) e_order[g] = e_order[g] + 1;                                       // plate reset switch must open BEFORE the sampling TG / Cref TG
            if ($realtime - t_rstf[g] < m_rst2tg[g]) m_rst2tg[g] = $realtime - t_rstf[g];
            tacq[g] = $realtime - t_tgr[g];
        end
        always @(posedge dut.cmp_clk[g]) begin
            t_ckr[g] = $realtime; n_ck[g] = n_ck[g] + 1; pend[g] = 1'b1;
            if (cs) e_idle[g] = e_idle[g] + 1;                                                             // comparator clocked while idle
            if ($realtime - t_gp[g] < m_dac2ck[g]) m_dac2ck[g] = $realtime - t_gp[g];
            if ($realtime - t_gp[g] < `TSET) e_tset[g] = e_tset[g] + 1;                                    // DAC settling time before the comparator clock
            if (dut.tg_on[g] !== 1'b0 || dut.rst_sw[g] !== 1'b0 || dut.dac_gdn[g] !== 1'b1) e_trk[g] = e_trk[g] + 1;   // sampling TG, Cref TG and plate reset open, dummy grounded
            if (|(gp & ~gn)) e_z[g] = e_z[g] + 1;                                                              // a bottom plate floats during a trial
            if (ne != n_ck[g] + g) e_edge[g] = e_edge[g] + 1;                                              // trial t of ADC i belongs to SCLK edge t + i (no wrap into the next cycle)
        end
        always @(negedge dut.cmp_clk[g]) begin
            t_ckf[g] = $realtime;
            if ($realtime - t_ckr[g] < m_w[g]) m_w[g] = $realtime - t_ckr[g];
            if ($realtime - t_rstf[g] > x_hold[g]) x_hold[g] = $realtime - t_rstf[g];
        end
        always @(posedge sclk) begin
            if (dut.cmp_clk[g] === 1'b1) e_win[g] = e_win[g] + 1;                                          // window not finished at the next SCLK edge
            else if (pend[g] && ($realtime - t_ckf[g] < m_ck2edge[g])) m_ck2edge[g] = $realtime - t_ckf[g];
            pend[g] = 1'b0;
        end
        always @(negedge cs) n_ck[g] = 0;
        always @(posedge cs) if (frame_clean && ne >= 21 && n_ck[g] != 12) e_nck[g] = e_nck[g] + 1;                       // 12 comparator pulses per ADC per complete conversion
        always @(dut.dac_gdn[g] or dut.tg_on[g]) begin : cgd
            #3.0 if (dut.dac_gdn[g] !== ~dut.tg_on[g]) e_gdn[g] = e_gdn[g] + 1;
        end
        // routing
        always @(dut.sw_rec[g] or dut.sw_ipg[g]) if (dut.sw_rec[g] === 1'b1 && dut.sw_ipg[g] === 1'b1) e_bbm = e_bbm + 1;
        always @(posedge dut.sw_rec[g]) begin t_swr[g] = $realtime; if (t_ipf[g] > 0 && $realtime - t_ipf[g] < m_bbm) m_bbm = $realtime - t_ipf[g]; if (dut.rst_sw !== {NCH{1'b1}}) e_route_conv = e_route_conv + 1; end
        always @(negedge dut.sw_rec[g]) begin t_swf[g] = $realtime; if ($realtime - t_swr[g] < 0.9 * PER) n_glitch = n_glitch + 1; if (dut.rst_sw !== {NCH{1'b1}}) e_route_conv = e_route_conv + 1; end
        always @(posedge dut.sw_ipg[g]) begin t_ipr[g] = $realtime; if (t_swf[g] > 0 && $realtime - t_swf[g] < m_bbm) m_bbm = $realtime - t_swf[g]; if (dut.rst_sw !== {NCH{1'b1}}) e_route_conv = e_route_conv + 1; end
        always @(negedge dut.sw_ipg[g]) begin t_ipf[g] = $realtime; if ($realtime - t_ipr[g] < 0.9 * PER) n_glitch = n_glitch + 1; if (dut.rst_sw !== {NCH{1'b1}}) e_route_conv = e_route_conv + 1; end
        always @(dut.sw_rec[g] or dut.sw_rec_b[g]) begin
            if (dut.sw_rec[g] === dut.sw_rec_b[g]) t_eq[g] = $realtime;
            else if (t_eq[g] > 0) begin if ($realtime - t_eq[g] > x_swskew) x_swskew = $realtime - t_eq[g]; t_eq[g] = 0; end
        end
        // zero-width hazards on the undelayed RTL nets (two events in one time step)
        always @(dut.sw_rec_r[g]) begin if ($realtime == t_raw[g] && $realtime > 1.0) n_haz = n_haz + 1; t_raw[g] = $realtime; end
        always @(dut.sw_ipg_r[g]) begin if ($realtime == t_raw2[g] && $realtime > 1.0) n_haz = n_haz + 1; t_raw2[g] = $realtime; end
        always @(posedge dut.ch[g].u.fs) t_fsr[g] = $realtime;
        always @(negedge dut.ch[g].u.fs) t_fsf[g] = $realtime;
    end endgenerate

    // simultaneous sampling: spread of the rst_sw falling edges after CS falls
    real x_skew = 0.0, m_cs2rst = 1.0e18, x_cs2rst = 0.0;
    always @(negedge cs) begin : samp
        integer k; real lo, hi;
        #60.0;
        if (rstn === 1'b1) begin
            lo = 1.0e18; hi = 0.0;
            for (k = 0; k < NCH; k = k + 1) begin if (t_rstf[k] - t_cs_f < lo) lo = t_rstf[k] - t_cs_f; if (t_rstf[k] - t_cs_f > hi) hi = t_rstf[k] - t_cs_f; end
            if (lo >= 0) begin if (hi - lo > x_skew) x_skew = hi - lo; if (lo < m_cs2rst) m_cs2rst = lo; if (hi > x_cs2rst) x_cs2rst = hi; end
        end
    end
    // DOUT
    integer e_dout = 0, e_oe = 0, e_dout_idle = 0;
    real x_dout = 0.0, m_dsu = 1.0e18, t_dch = 0.0;
    always @(dout) if (!cs && rstn === 1'b1) begin
        t_dch = $realtime;
        if (sclk) e_dout = e_dout + 1;
        else if (t_sf > t_cs_f && $realtime - t_sf > x_dout) x_dout = $realtime - t_sf;
    end
    always @(posedge sclk) if (!cs && t_dch > t_cs_f && $realtime - t_dch < m_dsu) m_dsu = $realtime - t_dch;
    always @(cs or dout_oe) #1 if (dout_oe !== ~cs) e_oe = e_oe + 1;
    always @(posedge cs) #20 if (dout !== 1'b1) e_dout_idle = e_dout_idle + 1;     // R14: DOUT is preset to 1 (the first sync bit) while CS is high; the pad is tri-state then

    // ------------------------------------------------------------------ SPI master
    reg [12*NCH-1:0] vin_all = 0;
    generate for (g = 0; g < NCH; g = g + 1) begin : drvvin
        always @(vin_all[12*g +: 12]) dut.ch[g].u.u_amp.sim_vin = vin_all[12*g +: 12];
    end endgenerate
    wire [NCH-1:0] fs_v;
    generate for (g = 0; g < NCH; g = g + 1) begin : fsv assign fs_v[g] = dut.ch[g].u.fs; end endgenerate   // REC[3:0] are top ports again (Decision 53)
    reg [79:0] rx;
    reg [NCH-1:0] fs_at_cs;
    reg [5:0] pre_cfg;
    reg din_rand = 1'b1;       // DIN after word 0: 1 = random data (stress, as tb_top.v), 0 = idle low (typical host)
    reg din_ones = 1'b0;       // 1 = all ones after word 0 (overrides din_rand): a restarted frame then decodes WR = 1 and a non-zero config (deterministic X5 hazard)
    // nclk SCLK cycles; after rising edge `stop_after` SCLK pauses (low) for pause_ns; CS falls cs_lead before the first rising edge and rises half a period after the last falling edge
    task frame(input integer nclk, input [15:0] w0, input integer stop_after, input real pause_ns);
        integer k;
        begin
            rx = 0;
            fs_at_cs = fs_v; pre_cfg = {dut.rst_amp_o, dut.mode_o, dut.en_o};
            cs = 0; #100.0;
            for (k = 1; k <= nclk; k = k + 1) begin
                din = (k <= 16) ? w0[16 - k] : (din_ones ? 1'b1 : din_rand ? $random : 1'b0);
                #(PER/2); sclk = 1;
                if (k <= 80) rx[80 - k] = dout;
                #(PER/2); sclk = 0;
                if (k == stop_after) #(pause_ns);
            end
            #(PER/2); cs = 1; #(PER);
        end
    endtask
    task period(input [15:0] w0);
        real t0;
        begin t0 = $realtime; frame(80, w0, 0, 0.0); #(250000.0 - ($realtime - t0)); end
    endtask
    function [15:0] word(input integer w); word = rx[79 - 16*w -: 16]; endfunction
    integer nbad = 0;
    task check_data;       // word 0 = status {1010, held config of before the frame, 0}; words 1..4 = {ID[1:0], 00, code}; code = 0xAAA if the amplifier stub was in reset at CS falling, else the input code
        integer c; reg [11:0] ex; reg [15:0] wd;
        begin
            for (c = 0; c < NCH; c = c + 1) begin
                ex = fs_at_cs[c] ? 12'hAAA : vin_all[12*c +: 12];
                wd = word(1 + c);
                if (wd !== {c[1:0], 2'b00, ex}) begin nbad = nbad + 1; if (nbad < 6) $display("   data error ch %0d: got %h expected %h (t = %0t)", c, wd, {c[1:0], 2'b00, ex}, $time); end
            end
            if (word(0) !== {4'b1010, pre_cfg, 6'd0}) begin nbad = nbad + 1; if (nbad < 6) $display("   status word error: %h expected %h", word(0), {4'b1010, pre_cfg, 6'd0}); end
        end
    endtask
    task rnd_codes; integer c; begin for (c = 0; c < NCH; c = c + 1) vin_all[12*c +: 12] = $random; end endtask

    // standing assertions evaluated after a scenario
    task rep(input [511:0] tag, input integer conv);
        begin
            $display("--- %0s (SCLK %0.3f MHz) ---", tag, 1000.0/PER);
            if (conv) begin
                A("S1.order", sum8(0) == 0, "plate reset switch (rst_sw) opens before the sampling TG / Cref TG (tg_on) at every sample");
                $display("        rst_sw -> tg_on min %0.2f ns; CS fall -> rst_sw %0.2f .. %0.2f ns; spread over the channels %0.3f ns", min8(3), m_cs2rst, x_cs2rst, x_skew);
                A("S2.simult", x_skew < 1.0, "all channels sample within 1 ns of each other (simultaneous sampling, Decision 34)");
                A("S3.gdn", sum8(8) == 0, "dummy-unit driver gate dac_gdn = ~tg_on (within 3 ns)");
                A("T1.edge", sum8(9) == 0, "trial t of ADC i is evaluated between SCLK edges t+i and t+i+1 (no wrap into the next cycle)");
                A("T2.settle", sum8(2) == 0, "DAC edge -> comparator clock >= the analog settling time TSET of this corner");
                $display("        DAC edge -> comparator clock: min %0.2f ns (TSET %0.1f ns)", min8(0), `TSET);
                A("T3.stable", sum8(3) == 0, "no DAC driver edge while a comparator evaluates");
                A("T4.window", sum8(4) == 0, "every comparator window ends before the next SCLK rising edge");
                $display("        window end -> next SCLK edge: min %0.2f ns; window width min %0.2f ns (comparator decision TDEC %0.2f ns)", min8(1), min8(2), `TDEC);
                A("T5.width", min8(2) >= `TDEC, "comparator window >= decision time of this corner");
                A("T6.open", sum8(5) == 0, "sampling TG, Cref TG and plate reset open and dummy grounded at every comparator clock");
                A("T7.driven", sum8(6) == 0, "all 12 bottoms driven (none tri-state) at every comparator clock");
                A("T8.count", sum8(12) == 0, "exactly 12 comparator pulses per ADC in every complete frame");
                A("T9.release", sum8(11) == 0, "DAC drivers released at SCLK edge 13+i");
                A("T10.resume", sum8(10) == 0, "tracking resumes at SCLK edge 14+i");
                A("T11.crowbar", sum8(7) == 0, "no crowbar (gp low and gn high on one bit) at the driver gates");
                if (sum8(7) != 0) $display("        crowbar overlaps (PMOS and NMOS gate of one bit both on): %0d events, longest %0.3f ns", sum8(7), max8(2));
                A("T12.contention", sum8(1) == 0, "sampling TG never on while a bottom-plate driver is on");
                if (sum8(1) != 0) $display("        driver / TG overlap: %0d events, longest %0.2f ns", sum8(1), max8(0));
                A("T13.idleclk", sum8(13) == 0, "no comparator clock while CS is high");
            end
            A("R1.bbm", e_bbm == 0, "record and IPG switch of a channel never on together");
            A("R2.conv", e_route_conv == 0, "no routing-switch edge while any ADC is converting");
            A("R3.glitch", n_glitch == 0 && n_haz == 0, "no pulse shorter than one SCLK period on sw_rec / sw_ipg (one-shot trigger), no zero-width hazard on the RTL nets");
            if (n_glitch != 0 || n_haz != 0) $display("        glitches at the pins %0d, zero-width hazards on the RTL nets %0d", n_glitch, n_haz);
            A("D1.edge", e_dout == 0, "DOUT changes only while SCLK is low (after the falling edge)");
            A("D2.oe", e_oe == 0 && e_dout_idle == 0, "DOUT_OE = ~CS, DOUT = 0 while CS is high");
            if (m_dsu < 1.0e17) $display("        DOUT: latest change %0.2f ns after the SCLK falling edge; setup to the host sampling edge min %0.2f ns", x_dout, m_dsu);
            if (m_bbm < 1.0e17) $display("        break-before-make gap min %0.1f ns; sw_rec / sw_rec_b overlap max %0.2f ns", m_bbm, x_swskew);
            clr; e_dout = 0; e_oe = 0; e_dout_idle = 0; x_dout = 0.0; m_dsu = 1.0e18; x_skew = 0.0; m_cs2rst = 1.0e18; x_cs2rst = 0.0;
        end
    endtask

    integer c, f, k;
    real w, gap, t0;
    reg known;
    initial begin
        if (!$value$plusargs("PER=%f", PER)) PER = 500.0;
        if (!$value$plusargs("SCEN=%s", SCEN)) SCEN = "main";
        for (c = 0; c < NCH; c = c + 1) vin_all[12*c +: 12] = 100 + 37 * c;
        if (SCEN == "noreset") begin
            // ---------------- P3: RSTN never low (host forgot / pad pull-down missing): which outputs are unknown, and when does the chip become defined?
            rstn = 1; #1000; clr;
            $display("--- P3 power-up WITHOUT a reset pulse (RSTN = 1 from t = 0) ---");
            A("P3.x_before", (^dut.sw_rec === 1'bx) || (^dut.sw_ipg === 1'bx) || (dut.rst_amp_o === 1'bx), "without RSTN the routing switches / RST_AMP are UNDEFINED after power-up (expected: this is why RSTN must be held low, Decision 41e)");
            $display("        sw_rec %b sw_ipg %b rst_amp %b mode %b en %b", dut.sw_rec, dut.sw_ipg, dut.rst_amp_o, dut.mode_o, dut.en_o);
            period(16'h8000);
            $display("        after one full frame (config 0): sw_rec %b sw_ipg %b rst_amp %b mode %b en %b", dut.sw_rec, dut.sw_ipg, dut.rst_amp_o, dut.mode_o, dut.en_o);
            period(16'h8000);
            known = (^{dut.sw_rec, dut.sw_ipg, dut.rst_amp_o, dut.mode_o, dut.en_o} !== 1'bx);
            A("P3.selfinit", known && dut.sw_rec === 4'h0 && dut.sw_ipg === 4'h0 && dut.rst_amp_o === 1'b0, "two full frames with config 0 (WR = 1) bring the chip to the defined all-open state even without RSTN");
            rnd_codes; nbad = 0; period(16'h8000); check_data; period(16'h8000); check_data;
            A("P3.data", nbad == 0, "conversions are correct after the self-initialisation");
        end else if (SCEN == "rstlate") begin
            // ---------------- P2: the host already clocks frames while RSTN is still low; RSTN is released in the middle of a frame
            rstn = 0; #200; clr;
            $display("--- P2 power-up with SCLK / CS frames running BEFORE RSTN is released ---");
            period(16'hA00F); period(16'hE00F);
            A("P2.held", dut.sw_rec === 4'h0 && dut.sw_ipg === 4'h0 && dut.rst_amp_o === 1'b0 && dut.sw_rec_b === 4'hf && fs_v === 4'h0, "while RSTN is low, frames (even config 0xE00F: WR, RST_AMP, MODE, EN) change nothing: switches open, park ON, no amplifier reset");
            A("P2.quiet", dut.dac_gp === {(12*NCH){1'b1}} && dut.dac_gn === {(12*NCH){1'b0}}, "DAC drivers stay tri-state in reset");
            // release RSTN between two frames (CS high) while the host keeps sending frames
            #(20000.0); rstn = 1; #(20000.0);
            A("P2.release", dut.sw_rec === 4'h0 && dut.sw_ipg === 4'h0 && dut.rst_amp_o === 1'b0, "RSTN released while CS is high: nothing moves until the next frame");
            rnd_codes; nbad = 0;
            period(16'hA00F);
            A("P2.next", dut.sw_rec === 4'hf && dut.mode_o === 1'b1, "the next complete frame configures the chip normally");
            for (f = 0; f < 20; f = f + 1) period(16'hA00F);     // one-shot pulse (3.56 ms stub) passes
            nbad = 0; rnd_codes; period(16'hA00F); check_data; rnd_codes; period(16'hA00F); check_data;
            A("P2.data", nbad == 0, "conversions correct after the late reset release");
            rep("P2 standing assertions", 1);
        end else begin
            // ---------------- P1: normal power-up: RSTN low (pad pull-down) from t = 0, released before SCLK starts
            rstn = 0; #200; clr;
            $display("--- P1 power-up, RSTN low then released before the first SCLK ---");
            A("P1.reset", dut.sw_rec === 4'h0 && dut.sw_ipg === 4'h0 && dut.sw_rec_b === 4'hf && dut.rst_amp_o === 1'b0 && fs_v === 4'h0, "in reset: all routing switches open, park ON, no amplifier reset");
            A("P1.pads", dout_oe === 1'b0 && dout === 1'b1 && rstn_pd === 1'b1 && rstn_pu === 1'b0 && d_ie === 1'b0, "DOUT not driven (pad tri-state) while CS is high, preset to the first sync bit; RSTN pull-down tie = 1");
            rstn = 1; #200;
            A("P1.released", dut.sw_rec === 4'h0 && dut.sw_ipg === 4'h0 && dut.rst_amp_o === 1'b0, "after the release nothing moves until the first frame");
            // first frame after reset: conversions are valid at once (digital side)
            nbad = 0; period(16'h8000); check_data;
            A("P1.first", nbad == 0, "first frame after reset returns the 4 codes and the status word A000");
            A("P1.treat0", dut.sw_ipg === 4'h0 && dut.sw_rec === 4'h0, "MODE = 0 with EN = 0: FSM in treat state but no switch closes");
            // ---------------- C1: RST_AMP level
            $display("--- C1 RST_AMP set, held with no clock, cleared ---");
            period(16'hC000);
            A("C1.set", dut.rst_amp_o === 1'b1 && fs_v === 4'hf && dut.sw_rec === 4'h0, "RST_AMP = 1 (WR = 1) -> fs high on all 4 channels, routing untouched");
            t0 = t_fsr[0];
            #100_000_000.0;
            A("C1.hold", fs_v === 4'hf, "fs still high after 100 ms without any clock (level held in the hold register)");
            period(16'h8000);
            A("C1.clear", dut.rst_amp_o === 1'b0 && fs_v === 4'h0 && (t_fsf[0] - t0) >= 100_000_000.0, "RST_AMP cleared by the next config frame; reset lasted >= 100 ms");
            rep("C1 standing assertions", 1);
            // ---------------- F1: record start and frames (the main record-mode check)
            $display("--- F1 record start (MODE = 1, EN = F), one-shot, 40 frames at the 250 us period ---");
            nbad = 0;
            period(16'hA00F);
            A("F1.commit", dut.sw_rec === 4'hf && dut.sw_rec_b === 4'h0 && dut.sw_ipg === 4'h0, "record switches closed, park OFF after the config frame");
            gap = t_fsr[0] - t_swr[0];
            A("F1.trig", gap >= 0.0 && gap < 2.0, "one-shot: fs rises within 2 ns after sw_rec");
            $display("        sw_rec rises %0.2f ns after SCLK edge 19; fs - sw_rec = %0.2f ns", t_swr[0] - (t_cs_f + 100.0 + 18.5*PER), gap);
            for (f = 0; f < 20; f = f + 1) begin period(16'hA00F); check_data; end
            A("F1.pulse", fs_v === 4'h0 && (t_fsf[0] - t_fsr[0]) > 3.55e6 && (t_fsf[0] - t_fsr[0]) < 3.57e6, "one-shot pulse ends (stub 3.56 ms): ~14 frames carry the reset code");
            for (f = 0; f < 20; f = f + 1) begin rnd_codes; if (f == 0) vin_all = {NCH{12'hfff}}; if (f == 1) vin_all = {12*NCH{1'b0}}; if (f == 2) vin_all = {NCH{12'h800}}; if (f == 3) vin_all = {NCH{12'h7ff}}; period(16'hA00F); check_data; end
            A("F1.data", nbad == 0, "every DOUT word of 41 frames correct (ID, code, status word)");
            $display("        T_ACQ (sampling TG closed before the next sample) ADC0 %0.3f us, ADC3 %0.3f us; plate hold time (sample -> last decision) ADC3 %0.3f us", tacq[0]/1000.0, tacq[NCH-1]/1000.0, x_hold[NCH-1]/1000.0);
            A("F1.tacq", tacq[NCH-1] >= 220000.0, "T_ACQ >= 220 us for the last ADC at the 250 us frame period");
            rep("F1 standing assertions", 1);
            // ---------------- M1: mode switches: record -> treat -> record, with the 2-cycle enable latency
            $display("--- M1 record -> treat -> record on 2 channels -> hazard case (EN bit falls in the frame that changes MODE) ---");
            eval = 4'h3; #10;
            A("M1.rec", REC === 4'h3, "REC follows E in record mode");
            period(16'h800F);
            A("M1.treat", dut.sw_rec === 4'h0 && dut.sw_ipg === 4'hf && dut.sw_rec_b === 4'hf && IPG === 4'h3 && REC === 4'hz, "treat: IPG switches closed, record open, park ON, REC floating at the TGATE model");
            gap = t_ipr[0] - t_swf[0];
            A("M1.bbm1", gap > 0.9*PER && gap < 1.1*PER, "record -> treat: sw_rec falls one SCLK period before sw_ipg rises (break before make)");
            $display("        record -> treat: sw_rec fall at edge 18, sw_ipg rise %0.1f ns later", gap);
            period(16'hA003);
            A("M1.rec4", dut.sw_rec === 4'h3 && dut.sw_ipg === 4'h0, "record on channels 0-1 only");
            gap = t_swr[0] - t_ipf[0];
            A("M1.bbm2", gap > 0.9*PER && gap < 1.1*PER, "treat -> record: sw_ipg falls one SCLK period before sw_rec rises");
            A("M1.os4", dut.ch[0].u.u_os.n_pulses == 2 && dut.ch[3].u.u_os.n_pulses == 1, "one-shot fired again on the newly closed channels only");
            rep("M1 standing assertions", 1);
            // hazard: treat on ch 0-1, then ONE config word that selects record on ch 2-3: rec_en rises and en_reg_2[1:0] falls on the same SCLK edge (19)
            period(16'h8003);
            for (f = 0; f < 3; f = f + 1) period(16'h8003);
            period(16'hA00C);
            A("M1.haz_state", dut.sw_rec === 4'hc && dut.sw_ipg === 4'h0, "treat(0x3) -> record(0xC) in one config word ends in the right state");
            A("M1.haz_os", dut.ch[0].u.u_os.n_pulses == 2, "no spurious one-shot on a channel whose EN falls while MODE rises");
            rep("M1 hazard case standing assertions", 0);
            period(16'h8003);     // record(0xC) -> treat(0x3): treat_en rises while en_reg_2[3:2] falls
            A("M1.haz2_state", dut.sw_rec === 4'h0 && dut.sw_ipg === 4'h3, "record(0xC) -> treat(0x3) in one config word ends in the right state");
            rep("M1 hazard case 2 standing assertions", 0);
            // ---------------- M2: a config frame of 17 clocks (the shortest that commits): the commit happens, the routing waits for the NEXT frame's first edges (= during its conversions)
            $display("--- M2 short config frame (17 clocks): routing completes in the next frame ---");
            period(16'h8000); for (f = 0; f < 2; f = f + 1) period(16'h8000);
            rep("M2 setup", 0);
            frame(17, 16'hA00F, 0, 0.0); #(250000.0 - 17*PER - 100.0 - 1.5*PER);
            A("M2.commit", dut.mode_o === 1'b1 && dut.en_o === 4'hf && dut.sw_rec === 4'h0, "17-clock frame commits the config but the routing has not moved (dbs FSM has no clock)");
            nbad = 0; rnd_codes; period(16'hA00F); check_data;
            A("M2.next", dut.sw_rec === 4'hf && nbad == 0, "the next frame finishes the mode change (at its SCLK edges 1-2) and its 4 codes are still correct");
            A("M2.note", e_route_conv != 0, "OBSERVATION (expected): in that case the routing switches toggle WHILE the ADCs convert (I0 mismatch 11): the only path to a routing edge near a decision");
            $display("        routing edges during conversions: %0d", e_route_conv);
            for (f = 0; f < 16; f = f + 1) period(16'hA00F);
            clr;
            // ---------------- X1: CS raised early
            $display("--- X1 CS raised early (after 5, 13, 16, 20 clocks), then a clean frame ---");
            nbad = 0;
            frame(5, 16'hA00F, 0, 0.0);  #2000; A("X1.a5", dut.rst_sw === {NCH{1'b1}} && dut.tg_on === {NCH{1'b1}} && dut.dac_gp === {(12*NCH){1'b1}} && dut.dac_gn === {(12*NCH){1'b0}}, "abort after 5 clocks: drivers tri-state, tracking back");
            frame(13, 16'hA00F, 0, 0.0); #2000; A("X1.a13", dut.rst_sw === {NCH{1'b1}} && dut.tg_on === {NCH{1'b1}} && dut.dac_gp === {(12*NCH){1'b1}} && dut.dac_gn === {(12*NCH){1'b0}}, "abort after 13 clocks: drivers tri-state, tracking back");
            frame(16, 16'h8000, 0, 0.0); #2000; A("X1.a16", dut.rst_sw === {NCH{1'b1}} && dut.tg_on === {NCH{1'b1}} && dut.dac_gp === {(12*NCH){1'b1}} && dut.dac_gn === {(12*NCH){1'b0}} && dut.mode_o === 1'b1 && dut.en_o === 4'hf, "abort after 16 clocks: drivers tri-state, tracking back; the config (WR = 1, 0x000) was NOT committed (needs edge 17)");
            frame(20, 16'h8000, 0, 0.0); #2000; A("X1.a20", dut.rst_sw === {NCH{1'b1}} && dut.tg_on === {NCH{1'b1}} && dut.dac_gp === {(12*NCH){1'b1}} && dut.dac_gn === {(12*NCH){1'b0}} && dut.mode_o === 1'b0 && dut.en_o === 4'h0, "abort after 20 clocks: drivers tri-state; config (WR = 1, 0x000) WAS committed at edge 17 (a short frame can change the routing)");
            $display("        driver / sampling-TG overlap on the aborted frames: %0d events, longest %0.2f ns (0 in a complete frame)", sum8(1), max8(0));
            A("X1.contention", sum8(1) == 0, "EXPECTED FAIL with real delays: on an aborted frame the sampling TG closes before the drivers release (the adc_top comment says it cannot)");
            #200000;
            clr;
            rnd_codes; period(16'hA00F); for (f = 0; f < 16; f = f + 1) period(16'hA00F);
            nbad = 0; rnd_codes; period(16'hA00F); check_data;
            A("X1.recover", nbad == 0, "clean frame after the aborted ones");
            rep("X1 standing assertions (clean frame)", 1);
            // ---------------- X2: SCLK stops in mid-conversion for 1 ms, CS stays low
            $display("--- X2 SCLK stops after edge 6 for 1 ms (CS low), then continues ---");
            nbad = 0; rnd_codes;
            t0 = $realtime; frame(80, 16'hA00F, 6, 1_000_000.0); check_data; #(250000.0);
            A("X2.digital", nbad == 0, "digital sequence survives the pause: all 4 codes correct in the model (the analog hold is NOT modelled)");
            $display("        plate hold time in that frame: ADC0 %0.1f us, ADC3 %0.1f us (normal: %0.1f us): a floating 3.49 pF plate droops 0.29 mV/ms per pA of leakage (ESTIMATE)", x_hold[0]/1000.0, x_hold[NCH-1]/1000.0, (20.0*PER + 100.0)/1000.0);
            rep("X2 standing assertions", 1);
            // ---------------- X3: SCLK toggles while CS is high (shared SPI bus)
            $display("--- X3 100 SCLK cycles while CS is high ---");
            din = 1;
            for (f = 0; f < 100; f = f + 1) begin #(PER/2) sclk = 1; #(PER/2) sclk = 0; end
            din = 0; #100;
            A("X3.quiet", dut.rst_sw === {NCH{1'b1}} && dut.tg_on === {NCH{1'b1}} && dut.dac_gp === {(12*NCH){1'b1}} && dut.dac_gn === {(12*NCH){1'b0}} && dut.sw_rec === 4'hf && dut.mode_o === 1'b1, "analog controls, config and routing unchanged");
            A("X3.noclk", sum8(13) == 0, "no comparator clock while CS is high (the delay chain itself toggles: power only)");
            nbad = 0; rnd_codes; period(16'hA00F); check_data;
            A("X3.next", nbad == 0 && dut.mode_o === 1'b1 && dut.en_o === 4'hf, "next frame correct (DIN shifted into the config shift register while CS was high is overwritten by word 0)");
            rep("X3 standing assertions", 1);
            // ---------------- X4: back-to-back frames (CS high for 1.5 SCLK periods): fastest possible sample rate
            $display("--- X4 back-to-back frames ---");
            nbad = 0;
            for (f = 0; f < 6; f = f + 1) begin rnd_codes; frame(80, 16'hA00F, 0, 0.0); check_data; end
            A("X4.data", nbad == 0, "6 back-to-back frames correct");
            $display("        frame period %0.2f us = %0.1f kS/s per channel; T_ACQ ADC0 %0.2f us, ADC3 %0.2f us", (80.0*PER + 100.0 + 1.5*PER)/1000.0, 1.0e6/(80.0*PER + 100.0 + 1.5*PER), tacq[0]/1000.0, tacq[NCH-1]/1000.0);
            rep("X4 standing assertions", 1);
            // ---------------- X5: RSTN pulse in mid-frame: (a) after the commit edge 17 with DIN idle low, (a2) same with ones on DIN, (b) during config word 0
            $display("--- X5 RSTN pulse in the middle of a frame ---");
            din_rand = 1'b0;
            fork
                frame(80, 16'hA00F, 0, 0.0);
                begin #(100.0 + 20.3*PER); rstn = 0; #(2*PER); rstn = 1; end
            join
            #2000;
            A("X5.after17", dut.sw_rec === 4'h0 && dut.sw_ipg === 4'h0 && dut.rst_amp_o === 1'b0 && dut.sw_rec_b === 4'hf && dut.en_o === 4'h0, "RSTN pulse after edge 17, DIN idle low: config and routing cleared and stay cleared; park ON");
            #250000; clr;
            din_ones = 1'b1;
            fork
                frame(80, 16'hA00F, 0, 0.0);
                begin #(100.0 + 20.3*PER); rstn = 0; #(2*PER); rstn = 1; end
            join
            #2000;
            A("X5.after17d", dut.sw_rec === 4'h0 && dut.sw_ipg === 4'h0 && dut.rst_amp_o === 1'b0 && dut.en_o === 4'h0, "RSTN pulse after edge 17 with ONES on DIN during the rest of the frame: config must stay cleared");
            $display("        the frame counter restarts at the RSTN release (frame_rn = rstn & ~cs_n): the rest of the frame is decoded as a new frame (word 0 = DIN ones: WR = 1); committed: rst_amp %b mode %b en %b", dut.rst_amp_o, dut.mode_o, dut.en_o);
            #250000; clr;
            fork
                frame(80, 16'hFFFF, 0, 0.0);
                begin #(100.0 + 7.3*PER); rstn = 0; #(2*PER); rstn = 1; end
            join
            #2000;
            A("X5.word0", dut.en_o === 4'h0 && dut.mode_o === 1'b0 && dut.sw_ipg === 4'h0 && dut.sw_rec === 4'h0, "RSTN pulse during config word 0 (edges 8-9): the SAME frame must not commit a partial config word");
            $display("        committed by that frame: rst_amp %b mode %b en %b (host sent 0xFFFF = WR, RST_AMP, record, all channels) -> sw_rec %b sw_ipg %b", dut.rst_amp_o, dut.mode_o, dut.en_o, dut.sw_rec, dut.sw_ipg);
            din_ones = 1'b0; din_rand = 1'b1;
            #250000; clr;
            nbad = 0; rnd_codes; period(16'h8000); check_data;
            A("X5.next", nbad == 0 && dut.sw_ipg === 4'h0 && dut.sw_rec === 4'h0, "the next complete frame restores the intended config and converts correctly");
        end
        $display("SUMMARY %0s PER %0.2f ns: %0d assertions, %0d FAIL", SCEN, PER, nass, nfail);
        $finish;
    end
endmodule
