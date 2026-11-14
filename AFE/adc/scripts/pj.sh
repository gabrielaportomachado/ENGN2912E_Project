#!/bin/bash
# usage: <list of command lines on stdin> | bash pj.sh   -> runs them in parallel on nproc-1 cores, one core each (ngspice -b ignores num_threads; taskset works)
# GNU parallel temp files go to sim/.ptmp (not the small /tmp); refuses to start with < 5 GB free on /foss/designs.
D="$(cd "$(dirname "$0")/.." && pwd)"; mkdir -p "$D/sim/.ptmp"
FREE=$(df -Pk "$D" | awk 'NR==2{print int($4/1048576)}'); [ "$FREE" -lt 5 ] && { echo "STOP: only ${FREE} GB free" >&2; exit 1; }
NC=$(( $(nproc --all) - 1 ))
parallel --tmpdir "$D/sim/.ptmp" -j $NC 'taskset -c $(( ({%} - 1) % '$NC' )) bash -c {}'
