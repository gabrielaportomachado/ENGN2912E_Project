#!/usr/bin/env python3
"""A4b: (c) ADC VDD-noise budget at the measured supply gain, (d) stage-1 saturation margins at VCM_IN = 1.65 V.  Reads sim/a4b_psrr.log and sim/a4b_op.log."""
import re, os
A = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'sim') + '/'
LSB = 3.3 / 4096
def parse(path):
    d, cur = {}, None
    for l in open(path):
        if l.startswith('###'): cur = l[4:].strip(); d[cur] = []
        elif cur: d[cur].append(l.strip())
    return d
ps = parse(A + 'a4b_psrr.log'); out = []
out.append('# A4b (c): ADC VDD-noise budget.  VREF = VDD (Decision 17): the code error of a VDD disturbance dVDD is |A - 0.5| x dVDD / LSB with A = |v(out)/v(vdd)| (A4b, 9 PVT, sim/a4b_psrr.log); 0.5 is the ratiometric ideal.')
out.append('# Allocation 0.2 LSB rms (AFE/adc/PLAN.md, D0).  dVDD_max = 0.2 LSB x 0.806 mV / |A - 0.5|.  Bands: DC and 50/60 Hz and 300 Hz are inside 0.5-300 Hz; 1 kHz and 10 kHz are out of band but alias into it at 4 kS/s (no anti-alias filter, Decision 23).')
out.append('band     A_min..A_max (9 PVT)   worst |A-0.5|   LSB per mV of VDD   dVDD_max for 0.2 LSB [mV rms]   (A4a, VCM_IN 1.5: worst in-band |A-0.5| 0.53)')
for key, lab in (('dc', 'DC'), ('50Hz', '50 Hz'), ('60Hz', '60 Hz'), ('300Hz', '300 Hz'), ('1k', '1 kHz'), ('10k', '10 kHz')):
    v = [float(re.search(rf'vdd2out_{key}=(\S+)', ' '.join(l)).group(1)) for l in ps.values()]
    w = max(abs(x - 0.5) for x in v)
    out.append(f'{lab:7s}  {min(v):.3f}..{max(v):.3f}          {w:.3f}           {w*1e-3/LSB:6.3f}              {0.2*LSB*1e3/w:8.2f}')
open(A + 'a4b_vddbudget.log', 'w').write('\n'.join(out) + '\n'); print('\n'.join(out))
op = parse(A + 'a4b_op.log'); dev = {}
for k, ls in op.items():
    for l in ls:
        if l.startswith('OPDEV xch.xs1.xota.') or l.startswith('OPDEV xch.xsink1'):
            nm = l.split()[1]; kv = dict(re.findall(r'(\w+)=(-?\d+\.?\d*(?:[eE][-+]?\d+)?)', l))
            dev.setdefault(nm, []).append((float(kv['margin_V']), k, float(kv['vgs_V']), float(kv['vds_V']), float(kv['id_A'])))
out = ['# A4b (d): stage-1 OTA saturation margins |Vds| - |Vdsat| at VCM_IN = 1.65 V (criterion >= 0.05 V), 9 PVT, DC operating point (sim/a4b_op.log)',
       'device                    min margin [V]  at corner             max margin [V]   Id range [uA]']
for nm in sorted(dev):
    m = sorted(dev[nm])
    out.append(f'{nm:25s} {m[0][0]:8.3f}      {m[0][1]:20s} {m[-1][0]:8.3f}        {min(x[4] for x in m)*1e6:.1f}..{max(x[4] for x in m)*1e6:.1f}')
out.append(f'stage-1 minimum over devices and corners: {min(min(x[0] for x in v) for v in dev.values()):.3f} V')
open(A + 'a4b_stage1_margin.log', 'w').write('\n'.join(out) + '\n'); print('\n'.join(out))
