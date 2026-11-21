#!/bin/bash
# run_whatif.sh (REVIEW.md R13 items 3c / 4): second job chain (start it only when run_all.sh is finished).
#   controls for the long reset transients (1 fF, capacitance without diodes), what-ifs for the 10 MOhm probe finding (100 MOhm / AC-coupled probe, 100 kOhm series resistor),
#   DC leakage what-ifs (1 nA, 10 nA from VDD into rec), all on the extracted amp_ch.
set -u
cd "$(dirname "$0")/../../../.."
LOG=AFE/layout/sim/recpad/run_whatif.log
echo "### $(date +%H:%M:%S) start" >> $LOG
for m in probe_100M probe_ac probe_rs100k leak_1n leak_10n; do bash AFE/layout/sim/recpad/run_matrix.sh pex $m; echo "### $(date +%H:%M:%S) matrix pex $m done" >> $LOG; done
for m in ctl_1f check_nodiodes; do
  O=AFE/layout/sim/recpad/pex_$m; mkdir -p $O
  for a in "" "--os 10m,100m --host-rst 0.1"; do
    python3 AFE/layout/tb/tb_amp_reset.py --netlist AFE/layout/sim/flow/amp_ch.pex.spice --corner all --rec-load AFE/layout/sim/recpad/models/pad_$m.spice --out $O $a >> $O/run.log 2>&1
  done
  python3 AFE/layout/tb/tb_amp_pwrup.py --netlist AFE/layout/sim/flow/amp_ch.pex.spice --corner all --rec-load AFE/layout/sim/recpad/models/pad_$m.spice --out $O >> $O/run.log 2>&1
  echo "### $(date +%H:%M:%S) control $m done" >> $LOG
done
echo "### $(date +%H:%M:%S) DONE" >> $LOG
