`timescale 1ns/1ps
// tb_adc_equiv (REVIEW R14, Decision 54): conversion-phase equivalence of the legacy adc8_top (8 channels, 160-SCLK frame) and the new adc_top #(N = 4) (80-SCLK frame).
// Both get the same CS / SCLK / DIN / RSTN and, for channels 0-3, the SAME comparator responses (the ideal comparator models hang on the new block's outputs; the legacy block's
// cmp_q[3:0] are the same wires, cmp_q[7:4] = 0).  Every output of the SAR logic of channels 0-3 is compared event by event for the whole time (not only edges 1..16):
//     rst_sw  tg_on  dac_gp[47:0]  dac_gn[47:0]  dac_gdn  cmp_clk
// and must be identical: the per-channel SAR logic and the comparator-clock chain did not change.  Reports the number of compared events and of mismatches.
// Plusargs: +PER=<ns> +NF=<frames> ; run with the same -DCORNER_* as tb_adc_top.
module tb_adc_equiv;
    localparam N = 4;
    reg cs_n = 1, sclk = 0, din = 0, rstn = 0;
    // new block
    wire dout_n, oe_n, mode_n, rst_n_o;
    wire [N-1:0] en_n, cmp_clk_n, rst_sw_n, tg_on_n, gdn_n;
    wire [12*N-1:0] gp_n, gn_n;
    // legacy block
    wire dout_o, oe_o, mode_o, rst_o_o;
    wire [7:0] en_o, cmp_clk_o, rst_sw_o, tg_on_o, gdn_o;
    wire [95:0] gp_o, gn_o;
    wire [N-1:0] cmp_q;
    reg  [12*N-1:0] vin_all = 0;
    real PER = 500.0;
    integer NF = 64;

    adc_top #(.N(N)) dn (.cs_n(cs_n), .sclk(sclk), .din(din), .rstn(rstn), .dout(dout_n), .dout_oe(oe_n), .rst_amp_o(rst_n_o), .mode_o(mode_n), .en_o(en_n),
                         .cmp_q(cmp_q), .cmp_clk(cmp_clk_n), .rst_sw(rst_sw_n), .tg_on(tg_on_n), .dac_gp(gp_n), .dac_gn(gn_n), .dac_gdn(gdn_n));
    adc8_top dl (.cs_n(cs_n), .sclk(sclk), .din(din), .rstn(rstn), .dout(dout_o), .dout_oe(oe_o), .rst_amp_o(rst_o_o), .mode_o(mode_o), .en_o(en_o),
                 .cmp_q({4'b0000, cmp_q}), .cmp_clk(cmp_clk_o), .rst_sw(rst_sw_o), .tg_on(tg_on_o), .dac_gp(gp_o), .dac_gn(gn_o), .dac_gdn(gdn_o));

    wire [31:0] ecb [0:N-1], eco [0:N-1], etm [0:N-1], ech [0:N-1], eor [0:N-1], ez [0:N-1], nd [0:N-1];
    wire [11:0] vs [0:N-1];
    genvar g;
    generate for (g = 0; g < N; g = g + 1) begin : an
        ana_model m (.tg_on(tg_on_n[g]), .rst_sw(rst_sw_n[g]), .cmp_clk(cmp_clk_n[g]), .gp(gp_n[12*g +: 12]), .gn(gn_n[12*g +: 12]), .vin(vin_all[12*g +: 12]),
                     .cmp_q(cmp_q[g]), .e_crowbar(ecb[g]), .e_cont(eco[g]), .e_tmin(etm[g]), .e_chg(ech[g]), .e_order(eor[g]), .e_z(ez[g]), .vs(vs[g]), .n_dec(nd[g]));
    end endgenerate

    // compared bundle: {rst_sw, tg_on, gdn, cmp_clk, gp, gn} of channels 0-3
    wire [6*N + 24*N - 1 : 0] bn = {rst_sw_n, tg_on_n, gdn_n, cmp_clk_n, gp_n, gn_n};
    wire [6*N + 24*N - 1 : 0] bo = {rst_sw_o[N-1:0], tg_on_o[N-1:0], gdn_o[N-1:0], cmp_clk_o[N-1:0], gp_o[12*N-1:0], gn_o[12*N-1:0]};
    integer n_ev = 0, n_bad = 0, n_in16 = 0, n_cmpclk = 0;
    integer edge_k = 0;
    always @(bn or bo) begin
        #0.002;
        n_ev = n_ev + 1;
        if (!cs_n && edge_k <= 16) n_in16 = n_in16 + 1;
        if (bn !== bo) begin n_bad = n_bad + 1; if (n_bad < 20) $display("  MISMATCH t=%0t new %h old %h", $time, bn, bo); end
    end
    always @(posedge cmp_clk_n[0] or posedge cmp_clk_n[1] or posedge cmp_clk_n[2] or posedge cmp_clk_n[3]) n_cmpclk = n_cmpclk + 1;
    // the first 16 edges of a frame: count compared events there separately (statement of the item: edges 1..16)
    always @(posedge sclk) if (!cs_n) edge_k = edge_k + 1;
    always @(negedge cs_n) edge_k = 0;

    integer f, c, k;
    reg [15:0] w0;
    task frame(input integer nclk, input [15:0] cfg);
        begin
            #(PER); cs_n = 0; #100.0;
            for (k = 1; k <= nclk; k = k + 1) begin
                din = (k <= 16) ? cfg[16 - k] : $random;
                #(PER/2); sclk = 1; #(PER/2); sclk = 0;
            end
            #(PER/2); cs_n = 1;
        end
    endtask
    initial begin
        if (!$value$plusargs("PER=%f", PER)) PER = 500.0;
        if (!$value$plusargs("NF=%d", NF)) NF = 64;
        #50 rstn = 1; #50;
        for (f = 0; f < NF; f = f + 1) begin
            for (c = 0; c < N; c = c + 1) vin_all[12*c +: 12] = (f < 4) ? (f == 0 ? 12'd0 : f == 1 ? 12'd4095 : f == 2 ? 12'd2048 : 12'd2047) : $random;
            w0 = $random;
            frame((f % 5 == 4) ? 20 + (f % 60) : 80, w0);        // some aborted frames too: the SAR logic must follow its edges identically
        end
        #1000;
        $display("EQUIV events %0d (%0d within edges 1..16) comparator pulses %0d mismatches %0d  (comparator model decisions %0d %0d %0d %0d)", n_ev, n_in16, n_cmpclk, n_bad, nd[0], nd[1], nd[2], nd[3]);
        $display("RESULT %0s EQUIV adc8_top vs adc_top N=4: rst_sw tg_on dac_gp dac_gn dac_gdn cmp_clk of channels 0-3 identical (PER %0.2f)", (n_bad == 0 && n_cmpclk > 0) ? "PASS" : "FAIL", PER);
        $finish;
    end
endmodule
