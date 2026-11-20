#!/usr/bin/env python3
"""sta_taps.py (LP kit, for L1d -> L1b): the comparator-clock timing of the hardened afe_dig in the form tb_adc_timing.py --sta reads.
usage: python3 AFE/dig/scripts/sta_taps.py [AFE/dig/reports/sta_audit_dig.log] [AFE/dig/reports/sta_taps.json]
From section 2 (SUMMARY PER CORNER, nom SPEF) and section 3 (SAMPLING) of the sta_audit.py log: T0 = comparator-clock rise of ADC 0, DL = Delta, W = window, arr = latest gp/gn arrival,
dtg = tg_on - rst_sw (worst), all in seconds, after the SCLK edge at the macro pin (the same definitions as AFE/review/scripts/mixcorner.py for the D3 macro)."""
import re, sys, json, os
D = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
src = sys.argv[1] if len(sys.argv) > 1 else os.path.join(D, 'reports', 'sta_audit_dig.log')
dst = sys.argv[2] if len(sys.argv) > 2 else os.path.join(D, 'reports', 'sta_taps.json')
txt = open(src).read()
KEY = {'ff_n40C_3v60': 'a_ff_n40', 'ff_125C_3v60': 'a_ff_125', 'tt_025C_3v30': 'a_tt', 'ss_125C_3v00': 'a_ss_125', 'ss_n40C_3v00': 'a_ss_n40'}
out = {}
for c, k in KEY.items():
    m = re.search(r'^\s+%s\s+([\d.]+)\s+([\d.]+)\s+([\d.]+)\s+[\d.]+\s+[\d.]+\s+[\d.]+\s+[\d.]+\s+[\d.]+\s+([\d.]+)\s+[\d.]+\s+[\d.]+\s*$' % c, txt, re.M)
    s = re.search(r'^\s+%s\s+[\d.]+ \.\. [\d.]+\s+[\d.]+ \.\. [\d.]+\s+[\d.]+ \.\. [\d.]+\s+([\d.]+)\s*$' % c, txt, re.M)
    if not (m and s):
        sys.exit('sta_taps.py: corner %s not found in %s' % (c, src))
    T0, DL, W, arr = [float(x) * 1e-9 for x in m.groups()]
    out[k] = dict(T0=T0, DL=DL, W=W, arr=arr, dtg=float(s.group(1)) * 1e-9, source=os.path.relpath(src, os.path.join(D, '..', '..')))
json.dump(out, open(dst, 'w'), indent=1)
print('sta_taps.py: %s -> %s: %s' % (src, dst, ', '.join('%s T0 %.2f ns arr %.2f ns' % (k, v['T0'] * 1e9, v['arr'] * 1e9) for k, v in out.items())))
