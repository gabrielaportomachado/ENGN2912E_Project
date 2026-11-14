#!/bin/bash
# D2 split-supply runs with (1) staggered comparator clocks and (2) smaller comparator charge; each python call < 1800 s; tags appended (>>) to sim/d2_supply3_done.txt
ADC="$(cd "$(dirname "$0")/.." && pwd)"; cd "$ADC"; export OMP_NUM_THREADS=1
for f in 5 1; do for cfg in "0 2.6" "1 2.6" "0 1.5" "1 1.5"; do set -- $cfg
  python3 scripts/d2_supply.py split3 $f $1 $2 > /dev/null 2>> sim/d2_supply3_err.log; echo "done f=$f cstag=$1 q=$2" >> sim/d2_supply3_done.txt; done
  python3 scripts/d2_supply.py split3 $f 1 1.5 dig > /dev/null 2>> sim/d2_supply3_err.log; echo "done f=$f cstag=1 q=1.5 dig" >> sim/d2_supply3_done.txt; done
echo ALLDONE >> sim/d2_supply3_done.txt
