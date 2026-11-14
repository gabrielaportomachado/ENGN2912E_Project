#!/bin/bash
# D3 simulation driver (Icarus). usage: bash run_d3_sim.sh   -> logs in sim/d3_*.log, temp files in sim/.ptmp (removed at the end). Waits by PID.
ADC="$(cd "$(dirname "$0")/.." && pwd)"; T=$ADC/sim/.ptmp; mkdir -p "$T"; cd "$ADC"
FREE=$(df -Pk "$ADC" | awk 'NR==2{print int($4/1048576)}'); [ "$FREE" -lt 5 ] && { echo "STOP: only ${FREE} GB free" >&2; exit 1; }
build() { iverilog -g2005 -D$1 -o "$T/tb_$1.vvp" tb/tb_adc8.v tb/ana_model.v tb/cells_sim.v rtl/*.v; }
for c in CORNER_TT CORNER_SS125 CORNER_SSN40 CORNER_FFN40 CORNER_FF125; do build $c || exit 1; done
pids=()
# 1. exhaustive: every code on every channel, 2 MHz, tt chain
vvp "$T/tb_CORNER_TT.vvp" +PER=500 +MODE=exh +NF=4096 > sim/d3_exh_tt_2MHz.log 2>&1 & pids+=($!)
# 2. edge cases: 2 MHz and 3 MHz (tt), 0.64 MHz (ss125)
( for f in "500 CORNER_TT 2" "333.333 CORNER_TT 3" "1562.5 CORNER_SS125 0.64" "200 CORNER_FFN40 5"; do set -- $f; echo "== edge PER $1 $2 ($3 MHz)"; vvp "$T/tb_$2.vvp" +PER=$1 +MODE=edge | grep -E "ERR|RESULT|BADCH|TMINCH"; done ) > sim/d3_edge.log 2>&1 & pids+=($!)
# 3. corner x frequency matrix, random codes, 64 frames
( for c in CORNER_TT CORNER_SS125 CORNER_SSN40 CORNER_FFN40 CORNER_FF125; do for p in "1000 1" "500 2" "333.333 3" "250 4"; do set -- $p; echo "== $c SCLK $2 MHz"; vvp "$T/tb_$c.vvp" +PER=$1 +MODE=rand +NF=64 | grep -E "RESULT|BADCH|TMINCH"; done; done ) > sim/d3_matrix.log 2>&1 & pids+=($!)
for p in "${pids[@]}"; do wait $p; done
rm -rf "$T"/tb_*.vvp
echo done > sim/d3_sim_done.txt
