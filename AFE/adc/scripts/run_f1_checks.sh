#!/bin/bash
# F1 (2026-11-20): the ADC replays that check the F1 netlist changes.  usage: bash scripts/run_f1_checks.sh [adc|steps|s4|all]   (from anywhere; needs AFE/layout/lvs/adc_ch.spice for `steps`)
#   adc   : ADC alone, closed loop, typ 12 inputs + ff85 8 inputs -> sim/f1_x2_adc.log (appended), then scripts/f1_x2_compare.py -> sim/f1_x2_compare.log (codes against sim/x2_adc.log)
#   steps : transfer steps at codes 1536 / 2048 for the design, for Cxa = 54.52 fF (the value of one 5 x 5 um MIM unit, AUDIT 4.9.3 rule 3), without Cpb / Cpm, and for the cells of the
#           LVS reference (which also carry no diffusion parameters) -> sim/f1_x2_inl_step.log (appended)
#   s4    : the 8-ADC supply run, typ, full-scale case, 3 MHz -> sim/f1_x2_s4_typ.log, sim/f1_x2_s4_summary.log (against sim/x2_s4_summary.log line 2)
# One ngspice thread per job, at most 3 jobs at a time (x2lib); nothing is piped through cut.
ADC="$(cd "$(dirname "$0")/.." && pwd)"; cd "$ADC"; what=${1:-all}
L="$ADC/../layout/lvs/adc_ch.spice"
if [ "$what" = adc ] || [ "$what" = all ]; then
  export X2_ADC_LOG="$ADC/sim/f1_x2_adc.log"
  echo "# ===== F1 run_f1_checks.sh $(date +%F): x2_adc.py typ 12 (design netlists as they are).  Baseline = first block of sim/x2_adc.log" >> "$X2_ADC_LOG"
  python3 scripts/x2_adc.py typ 12 > /dev/null
  echo "# ===== F1 run_f1_checks.sh $(date +%F): x2_adc.py ff85 at the 8 inputs of the X2 block 'ff85 cref' (line 114 of sim/x2_adc.log)" >> "$X2_ADC_LOG"
  python3 scripts/x2_adc.py ff85 1.7503,1.8507,1.9011,1.9512,2.0006,2.0509,2.1004,2.1507 > /dev/null
  unset X2_ADC_LOG
  python3 scripts/f1_x2_compare.py | grep -E 'RUN|inputs x|RESULT'
fi
if [ "$what" = steps ] || [ "$what" = all ]; then
  export X2_INLSTEP_LOG="$ADC/sim/f1_x2_inl_step.log"
  for B in 1536 2048; do
    python3 scripts/x2_inl_step.py typ "F1 re-run of the design (netlists after F1 items 1 and 3)" $B
    X2_EXTRA='.param CMP_CA=54.52f' X2_OFF=28.6 python3 scripts/x2_inl_step.py typ "F1 what-if (inputs re-centred): design netlists, Cxa 54.52 fF ideal" $B
    X2_EXTRA='.param CMP_CA=54.52f' X2_OFF=38.8 python3 scripts/x2_inl_step.py ff85 "F1 what-if: design netlists, Cxa 54.52 fF ideal" $B
    X2_EXTRA='.param CMP_CA=54.52f DSW_CPAR=1e-21' X2_OFF=28.6 python3 scripts/x2_inl_step.py typ "F1 what-if: design netlists, Cxa 54.52 fF ideal AND the 14 x 2 fF Cpb / Cpm removed" $B
    X2_ADC_INC=$L X2_OFF=32.3 python3 scripts/x2_inl_step.py typ "F1: LVS reference cells (Cxa = 5 x 5 um MIM unit, no Cpb / Cpm)" $B
    X2_ADC_INC=$L X2_OFF=43.5 python3 scripts/x2_inl_step.py ff85 "F1: LVS reference cells (Cxa = 5 x 5 um MIM unit, no Cpb / Cpm)" $B
  done
fi
if [ "$what" = s4 ] || [ "$what" = all ]; then
  X2_LOG_PREFIX=f1_x2 python3 scripts/x2_s4.py typ fs 3 | grep RESULT
fi
