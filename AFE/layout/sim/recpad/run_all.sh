#!/bin/bash
# run_all.sh (REVIEW.md R13): the whole simulation set, ONE job chain (never start two chains at once: tb_*.py hold a job slot while they wait for the next one, three chains deadlock).
#   bash AFE/layout/sim/recpad/run_all.sh        -> AFE/layout/sim/recpad/{pex,sch}_{open,probe}/ (L2b golden set with the pad), leak/, park_*/, recac_*/ (r13_extra.py), run_all.log
#   the pex_open matrix is run by `bash AFE/layout/sim/recpad/run_matrix.sh pex open` (done first, 7.5 min); the what-if series resistors: run_whatif.sh
set -u
cd "$(dirname "$0")/../../../.."
M=AFE/layout/sim/recpad/models
X="python3 AFE/layout/sim/recpad/r13_extra.py"
LOG=AFE/layout/sim/recpad/run_all.log
echo "### $(date +%H:%M:%S) start" >> $LOG
for c in "pex probe" "sch open" "sch probe"; do set -- $c; bash AFE/layout/sim/recpad/run_matrix.sh $1 $2; echo "### $(date +%H:%M:%S) matrix $1 $2 done" >> $LOG; done
$X leak --corner all --rec-load $M/pad_open.spice --out AFE/layout/sim/recpad/leak >> $LOG 2>&1
for n in pex sch; do
  if [ $n = pex ]; then NL=AFE/layout/sim/flow/amp_ch.pex.spice; else NL=schematic; fi
  $X park  --netlist $NL --corner all --out AFE/layout/sim/recpad/${n}_park_nopad >> $LOG 2>&1
  $X recac --netlist $NL --corner all --out AFE/layout/sim/recpad/${n}_recac_nopad >> $LOG 2>&1
  for e in open probe; do
    $X park  --netlist $NL --corner all --rec-load $M/pad_$e.spice --out AFE/layout/sim/recpad/${n}_park_$e >> $LOG 2>&1
    $X recac --netlist $NL --corner all --rec-load $M/pad_$e.spice --out AFE/layout/sim/recpad/${n}_recac_$e >> $LOG 2>&1
  done
done
echo "### $(date +%H:%M:%S) DONE" >> $LOG
