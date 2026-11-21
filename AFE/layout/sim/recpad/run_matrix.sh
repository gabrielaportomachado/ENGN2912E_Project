#!/bin/bash
# run_matrix.sh (REVIEW.md R13): the golden amplifier testbenches of L2b (typ / ff85 / ss-40) with a REC pad model on the amplifier input.
#   usage: bash AFE/layout/sim/recpad/run_matrix.sh <sch|pex> <model name> [<out dir name>]
#     sch / pex : schematic, or the L2b post-layout netlist AFE/layout/sim/flow/amp_ch.pex.spice
#     model name: open | probe | open_rs10k | open_rs100k | probe_rs10k ... = AFE/layout/sim/recpad/models/pad_<name>.spice ;  none = no pad (reference run, same tool state)
#     out dir   : default <sch|pex>_<model name>  under AFE/layout/sim/recpad/
# The commands are those of AFE/layout/reports/L2b.md section 3 (design convention, then --junction for ac / pwrup / reset-host) plus --rec-load.
set -u
cd "$(dirname "$0")/../../../.."          # repo root of this checkout
NET=$1; MOD=$2
OUT=AFE/layout/sim/recpad/${3:-${NET}_${MOD}}
mkdir -p "$OUT"
if [ "$NET" = pex ]; then NL=AFE/layout/sim/flow/amp_ch.pex.spice; else NL=schematic; fi
if [ "$MOD" = none ]; then RL=""; else RL="--rec-load AFE/layout/sim/recpad/models/pad_$MOD.spice"; fi
TB=AFE/layout/tb
run() { echo "### $(date +%H:%M:%S) $*" >> "$OUT/run.log"; python3 "$@" --netlist "$NL" --corner all $RL --out "$OUT" >> "$OUT/run.log" 2>&1 || echo "### FAILED exit $? : $*" >> "$OUT/run.log"; }
: > "$OUT/run.log"
for t in amp_ac amp_noise amp_psrr amp_thd amp_loop amp_pwrup amp_reset; do run $TB/tb_$t.py; done
run $TB/tb_amp_reset.py --os 10m,100m --host-rst 0.1
run $TB/tb_amp_ac.py --junction
run $TB/tb_amp_pwrup.py --junction
run $TB/tb_amp_reset.py --junction --os 10m,100m --host-rst 0.1
echo "### $(date +%H:%M:%S) DONE $NET $MOD" >> "$OUT/run.log"
