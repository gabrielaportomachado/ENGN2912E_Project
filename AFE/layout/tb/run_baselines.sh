#!/bin/bash
# run_baselines.sh (LP kit): (re)creates the committed pre-layout baselines AFE/layout/baseline/*.json by running every golden testbench on the SCHEMATIC netlists at the corners its phase
# prompt names.  usage: bash AFE/layout/tb/run_baselines.sh [amp|adc|top|all]   (amp about 10 min, adc about 30 min, top about 60 min on the LP machine; heavy jobs go through the job slots)
# Run it again only if a design netlist changed (then say so in the phase findings: the baselines are the reference that ACCEPT.md limits are judged against).
T="$(cd "$(dirname "$0")" && pwd)"; W="${1:-all}"; cd "$T/../../.." || exit 2
run(){ echo "### $*"; python3 "$@" 2>&1 | grep -E "^RESULT|^ERROR|^WARNING|Traceback|Error" ; }
if [ "$W" = amp ] || [ "$W" = all ]; then
  for c in amp_ac amp_noise amp_psrr amp_thd amp_loop amp_pwrup amp_reset; do run AFE/layout/tb/tb_$c.py --corner all; done
  for c in amp_ac amp_noise amp_psrr amp_thd amp_pwrup amp_reset; do run AFE/layout/tb/tb_$c.py --corner all --junction; done     # junction convention for the pseudo-resistor devices (LP finding; ACCEPT.md section 2)
  run AFE/layout/tb/tb_amp_reset.py --corner all --os 10m,100m --host-rst 0.1                # record start with the host's RST_AMP pulse (ACCEPT.md record-start rule)
  run AFE/layout/tb/tb_amp_reset.py --corner all --os 10m,100m --host-rst 0.1 --junction
  run AFE/layout/tb/tb_bias_startup.py --corner all
  run AFE/layout/tb/tb_tgate.py --corner all
fi
if [ "$W" = adc ] || [ "$W" = all ]; then
  for c in $(ls AFE/layout/tb/tb_adc_*.py 2>/dev/null); do run $c --corner all; done
fi
if [ "$W" = top ] || [ "$W" = all ]; then
  run AFE/layout/tb/tb_top_pwrup8.py --corner all
  run AFE/layout/tb/tb_top_stim.py --corner all
  run AFE/layout/tb/tb_top_xtalk.py --corner typ
  run AFE/layout/tb/tb_top_e2e.py --corner all
  run AFE/layout/tb/tb_top_supply.py --corner typ --corner ff-40
fi
echo "### baselines in AFE/layout/baseline: $(ls AFE/layout/baseline/*.json 2>/dev/null | wc -l) files"
