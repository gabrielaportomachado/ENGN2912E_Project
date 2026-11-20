#!/usr/bin/env python3
"""AUDIT step 6: power per mode from the static .op currents (review/sim/power_op.log) and the dynamic terms (sources stated per line).
usage: python3 power_total.py [out.log] [static-current log = sim/power_op.log] [variant = 1k_3L]
The variant column of the static-current log selects the resistor version: 1k_3L = the design since F1 (Decision 44a: ppolyf_u_1k, 3x the squares); 3k = the pre-F1 design.
The audit log sim/power_total.log was made with the 3k rows; F1 wrote sim/f1_power_total.log from sim/f1_bias_op.log with the 1k_3L rows."""
import sys, os, re, math
R = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
out = open(sys.argv[1], 'w') if len(sys.argv) > 1 else sys.stdout
P = lambda *a: print(*a, file=out)
# static, uA  [review/sim/power_op.log]: corner -> (channel, bias, vhalf, VDD)
ST = {}
SRC = sys.argv[2] if len(sys.argv) > 2 else os.path.join(R, 'sim', 'power_op.log')
VAR = sys.argv[3] if len(sys.argv) > 3 else '1k_3L'
for ln in open(SRC):
    m = re.match(r'(\w+)\s+(-?\d+)\s+([\d.]+) %s\s+\|' % re.escape(VAR) + r'\s+[\d.]+(?:\s+[\d.]+){5}\s+\|\s+([\d.]+)\s+[\d.]+\s+[\d.]+\s+\|\s+([\d.]+)\s+([\d.]+)', ln)
    if m:
        ST[(m.group(1), int(m.group(2)), float(m.group(3)))] = (float(m.group(4)), float(m.group(5)), float(m.group(6)))
# digital macro, W at SCLK 2 MHz running continuously, default activity  [AFE/adc/lg/runs/d3/53-openroad-stapostpnr/nom_*/power.rpt]
PD = {'tt_025C_3v30': 1.592672e-4, 'ss_125C_3v00': 1.350759e-4, 'ff_n40C_3v60': 1.923635e-4}
ECYC = {k: v / 2e6 for k, v in PD.items()}                 # J per SCLK cycle
E_CMP = {'typ': 6.0e-12, 'ff': 7.0e-12, 'ss': 5.8e-12}     # J per decision [AFE/adc/sim/d1_delay.log, AFE/adc/NOTES.md D1]
Q_DAC = {'typ': 17.8e-12, 'ff': 16.1e-12, 'ss': 19.5e-12}  # C per conversion from VDD, worst code [AFE/adc/sim/d2_settle.log, NOTES D2]
FS = 4000.0
NCLK = 160
DBS = 1.06                                                 # dbs_ctrl adds 18 flops to 149 + gates: +6 % of the macro (ESTIMATE from the cell areas: 1998 / 31872 um2)
P('AUDIT step 6: power.  Static currents [%s, rows %s]; digital energy' % (os.path.relpath(SRC, os.path.join(R, '..', '..')), VAR) + ' per SCLK cycle = LibreLane power.rpt / 2 MHz (tt 79.6 pJ, ss 125 C 3.0 V 67.5 pJ, ff -40 C 3.6 V 96.2 pJ; default data activity,')
P('clock and flop-clock-pin power dominate: 97 %); 160 SCLK per frame, 4000 frames/s.  DOUT pad: C_load ASSUMED, 36 rising edges per frame (144 data bits x 0.25), E = C V^2 per rising edge.')
P('')
P('%-22s | %8s %7s %7s | %8s %7s %7s %8s %8s | %8s %8s | %s' % ('corner', 'amps', 'bias', 'vhalf', 'digital', 'cmp', 'DAC', 'DOUT15pF', 'dyn_sum', 'RECORD', 'IDLE', 'uA record (avg from the pad)'))
rows = [(('typical', 27, 3.3), 'tt_025C_3v30', 'typ'), (('ff', 85, 3.3), 'ff_n40C_3v60', 'ff'), (('ss', -40, 3.3), 'ss_125C_3v00', 'ss'), (('ff', -40, 3.6), 'ff_n40C_3v60', 'ff'), (('ss', 125, 3.0), 'ss_125C_3v00', 'ss')]
for key, dk, ak in rows:
    ch, bias, vh = ST[key]
    v = key[2]
    sc = (v / {'tt_025C_3v30': 3.3, 'ss_125C_3v00': 3.0, 'ff_n40C_3v60': 3.6}[dk]) ** 2
    amps = 8 * ch * v
    pb = bias * v
    pv = 8 * vh * v
    dig = ECYC[dk] * sc * NCLK * FS * DBS * 1e6
    cmp_ = E_CMP[ak] * 12 * 8 * FS * 1e6
    dac = Q_DAC[ak] * v * 8 * FS * 1e6
    dout = 15e-12 * v * v * 36 * FS * 1e6
    dyn = dig + cmp_ + dac + dout
    rec = amps + pb + pv + dyn
    idle = amps + pb + pv
    P('%-8s %4d C %3.1f V  | %8.1f %7.1f %7.1f | %8.1f %7.2f %7.2f %8.1f %8.1f | %8.1f %8.1f | %7.1f' % (key[0], key[1], v, amps, pb, pv, dig, cmp_, dac, dout, dyn, rec, idle, rec / v))
P('  all in uW.  RECORD = STIMULATE (frames still read) = RESET (RST_AMP held) : the analog current does not depend on the mode; IDLE = SCLK stopped (static only).')
P('  SCLK 2 MHz and 3 MHz give the same average (160 clocks per frame at both).  If the host lets SCLK free-run: digital = 159 uW at 2 MHz, 239 uW at 3 MHz (tt) instead of ~54 uW.')
P('  DOUT load 10 / 20 pF: 15.7 / 31.4 uW at 3.3 V.  One-shot timer legs: 8 x ~2 nA while the routing switch is open (negligible).')
P('')
tt = ECYC['tt_025C_3v30']
P('PEAK / TRANSIENT (ESTIMATE):')
P('  digital charge per SCLK cycle = %.1f pC (tt), %.1f pC (ff -40 C 3.6 V), %.1f pC (ss 125 C 3.0 V); X2 S4 assumed 1.5 pC per converting ADC per edge = 12 pC at most.' % (tt / 3.3 * 1e12, ECYC['ff_n40C_3v60'] / 3.6 * 1e12, ECYC['ss_125C_3v00'] / 3.0 * 1e12))
P('  comparator 1.8-2.6 pC per decision in ~2 ns (about 1 mA peak each, staggered); DAC 2.9 pC on the MSB trial; DOUT pad 15 pF x 3.3 V = 50 pC per edge in 5-10 ns: 5-10 mA peak, only during read-out (after the conversions).')
P('  peak from the pad pair therefore ~10-25 mA for a few ns; on-chip decap 0.225 nF: 24 pC -> ~0.1 V if taken from 0.225 nF alone, 45 mV measured in X2 S4 with 12 pC [AFE/adc/sim/x2_s4_summary.log].')
P('')
P('STATIC IR DROP AND ELECTROMIGRATION (floorplan of section 5; sheet resistance from the PDK model: Metal1-4 0.09 ohm/sq, top metal 11k 0.04 ohm/sq):')
for name, i_ma, l, w, rs in (('analog strap, top metal, 1000 um x 10 um', 0.61, 1000, 10, 0.04), ('analog strap at ff 85 C', 0.97, 1000, 10, 0.04), ('same on Metal3, 1000 um x 10 um', 0.61, 1000, 10, 0.09), ('per-channel branch, Metal3 300 um x 2 um (0.085 mA)', 0.085, 300, 2, 0.09)):
    r = rs * l / w
    P('  %-52s R = %5.1f ohm, I = %.3f mA -> IR drop %.2f mV; current density %.3f mA/um (limit 2.09 mA/um at 85 C, 1.0 at 110 C for Metal1-4; 4.5 for the top metal: ORGANIZER table)' % (name, r, i_ma, r * i_ma, i_ma / w))
P('  one dvdd / dvss pad cell carries 60 mA DC (ORGANIZER table): average 0.6-1.0 mA is 60x below; one pad pair is enough for DC. The inductance question (X2 S4, ff -40 C) is separate.')
if out is not sys.stdout:
    out.close()
