#!/bin/bash
# A4b item 1: record-path TGATE on-resistance at 3.3 V (real gate drive) over 1.15..2.15 V, typical 27 / ff 85 / ss -40 (and 5 V for reference) -> sim/a4b_tg33_ron.log
AMP="$(cd "$(dirname "$0")/.." && pwd)"; LOG="$AMP/sim/a4b_tg33_ron.log"
echo "# TGATE (TGATE/TGATE.spice, read-only; nfet_05v0 0.565u/0.6u + pfet_05v0 1.22u/0.6u) on-resistance, 10 mV across the switch, gate drive C = VDD, CBAR = 0.  Ron in kOhm at the input voltage shown." > "$LOG"
echo "# supply   corner  T    Ron(1.15 V)  Ron(1.65 V)  Ron(2.15 V)  max Ron over 1.15..2.15 V" >> "$LOG"
for vs in 3.3 5.0; do for c in typical:27 ff:85 ss:-40; do k=${c%%:*}; T=${c##*:}
  f=$(mktemp /tmp/tgr_XXXXXX.spice)
  sed -e "s#VSWMAX#$vs#; s#^\.param VSW=.*#.param VSW=$vs#" "$AMP/tb/tb_tgate_ron.spice" > $f
  sed -i "s#models_typical#models_$k#; s#^\.temp .*#.temp $T#; s#\.\./spice/#$AMP/spice/#; s#\.\./\.\./\.\./TGATE#$AMP/../../TGATE#" $f
  r=$(cd $AMP/tb && taskset -c 7 ngspice -b $f 2>&1 | grep '^RESULT'); rm -f $f
  echo "$vs V   $k  $T   $(echo $r | sed 's/RESULT //')" >> "$LOG"
done; done
python3 - "$LOG" <<'PY'
import re, sys
out = []
for l in open(sys.argv[1]):
    if l.startswith('#'): out.append(l.rstrip()); continue
    m = re.findall(r'=([-\d.eE+]+)', l)
    if len(m) == 4:
        v = [float(x) / 1e3 for x in m]
        out.append(l.split('Ron_')[0].rstrip() + f'   {v[0]:9.2f}    {v[1]:9.2f}    {v[2]:9.2f}    {v[3]:9.2f}')
    else: out.append(l.rstrip())
open(sys.argv[1], 'w').write('\n'.join(out) + '\n'); print('\n'.join(out))
PY
