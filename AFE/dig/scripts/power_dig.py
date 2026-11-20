#!/usr/bin/env python3
"""power_dig.py (LP step 5 / L1d): supply charge of the digital macro afe_dig per SCLK cycle, for the 8-ADC supply run of L3b (AFE/adc/scripts/x2_s4.py; the D3 macro adc8_top
drew 24 pC per SCLK cycle at tt and 27 pC at ff -40 C 3.6 V, AFE/review/AUDIT.md 4.6 / m6).
Source: the OpenSTA power reports of the LibreLane sign-off STA (AFE/dig/reports/sta/<corner>/power.rpt, copied by collect_dig.py): SCLK free-running at the SDC period (500 ns),
default data activity of the tool, extracted wires, the output loads of AFE/dig/afe_dig.sdc.  energy per cycle = P * T, charge per cycle = P * T / VDD of the corner.
usage: python3 power_dig.py [out.log]     default AFE/dig/reports/power_dig.log"""
import os, re, sys
HERE = os.path.dirname(os.path.abspath(__file__))
RP = os.path.normpath(os.path.join(HERE, '..', 'reports'))
OUT = sys.argv[1] if len(sys.argv) > 1 else os.path.join(RP, 'power_dig.log')
T_NS = 500.0
CORN = [('nom_tt_025C_3v30', 3.3), ('nom_ff_n40C_3v60', 3.6), ('nom_ff_125C_3v60', 3.6), ('nom_ss_n40C_3v00', 3.0), ('nom_ss_125C_3v00', 3.0)]
L = ['LP step 5: afe_dig supply charge per SCLK cycle (OpenSTA report_power of the sign-off STA; SCLK free-running, period %.0f ns; default data activity; SDC output loads).' % T_NS,
     '%-18s %5s | %9s %9s %9s %9s | %10s %10s | %s' % ('corner', 'VDD', 'seq uW', 'comb uW', 'clock uW', 'total uW', 'pJ/cycle', 'pC/cycle', 'clock network share')]
val = {}
for c, vdd in CORN:
    f = os.path.join(RP, 'sta', c, 'power.rpt')
    if not os.path.exists(f):
        L.append('%-18s missing %s' % (c, f))
        continue
    t = open(f).read()
    g = {m.group(1): [float(x) for x in m.group(2).split()[:4]] for m in re.finditer(r'^(Sequential|Combinational|Clock|Total)\s+(.*)$', t, flags=re.M)}
    tot = g['Total'][3]
    val[c] = tot * T_NS * 1e-9 / vdd * 1e12
    L.append('%-18s %5.1f | %9.1f %9.1f %9.1f %9.1f | %10.1f %10.1f | %.0f %%' % (c, vdd, g['Sequential'][3] * 1e6, g['Combinational'][3] * 1e6, g['Clock'][3] * 1e6, tot * 1e6,
                                                                              tot * T_NS * 1e-9 * 1e12, val[c], 100 * g['Clock'][3] / tot))
if 'nom_tt_025C_3v30' in val and 'nom_ff_n40C_3v60' in val:
    L.append('FOR L3b (x2_s4.py digital charge): %.1f pC per SCLK cycle at tt 3.3 V, %.1f pC at ff -40 C 3.6 V (the D3 macro: 24 / 27 pC; X2 S4 assumed 12 pC).' % (val['nom_tt_025C_3v30'], val['nom_ff_n40C_3v60']))
    L.append('The increase over D3 is the clock buffer driving the 1 pF clock net (160 pins), 18 more flops (dbs_ctrl), and the output loads; it is drawn from the ADC-main strap.')
    L.append('At 4 kS/s per channel a frame has 160 SCLK cycles: average digital power = pJ/cycle x 160 x 4000 = %.1f uW at tt (+ the DOUT pad).' % (val['nom_tt_025C_3v30'] * 3.3 * 160 * 4000 * 1e-6))
open(OUT, 'w').write('\n'.join(L) + '\n')
print('\n'.join(L))
