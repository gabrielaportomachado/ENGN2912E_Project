#!/usr/bin/env python3
"""X2 / S3: LONG RUN, one channel, transistor level, closed-loop PWL replay: coherent sine, N samples at 4 kS/s.
Same netlist as S1 (bias_genc -> afe_chc A4c -> sampling TG + split DAC + drivers -> cmp_p + Cref + vhalf; ideal 3.3 V supply; numerical set of X2 S2: abstol 1e-12).
Start from the DC operating point; the electrode sine starts at its zero crossing at t = 0 (no step: the HPF start transient is A*gain*f_lo/f, < 2 mV, decaying over seconds; the LPF transient is gone after TPRE).
N frames from TPRE, SCLK 2 MHz.  First-pass bits: from an amplifier-only run of the same source (unloaded output at the sampling instants) + the ADC-alone calibration.
SNDR (coherent, bin M, no window): codes of the circuit; the amplifier output at the sampling instants (unquantised); that output through an ideal 12-bit quantiser.  ENOB raw = (SNDR - 1.76)/6.02 for this signal,
ENOB FS = raw + log2(1.65 V / amplitude).  Amplifier noise is NOT in a transient run: it is added analytically (D5 item 3 / A4c NOISE_D output noise 1.83 / 2.06 / 1.64 mV rms, white) as a separate line.
usage: x2_s3.py <typ|ff85|ss-40> [N=64] [M=1] [TPRE_ms=5] [amp_V_out_pk=0.45]   -> sim/x2_s3_<ck>_N<N>.log + .npz, summary to sim/x2_s3_summary.log"""
import sys, os, time, numpy as np
H = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, H)
import x2lib as X, x2_adc as A, x2_s1 as S1
T = 500e-9; TFR = 250e-6; GNOM = 1000.0
VN = {'typ': 1.83e-3, 'ff85': 2.06e-3, 'ss-40': 1.64e-3}                                  # amplifier output noise rms (ESTIMATE, D5 / A4c NOISE_D)
HYB = {'typ': (60.1, 44.7), 'ff85': (31.9, 31.7), 'ss-40': (59.9, 45.6)}                   # D5 hybrid SNDR [dB]: without / with the amplifier noise estimate (0.45 V pk)
def sndr(y, M):
    N = len(y); Y = np.fft.rfft(y - np.mean(y)) / N * 2; p = np.abs(Y) ** 2 / 2; ps = p[M]; pn = p[1:].sum() - ps
    hd = [10 * np.log10(p[(k * M) % N if (k * M) % N <= N // 2 else N - (k * M) % N] / ps) for k in (2, 3)]
    return 10 * np.log10(ps / pn), np.abs(Y[M]), hd
if __name__ == '__main__':
    ck = sys.argv[1]; N = int(sys.argv[2]) if len(sys.argv) > 2 else 64; M = int(sys.argv[3]) if len(sys.argv) > 3 else 1
    tpre = float(sys.argv[4]) * 1e-3 if len(sys.argv) > 4 else 5e-3; apk = float(sys.argv[5]) if len(sys.argv) > 5 else 0.45
    vdd = X.COR[ck][2]; f = M * 4000.0 / N; ae = apk / GNOM; out = []; t00 = time.time(); lsb = vdd / 4096
    def P(s): print(s, flush=True); out.append(s)
    P(f'# X2 S3 {ck} {X.COR[ck]}: coherent sine {f:.4f} Hz (M = {M} of N = {N} at 4 kS/s), {ae*1e6:.0f} uV pk at the electrode, TPRE {tpre*1e3:g} ms, SCLK 2 MHz, tmax {S1.TMAX}, options abstol 1e-12 gmin 1e-16 {S1.OPTS}')
    # ---- predictor calibration: from the S1 run of this corner if present, else a short ADC-alone run
    cal = X.Cal(vdd); npz = f'{X.ADC}/sim/x2_s1_{ck}.npz'
    if os.path.exists(npz):
        z = np.load(npz); cal.theta, cal.alpha, cal.c0 = float(z['theta']), float(z['alpha']), float(z['c0']); cal.gw = z['gw'] if 'gw' in z else cal.gw; cal.obs = [tuple(r) for r in z['obs']] if 'obs' in z else []; P(f'predictor calibration from {os.path.basename(npz)}: theta {cal.theta/lsb:+.2f} LSB, alpha {cal.alpha:.4f}, c0 {cal.c0/lsb:+.2f} LSB')
    else:
        n0 = 9; vc = list(1.15 + (np.arange(n0) + 0.37) / n0); cal, rows, _ = A.static(ck, vc, log=P, tag=f's3cal_{ck}'); A.summarize(cal, rows, f'ADC ALONE {ck}', P)
    prev = f'{X.ADC}/sim/x2_s3_{ck}_N64.npz'
    if os.path.exists(prev) and N != 64:          # a longer record starts from the predictor learned in the 64-sample run of this corner
        z3 = np.load(prev); cal.theta = float(z3['theta']); cal.gw = z3['gw']; cal.obs = [tuple(r) for r in z3['obs']]; P(f'predictor (bit-dependent threshold) from {os.path.basename(prev)}: {len(cal.obs)} decisions')
    cal.lo, cal.hi = cal.theta - 0.05 * lsb, cal.theta + 0.05 * lsb
    tcs = [tpre + k * TFR for k in range(N + 1)]; sl = [f'Vsin0 esa0 tis SIN(0 {ae:.9e} {f:.9g} 0 0 0)', 'Vstp0 es0 esa0 0']
    # ---- amplifier-only run: unloaded output at the sampling instants (first-pass prediction; also the reference for the loading effect)
    L = X.header(ck, 'S3 amplifier alone (first-pass prediction)', amp=True, gmin='1e-16') + X.supply(vdd) + X.ref_electrode() + X.bias() + X.amp_channel(0, sl) + ['Cl out0 vssi 20f'] + X.tail(['v(out0)'], tcs[-1] + 1e-6, '2u', tstep='1u')
    r = X.run_jobs([('amp', '\n'.join(L) + '\n')], tag=f's3amp_{ck}')['amp']
    if not r['ok']: P(f'S3 {ck}: amplifier-only run FAILED {r["tail"]}'); sys.exit(1)
    wa = X.Wave(r['raw']); vu = wa.at('v(out0)', np.array(tcs)); P(f'amplifier alone: output at the {N + 1} sampling instants {vu.min():.4f}..{vu.max():.4f} V, wall {r["wall"]:.0f} s')
    e = X.Exp(f's3_{ck}', ck, 1, tcs, T, S1.builder(ck, sl), [list(vu)], cal, resume_last=False)
    X.closed_loop([e], log=P, tag=f's3_{ck}', maxpass=14, wall=5400.0)
    if e.failed:
        P(f'RESULT S3 {ck} N={N}: FAILED after {e.npass} passes: {e.failed}')
    else:
        w = e.wave; codes = e.codes()[0].astype(float)[1:]; vo = w.at('v(out0)', np.array(tcs))[1:]; vu = vu[1:]; ci = np.floor(vo / lsb); tt = np.array([A.trans_err(cal, vo[k], e.x[0, k + 1, 11], int(codes[k])) for k in range(N)])
        P(f'PREDICTOR {ck}: {cal.fitinfo}')
        s_c, a_c, hd_c = sndr((codes + 0.5) * lsb, M); s_a, a_a, hd_a = sndr(vo, M); s_q, a_q, hd_q = sndr((ci + 0.5) * lsb, M); s_u, a_u, _ = sndr(vu, M)
        fs = np.log2(vdd / 2 / a_c); en = lambda s: (s - 1.76) / 6.02
        P(f'RESULT S3 {ck} N={N} M={M} ({f:.2f} Hz): {e.npass} passes, {e.nfix} bit corrections, {len(w.t)} time points, run completed to {w.tend*1e3:.3f} ms; unresolved comparator decisions {int(e.unres.sum())}')
        P(f'RESULT S3 {ck}: amplitude at the ADC input {a_a*1e3:.2f} mV pk (gain {a_a/ae:.1f} V/V), codes span {int(codes.min())}..{int(codes.max())}; code - ideal code: mean {np.mean(codes-ci):+.2f}, min {int((codes-ci).min()):+d}, max {int((codes-ci).max()):+d}; transition offset T mean {tt.mean():+.2f} LSB, max|T - mean| {np.abs(tt-tt.mean()).max():.2f} LSB; loaded - unloaded amplifier output at the sampling instants: mean {np.mean(vo-vu)/lsb:+.3f} LSB, max |.| {np.abs(vo-vu).max()/lsb:.3f} LSB')
        P(f'RESULT S3 {ck}: SNDR transistor-level codes {s_c:.2f} dB -> ENOB raw {en(s_c):.2f}, FS {en(s_c)+fs:.2f} bit (HD2 {hd_c[0]:.1f} dBc, HD3 {hd_c[1]:.1f} dBc) | amplifier output alone (unquantised) {s_a:.2f} dB (HD2 {hd_a[0]:.1f}, HD3 {hd_a[1]:.1f} dBc) | amplifier output through an IDEAL 12-bit quantiser {s_q:.2f} dB -> ENOB raw {en(s_q):.2f}, FS {en(s_q)+fs:.2f}')
        vn = VN[ck]; pn = lambda s, a: -10 * np.log10(10 ** (-s / 10) + vn ** 2 / (a ** 2 / 2))
        P(f'RESULT S3 {ck}: with the amplifier noise ESTIMATE added analytically ({vn*1e3:.2f} mV rms at the output): SNDR {pn(s_c, a_c):.2f} dB -> ENOB raw {en(pn(s_c, a_c)):.2f}, FS {en(pn(s_c, a_c))+fs:.2f} bit')
        h0, h1 = HYB[ck]; fs45 = np.log2(1.65 / 0.45)
        P(f'RESULT S3 {ck}: D5 HYBRID (0.45 V pk, 23.4 Hz, N 512): {h0:.1f} dB = ENOB FS {en(h0)+fs45:.2f} without amplifier noise, {h1:.1f} dB = ENOB FS {en(h1)+fs45:.2f} with it; transistor-level minus hybrid: {s_c-h0:+.1f} dB noise-free, {pn(s_c, a_c)-h1:+.1f} dB with the noise estimate (N = {N} here: about +-1.5 dB statistical for a 64-point record)')
        np.savez(f'{X.ADC}/sim/x2_s3_{ck}_N{N}.npz', codes=codes, vo=vo, vu=vu, ideal=ci, T=tt, x=e.x[0][1:], tcs=np.array(tcs)[1:], f=f, M=M, N=N, ae=ae, obs=np.array(cal.obs, float), gw=cal.gw, theta=cal.theta)
    P(f'# wall {time.time()-t00:.0f} s')
    open(f'{X.ADC}/sim/x2_s3_{ck}_N{N}.log', 'w').write('\n'.join(out) + '\n')
    open(f'{X.ADC}/sim/x2_s3_summary.log', 'a').write('\n'.join(l for l in out if l.startswith('RESULT')) + '\n')
    open(f'{X.ADC}/sim/x2_done.txt', 'a').write(f'{time.strftime("%F %T")} x2_s3 {ck} N={N} done, wall {time.time()-t00:.0f} s\n')
