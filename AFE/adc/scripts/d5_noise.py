#!/usr/bin/env python3
"""D5 item 3: input-referred noise in 0.5-300 Hz = amplifier (A4c table, sim/a4c_noise.log) + ADC (quantisation, kT/C, comparator) combined ANALYTICALLY (label ESTIMATE; no transient-noise run).
The ADC noise is white over 0 - fs/2 = 2 kHz after sampling (each sample's noise is independent); the part inside 0.5-300 Hz is sqrt(299.5/2000) = 0.387 of its rms.  Gain 1000 (60 dB): 1 LSB = 0.806 mV at the output = 0.806 uV at the electrode.
Comparator part: hybrid Monte Carlo (d4_hybrid chip(), 5 chips x 4000 inputs spread over +-2 LSB around mid-scale x independent noise draws), rms of (noisy code - noiseless code of the same chip and input), pair noise 118/168/108 uV + latch 50 uV (ESTIMATE, D1)."""
import sys, os, numpy as np
H = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, H); import d4_hybrid as hy
LSB = 3.3 / 4096; FB = np.sqrt(299.5 / 2000)
A = {'typical': dict(B=1.66753, C=1.79647, D=1.82648, B1=4.71952), 'ff': dict(B=1.84693, C=2.00323, D=2.0547, B1=4.93343), 'ss': dict(B=1.53982, C=1.62546, D=1.64096, B1=4.39318)}   # uV input-referred (A4c, 0.5-300 / 0.5-2k / 0.5-1M)
KTC = {'typical': 34.1, 'ff': 37.3, 'ss': 30.1}      # uV rms on the plate (D2 sim/d2_ktc.log)
out = []; P_ = lambda s='': (print(s, flush=True), out.append(s))
P_('D5 INPUT-REFERRED NOISE 0.5-300 Hz (ESTIMATE: analytic combination, no transient-noise run). Amplifier numbers from sim/a4c_noise.log (NOISE_B/C/D, typical flicker, ideal pseudo-R noise); FN=1 (fnoicor = 1) is the Decision-10 risk case.')
P_('  term (uV rms at the electrode)                                 typ 27     ff 85      ss -40')
rows = {}
for corner, nm in (('typical', 'typ 27'), ('ff', 'ff 85'), ('ss', 'ss -40')):
    a = A[corner]; amp = a['B']; alias = np.sqrt(max(a['D'] ** 2 - a['C'] ** 2, 0) * 299.5 / 2000)
    q = LSB / np.sqrt(12) * 1e6 / 1000 * FB            # quantisation: uV at the output / 1000
    kt = KTC[corner] / 1000 * FB
    rng = np.random.default_rng(11); c = hy.CORN[corner]; es = []
    for ch in range(5):
        d, lv, S, sup = hy.chip(rng, corner, True); v0 = 1.65 + (rng.random(4000) - 0.5) * 4 * LSB
        c0 = hy.sar(v0, lv, S + sup, None); sn = np.sqrt(c['npair'] ** 2 + 50e-6 ** 2)
        for k in range(8):
            c1 = hy.sar(v0, lv, S + sup, rng.normal(0, sn, (4000, 12))); es.append(np.mean((c1 - c0).astype(float) ** 2))
    cmp_lsb = np.sqrt(np.mean(es)); cmp_ = cmp_lsb * 0.806 * FB
    tot = np.sqrt(amp ** 2 + alias ** 2 + q ** 2 + kt ** 2 + cmp_ ** 2); tot1 = np.sqrt(a['B1'] ** 2 + alias ** 2 + q ** 2 + kt ** 2 + cmp_ ** 2)
    rows[corner] = (amp, alias, q, kt, cmp_, tot, tot1, cmp_lsb)
for i, lab in enumerate(('amplifier 0.5-300 Hz (A4c, FN=0)', 'amplifier noise above 2 kHz aliased into the band', 'ADC quantisation LSB/sqrt(12) (white, 0-2 kHz)', 'ADC kT/C (D2 34.1/37.3/30.1 uV on the plate)', 'ADC comparator (pair + 50 uV latch ESTIMATE)', 'TOTAL (FN=0)', 'TOTAL with the fnoicor = 1 amplifier (4.72/4.93/4.39 uV)')):
    P_(f'  {lab:62s} ' + ' '.join(f'{rows[c][i]:9.3f}' for c in ('typical', 'ff', 'ss')))
P_('  comparator noise as code rms (noisy - noiseless) [LSB]            ' + ' '.join(f'{rows[c][7]:9.3f}' for c in ('typical', 'ff', 'ss')))
P_('  ADC share of the total power (FN=0)                              ' + ' '.join(f'{100*(1-(rows[c][0]**2+rows[c][1]**2)/rows[c][5]**2):8.1f}%' for c in ('typical', 'ff', 'ss')))
P_('  target 2 uV: ' + ', '.join(f'{nm} {"OK" if rows[c][5] <= 2 else "MISS"} ({rows[c][5]:.3f})' for c, nm in (('typical', 'typ 27'), ('ff', 'ff 85'), ('ss', 'ss -40'))) + '; with fnoicor = 1 every corner misses (' + ', '.join(f'{rows[c][6]:.2f}' for c in ('typical', 'ff', 'ss')) + ' uV)')
open(f'{hy.ADC}/sim/d5_noise.log', 'w').write('\n'.join(out) + '\n')
