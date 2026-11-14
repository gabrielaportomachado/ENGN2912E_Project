#!/usr/bin/env python3
"""D1: comparator input range DEMANDED by the DAC switching scheme (exact enumeration with ideal decisions, no parasitics).  All comparisons of a 12-bit conversion for every input on a 0.5 mV grid.
Comparator inputs (inp, inn); CM = (inp+inn)/2, diff = inp-inn.  VREF = VDD = 3.3 V, Vcm = 1.65 V (D0b item 8: top plates reset to Vcm, comparator reference = same node).
 CONVENTIONAL (D0): single array 4096 u, bottom-plate sampling, top plate at Vcm during sampling, then all bottoms to GND; trial k sets bit k:  inp = Vx = Vcm + Vdac_k - Vin, inn = Vcm.
 MONOTONIC (pseudo-differential: P array samples Vin, N array samples Vcm, both top-plate sampled with bottoms at VREF; comparison 0 is free (Vin vs Vcm); after each comparison the higher side drops by
   VREF/2^(j+1) (j = 1..11); each side needs 4096 u for a 1 LSB last drop -> TWICE the DAC capacitance of the conventional single array (ESTIMATE note)).
Reported: ranges over (a) the amplifier output range Vin in [1.15, 2.15] V (A4c nominal swing), (b) the full ADC range [0, 3.3] V; 'critical' = comparisons with |diff| <= 4 LSB (3.2 mV), where a trip-point error matters.
Output -> stdout and sim/d1_icmr_need.log"""
import numpy as np, sys
VREF = 3.3; VCM = VREF / 2; N = 12; LSB = VREF / 2 ** N
def conventional(vin):
    code = 0; ev = []
    for k in range(N):
        vdac = (code + 2 ** (N - 1 - k)) * LSB
        vx = VCM + vdac - vin
        ev.append((vx, VCM))
        if vx <= VCM: code += 2 ** (N - 1 - k)       # Vdac <= Vin -> bit = 1
    return ev, code
def monotonic(vin):
    vp, vn = vin, VCM; code = 0; ev = []
    for j in range(N):
        ev.append((vp, vn))
        hi = vp > vn
        code = 2 * code + (1 if hi else 0)
        if j < N - 1:
            d = VREF / 2 ** (j + 2)
            if hi: vp -= d
            else:  vn -= d
    return ev, code
def run(fn, vins):
    cm, df, vlo, vhi = [], [], [], []
    for v in vins:
        ev, code = fn(v)
        for a, b in ev: cm.append((a + b) / 2); df.append(a - b); vlo.append(min(a, b)); vhi.append(max(a, b))
    return np.array(cm), np.array(df), np.array(vlo), np.array(vhi)
out = []
def P(s): print(s); out.append(s)
P('D1 comparator input range demanded by the DAC switching scheme (exact enumeration, ideal decisions, VREF = 3.3 V, Vcm = 1.65 V, 12 bits)')
for name, fn in [('conventional', conventional), ('monotonic', monotonic)]:
    for rng, (a, b) in [('amp range 1.15-2.15 V', (1.15, 2.15)), ('full range 0-3.3 V', (0.0, 3.3))]:
        vins = np.arange(a, b + 1e-9, 0.0005)
        cm, df, vlo, vhi = run(fn, vins)
        crit = np.abs(df) <= 4 * LSB
        P(f'{name:12s} {rng:22s}  all comparisons: CM {cm.min():.3f}..{cm.max():.3f} V, diff {df.min():+.3f}..{df.max():+.3f} V, node voltage {vlo.min():.3f}..{vhi.max():.3f} V'
          f'  | critical (|diff|<=4 LSB): CM {cm[crit].min():.3f}..{cm[crit].max():.3f} V')
# monotonic: CM at which a converged comparison happens, per trial index (Vin = Vcm, Vin = 1.15, 2.15, 0, 3.3)
P('monotonic common mode at each of the 12 comparisons (V) for Vin = 0 / 1.15 / 1.65 / 2.15 / 3.3 V')
for vin in [0.0, 1.15, 1.65, 2.15, 3.3]:
    ev, _ = monotonic(vin); P(f'  Vin {vin:4.2f}: ' + ' '.join(f'{(a+b)/2:.3f}' for a, b in ev))
# sanity: ideal codes
for fn in (conventional, monotonic):
    errs = [abs(fn(v)[1] - min(4095, int(v / LSB))) for v in np.arange(0.0001, 3.2999, 0.0137)]
    P(f'{fn.__name__}: max |code - ideal| over the test inputs = {max(errs)} (0 expected)')
open(sys.path[0] + '/../sim/d1_icmr_need.log', 'w').write('\n'.join(out) + '\n')
