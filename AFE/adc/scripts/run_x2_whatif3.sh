#!/bin/bash
# X2 what-if, part 3 (PROPOSAL P3, top-of-range plate error): first trial with the 11 lower bits switched X2_NOV1 after the MSB instead of 0.3 ns (testbench timing only).  ADC alone, 8 inputs 1.75-2.15 V.  -> sim/x2_adc.log
ADC="$(cd "$(dirname "$0")/.." && pwd)"; cd "$ADC"; export X2_YIELD=1
V=1.7503,1.8507,1.9011,1.9512,2.0006,2.0509,2.1004,2.1507
for ck in typ ff85; do
  python3 scripts/x2_adc.py $ck $V
  X2_NOV1=10e-9 python3 scripts/x2_adc.py $ck $V
  X2_NOV1=3e-9 python3 scripts/x2_adc.py $ck $V
done
echo "$(date '+%F %T') x2_whatif3 done" >> "$ADC/sim/x2_done.txt"
