#!/bin/bash
# run_noisecheck.sh (REVIEW.md R13): checks lptb.rec_patch's replacement of ngspice's onoise_total (nan as soon as a PDK diode is in the circuit, ngspice 46) in the noise bench (tb_amp_noise.py).
# A pad WITHOUT diodes (pad_check_nodiodes.spice = 2.87 pF on rec) keeps onoise_total finite: the integral of the spectrum (vo) must equal the simulator's own total (vo_ng).
# Third chain (start it only when no other chain runs). Output: noise_check/ (amp_noise logs) ; noise_check.md is written by hand from them.
set -u
cd "$(dirname "$0")/../../../.."
O=AFE/layout/sim/recpad/noise_check; rm -rf $O; mkdir -p $O
python3 AFE/layout/tb/tb_amp_noise.py --netlist schematic --corner typ --rec-load AFE/layout/sim/recpad/models/pad_check_nodiodes.spice --out $O >> $O/run.log 2>&1
echo "### $(date +%H:%M:%S) DONE" >> $O/run.log
# the 1 GOhm probe what-if (the board-rule candidate: FET probe), same matrix as the other what-ifs
bash AFE/layout/sim/recpad/run_matrix.sh pex probe_1G
echo "### $(date +%H:%M:%S) matrix pex probe_1G done" >> AFE/layout/sim/recpad/run_whatif.log
