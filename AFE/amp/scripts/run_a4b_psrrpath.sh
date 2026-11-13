#!/bin/bash
# A4b Decision 21(c): supply-to-output path decomposition at typical 27 C, before (VCM_IN 1.5 V, A4a) and after (VCM_IN 1.65 V, A4b) -> sim/a4b_psrrpath.log
# out(VDD) = sum_x T_x * r_x + direct, T_x = |v(out)| for 1 V injected in the wire of reference x, r_x = ripple of that reference per volt of VDD ripple.
AMP="$(cd "$(dirname "$0")/.." && pwd)"; LOG="$AMP/sim/a4b_psrrpath.log"; : > "$LOG"
for vc in 1.5 1.65; do
  echo "### VCM_IN=$vc  (VTT2 = 0.9, native-Vt follower; typical 27 C; VDD ripple 50 Hz unless noted)" >> "$LOG"
  for v in "ACVDD=1" "ACVDD=0 ACV_VCM=1" "ACVDD=0 ACV_VCMO=1" "ACVDD=0 ACV_VBN=1" "ACVDD=0 ACV_VG1=1" "ACVDD=0 ACV_VG2=1"; do
    echo "# $v" >> "$LOG"
    bash "$AMP/scripts/ngrun.sh" tb_afe_1ch_psrrpath.spice typical 27 VCM_IN=$vc $v 2>&1 | grep -E '^RESULT|rror' >> "$LOG"
  done
done
python3 - "$LOG" >> "$LOG" <<'PY'
import re, sys
txt = open(sys.argv[1]).read()
for blk in txt.split('### ')[1:]:
    head = blk.splitlines()[0]
    res = re.findall(r'RESULT (.*)', blk)
    kv = [dict((k, float(v)) for k, v in re.findall(r'(\w+)=(\S+)', r)) for r in res]
    tot, T = kv[0], {n: kv[i]['out_50'] for i, n in zip(range(1, 6), ['vcm(stage-1 ref)', 'vcmo(stage-2 ref)', 'vbn', 'vg1', 'vg2'])}
    r = {'vcm(stage-1 ref)': tot['r_vcm'], 'vcmo(stage-2 ref)': tot['r_vcmo'], 'vbn': tot['r_vbn'], 'vg1': tot['r_vg1'], 'vg2': tot['r_vg2']}
    print(f'\nPATHS {head[:30]}: total |out/vdd| @50 Hz = {tot["out_50"]:.4f} V/V')
    for k in T: print(f'   via {k:18s}: T = {T[k]:9.4f} V/V  x  ripple r = {r[k]:.4f}  -> {T[k]*r[k]:8.4f} V/V (magnitude; stage-1 ref and stage-2 ref enter with opposite sign)')
    print(f'   |T_vcmo r_vcmo - T_vcm r_vcm| = {abs(T["vcmo(stage-2 ref)"]*r["vcmo(stage-2 ref)"] - T["vcm(stage-1 ref)"]*r["vcm(stage-1 ref)"]):.4f}  vs total {tot["out_50"]:.4f} (residual = direct supply path + vbn/vg1/vg2)')
PY
echo "wrote sim/a4b_psrrpath.log"
