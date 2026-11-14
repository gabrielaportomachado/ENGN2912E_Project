#!/usr/bin/env python3
"""D2 DAC DNL/INL from unit-cap mismatch (own per-unit model, ASSUMPTION: sigma(dC/C) = A_C / sqrt(W*L), A_C swept 0.25/0.5/1 %*um) -> sim/d2_dnl.log
Exact charge-sharing network (d2lib.Dac), no SPICE here; scripts/d2_acweights.py checks the same weights against the PDK netlist in ngspice.
Run: python3 scripts/d2_dnl.py"""
import os, sys, numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); from d2lib import *
LOG = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'sim', 'd2_dnl.log'); L = []
def P(s=''): print(s); L.append(s)
def mc(n, sig, **kw):
    out = []
    for s in range(1, n + 1):
        d = Dac(rng=np.random.default_rng(1000 + s), sig=sig, **kw); dn, inl, st = dnl_inl(d.levels())
        out.append((np.abs(dn).max(), np.abs(inl).max(), dn.min(), int(np.argmax(np.abs(dn))) + 1))
    return np.array(out)
def stat(a, tag, nrun):
    P('   %-34s n=%-5d DNLmax: mean %.2f sigma %.2f max %.2f | INLmax: mean %.2f sigma %.2f max %.2f | runs with DNL<-1 (missing code): %d | |DNL|>1: %d | |INL|>1: %d | |INL|>2: %d' % (tag, nrun, a[:, 0].mean(), a[:, 0].std(), a[:, 0].max(), a[:, 1].mean(), a[:, 1].std(), a[:, 1].max(), (a[:, 2] < -1).sum(), (a[:, 0] > 1).sum(), (a[:, 1] > 1).sum(), (a[:, 1] > 2).sum()))
P('D2 DAC mismatch (ALGEBRA on the exact capacitor network; every unit is an independent Gaussian; A_C = matching constant in %%*um, sigma_unit = A_C/sqrt(area_um2)).  LSB = %.4f mV.' % (LSB * 1e3))
d = Dac(); P('== 0. Nominal check: split 6+6, 5x5 um unit (%.2f fF typ), bridge %.2f fF = %.4f units, total %.3f pF (%d unit-caps + bridge); ideal DNL/INL max = %.1e / %.1e LSB' % (CU * 1e15, d.cb * 1e15, d.cb / CU, (d.units.sum() + d.cb) * 1e12, len(d.units), np.abs(dnl_inl(d.levels())[0]).max(), np.abs(dnl_inl(d.levels())[1]).max()))
w, wd = d.weights(); P('   node T load (comparator plate) C_T = 63 units + series(bridge, LSB array 64 units) = %.3f pF;  C on bottoms (input load) = %.3f pF;  weights x4096: ' % ((d.units[64:].sum() + d.cb * d.units[:64].sum() / (d.cb + d.units[:64].sum())) * 1e12, d.units.sum() * 1e12) + ' '.join('%.4f' % x for x in (w * 4096)))
P(); P('== 1. Monte Carlo, 50 runs per A_C (headline), split 6+6, 5x5 um units, no parasitics.  Worst transition is nearly always the MSB carry (code 2048) and the next carries (1024, 3072, ...)')
res = {}
for ac in (0.25, 0.5, 1.0):
    sig = ac / 100 / 5.0; a = mc(50, sig); res[ac] = a
    stat(a, 'A_C=%.2f %%*um (sigma_u %.3f %%)' % (ac, sig * 100), 50)
    P('      worst-code histogram (code index of max |DNL|): ' + ', '.join('%d:%d' % (c, n) for c, n in zip(*np.unique(a[:, 3], return_counts=True))))
P(); P('== 2. Same, 2000 runs (tail statistics; ALGEBRA, extra to the 30-50 run ngspice-weights check in d2_acweights.py)')
for ac in (0.25, 0.5, 1.0):
    sig = ac / 100 / 5.0; a = mc(2000, sig); stat(a, 'A_C=%.2f %%*um' % ac, 2000)
    P('      percentiles of DNLmax 50/90/99 %%: %.2f / %.2f / %.2f   INLmax 50/90/99 %%: %.2f / %.2f / %.2f LSB' % (*np.percentile(a[:, 0], [50, 90, 99]), *np.percentile(a[:, 1], [50, 90, 99])))
P(); P('== 3. Design alternatives for the same MC (A_C = 0.5 %*um, 2000 runs; unit side in um, split m MSB bits + l LSB bits); area = number of unit caps x side^2 (drawn, no dummies/routing)')
P('   %-26s %8s %9s %12s | %-30s %-30s %s' % ('option', 'C_total', 'area um2', 'C_T', 'DNLmax mean/sigma/max', 'INLmax mean/sigma/max', 'P(|DNL|>1) P(|INL|>1)'))
for nm, m, l, side in (('6+6, 5x5 (chosen)', 6, 6, 5.0), ('7+5, 5x5 (fallback)', 7, 5, 5.0), ('8+4, 5x5', 8, 4, 5.0), ('6+6, 8x8', 6, 6, 8.0), ('7+5, 8x8', 7, 5, 8.0), ('binary 12+0, 5x5 (D0b: rejected)', 12, 0, 5.0)):
    if m == 12:
        cu = mim_c(side * 1e-6, side * 1e-6); sig = 0.5 / 100 / side; d0 = Dac(m=12, l=0, cu=cu); ctot = d0.units.sum(); area = len(d0.units) * side**2; ct = ctot
        r = []
        for s in range(1, 301):
            dd = Dac(m=12, l=0, cu=cu, sig=sig, rng=np.random.default_rng(s)); dn, inl, st = dnl_inl(dd.levels()); r.append((np.abs(dn).max(), np.abs(inl).max()))
        a = np.array(r); n = 300
    else:
        cu = mim_c(side * 1e-6, side * 1e-6); sig = 0.5 / 100 / side; d0 = Dac(m=m, l=l, cu=cu); ctot = d0.units.sum() + d0.cb; area = (len(d0.units) + 1) * side**2
        nl = 2**l; ct = d0.units[nl:].sum() + d0.cb * d0.units[:nl].sum() / (d0.cb + d0.units[:nl].sum())
        r = []
        for s in range(1, 2001):
            dd = Dac(m=m, l=l, cu=cu, sig=sig, rng=np.random.default_rng(s)); dn, inl, st = dnl_inl(dd.levels()); r.append((np.abs(dn).max(), np.abs(inl).max()))
        a = np.array(r); n = 2000
    P('   %-26s %6.2f pF %9.0f %9.2f pF | %5.2f / %5.2f / %5.2f              %5.2f / %5.2f / %5.2f              %.3f      %.3f   (n=%d)' % (nm, ctot * 1e12, area, ct * 1e12, a[:, 0].mean(), a[:, 0].std(), a[:, 0].max(), a[:, 1].mean(), a[:, 1].std(), a[:, 1].max(), (a[:, 0] > 1).mean(), (a[:, 1] > 1).mean(), n))
P(); P('== 4. Parasitic capacitance on the LSB-array node M (routing + switch junction), nominal unit caps; bridge uncompensated (ideal 64/63 unit) vs compensated (bridge re-sized so that LSB weights are exactly 1/64 of the MSB-array LSB)')
from scipy.optimize import brentq
P('   Cp_M[fF]   uncompensated: DNLmax  INLmax  | compensated bridge [fF] (width at 5 um length [um])   DNLmax INLmax | residual if Cp_M is mis-estimated by +-1 fF after compensation: DNLmax / INLmax')
for cpm in (0, 1, 2, 5, 10, 20):
    d = Dac(cpm=cpm * 1e-15); dn, inl, st = dnl_inl(d.levels())
    def err(cb):
        dd = Dac(cpm=cpm * 1e-15, cb=cb); w, wd = dd.weights(); return w[6] / w[0] - 64
    cb = brentq(err, 0.5 * CU, 3 * CU, xtol=1e-21, rtol=1e-12); dc = Dac(cpm=cpm * 1e-15, cb=cb); dnc, inlc, _ = dnl_inl(dc.levels())
    dm = [dnl_inl(Dac(cpm=(cpm + e) * 1e-15, cb=cb).levels()) for e in (-1, 1)]
    P('   %6.1f              %6.3f  %6.3f   |   %8.3f (%6.3f)                       %6.3f %6.3f | %.3f / %.3f' % (cpm, np.abs(dn).max(), np.abs(inl).max(), cb * 1e15, width_for(cb) * 1e6, np.abs(dnc).max(), np.abs(inlc).max(), max(np.abs(x[0]).max() for x in dm), max(np.abs(x[1]).max() for x in dm)))
P('   (1 fF = %.1f %% of a unit; the uncompensated error is a pure gain error of the 6-bit LSB array: 1 LSB step at the carries = 64 * Cp_M/(C of the array) ... see the table.)' % (1e-15 / CU * 100))
P(); P('== 5. Parasitic on the comparator node T (fF): attenuation only (gain, not DNL).  nominal caps: Cp_T = 0 / 100 / 190 / 300 fF')
for cpt in (0, 100, 190, 300):
    d = Dac(cpt=cpt * 1e-15); dn, inl, st = dnl_inl(d.levels()); w, wd = d.weights()
    P('   Cp_T %4d fF: DNLmax %.2e INLmax %.2e LSB; sum of weights (signal attenuation V_T per V_in) %.4f' % (cpt, np.abs(dn).max(), np.abs(inl).max(), w.sum() + wd))
open(LOG, 'w').write('\n'.join(L) + '\n')
