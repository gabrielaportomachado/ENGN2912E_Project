#!/bin/bash
# slot.sh: run ONE heavy job (ngspice, magic, klayout DRC, LibreLane / OpenROAD) in one of N machine-wide slots (common rule 4: at most 3 heavy jobs in parallel on an 8 GB machine).
# usage: bash AFE/layout/scripts/slot.sh <command> [args...]      (blocks until a slot is free, then runs the command and returns its exit code)
#        AFE_SLOTS=2 bash slot.sh ...                             (another limit; default 3)
# Works across shells, sessions and background jobs of this machine: the slots are lock files in /tmp/afe_slots (flock); a killed job frees its slot automatically.
N="${AFE_SLOTS:-3}"; D="${AFE_SLOT_DIR:-/tmp/afe_slots}"; mkdir -p "$D" 2>/dev/null
[ $# -ge 1 ] || { echo "usage: slot.sh <command> [args...]" >&2; exit 2; }
while :; do
  for i in $(seq 1 "$N"); do
    exec {fd}>"$D/slot$i.lock" || exit 2
    if flock -n "$fd"; then "$@"; exit $?; fi
    exec {fd}>&-
  done
  sleep 2
done
