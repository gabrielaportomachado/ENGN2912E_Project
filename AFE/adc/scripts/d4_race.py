#!/usr/bin/env python3
"""D4 capture-vs-reset race at transistor level (PDK spice: std cells inv_1, and3_1, dffq_1, dlya_1 + cmp_p).
tapw rises -> (a) directly to the CLK pin of the capture flop (+ an extra clock delay Dclk swept), (b) inv_1 -> [optional dlya_1] -> and3_1 (A2) -> cmp_clk -> cmp_p -> outp -> flop D.
Decision '0' (outp low, the one the comparator reset turns into 1).  Measures t_reset = tapw 50 % -> outp rising through 10 % VDD (start of reset), the flop's captured value vs Dclk, and the margin
= largest Dclk that still captures 0 (= race time minus flop hold, including the real flop).  usage: d4_race.py <corner ff|typical|ss> <tempC> <VDD> <slew ns> <W ns> [dly]"""
import sys, os, subprocess, tempfile, numpy as np
H = os.path.dirname(os.path.abspath(__file__)); ADC = os.path.abspath(os.path.join(H, '..'))
corner, T, VDD, slew, W = sys.argv[1], sys.argv[2], float(sys.argv[3]), float(sys.argv[4]) * 1e-9, float(sys.argv[5]) * 1e-9
dly = len(sys.argv) > 6 and sys.argv[6] == 'dly'
SC = '/foss/pdks/gf180mcuD/libs.ref/gf180mcu_fd_sc_mcu7t5v0/spice/gf180mcu_fd_sc_mcu7t5v0.spice'
def run(dclk, od=0.010, case0=True):
    t0 = 20e-9; t1 = t0 + W
    vc = VDD / 2
    net = f"""* D4 race
.include {ADC}/spice/models_{corner}.spice
.include {SC}
.include {ADC}/spice/comparator_params.spice
.include {ADC}/spice/comparator.spice
.options gmin=1e-12 reltol=1e-4 abstol=1e-15 vntol=1e-7 chgtol=1e-17 itl1=500 itl4=500
.temp {T}
Vdd vdd 0 {VDD}
Vtap tap 0 PWL(0 0 {t0-slew/2:.4e} 0 {t0+slew/2:.4e} {VDD})
Vtapw tapw 0 PWL(0 0 {t1-slew/2:.4e} 0 {t1+slew/2:.4e} {VDD})
Vtapwc tapwc 0 PWL(0 0 {t1+dclk-slew/2:.4e} 0 {t1+dclk+slew/2:.4e} {VDD})
Vact act 0 {VDD}
Vinp inp 0 {vc}
Vinn inn 0 {vc + od if case0 else vc - od}
Xinv tapw tapwb vdd vdd 0 0 gf180mcu_fd_sc_mcu7t5v0__inv_1
""" + ("Xdl tapwb tapwd vdd vdd 0 0 gf180mcu_fd_sc_mcu7t5v0__dlya_1\n.ic v(tapwb)=%g v(tapwd)=%g\n" % (VDD, VDD) if dly else "") + f"""Xand tap {'tapwd' if dly else 'tapwb'} act ck vdd vdd 0 0 gf180mcu_fd_sc_mcu7t5v0__and3_1
Xc inp inn ck outp outn vdd 0 cmp_p
Cl1 outp 0 5f
Cl2 outn 0 5f
Xff outp tapwc q vdd vdd 0 0 gf180mcu_fd_sc_mcu7t5v0__dffq_1
Cq q 0 5f
.options cshunt=2e-16 rshunt=1e12
.tran 5p {t1+12e-9:.4e} 0 20p
.control
run
wrdata @OUT@ v(tapw) v(ck) v(outp) v(q)
quit
.endc
.end
"""
    d = tempfile.mkdtemp(prefix='race_', dir=f'{ADC}/sim/.ptmp'); out = f'{d}/o.csv'
    open(f'{d}/n.spice', 'w').write(net.replace('@OUT@', out))
    subprocess.run(['ngspice', '-b', f'{d}/n.spice'], capture_output=True, text=True, timeout=600)
    a = np.loadtxt(out); os.system(f'rm -rf {d}')
    t = a[:, 0]; tw, ck, op, q = a[:, 1], a[:, 3], a[:, 5], a[:, 7]
    def cr(v, lev, rising, t_from=0):
        for i in range(1, len(t)):
            if t[i] > t_from and ((v[i-1] < lev <= v[i]) if rising else (v[i-1] > lev >= v[i])): return t[i-1] + (lev - v[i-1]) / (v[i] - v[i-1]) * (t[i] - t[i-1])
    t_tw = cr(tw, VDD / 2, True, t0 + W - 1e-9)
    t_ckf = cr(ck, VDD / 2, False, t_tw - 1e-9)
    t_rst = cr(op, 0.1 * VDD, True, t_tw - 1e-9)       # outp leaves the low decision
    t_w = cr(op, 0.9 * VDD, True, t_tw - 1e-9)
    qf = q[-1]
    return t_tw, t_ckf, t_rst, t_w, qf, ck, t, op
if __name__ == '__main__':
    os.makedirs(f'{ADC}/sim/.ptmp', exist_ok=True)
    t_tw, t_ckf, t_rst, t_w, qf, ck, t, op = run(0.0)
    # window width of cmp_clk
    tk = [t[i] for i in range(1, len(t)) if ck[i-1] < VDD/2 <= ck[i]]
    print(f'RACE {corner} {T}C {VDD}V slew {slew*1e9:.2f}ns W_in {W*1e9:.2f}ns dly={dly}: cmp_clk window {(t_ckf - tk[0])*1e9:.2f} ns, tapw->cmp_clk fall {(t_ckf-t_tw)*1e9:.3f} ns, tapw->outp starts to reset (10% VDD) {(t_rst-t_tw)*1e9:.3f} ns, ->90% {(t_w-t_tw)*1e9:.3f} ns, captured q at Dclk=0: {qf:.2f} V')
    lo, hi = 0.0, 4e-9
    flip = None
    for dc in np.arange(0.0, 4.01e-9, 0.1e-9):
        qf = run(dc)[4]
        if qf > VDD / 2: flip = dc; break
    print(f'RACE_MARGIN {corner} {T}C {VDD}V dly={dly}: capture still correct (q=0) for extra clock delay up to {(flip-0.1e-9 if flip else 4.0e-9)*1e9:.1f} ns (first wrong capture at {"%.1f ns" % (flip*1e9) if flip else ">4.0 ns"})')
