"""A4c (a4b_lib + vrs, gm1, gm2 columns) analysis helpers: read ngspice wrdata CSV (wr_singlescale + wr_vecnames), resample, THD by least squares."""
import numpy as np

COLS = ["time","out","v1","vn1","vn2","o2","rec","vbn","isup","cs","idm","idb1","fs","vrs","gm1","gm2"]


def load(path):
    d = np.loadtxt(path, skiprows=1)
    return {c: d[:, i] for i, c in enumerate(COLS[:d.shape[1]])}


def resample(t, y, t0, t1, n):
    tu = np.linspace(t0, t1, n, endpoint=False)
    return tu, np.interp(tu, t, y)


def harmonics(t, y, f, nper, nh=9, tend=None, ppc=400):
    """least-squares fit y = c0 + c1 (t-tm) + sum_k a_k cos + b_k sin over the last nper periods ending at tend.
    returns (amp1, thd_frac, mean, dict of harmonic amplitudes)."""
    if tend is None:
        tend = t[-1]
    T = 1.0 / f
    t0 = tend - nper * T
    tu, yu = resample(t, y, t0, tend, int(nper * ppc))
    tm = 0.5 * (t0 + tend)
    cols = [np.ones_like(tu), tu - tm]
    for k in range(1, nh + 1):
        cols += [np.cos(2 * np.pi * k * f * (tu - t0)), np.sin(2 * np.pi * k * f * (tu - t0))]
    A = np.array(cols).T
    c, *_ = np.linalg.lstsq(A, yu, rcond=None)
    amps = [np.hypot(c[2 + 2 * (k - 1)], c[3 + 2 * (k - 1)]) for k in range(1, nh + 1)]
    thd = np.sqrt(sum(a * a for a in amps[1:])) / amps[0]
    return amps[0], thd, c[0], {k + 1: amps[k] for k in range(nh)}
