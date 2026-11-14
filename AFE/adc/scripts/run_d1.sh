#!/bin/bash
# D1 driver.  usage: bash scripts/run_d1.sh <case> [extra NAME=VALUE overrides for all runs]     (jobs run in parallel, one core each; results -> sim/d1_<case>.log)
# cases: delay offset noise icmr conv kick tbl
ADC="$(cd "$(dirname "$0")/.." && pwd)"; cd "$ADC/tb"
CORN="typical:27 ff:85 ss:-40"; cs=$1; shift; X="$*"; R="python3 $ADC/scripts/d1_run.py"
case $cs in
delay)  { for c in $CORN; do k=${c%%:*}; T=${c##*:}; for cm in 1.65 0.6; do echo "$R delay $k $T cmp_p cm=$cm $X"; done; done; echo "$R delay typical 27 cmp_n cm=1.65 $X"; } ;;
offset) { for c in $CORN; do k=${c%%:*}; T=${c##*:}; for s in $(seq 1 ${NMC:-40}); do echo "$R offset $k $T cmp_p seed=$s $X"; done; done; } ;;
noise)  { for c in $CORN; do k=${c%%:*}; T=${c##*:}; echo "python3 $ADC/scripts/d1_noise.py $k $T $X --ncyc=${NCYC:-600} --span=${SPAN:-0.6} --tag=${TAG:-final}"; done; } ;;
icmr)   { for cell in cmp_p cmp_n; do for c in $CORN; do k=${c%%:*}; T=${c##*:}; for cm in $(seq 0 0.1 3.3) 0.05 3.25; do echo "$R icmr $k $T $cell cm=$cm $X"; done; done; done; } ;;
conv)   { for cell in cmp_p cmp_n; do for c in $CORN; do k=${c%%:*}; T=${c##*:}; echo "$R conv $k $T $cell $X"; done; done; } ;;
kick)   { for c in $CORN; do k=${c%%:*}; T=${c##*:}; for cm in 1.65; do echo "$R kick $k $T cmp_p cm=$cm $X"; done; done; } ;;
*) echo unknown case; exit 1 ;;
esac | bash "$ADC/scripts/pj.sh" | sort > "$ADC/sim/d1_$cs.log"
wc -l "$ADC/sim/d1_$cs.log"
