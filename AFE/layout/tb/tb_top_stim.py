#!/usr/bin/env python3
"""tb_top_stim.py (L3b item 2): stimulation mode of one channel wired as module afe_ch: layout cell amp_ch + the record TGATE (E -> rec) + the IPG TGATE (E -> IPG).  After power-up and RST_AMP
in the treat state (record switch open, rec parked on vcm_in), the IPG switch closes and a 130 Hz sine of 2.9 V pp (0.2 .. 3.1 V, inside the rails as the host rule asks) drives the IPG pad
for 100 ms through 1 kOhm; the electrode is the Randles network to the 1.65 V tissue node.  Then the IPG switch opens and, 0.3 s later (the electrode model has then lost the charge the
stimulation left on it; host rule), the record switch closes (the one-shot of the cell fires).
Run twice: without and with 200 pA of pad leakage out of the E and the REF pad (organizer README: about 200 pA for the analog pad).
Values (suffix _leak for the second run): rec_dev_mv (largest |rec - park level| during the stimulation: what the open record switch lets through), out_dev_mv (largest |output - its value
before the stimulation|: the parked amplifier must stay out of the rails), e_swing_v (peak-to-peak at the electrode pad: the stimulation reaches the electrode), e_resid_mv (electrode pad minus
tissue level just before the record start), final_v (output at the end, 6 s after the record start), t_1mv_s (settling after the record start).
usage: python3 AFE/layout/tb/tb_top_stim.py [--netlist schematic|<amp_ch PEX>] [--corner typ|ff85|ss-40|all] [--junction] [--out DIR]"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lptb import *
import numpy as np


def run(netlist, corner, a, log):
    dut = ampch_dut(netlist, a.prdiff)
    vs = CORNERS[corner][2]
    tb0, tset = SETTLE_T.get(corner, (1.2, 0.8))
    tr = tb0 + 0.1
    ts = tr + tset
    te = ts + 0.1
    tc = te + 0.3                      # the electrode model needs about 20 x Rct x Cdl (15 ms) to lose the charge the stimulation left on it (-15 mV after 50 ms: an 11 mV electrode
                                       # drift right after a 3 ms reset rails the output for seconds; AUDIT 4.7: no recording between stimulation pulses)
    tstop = tc + 6.0
    d = os.path.join(SCRATCH, 'tb', 'top_stim')
    os.makedirs(d, exist_ok=True)
    jobs = []
    for tag, leak in (('', 0.0), ('_leak', 200e-12)):
        f = os.path.join(d, 'st_%s_%s%s.dat' % (dut.tag, corner, tag))
        L, tp = ampch_bench(corner, dut, 'stimulation mode, pad leakage %g A' % leak, vdd='Vdd vdd 0 PWL(0 0 1m {VSUP})',
                            rst='Vrst rst_amp 0 PWL(0 0 1m {VSUP} %g {VSUP} %g 0)' % (tr, tr + 1e-6),
                            sw=('Vsw sw_rec 0 PWL(0 0 %g 0 %g {VSUP})' % (tc, tc + 1e-7), 'Vswb sw_rec_b 0 PWL(0 0 1m {VSUP} %g {VSUP} %g 0)' % (tc, tc + 1e-7)))
        L = [x.replace('Xsrc vd tis rec ref vosr vosf src_randles', 'Xsrc vd tis epad ref vosr vosf src_randles\nXtgr rec sw_rec sw_rec_b epad vdd 0 TGATE\nXtgi ipg sw_ipg sw_ipg_b epad vdd 0 TGATE') for x in L]
        L.insert(L.index([x for x in L if x.startswith('.options')][0]), '.include %s/TGATE/TGATE.spice' % REPO)
        L += ['Vswi sw_ipg 0 PWL(0 0 %g 0 %g {VSUP} %g {VSUP} %g 0)' % (ts - 1e-3, ts - 1e-3 + 1e-7, te + 1e-3, te + 1e-3 + 1e-7),
              'Vswib sw_ipg_b 0 PWL(0 0 1m {VSUP} %g {VSUP} %g 0 %g 0 %g {VSUP})' % (ts - 1e-3, ts - 1e-3 + 1e-7, te + 1e-3, te + 1e-3 + 1e-7),
              'Bstim stim 0 V = 1.65 + 1.45*sin(6.2831853*130*(time-%g))*(time>%g)*(time<%g)' % (ts, ts, te), 'Rstim stim ipg 1k', 'Ileak_e epad 0 %g' % leak, 'Ileak_r ref 0 %g' % leak,
              '.control', 'save v(out) v(rec) v(epad) v(vcm)', 'tran 100u %g 0 100u uic' % tstop, 'wrdata %s v(out) v(rec) v(epad) v(vcm)' % f, 'echo DONE', 'quit', '.endc', '.end']
        jobs.append(('st_%s_%s%s' % (dut.tag, corner, tag), '\n'.join(L) + '\n'))
    res = run_ng(jobs, 'top_stim', retry=lambda n, t: t.replace(' 0 100u uic', ' 0 70u uic'), log=log)
    v = {}
    for (jn, _), tag in zip(jobs, ('', '_leak')):
        if 'DONE' not in res[jn]['out']:
            raise TbError('run %s did not finish: %s' % (jn, res[jn]['abort'] or res[jn]['out'][-300:]))
        t, (out, rec, e, vcm) = read_wr(os.path.join(d, 'st_%s_%s%s.dat' % (dut.tag, corner, tag)))
        st = (t >= ts) & (t <= te)
        pre = float(np.interp(ts - 2e-3, t, out))
        fin = float(out[t > tstop - 0.15].mean())
        bad = np.where((t > tc) & (np.abs(out - fin) > 1e-3))[0]
        v['rec_dev_mv' + tag] = float(np.abs(rec[st] - vcm[st]).max() * 1e3)
        v['out_dev_mv' + tag] = float(np.abs(out[st] - pre).max() * 1e3)
        v['e_swing_v' + tag] = float(e[st].max() - e[st].min())
        v['final_v' + tag] = fin
        v['e_resid_mv' + tag] = float((np.interp(tc - 1e-3, t, e) - 1.65) * 1e3)
        v['t_1mv_s' + tag] = float(t[bad[-1]] - tc) if len(bad) and bad[-1] < len(t) - 2 else (0.0 if not len(bad) else float('nan'))
    return v, {'warnings': dut.warnings}


if __name__ == '__main__':
    sys.exit(cli('top_stim', __doc__, AMP_CORNERS, run))
