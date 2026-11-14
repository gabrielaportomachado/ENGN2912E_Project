#!/usr/bin/env python3
"""D2 supply model: 8 ADCs (staggered by one SCLK each, or simultaneous) draw the DAC-driver current waveform of the transistor-level DAC (sim/d2_idd_typical_200_1.2345.npz, cycle windows re-placed at the SCLK period)
+ the comparator charge (D1: 2.6 pC per decision, worst) [+ optional digital clock-edge charge, ESTIMATE] from an on-chip decap C fed through R-L (L = 2 nH ASSUMED, series R swept) from an ideal 3.3 V source.
Supply error at every decision instant n (clock rise of cycle n, evaluated over the 2 ns evaluate window): e = (f * dVDD_dac + k_cmp) ... in LSB, f = fraction of the DAC connected to VDD (0.5 mid-scale convention of the user, 1.0 worst), k_cmp = 0.038 LSB/mV (D1 fixed-reference).
usage: d2_supply.py table | sweep      -> sim/d2_supply_table.log / sim/d2_supply_sweep.log"""
import sys, os, subprocess, tempfile, shutil, atexit, threading, numpy as np
_tl = threading.local(); _cnt = [0]; _lk = threading.Lock()
def _core():
    if not hasattr(_tl, 'c'):
        with _lk: _tl.c = _cnt[0] % 7; _cnt[0] += 1
    return _tl.c
H = os.path.dirname(os.path.abspath(__file__)); ADC = os.path.abspath(os.path.join(H, '..')); sys.path.insert(0, H)
LSB = 3.3 / 4096; KCMP = 0.38 / 10.0           # LSB per mV, comparator, fixed 1.65 V reference (D1: 0.31-0.38 per 10 mV)
QCMP = 2.6e-12; WCMP = 2e-9                      # D1: 1.8-2.6 pC per decision in ~2 ns
QDIG = 1.5e-12; WDIG = 1e-9                      # ESTIMATE only (D0b: 25 flops x 0.2 pJ / 3.3 V), at the clock rising edge of every cycle
NADC = 8; NTR = 12
z = np.load(f'{ADC}/sim/d2_idd_typical_200_1.2345.npz'); TZ, IZ, T0 = z['t'], -z['i'], float(z['T'])   # load current positive
# cycle windows: [k*T0 - 0.5 ns, k*T0 + 100 ns) of the 5 MHz run (activity ends after ~60 ns; checked below)
def pulse_k(k):
    m = (TZ >= k * T0 - 0.5e-9) & (TZ < k * T0 + 100e-9); return TZ[m] - k * T0, IZ[m]
def build(T, stag, dig, dt=0.1e-9, ntr=NTR):
    ncyc = ntr + (NADC - 1) * stag + 2; tend = ncyc * T; t = np.arange(0, tend, dt); i = np.zeros_like(t); chk = []
    for a in range(NADC):
        for k in range(ntr):
            tt, ii = pulse_k(k); t0 = (k + a * stag) * T
            i += np.interp(t, t0 + tt, ii, left=0, right=0)
            tc = t0 + T / 2; i += ((t >= tc) & (t < tc + WCMP)) * QCMP / WCMP
            if dig: i += ((t >= t0) & (t < t0 + WDIG)) * QDIG / WDIG
    return t, i, tend
def run(C, R, T, stag, dig, L=2e-9, keep=None):
    tmp = tempfile.mkdtemp(prefix='d2s_', dir=f'{ADC}/sim/.ptmp'); atexit.register(shutil.rmtree, tmp, True)
    t, i, tend = build(T, stag, dig)
    open(f'{tmp}/i.inc', 'w').write('Iload vdd 0 PWL(\n' + '\n'.join(f'+ {a:.4e} {b:.5e}' for a, b in zip(t[::1], i[::1])) + ')\n')
    open(f'{tmp}/n.spice', 'w').write(f"""* D2 supply L-C-R
Vext vx 0 3.3
Rs vx vl {R}
Ls vl vdd {L}
Cd vdd 0 {C}
.include {tmp}/i.inc
.ic v(vdd)=3.3
.tran 0.05n {tend:.6e} 0 0.1n uic
.control
run
wrdata {tmp}/o.csv v(vdd)
quit
.endc
.end
""")
    subprocess.run(['taskset', '-c', str(_core()), 'ngspice', '-b', f'{tmp}/n.spice'], capture_output=True, text=True, timeout=1700)
    a = np.loadtxt(f'{tmp}/o.csv'); shutil.rmtree(tmp, True); return a[:, 0], a[:, 1] - 3.3, (t, i)
def decisions(tt, dv, T, stag, ntr=NTR):
    """per cycle n: dVDD at the comparator clock rise (the plate is sampled by the comparator; DAC term (a)) and the max |dVDD| in the 2 ns evaluate window (includes the comparators' own draw: conservative DAC term (b), and the comparator term)"""
    ra, wb = [], []
    for n in range(ntr + (NADC - 1) * stag):
        tr = n * T + T / 2; ra.append(np.interp(tr - 0.3e-9, tt, dv)); m = (tt >= tr) & (tt <= tr + 2e-9); wb.append(dv[m][np.argmax(np.abs(dv[m]))])
    return np.array(ra), np.array(wb)
def err_lsb(ra, wb, f): return f * np.abs(ra) / LSB + KCMP * np.abs(wb) * 1e3, f * np.abs(wb) / LSB + KCMP * np.abs(wb) * 1e3     # (a) DAC term at the clock rise, (b) DAC term at the window maximum
def build2(T, stag, dig, dt=0.1e-9, ntr=NTR):
    ncyc = ntr + (NADC - 1) * stag + 2; tend = ncyc * T; t = np.arange(0, tend, dt); idac = np.zeros_like(t); imain = np.zeros_like(t)
    for a in range(NADC):
        for k in range(ntr):
            tt, ii = pulse_k(k); t0 = (k + a * stag) * T; idac += np.interp(t, t0 + tt, ii, left=0, right=0)
            tc = t0 + T / 2; imain += ((t >= tc) & (t < tc + WCMP)) * QCMP / WCMP
            if dig: imain += ((t >= t0) & (t < t0 + WDIG)) * QDIG / WDIG
    return t, idac, imain, tend
def run_split(Cm, Cd, Rs, T, stag, dig, R=0.25, L=2e-9):
    tmp = tempfile.mkdtemp(prefix='d2p_', dir=f'{ADC}/sim/.ptmp'); atexit.register(shutil.rmtree, tmp, True)
    t, idac, imain, tend = build2(T, stag, dig)
    for nm, arr in (('d', idac), ('m', imain)): open(f'{tmp}/i{nm}.inc', 'w').write(f'I{nm}load v{nm} 0 PWL(\n' + '\n'.join(f'+ {a:.4e} {b:.5e}' for a, b in zip(t, arr)) + ')\n')
    open(f'{tmp}/n.spice', 'w').write(f'''* D2 split supply: pad pair -> R-L -> vpad; main rail (comparators + logic) = vpad with Cm; DAC rail vd = vpad through Rs with Cd
Vext vx 0 3.3
Rp vx vl {R}
Lp vl vm {L}
Cm vm 0 {Cm}
Rs vm vd {Rs}
Cd vd 0 {Cd}
.include {tmp}/id.inc
.include {tmp}/im.inc
.ic v(vm)=3.3 v(vd)=3.3
.tran 0.05n {tend:.6e} 0 0.1n uic
.control
run
wrdata {tmp}/o.csv v(vd) v(vm)
quit
.endc
.end
''')
    subprocess.run(['taskset', '-c', str(_core()), 'ngspice', '-b', f'{tmp}/n.spice'], capture_output=True, text=True, timeout=1700)
    a = np.loadtxt(f'{tmp}/o.csv'); shutil.rmtree(tmp, True); return a[:, 0], a[:, 1] - 3.3, a[:, 3] - 3.3
def build3(T, qcmp, cstag, dig, tbase=30e-9, dt=0.1e-9, ntr=NTR):
    """DAC pulses at (k+a)T per ADC a (staggered conversions); comparator pulse of ADC a at (k+a)T + tc_a with tc_a = T/2 (cstag = 0, all on the same edge) or tbase + a*Delta (cstag = 1, Delta = min(100 ns, (T - tbase - 15 ns)/8))"""
    ncyc = ntr + NADC + 1; tend = ncyc * T; t = np.arange(0, tend, dt); idac = np.zeros_like(t); imain = np.zeros_like(t); dly = min(100e-9, (T - tbase - 15e-9) / NADC); inst = []
    for a in range(NADC):
        for k in range(ntr):
            tt, ii = pulse_k(k); t0 = (k + a) * T; idac += np.interp(t, t0 + tt, ii, left=0, right=0)
            tc = t0 + (tbase + a * dly if cstag else T / 2); imain += ((t >= tc) & (t < tc + WCMP)) * qcmp / WCMP; inst.append(tc)
            if dig: imain += ((t >= t0) & (t < t0 + WDIG)) * QDIG / WDIG
    return t, idac, imain, tend, np.array(inst), dly
def run_split3(Cm, Cd, Rs, T, qcmp, cstag, dig, R=0.25, L=2e-9):
    tmp = tempfile.mkdtemp(prefix='d2p_', dir=f'{ADC}/sim/.ptmp'); atexit.register(shutil.rmtree, tmp, True)
    t, idac, imain, tend, inst, dly = build3(T, qcmp, cstag, dig)
    for nm, arr in (('d', idac), ('m', imain)): open(f'{tmp}/i{nm}.inc', 'w').write(f'I{nm}load v{nm} 0 PWL(\n' + '\n'.join(f'+ {a:.4e} {b:.5e}' for a, b in zip(t, arr)) + ')\n')
    open(f'{tmp}/n.spice', 'w').write(f"""* D2 split supply, staggered comparator clocks
Vext vx 0 3.3
Rp vx vl {R}
Lp vl vm {L}
Cm vm 0 {Cm}
Rs vm vd {Rs}
Cd vd 0 {Cd}
.include {tmp}/id.inc
.include {tmp}/im.inc
.ic v(vm)=3.3 v(vd)=3.3
.tran 0.05n {tend:.6e} 0 0.1n uic
.control
run
wrdata {tmp}/o.csv v(vd) v(vm)
quit
.endc
.end
""")
    subprocess.run(['taskset', '-c', str(_core()), 'ngspice', '-b', f'{tmp}/n.spice'], capture_output=True, text=True, timeout=1700)
    a = np.loadtxt(f'{tmp}/o.csv'); shutil.rmtree(tmp, True); return a[:, 0], a[:, 1] - 3.3, a[:, 3] - 3.3, inst, dly
if __name__ == '__main__' and sys.argv[1] == 'split3':
    # usage: d2_supply.py split3 <SCLK MHz> <cstag 0|1> <Qcmp pC> [dig]
    f = float(sys.argv[2]); cstag = int(sys.argv[3]); qc = float(sys.argv[4]) * 1e-12; dig = len(sys.argv) > 5 and sys.argv[5] == 'dig'; T = 1e-6 / f; L_ = []
    def P(s_=''): print(s_); L_.append(s_)
    import concurrent.futures as cf
    Rss = [10]; Cds = [0.1e-9, 0.25e-9, 0.5e-9]; Cms = [0.125e-9, 0.25e-9, 0.5e-9, 0.75e-9, 1e-9, 1.5e-9, 2e-9]
    dly = min(100e-9, (T - 30e-9 - 15e-9) / NADC)
    P(f'D2 SPLIT SUPPLY 3: SCLK {f:g} MHz, comparator clocks {"STAGGERED (first at 30 ns, Delta = %.1f ns)" % (dly * 1e9) if cstag else "all on the same edge (T/2)"}, Qcmp = {qc*1e12:.2f} pC per decision, digital charge {"ON (ESTIMATE)" if dig else "off"}; DAC rail Rs + Cd, main rail Cm, pad R 0.25 ohm + L 2 nH (ASSUMED)')
    P('   e_dac = f*|dV_dac at that ADC comparator clock rise|/LSB (worst over all ADC/trials), e_cmp = 0.038 LSB/mV * |dV_main in the 2 ns after the clock rise| (worst); total = e_dac + e_cmp [LSB]')
    def job(a_):
        Rs, Cd, Cm = a_; tt, vd, vm, inst, _ = run_split3(Cm, Cd, Rs, T, qc, cstag, dig)
        da = np.array([np.interp(x - 0.3e-9, tt, vd) for x in inst]); wb = []
        for x in inst:
            m = (tt >= x) & (tt <= x + 2e-9); wb.append(vm[m][np.argmax(np.abs(vm[m]))])
        return np.abs(da).max(), np.abs(wb).max(), np.abs(vd).max(), np.abs(vm).max()
    grid = [(Rs, Cd, Cm) for Rs in Rss for Cd in Cds for Cm in Cms]
    with cf.ThreadPoolExecutor(7) as ex: res = list(ex.map(job, grid))
    P('   Rs[ohm] Cd[nF] Cm[nF] | dV_dac clk rise [mV] | peak dV_dac [mV] | dV_main window [mV] | e_dac f=.5 | e_dac f=1 | e_cmp | total f=.5 | total f=1')
    for (Rs, Cd, Cm), (da, wm, pd, pm) in zip(grid, res):
        P('   %5d  %6.2f  %6.3f | %10.4f | %8.2f | %10.2f | %8.3f | %8.3f | %6.3f | %8.3f | %8.3f' % (Rs, Cd * 1e9, Cm * 1e9, da * 1e3, pd * 1e3, wm * 1e3, 0.5 * da / LSB, da / LSB, KCMP * wm * 1e3, 0.5 * da / LSB + KCMP * wm * 1e3, da / LSB + KCMP * wm * 1e3))
    P('   Minimum Cd + Cm for total <= 0.5 LSB (area at 4.6 fF/um2 MOS decap, ESTIMATE unchecked):')
    for fi, nm in ((0.5, 'f=0.5'), (1.0, 'f=1')):
        best = None
        for (Rs, Cd, Cm), (da, wm, pd, pm) in zip(grid, res):
            if fi * da / LSB + KCMP * wm * 1e3 <= 0.5 and (best is None or Cd + Cm < best[0]): best = (Cd + Cm, Rs, Cd, Cm)
        P('     %-6s %s' % (nm, ('Rs %d ohm, Cd %.2f nF + Cm %.3f nF = %.2f nF = %.0f um2 = %.3f mm2' % (best[1], best[2] * 1e9, best[3] * 1e9, best[0] * 1e9, best[0] / 4.6e-15, best[0] / 4.6e-15 / 1e6)) if best else 'not met on this grid'))
    open(f'{ADC}/sim/d2_supply_split3_{f:g}MHz_cstag{cstag}_q{qc*1e12:.2f}{"_dig" if dig else ""}.log', 'w').write('\n'.join(L_) + '\n')
    sys.exit(0)

if __name__ == '__main__' and sys.argv[1] == 'split':
    dig = len(sys.argv) > 2 and sys.argv[2] == 'dig'; L_ = []
    def P(s_=''): print(s_); L_.append(s_)
    import concurrent.futures as cf
    f = float(sys.argv[3]) if len(sys.argv) > 3 else 5.0; T = 1e-6 / f
    Rss = [10, 30, 100]; Cds = [0.1e-9, 0.2e-9, 0.5e-9, 1e-9, 2e-9, 4e-9, 8e-9]; Cms = [0.5e-9, 1e-9, 1.5e-9, 2e-9, 4e-9]
    P(f'D2 SPLIT SUPPLY: DAC drivers on their own strap (series Rs, local decap Cd), comparators + logic on the main rail (decap Cm), both from the same pad pair (R 0.25 ohm, L 2 nH ASSUMED), staggered, SCLK {f:g} MHz, digital charge {"ON (ESTIMATE)" if dig else "off"}')
    P('   e_dac = f*|dVDD of the DAC rail at the comparator clock rise|/LSB (f = 0.5 mid-scale | 1 worst); e_cmp = 0.038 LSB/mV * max|dVDD of the main rail in the 2 ns evaluate window| (D1 fixed-reference sensitivity); total = e_dac + e_cmp')
    def job(a_):
        Rs, Cd, Cm = a_; tt, vd, vm = run_split(Cm, Cd, Rs, T, 1, dig); ra, wb = [], []
        for n in range(NTR + (NADC - 1)):
            tr = n * T + T / 2; ra.append(np.interp(tr - 0.3e-9, tt, vd)); m = (tt >= tr) & (tt <= tr + 2e-9); wb.append(vm[m][np.argmax(np.abs(vm[m]))])
        return (np.abs(ra).max(), np.abs(wb).max(), np.abs(vd).max(), np.abs(vm).max())
    grid = [(Rs, Cd, Cm) for Rs in Rss for Cd in Cds for Cm in Cms]
    with cf.ThreadPoolExecutor(7) as ex: res = list(ex.map(job, grid))
    P('   Rs[ohm] Cd[nF] Cm[nF] | dV_dac at clock rise [mV] | peak dV_dac [mV] | dV_main window max [mV] | e_dac f=0.5 | e_dac f=1 | e_cmp | total f=0.5 | total f=1 [LSB] | tau=Rs*Cd [ns]')
    for (Rs, Cd, Cm), (da, wm, pd, pm) in zip(grid, res):
        ed5 = 0.5 * da / LSB; ed1 = da / LSB; ec = KCMP * wm * 1e3
        P('   %5d  %6.2f  %5.1f | %10.4f | %8.2f | %10.2f | %8.3f | %8.3f | %6.3f | %8.3f | %8.3f | %6.1f' % (Rs, Cd * 1e9, Cm * 1e9, da * 1e3, pd * 1e3, wm * 1e3, ed5, ed1, ec, ed5 + ec, ed1 + ec, Rs * Cd * 1e9))
    P('   Decap needed for total <= 0.5 LSB (f = 0.5 | f = 1), smallest grid point per Rs, minimising Cd + Cm on the grid:')
    for Rs in Rss:
        for fi, nm in ((0.5, 'f=0.5'), (1.0, 'f=1')):
            best = None
            for (R2, Cd, Cm), (da, wm, pd, pm) in zip(grid, res):
                if R2 != Rs: continue
                if fi * da / LSB + KCMP * wm * 1e3 <= 0.5:
                    cost = Cd + Cm
                    if best is None or cost < best[0]: best = (cost, Cd, Cm)
            P('     Rs = %3d ohm %-6s: %s' % (Rs, nm, ('Cd %.1f nF + Cm %.1f nF = %.1f nF  = %.3g um2 of MOS decap (4.6 fF/um2 ESTIMATE, unchecked) = %.3f mm2 per chip' % (best[1] * 1e9, best[2] * 1e9, best[0] * 1e9, best[0] / 4.6e-15 * 1e0 / 1e0 * 1e0 / 1e0 * 1e0, best[0] / 4.6e-15 / 1e6)) if best else 'not met on this grid (Cd <= 8 nF, Cm <= 4 nF)'))
    open(f'{ADC}/sim/d2_supply_split_{f:g}MHz{"_dig" if dig else ""}.log', 'w').write('\n'.join(L_) + '\n')
    sys.exit(0)
if __name__ == '__main__':
    mode = sys.argv[1]; L = []
    def P(s=''): print(s); L.append(s)
    dig = len(sys.argv) > 2 and sys.argv[2] == 'dig'
    if mode == 'table':
        T = float(sys.argv[3]) * 1e-9; stag = int(sys.argv[4]); C = float(sys.argv[5]); R = float(sys.argv[6])
        tt, dv, (t, i) = run(C, R, T, stag, dig)
        Q = np.array([i[(t >= n * T) & (t < (n + 1) * T)].sum() * 0.1e-9 for n in range(NTR + (NADC - 1) * stag)])
        Q = np.array([i[(t >= n * T) & (t < (n + 1) * T)].sum() * 0.1e-9 for n in range(NTR + (NADC - 1) * stag)])
        da, db = decisions(tt, dv, T, stag)
        P(f'D2 supply error at every decision instant: T = {T*1e9:.0f} ns ({1e3/(T*1e9):.2f} MHz), {"staggered" if stag else "SIMULTANEOUS"}, decap {C*1e9:g} nF, R = {R} ohm, L = 2 nH (ASSUMED), digital charge {"ON (ESTIMATE)" if dig else "off"}')
        P('   (a) = dVDD at the comparator clock rise (before the comparators draw), (b) = max |dVDD| in the 2 ns evaluate window (all comparators of that cycle draw 2.6 pC each: conservative); e = f*dV/LSB + 0.038 LSB/mV*|dV_window|')
        P('   cycle n | ADC trials deciding (trial index, 0 = MSB) | charge in the cycle [pC] | dV (a) [mV] | dV (b) [mV] | e (a) f=0.5 | e (b) f=0.5 | e (a) f=1 | e (b) f=1   [LSB]')
        for n, (q, va, vb) in enumerate(zip(Q, da, db)):
            tr = [n - a_ * stag for a_ in range(NADC) if 0 <= n - a_ * stag < NTR] if stag else ([n] * NADC if n < NTR else [])
            e5 = err_lsb(va, vb, 0.5); e1 = err_lsb(va, vb, 1.0)
            P('   %5d | %-30s | %6.2f | %+8.3f | %+8.3f | %6.3f | %6.3f | %6.3f | %6.3f' % (n, (' '.join(f'{x}' for x in tr) if stag else (f'{n} (x8)' if tr else '-')), q * 1e12, va * 1e3, vb * 1e3, e5[0], e5[1], e1[0], e1[1]))
        e5 = err_lsb(da, db, 0.5); e1 = err_lsb(da, db, 1.0)
        P('   MAX: dV (a) %.3f mV, (b) %.3f mV; e f=0.5: (a) %.3f (b) %.3f LSB; f=1: (a) %.3f (b) %.3f LSB; peak |dVDD| anywhere %.2f mV' % (np.abs(da).max() * 1e3, np.abs(db).max() * 1e3, e5[0].max(), e5[1].max(), e1[0].max(), e1[1].max(), np.abs(dv).max() * 1e3))
        open(f'{ADC}/sim/d2_supply_table_{sys.argv[3]}ns_{"stag" if stag else "sim"}{"_dig" if dig else ""}_C{C*1e9:g}_R{R}.log', 'w').write('\n'.join(L) + '\n')
    else:
        Cs = [0.25e-9, 0.5e-9, 1e-9, 2e-9, 4e-9, 8e-9, 16e-9, 32e-9]
        P(f'D2 supply sweep (L = 2 nH ASSUMED; ideal decap, no ESR; digital charge {"ON (ESTIMATE)" if dig else "off"}): max over the decision instants of the error in LSB')
        P('   (a) plate error from dVDD at the clock rise + comparator term; (b) conservative: dVDD at the maximum of the 2 ns evaluate window (comparators of all deciding ADCs draw 2.6 pC each)')
        P('   SCLK[MHz] schedule     R[ohm]   row                       C[nF]: ' + '  '.join(f'{c*1e9:>7g}' for c in Cs))
        import concurrent.futures as cf
        cases = [(f, st, R) for f in (5.0, 1.0) for st in (1, 0) for R in (0.1, 0.25, 0.5)]
        def job(a_):
            f, st, R, C = a_; T = 1e-6 / f; tt, dv, _ = run(C, R, T, st, dig); da, db = decisions(tt, dv, T, st)
            return (err_lsb(da, db, 0.5)[0].max(), err_lsb(da, db, 0.5)[1].max(), err_lsb(da, db, 1.0)[0].max(), err_lsb(da, db, 1.0)[1].max(), np.abs(da).max() * 1e3, np.abs(db).max() * 1e3)
        with cf.ThreadPoolExecutor(7) as ex: res = list(ex.map(job, [(f, st, R, C) for (f, st, R) in cases for C in Cs]))
        k = 0
        def need(e):
            e = np.array(e)
            if e[0] <= 0.5: return '<= %.2f nF' % (Cs[0] * 1e9)
            for j in range(1, len(Cs)):
                if e[j] <= 0.5 < e[j - 1]: return '%.2f nF' % (np.exp(np.interp(np.log(0.5), [np.log(e[j]), np.log(e[j - 1])], [np.log(Cs[j]), np.log(Cs[j - 1])])) * 1e9)
            return '> %g nF' % (Cs[-1] * 1e9)
        for (f, st, R) in cases:
            r = res[k:k + len(Cs)]; k += len(Cs); nm = 'staggered' if st else 'simultaneous'
            for lab, idx in (('e(a) f=0.5 LSB', 0), ('e(b) f=0.5 LSB', 1), ('e(a) f=1   LSB', 2), ('e(b) f=1   LSB', 3), ('dV(a) mV', 4), ('dV(b) mV', 5)):
                P('   %6.1f   %-12s %5.2f   %-16s       ' % (f, nm, R, lab) + '  '.join('%7.3f' % x[idx] for x in r) + (('   -> decap for <= 0.5 LSB: ' + need([x[idx] for x in r])) if idx < 4 else ''))
        open(f'{ADC}/sim/d2_supply_sweep{"_dig" if dig else ""}.log', 'w').write('\n'.join(L) + '\n')
