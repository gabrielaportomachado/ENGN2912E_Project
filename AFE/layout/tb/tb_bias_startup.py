#!/usr/bin/env python3
"""tb_bias_startup.py (L2b / L3a; Decision 46b): start-up of the shared bias cell bias_genc with the vbn load of N = 8 channels (and N = 1 for comparison).  VDD ramps 0 -> VDD in 1 ms from
the all-zero state, no node guesses.  The load is the model of AFE/review/scripts/bias_startup.py (per channel: 24 + 6 mirror gates 16u/4u, the stage-2 tail 1u/20u, the one-shot leg 0.28u/40u,
the OTA-1 bias diode 2 x 50u/4u).  t90 = time after the start of the ramp at which the current of the mirror load reaches 90 % of its final value.
Values: t90_n8_ms, t90_n1_ms, i_sink_n8_ua (24 x 8 mirror devices), vbn_v, vcm_v, vrs_v, settled_n8 (1 = the final state was reached inside the run).
The host waits >= 5 s before RST_AMP (Decision 44c): t90_n8 must stay below 5 s at every corner.  Audit, with the old 3 kOhm/sq ladders: 3.7 ms / 1.0 ms / 3565 ms (typ / ff 85 / ss -40).
Not a switching transient: abstol 1e-16 (as the audit; 1e-12 would be coarser than the pA start-up current).
usage: python3 AFE/layout/tb/tb_bias_startup.py [--netlist schematic|<bias_genc PEX>] [--corner typ|ff85|ss-40|all] [--out DIR]"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lptb import *
import numpy as np

TS = {'typ': 0.2, 'ff85': 0.2, 'ss-40': 30.0}


def net(corner, dut, n, tstop, f):
    c, T, vdd = CORNERS[corner]
    d = 'ad=2.88p as=2.88p pd=32.36u ps=32.36u nrd=0 nrs=0'
    L = ['* LP golden testbench: bias_genc start-up with the vbn load of %d channel(s) [%s]' % (n, corner)] + model_lines(corner, dut.models)
    L += ['.include %s/spice/%s.spice' % (AMP, x) for x in ('ota1_params', 'afe_params', 'a4c_params')]
    L += dut.wrapper() if dut.pex else ['.include %s/spice/bias_genc.spice' % AMP]
    L += ['.options gmin=1e-16 abstol=1e-16 reltol=1e-4 vntol=1e-7 chgtol=1e-17 itl1=500 itl4=500', '.temp %g' % T, 'Vdd vdd 0 PWL(0 0 1m %g)' % vdd, 'Xbias vbn vcm vg1 vcmo vg2 vrs vdd 0 bias_genc',
          'Xsink ib vbn 0 0 nfet_03v3 W=16u L=4u nf=1 %s m=%d' % (d, 24 * n), 'Xdio ib ib vdd vdd pfet_03v3 W=50u L=4u nf=1 ad=9p as=9p pd=100.36u ps=100.36u nrd=0 nrs=0 m=%d' % (2 * n),
          'Emid mid 0 vdd 0 0.5', 'Xms mid vbn 0 0 nfet_03v3 W=16u L=4u nf=1 %s m=%d' % (d, 6 * n), 'Xmt2 mid vbn 0 0 nfet_03v3 W=1u L=20u nf=1 ad=0.18p as=0.18p pd=2.36u ps=2.36u nrd=0 nrs=0 m=%d' % n,
          'Xlt vdd vbn 0 0 nfet_03v3 W=0.28u L=40u nf=1 ad=0.05p as=0.05p pd=0.92u ps=0.92u nrd=0 nrs=0 m=%d' % n,
          '.control', 'save v(vbn) v(vcm) v(vrs) @m.xsink.m0[id]', 'tran 1u %g 0 10m' % tstop, 'wrdata %s v(vbn) @m.xsink.m0[id] v(vcm) v(vrs)' % f, 'echo DONE', 'quit', '.endc', '.end']
    return '\n'.join(L) + '\n'


def run(netlist, corner, a, log):
    dut = bias_dut(netlist)
    ts = TS.get(corner, 30.0)
    d = os.path.join(SCRATCH, 'tb', 'bias_startup')
    os.makedirs(d, exist_ok=True)
    jobs, v = [], {}
    for n in (8, 1):
        f = os.path.join(d, 'bs_%s_%s_n%d.dat' % (dut.tag, corner, n))
        jobs.append(('bs_%s_%s_n%d' % (dut.tag, corner, n), net(corner, dut, n, ts if n == 8 else max(ts / 4, 0.2), f)))
    res = run_ng(jobs, 'bias_startup', log=log)
    for (jn, _), n in zip(jobs, (8, 1)):
        f = os.path.join(d, 'bs_%s_%s_n%d.dat' % (dut.tag, corner, n))
        if 'DONE' not in res[jn]['out']:
            raise TbError('start-up run n = %d did not finish: %s' % (n, res[jn]['abort'] or res[jn]['out'][-300:]))
        t, (vbn, isk, vcm, vrs) = read_wr(f)
        fin = float(np.mean(isk[t > 0.9 * t[-1]]))
        i90 = int(np.argmax(isk >= 0.9 * fin))
        v['t90_n%d_ms' % n] = float(t[i90] * 1e3) if isk[i90] >= 0.9 * fin else float('nan')
        if n == 8:
            ok = abs(isk[-1] - fin) < 0.01 * abs(fin) and abs(np.mean(isk[(t > 0.8 * t[-1]) & (t < 0.9 * t[-1])]) - fin) < 0.02 * abs(fin)
            v.update(i_sink_n8_ua=fin * 1e6, vbn_v=float(vbn[-1]), vcm_v=float(vcm[-1]), vrs_v=float(vrs[-1]), settled_n8=1.0 if ok else 0.0)
    return v, {'warnings': dut.warnings}


if __name__ == '__main__':
    sys.exit(cli('bias_startup', __doc__, AMP_CORNERS, run))
