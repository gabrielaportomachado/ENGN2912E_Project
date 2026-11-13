#!/usr/bin/env python3
"""A4b item 3: PWL playback of the REAL one-shot output.  usage: fs_pwl.py <corner> <T> <sel> <t_trigger_s>  -> prints "t,v,t,v,..." (comma separated, no spaces) for the channel testbench (FS_SRC=2),
the waveform of tb/tb_fsos_gate.spice (cached in /tmp/a4bfs/) shifted so that the trigger edge is at t_trigger.  Also prints the pulse width to stderr."""
import sys, os, subprocess, numpy as np
AMP = os.path.abspath(os.path.join(os.path.dirname(__file__), '..')); C = '/tmp/a4bfs'; os.makedirs(C, exist_ok=True)
corner, T, sel, t0 = sys.argv[1], sys.argv[2], sys.argv[3], float(sys.argv[4])
csv = f'{C}/{corner}_{T}_sel{sel}.csv'
if not os.path.exists(csv):
    env = dict(os.environ, OUT=csv)
    subprocess.run(['bash', f'{AMP}/scripts/ngrun.sh', 'tb_fsos_gate.spice', corner, T, f'SELV={sel}'], env=env, capture_output=True, text=True, timeout=300)
d = np.loadtxt(csv, skiprows=1); t, v = d[:, 0], d[:, 1]
tr = 110e-9 - 5e-9      # trigger edge midpoint at 105 ns
# pulse width (50 %)
up = np.where((v[:-1] < 1.65) & (v[1:] >= 1.65))[0]; dn = np.where((v[:-1] >= 1.65) & (v[1:] < 1.65))[0]
w = (np.interp(1.65, [v[dn[0] + 1], v[dn[0]]], [t[dn[0] + 1], t[dn[0]]]) - np.interp(1.65, [v[up[0]], v[up[0] + 1]], [t[up[0]], t[up[0] + 1]])) if len(up) and len(dn) else float('nan')
print(f'# {corner} {T} sel{sel}: fs pulse width {w*1e9:.1f} ns', file=sys.stderr)
# thin: keep points where the waveform changes
keep = [0]
for i in range(1, len(t)):
    if abs(v[i] - v[keep[-1]]) > 0.03 or i == len(t) - 1: keep.append(i)
pts = [(0.0, 0.0)] + [(t0 + (t[i] - tr), v[i]) for i in keep if t[i] - tr > -1e-12]
pts[0] = (0.0, 0.0)
pts.insert(1, (pts[1][0] - 1e-9, 0.0))        # hold 0 V until just before the first edge (otherwise PWL ramps from t = 0)
# strictly increasing times
out = []
for tt, vv in pts:
    if out and tt <= out[-1][0]: tt = out[-1][0] + 1e-12
    out.append((tt, vv))
print(','.join(f'{tt:.12e},{vv:.4f}' for tt, vv in out))
