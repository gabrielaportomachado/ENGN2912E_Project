#!/bin/bash
# usage: bash run_pseudoR.sh   -> sim/char_pseudoR.csv (R at 0 V and large-signal R at +/-100 mV)
# Columns: corner temp_C W L vt_V r0_ohm r_plus100mV r_minus100mV i_plus100mV_A i_minus100mV_A
cd "$(dirname "$0")/../tb" || exit 1
out=../sim/char_pseudoR.csv
echo "corner temp_C W L vt_V r0_ohm r_p100mV_ohm r_m100mV_ohm i_p100mV_A i_m100mV_A" > $out
for c in typical ff ss; do for T in -40 27 85; do for LL in 2u 4u; do for V in -0.3 -0.2 -0.1 0 0.1 0.2 0.3; do
  sed -e "s#models_typical#models_$c#; s#^\.temp .*#.temp $T#; s#^\.param WW=.*#.param WW=1u LL=$LL VTT=$V#" \
      -e 's#\.\./spice/#'"$PWD"'/../spice/#' -e 's#\.\./sim/#/tmp/#' char_pseudoR.spice > /tmp/pr.spice
  r=$(timeout 120 ngspice -b /tmp/pr.spice 2>&1 | grep '^RESULT')
  echo "$c $T 1u $LL $V ${r#RESULT }" >> $out
done; done; done; done
