#!/usr/bin/env python3
"""X2 / S1 report: re-reads sim/x2_s1_<corner>.npz (written by x2_s1.py) and evaluates all corners with ONE consistent set of definitions -> sim/x2_s1_report.log
Per conversion (frame 1 and 2 of each run = steady state; frame 0 = first conversion after the DC operating point, reported separately):
  e = code + 0.5 - Vout/LSB                       code centre minus the amplifier output at the sampling instant (the circuit's own decisions; an ideal quantiser with an offset gives a band of +-0.5 LSB)
  U = (Vout + x12/alpha)/LSB - (code | 1)         level of the transition tested at trial 12 minus its ideal value, WITHOUT the comparator threshold (x12 = plate - reference node 0.1 ns before the clock, measured):
                                                  linearity of sampling + DAC up to the comparator input, sub-LSB resolution, independent of the fitted threshold
  T = U - theta/(alpha LSB)                       the same with the fitted comparator threshold theta (one value per corner) = offset of the transition levels
ADC alone = the same ADC cell with an ideal input source (second frame), from the calibration part of x2_s1.py (npz adc_rows) or, for a corner run before that was stored, from sim/x2_adc.log.
usage: x2_s1_report.py [corner ...]"""
import sys, os, re, numpy as np
H = os.path.dirname(os.path.abspath(__file__)); ADC = os.path.abspath(os.path.join(H, '..'))
GNOM = 1000.0; FSIG = 3 * 4000.0 / 512; TFR = 250e-6; AE = 0.45e-3; LSB = 3.3 / 4096
def adc_alone(ck, z):
    if 'adc_rows' in z and len(z['adc_rows']): r = z['adc_rows']; return r[:, 0], r[:, 1], r[:, 4]
    # corner run before adc_rows was stored (typ): the FIRST design block of sim/x2_adc.log for this corner (reference variant cref, no testbench override, 12 inputs)
    blocks = []; cur = None
    for l in open(f'{ADC}/sim/x2_adc.log'):
        if l.startswith('# X2 ADC alone'):
            cur = [] if (f'corner {ck} ' in l and 'reference variant cref' in l and 'OVERRIDE' not in l) else None
            if cur is not None: blocks.append(cur)
            continue
        m = re.match(rf'ADC {re.escape(ck)} cref vin (\S+) code (\d+) ideal \d+ diff \S+ \| T \S+ LSB \| x12 (\S+) LSB \| first', l)
        if m and cur is not None: cur.append((float(m.group(1)), int(m.group(2)), float(m.group(3)) * LSB))
    b = np.array([b for b in blocks if len(b) == 12][0]); return b[:, 0], b[:, 1], b[:, 2]
out = []
def P(s): print(s); out.append(s)
for ck in (sys.argv[1:] or ['typ', 'ff85', 'ss-40']):
    fn = f'{ADC}/sim/x2_s1_{ck}.npz'
    if not os.path.exists(fn): P(f'S1REPORT {ck}: no result file'); continue
    z = np.load(fn, allow_pickle=True); R = z['R']; al = float(z['alpha']); th = float(z['theta'])
    U_ = lambda vo, x12v, code: (vo + x12v / al) / LSB - (code.astype(int) | 1)
    S = R[R[:, 2] > 0]; F0 = R[R[:, 2] == 0]; vo, c, ci = S[:, 4], S[:, 5], S[:, 6]; u = U_(vo, S[:, 8] * LSB, c); e = c + 0.5 - vo / LSB; lo = vo < 2.05; toff = -th / al / LSB
    va, ca, xa = adc_alone(ck, z); ua = U_(va, xa, ca); ea = ca + 0.5 - va / LSB; loa = va < 2.05; o = np.argsort(va)
    du = u - np.interp(vo, va[o], ua[o]); u0 = U_(F0[:, 4], F0[:, 8] * LSB, F0[:, 5])
    P(f'S1REPORT {ck}: {len(S)} steady conversions (frames 1-2 of {len(S)//2} runs: 9 levels + 8 sine points), amplifier output {vo.min():.4f}..{vo.max():.4f} V; passes per run {int(R[:, 11].min())}-{int(R[:, 11].max())}; unresolved comparator decisions {int(R[:, 12].sum())}')
    P(f'S1REPORT {ck}: OFFSET (fixed): code - ideal code mean {np.mean(c-ci):+.2f} (range {int((c-ci).min()):+d}..{int((c-ci).max()):+d}); code centre - input below 2.05 V: {e[lo].mean():+.2f} LSB = {e[lo].mean()*LSB*1e3:+.1f} mV at the ADC input = {e[lo].mean()*LSB/GNOM*1e6:+.1f} uV at the electrode; '
      f'transition-level offset T = U + {toff:.2f} = {u[lo].mean()+toff:+.2f} LSB (fitted comparator threshold theta {th/LSB:+.2f} LSB on the pre-clock residue); ADC alone: {ea[loa].mean():+.2f} LSB (code centre), T {ua[loa].mean()+toff:+.2f}')
    P(f'S1REPORT {ck}: INL beyond the fixed offset, sampling + DAC side (U - mean below 2.05 V): below 2.05 V {(u[lo]-u[lo].mean()).min():+.2f}..{(u[lo]-u[lo].mean()).max():+.2f} LSB; at the top of the range: ' +
      ', '.join(f'{v:.3f} V: {x-u[lo].mean():+.2f}' for v, x in sorted(zip(np.round(vo[~lo], 3), u[~lo]))) + ' LSB | ADC alone: below 2.05 V ' + f'{(ua[loa]-ua[loa].mean()).min():+.2f}..{(ua[loa]-ua[loa].mean()).max():+.2f}; top: ' + ', '.join(f'{v:.3f} V: {x-ua[loa].mean():+.2f}' for v, x in sorted(zip(va[~loa], ua[~loa]))))
    P(f'S1REPORT {ck}: INL beyond the fixed offset from the CODES (e - mean below 2.05 V; +-0.5 is pure quantisation): below 2.05 V {(e[lo]-e[lo].mean()).min():+.2f}..{(e[lo]-e[lo].mean()).max():+.2f} LSB -> excess over quantisation {max(0, np.abs(e[lo]-e[lo].mean()).max()-0.5):.2f} LSB (code-dependent comparator threshold); '
      f'top of the range: ' + ', '.join(f'{v:.3f} V: {x-e[lo].mean():+.2f}' for v, x in sorted(zip(np.round(vo[~lo], 3), e[~lo]))) + f' | ADC alone below 2.05 V: {(ea[loa]-ea[loa].mean()).min():+.2f}..{(ea[loa]-ea[loa].mean()).max():+.2f}')
    P(f'S1REPORT {ck}: AMPLIFIER -> ADC versus the ADC ALONE at the same input (U difference, interpolated): below 2.05 V mean {du[lo].mean():+.3f} LSB ({du[lo].min():+.3f}..{du[lo].max():+.3f}); whole range {du.min():+.3f}..{du.max():+.3f} LSB (D5 settling error of the loaded amplifier <= 0.114 LSB)')
    P(f'S1REPORT {ck}: first conversion after the DC operating point (frame 0, not counted): U higher by {u0[F0[:, 4] < 2.05].mean()-u[lo].mean():+.2f} LSB (spread {np.ptp(u0[F0[:, 4] < 2.05]):.2f})')
    p = np.polyfit(vo[lo] - 1.65, u[lo], 1); P(f'S1REPORT {ck}: ADC gain error below 2.05 V (slope of U): {-p[0]*LSB*100:+.3f} % ({p[0]:+.2f} LSB/V)')
    lv = S[S[:, 0] == 0]; sn = S[S[:, 0] == 1]
    if len(lv) >= 6:
        q = np.polyfit(lv[:, 3], (lv[:, 5] + 0.5) * LSB, 1); qa = np.polyfit(lv[:, 3], lv[:, 4], 1); mk = (lv[:, 4] > 1.3) & (lv[:, 4] < 2.0); qm = np.polyfit(lv[mk, 3], (lv[mk, 5] + 0.5) * LSB, 1); qam = np.polyfit(lv[mk, 3], lv[mk, 4], 1)
        P(f'S1REPORT {ck}: END-TO-END GAIN, DC levels (code vs electrode step, sampled 3-4.5 ms after the step: contains the HPF droop): {q[0]:.1f} V/V = {(q[0]/GNOM-1)*100:+.2f} % vs 1000 (1.3-2.0 V only {(qm[0]/GNOM-1)*100:+.2f} %); amplifier output vs electrode {qa[0]:.1f} V/V = {(qa[0]/GNOM-1)*100:+.2f} % (1.3-2.0 V {(qam[0]/GNOM-1)*100:+.2f} %); amplifier output range reached {lv[:, 4].min():.4f}..{lv[:, 4].max():.4f} V for 1.15..2.15 V asked')
    if len(sn) >= 12:
        ph = sn[:, 1] + 2 * np.pi * FSIG * sn[:, 2] * TFR; M = np.vstack([np.ones_like(ph), np.sin(ph), np.cos(ph)]).T
        for nm, y in (('codes', (sn[:, 5] + 0.5) * LSB), ('amplifier output', sn[:, 4])):
            (a0, a1, a2), *_ = np.linalg.lstsq(M, y, rcond=None); amp = np.hypot(a1, a2); r = y - M @ np.array([a0, a1, a2])
            P(f'S1REPORT {ck}: END-TO-END GAIN, 23.4 Hz sine 450 uV pk ({len(sn)} samples, 3-parameter fit), {nm}: amplitude {amp*1e3:.2f} mV = {amp/AE:.1f} V/V = {(amp/AE/GNOM-1)*100:+.2f} % vs 1000 = {20*np.log10(amp/AE):.3f} dB, phase {np.degrees(np.arctan2(a2, a1)):+.2f} deg, mean {a0:.5f} V, residual rms {np.std(r)/LSB:.2f} LSB (max {np.abs(r).max()/LSB:.2f}: amplifier distortion + start transient' + (' + quantisation' if nm == 'codes' else '') + ')')
    pk = S[S[:, 10] != 0, 10]; pk0 = F0[F0[:, 10] != 0, 10]; pk = np.r_[pk, pk0]
    P(f'S1REPORT {ck}: kick spike on the amplifier output at the resume (sampling TG closes on the floating bottoms): {np.abs(pk).min()*1e3:.0f}..{np.abs(pk).max()*1e3:.0f} mV peak (D5: 0.2-0.36 V)')
    inl_lo = max(np.abs(u[lo] - u[lo].mean()).max(), np.abs(e[lo] - e[lo].mean()).max() - 0.5); inl_all = max(np.abs(u - u[lo].mean()).max(), np.abs(e - e[lo].mean()).max() - 0.5)
    P(f'S1REPORT {ck}: VERDICT |INL| beyond a fixed offset <= 1 LSB: below 2.05 V {inl_lo:.2f} LSB -> {"PASS" if inl_lo <= 1 else "FAIL"}; whole 1.15-2.15 V range {inl_all:.2f} LSB -> {"PASS" if inl_all <= 1 else "FAIL"}; amplifier -> ADC adds {np.abs(du[lo]).max():.2f} LSB (below 2.05 V) to the ADC alone')
    if 'obs' in z and len(z['obs']) > 30:
        ob = z['obs']; x = ob[:, 0] / LSB; s = ob[:, 1] > 0.5; gw = z['gw'] / LSB if 'gw' in z else np.zeros(12); B = ((ob[:, 2].astype(int)[:, None] >> np.arange(12)) & 1)
        bad0 = int(np.sum((x < th / LSB) != s)); bad1 = int(np.sum((x < th / LSB + B @ gw) != s)); lo_ = x[s].max(); hi_ = x[~s].min()
        P(f'S1REPORT {ck}: COMPARATOR THRESHOLD vs DAC STATE ({len(x)} simulated decisions within 8 LSB of the threshold, ADC alone + amplifier runs): a constant threshold misclassifies {bad0}, the fitted per-bit model {bad1}; decisions overlap by {max(0, lo_-hi_):.2f} LSB (highest residue that still gave "keep" minus lowest that gave "reject"); '
          f'fitted threshold shift per bit at 1, b11..b0 [LSB]: ' + ' '.join(f'{v:+.2f}' for v in gw[::-1]) + f' (regularised fit; sum of |shift| {np.abs(gw).sum():.2f} LSB = bound of the code-dependent INL part)')
open(f'{ADC}/sim/x2_s1_report.log', 'w').write('\n'.join(out) + '\n')
