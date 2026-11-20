#!/bin/bash
# drc_dig.sh (LP step 5 / L1d): official gf180mcu KLayout DRC, variant D (5 metals, 11 kA top metal, MIM option B), on the hardened afe_dig GDS.  The LibreLane flow skips this
# step for gf180mcuD (KLAYOUT_DRC_RUNSET is unset in the PDK configuration), so it is run here.
# usage: bash AFE/dig/scripts/drc_dig.sh [<gds>]     default: the GDS of the run named in AFE/dig/trial/run_dir.txt  ->  AFE/dig/reports/klayout_drc.log (summary; PASS = 0 violations)
#   env AFE_DIG_RUN = scratch root (default /tmp/lp_dig); the .lyrdb databases stay in $AFE_DIG_RUN/drc
set -u
D="$(cd "$(dirname "$0")/.." && pwd)"; AFE="$(cd "$D/.." && pwd)"; RUN="${AFE_DIG_RUN:-/tmp/lp_dig}"
GDS="${1:-$(sed -n 's/.*): \(.*\)$/\1/p' "$D/trial/run_dir.txt" | head -1)/final/gds/afe_dig.gds}"
[ -f "$GDS" ] || { echo "STOP: no GDS at $GDS (run bash AFE/dig/run_dig.sh first)" >&2; exit 1; }
DECK=/foss/pdks/gf180mcuD/libs.tech/klayout/tech/drc/run_drc.py
O="$RUN/drc"; rm -rf "$O"; mkdir -p "$O" "$D/reports"
CMD="python3 $DECK --path=$GDS --variant=D --topcell=afe_dig --run_dir=$O --run_mode=flat --mp=1"
echo "drc_dig: $CMD"
bash "$AFE/layout/scripts/slot.sh" /usr/bin/time -v -o "$O/time.txt" $CMD > "$O/run_drc.log" 2>&1 &
pid=$!; wait $pid; rc=$?
{
  echo "KLayout DRC of afe_dig, official gf180mcu deck (libs.tech/klayout/tech/drc/run_drc.py), variant D.  $(date '+%F %T')"
  echo "command: $CMD"
  echo "GDS: $GDS ($(stat -c %s "$GDS") bytes)   klayout: $(klayout -v 2>&1 | head -1)"
  echo "exit code $rc; wall $(grep 'Elapsed (wall clock)' "$O/time.txt" | sed 's/.*): //'); peak RSS $(grep 'Maximum resident' "$O/time.txt" | awk '{printf "%.0f MB", $NF/1024}'); run directory $(du -sm "$O" | cut -f1) MB"
  echo "tables run: $(ls "$O"/*.lyrdb 2>/dev/null | wc -l) report databases: $(ls "$O"/*.lyrdb 2>/dev/null | xargs -n1 basename 2>/dev/null | sed 's/\.lyrdb//' | tr '\n' ' ')"
  python3 "$D/scripts/lyrdb_count.py" "$O"
} > "$D/reports/klayout_drc.log"
n=$(grep '^TOTAL' "$D/reports/klayout_drc.log" | awk '{print $2}'); nf=$(ls "$O"/*.lyrdb 2>/dev/null | wc -l)
if [ "$rc" = 0 ] && [ "$nf" -gt 0 ] && [ "$n" = 0 ]; then echo "RESULT KLayout DRC variant D: PASS (0 violations)" >> "$D/reports/klayout_drc.log"; else echo "RESULT KLayout DRC variant D: FAIL ($n violations, exit code $rc, $nf databases)" >> "$D/reports/klayout_drc.log"; fi
cat "$D/reports/klayout_drc.log"
