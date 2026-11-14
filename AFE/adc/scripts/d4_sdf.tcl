# D4: write an SDF (cell + interconnect delays, nom SPEF) of the D3 final netlist for one lib corner.  usage: CORNER=<lib corner> RUN=<final dir> OUT=<file.sdf> sta -no_init -no_splash -exit d4_sdf.tcl
set lib_root /foss/pdks/gf180mcuD/libs.ref/gf180mcu_fd_sc_mcu7t5v0/lib
read_liberty $lib_root/gf180mcu_fd_sc_mcu7t5v0__$::env(CORNER).lib
read_verilog $::env(RUN)/nl/adc8_top.nl.v
link_design adc8_top
read_spef $::env(RUN)/spef/nom/adc8_top.nom.spef
create_clock -name sclk -period 500 [get_ports sclk]
set_propagated_clock [get_clocks sclk]
write_sdf -digits 4 $::env(OUT)
