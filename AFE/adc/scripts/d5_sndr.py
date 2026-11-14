#!/usr/bin/env python3
"""D5 item 2: end-to-end SNDR.  Transistor-level amplifier (A4c, Randles electrode source) + real sampling TG + split DAC, 4 kS/s frames (250 us, D3 timing), coherent sine; the plate is read after every
sample (MSB high / rest low) and inverted to the effective sampled input; the 12 SAR decisions are then made by the D4 HYBRID model (D2 DAC MC weights, D1 shift/offset/noise, D4b supply table).
usage: d5_sndr.py run <corner> <tempC> <tag> <amp_V_out_pk> <M> [N=512] [TPRE=0.6] [codes.npy]  -> sim/d5_<tag>_<corner>.npz     (codes.npy = previous-pass final codes for the kick patterns; default = ideal code of the unloaded sine)"""
import sys, os, numpy as np, time
H = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, H)
import d5lib as L
def run(corner, temp, tag, apk, M, N=512, tpre=0.6, codes=None, tmaxs=float(os.environ.get('TMAXS','2e-6')), reltol=1e-4, gain=1000.0, phase=0.0):
    f = M * 4000.0 / N; vd = apk / gain; ts = tpre + np.arange(N + 1) * L.TFRAME
    if codes is None: codes = np.clip(np.round((1.6502 + apk * np.sin(2 * np.pi * f * ts)) / L.LSB), 0, 4095).astype(int)
    ctrl, tread = L.controls([(float(a), int(c)) for a, c in zip(ts, codes)])
    tb = L.build(vd=vd, fsig=f, tdsig=0.0, phase=phase, tstop=float(ts[-1] + L.TFRAME * 0.2), tsave=tpre - 2e-3, tstep=1e-7, tmaxs=tmaxs, reltol=reltol)
    t0 = time.time(); r = L.run(tb, ctrl, corner, temp, tag=f'{tag}_{corner}', tmo=int(os.environ.get('TMO', '1750')))
    if r is None: print(f'FAILED {tag} {corner}'); return None
    t, vl, vu, vt, vm = r
    ss = ts[:N]
    vin_eff = L.plate_to_vin(np.interp(tread[:N], t, vt)); oL = np.interp(ss - 20e-9, t, vl); oU = np.interp(ss - 20e-9, t, vu)
    # amplifier output (unloaded copy) every 2 us over the window for the analysis of the transient itself
    np.savez(f'{L.ADC}/sim/d5_{tag}_{corner}.npz', ts=ss, vin_eff=vin_eff, oL=oL, oU=oU, codes=codes, f=f, apk=apk, M=M, N=N, wall=time.time() - t0)
    return dict(vin_eff=vin_eff, oL=oL, oU=oU)
if __name__ == '__main__':
    if sys.argv[1] == 'run':
        corner, temp, tag, apk, M = sys.argv[2], int(sys.argv[3]), sys.argv[4], float(sys.argv[5]), int(sys.argv[6])
        N = int(sys.argv[7]) if len(sys.argv) > 7 else 512; tpre = float(sys.argv[8]) if len(sys.argv) > 8 else 0.6
        codes = np.load(sys.argv[9]) if len(sys.argv) > 9 else None
        r = run(corner, temp, tag, apk, M, N, tpre, codes)
        if r: d = np.load(f'{L.ADC}/sim/d5_{tag}_{corner}.npz'); print(f'RUN {tag} {corner} done, wall {float(d["wall"]):.0f} s; amp out pk {np.ptp(r["oU"])/2:.4f} V; (L-U) rms {np.std(r["oL"]-r["oU"])/L.LSB:.3f} LSB; (vin_eff - oL) mean {np.mean(r["vin_eff"]-r["oL"])/L.LSB:+.2f} LSB')
