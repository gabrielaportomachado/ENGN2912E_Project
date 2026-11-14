#!/usr/bin/env python3
"""D1 single-job runner.  usage: d1_run.py <mode> <corner> <tempC> <cell> [key=value ...]  [-- NAME=VALUE param overrides for the testbench]
Prints ONE result line (collected by scripts/run_d1.sh into sim/d1_<mode>.log).  Modes:
  delay   decision time / energy vs differential overdrive at CM (cm=1.65): +-d, d = 0.1 ... 2000 mV, alternating sign, 40 cycles
  offset  trip point (input-referred offset) by a staircase +-12 mV, 0.1 mV steps, with mismatch (SW_MM=1) and seed=<n>
  icmr    trip point and stuck test at common mode cm=<V> (staircase +-6 mV, 0.1 mV steps) [mode icmr]; mode conv: inn fixed at 1.65 V, inp = Vx list (0..3.3 V) sign check
  kick    charge drawn from the two input sources per clock edge pair for +-1 LSB / +-10 mV / +-0.5 V, and supply charge"""
import shutil, atexit, sys, os, subprocess, tempfile, math, numpy as np
sys.path.insert(0, os.path.dirname(__file__)); import dlib
ADC = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
a = sys.argv[1:]; mode, corner, T, cell = a[0], a[1], a[2], a[3]
rest = a[4:]; kv = {}; over = []
for x in rest:
    if '=' in x and x.split('=')[0].lower() == x.split('=')[0] and not x.split('=')[0].startswith('CMP'): kv[x.split('=')[0]] = x.split('=', 1)[1]
    else: over.append(x)
CS = float(os.environ.get('CS_PF', 7)) * 1e-12   # DAC / sampling capacitance (user decision: 7 pF)
TCYC = 30e-9; TCLK0 = 5e-9; VDD = 3.3; LSB = 3.3 / 4096
tmp = tempfile.mkdtemp(prefix='d1r_', dir=os.path.join(ADC, 'sim', '.ptmp')); atexit.register(shutil.rmtree, tmp, True)
def mk(name, vals, path): subprocess.run(['python3', f'{ADC}/scripts/mkpwl.py', path, name, str(TCYC), '100e-12', ','.join(f'{v:.9g}' for v in vals), str(-TCLK0)], check=True)
def run(vp, vn, extra=(), env=None):
    mk('inp', vp, f'{tmp}/p.inc'); mk('inn', vn, f'{tmp}/n.inc')
    e = dict(os.environ, OUT=f'{tmp}/o.csv', CELL=cell, SWAPS=f'@PWLP@={tmp}/p.inc @PWLN@={tmp}/n.inc ' + os.environ.get('XSWAP', '')); e.update(env or {})
    if os.path.exists(f'{tmp}/o.csv'): os.remove(f'{tmp}/o.csv')
    r = subprocess.run(['bash', f'{ADC}/scripts/dgrun.sh', 'tb_cmp_stair.spice', corner, T, f'NCYC={len(vp) + 2}', f'TCYC={TCYC}', f'TCLK0={TCLK0}'] + list(extra) + over, capture_output=True, text=True, env=e)
    if not os.path.exists(f'{tmp}/o.csv'): print(f'FAIL {mode} {corner} {T} {cell} {kv} ' + ' | '.join(l for l in r.stdout.splitlines() if 'rror' in l or 'nknown' in l or 'no such' in l)[:600]); sys.exit(1)
    return dlib.load(f'{tmp}/o.csv', ['outp', 'outn', 'clk', 'i_vdd', 'i_p', 'i_n'])
def decisions(t, d, n):
    out = []
    for k in range(n):
        ts = TCLK0 + k * TCYC; te = ts + TCYC / 2
        m = (t >= ts) & (t < te); dv = (d['outp'] - d['outn'])[m]
        idx = np.nonzero(np.abs(dv) > VDD / 2)[0]
        out.append((0, None) if not len(idx) else (1 if dv[idx[0]] > 0 else -1, t[m][idx[0]] - ts))
    return out
def charge(t, d, k, key, vdd=None):
    ts = TCLK0 + k * TCYC; m = (t >= ts) & (t < ts + TCYC); return -np.trapezoid(d[key][m], t[m])
cm = float(kv.get('cm', 1.65))
if mode == 'delay':
    ds = [0.1, 0.2, 0.5, 1, 2, 5, 10, 20, 50, 100, 200, 500, 1000, 2000]; seq = []
    for x in ds: seq += [x * 1e-3, -x * 1e-3]
    vp = [cm + s / 2 for s in seq]; vn = [cm - s / 2 for s in seq]
    t, d = run(vp, vn); dec = decisions(t, d, len(seq)); res = []
    for i, x in enumerate(ds):
        (d1, t1), (d2, t2) = dec[2 * i], dec[2 * i + 1]
        ok = d1 == 1 and d2 == -1
        e = np.mean([charge(t, d, 2 * i + j, 'i_vdd') * VDD for j in (0, 1)])
        res.append(f'{x:g}mV:{(t1 or 0)*1e9:.2f}/{(t2 or 0)*1e9:.2f}ns{"" if ok else "(WRONG)"}:{e*1e12:.2f}pJ')
    print(f'DELAY {corner} {T}C {cell} cm={cm} ' + ' '.join(res))
elif mode == 'offset':
    step = 0.1e-3; vd = np.arange(-12e-3, 12e-3 + 1e-9, step)
    t, d = run(cm + vd / 2, cm - vd / 2, ['SW_MM=1'], {'SEED': kv['seed']}); dec = decisions(t, d, len(vd))
    s = np.array([x[0] for x in dec]); pos = (s > 0).astype(int)
    flips = np.nonzero(np.diff(pos) != 0)[0]
    trip = float('nan') if len(flips) == 0 else (vd[flips[0]] + vd[flips[0] + 1]) / 2
    print(f'OFFSET {corner} {T}C {cell} seed={kv["seed"]} trip_uV={trip*1e6:.1f} nflips={len(flips)} undecided={int(np.sum(s==0))}')
elif mode == 'icmr':
    step = 0.1e-3; vd = np.arange(-6e-3, 6e-3 + 1e-9, step)
    t, d = run(cm + vd / 2, cm - vd / 2); dec = decisions(t, d, len(vd))
    s = np.array([x[0] for x in dec]); pos = (s > 0).astype(int); flips = np.nonzero(np.diff(pos) != 0)[0]
    trip = float('nan') if len(flips) == 0 else (vd[flips[0]] + vd[flips[0] + 1]) / 2
    i1 = int(np.argmin(abs(vd - LSB))); i2 = int(np.argmin(abs(vd + LSB)))
    ok1 = s[i1] == 1 and s[i2] == -1
    tm = [x[1] for x in dec if x[1]]; tmx = max(tm) if tm else float('nan')
    print(f'ICMR {corner} {T}C {cell} cm={cm:.3f} trip_uV={trip*1e6:.1f} nflips={len(flips)} undecided={int(np.sum(s==0))} correct_at_pm1LSB={int(ok1)} max_delay_ns={tmx*1e9:.2f}')
elif mode == 'conv':
    vx = np.array([0.0, 0.05, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.8, 1.0, 1.2, 1.4, 1.55, 1.6, 1.64, 1.66, 1.7, 1.75, 1.9, 2.1, 2.3, 2.5, 2.7, 2.9, 3.1, 3.2, 3.25, 3.3])
    t, d = run(vx, np.full(len(vx), 1.65)); dec = decisions(t, d, len(vx))
    bad = [f'{v:.2f}' for v, x in zip(vx, dec) if x[0] != (1 if v > 1.65 else -1)]
    print(f'CONV {corner} {T}C {cell} Vx_0..3.3_vs_Vref1.65 wrong_at=[{",".join(bad)}] max_delay_ns={max([x[1] for x in dec if x[1]])*1e9:.2f}')
elif mode == 'kick':
    # conventional scheme: inn = Vref = 1.65 V fixed, inp = Vx = 1.65 + d with d = the 12 trial overdrive limits 3.3/2^k (1.65 V ... 0.8 mV); per d the sequence +d,+d,-d,-d (prev decision same / opposite).
    # Charge window per decision = evaluate + reset of THAT cycle, [clk rise, next clk rise - 12 ns] (the input step to the next value starts 10 ns before the next rise); the testbench input step to the next value happens 10 ns before the next rise and is EXCLUDED
    # (the first version of this test integrated over the whole period and counted the source charging the pin capacitance for the next step, e.g. 'Qp +24.8 fC / Qn -16.5 fC' after the -10 mV row).
    ds = [3.3 / 2 ** k for k in range(1, 13)]; seq = [0.0]
    for x in ds: seq += [x, x, -x, -x]
    vp = [cm + s_ for s_ in seq]; vn = [cm] * len(seq)
    t, d = run(vp, vn); dec = decisions(t, d, len(seq))
    def q(k, key, tail=12e-9):
        ts = TCLK0 + k * TCYC; m = (t >= ts) & (t < ts + TCYC - tail); return -np.trapezoid(d[key][m], t[m])
    res = []
    for i, x in enumerate(ds):
        for j, lab in [(2, 'same'), (3, 'opp'), (4, 'same')]:    # cycles 2,3,4 of the group: prev decision same sign / opposite sign / same (negative)
            k = 1 + 4 * i + j - 1; sgn = 1 if seq[k] > 0 else -1
            qp, qn = q(k, 'i_p'), q(k, 'i_n'); ok = dec[k][0] == sgn
            res.append(f'{x*1e3:.1f}mV{"+" if sgn>0 else "-"}/{lab}{"" if ok else "(WRONG)"}:Qp={qp*1e15:.3f}fC,Qn={qn*1e15:.3f}fC,Qvdd={q(k,"i_vdd")*1e15:.0f}fC,Qp_tail14={q(k,"i_p",14e-9)*1e15:.3f}')
    print(f'KICK {corner} {T}C {cell} Vref=1.65 ' + ' '.join(res))
