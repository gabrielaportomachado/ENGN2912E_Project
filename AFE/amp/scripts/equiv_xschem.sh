#!/bin/bash
# A3: netlist xschem/ota1.sch in batch and check it simulates the same as the hand netlist spice/ota1.spice.
# usage: bash scripts/equiv_xschem.sh      -> sim/a3_equiv_xschem.log
# NOTE: xschem hangs in batch mode if DISPLAY points at an unreachable X server; unset it (done below).
AMP="$(cd "$(dirname "$0")/.." && pwd)"
LOG="$AMP/sim/a3_equiv_xschem.log"; : > "$LOG"
( cd "$AMP/xschem" && mkdir -p netlist && unset DISPLAY && \
  timeout 120 xschem --rcfile xschemrc --tcl 'set top_is_subckt 1' -n -s -q --no_x -o netlist ota1.sch < /dev/null ) >> "$LOG" 2>&1
[ -s "$AMP/xschem/netlist/ota1.spice" ] || { echo "xschem netlist failed" | tee -a "$LOG"; exit 1; }
grep -v -i -E '^\.end *$' "$AMP/xschem/netlist/ota1.spice" > "$AMP/xschem/netlist/ota1_sub.spice"
grep -i -E '^\.subckt' "$AMP/xschem/netlist/ota1_sub.spice" >> "$LOG"
# structural check: normalised device lines of both netlists must be identical (node names, models, every parameter)
python3 - "$AMP" >> "$LOG" <<'PY'
import re, sys
amp = sys.argv[1]
def norm(p):
    txt = re.sub(r'\n\+\s*', ' ', open(p).read())
    dev = {}
    for l in txt.splitlines():
        l = l.strip().lower().replace("'", '').replace('{', '').replace('}', '')
        if not l or l[0] in '*.': continue
        tk = l.split(); name = tk[0]
        isx = name.startswith('x')
        k = next(i for i, x in enumerate(tk) if i > 0 and ('=' in x or x in ('pfet_03v3', 'nfet_03v3', 'cap_mim_2f0_m2m3_noshield')))
        mod = tk[k] if '=' not in tk[k] else None
        nodes = tk[1:k]; par = sorted(x for x in tk[k + (1 if mod else 0):] if not re.fullmatch(r'm=1', x))
        dev[name] = (tuple(nodes), mod, tuple(par))
    return dev
a, b = norm(amp + '/spice/ota1.spice'), norm(amp + '/xschem/netlist/ota1_sub.spice')
bad = [k for k in sorted(set(a) | set(b)) if a.get(k) != b.get(k)]
print(f'EQUIV structure: {len(a)} hand devices, {len(b)} xschem devices, differing: {bad if bad else "none"} -> {"PASS" if not bad and len(a) == len(b) else "FAIL"}')
PY
KEYS='^(RESULT|OPDEV|OPSUM|NOISE|ICMR)|[Ee]rror'
run() { # name tb corner T [overrides]  (hand | xschem)
  local nm=$1; shift
  bash "$AMP/scripts/ngrun.sh" "$@" 2>&1 | grep -E "$KEYS" > /tmp/eq_hand_$nm.txt
  OTA_NETLIST=../xschem/netlist/ota1_sub.spice bash "$AMP/scripts/ngrun.sh" "$@" 2>&1 | grep -E "$KEYS" > /tmp/eq_xs_$nm.txt
  python3 - "$nm" >> "$LOG" <<'PY'
import re, sys
nm = sys.argv[1]
def nums(p): return [float(x) for l in open(p) for x in re.findall(r'(?<=[=\s])-?\d+\.?\d*(?:[eE][-+]?\d+)?', l)]
a, b = nums(f'/tmp/eq_hand_{nm}.txt'), nums(f'/tmp/eq_xs_{nm}.txt')
if len(a) != len(b) or not a: print(f'EQUIV {nm}: FAIL (different number of values {len(a)} vs {len(b)})'); sys.exit()
worst = 0; wi = 0
for x, y in zip(a, b):
    d = abs(x - y) / max(abs(x), abs(y), 1e-9) if max(abs(x), abs(y)) > 1e-9 else 0   # values below 1 nV/nA treated as equal
    if d > worst: worst = d
print(f'EQUIV {nm}: {len(a)} values compared, worst relative difference {worst*100:.4g} % -> {"PASS" if worst < 1e-3 else "FAIL"} (limit 0.1 %)')
PY
}
run op   tb_ota1_op.spice typical 27
run ol   tb_ota1_ol.spice typical 27
run loop tb_ota1_loop.spice typical 27
run ac   tb_st1_ac.spice typical 27
run noise tb_st1_noise.spice typical 27 RFIX=5.24e12
run opff tb_ota1_op.spice ff 85
cat "$LOG" | grep -E 'EQUIV|subckt|rror'
