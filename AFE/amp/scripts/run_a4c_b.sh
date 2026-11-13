#!/bin/bash
# A4c driver part 2 (same job/par machinery as run_a4c.sh; cases thd, pu, inj, leak).  usage: bash scripts/run_a4c.sh <case> [extra NAME=VALUE ...]   raw CSV -> /tmp/a4crun/<case>/ (not kept), analysis -> sim/a4c_<case>.log (python3 scripts/a4c_analyze.py <case>)
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
thd)   rmcase thd      # +-0.5 mV (VD = 0.5 mV differential pk) sine at 12.25 Hz, 8 s, 3 corners (THD, swing); no TGATE
  { for c in ${CS:-typical:27 ff:85 ss:-40}; do k=${c%%:*}; T=${c##*:}; for vd in ${VDS:-0.5m}; do
      echo "job thd ${k}_${T}_f12_${vd} $k $T VD=$vd F_SIG=12.25 TSTOP=8 TSAVE=7.2 TSTEP=2m TMAXS=2m $X"; done; done; } | par ;;
pu)    rmcase pu       # power-up: VDD ramp 0 -> 3.3 V in PU_T (no nodesets); record-path TGATE open + park ON from t = 0 (TG_TOFF = 1 us), closes at 0.5 s with the real one-shot (PWL playback), or FS_RAMP (fs follows VDD, released 10 ms after the ramp)
  { for c in ${CS:-typical:27 ff:85 ss:-40}; do k=${c%%:*}; T=${c##*:}; for pu in ${PUS:-1m}; do
      pw=$(python3 "$AMP/scripts/fs_pwl_c.py" $k $T 0.5 2>/dev/null)
      echo "job pu ${k}_${T}_pu${pu}_notg_nofs $k $T PU_T=$pu TSTOP=${TSTOP:-40} TSTEP=1n TMAXS=${TMAXS:-5m} $X"
      echo "job pu ${k}_${T}_pu${pu}_notg_fsramp $k $T PU_T=$pu FS_RAMP=1 FS_T0=0 FS_W=10m TSTOP=${TSTOP:-40} TSTEP=1n TMAXS=${TMAXS:-5m} $X"
      echo "SWAPS=FSPWL=$pw job pu ${k}_${T}_pu${pu}_tgpark_os $k $T PU_T=$pu USE_TG=1 TG_OPEN0=1 PARK_EN=1 TG_TON=0.5 FS_SRC=2 TSTOP=${TSTOP:-40} TSTEP=1n TMAXS=${TMAXS:-5m} $X"; done; done; } | par ;;
pur)   rmcase pur      # power-up (VDD ramp PU_T, no nodesets, no TGATE), then an IDEAL reset pulse of width W starting at T_FS0 = 3 s (bias is up at every corner: ss -40 C master needs ~0.6 s): which pulse width clears the power-up latch?
  { for c in ${CS:-typical:27 ff:85 ss:-40}; do k=${c%%:*}; T=${c##*:}; for w in ${WS:-4m 30m 100m 300m}; do
      echo "job pur ${k}_${T}_pu1m_w${w} $k $T PU_T=1m FS_EN=1 FS_T0=3 FS_W=$w FS_TR=100n TSTOP=${TSTOP:-40} TSTEP=1n TMAXS=${TMAXS:-5m} $X"; done; done; } | par ;;
inj)   rmcase inj      # park / routing-switch charge injection ALONE: tissue level TIS = vcm_in of the corner (no DC mismatch), no offset, no reset pulse; open 0.2 s, close 0.5 s; INIT_RST=1 only initialises
  { for c in ${CS:-typical:27 ff:85 ss:-40}; do k=${c%%:*}; T=${c##*:}; case $k$T in typical27) tis=1.64842;; ff85) tis=1.64823;; ss-40) tis=1.64864;; *) tis=1.6484;; esac
      echo "job inj ${k}_${T}_tis${tis} $k $T USE_TG=1 TG_OPEN0=1 PARK_EN=1 TG_TON=0.5 TIS=$tis TSTOP=${TSTOP:-12} TSTEP=1n TMAXS=${TMAXS:-1m} $X"; done; } | par ;;
leak)  rmcase leak     # pad leakage / capacitance ASSUMPTIONS on the REC node with the routing switch open (park ON vs OFF), typical 27, 10 mV electrode offset at 0.3 s, reset from the close (PWL playback of the real one-shot)
  { k=typical; T=27; pw=$(python3 "$AMP/scripts/fs_pwl_c.py" $k $T 0.5 2>/dev/null)
    for park in 1 0; do for cp in 0 10p; do for lk in ${LKS:-0 1p 10p}; do
      echo "SWAPS=FSPWL=$pw job leak ${k}_${T}_park${park}_cp${cp}_lk${lk} $k $T USE_TG=1 TG_OPEN0=1 OS_TR=100u PARK_EN=$park TG_TON=0.5 VOS_REC=10m T_OS=0.3 I_LEAK=$lk C_PAD=$cp FS_SRC=2 TSTOP=${TSTOP:-20} TSTEP=1n TMAXS=${TMAXS:-1m} $X"; done; done; done; } | par ;;
*) echo "unknown case"; exit 1 ;;
esac
