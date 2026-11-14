#!/usr/bin/env python3
"""D4 supply study with the REAL comparator stagger from the D3 STA (sim/d3_taps.log) and the transistor-level current waveforms (sim/d4_idd_*.npz DAC drivers, sim/d4_cmp_*.npz comparator, scripts/d4_idd.py).
Model (as D2 + damping): ideal VDD -> Rp -> L 2 nH -> main rail vm (comparators + logic) with Cm in series with Rd; vm -> Rs 10 ohm -> DAC rail vd with Cd in series with Rd.  Loads: DAC drivers on vd (8 ADCs, same Vin), comparators + digital charge (ESTIMATE 1.5 pC / ADC / SCLK edge at edge+1 ns) on vm.
Error at every decision instant (D2 definition): e = f*|dVd(t_c - 0.3 ns)|/LSB + 0.038 LSB/mV * |dVm| max over the 2 ns after the comparator clock rise (f = 0.5 mid-scale, 1 worst).
usage: d4_supply.py <MHz> -> sim/d4_supply_<MHz>MHz.log"""
import sys, os, subprocess, tempfile, shutil, numpy as np, concurrent.futures as cf
H = os.path.dirname(os.path.abspath(__file__)); ADC = os.path.abspath(os.path.join(H, '..'))
LSB = 3.3 / 4096; KC = 0.038
# corner: (analog corner, T, VDD, T0 [ns], Delta [ns], W [ns], DAC-edge arrival after SCLK [ns] mid of STA min/max)
COR = {'ff_n40': ('ff', -40, 3.6, 24.80, 7.30, 3.2, 0.5 * (0.837 + 3.777)),
       'tt_25': ('typical', 27, 3.3, 45.86, 13.5, 5.9, 0.5 * (1.375 + 6.301)),
       'ss_125': ('ss', 125, 3.0, 95.89, 28.4, 12.3, 0.5 * (2.640 + 12.082))}
VINS = [0.4, 1.2345, 1.65, 2.1]; NADC = 8; NTR = 12; QDIG = 1.5e-12
def waves(cn, T, vin, dt=0.1e-9):
    ac, tmp, vdd, T0, DL, W, tg = COR[cn]
    z = np.load(f'{ADC}/sim/d4_idd_{ac}_{tmp}_{vin:g}.npz'); TZ, IZ, TT = z['t'], -z['i'], float(z['T'])
    base = IZ[TZ < -0.5e-9].mean() if (TZ < -0.5e-9).any() else 0.0
    c = np.load(f'{ADC}/sim/d4_cmp_{ac}_{tmp}.npz'); CT, CI = c['dec0_t'], c['dec0_i']
    ncyc = NTR + NADC + 1; t = np.arange(0, ncyc * T, dt); idac = np.zeros_like(t); imain = np.zeros_like(t); inst = []
    for a in range(NADC):
        for k in range(NTR):
            m = (TZ >= k * TT - 0.5e-9) & (TZ < k * TT + 100e-9); tt_, ii = TZ[m] - k * TT, IZ[m] - base
            e0 = (k + a) * T; idac += np.interp(t, e0 + tg * 1e-9 + tt_, ii, left=0, right=0)
            tc = e0 + (T0 + a * DL) * 1e-9; imain += np.interp(t, tc + CT, CI, left=0, right=0); inst.append((a, k, tc))
            imain += ((t >= e0 + 1e-9) & (t < e0 + 2e-9)) * QDIG / 1e-9
    return t, idac, imain, inst, vdd
def sim(cn, T, vin, Rd, Rp, Cm=0.125e-9, Cd=0.1e-9, Rs=10.0, L=2e-9):
    t, idac, imain, inst, vdd = waves(cn, T, vin)
    d = tempfile.mkdtemp(prefix='d4s_', dir=f'{ADC}/sim/.ptmp')
    for nm, arr in (('d', idac), ('m', imain)):
        open(f'{d}/i{nm}.inc', 'w').write(f'I{nm}load v{nm} 0 PWL(\n' + '\n'.join(f'+ {a:.4e} {b:.5e}' for a, b in zip(t, arr)) + ')\n')
    open(f'{d}/n.spice', 'w').write(f"""* D4 supply L-C-R with damping
Vext vx 0 {vdd}
Rp vx vl {Rp}
Lp vl vm {L}
Cm vm cmx {Cm}
Rdm cmx 0 {Rd}
Rs vm vd {Rs}
Cd vd cdx {Cd}
Rdd cdx 0 {Rd}
.include {d}/id.inc
.include {d}/im.inc
.ic v(vm)={vdd} v(vd)={vdd} v(vl)={vdd} v(cmx)={vdd} v(cdx)={vdd}
.tran 0.05n {t[-1]:.6e} 0 0.1n uic
.control
run
wrdata {d}/o.csv v(vd) v(vm)
quit
.endc
.end
""")
    subprocess.run(['ngspice', '-b', f'{d}/n.spice'], capture_output=True, text=True, timeout=1700, env=dict(os.environ, OMP_NUM_THREADS='1'))
    a = np.loadtxt(f'{d}/o.csv'); shutil.rmtree(d, True)
    tt, vd, vm = a[:, 0], a[:, 1] - vdd, a[:, 3] - vdd; err = []
    for (ad, k, tc) in inst:
        dd = np.interp(tc - 0.3e-9, tt, vd); m = (tt >= tc) & (tt <= tc + 2e-9); wm = vm[m][np.argmax(np.abs(vm[m]))]
        err.append((ad, k, dd * 1e3, wm * 1e3))
    return np.array(err), np.abs(vd).max() * 1e3, np.abs(vm).max() * 1e3
if __name__ == '__main__':
    f = float(sys.argv[1]); T = 1e-6 / f; os.makedirs(f'{ADC}/sim/.ptmp', exist_ok=True); out = []
    P = lambda s='': (print(s, flush=True), out.append(s))
    P(f'D4 SUPPLY, SCLK {f:g} MHz, real stagger from D3 STA: L 2 nH, Cm 0.125 nF + Cd 0.1 nF (Rs 10 ohm) each in series with Rd, pad Rp as listed; comparator pulse = transistor-level cmp_p current (d4_cmp_*.npz), DAC = transistor-level drivers (d4_idd_*.npz), same Vin on all 8 ADCs (worst over Vin {VINS}), digital 1.5 pC/ADC/edge ESTIMATE')
    P('  err = f*|dVd at clock rise|/0.806 mV + 0.038 LSB/mV*|dVm in 2 ns|; "dVd" and "dVm" are the worst over the 96 decision instants [mV]')
    jobs = [(cn, Rp, Rd, v) for cn in COR for Rp in (0.25, 0.05) for Rd in (0.25, 1, 3, 10) for v in VINS]
    with cf.ThreadPoolExecutor(7) as ex: res = list(ex.map(lambda j: sim(j[0], T, j[3], j[2], j[1]), jobs))
    R = {}
    for j, r in zip(jobs, res): R.setdefault(j[:3], []).append((j[3], r))
    for cn in COR:
        P(f'\n== corner {cn} (analog {COR[cn][0]} {COR[cn][1]} C, VDD {COR[cn][2]} V): T0 {COR[cn][3]} ns, Delta {COR[cn][4]} ns, W {COR[cn][5]} ns')
        P('   Rp[ohm] Rd[ohm] | worst dVd[mV] dVm[mV] | peak rail dev vd/vm [mV] | err f=0.5 [LSB] (worst ADC, trial) | err f=1 [LSB] | per-ADC worst err f=0.5 (ADC 0..7)')
        for Rp in (0.25, 0.05):
            for Rd in (0.25, 1, 3, 10):
                best = None
                for v, (err, pvd, pvm) in R[(cn, Rp, Rd)]:
                    e5 = 0.5 * np.abs(err[:, 2]) * 1e-3 / LSB + KC * np.abs(err[:, 3]); e1 = np.abs(err[:, 2]) * 1e-3 / LSB + KC * np.abs(err[:, 3])
                    if best is None or e1.max() > best[1].max(): best = (e5, e1, err, pvd, pvm, v)
                e5, e1, err, pvd, pvm, v = best; i5 = int(np.argmax(e5))
                pa = [e5[err[:, 0] == a].max() for a in range(8)]
                P('   %5.2f  %5.2f  | %7.2f %7.2f | %6.1f / %6.1f | %6.3f (ADC %d trial %d, Vin %g) | %6.3f | ' % (Rp, Rd, np.abs(err[:, 2]).max(), np.abs(err[:, 3]).max(), pvd, pvm, e5.max(), err[i5, 0], err[i5, 1] + 1, v, e1.max()) + ' '.join('%.2f' % x for x in pa))
                if Rp == 0.25 and Rd in (1, 3) or (cn == 'ff_n40' and Rp == 0.05):
                    P(f'      per-instant error f=0.5 [LSB], Rp {Rp} Rd {Rd}, Vin {v:g}: rows = ADC 0..7, columns = trial 1..12')
                    for a in range(8): P('        ADC%d ' % a + ' '.join('%5.2f' % e5[(err[:, 0] == a) & (err[:, 1] == k)][0] for k in range(12)))
    open(f'{ADC}/sim/d4_supply_{f:g}MHz.log', 'w').write('\n'.join(out) + '\n')
