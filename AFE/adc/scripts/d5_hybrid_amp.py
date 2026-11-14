#!/usr/bin/env python3
"""D5 item 2 (HYBRID only): D4 SAR model fed with a synthetic A4c amplifier output: 1.6502 V + A sin(2 pi f t) + HD3 (A4c THD at +-0.5 mV, 12.25 Hz: 0.040 / 2.527 / 0.051 % typ/ff85/ss-40, applied as a 3rd harmonic, conservative sign/phase),
+ the item-1 end-of-acquisition settling error as a constant (0.086 / 0.114 / 0.070 LSB, sim/d5_settle.log worst case), + optional amp noise ESTIMATE (A4c NOISE_D x 1000 at the output).  N = 512, M = 3 (23.4375 Hz: 12.25 Hz is not coherent in 512 samples at 4 kS/s), 20 chips.
Not a circuit simulation of amplifier -> ADC (that run is NOT DONE)."""
import sys, os, numpy as np
H = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, H)
import d5_analyze as a, d5lib as L
LSB = a.LSB; out = []; P_ = lambda s='': (print(s, flush=True), out.append(s))
THD = {'typical': 0.040e-2, 'ff': 2.527e-2, 'ss': 0.051e-2}; SETL = {'typical': 0.086, 'ff': 0.114, 'ss': 0.070}
N = 512; M = 3; n = np.arange(N)
P_('D5 END-TO-END SNDR, HYBRID (D4 SAR model + synthetic A4c amplifier output; NOT the transistor-level amplifier->ADC run). 20 chips, mean; coherent N 512, M 3.')
for corner, nm in (('typical', 'typ 27'), ('ff', 'ff 85'), ('ss', 'ss -40')):
    for apk in (0.45, 0.10):
        v = 1.6502 + apk * np.sin(2 * np.pi * M * n / N) + apk * THD[corner] * np.sin(2 * np.pi * 3 * M * n / N + 0.5) + SETL[corner] * LSB
        s0 = a.sndr(np.round(v / LSB), M); fsx = 20 * np.log10(3.3 / (2 * apk))
        P_(f'[{nm}] amplitude {apk*1e3:.0f} mV pk at the output ({apk*1e3/1000*1e3:.0f} uV at the electrode): ideal 12-bit quantiser of the synthetic samples SNDR {s0[0]:.1f} dB THD {s0[1]:.1f} dBc')
        for lab, kw in (('HYBRID (no amp noise)', {}), ('HYBRID + D4b top-of-range plate error', dict(d4b=True)), ('HYBRID + amp noise ESTIMATE', dict(namp=1000 * a.AMPN[corner])), ('HYBRID + amp noise ESTIMATE + D4b', dict(namp=1000 * a.AMPN[corner], d4b=True))):
            rng = np.random.default_rng(5); r = np.array([a.sndr(a.convert(v, corner, rng, **kw), M) for _ in range(20)]); sn = r[:, 0].mean()
            P_(f'    {lab:40s}: SNDR {sn:.1f} dB (min {r[:,0].min():.1f}), THD {r[:,1].mean():.1f} dBc, ENOB raw {(sn-1.76)/6.02:.2f}, ENOB FS {(sn-1.76+fsx)/6.02:.2f}')
open(f'{L.ADC}/sim/d5_sndr.log', 'w').write('\n'.join(out) + '\n')
