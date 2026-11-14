#!/bin/bash
# D3 LibreLane run (separate design adc8_top, config in lg/). Checks free disk first; waits by PID. usage: bash run_d3_synth.sh [extra librelane args]
ADC="$(cd "$(dirname "$0")/.." && pwd)"; cd "$ADC/lg"
df -h "$ADC" | tail -1
FREE=$(df -Pk "$ADC" | awk 'NR==2{print int($4/1048576)}'); [ "$FREE" -lt 5 ] && { echo "STOP: only ${FREE} GB free" >&2; exit 1; }
rm -rf runs/d3
librelane --run-tag d3 config.json "$@" > "$ADC/sim/d3_librelane.log" 2>&1 &
pid=$!; wait $pid; echo "librelane exit $?"
