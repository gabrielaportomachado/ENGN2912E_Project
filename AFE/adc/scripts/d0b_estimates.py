#!/usr/bin/env python3
"""D0b hand estimates (one 12-bit SAR per channel, N = 8, one DOUT) -> sim/d0b_estimates.log.  Run: python3 scripts/d0b_estimates.py
Everything is an ESTIMATE (hand algebra / ideal charge-conservation model, no SPICE) unless a line says SIMULATED (value copied from an amplifier log, path given).
Inputs reused from D0 (PLAN.md section 3): unit cap 4.01 fF (1.2 x 1.2 um MIM), binary 12 bit + 1 dummy unit, C_total 16.4 pF, C_s ~17 pF."""
import os, math
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__)); OUT = os.path.join(HERE, '..', 'sim', 'd0b_estimates.log')
L = []
def P(s=''): L.append(s)
VDD = 3.3; LSB = VDD / 4096; Cu = 4.01e-15; N = 8; NB = 12
C = np.array([Cu * 2**k for k in range(NB)]); Cdummy = Cu; Ctot = C.sum() + Cdummy
P('D0b estimates.  N = %d ADCs (one per channel), VDD = VREF = %.1f V, LSB = %.4f mV, C_total = %.2f pF (4096 + 1 dummy units of %.2f fF).  ALL numbers ESTIMATE unless marked SIMULATED.' % (N, VDD, LSB * 1e3, Ctot * 1e12, Cu * 1e15))

# ------------------------------------------------------------------ 1. frame / clock budget
P(); P('== 1. Frame and clock budget (ESTIMATE, arithmetic).  Period per channel T = 250 us (4 kS/s, Decision 16/34).')
CONV = 32; RD = 8 * 16; FR = CONV + RD; STAG = N - 1; TRIAL_END = NB + STAG
P('   frame = %d SCLK = %d conversion window (words 0-1: DIN carries the config word in word 0; conversions end after clock %d = 12 trials + %d stagger clocks) + %d readout (8 x 16-bit words {4-bit ID, 12-bit code}) = %d x 16-bit words' % (FR, CONV, TRIAL_END, STAG, RD, FR // 16))
P('   tracking of ADC i resumes right after ITS last trial (clock %d+i), NOT at CS rising: T_ACQ = T - (%d)/f_SCLK, the readout does not shorten it.  Alternative (track only after CS rising) would give T - %d/f_SCLK.' % (NB, TRIAL_END, FR))
P('   f_SCLK[MHz]  frame[us]  quiet(CS high)[us]  T_ACQ(resume after trials)[us]  T_ACQ(resume at CS rising)[us]  hold time during conversion[us]')
for f in (0.64, 1.0, 2.0, 3.5, 5.0):
    tf = FR / (f * 1e6) * 1e6; ta = 250 - TRIAL_END / f; ta2 = 250 - tf
    P('   %8.2f   %9.1f  %17.1f  %28.1f  %29.1f  %24.1f' % (f, tf, 250 - tf, ta, ta2, TRIAL_END / f))
P('   minimum SCLK (frame must fit in 250 us): %.3f MHz; with >= 100 us of digital silence before the next CS falling: %.2f MHz.  Maximum 5 MHz (D0; D1/D2 confirm: 200 ns per bit trial).' % (FR / 250.0, FR / 150.0))
slope = 2 * math.pi * 300 * 0.5
P('   Sampling-instant jitter: full-scale 300 Hz sine slope = 2 pi 300 x 0.5 V = %.0f V/s -> 1 LSB = %.0f ns; 0.1 LSB = %.0f ns rms: the MCU must generate CS from a hardware timer (software-polled CS jitter of microseconds would cost SNR).' % (slope, LSB / slope * 1e9, 0.1 * LSB / slope * 1e9))
P('   Inter-channel skew of the sample instant = CS-buffer-tree skew (< ~1 ns ESTIMATE) -> 0.1 LSB limit of %.0f ns is met by a factor ~80; "simultaneous sampling" holds.' % (0.1 * LSB / slope * 1e9))
leak = 8 * 1e-12 * (TRIAL_END / 0.64e6) / 17e-12
P('   hold droop during conversion at the slowest SCLK (0.64 MHz, %.0f us), silicon-like 8 x 1 pA ESTIMATE: %.1f uV = %.3f LSB (this PDK model: ~10 fA per junction, 100x less).' % (TRIAL_END / 0.64, leak * 1e6, leak / LSB))

# ------------------------------------------------------------------ 2. supply charge drawn by one ADC (ideal charge conservation)
P(); P('== 2. Charge drawn from VDD by one ADC per bit trial (ESTIMATE, ideal charge-conservation model, bottom-plate sampling, top plate reset to VCM = VDD/2, conventional switching, random Vin uniform in 0..VDD, 20000 draws)')
rng = np.random.default_rng(1)
def run(vin):
    """returns supply charge per trial (list of 12). bits go GND->VDD (trial); a bit that fails the comparison returns to GND (sink, no VDD charge)"""
    Vcm = VDD / 2; b = np.zeros(NB); prev_vb = np.full(NB, vin); vtop_prev = Vcm; Q = []
    for j in range(NB):
        k = NB - 1 - j
        trial = b.copy(); trial[k] = 1
        Vb = (C * trial * VDD).sum() / Ctot
        vtop = Vcm - vin + Vb
        q = 0.0
        # bits that connect to VDD after this step
        for kk in range(NB):
            if trial[kk] == 1 and (j == 0 or prev_vb[kk] != VDD):
                q += C[kk] * ((VDD - vtop) - (prev_vb[kk] - vtop_prev))
        Q.append(q)
        prev_vb = np.where(trial == 1, VDD, 0.0)
        if Vb <= vin: b = trial
        else: prev_vb = np.where(b == 1, VDD, 0.0)
        # after the decision the failing bit goes to GND; top plate shifts (no VDD charge)
        Vb2 = (C * b * VDD).sum() / Ctot; vtop_prev = Vcm - vin + Vb2
    return np.array(Q)
Qs = np.array([run(v) for v in rng.uniform(0, VDD, 20000)])
Qmean = Qs.mean(0); Qmax = Qs.max(0)
P('   trial j (bit 11-j):  ' + ' '.join('%6d' % (11 - j) for j in range(NB)))
P('   mean charge [pC]:    ' + ' '.join('%6.2f' % (q * 1e12) for q in Qmean))
P('   max  charge [pC]:    ' + ' '.join('%6.2f' % (q * 1e12) for q in Qmax))
P('   per conversion: mean %.1f pC, max %.1f pC  (x VDD = %.0f pJ mean from VDD; D0 used 1.3 C V^2 = %.0f pJ, conservative)' % (Qs.sum(1).mean() * 1e12, Qs.sum(1).max() * 1e12, Qs.sum(1).mean() * VDD * 1e12, 1.3 * Ctot * VDD**2 * 1e12))
P('   MSB trial analytic check: C_msb x VDD/2 = %.2f pC (independent of Vin).  D0/Decision 27 used C_msb x VDD = %.1f pC: that is an UPPER BOUND, the floating top plate halves it.' % (C[-1] * VDD / 2 * 1e12, C[-1] * VDD * 1e12))
# simultaneous vs staggered: charge per SCLK cycle summed over the 8 ADCs (using per-trial max as a bound and the mean)
def cyc(Q, stag):
    tot = np.zeros(NB + (N - 1) * stag)
    for i in range(N):
        tot[i * stag:i * stag + NB] += Q
    return tot
P('   FINDING: the supply charge per trial is independent of Vin (a bit that fails its trial returns its charge to GND, not to VDD), so the first-order supply bounce is the SAME every frame (an offset/INL term), not inter-channel crosstalk; the data-dependent part is second order (finite Ron, parasitics: D2/D4).')
P('   charge per SCLK cycle, all %d ADCs together [pC]:' % N)
for nm, Q in (('mean', Qmean), ('max ', Qmax)):
    s = cyc(Q, 0); t = cyc(Q, 1)
    P('     %s simultaneous: peak %.1f pC (cycle 1).  staggered by one SCLK per channel: peak %.1f pC (cycle %d)  -> %.1fx lower' % (nm, s.max() * 1e12, t.max() * 1e12, int(t.argmax()) + 1, s.max() / t.max()))
Qsim = cyc(Qmax, 0).max(); Qstg = cyc(Qmax, 1).max()

# ------------------------------------------------------------------ 3. supply L-C model
P(); P('== 3. VDD disturbance at the decision instant (ESTIMATE; series R-L from board decap to chip, on-chip decap C; the charge Q of one SCLK cycle is drawn in ~1 ns, then the supply rings down)')
P('   ASSUMPTIONS (nothing is known about package/board): L = 2 nH (bond wire + pad + trace to the board capacitor), R = series resistance of that path; underdamped envelope  dV(T) = (Q/C) exp(-T/tau), tau = 2L/R (needs R < 2 sqrt(L/C)).')
P('   Criterion (conservative, error factor 1 on dVDD): dV <= 0.1 LSB = %.0f uV at the decision instant T = half an SCLK period (100 ns at 5 MHz, 143 ns at 3.5 MHz, 500 ns at 1 MHz).' % (0.1 * LSB * 1e6))
Lb = 2e-9
P('   on-chip decap  scheme         Q[pC]  R[ohm]  Z0[ohm]  peak Q/C[mV]  residual at 100 ns [LSB]  at 143 ns  at 500 ns')
for Cd in (0.25e-9, 1e-9, 2e-9):
    for nm, Q in (('simultaneous', Qsim), ('staggered   ', Qstg)):
        for R in (0.1, 0.25, 0.5):
            z0 = math.sqrt(Lb / Cd); tau = 2 * Lb / R; pk = Q / Cd
            r = [pk * math.exp(-T / tau) / LSB for T in (100e-9, 143e-9, 500e-9)]
            P('   %5.2f nF  %s  %7.1f  %5.2f  %6.2f  %12.1f  %16.3g %10.3g %10.3g%s' % (Cd * 1e9, nm, Q * 1e12, R, z0, pk * 1e3, r[0], r[1], r[2], '' if R < 2 * z0 else '  (overdamped: formula n/a)'))
dens = 4.6e-15   # F/um2 (ESTIMATE: 3.3 V gate oxide ~7.5 nm, Cox = 3.9 eps0/tox; NOT checked in the PDK)
cs, cg = Qsim / 0.05, Qstg / 0.05
P('   Peak droop without ringing = Q/C: to keep it <= 50 mV (so logic and comparator stay functional, ESTIMATE) the on-chip decap must be C >= Q/50 mV:  simultaneous %.2f nF, staggered %.2f nF.' % (cs * 1e9, cg * 1e9))
P('   MOS gate decap density ~%.1f fF/um2 (ESTIMATE, see code comment): %.2f nF = %.2f mm2 (simultaneous), %.2f nF = %.2f mm2 (staggered).  Slot ~1.23 mm2; ADCs themselves 0.136 mm2.  MIM decap (2 fF/um2) is ~2.3x worse per area unless overlaid on circuits.' % (dens * 1e15, cs * 1e9, cs / dens / 1e6, cg * 1e9, cg / dens / 1e6))
P('   => the supply is the biggest ADC risk of this architecture; staggering divides the peak charge (and the decap area) by ~%.1f for 7 flops and 7 extra clocks.  The ring-down needs R >~ 0.2-0.5 ohm of series damping (not known): D2/D4 simulate with an L-C-R supply model (Decision 27).' % (Qsim / Qstg))

# ------------------------------------------------------------------ 4. area
P(); P('== 4. Area (ESTIMATE; D0 per-ADC cell numbers, PLAN.md section 2: DAC 9,400 + comparator 2,000 + SAR logic 25 flops x 75 + 80 gates x 15 + switches/drivers 1,500)')
dac, cmpa, logic, sw = 9400, 2000, 25 * 75 + 80 * 15, 1500
chain = 12 * 25
per = dac + cmpa + logic + sw + chain
P('   per ADC: DAC %d + comparator %d + SAR logic %d + switches %d + 12 chain mux2 x 25 um2 = %d  = %d um2' % (dac, cmpa, logic, sw, chain, per))
sh_fl = 8 + 3 + 7 + 9 + 9 + 3; sh_gt = 150; sh = sh_fl * 75 + sh_gt * 15 + 1000
P('   shared digital (frame counter 8 + ID counter 3 + stagger token chain 7 + config shift 9 + config hold 9 + control 3 = %d flops x 75, ~%d gates x 15, + 1,000 clock/buffers) = %d um2' % (sh_fl, sh_gt, sh))
P('   8 ADCs %d um2 + shared %d = %d um2 = %.3f mm2   (TAPEOUT.md estimate ~0.13 mm2: confirmed).  Decap is NOT included: 0.16 mm2 (staggered) to 0.47 mm2 (simultaneous) of MOS decap if the 50 mV peak criterion is kept (section 3).' % (8 * per, sh, 8 * per + sh, (8 * per + sh) / 1e6))
P('   alternatives not chosen: 96 separate capture flops + 96 load/shift mux2 = ~%d um2 extra (vs %d for reusing the SAR result registers as the chain); ID-less 96-bit stream saves 3 flops, but breaks the Decision 18 word.' % (96 * 75 + 96 * 25, 96 * 25))

# ------------------------------------------------------------------ 5. power
P(); P('== 5. Power (ESTIMATE) at 8 x 4 kS/s = 32 kS/s total, 3.3 V')
E_dac = 1.3 * Ctot * VDD**2; agg = 32e3
p_dac = E_dac * agg; p_cmp = (12 * 0.5e-12 + 12 * 0.25e-12 * 25 / 5) * agg
Eflop = 0.2e-12; p_rd = FR / 160 * 128 * 96 * Eflop * 4e3
Cclk = 1.5e-12; p_clk = FR * Cclk * VDD**2 * 4e3
P('   DAC switching %.0f pJ x %d kS/s = %.1f uW;  comparator + SAR logic (D0 formula) %.2f uW;  readout chain 128 clocks x 96 flops x %.1f pJ x 4 kHz = %.1f uW;  clock tree %.1f pF x %d clocks x 4 kHz = %.1f uW' % (E_dac * 1e12, agg / 1e3, p_dac * 1e6, p_cmp * 1e6, Eflop * 1e12, p_rd * 1e6, Cclk * 1e12, FR, p_clk * 1e6))
tot = p_dac + p_cmp + p_rd + p_clk
P('   total ADC + interface %.0f uW (%.1f uA at 3.3 V) = %.1f %% of the 8 amplifiers (8 x 245 uW = 1.96 mW, SIMULATED A4a typical); the digital readout and the clock tree, not the DAC, dominate (D0 assumed ~17 uW).' % (tot * 1e6, tot / VDD * 1e6, tot / 1.96e-3 * 100))

# ------------------------------------------------------------------ 6. acquisition step / reset
P(); P('== 6. Acquisition: reset to 1.65 V or not (ESTIMATE + SIMULATED A4b data)')
for f in (1.0, 3.5, 5.0):
    t = TRIAL_END / f * 1e-6
    st = slope * t
    P('   f_SCLK %.1f MHz: ADC i reconnects to its amplifier %.1f us after the sample instant; the output moves at most %.0f V/s x that = %.1f mV = %.1f LSB, plus the code residual (<= ~2 LSB, D1/D2) -> step at reconnect ~%.1f mV' % (f, t * 1e6, slope, st * 1e3, st / LSB, st * 1e3 + 2 * LSB * 1e3))
P('   A4b SIMULATED (sim/a4b_adc245.log, no reset, C_s 17 pF behind 1 kOhm, step +-0.24 V = the sample-to-sample step of a 300 Hz full-scale sine): |err| at 245 us <= 0.26 LSB (0.21 uV input-referred) typ/ff 85/ss -40; <= 0.48 LSB even at 11 us.')
P('   The reconnect step is ~%.0fx smaller than the 0.24 V tested, so the A4b run is a conservative bound (error scales ~linearly with the step: ESTIMATE <= %.3f LSB).' % (0.24 / (slope * TRIAL_END / 3.5e6), 0.26 * (slope * TRIAL_END / 3.5e6) / 0.24))
P('   Reset to 1.65 V (A4b SIMULATED, sim/a4b_adc.log): -0.74..-2.25 LSB at 11 us and 0.4-2 mV left 240 us later; needs one more switch per ADC and a 1.65 V source -> REJECTED (also in Decision 28).')
P('   Large steps (power-up: C_s at 0 V, or an artifact): worst-corner follower sink 3.26 uA, tau 315 ns (D0, SIMULATED A4a): 1.65 V down = %.1f us to 0.5 LSB, well inside T_ACQ; the stage-2 loop kick (error ~ step^2, A4b) is ESTIMATED at (1.65/0.5)^2 x (0.4-2 mV) = %.0f-%.0f mV at 240 us for a 1.65 V step, decaying with the 0.3-0.5 ms loop constant -> discard the first ~10 frames (2.5 ms) after reset.' % ((17e-12 * 1.65 / 3.26e-6 + math.log(1.65 / (0.5 * LSB)) * 315e-9) * 1e6, (1.65 / .5)**2 * .4, (1.65 / .5)**2 * 2))
# ------------------------------------------------------------------ 7. VDD / crosstalk budget with the SIMULATED PSRR table
P(); P('== 7. VDD and crosstalk budget in LSB, with the SIMULATED amplifier supply gain (sim/a4b_vddbudget.log: dVDD_max for 0.2 LSB = 2.29 mV @50 Hz, 3.46 mV @300 Hz, 10.35 mV @DC, 0.58 mV @1 kHz, 0.35 mV @10 kHz)')
bud = [('kT/C (C_s 16.4 pF)', math.sqrt(1.380649e-23 * 300 / Ctot) / LSB), ('comparator noise (D1)', 0.25), ('DAC mismatch (D2)', 0.25),
       ('external VDD noise/ripple (0.2 LSB at the 2.3 mV rms in-band limit above; supply gain A4b)', 0.20), ('sampling switch distortion + injection (D2)', 0.15),
       ('NEW: inter-channel crosstalk: second-order data-dependent part of the on-chip supply bounce (8 ADCs; the first-order charge per trial is data-independent, section 2)', 0.07), ('NEW: shared vcm tap / digital activity at the decision instants (D1/D4)', 0.05)]
tt = 0
for n, v in bud: P('   %-100s %.3f' % (n, v)); tt += v * v
P('   RSS = %.2f LSB rms (limit 0.5 excluding quantisation 0.29)' % math.sqrt(tt))
P('   On-chip generated supply noise is synchronous with the conversions (4 kHz repetition) and ADC-code dependent: it shows up as offset/INL and cross-channel leakage, not as band noise; external supply noise at 1-10 kHz aliases (no anti-alias filter, Decision 23).')
open(OUT, 'w').write('\n'.join(L) + '\n'); print('\n'.join(L))
