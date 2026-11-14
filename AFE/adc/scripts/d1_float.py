#!/usr/bin/env python3
"""D1 floating-plate kickback check.  usage: d1_float.py <corner> <T> <sgn:+|-> <SCLK_MHz>   -> one line FLOAT ... (drift of the floating 7 pF node after each of 12 decisions, mV)"""
import sys, os, subprocess, tempfile, shutil, atexit, numpy as np
sys.path.insert(0, os.path.dirname(__file__)); import dlib
ADC = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
corner, T, sgn, f = sys.argv[1], sys.argv[2], sys.argv[3], float(sys.argv[4]); dmv = float(sys.argv[5]) if len(sys.argv) > 5 else 0.4
tb = 1e-6 / f; tmp = tempfile.mkdtemp(prefix='d1f_', dir=os.path.join(ADC, 'sim', '.ptmp')); atexit.register(shutil.rmtree, tmp, True)
vsup = float(sys.argv[6]) if len(sys.argv) > 6 else 3.3; trk = len(sys.argv) > 7 and sys.argv[7] == '1'; vref = vsup / 2 if trk else 1.65
dv = dmv * 1e-3 * (1 if sgn == '+' else -1)
out = f'{tmp}/o.csv'; e = dict(os.environ, OUT=out, CELL='cmp_p')
subprocess.run(['bash', f'{ADC}/scripts/dgrun.sh', 'tb_cmp_float.spice', corner, T, f'TB={tb:.4g}', f'DVX={dv}', f'VSUP={vsup}', f'VREFV={vref}'], capture_output=True, text=True, env=e)
if not os.path.exists(out): print(f'FAIL float {corner} {T} {sgn} {f}'); sys.exit(1)
t, d = dlib.load(out, ['x', 'clk', 'outp', 'outn'])
NPRE = 3; x0 = np.interp(40e-9 + NPRE * tb - 2e-9, t, d['x']); drift = []; dec = []; kdec = []; kpk = []
for k in range(12):
    tr = 40e-9 + (NPRE + k) * tb                                    # clk rise of decision k
    dec.append(1 if np.interp(tr + tb / 2 - 2e-9, t, d['outp']) - np.interp(tr + tb / 2 - 2e-9, t, d['outn']) > 0 else -1)
    kdec.append((np.interp(tr + 3e-9, t, d['x']) - x0) * 1e3)          # x shift 3 ns after the clk rise = at the decision instant (decision made after ~1-2 ns)
    mm = (t > tr) & (t < tr + tb / 2); kpk.append(((d['x'][mm] - x0)[np.argmax(np.abs(d['x'][mm] - x0))]) * 1e3)
    drift.append((np.interp(tr + tb - 2e-9, t, d['x']) - x0) * 1e3)   # node after decision k's evaluate + reset, just before the next rise
LSB = 3.3 / 4096 * 1e3
wrong = sum(1 for x in dec if x != (1 if sgn == '+' else -1))
print(f'FLOAT {corner} {T}C VDD={vsup:g}{"/2track" if trk else "fixref"} {sgn}{dmv:g}mV SCLK={f:g}MHz x0={x0:.6f}V dec={"".join("+" if x>0 else "-" for x in dec)} drift_mV_after_each=' + ','.join(f'{v:+.4f}' for v in drift) + f' total_mV={drift[-1]:+.4f} total_LSB={drift[-1]/LSB:+.3f} max|drift|_mV={max(abs(v) for v in drift):.4f} | DURING EVALUATE: x shift at decision instant {kdec[-1]:+.3f} mV ({kdec[-1]/LSB:+.1f} LSB), peak {kpk[-1]:+.3f} mV; wrong decisions {wrong}/12')
