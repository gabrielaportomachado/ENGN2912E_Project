#!/usr/bin/env python3
"""AUDIT step 6: static supply current per block from .op (no saved log has the per-block split).
Netlist = AFE/amp/tb/tb_a4c_op.spice (read, includes rewritten to absolute paths; design files untouched): bias_genc + ONE afe_chc; the OPDEV lines give every branch.
Also: vhalf alone, and the what-if for the HRES option of gf180mcuD (ppolyf_u_3k does not exist there): same drawn squares as ppolyf_u_1k (R/3) and 3x length (same R).
usage: python3 power_op.py [out.log]"""
import sys, os, re
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from ngjob import *

CORNERS = [('typical', 27, 3.3), ('ff', 85, 3.3), ('ss', -40, 3.3), ('ff', -40, 3.6), ('ss', 125, 3.0)]


def tb_op(corner, temp, vdd, variant='3k'):
    t = open(os.path.join(AMP, 'tb', 'tb_a4c_op.spice')).read()
    t = t.replace('../spice/models_typical.spice', '%s/spice/models_%s.spice' % (AMP, corner)).replace('../spice/', AMP + '/spice/')
    t = re.sub(r'^\.temp .*$', '.temp %g' % temp, t, flags=re.M)
    t = re.sub(r'^\.param VSUP=.*$', '.param VSUP=%g' % vdd, t, flags=re.M)
    if variant != '3k':
        # what-if: private copy of bias_genc with the D-variant resistor; VDDN is the design value the ladder lengths are computed from
        b = open(os.path.join(AMP, 'spice', 'bias_genc.spice')).read()
        if variant == '1k_sameL':
            b = b.replace('ppolyf_u_3k', 'ppolyf_u_1k')                       # same drawn squares: R / 3
        elif variant == '1k_3L':
            b = b.replace('/3000*1u}', '/1000*1u}').replace('ppolyf_u_3k', 'ppolyf_u_1k')   # 3x the squares: same R
        p = os.path.join(PT, 'pwr', 'bias_genc_%s.spice' % variant)
        os.makedirs(os.path.dirname(p), exist_ok=True)
        open(p, 'w').write(b)
        t = t.replace('.include %s/spice/bias_genc.spice' % AMP, '.include ' + p)
    return t


def tb_vhalf(corner, temp, vdd, variant='3k'):
    v = open(os.path.join(ADC, 'spice', 'vhalf.spice')).read()
    if variant == '1k_sameL':
        v = v.replace('ppolyf_u_3k', 'ppolyf_u_1k')
    elif variant == '1k_3L':
        v = v.replace('/3000*1u}', '/1000*1u}').replace('ppolyf_u_3k', 'ppolyf_u_1k')
    p = os.path.join(PT, 'pwr', 'vhalf_%s.spice' % variant)
    os.makedirs(os.path.dirname(p), exist_ok=True)
    open(p, 'w').write(v)
    return '\n'.join(['* vhalf static current (%s)' % variant, '.include %s/spice/models_%s.spice' % (AMP, corner), '.include ' + p, '.temp %g' % temp,
                      'Vdd vdd 0 %g' % vdd, 'Xvh out vdd 0 vhalf', 'Xvr out ci vdd 0 vdd 0 vrefs', '.control', 'op', 'let i = -i(Vdd)', 'let vo = v(out)', 'let vc = v(ci)',
                      'echo RESULT i_A=$&i vout_V=$&vo vci_V=$&vc', 'quit', '.endc', '.end'])


if __name__ == '__main__':
    out = open(sys.argv[1], 'w') if len(sys.argv) > 1 else sys.stdout
    P = lambda *a: (print(*a, file=out), out.flush())
    jobs = []
    for (c, T, v) in CORNERS:
        for var in ('3k', '1k_sameL', '1k_3L'):
            jobs.append(('op_%s_%d_%s' % (c, T, var), tb_op(c, T, v, var)))
            jobs.append(('vh_%s_%d_%s' % (c, T, var), tb_vhalf(c, T, v, var)))
    res = run_jobs(jobs, 'pwr', log=lambda s: None)
    P('AUDIT step 6: static supply currents from .op (bias_genc + ONE afe_chc, tb_a4c_op.spice; vhalf + vrefs alone).  uA unless stated.  ngspice-46, one thread.')
    P('channel = OTA1 (bias diode + tail + 2nd stage) + stage-2 tail + follower;  bias = master legs + start-up + ladders A and B (ladders = total - all MOS branches).')
    P('variant 3k = design as frozen (ppolyf_u_3k);  1k_sameL = same drawn squares with ppolyf_u_1k (the only HRES device of gf180mcuD): R/3;  1k_3L = ppolyf_u_1k with 3x the squares.')
    hdr = '%-9s %4s %4s %-9s | %8s %8s %8s %8s %8s %8s | %8s %8s %8s | %8s %8s | %8s %8s %8s %8s'
    P(hdr % ('corner', 'T', 'VDD', 'variant', 'total', 'ota1_b', 'ota1_t', 'ota1_2', 'st2tail', 'follow', 'channel', 'master', 'ladders', 'bias', 'vhalf', 'vcm_in', 'vg1', 'vcm_out', 'vg2'))
    tab = {}
    for (c, T, v) in CORNERS:
        for var in ('3k', '1k_sameL', '1k_3L'):
            r = res['op_%s_%d_%s' % (c, T, var)]
            dev = {}
            for ln in r['out'].split('\n'):
                m = re.match(r'OPDEV (\S+) id_A=(\S+)', ln)
                if m:
                    dev[m.group(1)] = float(m.group(2))
            s = results(r['out'], 'OPSUM')
            vh = results(res['vh_%s_%d_%s' % (c, T, var)]['out'])
            if not s or not dev or not vh:
                P('%-9s %4d %4.1f %-9s FAILED: %s' % (c, T, v, var, (r['abort'] or res['vh_%s_%d_%s' % (c, T, var)]['abort'])[:200]))
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
            tab[(c, T, v, var)] = dict(tot=tot, ch=ch, bias=mas + lad, vh=vh[0]['i_A'] * u, mas=mas, lad=lad)
            P('%-9s %4d %4.1f %-9s | %8.2f %8.2f %8.2f %8.2f %8.4f %8.2f | %8.2f %8.3f %8.2f | %8.2f %8.2f | %8.4f %8.4f %8.4f %8.4f' % (
                c, T, v, var, tot, o1b, o1t, o12, s2t, fol, ch, mas, lad, mas + lad, vh[0]['i_A'] * u, s['vcm_V'], s['vg1_V'], s['vcmo_V'], s['vg2_V']))
    P('\nCHIP STATIC CURRENT, N = 8 channels:  8 x channel + bias + 8 x vhalf   [uA]  (power = I x VDD)')
    for (c, T, v) in CORNERS:
        for var in ('3k', '1k_sameL', '1k_3L'):
            k = (c, T, v, var)
            if k not in tab:
                continue
            t = tab[k]
            I = 8 * t['ch'] + t['bias'] + 8 * t['vh']
            P('%-9s %4d %4.1f %-9s amplifiers %8.1f  bias %6.2f  vhalf x8 %7.1f  TOTAL %8.1f uA = %6.3f mW' % (c, T, v, var, 8 * t['ch'], t['bias'], 8 * t['vh'], I, I * v / 1000))
    if out is not sys.stdout:
        out.close()
    cleanup('pwr')
