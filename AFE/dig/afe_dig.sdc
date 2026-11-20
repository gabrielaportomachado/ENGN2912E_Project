# afe_dig constraints (LP step 5 / L1d).  From AFE/adc/lg/adc8.sdc (D3) with the macro pin names; period = CLOCK_PERIOD of the config (500 ns = 2 MHz nominal;
# the 3 MHz numbers are reported separately by AFE/review/scripts/sta_audit.py).
if { ![info exists ::env(AFE_DIG_CS_RST_MAX)] } { set ::env(AFE_DIG_CS_RST_MAX) 2.6 }   ;# ns, CS pin -> rst_sw[i] pin at the slowest corner (ss 125 C 3.0 V), see below
create_clock -name sclk -period $::env(CLOCK_PERIOD) [get_ports SCLK]
set_clock_uncertainty 0.5 [get_clocks sclk]
# The clock is NOT ideal: it goes through the one clock buffer ck.u_ckbuf (Decision 44h) or through a tree; the comparator delay chain is in the clock network on purpose.
set_propagated_clock [get_clocks sclk]
# Inputs come from 5 V pad cells run at 3.3 V + up to about 1.5 mm of top-level wire: 1 ns transition (ESTIMATE; the pad Y timing at 3.3 V is not characterised).
set_input_transition 1.0 [get_ports {CS SCLK DIN RSTN}]
set_input_transition 1.0 [get_ports {cmp_q[*]}]
# Host side, relative to SCLK (SPI mode 0: DIN changes on the falling edge: setup to rising = T/2; CS and RSTN are asynchronous frame / reset signals)
set_input_delay [expr 0.5 * $::env(CLOCK_PERIOD)] -clock sclk [get_ports {DIN}]
set_input_delay [expr 0.25 * $::env(CLOCK_PERIOD)] -clock sclk [get_ports {CS}]
set_false_path -from [get_ports {RSTN}]
set_output_delay [expr 0.3 * $::env(CLOCK_PERIOD)] -clock sclk [get_ports {DOUT}]
# comparator outputs: launched by the delayed comparator clock itself, captured by tapw of the same ADC: not a path against SCLK (decision time <= window W: sta_audit / tb_audit)
set_false_path -from [get_ports {cmp_q[*]}]
# analog-side controls, routing switches, RST_AMP level and the pad-control constants: no digital capture.  Their arrival times are REPORTED (sta_audit.py), not constrained.
set_false_path -to [get_ports {cmp_clk[*] tg_on[*] dac_gp[*] dac_gn[*] dac_gdn[*] sw_rec[*] sw_rec_b[*] sw_ipg[*] sw_ipg_b[*] rst_amp_o DOUT_OE}]
# SAMPLING INSTANT: CS falling opens the plate reset switch of all 8 ADCs (rst_sw[i] = cs_n | done[i]): the 8 paths must be equal (audit assertion S2: within 1 ns; the D3 macro had
# 0.18 ns).  Synthesis maps two of the eight differently (shared inverter + NAND2) and the placer leaves one of them 270 um from its loads: 1.7 ns of spread at ss 125 C without this.
# INSIDE OPENROAD (place and route) the eight paths get a max delay that the slowest corner cannot quite meet (AFE_DIG_CS_RST_MAX = 2.6 ns after the CS edge, + the 0.25 * period
# input delay of CS, which is part of the path): pressure for the repair steps, which then size all eight alike (0.22 / 0.31 / 0.56 ns of spread at ff_n40 / tt / ss_125, LP trial).
# IN OPENSTA (sign-off STA of the flow, sta_audit.py) the ports are a false path like the other analog controls: the requirement is the SPREAD, reported by sta_audit.py section 3 and
# asserted by the gate-level testbench (S2), not this number.  (`set_cts_config` exists only inside OpenROAD: it tells the two tools apart.)
if { [llength [info commands set_cts_config]] } {
    set_max_delay [expr 0.25 * $::env(CLOCK_PERIOD) + $::env(AFE_DIG_CS_RST_MAX)] -from [get_ports {CS}] -to [get_ports {rst_sw[*]}]
} else {
    set_false_path -to [get_ports {rst_sw[*]}]
}
set_false_path -to [get_ports {DOUT_IE DOUT_PD DOUT_PU DOUT_CS DOUT_SL DOUT_PDRV0 DOUT_PDRV1 CS_PU CS_PD DIN_PU DIN_PD SCLK_PU SCLK_PD RSTN_PU RSTN_PD}]
# Output loads (ESTIMATE, pF; replace by the extracted top-level wires in L3b): DAC driver gates and comparator / switch controls = up to about 250 um of wire + the gates;
# routing-switch controls run the length of a channel (about 400 um); DOUT goes to the pad through the pin ring.
set_load 0.05 [get_ports {cmp_clk[*] rst_sw[*] tg_on[*] dac_gp[*] dac_gn[*] dac_gdn[*]}]
set_load 0.10 [get_ports {sw_rec[*] sw_rec_b[*] sw_ipg[*] sw_ipg_b[*] rst_amp_o}]
set_load 0.30 [get_ports {DOUT DOUT_OE}]
# (the 15 pad-control constants are static: no load is set on them)
# Design rules: NO set_max_transition / set_max_capacitance / set_max_fanout here.  The liberty limits apply (max_transition 5.2 / 8.6 / 15.6 ns at ff_n40 / tt / ss_125 for the
# 3.3 V corners) and the repair steps keep a percentage margin to them at every corner (config: DESIGN_REPAIR_MAX_SLEW_PCT / _CAP_PCT, GRT_DESIGN_REPAIR_*), which scales with the corner.
# Tried and rejected: the PDK's 5 V defaults (3 ns, 0.2 pF, fanout 10) as flat limits: 295 slew "violations" at ss 125 C 3.0 V, 383 buffers, +24 % cell area and a congested Metal3.
# Clock tree synthesis (only used by `mk_dig_cfg.py --clock cts`; the default flow has no CTS): the comparator delay chain is a deliberate part of the clock network (the capture
# flops are clocked by its taps).  Left alone, TritonCTS builds a sub-tree on every tap net and then "balances latency" with hundreds of delay buffers, which is what fails in
# detailed placement (DPL-0036, D3 and LP).  The chain nets are therefore excluded from CTS.  (set_cts_config exists only inside OpenROAD, not in OpenSTA.)
if { [llength [info commands set_cts_config]] } {
    set_cts_config -skip_nets {u_adc.ckg.* u_adc.ch[*].u.cap_clk}
    # ... and TritonCTS must not "balance latency" (CTS-0033): OpenSTA still sees the capture flops 25-310 ns behind the other flops (through the skipped chain) and the balancer
    # answers with about 300 delay buffers.  LibreLane's cts.tcl has no switch for `clock_tree_synthesis -no_insertion_delay`, and that command sets the option back to true on
    # every call, so the setter is pinned to false here (OpenROAD 26Q2).  If this proc does not exist in another OpenROAD version the flow stops at DPL-0036 again: use --clock buf.
    if { [llength [info commands cts::set_insertion_delay]] && ![llength [info commands cts::set_insertion_delay_orig]] } {
        rename cts::set_insertion_delay cts::set_insertion_delay_orig
        proc cts::set_insertion_delay {x} { cts::set_insertion_delay_orig false }
    }
}
