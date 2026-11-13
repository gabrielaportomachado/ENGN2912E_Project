#!/usr/bin/env python3
"""A4c: PWL playback of the REAL current-starved one-shot (spice/fs_oneshot_c.spice, tb/tb_fsos_c.spice, cached in /tmp/a4cfs/).  usage: fs_pwl_c.py <corner> <T> <t_trigger_s>
prints "t,v,t,v,..." with the trigger edge at t_trigger (channel testbench FS_SRC=2); pulse width to stderr.  Reason: the channel netlist with the one-shot AND the record-path TGATE aborts .tran (A4c)."""
import sys, os, subprocess, numpy as np
AMP = os.path.abspath(os.path.join(os.path.dirname(__file__), '..')); C = '/tmp/a4cfs'; os.makedirs(C, exist_ok=True)
corner, T, t0 = sys.argv[1], sys.argv[2], float(sys.argv[3]); extra = sys.argv[4:]
csv = f'{C}/{corner}_{T}_{"_".join(extra)}.csv'
if not os.path.exists(csv):
    env = dict(os.environ, OUT=csv)
    subprocess.run(['bash', f'{AMP}/scripts/ngrun.sh', 'tb_fsos_c.spice', corner, T] + extra, env=env, capture_output=True, text=True, timeout=600)
d = np.loadtxt(csv, skiprows=1); t, v = d[:, 0], d[:, 1]
ttrig = 1e-3 + 5e-9
up = np.where((v[:-1] < 1.65) & (v[1:] >= 1.65))[0]; dn = np.where((v[:-1] >= 1.65) & (v[1:] < 1.65))[0]
w = (t[dn[0]] - t[up[0]]) if len(up) and len(dn) else float('nan')
print(f'# {corner} {T}: fs pulse width {w*1e3:.3f} ms', file=sys.stderr)
keep = [0]
for i in range(1, len(t)):
    if abs(v[i] - v[keep[-1]]) > 0.02 or i == len(t) - 1: keep.append(i)
# the playback keeps the REAL plateau and falling edge (slow, tens of us) but the rising edge is a 100 ns ramp (the real rise is ~1 ns; ns edges make the channel .tran with the TGATE abort, A4c)
fall = [i for i in keep if t[i] - ttrig > 1e-6]
pts = [(0.0, 0.0), (t0, 0.0), (t0 + 100e-9, float(v.max()))] + [(t0 + (t[i] - ttrig), v[i]) for i in fall]
out = []
for tt, vv in pts:
    if out and tt <= out[-1][0]: tt = out[-1][0] + 1e-12
    out.append((tt, vv))
print(','.join(f'{tt:.12e},{vv:.4f}' for tt, vv in out))
