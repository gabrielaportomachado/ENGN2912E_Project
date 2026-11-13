#!/bin/bash
# A4b priority 1: why the fast-settle release leaves stage 1 at a rail, and which cheap fixes work.  typical 27 C, fs pulse alone (no offset, no signal) at t0 = 10 ms, 12 s window.
#   short   : pulse widths 100 ns .. 3 us (the closed switch makes OTA1 a unity-gain follower; it oscillates from ~1.5 us on: see sim/a4b_fsfix.log)
#   edge    : 10 us pulse with slow edges (FS_TR 0.1 / 1 / 3 us)
#   rfs     : 100 us pulse, IDEAL series resistor RFS in the fast-settle path (EXPERIMENT: makes the loop stable if RFS >~ 20 MOhm)
# usage: bash scripts/run_a4b_fsfix.sh [corner T]   -> /tmp/a4brun/fsfix/<label>.csv ; analysis: python3 scripts/a4b_analyze.py fsfix
AMP="$(cd "$(dirname "$0")/.." && pwd)"; RUN=/tmp/a4brun/fsfix; mkdir -p $RUN
c=${1:-typical}; T=${2:-27}; NC=$(( $(nproc --all) - 1 )); export OMP_NUM_THREADS=1
one() { lab=$1; shift; OUT=$RUN/$lab.csv bash "$AMP/scripts/ngrun.sh" tb_afe_1ch_tran.spice $CC $TT FS_EN=1 FS_T0=0.01 TSTEP=${TS:-1n} TMAXS=1m TSTOP=12 "$@" > $RUN/$lab.log 2>&1; }
export -f one; export AMP RUN CC=$c TT=$T TS
{ if [ -z "$ONLY" ]; then for w in 100n 300n 1u 3u; do echo "one short_w$w FS_W=$w FS_TR=10n"; done
  for tr in 100n 1u 3u; do echo "one edge_tr$tr FS_W=10u FS_TR=$tr"; done; fi
  for r in 1M 10M 30M 100M; do echo "SWAPS=../spice/pseudoR.spice=/tmp/a4b/pseudoR_rfs.spice one rfs_$r FS_W=100u FS_TR=10n RFS=$r"; done; } |
  parallel -j $NC 'taskset -c $(( ({%} - 1) % '$NC' )) bash -c {}'
