#!/bin/bash
# run_ctl_nodiodes.sh (REVIEW.md R13): re-run of the last control of run_whatif.sh (the whatif chain was cut during it): the same pad capacitances WITHOUT the ESD diodes, extracted amp_ch.
set -u
cd "$(dirname "$0")/../../../.."
O=AFE/layout/sim/recpad/pex_check_nodiodes; rm -rf $O; mkdir -p $O
M=AFE/layout/sim/recpad/models/pad_check_nodiodes.spice; N=AFE/layout/sim/flow/amp_ch.pex.spice
for a in "" "--os 10m,100m --host-rst 0.1"; do
  python3 AFE/layout/tb/tb_amp_reset.py --netlist $N --corner all --rec-load $M --out $O $a >> $O/run.log 2>&1
done
python3 AFE/layout/tb/tb_amp_pwrup.py --netlist $N --corner all --rec-load $M --out $O >> $O/run.log 2>&1
echo "### $(date +%H:%M:%S) DONE" >> $O/run.log
