#!/bin/bash
# usage: bash run_pseudoR_iv.sh -> sim/char_pseudoR_iv.csv  (full +/-100 mV I-V, L=2u, vt=0, per corner/temp)
cd "$(dirname "$0")/../tb" || exit 1
out=../sim/char_pseudoR_iv.csv; echo "corner temp_C V_mV I_A" > $out
for c in typical ff ss; do for T in -40 27 85; do
  sed -e "s#models_typical#models_$c#; s#^\.temp .*#.temp $T#" -e 's#\.\./spice/#'"$PWD"'/../spice/#' -e 's#\.\./sim/#/tmp/#' char_pseudoR.spice > /tmp/pr.spice
  ngspice -b /tmp/pr.spice >/dev/null 2>&1
  awk -v c=$c -v T=$T '{printf "%s %s %.1f %s\n",c,T,($1-1.65)*1000,$2}' /tmp/char_pseudoR_iv_tmp.csv >> $out
done; done
