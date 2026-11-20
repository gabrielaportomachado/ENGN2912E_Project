# AUDIT step 4: digital -> analog arrival table from OpenSTA on the CURRENT hardened netlist (AFE/adc/lg/runs/d3/final, built 2026-11-14 15:59 in I1;
# the saved AFE/adc/sim/d3_taps.log is from the 08:38 netlist).  No CTS in that run: SCLK is one net, ideal edge at the port, propagated through the SPEF.
# usage: CORNER=<lib corner> RUN=<final dir> SPEF=<nom|min|max> sta -no_init -no_splash -exit sta_audit.tcl      (parsed by sta_audit.py)
set lib_root /foss/pdks/gf180mcuD/libs.ref/gf180mcu_fd_sc_mcu7t5v0/lib
read_liberty $lib_root/gf180mcu_fd_sc_mcu7t5v0__$::env(CORNER).lib
read_verilog $::env(RUN)/nl/adc8_top.nl.v
link_design adc8_top
read_spef $::env(RUN)/spef/$::env(SPEF)/adc8_top.$::env(SPEF).spef
create_clock -name sclk -period 500 [get_ports sclk]
set_propagated_clock [get_clocks sclk]
# async clear arcs (RN -> Q) are needed for the CS-rising release paths (cs_n -> frame_rn -> en_r -> gp/gn)
set sta_preset_clear_arcs_enabled 1
puts "CORNER $::env(CORNER) SPEF $::env(SPEF)"

proc rep {tag args} {
  puts "@@ $tag"
  eval report_checks $args -unconstrained -digits 3 -format end
}
proc capflop {i} {
  set n [get_nets "ch\[$i\].u.cap_r"]
  foreach p [get_pins -of_objects $n] { if {[get_property $p direction] == "output"} { return [get_full_name [get_cells -of_objects $p]] } }
}
# 1. comparator clock windows
for {set i 0} {$i < 8} {incr i} {
  rep "CMPCLK $i RISE MAX" -path_delay max -rise_from [get_ports sclk] -rise_to [get_ports cmp_clk[$i]]
  rep "CMPCLK $i RISE MIN" -path_delay min -rise_from [get_ports sclk] -rise_to [get_ports cmp_clk[$i]]
  rep "CMPCLK $i FALL MAX" -path_delay max -rise_from [get_ports sclk] -fall_to [get_ports cmp_clk[$i]]
  rep "CMPCLK $i FALL MIN" -path_delay min -rise_from [get_ports sclk] -fall_to [get_ports cmp_clk[$i]]
}
# 2. DAC driver gates (all 96 + 96), worst and best arrival after the SCLK rising edge (flop launched) and after CS rising (async release)
for {set k 0} {$k < 96} {incr k} {
  rep "GP $k MAX" -path_delay max -from [get_clocks sclk] -to [get_ports dac_gp[$k]]
  rep "GP $k MIN" -path_delay min -from [get_clocks sclk] -to [get_ports dac_gp[$k]]
  rep "GN $k MAX" -path_delay max -from [get_clocks sclk] -to [get_ports dac_gn[$k]]
  rep "GN $k MIN" -path_delay min -from [get_clocks sclk] -to [get_ports dac_gn[$k]]
  rep "GPCS $k MAX" -path_delay max -rise_from [get_ports cs_n] -to [get_ports dac_gp[$k]]
  rep "GNCS $k MAX" -path_delay max -rise_from [get_ports cs_n] -to [get_ports dac_gn[$k]]
}
# 3. tracking switches: CS falling (sample), CS rising (abort), SCLK (done flop)
for {set i 0} {$i < 8} {incr i} {
  foreach p {rst_sw tg_on dac_gdn} {
    rep "TRKF $p $i MAX" -path_delay max -fall_from [get_ports cs_n] -to [get_ports ${p}[$i]]
    rep "TRKF $p $i MIN" -path_delay min -fall_from [get_ports cs_n] -to [get_ports ${p}[$i]]
    rep "TRKR $p $i MAX" -path_delay max -rise_from [get_ports cs_n] -to [get_ports ${p}[$i]]
    rep "TRKR $p $i MIN" -path_delay min -rise_from [get_ports cs_n] -to [get_ports ${p}[$i]]
    rep "TRKC $p $i MAX" -path_delay max -from [get_clocks sclk] -to [get_ports ${p}[$i]]
    rep "TRKC $p $i MIN" -path_delay min -from [get_clocks sclk] -to [get_ports ${p}[$i]]
  }
}
# 4. serial / config outputs
rep "DOUT MAX" -path_delay max -from [get_clocks sclk] -to [get_ports dout]
rep "DOUT MIN" -path_delay min -from [get_clocks sclk] -to [get_ports dout]
rep "DOUTCS MAX" -path_delay max -from [get_ports cs_n] -to [get_ports dout]
rep "DOUTOE MAX" -path_delay max -to [get_ports dout_oe]
rep "RSTAMP MAX" -path_delay max -to [get_ports rst_amp_o]
rep "MODE MAX" -path_delay max -to [get_ports mode_o]
for {set i 0} {$i < 8} {incr i} { rep "EN $i MAX" -path_delay max -to [get_ports en_o[$i]] }
# 5. capture flop: clock arrival (tapw) and the cap -> code setup slack at 2 and 3 MHz
for {set i 0} {$i < 8} {incr i} {
  set f [capflop $i]
  foreach P {500 333.333} {
    create_clock -name sclk -period $P [get_ports sclk]
    set_propagated_clock [get_clocks sclk]
    puts "@@ CAPPATH $i P=$P flop=$f"
    report_checks -path_delay max -through [get_pins $f/Q] -digits 3 -format full_clock_expanded
  }
}
create_clock -name sclk -period 500 [get_ports sclk]
set_propagated_clock [get_clocks sclk]
# 6. recovery of the frame flops after CS falling: input delay 0 w.r.t. the SCLK rising edge at t = 0, capture at the next rising edge (500 ns):
#    required CS-fall -> first-SCLK-rise time = 500 - slack.  Same for RSTN.
set_input_delay 0 -clock sclk [get_ports cs_n]
set_input_delay 0 -clock sclk [get_ports rstn]
puts "@@ RECOVERY CS"
report_checks -path_delay max -fall_from [get_ports cs_n] -digits 3 -format end -group_path_count 3
puts "@@ RECOVERY RSTN"
report_checks -path_delay max -rise_from [get_ports rstn] -digits 3 -format end -group_path_count 3
puts "@@ MINPULSE"
report_check_types -min_pulse_width -digits 3
puts "@@ END"
