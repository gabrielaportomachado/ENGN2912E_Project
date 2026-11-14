#!/bin/bash
# D2 kT/C of the split DAC plate T by .noise on the PDK netlist (tb/tb_dac_noise.spice); writes sim/d2_ktc.log.  usage: bash scripts/d2_ktc.sh
ADC="$(cd "$(dirname "$0")/.." && pwd)"; cd "$ADC/tb"; LOG="$ADC/sim/d2_ktc.log"; : > "$LOG"
echo "D2 kT/C at the comparator plate T (equilibrium .noise, ideal 5 kOhm reset resistors, bottoms at AC ground, 100 Hz-100 GHz); hand value sqrt(kT/C_T), C_T = 63 units + series(bridge, LSB array) + CCMP" >> "$LOG"
for T in 27 85 -40; do for cfg in "1 70f" "0 70f" "0 190f" "0 0"; do set -- $cfg
  sed -e "s/^\.param MCLOSED=.*/.param MCLOSED=$1/" -e "s/^\.param CCMP=.*/.param CCMP=$2/" -e "s/^\.temp .*/.temp $T/" tb_dac_noise.spice > /tmp/d2n_$$.spice
  v=$(ngspice -b /tmp/d2n_$$.spice 2>&1 | grep -i onoise_total | head -1 | sed 's/.*= //')
  python3 - "$v" "$T" "$2" "$1" >> "$LOG" <<'PY'
import sys, math
v = float(sys.argv[1]); T = float(sys.argv[2]); c = sys.argv[3]; m = sys.argv[4]; cc = float(c.replace('f', '')) * 1e-15 if c != '0' else 0.0
CT = 3.48935e-12 + cc; k = 1.380649e-23 * (T + 273.15); LSB = 3.3 / 4096
print('T=%4.0f C  M switch closed=%s  C_cmp=%-5s  ngspice %.3f uV rms = %.4f LSB | hand sqrt(kT/C_T) with C_T = %.3f pF: %.3f uV  (ratio %.4f)' % (T, m, c, v * 1e6, v / LSB, CT * 1e12, math.sqrt(k / CT) * 1e6, v / math.sqrt(k / CT)))
PY
done; done; rm -f /tmp/d2n_$$.spice; cat "$LOG"
