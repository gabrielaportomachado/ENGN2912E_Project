#!/usr/bin/env python3
"""I2 analysis of sim/i2_replay.log (lines from i2_replay.py).  For each variant != ideal, corner:
  delta_k  = d_ev_k(variant) - d_ev_k(ideal) [LSB], d = (plate - ref node) 1.5 ns after the comparator rise (includes the comparator's evaluate shift, identical in both runs)
  offset   = mean over vins of delta_12 (the final trial: the margin is within a few LSB for every code = the fixed code shift) and its spread over vins
  rel      = for the vins placed 0.3 LSB above a code level c (MSB, MSB-1, MSB-2 transitions): delta at the trial that tests c (margin ~0.3 LSB) minus the corner's offset = the threshold error of THAT bit beyond the fixed offset (INL/DNL-type)
  e_ref    = reference-node change from just before the plate switch opens to the clock rise (pre) and 1.5 ns after it (ev), [LSB]; step = node step 20 ns after the plate switch opens
usage: python3 i2_analyze.py sim/i2_replay.log"""
import sys, re, numpy as np
rows = {}
for ln in open(sys.argv[1]):
    if not ln.startswith('I2 '): continue
    m = re.match(r'I2 (\S+) (\S+) (\S+)C VH (\S+) VR (\S+) vin (\S+) code (\d+) \| d_ev\[LSB\] (.*?) \| e_ref_pre\[LSB\] (.*?) \| e_ref_ev (.*?) \| dec (\d+) ideal (\d+) tri (\S+) \| ref\(open\)-1.65V (\S+) LSB, step in 20 ns (\S+) LSB', ln)
    if not m: continue
    var, corner, temp, vh, vr, vin, code = m.group(1), m.group(2), m.group(3), m.group(4), m.group(5), float(m.group(6)), int(m.group(7))
    f = lambda g: np.array([float(x) for x in g.split()])
    key = (var, vh, vr if var.startswith('cref') else '-', corner); rows.setdefault(key, {})[round(vin, 5)] = dict(d=f(m.group(8)), pre=f(m.group(9)), ev=f(m.group(10)), dec=m.group(11), seq=m.group(12), tri=[int(x) for x in m.group(13).split(',')], vo=float(m.group(14)), step=float(m.group(15)), code=code)
ide = {k[3]: v for k, v in rows.items() if k[0] == 'ideal'}
LV = {1024: 0.8252417, 1536: 1.23774, 2048: 1.6502417, 2560: 2.06274}
print('variant        VH   VR   corner   | offset d12 mean (spread over vins) [LSB] | threshold error beyond offset at bit-transition vins [LSB] (MSB 2048 / MSB-1 1024 / MSB-2 1536,2560) | worst |delta_k - delta_12| trials 9-12 | e_ref pre max / ev(12) | step at open | decisions==ideal')
for k, v in sorted(rows.items()):
    var, vh, vr, corner = k
    if var == 'ideal': continue
    I = ide[corner]; dl = {vin: v[vin]['d'] - I[vin]['d'] for vin in v if vin in I}
    off = np.array([x[11] for x in dl.values()]); offm = off.mean()
    rel = {}
    for vin in dl:
        for c, lv in LV.items():
            if abs(vin - lv) < 2e-6: kk = v[vin]['tri'].index(c); rel[c] = dl[vin][kk] - offm
    late = max(np.abs(x[8:] - x[11]).max() for x in dl.values())
    pre = max(np.abs(x['pre']).max() for x in v.values()); ev12 = np.mean([x['ev'][11] for x in v.values()])
    stp = np.mean([x['step'] for x in v.values()]); okdec = all(x['dec'] == x['seq'] for x in v.values())
    print(f'{var:8s} {vh:>6s} {vr:>5s} {corner:8s} | {offm:+7.2f} ({off.max()-off.min():.2f}) | ' + ' '.join(f'{c}:{rel[c]:+.2f}' for c in sorted(rel)) + f' | {late:.2f} | {pre:.2f} / {ev12:+.2f} | {stp:+.3f} | {okdec}')
