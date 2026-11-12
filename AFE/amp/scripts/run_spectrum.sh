#!/bin/bash
# spectrum of the recommended 5T pair, fnoicor 0 and 1 -> sim/char_ota5t_spectrum_fn{0,1}.csv
cd "$(dirname "$0")/../tb" || exit 1
for fn in 0 1; do
  sed -e "s/FN=0/FN=$fn/; s/FNTAG/fn$fn/" char_ota5t_spectrum.spice > /tmp/sp.spice
  sed -i "s#\.\./spice/#$PWD/../spice/#; s#\.\./sim/#$PWD/../sim/#" /tmp/sp.spice
  ngspice -b /tmp/sp.spice > ../sim/char_ota5t_spectrum_fn$fn.log 2>&1
done
