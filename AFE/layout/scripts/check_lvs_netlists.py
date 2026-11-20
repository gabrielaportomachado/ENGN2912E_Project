#!/usr/bin/env python3
"""check_lvs_netlists.py (F1): checks of the LVS reference netlists that mk_lvs_netlists.py wrote to AFE/layout/lvs/.  They are netlists a layout will be matched against, so they are
tested as CIRCUITS, not only as text:
  A. ngspice, typ 27 C: bias_genc + afe_chc of the LVS reference (flat, numeric, no ideal element, Cin in pieces) against the simulation netlists in the same testbenches
     (AFE/amp/tb/tb_a4c_op.spice, tb_a4c_ac.spice).  Three runs each: SIM = the design netlists as simulated (DIFF = 1), SIM0 = the design netlists with the diffusion parameters off
     (.param DIFF=0: the LVS reference carries no ad / as / pd / ps, the PDK default is 0), LVS = the reference.  LVS must equal SIM0; SIM0 against SIM shows what the dropped parameters are worth.
  B. ngspice, typ 27 C: the ADC cells of the LVS reference (dac_sw, cmp_p, vhalf, vrefs of adc_ch.spice: Cxa = one 5 x 5 um MIM unit instead of the ideal 40 fF, no Cpb / Cpm) in the X2
     closed-loop replay (AFE/adc/scripts/x2_adc.py with X2_ADC_INC), 12 inputs, against the X2 baseline block of AFE/adc/sim/x2_adc.log.  A FUNCTIONAL check: the flat cells must convert,
     with one uniform code shift.  The shift is NOT the effect of the rule substitutions alone: the reference also carries no diffusion parameters (junction capacitances), which the layout
     will have.  The effect of Cxa alone is measured separately on the design netlists (AFE/adc/sim/f1_x2_inl_step.log, `.param CMP_CA=54.52f`).
  C. netgen -batch (run by PID with a time limit): every file is read and its top cell compared with itself (syntax, device classes, pin lists, the black box, the 0-ohm ties).
usage: python3 check_lvs_netlists.py [A] [B] [C]     (default: all)   -> AFE/layout/lvs/check_lvs_netlists.log; scratch AFE/layout/.ptmp/lvschk (removed at the end)"""
import os, re, sys, subprocess, time, shutil
HERE = os.path.dirname(os.path.abspath(__file__))
LAY = os.path.normpath(os.path.join(HERE, '..'))
AFE = os.path.normpath(os.path.join(LAY, '..'))
REPO = os.path.normpath(os.path.join(AFE, '..'))
AMP, ADC, LVS = os.path.join(AFE, 'amp'), os.path.join(AFE, 'adc'), os.path.join(LAY, 'lvs')
PT = os.path.join(LAY, '.ptmp', 'lvschk')
NG = '/foss/tools/ngspice/bin/ngspice'
NETGEN_SETUP = '/foss/pdks/gf180mcuD/libs.tech/netgen/gf180mcuD_setup.tcl'
OUT = []


def P(*a):
    s = ' '.join(str(x) for x in a)
    print(s, flush=True)
    OUT.append(s)


def run_ng(jobs, npar=3, wall=1200.0):
    """jobs [(name, netlist text)] -> {name: stdout+stderr}; one thread per job (job-local .spiceinit), by PID, no cut, no timeout wrapper"""
    os.makedirs(PT, exist_ok=True)
    open(os.path.join(PT, '.spiceinit'), 'w').write('set num_threads=1\n')
    todo, run, res = list(jobs), [], {}
    while todo or run:
        while todo and len(run) < npar:
            name, net = todo.pop(0)
            fn, lg = os.path.join(PT, name + '.spice'), os.path.join(PT, name + '.log')
            open(fn, 'w').write(net)
            run.append((subprocess.Popen([NG, '-b', fn], cwd=PT, stdout=open(lg, 'w'), stderr=subprocess.STDOUT, env=dict(os.environ, OMP_NUM_THREADS='1')), name, lg, time.time()))
        time.sleep(0.2)
        for r in list(run):
            p, name, lg, t0 = r
            if p.poll() is None:
                if time.time() - t0 > wall:
                    p.kill()
                    p.wait()
                else:
                    continue
            run.remove(r)
            res[name] = open(lg, errors='replace').read().replace('\r', '\n')
    return res


def kv(txt, key):
    d = {}
    for ln in txt.split('\n'):
        if ln.startswith(key + ' '):
            tag = ln.split()[1] + '.' if key == 'OPDEV' else ''
            for k, v in re.findall(r'(\w+)=(\S+)', ln):
                try:
                    d[tag + k] = float(v)
                except ValueError:
                    pass
    return d


def flat_names(s):
    """hierarchical simulation names below the channel instance xch -> names of the flat LVS cell (mk_lvs_netlists.py: path joined with `_`); vng / vng2 no longer exist (joined with vn / vn2)"""
    def f(m):
        parts = m.group(1).split('.')
        tail = ''
        if parts[-1] == 'm0':
            parts, tail = parts[:-1], '.m0'
        return 'xch.' + '_'.join(parts) + tail
    s = re.sub(r'xch\.([\w.]+)', f, s)
    return s.replace('xch.xs1_vng)', 'xch.xs1_vn)').replace('xch.xs2_vng2)', 'xch.xs2_vn2)')


def amp_tb(tb, variant):
    t = open(os.path.join(AMP, 'tb', tb)).read()
    t = t.replace('../spice/', AMP + '/spice/').replace('../../../TGATE/', REPO + '/TGATE/')
    if variant == 'SIM0':
        t = re.sub(r'^(\.temp .*)$', r'\1\n.param DIFF=0', t, count=1, flags=re.M)
    if variant == 'LVS':
        for f in ('pseudoR', 'ota1', 'ota2', 'bias_genc', 'stage1c', 'stage2c', 'afe_chc'):
            a = '.include %s/spice/%s.spice\n' % (AMP, f)
            if t.count(a) != 1:
                sys.exit('check_lvs_netlists: include of %s not found in %s' % (f, tb))
            t = t.replace(a, '')
        t = re.sub(r'^(\.temp .*)$', r'.include %s/afe_chc.spice\n.include %s/bias_genc.spice\n\1' % (LVS, LVS), t, count=1, flags=re.M)
        t = flat_names(t)
    return t


def part_a():
    P('\nA. bias_genc + afe_chc: LVS reference against the simulation netlists, ngspice-46, typ 27 C, 3.3 V  (SIM = design netlists; SIM0 = the same with .param DIFF=0; LVS = AFE/layout/lvs)')
    jobs = [('%s_%s' % (tb[:-6], v), amp_tb(tb, v)) for tb in ('tb_a4c_op.spice', 'tb_a4c_ac.spice') for v in ('SIM', 'SIM0', 'LVS')]
    res = run_ng(jobs)
    ok = True
    op = {v: res['tb_a4c_op_' + v] for v in ('SIM', 'SIM0', 'LVS')}
    ac = {v: kv(res['tb_a4c_ac_' + v], 'RESULT') for v in ('SIM', 'SIM0', 'LVS')}
    s = {v: kv(op[v], 'OPSUM') for v in op}
    n = {v: kv(op[v], 'OPNODE') for v in op}
    d = {v: {k.replace('xs1_xota_', 'xs1.xota.').replace('xs2_xota2_', 'xs2.xota2.'): x for k, x in kv(op[v], 'OPDEV').items()} for v in op}
    for v in op:
        if not s[v] or not ac[v] or not d[v]:
            err = ' | '.join(l.strip()[:160] for l in (op[v] + res['tb_a4c_ac_' + v]).split('\n') if re.search(r'rror|ingular|no such|unknown|too small', l, flags=re.I))[:900]
            P('  %s: run FAILED: %s' % (v, err))
            ok = False
    if not ok:
        return False
    P('  .op   %-14s %14s %14s %14s | %12s %12s' % ('quantity', 'SIM', 'SIM0', 'LVS', 'LVS - SIM0', 'SIM0 - SIM'))
    worst_v, worst_i = 0.0, 0.0
    for k, unit, sc in (('vout_V', 'V', 1), ('vbn_V', 'V', 1), ('vcm_V', 'V', 1), ('vg1_V', 'V', 1), ('vcmo_V', 'V', 1), ('vg2_V', 'V', 1), ('i_supply_A', 'uA', 1e6), ('ibias1_A', 'uA', 1e6)):
        a, b, c = s['SIM'][k] * sc, s['SIM0'][k] * sc, s['LVS'][k] * sc
        P('        %-14s %14.6f %14.6f %14.6f | %+12.6f %+12.6f %s' % (k, a, b, c, c - b, b - a, unit))
        if unit == 'V':
            worst_v = max(worst_v, abs(c - b))
        else:
            worst_i = max(worst_i, abs(c / b - 1))
    for k in ('v1_V', 'vn1_V', 'vp1_V', 'vn2_V', 'o2_V'):
        a, b, c = n['SIM'][k], n['SIM0'][k], n['LVS'][k]
        P('        %-14s %14.6f %14.6f %14.6f | %+12.6f %+12.6f V' % (k, a, b, c, c - b, b - a))
        worst_v = max(worst_v, abs(c - b))
    ids = sorted(k for k in d['SIM0'] if k.endswith('.id_A'))
    miss = [k for k in ids if k not in d['LVS']]
    wd = max((abs(d['LVS'][k] / d['SIM0'][k] - 1), k) for k in ids if k in d['LVS'])
    ws = max((abs(d['SIM0'][k] / d['SIM'][k] - 1), k) for k in ids)
    P('        drain currents of %d transistors (every MOS of bias_genc and afe_chc with a DC current): LVS vs SIM0 worst %.2e relative (%s); SIM0 vs SIM worst %.2e (%s); missing in the LVS run: %s' % (
        len(ids), wd[0], wd[1][:-5], ws[0], ws[1][:-5], miss or 'none'))
    P('  .ac   %-14s %14s %14s %14s | %12s %12s' % ('quantity', 'SIM', 'SIM0', 'LVS', 'LVS - SIM0', 'SIM0 - SIM'))
    worst_g = 0.0
    worst_f = 0.0
    for k in ('g_mid_dB', 'g1_mid_dB', 'f_lo_Hz', 'f_hi_Hz', 'ph_mid_deg', 'g_300_dB', 'g_0p5_dB'):
        a, b, c = ac['SIM'][k], ac['SIM0'][k], ac['LVS'][k]
        P('        %-14s %14.5f %14.5f %14.5f | %+12.5f %+12.5f' % (k, a, b, c, c - b, b - a))
        if k.endswith('dB'):
            worst_g = max(worst_g, abs(c - b))
        if k.endswith('Hz'):
            worst_f = max(worst_f, abs(c / b - 1))
    good = worst_v <= 1e-4 and worst_i <= 1e-3 and wd[0] <= 1e-3 and not miss and worst_g <= 0.01 and worst_f <= 0.01
    P('  RESULT A: LVS reference vs the design netlists without diffusion parameters: DC nodes within %.1f uV, supply / bias currents within %.2e, device currents within %.2e, gains within %.4f dB, corner frequencies within %.2f %%  -> %s (limits 100 uV, 1e-3, 1e-3, 0.01 dB, 1 %%)' % (
        worst_v * 1e6, worst_i, wd[0], worst_g, worst_f * 100, 'PASS' if good else 'FAIL'))
    return good


def part_b():
    P('\nB. ADC cells of the LVS reference (adc_ch.spice: dac_sw, cmp_p, vhalf, vrefs) in the X2 closed-loop replay, ADC alone, typ 27 C, 12 inputs (x2_adc.py typ 12, X2_ADC_INC)')
    lg = os.path.join(PT, 'x2_adc_lvs.log')
    os.makedirs(PT, exist_ok=True)
    if os.path.exists(lg):
        os.remove(lg)
    env = dict(os.environ, X2_ADC_INC=os.path.join(LVS, 'adc_ch.spice'), X2_ADC_LOG=lg)
    p = subprocess.Popen([sys.executable, os.path.join(ADC, 'scripts', 'x2_adc.py'), 'typ', '12'], cwd=ADC, stdout=open(os.path.join(PT, 'x2_adc_lvs.out'), 'w'), stderr=subprocess.STDOUT, env=env)
    t0 = time.time()
    while p.poll() is None:
        if time.time() - t0 > 3600:
            p.kill()
        time.sleep(1)
    if not os.path.exists(lg):
        P('  run FAILED: ' + open(os.path.join(PT, 'x2_adc_lvs.out'), errors='replace').read()[-600:].replace('\n', ' | '))
        return False
    rx = re.compile(r'ADC typ cref vin ([\d.]+) code (\d+) ideal (\d+) diff \S+ \| T (\S+) LSB')
    new = {m.group(1): (int(m.group(2)), float(m.group(4))) for m in rx.finditer(open(lg).read())}
    base = {}
    for ln in open(os.path.join(ADC, 'sim', 'x2_adc.log')).read().split('\n')[:18]:          # the first block = x2_adc.py typ 12, design netlists (X2)
        m = rx.match(ln)
        if m:
            base[m.group(1)] = (int(m.group(2)), float(m.group(4)))
    if len(new) != 12 or set(new) != set(base):
        P('  run incomplete: %d of 12 conversions; %s' % (len(new), ' | '.join(l[:200] for l in open(lg).read().split('\n') if 'FAILED' in l)[:600]))
        return False
    P('  %-9s | %-10s %-10s %-6s | %-9s %-9s %-8s' % ('Vin [V]', 'code SIM', 'code LVS', 'diff', 'T SIM', 'T LVS', 'dT [LSB]'))
    dc, dt = [], []
    for v in sorted(new, key=float):
        dc.append(new[v][0] - base[v][0])
        dt.append(new[v][1] - base[v][1])
        P('  %-9s | %-10d %-10d %+6d | %+9.3f %+9.3f %+8.3f' % (v, base[v][0], new[v][0], dc[-1], base[v][1], new[v][1], dt[-1]))
    summ = [l for l in open(lg).read().split('\n') if l.startswith('SUMMARY')]
    P('  ' + (summ[0][:330] if summ else ''))
    spread = max(dt) - min(dt)
    good = max(abs(x) for x in dc) <= 4 and spread <= 0.5
    P('  RESULT B: every conversion converges; the flat LVS cells convert like the design netlists apart from ONE uniform shift: codes %+d .. %+d LSB, transition offset T %+.2f .. %+.2f LSB '
      '(spread over the 12 inputs %.2f LSB)  -> %s (limits: |code change| <= 4 LSB, spread <= 0.5 LSB)' % (min(dc), max(dc), min(dt), max(dt), spread, 'PASS' if good else 'FAIL'))
    P('  The shift has three causes: Cxa 40 fF ideal -> 54.52 fF MIM unit, the 14 x 2 fF Cpb / Cpm removed, and NO diffusion parameters in an LVS netlist (PDK default ad = as = pd = ps = 0).')
    P('  Separated on the design netlists (AFE/adc/sim/f1_x2_inl_step.log, typ): Cxa alone moves the code offset by +1.5 LSB, Cpb / Cpm by +0.1 LSB; the rest (about -3.4 LSB) is the missing junction capacitance.')
    shutil.copy(lg, os.path.join(LVS, 'check_x2_adc_lvs.log'))
    return good


def part_c():
    P('\nC. netgen -batch: each file read and its top cell compared with a copy of the same file (netgen does not compare two cells of one file); setup %s' % os.path.relpath(NETGEN_SETUP, '/foss/pdks'))
    P('   This is a READ check (syntax, bracketed bus names, m =, the black box, the 0-ohm ties, device classes known to the setup file), not an LVS against a layout.')
    os.makedirs(PT, exist_ok=True)
    ok = True
    for fn, cell in (('bias_genc.spice', 'bias_genc'), ('afe_chc.spice', 'amp_ch'), ('adc_ch.spice', 'adc_ch'), ('dbs_afe_top.spice', 'dbs_afe_top')):
        f = os.path.join(LVS, fn)
        f2 = os.path.join(PT, 'copy_' + fn)
        shutil.copy(f, f2)
        rep = os.path.join(PT, 'netgen_%s.out' % cell)
        lg = os.path.join(PT, 'netgen_%s.log' % cell)
        p = subprocess.Popen(['netgen', '-batch', 'lvs', '%s %s' % (f, cell), '%s %s' % (f2, cell), NETGEN_SETUP, rep], cwd=PT, stdout=open(lg, 'w'), stderr=subprocess.STDOUT, stdin=subprocess.DEVNULL)
        t0 = time.time()
        while p.poll() is None and time.time() - t0 < 300:
            time.sleep(0.5)
        if p.poll() is None:
            p.kill()
            p.wait()
            P('  %-18s %-12s netgen did not finish in 300 s: KILLED (pid %d)' % (fn, cell, p.pid))
            ok = False
            continue
        txt = open(lg, errors='replace').read()
        match = 'Circuits match uniquely' in txt and 'do not match' not in txt and 'Cannot compare' not in txt
        m = re.findall(r'Circuit 1 contains (\d+) devices, Circuit 2 contains (\d+) devices\.\s*\nCircuit 1 contains (\d+) nets,\s+Circuit 2 contains (\d+) nets', txt)
        last = txt[txt.rfind('Contents of circuit 1'):]
        cls = re.findall(r'Class: (\S+)\s+instances:\s+(\d+)', last[:last.find('Contents of circuit 2')])
        disc = re.findall(r'and (\d+) disconnected pin', last[:last.find('Contents of circuit 2')])
        msgs = sorted(set(l.strip()[:140] for l in txt.split('\n') if re.search(r'rror|mismatch|no such|cannot', l, flags=re.I)))
        ok = ok and match
        P('  %-18s %-12s %s | top cell: %s devices, %s nets%s | classes: %s | sub-cells compared: %d | messages: %s' % (
            fn, cell, 'READ, MATCHES ITS COPY' if match else 'PROBLEM', m[-1][0] if m else '?', m[-1][2] if m else '?', (', %s disconnected pin' % disc[0]) if disc else '',
            ', '.join('%s x%s' % c for c in cls), len(m), '; '.join(msgs)[:300] or 'none'))
    P('  netgen keeps the 15 pad-control ties as devices of class r (0 ohm) and reports DOUT_IN as the 1 disconnected pin of the top: the layout netlist must show the same (see the header of dbs_afe_top.spice).')
    P('  RESULT C: %s' % ('PASS' if ok else 'FAIL'))
    return ok


if __name__ == '__main__':
    parts = [a.upper() for a in sys.argv[1:]] or ['A', 'B', 'C']
    P('check_lvs_netlists.py: checks of the LVS reference netlists in %s (written by mk_lvs_netlists.py)   parts: %s' % (os.path.relpath(LVS, REPO), ' '.join(parts)))
    res = {}
    if 'A' in parts:
        res['A'] = part_a()
    if 'B' in parts:
        res['B'] = part_b()
    if 'C' in parts:
        res['C'] = part_c()
    P('\nSUMMARY: ' + ', '.join('%s %s' % (k, 'PASS' if v else 'FAIL') for k, v in res.items()))
    open(os.path.join(LVS, 'check_lvs_netlists.log'), 'w').write('\n'.join(OUT) + '\n')
    shutil.rmtree(PT, ignore_errors=True)
    sys.exit(0 if all(res.values()) else 1)
