#!/bin/bash
# X2 what-if, part 4 (supply, the S4 case that fails: ff -40 C 3.6 V, inputs near full scale): more main-rail decap, a second bond wire per pad, SCLK 2 MHz.  Testbench supply model only.  -> sim/x2_s4_summary.log, sim/x2_s4_ff-40_whatif.log
ADC="$(cd "$(dirname "$0")/.." && pwd)"; cd "$ADC"
X2_CM=0.25e-9 python3 scripts/x2_s4.py ff-40 fs 3 > sim/.ptmp/o_s4w_cm.out 2>&1 &
P1=$!
X2_LP=1e-9 X2_RP=0.125 python3 scripts/x2_s4.py ff-40 fs 3 > sim/.ptmp/o_s4w_lp.out 2>&1 &
P2=$!
X2_CM=0.5e-9 python3 scripts/x2_s4.py ff-40 fs 3 > sim/.ptmp/o_s4w_cm2.out 2>&1 &
P3=$!
wait $P1 $P2 $P3
echo "$(date '+%F %T') x2_whatif4 done" >> "$ADC/sim/x2_done.txt"
