#!/usr/bin/env python3
"""tb_amp_ac.py (L2b): amplifier channel operating point + small-signal response.  Bench = AFE/amp/tb/tb_a4c_ac.spice (real bias cell, Randles electrode pair, reset off, park off, 20 fF load).
Values: idd_ua (supply current of bias_genc + one channel), vout_v, the six bias taps, g_mid_db (12.25 Hz), g_pk_db, f_lo_hz / f_hi_hz (-3 dB from the peak, as tb_a4c_ac), g_300_db, g_0p5_db,
g1_mid_db (stage 1 alone, if the node v1 is known), and hf_<f> = gain at 1 k .. 1 MHz relative to g_mid: the port-level stand-in for the loop phase margin on an extracted netlist
(compare.py reports the largest change of the hf_ values; tb_amp_loop.py calibrates what 1 dB of change means in degrees).
usage: python3 AFE/layout/tb/tb_amp_ac.py [--netlist schematic|<amp_ch PEX>] [--corner typ|ff85|ss-40|all] [--settle] [--out DIR]"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lptb import *
import numpy as np

HF = [1e3, 3e3, 1e4, 3e4, 1e5, 3e5, 1e6]


def xing(f, g, level, rising):
    idx = np.where((g[:-1] < level) & (g[1:] >= level))[0] if rising else np.where((g[:-1] >= level) & (g[1:] < level))[0]
    if len(idx) == 0:
        return float('nan')
    i = idx[0]
    x = (level - g[i]) / (g[i + 1] - g[i])
    return float(10 ** (np.log10(f[i]) + x * (np.log10(f[i + 1]) - np.log10(f[i]))))


def run(netlist, corner, a, log):
    dut = amp_dut(netlist, a.prdiff)
    for w in dut.warnings:
        log('WARNING ' + w)
    use_settle = dut.pex or a.settle or dut.prdiff
    ns = settle(corner, dut, log) if use_settle else 'native'
    d = os.path.join(SCRATCH, 'tb', 'amp_ac')
    os.makedirs(d, exist_ok=True)
    f = os.path.join(d, 'ac_%s_%s' % (dut.tag, corner))
    tl, tp = dut.taps(['v1'])
    v1 = tp.get('v1')
    L = amp_bench(corner, dut, 'op + ac', nodeset=ns, extra=tl)
    L += ['.control', 'op', 'echo RESULT idd=$&i(Vdd) vout=$&v(out) vbn=$&v(vbn) vcm=$&v(vcm) vg1=$&v(vg1) vcmo=$&v(vcmo) vg2=$&v(vg2) vrs=$&v(vrs)' + (' v1=$&v(%s)' % v1 if v1 else ''),
          'ac dec 100 1e-3 1e7', 'wrdata %s.dat vdb(out)%s' % (f, (' vdb(%s)' % v1) if v1 else ''), 'echo DONE', 'quit', '.endc', '.end']
    r = list(run_ng([('ac_%s_%s' % (dut.tag, corner), '\n'.join(L) + '\n')], 'amp_ac', log=log).values())[0]
    if 'DONE' not in r['out'] or not os.path.exists(f + '.dat'):
        raise TbError('op / ac did not run: ' + (r['abort'] or r['out'][-300:]))
    o = results(r['out'])[0]
    dat = np.loadtxt(f + '.dat')
    fr, g = dat[:, 0], dat[:, 1]
    gm = float(np.interp(np.log10(12.25), np.log10(fr), g))
    gp = float(g.max())
    ip = int(g.argmax())
    v = {'idd_ua': -o['idd'] * 1e6, 'vout_v': o['vout'], 'vbn_v': o['vbn'], 'vcm_v': o['vcm'], 'vg1_v': o['vg1'], 'vcmo_v': o['vcmo'], 'vg2_v': o['vg2'], 'vrs_v': o['vrs'],
         'g_mid_db': gm, 'g_pk_db': gp, 'f_lo_hz': xing(fr[:ip + 1], g[:ip + 1], gp - 3, True), 'f_hi_hz': xing(fr[ip:], g[ip:], gp - 3, False),
         'g_300_db': float(np.interp(np.log10(300), np.log10(fr), g)), 'g_0p5_db': float(np.interp(np.log10(0.5), np.log10(fr), g))}
    if v1:
        v['v1_v'] = o['v1']
        v['g1_mid_db'] = float(np.interp(np.log10(12.25), np.log10(fr), dat[:, 3]))
    for x in HF:
        v['hf_%s' % ('%gk' % (x / 1e3) if x < 1e6 else '1M')] = float(np.interp(np.log10(x), np.log10(fr), g)) - gm
    return v, {'operating_point': 'power-up sequence + wrnodev' if use_settle else 'node guesses of tb_a4c_ac.spice', 'probes': dut.probes if dut.pex else 'simulation names', 'warnings': dut.warnings}


if __name__ == '__main__':
    sys.exit(cli('amp_ac', __doc__, AMP_CORNERS, run, lambda ap: ap.add_argument('--settle', action='store_true', help='schematic: use the power-up sequence for the operating point (the method of extracted netlists)')))
