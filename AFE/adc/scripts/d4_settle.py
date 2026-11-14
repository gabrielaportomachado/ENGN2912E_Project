#!/usr/bin/env python3
"""D4: DAC settling (0.5 LSB, per trial) at the STA-matched corner, then margin vs the comparator clock: T0 - (latest DAC-edge arrival from the STA) - settling.
usage: d4_settle.py <corner> <tempC> <VDD> <vin,vin,..>   prints SETTLE lines (as d2_conv settle) for the 12 trials"""
import sys, os, numpy as np
H = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, H)
import d2_conv as dc; from d2lib import *
corner, temp, vdd = sys.argv[1], sys.argv[2], float(sys.argv[3]); dc.VSUP = vdd
os.makedirs(f'{dc.ADC}/sim/.ptmp', exist_ok=True)
T = 200e-9
for vin in [float(x) for x in sys.argv[4].split(',')]:
    ctrl, tend, info = dc.control('conv', [vin], T); t, d = dc.run(corner, temp, ctrl, tend, f'd4s_{corner}', extra=[f'VSUP={vdd}'])
    ts, to, tc0, te = info[0]; tr = [tc0 + k * T for k in range(12)]; ts5 = []
    for k in range(12):
        vend = np.interp(tr[k] + T - 0.3e-9, t, d['t']); m = (t >= tr[k]) & (t <= tr[k] + T - 0.3e-9); big = np.nonzero(np.abs(d['t'][m] - vend) > 0.5 * LSB)[0]
        ts5.append((t[m][big[-1]] - tr[k] if len(big) else 0.0) * 1e9)
    print(f'SETTLE4 {corner} {temp}C {vdd}V vin={vin:.4f}: 0.5-LSB settling per trial [ns] ' + ' '.join(f'{x:.1f}' for x in ts5) + f' | max {max(ts5):.1f}')
