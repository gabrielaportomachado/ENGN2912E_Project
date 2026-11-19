#!/bin/bash
# X2 / S2 statistics, part 2.  The D5 aborts happened with the container default of 4 OpenMP threads (~/.spiceinit); X2 runs use 1 thread, which changes the round-off and therefore WHERE a
# tolerance-limited Newton failure happens.  So: (a) the prompt's numerical fixes and the proposed tolerance set again with 4 threads (same conditions as D5 and as the first X2 experiments),
# (b) the unchanged D5 tolerance set (abstol 1e-15) with 1 thread at four step caps and with 512 frames.  -> sim/x2_s2_repro.log (append; every line says threads=)
ADC="$(cd "$(dirname "$0")/.." && pwd)"; cd "$ADC"; mkdir -p sim/.ptmp; export X2_LOGOUT="$ADC/sim/x2_s2_repro.log" X2_YIELD=3
run() { tag=$1; shift; python3 scripts/x2_s2_repro.py typical 27 "$tag" 0.45 1 "$@" > "sim/.ptmp/o_s2_$tag.out" 2>&1 & PIDS="$PIDS $!"; }
PIDS=""; export X2_THREADS=4
X2_TR=5e-9 run F4_edges5n 64 0.03 3e-6 - "" 3000
run F4_gear 64 0.03 3e-6 - "method=gear" 3000
run F4_rshunt1e12 64 0.03 3e-6 - "rshunt=1e12" 3000
run F4_abstol1e-14 64 0.03 3e-6 - "abstol=1e-14" 3000
run F4_abstol1e-13 64 0.03 3e-6 - "abstol=1e-13" 3000
run P4_abstol1e-12_tmax2p1u 64 0.03 2.1e-6 - "abstol=1e-12" 3000
run P4_abstol1e-12_tmax4p2u 64 0.03 4.2e-6 - "abstol=1e-12" 3000
run P4_abstol1e-12_tmax1u 64 0.03 1e-6 - "abstol=1e-12" 3000
for p in $PIDS; do wait $p; done
python3 scripts/x2_s2_trace.py > sim/.ptmp/o_s2_trace.out 2>&1
PIDS=""; export X2_THREADS=1
run B1_abstol1e-15_tmax2p1u 64 0.03 2.1e-6 - "" 3000
run B1_abstol1e-15_tmax4p2u 64 0.03 4.2e-6 - "" 3000
run B1_abstol1e-15_tmax1u 64 0.03 1e-6 - "" 3000
run B1_abstol1e-15_N512 512 0.03 3e-6 - "" 5400
for p in $PIDS; do wait $p; done
echo "$(date '+%F %T') x2_s2_stats2 done" >> "$ADC/sim/x2_done.txt"
