#!/bin/bash
# D5 item 2 driver, N = 64 version (the N = 512 plan failed twice: first 0.6 s start-up / 1 us step cap did not finish in the 1750 s limit, then 30 ms start-up / 3 us cap: all 6 jobs aborted with ngspice "timestep too small" after ~60 frames).
# 9 jobs: 3 corners x {b1 = 0.45 V pk at 62.5 Hz (M 1), b3 = 0.45 V pk at 187.5 Hz (M 3), s1 = 0.10 V pk at 62.5 Hz}; -> sim/d5_<tag>_<corner>.npz, log sim/d5_sndr_run.log, done-file sim/d5_sndr_done.txt
ADC="$(cd "$(dirname "$0")/.." && pwd)"; cd $ADC; rm -f sim/d5_sndr_done.txt; mkdir -p sim/.ptmp; export TMAXS=3e-6 OMP_NUM_THREADS=1 TMO=900
for c in "typical 27 typ" "ff 85 ff" "ss -40 ss"; do set -- $c
  python3 scripts/d5_sndr.py run $1 $2 b1 0.45 1 64 0.03 >> sim/.ptmp/sndr_$3_b1.out 2>&1 &
  python3 scripts/d5_sndr.py run $1 $2 b3 0.45 3 64 0.03 >> sim/.ptmp/sndr_$3_b3.out 2>&1 &
  python3 scripts/d5_sndr.py run $1 $2 s1 0.10 1 64 0.03 >> sim/.ptmp/sndr_$3_s1.out 2>&1 &
done
wait
cat sim/.ptmp/sndr_*.out > sim/d5_sndr_run.log; rm -f sim/.ptmp/sndr_*.out
touch /foss/designs/ENGN2912E_Project/AFE/adc/sim/d5_sndr_done.txt
