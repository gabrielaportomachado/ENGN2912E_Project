#!/usr/bin/env python3
"""X2 / S2 strategy (b): instrument the abort.  Re-runs the D5 failing configuration (d5_sndr b1 typical, 64 frames, step cap 3 us, abstol 1e-15) with ALL node voltages and branch currents saved for
the last 0.5 us before the abort (TSAVE = 34.0085 ms; the abort is at 34.009 ms + 0.26 ns) and writes the time-step history, the unknowns that move, and the state of the DAC / comparator nodes.
usage: x2_s2_trace.py  -> sim/x2_s2_trace.log"""
import os, sys, subprocess, numpy as np
H = os.path.dirname(os.path.abspath(__file__)); ADC = os.path.abspath(os.path.join(H, '..')); PT = f'{ADC}/sim/.ptmp'; csv = f'{PT}/x2_s2_all.csv'
env = dict(os.environ, X2_SAVE='all', X2_CSV=csv, X2_NUMDGT='15', X2_LOGOUT=f'{ADC}/sim/x2_s2_repro.log', X2_OLDSTYLE='1')      # exactly as D5 ran it (working directory tb/, relative includes, the container's start-up files: no compatibility mode, 8 threads): the abort is then reproducible to the last digit
r = subprocess.run([sys.executable, f'{H}/x2_s2_repro.py', 'typical', '27', 'E5_instrumented_as_D5', '0.45', '1', '64', '0.03', '3e-6', '0.0340085', '', '900'], env=env, capture_output=True, text=True)
out = [l for l in r.stdout.split('\n') if l.startswith('S2REPRO') and 'start pid' not in l]
hdr = open(csv).readline().split(); a = np.loadtxt(csv, skiprows=1); names = hdr[1:]; t = a[:, 0]; t0 = 0.034009; rel = (t - t0) * 1e12; os.remove(csv)
col = lambda n: a[:, 1 + names.index(n)]
out.append(f'TRACE: {len(t)} saved points from TSAVE; release edge of frame 16 starts at t0 = 34.009 ms (gp -> VDD, gn -> 0 in 100 ps)')
out.append('TRACE accepted time points, t - t0 [ps]: ' + ' '.join(f'{x:.4f}' for x in rel[rel >= -1]))
out.append('TRACE accepted steps dt [ps]:             ' + ' '.join(f'{x:.3g}' for x in np.diff(t[rel >= -1]) * 1e12))
out.append('TRACE (a step shorter than half the previous one means Newton failed and ngspice divided the step by 8; the run ends when the step reaches delmin = 1e-11 x tmax = 3e-17 s: reported 3.75e-18)')
d = np.abs(a[-1, 1:] - a[-4, 1:]); idx = np.argsort(-d)[:8]
out.append('TRACE largest changes of any unknown over the last 3 accepted steps: ' + ', '.join(f'{names[i]} {d[i]:.3g}' for i in idx))
for n in ['gn1', 'gp11', 'xs.b1', 'xs.b0', 'xs.b11', 'xs.b5', 'xs.bd', 't', 'm', 'out', 'xc.a1', 'xc.a2', 'xc.tl', 'xc.o1', 'xc.o2', 'outp', 'outn', 'vgn1#branch', 'vck#branch', 'vsamb#branch', 'vgp11#branch', 'vfs#branch', 'vpkc#branch']:
    if n in names: out.append(f'TRACE {n:14s} last 8 points: ' + ' '.join(f'{x:.7g}' for x in col(n)[-8:]))
i = names.index('vgn1#branch'); ib = abs(a[-1, 1 + i]); dt = t[-1] - t[-2]
out.append(f'TRACE convergence test of the failing unknown vgn1#branch (current of the source that drives only the gate of the bit-1 NMOS driver): |i| = {ib:.3g} A, tolerance reltol*|i| + abstol = {1e-4*ib+1e-15:.3g} A;'
           f' i = C dV/dt with C ~ 0.3 fF (gate-drain overlap) and dt = {dt:.3g} s (last accepted step): the drain-side node must repeat within {(1e-4*ib+1e-15)*dt/0.3e-15:.3g} V between two Newton iterations; with abstol 1e-12: {(1e-4*ib+1e-12)*dt/0.3e-15:.3g} V')
open(f'{ADC}/sim/x2_s2_trace.log', 'w').write('\n'.join(out) + '\n'); print('\n'.join(l[:300] for l in out))
