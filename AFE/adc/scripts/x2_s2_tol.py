#!/usr/bin/env python3
"""X2 / S2: effect of a numerical setting on the AMPLIFIER ALONE (does the fix hide the fA leakage physics?).
Netlist: bias_genc + afe_chc (A4c) + Randles electrodes, 20 fF load, NO ADC.  From the DC operating point: 450 uV pk 62.5 Hz sine for 40 ms, then the output is compared between
the reference tolerance set (abstol 1e-15, the A4c/D5 set) and each variant, at 40 instants: max |difference| in uV and in LSB (0.806 mV), plus the DC operating point of the slow nodes.
usage: x2_s2_tol.py <corner key> "<variant options>" ["<variant options>" ...]      e.g.  x2_s2_tol.py typ "abstol=1e-12" "abstol=1e-13" "rshunt=1e12" "method=gear"
-> lines appended to sim/x2_s2_tol.log"""
import sys, os, re, numpy as np
H = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, H)
import x2lib as X
def net(ck, opts, tstop=40e-3, tmax='2u'):
    vdd = X.COR[ck][2]
    L = X.header(ck, f'S2 amplifier alone, options {opts}', amp=True, gmin='1e-16')
    if opts:
        ol = [l for l in L if l.startswith('.options')][0]; nl = ol
        for kv in opts.split():
            k = kv.split('=')[0]; nl = re.sub(rf'\b{k}=\S+', kv, nl) if re.search(rf'\b{k}=', nl) else nl + ' ' + kv
        L[L.index(ol)] = nl
    L += X.supply(vdd) + X.ref_electrode() + X.bias() + X.amp_channel(0, ['Vsin0 es0 tis SIN(0 0.45m 62.5 0 0 0)']) + ['Cl out0 vssi 20f']
    L += X.tail(['v(out0)', 'v(xch0.v1)', 'v(xch0.xs1.vn)', 'v(xch0.xs2.vn2)', 'v(vrs)', 'v(vcm)', 'v(vcmo)'], tstop, tmax, tstep='1u')
    return '\n'.join(L) + '\n'
if __name__ == '__main__':
    ck = sys.argv[1]; variants = sys.argv[2:]; names = ['ref'] + [f'v{i}' for i in range(len(variants))]
    res = X.run_jobs([(n, net(ck, o)) for n, o in zip(names, ['abstol=1e-15'] + variants)], tag='s2tol'); out = []      # the reference is the A4c / D5 set, set explicitly (x2lib's default is 1e-12)
    if not res['ref']['ok']: print('reference run failed', res['ref']['tail']); sys.exit(1)
    w0 = X.Wave(res['ref']['raw']); tt = np.linspace(1e-3, 39.9e-3, 40); LSB = 3.3 / 4096
    s = f'S2TOL {ck} reference (gmin 1e-16 abstol 1e-15 reltol 1e-4 vntol 1e-7 chgtol 1e-17): DC op out {w0.v("v(out0)")[0]:.6f} V, v1 {w0.v("v(xch0.v1)")[0]:.6f}, vn1 {w0.v("v(xch0.xs1.vn)")[0]:.6f}, vn2 {w0.v("v(xch0.xs2.vn2)")[0]:.6f}; out pk-pk {np.ptp(w0.v("v(out0)")):.4f} V; {len(w0.t)} points, wall {res["ref"]["wall"]:.0f} s'
    print(s); out.append(s)
    for n, o in zip(names[1:], variants):
        r = res[n]
        if not r['ok']: s = f'S2TOL {ck} "{o}": FAILED {r["tail"]}'
        else:
            w = X.Wave(r['raw'])
            if w.tend < 39.9e-3: s = f'S2TOL {ck} "{o}": ABORTED at {w.tend:.6f} s: {r["tail"]}'
            else:
                d = w.at('v(out0)', tt) - w0.at('v(out0)', tt); d1 = w.at('v(xch0.v1)', tt) - w0.at('v(xch0.v1)', tt)
                s = (f'S2TOL {ck} "{o}": DC op out {w.v("v(out0)")[0]:.6f} V ({(w.v("v(out0)")[0]-w0.v("v(out0)")[0])*1e6:+.1f} uV vs reference), v1 {(w.v("v(xch0.v1)")[0]-w0.v("v(xch0.v1)")[0])*1e6:+.2f} uV, vn1 {(w.v("v(xch0.xs1.vn)")[0]-w0.v("v(xch0.xs1.vn)")[0])*1e6:+.2f} uV, vn2 {(w.v("v(xch0.xs2.vn2)")[0]-w0.v("v(xch0.xs2.vn2)")[0])*1e6:+.2f} uV | '
                     f'transient 1-40 ms, output difference vs reference: max {np.abs(d).max()*1e6:.1f} uV = {np.abs(d).max()/LSB:.4f} LSB (rms {np.std(d)*1e6:.1f} uV), stage-1 output max {np.abs(d1).max()*1e6:.2f} uV | {len(w.t)} points, wall {r["wall"]:.0f} s')
        print(s); out.append(s)
    open(f'{X.ADC}/sim/x2_s2_tol.log', 'a').write('\n'.join(out) + '\n')
