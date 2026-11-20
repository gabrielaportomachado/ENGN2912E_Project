#!/usr/bin/env python3
"""lp_prdiff_study.py (LP evidence, not a golden testbench): what the junction area of the six pseudo-resistor transistors does to the amplifier, and what the two pseudo-resistor gate
taps could do about it.  AFE/amp/spice/pseudoR.spice gives the devices of pseudo_r_fg NO ad / as / pd / ps; an extracted netlist always has them.
Two models: `design` = the netlists as they are; `junction` = the same with area W x 0.18 um and perimeter 2 (W + 0.18 um) on those six devices (lptb.pseudo_r_with_diffusion).
Sweep: the gate taps are overridden by IDEAL sources vg1 = vcm_in + VTT1 (stage 1, design 0.2 V) and vg2 = vcm_out + VTT2 (stage 2, design 0.9 V); everything else is the real circuit.
Per point: f_lo (-3 dB from the peak; < 0.001 = no corner above 1 mHz), gain at 0.5 Hz and 12.25 Hz, noise 0.5-300 Hz with the real devices, and the STATIC output shift for an electrode
DC offset of 10 mV and 100 mV (the DC operating point with the offset in series with the recording electrode, minus the one without).
usage: python3 AFE/layout/tb/lp_prdiff_study.py [out.log]"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lptb import *
import numpy as np

PTS = [(0.2, 0.9), (0.15, 0.9), (0.1, 0.9), (0.05, 0.9), (0.0, 0.9), (0.2, 0.6), (0.1, 0.6), (0.1, 0.4), (0.05, 0.4), (0.0, 0.4), (0.0, 0.2), (0.0, 0.0)]


def bench(corner, dut, v1, v2, vos, ns, ctl):
    L = amp_bench(corner, dut, 'tap study VTT1 %g VTT2 %g offset %g' % (v1, v2, vos), nodeset=ns, vos=('Vosr vosr 0 %g' % vos, 'Vosf vosf 0 0'))
    L = [x.replace('Xbias vbn vcm vg1 vcmo vg2 vrs vdd 0 bias_genc', 'Xbias vbn vcm vg1x vcmo vg2x vrs vdd 0 bias_genc\nEg1 vg1 vcm tapv1 0 1\nVt1 tapv1 0 %g\nEg2 vg2 vcmo tapv2 0 1\nVt2 tapv2 0 %g' % (v1, v2)) for x in L]
    return '\n'.join(L + ['.control'] + ctl + ['quit', '.endc', '.end']) + '\n'


if __name__ == '__main__':
    out = open(sys.argv[1], 'w') if len(sys.argv) > 1 else sys.stdout
    P = lambda *a: (print(*a, file=out), out.flush())
    P(__doc__.split('usage')[0].strip())
    d = os.path.join(SCRATCH, 'tb', 'prdiff')
    os.makedirs(d, exist_ok=True)
    for model in ('design', 'junction'):
        for corner in AMP_CORNERS:
            dut = amp_dut('schematic', model == 'junction')
            ns = settle(corner, dut)
            jobs = []
            for (v1, v2) in PTS:
                tag = '%s_%s_%g_%g' % (model, corner, v1, v2)
                f = os.path.join(d, tag + '.dat')
                jobs.append((tag + '_ac', bench(corner, dut, v1, v2, 0, ns, ['op', 'echo RESULT vout=$&v(out)', 'ac dec 50 1e-4 1e5', 'wrdata %s vdb(out)' % f, 'noise v(out) Vd dec 100 0.5 300', 'setplot noise2', 'echo RESULT vo=$&onoise_total'])))
                for vos in (0.01, 0.1):
                    jobs.append((tag + '_os%g' % vos, bench(corner, dut, v1, v2, vos, ns, ['op', 'echo RESULT vout=$&v(out)'])))
            res = run_ng(jobs, 'prdiff')
            P('\n== model %-8s corner %-6s | VTT1  VTT2 | f_lo_Hz   g(0.5Hz)  g(12Hz) dB | noise_real uV | out DC V | static shift for 10 mV / 100 mV electrode offset [mV]' % (model, corner))
            for (v1, v2) in PTS:
                tag = '%s_%s_%g_%g' % (model, corner, v1, v2)
                r = results(res[tag + '_ac']['out'])
                try:
                    a = np.loadtxt(os.path.join(d, tag + '.dat'))
                    fr, g = a[:, 0], a[:, 1]
                    gm = float(np.interp(np.log10(12.25), np.log10(fr), g))
                    gp, ip = g.max(), int(g.argmax())
                    lo = np.where((g[:ip] < gp - 3))[0]
                    flo = fr[lo[-1]] if len(lo) else 0.0
                    g05 = float(np.interp(np.log10(0.5), np.log10(fr), g))
                    nz = r[1]['vo'] / 10 ** (gm / 20) * 1e6
                    v0 = r[0]['vout']
                    sh = []
                    for vos in (0.01, 0.1):
                        q = results(res[tag + '_os%g' % vos]['out'])
                        sh.append((q[0]['vout'] - v0) * 1e3 if q else float('nan'))
                    P('   %-33s | %4.2f  %4.2f | %8.4f  %7.2f  %7.2f    | %8.3f      | %.4f   | %+9.2f / %+9.2f' % ('', v1, v2, flo, g05, gm, nz, v0, sh[0], sh[1]))
                except Exception as e:                    # noqa
                    P('   VTT1 %g VTT2 %g: FAILED %s %s' % (v1, v2, repr(e)[:80], res[tag + '_ac']['abort'][:120]))
    if out is not sys.stdout:
        out.close()
