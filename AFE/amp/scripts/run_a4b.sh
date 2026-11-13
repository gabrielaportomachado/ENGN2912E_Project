#!/bin/bash
# A4b driver.  usage: bash scripts/run_a4b.sh <case> [vtt2]    raw CSV -> /tmp/a4brun/<case>/ (not kept), analysis -> sim/a4b_<case>.log (python3 scripts/a4b_analyze.py <case>)
#   thd     12.25 Hz and 300 Hz sine, VD = 0.25/0.5/0.6/0.8/1.0 mV pk, 9 PVT, 8 s (the pseudo-R DC drift needs seconds): THD, gain, swing, DC drift
#   slew    differential steps +-0.25/+-0.5 mV on REC, 9 PVT: max |dv/dt| up/down, 10-90 % rise, linearity
#   adc     ADC input model: C_s 17 pF behind 1 kOhm, precharged to VOCM + dV (dV = +-1, +-1.65, +-3.3 V), one long connect (40 us) at 9 PVT
#   adc2    same with T_ACQ = 11.05 us exactly: amplifier recovery after disconnect
#   fscharge  fast-settle pulse alone (no offset): charge injection / residual vs pulse width (1 us ... 100 ms), 9 PVT
#   recov   REC offset step 0.1 ... 300 mV with/without fast-settle pulses, typical 27 + corners
#   tg      TGATE in series with REC: on/off toggling, offset step while off, recovery
#   pwrup   VDD ramp from 0 V: bias currents, settling, with/without fast-settle
AMP="$(cd "$(dirname "$0")/.." && pwd)"; RUN=/tmp/a4brun; mkdir -p "$RUN"
COMBOS="typical:-40 typical:27 typical:85 ff:-40 ff:27 ff:85 ss:-40 ss:27 ss:85"
# ngspice starts 8 OpenMP threads per process (spinit; num_threads=1 in .spiceinit / .options is not honoured in batch mode, checked): pin every job to ONE core (job slot = core),
# run nproc-1 jobs in parallel (one core stays free for the shell).
export OMP_NUM_THREADS=1
NC=$(( $(nproc --all) - 1 ))   # nproc honours OMP_NUM_THREADS (=1 above): use --all, otherwise NC = 0 = unlimited jobs
par() { parallel -j $NC 'taskset -c $(( ({%} - 1) % '$NC' )) bash -c {}'; }   # slot numbers can exceed -j (seen: slot 9 with -j 7): wrap onto the NC cores
# job <case> <label> <corner> <T> [NAME=VALUE ...]
job() { local cs=$1 label=$2 c=$3 T=$4; shift 4; mkdir -p "$RUN/$cs"
  # RESUME=1: skip jobs whose CSV already exists.  A "Timestep too small" abort (random, in the quiet part of the run; A3 saw the same) is retried with TMAXS x 0.9 (up to 3 times).
  [ -n "$RESUME" ] && [ -s "$RUN/$cs/$label.csv" ] && [ "$(wc -l < "$RUN/$cs/$label.csv")" -gt 20 ] && return 0
  local try=0 args=("$@")
  case " ${args[*]} " in *" USE_TG=1 "*) args+=(INIT_G=1e-8 T_INIT=50m LOOPTEST=2);; esac    # start-up aid: see tb_afe_1ch_tran.spice (bistable railed DC state of stage 1)
  while :; do
    OUT="$RUN/$cs/$label.csv" bash "$AMP/scripts/ngrun.sh" tb_afe_1ch_tran.spice $c $T "${args[@]}" > "$RUN/$cs/$label.log" 2>&1
    if grep -q "Timestep too small" "$RUN/$cs/$label.log" && [ $try -lt 3 ]; then
      try=$((try+1))
      newargs=(); for a in "${args[@]}"; do case $a in TMAXS=*) v=${a#TMAXS=}; num=${v%%[a-zA-Z]*}; unit=${v#$num}; a="TMAXS=$(awk -v n=$num 'BEGIN{printf "%.4g", n*0.9}')$unit";; TSTEP=*) v=${a#TSTEP=}; num=${v%%[a-zA-Z]*}; unit=${v#$num}; a="TSTEP=$(awk -v n=$num 'BEGIN{printf "%.4g", n*3}')$unit";; esac; newargs+=("$a"); done; args=("${newargs[@]}")
    else break; fi
  done
  grep -E -q "rror|timestep too small|singular" "$RUN/$cs/$label.log" && echo "WARN $cs $label (tries $try): $(grep -E 'rror|imestep too small|singular' "$RUN/$cs/$label.log" | head -1 | cut -c1-150)"; return 0; }
rmcase() { [ -n "$RESUME" ] || rm -rf "$RUN/$1"; }
export -f job rmcase; export AMP RUN
case $1 in
thd)   D=${CASEDIR:-thd}; rm -rf $RUN/$D     # CASEDIR=<name> keeps variants apart (e.g. thd_vtt0.6 with $2 = "VTT2=0.6"); VDS="0.5m 0.8m" overrides the amplitude list
  for c in $COMBOS; do k=${c%%:*}; T=${c##*:}
    for vd in ${VDS:-0.25m 0.5m 0.6m 0.8m 1.0m}; do
      echo "job $D ${k}_${T}_f12_${vd} $k $T VD=$vd F_SIG=12.25 TSTOP=8 TSAVE=7.2 TSTEP=2m TMAXS=2m $2"
      echo "job $D ${k}_${T}_f300_${vd} $k $T VD=$vd F_SIG=300 TSTOP=8 TSAVE=7.9 TSTEP=20u TMAXS=80u $2"
    done; done | par ;;
slew)  rmcase slew
  for c in typical:27 ff:85 ss:-40; do k=${c%%:*}; T=${c##*:}
    for a in 0.25m 0.5m; do for sg in + -; do
      echo "job slew ${k}_${T}_s${sg}${a} $k $T VOS_REC=${sg}${a} T_OS=0.005 TSTOP=0.04 TSTEP=0.5u TMAXS=5u $2"; done; done; done | par ;;
adc)   rmcase adc     # Decision 28: C_s reset to VOUT_CM (DV_PREV = 0); the amplifier output holds +-0.5 V (REC offset step +-0.5 mV, 2 ms before); one long connect (40 us) -> error at any T_ACQ <= 40 us
  { for c in $COMBOS; do k=${c%%:*}; T=${c##*:}
    for a in +0.5m -0.5m; do
      echo "job adc ${k}_${T}_s${a} $k $T VOS_REC=${a} T_OS=1u ADC_EN=1 ADC_T0=2m DV_PREV=0 T_ACQ=40u TSAVE=1.9m TSTOP=2.065m TSTEP=100n TMAXS=500n $2"; done; done
    for c in typical:27 ss:-40; do k=${c%%:*}; T=${c##*:}   # reference WITHOUT the reset: C_s keeps the previous channel's level, +-1 V away from the new one (D0 model)
      for dv in +1 -1; do echo "job adc ${k}_${T}_noreset${dv} $k $T ADC_EN=1 ADC_T0=5u DV_PREV=${dv} T_ACQ=40u TSTOP=65u TSTEP=10n TMAXS=20n $2"; done; done; } | par ;;
adcks) rmcase adcks    # smallest extra follower sink that passes: BM_KSF (6 = A4a, unit 16u/4u mirror leg) with the hard (downward) step -0.5 V
  { for c in $COMBOS; do k=${c%%:*}; T=${c##*:}
    for ksf in ${KSFS:-6 9 12 18 24 36}; do
      echo "job adcks ${k}_${T}_ksf${ksf} $k $T VOS_REC=-0.5m T_OS=1u ADC_EN=1 ADC_T0=2m DV_PREV=0 T_ACQ=40u TSAVE=1.9m TSTOP=2.065m TSTEP=100n TMAXS=500n BM_KSF=$ksf $2"; done; done; } | par ;;
adc2)  rmcase adc2    # T_ACQ = 11.05 us exactly, then 400 us: amplifier recovery after the disconnect
  { for c in $COMBOS; do k=${c%%:*}; T=${c##*:}
    for a in +0.5m -0.5m; do
      echo "job adc2 ${k}_${T}_s${a} $k $T VOS_REC=${a} T_OS=1u ADC_EN=1 ADC_T0=2m DV_PREV=0 T_ACQ=11.05u TSAVE=1.9m TSTOP=2.42m TSTEP=100n TMAXS=500n $2"; done; done; } | par ;;
fscharge) rmcase fscharge   # fast-settle pulse alone, sine OFF (VD = 0): release charge injection / residual; typical 27, ff 85, ss -40
  { for c in typical:27 ff:85 ss:-40; do k=${c%%:*}; T=${c##*:}
    for w in 10u 100u 1m 10m; do
      echo "job fscharge ${k}_${T}_w${w} $k $T FS_EN=1 FS_T0=0.01 FS_W=$w FS_TR=10n TSTOP=12 TSTEP=10n TMAXS=1m $2"; done; done; } | par ;;
recov) rmcase recov     # no TGATE, no fs: REC offset step 1/10/100 mV (IDEAL, 1 us edge) at 0.1 s; typical 27, ff 85, ss -40
  { for c in typical:27 ff:85 ss:-40; do k=${c%%:*}; T=${c##*:}
    for a in 1m 10m; do echo "job recov ${k}_${T}_os${a}_w0 $k $T VOS_REC=$a T_OS=0.1 TSTOP=80 TSTEP=1u TMAXS=20m $2"; done
    echo "job recov ${k}_${T}_os100m_w0 $k $T VOS_REC=100m T_OS=0.1 TSTOP=1500 TSTEP=1u TMAXS=100m $2"; done; } | par ;;
tg)    rmcase tg        # TGATE (5 V devices, read-only TGATE.spice) in series with REC; closed 0..0.2 s, OPEN 0.2..0.5 s (offset step at 0.3 s), closes at 0.5 s.
                             # fs: asserted 10 us before the TGATE closes, released T_FS after it closes.  gain/toggle rows + offsets 1/10/100 mV x T_FS 0.1/1/10 ms, and the no-fs baseline.
  { for c in typical:27; do k=${c%%:*}; T=${c##*:}
      echo "job tg ${k}_${T}_notg_sine $k $T VD=100u F_SIG=12.25 TSTOP=6 TSAVE=5.2 TSTEP=2m TMAXS=2m $2"
      echo "job tg ${k}_${T}_tgon_sine $k $T USE_TG=1 TG_TOFF=1e6 TG_TON=2e6 VD=100u F_SIG=12.25 TSTOP=6 TSAVE=5.2 TSTEP=2m TMAXS=2m $2"
      echo "job tg ${k}_${T}_tgtog_none_fs0.1m $k $T USE_TG=1 TG_TOFF=0.2 TG_TON=0.5 FS_EN=1 FS_T0=0.49999 FS_W=0.11m TSTOP=30 TSTEP=100n TMAXS=2m $2"
      echo "job tg ${k}_${T}_tgtog_none_nofs $k $T USE_TG=1 TG_TOFF=0.2 TG_TON=0.5 TSTOP=30 TSTEP=100n TMAXS=2m $2"
      for a in 1m 10m 100m; do
        TS=60; TM=5m; [ $a = 100m ] && { TS=400; TM=50m; }
        echo "job tg ${k}_${T}_tgtog_os${a}_nofs $k $T USE_TG=1 TG_TOFF=0.2 TG_TON=0.5 VOS_REC=$a T_OS=0.3 TSTOP=$TS TSTEP=100n TMAXS=$TM $2"
        [ "$k" = ss ] && continue
        [ $a = 10m ] || continue
        for w in 0.1m 1m; do
          fw=$(awk -v w=$w 'BEGIN{v=w; sub(/m/,"",v); printf "%gm", v+0.01}')
          echo "job tg ${k}_${T}_tgtog_os${a}_fs${w} $k $T USE_TG=1 TG_TOFF=0.2 TG_TON=0.5 VOS_REC=$a T_OS=0.3 FS_EN=1 FS_T0=0.49999 FS_W=$fw TSTOP=40 TSTEP=100n TMAXS=2m $2"; done; done; done; } | par ;;
pwrup) rmcase pwrup
  { for c in typical:27 ff:85 ss:-40; do k=${c%%:*}; T=${c##*:}
      echo "job pwrup ${k}_${T}_op $k $T TSTOP=10u TSTEP=1u TMAXS=1u $2"
      for fs in 0 1; do echo "job pwrup ${k}_${T}_pu1m_fs${fs} $k $T PU_T=1m FS_RAMP=$fs FS_T0=0 FS_W=1m TSTOP=40 TSTEP=1u TMAXS=10m $2"; done; done
    for pu in 100u 10m; do for fs in 0 1; do echo "job pwrup typical_27_pu${pu}_fs${fs} typical 27 PU_T=$pu FS_RAMP=$fs FS_T0=0 FS_W=1m TSTOP=40 TSTEP=1u TMAXS=10m $2"; done; done; } | par ;;
fsshort) # ideal 100/300 ns fast-settle pulses (the cheap fix of the release problem), 3 corners -> same directory/labels as fscharge
  { for c in typical:27 ff:85 ss:-40; do k=${c%%:*}; T=${c##*:}
    for w in 100n 300n; do echo "job fscharge ${k}_${T}_w${w} $k $T FS_EN=1 FS_T0=0.01 FS_W=$w FS_TR=10n TSTOP=12 TSTEP=100n TMAXS=1m $2"; done; done; } | par ;;
fsos)  rmcase fsos          # the REAL one-shot (tb/tb_fsos_gate.spice, played back: FS_SRC=2) driving the channel; pulse alone, sel = 0 / 1
  { for c in typical:27 ff:85 ss:-40; do k=${c%%:*}; T=${c##*:}
    for sel in 0 1; do pw=$(python3 "$AMP/scripts/fs_pwl.py" $k $T $sel 0.01 2>/dev/null)
      echo "SWAPS=FSPWL=$pw job fsos ${k}_${T}_sel${sel} $k $T FS_SRC=2 FS_SEL=$sel FS_T0=0.01 TSTOP=12 TSTEP=100n TMAXS=1m $2"; done; done; } | par ;;
tgos)  rmcase tgos          # record-path TGATE (3.3 V) closes at 0.5 s after an offset step at 0.3 s; fast-settle = the real one-shot (played back), triggered by the closing edge
  { for c in typical:27; do k=${c%%:*}; T=${c##*:}
    for sel in 0 1; do pw=$(python3 "$AMP/scripts/fs_pwl.py" $k $T $sel 0.5 2>/dev/null)
      for a in 1m 10m 100m; do
        echo "SWAPS=FSPWL=$pw job tgos ${k}_${T}_tgos_os${a}_sel${sel} $k $T USE_TG=1 TG_TOFF=0.2 TG_TON=0.5 VOS_REC=$a T_OS=0.3 FS_SRC=2 FS_SEL=$sel TSTOP=24 TSTEP=100n TMAXS=5m $2"; done; done; done; } | par ;;
padfloat) rmcase padfloat   # pad loading with the routing switch OPEN (REC floats): C_PAD / I_LEAK (ASSUMPTIONS), switch open 0.2..0.5 s, recovery 60 s; with and without the one-shot (sel 1)
  { for c in typical:27; do k=${c%%:*}; T=${c##*:}
    pw=$(python3 "$AMP/scripts/fs_pwl.py" $k $T 1 0.5 2>/dev/null)
    for cp in 0 10p; do for il in 0 1p 10p; do
      echo "job padfloat ${k}_${T}_pad${cp}_leak${il}_nofs $k $T USE_TG=1 TG_TOFF=0.2 TG_TON=0.5 C_PAD=$cp I_LEAK=$il TSTOP=30 TSTEP=100n TMAXS=10m $2"
      [ $il != 0 ] && echo "SWAPS=FSPWL=$pw job padfloat ${k}_${T}_pad${cp}_leak${il}_fsos $k $T USE_TG=1 TG_TOFF=0.2 TG_TON=0.5 C_PAD=$cp I_LEAK=$il FS_SRC=2 FS_SEL=1 TSTOP=30 TSTEP=100n TMAXS=10m $2"
    done; done; done; } | par ;;
adc245) rmcase adc245       # ADC per channel (Decision 34): T_ACQ = 245 us, NO reset: C_s keeps the previous sample (+-0.24 V = 300 Hz full-scale sample-to-sample step); amplifier at rest
  { for c in typical:27 ff:85 ss:-40; do k=${c%%:*}; T=${c##*:}
    for dv in +0.24 -0.24; do echo "job adc245 ${k}_${T}_dv${dv} $k $T ADC_EN=1 ADC_T0=2m DV_PREV=${dv} T_ACQ=245u TSAVE=1.9m TSTOP=2.26m TSTEP=100n TMAXS=500n $2"; done; done; } | par ;;
pwrfs) rmcase pwrfs         # power-up with a SHORT fast-settle pulse 1 ms after the 1 ms supply ramp has finished (ideal 300 ns pulse), 3 corners
  { for c in typical:27 ff:85 ss:-40; do k=${c%%:*}; T=${c##*:}
      echo "job pwrfs ${k}_${T}_pu1m_fs300n $k $T PU_T=1m FS_EN=1 FS_T0=2m FS_W=300n FS_TR=10n TSTOP=40 TSTEP=1u TMAXS=10m $2"; done; } | par ;;
*) echo "unknown case"; exit 1 ;;
esac
