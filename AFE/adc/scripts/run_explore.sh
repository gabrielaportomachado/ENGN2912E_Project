#!/bin/bash
# usage: run_explore.sh <corner> <T> NAME=V ...   one 7-cycle decision test (tb_cmp_basic) for sizing; prints decisions, delay at 2 mV / 0.1 mV overdrive, energy per cycle
ADC="$(cd "$(dirname "$0")/.." && pwd)"; c=$1; T=$2; shift 2
tag=$(echo "$c$T $@" | tr ' =' '__'); export OUT=/tmp/exp_$tag.csv
bash $ADC/scripts/dgrun.sh tb_cmp_basic.spice $c $T "$@" >/tmp/exp_$tag.log 2>&1
python3 - "$tag" "$OUT" <<'PY'
import sys; sys.path.insert(0,'/foss/designs/ENGN2912E_Project/AFE/adc/scripts')
import dlib, os
if not os.path.exists(sys.argv[2]): print(sys.argv[1], 'FAILED'); sys.exit()
t,d=dlib.load(sys.argv[2],['clk','inp','inn','outp','outn','o1','o2','a1','a2','i_vdd'])
r=dlib.cycles(t,d,40e-9,5e-9,7)
f=lambda x: '%.2f'%(x*1e9) if x else 'none'
print(sys.argv[1], ' dec', ''.join('+' if x[0]>0 else '-' if x[0]<0 else '0' for x in r), ' delay(2mV) %s ns  delay(0.1mV) %s ns  E %.2f pJ' % (f(r[1][1]), f(r[5][1]), r[1][2]*1e12))
PY
