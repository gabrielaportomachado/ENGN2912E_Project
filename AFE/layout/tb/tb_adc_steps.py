#!/usr/bin/env python3
"""tb_adc_steps.py (L1b): size of the transfer step at code boundaries of ONE ADC cell (closed-loop replay, the method of AFE/adc/scripts/x2_inl_step.py): 2 x 8 inputs on a 5-code pitch just
below and just above boundary B; e = code + 0.5 - Vin/LSB; step = mean(e | code >= B) - mean(e | code < B), 0 for a linear converter (+-0.15 LSB of quantisation scatter).
Boundaries: 1536 and 2048 = the code-dependent comparator threshold of Decision 43b (pre-layout -1.1 / +1.3 LSB typ, -1.1 / +1.55 LSB ff 85; with the 54.5 fF MIM preamp capacitors of the
            layout +0.80 LSB at 2048 typ, F1);  2048 also carries the MSB-trial settling;
            2112 = a roll-over of the 6-bit LSB array: the bridge capacitor and the parasitic of the bridge node show here (Decision 40a; 0.018 LSB per fF, D2).
Values: step_<B>_lsb, offset_<B>_lsb (mean e), n_<B> (conversions used).
usage: python3 AFE/layout/tb/tb_adc_steps.py [--netlist schematic|<adc_ch PEX>] [--corner typ|ff85|ss-40|all] [--b 1536,2048,2112] [--out DIR]"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lptb import *
import numpy as np

OFF = {'typ': 30.3, 'ff85': 40.5, 'ss-40': 22.1, 'ff-40': 30.0, 'ss125': 25.0}        # code offset used only to place the inputs (X2 S1)


def run(netlist, corner, a, log):
    d = adc_env(netlist)
    sys.path.insert(0, os.path.join(ADC, 'scripts'))
    import x2lib as X, x2_adc as A
    lsb = X.COR[corner][2] / 4096
    v = {}
    NP = 8
    k = np.arange(-NP, NP)
    for B in [int(x) for x in a.b.split(',')]:
        vins = list((B + OFF.get(corner, 30.0) + 5 * k + 2.5 + 0.31 * np.sin(1.3 * k)) * lsb)
        cal, rows, _ = A.static(corner, vins, log=lambda s: None, tag='lp_step_%s_%d' % (corner, B))
        if len(rows) < 2 * NP - 2:
            raise TbError('boundary %d: %d of %d conversions failed' % (B, 2 * NP - len(rows), 2 * NP))
        r = np.array([(q[0], q[1]) for q in rows])
        vv, c = r[:, 0], r[:, 1]
        e = c + 0.5 - vv / lsb
        lo = c < B
        if lo.sum() < 3 or (~lo).sum() < 3:
            raise TbError('boundary %d: the inputs do not straddle it (codes %d..%d): the code offset moved by more than 30 LSB' % (B, c.min(), c.max()))
        v['step_%d_lsb' % B] = float(e[~lo].mean() - e[lo].mean())
        v['offset_%d_lsb' % B] = float(e.mean())
        v['n_%d' % B] = float(len(rows))
        log('STEP %s boundary %d: %d below (%d..%d), %d above (%d..%d): e below %+.2f, above %+.2f -> step %+.2f LSB' % (corner, B, lo.sum(), c[lo].min(), c[lo].max(), (~lo).sum(), c[~lo].min(), c[~lo].max(),
                                                                                                                     e[lo].mean(), e[~lo].mean(), v['step_%d_lsb' % B]))
    return v, {'warnings': d.warnings if d else []}


if __name__ == '__main__':
    sys.exit(cli('adc_steps', __doc__, ('typ', 'ff85', 'ss-40'), run, lambda ap: ap.add_argument('--b', default='1536,2048,2112')))
