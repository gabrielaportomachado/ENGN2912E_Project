#!/bin/bash
# REVIEW R14 (Decision 54) RTL verification of adc_top #(N = 4): usage  bash AFE/adc/scripts/run_r14_sim.sh   -> logs AFE/adc/sim/r14_*.log, prints one RESULT line per run.
#   tb_adc_top   : the 80-SCLK frame bit by bit (exh: every code on every channel at 2 MHz tt; edge cases at 2 / 3 / 5 MHz and 0.64 MHz ss125; rand matrix 5 corners x 4 frequencies)
#   tb_adc_equiv : conversion phase of the legacy adc8_top and adc_top N = 4 identical for channels 0-3
#   tb_adc8      : the legacy testbench on the legacy adc8_top (it must still PASS unchanged after adc_clkgen got its parameter N)
ADC="$(cd "$(dirname "$0")/.." && pwd)"; T="${AFE_SCRATCH:-/tmp}/r14_sim.$$"; mkdir -p "$T" "$ADC/sim"; cd "$ADC"
build() { iverilog -g2005 -D$1 -s $2 -o "$T/$2_$1.vvp" tb/$2.v tb/ana_model.v tb/cells_sim.v rtl/*.v || exit 1; }
for c in CORNER_TT CORNER_SS125 CORNER_SSN40 CORNER_FFN40 CORNER_FF125; do build $c tb_adc_top; done
build CORNER_TT tb_adc_equiv; build CORNER_SS125 tb_adc_equiv; build CORNER_FFN40 tb_adc_equiv; build CORNER_TT tb_adc8
pids=()
vvp "$T/tb_adc_top_CORNER_TT.vvp" +PER=500 +MODE=exh +NF=4096 > sim/r14_exh_tt_2MHz.log 2>&1 & pids+=($!)
( for f in "500 CORNER_TT 2" "333.333 CORNER_TT 3" "1562.5 CORNER_SS125 0.64" "200 CORNER_FFN40 5"; do set -- $f; echo "== edge PER $1 $2 ($3 MHz)"; vvp "$T/tb_adc_top_$2.vvp" +PER=$1 +MODE=edge | grep -E "ERR|RESULT"; done ) > sim/r14_edge.log 2>&1 & pids+=($!)
( for c in CORNER_TT CORNER_SS125 CORNER_SSN40 CORNER_FFN40 CORNER_FF125; do for p in "1000 1" "500 2" "333.333 3" "250 4"; do set -- $p; echo "== $c SCLK $2 MHz"; vvp "$T/tb_adc_top_$c.vvp" +PER=$1 +MODE=rand +NF=64 | grep -E "ERR|RESULT"; done; done ) > sim/r14_matrix.log 2>&1 & pids+=($!)
( for f in "500 CORNER_TT" "333.333 CORNER_TT" "1562.5 CORNER_SS125" "200 CORNER_FFN40"; do set -- $f; echo "== equiv PER $1 $2"; vvp "$T/tb_adc_equiv_$2.vvp" +PER=$1 +NF=96 | grep -E "MISMATCH|EQUIV|RESULT"; done ) > sim/r14_equiv.log 2>&1 & pids+=($!)
( vvp "$T/tb_adc8_CORNER_TT.vvp" +PER=500 +MODE=rand +NF=16 | grep -E "ERR|RESULT"; vvp "$T/tb_adc8_CORNER_TT.vvp" +PER=500 +MODE=edge | grep -E "ERR|RESULT" ) > sim/r14_legacy_adc8.log 2>&1 & pids+=($!)
for p in "${pids[@]}"; do wait $p; done
rm -rf "$T"
for l in sim/r14_exh_tt_2MHz.log sim/r14_edge.log sim/r14_matrix.log sim/r14_equiv.log sim/r14_legacy_adc8.log; do echo "--- $l"; grep -E "RESULT|ERR|MISMATCH" $l | sort | uniq -c | sort -rn | head -8; done
np=$(cat sim/r14_*.log | grep -c "RESULT PASS"); nf=$(cat sim/r14_*.log | grep -c "RESULT FAIL"); ne=$(cat sim/r14_*.log | grep -c "ERR\|MISMATCH")
echo "R14 RTL SIM: $np PASS lines, $nf FAIL lines, $ne ERR lines"; [ "$nf" = 0 ] && [ "$ne" = 0 ] && [ "$np" -ge 31 ] && echo "R14 RTL SIM PASS" || echo "R14 RTL SIM FAIL"
