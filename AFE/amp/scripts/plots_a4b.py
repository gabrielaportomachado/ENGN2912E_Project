#!/usr/bin/env python3
"""A4b figures (figs/a4b_*.png) from the CSVs of scripts/run_a4b.sh (/tmp/a4brun/<case>/).  Cases that were not run are skipped."""
import os, sys, glob, math, re
import numpy as np
import matplotlib; matplotlib.use('Agg')
import matplotlib.pyplot as plt
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import a4b_lib as L
AMP = os.path.abspath(os.path.join(os.path.dirname(__file__), '..')); RUN = '/tmp/a4brun'; F = AMP + '/figs/'
LSB = 3.3 / 4096
ORDER = ['typical_-40', 'typical_27', 'typical_85', 'ff_-40', 'ff_27', 'ff_85', 'ss_-40', 'ss_27', 'ss_85']
def num(s): return float(s.replace('m', 'e-3').replace('u', 'e-6').replace('n', 'e-9'))
def ld(cs, lab): return L.load(f'{RUN}/{cs}/{lab}.csv')

def thd():
    if not glob.glob(f'{RUN}/thd/*.csv'): return
    fig, ax = plt.subplots(1, 2, figsize=(10, 4))
    for i, (f, fl) in enumerate(((12.25, 'f12'), (300, 'f300'))):
        vds = sorted({re.search(r'_f\d+_([\d.]+m)\.csv', x).group(1) for x in glob.glob(f'{RUN}/thd/*_{fl}_*.csv')}, key=num)
        for k in ORDER:
            y = []
            for vd in vds:
                d = ld('thd', f'{k}_{fl}_{vd}'); a1, thd, mean, h = L.harmonics(d['time'], d['out'], f, 4); y.append(thd * 100)
            ax[i].semilogy([num(v) * 1e3 for v in vds], y, 'o-', lw=1, ms=3, label=k.replace('_', ' C ' if False else ' '))
        ax[i].axhline(1, color='k', ls='--', lw=0.8); ax[i].axvline(0.5, color='gray', ls=':', lw=0.8)
        ax[i].set_xlabel('input amplitude VD [mV pk]'); ax[i].set_ylabel('THD [%]'); ax[i].set_title(f'{f} Hz (1 % line dashed, full scale 0.5 mV dotted)'); ax[i].grid(alpha=0.3)
    ax[0].legend(fontsize=6, ncol=2)
    fig.tight_layout(); fig.savefig(F + 'a4b_thd.png', dpi=130); plt.close(fig)

def adc():
    if not glob.glob(f'{RUN}/adc/*.csv'): return
    fig, ax = plt.subplots(1, 2, figsize=(10, 4))
    for k, col in (('typical_27', 'C0'), ('ss_-40', 'C3'), ('ff_-40', 'C2')):
        for sg, ls in (('+', '-'), ('-', '--')):
            p = f'{RUN}/adc/{k}_s{sg}0.5m.csv'
            if not os.path.exists(p): continue
            d = ld('adc', f'{k}_s{sg}0.5m'); t = (d['time'] - 2e-3) * 1e6; vf = np.interp(2e-3 - 100e-9, d['time'], d['out'])
            ax[0].plot(t, (d['cs'] - vf) / LSB, ls, color=col, lw=1, label=f'{k} step {sg}0.5 V'); ax[1].plot(t, (d['cs'] - vf) / LSB, ls, color=col, lw=1)
    ax[0].set_xlim(0, 40); ax[0].set_xlabel('time after connect [us]'); ax[0].set_ylabel('v(C_s) - v(out)_rest [LSB]'); ax[0].legend(fontsize=6); ax[0].grid(alpha=0.3)
    ax[1].set_xlim(0, 40); ax[1].set_ylim(-3, 1); ax[1].axvline(11.05, color='k', ls=':'); ax[1].axhspan(-0.5, 0.5, color='g', alpha=0.15); ax[1].set_xlabel('time after connect [us] (zoom, +-0.5 LSB band, T_ACQ 11.05 us dotted)'); ax[1].grid(alpha=0.3)
    fig.tight_layout(); fig.savefig(F + 'a4b_adc_settle.png', dpi=130); plt.close(fig)

def fscharge():
    if not glob.glob(f'{RUN}/fscharge/*.csv'): return
    fig, ax = plt.subplots(1, 2, figsize=(10, 4))
    for k, col in (('typical_27', 'C0'), ('ss_-40', 'C3'), ('ff_85', 'C2')):
        for w, ls in (('10u', ':'), ('1m', '-'), ('100m', '--')):
            p = f'{RUN}/fscharge/{k}_w{w}.csv'
            if not os.path.exists(p): continue
            d = ld('fscharge', f'{k}_w{w}'); t = d['time']; pre = np.interp(0.01 - 1e-6, t, d['out']); trel = 0.01 + 20e-9 + num(w)
            ax[0].plot((t - trel) * 1e3, (d['out'] - pre) * 1e3, ls, color=col, lw=1, label=f'{k} W={w}s')
            ax[1].plot(t - trel, (d['out'] - pre) * 1e3, ls, color=col, lw=1)
    ax[0].set_xlim(-0.02, 5); ax[0].set_xlabel('time after fs release [ms]'); ax[0].set_ylabel('v(out) - v(out)_before [mV]'); ax[0].legend(fontsize=6); ax[0].grid(alpha=0.3)
    ax[1].set_xlim(0, 12); ax[1].set_xlabel('time after fs release [s]'); ax[1].grid(alpha=0.3)
    fig.tight_layout(); fig.savefig(F + 'a4b_fs_residual.png', dpi=130); plt.close(fig)

def recov():
    if not glob.glob(f'{RUN}/recov/typical_27_os1m_w0.csv'): return
    fig, ax = plt.subplots(1, 2, figsize=(10, 4))
    for a, col in (('1m', 'C0'), ('10m', 'C1'), ('100m', 'C3')):
        p = f'{RUN}/recov/typical_27_os{a}_w0.csv'
        if not os.path.exists(p): continue
        d = ld('recov', f'typical_27_os{a}_w0')
        ax[0].plot(d['time'] - 0.1, d['out'], color=col, lw=1, label=f'{a}V offset step'.replace('mV', ' mV')); ax[1].plot(d['time'] - 0.1, (d['out'] - 1.65) * 1e3, color=col, lw=1)
    ax[0].set_xscale('symlog', linthresh=0.01); ax[0].set_xlim(0, 1500); ax[0].set_xlabel('time after the REC offset step [s] (typical 27 C, no fast-settle)'); ax[0].set_ylabel('v(out) [V]'); ax[0].legend(fontsize=7); ax[0].grid(alpha=0.3)
    ax[1].set_xlim(0, 80); ax[1].set_ylim(-30, 30); ax[1].set_xlabel('same, zoom (mV around 1.65 V)'); ax[1].grid(alpha=0.3)
    fig.tight_layout(); fig.savefig(F + 'a4b_recovery.png', dpi=130); plt.close(fig)

def pwrup():
    if not glob.glob(f'{RUN}/pwrup/*_pu1m_fs*.csv'): return
    fig, ax = plt.subplots(1, 3, figsize=(13, 4))
    for k, col in (('typical_27', 'C0'), ('ss_-40', 'C3'), ('ff_85', 'C2')):
        for fs, ls in (('0', '-'), ('1', '--')):
            p = f'{RUN}/pwrup/{k}_pu1m_fs{fs}.csv'
            if not os.path.exists(p): continue
            d = ld('pwrup', f'{k}_pu1m_fs{fs}'); t = d['time']
            ax[0].plot(t * 1e3, d['idm'] * 1e6, ls, color=col, lw=1, label=f'{k} fs{fs}'); ax[1].plot(t * 1e3, d['idb1'] * 1e6, ls, color=col, lw=1)
            ax[2].plot(t, d['out'], ls, color=col, lw=1)
    ax[0].set_xlim(0, 5); ax[0].set_xlabel('t [ms]'); ax[0].set_ylabel('master Mn1 current [uA]'); ax[0].legend(fontsize=6); ax[0].grid(alpha=0.3)
    ax[1].set_xlim(0, 5); ax[1].set_xlabel('t [ms]'); ax[1].set_ylabel('OTA1 IBIAS sink [uA]'); ax[1].grid(alpha=0.3)
    ax[2].set_xscale('symlog', linthresh=1e-3); ax[2].set_xlabel('t [s]'); ax[2].set_ylabel('v(out) [V]'); ax[2].grid(alpha=0.3)
    fig.tight_layout(); fig.savefig(F + 'a4b_powerup.png', dpi=130); plt.close(fig)

def fsrelease():
    need = [f'{RUN}/fscharge/typical_27_w{w}.csv' for w in ('100n', '300n', '100u')]
    if not all(os.path.exists(x) for x in need): return
    fig, ax = plt.subplots(1, 3, figsize=(14, 4))
    d = ld('fscharge', 'typical_27_w100u'); t0 = 0.01; t = (d['time'] - t0) * 1e6
    ax[0].plot(t, d['v1'], lw=0.8, label='v1 (stage-1 output)'); ax[0].plot(t, d['vn1'], lw=0.8, label='vn1 (summing node)')
    ax[0].set_xlim(-1, 110); ax[0].set_xlabel('time after fs assertion [us] (100 us pulse)'); ax[0].set_ylabel('V'); ax[0].legend(fontsize=7); ax[0].set_title('fs closed: OTA1 unity-gain follower oscillates (period 1.8 us)', fontsize=8); ax[0].grid(alpha=0.3)
    for w, col in (('100n', 'C0'), ('300n', 'C1')):
        d = ld('fscharge', f'typical_27_w{w}'); t = (d['time'] - t0) * 1e6; trel = 0.02 + float(w[:-1]) * 1e-3
        ax[1].plot(t, d['v1'], color=col, lw=0.9, label=f'{w}s pulse'); 
    ax[1].set_xlim(-0.5, 5); ax[1].set_ylim(1.6, 1.7); ax[1].set_xlabel('time [us]'); ax[1].set_ylabel('v1 [V]'); ax[1].legend(fontsize=7); ax[1].set_title('short pulses: no oscillation', fontsize=8); ax[1].grid(alpha=0.3)
    for w, col in (('100n', 'C0'), ('300n', 'C1')):
        d = ld('fscharge', f'typical_27_w{w}'); pre = np.interp(t0 - 1e-6, d['time'], d['out'])
        ax[2].plot(d['time'] - t0, (d['out'] - pre) * 1e3, color=col, lw=1, label=f'{w}s pulse')
    ax[2].set_xlim(0, 8); ax[2].set_ylim(-12, 10); ax[2].axhspan(-1, 1, color='g', alpha=0.15); ax[2].set_xlabel('time after the pulse [s]'); ax[2].set_ylabel('v(out) - v(out)_before [mV]'); ax[2].legend(fontsize=7); ax[2].grid(alpha=0.3)
    fig.tight_layout(); fig.savefig(F + 'a4b_fs_release.png', dpi=130); plt.close(fig)

if __name__ == '__main__':
    for f in (thd, adc, fscharge, recov, pwrup, fsrelease):
        f()
    print('figs:', sorted(os.path.basename(x) for x in glob.glob(F + 'a4b_*.png')))
