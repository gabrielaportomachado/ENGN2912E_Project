#!/usr/bin/env python3
"""D4b replay check: ideal 12-trial decision sequence for a Vin, transistor-level DAC + cmp_p driven by scripted controls (d2_conv.control) and comparator clock pulses at the D3 STA instants
(DAC edge -> comparator rise = T0 - latest DAC-edge arrival: 21.0 ns ff_n40 digital, 39.6 tt, 83.8 ss_125; window 3.2 / 5.9 / 12.3 ns).
usage: d4_replay.py <corner> <tempC> <VDD> <dt_c ns> <W ns> <slew ns> <vin,vin,...> [T_ns=333.3]
Output: per trial: plate - Vcm at the comparator clock rise [LSB], sign margin vs the ideal decision [LSB], model-predicted value, error (meas - model) [LSB]; final plate error after trial 12."""
import sys, os, subprocess, tempfile, numpy as np
H = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, H)
import d2_conv as dc; from d2lib import *
corner, temp, vdd, dtc, W, slew = sys.argv[1], sys.argv[2], float(sys.argv[3]), float(sys.argv[4]) * 1e-9, float(sys.argv[5]) * 1e-9, float(sys.argv[6]) * 1e-9
NOCK = 0.0 if os.environ.get('NOCK') else 1.0
vins = [float(x) for x in sys.argv[7].split(',')]; T = float(sys.argv[8]) * 1e-9 if len(sys.argv) > 8 else 333.3e-9
dc.VSUP = vdd; ADC = dc.ADC
import d2lib; d2lib.VDD = vdd; LSB = vdd / 4096     # levels / LSB of the supply under test
def ideal_seq(vin, d):
    lv = d.levels(); code = 0; seq = []; tri = []
    for j in range(11, -1, -1):
        tr = code | (1 << j); tri.append(tr); k = vin >= lv[tr]; seq.append(int(k))
        if k: code = tr
    return code, seq, tri
def model_plate(tr, vin, d, vdd):
    w, wd = d.weights(); nb = 12; bits = np.array([(tr >> b) & 1 for b in range(nb)], float)
    return vdd / 2 + vdd * (w * bits).sum() - (w.sum() + wd) * vin
def run(vin):
    d = Dac(); code, seq, tri = ideal_seq(vin, d)
    ctrl, tend, info = dc.control('conv', [vin], T, d=d); ts, to, tc0, te = info[0]
    tmp = tempfile.mkdtemp(prefix='rp_', dir=f'{ADC}/sim/.ptmp'); open(f'{tmp}/c.inc', 'w').write(ctrl)
    pts = [(0.0, 0.0)]
    for k in range(12):
        tk = tc0 + k * T + dtc; pts += [(tk, 0.0), (tk + slew, vdd * NOCK), (tk + W, vdd * NOCK), (tk + W + slew, 0.0)]
    open(f'{tmp}/k.inc', 'w').write('Vck ck 0 PWL(' + ' '.join(f'{a:.5e} {b:.4f}' for a, b in pts) + ')\n')
    out = f'{tmp}/o.csv'
    e = dict(os.environ, OUT=out, SWAPS=f'@CTRL@={tmp}/c.inc @CK@={tmp}/k.inc @TEND@={tend:.6e} @TMAX@=50p', CELL='x', OMP_NUM_THREADS='1')
    subprocess.run(['bash', f'{ADC}/scripts/dgrun.sh', 'tb_dac_replay.spice', corner, temp, f'VSUP={vdd}'], capture_output=True, text=True, env=e)
    a = np.loadtxt(out); os.system(f'rm -rf {tmp}'); t, vt, op = a[:, 0], a[:, 1], a[:, 3]
    return d, code, seq, tri, tc0, t, vt, op
if __name__ == '__main__':
    os.makedirs(f'{ADC}/sim/.ptmp', exist_ok=True)
    for vin in vins:
        d, code, seq, tri, tc0, t, vt, op = run(vin)
        # calibrate the plate parasitic (comparator input cap) only on the safe case; here: fixed cpt from args via env
        cpt = float(os.environ.get('CPT', '130e-15')); dm = Dac(cpt=cpt)
        rows = []
        for k in range(12):
            tc = tc0 + k * T + dtc; v = np.interp(tc - 0.1e-9, t, vt); m = (t >= tc) & (t <= tc + W + 3e-9); dec = int(np.interp(tc + W - 0.2e-9, t, op) > vdd / 2)
            mdl = model_plate(tri[k], vin, dm, vdd); diff = (v - vdd / 2) / LSB
            marg = (vdd / 2 - v) / LSB * (1 if seq[k] else -1)     # >0: plate on the side that gives the ideal decision (outp = 1 <=> plate below Vcm <=> keep)
            rows.append((diff, marg, (v - mdl) / LSB, dec, vt[(t >= tc - 2e-9) & (t <= tc)].min()))
        tend_last = tc0 + 12 * T; vf = np.interp(tend_last - 1e-9, t, vt); trf = (code << 0)
        mdlf = model_plate(tri[11], vin, dm, vdd)
        print(f'REPLAY {corner} {temp}C {vdd}V vin={vin:.4f} ideal code {code} | diff plate-Vcm at the clock rise [LSB]: ' + ' '.join(f'{r[0]:+.1f}' for r in rows) +
              ' | margin vs ideal decision [LSB]: ' + ' '.join(f'{r[1]:+.1f}' for r in rows) + ' | meas-model [LSB]: ' + ' '.join(f'{r[2]:+.2f}' for r in rows) +
              ' | sim decision / ideal: ' + ' '.join(f'{r[3]}/{s}' for r, s in zip(rows, seq)) + f' | min plate V in 2 ns before clock: ' + ' '.join(f'{r[4]:.2f}' for r in rows[:3]) +
              f' | final plate error after trial 12 (meas-model, trial = final code) {(vf-mdlf)/LSB:+.2f} LSB, min plate V over run {vt.min():.3f}', flush=True)
