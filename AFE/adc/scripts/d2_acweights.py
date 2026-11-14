#!/usr/bin/env python3
"""D2: DAC bit weights from the PDK MIM netlist in ngspice (AC at 1 MHz) vs the python network model, per Monte Carlo draw.
modes: nominal | mismatch <A_C> <n> (per-unit random widths, own model, ASSUMPTION) | statistical <n> (PDK mimcap_statistical: global skew, sw_stat_global=1) ; corner typical/ff/ss for nominal.
usage: python3 scripts/d2_acweights.py <mode> [args]   -> sim/d2_acweights_<mode>.log"""
import sys, os, subprocess, tempfile, shutil, numpy as np, concurrent.futures as cf
H = os.path.dirname(os.path.abspath(__file__)); ADC = os.path.abspath(os.path.join(H, '..')); sys.path.insert(0, H)
from d2lib import *; from gen_dac import write_dac
TMP = tempfile.mkdtemp(prefix='d2ac_', dir=os.path.join(ADC, 'sim', '.ptmp'))
SRCS = [f'V{j}' for j in range(12)] + ['Vd']
def weights_spice(dacfile, tag, corner='typical', stat=None):
    out = {}
    for k, s in enumerate(SRCS):
        o = f'{TMP}/{tag}_{k}.txt'; n = f'{TMP}/{tag}_{k}.spice'
        t = open(f'{ADC}/tb/tb_dac_ac.spice').read().replace('@DACINC@', dacfile).replace('@OUT@', o).replace('@SRC@', s).replace('models_typical_mim', f'models_{corner}_mim')
        if stat is not None:
            t = t.replace('.param sw_stat_global=0', '.param sw_stat_global=1\n.options seed=%d' % stat).replace('models_typical_mim', 'models_statistical_mim')
        open(n, 'w').write(t)
        subprocess.run(['ngspice', '-b', n], cwd=f'{ADC}/tb', capture_output=True, text=True, timeout=300)
        r = open(o).read().split(); out[s] = (float(r[2]), float(r[3]))
    return out
def job(args):
    mode, k, ac, corner = args
    if mode == 'nominal': d = Dac()
    elif mode == 'mismatch': d = Dac(sig=ac / 100 / 5.0, rng=np.random.default_rng(1000 + k))
    else: d = Dac()
    f = f'{TMP}/dac_{mode}_{k}_{corner}.spice'; write_dac(f, d, corner)
    # the 'statistical' mode uses the nominal widths (the PDK skew multiplies every C)
    ws = weights_spice(f, f'{mode}{k}{corner}', corner, stat=(5000 + k) if mode == 'statistical' else None)
    return k, d, ws
if __name__ == '__main__':
    mode = sys.argv[1]; L = []
    def P(s=''): print(s); L.append(s)
    jobs = []
    if mode == 'nominal': jobs = [('nominal', 0, 0, c) for c in ('typical', 'ff', 'ss')]
    elif mode == 'mismatch': ac = float(sys.argv[2]); n = int(sys.argv[3]); jobs = [('mismatch', k, ac, 'typical') for k in range(1, n + 1)]
    else: n = int(sys.argv[2]); jobs = [('statistical', k, 0, 'typical') for k in range(1, n + 1)]
    tag = mode if mode != 'mismatch' else f'mismatch_{sys.argv[2]}'
    P(f'D2 AC-weight check ({mode}); ngspice weights from the PDK MIM netlist vs python network model.  LSB = {LSB*1e3:.4f} mV')
    with cf.ThreadPoolExecutor(7) as ex: res = list(ex.map(job, jobs))
    dmax, imax, dd, ii, cus = [], [], [], [], []
    for (mo, k, ac, corner), (kk, d, ws) in zip(jobs, res):
        w = np.array([ws[s][0] for s in SRCS[:12]]); wdum = ws['Vd'][0]; cu = ws['V0'][1]; cus.append(cu)
        wall = w.sum() + wdum
        codes = np.arange(4096); bits = ((codes[:, None] >> np.arange(12)) & 1).astype(float); lv = VDD * (bits @ w) / wall
        dn, inl, st = dnl_inl(lv); wp, wpd = d.weights(); lvp = d.levels(); dnp, inlp, _ = dnl_inl(lvp)
        dmax.append(np.abs(dn).max()); imax.append(np.abs(inl).max()); dd.append(np.abs(dn - dnp).max()); ii.append(np.abs(inl - inlp).max())
        P('  %-10s run %-3d %-7s Cu(probe) %.3f fF  sum(w)=%.5f  ngspice DNLmax %.3f INLmax %.3f | python DNLmax %.3f INLmax %.3f | max|DNL diff| %.2e  max|INL diff| %.2e LSB | max rel diff of weights %.1e' % (mo, k, corner, cu * 1e15, wall, np.abs(dn).max(), np.abs(inl).max(), np.abs(dnp).max(), np.abs(inlp).max(), dd[-1], ii[-1], np.abs(w / wp - 1).max()))
    P('SUMMARY %s: n=%d  ngspice DNLmax mean %.3f sigma %.3f max %.3f | INLmax mean %.3f sigma %.3f max %.3f | python-vs-ngspice max diff DNL %.1e INL %.1e LSB | unit-cap probe mean %.3f fF sigma %.3f fF (%.2f %%)' % (mode, len(jobs), np.mean(dmax), np.std(dmax), np.max(dmax), np.mean(imax), np.std(imax), np.max(imax), max(dd), max(ii), np.mean(cus) * 1e15, np.std(cus) * 1e15, 100 * np.std(cus) / np.mean(cus)))
    open(f'{ADC}/sim/d2_acweights_{tag}.log', 'w').write('\n'.join(L) + '\n'); shutil.rmtree(TMP, True)
