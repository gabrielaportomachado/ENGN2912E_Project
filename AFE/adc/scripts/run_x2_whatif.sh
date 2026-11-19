#!/bin/bash
# X2 what-if runs for the PROPOSALS (testbench .param overrides only; the design netlists are not touched): transfer step at the 1536 and 2048 code boundaries, ADC alone.  -> sim/x2_inl_step.log
ADC="$(cd "$(dirname "$0")/.." && pwd)"; cd "$ADC"; export X2_YIELD=1.5
for ck in typ ff85; do
  python3 scripts/x2_inl_step.py $ck "design (drivers 1u/2u, pair 80u)" 1536
  python3 scripts/x2_inl_step.py $ck "design (drivers 1u/2u, pair 80u)" 2048
  X2_EXTRA=".param DSW_WN=4u DSW_WP=8u" python3 scripts/x2_inl_step.py $ck "drivers x4 (4u/8u)" 1536
  X2_EXTRA=".param DSW_WN=1u DSW_WP=3u" python3 scripts/x2_inl_step.py $ck "PMOS driver 3u (Ron closer to the NMOS)" 1536
  X2_EXTRA=".param CMP_WP=20u" X2_OFF=$( [ $ck = typ ] && echo 12 || echo 16 ) python3 scripts/x2_inl_step.py $ck "comparator pair 20u (D2 option)" 1536
done
echo "$(date '+%F %T') x2_whatif done" >> "$ADC/sim/x2_done.txt"
