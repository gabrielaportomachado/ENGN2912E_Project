# D3 constraints for adc8_top (period set by the flow through CLOCK_PERIOD = 500 ns = 2 MHz nominal; reports at 333.3 ns are made separately by scripts/d3_sta.tcl)
create_clock -name sclk -period $::env(CLOCK_PERIOD) [get_ports sclk]
set_clock_uncertainty 0.5 [get_clocks sclk]
# MCU side, relative to SCLK (SPI mode 0: DIN changes on falling edge: setup to rising = T/2; CS and RSTN are asynchronous resets/frame signals)
set_input_delay [expr 0.5 * $::env(CLOCK_PERIOD)] -clock sclk [get_ports {din}]
set_input_delay [expr 0.25 * $::env(CLOCK_PERIOD)] -clock sclk [get_ports {cs_n}]
# RSTN: asynchronous, deassertion timing is not related to SCLK
set_false_path -from [get_ports {rstn}]
set_output_delay [expr 0.3 * $::env(CLOCK_PERIOD)] -clock sclk [get_ports {dout mode_o en_o[*]}]
# comparator outputs: launched by the delayed comparator clock itself, captured by tapw of the same ADC: not a path against SCLK (decision time <= window W is a separate check, sim/d3_taps.log)
set_false_path -from [get_ports {cmp_q[*]}]
# analog-side control outputs: no digital capture; their arrival times (delay chain taps, gp/gn, tg_on) are REPORTED by scripts/d3_sta.tcl, not constrained
set_false_path -to [get_ports {cmp_clk[*] rst_sw[*] tg_on[*] dac_gp[*] dac_gn[*] dout_oe}]
