#!/usr/bin/env python3
"""tb_amp_reset.py (L2b): record start on the layout cell amp_ch with its REAL one-shot (inside the cell; Decisions 36 / 38) and the routing TGATE in front of it (TGATE/TGATE.spice,
wired as in module afe_ch: OUT = rec, IN = electrode, C = sw_rec, CBAR = sw_rec_b).  Sequence: power-up in the treat state (record switch open, rec parked on vcm_in), RST_AMP as the host
does, release, settle; at T0 the record switch closes: the park opens, rec jumps from the park level to the electrode level (tissue 1.65 V + the electrode offset OS, present from the
start), and the closing edge fires the one-shot (reset pulse about 3.6 / 1.9 / 6.9 ms).  OS = 0 (only the 1.1 mV between park level and tissue, and the switch injection), 1 mV, 10 mV, 100 mV.
Values per OS (suffix _os0, _os1m, _os10m, _os100m):
  t_fs_ms      width of the reset pulse = time the timer node of the one-shot stays above VDD/2 after the edge (needs the anchor node of C_T; else nan)
  peak_mv      largest |output - final value| after the pulse has ended
  rel_step_mv  output change across the release of the reset (0.2 ms before to 1 ms after the end of the pulse)
  t_1mv_s      time after T0 from which the output stays within 1 mV of its final value (final = mean of the last 5 % of the run); nan = not inside the run
  final_v, resid_end_mv (|output at the end - final value|, shows a run that is still drifting), drift_mv_s (output slope between 3 s and 5 s after T0: the junction convention drifts by
               about 1 mV/s per mV of electrode offset because the capacitor leakage then sets the DC state)
Pre-layout reference with an IDEAL 3 ms pulse and no TGATE (AFE/amp/sim/a4c_rec.log): 1 mV 0.13-0.27 s, 10 mV 3.4-4.7 s, 100 mV 7.3-9.0 s (accepted, Decision 38b); release step <= 0.14 mV.
--host-rst 0.1: the host also sets RST_AMP for 0.1 s from T0 (the record-start rule that ACCEPT.md pre-approves); then peak / release step / settling are counted from the end of that pulse.
usage: python3 AFE/layout/tb/tb_amp_reset.py [--netlist schematic|<amp_ch PEX>] [--corner typ|ff85|ss-40|all] [--junction] [--os 0,1m,10m,100m] [--host-rst 0.1] [--out DIR]"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lptb import *
import numpy as np

TSTOP = {'0': 6.0, '1m': 6.0, '10m': 12.0, '100m': 40.0}


def run(netlist, corner, a, log):
    dut = ampch_dut(netlist, a.prdiff)
    vs = CORNERS[corner][2]
    tb0, tset = SETTLE_T.get(corner, (1.2, 0.8))
    tr = tb0 + 0.1                       # RST_AMP release
    t0 = tr + tset                       # the record switch closes
    jobs, files = [], {}
    hr = float(a.host_rst)               # host-issued RST_AMP pulse at the record start [s]; 0 = only the one-shot of the cell
    d = os.path.join(SCRATCH, 'tb', 'amp_reset')
    os.makedirs(d, exist_ok=True)
    for os_ in a.os.split(','):
        v = float(os_.replace('m', 'e-3'))
        tstop = t0 + TSTOP.get(os_, 12.0)
        f = os.path.join(d, 'rs_%s_%s_%s.dat' % (dut.tag, corner, os_))
        files[os_] = (f, t0, tstop)
        L, tp = ampch_bench(corner, dut, 'record start with the real one-shot and the routing TGATE, electrode offset %s V' % os_, vdd='Vdd vdd 0 PWL(0 0 1m {VSUP})',
                            rst='Vrst rst_amp 0 PWL(0 0 1m {VSUP} %g {VSUP} %g 0%s)' % (tr, tr + 1e-6, (' %g 0 %g {VSUP} %g {VSUP} %g 0' % (t0, t0 + 1e-6, t0 + hr, t0 + hr + 1e-6)) if hr else ''),
                            sw=('Vsw sw_rec 0 PWL(0 0 %g 0 %g {VSUP})' % (t0, t0 + 1e-7), 'Vswb sw_rec_b 0 PWL(0 0 1m {VSUP} %g {VSUP} %g 0)' % (t0, t0 + 1e-7)),
                            vos=('Vosr vosr 0 %g' % v, 'Vosf vosf 0 0'), probes=('ct',))
        # the electrode model drives the node `rece`; the routing TGATE sits between it and rec
        L = [x.replace('Xsrc vd tis rec ref vosr vosf src_randles', 'Xsrc vd tis rece ref vosr vosf src_randles\nXtg rec sw_rec sw_rec_b rece vdd 0 TGATE') for x in L]
        L.insert(L.index([x for x in L if x.startswith('.options')][0]), '.include %s/TGATE/TGATE.spice' % REPO)
        ct = tp.get('ct')
        L += ['.control', 'save v(out)%s' % ((' v(%s)' % ct) if ct else ''), 'tran 200u %g 0 200u uic' % tstop, 'wrdata %s v(out)%s' % (f, (' v(%s)' % ct) if ct else ''), 'echo DONE', 'quit', '.endc', '.end']
        jobs.append(('rs_%s_%s_%s' % (dut.tag, corner, os_), '\n'.join(L) + '\n'))
    res = run_ng(jobs, 'amp_reset', retry=lambda n, t: t.replace(' 0 200u uic', ' 0 140u uic'), log=log)
    v = {}
    for (jn, _), os_ in zip(jobs, a.os.split(',')):
        f, t0, tstop = files[os_]
        if 'DONE' not in res[jn]['out']:
            raise TbError('run %s did not finish: %s' % (jn, res[jn]['abort'] or res[jn]['out'][-300:]))
        t, cols = read_wr(f)
        out = cols[0]
        fin = float(out[t > tstop - 0.05 * (tstop - t0)].mean())
        tfs = float('nan')
        if len(cols) > 1:
            c = cols[1]
            i = np.where((t > t0) & (c < vs / 2))[0]
            if len(i):
                tfs = float(t[i[0]] - t0)
        te = t0 + max(tfs if tfs == tfs else 0.01, hr)
        after = t > te + 1e-3
        dev = np.abs(out - fin)
        bad = np.where((t > t0) & (dev > 1e-3))[0]
        t1 = float(t[bad[-1]] - t0) if len(bad) else 0.0
        if len(bad) and bad[-1] >= len(t) - 2:
            t1 = float('nan')
        k = '_os' + os_
        v['t_fs_ms' + k] = tfs * 1e3
        v['peak_mv' + k] = float(dev[after].max() * 1e3)
        v['rel_step_mv' + k] = float((np.interp(te + 1e-3, t, out) - np.interp(te - 2e-4, t, out)) * 1e3)
        v['t_1mv_s' + k] = t1
        v['final_v' + k] = fin
        if tstop - t0 >= 5.0:
            v['drift_mv_s' + k] = float((np.interp(t0 + 5.0, t, out) - np.interp(t0 + 3.0, t, out)) / 2.0 * 1e3)
        v['resid_end_mv' + k] = float(abs(out[-1] - fin) * 1e3)
    return v, {'warnings': dut.warnings, 'probe_ct': bool(dut.probes.get('ct')) if dut.pex else True}


if __name__ == '__main__':
    def more(ap):
        ap.add_argument('--os', default='0,1m,10m,100m')
        ap.add_argument('--host-rst', dest='host_rst', default='0', help='seconds of RST_AMP issued by the host at the record start (0.1 = the pre-approved record-start rule of ACCEPT.md); results go to amp_reset_host*.json')
    import lptb
    _cli = lptb.cli

    def cli2(check, doc, corners, run, extra):
        if '--host-rst' in sys.argv and sys.argv[sys.argv.index('--host-rst') + 1] not in ('0', '0.0'):
            check += '_host'
        return _cli(check, doc, corners, run, extra)
    sys.exit(cli2('amp_reset', __doc__, AMP_CORNERS, run, more))
