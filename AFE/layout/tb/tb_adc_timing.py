#!/usr/bin/env python3
"""tb_adc_timing.py (L1b): analog timing of ONE ADC cell against the comparator-clock chain, the method of AFE/review/scripts/mixcorner.py (closed-loop replay at the maximum SCLK of 3 MHz with the
STA timing of the hardened macro, AFE/review/sim/sta_audit.log; six inputs: range ends and 0.3 LSB above codes 1536, 2048, 2560).
  settle_worst_lsb   largest |s_k| over the 12 trials and the four inputs up to 2.0 V (the range of the INL claim, Decision 43c); s_k = DAC settling alone (a companion run of the same bits with the comparator clock held low): plate minus reference 0.1 ns
                     before the comparator clock would rise, minus its value 0.5 ns before the next DAC edge = what the DAC still had to settle when the comparator fires   (limit 0.5 LSB)
  settle_trial1_lsb, settle_trial2_lsb    the same for the MSB and MSB-1 trials alone;   settle_top_lsb = the two inputs above 2.0 V (2.06 V and 2.15 V at 3.3 V): the slow tail of the
                     accepted top-of-range error (pre-layout 0.47 / 1.45 LSB at ff -40 C 3.6 V), reported
  td_max_ns          slowest decision (clock rise -> the falling comparator output crosses VDD/2; decisions `0` only: an extracted cell has no outn pin), td_avail_ns the window the chain gives
  late               number of decisions slower than available;   failed  runs that did not converge
Corners: typ, ff-40, ss125 = MATCHED analog / digital corners (the D-phase pairing); ss-40x = the MIXED corner of the audit (slow 3.3 V devices at -40 C, 3.6 V, with the fastest standard cells):
0.65 LSB on trial 1 pre-layout, accepted by Decision 44f (same class as Decision 43b).  The rst = rstm single-net reset (I0 mismatch 4) is in every run (the cell has one rst_sw pin).
usage: python3 AFE/layout/tb/tb_adc_timing.py [--netlist schematic|<adc_ch PEX>] [--corner typ|ff-40|ss125|ss-40x|all] [--out DIR]"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lptb import *
import numpy as np

STA = {'a_ff_n40': dict(T0=25.03e-9, DL=7.42e-9, W=3.19e-9, arr=3.62e-9, dtg=1.75e-9), 'a_tt': dict(T0=46.20e-9, DL=13.75e-9, W=5.88e-9, arr=6.01e-9, dtg=3.26e-9),
       'a_ss_125': dict(T0=96.49e-9, DL=28.78e-9, W=12.26e-9, arr=11.48e-9, dtg=6.86e-9)}                      # AFE/review/sim/sta_audit.log (D3 macro); L1d restates them for afe_dig
CAPM = {'a_ff_n40': 0.33e-9, 'a_tt': 0.57e-9, 'a_ss_125': 1.09e-9}
CASE = {'typ': ('typical', 27, 3.3, 'a_tt'), 'ff-40': ('ff', -40, 3.6, 'a_ff_n40'), 'ss125': ('ss', 125, 3.0, 'a_ss_125'), 'ss-40x': ('ss', -40, 3.6, 'a_ff_n40')}
TSETUP = 0.2e-9


def run(netlist, corner, a, log):
    d = adc_env(netlist)
    sys.path.insert(0, os.path.join(ADC, 'scripts'))
    import x2lib as X
    sta = dict(STA)
    if a.sta:                                       # L1d writes AFE/dig/reports/sta_taps.json = {corner: {T0, DL, W, arr, dtg, capm}} in seconds
        for kk, vv in json.load(open(a.sta)).items():
            if kk in sta:
                sta[kk] = {q: vv[q] for q in ('T0', 'DL', 'W', 'arr', 'dtg')}
                CAPM[kk] = vv.get('capm', CAPM[kk])
    X.TIM.update(sta)
    ck = 'lp_' + corner
    X.COR[ck] = CASE[corner]
    mc, temp, vdd, tk = X.COR[ck]
    tim, lsb, T = X.TIM[tk], vdd / 4096, 333.333e-9

    def builder(vin, nock=False):
        def build(lines, meta):
            if nock:
                lines = [('Vck0 ck0 0 0' if l.startswith('Vck0 ') else l) for l in lines]
            L = X.header(ck, 'LP ADC timing', amp=False) + X.supply(vdd, None) + ['Vin0 vin0 vssi %.9g' % vin] + X.adc_cell(0, 'vin0', ref='cref') + lines
            L += X.tail(['v(t0)', 'v(ci0)', 'v(cq0)', 'v(cqn0)', 'v(ck0)'], meta['trel'].max() + 5e-9, '1u', tstep='20p')
            return '\n'.join(L) + '\n'
        return build
    vins = [1.15 * vdd / 3.3, (1536 + 0.3) * lsb, (2048 + 0.3) * lsb, 1.9 * vdd / 3.3, (2560 + 0.3) * lsb, 2.15 * vdd / 3.3]
    cal = X.Cal(vdd)
    tcs = [20e-9, 20e-9 + 250e-6]
    tg = corner.replace('-', 'm')
    exps = [X.Exp('lpt_%s_%d' % (tg, i), ck, 1, tcs, T, builder(v), [[v, v]], cal, resume_last=False) for i, v in enumerate(vins)]
    X.closed_loop(exps, log=lambda s: None, tag='lpt')
    avail = tim['W'] - CAPM[tk] - TSETUP
    ok = [(e, v) for e, v in zip(exps, vins) if not e.failed]
    jobs = []
    for e, v in ok:
        lines, meta = X.schedule(e.adcs, e.tcs, e.bits, e.tim, e.T, e.vdd, ref=e.ref, resume_last=e.resume_last)
        jobs.append((e.name + '_nock', builder(v, nock=True)(lines, meta)))
    rn = X.run_jobs(jobs, tag='lptn') if jobs else {}
    S, TD, late, bad = [], [], 0, len(exps) - len(ok)
    for e, v in ok:
        r = rn[e.name + '_nock']
        if not r['ok']:
            bad += 1
            continue
        w, m, f = e.wave, e.meta, 1
        q = w.v('v(cq0)')
        wn = X.Wave(r['raw'])
        xn = wn.v('v(t0)') - wn.v('v(ci0)')
        s, td = [], []
        for k in range(12):
            tck = m['tck'][0, f, k]
            tend = (m['tdac'][0, f, k + 1] if k < 11 else m['trel'][0, f]) - 0.5e-9
            s.append((np.interp(tck - 0.1e-9, wn.t, xn) - np.interp(tend, wn.t, xn)) / lsb)
            sel = (w.t >= tck) & (w.t <= tck + 40e-9)
            lo = q[sel] < vdd / 2
            if e.dec[0, f, k] == 0 and lo.any():
                td.append(w.t[sel][np.argmax(lo)] - tck)
        S.append(s)
        TD += td
        late += int(np.sum(np.array(td) > avail))
        log('TIMING %s Vin %.5f V code %d (ideal %d): s_k [LSB] %s | slowest decision %.2f ns' % (corner, v, int(e.codes()[0, f]), int(np.floor(v / lsb)), ' '.join('%+.2f' % x for x in s), (max(td) * 1e9 if td else float('nan'))))
        e.wave = None
        try:
            os.remove(r['raw'])
        except OSError:
            pass
    if not S:
        raise TbError('no run finished')
    S = np.abs(np.array(S))
    vok = np.array([v for e, v in ok if rn[e.name + '_nock']['ok']])
    lo = vok <= 2.0 * vdd / 3.3 + 1e-9                   # the claim of Decision 43c ends at 2.0 V (typ): the two inputs above it are the accepted top-of-range error, reported separately
    return ({'settle_worst_lsb': float(S[lo].max()), 'settle_trial1_lsb': float(S[lo][:, 0].max()), 'settle_trial2_lsb': float(S[lo][:, 1].max()), 'settle_top_lsb': float(S[~lo].max()) if (~lo).any() else float('nan'),
             'td_max_ns': float(max(TD) * 1e9) if TD else float('nan'),
             'td_avail_ns': avail * 1e9, 'dac_to_clk_ns': (tim['T0'] - tim['arr']) * 1e9, 'late': float(late), 'failed': float(bad)}, {'timing': tk, 'warnings': d.warnings if d else []})


if __name__ == '__main__':
    sys.exit(cli('adc_timing', __doc__, ('typ', 'ff-40', 'ss125', 'ss-40x'), run, lambda ap: ap.add_argument('--sta', default=None, help='JSON with the tap timing of the hardened afe_dig (L1d); default: the D3 macro numbers')))
