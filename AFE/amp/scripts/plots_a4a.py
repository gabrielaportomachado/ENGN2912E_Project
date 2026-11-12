#!/usr/bin/env python3
"""A4a figures -> figs/a4a_*.png, from sim/*.csv and sim/a4a_noise.log only (never *.raw).  python3 scripts/plots_a4a.py"""
import os, re
import numpy as np
import matplotlib; matplotlib.use('Agg')
import matplotlib.pyplot as plt
AMP = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); SIM = AMP + '/sim'; FIG = AMP + '/figs'
col = {'typical': 'C0', 'ff': 'C3', 'ss': 'C2'}; ls = {'-40': ':', '27': '-', '85': '--'}
fig, ax = plt.subplots(figsize=(7, 4.4))
for k in ('typical', 'ff', 'ss'):
    for T in ('-40', '27', '85'):
        a = np.loadtxt(f'{SIM}/a4a_bode_{k}_{T}.csv'); ax.semilogx(a[:, 0], a[:, 1], color=col[k], ls=ls[T], lw=1.1, label=f'{k} {T}C')
a = np.loadtxt(f'{SIM}/a4a_bode_typical_27.csv'); ax.semilogx(a[:, 2], a[:, 3], 'k', lw=.8, label='stage 1 only (typ 27C)')
ax.axvspan(0.5, 300, color='gray', alpha=.10); ax.axhspan(59, 61, color='gray', alpha=.15)
ax.set_xlim(1e-2, 1e6); ax.set_ylim(0, 64); ax.set_xlabel('frequency (Hz)'); ax.set_ylabel('channel gain (dB)'); ax.grid(True, which='both', alpha=.3)
ax.set_title('A4a channel gain, 9 PVT (shaded: 0.5-300 Hz band, 60 +-1 dB window)', fontsize=9); ax.legend(fontsize=6, ncol=2, loc='lower center')
fig.tight_layout(); fig.savefig(FIG + '/a4a_gain_9pvt.png', dpi=130); plt.close(fig)
# noise bars
txt = open(SIM + '/a4a_noise.log').read().split('### ')[1:]
val = {}
for blk in txt:
    lab = blk.splitlines()[0]; m = re.search(r'NOISE_B_0p5_300 .*?vn_in_mid_V=(\S+)', blk)
    val[lab] = float(m.group(1)) * 1e6
labs = [f'{k}\n{T}C' for k in ('typical', 'ff', 'ss') for T in ('-40', '27', '85')]
f0 = [val[f'noise_{k}_{T}_fn0'] for k in ('typical', 'ff', 'ss') for T in ('-40', '27', '85')]
f1 = [val[f'noise_{k}_{T}_fn1'] for k in ('typical', 'ff', 'ss') for T in ('-40', '27', '85')]
fig, ax = plt.subplots(figsize=(7, 3.8)); x = np.arange(9)
ax.bar(x - .2, f0, .4, label='typical flicker (fnoicor=0)'); ax.bar(x + .2, f1, .4, label='worst-case flicker (fnoicor=1)', color='C1')
ax.axhline(2, color='r', lw=1); ax.text(8.4, 2.08, '2 uV target', color='r', fontsize=7, ha='right')
ax.set_xticks(x); ax.set_xticklabels(labs, fontsize=7); ax.set_ylabel('input-referred noise, 0.5-300 Hz (uV rms)')
ax.set_title('A4a channel noise (integrated output noise / midband gain; IDEAL R in both stages)', fontsize=9); ax.legend(fontsize=7); ax.grid(True, axis='y', alpha=.3)
fig.tight_layout(); fig.savefig(FIG + '/a4a_noise_9pvt.png', dpi=130); plt.close(fig)
print('wrote figs/a4a_gain_9pvt.png, figs/a4a_noise_9pvt.png')
