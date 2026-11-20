#!/usr/bin/env python3
"""AUDIT steps 2 and 7: amplifier roll-off above the signal band, aliasing at 4 kS/s, and the auditor's own end-to-end noise / ENOB budget.
New simulation (cheap): .ac and .noise of the frozen A4c channel (AFE/amp/tb/tb_a4c_noise.spice netlist, includes rewritten to absolute paths, IDEAL feedback resistors
= R0 per corner as Decision 8 and sim/a4c_noise.log), typ 27 / ff 85 / ss -40, typical flicker (fnoicor = 0).  The spectrum is integrated here in Python:
  in band 0.5-300 Hz; first Nyquist zone 0.5 Hz-2 kHz; aliases = sum over k >= 1 of the bands k*4 kHz +- 300 Hz that fold onto 0.5-300 Hz; total 0.5 Hz - 2 MHz.
ADC terms from saved logs (stated per line).  usage: python3 freq_noise.py [out.log]"""
import sys, os, re, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from ngjob import *
import numpy as np

COR = [('typical', 27, 5.23534e12, 5.23572e12), ('ff', 85, 4.68481e12, 6.22437e12), ('ss', -40, 4.0999e12, 4.0999e12)]     # RFIX / RFIX2 from AFE/amp/sim/a4c_noise.log headers
FQ = [300, 1000, 2000, 3700, 4000, 4300, 7700, 8000, 16000, 40000, 100000, 400000, 1000000]
FS = 4000.0
LSB = 3.3 / 4096


def net(corner, temp, r1, r2, d):
    t = open(os.path.join(AMP, 'tb', 'tb_a4c_noise.spice')).read()
    t = t[:t.index('.control')]
    t = t.replace('../spice/models_typical.spice', '%s/spice/models_%s.spice' % (AMP, corner)).replace('../spice/', AMP + '/spice/').replace('../../../TGATE/', REPO + '/TGATE/')
    t = re.sub(r'^\.temp .*$', '.temp %g' % temp, t, flags=re.M)
    t = re.sub(r'^\.param RFIX=.*$', '.param RFIX=%g' % r1, t, flags=re.M)
    t = re.sub(r'^\.param RFIX2=.*$', '.param RFIX2=%g' % r2, t, flags=re.M)
    c = ['.control', 'ac dec 100 1e-2 2e6', 'wrdata %s_ac.dat vdb(out)' % d, 'noise v(out) Vd dec 200 0.1 2e6', 'setplot noise1', 'wrdata %s_n.dat onoise_spectrum' % d, 'echo DONE', 'quit', '.endc', '.end']
    return t + '\n'.join(c) + '\n'


def integ(f, s2, lo, hi):
    """integral of the PSD s2 [V2/Hz] from lo to hi (log-spaced grid, trapezoid on interpolated points)"""
    if hi <= f[0] or lo >= f[-1]:
        return 0.0
    x = np.unique(np.concatenate([[max(lo, f[0]), min(hi, f[-1])], f[(f > lo) & (f < hi)]]))
    y = np.interp(x, f, s2)
    return float(np.sum(0.5 * (y[1:] + y[:-1]) * np.diff(x)))


if __name__ == '__main__':
    out = open(sys.argv[1], 'w') if len(sys.argv) > 1 else sys.stdout
    P = lambda *a: (print(*a, file=out), out.flush())
    P(__doc__.split('usage')[0].strip())
    d = os.path.join(PT, 'fn')
    os.makedirs(d, exist_ok=True)
    res = run_jobs([('fn_%s_%d' % (c, T), net(c, T, r1, r2, os.path.join(d, 'fn_%s_%d' % (c, T)))) for (c, T, r1, r2) in COR], 'fn', log=lambda s: None)
    G = {}
    N = {}
    P('\n1. ROLL-OFF OF THE CHANNEL (|H| relative to the mid-band gain at 12.25 Hz, dB) and the local slope')
    P('%-8s %4s | gmid_dB f_hi_Hz | ' % ('corner', 'T') + ' '.join('%7s' % (('%gk' % (x / 1000)) if x >= 1000 else '%g' % x) for x in FQ) + ' | slope 4k-40k, 40k-400k dB/dec')
    for (c, T, r1, r2) in COR:
        k = 'fn_%s_%d' % (c, T)
        fa = os.path.join(d, k + '_ac.dat')
        if not os.path.exists(fa):
            P('%s FAILED %s' % (k, res[k]['abort']))
            continue
        a = np.loadtxt(fa)
        f, g = a[:, 0], a[:, 1]
        gm = np.interp(12.25, f, g)
        fhi = f[(f > 12.25) & (g < gm - 3)][0]
        rel = [np.interp(x, f, g) - gm for x in FQ]
        s1 = (np.interp(40e3, f, g) - np.interp(4e3, f, g))
        s2 = (np.interp(400e3, f, g) - np.interp(40e3, f, g))
        G[(c, T)] = (gm, fhi, f, g)
        P('%-8s %4d | %7.3f %7.1f | ' % (c, T, gm, fhi) + ' '.join('%7.1f' % x for x in rel) + ' | %6.1f %6.1f' % (s1, s2))
        n = np.loadtxt(os.path.join(d, k + '_n.dat'))
        N[(c, T)] = (n[:, 0], n[:, 1] ** 2)
    P('  -> first-order roll-off (-20 dB/decade) from f_hi up to at least 40 kHz; alias attenuation of an interferer at 3.7 / 4.3 kHz (lands at 300 Hz) and 7.7 kHz read from the table.')

    P('\n2. AMPLIFIER NOISE, input-referred = output noise / mid-band gain [uV rms], typical flicker, electrodes included (Randles pair)')
    P('%-8s %4s | %9s %11s %11s %12s | %14s %14s | %12s' % ('corner', 'T', '0.5-300Hz', '0.5Hz-2kHz', '2k-2MHz', 'total 2MHz', 'aliases->band', 'band+aliases', 'codes 0-2kHz'))
    AMPN = {}
    for (c, T, r1, r2) in COR:
        if (c, T) not in N:
            continue
        f, s2 = N[(c, T)]
        gm = 10 ** (G[(c, T)][0] / 20)
        ib = integ(f, s2, 0.5, 300)
        nyq = integ(f, s2, 0.5, 2000)
        hi = integ(f, s2, 2000, 2e6)
        al = sum(integ(f, s2, k * FS - 300, k * FS + 300) for k in range(1, int(2e6 / FS)))
        u = lambda p: math.sqrt(p) / gm * 1e6
        AMPN[(c, T)] = dict(ib=u(ib), nyq=u(nyq), hi=u(hi), tot=u(nyq + hi), al=u(al), gm=gm)
        P('%-8s %4d | %9.3f %11.3f %11.3f %12.3f | %14.3f %14.3f | %12.3f' % (c, T, u(ib), u(nyq), u(hi), u(nyq + hi), u(al), u(ib + al), u(nyq + hi)))
    P('  (aliases->band = noise from k*4 kHz +- 300 Hz folded onto the 0.5-300 Hz band; "codes 0-2kHz" = everything the 4 kS/s code stream contains if the host does NOT low-pass to 300 Hz = the total wideband noise)')
    P('  cross-check with AFE/amp/sim/a4c_noise.log: 0.5-300 Hz 1.668 / 1.847 / 1.540, 0.5 Hz-2 kHz 1.796 / 2.003 / 1.625, 0.5 Hz-1 MHz 1.826 / 2.055 / 1.641 uV')

    P('\n3. END-TO-END BUDGET at the electrode (1 LSB = 0.8057 mV at the ADC input = 0.8057 uV at the electrode; gain 1000)')
    # ADC terms [uV rms at the ADC input, white over 0-2 kHz unless stated]; sources in the text
    kTC = {('typical', 27): 34.1, ('ff', 85): 37.3, ('ss', -40): 30.1}               # AFE/adc/sim/d2_ktc.log
    cmpn = {('typical', 27): 118.0, ('ff', 85): 168.0, ('ss', -40): 108.0}           # AFE/adc/sim/d1_noise.log (input pair only)
    latch = 50.0                                                                       # ESTIMATE (D1), never measured
    q = LSB / math.sqrt(12) * 1e6                                                      # quantisation
    dnl = 0.25 * LSB * 1e6                                                             # ESTIMATE: extra code-width noise from DNL (D2: max |DNL| mean 0.54 LSB at A_C 0.5; rms over codes ~0.25 LSB)
    cref = {('typical', 27): 24.0, ('ff', 85): 28.0, ('ss', -40): 21.0}               # kT/C of Cref 7 pF (I2 ESTIMATE; partly common with the plate sample: taken in full)
    thd = {('typical', 27): 0.040e-2, ('ff', 85): 2.527e-2, ('ss', -40): 0.051e-2}    # AFE/amp/sim/a4c_thd.log, +-0.5 mV 12.25 Hz
    tg = {('typical', 27): (21.0e3, 300.15), ('ff', 85): (15.6e3, 358.15), ('ss', -40): (34.2e3, 233.15)}   # AFE/review/sim/tgate_ron.log max Ron at 3.3 V
    P('%-8s %4s | %7s %7s %7s | %6s %6s %6s %6s %6s %6s %8s | %9s %9s | %9s %9s | %6s %6s %6s' % ('corner', 'T', 'amp_ib', 'alias', 'TGATE', 'kT/C', 'Cref', 'cmp', 'latch', 'quant', 'DNL', 'ADC_rss', 'IN-BAND', 'margin%', 'WIDEBAND', 'ADC_LSB', 'SNR_dB', 'SINAD', 'ENOB_FS'))
    for (c, T, r1, r2) in COR:
        if (c, T) not in AMPN:
            continue
        a = AMPN[(c, T)]
        adc_uV = math.sqrt(kTC[(c, T)] ** 2 + cref[(c, T)] ** 2 + cmpn[(c, T)] ** 2 + latch ** 2 + q ** 2 + dnl ** 2)       # at the ADC input, 0-2 kHz
        adc_el = adc_uV / 1000.0                                                                                           # at the electrode
        frac = math.sqrt(300.0 / 2000.0)                                                                                   # white ADC noise: share inside 0-300 Hz
        ron, tk = tg[(c, T)]
        vtg = math.sqrt(4 * 1.380649e-23 * tk * ron * 299.5) * 1e6
        inband = math.sqrt(a['ib'] ** 2 + a['al'] ** 2 + vtg ** 2 + (adc_el * frac) ** 2)
        wide = math.sqrt(a['tot'] ** 2 + vtg ** 2 * (2000 / 299.5) + adc_el ** 2)
        sig = 500.0 / math.sqrt(2)                                                                                        # +-500 uV sine
        snr = 20 * math.log10(sig / wide)
        sinad = -10 * math.log10(10 ** (-snr / 10) + thd[(c, T)] ** 2)
        enob_fs = (sinad - 1.76) / 6.02 + math.log2(1.65 / 0.5)
        P('%-8s %4d | %7.3f %7.3f %7.3f | %6.1f %6.1f %6.1f %6.1f %6.1f %6.1f %8.1f | %9.3f %9.1f | %9.3f %9.3f | %6.1f %6.1f %6.2f' % (
            c, T, a['ib'], a['al'], vtg, kTC[(c, T)], cref[(c, T)], cmpn[(c, T)], latch, q, dnl, adc_uV, inband, 100 * (2.0 - inband) / 2.0, wide, adc_uV / (LSB * 1e6), snr, sinad, enob_fs))
    P('  columns: amp_ib, alias, TGATE [uV at the electrode]; kT/C .. DNL, ADC_rss [uV at the ADC input, over 0-2 kHz]; IN-BAND = rss of amplifier 0.5-300 Hz + aliases + TGATE Ron thermal noise')
    P('  + the ADC noise share inside 0-300 Hz [uV at the electrode]; margin vs the 2 uV target; WIDEBAND = all noise in the code stream without host filtering;')
    P('  SNR for a +-500 uV sine against WIDEBAND; SINAD adds the amplifier THD at +-0.5 mV (a4c_thd.log); ENOB_FS = (SINAD - 1.76)/6.02 + log2(1.65 V / 0.5 V).')
    P('  NOT in this budget (static, deterministic or host-side): fixed code offset -22..-40 LSB, the code-dependent threshold steps (-1.1 / +1.3 LSB at codes 1536 / 2048, Decision 43b), the')
    P('  top-of-range error (Decision 43c), supply ripple (0.6 LSB per mV: board requirement <= 1 mV rms), CS jitter (<= 85 ns rms for 0.1 LSB at 300 Hz full scale), fnoicor = 1 (4.4-4.9 uV, Decision 10).')
    if out is not sys.stdout:
        out.close()
    cleanup('fn')
