#!/usr/bin/env python3
"""collect_dig.py (LP step 5 / L1d): copy what is committed out of a finished LibreLane run of afe_dig and check the hand-instantiated cells.
usage: python3 collect_dig.py <run dir = .../runs/<tag>> [librelane log] [/usr/bin/time -v output]
Writes  AFE/dig/trial/   afe_dig.pnl.v (powered gate-level netlist: LVS port order, later LVS_VERILOG_FILES), afe_dig.lef, afe_dig_pins.json (AS-BUILT pin table), run_dir.txt
        AFE/dig/reports/ metrics.json, flow_summary.rpt (the table every L1d number comes from), warnings_summary.log, yosys_stat.rpt, sta/<corner>/{checks,clock,power,skew.*,ws.*,violator_list}.rpt
NOT copied (stay in the run directory; regenerate with run_dig.sh): GDS, DEF, SPEF, SDF, ODB, .lib, the full STA path reports and the 1 MB LibreLane log.
Exit code 1 if a structural check fails (delay chain touched, tie / clock / switch cells missing, pins not where pins_plan.json puts them)."""
import os, re, sys, json, shutil, glob, subprocess
HERE = os.path.dirname(os.path.abspath(__file__))
DIG = os.path.normpath(os.path.join(HERE, '..'))
REPO = os.path.normpath(os.path.join(DIG, '..', '..'))
CORN = ['nom_ff_n40C_3v60', 'nom_ff_125C_3v60', 'nom_tt_025C_3v30', 'nom_ss_n40C_3v00', 'nom_ss_125C_3v00']
PFX = 'gf180mcu_fd_sc_mcu7t5v0__'
OUTPINS = ('Z', 'ZN', 'Q', 'QN')
CKBUF = 'clkbuf_20'      # the one clock buffer of AFE/dig/afe_dig.v (CLKBUF = 1)


def read_netlist(path):
    """[(cell type, instance name, {pin: net})] of a flat gate-level netlist"""
    txt = open(path).read()
    out = []
    for m in re.finditer(r'^\s*(%s\w+)\s+(\\\S+\s|\w+)\s*\((.*?)\);' % PFX, txt, flags=re.S | re.M):
        pins = {p.group(1): p.group(2).strip().lstrip('\\').strip() for p in re.finditer(r'\.(\w+)\s*\(([^()]*)\)', m.group(3))}
        out.append((m.group(1)[len(PFX):], m.group(2).strip().lstrip('\\'), pins))
    return out


def chain_check(cells, L):
    ok = True

    def need(cond, msg):
        nonlocal ok
        L.append('  %-4s %s' % ('OK' if cond else 'FAIL', msg))
        ok = ok and cond
    by = {}
    for typ, name, pins in cells:
        by.setdefault(typ, []).append((name, pins))
    cnt = lambda typ, rx: sum(1 for n, _ in by.get(typ, []) if re.search(rx, n))
    need(cnt('dlyd_1', r'ckg.*\.u$') == 49 and cnt('dlyd_1', r'\.utg$') == 8, 'delay cells dlyd_1: %d in the comparator chain (want 49), %d utg (want 8); other dlyd_* cells: %d' % (
        cnt('dlyd_1', r'ckg.*\.u$'), cnt('dlyd_1', r'\.utg$'), sum(len(v) for t, v in by.items() if t.startswith('dlyd')) - cnt('dlyd_1', r'ckg.*\.u$') - cnt('dlyd_1', r'\.utg$')))
    need(cnt('dlyc_1', r'ckg.*\.u$') == 8 and cnt('dlya_1', r'ckg.*\.u$') == 2, 'delay cells dlyc_1 %d (want 8), dlya_1 %d (want 2) in the chain' % (cnt('dlyc_1', r'ckg.*\.u$'), cnt('dlya_1', r'ckg.*\.u$')))
    need(cnt('inv_1', r'ckg.*\.ui$') == 8, 'tapw inverters ...ckg.t[i].ui: %d inv_1 (want 8)' % cnt('inv_1', r'ckg.*\.ui$'))
    ug = [(t, n) for t, v in by.items() for n, _ in v if re.search(r'ckg.*\.ug$', n)]
    need(len(ug) == 8 and all(t == 'and3_1' for t, _ in ug), 'comparator-clock gates ...ckg.t[i].ug (not dont-touch): %s (want 8 x and3_1)' % ', '.join(sorted(set('%s' % t for t, _ in ug))))
    need(cnt(CKBUF, r'^ck\.u_ckbuf$') <= 1, 'clock buffer ck.u_ckbuf (%s): %d' % (CKBUF, cnt(CKBUF, r'^ck\.u_ckbuf$')))
    need(cnt('clkinv_4', r'^sw\[\d\]\.u_(rec|ipg)$') == 16 and cnt('clkbuf_8', r'^sw\[\d\]\.u_(rec|ipg)_b$') == 16, 'switch output pairs: %d clkinv_4 + %d clkbuf_8 (want 16 + 16)' % (
        cnt('clkinv_4', r'^sw\[\d\]\.u_(rec|ipg)$'), cnt('clkbuf_8', r'^sw\[\d\]\.u_(rec|ipg)_b$')))
    oe = [pins for n, pins in by.get('clkinv_20', []) if n == 'u_oe']
    need(len(oe) == 1 and oe[0].get('I') == 'CS' and oe[0].get('ZN') == 'DOUT_OE', 'DOUT_OE driver u_oe: %d clkinv_20 from CS to DOUT_OE (want 1)' % len(oe))
    tl = sorted(n[len('u_tie_'):] for n, _ in by.get('tiel', []) if n.startswith('u_tie_'))
    th = sorted(n[len('u_tie_'):] for n, _ in by.get('tieh', []) if n.startswith('u_tie_'))
    need(len(tl) == 14 and th == ['RSTN_PD'], 'pad-control tie cells: %d tiel (want 14: %s), tieh: %s (want RSTN_PD)' % (len(tl), ' '.join(tl), ' '.join(th)))
    drives = {}
    loads = {}
    for typ, name, pins in cells:
        for p, net in pins.items():
            if p in ('VDD', 'VSS', 'VNW', 'VPW') or not net:
                continue
            (drives if p in OUTPINS else loads).setdefault(net, []).append((typ, name, p))
    tie_ok = all(drives.get(n, [('', '', '')])[0][0] == ('tieh' if n == 'RSTN_PD' else 'tiel') and not loads.get(n) for n in tl + th)
    need(tie_ok, 'every pad-control pin is driven by its own tie cell and has no other load inside the macro')
    # chain nets: only chain cells, ui, ug and the capture flop may load them (no buffer was inserted)
    bad = []
    nchain = 0
    for net, ld in loads.items():
        if not re.search(r'ckg.*\.Z$|ckg.*\.w\[|tapw_b|cap_clk', net):
            continue
        nchain += 1
        for typ, name, p in ld:
            legal = re.search(r'ckg.*\.(u|ui|ug)$', name) or (typ.startswith('dff') and p in ('CLK', 'CLKN'))
            if not legal:
                bad.append('%s <- %s %s.%s' % (net, typ, name, p))
        for typ, name, p in drives.get(net, []):
            if not re.search(r'ckg.*\.(u|ui)$', name):
                bad.append('%s driven by %s %s' % (net, typ, name))
    want_nets = cnt('dlyd_1', r'ckg.*\.u$') + cnt('dlyc_1', r'ckg.*\.u$') + cnt('dlyb_1', r'ckg.*\.u$') + cnt('dlya_1', r'ckg.*\.u$') + cnt('inv_1', r'ckg.*\.ui$')   # one net per chain cell and per tapw inverter
    need(not bad and nchain == want_nets, 'delay-chain nets (taps, w[k], tapw_b, cap_clk): %d nets (want %d = one per chain cell and inverter), foreign drivers / loads: %s' % (nchain, want_nets, '; '.join(bad[:4]) or 'none'))
    # clock node: with the buffer, sclk_i feeds only flop clock pins and the first chain cell
    if cnt(CKBUF, r'^ck\.u_ckbuf$') == 1:
        ld = loads.get('sclk_i', [])
        ff = [x for x in ld if x[0].startswith('dff') and x[2] in ('CLK', 'CLKN')]
        ch = [x for x in ld if re.search(r'ckg\.t\[0\]\.first\.ch\.g\[0\]\..*\.u$', x[1])]
        other = [x for x in ld if x not in ff and x not in ch]
        oe_other = [x for x in loads.get('DOUT_OE', [])]
        need(not oe_other, 'the pin DOUT_OE has no load inside the macro (the internal ~CS net is separate): %s' % (', '.join('%s.%s' % (x[1], x[2]) for x in oe_other[:4]) or 'none'))
        cap = sum(1 for x in loads.get('SCLK', []))
        need(len(ch) == 1 and not other and cap == 1, 'clock node sclk_i (output of ck.u_ckbuf): %d flop clock pins + %d delay-chain input, other loads: %s; pin SCLK loads: %d (want 1 = the buffer)' % (
            len(ff), len(ch), ', '.join('%s.%s' % (x[1], x[2]) for x in other[:4]) or 'none', cap))
        need(True, 'flops in the netlist: %d, of which %d are clocked by sclk_i and %d by a delayed tap (capture flops)' % (
            sum(len(v) for t, v in by.items() if t.startswith('dff')), len(ff), sum(len(v) for t, v in by.items() if t.startswith('dff')) - len(ff)))
    return ok


def pins_from_def(path):
    txt = open(path).read()
    dbu = int(re.search(r'UNITS DISTANCE MICRONS (\d+)', txt).group(1))
    d = re.search(r'DIEAREA \( (-?\d+) (-?\d+) \) \( (-?\d+) (-?\d+) \)', txt)
    W, H = (int(d.group(3)) - int(d.group(1))) / dbu, (int(d.group(4)) - int(d.group(2))) / dbu
    sec = txt[txt.index('\nPINS '):txt.index('END PINS')]
    pins, power = [], {}
    for blk in re.split(r'\n\s*- ', sec)[1:]:
        name = blk.split()[0]
        use = re.search(r'\+ USE (\w+)', blk).group(1)
        shapes = []
        for port in re.split(r'\+ PORT', blk)[1:]:
            pl = re.search(r'\+ (?:PLACED|FIXED) \( (-?\d+) (-?\d+) \) (\w+)', port)
            if not pl:
                continue
            ox, oy = int(pl.group(1)), int(pl.group(2))
            for m in re.finditer(r'\+ LAYER (\w+) \( (-?\d+) (-?\d+) \) \( (-?\d+) (-?\d+) \)', port):
                shapes.append((m.group(1), (ox + int(m.group(2))) / dbu, (oy + int(m.group(3))) / dbu, (ox + int(m.group(4))) / dbu, (oy + int(m.group(5))) / dbu))
        if use in ('POWER', 'GROUND'):
            power[name] = [{'layer': s[0], 'x0_um': round(s[1], 3), 'y0_um': round(s[2], 3), 'x1_um': round(s[3], 3), 'y1_um': round(s[4], 3)} for s in shapes]
            continue
        if len(shapes) != 1:
            raise SystemExit('collect_dig: pin %s has %d shapes' % (name, len(shapes)))
        ly, x0, y0, x1, y1 = shapes[0]
        cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
        dist = {'W': x0, 'E': W - x1, 'S': y0, 'N': H - y1}
        side = min(dist, key=dist.get)
        x, y = (cx, H if side == 'N' else 0.0) if side in 'NS' else (0.0 if side == 'W' else W, cy)
        pins.append({'name': name, 'layer': ly, 'x_um': round(x, 3), 'y_um': round(y, 3), 'side': side, 'rect_um': [round(v, 3) for v in (x0, y0, x1, y1)]})
    return W, H, pins, power


def main():
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    run = os.path.abspath(sys.argv[1])
    fin = os.path.join(run, 'final')
    if not os.path.isdir(fin):
        sys.exit('collect_dig: %s has no final/ directory' % run)
    tr, rp = os.path.join(DIG, 'trial'), os.path.join(DIG, 'reports')
    os.makedirs(tr, exist_ok=True)
    os.makedirs(os.path.join(rp, 'sta'), exist_ok=True)
    shutil.copy(os.path.join(fin, 'pnl', 'afe_dig.pnl.v'), tr)
    shutil.copy(os.path.join(fin, 'lef', 'afe_dig.lef'), tr)
    open(os.path.join(tr, 'run_dir.txt'), 'w').write('LibreLane run directory of these files (scratch, not in git; regenerate with `bash AFE/dig/run_dig.sh`): %s\n'
                                                     'final/gds/afe_dig.gds, final/def, final/nl, final/spef/{nom,min,max}, final/sdf/<corner>, final/lib/<corner> are there.\n' % run)
    m = json.load(open(os.path.join(fin, 'metrics.json')))
    json.dump(m, open(os.path.join(rp, 'metrics.json'), 'w'), indent=1, sort_keys=True)
    # warnings: one line per distinct message with its count (the raw warning.log is 100+ kB of repeated [EST-...] "Missing route to pin" lines from the parasitics estimate
    # of the post-global-routing repair steps; the sign-off numbers come from the extracted SPEF, not from that estimate)
    if os.path.exists(os.path.join(run, 'warning.log')):
        cnt_w, first = {}, {}
        for ln in open(os.path.join(run, 'warning.log'), errors='replace'):
            ln = ln.rstrip()
            if not ln:
                continue
            key = re.sub(r'\d+', 'N', re.sub(r'pin \S+ in net \S+', 'pin <pin> in net <net>', ln))
            cnt_w[key] = cnt_w.get(key, 0) + 1
            first.setdefault(key, ln)
        with open(os.path.join(rp, 'warnings_summary.log'), 'w') as f:
            f.write('LibreLane warning.log of the run, condensed: count, first occurrence of each distinct message (numbers and pin / net names folded)\n')
            for key, n in sorted(cnt_w.items(), key=lambda kv: -kv[1]):
                f.write('%6d  %s\n' % (n, first[key][:400]))
    for f in ('warning.log', 'flow.log'):          # older copies of the raw files
        if os.path.exists(os.path.join(rp, f)):
            os.remove(os.path.join(rp, f))
    ys = glob.glob(os.path.join(run, '*-yosys-synthesis', 'reports', 'stat.rpt'))
    if ys:
        shutil.copy(ys[0], os.path.join(rp, 'yosys_stat.rpt'))
    sta = sorted(glob.glob(os.path.join(run, '*-openroad-stapostpnr')))
    for c in CORN:
        os.makedirs(os.path.join(rp, 'sta', c), exist_ok=True)
        for f in ('checks.rpt', 'clock.rpt', 'power.rpt', 'skew.max.rpt', 'skew.min.rpt', 'ws.max.rpt', 'ws.min.rpt', 'violator_list.rpt'):
            src = os.path.join(sta[-1], c, f) if sta else ''
            if os.path.exists(src):
                shutil.copy(src, os.path.join(rp, 'sta', c))
    # ---- as-built pins
    W, H, pins, power = pins_from_def(os.path.join(fin, 'def', 'afe_dig.def'))
    g = lambda k, d=None: m.get(k, d)
    cfg = json.load(open(os.path.join(run, 'resolved.json')))
    json.dump({'_comment': 'AS-BUILT pin table of the afe_dig run named in run_dir.txt, written by AFE/dig/scripts/collect_dig.py from final/def. x / y = pin centre on the die edge (um, origin = SW corner of the macro); '
                           'rect_um = the pin shape [x0, y0, x1, y1]. power = the VDD / VSS shapes (vertical Metal4 straps, die edge to die edge).',
               'die_w_um': W, 'die_h_um': H, 'core_bbox_um': [float(v) for v in str(g('design__core__bbox', '0 0 0 0')).split()], 'core_utilisation': g('design__instance__utilization'),
               'cell_count_stdcell': g('design__instance__count__stdcell'), 'cell_area_um2': g('design__instance__area__stdcell'), 'flops': g('design__instance__count__class:sequential_cell'),
               'max_routing_layer': cfg.get('RT_MAX_LAYER'), 'pins': pins, 'power': power}, open(os.path.join(tr, 'afe_dig_pins.json'), 'w'), indent=1)
    L = ['afe_dig hardening summary (AFE/dig/scripts/collect_dig.py).  Run directory: %s' % run]
    ok = True
    plan_f = os.path.join(DIG, 'pins_plan.json')
    if os.path.exists(plan_f):
        plan = {q['name']: q for q in json.load(open(plan_f))['pins']}
        built = {q['name']: q for q in pins}
        diff = [n for n in plan if n not in built or abs(plan[n]['x_um'] - built[n]['x_um']) > 0.006 or abs(plan[n]['y_um'] - built[n]['y_um']) > 0.006 or plan[n]['layer'] != built[n]['layer'] or plan[n]['side'] != built[n]['side']]
        extra = [n for n in built if n not in plan]
        okp = not diff and not extra
        ok = ok and okp
        L.append('PINS: %d signal pins as built, %d planned (AFE/dig/pins_plan.json); not at the planned place: %d %s; not planned: %d  -> %s' % (len(built), len(plan), len(diff), diff[:5], len(extra), 'PASS' if okp else 'FAIL'))
    byside = {}
    for q in pins:
        byside.setdefault((q['side'], q['layer']), []).append(q)
    L.append('      ' + '; '.join('%s edge %d pins on %s' % (s, len(v), ly) for (s, ly), v in sorted(byside.items())))
    for n, sh in sorted(power.items()):
        xs = sorted(set((s['x0_um'], s['x1_um']) for s in sh))
        L.append('      %s: %d shapes on %s, x = %s um, y = %.2f .. %.2f um' % (n, len(sh), '/'.join(sorted(set(s['layer'] for s in sh))), ' '.join('%.2f-%.2f' % x for x in xs), min(s['y0_um'] for s in sh), max(s['y1_um'] for s in sh)))
    # ---- metrics table
    L.append('DIE %s um, core %s um, std cells %s (%.0f um2, utilisation %.1f %%), flops %s, repair buffers %s, clock option: %s, routing up to %s' % (
        g('design__die__bbox'), g('design__core__bbox'), g('design__instance__count__stdcell'), g('design__instance__area__stdcell', 0), 100 * g('design__instance__utilization', 0),
        g('design__instance__count__class:sequential_cell'), g('design__instance__count__class:timing_repair_buffer'), 'CTS' if cfg.get('RUN_CTS') else 'no CTS + ck.u_ckbuf (Decision 44h)', cfg.get('RT_MAX_LAYER')))
    L.append('ROUTE drc errors %s, wirelength %s um, antenna violating nets %s; Magic DRC %s; LVS errors %s; XOR differences %s; KLayout DRC: not run by the flow (see reports/klayout_drc.log)' % (
        g('route__drc_errors'), g('route__wirelength'), g('antenna__violating__nets'), g('magic__drc_error__count'), g('design__lvs_error__count'), g('design__xor_difference__count')))
    L.append('STA after place and route (extracted nom SPEF, period %s ns, clock uncertainty 0.5 ns):' % cfg.get('CLOCK_PERIOD'))
    L.append('  %-18s %10s %9s %10s %9s %6s %5s %7s' % ('corner', 'setup ws', 'hold ws', 'setup vio', 'hold vio', 'slew', 'cap', 'fanout'))
    worst = dict(sv=0, hv=0, slew=0, cap=0)
    for c in CORN:
        v = [g('timing__setup__ws__corner:' + c), g('timing__hold__ws__corner:' + c), g('timing__setup_vio__count__corner:' + c), g('timing__hold_vio__count__corner:' + c),
             g('design__max_slew_violation__count__corner:' + c), g('design__max_cap_violation__count__corner:' + c), g('design__max_fanout_violation__count__corner:' + c)]
        L.append('  %-18s %10.3f %9.3f %10s %9s %6s %5s %7s' % tuple([c] + v))
        worst['sv'] += v[2] or 0; worst['hv'] += v[3] or 0; worst['slew'] = max(worst['slew'], v[4] or 0); worst['cap'] = max(worst['cap'], v[5] or 0)
    L.append('  worst corner: max-slew violations %d, max-cap violations %d (D3 macro: 16 / 3); setup violations %d, hold violations %d' % (worst['slew'], worst['cap'], worst['sv'], worst['hv']))
    L.append('POWER from the flow (default activity, NOT used; see reports/power_dig.log): %.1f uW' % (1e6 * g('power__total', 0)))
    if len(sys.argv) > 3 and os.path.exists(sys.argv[3]):
        t = open(sys.argv[3]).read()
        el = re.search(r'Elapsed \(wall clock\) time.*?: (\S+)', t)
        rs = re.search(r'Maximum resident set size \(kbytes\): (\d+)', t)
        du = subprocess.run(['du', '-sm', run], capture_output=True, text=True).stdout.split()[0]
        try:
            ver = subprocess.run(['librelane', '--version'], capture_output=True, text=True, timeout=120).stdout.split('\n')[0].strip()
        except Exception:
            ver = 'LibreLane (version not read)'
        L.append('RUN wall time %s, peak RSS %.0f MB, run directory %s MB (%s)' % (el.group(1) if el else '?', int(rs.group(1)) / 1024 if rs else -1, du, ver))
    L.append('STRUCTURE of the hand-instantiated cells in final/nl/afe_dig.nl.v:')
    ok = chain_check(read_netlist(os.path.join(fin, 'nl', 'afe_dig.nl.v')), L) and ok
    clean = worst['sv'] == 0 and worst['hv'] == 0 and (g('route__drc_errors') == 0) and (g('magic__drc_error__count') == 0) and (g('design__lvs_error__count') == 0)
    L.append('VERDICT: structure %s; timing / route / Magic DRC / LVS %s; max-slew / max-cap %s' % ('PASS' if ok else 'FAIL', 'PASS' if clean else 'FAIL', 'PASS' if worst['slew'] == 0 and worst['cap'] == 0 else 'VIOLATIONS LEFT'))
    open(os.path.join(rp, 'flow_summary.rpt'), 'w').write('\n'.join(L) + '\n')
    print('\n'.join(L))
    sys.exit(0 if ok and clean else 1)


if __name__ == '__main__':
    main()
