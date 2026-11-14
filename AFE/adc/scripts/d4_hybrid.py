#!/usr/bin/env python3
"""D4 HYBRID model (NOT a mixed-signal simulation): a vectorised Python SAR using
  - the D2 split-6+6 DAC network (d2lib.Dac, algebra verified against ngspice in D2), per-unit mismatch A_C = 0.5 %*um (sigma_u = A_C/5 um, Decision 26, ASSUMED),
  - the D1/D2 comparator: fixed evaluate shift (D2 flip reading 11.4 / 13.8 / 9.5 LSB typ / ff 85 / ss -40) + offset sigma 1.57 / 1.63 / 1.53 LSB (D1 MC) = a pure code shift per chip,
    pair noise 118 / 168 / 108 uV rms per decision (D1), latch noise ESTIMATE 50 uV rms (NOT measured: D1 open item; shown with and without), sampling kT/C 34 / 37 / 30 uV (D2),
  - the per-trial supply error of the D4 supply study (sim/d4_supply_3MHz.log, Rp 0.25 ohm, Rd 3 ohm, f = 0.5, ADC/trial table, random sign per trial fixed per chip).
usage: d4_hybrid.py dnl | enob      -> sim/d4_hybrid_dnl.log / sim/d4_hybrid_enob.log"""
import sys, os, re, numpy as np
H = os.path.dirname(os.path.abspath(__file__)); ADC = os.path.abspath(os.path.join(H, '..')); sys.path.insert(0, H)
from d2lib import *
CORN = {'typical': dict(shift=11.4, offs=1.57, npair=118e-6, ktc=34e-6, sup='tt_25'), 'ff': dict(shift=13.8, offs=1.63, npair=168e-6, ktc=37e-6, sup='ff_n40'), 'ss': dict(shift=9.5, offs=1.53, npair=108e-6, ktc=30e-6, sup='ss_125')}
AC = 0.5; SIGU = AC / 100 / 5.0
def supply_table(corner):
    """per-trial |error| [LSB] (f = 0.5) worst over the 8 ADCs, Rp 0.25 / Rd 3, from the supply log; zeros if the log is missing"""
    p = f'{ADC}/sim/d4_supply_3MHz.log'
    if not os.path.exists(p): return np.zeros(12)
    L = open(p).read().split('\n'); cn = CORN[corner]['sup']; on = False; rows = []
    for i, l in enumerate(L):
        if l.startswith('== corner'): on = cn in l
        if on and 'per-instant error f=0.5 [LSB], Rp 0.25 Rd 3' in l:
            rows = [np.array([float(x) for x in L[i + 1 + a].split()[1:]]) for a in range(8)]; break
    return np.max(rows, axis=0) if rows else np.zeros(12)
def sar(vin, lv, thr, nz=None):
    """vin: (n,) V; lv: DAC levels (4096,) V; thr: per-trial threshold offsets (12,) [V] (supply) plus scalar shift handled by caller; nz: (n, 12) noise [V] or None. returns codes"""
    code = np.zeros(len(vin), int)
    for k in range(12):
        j = 11 - k; tr = code | (1 << j); dec = vin >= lv[tr] + thr[k] + (0 if nz is None else nz[:, k]); code = np.where(dec, tr, code)
    return code
def chip(rng, corner, supply=True):
    d = Dac(sig=SIGU, rng=rng); lv = d.levels(); c = CORN[corner]
    S = (c['shift'] + rng.normal(0, c['offs'])) * LSB                      # comparator shift + offset (pure threshold shift)
    sup = supply_table(corner) * LSB * rng.choice([-1, 1], 12) if supply else np.zeros(12)
    return d, lv, S, sup
def dnlinl(lv, S, sup, ppl=32):
    vin = (np.arange(0, (4096 + 128) * ppl) - 64 * ppl) * (LSB / ppl) + 1e-9; code = sar(vin, lv, S + sup)
    first = np.full(4096, np.nan); idx = np.searchsorted(code, np.arange(4096), 'left')   # code is monotone only if the SAR is; use a robust first-hit instead
    for c in range(4096):
        w = np.nonzero(code == c)[0]
        if len(w): first[c] = vin[w[0]]
    return first, code
def stats(first):
    """codes 40..4055 (the comparator shift of 10-20 LSB moves the ends of the transfer curve out of the ramp; the ramp is extended by 64 LSB each side)"""
    cs = np.arange(40, 4056); T = first[cs]; ok = ~np.isnan(T); miss = int((~ok).sum())
    T = np.interp(cs, cs[ok], T[ok]); step = (T[-1] - T[0]) / (len(T) - 1); dnl = np.diff(T) / step - 1; inl = (T - T[0] - np.arange(len(T)) * step) / step
    return np.abs(dnl).max(), np.abs(inl).max(), miss, step / LSB
def enob_run(rng, corner, vdd_noise=False, latch=50e-6, N=1024, M=127, amp=0.49, mr=51, supply=True, ripa=10e-3, wnr=1e-3):
    d, lv, S, sup = chip(rng, corner, supply); c = CORN[corner]
    n = np.arange(N); vin = 1.65 + amp * np.sin(2 * np.pi * M * n / N)
    sig_n = np.sqrt(c['npair'] ** 2 + latch ** 2); nz = rng.normal(0, sig_n, (N, 12)); kt = rng.normal(0, c['ktc'], N)
    if not vdd_noise:
        code = sar(vin + kt, lv, S + sup, nz)
    else:
        # VREF = VDD ripple: DAC levels scale with VDD(t_k), the comparator reference (VDD/2 tap) tracks VDD, the plate charge was sampled at VDD(t_0):
        # decision k: sum_j w_j b_j (VDD+dk) - Vin*sum(w) + (d0 - dk)/2 >= shift  ->  Vin >= lv*(1+dk/VDD) + (d0 - dk)/2 + thr (with sum(w) = 1)
        VDD_ = 3.3; rip = ripa * np.sin(2 * np.pi * mr * n / N + 0.7)[:, None]            # 10 mV tone, bin 51, fixed over a 6 us conversion
        wn = rng.normal(0, wnr, (N, 13))                                                   # 1 mV rms white noise, independent per decision instant (bandwidth >> SCLK)
        d0 = (rip[:, 0] + wn[:, 0]); dk = rip + wn[:, 1:]
        code = np.zeros(N, int)
        for k in range(12):
            j = 11 - k; tr = code | (1 << j)
            lvl = lv[tr] * (1 + dk[:, k] / VDD_) + (d0 - dk[:, k]) / 2 + S + sup[k] + nz[:, k]
            code = np.where(vin + kt >= lvl, tr, code)
    x = code - code.mean(); X = np.fft.rfft(x * 1.0); P = np.abs(X) ** 2
    ps = P[M]; pn = P[1:].sum() - ps; sndr = 10 * np.log10(ps / pn); enob = (sndr - 1.76) / 6.02
    fs = (sndr - 1.76 + 20 * np.log10(3.3 / (2 * amp))) / 6.02
    return sndr, enob, fs
if __name__ == '__main__':
    out = []; P_ = lambda s='': (print(s, flush=True), out.append(s)); mode = sys.argv[1]
    if mode == 'dnl':
        P_('D4 HYBRID DNL/INL (python SAR, D2 DAC network, A_C 0.5 %*um, comparator shift+offset, supply per-trial error from d4_supply_3MHz.log); 32 inputs per LSB ramp, transitions = first input giving each code')
        nchip = 100
        for corner in CORN:
            rng = np.random.default_rng(1234); r = {'nom': [], 'mc': [], 'mc_nosup': []}
            d0 = Dac(); lv0 = d0.levels(); f0, _ = dnlinl(lv0, 0.0, np.zeros(12)); r['nom'] = stats(f0)
            for variant, sup_on in (('mc', True), ('mc_nosup', False)):
                res = []
                for i in range(nchip):
                    d, lv, S, sup = chip(rng, corner, sup_on); f, _ = dnlinl(lv, S, sup); res.append(stats(f))
                r[variant] = np.array(res)
            P_(f'  {corner}: ideal DAC, no comparator error: max|DNL| {r["nom"][0]:.3f} max|INL| {r["nom"][1]:.3f} LSB, missing {r["nom"][2]}')
            for v in ('mc_nosup', 'mc'):
                a = r[v]; P_(f'  {corner} MC {nchip} chips {"with supply error" if v == "mc" else "no supply error"}: max|DNL| median {np.median(a[:,0]):.2f} worst {a[:,0].max():.2f} ({(a[:,0]>1).mean()*100:.0f} % of chips > 1 LSB), max|INL| median {np.median(a[:,1]):.2f} worst {a[:,1].max():.2f} ({(a[:,1]>1).mean()*100:.0f} % > 1 LSB), chips with a missing code {(a[:,2]>0).mean()*100:.0f} %')
            P_(f'  {corner}: supply table used (|error| per trial, LSB): ' + ' '.join(f'{x:.2f}' for x in supply_table(corner)))
    else:
        P_('D4 HYBRID SNDR/ENOB: coherent sine N 1024, M 127, 0.49 V pk around 1.65 V (the claimed 1.15-2.15 V range); ENOB(raw) = (SNDR-1.76)/6.02 for the 0.98 Vpp signal, ENOB(FS) adds 20log(3.3/0.98) = 10.5 dB (referred to the 3.3 V full scale). 20 chips per case, noise + mismatch redrawn.')
        for corner in CORN:
            for lab, kw in (('no latch noise, ideal supply', dict(latch=0.0, supply=False)), ('latch 50 uV ESTIMATE + supply error', dict(latch=50e-6)), ('+ VDD noise (10 mV tone bin 51 + 1 mV rms white)', dict(latch=50e-6, vdd_noise=True))):
                rng = np.random.default_rng(99); a = np.array([enob_run(rng, corner, **kw) for _ in range(20)])
                P_(f'  {corner:8s} {lab:52s}: SNDR {a[:,0].mean():.1f} dB (min {a[:,0].min():.1f}), ENOB raw {a[:,1].mean():.2f} (min {a[:,1].min():.2f}), ENOB FS {a[:,2].mean():.2f} (min {a[:,2].min():.2f})')
    if mode == 'enob':
        for lab, kw in (('VDD tone only 10 mV', dict(ripa=10e-3, wnr=0.0)), ('VDD white noise only 1 mV rms', dict(ripa=0.0, wnr=1e-3)), ('VDD tone 1 mV pk', dict(ripa=1e-3, wnr=0.0))):
            rng = np.random.default_rng(99); a = np.array([enob_run(rng, 'typical', latch=50e-6, vdd_noise=True, **kw) for _ in range(20)])
            P_(f'  typical  {lab:52s}: SNDR {a[:,0].mean():.1f} dB, ENOB raw {a[:,1].mean():.2f}, ENOB FS {a[:,2].mean():.2f}')
    open(f'{ADC}/sim/d4_hybrid_{mode}.log', 'w').write('\n'.join(out) + '\n')
