#!/bin/bash
# one bisection job: d2_trip1.sh <corner> <T> <SCLK_MHz>  (trip precharge offset of cmp_p on the real DAC plate; failed runs (random .tran aborts) are retried with +0.013 mV)
ADC="$(cd "$(dirname "$0")/.." && pwd)"; cd "$ADC"; c=$1; T=$2; f=$3; lo=0; hi=40
for i in 1 2 3 4 5 6 7 8; do mid=$(python3 -c "print(($lo+$hi)/2)"); d=""
  for r in 0 1 2 3; do m2=$(python3 -c "print($mid+$r*0.013)"); d=$(python3 scripts/d2_float.py $c $T - $f $m2 2>/dev/null | sed -n 's/.*dec=\([+-]*\) .*/\1/p' | cut -c1); [ -n "$d" ] && break; done
  [ "$d" = "-" ] && hi=$mid || lo=$mid; done
echo "TRIP ${D2X:-nominal} $c $T C SCLK=${f}MHz: decision flips at precharge offset -$hi mV (bisection, +-0.15 mV) -> V* = $(python3 -c "print(round(1.65-$hi/1000,4))") V = code shift $(python3 -c "print(round($hi/0.8057,1))") LSB"
