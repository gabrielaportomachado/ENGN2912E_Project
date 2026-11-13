#!/bin/bash
# usage: bash ngrun.sh <tb.spice (in tb/)> <corner> <tempC> [NAME=VALUE ...]
# Copies the testbench to /tmp, swaps the model include (models_<corner>), the .temp line and any
# ".param NAME=VALUE" lines (one parameter per line in the tb), then runs ngspice -b from the tb/ directory
# (relative ../spice ../sim paths keep working). Prints ngspice stdout+stderr.
AMP="$(cd "$(dirname "$0")/.." && pwd)"
tb=$1; corner=$2; T=$3; shift 3
tmp=$(mktemp /tmp/a3_XXXXXXXX.spice)
sed -e "s#models_typical#models_${corner}#g" -e "s#^\.temp .*#.temp ${T}#" "$AMP/tb/$tb" > "$tmp"
# OTA_NETLIST=<path relative to tb/> swaps the hand-written ota1.spice for another netlist (xschem equivalence check)
[ -n "$OTA_NETLIST" ] && sed -i "s#\.\./spice/ota1\.spice#${OTA_NETLIST}#" "$tmp"
# SWAPS="old=new old2=new2": replace include paths (xschem equivalence runs), e.g. ../spice/ota2.spice=../xschem/netlist/ota2_sub.spice
# EXTRAOPT="reltol=1e-7 vntol=1e-9": extra .options tokens appended to the testbench options line (tight tolerances for the equivalence runs)
[ -n "$EXTRAOPT" ] && sed -i "s#^\.options .*#& $EXTRAOPT#" "$tmp"
[ -n "$OUT" ] && sed -i "s#@OUT@#${OUT}#g" "$tmp"   # OUT=<csv path>: replaces the token @OUT@ (tran testbenches that wrdata)
for pr in $SWAPS; do sed -i "s#${pr%%=*}#${pr#*=}#g" "$tmp"; done
for kv in "$@"; do
  n=${kv%%=*}; v=${kv#*=}
  if grep -q -E "^\.param ${n}=" "$tmp"; then
    sed -i -E "s#^(\.param ${n}=)[^ ]*#\1${v}#" "$tmp"
  else   # defined in an included file (e.g. ota1_params.spice): a later .param overrides it
    sed -i -E "s#^(\.temp .*)\$#\1\n.param ${n}=${v}#" "$tmp"
  fi
done
cd "$AMP/tb" && timeout "${TMO:-900}" ngspice -b "$tmp" 2>&1
rm -f "$tmp"
