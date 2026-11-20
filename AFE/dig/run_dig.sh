#!/bin/bash
# run_dig.sh (LP step 5 / L1d): harden the digital macro afe_dig with LibreLane and collect what is committed.
# usage: bash AFE/dig/run_dig.sh [tag] [mk_dig_cfg options, e.g. --clock cts --h 101.92]     (default tag: trial; default clock: buf = Decision 44h)
#   env AFE_DIG_RUN  = scratch root for the run directory (default /tmp/lp_dig; NEVER inside the repo: /foss/designs is the small host disk)
#   env AFE_DIG_KEEP = 1: keep an existing run directory of the same tag and resume with `--last-run`-style behaviour is NOT supported by this script: see "crash recovery" below
# Steps: (1) mk_dig_cfg.py -> config.json, afe_dig_template.def, pins_plan.json   (2) LibreLane Classic flow in $AFE_DIG_RUN/design/runs/<tag>, through slot.sh (one heavy job)
#        (3) scripts/collect_dig.py -> AFE/dig/reports/ (metrics, STA summary, logs) and AFE/dig/trial/ (powered netlist, netlist, LEF, SDC, SPEF nom, SDF, pin table, GDS path note)
# Crash recovery: the flow takes about 2 minutes; if it dies, just run this script again (the run directory of the tag is removed first).  To look at a failed run: $AFE_DIG_RUN/librelane_<tag>.log,
#        $AFE_DIG_RUN/design/runs/<tag>/error.log and the numbered step directories.
set -u
D="$(cd "$(dirname "$0")" && pwd)"; AFE="$(cd "$D/.." && pwd)"
RUN="${AFE_DIG_RUN:-/tmp/lp_dig}"; TAG="${1:-trial}"; [ $# -ge 1 ] && shift
case "$RUN" in "$AFE"*|/foss/designs/*) echo "STOP: AFE_DIG_RUN=$RUN is on the host disk; use a directory outside /foss/designs" >&2; exit 1;; esac
mkdir -p "$RUN/design" || exit 1
FREE=$(df -Pk "$RUN" | awk 'NR==2{print int($4/1048576)}'); [ "$FREE" -lt 2 ] && { echo "STOP: only ${FREE} GB free in $RUN (need 2 GB)" >&2; exit 1; }
python3 "$D/mk_dig_cfg.py" "$@" || exit 1
# LibreLane puts runs/ next to the config file: use a copy of the config with absolute source paths in the scratch directory
sed "s#dir::#$D/#g" "$D/config.json" > "$RUN/design/config.json"
cd "$RUN/design" || exit 1
rm -rf "runs/$TAG"
echo "run_dig: LibreLane run $TAG in $RUN/design/runs/$TAG (log $RUN/librelane_$TAG.log)"
bash "$AFE/layout/scripts/slot.sh" /usr/bin/time -v -o "$RUN/time_$TAG.txt" librelane --run-tag "$TAG" config.json > "$RUN/librelane_$TAG.log" 2>&1 &
pid=$!; wait $pid; rc=$?
echo "run_dig: librelane exit $rc; wall $(grep 'Elapsed (wall clock)' "$RUN/time_$TAG.txt" | sed 's/.*): //'); peak RSS $(grep 'Maximum resident' "$RUN/time_$TAG.txt" | awk '{printf "%.0f MB", $NF/1024}'); run dir $(du -sh "runs/$TAG" | cut -f1)"
[ -f "runs/$TAG/error.log" ] && [ -s "runs/$TAG/error.log" ] && { echo "run_dig: error.log:"; head -20 "runs/$TAG/error.log"; }
if [ $rc -ne 0 ] || [ ! -d "runs/$TAG/final" ]; then echo "run_dig: FLOW FAILED (no final/ views): nothing collected" >&2; exit 1; fi
python3 "$D/scripts/collect_dig.py" "$RUN/design/runs/$TAG" "$RUN/librelane_$TAG.log" "$RUN/time_$TAG.txt"
