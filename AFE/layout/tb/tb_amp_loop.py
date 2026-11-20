#!/usr/bin/env python3
"""tb_amp_loop.py (L2b): loop gain and phase margin of the stage-1 loop inside the full channel (stage 1 loaded by the real stage 2 and follower), Middlebrook / Tian two-injection
method of AFE/amp/tb/tb_a4c_loop.spice (two copies of the channel on one bias cell, voltage injection in one, current injection in the other, at the OTA-1 input).
  schematic : the simulation netlist has the break point built in (LOOPTEST = 1).  Also a CALIBRATION of the port-level stand-in used by tb_amp_ac.py: the same measurement with an extra
              capacitor on the stage-1 output (2, 5, 10 pF) gives pm_cx<C> and hfdev_cx<C>_db = the largest change of the hf_ values of tb_amp_ac.py that this capacitor causes.
  PEX       : the loop is opened inside the extracted netlist: every MOS gate on the summing node (found through the anchor of Cin1) is moved to a new node vng and the two injection
              sources are inserted between vng and the summing node (a copy in the scratch directory).  If the anchor is missing the check reports pm_deg = nan (then use hf_ of tb_amp_ac).
Values: t_100hz_db, fu_hz, pm_deg (+ the calibration values on the schematic).  Pre-layout (AFE/amp/sim/a4c_loop.log): 79.2 / 76.4 / 81.1 deg, fu 269 / 386 / 199 kHz.
usage: python3 AFE/layout/tb/tb_amp_loop.py [--netlist schematic|<amp_ch PEX>] [--corner typ|ff85|ss-40|all] [--junction] [--out DIR]"""
import os, sys, re
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lptb import *
import numpy as np

MOSM = ('nfet_03v3', 'pfet_03v3', 'nfet_06v0_nvt', 'nfet_05v0', 'pfet_05v0')


def pex_break(dut):
    """copy of the PEX netlist with the stage-1 loop opened at the summing node -> (path, subckt name)"""
    vn = dut.probes.get('vn')
    if not vn:
        return None, None
    out = os.path.join(SCRATCH, 'tb', 'loop_%s.spice' % dut.tag)
    L, n = ['* %s with the stage-1 loop opened at %s (tb_amp_loop.py)' % (dut.netlist, vn), '.subckt %s_lb %s params: BRKV=0 BRKI=0' % (dut.subname, ' '.join(dut.ports))], 0
    for e in dut.elems:
        t = e.split()
        nodes = [x for x in t[1:] if '=' not in x]
        if t[0][0] in 'xX' and nodes[-1].lower() in MOSM and nodes[1] == vn:
            t[2] = 'vng'
            n += 1
        L.append(' '.join(t))
    L += ['Vbrk vng %s dc 0 ac {BRKV}' % vn, 'Ibrk 0 vng dc 0 ac {BRKI}', '.ends']
    if n == 0:
        return None, None
    open(out, 'w').write('\n'.join(L) + '\n')
    return out, dut.subname + '_lb'


def bench(corner, dut, ns, cx=0.0):
    c, T, vs = CORNERS[corner]
    L = ['* LP golden testbench: stage-1 loop gain [%s]' % corner]
    if dut.pex:
        path, sub = pex_break(dut)
        L += model_lines(corner, dut.models) + ['.include %s/spice/%s.spice' % (AMP, amp_file(f)) for f in ('pseudoR', 'ota1_params', 'afe_params', 'a4c_params', 'ota1', 'ota2', 'bias_genc', 'stage1c', 'stage2c', 'fs_oneshot_c', 'src_randles')]
        conn = dict((p.lower(), AMP_MAP[q]) for q in AMP_PINS for p in dut.ports if p.lower() == q.lower())
        L += ['.include %s' % path, '.subckt afe_chc %s params: BRKV=0 BRKI=0' % ' '.join(AFE_CHC_PINS), 'Xpex %s %s BRKV={BRKV} BRKI={BRKI}' % (' '.join(conn[p.lower()] for p in dut.ports), sub), '.ends afe_chc']
        if dut.vsubs:
            L += ['.global VSUBS', 'Rvsubs VSUBS 0 1m']
        p = {'LOOPTEST': 0}
    else:
        L += amp_includes(corner, dut)
        p = {'LOOPTEST': 1}
    p.update(VSUP=vs, NSVRS=NSVRS.get(corner, 1.0))
    L += ['.options gmin=1e-16 abstol=1e-20 reltol=1e-4 itl1=500 itl4=500', '.temp %g' % T] + ['.param %s=%s' % kv for kv in p.items()]
    L += ['Vdd vdd 0 {VSUP}', 'Xbias vbn vcm vg1 vcmo vg2 vrs vdd 0 bias_genc', 'Vfs fs 0 0', 'Vpkc pkc 0 0', 'Vpkcb pkcb 0 {VSUP}', 'Vtis tis 0 1.65', 'Vd vd 0 dc 0 ac 0', 'Vosr vosr 0 0', 'Vosf vosf 0 0']
    for i in '12':
        L += ['Xsrc%s vd tis rec%s ref%s vosr vosf src_randles' % (i, i, i)] + ['E%s%s %s%s 0 %s 0 1' % (n, i, n, i, n) for n in ('vbn', 'vcm', 'vg1', 'vcmo', 'vg2', 'vrs')]
        L += ['Xch%s rec%s ref%s out%s vdd 0 vbn%s vcm%s vg1%s vcmo%s vg2%s vrs%s fs pkc pkcb afe_chc BRKV=%d BRKI=%d' % ((i,) * 10 + ((1, 0) if i == '1' else (0, 1))), 'Coff%s out%s 0 20f' % (i, i)]
        if cx:
            L.append('Cx%s %s 0 %g' % (i, dut.node('v1', 'xch' + i), cx))
    if dut.pex:
        vn = dut.probes['vn']
        L += ['Ep_vn p_vn 0 xch1.xpex.%s 0 1' % vn.lower(), 'Ep_vng p_vng 0 xch1.xpex.vng 0 1']
        tv, ir = '-v(p_vn)/v(p_vng)', 'v.xch2.xpex.vbrk#branch'
    else:
        tv, ir = '-v(xch1.xs1.vn)/v(xch1.xs1.vng)', 'v.xch2.xs1.vbrk#branch'
    if ns == 'native':
        for i in '12':
            L.append(NATIVE_NS.replace('xch.', 'xch%s.' % i).replace('v(rec)', 'v(rec%s)' % i).replace('v(out)', 'v(out%s)' % i))
    else:
        for i in '12':
            for ln in ns.split('\n'):
                m = re.match(r'\.nodeset v\(([^)]+)\)=(.*)', ln)
                n, val = m.group(1), m.group(2)
                if n.startswith('xch.'):
                    L.append('.nodeset v(xch%s.%s)=%s' % (i, n[4:], val))
                    if dut.pex and n == 'xch.xpex.%s' % dut.probes['vn'].lower():
                        L.append('.nodeset v(xch%s.xpex.vng)=%s' % (i, val))
                elif n in ('rec', 'ref', 'out'):
                    L.append('.nodeset v(%s%s)=%s' % (n, i, val))
                elif n in ('vbn', 'vcm', 'vg1', 'vcmo', 'vg2', 'vrs'):
                    L.append('.nodeset v(%s%s)=%s' % (n, i, val))
                    if i == '1':
                        L.append(ln)
                elif i == '1' and not n.startswith('xsrc.'):
                    L.append(ln)
    L += ['.control', 'ac dec 20 1e-2 1e9', 'let tv = %s' % tv, 'let iret = %s' % ir, 'let ti = iret/(1 - iret)', 'let t = (tv*ti - 1)/(tv + ti + 2)', 'let tdb = vdb(t)', 'let tph = cph(t)*180/pi',
          'meas ac t_lf find tdb at=100', 'meas ac fu when tdb=0 fall=1', 'meas ac ph_fu find tph at=$&fu', 'let pm = 180 + ph_fu', 'echo RESULT T_100Hz_dB=$&t_lf fu_Hz=$&fu pm_deg=$&pm', 'quit', '.endc', '.end']
    return '\n'.join(L) + '\n'


def run(netlist, corner, a, log):
    dut = amp_dut(netlist, a.prdiff)
    for w in dut.warnings:
        log('WARNING ' + w)
    if dut.pex and not dut.probes.get('vn'):
        return {'t_100hz_db': float('nan'), 'fu_hz': float('nan'), 'pm_deg': float('nan')}, {'warnings': dut.warnings + ['no anchor for the summing node: loop not measurable, use the hf_ values of tb_amp_ac.py']}
    simple = not (dut.pex or dut.prdiff)
    ns = 'native' if simple else settle(corner, dut, log)
    jobs = [('loop_%s_%s' % (dut.tag, corner), bench(corner, dut, ns))]
    cal = [2e-12, 5e-12, 10e-12] if simple else []
    for cx in cal:
        jobs.append(('loop_%s_%s_cx%g' % (dut.tag, corner, cx * 1e12), bench(corner, dut, ns, cx)))
    for cx in [0.0] + cal:                                # the same capacitor in the op + ac bench of tb_amp_ac.py: what it does to the port-level response
        L = amp_bench(corner, dut, 'ac with %g pF on the stage-1 output' % (cx * 1e12), nodeset=ns, extra=(['Cx %s 0 %g' % (dut.node('v1'), cx)] if cx else []))
        f = os.path.join(SCRATCH, 'tb', 'amp_loop', 'hf_%s_%s_%g.dat' % (dut.tag, corner, cx * 1e12))
        os.makedirs(os.path.dirname(f), exist_ok=True)
        L += ['.control', 'ac dec 100 1e-3 1e7', 'wrdata %s vdb(out)' % f, 'echo DONE', 'quit', '.endc', '.end']
        if simple:
            jobs.append(('hf_%s_%s_cx%g' % (dut.tag, corner, cx * 1e12), '\n'.join(L) + '\n'))
    res = run_ng(jobs, 'amp_loop', log=log)
    o = results(res[jobs[0][0]]['out'])
    if not o:
        raise TbError('loop-gain run failed: ' + (res[jobs[0][0]]['abort'] or res[jobs[0][0]]['out'][-300:]))
    v = {'t_100hz_db': o[0]['T_100Hz_dB'], 'fu_hz': o[0]['fu_Hz'], 'pm_deg': o[0]['pm_deg']}
    if simple:
        HF = [1e3, 3e3, 1e4, 3e4, 1e5, 3e5, 1e6]

        def hf(cx):
            d = np.loadtxt(os.path.join(SCRATCH, 'tb', 'amp_loop', 'hf_%s_%s_%g.dat' % (dut.tag, corner, cx * 1e12)))
            g = np.interp(np.log10(HF), np.log10(d[:, 0]), d[:, 1]) - np.interp(np.log10(12.25), np.log10(d[:, 0]), d[:, 1])
            return g
        h0 = hf(0.0)
        for cx in cal:
            oo = results(res['loop_%s_%s_cx%g' % (dut.tag, corner, cx * 1e12)]['out'])
            k = '%gp' % (cx * 1e12)
            v['pm_cx%s_deg' % k] = oo[0]['pm_deg'] if oo else float('nan')
            v['hfdev_cx%s_db' % k] = float(np.abs(hf(cx) - h0).max())
    return v, {'warnings': dut.warnings}


if __name__ == '__main__':
    sys.exit(cli('amp_loop', __doc__, AMP_CORNERS, run))
