#!/usr/bin/env python3
"""Analyse amp_out.txt (time v(out) v(rec) v(vcmo)) from tb_amp.spice: gain at the test tone, output DC, residual.

    python3 analyze_amp.py amp_out.txt amp_info.json [--t-meas 12e-3]

Fits  out = A sin(wt) + B cos(wt) + c + d*t  on t > t-meas (the d*t term absorbs a slow settling drift) and reports
gain = A_out / A_in in dB (design target 60 dB), the output DC level (design: ~1.65 V) and the rms of the fit residual.
PASS = gain within +-3 dB of 60 dB and DC within 0.3 V of 1.65 V (loose first-run limits, tighten them once real numbers are in).
"""
import argparse
import json
import sys

import numpy as np


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("out_txt")
    ap.add_argument("info_json")
    ap.add_argument("--t-meas", type=float, default=None, help="start of the measurement window (default t_rec + 11 ms)")
    a = ap.parse_args(argv)
    info = json.load(open(a.info_json))
    d = np.loadtxt(a.out_txt, skiprows=1)
    t, vout = d[:, 0], d[:, 1]
    t0 = a.t_meas if a.t_meas is not None else info["t_rec"] + 11e-3
    m = t > t0
    if m.sum() < 50:
        sys.exit(f"only {m.sum()} points after {t0 * 1e3:.1f} ms; lower --t-meas or raise --tstop")
    f = info["tone_hz"]
    tt = t[m]
    A = np.c_[np.sin(2 * np.pi * f * tt), np.cos(2 * np.pi * f * tt), np.ones_like(tt), tt - tt[0]]
    c, *_ = np.linalg.lstsq(A, vout[m], rcond=None)
    amp = float(np.hypot(c[0], c[1]))
    res = vout[m] - A @ c
    gain = amp / info["tone_amp"]
    gdb = 20 * np.log10(gain)
    cycles = (tt[-1] - tt[0]) * f
    print(f"window {t0 * 1e3:.1f}-{t[-1] * 1e3:.1f} ms ({cycles:.1f} cycles of {f:g} Hz), {m.sum()} points")
    print(f"output: {amp * 1e3:.1f} mV pk for {info['tone_amp'] * 1e3:.3f} mV in -> gain {gain:.0f} V/V = {gdb:.1f} dB (target 60 dB)")
    print(f"output DC {c[2]:.3f} V (drift {c[3] * 1e3:.2f} mV/s), fit residual {res.std() * 1e3:.2f} mV rms")
    ok = abs(gdb - 60) < 3 and abs(c[2] - 1.65) < 0.3
    print("RESULT:", "PASS" if ok else "CHECK (outside the loose limits)")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())