#!/bin/bash
# A3 diagnostics -> sim/a3_diag.log
#  (1) gain split: REC-only / REF-only / common-mode / differential drive of the real stage 1 (typ 27C, simulated pseudo-R)
#  (2) loop-gain plateau test: T(100 Hz) with the non-inverting gate vp AC-grounded by an IDEAL 1 F capacitor (hypothesis: M2 Cgd
#      feedthrough from the high-gain o1 node onto vp is what holds T below A0*beta)
AMP="$(cd "$(dirname "$0")/.." && pwd)"; LOG="$AMP/sim/a3_diag.log"; : > "$LOG"; cd "$AMP"
for v in "rec 1 0" "ref 0 -1" "cm 1 1" "diff 0.5 -0.5"; do set -- $v
  sed "s/^E1 s1 tis vd 0 .*/E1 s1 tis vd 0 $2/; s/^E2 s2 tis vd 0 .*/E2 s2 tis vd 0 $3/" spice/src_randles.spice > /tmp/src_$1.spice
  sed "s#\.\./spice/src_randles\.spice#/tmp/src_$1.spice#" tb/tb_st1_ac.spice > tb/zz_diag.spice
  echo "### gain_split_$1 (E1=$2 E2=$3)" >> "$LOG"; bash scripts/ngrun.sh zz_diag.spice typical 27 2>&1 | grep -E '^RESULT' | cut -c1-160 >> "$LOG"
done
# ideal-R reference (pseudo-R devices replaced by IDEAL resistors of the same R0): isolates the pseudo-R parasitic capacitance
echo "### gain_idealR_5.24T (pseudo-R devices replaced, RMODE=1)" >> "$LOG"
bash scripts/ngrun.sh tb_st1_ac.spice typical 27 RMODE=1 RFIX=5.24e12 2>&1 | grep -E '^RESULT' | cut -c1-160 >> "$LOG"
sed 's#^Xota vp vng ibias vout vdd vss ota1#Xota vp vng ibias vout vdd vss ota1\nCvp_ground vp 0 1   $ IDEAL AC ground on the non-inverting gate (diagnostic only)#' spice/stage1.spice > /tmp/stage1_vpgnd.spice
echo "### loop_T_normal" >> "$LOG"; bash scripts/ngrun.sh tb_ota1_loop.spice typical 27 2>&1 | grep -E '^RESULT' | cut -c1-160 >> "$LOG"
sed "s#\.\./spice/stage1\.spice#/tmp/stage1_vpgnd.spice#" tb/tb_ota1_loop.spice > tb/zz_diag.spice
echo "### loop_T_vp_ac_grounded" >> "$LOG"; bash scripts/ngrun.sh zz_diag.spice typical 27 2>&1 | grep -E '^RESULT' | cut -c1-160 >> "$LOG"
rm -f tb/zz_diag.spice sim/a3_loop_bode.csv sim/a3_cl_bode.csv
cat "$LOG"
