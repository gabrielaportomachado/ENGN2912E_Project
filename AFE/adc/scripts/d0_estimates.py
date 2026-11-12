#!/usr/bin/env python3
"""D0 hand estimates + aliasing budget -> sim/d0_estimates.log.  Run: python3 scripts/d0_estimates.py
Everything labelled ESTIMATE is a hand calculation (assumptions printed with it).  The aliasing section uses SIMULATED amplifier data:
amp/sim/a4a_nspec_<corner>_<T>.csv (output noise V/rtHz, IDEAL R, fnoicor=0) and amp/sim/a4a_bode_<corner>_<T>.csv (gain dB vs f)."""
import os, math
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__)); AMP = os.path.join(HERE, '..', '..', 'amp', 'sim'); OUT = os.path.join(HERE, '..', 'sim', 'd0_estimates.log')
L = []
def P(s=''): L.append(s)
k = 1.380649e-23; T = 300.0; kT = k * T
VDD = 3.3; N = 12; LSB = VDD / 2**N
P('D0 estimates (ADC).  VDD = VREF = 3.3 V, 12 bit: LSB = %.4f mV, full scale 4096 codes.  kT = %.3e J (300 K).' % (LSB * 1e3, kT))
# ---------------------------------------------------------------- 1. amplifier output noise in LSB
P(); P('== 1. What the ADC sees (SIMULATED, amp/sim/a4a_summary.txt): amplifier output noise = input-referred 1.54-1.80 uV x 1000 gain')
for vn in (1.54, 1.80): P('   input-referred %.2f uV  ->  %.2f mV rms at the ADC input = %.2f LSB rms' % (vn, vn, vn / (LSB * 1e3)))
P('   => the amplifier noise (~1.9-2.2 LSB rms) already sets the ENOB; the ADC itself should add <= 0.5 LSB rms (RSS +3 %% at 2.1 LSB: sqrt(2.1^2+0.5^2)=%.2f)' % math.hypot(2.1, .5))
P('   quantisation noise alone = LSB/sqrt(12) = %.3f LSB rms' % (1 / math.sqrt(12)))
# ---------------------------------------------------------------- 2. error budget
P(); P('== 2. ADC error budget (ESTIMATE; allocation in LSB rms, input-referred, RSS target <= 0.5 LSB rms excluding the 0.29 LSB quantisation)')
Ctot_bin = 4096 * 4e-15
bud = [('kT/C of the sampling cap (C_s = %.1f pF binary DAC)' % (Ctot_bin * 1e12), math.sqrt(kT / Ctot_bin) / LSB),
       ('comparator input-referred noise (allocation, D1)', 0.25), ('comparator offset (removed by offset in code / not a noise; INL-neutral, allocation 2 LSB max)', 0.0),
       ('DAC mismatch (random DNL/INL, D2; allocation)', 0.25), ('VDD noise / ripple at the decision instants (allocation, D4)', 0.20),
       ('sampling-switch distortion + charge injection (allocation, D2)', 0.15)]
tot = 0
for n, v in bud: P('   %-84s %.3f' % (n, v)); tot += v * v
P('   RSS of the allocations = %.2f LSB rms (limit 0.5)' % math.sqrt(tot))
# ---------------------------------------------------------------- 3. DAC sizing
P(); P('== 3. Cap DAC (ESTIMATE).  The PDK gives NO local MIM mismatch (mimcap_statistical = one global skew, agauss(0,0.025,3); no VCR term is active in cap_mim_2f0), so the unit-cap mismatch is an ASSUMPTION:')
Ac = 0.5e-2 * 1.0   # 0.5 %*um   (Pelgrom constant, ASSUMPTION)
P('   ASSUMPTION  sigma(dC/C) = A_C/sqrt(area), A_C = 0.5 %*um  (typical MIM; confirm / sweep in D2 with a per-unit agauss model)')
cx_area, cx_peri = 1.99e-15, 0.2383e-15           # F/um2, F/um (cap_mim_2f0 model: 1.99 fF/um2 + 0.2383 fF/um perimeter factor x 2(L+W))
def unitcap(side_um): return cx_area * side_um**2 + 2 * 2383e-10 * 1e-6 * 0 + 2.383e-10 * 2 * (2 * side_um) * 1e-6
for side in (1.0, 1.2, 1.5, 2.0):
    C = 1.99e-3 * side**2 * 1e-12 + 2.383e-10 * 2 * (2 * side) * 1e-6    # PDK formula C = 1.99e-3*L*W + 2.383e-10*2*(L+W) (SI), here per square unit
    sig = Ac / side
    msb = 64 * sig                       # binary 12 bit: sigma(DNL at the MSB carry) = sqrt(4096)*sigma_u LSB
    P('   unit %.1fx%.1f um: Cu = %.2f fF, sigma_u = %.2f %%, MSB-carry DNL sigma = %.2f LSB, total 4096 Cu = %.1f pF, array area ~ %.0f um2 (x1.6 spacing/dummies)' % (side, side, C * 1e15, sig * 100, msb, 4096 * C * 1e12, 4096 * side**2 * 1.6))
P('   => choose unit 1.2 x 1.2 um (Cu ~4.0 fF): sigma_u 0.42 %, DNL(MSB carry) sigma 0.27 LSB (3 sigma = 0.8 LSB), binary-weighted, C_total = 16.4 pF (+ ~1 pF parasitics = C_s ~ 17 pF), array ~ 9,400 um2')
P('   split (6+6, bridge) needs 64x larger units for the same MSB-array accuracy (sigma(MSB carry) = 512 sigma_u LSB) -> same total C, more parasitic sensitivity: no gain, not chosen')
P('   kT/C of 17 pF = %.1f uV = %.3f LSB: negligible.  Needed for kT/C <= 0.1 LSB would be only %.1f fF.' % (math.sqrt(kT / 17e-12) * 1e6, math.sqrt(kT / 17e-12) / LSB, kT / (0.1 * LSB)**2 * 1e15))
# ---------------------------------------------------------------- 4. 1 SAR + mux vs 16 SARs
P(); P('== 4. Decision 19: one SAR + 16:1 analog mux vs 16 SARs (ESTIMATE)')
Cs = 17e-12
dac = 9400; cmp_ = 2000; logic = 25 * 75 + 80 * 15; swd = 1500
one = dac + cmp_ + logic + swd; mux = 16 * 2 * 30 + 400
P('   per-ADC area: DAC %d + comparator %d + SAR/control logic %d (25 flops x 75 + 80 gates x 15 um2, ESTIMATE) + switches/drivers %d = %d um2' % (dac, cmp_, logic, swd, one))
P('   (a) 1 SAR + mux: %d + mux (16 TG pairs + decoder ~%d) = %d um2 = %.3f mm2' % (one, mux, one + mux, (one + mux) / 1e6))
P('   (b) 16 SARs   : 16 x %d = %d um2 = %.3f mm2  (%.1fx larger); needs its own conversion clock + 16 x 12-bit result storage for the SPI side (192 flops ~ %d um2 extra)' % (one, 16 * one, 16 * one / 1e6, 16 * one / (one + mux), 192 * 75))
E_conv = 1.3 * Ctot_bin * VDD**2        # conventional charge-redistribution switching energy ~ 1.3 * C_total * VDD^2 (ESTIMATE)
for rate in (64e3, 128e3, 256e3):
    P('   DAC switching energy %.0f pJ/conversion -> %.1f uW at %d kS/s aggregate (same for (a) and (b): conversions per second are equal); comparator+logic ~ %.1f uW' % (E_conv * 1e12, E_conv * rate * 1e6, rate / 1e3, (12 * 0.5e-12 + 12 * 0.25e-12 * 25 / 5) * rate * 1e6))
P('   amplifiers for reference: 16 x 245 uW = 3.9 mW (A4a) -> ADC power is < 1 %% either way; power does not discriminate, area does (%.0fx).' % (16 * one / (one + mux)))
Rout = 10e3; Ron = 1.0e3
tau = (Rout + Ron) * Cs
P('   mux acquisition: amp follower Zout ~ 1/gm_f ~ %.0f kOhm (A4a: gm_f 69 uS at 5 uA, so ~14 kOhm; 10 kOhm used) + TG Ron ~ %.1f kOhm (ESTIMATE: 3.3 V TG, W/L 10/0.5, 1.15-2.15 V)' % (Rout / 1e3, Ron / 1e3))
P('   tau = (R_out+Ron)*C_s = %.0f ns; settle to 0.1 LSB after a 3.3 V step: t_acq >= %.1f tau = %.2f us; after a 1 V step: %.1f tau = %.2f us' % (tau * 1e9, math.log(3.3 / (0.1 * LSB)), math.log(3.3 / (0.1 * LSB)) * tau * 1e6, math.log(1.0 / (0.1 * LSB)), math.log(1.0 / (0.1 * LSB)) * tau * 1e6))
P('   follower sink limit: it sinks only its bias (3.3-8.4 uA, A4a): slew into C_s = %.1f V/us at 5 uA -> a 3.3 V downward step needs %.2f us (adds to t_acq); source side is not limited' % (5e-6 / Cs * 1e-6, 3.3 / (5e-6 / Cs) * 1e6))
P('   crosstalk (mux memory): residual after t_acq = step * exp(-t_acq/tau); for t_acq = 3 us: %.2e of the step = %.3f LSB for a 1 V step, %.3f LSB for a 3.3 V step' % (math.exp(-3e-6 / tau), 1.0 * math.exp(-3e-6 / tau) / LSB, 3.3 * math.exp(-3e-6 / tau) / LSB))
P('   16 off TG leakage on the shared node (ESTIMATE, silicon-like 1 pA each at 85 C, model gives ~0): 16 pA x 8 us / 17 pF = %.1f uV = %.3f LSB' % (16e-12 * 8e-6 / 17e-12 * 1e6, 16e-12 * 8e-6 / 17e-12 / LSB))
# ---------------------------------------------------------------- 5. timing / interface
P(); P('== 5. Frame timing (ADS7953-style: SCLK clocks the conversion) (ESTIMATE)')
P('   frame = 16 SCLK cycles: CS falling = sample/hold instant; SCLK 1-12 = 12 bit trials MSB first; SCLK 1-16 shift out the PREVIOUS conversion [4-bit channel ID | 12-bit code] MSB first; CS rising = start of acquisition of the next mux channel')
P('   per-conversion time = 16/f_SCLK + t_acq (CS high). Aggregate rate = 16 channels x per-channel rate.')
for osr in (1, 2, 4):
    agg = 64e3 * osr
    for f in (2.048e6, 5e6):
        tf = 16 / f; tp = 1 / agg; ta = tp - tf
        P('   %dx oversampling: %d kS/s/ch, %.0f kS/s aggregate: period %.2f us; SCLK %.3f MHz -> frame %.2f us, t_acq = %.2f us %s' % (osr, 4 * osr, agg / 1e3, tp * 1e6, f / 1e6, tf * 1e6, ta * 1e6, '(OK, >= 3 us)' if ta >= 3e-6 else ('(too short for the 17 pF input at 10 kOhm)' if ta > 0 else '(IMPOSSIBLE)')))
P('   SAR bit-trial: 100-200 ns per SCLK cycle at 5-2.5 MHz; MSB switch drives 8.2 pF: needs Ron <= 0.1 us/(9*8.2 pF) = %.0f Ohm... (9 tau to 0.5 LSB in half a cycle at 5 MHz): W/L ~ 5-10 (ESTIMATE); comparator decision < 20 ns' % (0.1e-6 / (9 * 8.2e-12)))
P('   VREF = VDD: MSB trial draws Q = 8.2 pF x 3.3 V = %.0f pC from the local supply; on-chip decoupling cannot supply it at 0.1 LSB (needs %.0f nF): rely on board decoupling + low-inductance bond wires; the DAC supply must settle to <0.1 LSB (%.2f mV) before each decision (RISK, D2/D4: ringing of L=2 nH + board C)' % (8.2e-12 * 3.3 * 1e12, 8.2e-12 * 3.3 / (0.1 * LSB) * 1e9, 0.1 * LSB * 1e3))
P('   rate of VDD droop error if VDD is NOT ratiometric to Vin: %.2f LSB per mV at mid-scale (code x dVDD/VDD)' % (0.5 / LSB * 1e-3))
P(); P('== 5b. ADC INPUT MODEL for A4b and what it asks of the amplifier output stage')
P('   model (ESTIMATE): sampling cap C_s = 17 pF (16.4 pF binary DAC + ~0.6 pF parasitics) behind a transmission gate Ron = 1 kOhm; 16 mux inputs, off-channel load on each amp output ~ 20 fF;')
P('   the cap is connected for t_acq, then disconnected (CS falling) and its charge is not returned to the amp.  C_s starts at the PREVIOUS channel voltage: step = V_new - V_prev.')
import re
fol = {}
cur = None
for l in open(f'{AMP}/a4a_op.log'):
    if l.startswith('###'): cur = l[4:].strip().replace('op_', '')
    elif l.startswith('OPDEV xch.xs2.xota2.xmf'):
        idv = float(re.search(r'id_A=(\S+)', l).group(1)); g = float(re.search(r'gm_over_id=(\S+)', l).group(1)) * idv
        fol[cur] = (idv, 1 / g)
P('   SIMULATED A4a follower (sim/a4a_op.log): sink current Id and 1/gm_f per corner; DOWNWARD step into C_s = slew C*dV/Id then RC settling n*tau, n = ln(dV/0.5 LSB), tau = (1/gm_f + Ron) C_s (class-A follower: upward steps are source-driven and fast):')
P('   corner       Id[uA]  1/gm_f[kOhm]  tau[ns]   t_settle(1 V down)[us]   t_settle(3.3 V down)[us]')
worst1 = worst3 = 0
for key in sorted(fol, key=lambda x: fol[x][0]):
    idv, rg = fol[key]; tau_c = (rg + 1e3) * 17e-12
    t1 = 17e-12 * 1.0 / idv + math.log(1.0 / (0.5 * LSB)) * tau_c; t3 = 17e-12 * 3.3 / idv + math.log(3.3 / (0.5 * LSB)) * tau_c
    worst1 = max(worst1, t1); worst3 = max(worst3, t3)
    P('   %-12s %6.2f  %10.1f  %8.0f  %14.2f  %22.2f' % (key, idv * 1e6, rg / 1e3, tau_c * 1e9, t1 * 1e6, t3 * 1e6))
P('   WORST over 9 PVT: 1 V down %.2f us, 3.3 V down %.2f us.  Available windows: t_acq = 3.0 / 4.6 / 7.8 / 12.4 us  (SCLK 2.048 MHz at 1x -> 7.8 us; SCLK 5 MHz at 1x -> 12.4 us; 2x oversampling at 5 MHz -> 4.6 us)' % (worst1 * 1e6, worst3 * 1e6))
P('   => 1 V steps: met with 12.4 us (margin %.1f us), only just met at 7.8 us (margin %.2f us at the slowest corner), NOT met at 4.6 us / 3 us.  3.3 V (full-rail artifact) steps: not met at any window below %.1f us.' % ((12.4e-6 - worst1) * 1e6, (7.8e-6 - worst1) * 1e6, worst3 * 1e6))
P('   sink needed to settle a 1 V down step at the worst-case tau (%.0f ns) inside t_acq (slew budget = t_acq - n*tau):' % (((17.5e3 + 1e3) * 17e-12) * 1e9))
tw = (17.5e3 + 1e3) * 17e-12
for ta in (3e-6, 4.6e-6, 7.8e-6, 12.4e-6):
    n1 = math.log(1.0 / (0.5 * LSB)); n3 = math.log(3.3 / (0.5 * LSB))
    f = lambda step, n: ('%.1f uA' % (17e-12 * step / (ta - n * tw) * 1e6)) if ta - n * tw > 0 else 'IMPOSSIBLE'
    P('      t_acq = %4.1f us: 1 V: %-12s 3.3 V: %s' % (ta * 1e6, f(1.0, n1), f(3.3, n3)))
# ---------------------------------------------------------------- 6. aliasing budget (SIMULATED amp data)
P(); P('== 6. Decision 22: aliasing budget from the SIMULATED amplifier (amp/sim/a4a_nspec_*.csv, a4a_bode_*.csv).  f_out = 4 kS/s per channel is the delivered rate')
def load(path):
    a = np.loadtxt(path); return a[:, 0], a[:, 1]
def bode(k, t):
    a = np.loadtxt(f'{AMP}/a4a_bode_{k}_{t}.csv'); return a[:, 0], a[:, 1]
def hd(f, fout, R, order):
    """CIC/sinc^order decimate-by-R magnitude, ADC rate R*fout.  R=1: no digital filter."""
    if R == 1: return np.ones_like(f)
    x = np.pi * f / fout; y = np.pi * f / (R * fout)
    with np.errstate(divide='ignore', invalid='ignore'):
        h = np.abs(np.sin(x) / (R * np.sin(y)))
    h = np.where(np.abs(np.sin(y)) < 1e-9, 1.0, h)
    return h ** order
fout = 4e3; bw = 300.0
cfg = [('1x (4 kS/s/ch, no digital filter)', 1, 0), ('2x (8 kS/s/ch) + sinc^3 by 2', 2, 3), ('4x (16 kS/s/ch) + sinc^3 by 4', 4, 3), ('4x (16 kS/s/ch) + sinc^4 by 4', 4, 4), ('8x (32 kS/s/ch) + sinc^3 by 8', 8, 3)]
for (k, t) in (('ff', '85'), ('typical', '27'), ('ss', '-40')):
    f, s = load(f'{AMP}/a4a_nspec_{k}_{t}.csv'); fb, gdb = bode(k, t)
    gmid = 10 ** (np.interp(np.log10(12.25), np.log10(fb), gdb) / 20)
    fl = np.logspace(np.log10(0.1), np.log10(f.max()), 20000); S = np.interp(np.log10(fl), np.log10(f), s) ** 2     # V^2/Hz
    df = np.gradient(fl)
    base = np.sum(S[(fl >= 0.5) & (fl <= bw)] * df[(fl >= 0.5) & (fl <= bw)])
    P(); P('   corner %s %s C: midband gain %.2f dB; in-band noise 0.5-300 Hz = %.3f uV input-referred' % (k, t, 20 * np.log10(gmid), math.sqrt(base) / gmid * 1e6))
    for name, R, order in cfg:
        H = hd(fl, fout, R, order)
        # a component at f' lands in the 0..300 Hz output band if |f' - m*fout| <= 300 for some integer m >= 1
        m = np.round(fl / fout); d = np.abs(fl - m * fout)
        mask = (m >= 1) & (d <= bw) & (fl > fout / 2)
        alias = np.sum(S[mask] * H[mask] ** 2 * df[mask])
        P('      %-34s aliased noise (input-referred) %.4f uV  = %.3f %% of the in-band power;  total with in-band %.3f uV' % (name, math.sqrt(alias) / gmid * 1e6, 100 * alias / base, math.sqrt(base + alias) / gmid * 1e6))
    # interferer attenuation (dB, relative to the 12 Hz gain) at representative frequencies that alias into 0-300 Hz of the 4 kS/s output
    P('      interferer attenuation (amp response + digital filter) in dB at the frequency shown (alias lands in-band):')
    for fi in (3700, 4300, 7700, 8300, 15700, 16300, 31700):
        g = np.interp(np.log10(fi), np.log10(fb), gdb) - 20 * np.log10(gmid) * 0 - np.interp(np.log10(12.25), np.log10(fb), gdb)
        row = []
        for name, R, order in cfg:
            hdig = hd(np.array([float(fi)]), fout, R, order)[0] if R > 1 else 1.0
            # does this frequency alias at the ADC rate (image of the band) or only through the output decimation?  both are covered by the periodic H; add amp response
            row.append('%.0f' % -(g + 20 * np.log10(max(hdig, 1e-12))))
        P('        %6d Hz: amp alone %.1f dB;  total by option [1x | 2x s3 | 4x s3 | 4x s4 | 8x s3] = %s dB' % (fi, -g, ' | '.join(row)))
    # 100 uV interferer test
    for name, R, order in cfg[:3]:
        worst = 1e9
        for fi in (fout - bw, fout + bw, 2 * fout - bw, 2 * fout + bw, R * fout - bw, R * fout + bw):
            g = np.interp(np.log10(fi), np.log10(fb), gdb) - np.interp(np.log10(12.25), np.log10(fb), gdb)
            hdig = hd(np.array([float(fi)]), fout, R, order)[0] if R > 1 else 1.0
            worst = min(worst, -(g + 20 * np.log10(max(hdig, 1e-12))))
        P('      worst alias attenuation near the band edge (%s): %.1f dB -> a 100 uV pk interferer at the amp input aliases to %.2f uV (target <= 0.5 uV = 46 dB)' % (name, worst, 100 / 10 ** (worst / 20)))
# sinc droop
P(); P('   in-band droop of the digital filter at 300 Hz (fout = 4 kS/s): ' + ', '.join('%s %.2f dB' % (n, 20 * np.log10(hd(np.array([300.0]), fout, R, o)[0])) for n, R, o in cfg[1:]))
open(OUT, 'w').write('\n'.join(L) + '\n'); print('\n'.join(L))
