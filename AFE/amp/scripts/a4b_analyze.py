#!/usr/bin/env python3
"""A4b analysis.  usage: python3 scripts/a4b_analyze.py <case>   reads /tmp/a4brun/<case>/*.csv, writes sim/a4b_<case>.log (+ stdout)."""
import sys, os, glob, math, re
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import a4b_lib as L
AMP = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
RUN = '/tmp/a4brun'
ORDER = ['typical_-40', 'typical_27', 'typical_85', 'ff_-40', 'ff_27', 'ff_85', 'ss_-40', 'ss_27', 'ss_85']
LSB = 3.3 / 4096
def num(s):
    return float(s.replace('m', 'e-3').replace('u', 'e-6').replace('n', 'e-9'))
def load(cs, label):
    return L.load(f'{RUN}/{cs}/{label}.csv')
def write(name, lines):
    txt = '\n'.join(lines) + '\n'
    open(f'{AMP}/sim/a4b_{name}.log', 'w').write(txt); print(txt)

def case_thd(D='thd'):
    out = ['# A4b THD / swing / DC drift: sine on the differential input, last 4 periods (LSQ fit, 9 harmonics), 8 s of settling for the pseudo-R DC drift.',
           '# VD pk differential; gain = fundamental/VD; ymax/ymin over the fit window; drift = mean - 1.65 V.  THD and swing are what T6 checks (target: +-500 uV -> 1.15..2.15 V, no clipping).',
           'corner    T  f_Hz   VD_mV  gain_dB  THD_%    mean_V  drift_mV  ymax_V  ymin_V  o2max  o2min']
    res = {}
    VDL = sorted({re.search(r'_f\d+_([\d.]+m)\.csv', x).group(1) for x in glob.glob(f'{RUN}/{D}/*.csv')}, key=num)
    for k in ORDER:
        for f, fl in ((12.25, 'f12'), (300, 'f300')):
            for vd in VDL:
                p = f'{RUN}/{D}/{k}_{fl}_{vd}.csv'
                if not os.path.exists(p): continue
                d = load(D, f'{k}_{fl}_{vd}')
                a1, thd, mean, h = L.harmonics(d['time'], d['out'], f, 4)
                m = d['time'] > d['time'][-1] - 4 / f
                g = 20 * math.log10(a1 / num(vd))
                c, T = k.split('_')
                out.append(f'{c:7s} {T:>4s} {f:6.2f} {num(vd)*1e3:7.2f} {g:8.3f} {thd*100:7.3f} {mean:8.4f} {(mean-1.65)*1e3:8.1f} {d["out"][m].max():7.3f} {d["out"][m].min():7.3f} {d["o2"][m].max():6.3f} {d["o2"][m].min():6.3f}')
                res[(k, f, vd)] = (g, thd * 100, mean, d['out'][m].max(), d['out'][m].min())
    # summary: worst over PVT at 0.5 mV; first amplitude with THD > 1 %
    out.append('')
    out.append('== SUMMARY (worst over the 9 PVT points)')
    for f in (12.25, 300):
        for vd in VDL:
            rr = [res[(k, f, vd)] for k in ORDER if (k, f, vd) in res]
            if rr:
                out.append(f'f={f:6.2f} Hz VD={num(vd)*1e3:4.2f} mV: THD max {max(r[1] for r in rr):7.3f} %  gain {min(r[0] for r in rr):.2f}..{max(r[0] for r in rr):.2f} dB  ymax max {max(r[3] for r in rr):.3f} V  ymin min {min(r[4] for r in rr):.3f} V  drift {min((r[2]-1.65)*1e3 for r in rr):.0f}..{max((r[2]-1.65)*1e3 for r in rr):.0f} mV')
    write(D, out)


def at(t, y, tq):
    return float(np.interp(tq, t, y))

def rest(t, y, t0, T):
    """v(out) rest value at t0+T: value just before the connect plus the pre-connect slope (the amplifier is still settling slowly from the offset step)"""
    v0 = at(t, y, t0 - 100e-9); v1 = at(t, y, t0 - 5.1e-6)
    return v0 + (v0 - v1) / 5.0e-6 * T

def last_outside(t, y, ref, tol, t0):
    """last time (>= t0) at which |y-ref| > tol; returns None if never outside; t[-1] if still outside at the end"""
    m = t >= t0
    tt, e = t[m], np.abs(y[m] - ref)
    idx = np.where(e > tol)[0]
    return None if len(idx) == 0 else float(tt[idx[-1]])

def case_slew():
    out = ['# A4b slew / step response: differential step VOS_REC = +-amp at t = 5 ms (IDEAL, 1 us edge), corners that ran (typical 27, ff 85, ss -40 + two typical -40 files from an earlier batch).  dv/dt from the output resampled at 2 us.',
           '# SR needed for 0.5 V pk at 300 Hz = 2 pi 300 0.5 = 942 V/s (ESTIMATE, PLAN T7).  ratio = max|dv/dt| / (final step) [1/s]: constant when linear, falls when slewing.',
           'corner    T   step_mV  dVout_V   max_up_V/s  max_dn_V/s  ratio_1/s   t10-90_us']
    rows = {}
    for k in ORDER:
        for sg in ('+', '-'):
            for amp in ('0.25m', '0.5m'):
                lab = f'{k}_s{sg}{amp}'
                if not os.path.exists(f'{RUN}/slew/{lab}.csv'): continue
                d = load('slew', lab)
                t, y = d['time'], d['out']
                tu = np.arange(0.004, t[-1], 2e-6); yu = np.interp(tu, t, y)
                dy = np.gradient(yu, tu)
                pre = at(t, y, 0.0049); fin = at(t, y, 0.0049 + 0.030)
                m = tu > 0.005
                up, dn = dy[m].max(), dy[m].min()
                step = fin - pre
                lo, hi = pre + 0.1 * step, pre + 0.9 * step
                tt = tu[m]; yy = yu[m]
                i10 = np.argmax((yy - lo) * np.sign(step) >= 0); i90 = np.argmax((yy - hi) * np.sign(step) >= 0)
                tr = (tt[i90] - tt[i10]) * 1e6
                ratio = (up if step > 0 else -dn) / abs(step)
                c, T = k.split('_')
                out.append(f'{c:7s} {T:>4s}  {sg}{num(amp)*1e3:5.2f}  {step:8.4f}  {up:10.0f}  {dn:10.0f}  {ratio:9.0f}  {tr:8.1f}')
                rows[(k, sg, amp)] = (step, up, dn, ratio, tr)
    out.append('')
    out.append('== SUMMARY: lowest max|dv/dt| for a +-0.5 mV step (0.5 V out step) over 9 PVT, vs the 942 V/s requirement; ratio(0.5 mV)/ratio(0.25 mV) = linearity (1.00 = no slewing)')
    for sg in ('+', '-'):
        v = [(abs(rows[(k, sg, '0.5m')][1] if sg == '+' else rows[(k, sg, '0.5m')][2]), k) for k in ORDER if (k, sg, '0.5m') in rows]
        if v:
            lo = min(v)
            lin = [rows[(k, sg, '0.5m')][3] / rows[(k, sg, '0.25m')][3] for k in ORDER if (k, sg, '0.5m') in rows and (k, sg, '0.25m') in rows]
            out.append(f'step {sg}0.5 mV: min max|dv/dt| = {lo[0]:.0f} V/s at {lo[1]}; max over PVT {max(x[0] for x in v):.0f} V/s; linearity ratio {min(lin):.3f}..{max(lin):.3f}')
    write('slew', out)

def case_adc():
    TS = [(3e-6, '3'), (4.6e-6, '4.6'), (7.8e-6, '7.8'), (11.05e-6, '11.05'), (12.425e-6, '12.4'), (13.625e-6, '13.6'), (14.625e-6, '14.6')]
    out = ['# A4b ADC load (Decision 28): C_s = 17 pF behind R_ADC = 1 kOhm (IDEAL conductance), C_OFF 20 fF.  RESET runs: C_s is reset to VOUT_CM = 1.65 V and the amplifier holds 1.65 +- 0.5 V (REC offset step +-0.5 mV, 5 ms earlier); step = v(out)_rest - 1.65 V.',
           '# NORESET rows (reference): C_s keeps the previous channel level 1.65 +- 1 V (the D0 model, IDEAL precharge source), sine off.  err(T) = v(C_s)(t0+T) - v(out) just before the connect [LSB, 0.806 mV];',
           '# xtalk = the same error referred to the amplifier input (error / 1000) [uV].  Criterion (Decision 24): |err| <= 0.5 LSB at T_ACQ = 11.05 us (SCLK 3.5 MHz); T_ACQ = 15.625 us - 16/f_SCLK: 12.4 us at 5 MHz, 13.6 at 8, 14.6 at 16 MHz.',
           'corner    T   case          step_V   ' + '  '.join(f'err@{n}us' for _, n in TS) + '   xtalk@11.05_uV  kick_peak_mV']
    res = {}
    labs = sorted(os.path.basename(f)[:-4] for f in glob.glob(f'{RUN}/adc/*.csv'))
    def key(l):
        m = re.match(r'(\w+_-?\d+)_(.*)', l); return (ORDER.index(m.group(1)), m.group(2))
    for lab in sorted(labs, key=key):
        m = re.match(r'(\w+_-?\d+)_(s[+-]0.5m|noreset[+-]1)$', lab)
        if not m: continue
        k, case = m.groups()
        d = load('adc', lab); t, cs, vo = d['time'], d['cs'], d['out']
        t0 = 5e-6 if case.startswith('noreset') else 2e-3
        if t[-1] < t0 + 40e-6: out.append(f'{k}  {case}  INCOMPLETE (run ends at {t[-1]:.4g} s)'); continue
        vf = at(t, vo, t0 - 100e-9)
        e = [(at(t, cs, t0 + T) - rest(t, vo, t0, T)) / LSB for T, _ in TS]
        kick = np.abs(vo[(t >= t0) & (t <= t0 + 40e-6)] - vf).max() * 1e3
        c, Tm = k.split('_')
        out.append(f'{c:7s} {Tm:>4s}  {case:12s} {vf-1.65:8.3f}  ' + ' '.join(f'{x:9.3f}' for x in e) + f'   {e[3]*LSB*1e3:10.3f}  {kick:12.1f}')
        res[(k, case)] = e
    out.append('')
    out.append('== SUMMARY (worst over the corners that ran); pass = |err| <= 0.5 LSB')
    for case in ('s+0.5m', 's-0.5m', 'noreset+1', 'noreset-1'):
        r = [(k, v) for (k, c), v in res.items() if c == case]
        if r:
            w = [max(abs(v[i]) for _, v in r) for i in range(len(TS))]
            wk = max(r, key=lambda kv: abs(kv[1][3]))[0]
            out.append(f'{case:11s}: worst |err| ' + '  '.join(f'@{n}us {w[i]:.3f}' for i, (_, n) in enumerate(TS)) + f'  -> @11.05 us {"PASS" if w[3] <= 0.5 else "FAIL"} (worst at {wk}); xtalk {w[3]*LSB*1e3:.2f} uV input-referred; corners: {len(r)}')
    write('adc', out)

def case_adcks():
    ks = [6, 9, 12, 18, 24, 36]
    out = ['# A4b: follower sink sweep, hard (downward) step v(out)_rest = 1.65 - 0.5 V, C_s reset to 1.65 V.  BM_KSF = number of 16u/4u mirror legs of the follower sink (A4a/A4b baseline 6, typ 5.2 uA, 3.3-8.4 uA over PVT).',
           'err = v(C_s)(t0 + 11.05 us) - v(out)_rest, LSB (sign: the held value is above the rest value when positive).  Required: |err| <= 0.5 LSB at 9 PVT.',
           'corner    T  ' + ' '.join(f'ksf={x:<3d}' for x in ks)]
    res = {}
    for k in ORDER:
        row = []
        for x in ks:
            p = f'{RUN}/adcks/{k}_ksf{x}.csv'
            if not os.path.exists(p): row.append(float('nan')); continue
            d = load('adcks', f'{k}_ksf{x}'); t = d['time']
            if t[-1] < 2e-3 + 40e-6: row.append(float('nan')); continue
            row.append((at(t, d['cs'], 2e-3 + 11.05e-6) - rest(t, d['out'], 2e-3, 11.05e-6)) / LSB)
        res[k] = row
        c, T = k.split('_')
        out.append(f'{c:7s} {T:>4s}  ' + ' '.join(f'{x:8.3f}' for x in row))
    out.append('')
    ok = [x for i, x in enumerate(ks) if all(abs(res[k][i]) <= 0.5 for k in ORDER if not math.isnan(res[k][i]))]
    out.append(f'== smallest BM_KSF in the sweep with |err| <= 0.5 LSB at every corner that ran: {ok[0] if ok else "none (>36)"}; worst |err| at each value: ' + ', '.join(f'{x}: {max(abs(res[k][i]) for k in ORDER if not math.isnan(res[k][i])):.3f}' for i, x in enumerate(ks)))
    out.append('   extra sink per channel = (BM_KSF - 6) x 0.87 uA typ (master 0.85 uA x 1 unit/leg: follower sink = 5.2 uA typ at BM_KSF 6); x N channels x 3.3 V = power: N = 8 (Decision 29): KSF 24 -> +15.7 uA x 8 x 3.3 V = 0.41 mW typ, KSF 36 -> +26 uA x 8 x 3.3 V = 0.69 mW typ (the sweep itself is for the +-0.5 V step after the 1.65 V reset; with one ADC per channel (Decision 34) the reset is optional and the window ~245 us: see a4b_adc245.log).')
    write('adcks', out)

def case_adc2():
    out = ['# A4b ADC load, T_ACQ = 11.05 us exactly (Decision 24), then 400 us of observation: what the amplifier does after C_s is disconnected.',
           '# err = v(C_s) held after the disconnect minus the rest value of v(out) before the connect (LSB); kick = peak |v(out) - rest| over the whole event (mV); after disconnect: peak of |v(out)-rest| (mV),',
           '# time until |v(out)-rest| <= 0.5 LSB for good (us after the disconnect), number of sign changes of v(out)-rest beyond 0.1 LSB (ringing: 0 or 1 = monotonic/one overshoot), value at +100 us / +240 us (the next channel connect comes 250 us later).',
           'corner    T   dV_V   err_LSB  kick_mV  post_peak_mV  t_settle_us  sign_changes  out-rest@100us_mV  @240us_mV']
    res = []
    for k in ORDER:
        for dv in ('+0.5m', '-0.5m'):
            lab = f'{k}_s{dv}'
            if not os.path.exists(f'{RUN}/adc2/{lab}.csv'): continue
            d = load('adc2', lab); t, cs, vo = d['time'], d['cs'], d['out']
            t0 = 2e-3; td = t0 + 11.05e-6
            vf = at(t, vo, t0 - 100e-9)
            err = (at(t, cs, td + 1e-6) - vf) / LSB
            kick = np.abs(vo[(t >= t0) & (t <= t[-1])] - vf).max() * 1e3
            m = t >= td
            post = np.abs(vo[m] - vf).max() * 1e3
            tl = last_outside(t, vo, vf, 0.5 * LSB, td)
            tset = 0.0 if tl is None else (tl - td) * 1e6 if tl < t[-1] - 1e-9 else float('inf')
            e = vo[m] - vf; sg = np.sign(e[np.abs(e) > 0.1 * LSB]); sc = int(np.sum(sg[1:] != sg[:-1])) if len(sg) > 1 else 0
            c, T = k.split('_')
            out.append(f'{c:7s} {T:>4s} {dv:>6s} {err:9.3f} {kick:8.1f} {post:12.1f} {tset:11.2f} {sc:9d}  {(at(t, vo, td+100e-6)-vf)*1e3:14.3f} {(at(t, vo, td+240e-6)-vf)*1e3:10.3f}')
            res.append((err, tset, sc, k, dv))
    out.append('')
    out.append(f'== SUMMARY: worst |err| = {max(abs(r[0]) for r in res):.3f} LSB; worst settle after disconnect = {max(r[1] for r in res):.2f} us; max sign changes = {max(r[2] for r in res)}')
    write('adc2', out)

def verdict(t, v1, trel):
    """stage-1 output after a release: stuck at a rail or just recovering?"""
    tend = t[-1]
    v_end = at(t, v1, tend); v_prev = at(t, v1, tend - 0.1 * (tend - trel))
    rail = v_end < 0.3 or v_end > 3.0
    moving = abs(v_end - v_prev) > 2e-3
    return ('STUCK at rail' if rail and not moving else 'at rail, still moving' if rail else 'recovering' if moving else 'settled'), v_end

def case_fscharge():
    out = ['# A4b fast-settle pulse alone (no offset, no input signal): fs high from t0 = 10 ms for W (edges 10 ns), IDEAL control.  pre = value just before the pulse; jump = output - pre at the given time after the falling edge ends.',
           '# dv1/dout@10us = change of the stage-1 / channel output between 1 us before and 10 us after the release; Q1 = Cf1 (200 fF) x dv1 (ESTIMATE of the charge injected into the stage-1 summing node).',
           '# settle = last time after release with |out - pre| > thr (never = still outside at the end of the 12 s window).  v1 verdict: stage-1 output stuck at a rail / still moving / settled at the end of the window.',
           'corner    T   W_s    during_mV  dout@10us dv1@10us_mV  Q1_fC   jump@1ms jump@100ms jump@1s jump@end_mV   peak_mV   t_<10mV   t_<1mV    v1_end_V  v1 verdict']
    for k in ORDER:
        for w in ('100n', '300n', '10u', '100u', '1m', '10m'):
            lab = f'{k}_w{w}'
            if not os.path.exists(f'{RUN}/fscharge/{lab}.csv'): continue
            d = load('fscharge', lab); t, y, v1 = d['time'], d['out'], d['v1']
            t0 = 0.01; W = num(w); trel = t0 + 20e-9 + W
            pre = at(t, y, t0 - 1e-6)
            during = (at(t, y, t0 + 20e-9 + 0.9 * W) - pre) * 1e3
            dout = (at(t, y, trel + 10e-6) - at(t, y, trel - 1e-6)) * 1e3
            dv1 = (at(t, v1, trel + 10e-6) - at(t, v1, trel - 1e-6)) * 1e3
            q1 = dv1 * 1e-3 * 200e-15 * 1e15
            j = [(at(t, y, trel + x) - pre) * 1e3 for x in (1e-3, 0.1, 1.0, t[-1] - trel - 1e-3)]
            m = (t >= trel) & (t <= trel + 1.0); peak = np.abs(y[m] - pre).max() * 1e3
            def ts(thr):
                tl = last_outside(t, y, pre, thr, trel)
                return 0.0 if tl is None else (tl - trel if tl < t[-1] - 1e-9 else float('inf'))
            vd, vend = verdict(t, v1, trel)
            c, T = k.split('_')
            out.append(f'{c:7s} {T:>4s} {w:>5s}  {during:9.2f} {dout:9.2f} {dv1:10.2f} {q1:7.2f}  {j[0]:8.2f} {j[1]:9.2f} {j[2]:7.2f} {j[3]:9.2f}  {peak:9.2f}  {fmt_t(ts(10e-3)):>8s} {fmt_t(ts(1e-3)):>8s}   {vend:7.3f}  {vd}')
    write('fscharge', out)

def recov_metrics(d, t_step, trel, vexp=None):
    t, y = d['time'], d['out']
    pre = at(t, y, t_step - 5e-3)
    n = len(t); tend = t[-1]
    fin = at(t, y, tend)
    late = at(t, y, tend - 0.03 * (tend - t_step))
    settled = abs(fin - late) < 0.2e-3
    m = t >= t_step
    ymax, ymin = y[m].max(), y[m].min()
    mm = (t >= trel) & (t <= trel + 1.0)
    peak_after = np.abs(y[mm] - pre).max() if mm.any() else float('nan')
    r = {'pre': pre, 'fin': fin, 'settled': settled, 'ymax': ymax, 'ymin': ymin, 'peak_after': peak_after,
         'peak_all': np.abs(y[m] - pre).max(), 'd100us': at(t, y, trel + 100e-6) - pre, 'd10ms': at(t, y, trel + 10e-3) - pre, 'd100ms': at(t, y, trel + 0.1) - pre}
    for nm, thr in (('t10', 10e-3), ('t1', 1e-3), ('t04', 0.4032e-3)):
        tl = last_outside(t, y, fin, thr, trel)
        r[nm] = 0.0 if tl is None else (tl - trel if tl < tend - 1e-6 else float('inf'))
    return r

def fmt_t(x):
    return 'never' if x == float('inf') else f'{x:.4g}'

def case_recov():
    out = ['# A4b recovery after an electrode DC-offset step on REC (IDEAL, 1 us edge) at t = 0.1 s, with and without a fast-settle pulse (IDEAL fs, 3.3 V, edges 10 ns) starting at the same time.',
           '# pre = output before the step; settle references = the output at the END of the run (settled = last 3 % moved < 0.2 mV); t_x = time after the step (no fs) or after fs release (fs) of the LAST excursion beyond x of the final value;',
           '# 10 mV = 12 LSB, 1 mV = 1.2 LSB, 0.4 mV = 0.5 LSB.  "never" = still outside at the end of the simulated window.  Output clips below ~0.8 V / above ~2.2 V (see thd log).  The step of the offset in the unspecified-requirement sweep is not a pass/fail test.',
           'corner    T   step_mV  fsW_s    ymin_V  ymax_V  peak_after_rel_mV  d@100us_mV d@10ms_mV d@100ms_mV  fin-pre_mV settled  t_10mV_s  t_1mV_s  t_0.5LSB_s  (window_s)']
    rows = []
    for f in sorted(glob.glob(f'{RUN}/recov/*.csv')):
        lab = os.path.basename(f)[:-4]
        mt = re.match(r'(\w+_-?\d+)_os([\d.]+m)_w(\w+)$', lab)
        if not mt: continue
        k, amp, w = mt.groups()
        d = load('recov', lab)
        W = 0.0 if w == '0' else num(w)
        trel = 0.1 + (20e-9 + W if W > 0 else 0.0)
        r = recov_metrics(d, 0.1, trel)
        rows.append((ORDER.index(k) if k in ORDER else 99, num(amp), W, k, amp, w, r, d['time'][-1]))
    for _, a, W, k, amp, w, r, tend in sorted(rows, key=lambda x: (x[0], x[1], x[2])):
        c, T = k.split('_')
        out.append(f'{c:7s} {T:>4s}  {a*1e3:7.1f}  {w:>6s}  {r["ymin"]:7.3f} {r["ymax"]:7.3f}  {r["peak_after"]*1e3:14.1f}  {r["d100us"]*1e3:10.2f} {r["d10ms"]*1e3:9.2f} {r["d100ms"]*1e3:10.2f}  {(r["fin"]-r["pre"])*1e3:9.2f}  {int(r["settled"])}   {fmt_t(r["t10"]):>8s} {fmt_t(r["t1"]):>8s} {fmt_t(r["t04"]):>9s}   ({tend:.0f})')
    write('recov', out)

def case_tg():
    out = ['# A4b TGATE (existing TGATE.spice, 5 V devices, VDD5 = 5 V, read-only include) in series between the REC electrode and Cin1.  sw_rec: closed until 0.2 s, OPEN 0.2..0.5 s, closes at 0.5 s (10 ns edges).',
           '# REC offset step (IDEAL) at 0.3 s while the switch is open = the TREAT->REC event.  fs (IDEAL control) asserted 10 us BEFORE the TGATE closes, released T_FS after it closes (T_FS = 0.1 / 1 / 10 ms); "nofs" = no fast-settle.',
           '# gain rows: 12.25 Hz, 100 uV pk, switch always closed vs no TGATE.']
    for f in sorted(glob.glob(f'{RUN}/tg/*sine*.csv')):
        lab = os.path.basename(f)[:-4]; d = load('tg', lab)
        a1, thd, mean, h = L.harmonics(d['time'], d['out'], 12.25, 4)
        out.append(f'gain {lab:34s} fund {a1:.5f} V  gain {20*math.log10(a1/100e-6):.3f} dB  THD {thd*100:.3f} %')
    out.append('')
    out.append('toggle / recovery rows: pre = out before the switch opens (0.19 s); jump_off = max |out - pre| within 100 us after the switch opens (charge injection at opening); drift = out(0.4999 s) - pre (leakage while open + the offset step passes only through Cin);')
    out.append('dout/dv1@close = change of the channel / stage-1 output between 1 us before and 10 us after the switch closes (or after the fs release when fs is used: marked REL); peak = max |out - pre| after closing (1 s window); t_x = last time after the')
    out.append('release (fs) or after the closing (nofs) with |out - final| > x; final = value at the end of the window; "never" = still outside at the end.  v1 verdict as in the fscharge log.')
    out.append('run                                         jump_off drift_mV  dout@ev  dv1@ev  Q1_fC   peak_mV  fin-pre_mV  t_<10mV_s  t_<1mV_s   window_s  v1 verdict')
    for f in sorted(glob.glob(f'{RUN}/tg/*tgtog*.csv')):
        lab = os.path.basename(f)[:-4]; d = load('tg', lab)
        t, y, v1 = d['time'], d['out'], d['v1']
        if t[-1] < 5:
            out.append(f'{lab:43s} INCOMPLETE (run ends at {t[-1]:.3g} s)'); continue
        mw = re.search(r'_fs([\d.]+)m$', lab)
        if mw:
            tev = 0.5 + float(mw.group(1)) * 1e-3 + 10e-9      # release of the fs pulse (FS_T0 = 0.49999, width T_FS + 10 us)
        else:
            tev = 0.5
        pre = at(t, y, 0.19)
        joff = np.abs(y[(t >= 0.2) & (t <= 0.2 + 100e-6)] - pre).max() * 1e3
        drift = (at(t, y, 0.4999) - pre) * 1e3
        dout = (at(t, y, tev + 10e-6) - at(t, y, tev - 1e-6)) * 1e3
        dv1 = (at(t, v1, tev + 10e-6) - at(t, v1, tev - 1e-6)) * 1e3
        m = (t >= tev) & (t <= tev + 1.0); peak = np.abs(y[m] - pre).max() * 1e3
        fin = at(t, y, t[-1])
        r = {}
        for nm, thr in (('t10', 10e-3), ('t1', 1e-3)):
            tl = last_outside(t, y, fin, thr, tev)
            r[nm] = 0.0 if tl is None else (tl - tev if tl < t[-1] - 1e-6 else float('inf'))
        vd, _ = verdict(t, v1, tev)
        out.append(f'{lab:43s} {joff:8.2f} {drift:8.2f}  {dout:8.2f} {dv1:7.2f} {dv1*0.2:7.2f}  {peak:8.1f}  {(fin-pre)*1e3:9.2f}  {fmt_t(r["t10"]):>9s} {fmt_t(r["t1"]):>8s}   {t[-1]:7.0f}   {vd}')
    write('tg', out)

def case_pwrup():
    out = ['# A4b power-up: VDD ramps 0 -> 3.3 V in PU_T from the all-zero state (no nodesets); electrode source at the 1.65 V tissue node from t = 0; fs = control derived from VDD (follows the ramp), released at 1 ms + PU_T when "fs1".',
           '# idm = master Mn1 current, idb1 = OTA1 IBIAS sink, both read at the END of the run (last 1 s average) and compared with the DC operating point (case "op", same netlist, PU_T = 0) of the same corner.',
           '# t90 = time for idm to reach 90 % of its final value; t_<10mV = last time |out - 1.65 V| > 10 mV after the ramp; peak = max |out - 1.65 V| during the run.',
           'corner    T  PU_T   fs   idm_uA (op_uA)  idb1_uA (op_uA)  isup_uA  t90_idm_ms  out_final_mV  peak_V   t_<10mV_s  t_<1mV_s   window_s  settled']
    ref = {}
    for f in sorted(glob.glob(f'{RUN}/pwrup/*_op.csv')):
        lab = os.path.basename(f)[:-4]; d = load('pwrup', lab)
        ref[lab[:-3]] = (d['idm'][0], d['idb1'][0])
    for f in sorted(glob.glob(f'{RUN}/pwrup/*_pu*.csv'), key=lambda x: (ORDER.index(re.match(r'.*/(\w+_-?\d+)_pu', x).group(1)) if re.match(r'.*/(\w+_-?\d+)_pu', x) and re.match(r'.*/(\w+_-?\d+)_pu', x).group(1) in ORDER else 99, x)):
        lab = os.path.basename(f)[:-4]
        mt = re.match(r'(\w+_-?\d+)_pu(\w+)_fs(\d)$', lab)
        k, pu, fs = mt.groups(); d = load('pwrup', lab); t = d['time']; tend = t[-1]
        m = t > tend - 1.0
        idm, idb, isup = d['idm'][m].mean(), d['idb1'][m].mean(), d['isup'][m].mean()
        r = ref.get(k, (float('nan'), float('nan')))
        i90 = np.argmax(d['idm'] >= 0.9 * idm); t90 = t[i90] * 1e3
        dv = d['out'] - 1.65; fin = dv[m].mean()
        tp = num(pu)
        mm = t > tp
        peak = np.abs(dv[mm]).max() if mm.any() else float('nan')
        res = []
        for thr in (10e-3, 1e-3):
            tl = last_outside(t, d['out'], 1.65, thr, tp)
            res.append(0.0 if tl is None else (tl if tl < tend - 1e-6 else float('inf')))
        late = abs(d['out'][m].mean() - at(t, d['out'], tend - 0.5 * (tend - tp)))
        c, T = k.split('_')
        out.append(f'{c:7s} {T:>4s} {pu:>5s}  {fs}  {idm*1e6:8.3f} ({r[0]*1e6:6.3f})  {idb*1e6:8.2f} ({r[1]*1e6:6.2f})  {isup*1e6:7.1f}  {t90:9.3f}   {fin*1e3:9.1f}  {peak:7.3f}  {fmt_t(res[0]):>8s} {fmt_t(res[1]):>8s}   {tend:6.0f}   {int(late < 2e-3)}')
    write('pwrup', out)

def case_fsfix():
    out = ['# A4b priority 1: fast-settle pulse alone (typical 27 C, no offset, no signal), t0 = 10 ms, 12 s window.  Diagnosis: with the switch closed the stage-1 loop is OTA1 as a unity-gain follower (A3: PM -45 deg at beta = 1) and oscillates;',
           '# osc_pp = peak-peak of v(stage-1 output) during the second half of the pulse (> 10 mV = oscillating); at the release the summing node is wherever the oscillation left it, the loop (beta = 0.01) cannot pull it back and the output goes to a rail.',
           '# dout/dv1@10us = change of the channel / stage-1 output between 1 us before and 10 us after the release; "ok" = |out - pre| < 1 mV at +1 s and at the end of the window.',
           'variant           W_s     TR_s    osc_pp_mV  vn1_pp_mV  dout@10us  dv1@10us  out-pre@1ms  @100ms   @1s   @end_mV   t_<1mV_s  t_<10mV_s  v1_end_V  v1 verdict            ok']
    rows = []
    for f in glob.glob(f'{RUN}/fsfix/*.csv'):
        lab = os.path.basename(f)[:-4]
        m = re.match(r'(short_w|edge_tr|rfs_|ccx_|ff_short_w|ss_short_w)(\w+)$', lab)
        if not m: continue
        kind, val = m.groups()
        if kind == 'short_w': W, TR = num(val), 10e-9
        elif kind == 'edge_tr': W, TR = 10e-6, num(val)
        elif kind.endswith('short_w'): W, TR = num(val), 10e-9
        else: W, TR = 100e-6, 10e-9
        rows.append((kind, num(val.replace('M', 'e6')) if kind == 'rfs_' else num(val), lab, W, TR))
    for kind, v, lab, W, TR in sorted(rows):
        d = load('fsfix', lab); t, y, v1, vn1 = d['time'], d['out'], d['v1'], d['vn1']
        t0 = 0.01; trel = t0 + 2 * TR + W
        if t[-1] < 11.9: out.append(f'{lab:16s} INCOMPLETE (ends {t[-1]:.3g} s)'); continue
        pre = at(t, y, t0 - 1e-6)
        m = (t > t0 + 0.5 * W) & (t < trel)
        osc = (v1[m].max() - v1[m].min()) * 1e3 if m.sum() > 2 else float('nan'); vnp = (vn1[m].max() - vn1[m].min()) * 1e3 if m.sum() > 2 else float('nan')
        dout = (at(t, y, trel + 10e-6) - at(t, y, trel - 0.5 * min(W, 1e-6))) * 1e3
        dv1 = (at(t, v1, trel + 10e-6) - at(t, v1, trel - 0.5 * min(W, 1e-6))) * 1e3
        j = [(at(t, y, trel + x) - pre) * 1e3 for x in (1e-3, 0.1, 1.0, t[-1] - trel - 1e-3)]
        def ts(thr):
            tl = last_outside(t, y, pre, thr, trel)
            return 0.0 if tl is None else (tl - trel if tl < t[-1] - 1e-9 else float('inf'))
        vd, vend = verdict(t, v1, trel)
        ok = abs(j[2]) < 1 and abs(j[3]) < 1
        out.append(f'{lab:16s} {W:7.3g} {TR:8.3g}  {osc:9.1f} {vnp:9.1f}  {dout:9.2f} {dv1:9.2f}  {j[0]:10.2f} {j[1]:8.2f} {j[2]:7.2f} {j[3]:8.2f}   {fmt_t(ts(1e-3)):>8s} {fmt_t(ts(10e-3)):>9s}  {vend:7.3f}  {vd:20s} {"ok" if ok else "NO"}')
    write('fsfix', out)

def fs_edges(t, fs, tmin, tmax, thr=1.65):
    m = (t >= tmin) & (t <= tmax); tt, f = t[m], fs[m]
    up = np.where((f[:-1] < thr) & (f[1:] >= thr))[0]; dn = np.where((f[:-1] >= thr) & (f[1:] < thr))[0]
    if len(up) == 0 or len(dn) == 0: return None, None
    i, j = up[0], dn[dn > up[0]][0] if (dn > up[0]).any() else None
    if j is None: return None, None
    tu = tt[i] + (thr - f[i]) / (f[i + 1] - f[i]) * (tt[i + 1] - tt[i]); td = tt[j] + (thr - f[j]) / (f[j + 1] - f[j]) * (tt[j + 1] - tt[j])
    return tu, td

def case_fsos():
    out = ['# A4b item 3: the fast-settle control from the REAL one-shot (spice/fs_oneshot.spice: poly RC delay + NAND + inverter, 3.3 V gates), pulse alone (no offset, no signal), trigger edge at t0 = 10 ms.',
           '# width = fs 50 % crossings; sel = 0 -> C = CA, sel = 1 -> CA + CB.  Release behaviour as in a4b_fscharge.log (dout/dv1 = step 1 us before .. 10 us after the falling edge).',
           'corner    T  sel  width_ns  osc_pp_mV  dout@10us dv1@10us  out-pre@1ms  @1s    @end_mV   t_<1mV_s  t_<10mV_s  v1_end_V  v1 verdict   ok']
    for k in ORDER:
        for sel in (0, 1):
            lab = f'{k}_sel{sel}'
            if not os.path.exists(f'{RUN}/fsos/{lab}.csv'): continue
            d = load('fsos', lab); t, y, v1 = d['time'], d['out'], d['v1']
            tu, td = fs_edges(t, d['fs'], 9e-3, 0.5)
            if tu is None or t[-1] < 11.9: out.append(f'{k} sel{sel}: INCOMPLETE or no pulse'); continue
            pre = at(t, y, 9.9e-3); m = (t > tu) & (t < td)
            osc = (v1[m].max() - v1[m].min()) * 1e3
            dout = (at(t, y, td + 10e-6) - at(t, y, td - 20e-9)) * 1e3; dv1 = (at(t, v1, td + 10e-6) - at(t, v1, td - 20e-9)) * 1e3
            j = [(at(t, y, td + x) - pre) * 1e3 for x in (1e-3, 1.0, t[-1] - td - 1e-3)]
            def ts(thr):
                tl = last_outside(t, y, pre, thr, td)
                return 0.0 if tl is None else (tl - td if tl < t[-1] - 1e-9 else float('inf'))
            vd, vend = verdict(t, v1, td)
            c, T = k.split('_')
            out.append(f'{c:7s} {T:>4s}  {sel}  {(td-tu)*1e9:8.1f}  {osc:9.1f}  {dout:9.2f} {dv1:8.2f}  {j[0]:10.2f} {j[1]:7.2f} {j[2]:8.2f}   {fmt_t(ts(1e-3)):>8s} {fmt_t(ts(10e-3)):>9s}  {vend:7.3f}  {vd:12s} {"ok" if abs(j[1]) < 1 and abs(j[2]) < 1 else "NO"}')
    write('fsos', out)

def case_tgos():
    out = ['# A4b: record-path TGATE (3.3 V, real gate drive) opens at 0.2 s, REC offset step (IDEAL) at 0.3 s while it is open, TGATE closes at 0.5 s; the REAL one-shot (width sel 0 ~100 ns / sel 1 ~300 ns) is triggered by the closing edge.',
           '# pre = output before the switch opens; final = end of the run (40 s); peak = max |out - pre| after the release (1 s window); dout/dv1 = step 20 ns before .. 10 us after the release; "ok" = |final - pre| < 1 mV AND |out - pre| < 1 mV from t_<1mV on.',
           'corner    T  step_mV sel  width_ns   peak_mV  dout@10us  dv1@10us  out-pre@1s  fin-pre_mV   t_<10mV_s  t_<1mV_s  v1_end_V  v1 verdict']
    for k in ORDER:
        for a in ('1m', '10m', '100m'):
            for sel in (0, 1):
                lab = f'{k}_tgos_os{a}_sel{sel}'
                if not os.path.exists(f'{RUN}/tgos/{lab}.csv'): continue
                d = load('tgos', lab); t, y, v1 = d['time'], d['out'], d['v1']
                tu, td = fs_edges(t, d['fs'], 0.49, 0.6)
                if tu is None or t[-1] < 23: out.append(f'{lab}: INCOMPLETE or no pulse (ends {t[-1]:.3g} s)'); continue
                pre = at(t, y, 0.19); m = (t >= td) & (t <= td + 1.0); fin = at(t, y, t[-1])
                dout = (at(t, y, td + 10e-6) - at(t, y, td - 20e-9)) * 1e3; dv1 = (at(t, v1, td + 10e-6) - at(t, v1, td - 20e-9)) * 1e3
                r = {}
                for nm, thr in (('t10', 10e-3), ('t1', 1e-3)):
                    tl = last_outside(t, y, fin, thr, td); r[nm] = 0.0 if tl is None else (tl - td if tl < t[-1] - 1e-6 else float('inf'))
                vd, vend = verdict(t, v1, td)
                c, T = k.split('_')
                out.append(f'{c:7s} {T:>4s}  {num(a)*1e3:6.0f}   {sel}  {(td-tu)*1e9:8.1f}  {np.abs(y[m]-pre).max()*1e3:9.1f}  {dout:9.2f} {dv1:9.2f}  {(at(t,y,td+1.0)-pre)*1e3:10.2f}  {(fin-pre)*1e3:10.2f}   {fmt_t(r["t10"]):>9s} {fmt_t(r["t1"]):>9s}  {vend:7.3f}  {vd}')
    write('tgos', out)

def case_padfloat():
    out = ['# A4b item 2: pad loading ON THE REC NODE AND THE E NODE (ASSUMPTION values: C_PAD = ESD/pad capacitance to ground, I_LEAK = leakage out of the node to ground), with the routing TGATE (3.3 V) OPEN 0.2..0.5 s so REC floats.',
           '# pre = output before the switch opens (0.19 s); open_min/open_max = output extremes while open; drift_open = out(0.4999 s) - pre.  After the close: peak = max |out - pre| in the next second, t_x = last time |out - final| > x (final = 60 s),',
           '# fsos = the real one-shot (sel 1, ~300 ns) triggered by the closing edge.  rail = output outside 0.3..3.0 V at any time while open.',
           'corner    T  C_PAD  I_LEAK  fs     open_min_V open_max_V drift_open_mV   peak_mV  fin-pre_mV   t_<10mV_s  t_<1mV_s  v1 verdict']
    for k in ORDER:
        for cp in ('0', '10p'):
            for il in ('0', '1p', '10p'):
                for fsm in ('nofs', 'fsos'):
                    lab = f'{k}_pad{cp}_leak{il}_{fsm}'
                    if not os.path.exists(f'{RUN}/padfloat/{lab}.csv'): continue
                    d = load('padfloat', lab); t, y, v1 = d['time'], d['out'], d['v1']
                    if t[-1] < 29: out.append(f'{lab}: INCOMPLETE'); continue
                    pre = at(t, y, 0.19); mo = (t >= 0.2) & (t <= 0.4999)
                    if fsm == 'fsos':
                        tu, td = fs_edges(t, d['fs'], 0.49, 0.6); tev = td if td else 0.5
                    else: tev = 0.5
                    m = (t >= tev) & (t <= tev + 1.0); fin = at(t, y, t[-1]); r = {}
                    for nm, thr in (('t10', 10e-3), ('t1', 1e-3)):
                        tl = last_outside(t, y, fin, thr, tev); r[nm] = 0.0 if tl is None else (tl - tev if tl < t[-1] - 1e-6 else float('inf'))
                    vd, vend = verdict(t, v1, tev)
                    c, T = k.split('_')
                    out.append(f'{c:7s} {T:>4s}  {cp:>4s}  {il:>5s}  {fsm:5s}  {y[mo].min():8.3f} {y[mo].max():9.3f}  {(at(t,y,0.4999)-pre)*1e3:12.1f}  {np.abs(y[m]-pre).max()*1e3:8.1f}  {(fin-pre)*1e3:9.2f}   {fmt_t(r["t10"]):>9s} {fmt_t(r["t1"]):>9s}  {vd}')
    write('padfloat', out)

def case_adc245():
    TS = [11.05e-6, 50e-6, 100e-6, 150e-6, 200e-6, 245e-6]
    out = ['# A4b item 4 (Decision 34: one ADC per channel, T_ACQ ~245 us): C_s = 17 pF behind 1 kOhm, NO reset: C_s keeps the previous sample, +-0.24 V away from the amplifier output (300 Hz full-scale sample-to-sample step at 4 kS/s), amplifier at rest.',
           '# err(T) = v(C_s)(t0 + T) - v(out) before the connect [LSB]; xtalk = err at 245 us referred to the amplifier input [uV] (err x 0.806 mV / 1000).  PROVISIONAL (Decisions 24 and 28 are provisional until D0b).',
           'corner    T   dV_V  ' + ' '.join(f'err@{x*1e6:.0f}us' for x in TS) + '   xtalk@245us_uV']
    for k in ORDER:
        for dv in ('+0.24', '-0.24'):
            lab = f'{k}_dv{dv}'
            if not os.path.exists(f'{RUN}/adc245/{lab}.csv'): continue
            d = load('adc245', lab); t = d['time']
            if t[-1] < 2e-3 + 250e-6: out.append(f'{lab}: INCOMPLETE'); continue
            vf = at(t, d['out'], 2e-3 - 100e-9); e = [(at(t, d['cs'], 2e-3 + x) - vf) / LSB for x in TS]
            c, T = k.split('_')
            out.append(f'{c:7s} {T:>4s}  {dv:>5s}  ' + ' '.join(f'{x:9.3f}' for x in e) + f'   {e[-1]*LSB*1e3:9.3f}')
    write('adc245', out)

if __name__ == '__main__':
    arg = sys.argv[2] if len(sys.argv) > 2 else None
    if sys.argv[1] == 'thd' and arg: case_thd(arg); sys.exit()
    {'thd': case_thd, 'slew': case_slew, 'adc': case_adc, 'adc2': case_adc2, 'adcks': case_adcks, 'fsfix': case_fsfix, 'fsos': case_fsos, 'tgos': case_tgos, 'padfloat': case_padfloat, 'adc245': case_adc245, 'fscharge': case_fscharge, 'recov': case_recov, 'tg': case_tg, 'pwrup': case_pwrup}[sys.argv[1]]()
