#!/bin/bash
# A4a: netlist xschem/{ota1,ota2,bias_gen}.sch in batch and check they simulate like the hand netlists.
# usage: bash scripts/equiv_xschem_a4a.sh   -> sim/a4a_equiv_xschem.log
# NOTE: xschem hangs in batch mode if DISPLAY points at an unreachable X server; it is unset below.
AMP="$(cd "$(dirname "$0")/.." && pwd)"
LOG="$AMP/sim/a4a_equiv_xschem.log"; : > "$LOG"
for c in ota1 ota2 bias_gen; do
  ( cd "$AMP/xschem" && mkdir -p netlist && unset DISPLAY && timeout 120 xschem --rcfile xschemrc --tcl 'set top_is_subckt 1' -n -s -q --no_x -o netlist $c.sch < /dev/null ) >> "$LOG" 2>&1
  [ -s "$AMP/xschem/netlist/$c.spice" ] || { echo "xschem netlist of $c failed" | tee -a "$LOG"; exit 1; }
  grep -v -i -E '^\.end *$' "$AMP/xschem/netlist/$c.spice" > "$AMP/xschem/netlist/${c}_sub.spice"
done
python3 - "$AMP" >> "$LOG" <<'PY'
import re, sys
amp = sys.argv[1]
MODELS = ('pfet_03v3', 'nfet_03v3', 'cap_mim_2f0_m2m3_noshield', 'ppolyf_u_1k', 'ppolyf_u_3k')
def norm(p):
    txt = re.sub(r'\n\+\s*', ' ', open(p).read())
    dev, sub = {}, None
    for l in txt.splitlines():
        l = l.strip().lower().replace("'", '').replace('{', '').replace('}', '')
        if l.startswith('.subckt'): sub = l.split()[1:]
        if not l or l[0] in '*.': continue
        tk = l.split(); name = tk[0]
        k = next(i for i, x in enumerate(tk) if i > 0 and ('=' in x or x in MODELS))
        mod = tk[k] if '=' not in tk[k] else None
        nodes = list(tk[1:k])
        if mod and mod.startswith('ppolyf'): nodes = sorted(nodes[:2]) + nodes[2:]       # two-terminal resistor: terminals commutative
        par = sorted(x for x in tk[k + (1 if mod else 0):] if not re.fullmatch(r'm=1', x))
        par = [re.sub(r'^(w|l)=', lambda m: 'r_width=' if False else m.group(0), x) for x in par]
        dev[name] = (tuple(nodes), mod, tuple(par))
    return sub, dev
def canon(dev):
    # resistor parameter names differ in order only (r_width/r_length); values are compared as sets
    return {k: (n, m, tuple(sorted(p))) for k, (n, m, p) in dev.items()}
for c in ('ota1', 'ota2', 'bias_gen'):
    sa, a = norm(f'{amp}/spice/{c}.spice'); sb, b = norm(f'{amp}/xschem/netlist/{c}_sub.spice')
    a, b = canon(a), canon(b)
    bad = [k for k in sorted(set(a) | set(b)) if a.get(k) != b.get(k)]
    print(f'EQUIV structure {c}: pins hand {sa} vs xschem {sb}: {"same" if sa == sb else "DIFFERENT"}; {len(a)} hand devices, {len(b)} xschem devices, differing: {bad if bad else "none"} -> {"PASS" if not bad and len(a) == len(b) and sa == sb else "FAIL"}')
    for k in bad: print('   hand  ', k, a.get(k)); print('   xschem', k, b.get(k))
PY
export EXTRAOPT="reltol=1e-7 vntol=1e-9"   # same operating point for both netlists (high-impedance DC nodes are sensitive to the Newton stop)
KEYS='^(RESULT|OPDEV|OPSUM|OPNODE|NOISE)|[Ee]rror'
SW="../spice/ota1.spice=../xschem/netlist/ota1_sub.spice ../spice/ota2.spice=../xschem/netlist/ota2_sub.spice ../spice/bias_gen.spice=../xschem/netlist/bias_gen_sub.spice"
run() { # name tb corner T [overrides]
  local nm=$1; shift
  bash "$AMP/scripts/ngrun.sh" "$@" 2>&1 | grep -E "$KEYS" > /tmp/eqa_hand_$nm.txt
  SWAPS="$SW" bash "$AMP/scripts/ngrun.sh" "$@" 2>&1 | grep -E "$KEYS" > /tmp/eqa_xs_$nm.txt
  python3 - "$nm" >> "$LOG" <<'PY'
import re, sys
nm = sys.argv[1]
def kv(p):
    out = []
    for l in open(p):
        out += [(l.split()[1] if l.startswith('OPDEV') else '') + k for k, v in re.findall(r'(\w+)=(-?\d+\.?\d*(?:[eE][-+]?\d+)?)', l)] and \
               [((l.split()[1] if l.startswith('OPDEV') else '') + k, float(v)) for k, v in re.findall(r'(\w+)=(-?\d+\.?\d*(?:[eE][-+]?\d+)?)', l)]
    return out
a, b = kv(f'/tmp/eqa_hand_{nm}.txt'), kv(f'/tmp/eqa_xs_{nm}.txt')
if len(a) != len(b) or not a: print(f'EQUIV {nm}: FAIL (different number of values {len(a)} vs {len(b)})'); sys.exit()
worst_rel, worst_abs, wk = 0, 0, ''
for (k, x), (k2, y) in zip(a, b):
    if k.endswith('err_V') or k.endswith('offset_V'):       # difference of two nearly equal voltages: compare absolutely (V)
        worst_abs = max(worst_abs, abs(x - y))
    elif max(abs(x), abs(y)) > 1e-9:
        d = abs(x - y) / max(abs(x), abs(y))
        if d > worst_rel: worst_rel, wk = d, k
ok = worst_rel < 1e-2 and worst_abs < 5e-4
print(f'EQUIV {nm}: {len(a)} values compared, worst relative difference {worst_rel*100:.4g} % ({wk}), worst absolute difference of the *_err/offset voltages {worst_abs*1e3:.3g} mV -> {"PASS" if ok else "FAIL"} (limits 1 %, 0.5 mV)')
PY
}
run op_typ27 tb_afe_1ch_op.spice typical 27
run op_ff85  tb_afe_1ch_op.spice ff 85
run ac_typ27 tb_afe_1ch_ac.spice typical 27
run ac_ss40  tb_afe_1ch_ac.spice ss -40
run ol2      tb_ota2_ol.spice typical 27
run noise    tb_afe_1ch_noise.spice typical 27 RFIX=5.236e12 RFIX2=5.236e12
grep -E 'EQUIV|rror' "$LOG"
