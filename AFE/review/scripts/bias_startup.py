#!/usr/bin/env python3
"""AUDIT step 8 (robustness): start-up of bias_genc with the vbn gate load of N channels.
A4b measured the master start-up with ONE channel (0.55 ms typ, 611 ms at ss -40 C: the 3-diode start-up stack only conducts at leakage level when cold/slow).
The chip has 8 channels on vbn: per channel 30 x 16u/4u mirror gates (OTA1 sink x24, follower sink x6) + stage-2 tail 1u/20u + one-shot leg 0.28u/40u.
Netlist: bias_genc (design file, read only) + that load x N; VDD ramps 0 -> VDD in 1 ms from the all-zero state (no nodesets, as A4b).
t90 = time after the START of the ramp at which the master current (Xmn1) reaches 90 % of its final value.
Not a switching transient: abstol 1e-16 (A4b used 1e-20; 1e-12 would be coarser than the pA start-up current).  usage: python3 bias_startup.py [out.log]"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from ngjob import *
import numpy as np

CASES = [('typical', 27, 3.3, 0.2), ('ff', 85, 3.3, 0.2), ('ss', -40, 3.3, 30.0), ('ss', -40, 3.0, 60.0), ('typical', -40, 3.3, 10.0), ('ss', 27, 3.3, 5.0)]


def net(corner, temp, vdd, n, tstop, abstol='1e-16', tmax='10m'):
    d = 'ad=2.88p as=2.88p pd=32.36u ps=32.36u nrd=0 nrs=0'
    L = ['* audit: bias_genc start-up with the vbn load of %d channel(s), %s %g C VDD %g' % (n, corner, temp, vdd)]
    L += amp_includes(corner)[:1] + ['.include %s/spice/%s.spice' % (AMP, f) for f in ('ota1_params', 'afe_params', 'a4c_params', 'bias_genc')]
    L += ['.options gmin=1e-16 abstol=%s reltol=1e-4 vntol=1e-7 chgtol=1e-17 itl1=500 itl4=500' % abstol, '.temp %g' % temp,
          'Vdd vdd 0 PWL(0 0 1m %g)' % vdd,
          'Xbias vbn vcm vg1 vcmo vg2 vrs vdd 0 bias_genc',
          '* load of N channels on vbn (afe_chc Xsink1 m=24 into the OTA1 bias diode Xmb m=2; ota2 Xms m=6 and Xmt; fs_oneshot_c Xlt)',
          'Xsink ib vbn 0 0 nfet_03v3 W=16u L=4u nf=1 %s m=%d' % (d, 24 * n),
          'Xdio ib ib vdd vdd pfet_03v3 W=50u L=4u nf=1 ad=9p as=9p pd=100.36u ps=100.36u nrd=0 nrs=0 m=%d' % (2 * n),
          'Emid mid 0 vdd 0 0.5',
          'Xms mid vbn 0 0 nfet_03v3 W=16u L=4u nf=1 %s m=%d' % (d, 6 * n),
          'Xmt2 mid vbn 0 0 nfet_03v3 W=1u L=20u nf=1 ad=0.18p as=0.18p pd=2.36u ps=2.36u nrd=0 nrs=0 m=%d' % n,
          'Xlt vdd vbn 0 0 nfet_03v3 W=0.28u L=40u nf=1 ad=0.05p as=0.05p pd=0.92u ps=0.92u nrd=0 nrs=0 m=%d' % n,
          '.control', 'save v(vbn) v(vcm) v(vrs) v(vdd) @m.xbias.xmn1.m0[id] @m.xsink.m0[id]',
          'tran 1u %g 0 %s' % (tstop, tmax),
          'wrdata @OUT@ v(vbn) @m.xbias.xmn1.m0[id] @m.xsink.m0[id] v(vcm) v(vrs)', 'echo DONE', 'quit', '.endc', '.end']
    return '\n'.join(L)


def analyse(fn):
    a = np.loadtxt(fn)
    t = a[:, 0]
    vbn, im, isk, vcm, vrs = a[:, 1], a[:, 3], a[:, 5], a[:, 7], a[:, 9]
    fin = np.mean(im[t > 0.9 * t[-1]])
    i90 = np.argmax(im >= 0.9 * fin)
    t90 = t[i90] if im[i90] >= 0.9 * fin else float('nan')
    settled = abs(im[-1] - fin) < 0.01 * abs(fin) and abs(np.mean(im[(t > 0.8 * t[-1]) & (t < 0.9 * t[-1])]) - fin) < 0.02 * abs(fin)
    return dict(t90=t90, im=fin, isk=np.mean(isk[t > 0.9 * t[-1]]), vbn=vbn[-1], vcm=vcm[-1], vrs=vrs[-1], settled=settled, tend=t[-1])


if __name__ == '__main__':
    out = open(sys.argv[1], 'w') if len(sys.argv) > 1 else sys.stdout
    P = lambda *a: (print(*a, file=out), out.flush())
    P(__doc__.split('usage')[0].strip())
    P('%-8s %4s %4s %2s | %10s %10s %10s %8s %8s %8s %s' % ('corner', 'T', 'VDD', 'N', 't90_ms', 'Imaster_uA', 'Isink_uA', 'vbn_V', 'vcm_V', 'vrs_V', 'final state reached inside the window'))
    d = os.path.join(PT, 'bst')
    os.makedirs(d, exist_ok=True)
    jobs = []
    for (c, T, v, ts) in CASES:
        for n in (1, 8):
            nm = 'bst_%s_%d_%g_n%d' % (c, T, v, n)
            jobs.append((nm, net(c, T, v, n, ts if n == 8 else max(ts / 4, 0.2)).replace('@OUT@', os.path.join(d, nm + '.dat'))))
    # sensitivity of the cold case to the tolerance (one job)
    jobs.append(('bst_ss_-40_3.3_n8_abstol1e-13', net('ss', -40, 3.3, 8, 30.0, abstol='1e-13').replace('@OUT@', os.path.join(d, 'bst_ss_-40_3.3_n8_abstol1e-13.dat'))))
    res = run_jobs(jobs, 'bst', wall=1700.0, log=lambda s: P(s))
    for nm, _ in jobs:
        f = os.path.join(d, nm + '.dat')
        if not os.path.exists(f):
            P('%s: NO RESULT %s' % (nm, res[nm]['abort']))
            continue
        r = analyse(f)
        P('%-34s | t90 %10.3f ms  Imaster %8.4f uA  Isink(N x 24) %9.3f uA  vbn %6.4f  vcm %6.4f  vrs %6.4f  %s (window %.1f s, wall %.0f s)' % (
            nm, r['t90'] * 1e3, r['im'] * 1e6, r['isk'] * 1e6, r['vbn'], r['vcm'], r['vrs'], 'settled' if r['settled'] else 'NOT SETTLED', r['tend'], res[nm]['wall']))
    if out is not sys.stdout:
        out.close()
    cleanup('bst')
