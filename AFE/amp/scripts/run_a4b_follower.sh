#!/bin/bash
# A4b: why the A4a output could not reach 2.15 V, and why the stage-2 pseudo-R gate offset had to change -> sim/a4b_follower.log
# 12.25 Hz, VD = 0.5 mV (full scale), 8 s, last 4 periods fitted.  A4a bias = VCM_IN 1.5 V, VTT2 0.2 V.  Variants of the follower (ota2.spice Xmf) and of the stage-2 feedback resistor.
AMP="$(cd "$(dirname "$0")/.." && pwd)"; T=/tmp/a4bfol; rm -rf $T; mkdir -p $T; LOG="$AMP/sim/a4b_follower.log"
sed -e '/^Xmf /s/nfet_06v0_nvt/nfet_03v3/' "$AMP/spice/ota2.spice" > $T/ota2_n33.spice          # A4a follower: 3.3 V NMOS 10u/2u
one() { lab=$1; c=$2; Tc=$3; sw=$4; shift 4
  OUT=$T/$lab.csv SWAPS="$sw" taskset -c $(( ${lab//[^0-9]/} % 7 )) bash "$AMP/scripts/ngrun.sh" tb_afe_1ch_tran.spice $c $Tc VD=0.5m F_SIG=12.25 TSTOP=8 TSAVE=7.2 TSTEP=2m TMAXS=2m "$@" > $T/$lab.log 2>&1; }
n=0
for c in typical:27 ff:85 ss:-40; do k=${c%%:*}; t=${c##*:}
  R=$(awk -v c=$k -v T=$t '$1==c && $2==T && $3==1.5 && $4==0.2 && $5==0 {print $6}' "$AMP/sim/a4a_prfg.csv")
  one "a4a_$k$t$((++n))" $k $t "../spice/ota2.spice=$T/ota2_n33.spice" VCM_IN=1.5 VTT2=0.2 &
  one "nvt_$k$t$((++n))" $k $t "x=x" VCM_IN=1.5 VTT2=0.2 &
  one "nvtidealR_$k$t$((++n))" $k $t "x=x" VCM_IN=1.5 VTT2=0.2 RMODE2=1 RFIX2=$R &
  one "final_$k$t$((++n))" $k $t "x=x" &
done; wait
python3 - "$T" > "$LOG" <<'PY'
import sys, math, glob, os
sys.path.insert(0, os.environ.get('AMP', '.') + '/scripts') if False else None
sys.path.insert(0, '/foss/designs/ENGN2912E_Project/AFE/amp/scripts')
import a4b_lib as L
print('# A4b follower / stage-2 resistor diagnosis.  12.25 Hz, 0.5 mV pk differential (= +-0.5 V full scale), 8 s, last 4 periods.  gain = fundamental / 0.5 mV')
print('# a4a   = A4a netlist: 3.3 V NMOS follower 10u/2u, VCM_IN 1.5 V, VTT2 0.2 V          nvt = native-Vt follower nfet_06v0_nvt 10u/2u, same bias')
print('# nvtidealR = nvt + IDEAL 4kT/R resistor (R0) in place of the stage-2 pseudo-R      final = A4b baseline (nvt, VCM_IN 1.65 V, VTT2 0.9 V)')
print('variant      corner   T   gain_dB   THD_%   mean_V  drift_mV  ymax_V  ymin_V   o2max  o2min')
order = {'a4a': 0, 'nvt': 1, 'nvtidealR': 2, 'final': 3}
rows = []
for f in glob.glob(sys.argv[1] + '/*.csv'):
    lab = os.path.basename(f)[:-4]; v = lab.split('_')[0]; rest = lab.split('_', 1)[1]
    d = L.load(f)
    a1, thd, mean, h = L.harmonics(d['time'], d['out'], 12.25, 4); m = d['time'] > d['time'][-1] - 4 / 12.25
    corner = ''.join(ch for ch in rest if not (ch.isdigit() or ch == '-'))[:7] if False else rest
    rows.append((order[v], rest, v, a1, thd, mean, d['out'][m].max(), d['out'][m].min(), d['o2'][m].max(), d['o2'][m].min()))
for o, rest, v, a1, thd, mean, ymax, ymin, o2x, o2n in sorted(rows):
    print(f'{v:10s} {rest:12s} {20*math.log10(a1/0.5e-3):8.3f} {thd*100:8.3f} {mean:8.4f} {(mean-1.65)*1e3:8.1f} {ymax:7.3f} {ymin:7.3f} {o2x:7.3f} {o2n:6.3f}')
PY
echo "wrote sim/a4b_follower.log"
