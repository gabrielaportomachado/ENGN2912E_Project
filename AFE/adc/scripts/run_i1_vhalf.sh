#!/bin/bash
# I1: vhalf sweep, C = 10 / 20 / 40 pF in parallel (9 ngspice jobs), typ 27 / ss 125 / ff -40.  usage: bash run_i1_vhalf.sh  -> sim/i1_vhalf.log (raw waveforms kept in sim/.ptmp/i1_raw_*.csv)
ADC="$(cd "$(dirname "$0")/.." && pwd)"; cd "$ADC"; rm -f sim/i1_vhalf_C*.log
for c in 10 20 40; do python3 scripts/i1_vhalf.py $c > sim/i1_vhalf_C$c.log 2>&1 & done; wait
cat sim/i1_vhalf_C10.log sim/i1_vhalf_C20.log sim/i1_vhalf_C40.log > sim/i1_vhalf.log; rm -f sim/i1_vhalf_C*.log; echo done >> sim/i1_vhalf.log
