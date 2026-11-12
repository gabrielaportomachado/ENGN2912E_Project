#!/bin/bash
# usage: bash run_hpf_cf.sh <case> ; cases: check | cf | corners | vt
# Writes sim/hpf_<case>.csv. Columns:
# mode corner temp_C Cf_F Cin_F elec_noise vt_V Rfix_ohm VOSD_V gain_mid_dB f_lo_Hz vn_out_0p5_300_V vn_in_0p5_300_V vn_wide_out_V dcout_V
cd "$(dirname "$0")/../tb" || exit 1
run() { # mode corner T CF GAIN ELN VT RFIX
  local mode=$1 c=$2 T=$3 CF=$4 G=$5 EL=$6 VT=$7 RF=$8 VO=${9:-0}
  sed -e "s#models_typical#models_$c#; s#^\.temp .*#.temp $T#" \
      -e "s#^\.param CFF=.*#.param CFF=$CF GAIN=$G VTT=$VT PW=1u PL=2u RFIX=$RF VOSD=$VO#" \
      -e 's#\.\./spice/#'"$PWD"'/../spice/#' tb_hpf_cf.spice > /tmp/h.spice
  if [ "$mode" = res ]; then
    sed -i -e 's#^Xr1 .*#Rf1 vn vout {RFIX}#; s#^Xr2 .*#Rf2 vp vcm {RFIX}#' /tmp/h.spice
  fi
  if [ "$EL" = 0 ]; then
    sed -i -E 's#^(Rs[12] .*|Rct[12] .*)$#\1 noisy=0#' /tmp/h.spice
  fi
  o=$(timeout 300 ngspice -b /tmp/h.spice 2>&1)
  r=$(echo "$o" | grep '^RESULT'); n=$(echo "$o" | grep '^NOISE_B_0p5'); w=$(echo "$o" | grep '^NOISE_B_wide'); d=$(echo "$o" | grep '^DCOUT')
  cin=${G}xCf
  echo "$mode $c $T $CF $cin $EL $VT $RF $VO ${r#RESULT } ${n#NOISE_B_0p5_300 } ${w#NOISE_B_wide } ${d#DCOUT }"
}
case $1 in
check)  out=../sim/hpf_check.csv; : > $out
  for m in res pr; do for el in 1 0; do run $m typical 27 200f 100 $el 0 5.2e12 >> $out; done; done ;;
cf)     out=../sim/hpf_cf.csv; : > $out
  for cf in 100f 200f 400f 800f 1.6p; do for m in pr; do run $m typical 27 $cf 100 1 0 5.2e12 >> $out; run $m typical 27 $cf 100 0 0 5.2e12 >> $out; done; done ;;
corners) out=../sim/hpf_corners.csv; : > $out
  for c in typical ff ss; do for T in -40 27 85; do for cf in 200f 400f; do for vt in 0; do
    run pr $c $T $cf 100 1 $vt 5.2e12 >> $out; run pr $c $T $cf 100 0 $vt 5.2e12 >> $out; done; done; done; done ;;
vt)     out=../sim/hpf_vt.csv; : > $out
  for c in typical ff ss; do for T in -40 27 85; do for vt in -0.1 0.1 0.2; do
    run pr $c $T 200f 100 0 $vt 5.2e12 >> $out; done; done; done ;;
rsweep) out=../sim/hpf_rsweep.csv; : > $out   # IDEAL resistor sweep: noise vs HPF corner (conservative 4kT/R noise)
  for cf in 200f 400f 800f; do for R in 0.5e12 1e12 1.6e12 2.5e12 5.2e12 1e13 2e13 5e13; do
    run res typical 27 $cf 100 1 0 $R >> $out; done; done ;;
pvt)    out=../sim/hpf_pvt.csv; : > $out   # R0 taken from sim/char_pseudoR.csv (L=2u); noise = IDEAL 4kT/R at that R (PDK pfet noise is understated, see NOTES)
  for c in typical ff ss; do for T in -40 27 85; do for vt in -0.1 0 0.1 0.2; do
    R=$(awk -v c=$c -v T=$T -v v=$vt '$1==c && $2==T && $4=="2u" && $5==v {print $6}' ../sim/char_pseudoR.csv)
    for cf in 200f 400f; do
      run res $c $T $cf 100 1 $vt $R 0 >> $out
      run pr  $c $T $cf 100 1 $vt $R 0.1 >> $out
    done; done; done; done ;;
esac
