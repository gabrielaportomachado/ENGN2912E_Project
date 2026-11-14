#!/usr/bin/env python3
"""D2 transistor-level DAC runs (tb/tb_dac_conv.spice, IDEAL SAR logic = scripted control waveforms).
usage: d2_conv.py settle <corner> <tempC> <T_ns> <vin1,vin2,...> [tag]   per-trial settling / supply charge, one line per Vin
       d2_conv.py samp   <corner> <tempC> <top_first|bottom_first> [tag]  sampling-switch transfer over 0-3.3 V (code 0 after the hold)
Prints result lines; saves the supply-current waveform of 'settle' runs to sim/d2_idd_<tag>.npz (for scripts/d2_supply.py)."""
import sys, os, subprocess, tempfile, shutil, atexit, numpy as np
H = os.path.dirname(os.path.abspath(__file__)); ADC = os.path.abspath(os.path.join(H, '..')); sys.path.insert(0, H)
import dlib; from d2lib import *
VSUP = 3.3; TR = 100e-12; NOV = 0.3e-9
def pwl(name, ev, v0, kind='V'):
    """ev = [(t, newvalue)] sorted; returns a PWL source line"""
    pts = [(0.0, v0)]; prev = v0
    for t, v in ev:
        if v == prev: continue
        pts += [(t, prev), (t + TR, v)]; prev = v
    return f'{kind}{name} {name} 0 PWL(' + ' '.join(f'{t:.4e} {v:.4f}' for t, v in pts) + ')'
def sar(vin, d):
    lv = d.levels(); code = 0
    for j in range(11, -1, -1):
        tr = code | (1 << j)
        if vin >= lv[tr]: code = tr
    return code
def control(mode, vins, T, TS=300e-9, order='top_first', d=None):
    """returns (control text, tend, list of (t_start_track, t_open, tc0) per cycle)"""
    d = d or Dac(); H1 = 1.0 * VSUP; ev = {k: [] for k in ['sam', 'samb', 'rst', 'rstm'] + [f'gp{j}' for j in range(12)] + ['gdp'] + [f'gn{j}' for j in range(12)] + ['gdn', 'vin']}
    t = 0.0; info = []
    for vin in vins:
        ev['vin'].append((t - 2e-9 if t > 0 else 0, vin))
        ev['sam'].append((t + 1.2e-9, VSUP)); ev['samb'].append((t + 1.2e-9, 0.0)); ev['rst'].append((t, VSUP)); ev['rstm'].append((t, VSUP))
        for j in range(12): ev[f'gp{j}'].append((t + 1e-9, VSUP)); ev[f'gn{j}'].append((t + 1e-9, 0.0))
        ev['gdp'].append((t + 1e-9, VSUP)); ev['gdn'].append((t + 1e-9, 0.0))
        to = t + TS
        if order == 'top_first':      # T and M switches open first; the drivers take over (gn rises) 1 ns after, while the sampling TG is still on (overlap AFTER the top plate is isolated: the sample is already taken)
            ev['rstm'].append((to, 0.0)); ev['rst'].append((to + 1e-9, 0.0)); tdrv = to + 2e-9; ev['sam'].append((to + 3e-9, 0.0)); ev['samb'].append((to + 3e-9, VSUP))
        else:                         # BAD order: bottom TG first (bottoms float), then top, then drivers
            ev['sam'].append((to, 0.0)); ev['samb'].append((to, VSUP)); ev['rstm'].append((to + 0.5e-9, 0.0)); ev['rst'].append((to + 1e-9, 0.0)); tdrv = to + 2e-9
        tc0 = tdrv
        ev['gdn'].append((tc0 + NOV, VSUP))
        if mode == 'conv':
            code = sar(vin, d); acc = 0; prev = 0
            for k in range(12):
                tk = tc0 + k * T; j = 11 - k; pat = acc | (1 << j)
                for b in range(12):
                    new = (pat >> b) & 1; old = (prev >> b) & 1
                    if k == 0:   # from hi-Z sampling state to defined
                        if new: ev[f'gp{b}'].append((tk, 0.0))            # MSB first: the plate never undershoots below 0 V
                        else: ev[f'gn{b}'].append((tk + NOV, VSUP))
                    elif new != old:
                        if new: ev[f'gn{b}'].append((tk, 0.0)); ev[f'gp{b}'].append((tk + NOV, 0.0))
                        else: ev[f'gp{b}'].append((tk, VSUP)); ev[f'gn{b}'].append((tk + NOV, VSUP))
                prev = pat
                if (code >> j) & 1: acc |= (1 << j)
            tend_c = tc0 + 12 * T
        else:   # samp: all bits to 0 and hold
            for b in range(11): ev[f'gn{b}'].append((tc0 + NOV, VSUP))
            ev['gp11'].append((tc0, 0.0))   # MSB high: keeps V_T inside 0..3.3 V for every Vin (as the first SAR trial does)
            tend_c = tc0 + T
        info.append((t, to, tc0, tend_c)); t = tend_c + 5e-9
    lines = []
    for k, e in ev.items():
        e = sorted(e, key=lambda x: x[0]); v0 = e[0][1] if e else 0.0
        if k == 'vin': lines.append(pwl('vin', e, v0, 'V').replace('Vvin vin', 'Vvin vin'))
        else: lines.append(pwl(k, e, v0))
    return '\n'.join(lines) + '\n', t + 10e-9, info
def run(corner, T, ctrl, tend, tag, extra=()):
    for k, (rt, tm) in enumerate((('1e-5', '50p'), ('2e-5', '40p'), ('5e-6', '60p'), ('1e-4', '30p'), ('3e-5', '70p'))):
        r = run1(corner, T, ctrl, tend, tag, extra, rt, tm)
        if r is not None: return r
    print(f'FAIL run {tag}: aborted in 5 attempts'); sys.exit(1)
def run1(corner, T, ctrl, tend, tag, extra, rt, tm):
    tmp = tempfile.mkdtemp(prefix='d2c_', dir=os.path.join(ADC, 'sim', '.ptmp')); atexit.register(shutil.rmtree, tmp, True)
    open(f'{tmp}/c.inc', 'w').write(ctrl); out = f'{tmp}/o.csv'
    e = dict(os.environ, OUT=out, SWAPS=f'@CTRL@={tmp}/c.inc @TEND@={tend:.6e} @RELTOL@={rt} @TMAX@={tm}', CELL='x')
    r = subprocess.run(['bash', f'{ADC}/scripts/dgrun.sh', 'tb_dac_conv.spice', corner, str(T)] + list(extra), capture_output=True, text=True, env=e)
    if not os.path.exists(out): return None
    try: t, d = dlib.load(out, ['t', 'm', 'idd', 'iin', 'b11', 'b5', 'b0'])
    except Exception: return None
    if t[-1] < tend - 2e-9: return None
    return t, d
if __name__ == '__main__':
    cmd, corner, temp = sys.argv[1], sys.argv[2], sys.argv[3]
    if cmd == 'settle':
        T = float(sys.argv[4]) * 1e-9; vins = [float(x) for x in sys.argv[5].split(',')]; tag = sys.argv[6] if len(sys.argv) > 6 else f'{corner}_{temp}_{sys.argv[4]}'
        dd = Dac(); res = []
        for vin in vins:
            ctrl, tend, info1 = control('conv', [vin], T); t, d = run(corner, temp, ctrl, tend, tag); (ts, to, tc0, te) = info1[0]; info = info1
            code = sar(vin, dd); trial_t = [tc0 + k * T for k in range(12)]
            vt = [np.interp(trial_t[k] + T - 0.3e-9 - NOV * 0, t, d['t']) for k in range(12)]    # settled value at the end of cycle k (just before the next switch)
            vd = [np.interp(trial_t[k] + T / 2, t, d['t']) for k in range(12)]                   # value at the comparator sample instant (clk rise at T/2)
            err = [(vd[k] - vt[k]) / LSB for k in range(12)]
            ts5 = []
            for k in range(12):
                m = (t >= trial_t[k]) & (t <= trial_t[k] + T - 0.3e-9); tt = t[m]; ve = np.abs(d['t'][m] - vt[k]); big = np.nonzero(ve > 0.5 * LSB)[0]
                ts5.append((tt[big[-1]] - trial_t[k] if len(big) else 0.0) * 1e9)
            # supply charge per cycle from the drivers (i(Vdd) is negative when sourcing)
            q = [-np.trapezoid(d['idd'][(t >= trial_t[k] - 0.5e-9) & (t < trial_t[k] + T)], t[(t >= trial_t[k] - 0.5e-9) & (t < trial_t[k] + T)]) * 1e12 for k in range(12)]
            res.append((vin, code, ts5, err, q))
            m2 = (t >= tc0 - 2e-9) & (t <= tc0 + 12 * T + 5e-9); np.savez(f'{ADC}/sim/d2_idd_{tag}_{vin:g}.npz', t=t[m2] - tc0, i=d['idd'][m2], iq=d['iin'][m2], T=T, vin=vin)
            print(f'SETTLE {corner} {temp}C T={T*1e9:.0f}ns vin={vin:.4f} code={code} | time to stay within 0.5 LSB [ns]: ' + ' '.join(f'{x:.1f}' for x in ts5) + ' | error at T/2 [LSB]: ' + ' '.join(f'{x:+.2f}' for x in err) + ' | supply charge per trial [pC]: ' + ' '.join(f'{x:.2f}' for x in q) + f' | total {sum(q):.2f} pC')
    elif cmd == 'samp':
        order = sys.argv[4]; tag = sys.argv[5] if len(sys.argv) > 5 else f'{corner}_{temp}_{order}'
        vins = [round(x, 4) for x in list(np.arange(0.0, 3.31, 0.1))]
        T = 60e-9; dd = Dac(cpt=190e-15); wsum = dd.weights()[0].sum() + dd.weights()[1]; vc = VSUP / 2
        vt = []; qin = []
        for vin in vins:
            ctrl, tend, info1 = control('samp', [vin], T, TS=300e-9, order=order); t, d = run(corner, temp, ctrl, tend, tag); (ts, to, tc0, te) = info1[0]
            vt.append(np.interp(tc0 + T - 2e-9, t, d['t'])); mk = (t >= ts) & (t <= to); qin.append(-np.trapezoid(d['iin'][mk], t[mk]) * 1e12)
        vt = np.array(vt); vins = np.array(vins); ideal = vc + VSUP * dd.weights()[0][11] - wsum * vins        # code 0: V_T = Vcm - Vin * sum(w) (sum(w) = 1 with no parasitics; CCMP attenuates, fitted below)
        out = []
        for nm, mk in (('1.15-2.15 V', (vins > 1.149) & (vins < 2.151)), ('0.0-3.3 V', vins >= 0)):
            p = np.polyfit(vins[mk], vt[mk], 1); res = vt[mk] - np.polyval(p, vins[mk])
            out.append(f'{nm}: gain {p[0]:+.5f} V/V, V_T error vs ideal (Vcm + w11 VDD - sum(w) Vin, sum(w) = {wsum:.4f}) at Vin = 1.65 V {(np.polyval(p, vc)-(vc+VSUP*dd.weights()[0][11]-wsum*vc))*1e3:+.3f} mV = {(np.polyval(p, vc)-(vc+VSUP*dd.weights()[0][11]-wsum*vc))/LSB:+.2f} LSB, gain error {(-p[0]-wsum)*100:+.3f} %, nonlinearity (max |residual| of the straight-line fit) {np.abs(res).max()/LSB:.3f} LSB = {np.abs(res).max()*1e3:.3f} mV')
        print(f'SAMP {corner} {temp}C order={order} | ' + ' | '.join(out) + f' | V_T(Vin=0.0/1.65/3.3) = {vt[0]:.5f}/{vt[16]:.5f}/{vt[33]:.5f} V | charge from the input per sample, mean over 0.1-3.2 V steps: see sampqin')
        np.savez(f'{ADC}/sim/d2_samp_{tag}.npz', vin=vins, vt=vt, qin=np.array(qin))
