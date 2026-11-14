#!/usr/bin/env python3
"""D4: supply-current waveforms at the STA-matched corners.  usage: d4_idd.py dac <corner> <tempC> <VDD> <vin> -> sim/d4_idd_<corner>_<T>_<vin>.npz   (transistor-level DAC, scripted controls, T = 200 ns)
       d4_idd.py cmp <corner> <tempC> <VDD> <W ns> <slew ns> -> sim/d4_cmp_<corner>_<T>.npz  (cmp_p + clock edges, i(Vdd) of the two decisions)"""
import sys, os, subprocess, tempfile, numpy as np
H = os.path.dirname(os.path.abspath(__file__)); ADC = os.path.abspath(os.path.join(H, '..')); sys.path.insert(0, H)
import d2_conv as dc; from d2lib import *
cmd, corner, temp, vdd = sys.argv[1], sys.argv[2], sys.argv[3], float(sys.argv[4])
os.makedirs(f'{ADC}/sim/.ptmp', exist_ok=True)
if cmd == 'dac':
    vin = float(sys.argv[5]); T = 200e-9; dc.VSUP = vdd
    ctrl, tend, info = dc.control('conv', [vin], T); t, d = dc.run(corner, temp, ctrl, tend, f'd4_{corner}', extra=[f'VSUP={vdd}'])
    ts, to, tc0, te = info[0]; m = (t >= tc0 - 2e-9) & (t <= tc0 + 12 * T + 5e-9)
    q = [-np.trapezoid(d['idd'][(t >= tc0 + k*T - 0.5e-9) & (t < tc0 + (k+1)*T)], t[(t >= tc0 + k*T - 0.5e-9) & (t < tc0 + (k+1)*T)]) * 1e12 for k in range(12)]
    np.savez(f'{ADC}/sim/d4_idd_{corner}_{temp}_{vin:g}.npz', t=t[m] - tc0, i=d['idd'][m], T=T, vin=vin, vdd=vdd)
    print(f'IDD {corner} {temp}C {vdd}V vin {vin}: charge per trial [pC] ' + ' '.join(f'{x:.2f}' for x in q) + f' total {sum(q):.2f}')
else:
    W, slew = float(sys.argv[5]) * 1e-9, float(sys.argv[6]) * 1e-9; vc = vdd / 2; res = {}
    for name, od in (('dec0', 0.010), ('dec1', -0.010), ('small', 0.0002)):
        net = f"""* D4 comparator supply current
.include {ADC}/spice/models_{corner}.spice
.include {ADC}/spice/comparator_params.spice
.include {ADC}/spice/comparator.spice
.options gmin=1e-12 reltol=1e-4 abstol=1e-15 vntol=1e-7 chgtol=1e-17 itl1=500 itl4=500
.temp {temp}
Vdd vdd 0 {vdd}
Vck ck 0 PWL(0 0 {20e-9:.4e} 0 {20e-9+slew:.4e} {vdd} {20e-9+W:.4e} {vdd} {20e-9+W+slew:.4e} 0)
Vinp inp 0 {vc}
Vinn inn 0 {vc + od}
Xc inp inn ck outp outn vdd 0 cmp_p
Cl1 outp 0 5f
Cl2 outn 0 5f
.tran 5p 60n 0 20p
.control
run
wrdata @OUT@ i(Vdd)
quit
.endc
.end
"""
        d = tempfile.mkdtemp(prefix='cmp_', dir=f'{ADC}/sim/.ptmp'); open(f'{d}/n.spice', 'w').write(net.replace('@OUT@', f'{d}/o.csv'))
        subprocess.run(['ngspice', '-b', f'{d}/n.spice'], capture_output=True, text=True, timeout=600); a = np.loadtxt(f'{d}/o.csv'); os.system(f'rm -rf {d}')
        t, i = a[:, 0], -a[:, 1]; m = (t >= 18e-9) & (t <= 59e-9); q = np.trapezoid(i[m] - i[(t > 10e-9) & (t < 15e-9)].mean(), t[m]) * 1e12
        res[name] = (t[m] - 20e-9, i[m] - i[(t > 10e-9) & (t < 15e-9)].mean(), q)
    np.savez(f'{ADC}/sim/d4_cmp_{corner}_{temp}.npz', **{f'{k}_t': v[0] for k, v in res.items()}, **{f'{k}_i': v[1] for k, v in res.items()}, W=W, vdd=vdd)
    print(f'CMPI {corner} {temp}C {vdd}V W {W*1e9:.1f} ns: charge per decision [pC] ' + ' '.join(f'{k} {v[2]:.2f} (peak {v[1].max()*1e3:.2f} mA)' for k, v in res.items()))
