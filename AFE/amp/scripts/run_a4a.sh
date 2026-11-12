#!/bin/bash
# A4a driver.  usage: bash scripts/run_a4a.sh <case>      (logs/CSV in sim/a4a_*)
#   prfg      fixed-gate pseudo-resistor R0 (REAL gate bias) at 9 PVT, with/without the fast-settle switch candidates -> sim/a4a_prfg.csv
#   biascore  beta-multiplier master over 9 PVT, VDD 3.0/3.3/3.6 and two Rb values                                  -> sim/a4a_biascore.csv
#   diagtran  Decision 13: which diffusion parameter breaks .tran (stage-1 recovery tb, 0.4 s)                          -> sim/a4a_diag_tran.log
#   op ac acfs ol2 psrr noise   full channel (afe_ch + bias_gen) at 9 PVT -> sim/a4a_<case>.log (acfs = fast-settle switches closed)
#   diffcheck Decision 13: A3 op/ol/loop/cl/noise rerun at 9 PVT with real diffusion (DIFF=1)                         -> sim/a4a_diff_<case>.log
AMP="$(cd "$(dirname "$0")/.." && pwd)"; RUN=/tmp/a4arun; mkdir -p "$RUN"
COMBOS="typical:-40 typical:27 typical:85 ff:-40 ff:27 ff:85 ss:-40 ss:27 ss:85"
KEYS='^(RESULT|OPDEV|OPSUM|OPNODE|NOISE|ICMR|CHECK)|[Ee]rror|[Ff]atal|singular'
par() { xargs -P 8 -I{} bash -c "{}"; }
r0fg() { awk -v c=$1 -v T=$2 '$1==c && $2==T && $3==1.5 && $4==0.2 && $5==0 {print $6}' "$AMP/sim/a4a_prfg.csv"; }
r0() { awk -v c=$1 -v T=$2 '$1==c && $2==T && $4=="2u" && ($5+0)==0.2 {print $6}' "$AMP/sim/char_pseudoR.csv"; }
job() { local cs=$1 label=$2; shift 2; mkdir -p "$RUN/$cs"
  { echo "### $label"; bash "$AMP/scripts/ngrun.sh" "$@" 2>&1 | grep -E "$KEYS" | head -40; } > "$RUN/$cs/$label.txt"; }
fin() { cat "$RUN/$1"/*.txt > "$AMP/sim/a4a_$1.log"; echo "wrote sim/a4a_$1.log ($(grep -c '^###' "$AMP/sim/a4a_$1.log") jobs)"; }
export -f job r0 r0fg; export AMP RUN KEYS
case $1 in
prfg)  # one job: corner T VCM VTT SW
  rm -rf $RUN/prfg; mkdir -p $RUN/prfg
  one() { c=$1; T=$2; VC=$3; V=$4; SW=$5; lo=$(awk -v v=$VC 'BEGIN{printf "%.2f",v-0.1}'); hi=$(awk -v v=$VC 'BEGIN{printf "%.2f",v+0.1}')
    f=$(mktemp /tmp/prfg_XXXXXX.spice)
    sed -e "s#models_typical#models_$c#; s#^\.temp .*#.temp $T#; s#^\.param WW=.*#.param WW=1u LL=2u VTT=$V SW=$SW VCM=$VC#; s#SWEEPLO#$lo#; s#SWEEPHI#$hi#" \
        -e 's#\.\./spice/#'"$AMP"'/spice/#' "$AMP/tb/char_pseudoR_fg.spice" > $f
    r=$(timeout 250 ngspice -b $f 2>&1 | grep '^RESULT'); rm -f $f
    echo "$c $T $VC $V $SW ${r#RESULT }" > "$RUN/prfg/${c}_${T}_${VC}_${V}_${SW}.txt"; }
  export -f one; export AMP RUN
  for c in $COMBOS; do k=${c%%:*}; T=${c##*:}
    for V in 0.1 0.2 0.3; do echo "one $k $T 1.5 $V 0"; done
    for SW in 1 2; do echo "one $k $T 1.5 0.2 $SW"; done
    echo "one $k $T 1.65 0.2 0"; echo "one $k $T 1.65 0.2 2"
  done | par
  { echo "corner temp_C VCM_V VTT_V SW(0=none,1=PMOS,2=NMOS) r0_ohm r_p100mV_ohm r_m100mV_ohm i_p100mV_A i_m100mV_A   [W/L=1u/2u pseudo_r_fg, fs open]"
    cat $RUN/prfg/*.txt | sort -k1,1 -k3,3 -k5,5 -k4,4 -k2,2n; } > "$AMP/sim/a4a_prfg.csv"; echo "wrote sim/a4a_prfg.csv" ;;
biascore)
  rm -rf $RUN/bc; mkdir -p $RUN/bc
  one() { c=$1; T=$2; RL=$3; VD=$4
    f=$(mktemp /tmp/bc_XXXXXX.spice)
    sed -e "s#models_typical#models_$c#; s#^\.temp .*#.temp $T#; s#^\.param RLEN=.*#.param RLEN=$RL VDDV=$VD#" -e 's#\.\./spice/#'"$AMP"'/spice/#' "$AMP/tb/char_bias_core.spice" > $f
    r=$(timeout 200 ngspice -b $f 2>&1 | grep -E '^RESULT|^Error' | head -2 | tr '\n' ' '); rm -f $f
    echo "$c $T $RL $VD ${r#RESULT }" > "$RUN/bc/${c}_${T}_${RL}_${VD}.txt"; }
  export -f one
  for c in $COMBOS; do k=${c%%:*}; T=${c##*:}; for RL in 60u 120u; do echo "one $k $T $RL 3.3"; done; done | par
  for VD in 3.0 3.6; do for RL in 60u 120u; do echo "one typical 27 $RL $VD"; done; done | par
  { echo "corner temp_C Rb_len_um(w=2u,1k/sq poly) VDD_V id1_A id2_A gm1_S vbn_V istart_A"; cat $RUN/bc/*.txt | sort -k3,3 -k4,4n -k1,1 -k2,2n; } > "$AMP/sim/a4a_biascore.csv"; echo "wrote sim/a4a_biascore.csv" ;;
diagtran)  # Decision 13: isolate the .tran failure.  Variants of ota1.spice with each diffusion term on its own.
  D=$RUN/diag; rm -rf $D; mkdir -p $D
  python3 - "$AMP" "$D" <<'PY'
import re, sys
amp, d = sys.argv[1], sys.argv[2]
src = open(amp + '/spice/ota1.spice').read()
def variant(area, perim, res):
    out = []
    for l in src.splitlines():
        m = re.match(r'(X\w+ .*? )W=\{(\w+)\}(.*?)ad=\S+ as=\S+ pd=\S+ ps=\S+ nrd=0 nrs=0(.*)', l)
        if m:
            P = m.group(2)
            ad = f'{{{P}*0.18u}}' if area else '0'; pp = f'{{2*({P}+0.18u)}}' if perim else '0'; rr = f'{{0.18u/{P}}}' if res else '0'
            l = f'{m.group(1)}W={{{P}}}{m.group(3)}ad={ad} as={ad} pd={pp} ps={pp} nrd={rr} nrs={rr}{m.group(4)}'
        out.append(l)
    return '\n'.join(out) + '\n'
for name, a in {'zero': (0,0,0), 'area': (1,0,0), 'perim': (0,1,0), 'res': (0,0,1), 'area_perim': (1,1,0), 'full': (1,1,1)}.items():
    open(f'{d}/ota_{name}.spice', 'w').write(variant(*a))
PY
  OPA=".options gmin=1e-16 abstol=1e-20 reltol=1e-4 itl1=500 itl4=500 chgtol=1e-19"
  mk() { sed -e "s#\.\./spice/ota1\.spice#$D/ota_$1.spice#" -e "s#^\.options .*#$2#" -e "s#\.\./spice/#$AMP/spice/#g" -e "s#^\.param TSTOP=.*#.param TSTOP=0.4#" -e "s#^\.param TMAXS=.*#.param TMAXS=0.01#" "$AMP/tb/tb_st1_tran.spice" > "$D/s_$3.spice"; }
  runone() { { echo "### $2"; (cd $AMP/tb && timeout 280 ngspice -b $D/s_$1.spice 2>&1 | cut -c1-230 | grep -E "RESULT_REC|imestep|Fatal|singular" | head -2); } > $D/r_$1.txt; }
  export -f runone; export D AMP
  mk zero "$OPA" zero_A3opt; mk area "$OPA" area_A3opt; mk perim "$OPA" perim_A3opt; mk res "$OPA" res_A3opt; mk area_perim "$OPA" areaperim_A3opt; mk full "$OPA" full_A3opt
  mk full "* default options (gmin=1e-12)" full_defopt; mk zero "* default options (gmin=1e-12)" zero_defopt
  mk full ".options gmin=1e-14 abstol=1e-20 reltol=1e-4 itl1=500 itl4=500 chgtol=1e-19" full_gmin1e-14
  for t in zero_A3opt area_A3opt perim_A3opt res_A3opt areaperim_A3opt full_A3opt full_defopt zero_defopt full_gmin1e-14; do echo "runone $t \"\$(echo $t)\""; done | par
  { echo "# tb_st1_tran (0.4 s), ota1 variants; A3 options = gmin=1e-16 abstol=1e-20 reltol=1e-4 itl1/4=500 chgtol=1e-19"
    echo "# variants: zero = ad/as/pd/ps/nrd/nrs all 0 (A3); area = ad,as=W*0.18u; perim = pd,ps=2(W+0.18u); res = nrd,nrs=0.18u/W; area_perim = A4a real; full = all"
    for t in zero_A3opt area_A3opt perim_A3opt res_A3opt areaperim_A3opt full_A3opt full_defopt zero_defopt full_gmin1e-14; do cat $D/r_$t.txt; done; } > "$AMP/sim/a4a_diag_tran.log"; echo "wrote sim/a4a_diag_tran.log" ;;
diffcheck)  # A3 testbenches unchanged (IDEAL bias, IDEAL vt), only DIFF=1 (real diffusion)
  for cs in op ol loop cl noise; do rm -rf $RUN/diff_$cs; done
  for c in $COMBOS; do k=${c%%:*}; T=${c##*:}; R=$(r0 $k $T)
    echo "job diff_op op_${k}_$T tb_ota1_op.spice $k $T DIFF=1"
    echo "job diff_ol ol_${k}_$T tb_ota1_ol.spice $k $T DIFF=1"
    echo "job diff_loop loop_${k}_$T tb_ota1_loop.spice $k $T DIFF=1"
    echo "job diff_cl cl_${k}_$T tb_st1_ac.spice $k $T DIFF=1"
    for fn in 0 1; do echo "job diff_noise noise_${k}_${T}_fn$fn tb_st1_noise.spice $k $T RFIX=$R FN=$fn DIFF=1"; done
  done | par
  for cs in op ol loop cl noise; do cat $RUN/diff_$cs/*.txt > "$AMP/sim/a4a_diff_$cs.log"; echo "wrote sim/a4a_diff_$cs.log ($(grep -c '^###' "$AMP/sim/a4a_diff_$cs.log") jobs)"; done ;;
op)    rm -rf $RUN/op; for c in $COMBOS; do k=${c%%:*}; T=${c##*:}; echo "job op op_${k}_$T tb_afe_1ch_op.spice $k $T"; done | par; fin op ;;
ac)    rm -rf $RUN/ac; for c in $COMBOS; do k=${c%%:*}; T=${c##*:}; echo "job ac ac_${k}_$T tb_afe_1ch_ac.spice $k $T"; done | par; fin ac ;;
acfs)  rm -rf $RUN/acfs; for c in $COMBOS; do k=${c%%:*}; T=${c##*:}; echo "job acfs acfs_${k}_$T tb_afe_1ch_ac.spice $k $T FSV=3.3"; done | par; fin acfs ;;
ol2)   rm -rf $RUN/ol2; for c in $COMBOS; do k=${c%%:*}; T=${c##*:}; echo "job ol2 ol2_${k}_$T tb_ota2_ol.spice $k $T"; done | par; fin ol2 ;;
psrr)  rm -rf $RUN/psrr; for c in $COMBOS; do k=${c%%:*}; T=${c##*:}; echo "job psrr psrr_${k}_$T tb_afe_1ch_psrr.spice $k $T"; done | par; fin psrr ;;
noise) rm -rf $RUN/noise   # IDEAL RESISTOR (noise) = R0 of the fixed-gate pseudo-R at each corner, both stages; typical flicker and fnoicor=1
  for c in $COMBOS; do k=${c%%:*}; T=${c##*:}; R=$(r0fg $k $T)
    for fn in 0 1; do echo "job noise noise_${k}_${T}_fn$fn tb_afe_1ch_noise.spice $k $T RFIX=$R RFIX2=$R FN=$fn"; done; done | par; fin noise ;;
vdd)   # supply sanity (PLAN T1, not a target): VSUP 3.0 / 3.3 / 3.6 V, ladders unchanged (designed for 3.3 V), typical 27 C
  rm -rf $RUN/vdd; for V in 3.0 3.3 3.6; do echo "job vdd op_V$V tb_afe_1ch_op.spice typical 27 VSUP=$V"; echo "job vdd ac_V$V tb_afe_1ch_ac.spice typical 27 VSUP=$V"; done | par; fin vdd ;;
plotdata) # 9-PVT Bode data for the figures (wrdata: frequency, channel gain dB, stage-1 gain dB) -> sim/a4a_bode_<corner>_<T>.csv
  pd1() { k=$1; T=$2; f="$AMP/tb/_pd_${k}_${T}.spice"
    sed -e "s#models_typical#models_${k}#" -e "s#^\.temp .*#.temp ${T}#" -e "s#^quit#wrdata ../sim/a4a_bode_${k}_${T}.csv gdb g1db\nquit#" "$AMP/tb/tb_afe_1ch_ac.spice" > "$f"
    (cd "$AMP/tb" && timeout 300 ngspice -b "$f" > /dev/null 2>&1); rm -f "$f"; }
  export -f pd1
  for c in $COMBOS; do k=${c%%:*}; T=${c##*:}; echo "pd1 $k $T"; done | par; ls "$AMP"/sim/a4a_bode_*.csv | wc -l ;;
nspec) # D0 (Decision 22): output noise spectra V/rtHz (IDEAL R = R0, fnoicor=0) at the f_hi extremes -> sim/a4a_nspec_<corner>_<T>.csv
  ns1() { k=$1; T=$2; R=$(r0fg $k $T); f="$AMP/tb/_ns_${k}_${T}.spice"
    sed -e "s#NSPECFILE#../sim/a4a_nspec_${k}_${T}.csv#" -e "s#models_typical#models_${k}#" -e "s#^\.temp .*#.temp ${T}#" -e "s#^\.param RFIX=.*#.param RFIX=$R#" -e "s#^\.param RFIX2=.*#.param RFIX2=$R#" "$AMP/tb/tb_afe_1ch_nspec.spice" > "$f"
    (cd "$AMP/tb" && timeout 600 ngspice -b "$f" > /dev/null 2>&1); rm -f "$f"; }
  export -f ns1
  for c in ff:85 typical:27 ss:-40; do k=${c%%:*}; T=${c##*:}; echo "ns1 $k $T"; done | par; ls "$AMP"/sim/a4a_nspec_*.csv ;;
*) echo "unknown case"; exit 1 ;;
esac
