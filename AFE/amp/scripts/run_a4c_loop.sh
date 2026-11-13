#!/bin/bash
# A4c item 1: stage-1 loop gain / phase margin in the RESET state (fs = 3.3 V: pseudo-R gates at the reset level VRS), Tian two-injection (tb/tb_a4c_loop.spice), 3 corners.
# usage: bash scripts/run_a4c_loop.sh <label> "<RSL list (reset-replica sink length: I_REF ~ 1/RSL)>" "<W> <L>"  [CORNERS="typical:27 ff:85 ss:-40"] [EXTRA="NAME=VALUE ..."] -> sim/a4c_loop_<label>.log
AMP="$(cd "$(dirname "$0")/.." && pwd)"; LAB=$1; VRSL=$2; SZ=${3:-"1u 2u"}; set -- $SZ; W=$1; L=$2
LOG="$AMP/sim/a4c_loop_$LAB.log"; RUN=/tmp/a4c/loop_$LAB; rm -rf $RUN; mkdir -p $RUN; export OMP_NUM_THREADS=1
one() { c=$1; T=$2; v=$3; id=$4; core=$5; ns=$(taskset -c $core bash "$AMP/scripts/ngrun.sh" tb_a4c_bias.spice $c $T RSL=$v PR1W=$W PR1L=$L $EXTRA 2>&1 | grep -o "vrs=[0-9.]*" | head -1 | cut -d= -f2); { echo "### loop corner=$c T=$T RSL=$v PR1=$W/$L vrs_nodeset=$ns $EXTRA"; taskset -c $core bash "$AMP/scripts/ngrun.sh" tb_a4c_loop.spice $c $T FSV=3.3 NSVRS=${ns:-0.99} RSL=$v PR1W=$W PR1L=$L $EXTRA 2>&1 | cut -c1-200 | grep -E '^RESULT|rror' | head -3; } > $RUN/$id.txt; }
export -f one; export AMP W L EXTRA RUN
i=0; for c in ${CORNERS:-typical:27 ff:85 ss:-40}; do for v in $VRSL; do echo "one ${c%%:*} ${c##*:} $v $(printf %03d $i) $((i%7))"; i=$((i+1)); done; done | parallel -j 7
cat $RUN/*.txt > "$LOG"; echo "wrote $LOG"
