#!/usr/bin/env python3
"""LP step 6: X2 S1 (short-window end-to-end, transistor-level amplifier -> ADC, closed-loop PWL replay) with the ORIGINAL amplifier and with the native-Vt-free variant, same script, same session.
It runs AFE/adc/scripts/x2_s1.py UNCHANGED (in this process, by runpy) with
  X2_AMP_INC  = ota1 : ota2_rvt : stage1c : stage2c : afe_chc_rvt   (variant `rvt`; empty for `orig`: the design netlists)      -> the new additive option of x2lib.py
  X2_SUFFIX   = _lprvt_<variant>      (so x2_s1.py writes its own files and does not append to sim/x2_s1_summary.log)
  X2_NCAL     = number of ADC-alone calibration inputs (default here 12; X2 used 24)
and three process changes that do not touch the circuit: (a) x2lib.NPAR = 2 (this fork may run at most two ngspice at a time; the x2 slot directories are machine-wide, so both variants together
stay within 2), (b) `ngspice` resolves to a shim that starts the real one through AFE/layout/scripts/slot.sh (common rule 4), (c) the line x2_s1.py appends to the tracked sim/x2_done.txt is
dropped.  The result files are then moved to AFE/adc/sim/lp_rvt_x2_s1_<variant>_<corner>.{log,npz}.
usage: python3 lp_rvt_x2.py run <orig|rvt|nodnw> <typ|ff85|ss-40> [TPRE_ms] [which=all|levels|sine]      (nodnw = the second fallback ota2_rvt_nodnw.spice)
       python3 lp_rvt_x2.py report            -> AFE/adc/sim/lp_rvt_x2_s1_report.log (+ .json): both variants, every corner that has run, the definitions of x2_s1_report.py
"""
import sys, os, re, json, runpy, builtins, shutil, stat
HERE = os.path.dirname(os.path.abspath(__file__))
AMP = os.path.normpath(os.path.join(HERE, '..'))
AFE = os.path.normpath(os.path.join(AMP, '..'))
ADC = os.path.join(AFE, 'adc')
SCR = os.environ.get('LP_RVT_SCRATCH', '/tmp/lp_rvt')
TPRE = {'typ': 4, 'ff85': 3, 'ss-40': 4}          # ms, as X2 S1


def run(var, ck, tpre=None, which='all'):
    os.environ['X2_SUFFIX'] = '_lprvt_' + var
    os.environ.setdefault('X2_NCAL', '12')
    if var == 'rvt':
        os.environ['X2_AMP_INC'] = ':'.join(os.path.join(AMP, 'spice', f) for f in ('ota1.spice', 'ota2_rvt.spice', 'stage1c.spice', 'stage2c.spice', 'afe_chc_rvt.spice'))
    elif var == 'nodnw':          # second fallback (runner-up): ota2_rvt_nodnw.spice
        os.environ['X2_AMP_INC'] = ':'.join(os.path.join(AMP, 'spice', f) for f in ('ota1.spice', 'ota2_rvt_nodnw.spice', 'stage1c.spice', 'stage2c.spice', 'afe_chc_rvt.spice'))
    elif var == 'orig':
        os.environ.pop('X2_AMP_INC', None)
    else:
        raise SystemExit('variant must be orig, rvt or nodnw')
    os.environ.pop('X2_AMP_SUBCKT', None)
    # (b) ngspice shim -> slot.sh
    bind = os.path.join(SCR, 'bin')
    os.makedirs(bind, exist_ok=True)
    shim = os.path.join(bind, 'ngspice')
    open(shim, 'w').write('#!/bin/bash\nexec bash %s /foss/tools/bin/ngspice "$@"\n' % os.path.join(AFE, 'layout', 'scripts', 'slot.sh'))
    os.chmod(shim, os.stat(shim).st_mode | stat.S_IEXEC)
    os.environ['PATH'] = bind + ':' + os.environ['PATH']
    sys.path.insert(0, os.path.join(ADC, 'scripts'))
    import x2lib as X
    X.NPAR = 2                                       # (a)
    assert bool(X.AMP_INC) == (var != 'orig')
    real_open = builtins.open

    def my_open(file, mode='r', *a, **k):             # (c)
        if isinstance(file, str) and file.endswith('x2_done.txt') and 'a' in mode:
            return real_open(os.devnull, 'w')
        return real_open(file, mode, *a, **k)
    builtins.open = my_open
    sys.argv = ['x2_s1.py', ck, str(tpre if tpre is not None else TPRE[ck]), which]
    try:
        runpy.run_path(os.path.join(ADC, 'scripts', 'x2_s1.py'), run_name='__main__')
    finally:
        builtins.open = real_open
    sfx = '' if which == 'all' else '_' + which.replace(',', '_')
    src_log = os.path.join(ADC, 'sim', 'x2_s1_%s%s_lprvt_%s.log' % (ck, sfx, var))
    src_npz = os.path.join(ADC, 'sim', 'x2_s1_%s_lprvt_%s.npz' % (ck, var))
    tag = '%s_%s%s' % (var, ck, sfx)
    for s, d in ((src_log, 'lp_rvt_x2_s1_%s.log' % tag), (src_npz, 'lp_rvt_x2_s1_%s.npz' % tag)):
        if os.path.exists(s):
            shutil.move(s, os.path.join(ADC, 'sim', d))
    print('LP_RVT_X2 done: %s' % tag, flush=True)


def report():
    import numpy as np
    LSB = 3.3 / 4096
    GNOM = 1000.0
    FSIG = 3 * 4000.0 / 512
    TFR = 250e-6
    AE = 0.45e-3
    out = []

    def P(s):
        print(s)
        out.append(s)
    P('LP step 6: X2 S1 (AFE/adc/scripts/x2_s1.py, unchanged) with the ORIGINAL amplifier (orig) and the native-Vt-free variant (rvt = ota2_rvt.spice + afe_chc_rvt.spice through X2_AMP_INC).')
    P('Definitions = AFE/adc/scripts/x2_s1_report.py: frames 1-2 of each run (steady state); e = code + 0.5 - Vout / LSB (the circuit\'s decisions; an ideal quantiser gives +-0.5);')
    P('U = (Vout + x12 / alpha) / LSB - (code | 1) (sampling + DAC side, sub-LSB); INL beyond a fixed offset = larger of max|U - mean| and max|e - mean| - 0.5, means taken below 2.05 V.')
    P('ADC alone = the same ADC cell with an ideal source (calibration part of x2_s1.py, X2_NCAL inputs).  Pre-layout reference (X2, sim/x2_s1_report.log): offset -30.3 / -40.4 / -22.0 LSB,')
    P('INL below 2.05 V 0.63 / 1.99 / 0.61 LSB, whole range 2.19 / 5.07 / 0.61 LSB, amplifier -> ADC adds <= 0.08 LSB, kick spike 103-492 mV.')
    J = {}
    for ck in ('typ', 'ff85', 'ss-40'):
        for var in ('orig', 'rvt', 'nodnw'):
            fns = [f for f in sorted(os.listdir(os.path.join(ADC, 'sim'))) if re.fullmatch(r'lp_rvt_x2_s1_%s_%s(_\w+)?\.npz' % (var, re.escape(ck)), f)]
            if not fns:
                if var != 'nodnw':
                    P('S1 %-5s %-4s: not run' % (ck, var))
                continue
            z = np.load(os.path.join(ADC, 'sim', fns[0]), allow_pickle=True)
            R = z['R']
            al = float(z['alpha'])
            th = float(z['theta'])
            U_ = lambda vo, x12v, code: (vo + x12v / al) / LSB - (code.astype(int) | 1)
            S = R[R[:, 2] > 0]
            vo, c, ci = S[:, 4], S[:, 5], S[:, 6]
            u = U_(vo, S[:, 8] * LSB, c)
            e = c + 0.5 - vo / LSB
            lo = vo < 2.05
            r = z['adc_rows']
            va, ca, xa = r[:, 0], r[:, 1], r[:, 4]
            ua = U_(va, xa, ca)
            ea = ca + 0.5 - va / LSB
            loa = va < 2.05
            o = np.argsort(va)
            du = u - np.interp(vo, va[o], ua[o])
            inl_lo = max(np.abs(u[lo] - u[lo].mean()).max(), np.abs(e[lo] - e[lo].mean()).max() - 0.5)
            inl_all = max(np.abs(u - u[lo].mean()).max(), np.abs(e - e[lo].mean()).max() - 0.5)
            pk = np.r_[S[S[:, 10] != 0, 10], R[(R[:, 2] == 0) & (R[:, 10] != 0), 10]]
            d = dict(n=int(len(S)), runs=int(len(S) // 2), vout_min=float(vo.min()), vout_max=float(vo.max()), offset_lsb=float(e[lo].mean()), offset_adc_alone_lsb=float(ea[loa].mean()),
                     code_minus_ideal=[int((c - ci).min()), int((c - ci).max())], inl_u_lo=[float((u[lo] - u[lo].mean()).min()), float((u[lo] - u[lo].mean()).max())],
                     inl_e_lo=[float((e[lo] - e[lo].mean()).min()), float((e[lo] - e[lo].mean()).max())], inl_lo_lsb=float(inl_lo), inl_all_lsb=float(inl_all),
                     amp_minus_adc_lo=[float(du[lo].mean()), float(du[lo].min()), float(du[lo].max())], kick_mv=[float(np.abs(pk).min() * 1e3), float(np.abs(pk).max() * 1e3)] if len(pk) else None,
                     passes=[int(R[:, 11].min()), int(R[:, 11].max())], unresolved=int(R[:, 12].sum()), top={('%.3f' % v): float(x - u[lo].mean()) for v, x in sorted(zip(vo[~lo], u[~lo]))}, file=fns[0])
            lv = S[S[:, 0] == 0]
            sn = S[S[:, 0] == 1]
            if len(lv) >= 6:
                q = np.polyfit(lv[:, 3], (lv[:, 5] + 0.5) * LSB, 1)
                qa = np.polyfit(lv[:, 3], lv[:, 4], 1)
                d['gain_dc_code'] = float(q[0])
                d['gain_dc_amp'] = float(qa[0])
            if len(sn) >= 12:
                ph = sn[:, 1] + 2 * np.pi * FSIG * sn[:, 2] * TFR
                M = np.vstack([np.ones_like(ph), np.sin(ph), np.cos(ph)]).T
                for nm, y in (('code', (sn[:, 5] + 0.5) * LSB), ('amp', sn[:, 4])):
                    (a0, a1, a2), *_ = np.linalg.lstsq(M, y, rcond=None)
                    amp = float(np.hypot(a1, a2))
                    rr = y - M @ np.array([a0, a1, a2])
                    d['gain_sine_%s_db' % nm] = float(20 * np.log10(amp / AE))
                    d['sine_resid_%s_lsb' % nm] = float(np.std(rr) / LSB)
            J.setdefault(ck, {})[var] = d
            P('S1 %-5s %-4s: %d steady conversions of %d runs (%s), amplifier output %.4f..%.4f V, passes %d-%d, unresolved decisions %d' % (ck, var, d['n'], d['runs'], fns[0], d['vout_min'], d['vout_max'], d['passes'][0], d['passes'][1], d['unresolved']))
            P('   OFFSET code centre - input (below 2.05 V) %+.2f LSB (ADC alone %+.2f); code - ideal code %+d..%+d' % (d['offset_lsb'], d['offset_adc_alone_lsb'], d['code_minus_ideal'][0], d['code_minus_ideal'][1]))
            P('   INL beyond the fixed offset: sampling + DAC side (U) below 2.05 V %+.2f..%+.2f LSB, from the codes (e) %+.2f..%+.2f LSB -> |INL| below 2.05 V %.2f LSB (%s), whole range %.2f LSB (%s); top of the range (U): %s' % (
                d['inl_u_lo'][0], d['inl_u_lo'][1], d['inl_e_lo'][0], d['inl_e_lo'][1], d['inl_lo_lsb'], 'PASS' if d['inl_lo_lsb'] <= 1 else 'FAIL', d['inl_all_lsb'], 'PASS' if d['inl_all_lsb'] <= 1 else 'FAIL',
                ', '.join('%s V %+.2f' % kv for kv in d['top'].items()) or '-'))
            P('   AMPLIFIER -> ADC minus the ADC ALONE at the same input (U, below 2.05 V): mean %+.3f LSB (%+.3f..%+.3f)%s' % (d['amp_minus_adc_lo'][0], d['amp_minus_adc_lo'][1], d['amp_minus_adc_lo'][2],
                                                                                                                 ('; kick spike at the resume %.0f..%.0f mV' % tuple(d['kick_mv'])) if d['kick_mv'] else ''))
            if 'gain_dc_code' in d:
                P('   END-TO-END GAIN, DC levels (code vs electrode, contains the HPF droop): %.1f V/V (%+.2f %% vs 1000); amplifier output %.1f V/V' % (d['gain_dc_code'], (d['gain_dc_code'] / GNOM - 1) * 100, d['gain_dc_amp']))
            if 'gain_sine_code_db' in d:
                P('   END-TO-END GAIN, 23.4 Hz sine 450 uV pk: codes %.3f dB (fit residual %.2f LSB rms), amplifier output %.3f dB (residual %.2f LSB rms)' % (d['gain_sine_code_db'], d['sine_resid_code_lsb'], d['gain_sine_amp_db'], d['sine_resid_amp_lsb']))
    P('')
    P('COMPARISON variant vs orig per corner (same script, same session); rvt = the delivered variant, nodnw = the second fallback (ota2_rvt_nodnw.spice):')
    for ck in J:
        for vv in ('rvt', 'nodnw'):
            if 'orig' not in J[ck] or vv not in J[ck]:
                continue
            a, b = J[ck]['orig'], J[ck][vv]
            P('  %-5s %-5s offset %+.2f -> %+.2f LSB (%+.2f); |INL| below 2.05 V %.2f -> %.2f LSB; whole range %.2f -> %.2f LSB; amplifier -> ADC vs ADC alone (mean, below 2.05 V) %+.3f -> %+.3f LSB; kick spike max %s -> %s mV%s' % (
                ck, vv, a['offset_lsb'], b['offset_lsb'], b['offset_lsb'] - a['offset_lsb'], a['inl_lo_lsb'], b['inl_lo_lsb'], a['inl_all_lsb'], b['inl_all_lsb'], a['amp_minus_adc_lo'][0], b['amp_minus_adc_lo'][0],
                '%.0f' % a['kick_mv'][1] if a['kick_mv'] else '-', '%.0f' % b['kick_mv'][1] if b['kick_mv'] else '-',
                ('; sine gain (codes) %.3f -> %.3f dB, residual %.2f -> %.2f LSB rms' % (a['gain_sine_code_db'], b['gain_sine_code_db'], a['sine_resid_code_lsb'], b['sine_resid_code_lsb'])) if 'gain_sine_code_db' in a and 'gain_sine_code_db' in b else ''))
    open(os.path.join(ADC, 'sim', 'lp_rvt_x2_s1_report.log'), 'w').write('\n'.join(out) + '\n')
    json.dump(J, open(os.path.join(ADC, 'sim', 'lp_rvt_x2_s1_report.json'), 'w'), indent=1)


if __name__ == '__main__':
    if sys.argv[1] == 'run':
        run(sys.argv[2], sys.argv[3], float(sys.argv[4]) if len(sys.argv) > 4 else None, sys.argv[5] if len(sys.argv) > 5 else 'all')
    else:
        report()
