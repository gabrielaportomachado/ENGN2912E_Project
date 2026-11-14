#!/usr/bin/env python3
"""D1: tables from sim/d1_*.log -> sim/d1_summary.txt.  ICMR window definitions (trip point = input difference at which the decision flips, staircase 0.1 mV steps):
 functional : decision correct at +-1 LSB (0.806 mV) differential        |  +-2 LSB: and |trip(CM) - trip(1.65 V)| <= 2 LSB   |  +-0.5 LSB: ... <= 0.5 LSB (0.403 mV)
Demanded ranges: sim/d1_icmr_need.log (scripts/d1_icmr_need.py)."""
import re, glob, collections, numpy as np, os
D = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'sim'); LSB = 3.3 / 4096 * 1e6   # uV
out = []
def P(s=''): print(s); out.append(s)
def rd(n): p = f'{D}/d1_{n}.log'; return open(p).read().splitlines() if os.path.exists(p) else []
CN = {('typical', '27'): 'typ 27C', ('ff', '85'): 'ff 85C', ('ss', '-40'): 'ss -40C'}
# ---- delay / energy
P('== decision time (clk 50% -> |outp-outn| > VDD/2), ns, +d/-d, and energy per cycle (pJ, incl. clock inverter + buffers) =='); 
for l in rd('delay'):
    m = re.match(r'DELAY (\S+) (-?\d+)C (\S+) cm=(\S+) (.*)', l)
    if m: P(f'{CN[(m.group(1), m.group(2))]:8s} {m.group(3)} CM={m.group(4)} V: ' + ' | '.join(x for x in m.group(5).split() if re.match(r'(0.1|1|10|100|1000|2000)mV', x)))
# ---- offset
P('\n== input-referred offset (trip point), Monte Carlo sw_stat_mismatch=1, uV ==')
g = collections.defaultdict(list)
for l in rd('offset'):
    m = re.match(r'OFFSET (\S+) (-?\d+)C \S+ seed=\d+ trip_uV=(\S+) nflips=(\d+)', l)
    if m and m.group(3) != 'nan' and m.group(4) == '1': g[(m.group(1), m.group(2))].append(float(m.group(3)))
for k, v in g.items(): P(f'{CN[k]:8s} n={len(v)} mean {np.mean(v):7.0f}  sigma {np.std(v, ddof=1):6.0f} uV = {np.std(v, ddof=1)/LSB:.2f} LSB   min/max {min(v):.0f}/{max(v):.0f}   |max|/sigma {max(abs(x) for x in v)/np.std(v, ddof=1):.2f}')
# ---- noise
P('\n== input-referred noise (injected thermal noise on the input pair, probit fit) ==')
for l in rd('noise'):
    if l.startswith('NOISE'): P(l.replace('decisions1=', 'dec1='))
# ---- ICMR
P('\n== common-mode range of the comparator (symmetric +-d/2 around CM) vs demanded range ==')
ic = collections.defaultdict(dict)
for l in rd('icmr'):
    m = re.match(r'ICMR (\S+) (-?\d+)C (\S+) cm=(\S+) trip_uV=(\S+) nflips=(\d+) undecided=(\d+) correct_at_pm1LSB=(\d) max_delay_ns=(\S+)', l)
    if m: ic[(m.group(3), m.group(1), m.group(2))][float(m.group(4))] = (float(m.group(5)), int(m.group(6)), int(m.group(8)), float(m.group(9)))
def windows(d):
    cms = sorted(d); ref = d[min(cms, key=lambda c: abs(c - 1.65))][0]
    f = lambda pred: [c for c in cms if pred(d[c], c)]
    func = f(lambda v, c: v[2] == 1 and v[1] == 1)
    w2 = f(lambda v, c: v[2] == 1 and v[1] == 1 and abs(v[0] - ref) <= 2 * LSB)
    w05 = f(lambda v, c: v[2] == 1 and v[1] == 1 and abs(v[0] - ref) <= 0.5 * LSB)
    rng = lambda L: (f'{min(L):.2f}..{max(L):.2f} V' + ('' if len(L) == round((max(L) - min(L)) / 0.1) + 1 or True else '')) if L else 'none'
    def contig(L):
        S = set(round(x, 3) for x in L)
        if 1.65 not in S: return 'none at 1.65 V'
        k = cms.index(1.65); lo = hi = k
        while lo - 1 >= 0 and round(cms[lo - 1], 3) in S: lo -= 1
        while hi + 1 < len(cms) and round(cms[hi + 1], 3) in S: hi += 1
        return f'{cms[lo]:.2f}..{cms[hi]:.2f} V'
    return contig(func), contig(w2), contig(w05), ref
for cell in ('cmp_p', 'cmp_n'):
    for k in [('typical', '27'), ('ff', '85'), ('ss', '-40')]:
        d = ic.get((cell, k[0], k[1]))
        if d:
            a, b, c, ref = windows(d); P(f'{cell} {CN[k]:8s} ({len(d)} CM points)  functional {a}   | within 2 LSB of trip(1.65 V) {b}   | within 0.5 LSB {c}   (trip at 1.65 V = {ref:.0f} uV)')
P('\n== single-ended conventional test: Vref = 1.65 V fixed, Vx swept 0..3.3 V (sign must follow Vx - 1.65) =='); 
for l in rd('conv'): P(l)
# ---- kick
P('\n== kickback: charge drawn from the ideal input sources per clock cycle (fC) and dV on a 7 pF top plate (user decision: C_s = 7 pF) =='); 
for l in rd('kick'):
    P(l[:400])
open(f'{D}/d1_summary.txt', 'w').write('\n'.join(out) + '\n')
