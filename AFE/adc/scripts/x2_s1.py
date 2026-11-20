#!/usr/bin/env python3
"""X2 / S1: SHORT-WINDOW END-TO-END, ONE CHANNEL, transistor level, closed-loop PWL replay.
Netlist = dbs_afe_top.afe_ch without the digital cells: shared-style bias_genc -> afe_chc (A4c amplifier; REF = reference-electrode Randles network on the shared REF node,
park TG off, fs = 0) -> sampling TG + split 6+6 DAC + drivers (dac_sw) -> cmp_p with vhalf (2 x 250 kOhm + 1 pF) and the sampled floating reference Cref 7 pF (vrefs).  Ideal 3.3 V supply.
Start: the DC operating point of this netlist (.tran without uic; electrode at 0 V differential), then the electrode moves:
  level runs : step (20 us edge) at 20 us to (L - 1.65 V)/1000 for 9 output levels L = 1.15 .. 2.15 V
  sine runs  : 450 uV pk, 23.4375 Hz (M = 3 of N = 512 at 4 kS/s); the electrode jumps onto the sine at 20 us such that the phase at the first frame is k x 45 deg (8 points)
3 frames (250 us apart, SCLK 2 MHz, D3 RTL frame timing, STA comparator-clock timing of the paired digital corner) starting TPRE after the start.
Ideal code = floor(amplifier output at the sampling instant / LSB).  T = level of the code transition tested at trial 12 minus its ideal value (sub-LSB, see x2_adc.py).
usage: x2_s1.py <corner key typ|ff85|ss-40> [TPRE_ms=4] [which=all|levels|sine|<name,name>] [tgate]   -> sim/x2_s1_<ck>.log (+ .npz), summary line appended to sim/x2_s1_summary.log"""
import sys, os, time, numpy as np
H = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, H)
import x2lib as X, x2_adc as A
T = 500e-9; TFR = 250e-6; FSIG = 3 * 4000.0 / 512; AE = 0.45e-3; GNOM = 1000.0; TJ = 20e-6; TEDGE = 20e-6
OPTS = os.environ.get('X2_OPTS', ''); TMAX = os.environ.get('X2_TMAX', '1u'); SUF = os.environ.get('X2_SUFFIX', ''); LOGP = os.environ.get('X2_LOG_PREFIX', 'x2')
def src(kind, par, tpre):
    """electrode differential source of channel 0 (two series sources between the tissue node and the Randles network); returns (lines, ve(t) function)"""
    if kind == 'lvl':
        vs = (par - 1.65) / GNOM
        return ['Vsin0 esa0 tis 0', f'Vstp0 es0 esa0 PWL(0 0 {TJ:.6e} 0 {TJ+TEDGE:.6e} {vs:.9e})'], (lambda t: vs * np.ones_like(np.asarray(t, float)))
    ph0 = par - 2 * np.pi * FSIG * tpre; v0 = AE * np.sin(ph0)        # phase at t = 0 so that the phase at the first frame is `par`
    return [f'Vsin0 esa0 tis SIN(0 {AE:.9e} {FSIG:.9g} 0 0 {np.degrees(ph0):.9f})', f'Vstp0 es0 esa0 PWL(0 {-v0:.9e} {TJ:.6e} {-v0:.9e} {TJ+TEDGE:.6e} 0)'], (lambda t: AE * np.sin(2 * np.pi * FSIG * np.asarray(t, float) + ph0))
def builder(ck, slines, tgate=False):
    vdd = X.COR[ck][2]
    def build(lines, meta):
        L = X.header(ck, 'S1 amplifier -> ADC, one channel', amp=True, gmin='1e-16', opts=OPTS)
        if tgate: L.append(f'.include {os.path.abspath(X.AFE + "/../TGATE/TGATE.spice")}')
        L += X.supply(vdd) + X.ref_electrode() + X.bias() + X.amp_channel(0, slines, tgate=tgate) + X.adc_cell(0, 'out0') + lines
        L += X.tail(['v(out0)', 'v(t0)', 'v(ci0)', 'v(cq0)', 'v(cqn0)'], meta['tcap'].max() + 3e-9, TMAX, tstep='1n')
        return '\n'.join(L) + '\n'
    return build
if __name__ == '__main__':
    ck = sys.argv[1]; tpre = float(sys.argv[2]) * 1e-3 if len(sys.argv) > 2 else 4e-3; which = sys.argv[3] if len(sys.argv) > 3 else 'all'; tgate = len(sys.argv) > 4 and sys.argv[4] == 'tgate'
    vdd = X.COR[ck][2]; out = []; t00 = time.time()
    def P(s): print(s, flush=True); out.append(s)
    P(f'# X2 S1 {ck} {X.COR[ck]}: amplifier (A4c) -> TG -> split 6+6 DAC -> cmp_p + Cref 7 pF + vhalf, real bias_genc, ideal 3.3 V supply, closed-loop replay; TPRE {tpre*1e3:g} ms, SCLK 2 MHz, tmax {TMAX}, options "{OPTS}", routing TGATE {"IN (closed)" if tgate else "not in the netlist"}')
    # ---- 1. ADC alone: calibrates the predictor and gives the reference transfer (same cell, ideal source)
    n0 = int(os.environ.get('X2_NCAL', '24')); vcal = list(1.15 + (np.arange(n0) + 0.37) / n0 + 0.000217 * np.sin(np.arange(n0) * 1.7))
    cal, rows, _ = A.static(ck, vcal, log=P, tag=f's1cal_{ck}', nfr=2)
    for r, r0 in zip(rows, A.static.rows0): P(f'ADC ALONE {ck} vin {r[0]:.6f} code {r[1]} ideal {r[2]} diff {r[1]-r[2]:+d} | T {r[3]:+.3f} LSB | x12 {r[4]/cal.lsb:+.2f} LSB | first conversion from the DC op: code {r0[1]}, T {r0[3]:+.3f} | passes {r[5]}')
    adc_v = np.array([r[0] for r in rows]); adc_t = np.array([r[3] for r in rows]); adc_e = np.array([r[1] + 0.5 - r[0] / cal.lsb for r in rows])
    adc = A.summarize(cal, rows, f'ADC ALONE (ideal source) {ck}', P)
    # ---- 2. amplifier -> ADC
    tcs = [tpre + k * TFR for k in range(3)]; todo = []
    lv = [('lvl', L) for L in np.linspace(1.15, 2.15, 9)]; sn = [('sin', k * np.pi / 4) for k in range(8)]
    plan = (lv if which in ('all', 'levels') else []) + (sn if which in ('all', 'sine') else [])
    # first-pass prediction of the amplifier output at the sampling instants: the same source into the amplifier ALONE (20 fF load, no ADC), a cheap run
    pj = []
    for kind, par in plan:
        sl, ve = src(kind, par, tpre)
        L = X.header(ck, 'S1 amplifier alone (prediction)', amp=True, gmin='1e-16', opts=OPTS) + X.supply(vdd) + X.ref_electrode() + X.bias() + X.amp_channel(0, sl) + ['Cl out0 vssi 20f'] + X.tail(['v(out0)'], tcs[-1] + 1e-6, '2u', tstep='1u')
        pj.append((f'p{kind}{par:.3f}'.replace('.', 'p'), '\n'.join(L) + '\n'))
    pr = X.run_jobs(pj, tag=f's1p_{ck}'); P(f'   amplifier-alone prediction runs: {len(pj)} runs, {sum(1 for r in pr.values() if r["ok"])} ok, wall each {np.mean([r["wall"] for r in pr.values()]):.0f} s')
    for (kind, par), (pn, _) in zip(plan, pj):
        name = f'{kind}{par:.3f}'.replace('.', 'p'); sl, ve = src(kind, par, tpre)
        g = [1.65 + GNOM * 0.995 * float(ve(t)) for t in tcs]
        if pr[pn]['ok']:
            wp = X.Wave(pr[pn]['raw'])
            if wp.tend >= tcs[-1]: g = [float(wp.at('v(out0)', t)) for t in tcs]
        e = X.Exp(name, ck, 1, tcs, T, builder(ck, sl, tgate), [g], cal, resume_last=False)
        e.kind, e.par, e.ve, e.vpred = kind, par, ve, g; todo.append(e)
    X.closed_loop(todo, log=P, tag=f's1_{ck}')
    R = []
    for e in todo:
        if e.failed: P(f'S1 {ck} {e.name}: FAILED after {e.npass} passes: {e.failed}'); continue
        w = e.wave; m = e.meta; codes = e.codes()[0]
        for f, tc in enumerate(tcs):
            vo = float(w.at('v(out0)', tc)); c = int(codes[f]); ci = int(np.floor(vo / cal.lsb)); x12 = e.x[0, f, 11]; tt = A.trans_err(cal, vo, x12, c); ve = float(e.ve(tc))
            slope = float((w.at('v(out0)', tc) - w.at('v(out0)', tc - 20e-6)) / 20e-6)
            pk = 0.0
            if f < 2:
                tr = m['tres'][0, f]; mk = (w.t > tr - 1e-9) & (w.t < tr + 2e-6); vv = w.v('v(out0)')[mk]; pk = float(vv[np.argmax(np.abs(vv - vv[0]))] - vv[0])
            R.append((e.kind == 'sin', e.par, f, ve, vo, c, ci, tt, x12 / cal.lsb, slope, pk, e.npass, int(e.unres.sum())))
            P(f'S1 {ck} {e.name} frame {f}: electrode {ve*1e6:+8.2f} uV | amp out at the sampling instant {vo:.6f} V (slope {slope:+7.2f} V/s) | code {c} ideal {ci} diff {c-ci:+d} | T {tt:+.3f} LSB | x12 {x12/cal.lsb:+.2f} LSB | '
              f'kick spike on the amp output at the resume {pk*1e3:+.1f} mV | passes {e.npass}')
    R = np.array(R, float)
    if len(R) >= 6:
        Rall = R; f0 = R[R[:, 2] == 0]; R = R[R[:, 2] > 0]                         # frames 1, 2 = steady state; frame 0 = first conversion after the DC operating point
        vo, c, ci, tt = R[:, 4], R[:, 5], R[:, 6], R[:, 7]; ec = c + 0.5 - vo / cal.lsb; lo = vo < 2.05
        p = np.polyfit(vo[lo] - vdd / 2, tt[lo], 1); res = tt - np.polyval(p, vo - vdd / 2)
        tadc = np.interp(vo, adc_v, adc_t); dta = tt - tadc
        P(f'RESULT S1 {ck}: {len(R)} conversions (frames 1 and 2 of each run), amp out {vo.min():.4f}..{vo.max():.4f} V | code - ideal code: mean {np.mean(c-ci):+.2f} LSB, range {int((c-ci).min()):+d}..{int((c-ci).max()):+d} | OFFSET: code centre minus input {ec[lo].mean():+.2f} LSB (below 2.05 V) = {ec[lo].mean()*cal.lsb*1e3:+.2f} mV at the ADC input = {ec[lo].mean()*cal.lsb*1e6/GNOM:+.1f} uV at the electrode; transition-level offset T {tt[lo].mean():+.2f} LSB')
        P(f'RESULT S1 {ck}: first conversion after the DC operating point (frame 0): T {f0[:, 7].mean():+.2f} LSB vs {tt[lo].mean():+.2f} in frames 1-2 (difference {f0[f0[:, 4] < 2.05, 7].mean()-tt[lo].mean():+.2f} LSB, spread {np.ptp(f0[f0[:, 4] < 2.05, 7]):.2f}): start state of the simulation (comparator tail node / reference capacitor before any conversion), not counted as INL')
        P(f'RESULT S1 {ck}: ADC gain error below 2.05 V (T slope) {-p[0]*cal.lsb*100:+.3f} % ({p[0]:+.2f} LSB/V) | INL beyond a FIXED OFFSET, DAC/sampling side (T - mean T below 2.05 V): below 2.05 V max {np.abs(tt[lo]-tt[lo].mean()).max():.2f} LSB; top of the range: ' + ', '.join(f'{v:.3f} V {x-tt[lo].mean():+.2f}' for v, x in sorted(zip(vo[~lo], tt[~lo]))) + ' LSB')
        P(f'RESULT S1 {ck}: INL beyond a fixed offset from the CODES (code + 0.5 - Vin/LSB - mean; an ideal quantiser gives +-0.5): below 2.05 V {(ec[lo]-ec[lo].mean()).min():+.2f}..{(ec[lo]-ec[lo].mean()).max():+.2f} LSB; top of the range: ' + ', '.join(f'{v:.3f} V {x-ec[lo].mean():+.2f}' for v, x in sorted(zip(vo[~lo], ec[~lo]))) + f' LSB; whole range max|e - mean| {np.abs(ec-ec[lo].mean()).max():.2f} LSB')
        P(f'RESULT S1 {ck}: versus the SAME ADC ALONE (ideal source, second frame, interpolated to the same input): T(amp->ADC) - T(ADC alone): mean {np.mean(dta):+.3f} LSB, min {np.min(dta):+.3f}, max {np.max(dta):+.3f} LSB; below 2.05 V: {np.mean(dta[lo]):+.3f} ({np.min(dta[lo]):+.3f}..{np.max(dta[lo]):+.3f}) (D5 item 1 loaded-minus-unloaded settling error: <= 0.114 LSB)')
        lv_ = R[R[:, 0] == 0]; sn_ = R[R[:, 0] == 1]
        if len(lv_) >= 6:
            q = np.polyfit(lv_[:, 3], lv_[:, 5] + 0.5, 1); qa = np.polyfit(lv_[:, 3], lv_[:, 4], 1); mk = (lv_[:, 4] > 1.3) & (lv_[:, 4] < 2.0); qm = np.polyfit(lv_[mk, 3], lv_[mk, 5] + 0.5, 1)
            P(f'RESULT S1 {ck}: END-TO-END GAIN, DC levels ({tpre*1e3:g} ms after the electrode step, so it contains the HPF droop): code vs electrode {q[0]*cal.lsb:.2f} V/V = {(q[0]*cal.lsb/GNOM-1)*100:+.2f} % vs 1000 (1.3-2.0 V only: {(qm[0]*cal.lsb/GNOM-1)*100:+.2f} %); amplifier alone (output vs electrode) {qa[0]:.2f} V/V = {(qa[0]/GNOM-1)*100:+.2f} %')
        if len(sn_) >= 12:
            ph = sn_[:, 1] + 2 * np.pi * FSIG * sn_[:, 2] * TFR; M = np.vstack([np.ones_like(ph), np.sin(ph), np.cos(ph)]).T
            for nm, y in (('code', (sn_[:, 5] + 0.5) * cal.lsb), ('amplifier output', sn_[:, 4])):
                (a0, a1, a2), *_ = np.linalg.lstsq(M, y, rcond=None); amp = np.hypot(a1, a2); r = y - M @ np.array([a0, a1, a2])
                P(f'RESULT S1 {ck}: END-TO-END GAIN, 23.4 Hz sine (8 phases x 3 frames, 3-parameter fit): {nm}: amplitude {amp*1e3:.3f} mV for {AE*1e6:.0f} uV pk = {amp/AE:.2f} V/V = {(amp/AE/GNOM-1)*100:+.2f} % vs 1000 ({20*np.log10(amp/AE):.3f} dB), phase {np.degrees(np.arctan2(a2, a1)):+.2f} deg, mean {a0:.5f} V, fit residual rms {np.std(r)/cal.lsb:.2f} LSB (max {np.abs(r).max()/cal.lsb:.2f}; includes the amplifier distortion and the start transient)')
        pk = R[R[:, 10] != 0, 10]
        if len(pk): P(f'RESULT S1 {ck}: kick spike on the amplifier output at the resume (TG closes on the floating bottoms): {np.abs(pk).min()*1e3:.0f}..{np.abs(pk).max()*1e3:.0f} mV peak (D5: 0.2-0.36 V)')
        inl = max(np.abs(tt - tt[lo].mean()).max(), np.abs(ec - ec[lo].mean()).max() - 0.5); inl_lo = max(np.abs(tt[lo] - tt[lo].mean()).max(), np.abs(ec[lo] - ec[lo].mean()).max() - 0.5); dd = np.abs(dta).max(); R = Rall
        P(f'VERDICT S1 {ck}: |INL| beyond a fixed offset: whole range 1.15-2.15 V {inl:.2f} LSB -> {"PASS" if inl <= 1.0 else "FAIL"}; below 2.05 V {inl_lo:.2f} LSB -> {"PASS" if inl_lo <= 1.0 else "FAIL"} (limit 1 LSB; larger of the T-based and the code-based value less 0.5 LSB quantisation); amp->ADC vs ADC alone within {dd:.2f} LSB; passes per run {int(R[:,11].min())}..{int(R[:,11].max())}; unresolved comparator decisions {int(R[:,12].sum())}; wall {time.time()-t00:.0f} s')
        P(f'PREDICTOR {ck} (decision threshold on the pre-clock residue vs the DAC state; all ADC-alone and amp->ADC decisions): {cal.fitinfo}')
        np.savez(f'{X.ADC}/sim/x2_s1_{ck}{"_tgate" if tgate else ""}{SUF}.npz', R=R, theta=cal.theta, alpha=cal.alpha, c0=cal.c0, gw=cal.gw, obs=np.array(cal.obs, float), adc_rows=np.array(rows, float), adc_rows0=np.array(A.static.rows0, float), adc_mid=adc['mid'], adc_slope=adc['slope'],
                 cols='is_sine par frame electrode_V ampout_V code ideal T_LSB x12_LSB slope_V_per_s kick_V passes unresolved')
        if not SUF: open(f'{X.ADC}/sim/x2_s1_summary.log', 'a').write('\n'.join(l for l in out if l.startswith(('RESULT', 'VERDICT', 'ADC ALONE (', 'PREDICTOR'))) + '\n')
    open(f'{X.ADC}/sim/x2_s1_{ck}{"_tgate" if tgate else ""}{"" if which == "all" else "_" + which.replace(",", "_")}{SUF}.log', 'w').write('\n'.join(out) + '\n')
    open(f'{X.ADC}/sim/{LOGP}_done.txt', 'a').write(f'{time.strftime("%F %T")} x2_s1 {ck} {which} done, wall {time.time()-t00:.0f} s\n')
