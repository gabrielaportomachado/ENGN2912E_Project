#!/bin/bash
# usage: bash dgrun.sh <tb.spice (in tb/)> <corner> <tempC> [NAME=VALUE ...]   (D1 driver, derived from AFE/amp/scripts/ngrun.sh)
# Copies the testbench to /tmp, swaps models_typical -> models_<corner>, sets .temp, rewrites ".param NAME=VALUE" lines (also in the included comparator_params file via a later .param),
# replaces @OUT@ with $OUT, then runs ngspice -b from tb/ (relative ../spice ../sim paths work).  SEED=<n> adds ".options seed=n" (Monte Carlo).
ADC="$(cd "$(dirname "$0")/.." && pwd)"
tb=$1; corner=$2; T=$3; shift 3
tmp=$(mktemp /tmp/d1_XXXXXXXX.spice)
sed -e "s#models_typical#models_${corner}#g" -e "s#^\.temp .*#.temp ${T}#" "$ADC/tb/$tb" > "$tmp"
[ -n "$OUT" ] && sed -i "s#@OUT@#${OUT}#g" "$tmp"
sed -i "s#@CELL@#${CELL:-cmp_p}#g" "$tmp"
[ -n "$SEED" ] && sed -i "s#^\.temp .*#&\n.options seed=${SEED}#" "$tmp"
for pr in $SWAPS; do sed -i "s#${pr%%=*}#${pr#*=}#g" "$tmp"; done
for kv in "$@"; do
  n=${kv%%=*}; v=${kv#*=}
  if grep -q -E "^\.param ${n}=" "$tmp"; then sed -i -E "s#^(\.param ${n}=)[^ ]*#\1${v}#" "$tmp"
  else sed -i -E "s#^(\.temp .*)\$#\1\n.param ${n}=${v}#" "$tmp"; fi
done
# F1 / Decision 43a: the output is NOT cut to 300 columns any more (ngspice writes its progress values and the abort message on ONE carriage-return separated line;
# `cut` kept the first progress values and lost the abort: the D5 "28.8 ms" artifact).  Carriage returns become newlines so that the "doAnalyses:" line stands alone.
cd "$ADC/tb" && timeout "${TMO:-1800}" ngspice -b "$tmp" 2>&1 | tr '\r' '\n'
rm -f "$tmp"
