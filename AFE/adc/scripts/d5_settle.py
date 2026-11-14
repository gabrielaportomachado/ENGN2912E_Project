#!/usr/bin/env python3
"""D5 item 1: amplifier output error at the end of the acquisition window with the REAL sampling switch + split DAC (plate 3.49 pF, C on the bottoms 6.92 pF) on the amplifier output.
usage: d5_settle.py <corner> <tempC> [case,case,...]      case = <level>_<prevlevel>_<p|m|0>   (V, V, kick polarity), e.g. 1.65_1.65_0, 2.1_1.86_p
The kick is the charge the amplifier must deliver when the bottoms (floating at the previous code pattern, D3: drivers released 1 SCLK before the resume) are connected to Vin:
  Q = sum_j C_j (Vin - Vb_j) = Cu (127 Vin - VDD (code mod 64 + code div 64))   (bits 0-5 and 6-11 each carry 1..32 units).  p / m = the previous code within +-32 codes of the previous level that gives the MAXIMUM / MINIMUM Q, 0 = the nearest code.
Sequence: frame 0 at 2 ms (hold, bottoms to the previous pattern, released, TG closes after T_CONV = 9.5 us), acquisition 240.5 us, error = out_L - out_U at the next CS falling (frame 1, 250 us later).
Level: electrode offset step at 0.5 ms (1 us edge) puts the amplifier output at Vin (the HPF droop is common to both copies)."""
import sys, os, numpy as np
H = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, H)
import d5lib as L
CU = 54.52e-15
def qkick(code, vin): return CU * (127 * vin - L.VSUP * ((code & 63) + (code >> 6)))
def pick(vprev, vin, pol):
    c0 = int(round(vprev / L.LSB)); cands = np.arange(c0 - 32, c0 + 33); q = np.array([qkick(int(c), vin) for c in cands])
    if pol == '0': i = 32
    elif pol == 'z': i = int(np.argmin(np.abs(q)))
    elif pol == 'p': i = int(np.argmax(q))
    else: i = int(np.argmin(q))
    return int(cands[i]), q[i]
def run_case(corner, temp, case, reltol=float(os.environ.get("RELTOL", "1e-4")), tag=None):
    lv, pv, pol = case.split('_'); lv, pv = float(lv), float(pv)
    code, q = pick(pv, lv, pol); vos = (lv - 1.65) / 1000.0 if abs(lv - 1.65) > 1e-9 else 0.0
    if abs(lv - 1.65) > 1e-9: vos = (lv - 1.650164) / 1000.0
    t0 = 2e-3; fr = [(t0, code), (t0 + L.TFRAME, int(round(lv / L.LSB)))]
    ctrl, tr = L.controls(fr); tb = L.build(vos=vos, tos=0.5e-3, tstop=t0 + L.TFRAME + 1e-6, tsave=1.8e-3, tmaxs=1e-6, reltol=reltol)
    r = L.run(tb, ctrl, corner, temp, tag=tag or f'{case}_{corner}')
    if r is None: return None
    t, vl, vu, vt, vm = r; tc = t0 + L.TCONV; d = (vl - vu) / L.LSB
    cur = {dt: float(np.interp(tc + dt, t, d)) for dt in (1e-6, 11e-6, 50e-6, 100e-6, 150e-6, 200e-6, 240e-6)}
    te = t0 + L.TFRAME - 20e-9; e_end = float(np.interp(te, t, d)); pre = float(np.interp(t0 - 1e-6, t, d))
    m = (t > tc) & (t < tc + 5e-6); pk = float(d[m][np.argmax(np.abs(d[m]))])
    mm = (t > tc + 1e-6) & (t < t0 + L.TFRAME - 100e-9); big = np.nonzero(np.abs(d[mm]) > 0.5)[0]; tb5 = float((t[mm][big[-1]] - tc) * 1e9) if len(big) else 0.0
    return dict(vu=float(np.interp(te, t, vu)), code=code, q=q, e_end=e_end, pre=pre, curve=cur, peak=pk, t05=tb5)
if __name__ == '__main__':
    corner, temp = sys.argv[1], int(sys.argv[2]); cases = sys.argv[3].split(',') if len(sys.argv) > 3 else ['1.65_1.65_0']
    for c in cases:
        r = run_case(corner, temp, c)
        if r is None: print(f'SETTLE {corner} {temp}C case {c}: FAILED', flush=True); continue
        print(f'SETTLE {corner} {temp}C case {c}: amp out (unloaded) {r["vu"]:.4f} V, prev code {r["code"]} (kick Q {r["q"]*1e12:+.2f} pC) | L-U before {r["pre"]:+.3f} | spike peak {r["peak"]:+.1f} LSB, last time |L-U| > 0.5 LSB: {r["t05"]:.0f} ns after the TG closes | '
              f'L-U [LSB] at +1/11/50/100/150/200/240 us: ' + ' '.join(f'{v:+.3f}' for v in r['curve'].values()) + f' | AT THE NEXT CS FALLING (end of T_ACQ): {r["e_end"]:+.3f} LSB', flush=True)
