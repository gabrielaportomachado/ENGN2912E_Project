#!/bin/bash
# usage: bash run_gmin_check.sh -> sim/gmin_check.csv ; R0 (char_pseudoR tb), f_lo and noise (PDK pfet vs IDEAL 4kT/R at that R0) vs .options gmin
cd "$(dirname "$0")/../tb" || exit 1
out=../sim/gmin_check.csv
echo "gmin corner temp_C vt_V r0_ohm f_lo_pdk_Hz noise_pdk_uV f_lo_ideal_Hz noise_ideal4kTR_uV" > $out
for g in 1e-15 1e-18; do for cv in "typical 27" "ff 85"; do set -- $cv; c=$1; T=$2; for vt in 0 0.2; do
  sed -e "s#models_typical#models_$c#; s#^\.temp .*#.temp $T#; s#^\.param WW=.*#.param WW=1u LL=2u VTT=$vt#; s#gmin=[0-9e.-]*#gmin=$g#" \
      -e 's#\.\./spice/#'"$PWD"'/../spice/#' -e 's#\.\./sim/#/tmp/#' char_pseudoR.spice > /tmp/g1.spice
  R=$(ngspice -b /tmp/g1.spice 2>&1 | grep '^RESULT' | awk '{print $2}')
  mk() { sed -e "s#models_typical#models_$c#; s#^\.temp .*#.temp $T#; s#gmin=[0-9e.-]*#gmin=$g#" \
      -e "s#^\.param CFF=.*#.param CFF=200f GAIN=100 VTT=$vt PW=1u PL=2u RFIX=$R VOSD=0#" \
      -e 's#\.\./spice/#'"$PWD"'/../spice/#' -e 's#^\(Rs[12] .*\|Rct[12] .*\)$#\1 noisy=0#' tb_hpf_cf.spice > /tmp/g2.spice; }
  mk; o=$(ngspice -b /tmp/g2.spice 2>&1); fp=$(echo "$o"|grep ^RESULT|awk '{print $3}'); np=$(echo "$o"|grep ^NOISE_B_0p5|awk '{print $3}')
  mk; sed -i -e 's#^Xr1 .*#Rf1 vn vout {RFIX}#; s#^Xr2 .*#Rf2 vp vcm {RFIX}#' /tmp/g2.spice; o=$(ngspice -b /tmp/g2.spice 2>&1); fi=$(echo "$o"|grep ^RESULT|awk '{print $3}'); ni=$(echo "$o"|grep ^NOISE_B_0p5|awk '{print $3}')
  echo "$g $c $T $vt $R $fp $np $fi $ni" >> $out
done; done; done
