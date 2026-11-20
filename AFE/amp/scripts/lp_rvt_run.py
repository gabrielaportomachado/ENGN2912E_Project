#!/usr/bin/env python3
"""LP step 6 (M7): full-channel verification of follower variants against the ORIGINAL netlist, same script, same session.
usage: python3 lp_rvt_run.py <stage> [variant,variant,...]          variants = names of lp_rvt_lib.CAND, 'orig', or 'rvt' (= the committed spice/ota2_rvt.spice + afe_chc_rvt.spice)
stages (each writes AFE/amp/sim/lp_rvt_<stage>.log + lp_rvt_<stage>.json + the complete ngspice outputs lp_rvt_<stage>_nglogs.tgz):
  tables   .op (currents, o2, follower), .ac (gain, f_lo, f_hi), .noise 0.5-300 Hz (fnoicor 0 and 1, IDEAL RESISTOR (noise) as Decision 8), stage-1 loop (Tian, real stage 2 as load),
           stage-2 OTA + follower open loop (A0, GBW, PM at beta = 1 and at the real beta), supply -> output gain (PSRR path) at 50 Hz; typ 27 / ff 85 / ss -40, 3.3 V
  swing    transient +-0.5 mV (and 0.55 / 0.6 mV) at 12.25 Hz, 8 s, and +-0.5 mV at 300 Hz: gain, THD, output and o2 extremes
  adc245   ideal ADC load model (C_s 17 pF behind 1 kOhm, no reset, +-0.24 V away, T_ACQ 245 us): error at the end of the window   (the A4b check behind Decision 37)
  settle   REAL sampling TG + split 6+6 DAC + cmp_p on the output (D5 method: loaded copy minus unloaded copy): error at the next CS falling, kick spike
  settle_tight   4 of the settle cases again with 100x tighter tolerances (removes the DC-solve difference between the two copies)
  slew     +-0.5 mV electrode steps: maximum slope, 10-90 % rise time
  rec      reset-pulse recovery (ideal 3 ms pulse, 10 mV electrode step): release step and time to within 1 mV   (sanity: the gate-switched reset is not touched by the variant)
  pur      power-up from 0 V with the host reset (RST_AMP 100 ms at 3 s): the latch at power-up and its clearing (sanity)
Every testbench is the existing one of AFE/amp/tb (read only).  Transients: `.options abstol=1e-12` (Decision 43a), one ngspice thread, slot.sh, at most 2 jobs at a time.
"""
import sys
from lp_rvt_lib import *

sys.path.insert(0, os.path.join(ADC, 'scripts'))
TIGHT_OPT = '.options gmin=1e-16 abstol=1e-12 reltol=1e-6 vntol=1e-9 chgtol=1e-17 itl1=2000 itl4=500'      # 100x tighter voltage tolerances; abstol stays 1e-12 (1e-15 aborts at the first switching event: Decision 43a)
COLS = ["time", "out", "v1", "vn1", "vn2", "o2", "rec", "vbn", "isup", "cs", "idm", "idb1", "fs", "vrs", "gm1", "gm2"]      # tb_a4c_tran.spice wrdata order (scripts/a4c_lib.py)


def tcsv(path):
    a = np.loadtxt(path, skiprows=1)
    return {c: a[:, i] for i, c in enumerate(COLS[:a.shape[1]])}


def at(t, y, x):
    return float(np.interp(x, t, y))


def vname(v):
    if v.endswith('+dio'):
        return '%s = %s with the parasitic p-well / deep-n-well junction as diode_pw2dw (area %g um2, perimeter %g um, ESTIMATE) from out to vdd at testbench level' % (v, base(v), DIO_AREA * 1e12, DIO_PJ * 1e6)
    return 'orig = spice/ota2.spice (nfet_06v0_nvt 10u/2u, bulk vss)' if v == 'orig' else (
        'rvt = spice/ota2_rvt.spice + afe_chc_rvt.spice (nfet_03v3 8 x 10u/1u, isolated p-well, bulk = source)' if v == 'rvt' else '%s: %s' % (v, CAND[v][5]))


# ------------------------------------------------------------------ tables
PSRR_CTL = ['ac dec 10 1e-2 1e5', 'let a = mag(v(out))', 'meas ac a_dc find a at=0.05', 'meas ac a_50 find a at=50', 'meas ac a_60 find a at=60', 'meas ac a_300 find a at=300',
            'meas ac a_1k find a at=1k', 'meas ac a_10k find a at=10k', 'echo RESULT vdd2out_dc=$&a_dc vdd2out_50Hz=$&a_50 vdd2out_60Hz=$&a_60 vdd2out_300Hz=$&a_300 vdd2out_1k=$&a_1k vdd2out_10k=$&a_10k', 'quit']
# stage-2 OTA + follower open loop: PM at beta = 1 (worst-case bound, as A4a) and at the real feedback factor beta = CF2 / (CIN2 + CF2) = 0.294 / 3.294 (1 / beta = 20.99 dB; the pair's Cgg is neglected)
OL2_CTL = ['ac dec 40 1e-3 1e8', 'let gdb = vdb(out)', 'let gph = cph(out)*180/pi', 'meas ac a0 find gdb at=0.01', 'let tgt = a0 - 3', 'meas ac f_p1 when gdb=tgt fall=1',
           'meas ac gbw when gdb=0 fall=1', 'meas ac ph_u find gph at=$&gbw', 'let pm = 180 + ph_u', 'meas ac f_b when gdb=20.99 fall=1', 'meas ac ph_b find gph at=$&f_b', 'let pmb = 180 + ph_b',
           'echo RESULT a0_dB=$&a0 f_p1_Hz=$&f_p1 gbw_Hz=$&gbw pm_beta1_deg=$&pm f_loop_Hz=$&f_b pm_beta_real_deg=$&pmb', 'quit']
OPX = ['let idf = abs(@m.xch.xs2.xota2.xmf.m0[id])', 'let vgsf = @m.xch.xs2.xota2.xmf.m0[vgs]', 'let vthf = @m.xch.xs2.xota2.xmf.m0[vth]', 'let vdsf = @m.xch.xs2.xota2.xmf.m0[vds]',
       'let gmf = @m.xch.xs2.xota2.xmf.m0[gm]', 'let vbsf = @m.xch.xs2.xota2.xmf.m0[vbs]', 'let vsd4 = abs(@m.xch.xs2.xota2.xm4.m0[vds])', 'let vdsat4 = abs(@m.xch.xs2.xota2.xm4.m0[vdsat])',
       'let ids = abs(@m.xch.xs2.xota2.xms.m0[id])',
       'echo OPFOL id_A=$&idf vgs_V=$&vgsf vth_V=$&vthf vds_V=$&vdsf vbs_V=$&vbsf gm_S=$&gmf m4_vsd_V=$&vsd4 m4_vdsat_V=$&vdsat4 sink_id_A=$&ids']


def stage_tables(variants):
    P = Log(os.path.join(SIM, 'lp_rvt_tables.log'))
    P(__doc__.split('usage')[0].strip())
    P('STAGE tables: typ 27 / ff 85 / ss -40 C, 3.3 V.  Testbenches: tb_a4c_op / tb_a4c_ac / tb_a4c_noise / tb_a4c_loop (FSV = 0), tb_ota2_ol (stage-2 OTA alone, IDEAL DC servo, CL 10 pF as A4a),')
    P('  psrr = tb_a4c_ac with the AC source moved from the electrode to VDD (as tb_afe_1ch_psrr.spice of A4b).  Noise: IDEAL RESISTOR (noise) RFIX / RFIX2 per corner (a4c_noise.log headers).')
    jobs = []
    for v in variants:
        for (k, T) in CORNERS:
            tg = '%s_%s_%g' % (v, k, T)
            t = deck('tb_a4c_op.spice', k, T, v)
            i = t.rindex('quit')
            jobs.append(('op_' + tg, t[:i] + '\n'.join(OPX) + '\n' + t[i:]))
            jobs.append(('ac_' + tg, deck('tb_a4c_ac.spice', k, T, v)))
            for fn in (0, 1):
                jobs.append(('noise%d_%s' % (fn, tg), deck('tb_a4c_noise.spice', k, T, v, params=dict(RFIX=RFIX[(k, T)][0], RFIX2=RFIX[(k, T)][1], FN=fn), dio_as_cap=True)))
            jobs.append(('loop_' + tg, deck('tb_a4c_loop.spice', k, T, v, params=dict(FSV=0, NSVRS=NSVRS[(k, T)]))))
            jobs.append(('ol2_' + tg, deck('tb_ota2_ol.spice', k, T, v, control=OL2_CTL)))
            tp = open(os.path.join(AMP, 'tb', 'tb_a4c_ac.spice')).read().replace('Vdd vdd 0 {VSUP}', 'Vdd vdd 0 {VSUP} ac 1').replace('Vd vd 0 dc 0 ac 1', 'Vd vd 0 dc 0 ac 0')
            jobs.append(('psrr_' + tg, deck(None, k, T, v, tbtext=tp, control=PSRR_CTL)))
    res = run_jobs(jobs, 'tables', log=lambda s: None)
    R = {}
    for v in variants:
        R[v] = {}
        for (k, T) in CORNERS:
            tg = '%s_%s_%g' % (v, k, T)
            d = {}
            o = res['op_' + tg]['out']
            for key in ('OPSUM', 'OPNODE', 'OPFOL'):
                r = results(o, key)
                if r:
                    d.update(r[0])
            for nm, key in (('ac_', 'RESULT'), ('loop_', 'RESULT'), ('ol2_', 'RESULT'), ('psrr_', 'RESULT')):
                r = results(res[nm + tg]['out'], key)
                if r:
                    d.update(r[0])
                else:
                    d[nm + 'FAILED'] = res[nm + tg]['abort'][:200]
            for fn in (0, 1):
                r = results(res['noise%d_%s' % (fn, tg)]['out'], 'NOISE_B_0p5_300')
                if r:
                    d['noise_fn%d_uV' % fn] = r[0]['vn_in_mid_V'] * 1e6
                r = results(res['noise%d_%s' % (fn, tg)]['out'], 'NOISE_C_0p5_2k')
                if r:
                    d['noise_2k_fn%d_uV' % fn] = r[0]['vn_in_mid_V'] * 1e6
            R[v][CKEY[(k, T)]] = d
    g = lambda v, c, key, sc=1.0: (R[v][c].get(key, float('nan')) * sc) if isinstance(R[v][c].get(key, float('nan')), float) else float('nan')
    rows = [('supply current (bias + channel) [uA]', 'i_supply_A', 1e6, '%.2f'), ('output DC error out - vcm_out [mV]', 'vout_err_V', 1e3, '%.3f'), ('o2 (stage-2 OTA output) [V]', 'o2_V', 1, '%.4f'),
            ('follower Vgs [V]', 'vgs_V', 1, '%.4f'), ('follower Vth [V]', 'vth_V', 1, '%.4f'), ('follower Vbs [V]', 'vbs_V', 1, '%.4f'), ('follower Id, all fingers [uA]', 'id_A', 1e6, '%.4f'),
            ('follower gm, all fingers [uS]', 'gm_S', 1e6, '%.2f'), ('follower sink Id (6 x 16u/4u) [uA]', 'sink_id_A', 1e6, '%.4f'), ('mirror M4: Vsd [V]', 'm4_vsd_V', 1, '%.3f'), ('mirror M4: Vdsat [V]', 'm4_vdsat_V', 1, '%.3f'),
            ('mid-band gain [dB] (60 +- 1)', 'g_mid_dB', 1, '%.4f'), ('f_lo [Hz] (<= 0.5)', 'f_lo_Hz', 1, '%.4f'), ('f_hi [Hz] (>= 300)', 'f_hi_Hz', 1, '%.2f'), ('gain at 300 Hz [dB]', 'g_300_dB', 1, '%.3f'),
            ('noise 0.5-300 Hz, fnoicor 0 [uV] (<= 2)', 'noise_fn0_uV', 1, '%.4f'), ('noise 0.5-300 Hz, fnoicor 1 [uV] (report)', 'noise_fn1_uV', 1, '%.4f'), ('noise 0.5 Hz-2 kHz, fnoicor 0 [uV]', 'noise_2k_fn0_uV', 1, '%.4f'),
            ('stage-1 loop: T at 100 Hz [dB]', 'T_100Hz_dB', 1, '%.3f'), ('stage-1 loop: fu [kHz]', 'fu_Hz', 1e-3, '%.1f'), ('stage-1 loop: PM [deg]', 'pm_deg', 1, '%.2f'),
            ('stage-2 OTA + follower: A0 [dB]', 'a0_dB', 1, '%.2f'), ('stage-2 OTA + follower: GBW [kHz]', 'gbw_Hz', 1e-3, '%.3f'), ('stage-2: PM at beta = 1 [deg]', 'pm_beta1_deg', 1, '%.2f'),
            ('stage-2: loop crossover at the real beta [Hz]', 'f_loop_Hz', 1, '%.1f'), ('stage-2: PM at the real beta [deg]', 'pm_beta_real_deg', 1, '%.2f'),
            ('supply -> output gain at DC [V/V]', 'vdd2out_dc', 1, '%.4f'), ('supply -> output gain at 50 Hz [V/V]', 'vdd2out_50Hz', 1, '%.4f'), ('supply -> output gain at 300 Hz [V/V]', 'vdd2out_300Hz', 1, '%.4f'),
            ('supply -> output gain at 10 kHz [V/V]', 'vdd2out_10k', 1, '%.4f')]
    cs = [CKEY[c] for c in CORNERS]
    P('\n%-48s | ' % 'quantity  [typ 27 / ff 85 / ss -40]' + ' | '.join('%-34s' % v for v in variants))
    for lab, key, sc, fmt in rows:
        P('%-48s | ' % lab + ' | '.join('%-34s' % ' / '.join(fmt % g(v, c, key, sc) for c in cs) for v in variants))
    for v in variants:
        P('# %s' % vname(v))
    P('# (ngspice reports @m...[id] and [gm] of an instance with m > 1 as the total of all fingers: checked against the sink current)')
    P('# (+dio what-if, noise rows only: the junction is an IDEAL capacitor of %.0f fF = its zero-bias value, because .noise returns NaN with the PDK diode card)' % (DIO_C0 * 1e15))
    bad = [n for n in res if not res[n]['ok']]
    P('\njobs: %d, not ok: %s' % (len(res), ', '.join('%s (%s)' % (n, res[n]['abort'][:100]) for n in bad) or 'none'))
    P('(the "Error: &g_mid: no such variable" line of the noise testbench is its own known echo problem, a4c_noise.log has it too; a job is "not ok" only on an abort / non-zero exit)')
    json.dump(R, open(os.path.join(SIM, 'lp_rvt_tables.json'), 'w'), indent=1)
    keep_logs(res, os.path.join(SIM, 'lp_rvt_tables_nglogs.tgz'))


# ------------------------------------------------------------------ swing / THD
def stage_swing(variants, quick=False):
    P = Log(os.path.join(SIM, 'lp_rvt_swing.log'))
    P('STAGE swing: tb_a4c_tran.spice, differential electrode sine VD pk (0.5 mV = +-0.5 V at the output), 8 s, last 4 periods (12.25 Hz) / last 0.1 s (300 Hz) fitted by least squares (9 harmonics),')
    P('  as scripts/run_a4c_b.sh thd / a4c_analyze.py; the only difference to the A4c runs: .options abstol=1e-12 chgtol=1e-17 vntol=1e-7 (Decision 43a) instead of abstol=1e-20 chgtol=1e-19.')
    cases = [('f12', 12.25, '0.5m', dict(TSTOP=8, TSAVE=7.2, TSTEP='2m', TMAXS='2m')), ('f12', 12.25, '0.55m', dict(TSTOP=8, TSAVE=7.2, TSTEP='2m', TMAXS='2m')),
             ('f12', 12.25, '0.6m', dict(TSTOP=8, TSAVE=7.2, TSTEP='2m', TMAXS='2m')), ('f300', 300.0, '0.5m', dict(TSTOP=8, TSAVE=7.9, TSTEP='20u', TMAXS='80u'))]
    if quick:
        cases = cases[:1]
    jobs, meta = [], {}
    for v in variants:
        for (k, T) in CORNERS:
            for lab, f, vd, pr in cases:
                n = 'thd_%s_%s_%g_%s_%s' % (v, k, T, lab, vd)
                csv = os.path.join(SCR, 'swing', n + '.csv')
                p = dict(pr, VD=vd, F_SIG=f, NSVRS=NSVRS[(k, T)])
                jobs.append((n, deck('tb_a4c_tran.spice', k, T, v, params=p, out=csv, opt=TRAN_OPT)))
                meta[n] = (v, k, T, lab, f, float(vd[:-1]) * 1e-3, csv)
    res = run_jobs(jobs, 'swing', log=lambda s: None, retry=retry_tmax)
    R = {}
    P('\n%-14s %-8s %4s %5s %6s | %8s %8s %9s | %7s %7s | %7s %7s | %s' % ('variant', 'corner', 'T', 'f Hz', 'VD mV', 'gain dB', 'THD %', 'mean mV', 'out max', 'out min', 'o2 max', 'o2 min', 'note'))
    for n, (v, k, T, lab, f, vd, csv) in meta.items():
        if not res[n]['ok'] or not os.path.exists(csv):
            P('%-14s %-8s %4g %5g %6.2f | FAILED %s' % (v, k, T, f, vd * 1e3, res[n]['abort'][:200]))
            continue
        d = tcsv(csv)
        t = d['time']
        nper = 4 if f < 100 else 30
        a1, thd, mean = harmonics(t, d['out'], f, nper)
        m = t > t[-1] - nper / f
        r = dict(gain_db=20 * math.log10(a1 / vd), thd_pct=thd * 100, mean_mv=(mean - 1.65) * 1e3, out_max=float(d['out'][m].max()), out_min=float(d['out'][m].min()),
                 o2_max=float(d['o2'][m].max()), o2_min=float(d['o2'][m].min()), tries=res[n]['tries'])
        R.setdefault(v, {}).setdefault(CKEY[(k, T)], {})['%s_%gm' % (lab, vd * 1e3)] = r
        P('%-14s %-8s %4g %5g %6.2f | %8.3f %8.3f %9.2f | %7.3f %7.3f | %7.3f %7.3f | %s' % (v, k, T, f, vd * 1e3, r['gain_db'], r['thd_pct'], r['mean_mv'], r['out_max'], r['out_min'], r['o2_max'], r['o2_min'],
                                                                                         '' if res[n]['tries'] == 1 else 're-run once with TMAXS x 0.9'))
    for v in variants:
        P('# %s' % vname(v))
    P('# A4c reference (sim/a4c_thd.log, 12.25 Hz, 0.5 mV): THD 0.040 / 2.527 / 0.051 %, out 1.148-2.154 V typ, bottom 1.220 V at ff 85 (the accepted Decision-28 miss)')
    json.dump(R, open(os.path.join(SIM, 'lp_rvt_swing.json'), 'w'), indent=1)
    keep_logs(res, os.path.join(SIM, 'lp_rvt_swing_nglogs.tgz'))


# ------------------------------------------------------------------ ideal ADC load, 245 us (A4b adc245)
def stage_adc245(variants):
    P = Log(os.path.join(SIM, 'lp_rvt_adc245.log'))
    P('STAGE adc245 (the A4b check behind Decision 37): spice/adc_load.spice = IDEAL switch 1 kOhm + C_s 17 pF, NO reset: C_s starts +-0.24 V away from the amplifier output (300 Hz full-scale')
    P('  sample-to-sample step), connected for T_ACQ = 245 us, amplifier at rest.  err(T) = v(C_s)(t0 + T) - v(out) before the connect [LSB = 0.806 mV].  A4b result: |err| <= 0.26 LSB at 245 us.')
    TS = [11.05e-6, 50e-6, 100e-6, 150e-6, 200e-6, 245e-6]
    jobs, meta = [], {}
    for v in variants:
        for (k, T) in CORNERS:
            for dv in ('+0.24', '-0.24'):
                n = 'adc245_%s_%s_%g_dv%s' % (v, k, T, dv)
                csv = os.path.join(SCR, 'adc245', n + '.csv')
                p = dict(ADC_EN=1, ADC_T0='2m', DV_PREV=dv, T_ACQ='245u', TSAVE='1.9m', TSTOP='2.26m', TSTEP='100n', TMAXS='500n', NSVRS=NSVRS[(k, T)])
                jobs.append((n, deck('tb_a4c_tran.spice', k, T, v, params=p, out=csv, opt=TRAN_OPT)))
                meta[n] = (v, k, T, dv, csv)
    res = run_jobs(jobs, 'adc245', log=lambda s: None, retry=retry_tmax)
    R = {}
    P('\n%-14s %-8s %4s %6s | ' % ('variant', 'corner', 'T', 'dV V') + ' '.join('err@%3.0fus' % (x * 1e6) for x in TS) + ' | kick peak mV')
    for n, (v, k, T, dv, csv) in meta.items():
        if not res[n]['ok'] or not os.path.exists(csv):
            P('%-14s %-8s %4g %6s | FAILED %s' % (v, k, T, dv, res[n]['abort'][:200]))
            continue
        d = tcsv(csv)
        t = d['time']
        vf = at(t, d['out'], 2e-3 - 100e-9)
        e = [(at(t, d['cs'], 2e-3 + x) - vf) / LSB for x in TS]
        m = t >= 2e-3
        kick = float((d['out'][m] - vf)[np.argmax(np.abs(d['out'][m] - vf))]) * 1e3
        R.setdefault(v, {}).setdefault(CKEY[(k, T)], {})[dv] = dict(err_lsb=e, kick_mv=kick)
        P('%-14s %-8s %4g %6s | ' % (v, k, T, dv) + ' '.join('%9.3f' % x for x in e) + ' | %9.1f' % kick)
    for v in variants:
        P('# %s' % vname(v))
    json.dump(R, open(os.path.join(SIM, 'lp_rvt_adc245.json'), 'w'), indent=1)
    keep_logs(res, os.path.join(SIM, 'lp_rvt_adc245_nglogs.tgz'))


# ------------------------------------------------------------------ real DAC settle (D5 method)
D5CASES = '1.65_1.65_0,1.65_1.65_p,1.65_1.65_m,1.65_1.89_p,1.65_1.89_m,1.65_1.41_p,1.65_1.41_m,2.1_2.1_p,2.1_2.1_m,2.1_1.86_p,2.1_1.86_m,2.15_2.15_p,2.15_2.15_m,2.15_1.91_p,2.15_1.91_m,1.2_1.2_p,1.2_1.2_m,1.2_1.44_p,1.2_1.44_m'.split(',')


def stage_settle(variants, cases=None, tight=False):
    import d5lib as L5
    import d5_settle as S5
    cases = cases or D5CASES
    P = Log(os.path.join(SIM, 'lp_rvt_settle%s.log' % ('_tight' if tight else '')))
    opt_run = TIGHT_OPT if tight else TRAN_OPT
    if tight:
        P('TIGHT-TOLERANCE REPEAT of a few cases (reltol 1e-6, vntol 1e-9 for the DC operating point AND the transient; abstol stays 1e-12: with 1e-15 every run aborts at the first switching event,')
        P('  "Timestep too small ... vck#branch", the abort class of Decision 43a): the settling numbers without the DC-solve difference of the two copies (see the NOTE in lp_rvt_settle.log).')
    P('STAGE settle (D5 item 1 method, AFE/adc/scripts/d5lib.py + d5_settle.py, their netlist builder and case list): TWO copies of the amplifier in one netlist, L loaded by the REAL sampling TG +')
    P('  split 6+6 DAC + cmp_p (AFE/adc/spice), U unloaded (20 fF); frame 0 at 2 ms leaves the bottoms at the previous code, the TG closes after T_CONV 9.5 us (the kick), acquisition 240.5 us;')
    P('  error = out_L - out_U at the next CS falling [LSB].  Case = <level>_<previous level>_<kick polarity p / m / 0>.  Differences to D5: .options abstol=1e-12 (D5 had 1e-15, the abort cause),')
    P('  one ngspice thread.  D5 result (sim/d5_settle.log, 57 runs): <= 0.086 / 0.114 / 0.070 LSB (typ / ff 85 / ss -40), spikes up to 362 LSB.')
    jobs, meta, opn = [], {}, []
    d = os.path.join(SCR, 'settle_tight' if tight else 'settle')
    os.makedirs(d, exist_ok=True)
    for v in variants:
        for (k, T) in CORNERS:
            for c in cases:
                lv, pv, pol = c.split('_')
                lv, pv = float(lv), float(pv)
                code, q = S5.pick(pv, lv, pol)
                vos = (lv - 1.650164) / 1000.0 if abs(lv - 1.65) > 1e-9 else 0.0
                t0 = 2e-3
                fr = [(t0, code), (t0 + L5.TFRAME, int(round(lv / L5.LSB)))]
                ctrl, tr = L5.controls(fr)
                n = 'set_%s_%s_%g_%s' % (v, k, T, c)
                cf, csv = os.path.join(d, n + '.inc'), os.path.join(d, n + '.csv')
                open(cf, 'w').write(ctrl)
                tb = L5.build(vos=vos, tos=0.5e-3, tstop=t0 + L5.TFRAME + 1e-6, tsave=1.8e-3, tmaxs=1e-6, reltol=1e-4, ctrl=cf)
                tb = tb.replace('../../amp/spice/models_typical.spice', '%s/spice/models_%s.spice' % (AMP, k)).replace('../../amp/spice/ota2.spice', ota2_file(v)).replace('../../amp/spice/afe_chc.spice', chc_file(v))
                tb = tb.replace('../../amp/spice/', AMP + '/spice/').replace('../spice/', ADC + '/spice/')
                tb = re.sub(r'^\.options .*$', opt_run, tb, count=1, flags=re.M)
                tb = re.sub(r'^\.temp .*$', '.temp %g' % T, tb, flags=re.M)
                tb = re.sub(r'^\.param NSVRS=.*$', '.param NSVRS=%g' % NSVRS[(k, T)], tb, flags=re.M)
                tb = tb.replace('@OUT@', csv)
                jobs.append((n, tb))
                meta[n] = (v, k, T, c, code, q, csv, t0)
                if c == cases[0]:          # DC check of the two copies (see the note in the log): the same netlist, .op only, with the run's tolerances and with 100x tighter ones
                    for tol, o in (('def', opt_run), ('tight', TIGHT_OPT)):
                        i = tb.index('.tran')
                        opn.append(('dc%s_%s_%s_%g' % (tol, v, k, T), re.sub(r'^\.options .*$', o, tb[:i], count=1, flags=re.M) + '\n'.join(
                            ['.control', 'op', 'let d = v(out) - v(outu)', 'let il = @m.xch.xs2.xota2.xmf.m0[id] - @m.xch.xs2.xota2.xms.m0[id]', 'echo RESULT dout_V=$&d iload_A=$&il', 'quit', '.endc', '.end']) + '\n'))
    res = run_jobs(jobs + opn, 'settle_tight' if tight else 'settle', log=lambda s: None, retry=retry_tmax)
    R = {}
    for n, (v, k, T, c, code, q, csv, t0) in meta.items():
        if not res[n]['ok'] or not os.path.exists(csv):
            P('SETTLE %-14s %-8s %4g case %-12s FAILED %s' % (v, k, T, c, res[n]['abort'][:200]))
            continue
        a = np.loadtxt(csv, skiprows=1)
        t, vl, vu = a[:, 0], a[:, 1], a[:, 2]
        tc = t0 + L5.TCONV
        dd = (vl - vu) / L5.LSB
        te = t0 + L5.TFRAME - 20e-9
        e_end = at(t, dd, te)
        pre = at(t, dd, t0 - 1e-6)
        m = (t > tc) & (t < tc + 5e-6)
        pk = float(dd[m][np.argmax(np.abs(dd[m]))])
        mm = (t > tc + 1e-6) & (t < t0 + L5.TFRAME - 100e-9)
        big = np.nonzero(np.abs(dd[mm]) > 0.5)[0]
        t05 = float((t[mm][big[-1]] - tc) * 1e9) if len(big) else 0.0
        cur = [at(t, dd, tc + x) for x in (1e-6, 11e-6, 50e-6, 100e-6, 240e-6)]
        R.setdefault(v, {}).setdefault(CKEY[(k, T)], {})[c] = dict(e_end=e_end, pre=pre, d_end=e_end - pre, peak_lsb=pk, t05_ns=t05, vu=at(t, vu, te), tries=res[n]['tries'])
        P('SETTLE %-14s %-8s %4g case %-12s amp out (unloaded) %.4f V, prev code %4d (kick Q %+5.2f pC) | L-U before %+.3f | spike peak %+7.1f LSB, |L-U| > 0.5 LSB until %5.0f ns after the TG closes | L-U [LSB] at +1/11/50/100/240 us: %s | END OF T_ACQ: %+.3f LSB' % (
            v, k, T, c, at(t, vu, te), code, q * 1e12, pre, pk, t05, ' '.join('%+.3f' % x for x in cur), e_end))
    P('\nSUMMARY per variant and corner (%d cases each) [LSB = 0.806 mV]: END = max |L-U| at the end of T_ACQ (the D5 number); CHANGE = max |(L-U at the end) - (L-U before the frame)| = what the' % len(cases))
    P('  kick leaves; STATIC = L-U before the frame (range over the cases); SPIKE = largest |L-U| in the 5 us after the TG closes')
    mx = lambda x, key: max([abs(y[key]) for y in x.values()] or [float('nan')])
    for v in variants:
        row = []
        for (k, T) in CORNERS:
            x = R.get(v, {}).get(CKEY[(k, T)], {})
            pr = [y['pre'] for y in x.values()] or [float('nan')]
            row.append('%s: %d runs, END %.3f, CHANGE %.3f, STATIC %+.3f..%+.3f, SPIKE %.0f LSB = %.0f mV' % (CKEY[(k, T)], len(x), mx(x, 'e_end'), mx(x, 'd_end'), min(pr), max(pr), mx(x, 'peak_lsb'), mx(x, 'peak_lsb') * 0.8057))
        P('  %-14s %s' % (v, ' | '.join(row)))
    P('\nNOTE on STATIC (L-U before any ADC event): it is the difference of the two copies in the DC operating point of the run.  The output DC level is out = vn2 + (leakage at the summing node) x R(pseudo-R),')
    P('  i.e. it is set by currents of 1e-17 A in 5 TOhm, and the DC solution of such a node is only as good as the Newton stop criterion (reltol 1e-4 x 1.65 V = 165 uV = 0.2 LSB): the two copies')
    P('  can stop up to that far apart, and the transient keeps the difference (time constant R0 x Cf2 = seconds).  Check: the same netlist, .op only, with the tolerances of the run and 100x tighter')
    P('  (reltol 1e-6, vntol 1e-9); the ADC cell draws the DC load current shown from the amplifier output (driver / TG off-state leakage, about 1 nA at ff 85 C).')
    P('  %-14s %-8s %4s | %22s %22s | %12s' % ('variant', 'corner', 'T', 'L-U at DC, run tol', 'L-U at DC, tight tol', 'DC load'))
    for v in variants:
        for (k, T) in CORNERS:
            a = results(res['dcdef_%s_%s_%g' % (v, k, T)]['out'])
            b = results(res['dctight_%s_%s_%g' % (v, k, T)]['out'])
            if a and b and isinstance(a[0].get('dout_V'), float) and isinstance(b[0].get('dout_V'), float):
                P('  %-14s %-8s %4g | %12.2f uV = %+.3f LSB %10.2f uV = %+.3f LSB | %9.3f nA' % (v, k, T, a[0]['dout_V'] * 1e6, a[0]['dout_V'] / L5.LSB, b[0]['dout_V'] * 1e6, b[0]['dout_V'] / L5.LSB, a[0]['iload_A'] * 1e9))
                R.setdefault(v, {}).setdefault(CKEY[(k, T)], {})['_dc'] = dict(dout_run_uv=a[0]['dout_V'] * 1e6, dout_tight_uv=b[0]['dout_V'] * 1e6, iload_na=a[0]['iload_A'] * 1e9)
            else:
                P('  %-14s %-8s %4g | DC check failed' % (v, k, T))
    P('  -> the settling result of a variant is CHANGE (and END once STATIC is removed); a STATIC value that vanishes with the tight tolerances is a property of the DC solve, not of the circuit.')
    for v in variants:
        P('# %s' % vname(v))
    json.dump(R, open(os.path.join(SIM, 'lp_rvt_settle%s.json' % ('_tight' if tight else '')), 'w'), indent=1)
    keep_logs(res, os.path.join(SIM, 'lp_rvt_settle%s_nglogs.tgz' % ('_tight' if tight else '')))


# ------------------------------------------------------------------ slew
def stage_slew(variants):
    P = Log(os.path.join(SIM, 'lp_rvt_slew.log'))
    P('STAGE slew (as scripts/run_a4b.sh slew): electrode offset step +-0.5 mV at 5 ms (1 us edge): maximum |d out / dt|, 10-90 % rise time, step reached at 35 ms after the edge.')
    P('  Need (ESTIMATE): 2 pi x 300 Hz x 0.5 V = 942 V/s.  A4b: 1937 / 2985 / 1227 V/s (typ / ff 85 / ss -40).')
    jobs, meta = [], {}
    for v in variants:
        for (k, T) in CORNERS:
            for sg in ('+', '-'):
                n = 'slew_%s_%s_%g_%s' % (v, k, T, 'p' if sg == '+' else 'm')
                csv = os.path.join(SCR, 'slew', n + '.csv')
                p = dict(VOS_REC=sg + '0.5m', T_OS=0.005, TSTOP=0.04, TSTEP='0.5u', TMAXS='5u', NSVRS=NSVRS[(k, T)])
                jobs.append((n, deck('tb_a4c_tran.spice', k, T, v, params=p, out=csv, opt=TRAN_OPT)))
                meta[n] = (v, k, T, sg, csv)
    res = run_jobs(jobs, 'slew', log=lambda s: None, retry=retry_tmax)
    R = {}
    P('\n%-14s %-8s %4s %5s | %10s %10s %10s' % ('variant', 'corner', 'T', 'step', 'max V/s', 't10-90 ms', 'step V'))
    for n, (v, k, T, sg, csv) in meta.items():
        if not res[n]['ok'] or not os.path.exists(csv):
            P('%-14s %-8s %4g %5s | FAILED %s' % (v, k, T, sg, res[n]['abort'][:200]))
            continue
        d = tcsv(csv)
        t, y = d['time'], d['out']
        y0 = at(t, y, 0.0049)
        yf = y[-1]
        tu = np.linspace(0.005, 0.04, 70001)
        yu = np.interp(tu, t, y)
        sl = float(np.abs(np.gradient(yu, tu)).max())
        fr = (yu - y0) / (yf - y0)
        t10 = tu[np.argmax(fr >= 0.1)]
        t90 = tu[np.argmax(fr >= 0.9)]
        R.setdefault(v, {}).setdefault(CKEY[(k, T)], {})[sg] = dict(slew=sl, t1090_ms=(t90 - t10) * 1e3, step=yf - y0)
        P('%-14s %-8s %4g %5s | %10.0f %10.3f %10.4f' % (v, k, T, sg + '0.5m', sl, (t90 - t10) * 1e3, yf - y0))
    json.dump(R, open(os.path.join(SIM, 'lp_rvt_slew.json'), 'w'), indent=1)
    keep_logs(res, os.path.join(SIM, 'lp_rvt_slew_nglogs.tgz'))


# ------------------------------------------------------------------ reset recovery (sanity)
def stage_rec(variants):
    P = Log(os.path.join(SIM, 'lp_rvt_rec.log'))
    P('STAGE rec (as scripts/run_a4c.sh rec, one case): 10 mV electrode offset step at 0.1 s with the IDEAL reset pulse (fs high) of 3 ms starting 10 us before the step, no TGATE, 20 s.')
    P('  release step = out just after the pulse minus out at the pulse end; time until the output stays within 1 mV of its final value.  A4c: release step -0.05..-0.14 mV, 10 mV step 3.4-4.7 s.')
    jobs, meta = [], {}
    for v in variants:
        for (k, T) in CORNERS:
            n = 'rec_%s_%s_%g' % (v, k, T)
            csv = os.path.join(SCR, 'rec', n + '.csv')
            p = dict(VOS_REC='10m', T_OS=0.1, FS_EN=1, FS_T0=0.09999, FS_W='3m', FS_TR='100n', TSTOP=20, TSTEP='1u', TMAXS='1m', NSVRS=NSVRS[(k, T)])
            jobs.append((n, deck('tb_a4c_tran.spice', k, T, v, params=p, out=csv, opt=TRAN_OPT)))
            meta[n] = (v, k, T, csv)
    res = run_jobs(jobs, 'rec', log=lambda s: None, retry=retry_tmax)
    R = {}
    P('\n%-14s %-8s %4s | %12s %14s %14s %16s %12s' % ('variant', 'corner', 'T', 'rest V', 'err@end mV', 'release mV', 'out@+1ms mV', 't(1 mV) s'))
    for n, (v, k, T, csv) in meta.items():
        if not res[n]['ok'] or not os.path.exists(csv):
            P('%-14s %-8s %4g | FAILED %s' % (v, k, T, res[n]['abort'][:200]))
            continue
        d = tcsv(csv)
        t, y = d['time'], d['out']
        rest = at(t, y, 0.0999)
        te = 0.09999 + 100e-9 + 3e-3
        eend = (at(t, y, te - 1e-6) - rest) * 1e3
        rel = (at(t, y, te + 100e-9 + 20e-6) - at(t, y, te - 1e-6)) * 1e3
        p1 = (at(t, y, te + 1e-3) - rest) * 1e3
        fin = y[-1]
        m = (t > te) & (np.abs(y - fin) > 1e-3)
        ts = float(t[m][-1] - te) if m.any() else 0.0
        R.setdefault(v, {})[CKEY[(k, T)]] = dict(rest=rest, err_end_mv=eend, release_mv=rel, out_1ms_mv=p1, t_1mv_s=ts)
        P('%-14s %-8s %4g | %12.4f %14.3f %14.3f %16.3f %12.3f' % (v, k, T, rest, eend, rel, p1, ts))
    json.dump(R, open(os.path.join(SIM, 'lp_rvt_rec.json'), 'w'), indent=1)
    keep_logs(res, os.path.join(SIM, 'lp_rvt_rec_nglogs.tgz'))


# ------------------------------------------------------------------ power-up with the host reset (sanity)
def stage_pur(variants):
    P = Log(os.path.join(SIM, 'lp_rvt_pur.log'))
    P('STAGE pur (as scripts/run_a4c_b.sh pur, W = 100 ms): VDD ramp 0 -> 3.3 V in 1 ms from the all-zero state (no nodesets), no TGATE, then the IDEAL reset pulse (fs = RST_AMP) at 3 s for 100 ms, 12 s.')
    P('  Time from the end of the pulse until the output stays within 10 mV / 1 mV of 1.65 V; supply current at the end.  A4c (sim/a4c_pur.log, 100 ms): within 1 mV after 0.14 / 0 / 0.92 s,')
    P('  supply 74.4 / 119.3 / 46.8 uA (the 3k-poly ladders of that time; 74.4 / 118.8 / 47.1 uA with ppolyf_u_1k, F1).')
    jobs, meta = [], {}
    for v in variants:
        for (k, T) in CORNERS:
            n = 'pur_%s_%s_%g' % (v, k, T)
            csv = os.path.join(SCR, 'pur', n + '.csv')
            p = dict(PU_T='1m', FS_EN=1, FS_T0=3, FS_W='100m', FS_TR='100n', TSTOP=12, TSTEP='1n', TMAXS='5m')
            jobs.append((n, deck('tb_a4c_tran.spice', k, T, v, params=p, out=csv, opt=TRAN_OPT)))
            meta[n] = (v, k, T, csv)
    res = run_jobs(jobs, 'pur', log=lambda s: None, retry=retry_tmax)
    R = {}
    P('\n%-14s %-8s %4s | %10s %10s | %12s %12s | %10s %10s | %s' % ('variant', 'corner', 'T', 'final V', 'err mV', 't(10 mV) s', 't(1 mV) s', 'I sup uA', 'I master', 'out min / max before the reset'))
    for n, (v, k, T, csv) in meta.items():
        if not res[n]['ok'] or not os.path.exists(csv):
            P('%-14s %-8s %4g | FAILED %s' % (v, k, T, res[n]['abort'][:200]))
            continue
        d = tcsv(csv)
        t, y = d['time'], d['out']
        te = 3.0 + 0.1 + 200e-9

        def tset(lim):
            m = (t > te) & (np.abs(y - 1.65) > lim)
            return float(t[m][-1] - te) if m.any() else 0.0
        mb = (t > 0.01) & (t < 3.0)
        r = dict(final=float(y[-1]), t10=tset(10e-3), t1=tset(1e-3), isup=float(np.mean(d['isup'][t > t[-1] - 1])), idm=float(np.mean(d['idm'][t > t[-1] - 1])), pre_min=float(y[mb].min()), pre_max=float(y[mb].max()), tries=res[n]['tries'])
        R.setdefault(v, {})[CKEY[(k, T)]] = r
        P('%-14s %-8s %4g | %10.4f %10.2f | %12.3f %12.3f | %10.2f %10.3f | %.3f / %.3f V%s' % (v, k, T, r['final'], (r['final'] - 1.65) * 1e3, r['t10'], r['t1'], r['isup'] * 1e6, r['idm'] * 1e6, r['pre_min'], r['pre_max'],
                                                                                           '' if r['tries'] == 1 else '  (re-run once with TMAXS x 0.9)'))
    for v in variants:
        P('# %s' % vname(v))
    json.dump(R, open(os.path.join(SIM, 'lp_rvt_pur.json'), 'w'), indent=1)
    keep_logs(res, os.path.join(SIM, 'lp_rvt_pur_nglogs.tgz'))


if __name__ == '__main__':
    st = sys.argv[1]
    vs = sys.argv[2].split(',') if len(sys.argv) > 2 else ['orig', 'rvt']
    if st == 'settle_tight':
        stage_settle(vs, cases=['1.65_1.65_0', '1.65_1.89_m', '2.15_1.91_p', '1.2_1.44_m'], tight=True)
    else:
        {'tables': stage_tables, 'swing': stage_swing, 'adc245': stage_adc245, 'settle': stage_settle, 'slew': stage_slew, 'rec': stage_rec, 'pur': stage_pur}[st](vs)
