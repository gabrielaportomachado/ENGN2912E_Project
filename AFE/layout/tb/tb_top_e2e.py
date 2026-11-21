#!/usr/bin/env python3
"""tb_top_e2e.py (L3b item 1): end-to-end transistor-level run of ONE channel: electrode (Randles) -> routing TGATE (record) -> amplifier -> its own ADC cell -> the 12 decisions = the code the
SPI frame carries (the digital frame itself - 80 SCLK, status word + channel words 1-4 {ID[1:0], 00, code} of AFE/adc/SPI_FRAME.md, IDs 0-3 - is proven by AFE/adc/tb/tb_adc_top.v and the gate-level testbench of L1d / R14; REVIEW R16: this bench is ONE channel, it does not depend on the channel count).  It is the X2 S1 run (AFE/adc/scripts/x2_s1.py, unchanged, closed-loop PWL replay, option `tgate`):
9 electrode steps to outputs of 1.15 .. 2.15 V and a 450 uV pk 23.4 Hz sine at 8 phases, 3 frames at 4 kS/s each, evaluated with the definitions of x2_s1_report.py.
Values: offset_lsb (code centre minus amplifier output, below 2.05 V), inl_lo_lsb / inl_all_lsb (INL beyond the fixed offset below 2.05 V / over 1.15-2.15 V), amp_minus_adc_lsb (largest |difference|
to the same ADC alone: what the amplifier and the TGATE add), gain_sine_code_db (end-to-end gain from the codes), vout_min_v / vout_max_v (amplifier output reached; = the internal node the REC pad
would have shown, Decision 45), kick_max_mv, unresolved.   Pre-layout X2 (without the TGATE): offset -30.3 / -40.4 / -22.0 LSB, INL 0.63 / 1.99 / 0.61, gain 60.007 / 59.865 / 59.990 dB.
usage: python3 AFE/layout/tb/tb_top_e2e.py [--netlist schematic|<amp_ch PEX>] [--adc schematic|<adc_ch PEX>] [--corner typ|ff85|ss-40|all] [--out DIR]"""
import os, sys, re, runpy, builtins
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lptb import *
import numpy as np

TPRE = {'typ': 4, 'ff85': 3, 'ss-40': 4}


def run(netlist, corner, a, log):
    d1 = amp_x2_env(netlist, corner, log)
    d2 = adc_env(a.adc)
    suf = '_lptop'
    env = {'X2_SUFFIX': suf, 'X2_NCAL': '12', 'X2_LOG_PREFIX': X2_PREFIX}
    fn0 = os.path.join(ADC, 'sim', 'x2_s1_%s_tgate%s.npz' % (corner, suf))
    if os.path.exists(fn0):
        os.remove(fn0)                                                                   # never evaluate a result of an earlier run
    txt = run_script([os.path.join(ADC, 'scripts', 'x2_s1.py'), corner, str(TPRE.get(corner, 4)), 'all', 'tgate'], env, log)
    fn = os.path.join(ADC, 'sim', 'x2_s1_%s_tgate%s.npz' % (corner, suf))
    if not os.path.exists(fn):
        raise TbError('x2_s1.py wrote no result file: ' + txt[-400:])
    LSB, AE, FSIG, TFR = 3.3 / 4096, 0.45e-3, 3 * 4000.0 / 512, 250e-6
    z = np.load(fn, allow_pickle=True)
    R, al = z['R'], float(z['alpha'])
    U_ = lambda vo, x12v, code: (vo + x12v / al) / LSB - (code.astype(int) | 1)
    S = R[R[:, 2] > 0]
    vo, c = S[:, 4], S[:, 5]
    u = U_(vo, S[:, 8] * LSB, c)
    e = c + 0.5 - vo / LSB
    lo = vo < 2.05
    r = z['adc_rows']
    va, ca, xa = r[:, 0], r[:, 1], r[:, 4]
    ua = U_(va, xa, ca)
    o = np.argsort(va)
    du = u - np.interp(vo, va[o], ua[o])
    pk = np.r_[S[S[:, 10] != 0, 10], R[(R[:, 2] == 0) & (R[:, 10] != 0), 10]]
    v = {'offset_lsb': float(e[lo].mean()), 'inl_lo_lsb': float(max(np.abs(u[lo] - u[lo].mean()).max(), np.abs(e[lo] - e[lo].mean()).max() - 0.5)),
         'inl_all_lsb': float(max(np.abs(u - u[lo].mean()).max(), np.abs(e - e[lo].mean()).max() - 0.5)), 'amp_minus_adc_lsb': float(np.abs(du[lo]).max()),
         'vout_min_v': float(vo.min()), 'vout_max_v': float(vo.max()), 'kick_max_mv': float(np.abs(pk).max() * 1e3) if len(pk) else float('nan'), 'unresolved': float(R[:, 12].sum()), 'n': float(len(S))}
    sn = S[S[:, 0] == 1]
    if len(sn) >= 12:
        ph = sn[:, 1] + 2 * np.pi * FSIG * sn[:, 2] * TFR
        M = np.vstack([np.ones_like(ph), np.sin(ph), np.cos(ph)]).T
        (a0, a1, a2), *_ = np.linalg.lstsq(M, (sn[:, 5] + 0.5) * LSB, rcond=None)
        v['gain_sine_code_db'] = float(20 * np.log10(np.hypot(a1, a2) / AE))
    for f in (fn, fn.replace('.npz', '.log')):
        try:
            os.replace(f, os.path.join(out_dir(netlist, a.out), 'top_e2e_x2_s1_%s%s' % (corner, os.path.splitext(f)[1])))
        except OSError:
            pass
    x2_collect(out_dir(netlist, a.out), 'top_e2e', corner)
    return v, {'amp': netlist, 'adc': a.adc, 'warnings': (d1.warnings if d1 else []) + (d2.warnings if d2 else [])}


if __name__ == '__main__':
    sys.exit(cli('top_e2e', __doc__, AMP_CORNERS, run, lambda ap: ap.add_argument('--adc', default='schematic')))
