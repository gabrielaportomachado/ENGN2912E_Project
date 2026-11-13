"""A4c analysis: python3 a4c_analyze.py <case>   reads /tmp/a4crun/<case>/*.csv, writes sim/a4c_<case>.log.
Cases: rec (offset step + reset pulse recovery).  Label format <corner>_<T>_os<mV>_w<ms>[...]; parameters are read from the saved .log of each run (the ngspice command line is not kept) -> pass via labels."""
import sys, glob, re, os, numpy as np
sys.path.insert(0, os.path.dirname(__file__)); import a4c_lib as L
AMP = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))

def tval(s):
    m = re.match(r'([0-9.]+)([munp]?)$', s); return float(m.group(1)) * {'': 1, 'm': 1e-3, 'u': 1e-6, 'n': 1e-9, 'p': 1e-12}[m.group(2)]

def first_settle(t, y, ref, lim, t0):
    """first time after t0 from which |y-ref| < lim for the rest of the record"""
    m = t >= t0; tt = t[m]; bad = np.abs(y[m] - ref) >= lim
    if not bad.any(): return tt[0] - t0
    i = np.where(bad)[0][-1]
    return (tt[i + 1] - t0) if i + 1 < len(tt) else float('nan')

def rec(case='rec'):
    out = []
    for f in sorted(glob.glob('/tmp/a4crun/%s/*.csv' % case)):
        lab = os.path.basename(f)[:-4]; d = L.load(f); t = d['time']
        p = dict(re.findall(r'_(os|w|t0|os0)([0-9.]+[munp]?)', lab))
        os_ = tval(p['os']) if 'os' in p else 0.0
        w = tval(p['w']) if 'w' in p else 0.0
        T0 = float(os.environ.get('T0', 0.1)); TOS = float(os.environ.get('TOS', 0.1))
        rest = np.interp(T0 - 1e-3, t, d['out']); y = d['out']
        toff = float(os.environ.get('FSON', T0 - 1e-5)) + w
        pre = np.interp(toff - 20e-6, t, y); post = np.interp(toff + 20e-6, t, y)
        v1pre = np.interp(toff - 20e-6, t, d['v1']); v1post = np.interp(toff + 20e-6, t, d['v1'])
        endv = np.mean(y[t > t[-1] - 1.0]) if t[-1] > 3 else y[-1]
        mk = t > toff
        ts1 = first_settle(t, y, endv, 1e-3, toff); ts10 = first_settle(t, y, endv, 10e-3, toff)
        pk = np.max(np.abs(y[mk] - endv)) * 1e3
        out.append('%-34s os %6.1f mV pulse %7.3f ms | at pulse end: out-rest %8.3f mV v1-rest %8.3f mV | release step out %7.3f mV v1 %7.3f mV | out-rest at +1ms %8.3f +10ms %8.3f +100ms %8.3f mV | final(end) %8.3f mV | within 10 mV %8.3f s, 1 mV %8.3f s after release, peak|out-final| %8.1f mV' % (
            lab, os_ * 1e3, w * 1e3, 1e3 * (pre - rest), 1e3 * (v1pre - np.interp(T0 - 1e-3, t, d['v1'])), 1e3 * (post - pre), 1e3 * (v1post - v1pre),
            1e3 * (np.interp(toff + 1e-3, t, y) - rest), 1e3 * (np.interp(toff + 1e-2, t, y) - rest), 1e3 * (np.interp(toff + 0.1, t, y) - rest), 1e3 * (endv - rest), ts10, ts1, pk))
    return out

def _main():
    case = sys.argv[1]; lines = tg(case) if case.startswith('tg') or case in ('leak', 'inj') else thd(case) if case == 'thd' else pu(case) if case in ('pu', 'pur') else rec(case)
    open('%s/sim/a4c_%s.log' % (AMP, case), 'w').write('\n'.join(lines) + '\n'); print('\n'.join(lines))

def tg(case='tg'):
    """TGATE + park scenarios.  Timeline: init reset 1..31 ms, TG open+park 0.2 s, offset step 0.3 s, TG close 0.5 s (reset pulse from the close), record to the end of the run."""
    out = []
    for f in sorted(glob.glob('/tmp/a4crun/%s/*.csv' % case)):
        lab = os.path.basename(f)[:-4]; d = L.load(f); t = d['time']; y = d['out']; v1 = d['v1']; vn = d['vn1']
        if t[-1] < 0.9 * float(os.environ.get('TEND', 30)):
            out.append('%-40s INCOMPLETE: .tran aborted at t = %.6g s ("timestep too small")' % (lab, t[-1])); continue
        def at(x, tt): return float(np.interp(tt, t, x))
        rest = at(y, 0.15); r1 = at(v1, 0.15); rn = at(vn, 0.15)
        m = (t > 0.2) & (t < 0.5)
        endv = np.mean(y[t > t[-1] - 1.0]) if t[-1] > 3 else y[-1]
        mk = t > 0.5
        ts1 = first_settle(t, y, endv, 1e-3, 0.5); ts10 = first_settle(t, y, endv, 10e-3, 0.5)
        out.append('%-40s pre-open |out-rest| max %7.3f mV | open phase: v1-rest min/max %8.2f / %8.2f mV, vn1-rest max|.| %8.3f mV, out-rest min/max %9.2f / %9.2f mV (rail check: v1 in [%.2f, %.2f] V) | close: out-rest at +10ms %8.3f +100ms %8.3f +1s %8.3f mV | final(mean last s) %8.3f mV | within 10 mV %7.3f s, 1 mV %7.3f s after close | peak|out-final| after 0.52 s %8.1f mV' % (
            lab, 1e3 * np.max(np.abs(y[(t > 0.05) & (t < 0.2)] - rest)), 1e3 * (v1[m].min() - r1), 1e3 * (v1[m].max() - r1), 1e3 * np.max(np.abs(vn[m] - rn)), 1e3 * (y[m].min() - rest), 1e3 * (y[m].max() - rest), v1[m].min(), v1[m].max(),
            1e3 * (at(y, 0.51) - rest), 1e3 * (at(y, 0.6) - rest), 1e3 * (at(y, 1.5) - rest), 1e3 * (endv - rest), ts10, ts1, 1e3 * np.max(np.abs(y[t > 0.52] - endv))))
    return out



def thd(case='thd'):
    out = []
    for f in sorted(glob.glob('/tmp/a4crun/%s/*.csv' % case)):
        lab = os.path.basename(f)[:-4]; d = L.load(f); t = d['time']
        fr = 12.25; vd = tval(re.search(r'_f12_([0-9.]+[mu]?)', lab).group(1))
        a1, th, mean, h = L.harmonics(t, d['out'], fr, 4)
        m = t > t[-1] - 4 / fr
        out.append('%-24s VD %.2f mV pk: gain %.3f dB  THD %.3f %%  mean-1.65 %.1f mV  out max %.3f min %.3f V  o2 max %.3f min %.3f V' % (lab, vd * 1e3, 20 * np.log10(a1 / vd), th * 100, (mean - 1.65) * 1e3, d['out'][m].max(), d['out'][m].min(), d['o2'][m].max(), d['o2'][m].min()))
    return out


def pu(case='pu'):
    out = []
    for f in sorted(glob.glob('/tmp/a4crun/%s/*.csv' % case)):
        lab = os.path.basename(f)[:-4]; d = L.load(f); t = d['time']; y = d['out']
        tg_ = 'tgpark' in lab; t0 = 0.5 if tg_ else 0.0
        mw = re.search(r'_w([0-9.]+[munp]?)$', lab)
        if case == 'pur' and mw: t0 = 3.0 + tval(mw.group(1))
        out.append('%-34s final out %.4f V (err %.2f mV) | within 10 mV of 1.65 V after %8.3f s, 1 mV after %8.3f s (from %s) | supply I at end %.1f uA, I(vbn master) %.3f uA | out min/max %.3f / %.3f V' % (
            lab, y[-1], 1e3 * (y[-1] - 1.65), first_settle(t, y, 1.65, 10e-3, t0), first_settle(t, y, 1.65, 1e-3, t0), 'close of the routing switch at 0.5 s' if tg_ else ('the end of the reset pulse (3 s + W)' if case == 'pur' else 't = 0'),
            1e6 * np.mean(d['isup'][t > t[-1] - 1]), 1e6 * np.mean(d['idm'][t > t[-1] - 1]), y[t > 0.01].min(), y[t > 0.01].max()))
    return out


if __name__ == '__main__':
    _main()
