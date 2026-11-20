#!/usr/bin/env python3
"""tb_amp_pwrup.py (L2b; one channel of L3b item 5): host power-up sequence on the layout cell amp_ch with the real bias cell.  VDD ramps 0 -> VDD in 1 ms from the all-zero state
(record switch open: sw_rec = 0, park on), the host waits T_WAIT, sets RST_AMP for 100 ms (Decision 38a / 44c), releases it and reads.
Values: vout_before_v (output just before RST_AMP: a rail = the power-up latch of A4c), vout_100ms_v / vout_1s_v (0.1 s and 1 s after the release), err_1s_mv = |vout_1s - 1.65 V| (limit 10 mV),
        codes_from_mid_1s = that error in ADC LSB (the host accepts 200 LSB, Decision 44c), t_wait_s.
usage: python3 AFE/layout/tb/tb_amp_pwrup.py [--netlist schematic|<amp_ch PEX>] [--corner typ|ff85|ss-40|all] [--junction] [--out DIR]"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lptb import *
import numpy as np

TW = {'typ': 0.2, 'ff85': 0.2, 'ss-40': 1.5}          # one channel on the bias: start-up 0.6 s at ss -40 C (AFE/review/sim/bias_startup.log); the 8-channel time is tb_bias_startup.py


def run(netlist, corner, a, log):
    dut = ampch_dut(netlist, a.prdiff)
    tw = TW.get(corner, 1.5)
    t1, t2 = tw, tw + 0.1
    tstop = t2 + 1.0
    d = os.path.join(SCRATCH, 'tb', 'amp_pwrup')
    os.makedirs(d, exist_ok=True)
    f = os.path.join(d, 'pu_%s_%s.dat' % (dut.tag, corner))
    L, tp = ampch_bench(corner, dut, 'power-up: VDD ramp, wait %.1f s, RST_AMP 100 ms, release' % tw, vdd='Vdd vdd 0 PWL(0 0 1m {VSUP})',
                        rst='Vrst rst_amp 0 PWL(0 0 %g 0 %g {VSUP} %g {VSUP} %g 0)' % (t1, t1 + 1e-6, t2, t2 + 1e-6), sw=('Vsw sw_rec 0 0', 'Vswb sw_rec_b 0 PWL(0 0 1m {VSUP})'))
    L += ['.control', 'save v(out) v(vbn) v(vrs)', 'tran 1m %g 0 1m uic' % tstop, 'wrdata %s v(out) v(vbn) v(vrs)' % f, 'echo DONE', 'quit', '.endc', '.end']
    r = list(run_ng([('pu_%s_%s' % (dut.tag, corner), '\n'.join(L) + '\n')], 'amp_pwrup', retry=lambda n, t: t.replace('tran 1m ', 'tran 0.7m ').replace(' 0 1m uic', ' 0 0.7m uic'), log=log).values())[0]
    if 'DONE' not in r['out']:
        raise TbError('transient did not finish: ' + (r['abort'] or r['out'][-300:]))
    t, (out, vbn, vrs) = read_wr(f)
    at = lambda x: float(np.interp(x, t, out))
    v1s = at(t2 + 1.0)
    return {'t_wait_s': tw, 'vout_before_v': at(t1 - 1e-3), 'vout_100ms_v': at(t2 + 0.1), 'vout_1s_v': v1s, 'err_1s_mv': abs(v1s - 1.65) * 1e3, 'codes_from_mid_1s': abs(v1s - 1.65) / (CORNERS[corner][2] / 4096),
            'vbn_end_v': float(vbn[-1]), 'vrs_end_v': float(vrs[-1])}, {'warnings': dut.warnings}


if __name__ == '__main__':
    sys.exit(cli('amp_pwrup', __doc__, AMP_CORNERS, run))
