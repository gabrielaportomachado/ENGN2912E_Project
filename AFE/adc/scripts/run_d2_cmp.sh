#!/bin/bash
# D2 confirming sims for a smaller comparator input pair (hand-back for D1b): energy/charge, input noise, kick trip.  usage: run_d2_cmp.sh <CMP_WP value, e.g. 20u> ; results -> sim/d2_cmp_<WP>.log
ADC="$(cd "$(dirname "$0")/.." && pwd)"; cd "$ADC"; export OMP_NUM_THREADS=1; W=$1; LOG=sim/d2_cmp_$W.log
{ for c in "typical 27" "ff 85" "ss -40"; do
    echo "python3 scripts/d1_run.py delay $c cmp_p cm=1.65 CMP_WP=$W"
    echo "python3 scripts/d2_cmp_noise.py $c CMP_WP=$W --ncyc=300 --span=0.8 --tag=w$W"
    echo "D2X=CMP_WP=$W bash scripts/d2_trip1.sh $c 5"
  done; } | bash scripts/pj.sh 2>&1 | grep -E "^DELAY|^NOISE|^TRIP|SHORT|FAIL" | sort > "$LOG"
echo "finished $W" >> sim/d2_cmp_done.txt
