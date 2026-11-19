#!/usr/bin/env python3
"""X2: ONE ADC analog cell alone (ideal input source, ideal supply), closed-loop PWL replay (x2lib).  Used (a) to calibrate the bit predictor per corner,
(b) as the transistor-level static transfer of the ADC (code, offset, gain, INL), (c) as the 'same ADC alone, ideal supply' reference of S4.
usage: x2_adc.py <corner key: typ|ff85|ss-40|ff-40|ss125> <npts | v1,v2,...> [ref=cref|tied|ideal] [T_ns=500]   -> prints per-point lines and a summary; appends to sim/x2_adc.log
Metrics per conversion (x_k = plate - reference node 0.1 ns before the comparator clock of trial k, measured):
  code            = the circuit's own 12 decisions (closed loop)
  T [LSB]         = level of the code transition tested at trial 12 minus its ideal value: T = (Vin + (x_12 - theta)/alpha)/LSB - (code | 1); mean T = fixed offset, T - mean = INL of that transition (sub-LSB resolution)
  theta, alpha    = comparator decision threshold on x and the plate attenuation, both fitted from the runs (theta: keep <=> x < theta)."""
import sys, os, time, numpy as np
H = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, H)
import x2lib as X
def builder(ck, vin, ref='cref', tmax='1u', supply=None, extra=(), gmin='1e-16'):
    vdd = X.COR[ck][2]
    def build(lines, meta):
        L = X.header(ck, f'ADC alone, ref={ref}', amp=False, gmin=gmin) + X.supply(vdd, supply) + [f'Vin0 vin0 vssi {vin:.9g}'] + X.adc_cell(0, 'vin0', ref=ref) + list(extra) + lines
        L += X.tail(['v(t0)', 'v(ci0)', 'v(cq0)', 'v(cqn0)'], meta['tcap'].max() + 3e-9, tmax, tstep='20p')
        return '\n'.join(L) + '\n'
    return build
def fit_cal(cal, exps, vins):
    """alpha, c0 from the MSB trial (x_1 = c0 + alpha (VDD/2 - Vin)); theta is maintained by Cal.observe"""
    x1 = np.array([e.x[0, 0, 0] for e in exps]); v = np.array(vins); A = np.vstack([np.ones_like(v), cal.vdd / 2 - v]).T
    (c0, al), *_ = np.linalg.lstsq(A, x1, rcond=None); cal.c0, cal.alpha = float(c0), float(al)
    return cal
def trans_err(cal, vin, x12, code): return (vin + (x12 - cal.theta) / cal.alpha) / cal.lsb - (code | 1)
def static(ck, vins, ref='cref', T=500e-9, log=print, cal=None, tag='adc', nfr=2, tfr=250e-6):
    """nfr frames per input (4 kS/s); the LAST frame is the result (rows), the first one (the conversion that starts from the DC operating point, where the comparator's floating tail node and the
    reference capacitor have not yet seen a conversion) is returned separately: rows0.  nfr = 1: single conversion from the DC operating point."""
    vdd = X.COR[ck][2]; cal = cal or X.Cal(vdd); tcs = [20e-9 + k * tfr for k in range(nfr)]
    extra = [l for l in os.environ.get('X2_EXTRA', '').split(';') if l.strip()]           # testbench-only .param overrides (what-if runs for PROPOSALS), e.g. X2_EXTRA='.param DSW_WN=4u DSW_WP=8u'
    exps = [X.Exp(f'{tag}{i}', ck, 1, tcs, T, builder(ck, v, ref, extra=extra), [[v] * nfr], cal, resume_last=False) for i, v in enumerate(vins)]
    X.closed_loop(exps, log=log, tag=tag)
    ok = [(e, v) for e, v in zip(exps, vins) if not e.failed]
    for e, v in zip(exps, vins):
        if e.failed: log(f'ADC {ck} {ref} vin {v:.6f}: FAILED {e.failed}')
    if len(ok) >= 3:
        x1 = np.array([e.x[0, nfr - 1, 0] for e, _ in ok]); v = np.array([v for _, v in ok]); Am = np.vstack([np.ones_like(v), cal.vdd / 2 - v]).T
        (c0, al), *_ = np.linalg.lstsq(Am, x1, rcond=None); cal.c0, cal.alpha = float(c0), float(al)
    rows = []; rows0 = []
    for e, v in ok:
        for f, dst in ((nfr - 1, rows), (0, rows0)):
            c = int(e.codes()[0, f]); x12 = e.x[0, f, 11]; t = trans_err(cal, v, x12, c)
            dst.append((v, c, int(np.floor(v / cal.lsb)), t, x12, e.npass, int(e.unres.sum())))
    static.rows0 = rows0
    return cal, rows, exps
def summarize(cal, rows, label, log=print):
    a = np.array([(r[0], r[1], r[2], r[3]) for r in rows]); v, c, ci, t = a.T; lo = v < 2.05 * cal.vdd / 3.3
    ec = c + 0.5 - v / cal.lsb                                     # code centre minus input [LSB]
    p = np.polyfit(v - cal.vdd / 2, t, 1); res = t - np.polyval(p, v - cal.vdd / 2)
    pc = np.polyfit(v - cal.vdd / 2, ec, 1)
    s = (f'{label}: {len(rows)} conversions | theta {cal.theta/cal.lsb:+.2f} LSB (keep <=> plate-ref < theta; decision overlap {max(0.0,(cal.lo-cal.hi))/cal.lsb:.2f} LSB), alpha {cal.alpha:.4f}, c0 {cal.c0/cal.lsb:+.2f} LSB | '
         f'code - ideal code: mean {np.mean(c-ci):+.2f}, range {int((c-ci).min()):+d}..{int((c-ci).max()):+d} | transition offset T: mean {t.mean():+.2f} LSB, at mid-scale {p[1]:+.2f}, slope {p[0]:+.2f} LSB/V = gain error {-p[0]*cal.lsb*100:+.3f} % | '
         f'DAC-side INL beyond a fixed offset (T, constant comparator threshold assumed): max|T - mean| {np.abs(t-t.mean()).max():.2f} LSB over the whole range, {np.abs(t[lo]-t[lo].mean()).max() if lo.any() else float("nan"):.2f} LSB below 2.05 V; beyond offset+gain: {np.abs(res).max():.2f} LSB | '
         f'CODE-based (the circuit decisions; contains +-0.5 LSB quantisation): code + 0.5 - Vin/LSB = {ec.mean():+.2f} mean, {ec.min():+.2f}..{ec.max():+.2f}; max|e - mean| {np.abs(ec-ec.mean()).max():.2f} LSB (below 2.05 V: {np.abs(ec[lo]-ec[lo].mean()).max() if lo.any() else float("nan"):.2f})')
    log(s); return dict(off=t.mean(), mid=p[1], slope=p[0], inl=np.abs(t - t.mean()).max(), inl_g=np.abs(res).max(), codeoff=np.mean(c - ci))
if __name__ == '__main__':
    ck = sys.argv[1]; spec = sys.argv[2]; ref = sys.argv[3] if len(sys.argv) > 3 else 'cref'; T = float(sys.argv[4]) * 1e-9 if len(sys.argv) > 4 else 500e-9
    if ',' in spec or '.' in spec: vins = [float(x) for x in spec.split(',')]
    else:
        n = int(spec); vins = list(1.15 + (np.arange(n) + 0.37) / n * 1.0 + 0.000217 * np.sin(np.arange(n) * 1.7))     # spread over 1.15-2.15 V with irregular sub-LSB positions
    out = []; P = lambda s: (print(s, flush=True), out.append(s))
    t0 = time.time(); P(f'# X2 ADC alone, closed-loop replay: corner {ck} {X.COR[ck]}, reference variant {ref}, SCLK {1e3/(T*1e9):.3g} MHz, timing {X.TIM[X.COR[ck][3]]}' + (f', TESTBENCH OVERRIDE (not the design): {os.environ["X2_EXTRA"]}' if os.environ.get('X2_EXTRA') else '') + (f', TESTBENCH TIMING OVERRIDE (not the design): lower bits of trial 1 switched {X.NOV1*1e9:g} ns after the MSB' if os.environ.get('X2_NOV1') else ''))
    nfr = int(os.environ.get('X2_NFR', '2'))
    cal, rows, exps = static(ck, vins, ref, T, log=P, nfr=nfr)
    for r, r0 in zip(rows, static.rows0): P(f'ADC {ck} {ref} vin {r[0]:.6f} code {r[1]} ideal {r[2]} diff {r[1]-r[2]:+d} | T {r[3]:+.3f} LSB | x12 {r[4]/cal.lsb:+.2f} LSB | first conversion from the DC op: code {r0[1]}, T {r0[3]:+.3f} | passes {r[5]} unresolved decisions {r[6]}')
    summarize(cal, rows, f'SUMMARY ADC alone {ck} ref={ref} (frame {nfr} of {nfr})', P); P(f'PREDICTOR {ck} ref={ref}: {cal.fitinfo}'); P(f'# wall {time.time()-t0:.0f} s')
    open(f'{X.ADC}/sim/x2_adc.log', 'a').write('\n'.join(out) + '\n')
