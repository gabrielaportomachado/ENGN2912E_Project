#!/usr/bin/env python3
"""A3: parse sim/a3_<case>.log (written by scripts/run_a3.sh) into CSVs and sim/a3_summary.txt.  Every number
in the summary comes from those logs.  usage: python3 scripts/a3_collect.py"""
import re, os, csv, math, sys
AMP = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SIM = os.path.join(AMP, 'sim')

def blocks(case):
    p = os.path.join(SIM, f'a3_{case}.log')
    out, cur = {}, None
    for line in open(p):
        line = line.rstrip('\n')
        if line.startswith('### '):
            cur = line[4:]; out[cur] = []
        elif cur is not None:
            out[cur].append(line)
    return out

def kv(lines, key):
    """first RESULT-style token key=value among lines, as float (or None)"""
    for l in lines:
        m = re.search(r'(?<![\w.])' + re.escape(key) + r'=([-+0-9.eE]+)', l)
        if m: return float(m.group(1))
    return None

def corner_T(label):
    m = re.match(r'[a-z]+_(typical|ff|ss)_(-?\d+)', label)
    return m.group(1), int(m.group(2))

def r0(corner, T):
    for row in csv.reader(open(os.path.join(SIM, 'char_pseudoR.csv')), delimiter=' '):
        if row[0] == corner and row[1] == str(T) and row[3] == '2u' and abs(float(row[4]) - 0.2) < 1e-9:
            return float(row[5])
S = []
def w(s=''): S.append(s)
ORD = {'typical': 0, 'ff': 1, 'ss': 2}
def sk(l): c, T = corner_T(l); return (ORD[c], T)

# ---------------- op
op = blocks('op'); rows = []
w('A3 summary (typical flicker, fnoicor=0 unless stated).  Source logs: sim/a3_*.log.  OTA sizing: sim/../spice/ota1_params.spice')
w()
w('== 1. .op at VCM_IN = 1.5 V (unity follower).  margin = |Vds|-|Vdsat| of the WORST transistor [V]; criterion >= 0.05 V')
w('corner   T   worst_margin_V  worst_dev  gm/Id_pair  gm/Id_load  offset_uV  Isupply_uA')
for l in sorted(op, key=sk):
    c, T = corner_T(l); devs = {}
    for ln in op[l]:
        m = re.match(r'OPDEV (\w+) ', ln)
        if m: devs[m.group(1)] = dict(margin=kv([ln], 'margin_V'), gmid=kv([ln], 'gm_over_id'))
    wd = min(devs, key=lambda d: devs[d]['margin'])
    off = kv(op[l], 'offset_V'); ic = kv(op[l], 'i_supply_A')
    w(f"{c:8s} {T:4d}  {devs[wd]['margin']:8.3f}      {wd:6s}   {devs['xm1']['gmid']:6.1f}     {devs['xm3']['gmid']:6.1f}    {off*1e6:8.1f}   {ic*1e6:7.2f}")
    rows.append([c, T, devs[wd]['margin'], wd, devs['xm1']['gmid'], devs['xm3']['gmid'], off, ic])
with open(os.path.join(SIM, 'a3_op.csv'), 'w') as f:
    f.write('corner T_C worst_margin_V worst_dev gm_id_pair gm_id_load offset_V isupply_A\n')
    for r in rows: f.write(' '.join(str(x) for x in r) + '\n')
ic_ = blocks('icmr'); l = list(ic_)[0]
w(f"OTA follower range with every transistor >= 50 mV in saturation and |err| < 5 mV (typ 27C): {kv(ic_[l],'ICMR_lo_V'):.2f} to {kv(ic_[l],'ICMR_hi_V'):.2f} V")

# ---------------- open loop and loop gain
ol = blocks('ol'); lp = blocks('loop')
w(); w('== 2. Open loop (A(s), DC servo, load = Cf + CL_NEXT 2 pF PLACEHOLDER) and the REAL loop (Tian, real Cf/Cin/Randles)')
w('corner   T   A0_dB  f_p1_Hz  GBW_MHz  PM(beta=1)_deg | T(100Hz)_dB  fu_kHz  PM_deg   [target (derived): A0 >= 70 dB, PM >= 60 deg]')
rows = []
for l in sorted(ol, key=sk):
    c, T = corner_T(l); a = ol[l]; b = lp['loop_%s_%d' % (c, T)]
    r = [c, T, kv(a, 'a0_dB'), kv(a, 'f_p1_Hz'), kv(a, 'gbw_Hz'), kv(a, 'pm_beta1_deg'), kv(b, 'T_100Hz_dB'), kv(b, 'fu_Hz'), kv(b, 'pm_deg')]
    rows.append(r)
    w(f"{c:8s} {T:4d}  {r[2]:6.1f} {r[3]:7.1f}  {r[4]/1e6:6.2f}   {r[5]:7.1f}      | {r[6]:6.1f}      {r[7]/1e3:6.0f}   {r[8]:6.1f}")
with open(os.path.join(SIM, 'a3_ol_loop.csv'), 'w') as f:
    f.write('corner T_C a0_dB f_p1_Hz gbw_Hz pm_beta1_deg T100_dB fu_Hz pm_deg\n')
    for r in rows: f.write(' '.join(str(x) for x in r) + '\n')

# ---------------- closed loop AC with the pseudo-resistor device
cl = blocks('cl')
w(); w('== 3. Closed loop, REAL pseudo-resistor devices (vt=+0.2 V IDEAL shifter, 1u/2u), Randles source, stage 1 only')
w('corner   T   gain_mid_dB  f_lo_Hz  f_hi_kHz  vout_err_uV  Isupply_uA   [stage-1 nominal gain 40 dB; f_lo target <= 0.5 Hz]')
rows = []
for l in sorted(cl, key=sk):
    c, T = corner_T(l); a = cl[l]
    r = [c, T, kv(a, 'g_mid_dB'), kv(a, 'f_lo_Hz'), kv(a, 'f_hi_Hz'), kv(a, 'vout_err_V'), kv(a, 'i_supply_A')]
    rows.append(r)
    w(f"{c:8s} {T:4d}   {r[2]:7.3f}    {r[3]:7.3f}  {r[4]/1e3:7.0f}   {r[5]*1e6:9.2f}   {r[6]*1e6:8.2f}")
with open(os.path.join(SIM, 'a3_cl.csv'), 'w') as f:
    f.write('corner T_C gain_mid_dB f_lo_Hz f_hi_Hz vout_err_V isupply_A\n')
    for r in rows: f.write(' '.join(str(x) for x in r) + '\n')

# ---------------- noise per corner (IDEAL RESISTOR (noise) = R0)
nz = blocks('noise')
w(); w('== 4. Input-referred noise 0.5-300 Hz = integrated output noise / midband gain.  IDEAL RESISTOR (noise) of value R0 (Decision 8).')
w('corner   T   R0_TOhm   fn0_uV   fn1_uV   (fn1/fn0)   fn0 0.5-2k_uV   fn0 0.5-1M_uV   [target <= 2 uV at fn0; fn1 is a risk, Decision 4]')
rows = []
for l in sorted({k.rsplit('_fn', 1)[0] for k in nz}, key=sk):
    c, T = corner_T(l); a0 = nz[l + '_fn0']; a1 = nz[l + '_fn1']
    r = [c, T, r0(c, T), kv(a0, 'vn_in_mid_V'), kv(a1, 'vn_in_mid_V'), kv(a0, 'vn_in_ngspice_V')]
    k2 = [x for x in a0 if x.startswith('NOISE_C')]; k3 = [x for x in a0 if x.startswith('NOISE_D')]
    r += [kv(k2, 'vn_in_mid_V'), kv(k3, 'vn_in_mid_V')]
    rows.append(r)
    w(f"{c:8s} {T:4d}  {r[2]/1e12:7.2f}   {r[3]*1e6:6.3f}   {r[4]*1e6:6.3f}    {r[4]/r[3]:5.2f}       {r[6]*1e6:7.3f}        {r[7]*1e6:8.2f}")
with open(os.path.join(SIM, 'a3_noise.csv'), 'w') as f:
    f.write('corner T_C R0_ohm vn_in_mid_fn0_V vn_in_mid_fn1_V vn_in_ngspice_fn0_V vn_0p5_2k_V vn_0p5_1M_V\n')
    for r in rows: f.write(' '.join(str(x) for x in r) + '\n')

# ---------------- R sweep (Decision 7)
rs = blocks('rsweep'); Rs = sorted({float(re.search(r'_R([-+0-9.e]+)$', k).group(1)) for k in rs})
w(); w('== 5. Feedback-resistance sweep (Decision 7): IDEAL resistor R (both sides), typical 27C, Cf = 200 fF, Cin = 20 pF, real OTA')
w('R_TOhm  f_lo_Hz  tau=1/(2pi f_lo)_s | noise_fn0_uV  noise_fn1_uV  noise_Rnoiseless_uV  R-only_uV | rec(1mV step): t10mV_s t1mV_s dc_shift_mV | rec(10mV): t10mV_s t1mV_s dc_shift_mV')
rows = []
for R in Rs:
    tag = ('%g' % R).replace('+', '')
    g = lambda pre: rs['%s_R%s' % (pre, ('%g' % R).replace('+', ''))] if ('%s_R%s' % (pre, ('%g' % R).replace('+', ''))) in rs else None
    def find(pre):
        for k in rs:
            if k.startswith(pre + '_R') and abs(float(k.split('_R')[1]) - R) / R < 1e-9: return rs[k]
    ac, n0, n1, nr, r1, r10 = find('ac'), find('n0'), find('n1'), find('nr0'), find('rec1'), find('rec10')
    flo = kv(ac, 'f_lo_Hz'); v0 = kv(n0, 'vn_in_mid_V'); v1 = kv(n1, 'vn_in_mid_V'); vr = kv(nr, 'vn_in_mid_V')
    ronly = math.sqrt(max(v0 ** 2 - vr ** 2, 0))
    row = [R, flo, 1 / (2 * math.pi * flo), v0, v1, vr, ronly,
           kv(r1, 't_rec_10mV_s'), kv(r1, 't_rec_1mV_s'), kv(r1, 'dc_shift_V'), kv(r1, 'settled'),
           kv(r10, 't_rec_10mV_s'), kv(r10, 't_rec_1mV_s'), kv(r10, 'dc_shift_V'), kv(r10, 'settled'), kv(r10, 'vout_min_V')]
    rows.append(row)
    w(f"{R/1e12:6.2f}  {flo:7.3f}   {row[2]:6.2f}      |  {v0*1e6:6.3f}       {v1*1e6:6.3f}        {vr*1e6:6.3f}         {ronly*1e6:6.3f}   |   {row[7]:6.2f}  {row[8]:6.2f}  {row[9]*1e3:7.3f}      |   {row[11]:6.2f}  {row[12]:6.2f}  {row[13]*1e3:7.3f}   {'' if row[10] and row[14] else '(NOT SETTLED)'}")
with open(os.path.join(SIM, 'a3_rsweep.csv'), 'w') as f:
    f.write('R_ohm f_lo_Hz tau_s noise_fn0_V noise_fn1_V noise_Rnoiseless_V noise_Ronly_V rec1_t10_s rec1_t1_s rec1_dc_V rec1_settled rec10_t10_s rec10_t1_s rec10_dc_V rec10_settled rec10_vout_min_V\n')
    for r in rows: f.write(' '.join(str(x) for x in r) + '\n')
# interpolate: R needed for total <= 2 uV (fn0) and the f_lo/tau there
def interp_target(rows, col, tgt):
    for a, b in zip(rows, rows[1:]):
        if (a[col] - tgt) * (b[col] - tgt) <= 0:
            la, lb = math.log(a[0]), math.log(b[0]); f = (tgt - a[col]) / (b[col] - a[col])
            return math.exp(la + f * (lb - la))
Rn = interp_target(rows, 3, 2e-6)
if Rn:
    flo_n = 1 / (2 * math.pi * Rn * 200e-15)
    w(f"-> total noise (fn0) crosses 2.00 uV at R ~ {Rn/1e12:.2f} TOhm (log interpolation), i.e. f_lo ~ {flo_n:.2f} Hz (from 1/(2 pi R Cf), Cf = 200 fF)")

# ---------------- device recovery
rc = blocks('rec')
w(); w('== 6. Recovery with the REAL pseudo-resistor device (nonlinear), REC electrode offset step; stage-1 output time to settle to FINAL value')
w('corner   T  step_mV  excursion_V  vout_min_V  dc_shift_mV  t_to_10mV_s  t_to_1mV_s  settled')
rows = []
for l in sorted(rc, key=lambda k: (ORD[k.split('_')[1]], int(k.split('_')[2]), float(k.split('_')[3].replace('m', '')))):
    c, T = l.split('_')[1], int(l.split('_')[2]); st = l.split('_')[3]; a = rc[l]
    r = [c, T, st, kv(a, 'dv_max_V'), kv(a, 'vout_min_V'), kv(a, 'dc_shift_V'), kv(a, 't_rec_10mV_s'), kv(a, 't_rec_1mV_s'), kv(a, 'settled')]
    rows.append(r)
    w(f"{c:8s} {T:4d}  {st:>5s}   {r[3]:8.3f}    {r[4]:7.3f}    {r[5]*1e3:8.3f}    {r[6]:8.2f}    {r[7]:8.2f}     {int(r[8])}")
with open(os.path.join(SIM, 'a3_rec.csv'), 'w') as f:
    f.write('corner T_C step excursion_V vout_min_V dc_shift_V t10_s t1_s settled\n')
    for r in rows: f.write(' '.join(str(x) for x in r) + '\n')

# ---------------- CL sensitivity
cs = blocks('clsens')
w(); w('== 7. Sensitivity to the stage-2 input capacitance placeholder CL_NEXT (typical 27C)')
w('CL_NEXT   fu_kHz  PM_deg  f_hi_kHz  gain_mid_dB')
for CL in ['0.5p', '1p', '2p', '5p', '10p']:
    a = cs['loop_CL' + CL]; b = cs['ac_CL' + CL]
    w(f"{CL:6s}   {kv(a,'fu_Hz')/1e3:7.0f} {kv(a,'pm_deg'):7.1f} {kv(b,'f_hi_Hz')/1e3:8.0f}   {kv(b,'g_mid_dB'):7.3f}")

# ---------------- variants
vr = blocks('variants')
w(); w('== 8. Decision-5 load rows (typical 27C, R0 = %.2f TOhm ideal): NMOS load m x 50u/16u, second stage NMOS m = 2 x load m' % (r0('typical', 27) / 1e12))
w('load_m  noise_fn0_uV  noise_fn1_uV  PM_deg  fu_kHz  A0_dB  GBW_MHz  worst_margin_V  gate_area_um2')
for KN in (1, 2):
    n0 = vr['n0_KN%d' % KN]; n1 = vr['n1_KN%d' % KN]; lp_ = vr['loop_KN%d' % KN]; ol_ = vr['ol_KN%d' % KN]; o_ = vr['op_KN%d' % KN]
    mg = min(kv([x], 'margin_V') for x in o_ if x.startswith('OPDEV'))
    area = 16 * 50 * 2 + 2 * (50 * 4) + 2 * (50 * 4) * 0 + 2 * KN * 50 * 16 + 2 * KN * 50 * 16 + 2 * 50 * 4 * 3  # pair + tail/bias/M7 (50u/4u units) + M3/M4 + M6
    area = 16*50*2 + (2+2+2)*50*4 + 2*KN*50*16 + 2*KN*50*16
    w(f"{KN:4d}    {kv(n0,'vn_in_mid_V')*1e6:8.3f}      {kv(n1,'vn_in_mid_V')*1e6:8.3f}     {kv(lp_,'pm_deg'):6.1f}  {kv(lp_,'fu_Hz')/1e3:6.0f}  {kv(ol_,'a0_dB'):6.1f}  {kv(ol_,'gbw_Hz')/1e6:6.2f}   {mg:8.3f}      {area:6d}")
w(); w('== 9. xschem equivalence (scripts/equiv_xschem.sh, sim/a3_equiv_xschem.log) and Tian loop-break validation (sim/a3_tian_check.log)')
for fn in ('a3_equiv_xschem.log', 'a3_tian_check.log', 'a3_diag.log'):
    for ln in open(os.path.join(SIM, fn)):
        if ln.startswith(('EQUIV', 'CHECK', '.subckt', '###', 'RESULT')): w(ln.rstrip()[:170])
open(os.path.join(SIM, 'a3_summary.txt'), 'w').write('\n'.join(S) + '\n')
print('\n'.join(S))
