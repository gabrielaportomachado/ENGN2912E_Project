#!/usr/bin/env python3
"""A4b corner table: one row per PVT point, from the saved logs only -> sim/a4b_corner_table.txt"""
import re, os
A = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'sim') + '/'
ORDER = [(k, t) for k in ('typical', 'ff', 'ss') for t in ('-40', '27', '85')]
def blocks(path):
    d, cur = {}, None
    for l in open(path):
        if l.startswith('###'): cur = l[4:].strip(); d[cur] = []
        elif cur: d[cur].append(l.strip())
    return d
def kv(lines, tag=None):
    out = {}
    for l in lines:
        if tag is None or l.startswith(tag):
            out.update({k: float(v) for k, v in re.findall(r'(\w+)=(-?\d+\.?\d*(?:[eE][-+]?\d+)?)', l)})
    return out
ac, nz, op, ps, lp = (blocks(A + f'a4b_{n}.log') for n in ('ac', 'noise', 'op', 'psrr', 'loop'))
thd = {}
for l in open(A + 'a4b_thd.log'):
    p = l.split()
    if len(p) >= 12 and p[0] in ('typical', 'ff', 'ss') and p[1].lstrip('-').isdigit() and float(p[3]) == 0.5:
        thd[(p[0], p[1], float(p[2]))] = (float(p[5]), float(p[8]), float(p[9]))
adc = {}
for l in open(A + 'a4b_adc.log'):
    p = l.split()
    if len(p) >= 12 and p[0] in ('typical', 'ff', 'ss') and p[2] in ('s+0.5m', 's-0.5m'):
        adc[(p[0], p[1], p[2])] = float(p[7])        # err@11.05 us
fs = {}
for l in open(A + 'a4b_fscharge.log'):
    p = l.split()
    if len(p) >= 15 and p[0] in ('typical', 'ff', 'ss') and p[2] == '100n':
        fs[(p[0], p[1])] = (float(p[4]), float(p[5]))
out = ['# A4b corner table (typical flicker, VDD 3.3 V, VOUT_CM 1.65 V, VCM_IN 1.65 V, VTT2 0.9 V, native-Vt follower).  Every column comes from a saved log in sim/ (a4b_ac, a4b_noise, a4b_op, a4b_psrr, a4b_loop, a4b_thd, a4b_adc, a4b_fscharge).',
       'corner    T  gain_dB f_lo_Hz f_hi_Hz  noise_uV  noise_fn1  Isup_uA  PSRR50  loopPM  THD12@0.5mV_% THD300_% ymax12 ymin12  ADC_err(-0.5V)@11us_LSB  ADC_err(+0.5V)  fs100ns_dout_mV fs100ns_dv1_mV']
for k, t in ORDER:
    a = kv(ac.get(f'ac_{k}_{t}', [])); n0 = kv(nz.get(f'noise_{k}_{t}_fn0', []), 'NOISE_B'); n1 = kv(nz.get(f'noise_{k}_{t}_fn1', []), 'NOISE_B')
    o = kv(op.get(f'op_{k}_{t}', []), 'OPSUM'); p = kv(ps.get(f'psrr_{k}_{t}', [])); l = kv(lp.get(f'loop_{k}_{t}', []))
    t12 = thd.get((k, t, 12.25), (float('nan'),) * 3); t300 = thd.get((k, t, 300.0), (float('nan'),) * 3)
    f = fs.get((k, t))
    out.append(f'{k:7s} {t:>4s}  {a.get("g_mid_dB", float("nan")):7.3f} {a.get("f_lo_Hz", float("nan")):7.3f} {a.get("f_hi_Hz", float("nan")):7.1f}  {n0.get("vn_in_mid_V", float("nan"))*1e6:8.3f}  {n1.get("vn_in_mid_V", float("nan"))*1e6:8.3f}  {o.get("i_supply_A", float("nan"))*1e6:7.1f}  {p.get("vdd2out_50Hz", float("nan")):6.3f}  {l.get("pm_deg", float("nan")):6.1f}  {t12[0]:9.3f}  {t300[0]:8.3f} {t12[1]:7.3f} {t12[2]:7.3f}  {adc.get((k, t, "s-0.5m"), float("nan")):10.3f}  {adc.get((k, t, "s+0.5m"), float("nan")):14.3f}  ' + (f'{f[0]:9.2f} {f[1]:9.2f}' if f else '       n/a       n/a'))
open(A + 'a4b_corner_table.txt', 'w').write('\n'.join(out) + '\n'); print('\n'.join(out))
