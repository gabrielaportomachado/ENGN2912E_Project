#!/usr/bin/env python3
"""X2 / S4: 8-ADC TRANSISTOR-LEVEL RUN  [REVIEW R16: the number of ADC cells is X2_NADC (default 8 = the text below, byte-identical behaviour); X2_NADC=4 = the 4-channel chip, whose default decap is the one of
AFE/layout/lvs/dbs_afe_top.spice: Cm = 74 x 1.593 pF = 117.9 pF, Cd = 30 x 1.593 pF = 47.8 pF; the calibration inputs use ADC indices 0, (N-1)//2, N-1 (= 0, 3, 7 for N = 8)] on the modelled supply, closed-loop PWL replay per ADC.
8 ADC analog cells (sampling TG + split 6+6 DAC + drivers [dac_sw] + cmp_p + Cref 7 pF + vhalf) share:
  one VDD pad and one VSS pad, EACH 2 nH + 0.25 ohm (ASSUMED) and 1 pF of pad capacitance to the board ground (ASSUMED, also a numerical necessity: x2lib.supply) -> on-chip main rail vm / on-chip ground vssi;
  main rail vm: comparators, vhalf dividers, Cref TGs [+ digital-logic charge 1.5 pC per ADC per SCLK edge, ESTIMATE, as a current source];  decap Cm 0.125 nF + ESR Rd 3 ohm (ideal C + ESR);
  DAC strap vd = vm through Rs 10 ohm: the bottom-plate drivers (dac_sw.vdd);  decap Cd 0.1 nF + ESR Rd 3 ohm.   Total decap 0.225 nF (Decision 40e, D4 hand-back).
All gate-control PWL sources, the 8 ideal input sources and the comparator loads are referenced to the on-chip ground vssi.
Timing: SCLK 3 MHz (the Decision-40c maximum, the D4 supply case); ADC i does trial t at SCLK edge t+i and its comparator clock rises T0 + i*Delta after that edge (D3 STA: ff_n40 24.8/7.3 ns,
tt 45.9/13.5 ns, ss_125 95.9/28.4 ns), width W; analog corners ff -40 C 3.6 V / typ 27 C 3.3 V / ss 125 C 3.0 V (the D4 pairing).
Method per input case: (1) each ADC ALONE with an IDEAL supply (same stagger index, same timing) -> its code and the level of the tested transition; the input is then moved to the CENTRE of its code
(0.5 LSB from both neighbouring transitions) and the alone run repeated = the reference; (2) the 8-ADC netlist on the modelled supply at the same inputs, closed loop.
Reported per ADC: code vs the reference; dT = shift of the trial-12 transition level (from the measured plate - reference residue just before the comparator clock) [LSB];
max over the 12 trials of the residue change [LSB]; worst decision-instant droop of the DAC strap (0.3 ns before the comparator clock) and of the main rail (within 2 ns after the clock rise);
the D2/D4 formula applied to these MEASURED droops for comparison with the superposition estimate.
usage: x2_s4.py <ff-40|typ|ss125> <fs|mid|alt|all> [SCLK MHz=3] [nodig]     -> sim/x2_s4_<ck>.log (appended), summary lines to sim/x2_s4_summary.log  (X2_LOG_PREFIX=<p> writes sim/<p>_s4_* instead)"""
import sys, os, time, numpy as np
H = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, H)
import x2lib as X, x2_adc as A
NADC = int(os.environ.get('X2_NADC', '8'))          # number of ADC cells (REVIEW R16); 8 = the original S4 run
MODEL = dict(Rp=0.25, Lp=2e-9, Cm=0.125e-9 if NADC == 8 else 74 * 1.593e-12, Cd=0.1e-9 if NADC == 8 else 30 * 1.593e-12, Rs=10.0, Rd=3.0, Cpad=float(os.environ.get('X2_CPAD', '1e-12'))); QDIG = float(os.environ.get('X2_QDIG', '1.5e-12')); KC = 0.038       # Cpad: see x2lib.supply (1 pF per supply pad to the board ground, ASSUMED)
TCS = 20e-9
LOGP = os.environ.get('X2_LOG_PREFIX', 'x2')          # log-file prefix: sim/<prefix>_s4_<corner>.log, <prefix>_s4_summary.log (F1 uses f1_x2 so that the X2 logs stay as they are)
for _k, _e in (('Cm', 'X2_CM'), ('Cd', 'X2_CD'), ('Lp', 'X2_LP'), ('Rd', 'X2_RD'), ('Rs', 'X2_RS'), ('Rp', 'X2_RP')):       # what-if overrides of the ASSUMED supply model (PROPOSAL evidence); logged in every line
    if os.environ.get(_e): MODEL[_k] = float(os.environ[_e])
WHATIF = ' '.join(f'{_k}={os.environ[_e]}' for _k, _e in (('Cm', 'X2_CM'), ('Cd', 'X2_CD'), ('Lp', 'X2_LP'), ('Rd', 'X2_RD'), ('Rs', 'X2_RS'), ('Rp', 'X2_RP')) if os.environ.get(_e))
def dig_line(T, on=True):
    """ESTIMATE (D0b/D4): 1.5 pC per converting ADC per SCLK edge, 1 ns pulse starting 1 ns after the edge, drawn from the main rail"""
    if not on: return None
    pts = [(0.0, 0.0)]
    for e in range(1, 21):
        n = sum(1 for a in range(NADC) if 1 <= e - a <= 12)
        if n == 0: continue
        t = X.sclk_edge(TCS, e, T) + 1e-9; i = n * QDIG / 1e-9
        pts += [(t, 0.0), (t + 0.1e-9, i), (t + 1e-9, i), (t + 1.1e-9, 0.0)]
    return 'Idig vm vssi PWL(' + ' '.join(f'{t:.13e} {v:.6g}' for t, v in pts) + ')'
def builder(ck, vins, adcs, model, T, dig=None, tmax='5n'):
    vdd = X.COR[ck][2]
    def build(lines, meta):
        L = X.header(ck, f'S4 {len(adcs)} ADC cell(s), supply {"MODEL" if model else "ideal"}', amp=False, gmin='1e-12') + X.supply(vdd, model, dig=dig)
        sv = ['v(vm)', 'v(vd)', 'v(vssi)']
        for i in adcs:
            L += [f'Vin{i} vin{i} vssi {vins[i]:.9g}'] + X.adc_cell(i, f'vin{i}'); sv += [f'v(t{i})', f'v(ci{i})', f'v(cq{i})', f'v(cqn{i})']
        return '\n'.join(L + lines + X.tail(sv, meta['tcap'].max() + 3e-9, tmax, tstep='20p')) + '\n'
    return build
def alone(ck, vins, cals, T, tag, log, init=None):
    ex = [X.Exp(f'{tag}{i}', ck, 1, [TCS], T, builder(ck, vins, [i], None, T), [[vins[i]]], cals[i], ref='vssi', adcs=[i]) for i in range(NADC)]
    if init is not None:
        for e, b in zip(ex, init):
            if b is not None: e.bits = [[list(b)]]
    X.closed_loop(ex, log=log, tag=tag); return ex
def targets(case, ck, cals):
    lsb = cals[0].lsb; vdd = X.COR[ck][2]; s = vdd / 3.3          # the amplifier range 1.15-2.15 V of a 3.3 V chip, scaled with VDD (ratiometric)
    if case == 'fs': return [(2.15 - 0.004 * i) * s for i in range(NADC)]
    if case == 'alt': return [(1.15 if i % 2 == 0 else 2.15) * s + 0.0013 * i for i in range(NADC)]
    return [vdd / 2 + (cals[i].c0 - cals[i].theta) / cals[i].alpha + (-0.5 if i % 2 == 0 else 0.5) * lsb for i in range(NADC)]       # mid: around the 2047/2048 (MSB) transition
if __name__ == '__main__':
    ck = sys.argv[1]; cases = ['fs', 'mid', 'alt'] if sys.argv[2] == 'all' else sys.argv[2].split(','); f = float(sys.argv[3]) if len(sys.argv) > 3 else 3.0; dig = not (len(sys.argv) > 4 and sys.argv[4] == 'nodig')
    T = 1e-6 / f; vdd = X.COR[ck][2]; tim = X.TIM[X.COR[ck][3]]; out = []; t00 = time.time(); lsb = vdd / 4096
    def P(s): print(s, flush=True); out.append(s)
    P(f'# X2 S4 {ck} {X.COR[ck]}: {NADC} ADC cells, supply model {MODEL} (pad R/L on VDD AND on VSS), digital charge {"1.5 pC/ADC/edge (ESTIMATE) ON" if dig else "off"}, SCLK {f:g} MHz, T0 {tim["T0"]*1e9:.1f} ns, Delta {tim["DL"]*1e9:.1f} ns, W {tim["W"]*1e9:.1f} ns, DAC edge {tim["arr"]*1e9:.1f} ns after SCLK')
    # ---- calibration of the predictor per stagger index (ADC alone, ideal supply): 3 inputs each
    cal = X.Cal(vdd); cals = [cal] * NADC; v3 = [vdd * 0.35, vdd * 0.5 + 0.0007, vdd * 0.65]          # one predictor for all stagger indices (it only predicts; it learns from every run below)
    ex = [X.Exp(f'c{j}', ck, 1, [TCS], T, builder(ck, {i: v}, [i], None, T), [[v]], cal, ref='vssi', adcs=[i]) for j, (i, v) in enumerate(zip((0, (NADC - 1) // 2, NADC - 1), v3))]
    X.closed_loop(ex, log=P, tag=f's4cal_{ck}')
    ee = [e for e in ex if not e.failed]
    if len(ee) == 3: A.fit_cal(cal, ee, v3)
    P(f'predictor calibration (3 conversions, ADC alone, ideal supply): theta {cal.theta/lsb:+.2f} LSB, alpha {cal.alpha:.4f}, c0 {cal.c0/lsb:+.2f} LSB; failed {sum(1 for e in ex if e.failed)}')
    for case in cases:
        tc0 = time.time(); v0 = targets(case, ck, cals)
        r1 = alone(ck, v0, cals, T, f's4a_{ck}_{case}', P)
        if any(e.failed for e in r1): P(f'S4 {ck} {case}: alone round 1 FAILED: ' + '; '.join(str(e.failed) for e in r1 if e.failed)); continue
        vin = []
        for i, e in enumerate(r1):
            c = int(e.codes()[0, 0]); x12 = e.x[0, 0, 11]; d12 = e.dec[0, 0, 11]; vth = v0[i] + (x12 - cals[i].theta) / cals[i].alpha; p12 = c | 1
            if case == 'mid': vin.append(vth + (2048 - p12) * lsb + (-0.5 if i % 2 == 0 else 0.5) * lsb)
            else: vin.append(vth + (0.5 if d12 else -0.5) * lsb)
        r2 = alone(ck, vin, cals, T, f's4b_{ck}_{case}', P, init=None if case == 'mid' else [e.bits[0][0] for e in r1])     # the centred input keeps the code of round 1
        if any(e.failed for e in r2): P(f'S4 {ck} {case}: alone round 2 FAILED: ' + '; '.join(str(e.failed) for e in r2 if e.failed)); continue
        e8 = X.Exp(f'm_{case}', ck, NADC, [TCS], T, builder(ck, vin, list(range(NADC)), MODEL, T, dig=dig_line(T, dig)), [[v] for v in vin], cals[0], ref='vssi', cals=cals)
        e8.bits = [[list(r2[i].bits[0][0])] for i in range(NADC)]                 # first guess = the codes of the ADCs alone
        X.closed_loop([e8], log=P, tag=f's4m_{ck}_{case}', maxpass=12)
        if e8.failed: P(f'S4 {ck} {case}: {NADC}-ADC run FAILED after {e8.npass} passes: {e8.failed}'); continue
        w = e8.wave; m = e8.meta; vss = w.v('v(vssi)'); dvd = w.v('v(vd)') - vss - vdd; dvm = w.v('v(vm)') - vss - vdd; c8 = e8.codes()[:, 0]; worst = dict(dT=0, dx=0, dvd=0, dvm=0, e5=0, e1=0, dc=0)
        base_d = float(np.interp(TCS - 5e-9, w.t, dvd)); base_m = float(np.interp(TCS - 5e-9, w.t, dvm))
        P(f'S4 {ck} {case}: static rail offset before the conversion (IR drop): DAC strap {base_d*1e3:+.3f} mV, main {base_m*1e3:+.3f} mV; peak excursion during the frame: DAC strap {np.abs(dvd-base_d).max()*1e3:.1f} mV, main {np.abs(dvm-base_m).max()*1e3:.1f} mV, on-chip ground {np.abs(vss).max()*1e3:.1f} mV; {NADC}-ADC passes {e8.npass}, bits corrected {e8.nfix}')
        for i in range(NADC):
            cr = int(r2[i].codes()[0, 0]); xr = r2[i].x[0, 0]; x8 = e8.x[i, 0]; same = list(r2[i].bits[0][0]) == list(e8.bits[i][0]); al = cals[i].alpha
            tr = A.trans_err(cals[i], vin[i], xr[11], cr); t8 = A.trans_err(cals[i], vin[i], x8[11], int(c8[i]))
            dx = (x8 - xr) / al / lsb if same else np.full(12, np.nan)
            dd = np.array([np.interp(m['tck'][i, 0, k] - 0.3e-9, w.t, dvd) - base_d for k in range(12)])
            dm = []
            for k in range(12):
                tk = m['tck'][i, 0, k]; mk = (w.t >= tk) & (w.t <= tk + 2e-9); seg = dvm[mk] - base_m; dm.append(seg[np.argmax(np.abs(seg))] if len(seg) else 0.0)
            dm = np.array(dm); e5 = 0.5 * np.abs(dd) / lsb + KC * np.abs(dm) * 1e3; e1 = np.abs(dd) / lsb + KC * np.abs(dm) * 1e3
            marg = np.abs(x8 - cals[i].theta) / al / lsb
            for k_, v_ in (('dT', abs(t8 - tr)), ('dx', np.nanmax(np.abs(dx)) if same else np.nan), ('dvd', np.abs(dd).max()), ('dvm', np.abs(dm).max()), ('e5', e5.max()), ('e1', e1.max()), ('dc', abs(int(c8[i]) - cr))):
                if not np.isnan(v_): worst[k_] = max(worst[k_], v_)
            P(f'S4 {ck} {case} ADC{i}: Vin {vin[i]:.6f} V | code alone/ideal supply {cr}, in the {NADC}-ADC run {int(c8[i])} (diff {int(c8[i])-cr:+d}) | transition level shift dT {t8-tr:+.3f} LSB | residue change per trial [LSB] ' +
              (' '.join(f'{v:+.2f}' for v in dx) if same else 'n/a (decisions differ)') + f' | smallest |residue - threshold| over the 12 trials {np.nanmin(marg):.2f} LSB | droop at the decision instants: DAC strap worst {dd[np.argmax(np.abs(dd))]*1e3:+.2f} mV (trial {np.argmax(np.abs(dd))+1}), '
              f'main rail worst {dm[np.argmax(np.abs(dm))]*1e3:+.2f} mV (trial {np.argmax(np.abs(dm))+1}) | D2/D4 formula on these droops: {e5.max():.3f} LSB (f = 0.5), {e1.max():.3f} (f = 1) | unresolved decisions {int(e8.unres[i].sum())}')
        ok = worst['dc'] == 0 and worst['dT'] <= 0.5 and (np.isnan(worst['dx']) or worst['dx'] <= 0.5)
        s = (f'RESULT S4 {ck} {case} (SCLK {f:g} MHz, dig {"on" if dig else "off"}{", WHAT-IF supply " + WHATIF if WHATIF else ""}): code changes vs the ADC alone: max {int(worst["dc"])} LSB; max |dT| {worst["dT"]:.3f} LSB; max per-trial residue change {worst["dx"]:.3f} LSB; worst decision-instant droop: DAC strap {worst["dvd"]*1e3:.2f} mV, main rail {worst["dvm"]*1e3:.2f} mV; '
             f'D2/D4 formula on the measured droop {worst["e5"]:.3f} (f=0.5) / {worst["e1"]:.3f} (f=1) LSB vs superposition estimate <= 0.5 | {"PASS" if ok else "FAIL"} (no ADC gains > 0.5 LSB: {ok}); wall {time.time()-tc0:.0f} s')
        P(s); open(f'{X.ADC}/sim/{LOGP}_s4_summary.log', 'a').write(s + '\n')
    open(f'{X.ADC}/sim/{LOGP}_s4_{ck}{"_whatif" if WHATIF else ""}.log', 'a').write('\n'.join(out) + '\n')
    open(f'{X.ADC}/sim/{LOGP}_done.txt', 'a').write(f'{time.strftime("%F %T")} x2_s4 {ck} {",".join(cases)} done, wall {time.time()-t00:.0f} s\n')
