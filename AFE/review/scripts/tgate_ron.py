#!/usr/bin/env python3
"""AUDIT step 8: the 5 V-device routing TGATE (TGATE/TGATE.spice, read only) at the single 3.3 V supply (Decision 30).
A4b measured Ron only over 1.15-2.15 V (sim/a4b_tg33_ron.log).  Here: Ron over the whole 0-VDD range (10 mV across the switch, C = VDD, CBAR = 0),
the OFF leakage (C = 0, CBAR = VDD, 1 V across) and the current into the supply when a pad is driven beyond the rails (body diodes).
usage: python3 tgate_ron.py [out.log]"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from ngjob import *
import numpy as np

CASES = [('typical', 27, 3.3), ('ff', 85, 3.3), ('ss', -40, 3.3), ('ss', -40, 3.0), ('ss', 125, 3.0), ('ff', -40, 3.6)]


def net(corner, temp, vdd, f):
    return '\n'.join(['* audit TGATE Ron / leakage', '.include %s/spice/models_%s.spice' % (AMP, corner), '.include %s/TGATE/TGATE.spice' % REPO,
                      '.options gmin=1e-15', '.temp %g' % temp,
                      'Vdd vdd 0 %g' % vdd, 'Vc c 0 %g' % vdd, 'Vcb cb 0 0', 'Vin in 0 1.65', 'Bo out 0 V = V(in) - 0.01',
                      'Xtg out c cb in vdd 0 TGATE',
                      '* OFF switch: 1 V across, and a pad driven beyond the rails',
                      'Vc2 c2 0 0', 'Vcb2 cb2 0 %g' % vdd, 'Vin2 in2 0 1.65', 'Vo2 out2 0 1.65', 'Xtg2 out2 c2 cb2 in2 vdd 0 TGATE',
                      '.control', 'dc Vin 0.0 %g 0.025' % vdd, 'let ron = 0.01/abs(i(Vin))', 'wrdata %s_on.dat ron' % f,
                      'dc Vin2 -0.8 %g 0.05' % (vdd + 0.8), 'let ioff = -i(Vin2)', 'wrdata %s_off.dat ioff' % f, 'echo DONE', 'quit', '.endc', '.end'])


if __name__ == '__main__':
    out = open(sys.argv[1], 'w') if len(sys.argv) > 1 else sys.stdout
    P = lambda *a: (print(*a, file=out), out.flush())
    P(__doc__.split('usage')[0].strip())
    d = os.path.join(PT, 'tg')
    os.makedirs(d, exist_ok=True)
    jobs = [('tg_%s_%d_%g' % (c, T, v), net(c, T, v, os.path.join(d, 'tg_%s_%d_%g' % (c, T, v)))) for (c, T, v) in CASES]
    res = run_jobs(jobs, 'tg', log=lambda s: None)
    vs = [0.0, 0.1, 0.3, 0.5, 0.825, 1.15, 1.65, 2.15, 2.475, 2.8, 3.0, 3.2, 3.3]
    P('\nON resistance [kOhm] vs signal voltage (both terminals at V, 10 mV across):')
    P('%-8s %4s %4s | ' % ('corner', 'T', 'VDD') + ' '.join('%7.3g' % v for v in vs) + ' |   max  at V')
    for (c, T, v) in CASES:
        f = os.path.join(d, 'tg_%s_%d_%g' % (c, T, v))
        if not os.path.exists(f + '_on.dat'):
            P('%-8s %4d %4.1f FAILED %s' % (c, T, v, res['tg_%s_%d_%g' % (c, T, v)]['abort']))
            continue
        a = np.loadtxt(f + '_on.dat')
        x, r = a[:, 0], a[:, 1] / 1e3
        P('%-8s %4d %4.1f | ' % (c, T, v) + ' '.join(('%7.1f' % np.interp(q, x, r)) if q <= v + 1e-9 else '      -' for q in vs) + ' | %6.1f  %.2f' % (r.max(), x[r.argmax()]))
    P('\nOFF switch (C = 0, CBAR = VDD), far side held at 1.65 V: current into the driven pin [A] vs its voltage (negative = flows out of the pin):')
    vo = [-0.8, -0.6, -0.4, -0.2, 0.0, 0.65, 1.65, 2.65, 3.3, 3.5, 3.7, 3.9, 4.1]
    P('%-8s %4s %4s | ' % ('corner', 'T', 'VDD') + ' '.join('%9.3g' % v for v in vo))
    for (c, T, v) in CASES:
        f = os.path.join(d, 'tg_%s_%d_%g' % (c, T, v))
        if not os.path.exists(f + '_off.dat'):
            continue
        a = np.loadtxt(f + '_off.dat')
        x, i = a[:, 0], a[:, 1]
        P('%-8s %4d %4.1f | ' % (c, T, v) + ' '.join(('%9.2e' % np.interp(q, x, i)) if q <= v + 0.8 + 1e-9 else '        -' for q in vo))
    if out is not sys.stdout:
        out.close()
    cleanup('tg')
