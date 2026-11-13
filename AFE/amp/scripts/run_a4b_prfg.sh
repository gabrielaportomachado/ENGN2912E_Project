#!/bin/bash
# A4b: small-signal R0 of the fixed-gate pseudo-resistor (tb/char_pseudoR_fg.spice, SW=0 = fast-settle switch absent) at larger gate offsets VTT, node DC 1.65 V, 9 PVT -> sim/a4b_prfg.csv
# (VTT2 decision: the stage-2 gate offset must keep R0 on the model floor, otherwise f_lo and the noise change).
AMP="$(cd "$(dirname "$0")/.." && pwd)"; RUN=/tmp/a4bprfg; rm -rf $RUN; mkdir -p $RUN
COMBOS="typical:-40 typical:27 typical:85 ff:-40 ff:27 ff:85 ss:-40 ss:27 ss:85"
one() { c=$1; T=$2; VC=$3; V=$4; lo=$(awk -v v=$VC 'BEGIN{printf "%.2f",v-0.1}'); hi=$(awk -v v=$VC 'BEGIN{printf "%.2f",v+0.1}')
  f=$(mktemp /tmp/prfg_XXXXXX.spice)
  sed -e "s#models_typical#models_$c#; s#^\.temp .*#.temp $T#; s#^\.param WW=.*#.param WW=1u LL=2u VTT=$V SW=0 VCM=$VC PWTG=1u#; s#SWEEPLO#$lo#; s#SWEEPHI#$hi#" -e 's#\.\./spice/#'"$AMP"'/spice/#' "$AMP/tb/char_pseudoR_fg.spice" > $f
  r=$(cd $AMP/tb && taskset -c $5 timeout 250 ngspice -b $f 2>&1 | grep '^RESULT'); rm -f $f
  echo "$c $T $VC $V 0 ${r#RESULT }" > "$RUN/${c}_${T}_${VC}_${V}.txt"; }
export -f one; export AMP RUN
i=0; for c in $COMBOS; do k=${c%%:*}; T=${c##*:}; for V in 0.2 0.6 0.9 1.2; do echo "one $k $T 1.65 $V $((i%8))"; i=$((i+1)); done; done | parallel -j 8
{ echo "corner temp_C VCM_V VTT_V SW r0_ohm r_p100mV_ohm r_m100mV_ohm i_p100mV_A i_m100mV_A"; cat $RUN/*.txt | sort -k1,1 -k4,4n -k2,2n; } > "$AMP/sim/a4b_prfg.csv"; echo wrote sim/a4b_prfg.csv
