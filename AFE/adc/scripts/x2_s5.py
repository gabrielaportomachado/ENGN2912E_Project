#!/usr/bin/env python3
"""X2 / S5: CROSSTALK WITH REAL AMPLIFIERS.  Two full channels (afe_chc A4c + ADC analog cell each) sharing ONE bias_genc (vbn, vcm_in, vg1, vcm_out, vg2, vrs taps), the REF node
(one reference-electrode Randles network) and the modelled supply of S4 (VDD and VSS pad 2 nH + 0.25 ohm each, ASSUMED; amplifiers, bias, comparators, vhalf on the main rail vm; DAC drivers on the
strap vd = vm through 10 ohm; decaps 0.125 nF and 0.1 nF with 3 ohm ESR).  Channel 0 = aggressor (electrode step to an output level L, its ADC converts every frame, index 0 of the stagger),
channel 1 = victim (quiet electrode, its ADC converts every frame, index 1).  3 frames, SCLK 2 MHz, closed-loop replay of both ADCs.
Runs per level:  A = both ADCs convert;  B = ADC 0 held in tracking (no sampling, no conversion, no resume kick), same electrode signals: A - B on channel 1 = the effect of the aggressor's conversions;
C (once) = aggressor electrode quiet and ADC 0 idle: B - C = the effect of the aggressor's SIGNAL through the shared taps.
Reported: aggressor output spike at its resume (TG closes on the floating bottoms; D5 saw 0.2-0.36 V); victim output: peak of (A - B) between the aggressor's resume and its own resume 0.5 us later,
and (A - B) at the next two sampling instants [uV at the output, LSB, uV at the electrode]; victim code and transition level (A vs B); peak (A - B) on the shared taps.
usage: x2_s5.py <typ|ff85|ss-40> [levels=2.15,1.15] [TPRE_ms=4]   -> sim/x2_s5_<ck>.log, summary to sim/x2_s5_summary.log"""
import sys, os, time, numpy as np
H = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, H)
import x2lib as X, x2_adc as A, x2_s4 as S4
T = 500e-9; TFR = 250e-6; GNOM = 1000.0; TJ = 20e-6; TEDGE = 20e-6
LOGP = os.environ.get('X2_LOG_PREFIX', 'x2')          # log-file prefix (LP kit: the wrappers of AFE/layout/tb use their own so that the X2 logs stay as they are)
CALNPZ = os.environ.get('X2_CAL_NPZ', '')           # predictor calibration file instead of sim/x2_s1_<corner>.npz (a missing file = calibrate here); used with an extracted ADC cell
SH = ['vcm', 'vcmo', 'vbn', 'vrs', 'vg1', 'vg2', 'ref']
def esrc(c, v):
    return [f'Vsin{c} esa{c} tis 0', f'Vstp{c} es{c} esa{c} PWL(0 0 {TJ:.6e} 0 {TJ+TEDGE:.6e} {v:.9e})']
def idle(a, vdd):
    L = [f'Vrst{a} rst{a} vssi {vdd}', f'Vsam{a} sam{a} vssi {vdd}', f'Vsamb{a} samb{a} vssi 0', f'Vgdn{a} gdn{a} vssi 0', f'Vck{a} ck{a} vssi 0']
    return L + [f'Vgp{a}_{b} gp{a}_{b} vssi {vdd}' for b in range(12)] + [f'Vgn{a}_{b} gn{a}_{b} vssi 0' for b in range(12)]
def builder(ck, v0, active, tmax='1u'):
    vdd = X.COR[ck][2]
    def build(lines, meta):
        L = X.header(ck, f'S5 two channels, ADCs converting: {active}', amp=True, gmin='1e-16') + X.supply(vdd, S4.MODEL) + X.ref_electrode() + X.bias()
        L += X.amp_channel(0, esrc(0, v0)) + X.amp_channel(1, esrc(1, 0.0)) + X.adc_cell(0, 'out0') + X.adc_cell(1, 'out1')
        for a in (0, 1):
            if a not in active: L += idle(a, vdd)
        sv = ['v(vm)', 'v(vd)', 'v(vssi)', 'v(out0)', 'v(out1)'] + [f'v({n})' for n in SH] + [f'v({n}{a})' for a in (0, 1) for n in ('t', 'ci', 'cq', 'cqn')]
        return '\n'.join(L + lines + X.tail(sv, meta['tcap'].max() + 3e-9, tmax, tstep='1n')) + '\n'
    return build
if __name__ == '__main__':
    ck = sys.argv[1]; levels = [float(x) for x in (sys.argv[2] if len(sys.argv) > 2 else '2.15,1.15').split(',')]; tpre = float(sys.argv[3]) * 1e-3 if len(sys.argv) > 3 else 4e-3
    vdd = X.COR[ck][2]; lsb = vdd / 4096; out = []; t00 = time.time()
    def P(s): print(s, flush=True); out.append(s)
    P(f'# X2 S5 {ck} {X.COR[ck]}: 2 channels (A4c amplifier + ADC cell) on one bias_genc, shared REF electrode, supply model {S4.MODEL}; aggressor levels {levels} V, TPRE {tpre*1e3:g} ms, SCLK 2 MHz, abstol 1e-12')
    cal = X.Cal(vdd); npz = CALNPZ or f'{X.ADC}/sim/x2_s1_{ck}.npz'
    if os.path.exists(npz): z = np.load(npz); cal.theta, cal.alpha, cal.c0 = float(z['theta']), float(z['alpha']), float(z['c0']); cal.gw = z['gw'] if 'gw' in z else cal.gw; cal.obs = [tuple(r) for r in z['obs']] if 'obs' in z else []
    else:
        vc = list(1.15 + (np.arange(9) + 0.37) / 9); cal, rows, _ = A.static(ck, vc, log=P, tag=f's5cal_{ck}')
    cal.lo, cal.hi = cal.theta - 0.05 * lsb, cal.theta + 0.05 * lsb
    tcs = [tpre + k * TFR for k in range(3)]; ex = {}
    for L in levels:
        v0 = (L - 1.65) / GNOM; g0 = 1.65 + 0.995 * (L - 1.65)
        ex[('A', L)] = X.Exp(f'A{L:.2f}'.replace('.', 'p'), ck, 2, tcs, T, builder(ck, v0, (0, 1)), [[g0] * 3, [1.65] * 3], cal, ref='vssi', adcs=[0, 1])
        ex[('B', L)] = X.Exp(f'B{L:.2f}'.replace('.', 'p'), ck, 1, tcs, T, builder(ck, v0, (1,)), [[1.65] * 3], cal, ref='vssi', adcs=[1])
    ex[('C', 0)] = X.Exp('C', ck, 1, tcs, T, builder(ck, 0.0, (1,)), [[1.65] * 3], cal, ref='vssi', adcs=[1])
    X.closed_loop(list(ex.values()), log=P, tag=f's5_{ck}', maxpass=10)
    for k, e in ex.items():
        if e.failed: P(f'S5 {ck} run {k}: FAILED after {e.npass} passes: {e.failed}')
    worst = dict(dv=0.0, dT=0.0, dc=0, spk=0.0, vict=0.0); eC = ex[('C', 0)]
    for L in levels:
        a, b = ex[('A', L)], ex[('B', L)]
        if a.failed or b.failed: continue
        wa, wb, ma, mb = a.wave, b.wave, a.meta, b.meta; ca = a.codes(); cb = b.codes()
        for f in range(3):
            vo0 = float(wa.at('v(out0)', tcs[f])); vo1 = float(wa.at('v(out1)', tcs[f])); vo1b = float(wb.at('v(out1)', tcs[f])); dv = vo1 - vo1b
            ta = A.trans_err(cal, vo1, a.x[1, f, 11], int(ca[1, f])); tb = A.trans_err(cal, vo1b, b.x[0, f, 11], int(cb[0, f]))
            # the level of the tested transition referred to the SAME input (victim input of run B) so that dT contains the change of the sampled value too
            dT = (vo1 - vo1b) / lsb - (ta - tb) if False else (a.x[1, f, 11] - b.x[0, f, 11]) / cal.alpha / lsb if int(ca[1, f]) == int(cb[0, f]) else float('nan')
            s = f'S5 {ck} L={L:.2f} frame {f}: aggressor out {vo0:.5f} V code {int(ca[0, f])} | victim out A {vo1:.6f} V, B {vo1b:.6f} V, A - B {dv*1e6:+.1f} uV = {dv/lsb:+.4f} LSB = {dv/GNOM*1e6:+.4f} uV at the electrode | victim code A {int(ca[1, f])} / B {int(cb[0, f])} (diff {int(ca[1, f])-int(cb[0, f]):+d}), trial-12 residue change (A - B) {dT:+.3f} LSB'
            if f > 0:
                worst['dv'] = max(worst['dv'], abs(dv)); worst['dc'] = max(worst['dc'], abs(int(ca[1, f]) - int(cb[0, f])))
                if not np.isnan(dT): worst['dT'] = max(worst['dT'], abs(dT))
            if f < 2:
                tr0 = ma['tres'][0, f]; tr1 = ma['tres'][1, f]
                mk = (wa.t > tr0 - 1e-9) & (wa.t < tr0 + 2e-6); v = wa.v('v(out0)')[mk]; spk = float(v[np.argmax(np.abs(v - v[0]))] - v[0]); worst['spk'] = max(worst['spk'], abs(spk))
                mk1 = (wa.t > tr1 - 1e-9) & (wa.t < tr1 + 2e-6); v1 = wa.v('v(out1)')[mk1]; spk1 = float(v1[np.argmax(np.abs(v1 - v1[0]))] - v1[0])
                tg = np.arange(tr0 - 20e-9, tr1 - 5e-9, 0.05e-9); d1 = wa.at('v(out1)', tg) - wb.at('v(out1)', tg); pk = float(d1[np.argmax(np.abs(d1))]); worst['vict'] = max(worst['vict'], abs(pk))
                tl = [5e-6, 20e-6, 100e-6]; dl = [float(wa.at('v(out1)', tr0 + x) - wb.at('v(out1)', tr0 + x)) for x in tl]
                sh = []
                for n in SH + ['vm', 'vd', 'vssi']:
                    tg2 = np.arange(tr0 - 20e-9, tr0 + 0.45e-6, 0.05e-9); dd = wa.at(f'v({n})', tg2) - wb.at(f'v({n})', tg2); sh.append(f'{n} {dd[np.argmax(np.abs(dd))]*1e3:+.3f}')
                s += (f' || resume of the aggressor at +{(tr0-tcs[f])*1e6:.2f} us: aggressor output spike {spk*1e3:+.1f} mV; victim own-resume spike {spk1*1e3:+.1f} mV; victim output (A - B) peak before its own resume {pk*1e3:+.3f} mV = {pk/GNOM*1e6:+.3f} uV at the electrode; '
                      f'(A - B) at +5/20/100 us: ' + ' / '.join(f'{x*1e6:+.1f}' for x in dl) + ' uV | peak (A - B) in the 0.45 us after the aggressor resume [mV]: ' + ', '.join(sh))
            P(s)
        if not eC.failed and L == levels[0]:
            for f in range(3):
                vb = float(wb.at('v(out1)', tcs[f])); vc = float(eC.wave.at('v(out1)', tcs[f]))
                P(f'S5 {ck} L={L:.2f} frame {f}: SIGNAL crosstalk (B - C, aggressor output {float(wb.at("v(out0)", tcs[f]))-1.65:+.3f} V from mid-scale, no aggressor conversions): victim output {(vb-vc)*1e6:+.1f} uV = {(vb-vc)/lsb:+.4f} LSB = {(vb-vc)/GNOM*1e6:+.4f} uV at the electrode; victim code B {int(cb[0, f])} / C {int(eC.codes()[0, f])}; shared taps B - C: ' +
                  ', '.join(f'{n} {float(wb.at(f"v({n})", tcs[f]) - eC.wave.at(f"v({n})", tcs[f]))*1e6:+.1f} uV' for n in SH))
    ok = worst['dv'] / lsb < 0.5 and worst['dT'] < 0.5 and worst['dc'] == 0
    s = (f'RESULT S5 {ck}: aggressor kick spike on its own output up to {worst["spk"]*1e3:.0f} mV; on the victim output (A - B) peak {worst["vict"]*1e3:.3f} mV right after it; at the victim\'s next sampling instants |A - B| <= {worst["dv"]*1e6:.1f} uV = {worst["dv"]/lsb:.4f} LSB '
         f'= {worst["dv"]/GNOM*1e6:.4f} uV input-referred; victim code changes {worst["dc"]}, trial-12 residue change <= {worst["dT"]:.3f} LSB | {"PASS" if ok else "FAIL"} (limit 0.5 LSB); wall {time.time()-t00:.0f} s')
    P(s); open(f'{X.ADC}/sim/{LOGP}_s5_summary.log', 'a').write(s + '\n')
    open(f'{X.ADC}/sim/{LOGP}_s5_{ck}.log', 'w').write('\n'.join(out) + '\n')
    open(f'{X.ADC}/sim/{LOGP}_done.txt', 'a').write(f'{time.strftime("%F %T")} x2_s5 {ck} done, wall {time.time()-t00:.0f} s\n')
