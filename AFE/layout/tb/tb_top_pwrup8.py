#!/usr/bin/env python3
"""tb_top_pwrup8.py (L3b item 5; audit R10): ALL N amplifier channels (N = --nch, default 4 = the chip; 8 = the n8 baseline; layout cell amp_ch each: amplifier + one-shot + OR2) on the ONE bias cell.  The file name keeps "8" (REVIEW R16).  VDD ramps 0 -> VDD in 1 ms from the
all-zero state (record switches open, every rec node parked), the host waits T_WAIT (5 s at ss -40 C: the 8-channel bias start-up of Decision 44c, NOT re-derived for 4 channels - the 4-channel bias has less load; SPI_FRAME.md says up to 3.6 s), sets RST_AMP for 100 ms on all channels
together, releases it.  Each channel has its own electrode pair network on the shared tissue node and the shared REF electrode; electrode DC offsets over the channels: N = 8: 0, +-1, +-3, +-10, 0 mV; N = 4: 0, -3, +10, -10 mV (both signs of the largest offset kept).
Values: err_max_mv (largest |output - 1.65 V| over the 8 channels 1 s after the release; limit 10 mV), err_100ms_max_mv, vrs_dip_mv (largest dip of the shared reset level while the 8 channels
reset together; ESTIMATE of the audit about 12 mV), vrs_end_v, latched_before (channels more than 0.2 V from mid-scale before the reset: the power-up latch), t_wait_s.
--netlist / --amp: schematic or the amp_ch PEX; --bias: schematic or the bias_genc PEX.  Values latched_before = N: every channel latched before the reset (expected, A4c).
usage: python3 AFE/layout/tb/tb_top_pwrup8.py [--netlist schematic|<amp_ch PEX>] [--bias schematic|<bias_genc PEX>] [--corner typ|ff85|ss-40|all] [--junction] [--nch 4] [--out DIR]"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lptb import *
import numpy as np

TW = {'typ': 0.3, 'ff85': 0.3, 'ss-40': 5.0}
OFFS_BY_N = {8: [0.0, 1e-3, -1e-3, 3e-3, -3e-3, 10e-3, -10e-3, 0.0], 4: [0.0, -3e-3, 10e-3, -10e-3]}


def run(netlist, corner, a, log):
    n = N_CH['n']
    if n not in OFFS_BY_N:
        raise TbError('electrode offsets for N = %d are not defined (OFFS_BY_N)' % n)
    OFFS = OFFS_BY_N[n]
    dut = ampch_dut(netlist, a.prdiff)
    bd = bias_dut(a.bias)
    c, T, vs = CORNERS[corner]
    tw = TW.get(corner, 5.0)
    t1, t2 = tw, tw + 0.1
    tstop = t2 + 1.0
    d = os.path.join(SCRATCH, 'tb', 'top_pwrup8')
    os.makedirs(d, exist_ok=True)
    f = os.path.join(d, 'p8_%s_%s.dat' % (dut.tag, corner))
    L = ['* LP golden testbench: %d channels on one bias cell, power-up + common RST_AMP [%s]' % (n, corner)] + ampch_includes(corner, dut)
    if bd.pex:
        L = [x for x in L if not x.endswith('/bias_genc.spice')] + bd.wrapper()
    L += ['.options gmin=1e-16 abstol=1e-12 chgtol=1e-17 reltol=1e-4 itl1=500 itl4=500', '.temp %g' % T, '.param VSUP=%g LOOPTEST=0' % vs, 'Vdd vdd 0 PWL(0 0 1m {VSUP})',
          'Xbias vbn vcm vg1 vcmo vg2 vrs vdd 0 bias_genc', 'Vrst rst_amp 0 PWL(0 0 %g 0 %g {VSUP} %g {VSUP} %g 0)' % (t1, t1 + 1e-6, t2, t2 + 1e-6), 'Vsw sw_rec 0 0', 'Vswb sw_rec_b 0 PWL(0 0 1m {VSUP})',
          'Vtis tis 0 1.65', 'Rsr tis er 1k', 'Cdlr er ref 300n', 'Rctr er ref 50k']
    for i in range(n):
        L += ['Vos%d os%d tis %g' % (i, i, OFFS[i]), 'Rs%d os%d e%d 1k' % (i, i, i), 'Cdl%d e%d rec%d 300n' % (i, i, i), 'Rct%d e%d rec%d 50k' % (i, i, i),
              'Xch%d ref sw_rec sw_rec_b rst_amp vbn vcm vg1 vcmo vg2 vrs rec%d out%d vdd 0 amp_ch_tb' % (i, i, i), 'Cl%d out%d 0 20f' % (i, i)]
    sv = ' '.join('v(out%d)' % i for i in range(n)) + ' v(vrs) v(vbn)'
    L += ['.control', 'save ' + sv, 'tran 1m %g 0 1m uic' % tstop, 'wrdata %s %s' % (f, sv), 'echo DONE', 'quit', '.endc', '.end']
    r = list(run_ng([('p8_%s_%s' % (dut.tag, corner), '\n'.join(L) + '\n')], 'top_pwrup8', retry=lambda n, t: t.replace('tran 1m ', 'tran 0.7m ').replace(' 0 1m uic', ' 0 0.7m uic'), log=log).values())[0]
    if 'DONE' not in r['out']:
        raise TbError('transient did not finish: ' + (r['abort'] or r['out'][-300:]))
    t, cols = read_wr(f)
    outs, vrs = cols[:n], cols[n]
    at = lambda y, x: float(np.interp(x, t, y))
    pre = float(np.mean(vrs[(t > t1 - 0.05) & (t < t1 - 0.001)]))
    during = vrs[(t >= t1) & (t <= t2)]
    return ({'t_wait_s': tw, 'err_max_mv': max(abs(at(o, t2 + 1.0) - 1.65) for o in outs) * 1e3, 'err_100ms_max_mv': max(abs(at(o, t2 + 0.1) - 1.65) for o in outs) * 1e3,
             'vrs_dip_mv': float(np.abs(during - pre).max() * 1e3), 'vrs_end_v': float(vrs[-1]), 'latched_before': float(sum(1 for o in outs if abs(at(o, t1 - 1e-3) - 1.65) > 0.2))},
            {'amp': netlist, 'bias': a.bias, 'offsets_mv': [x * 1e3 for x in OFFS], 'warnings': dut.warnings + bd.warnings})


if __name__ == '__main__':
    sys.exit(cli('top_pwrup8', __doc__, AMP_CORNERS, run, lambda ap: (ap.add_argument('--bias', default='schematic'), add_nch(ap))))
