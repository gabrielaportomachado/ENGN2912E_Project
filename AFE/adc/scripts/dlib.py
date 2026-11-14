"""D1 helpers: read ngspice wrdata CSV (time,value pairs per vector), per-cycle decision / delay / energy extraction."""
import numpy as np
def load(path, names):
    a = np.loadtxt(path); t = a[:, 0]
    return t, {n: a[:, 1 + 2 * i] for i, n in enumerate(names)}
def cross(t, v, level, rising=True, t0=0.0, t1=1e9):
    """first time in [t0,t1] where v crosses level (linear interpolation); None if none."""
    m = (t >= t0) & (t <= t1); tt = t[m]; vv = v[m]
    s = (vv[:-1] - level) * (vv[1:] - level) <= 0
    for i in np.nonzero(s)[0]:
        if (vv[i + 1] > vv[i]) == rising and vv[i + 1] != vv[i]:
            return tt[i] + (level - vv[i]) / (vv[i + 1] - vv[i]) * (tt[i + 1] - tt[i])
    return None
def cycles(t, d, tcyc, t0, n, vdd=3.3, clk_name='clk'):
    """per-cycle: decision (1/-1/0 if not resolved), delay clk-rise(50%) -> |outp-outn| > vdd/2 [s], charge from supply over the cycle -> energy [J]."""
    out = []
    for k in range(n):
        ts = t0 + k * tcyc; te = ts + tcyc
        m = (t >= ts) & (t < te)
        dv = d['outp'][m] - d['outn'][m]
        dec = 0
        tdel = None
        idx = np.nonzero(np.abs(dv) > vdd / 2)[0]
        if len(idx):
            dec = 1 if dv[idx[0]] > 0 else -1
            tdel = t[m][idx[0]] - ts
        q = -np.trapezoid(d['i_vdd'][m], t[m]) if 'i_vdd' in d else float('nan')
        out.append((dec, tdel, q * vdd))
    return out
