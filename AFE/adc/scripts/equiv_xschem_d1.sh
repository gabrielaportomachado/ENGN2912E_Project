#!/bin/bash
# D1: netlist xschem/cmp_p.sch + cmp_inv.sch in batch (unset DISPLAY, see AFE/NOTES.md) and check that they match the hand netlist spice/comparator.spice (structure) and simulate identically.
# usage: bash scripts/equiv_xschem_d1.sh  -> sim/d1_equiv_xschem.log
ADC="$(cd "$(dirname "$0")/.." && pwd)"; LOG="$ADC/sim/d1_equiv_xschem.log"; : > "$LOG"
( cd "$ADC/xschem" && mkdir -p netlist && unset DISPLAY && for c in cmp_inv cmp_p; do timeout 120 xschem --rcfile xschemrc --tcl 'set top_is_subckt 1' -n -s -q --no_x -o netlist $c.sch < /dev/null; done ) >> "$LOG" 2>&1
# cmp_p.spice already contains the expanded cmp_inv with its default WN/WP; also adding cmp_inv.spice defined it twice WITHOUT defaults and the xschem netlist errored (first version: every sim 'differed by 100 %' = it never ran)
grep -v -i -E '^\.end *$' "$ADC/xschem/netlist/cmp_p.spice" > "$ADC/xschem/netlist/comparator_sub.spice"
python3 - "$ADC" >> "$LOG" <<'PY'
import re, sys
adc = sys.argv[1]
MODELS = ('pfet_03v3', 'nfet_03v3')
def norm(p, want):
    txt = re.sub(r'\n\+\s*', ' ', open(p).read()); dev = {}; sub = None; keep = False
    for l in txt.splitlines():
        l = l.strip().lower().replace("'", '').replace('{', '').replace('}', '')
        if l.startswith('.subckt'): sub = l.split(); keep = sub[1] == want; sp = sub[2:] if keep else None
        if l.startswith('.ends'): keep = False
        if not keep or not l or l[0] in '*.': continue
        tk = l.split(); name = tk[0]
        if name.startswith('c'): dev[name] = (tuple(sorted(tk[1:3])), 'cap', (tk[3],))   # capacitor: terminals commutative
        else:
            k = next(i for i, x in enumerate(tk) if i > 0 and ('=' in x or x in MODELS or x.startswith('cmp_')))
            mod = tk[k] if '=' not in tk[k] else None
            dev[name] = (tuple(tk[1:k]), mod, tuple(sorted(x for x in tk[k + (1 if mod else 0):] if x != 'm=1')))
    return dev
ok_all = True
for cell, hand_f, xs_f in [('cmp_p', f'{adc}/spice/comparator.spice', f'{adc}/xschem/netlist/comparator_sub.spice'), ('cmp_inv', f'{adc}/spice/comparator.spice', f'{adc}/xschem/netlist/comparator_sub.spice')]:
    a, b = norm(hand_f, cell), norm(xs_f, cell)
    if cell == 'cmp_p':   # nets of the xschem instance lines (auto numbered nets are fine only if they do not occur) - compare everything
        pass
    bad = [k for k in sorted(set(a) | set(b)) if a.get(k) != b.get(k)]
    ok = not bad and len(a) == len(b); ok_all &= ok
    print(f'EQUIV structure {cell}: {len(a)} hand devices, {len(b)} xschem devices, differing: {bad if bad else "none"} -> {"PASS" if ok else "FAIL"}')
    for k in bad: print('   hand  ', k, a.get(k)); print('   xschem', k, b.get(k))
PY
cd "$ADC/tb"
# (the Monte-Carlo offset is NOT used here: with the same seed the agauss draws are assigned to devices in netlist order, which differs between the hand and the xschem netlist, so equal seeds give different random circuits)
for job in "delay typical 27 cmp_p cm=1.65" "icmr ss -40 cmp_p cm=0.3" "icmr ff 85 cmp_p cm=1.2" "kick typical 27 cmp_p cm=1.65"; do
  python3 "$ADC/scripts/d1_run.py" $job > /tmp/eqd_hand.txt 2>&1
  XSWAP="../spice/comparator.spice=../xschem/netlist/comparator_sub.spice" python3 "$ADC/scripts/d1_run.py" $job > /tmp/eqd_xs.txt 2>&1
  python3 - "$job" >> "$LOG" <<'PY'
import re, sys
f = lambda p: [float(x) for x in re.findall(r'-?\d+\.?\d*(?:e[-+]?\d+)?', open(p).read().split('\n')[0])]
a, b = f('/tmp/eqd_hand.txt'), f('/tmp/eqd_xs.txt')
worst = max((abs(x - y) / max(abs(x), abs(y), 1e-12) for x, y in zip(a, b)), default=1) if len(a) == len(b) and a else 1
print(f'EQUIV sim [{sys.argv[1]}]: {len(a)} numbers, worst relative difference {worst*100:.3g} % -> {"PASS" if worst < 0.02 else "FAIL"} (limit 2 %; trip points are quantised to 0.1 mV)')
PY
done
grep -E 'EQUIV|rror' "$LOG"
