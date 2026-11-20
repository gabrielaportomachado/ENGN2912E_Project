#!/usr/bin/env python3
"""AUDIT step 8: the amplifier at the skewed MOS corners fs / sf (never simulated in A1-A4c): gain, f_hi, in-band noise and supply current of the frozen A4c channel at 27 C, 3.3 V.
Same netlist and method as freq_noise.py (tb_a4c_noise.spice, IDEAL feedback resistors at the typical-corner R0 5.235 TOhm: the pseudo-R floor does not depend on the MOS corner at 27 C, A2).
typical is run alongside as the reference.  usage: python3 amp_fssf.py [out.log]"""
import sys, os, re, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from ngjob import *
import numpy as np
import freq_noise as F

MD = os.path.join(PT, 'fssf')
os.makedirs(MD, exist_ok=True)


def net(corner, d):
    t = F.net('typical', 27, 5.23534e12, 5.23572e12, d)
    if corner != 'typical':
        mf = os.path.join(MD, 'models_%s.spice' % corner)
        open(mf, 'w').write('* audit: %s MOS corner, typical MIM and resistors\n.include %s/design.ngspice\n.lib %s/sm141064.ngspice %s\n.lib %s/sm141064.ngspice mimcap_typical\n.lib %s/sm141064.ngspice res_typical\n' % (corner, PDKNG, PDKNG, corner, PDKNG, PDKNG))
        t = t.replace('.include %s/spice/models_typical.spice' % AMP, '.include ' + mf)
    return t.replace('.control\n', '.control\nop\nlet isup = -i(Vdd)\nlet vo = v(out)\necho OPR isup=$&isup vout=$&vo\n', 1)


if __name__ == '__main__':
    out = open(sys.argv[1], 'w') if len(sys.argv) > 1 else sys.stdout
    P = lambda *a: (print(*a, file=out), out.flush())
    P(__doc__.split('usage')[0].strip())
    res = run_jobs([('a_%s' % c, net(c, os.path.join(MD, 'a_%s' % c))) for c in ('typical', 'fs', 'sf')], 'fssf', log=lambda s: None)
    P('%-8s | %8s %8s %8s | %10s %10s | %9s %8s' % ('corner', 'gmid_dB', 'f_lo_Hz', 'f_hi_Hz', 'noise_ib', 'noise_tot', 'Isup_uA', 'vout_V'))
    for c in ('typical', 'fs', 'sf'):
        fa = os.path.join(MD, 'a_%s_ac.dat' % c)
        if not os.path.exists(fa):
            P('%-8s FAILED %s' % (c, res['a_%s' % c]['abort']))
            continue
        a = np.loadtxt(fa)
        f, g = a[:, 0], a[:, 1]
        gm = np.interp(12.25, f, g)
        fhi = f[(f > 12.25) & (g < gm - 3)][0]
        flo = f[(f < 12.25) & (g < gm - 3)][-1]
        n = np.loadtxt(os.path.join(MD, 'a_%s_n.dat' % c))
        s2 = n[:, 1] ** 2
        k = 10 ** (gm / 20)
        ib = math.sqrt(F.integ(n[:, 0], s2, 0.5, 300)) / k * 1e6
        tot = math.sqrt(F.integ(n[:, 0], s2, 0.5, 2e6)) / k * 1e6
        o = results(res['a_%s' % c]['out'], 'OPR')
        P('%-8s | %8.3f %8.3f %8.1f | %10.3f %10.3f | %9.2f %8.4f' % (c, gm, flo, fhi, ib, tot, o[0]['isup'] * 1e6 if o else float('nan'), o[0]['vout'] if o else float('nan')))
    P('noise in uV rms at the electrode (0.5-300 Hz, and 0.5 Hz-2 MHz), typical flicker.  f_lo here is with the IDEAL 5.235 TOhm resistors.')
    if out is not sys.stdout:
        out.close()
    cleanup('fssf')
