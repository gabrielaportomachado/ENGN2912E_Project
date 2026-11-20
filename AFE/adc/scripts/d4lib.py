#!/usr/bin/env python3
"""D4 mixed-signal testbench generator + runner.
Digital = the synthesized D3 netlist as XSPICE gate-level (spice/dig/adc8_<libcorner>.inc, per-instance SDF delays; ivlng is not usable in this ngspice build);
analog = PDK transistor-level DAC (dac_units + dac_sw) + cmp_p per ADC, bridged with adc_bridge / dac_bridge.  Everything under tb-less generation: text netlist written to a temp file in sim/.ptmp.
"""
import os, sys, re, subprocess, tempfile, shutil, atexit, numpy as np
H = os.path.dirname(os.path.abspath(__file__)); ADC = os.path.abspath(os.path.join(H, '..')); sys.path.insert(0, H)
PT = f'{ADC}/sim/.ptmp'; os.makedirs(PT, exist_ok=True)
LIBC = {'typical': 'tt_025C_3v30', 'ff': 'ff_n40C_3v60', 'ss': 'ss_125C_3v00'}      # digital delay corner paired with each analog corner
def pwl(name, pts, kind='V', n1=None, n2='0'):
    return f'{kind}{name} {n1 or name} {n2} PWL(' + ' '.join(f'{t:.5e} {v:.5g}' for t, v in pts) + ')'
def frames_ctl(tfr, nedge, per, t_cs0=2e-6, lead=0.15e-6, vsup=3.3, tr=0.2e-9):
    """CS / SCLK / RSTN / DIN waveforms for len(tfr) frames.  tfr[k] = start time of frame k (CS falls), nedge SCLK rising edges at lead + (j+0.5)*per; CS rises half a period after the last edge."""
    cs = [(0, vsup)]; sc = [(0, 0.0)]; ends = []
    for t0 in tfr:
        cs += [(t0, vsup), (t0 + tr, 0.0)]
        for j in range(nedge):
            te = t0 + lead + j * per
            sc += [(te, 0.0), (te + tr, vsup), (te + per / 2, vsup), (te + per / 2 + tr, 0.0)]
        tend = t0 + lead + nedge * per; cs += [(tend, 0.0), (tend + tr, vsup)]; ends.append(tend)
    return cs, sc, ends
def build(o):
    """o: dict of options -> netlist text.  Keys: corner, temp, vsup, nadc (analog ADCs, 1..8), vins (list per frame of list per ADC), per (SCLK period), nedge, mism (python Dac or None), noise (dict) , supply (dict), probes"""
    corner, T, vsup, nadc = o['corner'], o['temp'], o['vsup'], o.get('nadc', 1)
    per = o['per']; nedge = o.get('nedge', 14 if nadc == 1 else 22); vins = o['vins']; nfr = len(vins)
    lead = 0.15e-6; tgap = o.get('tgap', 1.2e-6); tfr = []; t = o.get('t0', 2e-6)
    for k in range(nfr): tfr.append(t); t += lead + nedge * per + tgap
    tstop = t; cs, sc, ends = frames_ctl(tfr, nedge, per, lead=lead, vsup=vsup)
    libc = o.get('libc') or LIBC[corner]
    mimfile = {'typical': 'models_typical_mim', 'ff': 'models_ff_mim', 'ss': 'models_ss_mim'}[corner]
    L = [f'* D4 mixed-signal testbench ({corner}, {T} C, VDD {vsup} V, digital {libc}, {nadc} analog ADC(s), {nfr} frames)']
    L += [f'.include {ADC}/spice/{mimfile}.spice', f'.include {o.get("dacfile") or ADC + "/spice/dac_units.spice"}', f'.include {ADC}/spice/dac_sw.spice', f'.include {ADC}/spice/comparator_params.spice', f'.include {ADC}/spice/comparator.spice']
    if o.get('cmp_noise'): L.append(f'.include {o["cmp_noise"]}')
    L += [f'.options gmin=1e-12 reltol={o.get("reltol", "1e-4")} abstol=1e-15 vntol=1e-7 chgtol=1e-17 itl1=500 itl4=500', f'.temp {T}', f'.param VSUP={vsup}']
    # ---- supply
    sp = o.get('supply', {})
    vxsrc = sp.get('vx')            # optional PWL points for a rippled / noisy source
    L.append(pwl('x', vxsrc, 'V', 'vx') if vxsrc else f'Vx vx 0 {vsup}')
    if sp.get('lcr'):
        r = sp['lcr']; Rp, Lp, Cm, Cd, Rs, Rdm, Rdd = r['Rp'], r['L'], r['Cm'], r['Cd'], r['Rs'], r['Rdm'], r['Rdd']
        L += [f'Rp vx vl {Rp}', f'Lp vl vm {Lp}', f'Cm vm cmx {Cm}', f'Rdm cmx 0 {Rdm}', f'Rs vm vd {Rs}', f'Cd vd cdx {Cd}', f'Rdd cdx 0 {Rdd}']
        L.append(f'.ic v(vm)={vsup} v(vd)={vsup} v(vl)={vsup} v(cmx)={vsup} v(cdx)={vsup}')
        for j, ex in enumerate(sp.get('extra_main', [])): L.append(ex)
        for ex in sp.get('extra_dac', []): L.append(ex)
    else:
        L += ['Rv1 vx vm 1u', 'Rv2 vx vd 1u']
    L.append(f'Bvcm vcm 0 V=V(vm)/2' if sp.get('vcm_track', True) else f'Vcm vcm 0 {vsup/2}')
    # ---- digital block + bridges
    L.append(f'.include {ADC}/spice/dig/adc8_{libc}.inc')
    L.append('.model adcb adc_bridge(in_low={0:.4g} in_high={1:.4g})'.format(0.45 * vsup, 0.55 * vsup))
    L.append(f'.model dacb dac_bridge(out_low=0 out_high={vsup} t_rise=0.1n t_fall=0.1n)')
    L += [pwl('cs', cs, 'V', 'cs_a'), pwl('sclk', sc, 'V', 'sclk_a'), f'Vrst rstn_a 0 PWL(0 0 0.4u 0 0.41u {vsup})', 'Vdin din_a 0 0', 'Vz zr 0 0', f'Vo one 0 {vsup}']
    L += ['Abc [cs_a] [d_cs_n] adcb', 'Abs [sclk_a] [d_sclk] adcb', 'Abr [rstn_a] [d_rstn] adcb', 'Abd [din_a] [d_din] adcb', 'Abz [zr] [zero_d] adcb', 'Abo [one] [one_d] adcb']
    for i in range(8):
        if i >= nadc: L.append(f'Atie{i} zero_d d_cmp_q{i} bufq')
    L.append('.model bufq d_buffer(rise_delay=1p fall_delay=1p)')
    # ---- per-ADC analog
    for i in range(nadc):
        L.append(f'* ---- ADC {i}')
        gp = ' '.join(f'd_dac_gp{12*i+b}' for b in range(12)); gn = ' '.join(f'd_dac_gn{12*i+b}' for b in range(12))
        L.append(f'Adrv{i}p [{gp}] [{" ".join(f"gp{i}_{b}" for b in range(12))}] dacb')
        L.append(f'Adrv{i}n [{gn}] [{" ".join(f"gn{i}_{b}" for b in range(12))}] dacb')
        L.append(f'Actl{i} [d_rst_sw{i} d_tg_on{i} d_cmp_clk{i}] [rst{i} sam{i} ck{i}] dacb')
        L.append(f'Ainv{i} d_tg_on{i} d_tgb{i} inv_d'); L.append(f'Abb{i} [d_tgb{i}] [samb{i}] dacb')   # samb = ~sam
        L.append(f'Adum{i} [d_tgb{i}] [gdn{i}] dacb')      # dummy-unit bottom: grounded whenever the TG is off (D3 has no dummy-bit driver; added here, see NOTES D4)
        L.append(f'Vgdp{i} gdp{i} 0 {vsup}')
        # DAC
        L.append(f'Xs{i} vin{i} t{i} m{i} vcm vd vd 0 rst{i} rst{i} sam{i} samb{i} ' + ' '.join(f'gp{i}_{b}' for b in range(12)) + f' gdp{i} ' + ' '.join(f'gn{i}_{b}' for b in range(12)) + f' gdn{i} dac_sw')
        vi = [v[i] if isinstance(v, (list, tuple, np.ndarray)) else v for v in vins]
        pts = [(0, vi[0])]
        for k, tf in enumerate(tfr):
            pts += [(tf - 0.6e-6, vi[max(k - 1, 0)]), (tf - 0.5e-6, vi[k])]
        L.append(pwl(f'vin{i}', pts, 'V', f'vin{i}'))
        # comparator: plate t -> inn, reference vcm -> inp (D3 convention); optional noise sources in series with the plate (pair + kTC of the sampling)
        nz = o.get('noise')
        inn = f't{i}'
        if nz and nz.get('inn'):
            L.append(pwl(f'nin{i}', nz['inn'][i], 'V', f'nin{i}', f'nin{i}b')); L.append(f'Rnn{i} nin{i}b 0 1e12'.replace('nin%db 0 1e12' % i, 'nin%db 0 1e12' % i))
            L[-2] = pwl(f'nin{i}', nz['inn'][i], 'V', f'ncn{i}', f't{i}')   # series source: ncn = t + noise
            inn = f'ncn{i}'
        cell = 'cmp_p'
        if nz and nz.get('cell'): cell = nz['cell']
        extra = ''
        if nz and nz.get('cell'): extra = ' ' + ' '.join(nz['pins'](i))
        L.append(f'Xc{i} vcm {inn} ck{i} cq{i} cqn{i} vm 0{extra} {cell}')
        L += [f'Cl1_{i} cq{i} 0 5f', f'Cl2_{i} cqn{i} 0 5f']
        L.append(f'Aq{i} [cq{i}] [d_cmp_q{i}] adcb')
        L.append(f'Cwp{i} t{i} 0 {o.get("cpar_t", "0")}')
        L.append(f'Ccin{i} t{i} 0 70f' if False else '')
        for b in range(12): pass
        L.append(f'Acode{i} [' + ' '.join(f'n_ch_{i}__u_code_{b}_' for b in range(12)) + '] [' + ' '.join(f'qc{i}_{b}' for b in range(12)) + '] dacb')
        L.append(f'Adone{i} [d_cmp_clk{i}] [ckd{i}] dacb')
    for k, nm in enumerate(o.get('dbg', [])): L.append(f'Adbg{k} [{nm}] [x_{nm}] dacb')
    L.append('.model inv_d d_inverter(rise_delay=1p fall_delay=1p inertial_delay=false)')
    # ---- output
    sv = ['v(vd)', 'v(vm)'] + [f'v(qc{i}_{b})' for i in range(nadc) for b in range(11, -1, -1)] + [f'v(t{i})' for i in range(nadc)] + [f'v(ck{i})' for i in range(nadc)] + [f'v(cq{i})' for i in range(nadc)]
    sv += [f'v(x_{nm})' for nm in o.get('dbg', [])]; sv += [f'i(Vx)'] + o.get('save_extra', [])
    L.append(f'.tran {o.get("tstep", "0.5u")} {tstop:.6e} 0 {o.get("tmax", "0.1n")}')
    L += ['.control', 'run', f'wrdata {o["out"]} ' + ' '.join(sv), 'quit', '.endc', '.end']
    info = dict(tfr=tfr, ends=ends, tstop=tstop, per=per, nedge=nedge, names=sv, nadc=nadc)
    return '\n'.join(l for l in L if l) + '\n', info
def run(o, tag, timeout=1700, keep=False):
    tmp = tempfile.mkdtemp(prefix='d4_', dir=PT); atexit.register(shutil.rmtree, tmp, True)
    o = dict(o, out=f'{tmp}/o.csv'); txt, info = build(o)
    open(f'{tmp}/n.spice', 'w').write(txt)
    r = subprocess.run(['ngspice', '-b', f'{tmp}/n.spice'], capture_output=True, text=True, timeout=timeout)
    if not os.path.exists(f'{tmp}/o.csv'): return None, info, r.stdout[-1500:] + r.stderr[-500:]
    a = np.loadtxt(f'{tmp}/o.csv'); shutil.rmtree(tmp, True)
    return a, info, r.stdout[-300:]
def col(a, info, name):
    return a[:, 1 + 2 * info['names'].index(name)]
def codes(a, info, adc=0, vsup=3.3):
    """code of ADC <adc> at the end of each frame (value of the 12 code flops 0.5 us after the last edge: the flops hold until the next frame)"""
    t = a[:, 0]; out = []
    for te in info['ends']:
        i = np.searchsorted(t, te + 0.2e-6); c = 0
        for b in range(11, -1, -1): c = (c << 1) | int(col(a, info, f'v(qc{adc}_{b})')[i] > vsup / 2)
        out.append(c)
    return out
