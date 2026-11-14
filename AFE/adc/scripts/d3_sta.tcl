# OpenSTA on the LibreLane final netlist + extracted SPEF (nom). usage: CORNER=<lib corner> RUN=<run final dir> sta -no_init -no_splash -exit d3_sta.tcl   (parsed by d3_taps.py)
set lib_root /foss/pdks/gf180mcuD/libs.ref/gf180mcu_fd_sc_mcu7t5v0/lib
read_liberty $lib_root/gf180mcu_fd_sc_mcu7t5v0__$::env(CORNER).lib
read_verilog $::env(RUN)/nl/adc8_top.nl.v
link_design adc8_top
read_spef $::env(RUN)/spef/nom/adc8_top.nom.spef
create_clock -name sclk -period 500 [get_ports sclk]
set_propagated_clock [get_clocks sclk]
puts "CORNER $::env(CORNER)"
proc capflop {i} {
  set n [get_nets "ch\[$i\].u.cap_r"]
  foreach p [get_pins -of_objects $n] { if {[get_property $p direction] == "output"} { return [get_full_name [get_cells -of_objects $p]] } }
}
for {set i 0} {$i < 8} {incr i} {
  puts "ADC $i RISE"
  report_checks -path_delay max -rise_from [get_ports sclk] -rise_to [get_ports cmp_clk[$i]] -unconstrained -digits 3 -format end
  puts "ADC $i FALL"
  report_checks -path_delay max -rise_from [get_ports sclk] -fall_to [get_ports cmp_clk[$i]] -unconstrained -digits 3 -format end
  set f [capflop $i]
  foreach P {500 333.333} {
    create_clock -name sclk -period $P [get_ports sclk]
    puts "ADC $i CAPPATH P=$P flop=$f"
    report_checks -path_delay max -through [get_pins $f/Q] -digits 3 -format full_clock_expanded
  }
  create_clock -name sclk -period 500 [get_ports sclk]
}
# DAC drive paths and tracking switches (arrival from SCLK rise / CS fall)
puts "GPGN"
report_checks -path_delay max -rise_from [get_ports sclk] -to [get_ports dac_gp[0]] -unconstrained -digits 3 -format end
report_checks -path_delay max -fall_from [get_ports sclk] -to [get_ports dac_gp[0]] -unconstrained -digits 3 -format end
report_checks -path_delay max -rise_from [get_ports sclk] -to [get_ports dac_gn[5]] -unconstrained -digits 3 -format end
report_checks -path_delay max -rise_from [get_ports sclk] -to [get_ports dac_gp[95]] -unconstrained -digits 3 -format end
puts "TRK"
report_checks -path_delay max -fall_from [get_ports cs_n] -to [get_ports rst_sw[0]] -unconstrained -digits 3 -format end
report_checks -path_delay max -fall_from [get_ports cs_n] -to [get_ports tg_on[0]] -unconstrained -digits 3 -format end
report_checks -path_delay min -fall_from [get_ports cs_n] -to [get_ports rst_sw[0]] -unconstrained -digits 3 -format end
report_checks -path_delay min -fall_from [get_ports cs_n] -to [get_ports tg_on[7]] -unconstrained -digits 3 -format end
