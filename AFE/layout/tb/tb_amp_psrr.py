#!/usr/bin/env python3
"""tb_amp_psrr.py (L2b): supply-to-output gain of the amplifier channel [V/V] at 50, 60, 300 Hz and 1 kHz (AC source in series with VDD, electrode quiet).  Pre-layout 0.557-0.570 V/V at
50 / 60 Hz over 9 PVT (AFE/amp/sim/a4b_summary.txt): no target, a host requirement follows from it (board ripple <= about 1 mV rms).
usage: python3 AFE/layout/tb/tb_amp_psrr.py [--netlist schematic|<amp_ch PEX>] [--corner typ|ff85|ss-40|all] [--junction] [--out DIR]"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lptb import *


def run(netlist, corner, a, log):
    dut = amp_dut(netlist, a.prdiff)
    ns = 'native' if not (dut.pex or dut.prdiff) else settle(corner, dut, log)
    L = amp_bench(corner, dut, 'supply gain', vdd='Vdd vdd 0 dc {VSUP} ac 1', vd='Vd vd 0 dc 0 ac 0', nodeset=ns)
    L += ['.control', 'ac dec 50 1 1e4'] + ['meas ac g%d find vm(out) at=%d' % (f, f) for f in (50, 60, 300, 1000)] + ['echo RESULT g50=$&g50 g60=$&g60 g300=$&g300 g1000=$&g1000', 'quit', '.endc', '.end']
    r = list(run_ng([('psrr_%s_%s' % (dut.tag, corner), '\n'.join(L) + '\n')], 'amp_psrr', log=log).values())[0]
    o = results(r['out'])
    if not o:
        raise TbError('ac did not run: ' + (r['abort'] or r['out'][-300:]))
    return {'supply_gain_50hz': o[0]['g50'], 'supply_gain_60hz': o[0]['g60'], 'supply_gain_300hz': o[0]['g300'], 'supply_gain_1khz': o[0]['g1000']}, {'warnings': dut.warnings}


if __name__ == '__main__':
    sys.exit(cli('amp_psrr', __doc__, AMP_CORNERS, run))
