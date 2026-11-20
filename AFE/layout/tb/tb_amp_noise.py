#!/usr/bin/env python3
"""tb_amp_noise.py (L2b): input-referred noise of the amplifier channel, 0.5-300 Hz = integrated output noise / mid-band gain (Decision 1), typical flicker (fnoicor = 0, Decision 4).
  noise_d8_uv    Decision 8 method: the pseudo-resistors replaced by IDEAL noisy resistors of the same value (RFIX per corner, AFE/amp/sim/a4c_noise.log).  Schematic only: it needs the
                 simulation netlist.  THIS is the number the 2 uV target is judged on.
  noise_real_uv  the netlist as it is (pseudo-resistor transistors).  Runs on the schematic AND on an extracted netlist: compare.py scales the Decision-8 baseline by post / pre of this value.
  *_fn1_uv       the same with fnoicor = 1 (worst-case flicker, documented risk of Decision 10), typ only.
usage: python3 AFE/layout/tb/tb_amp_noise.py [--netlist schematic|<amp_ch PEX>] [--corner typ|ff85|ss-40|all] [--junction] [--out DIR]"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lptb import *


def run(netlist, corner, a, log):
    dut = amp_dut(netlist, a.prdiff)
    for w in dut.warnings:
        log('WARNING ' + w)
    simple = not (dut.pex or dut.prdiff)
    ns = 'native' if simple else settle(corner, dut, log)
    modes = [('real', 0, 0)] + ([('d8', 1, 0)] if simple else [])
    if corner == 'typ':
        modes += [('real_fn1', 0, 1)] + ([('d8_fn1', 1, 1)] if simple else [])
    jobs = []
    for name, rmode, fn in modes:
        p = {'fnoicor': fn}
        if rmode:
            p.update(RMODE=1, RMODE2=1, RFIX=RFIX[corner][0], RFIX2=RFIX[corner][1], RNOISY=1, RNOISY2=1)
        L = amp_bench(corner, dut, 'noise %s' % name, params=p, nodeset=ns)
        L += ['.control', 'ac dec 20 1 100', 'meas ac gm find vdb(out) at=12.25', 'noise v(out) Vd dec 100 0.5 300', 'setplot noise2', 'echo RESULT gm_db=$&ac1.gm vo=$&onoise_total', 'quit', '.endc', '.end']
        jobs.append(('n_%s_%s_%s' % (dut.tag, corner, name), '\n'.join(L) + '\n'))
    res = run_ng(jobs, 'amp_noise', log=log)
    v = {}
    for (name, _, _), (jn, _) in zip(modes, jobs):
        r = results(res[jn]['out'])
        if not r:
            raise TbError('noise run %s failed: %s' % (name, res[jn]['abort'] or res[jn]['out'][-300:]))
        g = 10 ** (r[0]['gm_db'] / 20)
        v['noise_%s_uv' % name] = r[0]['vo'] / g * 1e6
        if name == 'real':
            v['g_mid_db'] = r[0]['gm_db']
    return v, {'warnings': dut.warnings}


if __name__ == '__main__':
    sys.exit(cli('amp_noise', __doc__, AMP_CORNERS, run))
