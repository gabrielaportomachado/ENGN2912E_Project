#!/bin/bash
# A4c: normal-state R0 of the pseudo-resistor pair versus device size (W L), VTT = 0.2 (stage 1) and 0.9 (stage 2), node DC 1.65 V, 9 PVT -> sim/a4c_prsize.csv (tb/char_pseudoR_fg.spice, SW=0)
AMP="$(cd "$(dirname "$0")/.." && pwd)"; RUN=/tmp/a4cprsz; rm -rf $RUN; mkdir -p $RUN
COMBOS="typical:-40 typical:27 typical:85 ff:-40 ff:27 ff:85 ss:-40 ss:27 ss:85"
one() { c=$1; T=$2; W=$3; L=$4; V=$5; id=$6; core=$7; VC=1.65; lo=1.55; hi=1.75
  f=$(mktemp /tmp/prsz_XXXXXX.spice)
  sed -e "s#models_typical#models_$c#; s#^\.temp .*#.temp $T#; s#^\.param WW=.*#.param WW=$W LL=$L VTT=$V SW=0 VCM=$VC PWTG=1u#; s#SWEEPLO#$lo#; s#SWEEPHI#$hi#" -e 's#\.\./spice/#'"$AMP"'/spice/#' "$AMP/tb/char_pseudoR_fg.spice" > $f
  r=$(cd $AMP/tb && taskset -c $core timeout 250 ngspice -b $f 2>&1 | grep '^RESULT'); rm -f $f
  echo "$c $T $W $L $V ${r#RESULT }" > "$RUN/$id.txt"; }
export -f one; export AMP RUN
i=0; for sz in "1u 2u" "0.5u 1u" "0.22u 1u" "0.22u 0.5u" "0.22u 0.28u"; do set -- $sz; for V in 0.2 0.9; do for c in $COMBOS; do echo "one ${c%%:*} ${c##*:} $1 $2 $V $(printf %04d $i) $((i%7))"; i=$((i+1)); done; done; done | parallel -j 7
{ echo "corner temp_C W L VTT r0_ohm r_p100mV_ohm r_m100mV_ohm i_p100mV_A i_m100mV_A"; cat $RUN/*.txt; } > "$AMP/sim/a4c_prsize.csv"; echo wrote sim/a4c_prsize.csv
