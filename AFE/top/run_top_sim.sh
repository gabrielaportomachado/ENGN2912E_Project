#!/bin/bash
# I0 whole-digital-part simulation (Icarus).  usage: bash run_top_sim.sh   (from anywhere) -> sim/i0_top.log
T="$(cd "$(dirname "$0")" && pwd)"; R="$T/../.."; cd "$T"
iverilog -g2005 -DSIM_STUBS -s tb_top -o /tmp/i0_top.vvp tb_top.v dbs_afe_top.v stubs_analog.v ../adc/rtl/*.v ../adc/tb/cells_sim.v "$R/rtl/dbs.v" "$R/TGATE/TGATE.v" 2>&1 | head -30
vvp /tmp/i0_top.vvp > sim/i0_top.log 2>&1; head -80 sim/i0_top.log; rm -f /tmp/i0_top.vvp
