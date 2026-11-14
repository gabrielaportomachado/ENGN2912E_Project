#!/bin/bash
# D5 item 1 driver: 3 corners x 19 cases (each ~3 s) -> sim/d5_settle.log ; done-file sim/d5_settle_done.txt
ADC="$(cd "$(dirname "$0")/.." && pwd)"; cd $ADC; rm -f sim/d5_settle_done.txt; mkdir -p sim/.ptmp
CASES=1.65_1.65_0,1.65_1.65_p,1.65_1.65_m,1.65_1.89_p,1.65_1.89_m,1.65_1.41_p,1.65_1.41_m,2.1_2.1_p,2.1_2.1_m,2.1_1.86_p,2.1_1.86_m,2.15_2.15_p,2.15_2.15_m,2.15_1.91_p,2.15_1.91_m,1.2_1.2_p,1.2_1.2_m,1.2_1.44_p,1.2_1.44_m
for c in "typical 27" "ff 85" "ss -40"; do set -- $c; (python3 scripts/d5_settle.py $1 $2 $CASES > sim/.ptmp/settle_$1.out 2>&1) & done; wait
{ echo "# D5 item 1: amplifier output error (out_L - out_U, loaded minus unloaded copy) in LSB (0.806 mV) with the real TG + split DAC on the output; reltol 1e-4; kick polarity p/m/0 = previous code giving max/min/nearest charge (see d5_settle.py)"; cat sim/.ptmp/settle_typical.out sim/.ptmp/settle_ff.out sim/.ptmp/settle_ss.out; } > sim/d5_settle.log
rm -f sim/.ptmp/settle_*.out; touch /foss/designs/ENGN2912E_Project/AFE/adc/sim/d5_settle_done.txt
