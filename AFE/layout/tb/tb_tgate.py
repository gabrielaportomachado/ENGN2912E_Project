#!/usr/bin/env python3
"""tb_tgate.py (L3a): the routing switch TGATE (5 V devices) at the single 3.3 V supply.  On resistance over the whole 0..VDD signal range (10 mV across the closed switch, C = VDD,
CBAR = 0) and the off leakage (C = 0, CBAR = VDD, 1 V across).  The bench of AFE/review/scripts/tgate_ron.py (pre-layout: 4.3-21.0 / 4.1-15.6 / 4.5-34.2 kOhm, leakage < 1 pA inside the rails).
--netlist: schematic = TGATE/TGATE.spice; or the PEX netlist of the TGATE with its tap cell (flow.py pex of test cell lp_tgate_tap, or of the cell L3a places).  Port names OUT C CBAR IN VDD VSS.
Values: ron_max_kohm, ron_min_kohm, ron_1v65_kohm, v_at_ron_max, i_off_pa (|current| through the open switch with 1 V across, far side at 1.65 V).
usage: python3 AFE/layout/tb/tb_tgate.py [--netlist schematic|<PEX>] [--corner typ|ff85|ss-40|all] [--out DIR]"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lptb import *
import numpy as np


def run(netlist, corner, a, log):
    dut = tgate_dut(netlist)
    for w in dut.warnings:
        log('WARNING ' + w)
    c, T, vdd = CORNERS[corner]
    d = os.path.join(SCRATCH, 'tb', 'tgate')
    os.makedirs(d, exist_ok=True)
    f = os.path.join(d, 'tg_%s_%s' % (dut.tag, corner))
    L = ['* LP golden testbench: routing TGATE at %g V [%s]' % (vdd, corner)] + model_lines(corner)
    L += dut.wrapper() if dut.pex else ['.include %s/TGATE/TGATE.spice' % REPO]
    L += ['.options gmin=1e-15', '.temp %g' % T, 'Vdd vdd 0 %g' % vdd, 'Vc c 0 %g' % vdd, 'Vcb cb 0 0', 'Vin in 0 1.65', 'Bo out 0 V = V(in) - 0.01', 'Xtg out c cb in vdd 0 TGATE',
          'Vc2 c2 0 0', 'Vcb2 cb2 0 %g' % vdd, 'Vin2 in2 0 2.65', 'Vo2 out2 0 1.65', 'Xtg2 out2 c2 cb2 in2 vdd 0 TGATE',
          '.control', 'dc Vin 0.0 %g 0.025' % vdd, 'let ron = 0.01/abs(i(Vin))', 'wrdata %s_on.dat ron' % f, 'op', 'echo RESULT ioff=$&i(Vin2)', 'echo DONE', 'quit', '.endc', '.end']
    r = list(run_ng([('tg_%s_%s' % (dut.tag, corner), '\n'.join(L) + '\n')], 'tgate', log=log).values())[0]
    if 'DONE' not in r['out']:
        raise TbError('dc sweep did not run: ' + (r['abort'] or r['out'][-300:]))
    x, (ron,) = read_wr(f + '_on.dat')
    o = results(r['out'])[0]
    return {'ron_max_kohm': float(ron.max() / 1e3), 'ron_min_kohm': float(ron.min() / 1e3), 'ron_1v65_kohm': float(np.interp(1.65, x, ron) / 1e3), 'v_at_ron_max': float(x[ron.argmax()]),
            'i_off_pa': abs(o['ioff']) * 1e12}, {'warnings': dut.warnings, 'ports': dut.ports if dut.pex else TGATE_PINS}


if __name__ == '__main__':
    sys.exit(cli('tgate', __doc__, AMP_CORNERS, run))
