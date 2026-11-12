#!/bin/bash
# 5T-OTA input-referred noise vs pair size/load size; fnoicor 0/1 -> sim/char_ota5t_noise.csv
cd "$(dirname "$0")/../tb" || exit 1
out=../sim/char_ota5t_noise.csv
echo "fnoicor L_pair M_pair(x50um) L_load M_load(x50um) vn_in_Vrms_0p5_300Hz" > $out
for fn in 0 1; do for L in 2u 4u; do for K in 4 16 40; do for LN in 2u 4u; do for KN in 1 2 4; do
  sed "s/^\.param LLP=.*/.param LLP=$L LLN=$LN KP=$K KT=2 KN=$KN FN=$fn/" char_ota5t_noise.spice > /tmp/co.spice
  sed -i 's#\.\./spice/#'"$PWD"'/../spice/#' /tmp/co.spice
  r=$(timeout 60 ngspice -b /tmp/co.spice 2>&1 | grep '^RESULT')
  echo "$fn $L $K $LN $KN ${r#RESULT }" >> $out
done; done; done; done; done
