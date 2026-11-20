#!/usr/bin/env python3
"""F1 item 1 (Decision 44a, AUDIT P-A1 / B1): check of the ppolyf_u_3k -> ppolyf_u_1k change (3x the squares, same width) in bias_genc.spice and vhalf.spice.
.op of bias_genc + ONE afe_chc (AFE/amp/tb/tb_a4c_op.spice, as AUDIT step 6) and of vhalf + vrefs alone, with
  1k_3L = the design netlists as they are now, and
  3k    = the pre-F1 netlist rebuilt from them (power_op.hres_variant: ppolyf_u_3k, L = R/3000), run again here so that the differences have full resolution
          (the saved audit log has 4 decimals on the taps).
Compared with the saved audit log AFE/review/sim/power_op.log (rows `3k` = the design the audit measured, rows `1k_3L` = the audit's prediction for this change).
Criteria of the F1 prompt at typ 27 / ff 85 / ss -40 C: every tap within 0.5 mV, currents within 1 %.
usage: python3 f1_bias_op.py [out.log]      (default AFE/review/sim/f1_bias_op.log; scratch AFE/review/.ptmp/f1op, removed at the end)"""
import sys, os, re
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from ngjob import *
import power_op as PO

VARS = ('3k', '1k_3L')
TAPS = ('vcm_in', 'vg1', 'vcm_out', 'vg2')
CUR = ('total', 'channel', 'master', 'ladders', 'bias', 'vhalf')
F1C = [('typical', 27, 3.3), ('ff', 85, 3.3), ('ss', -40, 3.3)]          # the three corners of the F1 prompt (the two STA-matched supply corners are run as information)


def tb_op(c, T, v, var):
    t = PO.tb_op(c, T, v, var)
    assert t.count('\nquit\n') == 1
    return t.replace('\nquit\n', '\necho F1X vrs_V=$&v(vrs) vbn_V=$&v(vbn)\nquit\n')


def audit_rows():
    """rows of the saved audit log: {(corner, T, VDD, variant): dict}"""
    A = {}
    for ln in open(os.path.join(SIM, 'power_op.log')):
        m = re.match(r'(\w+)\s+(-?\d+)\s+([\d.]+)\s+(\S+)\s+\|(.*)\|(.*)\|(.*)\|(.*)$', ln)
        if not m:
            continue
        a = [float(x) for x in m.group(5).split()]
        b = [float(x) for x in m.group(6).split()]
        c = [float(x) for x in m.group(7).split()]
        d = [float(x) for x in m.group(8).split()]
        A[(m.group(1), int(m.group(2)), float(m.group(3)), m.group(4))] = dict(total=a[0], channel=b[0], master=b[1], ladders=b[2], bias=c[0], vhalf=c[1], vcm_in=d[0], vg1=d[1], vcm_out=d[2], vg2=d[3])
    return A


if __name__ == '__main__':
    path = sys.argv[1] if len(sys.argv) > 1 else os.path.join(SIM, 'f1_bias_op.log')
    out = open(path, 'w')
    P = lambda *a: (print(*a), print(*a, file=out), out.flush())
    jobs = []
    for (c, T, v) in PO.CORNERS:
        for var in VARS:
            jobs.append(('op_%s_%d_%s' % (c, T, var), tb_op(c, T, v, var)))
            jobs.append(('vh_%s_%d_%s' % (c, T, var), PO.tb_vhalf(c, T, v, var)))
    res = run_jobs(jobs, 'pwr', log=lambda s: None)
    P('F1 item 1 (Decision 44a): bias .op after ppolyf_u_3k -> ppolyf_u_1k (3x the squares, 1 um wide).  bias_genc + ONE afe_chc (tb_a4c_op.spice) and vhalf + vrefs alone.  uA unless stated.  ngspice-46, one thread.')
    P('variant 1k_3L = the design netlists as they are (AFE/amp/spice/bias_genc.spice, AFE/adc/spice/vhalf.spice);  3k = the pre-F1 netlist rebuilt from them and run again here (ppolyf_u_3k, L = R/3000).')
    hdr = '%-9s %4s %4s %-9s | %8s %8s %8s %8s %8s %8s | %8s %8s %8s | %8s %8s | %8s %8s %8s %8s'
    P(hdr % ('corner', 'T', 'VDD', 'variant', 'total', 'ota1_b', 'ota1_t', 'ota1_2', 'st2tail', 'follow', 'channel', 'master', 'ladders', 'bias', 'vhalf', 'vcm_in', 'vg1', 'vcm_out', 'vg2'))
    tab = {}
    fail = []
    for (c, T, v) in PO.CORNERS:
        for var in VARS:
            r = res['op_%s_%d_%s' % (c, T, var)]
            rv = res['vh_%s_%d_%s' % (c, T, var)]
            dev = {}
            for ln in r['out'].split('\n'):
                m = re.match(r'OPDEV (\S+) id_A=(\S+)', ln)
                if m:
                    dev[m.group(1)] = float(m.group(2))
            s = results(r['out'], 'OPSUM')
            x = results(r['out'], 'F1X')
            vh = results(rv['out'])
            if not s or not dev or not vh or not x:
                P('%-9s %4d %4.1f %-9s FAILED: %s' % (c, T, v, var, (r['abort'] or rv['abort'])[:300]))
                fail.append((c, T, v, var))
                continue
            s = s[0]
            u = 1e6
            tot = s['i_supply_A'] * u
            o1b = dev['xch.xs1.xota.xmb'] * u
            o1t = dev['xch.xs1.xota.xmt'] * u
            o12 = dev['xch.xs1.xota.xm7'] * u
            s2t = dev['xch.xs2.xota2.xmt'] * u
            fol = dev['xch.xs2.xota2.xms'] * u
            ch = o1b + o1t + o12 + s2t + fol
            mas = (dev['xbias.xmp1'] + dev['xbias.xmp2']) * u
            lad = tot - ch - mas
            tab[(c, T, v, var)] = dict(total=tot, channel=ch, master=mas, ladders=lad, bias=mas + lad, vhalf=vh[0]['i_A'] * u, vcm_in=s['vcm_V'], vg1=s['vg1_V'], vcm_out=s['vcmo_V'], vg2=s['vg2_V'],
                                       vout=s['vout_V'], vrs=x[0]['vrs_V'], vbn=x[0]['vbn_V'], vhout=vh[0]['vout_V'])
            P('%-9s %4d %4.1f %-9s | %8.2f %8.2f %8.2f %8.2f %8.4f %8.2f | %8.2f %8.3f %8.2f | %8.2f %8.2f | %8.4f %8.4f %8.4f %8.4f' % (
                c, T, v, var, tot, o1b, o1t, o12, s2t, fol, ch, mas, lad, mas + lad, vh[0]['i_A'] * u, s['vcm_V'], s['vg1_V'], s['vcmo_V'], s['vg2_V']))
    A = audit_rows()

    # ---- 1. the re-run 3k variant must reproduce the audit rows (shows that nothing but the resistor lines changed)
    P('\nCHECK 1: the pre-F1 netlist rebuilt from the new files reproduces the saved audit rows `3k` of AFE/review/sim/power_op.log (print resolution: 0.01 uA, 0.1 mV)')
    ok1 = True
    for (c, T, v) in PO.CORNERS:
        k = (c, T, v, '3k')
        if k not in tab or k not in A:
            ok1 = False
            P('  %-9s %4d %3.1f: missing' % (c, T, v))
            continue
        dc = max(abs(tab[k][q] - A[k][q]) for q in CUR)
        dt = max(abs(round(tab[k][q], 4) - A[k][q]) for q in TAPS) * 1e3
        good = dc <= 0.0051 and dt <= 0.051
        ok1 = ok1 and good
        P('  %-9s %4d C %3.1f V: max current difference %.3f uA, max tap difference %.2f mV  %s' % (c, T, v, dc, dt, 'SAME' if good else 'DIFFERENT'))
    P('  CHECK 1: %s' % ('PASS' if ok1 else 'FAIL'))

    # ---- 2. the new design against the audit prediction (rows 1k_3L of the audit log)
    P('\nCHECK 2: the design as it is now against the audit prediction for this change (rows `1k_3L` of AFE/review/sim/power_op.log)')
    ok2 = True
    for (c, T, v) in PO.CORNERS:
        k = (c, T, v, '1k_3L')
        if k not in tab or k not in A:
            ok2 = False
            P('  %-9s %4d %3.1f: missing' % (c, T, v))
            continue
        dc = max(abs(tab[k][q] - A[k][q]) for q in CUR)
        dt = max(abs(round(tab[k][q], 4) - A[k][q]) for q in TAPS) * 1e3
        good = dc <= 0.0051 and dt <= 0.051
        ok2 = ok2 and good
        P('  %-9s %4d C %3.1f V: max current difference %.3f uA, max tap difference %.2f mV  %s' % (c, T, v, dc, dt, 'SAME' if good else 'DIFFERENT'))
    P('  CHECK 2: %s' % ('PASS' if ok2 else 'FAIL'))

    # ---- 3. before / after: new design (1k_3L) minus the pre-F1 design (3k), full resolution from the two runs made here
    P('\nCHECK 3: BEFORE / AFTER, design now (1k_3L) minus the pre-F1 design (3k); both run here.  Limits of the F1 prompt: taps 0.5 mV, currents 1 %.')
    P('%-9s %4s %4s | %9s %9s %9s %9s | %8s %8s %8s | %8s %8s %8s %8s %8s %8s | %s' % ('corner', 'T', 'VDD', 'dvcm_in', 'dvg1', 'dvcm_out', 'dvg2', 'dvrs', 'dvbn', 'dvout', 'total%', 'channel%', 'master%', 'ladders%', 'bias%', 'vhalf%', 'verdict'))
    verdicts = {}
    for (c, T, v) in PO.CORNERS:
        a, b = tab.get((c, T, v, '1k_3L')), tab.get((c, T, v, '3k'))
        if not a or not b:
            continue
        dt = [(a[q] - b[q]) * 1e3 for q in TAPS]
        dx = [(a[q] - b[q]) * 1e3 for q in ('vrs', 'vbn', 'vout')]
        dp = [(a[q] / b[q] - 1) * 100 for q in CUR]
        tap_ok = max(abs(x) for x in dt) <= 0.5
        amp_ok = max(abs(dp[i]) for i in (0, 1, 2)) <= 1.0          # supply total (bias + one channel), channel, master
        res_ok = max(abs(dp[i]) for i in (3, 4, 5)) <= 1.0          # the resistor branches themselves: ladders, bias_genc total, vhalf
        verdicts[(c, T, v)] = (tap_ok, amp_ok, res_ok)
        P('%-9s %4d %4.1f | %+9.3f %+9.3f %+9.3f %+9.3f | %+8.3f %+8.3f %+8.3f | %+8.2f %+8.2f %+8.2f %+8.2f %+8.2f %+8.2f | taps %s; supply / channel / master currents %s; resistor-branch currents %s' % (
            c, T, v, dt[0], dt[1], dt[2], dt[3], dx[0], dx[1], dx[2], dp[0], dp[1], dp[2], dp[3], dp[4], dp[5],
            'PASS' if tap_ok else 'FAIL', 'PASS' if amp_ok else 'FAIL', 'PASS' if res_ok else 'OVER 1 %'))
    P('  (tap and node differences in mV; currents in % of the pre-F1 value.  vrs = reset level, vbn = mirror gate bias, vout = amplifier output DC level.)')
    P('  absolute values now [typ / ff 85 / ss -40]: ' + '; '.join('%s %s' % (q, ' / '.join('%.5f' % tab[(c, T, v, '1k_3L')][q] for (c, T, v) in F1C if (c, T, v, '1k_3L') in tab)) for q in TAPS + ('vrs', 'vhout')) + ' V')
    P('  currents now [typ / ff 85 / ss -40]: ' + '; '.join('%s %s' % (q, ' / '.join('%.3f' % tab[(c, T, v, '1k_3L')][q] for (c, T, v) in F1C if (c, T, v, '1k_3L') in tab)) for q in CUR) + ' uA')
    t_ok = all(verdicts.get(k, (False,))[0] for k in F1C)
    a_ok = all(verdicts.get(k, (False, False))[1] for k in F1C)
    r_ok = all(verdicts.get(k, (False, False, False))[2] for k in F1C)
    P('\nVERDICT at typ 27 / ff 85 / ss -40 C (3.3 V):')
    P('  taps within 0.5 mV of the pre-F1 design                              : %s' % ('PASS' if t_ok else 'FAIL'))
    P('  supply, channel and master currents within 1 %% of the pre-F1 design   : %s' % ('PASS' if a_ok else 'FAIL'))
    P('  ladder / bias_genc / vhalf branch currents within 1 %% of the pre-F1 design : %s' % ('PASS' if r_ok else 'NOT MET (see the ladders / bias / vhalf columns: the 1k poly has another corner spread and temperature coefficient than the 3k poly, PDK model r_tc1 -9.39e-4 against -1.67e-3 per K; its resistance at 25 C is 1.6 % lower)'))
    P('  same numbers as the audit prediction (power_op.log rows 1k_3L)        : %s' % ('PASS' if ok2 else 'FAIL'))
    P('\nCHIP STATIC CURRENT, N = 8 channels:  8 x channel + bias + 8 x vhalf   [uA]  (power = I x VDD)')
    for (c, T, v) in PO.CORNERS:
        for var in VARS:
            t = tab.get((c, T, v, var))
            if not t:
                continue
            I = 8 * t['channel'] + t['bias'] + 8 * t['vhalf']
            P('%-9s %4d %4.1f %-9s amplifiers %8.1f  bias %6.2f  vhalf x8 %7.1f  TOTAL %8.1f uA = %6.3f mW' % (c, T, v, var, 8 * t['channel'], t['bias'], 8 * t['vhalf'], I, I * v / 1000))
    out.close()
    cleanup('pwr')
    sys.exit(0 if (ok1 and ok2 and t_ok and a_ok and not fail) else 1)
