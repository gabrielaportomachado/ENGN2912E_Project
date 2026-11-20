#!/usr/bin/env python3
"""tb_adc_overlap.py (L1b item g): one ADC cell with the driver-gate OVERLAP that the gate-level timing shows (PMOS and NMOS gate of one bit both on for up to 0.21 ns,
AFE/review/sim/tb_audit_summary.log, audit m3) instead of the 0.3 ns break-before-make of the D2-X2 testbenches.  Six inputs, closed-loop replay, nominal and with the overlap.
Values: dt_max_lsb = largest change of the transition level T over the inputs, dcode_max = largest code change, t_offset_nom_lsb, t_offset_ovl_lsb.   (expected: a few 0.01 LSB)
usage: python3 AFE/layout/tb/tb_adc_overlap.py [--netlist schematic|<adc_ch PEX>] [--corner typ|ff-40|all] [--overlap 0.21e-9] [--out DIR]"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lptb import *
import numpy as np


def run(netlist, corner, a, log):
    d = adc_env(netlist)
    sys.path.insert(0, os.path.join(ADC, 'scripts'))
    import x2lib as X, x2_adc as A
    vdd = X.COR[corner][2]
    lsb = vdd / 4096
    vins = [1.15 * vdd / 3.3, (1536 + 0.3) * lsb, (2048 + 0.3) * lsb, 1.9 * vdd / 3.3, (2560 + 0.3) * lsb, 2.0 * vdd / 3.3]
    nov, nov1 = X.NOV, X.NOV1
    try:
        cal, r0, _ = A.static(corner, vins, log=lambda s: None, tag='lp_ovl0_%s' % corner)
        X.NOV = X.NOV1 = -float(a.overlap)
        cal2, r1, _ = A.static(corner, vins, log=lambda s: None, tag='lp_ovl1_%s' % corner)
    finally:
        X.NOV, X.NOV1 = nov, nov1
    m0, m1 = {q[0]: q for q in r0}, {q[0]: q for q in r1}
    both = [x for x in m0 if x in m1]
    if len(both) < 4:
        raise TbError('only %d of %d inputs converged in both runs' % (len(both), len(vins)))
    dt = [m1[x][3] - m0[x][3] for x in both]
    dc = [m1[x][1] - m0[x][1] for x in both]
    for x in both:
        log('OVERLAP %s Vin %.5f: code %d -> %d, T %+.3f -> %+.3f LSB' % (corner, x, m0[x][1], m1[x][1], m0[x][3], m1[x][3]))
    return ({'dt_max_lsb': float(np.abs(dt).max()), 'dcode_max': float(np.abs(dc).max()), 't_offset_nom_lsb': float(np.mean([m0[x][3] for x in both])), 't_offset_ovl_lsb': float(np.mean([m1[x][3] for x in both])),
             'overlap_ns': float(a.overlap) * 1e9, 'n': float(len(both))}, {'warnings': d.warnings if d else []})


if __name__ == '__main__':
    sys.exit(cli('adc_overlap', __doc__, ('typ', 'ff-40'), run, lambda ap: ap.add_argument('--overlap', default='0.21e-9')))
