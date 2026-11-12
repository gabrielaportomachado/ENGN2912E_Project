#!/bin/bash
# usage: run_noise_sweep.sh p|n   -> sim/char_noise_<p|n>.csv   (run from anywhere)
cd "$(dirname "$0")/../tb" || exit 1
T=${1:-p}
out=../sim/char_noise_$T.csv
echo "fnoicor M(Wtot=Mx50um) L_m Id_A Vgs_or_Vsg_V gm_S cgg_F vn_in_Vrms_0p5_300Hz" > $out
for fn in 0 1; do for L in 1u 2u 4u; do for W in 1 4 16 40; do for I in 2u 10u 50u; do
  sed -e "s/^\.param MM=.*/.param MM=$W LL=$L FN=$fn/" -e "s/^set idt = .*/set idt = $I/" char_noise_$T.spice > /tmp/cn_$T.spice
  sed -i 's#\.\./spice/#'"$PWD"'/../spice/#; s#\.\./sim/#/tmp/#' /tmp/cn_$T.spice
  r=$(timeout 60 ngspice -b /tmp/cn_$T.spice 2>&1 | grep '^RESULT')
  echo "$fn $W $L $I ${r#RESULT }" >> $out
done; done; done; done
