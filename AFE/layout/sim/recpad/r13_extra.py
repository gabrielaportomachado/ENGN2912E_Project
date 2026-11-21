#!/usr/bin/env python3
"""r13_extra.py (REVIEW.md R13 item 3): the three extra simulations, on top of lptb.py (--rec-load works the same way).  Simulation only, nothing of the design is touched.
  leak   (3c) the pad model ALONE on a DC source: current into the pad at rec = 0 / 1.65 / 3.3 V, split into the two ESD diodes, at typ 27 / ff 85 / ss -40; pad capacitance at 1 Hz and 300 Hz.
  park   (3a) host power-up sequence of tb_amp_pwrup.py (record switch OPEN = stimulation mode, park on) and then 10 s of hold: v(rec) - v(vcm) at the end, the pad current into rec
              and the output offset, with and without the pad (--rec-load).  Recovery after the switch closes = tb_amp_reset.py rows t_1mv_s_os0 / os1m (matrix runs).
  recac  (3b) record path E -> routing TGATE (TGATE/TGATE.spice, closed) -> rec -> amplifier: gain / f_lo / f_hi of the whole chain, bandwidth of the node rec itself
              (v(rec) / v(E side of the TGATE)), 0.5-300 Hz input-referred noise (real devices) and the DC level of rec, with and without the pad.
usage: python3 AFE/layout/sim/recpad/r13_extra.py <leak|park|recac> [--netlist schematic|<amp_ch PEX>] [--corner typ|ff85|ss-40|all] [--rec-load FILE] [--out DIR]"""
import os, sys, re, json, math
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', '..', 'tb'))
import lptb
from lptb import *
import numpy as np

PAD = os.path.join(HERE, 'models', 'pad_open.spice')


def leak(a, c, log):
    """pad alone: DC current into the pad at three rec voltages + capacitance"""
    set_rec_load(a.rec_load or PAD)
    cname, T, vs = CORNERS[c]
    d = os.path.join(SCRATCH, 'tb', 'recpad_leak')
    os.makedirs(d, exist_ok=True)
    L = ['* R13 pad alone, corner %s' % c, '.include %s/spice/models_%s.spice' % (AMP, cname)] + rec_models(c) + ['.options gmin=1e-16 abstol=1e-20 reltol=1e-4 itl1=500 itl4=500', '.temp %g' % T,
         'Vdd vdd 0 %g' % vs, 'Vr rec 0 1.65 ac 1', 'Xrecpad rec vdd 0 recpad']
    f = os.path.join(d, 'leak_%s.dat' % c)
    L += ['.control', 'save @d.xrecpad.xasig.d2[id] @d.xrecpad.xasig.d3[id] @d.xrecpad.xasig.d0[id] i(Vr)', 'dc Vr 0 %g 0.05' % vs,
          'wrdata %s i(Vr) @d.xrecpad.xasig.d2[id] @d.xrecpad.xasig.d3[id]' % f, 'ac dec 1 1 100', 'let cp = -imag(i(Vr))/(2*pi*frequency)',
          'let c1 = cp[0]', 'let c100 = cp[2]', 'echo RESULT cap_1hz=$&c1 cap_100hz=$&c100', 'echo DONE', 'quit', '.endc', '.end']
    r = list(run_ng([('leak_%s' % c, '\n'.join(L) + '\n')], 'recpad_leak', log=log).values())[0]
    if 'DONE' not in r['out']:
        raise TbError('pad dc run failed: ' + (r['abort'] or r['out'][-300:]))
    x, ys = read_wr(f)
    v = {}
    for vr in (0.0, 1.65, 3.3):
        i = int(np.argmin(abs(x - vr)))
        v['i_rec_to_pad_%gv_pa' % vr] = float(ys[0][i]) * -1e12           # current from rec into the pad (= minus the current into the source Vr); negative = the pad feeds rec
        v['i_d2_%gv_pa' % vr] = float(ys[1][i]) * 1e12                    # D2 DVSS -> ASIG5V (N+/Psub): negative = reverse leakage from rec to ground
        v['i_d3_%gv_pa' % vr] = float(ys[2][i]) * 1e12                    # D3 ASIG5V -> DVDD (P+/Nwell): negative = reverse leakage from VDD into rec
    o = results(r['out'])
    if o:
        v['cap_1hz_pf'] = o[0]['cap_1hz'] * 1e12
        v['cap_100hz_pf'] = o[0]['cap_100hz'] * 1e12
    return v, {'pad_file': os.path.relpath(REC_LOAD['file'], REPO)}


def park(a, c, log):
    """stimulation mode: record switch open, park on, long hold"""
    dut = ampch_dut(a.netlist)
    for w in dut.warnings:
        log('WARNING ' + w)
    vs = CORNERS[c][2]
    tw = {'typ': 0.2, 'ff85': 0.2, 'ss-40': 1.5}[c]
    t1, t2 = tw, tw + 0.1
    tstop = t2 + 10.0
    d = os.path.join(SCRATCH, 'tb', 'recpad_park')
    os.makedirs(d, exist_ok=True)
    f = os.path.join(d, 'park_%s_%s.dat' % (dut.tag, c))
    L, tp = ampch_bench(c, dut, 'R13 stimulation mode hold: VDD ramp, wait %.1f s, RST_AMP 100 ms, release, hold 10 s with the record switch open' % tw, vdd='Vdd vdd 0 PWL(0 0 1m {VSUP})',
                        rst='Vrst rst_amp 0 PWL(0 0 %g 0 %g {VSUP} %g {VSUP} %g 0)' % (t1, t1 + 1e-6, t2, t2 + 1e-6), sw=('Vsw sw_rec 0 0', 'Vswb sw_rec_b 0 PWL(0 0 1m {VSUP})'))
    ipad = '@r.xrecpad.rser[i]' if REC_LOAD['file'] else None
    L += ['.control', 'save v(out) v(rec) v(vcm)' + ((' ' + ipad) if ipad else ''), 'tran 2m %g 0 2m uic' % tstop,
          'wrdata %s v(out) v(rec) v(vcm)%s' % (f, (' ' + ipad) if ipad else ''), 'echo DONE', 'quit', '.endc', '.end']
    r = list(run_ng([('park_%s_%s' % (dut.tag, c), '\n'.join(L) + '\n')], 'recpad_park', retry=lambda n, t: t.replace('tran 2m ', 'tran 1.4m ').replace(' 0 2m uic', ' 0 1.4m uic'), log=log).values())[0]
    if 'DONE' not in r['out']:
        raise TbError('park run failed: ' + (r['abort'] or r['out'][-300:]))
    t, cols = read_wr(f)
    out, rec, vcm = cols[0], cols[1], cols[2]
    at = lambda y, x: float(np.interp(x, t, y))
    v = {'rec_minus_vcm_uv_end': (at(rec, tstop) - at(vcm, tstop)) * 1e6, 'rec_minus_vcm_uv_before_rst': (at(rec, t1 - 1e-3) - at(vcm, t1 - 1e-3)) * 1e6, 'rec_v_end': at(rec, tstop),
         'vcm_v_end': at(vcm, tstop), 'out_end_v': at(out, tstop), 'out_err_mv_end': abs(at(out, tstop) - 1.65) * 1e3, 'out_err_mv_1s': abs(at(out, t2 + 1.0) - 1.65) * 1e3,
         'out_drift_mv_s': (at(out, tstop) - at(out, tstop - 5.0)) / 5.0 * 1e3}
    if ipad:
        v['i_rec_to_pad_pa'] = at(cols[3], tstop) * 1e12                   # resistor current is positive from rec into the pad
    return v, {'warnings': dut.warnings}


def with_tgate(L):
    """routing TGATE (closed: C = VDD, CBAR = 0) between the electrode model (node rece) and the amplifier input rec"""
    L = [x.replace('Xsrc vd tis rec ref vosr vosf src_randles', 'Xsrc vd tis rece ref vosr vosf src_randles\nXtg rec vdd 0 rece vdd 0 TGATE') for x in L]
    L.insert(L.index([x for x in L if x.startswith('.options')][0]), '.include %s/TGATE/TGATE.spice' % REPO)
    return L


def settle_tg(c, dut, log):
    """host power-up sequence of lptb.settle() with the TGATE in the loop -> .nodeset text (the plain nodesets lead to the latched state of stage 1 in some corners)"""
    tb0, tset = SETTLE_T.get(c, (1.2, 0.8))
    cache = os.path.join(SCRATCH, 'tb', 'settle_tg_%s_%s.ns' % (dut.tag, c))
    if os.path.exists(cache):
        return open(cache).read()
    trel = tb0 + 0.1
    tstop = trel + tset
    nv = os.path.join(SCRATCH, 'tb', 'settle', 'tg_%s_%s.nodev' % (dut.tag, c))
    os.makedirs(os.path.dirname(nv), exist_ok=True)
    L = amp_bench(c, dut, 'R13 power-up with TGATE', opts='abstol=1e-12 chgtol=1e-17', vdd='Vdd vdd 0 PWL(0 0 1m {VSUP})', fs='Vfs fs 0 PWL(0 0 1m {VSUP} %g {VSUP} %g 0)' % (trel, trel + 1e-6),
                  vd='Vd vd 0 dc 0', nodeset=None)
    L = with_tgate(L) + ['.control', 'tran 1m %g 0 1m uic' % tstop, 'wrnodev %s' % nv, 'echo SETTLE_DONE', 'quit', '.endc', '.end']
    r = list(run_ng([('settletg_%s_%s' % (dut.tag, c), '\n'.join(L) + '\n')], 'recpad_settle', retry=lambda n, t: t.replace('tran 1m ', 'tran 0.7m ').replace(' 0 1m uic', ' 0 0.7m uic'), log=log).values())[0]
    if 'SETTLE_DONE' not in r['out'] or not os.path.exists(nv):
        raise TbError('power-up run with TGATE failed: ' + (r['abort'] or r['out'][-300:]))
    ns = []
    for ln in open(nv):
        m = re.match(r'\s*\.ic\s+v\(([^)]+)\)\s*=\s*([-+0-9.eE]+)', ln)
        if m and not m.group(1).lower().endswith('#branch'):
            ns.append('.nodeset v(%s)=%s' % (m.group(1), m.group(2)))
    txt = '\n'.join(ns)
    open(cache, 'w').write(txt)
    return txt


def recac(a, c, log):
    """record path with the routing TGATE closed in front of rec; ac + noise"""
    dut = amp_dut(a.netlist)
    for w in dut.warnings:
        log('WARNING ' + w)
    simple = not dut.pex
    ns = settle_tg(c, dut, log)
    d = os.path.join(SCRATCH, 'tb', 'recpad_recac')
    os.makedirs(d, exist_ok=True)
    fa, fn = os.path.join(d, 'ac_%s_%s.dat' % (dut.tag, c)), os.path.join(d, 'nz_%s_%s.dat' % (dut.tag, c))

    def bench(extra_ctl):
        L = amp_bench(c, dut, 'R13 record path with TGATE', nodeset=ns, opts='abstol=1e-12 chgtol=1e-17')
        return with_tgate(L) + extra_ctl + ['.end']
    ctl = ['.control', 'op', 'echo RESULT_OP vrec=$&v(rec) vout=$&v(out) vrece=$&v(rece)', 'ac dec 100 1e-3 1e7', 'let grec = vdb(rec)-vdb(rece)', 'wrdata %s vdb(out) grec' % fa,
           'meas ac gm find vdb(out) at=12.25', 'noise v(out) Vd dec 100 0.5 300', 'setplot noise2', 'echo RESULT gm_db=$&ac1.gm vo=$&onoise_total', 'echo DONE', 'quit', '.endc']
    r = list(run_ng([('recac_%s_%s' % (dut.tag, c), '\n'.join(bench(ctl)) + '\n')], 'recpad_recac', log=log).values())[0]
    if 'DONE' not in r['out']:
        raise TbError('record-path run failed: ' + (r['abort'] or r['out'][-300:]))
    op = results(r['out'], 'RESULT_OP')[0]
    o = results(r['out'])[0]
    dat = np.loadtxt(fa)
    fr, g, gr = dat[:, 0], dat[:, 1], dat[:, 3]
    vo = o['vo']                                                    # with --rec-load lptb.rec_patch swaps ngspice's nan total for the integral of the spectrum (same lines as tb_amp_noise.py)
    gm = 10 ** (o['gm_db'] / 20)
    gp, ip = float(g.max()), int(g.argmax())
    from tb_amp_ac import xing
    v = {'g_mid_db': o['gm_db'], 'f_lo_hz': xing(fr[:ip + 1], g[:ip + 1], gp - 3, True), 'f_hi_hz': xing(fr[ip:], g[ip:], gp - 3, False), 'noise_tgate_real_uv': vo / gm * 1e6,
         'vrec_dc_v': op['vrec'], 'vout_dc_v': op['vout'], 'vrec_minus_vrece_dc_uv': (op['vrec'] - op['vrece']) * 1e6,
         'rec_node_gain_12hz_db': float(np.interp(math.log10(12.25), np.log10(fr), gr)), 'rec_node_gain_300hz_db': float(np.interp(math.log10(300), np.log10(fr), gr)),
         'f_rec_3db_hz': xing(fr, gr - gr[np.searchsorted(fr, 12.25)], -3, False)}
    return v, {'warnings': dut.warnings}


if __name__ == '__main__':
    mode = sys.argv[1]
    sys.argv = [sys.argv[0]] + sys.argv[2:]
    fun = {'leak': leak, 'park': park, 'recac': recac}[mode]
    if '--out' not in sys.argv:
        sys.exit('r13_extra.py needs --out DIR (results must not go to baseline / sim/post)')

    def run(netlist, corner, a, log):
        a.netlist = netlist
        return fun(a, corner, log)
    sys.exit(cli('r13_' + mode, __doc__, AMP_CORNERS, run))
