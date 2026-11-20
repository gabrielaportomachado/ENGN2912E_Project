#!/usr/bin/env python3
"""A4a/A4b (TAG=a4b): collect the full-channel logs (sim/a4a_{op,ac,acfs,ol2,psrr,noise}.log) into sim/a4a_summary.txt (9 PVT tables)."""
import re, os
import os
TAG = os.environ.get('TAG', 'a4a')
A = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'sim') + '/'
combos = [(k, t) for k in ('typical', 'ff', 'ss') for t in ('-40', '27', '85')]
def parse(path):
    d, cur = {}, None
    for l in open(path):
        if l.startswith('###'): cur = l[4:].strip(); d[cur] = []
        elif cur: d[cur].append(l.strip())
    return d
def kv(lines, tag=None): return {k: float(v) for l in lines if tag is None or l.startswith(tag) for k, v in re.findall(r'(\w+)=(-?\d+\.?\d*(?:[eE][-+]?\d+)?)', l)}
out = []
def P(s=''): out.append(s)
P(('A4a' if TAG == 'a4a' else 'A4b (re-run of the A4a tables with the A4b netlist: native-Vt follower, VCM_IN = 1.65 V, VTT2 per spice/afe_params.spice)') + ' full channel (stage 1 + stage 2 + follower buffer + REAL bias_gen), typical/ff/ss x -40/27/85 C, VDD 3.3 V, VOUT_CM 1.65 V.  Source: sim/' + TAG + '_*.log')
P('Models: MOS corner + mimcap corner + poly-resistor corner (res_<corner>: ppolyf_u_1k 1000/800/1200 Ohm/sq since F1; the saved A4a / A4b tables were made with ppolyf_u_3k, 3000/2250/3750 Ohm/sq).  Diffusion real (DIFF=1).  ADC load: ' + ('placeholder 10 pF' if TAG == 'a4a' else '20 fF off-channel mux load only (D0 model; the 17 pF / 1 kOhm sampling event is in a4b_adc.log)') + '.')
P()
op = parse(A + TAG + '_op.log')
P('== 1. .op: DC levels and bias (every transistor margin = |Vds|-|Vdsat| of the analog devices; criterion >= 0.05 V; start-up/ladder not listed)')
P('corner   T  vout_err_mV  vcmo_V  vn1-v1_mV  worst_margin_V(device)       IBIAS1_uA  Isupply_uA  follower_Id_uA  OTA2_tail_nA')
for k, t in combos:
    L = op[f'op_{k}_{t}']; s = kv(L, 'OPSUM'); n = kv(L, 'OPNODE')
    dev = [(float(re.search(r'margin_V=(\S+)', l).group(1)), l.split()[1]) for l in L if l.startswith('OPDEV')]
    w = min(dev)
    idd = {l.split()[1]: float(re.search(r'id_A=(\S+)', l).group(1)) for l in L if l.startswith('OPDEV')}
    P(f'{k:8s} {t:>4s} {s["vout_err_V"]*1e3:10.2f} {s["vcmo_V"]:8.4f} {(n["vn1_V"]-n["v1_V"])*1e3:9.1f}   {w[0]:7.3f} ({w[1].replace("xch.","")[:18]:18s}) {s["ibias1_A"]*1e6:8.2f} {s["i_supply_A"]*1e6:10.2f}  {idd["xch.xs2.xota2.xmf"]*1e6:10.2f}  {idd["xch.xs2.xota2.xmt"]*1e9:12.2f}')
P()
ac = parse(A + TAG + '_ac.log'); acfs = parse(A + TAG + '_acfs.log')
P('== 2. .ac, simulated pseudo-resistors, fast-settle OPEN.  Targets: gain 60 +-1 dB (T2), f_lo <= 0.5 Hz, f_hi >= 300 Hz (T3)')
P('corner   T  gain_12Hz_dB  stage1_dB  stage2_dB  peak_dB  f_lo_Hz  f_hi_Hz  gain@300Hz_dB  phase_deg')
for k, t in combos:
    r = kv(ac[f'ac_{k}_{t}'], 'RESULT')
    P(f'{k:8s} {t:>4s} {r["g_mid_dB"]:11.3f} {r["g1_mid_dB"]:10.3f} {r["g_mid_dB"]-r["g1_mid_dB"]:9.3f} {r["g_pk_dB"]:8.3f} {r["f_lo_Hz"]:8.3f} {r["f_hi_Hz"]:8.1f} {r["g_300_dB"]:11.3f}  {r["ph_mid_deg"]:8.2f}')
P()
P('== 3. .ac with the fast-settle transmission gates CLOSED (fs = 3.3 V): the amplifier must stay stable and the passband collapses to a DC reset (f_lo up to the MHz range)')
P('corner   T  gain_12Hz_dB  peak_dB  f_lo_Hz  f_hi_Hz')
for k, t in combos:
    L = acfs[f'acfs_{k}_{t}']
    r = kv(L, 'RESULT')
    P(f'{k:8s} {t:>4s} ' + (f'{r["g_mid_dB"]:11.2f} {r["g_pk_dB"]:8.2f} {r.get("f_lo_Hz", float("nan")):9.4g} {r.get("f_hi_Hz", float("nan")):9.4g}' if r else ' '.join(L)[:100]))
P()
ol = parse(A + TAG + '_ol2.log')
P('== 4. Stage-2 OTA open loop A(s) (DC servo, load CF2 + 10 pF): loop PM with beta = 1 is the worst case; closed-loop f_H = beta*GBW')
P('corner   T  A0_dB  f_p1_Hz  GBW_Hz  PM(beta=1)_deg')
for k, t in combos:
    r = kv(ol[f'ol2_{k}_{t}'], 'RESULT')
    P(f'{k:8s} {t:>4s} {r["a0_dB"]:6.2f} {r["f_p1_Hz"]:8.2f} {r["gbw_Hz"]:8.1f} {r["pm_beta1_deg"]:8.2f}')
P()
ps = parse(A + TAG + '_psrr.log')
P('== 5. Supply rejection (Decision 17b): |v(out)/v(vdd)| in V/V; ideal ratiometric tracking of the ADC mid-scale (VREF = VDD) is 0.5 V/V.  Input-referred: divide by 1000')
P('corner   T  dc     50Hz   60Hz   300Hz   1kHz   10kHz')
for k, t in combos:
    r = kv(ps[f'psrr_{k}_{t}'], 'RESULT')
    P(f'{k:8s} {t:>4s} {r["vdd2out_dc"]:6.3f} {r["vdd2out_50Hz"]:6.3f} {r["vdd2out_60Hz"]:6.3f} {r["vdd2out_300Hz"]:6.3f} {r["vdd2out_1k"]:6.3f} {r["vdd2out_10k"]:6.3f}')
P()
nz = parse(A + TAG + '_noise.log')
P('== 6. Input-referred noise = integrated OUTPUT noise / midband gain.  IDEAL RESISTOR (noise) = R0 in both stages (Decision 8).  Target <= 2 uV (0.5-300 Hz, typical flicker fn0)')
P('corner   T  R0_TOhm  fn0_0.5-300Hz_uV  stage1_only_fn0_uV  fn1_0.5-300Hz_uV  (fn1/fn0)  fn0_0.5-2k_uV  fn0_0.5-1M_uV')
R0 = {}
for l in open(A + 'a4a_prfg.csv').read().splitlines()[1:]:
    f = l.split()
    if f[2] == '1.5' and f[3] == '0.2' and f[4] == '0': R0[(f[0], f[1])] = float(f[5]) / 1e12
for k, t in combos:
    a = nz[f'noise_{k}_{t}_fn0']; b = nz[f'noise_{k}_{t}_fn1']
    g = lambda L, tag, key: kv(L, tag)[key] * 1e6
    P(f'{k:8s} {t:>4s} {R0[(k,t)]:7.2f} {g(a,"NOISE_B","vn_in_mid_V"):14.3f} {g(a,"NOISE_S1","vn_in_stage1_V"):18.3f} {g(b,"NOISE_B","vn_in_mid_V"):16.3f} {g(b,"NOISE_B","vn_in_mid_V")/g(a,"NOISE_B","vn_in_mid_V"):9.2f} {g(a,"NOISE_C","vn_in_mid_V"):13.3f} {g(a,"NOISE_D","vn_in_mid_V"):13.3f}')
open(A + TAG + '_summary.txt', 'w').write('\n'.join(out) + '\n'); print('\n'.join(out))
