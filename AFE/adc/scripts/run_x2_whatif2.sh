#!/bin/bash
# X2 what-if runs, part 2 (testbench .param overrides only): the items of run_x2_whatif.sh that were lost to a library edit during the run, plus the 2048 boundary and a x2 driver.  -> sim/x2_inl_step.log
ADC="$(cd "$(dirname "$0")/.." && pwd)"; cd "$ADC"; export X2_YIELD=1.5
X2_EXTRA=".param DSW_WN=1u DSW_WP=3u" python3 scripts/x2_inl_step.py typ "PMOS driver 3u (Ron closer to the NMOS)" 1536
X2_EXTRA=".param CMP_WP=20u" X2_OFF=12 python3 scripts/x2_inl_step.py typ "comparator pair 20u (D2 option)" 1536
python3 scripts/x2_inl_step.py ff85 "design (drivers 1u/2u, pair 80u)" 1536
python3 scripts/x2_inl_step.py ff85 "design (drivers 1u/2u, pair 80u)" 2048
X2_EXTRA=".param DSW_WN=4u DSW_WP=8u" X2_OFF=13 python3 scripts/x2_inl_step.py typ "drivers x4 (4u/8u)" 2048
X2_EXTRA=".param DSW_WN=2u DSW_WP=4u" X2_OFF=21 python3 scripts/x2_inl_step.py typ "drivers x2 (2u/4u)" 1536
X2_EXTRA=".param DSW_WN=4u DSW_WP=8u" X2_OFF=13 python3 scripts/x2_adc.py typ 12
echo "$(date '+%F %T') x2_whatif2 done" >> "$ADC/sim/x2_done.txt"
