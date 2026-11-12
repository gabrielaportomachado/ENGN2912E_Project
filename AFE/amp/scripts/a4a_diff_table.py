#!/usr/bin/env python3
"""A4a Decision 13: compare A3 logs (diffusion = 0) with the A4a reruns (real ad/as/pd/ps) over 9 PVT -> sim/a4a_diff_summary.txt"""
import re, os
A = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'sim') + '/'
def parse(path):
    d, cur = {}, None
    for l in open(path):
        if l.startswith('###'): cur = l[4:].strip(); d[cur] = []
        elif cur: d[cur].append(l.strip())
    return d
def kv(lines): return {k: float(v) for l in lines for k, v in re.findall(r'(\w+)=(-?\d+\.?\d*(?:[eE][-+]?\d+)?)', l)}
def op_metrics(lines):
    m = [float(re.search(r'margin_V=(\S+)', l).group(1)) for l in lines if l.startswith('OPDEV')]
    s = kv([l for l in lines if l.startswith('OPSUM')])
    return {'worst_margin_V': min(m), 'offset_uV': s['offset_V'] * 1e6, 'Isupply_uA': s['i_supply_A'] * 1e6}
out = []
def P(s=''): out.append(s)
combos = [f'{k}_{t}' for k in ('typical', 'ff', 'ss') for t in ('-40', '27', '85')]
spec = [('op', 'op', op_metrics, ['worst_margin_V', 'offset_uV', 'Isupply_uA']),
        ('ol', 'ol', lambda L: kv([l for l in L if l.startswith('RESULT')]), ['a0_dB', 'f_p1_Hz', 'gbw_Hz', 'pm_beta1_deg']),
        ('loop', 'loop', lambda L: kv([l for l in L if l.startswith('RESULT')]), ['T_100Hz_dB', 'fu_Hz', 'pm_deg']),
        ('cl', 'cl', lambda L: kv([l for l in L if l.startswith('RESULT')]), ['g_mid_dB', 'f_lo_Hz', 'f_hi_Hz'])]
P('A4a diffusion check (Decision 13): A3 netlist (ad/as/pd/ps = 0, sim/a3_*.log) vs real diffusion (ad=as=W*0.18u, pd=ps=2*(W+0.18u), nrd=nrs=0; sim/a4a_diff_*.log).')
P('Everything else is the A3 environment (IDEAL bias, IDEAL vt shifter).  Columns: typical 27 C old -> new, worst relative change over 9 PVT (abs change for margin/offset).')
P()
for cs, nm, f, keys in spec:
    new, old = parse(A + f'a4a_diff_{cs}.log'), parse(A + f'a3_{cs}.log')
    P(f'== {nm}')
    for key in keys:
        worst, ref = 0, None
        for c in combos:
            lab = f'{nm}_{c}'
            if lab not in new or lab not in old: continue
            o, n = f(old[lab])[key], f(new[lab])[key]
            d = abs(n - o) if key in ('worst_margin_V', 'offset_uV') else abs(n - o) / max(abs(o), 1e-30) * 100
            worst = max(worst, d)
            if c == 'typical_27': ref = (o, n)
        unit = '' if key in ('worst_margin_V', 'offset_uV') else ' %'
        P(f'  {key:16s} typical27 {ref[0]:.6g} -> {ref[1]:.6g}   worst change over 9 PVT {worst:.4g}{unit}')
P('== noise (IDEAL RESISTOR, R0 per corner; integrated output noise / midband gain, 0.5-300 Hz, uV)')
new, old = parse(A + 'a4a_diff_noise.log'), parse(A + 'a3_noise.log')
for fn in (0, 1):
    worst, ref, lo, hi = 0, None, 1e9, 0
    for c in combos:
        lab = f'noise_{c}_fn{fn}'
        g = lambda L: float(re.search(r'NOISE_B_0p5_300 .*?vn_in_mid_V=(\S+)', ' '.join(L)).group(1)) * 1e6
        o, n = g(old[lab]), g(new[lab]); worst = max(worst, abs(n - o) / o * 100); lo, hi = min(lo, n), max(hi, n)
        if c == 'typical_27': ref = (o, n)
    P(f'  fnoicor={fn}: typical27 {ref[0]:.4f} -> {ref[1]:.4f} uV; new range over 9 PVT {lo:.3f}-{hi:.3f} uV; worst change {worst:.3f} %')
open(A + 'a4a_diff_summary.txt', 'w').write('\n'.join(out) + '\n'); print('\n'.join(out))
