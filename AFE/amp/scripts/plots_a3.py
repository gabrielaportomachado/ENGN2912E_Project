#!/usr/bin/env python3
"""A3 figures -> figs/a3_*.png, from sim/*.csv only (never *.raw).  Run from anywhere: python3 scripts/plots_a3.py"""
import os, csv
import numpy as np
import matplotlib; matplotlib.use('Agg')
import matplotlib.pyplot as plt
AMP = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); SIM = AMP + '/sim'; FIG = AMP + '/figs'
def bode(name):
    a = np.loadtxt(f'{SIM}/a3_bode_{name}.csv'); return a[:, 0], a[:, 1], a[:, 3]
col = {'typical': 'C0', 'ff': 'C3', 'ss': 'C2'}
# ---- 1. OTA open-loop A(s) and real loop gain T(s)
fig, (a1, a2) = plt.subplots(2, 1, figsize=(6.4, 6), sharex=True)
f, g, p = bode('ol_typical_27'); a1.semilogx(f, g, 'k', lw=1.4, label='A(s): open loop, typ 27C (feedback factor 1)')
for k in ('typical', 'ff', 'ss'):
    f, g, p = bode(f'loop_{k}_27'); a1.semilogx(f, g, color=col[k], label=f'T(s): real loop, {k} 27C')
    a2.semilogx(f, p, color=col[k])
f, g, p = bode('ol_typical_27'); a2.semilogx(f, p, 'k', lw=1.4)
a1.axhline(0, color='gray', lw=.6); a2.axhline(-180, color='gray', lw=.6)
a1.set_ylabel('magnitude (dB)'); a2.set_ylabel('phase (deg)'); a2.set_xlabel('frequency (Hz)')
a1.set_xlim(1e-2, 1e9); a1.set_ylim(-60, 130); a1.grid(True, which='both', alpha=.3); a2.grid(True, which='both', alpha=.3)
a1.legend(fontsize=7); a1.set_title('Stage-1 OTA: A(s) and Tian loop gain T(s) (PM 70-76 deg, A(s) alone is not unity-gain stable)', fontsize=8)
fig.tight_layout(); fig.savefig(FIG + '/a3_ota_bode.png', dpi=130); plt.close(fig)
# ---- 2. closed-loop gain
fig, ax = plt.subplots(figsize=(6.4, 4))
for c in ('typical_-40', 'typical_27', 'typical_85', 'ff_27', 'ss_27'):
    f, g, p = bode('cl_' + c); k = c.split('_')[0]
    ax.semilogx(f, g, color=col[k], ls={'-40': ':', '27': '-', '85': '--'}[c.split('_')[1]], label=c.replace('_', ' ') + 'C')
ax.axvline(0.5, color='k', lw=.6); ax.axvline(300, color='k', lw=.6); ax.axhline(37, color='gray', lw=.6)
ax.set_xlim(1e-2, 1e7); ax.set_ylim(0, 42); ax.set_xlabel('frequency (Hz)'); ax.set_ylabel('stage-1 gain (dB)')
ax.set_title('Stage 1 closed loop, real pseudo-R (vt=+0.2 V IDEAL), Randles source; lines: 0.5 Hz, 300 Hz', fontsize=8)
ax.grid(True, which='both', alpha=.3); ax.legend(fontsize=7); fig.tight_layout(); fig.savefig(FIG + '/a3_cl_gain.png', dpi=130); plt.close(fig)
# ---- 3. noise vs R (Decision 7/8)
rs = np.loadtxt(SIM + '/a3_rsweep.csv', skiprows=1); R = rs[:, 0] / 1e12
fig, ax = plt.subplots(figsize=(6.4, 4.3))
ax.semilogx(R, rs[:, 3] * 1e6, 'ko-', label='total: OTA + R + electrodes (IDEAL RESISTOR, typ flicker)')
ax.semilogx(R, rs[:, 5] * 1e6, 's--', color='C1', label='OTA + electrodes (R noiseless)')
ax.semilogx(R, rs[:, 6] * 1e6, '^--', color='C2', label='feedback R only (quadrature difference)')
ax.axhline(2.0, color='r', lw=.8); ax.text(0.55, 2.03, '2 uV target', color='r', fontsize=7)
nz = [r.split() for r in open(SIM + '/a3_noise.csv')][1:]
ax.plot([float(r[2]) / 1e12 for r in nz], [float(r[3]) * 1e6 for r in nz], 'x', color='C3', ms=7, label='9 PVT points at the device R0 (corner/T)')
ax.set_xlabel('feedback resistance R (TOhm), Cf = 200 fF;  f_lo = 0.16 Hz x (5 TOhm / R)')
ax.set_ylabel('input-referred noise 0.5-300 Hz (uV rms)'); ax.grid(True, which='both', alpha=.3); ax.legend(fontsize=6.5)
ax.set_title('Stage-1 noise vs feedback resistance (fnoicor=1: 4.6-4.8 uV for every R, not plotted)', fontsize=8)
fig.tight_layout(); fig.savefig(FIG + '/a3_noise_vs_R.png', dpi=130); plt.close(fig)
# ---- 4. recovery vs R
fig, ax = plt.subplots(figsize=(6.4, 4.3))
ax.loglog(R, rs[:, 7], 'o-', label='ideal R, 1 mV step (100 mV excursion)')
ax.loglog(R, rs[:, 11], 's-', label='ideal R, 10 mV step (1 V excursion)')
rc = [r.split() for r in open(SIM + '/a3_rec.csv')][1:]
mk = {'1m': ('o', 'C0'), '5m': ('d', 'C4'), '10m': ('s', 'C1')}
for r in rc:
    if r[2] in mk and r[0] == 'typical' and r[1] == '27':
        ax.plot(5.24, float(r[6]), mk[r[2]][0], mfc='none', color='k', ms=9)
        if r[2] != '5m': ax.text(6.0, float(r[6]) * (1.0 if r[2] == '1m' else 1.12), 'device ' + ('1 mV' if r[2] == '1m' else '5 & 10 mV'), fontsize=6.5)
ax.set_xlabel('feedback R (TOhm); open symbols: simulated pseudo-R, typ 27C, at R0')
ax.set_ylabel('time to settle within 10 mV of final value (s)'); ax.grid(True, which='both', alpha=.3); ax.legend(fontsize=7)
ax.set_title('Stage-1 recovery after a REC electrode DC step (time to 10 mV of final, stage-1 output)', fontsize=8)
fig.tight_layout(); fig.savefig(FIG + '/a3_recovery.png', dpi=130); plt.close(fig)
print('wrote figs/a3_ota_bode.png a3_cl_gain.png a3_noise_vs_R.png a3_recovery.png')
