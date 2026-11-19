#!/usr/bin/env python3
"""X2 / S4 follow-up: HOW MUCH does the modelled supply move a code transition?  (The code-change test of x2_s4.py depends on where the input sits inside its code; its centring assumes a constant
comparator threshold, which X2 S1 shows to be code dependent by up to +-0.5 LSB, so a 1 LSB code change there can come from a 0.03 LSB shift.)
Method: the 8 inputs of a case are stepped together over +-0.5 LSB in 0.125 LSB steps (9 points).  At each point: every ADC alone on an ideal supply, and the 8-ADC netlist on the modelled supply
(same netlists and timing as x2_s4.py).  Per ADC the code steps once inside the window; shift = (step position in the 8-ADC run) - (step position alone), resolution 0.125 LSB.
A positive shift = the transition moved to a higher input = the ADC reads lower.
usage: x2_s4_sweep.py <ff-40|typ|ss125> <fs|mid|alt> [SCLK MHz=3]   (X2_CM, X2_LP ... what-if overrides as x2_s4.py)   -> sim/x2_s4_sweep.log (append)"""
import sys, os, time, numpy as np
H = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, H)
import x2lib as X, x2_adc as A, x2_s4 as S4
ck, case = sys.argv[1], sys.argv[2]; f = float(sys.argv[3]) if len(sys.argv) > 3 else 3.0; T = 1e-6 / f; vdd = X.COR[ck][2]; lsb = vdd / 4096; out = []; t0 = time.time()
def P(s): print(s, flush=True); out.append(s)
cal = X.Cal(vdd); cals = [cal] * 8; v3 = [vdd * 0.35, vdd * 0.5 + 0.0007, vdd * 0.65]
ex = [X.Exp(f'c{j}', ck, 1, [S4.TCS], T, S4.builder(ck, {i: v}, [i], None, T), [[v]], cal, ref='vssi', adcs=[i]) for j, (i, v) in enumerate(zip((0, 3, 7), v3))]
X.closed_loop(ex, log=lambda s: None, tag=f'swc_{ck}'); A.fit_cal(cal, ex, v3)
v0 = S4.targets(case, ck, cals); r1 = S4.alone(ck, v0, cals, T, f'swa_{ck}_{case}', lambda s: None)
vc = [v0[i] + (r1[i].x[0, 0, 11] - cal.theta) / cal.alpha + (0.5 if r1[i].dec[0, 0, 11] else -0.5) * lsb for i in range(8)]          # nominal code centres (constant-threshold estimate)
deltas = np.arange(-4, 5) * 0.125; ca = np.zeros((9, 8), int); c8 = np.zeros((9, 8), int); prev = [e.bits[0][0] for e in r1]; fails = 0
for k, d in enumerate(deltas):
    vin = [v + d * lsb for v in vc]
    ra = S4.alone(ck, vin, cals, T, f'swb_{ck}_{case}', lambda s: None, init=prev); prev = [e.bits[0][0] for e in ra]; ca[k] = [int(e.codes()[0, 0]) for e in ra]
    e8 = X.Exp(f'sw8_{k}', ck, 8, [S4.TCS], T, S4.builder(ck, vin, list(range(8)), S4.MODEL, T, dig=S4.dig_line(T, True)), [[v] for v in vin], cal, ref='vssi', cals=cals)
    e8.bits = [[list(ra[i].bits[0][0])] for i in range(8)]; X.closed_loop([e8], log=lambda s: None, tag=f'sw8_{ck}_{case}', maxpass=12)
    if e8.failed: fails += 1; c8[k] = -1; P(f'S4SWEEP {ck} {case} delta {d:+.3f} LSB: 8-ADC run FAILED: {e8.failed}'); continue
    c8[k] = e8.codes()[:, 0]
P(f'S4SWEEP {ck} {case} (SCLK {f:g} MHz{", WHAT-IF supply " + S4.WHATIF if S4.WHATIF else ""}): inputs stepped -0.5 .. +0.5 LSB in 0.125 LSB steps around {", ".join(f"{v:.5f}" for v in vc)} V; supply model {S4.MODEL}')
sh = []
for i in range(8):
    def step(c):
        ok = c >= 0; idx = [k for k in range(1, 9) if ok[k] and ok[k - 1] and c[k] != c[k - 1]]
        return (0.5 * (deltas[idx[0]] + deltas[idx[0] - 1]), len(idx)) if idx else (float('nan'), 0)
    sa, na = step(ca[:, i]); s8, n8 = step(c8[:, i]); sh.append(s8 - sa)
    P(f'S4SWEEP {ck} {case} ADC{i}: codes alone {" ".join(map(str, ca[:, i]))} | in the 8-ADC run {" ".join(map(str, c8[:, i]))} | transition at {sa:+.4f} LSB alone, {s8:+.4f} LSB with the modelled supply -> SHIFT {s8-sa:+.3f} LSB' + ('' if na == 1 and n8 == 1 else f' (steps found: {na} / {n8})'))
sh = np.array(sh)
s = f'RESULT S4SWEEP {ck} {case}{" WHAT-IF " + S4.WHATIF if S4.WHATIF else ""}: transition shift caused by the modelled supply, per ADC 0..7 [LSB, resolution 0.125]: ' + ' '.join(f'{x:+.3f}' for x in sh) + f' | max |shift| {np.nanmax(np.abs(sh)):.3f} LSB -> {"PASS" if np.nanmax(np.abs(sh)) <= 0.5 else "FAIL"} (limit 0.5 LSB); failed runs {fails}; wall {time.time()-t0:.0f} s'
P(s); open(f'{X.ADC}/sim/x2_s4_sweep.log', 'a').write('\n'.join(out) + '\n'); open(f'{X.ADC}/sim/x2_s4_summary.log', 'a').write(s + '\n')
