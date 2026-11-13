#!/bin/bash
# A4c driver (derived from run_a4b.sh).  usage: bash scripts/run_a4c.sh <case> [extra NAME=VALUE ...]   raw CSV -> /tmp/a4crun/<case>/ (not kept), analysis -> sim/a4c_<case>.log (python3 scripts/a4c_analyze.py <case>)
AMP="$(cd "$(dirname "$0")/.." && pwd)"; RUN=/tmp/a4crun; mkdir -p "$RUN"
COMBOS="typical:-40 typical:27 typical:85 ff:-40 ff:27 ff:85 ss:-40 ss:27 ss:85"
export OMP_NUM_THREADS=1
NC=$(( $(nproc --all) - 1 ))
par() { parallel -j $NC 'taskset -c $(( ({%} - 1) % '$NC' )) bash -c {}'; }
job() { local cs=$1 label=$2 c=$3 T=$4; shift 4; mkdir -p "$RUN/$cs"
  [ -n "$RESUME" ] && [ -s "$RUN/$cs/$label.csv" ] && [ "$(wc -l < "$RUN/$cs/$label.csv")" -gt 20 ] && return 0
  local try=0 args=("$@")
  local nsv=$(awk -v c=$c -v T=$T '$1==c && $2==T {sub("vrs=","",$3); print $3}' "$AMP/sim/a4c_reset_replica.log"); [ -n "$nsv" ] && args+=(NSVRS=$nsv)   # start-up guess of the reset-level node (corner dependent; a wrong guess makes the DC solve fail at ss -40 C)
  while :; do
    OUT="$RUN/$cs/$label.csv" bash "$AMP/scripts/ngrun.sh" ${TB:-tb_a4c_tran.spice} $c $T "${args[@]}" > "$RUN/$cs/$label.log" 2>&1
    if grep -q "Timestep too small" "$RUN/$cs/$label.log" && [ $try -lt 3 ]; then
      try=$((try+1)); newargs=(); for a in "${args[@]}"; do case $a in TMAXS=*) v=${a#TMAXS=}; num=${v%%[a-zA-Z]*}; unit=${v#$num}; a="TMAXS=$(awk -v n=$num 'BEGIN{printf "%.4g", n*0.9}')$unit";; TSTEP=*) v=${a#TSTEP=}; num=${v%%[a-zA-Z]*}; unit=${v#$num}; a="TSTEP=$(awk -v n=$num 'BEGIN{printf "%.4g", n*3}')$unit";; esac; newargs+=("$a"); done; args=("${newargs[@]}")
    else break; fi
  done
  grep -E -q "rror|timestep too small|singular" "$RUN/$cs/$label.log" && echo "WARN $cs $label (tries $try): $(grep -E 'rror|imestep too small|singular' "$RUN/$cs/$label.log" | head -1 | cut -c1-150)"; return 0; }
rmcase() { [ -n "$RESUME" ] || rm -rf "$RUN/$1"; }
export -f job rmcase; export AMP RUN TB
cs=$1; shift; X="$*"
case $cs in
pw)    rmcase pw       # reset pulse width sweep, 100 mV REC offset step at 0.1 s, no TGATE, typical 27 (RSL / PR sizes via extra args)
  { for w in ${WS:-0.3m 1m 3m 10m 30m}; do
      echo "job pw ${CORNER:-typical}_${TEMPC:-27}_w$w ${CORNER:-typical} ${TEMPC:-27} VOS_REC=${OS:-100m} T_OS=0.1 FS_EN=1 FS_T0=0.09999 FS_W=$w FS_TR=${TR:-10n} TSTOP=${TSTOP:-1} TSTEP=1u TMAXS=${TMAXS:-50u} $X"; done; } | par ;;
rec)   rmcase rec      # reset-pulse recovery: REC offset step OS (1/10/100 mV) at 0.1 s with the ideal reset pulse of width W starting 10 us before the step (no TGATE), corners CS, record TSTOP s
  { for c in ${CS:-typical:27 ff:85 ss:-40}; do k=${c%%:*}; T=${c##*:}; for os in ${OSS:-1m 10m 100m}; do for w in ${WS:-1m 3m 10m 30m}; do
      echo "job rec ${k}_${T}_os${os}_w${w} $k $T VOS_REC=$os T_OS=0.1 FS_EN=1 FS_T0=0.09999 FS_W=$w FS_TR=${TR:-100n} TSTOP=${TSTOP:-40} TSTEP=1u TMAXS=${TMAXS:-1m} $X"; done; done; done; } | par ;;
tg)    rmcase tg       # record-path TGATE (3.3 V drive) + REC park: closed 0..0.2 s, OPEN 0.2..0.5 s (park ON if PARK=1; offset step OS at 0.3 s on the electrode), closes at 0.5 s.  Reset: FSSRC=3 -> the REAL one-shot (trigger = routing switch C net), else an
                       # ideal pulse of width W from 10 us before the close; WS=0 -> no reset pulse.  INIT_RST=1: ideal initialisation reset pulse at 1 ms (the DC operating point with the TGATE attached is the railed state, see tb comment).  TIS = tissue level
  { for c in ${CS:-typical:27 ff:85 ss:-40}; do k=${c%%:*}; T=${c##*:}; for os in ${OSS:-0 1m 10m 100m}; do for w in ${WS:-10m}; do for lk in ${LKS:-0}; do for cp in ${CPS:-0}; do
      osarg=""; [ "$os" != 0 ] && osarg="VOS_REC=$os T_OS=0.3"
      swp=""; if [ "$FSSRC" = 3 ]; then fsarg="FS_SRC=2"; w=os3; swp="SWAPS=FSPWL=$(python3 $AMP/scripts/fs_pwl_c.py $k $T 0.5 2>/dev/null)"; elif [ "$w" = 0 ]; then fsarg=""; else fsarg="FS_EN=1 FS_T0=0.49999 FS_W=$w FS_TR=${TR:-100n}"; fi
      echo "$swp job tg ${k}_${T}_os${os}_w${w}_lk${lk}_cp${cp}_park${PARK:-1} $k $T USE_TG=1 TG_OPEN0=1 PARK_EN=${PARK:-1} TG_TON=0.5 OS_TR=100u $osarg I_LEAK=$lk C_PAD=$cp $fsarg TSTOP=${TSTOP:-30} TSTEP=1n TMAXS=${TMAXS:-1m} $X"; done; done; done; done; done; } | par ;;
ring)  rmcase ring     # reset held ON (fs rises at 20 us), small REC step VOS (default 1 mV = 100 mV at v1) at 200 us: ringing / stability of the stage-1 loop IN THE RESET STATE (time domain; the AC operating point of the reset state is unreliable, see NOTES A4c)
  { for c in ${CS:-typical:27 ff:85 ss:-40 ff:-40 typical:85 ss:85}; do k=${c%%:*}; T=${c##*:}
      echo "job ring ${k}_${T} $k $T VOS_REC=${OS:-1m} T_OS=200u FS_EN=1 FS_T0=20u FS_W=10 FS_TR=100n TSTOP=600u TSTEP=10n TMAXS=100n $X"; done; } | par ;;
*) echo "unknown case"; exit 1 ;;
esac
