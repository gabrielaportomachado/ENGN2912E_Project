#!/bin/bash
# A4c item 5: key A4b tables re-run with the A4c netlist (reset OFF, park OFF) at typical 27 / ff 85 / ss -40 (+ any extra CORNERS): ac, noise (typical flicker FN=0 and fnoicor=1), op, loop (normal state).
# usage: [CORE=7] [CORNERS="typical:27 ff:85 ss:-40"] bash scripts/run_a4c_tbl.sh <ac|noise|op|loop>   -> sim/a4c_<case>.log
AMP="$(cd "$(dirname "$0")/.." && pwd)"; CS=${CORNERS:-typical:27 ff:85 ss:-40}; CORE=${CORE:-7}; export OMP_NUM_THREADS=1
KEYS='^(RESULT|OPSUM|OPNODE|NOISE)|[Ee]rror|[Ff]atal'
LOG="$AMP/sim/a4c_$1.log"; : > "$LOG"
for c in $CS; do k=${c%%:*}; T=${c##*:}
  case $1 in
  ac)    echo "### ac $k $T" >> "$LOG"; taskset -c $CORE bash "$AMP/scripts/ngrun.sh" tb_a4c_ac.spice $k $T 2>&1 | cut -c1-300 | grep -E "$KEYS" >> "$LOG" ;;
  noise) R1=$(awk -v c=$k -v T=$T '$1==c && $2==T && $3=="0.22u" && $4=="0.5u" && $5==0.2 {print $6}' "$AMP/sim/a4c_prsize.csv"); R2=$(awk -v c=$k -v T=$T '$1==c && $2==T && $3=="0.22u" && $4=="0.5u" && $5==0.9 {print $6}' "$AMP/sim/a4c_prsize.csv")
         for fn in 0 1; do echo "### noise $k $T FN=$fn RFIX=$R1 (stage 1, VTT 0.2) RFIX2=$R2 (stage 2, VTT 0.9): IDEAL RESISTOR (noise) = R0 of the A4c pseudo-R (0.22u/0.5u, sim/a4c_prsize.csv) at this corner" >> "$LOG"; taskset -c $CORE bash "$AMP/scripts/ngrun.sh" tb_a4c_noise.spice $k $T RFIX=$R1 RFIX2=$R2 FN=$fn 2>&1 | cut -c1-300 | grep -E "$KEYS" >> "$LOG"; done ;;
  op)    echo "### op $k $T" >> "$LOG"; taskset -c $CORE bash "$AMP/scripts/ngrun.sh" tb_a4c_op.spice $k $T 2>&1 | cut -c1-400 | grep -E "$KEYS" >> "$LOG" ;;
  loop)  echo "### loop (normal state, FSV=0) $k $T" >> "$LOG"; taskset -c $CORE bash "$AMP/scripts/ngrun.sh" tb_a4c_loop.spice $k $T FSV=0 2>&1 | cut -c1-200 | grep -E "$KEYS" >> "$LOG" ;;
  esac
done; echo "wrote $LOG"
