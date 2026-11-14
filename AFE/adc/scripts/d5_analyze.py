#!/usr/bin/env python3
"""D5 item 2 analysis (HYBRID): feeds the sampled values of the transistor-level amplifier + real switch (sim/d5_<tag>_<corner>.npz) to the D4 hybrid SAR model.
usage: d5_analyze.py <tag,tag,...> [nchips=20]   -> sim/d5_sndr.log
Sample fed to the SAR = out_L(t_s) + r, with out_L = amplifier output of the loaded copy just before CS falling, r = the residual of the plate-derived sampled value (V_T read after the sample, inverted with the
D2 network relation) from its straight-line fit against out_L (removes the gain/offset of the inversion, keeps the sampling nonlinearity, charge injection and the switch/DAC settling error)."""
import sys, os, numpy as np
H = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, H)
import d4_hybrid as hy, d5lib as L
LSB = 3.3 / 4096; CK = {'typical': 'typical', 'ff': 'ff', 'ss': 'ss'}
AMPN = {'typical': 1.826e-6, 'ff': 2.055e-6, 'ss': 1.641e-6}          # input-referred 0.5 Hz - 1 MHz, A4c sim/a4c_noise.log NOISE_D (typical flicker, ideal R); output = x 1000
# D4b replay, plate error above the Vin = 1.2345 baseline at the end of the 12 trials [LSB] (sim/d4_replay.log): ff 85 C, ss 125 C; typ: only 2.1 V (+0.97): scaled ff curve (ASSUMPTION)
TAB = {'ff': ([1.65, 1.8, 1.9, 2.0, 2.05, 2.1, 2.15], [0.05, 0.03, 0.34, 1.58, 2.45, 3.34, 4.28]), 'ss': ([1.65, 1.8, 1.9, 2.0, 2.05, 2.1, 2.15], [0.02, 0.07, 0.58, 2.04, 3.00, 4.00, 5.03])}
TAB['typical'] = (TAB['ff'][0], [x * 0.97 / 3.34 for x in TAB['ff'][1]])
def d4b_err(v, corner):
    x, y = TAB[corner]; return np.interp(v, x, y, right=y[-1]) * LSB       # plate higher by e -> input appears lower by e
def sndr(code, M):
    N = len(code); P = np.abs(np.fft.rfft(code - code.mean())) ** 2; ps = P[M]; pn = P[1:N // 2 + 1].sum() - ps
    hb = []
    for k in range(2, 11):
        b = (k * M) % N; b = N - b if b > N // 2 else b
        if b not in (0, M) and b not in hb: hb.append(b)
    thd = 10 * np.log10(P[hb].sum() / ps); return 10 * np.log10(ps / pn), thd, 10 * np.log10(ps / P[hb + [M]].max() if False else ps / max(P[b] for b in range(1, N // 2 + 1) if b != M))
def convert(v, corner, rng, latch=50e-6, namp=0.0, d4b=False, noise=True):
    d, lv, S, sup = hy.chip(rng, corner, True); c = hy.CORN[corner]; N = len(v)
    nz = rng.normal(0, np.sqrt(c['npair'] ** 2 + latch ** 2), (N, 12)) if noise else None; kt = rng.normal(0, c['ktc'], N) if noise else 0.0
    vi = v + kt + (rng.normal(0, namp, N) if namp else 0.0) - (d4b_err(v, corner) if d4b else 0.0)
    return hy.sar(vi, lv, S + sup, nz)
def load(tag, corner):
    p = f'{L.ADC}/sim/d5_{tag}_{corner}.npz'
    return np.load(p) if os.path.exists(p) else None
def prep(d, detrend=False):
    oL, oU, ve, ts = d['oL'], d['oU'], d['vin_eff'], d['ts']
    a, b = np.polyfit(oL, ve, 1); r = ve - (a * oL + b); v = oL + r
    if detrend:
        tt = ts - ts.mean(); A = np.c_[np.sin(2 * np.pi * float(d['f']) * tt), np.cos(2 * np.pi * float(d['f']) * tt), np.ones_like(tt), tt]
        co = np.linalg.lstsq(A, oU, rcond=None)[0]; v = v - co[3] * tt
    return v, (a, b, r, oL - oU)
if __name__ == '__main__':
    tags = sys.argv[1].split(','); nch = int(sys.argv[2]) if len(sys.argv) > 2 else 20; out = []
    P_ = lambda s='': (print(s, flush=True), out.append(s))
    P_('D5 END-TO-END SNDR (HYBRID: transistor-level A4c amplifier with the Randles source + real sampling TG + split DAC loaded at 4 kS/s, then the D4 hybrid SAR, mean of %d chips; N = 64 (see NOTES: N = 512 was not obtained), coherent, rectangular window)' % nch)
    P_('  ENOB raw = (SNDR - 1.76)/6.02 for the test amplitude; ENOB FS adds 20 log10(3.3 V / (2 Apk)) (referred to the 3.3 V full scale, as D4). "amp noise" rows add the A4c ESTIMATE of the amplifier noise (white, rms 1.83 / 2.06 / 1.64 mV at the output) which the transient does not contain.')
    for tag in tags:
        for corner, nm in (('typical', 'typ 27'), ('ff', 'ff 85'), ('ss', 'ss -40')):
            d = load(tag, corner)
            if d is None: continue
            M = int(d['M']); apk = float(d['apk']); N = int(d['N']); f = float(d['f'])
            v, (a, b, r, dl) = prep(d); vd, _ = prep(d, True)[0], None
            c0 = np.round(v / LSB)
            P_(f'[{tag} {nm}] f = {f:.4f} Hz (bin {M} of {N}), amplifier output amplitude {np.ptp(d["oU"])/2*1e3:.1f} mV pk, sampled-value fit gain {a:.5f} offset {b*1e3:+.2f} mV; sampling-chain residual r: rms {np.std(r)/LSB:.3f} LSB, max {np.abs(r).max()/LSB:.3f} LSB; '
                f'amplifier loaded - unloaded at the sampling instants: mean {dl.mean()/LSB:+.3f} rms {np.std(dl)/LSB:.3f} max|.| {np.abs(dl).max()/LSB:.3f} LSB')
            s0 = sndr(np.round(v / LSB), M); s0u = sndr(np.round(d['oU'] / LSB), M)
            P_(f'    ideal 12-bit quantiser of the transistor-level samples: SNDR {s0[0]:.1f} dB, THD {s0[1]:.1f} dBc | of the unloaded amplifier output (amplifier distortion alone, no ADC): SNDR {s0u[0]:.1f} dB, THD {s0u[1]:.1f} dBc')
            for lab, kw in (('HYBRID (D4 ADC model, no amp noise)', {}), ('HYBRID, detrended', dict(det=True)), ('HYBRID + D4b top-of-range plate error', dict(d4b=True)), ('HYBRID + amp noise ESTIMATE', dict(namp=1000 * AMPN[corner])), ('HYBRID + amp noise ESTIMATE + D4b', dict(namp=1000 * AMPN[corner], d4b=True))):
                rng = np.random.default_rng(5); vv = vd if kw.get('det') else v
                res = np.array([sndr(convert(vv, corner, rng, namp=kw.get('namp', 0.0), d4b=kw.get('d4b', False)), M) for _ in range(nch)])
                fsx = 20 * np.log10(3.3 / (2 * apk)); sn = res[:, 0].mean()
                P_(f'    {lab:42s}: SNDR {sn:.1f} dB (min {res[:,0].min():.1f}), THD {res[:,1].mean():.1f} dBc, SFDR {res[:,2].mean():.1f} dB, ENOB raw {(sn-1.76)/6.02:.2f}, ENOB FS {(sn-1.76+fsx)/6.02:.2f}')
    open(f'{L.ADC}/sim/d5_sndr.log', 'w').write('\n'.join(out) + '\n')
