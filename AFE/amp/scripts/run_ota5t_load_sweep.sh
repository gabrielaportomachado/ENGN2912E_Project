#!/bin/bash
# load-device sweep for the 5T OTA noise check -> sim/char_ota5t_load.csv
cd "$(dirname "$0")/../tb" || exit 1
out=../sim/char_ota5t_load.csv
echo "fnoicor L_pair M_pair(x50um) L_load M_load(x50um) vn_in_Vrms_0p5_300Hz" > $out
for fn in 0 1; do for P in "2u 16" "4u 16" "2u 40"; do set -- $P; for LN in 4u 8u 16u; do for KN in 1 2 4 8; do
  sed "s/^\.param LLP=.*/.param LLP=$1 LLN=$LN KP=$2 KT=2 KN=$KN FN=$fn/" char_ota5t_noise.spice > /tmp/co.spice
  sed -i 's#\.\./spice/#'"$PWD"'/../spice/#' /tmp/co.spice
  r=$(timeout 60 ngspice -b /tmp/co.spice 2>&1 | grep '^RESULT')
  echo "$fn $1 $2 $LN $KN ${r#RESULT }" >> $out
done; done; done; done
