#!/bin/bash
# X2 / S2 statistics on the D5 long-run netlist (scripts/x2_s2_repro.py; every run takes one of the 3 machine-wide ngspice slots of x2lib and is waited on by PID).
# Baseline tolerance set (abstol 1e-15) with the numerical fixes of the X2 prompt, one at a time, and the proposed set (abstol 1e-12) with different step caps.  -> sim/x2_s2_repro.log (append)
ADC="$(cd "$(dirname "$0")/.." && pwd)"; cd "$ADC"; mkdir -p sim/.ptmp; export X2_LOGOUT="$ADC/sim/x2_s2_repro.log"
run() { tag=$1; shift; python3 scripts/x2_s2_repro.py typical 27 "$tag" 0.45 1 "$@" > "sim/.ptmp/x2_s2_$tag.out" 2>&1 & PIDS="$PIDS $!"; }
PIDS=""
# proposed set, three other step caps (the D5 retries x0.7 / x1.4 and the 1 us cap), 64 frames
run P_abstol1e-12_tmax2p1u 64 0.03 2.1e-6 - "abstol=1e-12" 2400
run P_abstol1e-12_tmax4p2u 64 0.03 4.2e-6 - "abstol=1e-12" 2400
run P_abstol1e-12_tmax1u   64 0.03 1e-6   - "abstol=1e-12" 2400
# baseline set + one prompt fix each
X2_TR=5e-9 run F_edges5n   64 0.03 3e-6 - "" 2400
run F_gear       64 0.03 3e-6 - "method=gear" 2400
run F_rshunt1e12 64 0.03 3e-6 - "rshunt=1e12" 2400
run F_abstol1e-13 64 0.03 3e-6 - "abstol=1e-13" 2400
run F_abstol1e-14 64 0.03 3e-6 - "abstol=1e-14" 2400
for p in $PIDS; do wait $p; done
python3 scripts/x2_s2_trace.py > sim/.ptmp/x2_s2_trace.out 2>&1
# the original D5 goal: 512 frames, 30 ms start-up, with the proposed set
PIDS=""; run P_abstol1e-12_N512 512 0.03 3e-6 - "abstol=1e-12" 5400
for p in $PIDS; do wait $p; done
echo "$(date '+%F %T') x2_s2_stats done" >> "$ADC/sim/x2_done.txt"
