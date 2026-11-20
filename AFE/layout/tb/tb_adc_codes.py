#!/usr/bin/env python3
"""tb_adc_codes.py (L1b): static transfer of ONE ADC cell, closed-loop PWL replay of AFE/adc/scripts/x2lib.py (the circuit's own 12 decisions; ideal input source, ideal supply, D3 frame and
STA timing of the corner, second frame at 4 kS/s; common rule 8).  N inputs spread over 1.15-2.15 V (scaled with VDD), default 12 as in F1.
Values: code_offset_lsb   mean of (code - ideal code) for inputs below 2.05 V             (pre-layout -30 / -40 / -22 LSB at typ / ff 85 / ss -40, Decision 43e; restated by L1b, Decision 46d)
        inl_lo_lsb        max |T - mean| below 2.05 V, T = level of the transition tested at trial 12 minus its ideal value (sub-LSB; the DAC and sampling side)        (limit 1 LSB, Decision 43c)
        inl_code_lo_lsb   the same from the codes, less the 0.5 LSB of quantisation (contains the code-dependent comparator threshold, Decision 43b)
        top_2v10_lsb, top_2v15_lsb   T - mean(T below 2.05 V) at the two highest inputs (top-of-range plate error, accepted: +1.2 / +2.1 LSB typ, +3.4 / +4.4 LSB ff 85, Decision 43c)
        gain_err_pct, alpha (plate attenuation: falls if the layout adds capacitance on the DAC top plate), theta_lsb (comparator threshold on the plate), unresolved (metastable decisions), failed
        first_conv_dlsb   T of the first conversion after the operating point minus the second (Decision 43d: the host discards it)
usage: python3 AFE/layout/tb/tb_adc_codes.py [--netlist schematic|<adc_ch PEX>] [--corner typ|ff85|ss-40|ff-40|ss125|all] [--n 12] [--out DIR]"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lptb import *
import numpy as np


def run(netlist, corner, a, log):
    d = adc_env(netlist)
    sys.path.insert(0, os.path.join(ADC, 'scripts'))
    import x2lib as X, x2_adc as A
    vdd = X.COR[corner][2]
    n = int(a.n)
    k = vdd / 3.3
    vins = list((1.15 + (np.arange(n - 2) + 0.37) / (n - 2) * 0.90 + 0.000217 * np.sin(np.arange(n - 2) * 1.7)) * k) + [2.10 * k, 2.15 * k]
    cal, rows, exps = A.static(corner, vins, 'cref', 500e-9, log=log, tag='lp_codes_%s' % corner)
    if len(rows) < n - 1:
        raise TbError('%d of %d conversions failed' % (n - len(rows), n))
    r = np.array([(q[0], q[1], q[2], q[3]) for q in rows])
    v, c, ci, t = r.T
    lo = v < 2.05 * k
    tm = t[lo].mean()
    ec = c + 0.5 - v / cal.lsb
    p = np.polyfit(v[lo] - vdd / 2, t[lo], 1)
    r0 = {q[0]: q[3] for q in A.static.rows0}
    for q in rows:
        log('ADC %s vin %.6f code %d ideal %d diff %+d | T %+.3f LSB | passes %d unresolved %d' % (corner, q[0], q[1], q[2], q[1] - q[2], q[3], q[5], q[6]))
    top = lambda x: float(t[np.argmin(np.abs(v - x * k))] - tm)
    return ({'code_offset_lsb': float(np.mean((c - ci)[lo])), 't_offset_lsb': float(tm), 'inl_lo_lsb': float(np.abs(t[lo] - tm).max()), 'inl_code_lo_lsb': float(max(0.0, np.abs(ec[lo] - ec[lo].mean()).max() - 0.5)),
             'top_2v10_lsb': top(2.10), 'top_2v15_lsb': top(2.15), 'gain_err_pct': float(-p[0] * cal.lsb * 100), 'alpha': float(cal.alpha), 'theta_lsb': float(cal.theta / cal.lsb),
             'unresolved': float(sum(q[6] for q in rows)), 'failed': float(n - len(rows)), 'first_conv_dlsb': float(np.mean([r0[q[0]] - q[3] for q in rows if q[0] in r0 and q[0] < 2.05 * k])), 'n_inputs': float(n)},
            {'predictor': cal.fitinfo[:300], 'warnings': d.warnings if d else []})


if __name__ == '__main__':
    sys.exit(cli('adc_codes', __doc__, ('typ', 'ff85', 'ss-40', 'ff-40', 'ss125'), run, lambda ap: ap.add_argument('--n', default='12')))
