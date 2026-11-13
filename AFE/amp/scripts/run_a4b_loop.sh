#!/bin/bash
# A4b Decision 21(b): stage-1 loop gain/phase margin with the REAL stage 2 as load (Cin2 3 pF through ota2 + follower), Tian two-injection, 9 PVT -> sim/a4b_loop.log
AMP="$(cd "$(dirname "$0")/.." && pwd)"; LOG="$AMP/sim/a4b_loop.log"; : > "$LOG"
for c in typical:-40 typical:27 typical:85 ff:-40 ff:27 ff:85 ss:-40 ss:27 ss:85; do k=${c%%:*}; T=${c##*:}
  echo "### loop_${k}_$T" >> "$LOG"
  taskset -c ${LOOPCORE:-7} bash "$AMP/scripts/ngrun.sh" tb_afe_1ch_loop.spice $k $T 2>&1 | cut -c1-200 | grep -E '^RESULT|rror' >> "$LOG"
done
echo "wrote sim/a4b_loop.log"
