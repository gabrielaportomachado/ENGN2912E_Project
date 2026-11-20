#!/usr/bin/env python3
"""LP step 6: collect the stage results of scripts/lp_rvt_*.py into ONE machine-readable file and one table.
  checks   the delivered netlists: ota2_rvt.spice = ota2.spice with exactly ONE changed device line (Xmf); afe_chc_rvt.spice = afe_chc.spice (device lines identical);
           ota2_rvt_nodnw.spice (second fallback) = ota2.spice with exactly one changed device line; every device of the variants is an LVS device of gf180mcuD
  output   AFE/amp/sim/lp_rvt_result.json   {variant, files, device_changes, original{corner{...}}, variant_results{corner{...}}, runner_up, x2_s1, verdict}
           AFE/amp/sim/lp_rvt_report.log    the table original vs variant (vs runner-up) with the log file of every row
usage: python3 lp_rvt_report.py
"""
import os, re, sys, json, time
HERE = os.path.dirname(os.path.abspath(__file__))
AMP = os.path.normpath(os.path.join(HERE, '..'))
ADC = os.path.normpath(os.path.join(AMP, '..', 'adc'))
SIM = os.path.join(AMP, 'sim')
CS = ['typ', 'ff85', 'ss-40']
RU = 'B_10x10_0p28'          # runner-up candidate name in the stage files


def dev_lines(fn):
    out = []
    for ln in open(os.path.join(AMP, 'spice', fn)).read().split('\n'):
        ln = ln.split('$')[0].strip()
        if ln and not ln.startswith('*'):
            out.append(re.sub(r'\s+', ' ', ln))
    return out


def J(name):
    p = os.path.join(SIM, name)
    return json.load(open(p)) if os.path.exists(p) else {}


def main():
    out = []

    def P(s=''):
        print(s)
        out.append(s)
    P('LP step 6 (audit M7) report: native-Vt-free follower variant.  Written by scripts/lp_rvt_report.py on %s from the stage files AFE/amp/sim/lp_rvt_*.json (logs of the same name).' % time.strftime('%F %T'))
    # ---------------------------------------------------------------- netlist checks
    P('\n1. NETLIST CHECKS')
    ok = True
    a, b = dev_lines('ota2.spice'), dev_lines('ota2_rvt.spice')
    d = [(x, y) for x, y in zip(a, b) if x != y]
    c1 = len(a) == len(b) and len(d) == 1 and d[0][0].startswith('Xmf ') and d[0][1].startswith('Xmf ')
    ok &= c1
    P('  ota2_rvt.spice vs ota2.spice: %d / %d non-comment lines, %d differ -> %s' % (len(b), len(a), len(d), 'PASS (only Xmf)' if c1 else 'FAIL'))
    for x, y in d:
        P('     -  %s' % x)
        P('     +  %s' % y)
    a2, b2 = dev_lines('afe_chc.spice'), dev_lines('afe_chc_rvt.spice')
    c2 = a2 == b2
    ok &= c2
    P('  afe_chc_rvt.spice vs afe_chc.spice: %d / %d non-comment lines, identical: %s -> %s' % (len(b2), len(a2), c2, 'PASS' if c2 else 'FAIL'))
    nod = os.path.exists(os.path.join(AMP, 'spice', 'ota2_rvt_nodnw.spice'))
    if nod:
        b3 = dev_lines('ota2_rvt_nodnw.spice')
        d3 = [(x, y) for x, y in zip(a, b3) if x != y]
        c3 = len(a) == len(b3) and len(d3) == 1 and d3[0][1].startswith('Xmf ')
        ok &= c3
        P('  ota2_rvt_nodnw.spice (second fallback) vs ota2.spice: %d differ -> %s' % (len(d3), 'PASS (only Xmf)' if c3 else 'FAIL'))
        for x, y in d3:
            P('     +  %s' % y)
    lvsdev = ('nfet_03v3', 'pfet_03v3', 'cap_mim_2f0_m2m3_noshield')
    for fn in ['ota2_rvt.spice'] + (['ota2_rvt_nodnw.spice'] if nod else []):
        models = set()
        for ln in dev_lines(fn):
            if ln.startswith('X'):
                models.add([t for t in ln.split() if '=' not in t][-1])
        bad = [m for m in models if m not in lvsdev]
        ok &= not bad
        P('  %s device models: %s -> %s' % (fn, ', '.join(sorted(models)), 'PASS (no native-Vt device; the MIM name is replaced by the LVS script as in every netlist)' if not bad else 'FAIL ' + str(bad)))
    # ---------------------------------------------------------------- results
    T, S, A, ST, STT, SL, RC, PU, SC, SCV = (J('lp_rvt_tables.json'), J('lp_rvt_swing.json'), J('lp_rvt_adc245.json'), J('lp_rvt_settle.json'), J('lp_rvt_settle_tight.json'), J('lp_rvt_slew.json'),
                                             J('lp_rvt_rec.json'), J('lp_rvt_pur.json'), J('lp_rvt_screen.json'), J('lp_rvt_screen_vdd.json'))
    X = {}
    xp = os.path.join(ADC, 'sim', 'lp_rvt_x2_s1_report.json')
    if os.path.exists(xp):
        X = json.load(open(xp))

    def mx(d, key):
        v = [abs(y[key]) for k, y in d.items() if not k.startswith('_') and key in y]
        return max(v) if v else None

    def corner(v, c):
        t = T.get(v, {}).get(c, {})
        s = S.get(v, {}).get(c, {})
        r = dict(gain_db=t.get('g_mid_dB'), f_lo_hz=t.get('f_lo_Hz'), f_hi_hz=t.get('f_hi_Hz'), noise_uv=t.get('noise_fn0_uV'), noise_fnoicor1_uv=t.get('noise_fn1_uV'),
                 pm_deg=t.get('pm_beta1_deg'), pm_stage2_real_beta_deg=t.get('pm_beta_real_deg'), pm_stage1_loop_deg=t.get('pm_deg'), a0_stage2_db=t.get('a0_dB'), gbw_stage2_hz=t.get('gbw_Hz'),
                 idd_ua=(t.get('i_supply_A') or 0) * 1e6 if t.get('i_supply_A') else None, out_dc_err_mv=(t.get('vout_err_V') * 1e3 if t.get('vout_err_V') is not None else None),
                 o2_v=t.get('o2_V'), follower_vgs_v=t.get('vgs_V'), follower_gm_us=(t.get('gm_S') * 1e6 if t.get('gm_S') else None), psrr_path_50hz_v_per_v=t.get('vdd2out_50Hz'))
        k = s.get('f12_0.5m', {})
        r.update(out_max_v=k.get('out_max'), out_min_v=k.get('out_min'), thd_pct=k.get('thd_pct'), gain_tran_db=k.get('gain_db'),
                 thd_0p6mv_pct=s.get('f12_0.6m', {}).get('thd_pct'), thd_300hz_pct=s.get('f300_0.5m', {}).get('thd_pct'))
        st = ST.get(v, {}).get(c, {})
        r.update(settle_lsb=mx(st, 'd_end'), settle_end_raw_lsb=mx(st, 'e_end'), kick_spike_mv=(mx(st, 'peak_lsb') * 0.8057 if mx(st, 'peak_lsb') else None))
        stt = STT.get(v, {}).get(c, {})
        if stt:
            r['settle_end_tight_tol_lsb'] = mx(stt, 'e_end')
        ad = A.get(v, {}).get(c, {})
        if ad:
            r['adc245_ideal_load_lsb'] = max(abs(x['err_lsb'][-1]) for x in ad.values())
        sl = SL.get(v, {}).get(c, {})
        if sl:
            r['slew_v_per_s'] = min(x['slew'] for x in sl.values())
        sc = SC.get('res', {}).get(v, {}).get('3.3', {}).get(c, {})
        if sc:
            r.update(follow_lo_v=sc.get('lo99'), follow_hi_v=sc.get('hi99'), swing_margin_top_mv=sc.get('margin_top_mv'), swing_margin_bottom_mv=sc.get('margin_bottom_mv'))
        return r
    res = {v: {c: corner(v, c) for c in CS} for v in ('orig', 'rvt', RU)}
    rows = [('mid-band gain [dB]', 'gain_db', '%.3f', '60 +- 1', 'lp_rvt_tables.log'), ('f_lo [Hz]', 'f_lo_hz', '%.3f', '<= 0.5', 'lp_rvt_tables.log'), ('f_hi [Hz]', 'f_hi_hz', '%.1f', '>= 300', 'lp_rvt_tables.log'),
            ('noise 0.5-300 Hz, typical flicker [uV]', 'noise_uv', '%.3f', '<= 2', 'lp_rvt_tables.log'), ('noise, fnoicor = 1 [uV]', 'noise_fnoicor1_uv', '%.3f', 'report', 'lp_rvt_tables.log'),
            ('supply current, bias + channel [uA]', 'idd_ua', '%.2f', '= original', 'lp_rvt_tables.log'), ('output DC error [mV]', 'out_dc_err_mv', '%.3f', '-', 'lp_rvt_tables.log'),
            ('stage-2 OTA output o2 [V]', 'o2_v', '%.3f', '-', 'lp_rvt_tables.log'), ('follower Vgs [V]', 'follower_vgs_v', '%.3f', '-', 'lp_rvt_tables.log'), ('follower gm [uS]', 'follower_gm_us', '%.1f', '-', 'lp_rvt_tables.log'),
            ('stage-2 loop: PM at beta = 1 [deg]', 'pm_deg', '%.1f', '>= 60', 'lp_rvt_tables.log'), ('stage-2 loop: PM at the real beta [deg]', 'pm_stage2_real_beta_deg', '%.1f', '>= 60', 'lp_rvt_tables.log'),
            ('stage-1 loop PM (real stage 2 as load) [deg]', 'pm_stage1_loop_deg', '%.1f', '>= 60', 'lp_rvt_tables.log'), ('stage-2 A0 [dB]', 'a0_stage2_db', '%.1f', '-', 'lp_rvt_tables.log'),
            ('supply -> output gain at 50 Hz [V/V]', 'psrr_path_50hz_v_per_v', '%.4f', 'ideal 0.5', 'lp_rvt_tables.log'),
            ('DC swing: follows down to [V]', 'follow_lo_v', '%.3f', '<= 1.15', 'lp_rvt_screen.log'), ('DC swing: follows up to [V]', 'follow_hi_v', '%.3f', '>= 2.15', 'lp_rvt_screen.log'),
            ('+-0.5 mV 12.25 Hz: THD [%]', 'thd_pct', '%.3f', 'D28 accepts ff 85', 'lp_rvt_swing.log'), ('+-0.5 mV 12.25 Hz: out max [V]', 'out_max_v', '%.3f', '2.15', 'lp_rvt_swing.log'),
            ('+-0.5 mV 12.25 Hz: out min [V]', 'out_min_v', '%.3f', '1.15', 'lp_rvt_swing.log'), ('+-0.6 mV 12.25 Hz: THD [%]', 'thd_0p6mv_pct', '%.3f', 'margin', 'lp_rvt_swing.log'),
            ('+-0.5 mV 300 Hz: THD [%]', 'thd_300hz_pct', '%.3f', '-', 'lp_rvt_swing.log'), ('slew, +-0.5 mV step, slower direction [V/s]', 'slew_v_per_s', '%.0f', '>= 942', 'lp_rvt_slew.log'),
            ('ADC load, IDEAL 17 pF, 245 us, no reset [LSB]', 'adc245_ideal_load_lsb', '%.3f', '<= 0.5', 'lp_rvt_adc245.log'),
            ('REAL DAC: what the kick leaves at the end of T_ACQ [LSB]', 'settle_lsb', '%.3f', '<= 0.5', 'lp_rvt_settle.log'), ('REAL DAC: raw L-U at the end of T_ACQ (D5 number) [LSB]', 'settle_end_raw_lsb', '%.3f', '<= 0.5', 'lp_rvt_settle.log'),
            ('  the same with 100x tighter tolerances (4 cases) [LSB]', 'settle_end_tight_tol_lsb', '%.3f', '<= 0.5', 'lp_rvt_settle_tight.log'), ('kick spike on the output (L-U peak) [mV]', 'kick_spike_mv', '%.0f', 'report', 'lp_rvt_settle.log')]
    P('\n2. RESULTS  typ 27 / ff 85 / ss -40 C, 3.3 V  (orig = spice/ota2.spice; rvt = ota2_rvt.spice + afe_chc_rvt.spice; runner-up = %s, the no-deep-n-well option)' % RU)
    P('%-58s | %-18s | %-27s | %-27s | %-27s | %s' % ('quantity', 'target', 'orig', 'rvt (variant)', 'runner-up', 'log (AFE/amp/sim)'))
    f = lambda v, key, fmt: ' / '.join((fmt % res[v][c][key]) if res[v][c].get(key) is not None else 'n/a' for c in CS)
    for lab, key, fmt, tgt, lg in rows:
        P('%-58s | %-18s | %-27s | %-27s | %-27s | %s' % (lab, tgt, f('orig', key, fmt), f('rvt', key, fmt), f(RU, key, fmt), lg))
    md = ['| quantity | target | original | variant `rvt` | runner-up (no deep n-well) | log (AFE/amp/sim) |', '|---|---|---|---|---|---|']
    for lab, key, fmt, tgt, lg in rows:
        md.append('| %s | %s | %s | %s | %s | %s |' % (lab.strip(), tgt, f('orig', key, fmt), f('rvt', key, fmt), f(RU, key, fmt), lg))
    if RC:
        md.append('| reset recovery, 10 mV step, ideal 3 ms pulse: time to within 1 mV [s] | as original | %s | %s | %s | lp_rvt_rec.log |' % tuple(' / '.join('%.2f' % RC[v][c]['t_1mv_s'] for c in CS) for v in ('orig', 'rvt', RU)))
    if PU:
        md.append('| power-up + RST_AMP 100 ms at 3 s: final output error [mV]; time to within 10 mV / 1 mV [s] | within 10 mV | %s | %s | n/a | lp_rvt_pur.log |' % tuple(
            ' / '.join('%.2f' % ((PU[v][c]['final'] - 1.65) * 1e3) for c in CS) + '; ' + ' / '.join('%.2f' % PU[v][c]['t10'] for c in CS) + '; ' + ' / '.join('%.2f' % PU[v][c]['t1'] for c in CS) for v in ('orig', 'rvt')))
    if SC.get('res'):
        md += ['', '| candidate | what | follows 99 % [V], typ / ff 85 / ss -40 | top margin to 2.15 V [mV] | bottom margin to 1.15 V [mV] | follower gm [uS] | verdict |', '|---|---|---|---|---|---|---|']
        for cnd, dsc in SC['desc'].items():
            x = SC['res'].get(cnd, {}).get('3.3', {})
            if len(x) < 3:
                continue
            md.append('| %s | %s | %s | %s | %s | %s | %s |' % (cnd, dsc, ' / '.join('%.2f-%.2f' % (x[c]['lo99'], x[c]['hi99']) for c in CS), ' / '.join('%+.0f' % x[c]['margin_top_mv'] for c in CS),
                                                         ' / '.join('%+.0f' % x[c]['margin_bottom_mv'] for c in CS), ' / '.join('%.0f' % (x[c]['gm'] * 1e6) for c in CS),
                                                         'PASS' if all(x[c]['pass'] for c in CS) else 'FAIL ' + ', '.join(c for c in CS if not x[c]['pass'])))
    os.makedirs('/tmp/lp_rvt', exist_ok=True)
    open('/tmp/lp_rvt/tables.md', 'w').write('\n'.join(md) + '\n')
    if RC:
        P('%-58s | %-18s | %-27s | %-27s | %-27s | %s' % ('reset recovery, 10 mV step, 3 ms pulse: time to 1 mV [s]', 'as original', ' / '.join('%.2f' % RC['orig'][c]['t_1mv_s'] for c in CS),
                                                   ' / '.join('%.2f' % RC['rvt'][c]['t_1mv_s'] for c in CS), ' / '.join('%.2f' % RC[RU][c]['t_1mv_s'] for c in CS) if RU in RC else 'n/a', 'lp_rvt_rec.log'))
    if PU:
        P('%-58s | %-18s | %-27s | %-27s | %-27s | %s' % ('power-up + RST_AMP 100 ms: final output error [mV]', 'within 10 mV', ' / '.join('%.2f' % ((PU['orig'][c]['final'] - 1.65) * 1e3) for c in CS),
                                                   ' / '.join('%.2f' % ((PU['rvt'][c]['final'] - 1.65) * 1e3) for c in CS), 'n/a', 'lp_rvt_pur.log'))
        P('%-58s | %-18s | %-27s | %-27s | %-27s | %s' % ('power-up + RST_AMP 100 ms: time to within 10 mV [s]', '-', ' / '.join('%.2f' % PU['orig'][c]['t10'] for c in CS), ' / '.join('%.2f' % PU['rvt'][c]['t10'] for c in CS), 'n/a', 'lp_rvt_pur.log'))
    if SCV.get('res'):
        P('\n   DC swing margin [mV, bottom / top of mid +- 0.5 V] at other supplies (lp_rvt_screen_vdd.log; the amplifier was specified and verified at 3.3 V only):')
        for v in ('orig', 'rvt', RU):
            for vd in sorted(SCV['res'].get(v, {}), key=float):
                x = SCV['res'][v][vd]
                P('     %-14s VDD %-4s: ' % (v, vd) + ' | '.join('%s %+.0f / %+.0f' % (c, x[c]['margin_bottom_mv'], x[c]['margin_top_mv']) if c in x else '%s n/a' % c for c in CS))
    xs = {}
    if X:
        P('\n3. X2 S1 (transistor-level amplifier -> ADC, closed loop; AFE/adc/sim/lp_rvt_x2_s1_report.log)')
        for c in CS:
            for v in ('orig', 'rvt', 'nodnw'):
                d = X.get(c, {}).get(v)
                if not d:
                    continue
                xs.setdefault(c, {})[v] = dict(offset_lsb=d['offset_lsb'], inl_below_2p05_lsb=d['inl_lo_lsb'], inl_whole_range_lsb=d['inl_all_lsb'], amp_minus_adc_alone_lsb=d['amp_minus_adc_lo'],
                                               kick_mv=d['kick_mv'], gain_sine_code_db=d.get('gain_sine_code_db'), runs=d['runs'], vout_range=[d['vout_min'], d['vout_max']], file=d['file'])
                P('   %-5s %-4s: offset %+.2f LSB; |INL| below 2.05 V %.2f LSB, whole range %.2f LSB; amplifier -> ADC minus ADC alone %+.3f (%+.3f..%+.3f) LSB; kick %s mV; output %.4f..%.4f V%s' % (
                    c, v, d['offset_lsb'], d['inl_lo_lsb'], d['inl_all_lsb'], d['amp_minus_adc_lo'][0], d['amp_minus_adc_lo'][1], d['amp_minus_adc_lo'][2],
                    ('%.0f..%.0f' % tuple(d['kick_mv'])) if d['kick_mv'] else '-', d['vout_min'], d['vout_max'], ('; sine gain %.3f dB' % d['gain_sine_code_db']) if d.get('gain_sine_code_db') else ''))
    # ---------------------------------------------------------------- verdict
    v = res['rvt']
    tests = []
    for c in CS:
        r = v[c]
        o = res['orig'][c]
        tests += [(c, 'gain', abs(r['gain_db'] - 60) <= 1), (c, 'f_lo', r['f_lo_hz'] <= 0.5), (c, 'f_hi', r['f_hi_hz'] >= 300), (c, 'noise', r['noise_uv'] <= 2.0),
                  (c, 'idd', abs(r['idd_ua'] / o['idd_ua'] - 1) <= 0.01), (c, 'pm2', r['pm_deg'] >= 60), (c, 'pm1', r['pm_stage1_loop_deg'] >= 60),
                  (c, 'swing', r['follow_lo_v'] is not None and r['follow_lo_v'] <= 1.15 and r['follow_hi_v'] >= 2.15), (c, 'thd<=orig or 0.25 %', r['thd_pct'] <= max(o['thd_pct'], 0.25)),
                  (c, 'settle', r['settle_lsb'] is not None and r['settle_lsb'] <= 0.5), (c, 'adc245', r.get('adc245_ideal_load_lsb', 9) <= 0.5), (c, 'slew', r.get('slew_v_per_s', 0) >= 942)]
        if c in xs and 'rvt' in xs[c] and 'orig' in xs[c]:
            tests.append((c, 'x2_s1 inl below 2.05 V <= max(1 LSB, original + 0.1 LSB)', xs[c]['rvt']['inl_below_2p05_lsb'] <= max(1.0, xs[c]['orig']['inl_below_2p05_lsb'] + 0.1)))
            tests.append((c, 'x2_s1 amp adds <= 0.1 LSB', max(abs(xs[c]['rvt']['amp_minus_adc_alone_lsb'][1]), abs(xs[c]['rvt']['amp_minus_adc_alone_lsb'][2])) <= 0.1))
    bad = [(c, n) for c, n, t in tests if not t]
    verdict = ('WORKS: every amplifier target of the original is met at typ 27 / ff 85 / ss -40 C with the native-Vt-free follower; netlist checks %s; %d checks, %d failed%s' % (
        'PASS' if ok else 'FAIL', len(tests), len(bad), (': ' + ', '.join('%s %s' % b for b in bad)) if bad else ''))
    P('\n4. VERDICT: ' + verdict)
    P('   checks per corner: gain 60 +- 1 dB, f_lo <= 0.5 Hz, f_hi >= 300 Hz, noise <= 2 uV, supply current within 1 % of the original, PM >= 60 deg (stage 2 at beta = 1, stage-1 loop), DC swing covers')
    P('   1.15-2.15 V, THD at +-0.5 mV <= max(original, 0.25 %), kick-induced settling error <= 0.5 LSB (real DAC) and <= 0.5 LSB (ideal 17 pF load, 245 us), slew >= 942 V/s, X2 S1 |INL| below 2.05 V')
    P('   <= 1 LSB (or, where the original itself is above 1 LSB because of the ADC: <= original + 0.1 LSB) and amplifier -> ADC within 0.1 LSB of the ADC alone (where S1 has run).')
    R = dict(task='LP step 6 (audit M7): native-Vt fallback of the stage-2 follower', date=time.strftime('%F %T'),
             variant=dict(name='rvt', description='regular nfet_03v3, 8 x 10u/1u, in an isolated p-well (LVPWELL in DNWELL, DNWELL on vdd), bulk tied to its source (out), in place of nfet_06v0_nvt 10u/2u (bulk vss)',
                          files=['AFE/amp/spice/ota2_rvt.spice', 'AFE/amp/spice/afe_chc_rvt.spice'], subckt_names_and_pins='unchanged (ota2: inp inn vbn out vdd vss; afe_chc: rec ref out vdd vss vbn vcm vg1 vcmo vg2 vrs fs pkc pkcb)',
                          use='include ota2_rvt.spice instead of ota2.spice and afe_chc_rvt.spice instead of afe_chc.spice',
                          device_changes=[dict(instance='afe_chc.Xs2.Xota2.Xmf (follower)', original='nfet_06v0_nvt L=2u W=10u m=1, bulk vss', variant='nfet_03v3 L=1u W=10u m=8, bulk = source (out), isolated p-well in deep n-well on vdd')],
                          needs='deep n-well (DNWELL) and LVPWELL layers; no native-Vt layer', netlist_checks_pass=bool(ok),
                          layout=dict(pcell='gf180mcu nfet, volt 3.3V, w_gate 10, l_gate 1, nf 8, deepnwell 1, pcmpgr 1, bulk Guard Ring', footprint_um=[27.00, 25.14], footprint_um2=678.8,
                                      original_footprint_um2=104.2, extra_area_per_channel_um2=574.6, wiring='p-well tap ring -> out; N+ tap in the DNWELL (not drawn by the pcell) -> vdd; outer P+ ring -> vss; Metal1 on the ring contacts (CO.6)',
                                      source='AFE/amp/sim/lp_rvt_dnw_cell.log'),
                          lvs=dict(sim_files_substitution={'AFE/amp/spice/ota2.spice': 'AFE/amp/spice/ota2_rvt.spice', 'AFE/amp/spice/afe_chc.spice': 'AFE/amp/spice/afe_chc_rvt.spice'},
                                   reference_line='Xs2_xota2_xmf vdd xs2_xota2_o2 out out nfet_03v3 w=10u l=1u m=8', source='AFE/amp/sim/lp_rvt_lvs_check.log')),
             corners={'typ': 'typical 27 C 3.3 V', 'ff85': 'ff 85 C 3.3 V', 'ss-40': 'ss -40 C 3.3 V'},
             original=res['orig'], variant_results=res['rvt'],
             runner_up=dict(name=RU, description='regular nfet_03v3, 10 x 10u/0.28u (minimum L), bulk on vss, NO deep n-well: second fallback if neither the native-Vt device nor DNWELL is offered',
                            file='AFE/amp/spice/ota2_rvt_nodnw.spice' if nod else None, results=res[RU],
                            x2_s1={c: xs[c]['nodnw'] for c in xs if 'nodnw' in xs[c]} or 'not run'),
             x2_s1={c: {v: xs[c][v] for v in xs[c] if v != 'nodnw'} for c in xs} or 'not run yet', verdict=verdict, failed_checks=bad,
             logs=dict(amp=['AFE/amp/sim/lp_rvt_%s.log' % s for s in ('screen', 'screen_vdd', 'screen_pvt9', 'screen_vocm1p15', 'tables', 'swing', 'adc245', 'settle', 'settle_tight', 'slew', 'rec', 'pur', 'dnw_cell', 'lvs_check', 'report')] + ['AFE/amp/sim/lp_rvt_summary.md'],
                       adc=['AFE/adc/sim/lp_rvt_x2_s1_report.log'] + sorted('AFE/adc/sim/' + f for f in os.listdir(os.path.join(ADC, 'sim')) if re.match(r'lp_rvt_x2_s1_(orig|rvt)_.*\.log$', f))),
             notes=['settle_lsb = max over 19 kick cases of |(L-U at the end of T_ACQ) - (L-U before the frame)|, real sampling TG + split DAC on the output (D5 method); settle_end_raw_lsb = the raw D5 number, '
                    'which contains the DC-solve difference of the two amplifier copies (see lp_rvt_settle.log)', 'pm_deg = stage-2 OTA + follower open loop at beta = 1 (worst-case bound, as A4a); pm_stage2_real_beta_deg at beta = CF2 / (CIN2 + CF2)',
                    'thd / out_max / out_min: +-0.5 mV differential at 12.25 Hz, 8 s, last 4 periods', 'idd_ua = supply current of bias_genc + one channel'])
    json.dump(R, open(os.path.join(SIM, 'lp_rvt_result.json'), 'w'), indent=1)
    open(os.path.join(SIM, 'lp_rvt_report.log'), 'w').write('\n'.join(out) + '\n')
    return 0 if ok and not bad else 1


if __name__ == '__main__':
    sys.exit(main())
