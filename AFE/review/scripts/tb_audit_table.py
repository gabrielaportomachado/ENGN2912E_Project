#!/usr/bin/env python3
"""AUDIT step 4: compact table of the numbers measured by tb_audit.v (worst over all scenario blocks of the `main` run) -> appended to sim/tb_audit_summary.log"""
import re, os, glob, sys
R = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
rows = []
for f in sorted(glob.glob(os.path.join(R, 'sim', 'tb_audit_*_main.log'))):
    t = open(f).read()
    name = os.path.basename(f)[9:-9]
    g = lambda pat, fn, d=float('nan'): (fn([float(x) for x in re.findall(pat, t)]) if re.findall(pat, t) else d)
    r = dict(name=name,
             dac2ck=g(r'DAC edge -> comparator clock: min ([\d.]+) ns', min), tset=g(r'\(TSET ([\d.]+) ns\)', min),
             end2edge=g(r'window end -> next SCLK edge: min ([\d.]+) ns', min), w=g(r'window width min ([\d.]+) ns', min), tdec=g(r'TDEC ([\d.]+) ns', min),
             rst2tg=g(r'rst_sw -> tg_on min ([\d.]+) ns', min), cs2rst=g(r'CS fall -> rst_sw [\d.]+ \.\. ([\d.]+) ns', max), spread=g(r'spread over the 8 channels ([\d.]+) ns', max),
             dout=g(r'DOUT: latest change ([\d.]+) ns', max), dsu=g(r'setup to the host sampling edge min ([\d.]+) ns', min),
             cb=g(r'crowbar overlaps .*?longest ([\d.]+) ns', max, 0.0), ncb=g(r'crowbar overlaps \(PMOS and NMOS gate of one bit both on\): (\d+) events', sum, 0.0),
             ov=g(r'overlap on the aborted frames: \d+ events, longest ([\d.]+) ns', max), tacq7=g(r'T_ACQ \(sampling TG closed before the next sample\) ADC0 [\d.]+ us, ADC7 ([\d.]+) us', min),
             hold7=g(r'plate hold time \(sample -> last decision\) ADC7 ([\d.]+) us', max), nass=len(re.findall(r'^ASSERT', t, flags=re.M)), nfail=len(re.findall(r'^ASSERT \S+ FAIL', t, flags=re.M)),
             fails=' '.join(sorted(set(re.findall(r'^ASSERT (\S+) FAIL', t, flags=re.M)))))
    rows.append(r)
out = open(os.path.join(R, 'sim', 'tb_audit_summary.log'), 'a')
P = lambda s: (print(s), print(s, file=out))
P('\nMEASURED NUMBERS (worst over the `main` scenario; ns unless stated).  rtl_* = RTL + per-corner cell models + STA port delays; gls_* = delay-annotated hardened netlist (gen_gl.py)')
P('%-24s %7s %6s | %8s %6s %5s | %6s %6s %6s | %5s %7s | %6s %5s %6s | %8s %7s | %s' % ('build_corner_f', 'DAC->ck', 'TSET', 'end->edg', 'W', 'TDEC', 'rst->tg', 'CS->rst', 'spread', 'DOUT', 'DOUTsu', 'crowb', 'n', 'abort', 'TACQ7_us', 'hold_us', 'failing assertions'))
for r in rows:
    P('%-24s %7.2f %6.1f | %8.2f %6.2f %5.2f | %6.2f %6.2f %6.3f | %5.2f %7.2f | %6.3f %5d %6.2f | %8.2f %7.2f | %s' % (r['name'], r['dac2ck'], r['tset'], r['end2edge'], r['w'], r['tdec'], r['rst2tg'], r['cs2rst'], r['spread'],
                                                                                                                  r['dout'], r['dsu'], r['cb'], int(r['ncb']), r['ov'], r['tacq7'], r['hold7'], r['fails']))
