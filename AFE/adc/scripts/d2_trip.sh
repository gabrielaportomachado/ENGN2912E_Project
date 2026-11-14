#!/bin/bash
# D2: evaluate-phase shift and trip voltage of cmp_p on the REAL DAC plate (tb/tb_dac_float.spice) -> sim/d2_float.log  (one core per job via pj.sh)
ADC="$(cd "$(dirname "$0")/.." && pwd)"; cd "$ADC"; LOG=sim/d2_float.log
{ for c in "typical 27" "ff 85" "ss -40"; do echo "bash scripts/d2_trip1.sh $c 5"; echo "python3 scripts/d2_float.py $c + 5 0.4"; echo "python3 scripts/d2_float.py $c + 1 0.4"; done; } | bash scripts/pj.sh | sort > "$LOG"
cut -c1-500 "$LOG"
