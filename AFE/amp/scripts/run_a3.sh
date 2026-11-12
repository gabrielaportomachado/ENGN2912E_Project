#!/bin/bash
# A3 driver.  usage: bash scripts/run_a3.sh <case>
#   cases: op icmr ol loop cl noise rsweep rec clsens variants all
# Each job runs one ngspice testbench through scripts/ngrun.sh and keeps only the key lines (RESULT/OPDEV/OPSUM/
# NOISE*/ICMR/errors) in sim/a3_<case>.log under a "### <label>" header.  scripts/a3_collect.py turns the logs into CSV.
AMP="$(cd "$(dirname "$0")/.." && pwd)"
RUN=/tmp/a3run; mkdir -p "$RUN"
COMBOS="typical:-40 typical:27 typical:85 ff:-40 ff:27 ff:85 ss:-40 ss:27 ss:85"
KEYS='^(RESULT|OPDEV|OPSUM|NOISE|ICMR|CHECK)|[Ee]rror|[Ff]atal|singular'
# R0 of the simulated pseudo-resistor (A2: sim/char_pseudoR.csv, W=1u L=2u vt=+0.2 V)
r0() { awk -v c=$1 -v T=$2 '$1==c && $2==T && $4=="2u" && ($5+0)==0.2 {print $6}' "$AMP/sim/char_pseudoR.csv"; }
job() { # case label tb corner T [NAME=VALUE ...]
  local cs=$1 label=$2; shift 2
  mkdir -p "$RUN/$cs"
  { echo "### $label"; bash "$AMP/scripts/ngrun.sh" "$@" 2>&1 | grep -E "$KEYS" | head -40; } > "$RUN/$cs/$label.txt"
}
par() { xargs -P 8 -I{} bash -c "{}"; }   # one command per line on stdin
fin() { cat "$RUN/$1"/*.txt > "$AMP/sim/a3_$1.log"; echo "wrote sim/a3_$1.log ($(grep -c '^###' "$AMP/sim/a3_$1.log") jobs)"; }
export -f job r0; export AMP RUN KEYS
J="job"
case $1 in
op)    rm -rf $RUN/op; for c in $COMBOS; do k=${c%%:*}; T=${c##*:}; echo "$J op op_${k}_$T tb_ota1_op.spice $k $T"; done | par; fin op ;;
icmr)  rm -rf $RUN/icmr; $J icmr icmr_typical_27 tb_ota1_icmr.spice typical 27; fin icmr ;;
ol)    rm -rf $RUN/ol; for c in $COMBOS; do k=${c%%:*}; T=${c##*:}; echo "$J ol ol_${k}_$T tb_ota1_ol.spice $k $T"; done | par; fin ol ;;
loop)  rm -rf $RUN/loop; for c in $COMBOS; do k=${c%%:*}; T=${c##*:}; echo "$J loop loop_${k}_$T tb_ota1_loop.spice $k $T"; done | par; fin loop ;;
cl)    rm -rf $RUN/cl   # closed loop .ac with the simulated pseudo-resistor device (RMODE=0)
  for c in $COMBOS; do k=${c%%:*}; T=${c##*:}; echo "$J cl cl_${k}_$T tb_st1_ac.spice $k $T"; done | par; fin cl ;;
noise) rm -rf $RUN/noise   # IDEAL RESISTOR (noise) with R = R0(corner,T); typical flicker and fnoicor=1
  for c in $COMBOS; do k=${c%%:*}; T=${c##*:}; R=$(r0 $k $T)
    for fn in 0 1; do echo "$J noise noise_${k}_${T}_fn$fn tb_st1_noise.spice $k $T RFIX=$R FN=$fn"; done; done | par; fin noise ;;
rsweep) rm -rf $RUN/rsweep   # Decision 7: feedback R swept 0.5-50 TOhm (IDEAL resistor), typical 27 C
  for R in 0.5e12 1e12 1.6e12 2.5e12 5e12 1e13 2e13 5e13; do
    TS=$(awk -v r=$R 'BEGIN{t=9*r*2e-13; if (t<8) t=8; printf "%.3g", t}'); TM=$(awk -v t=$TS 'BEGIN{printf "%.3g", t/1000}')
    echo "$J rsweep ac_R$R tb_st1_ac.spice typical 27 RMODE=1 RFIX=$R"
    echo "$J rsweep n0_R$R tb_st1_noise.spice typical 27 RFIX=$R FN=0"
    echo "$J rsweep n1_R$R tb_st1_noise.spice typical 27 RFIX=$R FN=1"
    echo "$J rsweep nr0_R$R tb_st1_noise.spice typical 27 RFIX=$R FN=0 RNOISY=0"
    echo "$J rsweep rec1_R$R tb_st1_tran.spice typical 27 RMODE=1 RFIX=$R VSTEP=1m TSTOP=$TS TMAXS=$TM"
    echo "$J rsweep rec10_R$R tb_st1_tran.spice typical 27 RMODE=1 RFIX=$R VSTEP=10m TSTOP=$TS TMAXS=$TM"
  done | par; fin rsweep ;;
rec)   rm -rf $RUN/rec   # as-simulated pseudo-resistor device: recovery vs step size, corners
  for c in typical:27 ff:27 ss:27 typical:-40 typical:85 ff:85 ss:-40; do k=${c%%:*}; T=${c##*:}
    for V in 1m 5m 10m; do echo "$J rec rec_${k}_${T}_$V tb_st1_tran.spice $k $T RMODE=0 VSTEP=$V TSTOP=40 TMAXS=0.04"; done; done | par; fin rec ;;
clsens) rm -rf $RUN/clsens   # sensitivity to the stage-2 input capacitance placeholder
  for CL in 0.5p 1p 2p 5p 10p; do
    echo "$J clsens loop_CL$CL tb_ota1_loop.spice typical 27 CL_NEXT=$CL"
    echo "$J clsens ac_CL$CL tb_st1_ac.spice typical 27 CL_NEXT=$CL"
  done | par; fin clsens ;;
variants) rm -rf $RUN/variants   # Decision 5 rows: load m=1 vs m=2 (second-stage m=2*load m)
  for KN in 1 2; do K6=$((2*KN)); R=$(r0 typical 27)
    echo "$J variants n0_KN$KN tb_st1_noise.spice typical 27 RFIX=$R FN=0 OTA_KN=$KN OTA_K6=$K6"
    echo "$J variants n1_KN$KN tb_st1_noise.spice typical 27 RFIX=$R FN=1 OTA_KN=$KN OTA_K6=$K6"
    echo "$J variants loop_KN$KN tb_ota1_loop.spice typical 27 OTA_KN=$KN OTA_K6=$K6"
    echo "$J variants op_KN$KN tb_ota1_op.spice typical 27 OTA_KN=$KN OTA_K6=$K6"
    echo "$J variants ol_KN$KN tb_ota1_ol.spice typical 27 OTA_KN=$KN OTA_K6=$K6"
  done | par; fin variants ;;
all) for c in op icmr ol loop cl noise rsweep rec clsens variants; do bash "$0" $c; done ;;
*) echo "unknown case"; exit 1 ;;
esac
