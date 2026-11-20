#!/usr/bin/env python3
"""tb_amp_thd.py (L2b): large-signal transient of the amplifier channel: differential electrode sine of +-0.5 mV at 12.25 Hz (output +-0.5 V around 1.65 V, the whole 1.15-2.15 V range).
Values: thd_pct (harmonics 2-9 / fundamental, least-squares fit over the last 4 periods of 16, with a linear drift term, as AFE/amp/scripts/a4c_lib.py), out_max_v, out_min_v,
gain_db (fundamental / 0.5 mV), hd2_dbc, hd3_dbc.  Pre-layout (AFE/amp/sim/a4c_thd.log): 0.040 / 2.527 / 0.051 %, 1.148-2.154 V typ, bottom 1.220 V at ff 85 C (accepted, Decision 28).
usage: python3 AFE/layout/tb/tb_amp_thd.py [--netlist schematic|<amp_ch PEX>] [--corner typ|ff85|ss-40|all] [--junction] [--amp 0.5m] [--out DIR]"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'amp', 'scripts'))
from lptb import *
import numpy as np
from a4c_lib import harmonics

F = 12.25


def run(netlist, corner, a, log):
    dut = amp_dut(netlist, a.prdiff)
    ns = 'native' if not (dut.pex or dut.prdiff) else settle(corner, dut, log)
    amp = float(a.amp)
    d = os.path.join(SCRATCH, 'tb', 'amp_thd')
    os.makedirs(d, exist_ok=True)
    f = os.path.join(d, 'thd_%s_%s.dat' % (dut.tag, corner))
    tstop = 16.0 / F                  # 1.3 s: the start transient of the 0.2 Hz high-pass (the sine starts at its zero crossing) has decayed over the fitted periods
    L = amp_bench(corner, dut, 'THD +-%g V at %g Hz' % (amp, F), vd='Vd vd 0 SIN(0 %g %g 0)' % (amp, F), nodeset=ns, opts='abstol=1e-12 chgtol=1e-17')
    L += ['.control', 'save v(out)', 'tran 20u %g 0 100u' % tstop, 'wrdata %s v(out)' % f, 'echo DONE', 'quit', '.endc', '.end']
    r = list(run_ng([('thd_%s_%s' % (dut.tag, corner), '\n'.join(L) + '\n')], 'amp_thd', retry=lambda n, t: t.replace(' 0 100u', ' 0 70u'), log=log).values())[0]
    if 'DONE' not in r['out']:
        raise TbError('transient did not finish: ' + (r['abort'] or r['out'][-300:]))
    t, (y,) = read_wr(f)
    a1, thd, mean, h = harmonics(t, y, F, 4, nh=9, tend=t[-1])
    sel = t > t[-1] - 4.0 / F
    return {'thd_pct': 100 * thd, 'out_max_v': float(y[sel].max()), 'out_min_v': float(y[sel].min()), 'gain_db': 20 * np.log10(a1 / amp), 'hd2_dbc': 20 * np.log10(h[2] / h[1]), 'hd3_dbc': 20 * np.log10(h[3] / h[1]),
            'out_mean_v': float(mean)}, {'warnings': dut.warnings}


if __name__ == '__main__':
    sys.exit(cli('amp_thd', __doc__, AMP_CORNERS, run, lambda ap: ap.add_argument('--amp', default='0.5e-3', help='differential electrode amplitude, V peak')))
