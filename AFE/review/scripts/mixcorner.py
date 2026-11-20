#!/usr/bin/env python3
"""AUDIT step 4 / 8: ADC timing at MIXED corners (never simulated: D4 / I2 / X2 always paired analog ff with digital ff and ss with ss).
The comparator-clock chain is built from 7t5v0 standard cells (5 V thick-oxide devices); the DAC drivers, switches and the comparator are 3.3 V devices.
The two device families are only partly correlated, so the worst case for the analog-digital timing is: FASTEST std-cell timing (shortest DAC -> comparator time T0 - arr and
shortest decision window W) with SLOW 3.3 V devices (slowest DAC settling, slowest comparator).  Also fs / sf (never run).
Method: X2 closed-loop PWL replay (AFE/adc/scripts/x2lib.py, read only; scratch redirected to AFE/review/.ptmp), ONE ADC cell, ideal supply and input, SCLK 3 MHz,
STA timing from AFE/review/sim/sta_audit.log (current netlist).  Per trial k (frame 2 of 2):
  s_k  = DAC settling alone (companion run of the same replayed bits with the comparator clock held at 0): (plate - ref) 0.1 ns before the instant the comparator clock would rise
         MINUS its value 0.5 ns before the next DAC edge = what the DAC still had to settle when the comparator fires [LSB]
  td_k = comparator clock rise -> first output below VDD/2 (decision time); available = cap - rise - flop setup (STA: tapw arrives before the window end)
usage: python3 mixcorner.py [out.log]"""
import sys, os, time
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from ngjob import REV, AFE, AMP, ADC, PT, PDKNG
sys.path.insert(0, os.path.join(ADC, 'scripts'))
import numpy as np
import x2lib as X
X.PT = os.path.join(PT, 'x2')            # scratch + slots under AFE/review/.ptmp (audit rule 3)
os.makedirs(X.PT, exist_ok=True)
MD = os.path.join(PT, 'mixmodels')
os.makedirs(MD, exist_ok=True)
for c in ('fs', 'sf'):
    open(os.path.join(MD, 'models_%s.spice' % c), 'w').write('* audit: %s MOS corner, typical MIM / resistors\n.include %s/design.ngspice\n.lib %s/sm141064.ngspice %s\n.lib %s/sm141064.ngspice mimcap_typical\n.lib %s/sm141064.ngspice res_typical\n' % (c, PDKNG, PDKNG, c, PDKNG, PDKNG))
# STA of the CURRENT netlist (sim/sta_audit.log): T0, Delta, W, latest gp/gn arrival; dtg = tg_on - rst_sw; capm = window end - capture clock arrival
X.TIM.update({'a_ff_n40': dict(T0=25.03e-9, DL=7.42e-9, W=3.19e-9, arr=3.62e-9, dtg=1.75e-9), 'a_ff_125': dict(T0=36.93e-9, DL=10.97e-9, W=4.65e-9, arr=5.02e-9, dtg=2.58e-9),
              'a_tt': dict(T0=46.20e-9, DL=13.75e-9, W=5.88e-9, arr=6.01e-9, dtg=3.26e-9), 'a_ss_125': dict(T0=96.49e-9, DL=28.78e-9, W=12.26e-9, arr=11.48e-9, dtg=6.86e-9)})
CAPM = {'a_ff_n40': 0.33e-9, 'a_ff_125': 0.45e-9, 'a_tt': 0.57e-9, 'a_ss_125': 1.09e-9}
TSETUP = 0.2e-9          # ESTIMATE of the dffq_1 setup time (liberty: 0.1-0.3 ns)
CASES = [  # key: (analog corner, T, VDD, digital timing corner), note
    ('ff-40m', ('ff', -40, 3.6, 'a_ff_n40'), 'MATCHED reference (the D4 / X2 pairing)'),
    ('tt-40x', ('typical', -40, 3.6, 'a_ff_n40'), 'mixed: typical 3.3 V devices, fastest std cells'),
    ('ss-40x', ('ss', -40, 3.6, 'a_ff_n40'), 'MIXED worst: slow 3.3 V devices, fastest std cells'),
    ('fs-40x', ('fs', -40, 3.6, 'a_ff_n40'), 'fs (never run), fastest std cells'),
    ('sf-40x', ('sf', -40, 3.6, 'a_ff_n40'), 'sf (never run), fastest std cells'),
    ('ss125x', ('ss', 125, 3.6, 'a_ff_125'), 'MIXED hot: slow 3.3 V devices, ff_125C std cells'),
    ('tt27m', ('typical', 27, 3.3, 'a_tt'), 'MATCHED typical (reference)'),
    ('ff125s', ('ff', 125, 3.0, 'a_ss_125'), 'mixed the other way: fast 3.3 V devices, slowest std cells (window end check)'),
]
for k, v, _ in CASES:
    X.COR[k] = v


def header(ck, extra=()):
    corner, temp, vdd, _ = X.COR[ck]
    mod = '%s/spice/models_%s.spice' % (AMP, corner) if corner in ('typical', 'ff', 'ss') else os.path.join(MD, 'models_%s.spice' % corner)
    L = ['* audit mixed-corner ADC run (%s: %s %g C, VDD %g V, timing %s)' % (ck, corner, temp, vdd, X.COR[ck][3]), '.include ' + mod]
    L += ['.include %s/spice/%s.spice' % (ADC, f) for f in ('dac_units', 'dac_sw', 'comparator_params', 'comparator', 'vhalf')]
    L += list(extra)
    L += ['.options gmin=1e-16 abstol=1e-12 reltol=1e-4 vntol=1e-7 chgtol=1e-17 itl1=500 itl4=500', '.temp %g' % temp]
    return L


def builder(ck, vin, extra=(), nock=False):
    """nock = True: the comparator clock source is replaced by 0 V (the comparator never fires): the plate waveform is then the DAC settling alone (D4 settle method)."""
    vdd = X.COR[ck][2]

    def build(lines, meta):
        if nock:
            lines = [('Vck0 ck0 0 0' if l.startswith('Vck0 ') else l) for l in lines]
        L = header(ck, extra) + X.supply(vdd, None) + ['Vin0 vin0 vssi %.9g' % vin] + X.adc_cell(0, 'vin0', ref='cref') + lines
        L += X.tail(['v(t0)', 'v(ci0)', 'v(cq0)', 'v(cqn0)', 'v(ck0)'], meta['trel'].max() + 5e-9, '1u', tstep='20p')
        return '\n'.join(L) + '\n'
    return build


def run_case(ck, note, P, extra=(), tag=''):
    corner, temp, vdd, tk = X.COR[ck]
    tim = X.TIM[tk]
    lsb = vdd / 4096
    T = 333.333e-9
    # inputs: range ends and 0.3 LSB above the levels of codes 1536, 2048, 2560 (as I2), all scaled with VDD
    vins = [1.15 * vdd / 3.3, (1536 + 0.3) * lsb, (2048 + 0.3) * lsb, 1.9 * vdd / 3.3, (2560 + 0.3) * lsb, 2.15 * vdd / 3.3]
    cal = X.Cal(vdd)
    tcs = [20e-9, 20e-9 + 250e-6]
    exps = [X.Exp('%s%s_%d' % (ck.replace('-', 'm'), tag, i), ck, 1, tcs, T, builder(ck, v, extra), [[v, v]], cal, resume_last=False) for i, v in enumerate(vins)]
    t0 = time.time()
    X.closed_loop(exps, log=lambda s: None, tag='mix')
    avail = tim['W'] - CAPM[tk] - TSETUP
    P('\n== %s%s  %s %g C  VDD %.1f V  timing %s  (%s)' % (ck, tag, corner, temp, vdd, tk, note) + (('  TESTBENCH OVERRIDE: ' + ' '.join(extra)) if extra else ''))
    P('   DAC edge -> comparator clock %.2f ns; window W %.2f ns; decision time available (cap - rise - setup) %.2f ns; wall %.0f s' % ((tim['T0'] - tim['arr']) * 1e9, tim['W'] * 1e9, avail * 1e9, time.time() - t0))
    worst_s = 0.0
    worst_td = 0.0
    nbad = 0
    nlate = 0
    # companion runs WITHOUT the comparator clock: same replayed bits, DAC settling alone
    ok = [(e, v) for e, v in zip(exps, vins) if not e.failed]
    for e, v in ok:
        e.build_nock = builder(ck, v, extra, nock=True)
    jobs = []
    for e, v in ok:
        lines, meta = X.schedule(e.adcs, e.tcs, e.bits, e.tim, e.T, e.vdd, ref=e.ref, resume_last=e.resume_last)
        jobs.append((e.name + '_nock', e.build_nock(lines, meta)))
    rn = X.run_jobs(jobs, tag='mixn') if jobs else {}
    for e, v in zip(exps, vins):
        if e.failed:
            P('   Vin %.5f V: FAILED %s' % (v, e.failed[:200]))
            nbad += 1
            continue
        w = e.wave
        m = e.meta
        f = 1
        q = w.v('v(cq0)')
        qn = w.v('v(cqn0)')
        r = rn[e.name + '_nock']
        if not r['ok']:
            P('   Vin %.5f V: no-clock run FAILED %s' % (v, r['tail'][:200]))
            nbad += 1
            continue
        wn = X.Wave(r['raw'])
        xn = wn.v('v(t0)') - wn.v('v(ci0)')
        s = []
        td = []
        for k in range(12):
            tck = m['tck'][0, f, k]
            tend = (m['tdac'][0, f, k + 1] if k < 11 else m['trel'][0, f]) - 0.5e-9
            s.append((np.interp(tck - 0.1e-9, wn.t, xn) - np.interp(tend, wn.t, xn)) / lsb)
            sel = (w.t >= tck) & (w.t <= tck + 40e-9)
            lo = np.minimum(q[sel], qn[sel]) < vdd / 2
            td.append((w.t[sel][np.argmax(lo)] - tck) if lo.any() else float('nan'))
        s = np.array(s)
        td = np.array(td)
        late = int(np.sum(~(td <= avail)))
        nlate += late
        worst_s = max(worst_s, np.abs(s).max())
        worst_td = max(worst_td, np.nanmax(td))
        P('   Vin %.5f V code %4d (ideal %4d, diff %+d) passes %d unres %d | DAC-only s_k [LSB] trial 1..12: %s | max|s| %.2f at trial %d | td max %.2f ns (trial %d), decisions later than available: %d' % (
            v, int(e.codes()[0, f]), int(np.floor(v / lsb)), int(e.codes()[0, f]) - int(np.floor(v / lsb)), e.npass, int(e.unres.sum()), ' '.join('%+.2f' % a for a in s), np.abs(s).max(), int(np.abs(s).argmax()) + 1,
            np.nanmax(td) * 1e9, int(np.nanargmax(td)) + 1, late))
        e.wave = None
        try:
            os.remove(r['raw'])
        except OSError:
            pass
    P('   VERDICT %s%s: worst unsettled plate at a comparator clock %.2f LSB (limit 0.5): %s;  slowest decision %.2f ns vs %.2f ns available: %s;  failed runs %d' % (
        ck, tag, worst_s, 'PASS' if worst_s <= 0.5 else 'FAIL', worst_td * 1e9, avail * 1e9, 'PASS' if nlate == 0 else 'FAIL (%d late)' % nlate, nbad))
    return worst_s, worst_td


if __name__ == '__main__':
    out = open(sys.argv[1], 'a') if len(sys.argv) > 1 else sys.stdout
    P = lambda s: (print(s, file=out), out.flush())
    sel = sys.argv[2].split(',') if len(sys.argv) > 2 else None
    P(__doc__.split('usage')[0].strip())
    for k, v, note in CASES:
        if sel and k not in sel:
            continue
        run_case(k, note, P)
    if not sel or 'ca' in sel:
        # what-if: the 40 fF preamp capacitors of cmp_p are IDEAL in the netlist and 40 fF is below the smallest legal MIM (5 x 5 um = 54.5 fF): one legal unit per node
        run_case('tt27m', 'what-if: CMP_CA = 54.5 fF (one legal 5x5 um MIM unit per preamp node)', P, extra=('.param CMP_CA=54.5f',), tag='_ca54')
        run_case('ss-40x', 'what-if: CMP_CA = 54.5 fF at the mixed worst corner', P, extra=('.param CMP_CA=54.5f',), tag='_ca54')
    if out is not sys.stdout:
        out.close()
