#!/bin/bash
# A4b items 1+2: input-referred noise (0.5-300 Hz, typical flicker, IDEAL resistor = R0 in both stages as in A4a/A4b) of the full channel with the Randles source and
#   (a) no record-path switch, (b) the real TGATE at 3.3 V (closed), (c) an IDEAL series resistor RTG (max Ron for 2 uV), (d) pad capacitance C_PAD (ASSUMPTION) behind the real TGATE.
# -> sim/a4b_tg33_noise.log.  typical 27 / ff 85 / ss -40.
AMP="$(cd "$(dirname "$0")/.." && pwd)"; RUN=/tmp/a4b_tgn; rm -rf $RUN; mkdir -p $RUN; export AMP RUN OMP_NUM_THREADS=1
r0fg() { awk -v c=$1 -v T=$2 '$1==c && $2==T && $3==1.5 && $4==0.2 && $5==0 {print $6}' "$AMP/sim/a4a_prfg.csv"; }
job() { lab=$1; c=$2; T=$3; shift 3; R=$(r0fg $c $T); { echo "### $lab"; bash "$AMP/scripts/ngrun.sh" tb_afe_1ch_noise.spice $c $T RFIX=$R RFIX2=$R "$@" 2>&1 | grep -E '^NOISE_B|^NOISE_S1|rror'; } > $RUN/$lab.txt; }
export -f job r0fg
NC=$(( $(nproc --all) - 1 ))
{ for c in typical:27 ff:85 ss:-40; do k=${c%%:*}; T=${c##*:}
    echo "job none_${k}_${T} $k $T"
    echo "job realTG_${k}_${T} $k $T USE_TG=1"
    for r in 10k 30k 100k 300k 1M; do echo "job rtg${r}_${k}_${T} $k $T RTG=${r/k/000}"; done
    for cp in 2p 10p; do echo "job realTG_cpad${cp}_${k}_${T} $k $T USE_TG=1 C_PAD=$cp"; done
    for cp in 2p 10p; do echo "job none_cpad${cp}_${k}_${T} $k $T C_PAD=$cp"; done
  done; } | sed 's#RTG=1M#RTG=1000000#' | parallel -j ${NCJ:-$NC} 'taskset -c $(( ({%} - 1) % '$NC' )) bash -c {}'
cat $RUN/*.txt > "$AMP/sim/a4b_tg33_noise.log"; echo "wrote sim/a4b_tg33_noise.log ($(grep -c '^###' "$AMP/sim/a4b_tg33_noise.log") jobs)"
