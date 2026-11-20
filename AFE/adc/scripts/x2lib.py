#!/usr/bin/env python3
"""X2 library: transistor-level amplifier -> ADC verification by CLOSED-LOOP PWL REPLAY (no SAR logic inside ngspice).

Replay principle (strategy 1 of the X2 prompt): the SAR decisions are computed in Python, the DAC driver / sampling TG / reset /
comparator-clock waveforms are written as PWL sources with the D3 RTL frame timing (rtl/adc_sar_ch.v: ADC i does trial t at SCLK
edge t+i, drivers released at edge 13+i, tracking resumes at edge 14+i) and the D3/D4 STA timing per corner (comparator clock of
ADC i rises T0 + i*Delta after the SCLK edge, width W; DAC edges arrive `arr` after the SCLK edge).  After each run the comparator
output is read at the capture instant of every trial; at the first trial of a conversion whose decision differs from the replayed
bit, that bit is corrected, the remaining bits are re-predicted from the MEASURED plate residue of that trial, and the netlist is
re-run.  A conversion is final when the 11 decisions that drive the DAC all equal the replayed bits (the 12th is only read), so
the code is the circuit's own code.

Process rules (strategy 4): every ngspice is started with Popen, its PID is kept and polled (no pgrep/pkill, no `timeout`
wrapper); at most NPAR = 3 at a time; scratch only in sim/.ptmp/x2_* (removed at exit); only named vectors are saved (.save +
binary `write`); disk and RAM are checked before each batch.
"""
import os, sys, re, subprocess, tempfile, shutil, atexit, time, random, numpy as np
H = os.path.dirname(os.path.abspath(__file__)); ADC = os.path.abspath(os.path.join(H, '..')); AFE = os.path.abspath(os.path.join(ADC, '..')); AMP = f'{AFE}/amp'
sys.path.insert(0, H)
from d2lib import Dac
PT = f'{ADC}/sim/.ptmp'; os.makedirs(PT, exist_ok=True)
NPAR = 3
# ngspice start-up file for every X2 job, written into the job directory (= ngspice's working directory), where ngspice looks first.
# WHY: in this container SPICE_USERINIT_DIR points to the PDK directory, whose .spiceinit is EMPTY, so ~/.spiceinit is never read and the system spinit applies: num_threads=8.  With these
# small netlists the 8 OpenMP threads of the BSIM4 loop cost 5-6x in WALL time (ADC alone, one conversion: 15.1 s -> 2.8 s; amplifier + ADC, 65 frames: 28 min -> 4.3 min).
# `.options num_threads=1` in the D2-D5 scripts is not an ngspice option and does nothing.
# X2_NGBEHAVIOR=hsa adds `set ngbehavior=hsa` (the line of ~/.spiceinit).  The project default is NO compatibility mode (every A/D-phase log says "No compatibility mode selected").
# The X2 runs made on 2026-11-19 after 21:57 used hsa by mistake; it changes nothing but round-off here (same DC operating point to 6 digits, same codes: X2 notes), so they were kept.
SPICEINIT = "set num_threads=1\n" + ("set ngbehavior=hsa\nset ng_nomodcheck\nset enable_noisy_r\n" if os.environ.get('X2_NGBEHAVIOR', '') == 'hsa' else '')
# X2_ADC_INC = colon-separated netlist files that REPLACE the simulation netlists of the ADC cell (they must define dac_sw, cmp_p, vhalf, vrefs with the same pin order): the LVS reference
# AFE/layout/lvs/adc_ch.spice (F1 check of mk_lvs_netlists.py) or, in L1b, the netlist extracted from the layout.  Empty = the design netlists of AFE/adc/spice.
ADC_INC = [os.path.abspath(f) for f in os.environ.get('X2_ADC_INC', '').split(':') if f]
NOV1 = float(os.environ.get('X2_NOV1', '0.3e-9'))      # trial 1 only: delay between the MSB driver (PMOS on) and the NMOS drivers of the 11 lower bits; design = 0.3 ns (D2 script); what-if for PROPOSAL P3
PRIO = float(os.environ.get('X2_YIELD', '0'))       # extra seconds a script waits after giving a slot back (larger = lower priority)
TR = 100e-12; NOV = 0.3e-9; CKSLEW = 0.2e-9; DCS = 1e-9; DINV = 0.15e-9; LEAD = 150e-9
# D3 STA (sim/d3_taps.log) + D4 DAC-edge arrival (latest), per digital corner.  dtg = one dlyd cell (3.4 ns tt, scaled with the chain ratio).
# ss_n40 arrival is an ESTIMATE (tt value x T0 ratio 65.58/45.86); the others are STA numbers from AFE/adc/NOTES.md D3/D4.
TIM = {'ff_n40': dict(T0=24.80e-9, DL=7.30e-9, W=3.2e-9, arr=3.777e-9, dtg=1.84e-9),
       'tt':     dict(T0=45.86e-9, DL=13.5e-9, W=5.9e-9, arr=6.301e-9, dtg=3.4e-9),
       'ss_n40': dict(T0=65.58e-9, DL=19.4e-9, W=8.5e-9, arr=9.01e-9, dtg=4.86e-9),
       'ss_125': dict(T0=95.89e-9, DL=28.4e-9, W=12.3e-9, arr=12.082e-9, dtg=7.1e-9)}
# analog corner key -> (model corner, tempC, VDD, digital timing corner)
COR = {'typ':   ('typical', 27, 3.3, 'tt'),
       'ff85':  ('ff', 85, 3.3, 'ff_n40'),      # fastest digital timing with the hot fast analog corner (D4b pairing)
       'ss-40': ('ss', -40, 3.3, 'ss_n40'),
       'ff-40': ('ff', -40, 3.6, 'ff_n40'),     # D4 supply corners (STA-matched VDD)
       'ss125': ('ss', 125, 3.0, 'ss_125')}
NSVRS = {('typical', 27): 1.02771, ('ff', 85): 1.22173, ('ss', -40): 0.813879, ('ff', -40): 1.04386, ('ss', 125): 1.05}

# ---------------------------------------------------------------- job runner (PID based)
_tmpdirs = []
def scratch(tag):
    d = tempfile.mkdtemp(prefix=f'x2_{tag}_', dir=PT); _tmpdirs.append(d)
    return d
def _cleanup():
    for d in _tmpdirs: shutil.rmtree(d, ignore_errors=True)
atexit.register(_cleanup)
def resources():
    st = os.statvfs(ADC); free_gb = st.f_bavail * st.f_frsize / 2**30
    mem = {l.split(':')[0]: int(l.split()[1]) for l in open('/proc/meminfo') if ':' in l}
    return free_gb, mem['MemAvailable'] / 1024
def check_resources(min_gb=4.0, min_mb=1200):
    g, m = resources()
    if g < min_gb: raise SystemExit(f'STOP: only {g:.1f} GB free on the design disk')
    t0 = time.time()
    while m < min_mb and time.time() - t0 < 300: time.sleep(5); g, m = resources()
    if m < min_mb: raise SystemExit(f'STOP: only {m:.0f} MB RAM available')
    return g, m
# machine-wide limit of NPAR ngspice processes across ALL x2 scripts: a slot = a directory in sim/.ptmp created atomically (mkdir) by the holder, with the holder's PID inside
_seen = {}
def _slot_take():
    """returns the slot directory or None.  A slot whose pid file names a dead process is reclaimed; a slot without a readable pid file is treated as busy (reclaimed only after this
    process has seen it in that state for 90 s of its own monotonic clock: file times on the host mount are not compared with the container clock)."""
    for i in range(NPAR):
        d = f'{PT}/x2_slot{i}.d'
        try:
            os.mkdir(d)
        except FileExistsError:
            try: pid = int(open(f'{d}/pid').read().strip() or 0)
            except (OSError, ValueError): pid = None
            if pid:
                _seen.pop(d, None)
                if not os.path.exists(f'/proc/{pid}'): shutil.rmtree(d, ignore_errors=True)
            else:
                t0 = _seen.setdefault(d, time.monotonic())
                if time.monotonic() - t0 > 90: shutil.rmtree(d, ignore_errors=True); _seen.pop(d, None)
            continue
        except OSError:
            continue
        try:
            with open(f'{d}/pid', 'w') as f: f.write(str(os.getpid()))
            return d
        except OSError:
            continue
    return None
def _slot_free(d): shutil.rmtree(d, ignore_errors=True)
_slots = []
atexit.register(lambda: [_slot_free(d) for d in _slots])
def run_jobs(jobs, npar=NPAR, wall=3600.0, tag='j', log=None):
    """jobs: list of (name, netlist_text_with_@RAW@).  Runs ngspice -b by PID, at most npar at a time.
    Returns {name: dict(ok, raw, log, wall, tail)}; the raw files live in a scratch dir (removed at exit or by the caller)."""
    check_resources(); d = scratch(tag); todo = list(jobs); run = []; res = {}; yielded = False
    open(f'{d}/.spiceinit', 'w').write(SPICEINIT)          # read by ngspice from its working directory: ONE thread (see SPICEINIT)
    while todo or run:
        if yielded:                      # fairness between scripts: after giving a slot back, let the processes that are waiting for one poll first
            time.sleep(1.0 + 1.5 * random.random() + PRIO); yielded = False
        while todo and len(run) < npar:
            slot = _slot_take()
            if slot is None: break
            _slots.append(slot)
            name, net = todo.pop(0); fn = f'{d}/{name}.spice'; raw = f'{d}/{name}.raw'; lg = f'{d}/{name}.log'
            open(fn, 'w').write(net.replace('@RAW@', raw))
            p = subprocess.Popen(['ngspice', '-b', fn], cwd=d, stdout=open(lg, 'w'), stderr=subprocess.STDOUT, env=dict(os.environ, OMP_NUM_THREADS='1'))
            run.append((p, name, raw, lg, time.time(), slot))
        time.sleep(0.3)
        for r in list(run):
            p, name, raw, lg, t0, slot = r
            if p.poll() is None:
                if time.time() - t0 > wall: p.kill(); p.wait()
                else: continue
            run.remove(r); _slot_free(slot); _slots.remove(slot); yielded = True
            txt = open(lg, errors='replace').read().replace('\r', '\n'); tail = ' | '.join(l.strip()[:300] for l in txt.split('\n') if re.search(r'imestep too small|trouble with|ingular|aborted|rror', l))[:900]
            ok = os.path.exists(raw) and os.path.getsize(raw) > 500
            res[name] = dict(ok=ok, raw=raw, log=lg, wall=time.time() - t0, tail=tail, dir=d)
            if log: log(f'   job {name}: pid {p.pid} exit {p.returncode} wall {time.time()-t0:.0f} s' + (f' MSG {tail}' if tail else ''))
    return res
def read_raw(path):
    buf = open(path, 'rb').read(); i = buf.find(b'Binary:\n'); hdr = buf[:i].decode(errors='replace')
    nv = int(re.search(r'No. Variables:\s*(\d+)', hdr).group(1)); npt = int(re.search(r'No. Points:\s*(\d+)', hdr).group(1))
    names = [l.split()[1].lower() for l in hdr.split('Variables:\n')[1].strip().split('\n')]
    a = np.frombuffer(buf, dtype='<f8', offset=i + 8, count=nv * npt).reshape(npt, nv)
    return names, a
class Wave:
    def __init__(self, path):
        self.names, self.a = read_raw(path); self.t = self.a[:, 0]
    def v(self, name): return self.a[:, self.names.index(name.lower())]
    def at(self, name, t): return np.interp(t, self.t, self.v(name))
    @property
    def tend(self): return self.t[-1]

# ---------------------------------------------------------------- control waveforms
def pwl_src(name, node, ref, ev, v0, tr=TR, kind='V'):
    pts = [(0.0, v0)]; prev = v0
    for t, v in sorted(ev, key=lambda x: x[0]):
        if v == prev: continue
        t = max(t, pts[-1][0] + 1e-13)
        pts += [(t, prev), (t + tr, v)]; prev = v
    return f'{kind}{name} {node} {ref} PWL(' + ' '.join(f'{t:.13e} {v:.5g}' for t, v in pts) + ')'
def sclk_edge(tcs, e, T, lead=LEAD): return tcs + lead + (e - 1) * T          # time of SCLK rising edge number e (1-based) of the frame that starts at tcs
def schedule(adcs, tcs, bits, tim, T, vdd, ref='0', resume_last=True, lead=LEAD):
    """adcs = number of ADCs (indices 0..n-1) or a list of ADC indices (index i = position in the D3 stagger: trial t at SCLK edge t+i, comparator clock at T0 + i*Delta).
    bits[p][f] = 12 replayed decisions (trial 1 = MSB) of the p-th listed ADC.  Returns (list of source lines, meta; meta arrays are indexed by p).  Node names: rst<i> sam<i> samb<i> gdn<i> ck<i> gp<i>_<b> gn<i>_<b>."""
    if isinstance(adcs, int): adcs = list(range(adcs))
    nadc = len(adcs)
    nf = len(tcs); lines = []; meta = dict(tck=np.zeros((nadc, nf, 12)), tcap=np.zeros((nadc, nf, 12)), tsamp=np.zeros(nf), tres=np.zeros((nadc, nf)), tdac=np.zeros((nadc, nf, 12)), trel=np.zeros((nadc, nf)), adcs=list(adcs))
    for p_, a in enumerate(adcs):
        ev = {}; ck = [(0.0, 0.0)]
        def add(n, t, v): ev.setdefault(n, []).append((t, v))
        for f, t0 in enumerate(tcs):
            b = bits[p_][f]; tro = t0 + DCS; meta['tsamp'][f] = tro + TR / 2
            add('rst', tro, 0.0); tto = tro + tim['dtg']; add('sam', tto, 0.0); add('samb', tto + DINV, vdd); add('gdn', tto + DINV, vdd)
            for k in range(1, 13):
                te = sclk_edge(t0, a + k, T, lead); tk = te + tim['arr']; j = 12 - k; meta['tdac'][p_, f, k - 1] = tk
                if k == 1:
                    add('gp11', tk, 0.0)
                    for bb in range(11): add(f'gn{bb}', tk + NOV1, vdd)
                else:
                    add(f'gn{j}', tk, 0.0); add(f'gp{j}', tk + NOV, 0.0)
                    if not b[k - 2]: add(f'gp{j+1}', tk, vdd); add(f'gn{j+1}', tk + NOV, vdd)
                tc = te + tim['T0'] + a * tim['DL']; ck += [(tc, 0.0), (tc + CKSLEW, vdd), (tc + tim['W'], vdd), (tc + tim['W'] + CKSLEW, 0.0)]
                meta['tck'][p_, f, k - 1] = tc; meta['tcap'][p_, f, k - 1] = tc + tim['W']
            trel = sclk_edge(t0, a + 13, T, lead) + tim['arr']; meta['trel'][p_, f] = trel
            for bb in range(12): add(f'gp{bb}', trel, vdd); add(f'gn{bb}', trel, 0.0)
            tres = sclk_edge(t0, a + 14, T, lead) + tim['arr']; meta['tres'][p_, f] = tres
            if resume_last or f < nf - 1:
                add('rst', tres, vdd); add('sam', tres + tim['dtg'], vdd); add('samb', tres + tim['dtg'] + DINV, 0.0); add('gdn', tres + tim['dtg'] + DINV, 0.0)
        ini = dict(rst=vdd, sam=vdd, samb=0.0, gdn=0.0); ini.update({f'gp{b}': vdd for b in range(12)}); ini.update({f'gn{b}': 0.0 for b in range(12)})
        for n in ['rst', 'sam', 'samb', 'gdn'] + [f'gp{b}' for b in range(12)] + [f'gn{b}' for b in range(12)]:
            node = f'{n}{a}' if not n.startswith('g') or n == 'gdn' else f'{n[:2]}{a}_{n[2:]}'
            lines.append(pwl_src(node, node, ref, ev.get(n, []), ini[n]))
        lines.append(f'Vck{a} ck{a} {ref} PWL(' + ' '.join(f'{t:.13e} {v:.5g}' for t, v in ck) + ')')
    return lines, meta

# ---------------------------------------------------------------- netlist pieces
def header(ck, title, amp=True, gmin='1e-16', opts='', abstol='1e-12'):
    """abstol 1e-12 (ngspice default), NOT the 1e-15 of D2-D5: see X2 S2 (the 1e-15 A branch-current tolerance is the cause of the 'timestep too small' aborts; the amplifier alone is unchanged to < 0.05 uV)"""
    corner, temp, vdd, _ = COR[ck]
    L = [f'* X2 {title} ({ck}: {corner} {temp} C, VDD {vdd} V)  generated by scripts/x2lib.py' + (f'  ADC CELL NETLISTS REPLACED BY {ADC_INC}' if ADC_INC else ''), f'.include {AMP}/spice/models_{corner}.spice']
    if amp:
        L += [f'.include {AMP}/spice/{f}.spice' for f in ('pseudoR', 'ota1_params', 'afe_params', 'a4c_params', 'ota1', 'ota2', 'bias_genc', 'stage1c', 'stage2c', 'afe_chc')]
        L += [f'.param NSVRS={NSVRS[(corner, temp)]}']
    L += [f'.include {f}' for f in ADC_INC] if ADC_INC else [f'.include {ADC}/spice/{f}.spice' for f in ('dac_units', 'dac_sw', 'comparator_params', 'comparator', 'vhalf')]
    L += [f'.options gmin={gmin} abstol={abstol} reltol=1e-4 vntol=1e-7 chgtol=1e-17 itl1=500 itl4=500 {opts}', f'.temp {temp}']
    return L
def supply(vdd, model=None, dig=None):
    """model None: ideal rails (nodes vm = vd = vdd source, vssi = 0).  model = dict(Rp, Lp, Cm, Cd, Rs, Rd): one VDD/VSS pad pair (Rp + Lp EACH, ASSUMED), main rail vm (decap Cm + ESR Rd), DAC strap vd through Rs (decap Cd + ESR Rd)."""
    if model is None: return ['Vext vx 0 %g' % vdd, 'Rvm vx vm 1m', 'Rvd vx vd 1m', 'Rvs vssi 0 1m']
    m = model
    L = ['Vext vx 0 %g' % vdd, f'Rpv vx vxl {m["Rp"]}', f'Lpv vxl vm {m["Lp"]}', f'Rpg vssi vsl {m["Rp"]}', f'Lpg vsl 0 {m["Lp"]}',
         f'Cm vm cmx {m["Cm"]}', f'Rdm cmx vssi {m["Rd"]}', f'Rs vm vd {m["Rs"]}', f'Cd vd cdx {m["Cd"]}', f'Rdd cdx vssi {m["Rd"]}']
    if m.get('Cpad'): L += [f'Cpadv vm 0 {m["Cpad"]}', f'Cpadg vssi 0 {m["Cpad"]}']     # pad / ESD capacitance of the two supply pads to the board ground (ASSUMED).  Without it NOTHING but the two pad
    # inductors ties the on-chip island (rails, ideal inputs, gate sources: all referenced to vssi) to node 0, and an ideal inductor is an open circuit at very small time steps: the common mode of
    # the island is then singular and a run can die with 'Timestep too small ... trouble with node vm' (4 of the first 9 eight-ADC runs of X2 S4).
    if m.get('Rlp'): L += [f'Rlpv vxl vm {m["Rlp"]}', f'Rlpg vsl 0 {m["Rlp"]}']        # optional loss resistor across each pad inductor (numerical aid: at very small steps an ideal L is an open circuit)
    if dig: L.append(dig)
    return L
def adc_cell(a, vin, vmain='vm', vdac='vd', vss='vssi', ref='cref', vana=None, vtg=None):
    """ref = 'cref' (design: vhalf divider + Cref behind the TG, Decision 42), 'tied' (cmp_p.inp on the vhalf node, I1), 'ideal' (IDEAL VDD/2 source on dac_sw.vcm and cmp_p.inp, the D2/D4b condition)
    SUPPLY PINS (F1, Decision 44d, AUDIT 4.9.2): the chip cell has vdd (analog strap: vhalf, Cref switch, n-wells of the 13 sampling TGs), vdd_cmp (ADC-main strap: cmp_p) and vdd_dac (ADC-DAC strap: the
    13 bottom-plate drivers).  The DEFAULT here is the X2 S4 / S5 partition, kept so that every X2 result stays reproducible: vmain = cmp_p.vdd_cmp AND vhalf AND the Cref switch (the less favourable
    case: they see the comparator droop), vdac = dac_sw.vdd_dac AND dac_sw.vdd (the sampling-TG n-wells) AND gdp.  vana / vtg give the chip partition when a run needs it (L3b on the extracted straps):
    vana = node of vhalf and the Cref switch (default vmain), vtg = node of the sampling-TG n-wells (default vdac)."""
    vana = vana or vmain; vtg = vtg or vdac
    gp = ' '.join(f'gp{a}_{b}' for b in range(12)); gn = ' '.join(f'gn{a}_{b}' for b in range(12))
    rf = {'cref': [f'Xvh{a} vcmd{a} {vana} {vss} vhalf', f'Xvr{a} vcmd{a} ci{a} sam{a} samb{a} {vana} {vss} vrefs'],
          'tied': [f'Xvh{a} vcmd{a} {vana} {vss} vhalf', f'Vci{a} ci{a} vcmd{a} 0'],
          'ideal': [f'Ehalf{a} vcmd{a} {vss} {vmain} {vss} 0.5', f'Vci{a} ci{a} vcmd{a} 0']}[ref]
    return [f'* ---- ADC {a}: vhalf + sampled floating reference (Cref) + sampling TG / split DAC / drivers + cmp_p   (afe_ch wiring: rstm = rst, gdp tied high (to vdd_dac), samb/gdn = ~tg_on; dac_sw pins ... vcm vdd vdd_dac vss ...)'] + rf + [
            f'Xs{a} {vin} t{a} m{a} vcmd{a} {vtg} {vdac} {vss} rst{a} rst{a} sam{a} samb{a} {gp} {vdac} {gn} gdn{a} dac_sw',
            f'Xc{a} ci{a} t{a} ck{a} cq{a} cqn{a} {vmain} {vss} cmp_p', f'Cl1_{a} cq{a} {vss} 5f', f'Cl2_{a} cqn{a} {vss} 5f']
def bias(vdd='vm', vss='vssi'):
    return [f'Xbias vbn vcm vg1 vcmo vg2 vrs {vdd} {vss} bias_genc',
            '.nodeset v(vrs)={NSVRS} v(vbn)=0.65 v(xbias.a)=2.4 v(vcm)=1.65 v(vg1)=1.85 v(vcmo)=1.65 v(vg2)=2.55']
def amp_channel(c, src_lines, vdd='vm', vss='vssi', tgate=False):
    """one afe_chc on the shared bias; electrode = Randles network from node es<c> (driven by src_lines) to rec<c>; REF is the shared node `ref` (dbs_afe_top: REF pad -> afe_chc.ref of every channel).
    Park TG off (pkc = 0, pkcb = VDD: routing switch closed), fs = 0 (no reset pulse).  tgate=True puts the 5 V routing TGATE (closed) between the electrode pad and rec."""
    x = f'xch{c}'
    L = [f'* ---- channel {c}: electrode -> afe_chc'] + src_lines
    if tgate: L += [f'Rse{c} es{c} e{c} 1k', f'Cdl{c} e{c} epad{c} 300n', f'Rct{c} e{c} epad{c} 50k', f'Xtg{c} rec{c} {vdd} {vss} epad{c} {vdd} {vss} TGATE']
    else: L += [f'Rse{c} es{c} e{c} 1k', f'Cdl{c} e{c} rec{c} 300n', f'Rct{c} e{c} rec{c} 50k']
    L += [f'Vfs{c} fs{c} {vss} 0', f'Vpkc{c} pkc{c} {vss} 0', f'Epkcb{c} pkcb{c} {vss} {vdd} {vss} 1',
          f'Xch{c} rec{c} ref out{c} {vdd} {vss} vbn vcm vg1 vcmo vg2 vrs fs{c} pkc{c} pkcb{c} afe_chc',
          f'.nodeset v({x}.gm1)=1.85 v({x}.gm2)=2.55 v({x}.xs1.vn)=1.65 v({x}.xs1.vp)=1.65 v({x}.xs1.vng)=1.65 v({x}.v1)=1.65 v({x}.xs1.xota.o1)=0.78 v({x}.xs1.xota.d1)=0.78 v({x}.xs1.xota.tail)=2.55 v({x}.ibias1)=2.4',
          f'.nodeset v({x}.xs1.xr1.m)=1.65 v({x}.xs1.xr2.m)=1.65 v({x}.xs2.xr.m)=1.65 v({x}.xs2.vn2)=1.65 v({x}.xs2.vng2)=1.65 v(out{c})=1.65 v({x}.xs2.xota2.o2)=2.45 v({x}.xs2.xota2.d1)=2.6 v({x}.xs2.xota2.tail)=1.0']
    return L
def ref_electrode():
    return ['* shared reference electrode (REF pad): Randles network to the IDEAL tissue node', 'Vtis tis 0 1.65', 'Rsr tis er 1k', 'Cdlr er ref 300n', 'Rctr er ref 50k']
def tail(saves, tstop, tmax, tstep='1n', extra_ctl=()):
    return ['.save ' + ' '.join(saves), f'.tran {tstep} {tstop:.9e} 0 {tmax}', '.control', 'set filetype=binary', 'run'] + list(extra_ctl) + ['write @RAW@', 'quit', '.endc', '.end']

# ---------------------------------------------------------------- SAR model used only to PREDICT the replayed bits
_W = Dac().weights()[0]          # nominal bit weights (sum with the dummy = 1): V_plate step = alpha * VDD * w_j
class Cal:
    """per-corner calibration of the bit PREDICTOR (it never decides a code: every decision comes from the simulated comparator).
    x = plate - reference node just before the comparator clock.  keep <=> x < theta(P), theta(P) = theta + gw . bits(P): the decision threshold on x depends on the DAC state P of the trial
    (which bottoms are held by a PMOS / an NMOS driver: X2 S1 finding); gw is learned from the simulated decisions (logistic regression, refit()).  alpha = plate attenuation, c0 = x offset of trial 1."""
    def __init__(self, vdd, alpha=0.98, theta=-29.0 * 3.3 / 4096):
        self.vdd, self.alpha, self.theta = vdd, alpha, theta; self.lo = -1e9; self.hi = 1e9; self.obs = []; self.c0 = 0.0; self.gw = np.zeros(12); self.fitinfo = ''
    @property
    def lsb(self): return self.vdd / 4096
    def theta_of(self, pat): return self.theta + float(self.gw @ ((pat >> np.arange(12)) & 1))
    def observe(self, x, dec, pat=0):
        if dec and x > self.lo: self.lo = x
        if (not dec) and x < self.hi: self.hi = x
        if abs(x - self.theta) < 8 * self.lsb: self.obs.append((x, dec, pat))
        if self.lo > -1e8 and self.hi < 1e8 and self.lo < self.hi and not self.gw.any(): self.theta = 0.5 * (self.lo + self.hi)
    def refit(self, lam=0.02):
        """theta0 + per-bit threshold weights from all near-threshold observations: regularised logistic regression (scale 0.15 LSB)"""
        if len(self.obs) < 30: return
        from scipy.optimize import minimize
        o = np.array(self.obs, float); x = o[:, 0] / self.lsb; s = np.where(o[:, 1] > 0.5, 1.0, -1.0); B = ((o[:, 2].astype(int)[:, None] >> np.arange(12)) & 1).astype(float)
        def f(p):
            z = s * (p[0] + B @ p[1:] - x) / 0.15; return np.sum(np.logaddexp(0, -z)) + lam * len(x) * np.sum(p[1:] ** 2)
        r = minimize(f, np.r_[self.theta / self.lsb, self.gw / self.lsb], method='BFGS'); p = r.x
        bad0 = int(np.sum((x < self.theta / self.lsb) != (s > 0))); bad1 = int(np.sum((x < p[0] + B @ p[1:]) != (s > 0)))
        if bad1 <= bad0:
            self.theta = p[0] * self.lsb; self.gw = p[1:] * self.lsb
        self.fitinfo = f'{len(x)} decisions within 8 LSB of the threshold: misclassified by a constant threshold {bad0}, by the bit-dependent threshold {bad1}; theta0 {p[0]:+.2f} LSB, per-bit shift b11..b0 [LSB] ' + ' '.join(f'{v:+.2f}' for v in p[1:][::-1])
    def guess_bits(self, vin):
        """SAR on the predicted input with the modelled thresholds (first pass only)"""
        x = self.c0 + self.alpha * (self.vdd / 2 - vin); bits = []; acc = 0
        for k in range(1, 13):
            j = 12 - k; pat = acc | (1 << j)
            if k > 1: x = x + self.alpha * self.vdd * (_W[j] - (0.0 if bits[-1] else _W[j + 1]))
            d = int(x < self.theta_of(pat)); bits.append(d)
            if d: acc = pat
        return bits
    def predict_rest(self, x, k, d, prefix=()):
        """x = measured residue of trial k (1-based), d = its decision, prefix = decisions of trials 1..k-1; returns the predicted decisions of trials k+1..12"""
        acc = 0
        for i, b in enumerate(list(prefix)[:k - 1]):
            if b: acc |= 1 << (11 - i)
        if d: acc |= 1 << (12 - k)
        out = []
        for kk in range(k, 12):
            j = 12 - kk                     # bit tested at trial kk; the next trial tests bit j-1
            x = x + self.alpha * self.vdd * (_W[j - 1] - (0.0 if d else _W[j])); pat = acc | (1 << (j - 1))
            d = int(x < self.theta_of(pat)); out.append(d)
            if d: acc = pat
        return out
def code_of(bits):
    c = 0
    for b in bits: c = (c << 1) | int(b)
    return c
class Exp:
    """one closed-loop replay experiment: nadc ADC cells x nf frames.  build(ctrl_lines, meta) -> netlist text.  vin_guess[a][f] = predicted input for the first pass."""
    def __init__(self, name, ck, nadc, tcs, T, build, vin_guess, cal, resume_last=True, ref='0', vdd=None, adcs=None, cals=None):
        """nadc ADC cells; adcs = their indices (default 0..nadc-1); cal = shared predictor calibration, cals = optional per-ADC list"""
        self.name, self.ck, self.nadc, self.tcs, self.T, self.build, self.cal = name, ck, nadc, list(tcs), T, build, cal
        self.adcs = list(adcs) if adcs is not None else list(range(nadc)); self.cals = cals or [cal] * nadc
        self.vdd = vdd or COR[ck][2]; self.tim = TIM[COR[ck][3]]; self.nf = len(tcs); self.resume_last = resume_last; self.ref = ref
        self.bits = [[self.cals[a].guess_bits(vin_guess[a][f]) for f in range(self.nf)] for a in range(nadc)]
        self.done = False; self.npass = 0; self.x = np.full((nadc, self.nf, 12), np.nan); self.dec = np.zeros((nadc, self.nf, 12), int); self.unres = np.zeros((nadc, self.nf, 12), int)
        self.failed = None; self.wave = None; self.meta = None; self.nfix = 0
    def netlist(self):
        lines, self.meta = schedule(self.adcs, self.tcs, self.bits, self.tim, self.T, self.vdd, ref=self.ref, resume_last=self.resume_last)
        return self.build(lines, self.meta)
    def absorb(self, r):
        self.npass += 1
        if not r['ok']: self.failed = r['tail'] or 'no raw file'; self.done = True; return
        w = Wave(r['raw']); m = self.meta; tlast = m['tcap'].max()
        if w.tend < tlast: self.failed = f'run ended at {w.tend:.6e} s < last capture {tlast:.6e} s: {r["tail"]}'; self.done = True; return
        self.wave = w; allok = True; self.pending = []
        for a, ia in enumerate(self.adcs):
            cal = self.cals[a]
            vt = w.v(f'v(t{ia})'); vc = w.v(f'v(ci{ia})'); q = w.v(f'v(cq{ia})'); qn = w.v(f'v(cqn{ia})')
            if self.ref != '0': vr = w.v(f'v({self.ref})'); q = q - vr; qn = qn - vr
            for f in range(self.nf):
                b = self.bits[a][f]
                for k in range(1, 13):
                    tc = m['tck'][a, f, k - 1]; tcap = m['tcap'][a, f, k - 1]
                    x = np.interp(tc - 0.1e-9, w.t, vt) - np.interp(tc - 0.1e-9, w.t, vc)
                    qp = np.interp(tcap - 0.05e-9, w.t, q); qm = np.interp(tcap - 0.05e-9, w.t, qn); d = int(qp > self.vdd / 2)
                    self.x[a, f, k - 1] = x; self.dec[a, f, k - 1] = d; self.unres[a, f, k - 1] = int(qp > self.vdd / 2 and qm > self.vdd / 2)
                    pat = (code_of(b[:k - 1]) << (13 - k)) | (1 << (12 - k)); cal.observe(x, d, pat)
                    if d != b[k - 1]:
                        b[k - 1] = d
                        if k < 12:
                            self.pending.append((a, f, k, x, d)); allok = False; self.nfix += 1
                            self.x[a, f, k:] = np.nan
                        break
        self.done = allok
    def repredict(self):
        """after the predictor was refitted on this pass: re-predict the bits after each first mismatch from the measured residue of that trial"""
        for a, f, k, x, d in getattr(self, 'pending', []):
            b = self.bits[a][f]; b[k:] = self.cals[a].predict_rest(x, k, d, b[:k - 1])
        self.pending = []
    def codes(self): return np.array([[code_of(self.bits[a][f]) for f in range(self.nf)] for a in range(self.nadc)])
def closed_loop(exps, npar=NPAR, maxpass=10, wall=3600.0, log=print, tag='cl', keep_wave=True):
    """iterate all experiments to self-consistency.  Returns the list (each with .codes(), .x, .dec, .wave of the final pass)."""
    for p in range(maxpass):
        todo = [e for e in exps if not e.done]
        if not todo: break
        t0 = time.time(); res = run_jobs([(e.name, e.netlist()) for e in todo], npar=npar, wall=wall, tag=tag)
        for e in todo:
            e.absorb(res[e.name])
            if not keep_wave or not e.done:
                e.wave = None
            try: os.remove(res[e.name]['raw'])
            except OSError: pass
        seen = []
        for e in todo:
            for c in e.cals:
                if not any(c is q for q in seen): seen.append(c); c.refit()
        for e in todo: e.repredict()
        g, mm = resources()
        log(f'   pass {p+1}: {len(todo)} runs in {time.time()-t0:.0f} s, still open {sum(1 for e in exps if not e.done)}, failed {sum(1 for e in exps if e.failed)}; disk {g:.1f} GB, RAM {mm:.0f} MB free' + (f' | predictor: {seen[0].fitinfo}' if seen and seen[0].fitinfo else ''))
    for e in exps:
        if not e.done: e.failed = e.failed or f'not self-consistent after {maxpass} passes'
    return exps
