#!/usr/bin/env python3
"""flow.py (LP kit): the ONE tested command set for DRC / extraction / LVS / PEX of every layout phase (L2b, L1a, L1b, L1d, L3a, L3b).
gate.py reads the JSON reports that these commands write, so always use them (do not call run_drc.py / magic / netgen by hand for a result that counts).

  python3 AFE/layout/scripts/flow.py drc --gds G --top T [--out DIR] [--mode flat|deep] [--antenna] [--density] [--no-offgrid]
        official gf180mcuD KLayout deck, --variant=D (common rule 9).   -> DIR/T.drc.json  {total, rules{rule: count}, ...}, DIR/T.drc.log, DIR/drc_T/*.lyrdb
  python3 AFE/layout/scripts/flow.py lvs --gds G --top T --ref REF.spice [--refcell NAME] [--out DIR] [--flatten CELL ...]
        Magic extraction (no parasitics) + netgen -batch (timeout, waited by PID).  -> DIR/T.lvs.spice, DIR/T.lvs.out (netgen report), DIR/T.lvs.json {match, ...}
  python3 AFE/layout/scripts/flow.py pex --gds G --top T [--out DIR] [--mode c|rc] [--cthresh fF] [--lvsnet DIR/T.lvs.spice]
        Magic parasitic extraction of the flattened cell.  c = devices + coupling / ground capacitance; rc = + extresist series resistance.
        -> DIR/T.pex.spice (subckt T, Magic's own port order), DIR/T.pex.json {devices{model: n}, n_cap, n_res, c_total_fF, census_equal_lvs}
  python3 AFE/layout/scripts/flow.py info --gds G [--top T]        bounding box, cells, labels per layer (for floorplan / pin checks)   -> JSON on stdout
  python3 AFE/layout/scripts/flow.py versions                      tool versions as JSON

Defaults: --out = AFE/layout/sim/flow (reports are small and are committed); scratch = $AFE_SCRATCH or AFE/layout/.ptmp (git-ignored; delete it at the end of a phase).
Every heavy tool runs in one of the machine-wide job slots of slot.sh (common rule 4: at most 3 heavy jobs; AFE_SLOTS overrides).
Exit code: 0 = ran AND clean (DRC total 0 / LVS match / PEX census equal), 1 = ran but not clean, 2 = the tool failed.  The JSON always says why.
"""
import os, sys, json, subprocess, time, re, argparse, fcntl, shutil, glob

HERE = os.path.dirname(os.path.abspath(__file__))
LAY = os.path.normpath(os.path.join(HERE, '..'))
REPO = os.path.normpath(os.path.join(LAY, '..', '..'))
PDK_ROOT = os.environ.get('PDK_ROOT', '/foss/pdks')
PDK = os.environ.get('PDK', 'gf180mcuD')
TECH = os.path.join(PDK_ROOT, PDK, 'libs.tech')
DRC_PY = os.path.join(TECH, 'klayout/tech/drc/run_drc.py')
MAGICRC = os.path.join(TECH, 'magic', PDK + '.magicrc')
NETGEN_SETUP = os.path.join(TECH, 'netgen', PDK + '_setup.tcl')
VARIANT = 'D'
SCRATCH = os.environ.get('AFE_SCRATCH', os.path.join(LAY, '.ptmp'))
OUT_DEFAULT = os.path.join(LAY, 'sim', 'flow')
DEVICE_RE = re.compile(r'^(?:x|m)\S*\s+(.*)$', re.I)
KNOWN_MODELS = ('nfet_03v3', 'pfet_03v3', 'nfet_05v0', 'pfet_05v0', 'nfet_06v0', 'pfet_06v0', 'nfet_06v0_nvt', 'cap_mim_2f0_m4m5_noshield', 'cap_nmos_03v3', 'cap_nmos_06v0',
                'cap_pmos_03v3', 'ppolyf_u_1k', 'ppolyf_u', 'ppolyf_s', 'npolyf_u', 'npolyf_s', 'rm1', 'rm2', 'rm3', 'rm4', 'rmtp', 'nplus_u', 'pplus_u', 'nwell_1p5')


# ------------------------------------------------------------------ job slots (same lock files as slot.sh)
class Slot:
    def __init__(self):
        self.n = int(os.environ.get('AFE_SLOTS', '3'))
        self.d = os.environ.get('AFE_SLOT_DIR', '/tmp/afe_slots')
        self.f = None

    def __enter__(self):
        os.makedirs(self.d, exist_ok=True)
        while True:
            for i in range(1, self.n + 1):
                f = open(os.path.join(self.d, 'slot%d.lock' % i), 'w')
                try:
                    fcntl.flock(f, fcntl.LOCK_EX | fcntl.LOCK_NB)
                    self.f = f
                    return self
                except OSError:
                    f.close()
            time.sleep(2)

    def __exit__(self, *a):
        if self.f:
            fcntl.flock(self.f, fcntl.LOCK_UN)
            self.f.close()


def run(cmd, cwd, log, timeout=None, stdin=None, env=None):
    """run one tool in a job slot; wait by PID; returns (rc, wall_s, maxrss_MB).  rc = -9 on timeout."""
    with Slot():
        t0 = time.time()
        with open(log, 'w') as lf:
            p = subprocess.Popen(cmd, cwd=cwd, stdout=lf, stderr=subprocess.STDOUT, stdin=(stdin or subprocess.DEVNULL), env=env)
            rss = 0
            while True:
                pid, st, ru = os.wait4(p.pid, os.WNOHANG)
                if pid == p.pid:
                    rss = ru.ru_maxrss / 1024.0
                    rc = os.waitstatus_to_exitcode(st)
                    p.returncode = rc
                    break
                if timeout and time.time() - t0 > timeout:
                    p.kill()
                    os.wait4(p.pid, 0)
                    p.returncode = -9
                    rc = -9
                    break
                time.sleep(0.2)
        return rc, time.time() - t0, rss


def wjson(path, d):
    g = d.get('gds')
    if g and 'gds_sha1' not in d:                        # gate.py checks that a report belongs to the GDS that is committed
        gp = g if os.path.isabs(g) else os.path.join(REPO, g)
        if os.path.exists(gp):
            import hashlib
            d['gds_sha1'] = hashlib.sha1(open(gp, 'rb').read()).hexdigest()
    with open(path, 'w') as f:
        json.dump(d, f, indent=1, sort_keys=True)
        f.write('\n')
    return d


def rel(p):
    try:
        return os.path.relpath(p, REPO)
    except ValueError:
        return p


def scratch(tag):
    d = os.path.join(SCRATCH, tag)
    shutil.rmtree(d, ignore_errors=True)
    os.makedirs(d, exist_ok=True)
    return d


# ------------------------------------------------------------------ DRC
def lyrdb_counts(path):
    """rule -> number of violations in a KLayout report database (streamed: the file can be large)"""
    import xml.etree.ElementTree as ET
    cnt = {}
    for ev, el in ET.iterparse(path, events=('end',)):
        if el.tag == 'item':
            c = el.find('category')
            name = (c.text or '').strip().strip("'") if c is not None else '?'
            cnt[name] = cnt.get(name, 0) + 1
            el.clear()
    return cnt


def cmd_drc(a):
    gds = os.path.abspath(a.gds)
    os.makedirs(a.out, exist_ok=True)
    rd = os.path.join(a.out, 'drc_' + a.top)
    shutil.rmtree(rd, ignore_errors=True)
    os.makedirs(rd)
    cmd = ['python3', DRC_PY, '--path=' + gds, '--variant=' + VARIANT, '--topcell=' + a.top, '--run_dir=' + rd, '--run_mode=' + a.mode, '--thr=%d' % a.thr]
    if a.antenna:
        cmd.append('--antenna')
    if a.density:
        cmd.append('--density')
    if a.no_offgrid:
        cmd.append('--no_offgrid')
    log = os.path.join(a.out, a.top + '.drc.log')
    rc, wall, rss = run(cmd, a.out, log)
    txt = open(log, errors='replace').read()
    rules, dbs = {}, sorted(glob.glob(os.path.join(rd, '*.lyrdb')))
    for db in dbs:
        for k, v in lyrdb_counts(db).items():
            rules[k] = rules.get(k, 0) + v
    ran = bool(dbs) and ('Klayout DRC run is clean' in txt or 'Klayout DRC run is not clean' in txt or 'DRC Total Run time' in txt)
    for junk in glob.glob(os.path.join(rd, '*.drc')):          # the generated rule deck copies (0.4 MB each): not evidence
        os.remove(junk)
    res = dict(tool='klayout DRC', deck=rel(DRC_PY), variant=VARIANT, gds=rel(gds), top=a.top, mode=a.mode, antenna=bool(a.antenna), density=bool(a.density), offgrid=not a.no_offgrid,
               ran=ran, total=sum(rules.values()), rules=rules, wall_s=round(wall, 1), maxrss_mb=round(rss), databases=[rel(d) for d in dbs], log=rel(log), date=time.strftime('%Y-%m-%d %H:%M'))
    wjson(os.path.join(a.out, a.top + '.drc.json'), res)
    print('DRC %s: %s, %d violations%s  (%.0f s, %d MB)  -> %s' % (a.top, 'ran' if ran else 'TOOL FAILED (see %s)' % rel(log), res['total'],
          (' ' + ', '.join('%s x%d' % kv for kv in sorted(rules.items()))) if rules else '', wall, rss, rel(os.path.join(a.out, a.top + '.drc.json'))))
    return 2 if not ran else (0 if res['total'] == 0 else 1)


# ------------------------------------------------------------------ Magic
def magic(script, cwd, log, timeout=None):
    fn = os.path.join(cwd, 'run.tcl')
    open(fn, 'w').write(script)
    return run(['magic', '-dnull', '-noconsole', '-rcfile', MAGICRC, fn], cwd, log, timeout=timeout)


def census(path, top=None):
    """device model -> count of the subckt `top` (or of the whole file) of a SPICE netlist; also counts C / R elements"""
    dev, nc, nr, ctot = {}, 0, 0, 0.0
    inside = top is None
    cur = ''
    lines = []
    for ln in open(path, errors='replace'):
        ln = ln.rstrip('\n')
        if ln.startswith('+'):
            cur += ' ' + ln[1:]
        else:
            lines.append(cur)
            cur = ln
    lines.append(cur)
    ports = None
    for ln in lines:
        s = ln.strip()
        lo = s.lower()
        if lo.startswith('.subckt'):
            t = s.split()
            if top is not None and t[1].lower() == top.lower():
                inside, ports = True, t[2:]
            continue
        if lo.startswith('.ends'):
            if top is not None:
                inside = False
            continue
        if not inside or not s or s[0] in '*.':
            continue
        if lo[0] == 'x' or lo[0] == 'm':
            t = [x for x in s.split() if '=' not in x]
            model = t[-1].lower()
            m = re.search(r'\bm=(\d+)', lo)
            dev[model] = dev.get(model, 0) + (int(m.group(1)) if m and model in ('cap_nmos_03v3',) else 1)
        elif lo[0] == 'c':
            nc += 1
            t = s.split()
            m = re.match(r'([-+0-9.e]+)\s*(f|p|n|u|a)?', t[3].lower())
            if m:
                ctot += float(m.group(1)) * {'f': 1.0, 'p': 1e3, 'n': 1e6, 'u': 1e9, 'a': 1e-3, None: 1e15}[m.group(2)]
        elif lo[0] == 'r':
            nr += 1
    return dev, nc, nr, ctot, ports


def cmd_ext(a, quiet=False):
    """Magic extraction without parasitics -> out/T.lvs.spice"""
    gds = os.path.abspath(a.gds)
    os.makedirs(a.out, exist_ok=True)
    d = scratch('ext_' + a.top)
    net = os.path.join(a.out, a.top + '.lvs.spice')
    if os.path.exists(net):
        os.remove(net)
    flat = ''.join('catch {flatten -dotoplabels %s_fl; }\n' % c for c in (a.flatten or []))
    script = ('gds flatglob *$$*\ngds read %s\nload %s\nselect top cell\n%sextract path %s\nextract all\next2spice lvs\next2spice -p %s -o %s\nputs "FLOW_EXT_DONE"\nquit -noprompt\n'
              % (gds, a.top, flat, d, d, net))
    log = os.path.join(a.out, a.top + '.ext.log')
    rc, wall, rss = magic(script, d, log)
    ok = os.path.exists(net) and 'FLOW_EXT_DONE' in open(log, errors='replace').read()
    if not quiet:
        print('EXT %s: %s (%.0f s, %d MB) -> %s' % (a.top, 'ok' if ok else 'FAILED (see %s)' % rel(log), wall, rss, rel(net)))
    return ok, net, wall, rss, log


def netgen_summary(txt):
    """netgen report text -> verdict.  MATCH only if the final result is exactly 'Circuits match uniquely.' and no cell is listed with property errors."""
    res = dict(match=False, property_errors=False, pin_mismatch=False, final='', property_error_cells=[])
    L = [l.strip() for l in txt.split('\n')]
    for i, s in enumerate(L):
        if s.startswith('Final result:'):
            r = s[len('Final result:'):].strip()
            if not r:
                r = next((x for x in L[i + 1:i + 4] if x), '')
            res['final'] = r
        if s.startswith('The following cells had property errors'):
            res['property_error_cells'] = [x for x in L[i + 1:i + 40] if x and not x.startswith('---')]
    res['property_errors'] = bool(res['property_error_cells']) or 'property errors' in res['final'].lower()
    res['pin_mismatch'] = 'failed pin matching' in txt or 'port errors' in txt or 'port and property errors' in txt
    res['match'] = (res['final'] == 'Circuits match uniquely.') and not res['property_errors']
    return res


def cmd_lvs(a):
    ok, net, w1, r1, elog = cmd_ext(a, quiet=True)
    out = os.path.join(a.out, a.top + '.lvs.out')
    jf = os.path.join(a.out, a.top + '.lvs.json')
    ref = os.path.abspath(a.ref)
    refcell = a.refcell or a.top
    res = dict(tool='magic + netgen', gds=rel(os.path.abspath(a.gds)), top=a.top, ref=rel(ref), refcell=refcell, layout_netlist=rel(net), report=rel(out), setup=rel(NETGEN_SETUP),
               extract_ok=ok, ran=False, match=False, date=time.strftime('%Y-%m-%d %H:%M'))
    if not ok:
        res['why'] = 'Magic extraction failed, see ' + rel(elog)
        wjson(jf, res)
        print('LVS %s: TOOL FAILED: %s' % (a.top, res['why']))
        return 2
    if os.path.exists(out):
        os.remove(out)
    d = scratch('lvs_' + a.top)
    log = os.path.join(a.out, a.top + '.netgen.log')
    cmd = ['netgen', '-batch', 'lvs', '%s %s' % (net, a.top), '%s %s' % (ref, refcell), NETGEN_SETUP, out]
    rc, wall, rss = run(cmd, d, log, timeout=a.timeout)
    txt = open(out, errors='replace').read() if os.path.exists(out) else ''
    s = netgen_summary(txt)
    dl, _, _, _, pl = census(net, a.top)
    dr = {}
    try:
        dr, _, _, _, pr = census(ref, refcell)
    except OSError:
        pr = None
    res.update(ran=bool(txt) and rc != -9, timeout=(rc == -9), wall_s=round(w1 + wall, 1), maxrss_mb=round(max(r1, rss)), devices_layout=dl, ports_layout=pl, ports_ref=pr, **s)
    if not res['ran']:
        res['why'] = 'netgen %s, see %s' % ('timed out after %d s' % a.timeout if rc == -9 else 'wrote no report', rel(log))
    wjson(jf, res)
    print('LVS %s vs %s:%s: %s  [%s]  (%.0f s)  -> %s' % (a.top, rel(ref), refcell, 'MATCH' if res['match'] else ('NO MATCH' if res['ran'] else 'TOOL FAILED'), res.get('final') or res.get('why', ''),
          w1 + wall, rel(jf)))
    return 2 if not res['ran'] else (0 if res['match'] else 1)


MIM_MODEL = 'cap_mim_2f0_m4m5_noshield'
_SUF = {'f': 1.0, 'p': 1e3, 'n': 1e6, 'u': 1e9, 'a': 1e-3, 'm': 1e12, '': 1e15}


def _val_fF(tok):
    m = re.match(r'^([-+]?[0-9.]+(?:e[-+]?\d+)?)([a-z]?)', tok.lower())
    return float(m.group(1)) * _SUF[m.group(2)]


def _len_um(tok):
    m = re.match(r'^([-+]?[0-9.]+(?:e[-+]?\d+)?)([a-z]?)', tok.lower())
    return float(m.group(1)) * {'u': 1.0, 'm': 1e3, 'n': 1e-3, '': 1e6}[m.group(2)]


def nomim_tech():
    """a copy of the Magic tech file in which the MIM top-plate tile (`mimcap`, plane metal4) takes NO part in the parasitic capacitance rules, and an rc file that loads it.
    WHY (LP finding, AFE/layout/sim/check_env_ref.log): Magic treats the mimcap tile as Metal4 that belongs to the TOP-plate node, so the stock extraction attaches the capacitance
    between the capacitor and whatever lies below it (substrate, wells, Metal1-3) to terminal 1 = the top plate.  In silicon the bottom plate (Metal4) faces downward and shields the top
    plate.  `pex` therefore extracts twice (stock, and with this file) and moves the difference from each top-plate net to the bottom-plate net(s) of its capacitors."""
    d = os.path.join(SCRATCH, 'tech')
    os.makedirs(d, exist_ok=True)
    src = os.path.join(TECH, 'magic', PDK + '.tech')
    out = os.path.join(d, PDK + '_nomimpar.tech')
    txt = open(src, errors='replace').read().split('\n')
    res, n_alias, n_rule, in_ext = [], 0, 0, False
    for ln in txt:
        if re.match(r'^\s*allm4\s+\*m4,rm4,\*mimcap\s*$', ln):
            res.append(ln)
            res.append('  allm4np\t\t*m4,rm4')
            n_alias += 1
            continue
        if re.match(r'^extract\s*$', ln):
            in_ext = True
        elif in_ext and re.match(r'^end\s*$', ln):
            in_ext = False
        if in_ext and re.match(r'^\s*default(areacap|perimeter|overlap|sideoverlap|sidewall)\b', ln) and re.search(r'\ballm4\b', ln):
            ln = re.sub(r'\ballm4\b', 'allm4np', ln)
            n_rule += 1
        res.append(ln)
    if n_alias != 1 or n_rule < 20:
        raise SystemExit('flow.py pex: the Magic tech file does not look as expected (alias lines %d, capacitance rules %d): the MIM correction cannot be built' % (n_alias, n_rule))
    open(out, 'w').write('\n'.join(res))
    rc = open(MAGICRC, errors='replace').read()
    key = '$PDK_ROOT/%s/libs.tech/magic/%s.tech' % (PDK, PDK)
    if key not in rc:
        raise SystemExit('flow.py pex: %s does not load the tech file the expected way' % MAGICRC)
    rcout = os.path.join(d, PDK + '_nomimpar.magicrc')
    open(rcout, 'w').write(rc.replace(key, out))
    return rcout, n_rule


def read_pex(path, top):
    """-> (header lines up to and incl. .subckt, device lines, {(a, b): fF} with a < b, other lines (R ...), ports)"""
    cur, lines = '', []
    for ln in open(path, errors='replace'):
        ln = ln.rstrip('\n')
        if ln.startswith('+'):
            cur += ' ' + ln[1:]
        else:
            lines.append(cur)
            cur = ln
    lines.append(cur)
    head, dev, caps, other, ports, inside = [], [], {}, [], None, False
    for ln in lines:
        s = ln.strip()
        lo = s.lower()
        if lo.startswith('.subckt') and s.split()[1].lower() == top.lower():
            inside, ports = True, s.split()[2:]
            head.append(ln)
            continue
        if not inside:
            if s:
                head.append(ln)
            continue
        if lo.startswith('.ends'):
            inside = False
            continue
        if not s or s[0] == '*':
            continue
        if lo[0] == 'c':
            t = s.split()
            k = tuple(sorted((t[1], t[2])))
            caps[k] = caps.get(k, 0.0) + _val_fF(t[3])
        elif lo[0] in 'xm':
            dev.append(s)
        else:
            other.append(s)
    return head, dev, caps, other, ports


def mim_fix(stock, nomim, top):
    """moves the capacitance that the stock extraction attached to MIM top plates onto the bottom plates.  Returns (text of the corrected netlist, report dict)."""
    h1, d1, c1, o1, p1 = read_pex(stock, top)
    h2, d2, c2, o2, p2 = read_pex(nomim, top)
    if [x.split()[1:] for x in d1] != [x.split()[1:] for x in d2] or p1 != p2:
        raise SystemExit('flow.py pex: the two extraction passes disagree on devices or ports (MIM correction not possible)')
    tops = {}                                           # top-plate net -> {bottom net: MIM area um2}
    for s in d1:
        t = s.split()
        nodes = [x for x in t[1:] if '=' not in x]
        if nodes[-1].lower() != MIM_MODEL:
            continue
        par = dict(x.lower().split('=') for x in t if '=' in x)
        area = _len_um(par['c_width']) * _len_um(par['c_length']) * float(par.get('m', 1))
        tops.setdefault(nodes[0], {})
        tops[nodes[0]][nodes[1]] = tops[nodes[0]].get(nodes[1], 0.0) + area
    new = dict(c2)
    moved = {}
    odd = 0.0
    for k in set(c1) | set(c2):
        dlt = c1.get(k, 0.0) - c2.get(k, 0.0)
        if abs(dlt) < 1e-4:
            continue
        a, b = k
        if a not in tops and b not in tops:
            odd += abs(dlt)                              # a difference that no top plate explains: keep the stock value
            new[k] = c1.get(k, 0.0)
            continue
        ta = [(n, w / sum(tops[a].values())) for n, w in tops[a].items()] if a in tops else [(a, 1.0)]
        tb = [(n, w / sum(tops[b].values())) for n, w in tops[b].items()] if b in tops else [(b, 1.0)]
        for na, wa in ta:
            for nb, wb in tb:
                if na == nb:
                    continue
                kk = tuple(sorted((na, nb)))
                new[kk] = new.get(kk, 0.0) + dlt * wa * wb
        for n in (a, b):
            if n in tops:
                moved[n] = moved.get(n, 0.0) + dlt
    cl = ['C%d %s %s %.5gf' % (i, a, b, v) for i, ((a, b), v) in enumerate(sorted(new.items())) if v > 0]
    hdr = [x for x in h2 if not x.lower().startswith('.subckt')] + [
        '* MIM correction of flow.py pex: capacitance to the layers below that Magic attached to MIM TOP plates was moved to the bottom plates:',
        '*   ' + ('; '.join('%s: %.2f fF -> %s' % (n, v, ' + '.join('%s' % q for q in tops[n])) for n, v in sorted(moved.items())) or 'nothing to move')]
    txt = '\n'.join(hdr + [x for x in h2 if x.lower().startswith('.subckt')] + d2 + o2 + cl + ['.ends', ''])
    rep = dict(moved_fF={n: round(v, 3) for n, v in moved.items()}, top_plate_nets={n: {q: round(w, 2) for q, w in d.items()} for n, d in tops.items()}, unexplained_fF=round(odd, 4),
               c_total_stock_fF=round(sum(c1.values()), 3), c_total_fixed_fF=round(sum(new.values()), 3))
    return txt, rep


def cmd_pex(a):
    gds = os.path.abspath(a.gds)
    os.makedirs(a.out, exist_ok=True)
    d = scratch('pex_' + a.top)
    net = os.path.join(a.out, a.top + '.pex.spice')
    fl = a.top + '_pexflat'
    log = os.path.join(a.out, a.top + '.pex.log')
    jf = os.path.join(a.out, a.top + '.pex.json')
    res = dict(tool='magic PEX', mode=a.mode, cthresh_fF=a.cthresh, gds=rel(gds), top=a.top, netlist=rel(net), log=rel(log), date=time.strftime('%Y-%m-%d %H:%M'))

    def one(tag, rcfile):
        dd = os.path.join(d, tag)
        os.makedirs(dd, exist_ok=True)
        raw = os.path.join(dd, a.top + '_raw.spice')
        rcs = ''
        if a.mode == 'rc':
            rcs = 'ext2sim labels on\next2sim -p %s -o %s/%s.sim\nextresist tolerance %g\nextresist all\n' % (dd, dd, fl, a.rtol)
        script = ('gds flatglob *$$*\ngds read %s\nload %s\nselect top cell\nflatten -dotoplabels %s\nload %s\nselect top cell\nextract path %s\nextract all\n%s'
                  'ext2spice lvs\next2spice cthresh %g\next2spice rthresh %g\n%sext2spice -p %s -o %s\nputs "FLOW_PEX_DONE"\nquit -noprompt\n'
                  % (gds, a.top, fl, fl, dd, rcs, a.cthresh, a.rthresh, 'ext2spice extresist on\n' if a.mode == 'rc' else '', dd, raw))
        fn = os.path.join(dd, 'run.tcl')
        open(fn, 'w').write(script)
        lg = log if tag == 'stock' else log.replace('.pex.log', '.pex_nomim.log')
        rc, wall, rss = run(['magic', '-dnull', '-noconsole', '-rcfile', rcfile, fn], dd, lg)
        ok = os.path.exists(raw) and 'FLOW_PEX_DONE' in open(lg, errors='replace').read()
        if ok:                                           # the flattened copy is called <top>_pexflat: give the subckt the name of the cell again
            txt = open(raw, errors='replace').read()
            txt = re.sub(r'(?im)^(\.subckt\s+)%s\b' % re.escape(fl), r'\g<1>' + a.top, txt)
            txt = re.sub(r'(?im)^(\.ends)\s+%s\b' % re.escape(fl), r'\g<1> ' + a.top, txt)
            open(raw, 'w').write(txt.replace(fl + '.ext', a.top + ' (flattened)'))
        return ok, raw, wall, rss, lg

    ok, raw, wall, rss, lg = one('stock', MAGICRC)
    if not ok:
        res.update(ran=False, why='Magic PEX failed, see ' + rel(lg))
        wjson(jf, res)
        print('PEX %s: TOOL FAILED (see %s)' % (a.top, rel(lg)))
        return 2
    dev, nc, nr, ctot, ports = census(raw, a.top)
    res['mim_fix'] = None
    if dev.get(MIM_MODEL) and not a.no_mimfix:
        rcfile, nrule = nomim_tech()
        ok2, raw2, wall2, rss2, lg2 = one('nomim', rcfile)
        if not ok2:
            res.update(ran=False, why='second Magic PEX pass (MIM correction) failed, see ' + rel(lg2))
            wjson(jf, res)
            print('PEX %s: TOOL FAILED (see %s)' % (a.top, rel(lg2)))
            return 2
        txt, rep = mim_fix(raw, raw2, a.top)
        open(net, 'w').write(txt)
        shutil.copy(raw, net.replace('.pex.spice', '.pex_stock.spice'))
        res['mim_fix'] = rep
        res['netlist_stock'] = rel(net.replace('.pex.spice', '.pex_stock.spice'))
        wall, rss = wall + wall2, max(rss, rss2)
    else:
        shutil.copy(raw, net)
    dev, nc, nr, ctot, ports = census(net, a.top)
    res.update(ran=True, devices=dev, n_cap=nc, n_res=nr, c_total_fF=round(ctot, 3), ports=ports, bytes=os.path.getsize(net), wall_s=round(wall, 1), maxrss_mb=round(rss))
    lvsnet = a.lvsnet or os.path.join(a.out, a.top + '.lvs.spice')
    if os.path.exists(lvsnet):
        dl = census_flat(lvsnet, a.top)
        res['devices_lvs_extraction'] = dl
        res['census_equal_lvs'] = (dl == dev)
    else:
        res['census_equal_lvs'] = None
    unknown = sorted(k for k in dev if k not in KNOWN_MODELS)
    res['unknown_models'] = unknown
    wjson(jf, res)
    mf = res['mim_fix']
    print('PEX %s (%s): %d devices %s, %d C (%.1f fF), %d R, ports %s; census vs LVS extraction: %s%s  (%.0f s, %d MB) -> %s' % (
        a.top, a.mode, sum(dev.values()), dict(sorted(dev.items())), nc, ctot, nr, ' '.join(ports or []), res['census_equal_lvs'],
        ('; MIM correction moved ' + ', '.join('%s %.1f fF' % kv for kv in sorted(mf['moved_fF'].items()))) if mf else '', wall, rss, rel(net)))
    return 0 if (res['census_equal_lvs'] is not False and not unknown) else 1


def census_flat(path, top):
    """leaf-device census of `top` in a hierarchical netlist (Magic LVS extraction keeps the pcell sub-cells as subckts)"""
    subs, cur, name = {}, '', None
    lines = []
    for ln in open(path, errors='replace'):
        ln = ln.rstrip('\n')
        if ln.startswith('+'):
            cur += ' ' + ln[1:]
        else:
            lines.append(cur)
            cur = ln
    lines.append(cur)
    for ln in lines:
        s = ln.strip()
        lo = s.lower()
        if lo.startswith('.subckt'):
            name = s.split()[1].lower()
            subs[name] = []
        elif lo.startswith('.ends'):
            name = None
        elif name and s and lo[0] in 'xm':
            t = [x for x in s.split() if '=' not in x]
            m = re.search(r'\bm=(\d+)', lo)
            subs[name].append((t[-1].lower(), int(m.group(1)) if m else 1))

    def leaf(n, mult, acc, depth=0):
        for model, m in subs.get(n, []):
            if model in subs and depth < 50:
                leaf(model, mult * m, acc, depth + 1)
            else:
                acc[model] = acc.get(model, 0) + mult * (m if model == 'cap_nmos_03v3' else 1)
        return acc
    return leaf(top.lower(), 1, {})


# ------------------------------------------------------------------ info (KLayout, batch)
INFO_PY = r'''
import pya, json
ly = pya.Layout(); ly.read(gds)
tops = [c for c in ly.top_cells()] if not top else [ly.cell(top)]
res = {"dbu": ly.dbu, "cells": ly.cells(), "tops": []}
for c in tops:
    if c is None: continue
    bb = c.dbbox()
    t = {"name": c.name, "bbox_um": [bb.left, bb.bottom, bb.right, bb.top], "w_um": bb.width(), "h_um": bb.height(), "labels": [], "layers": {}}
    for li in ly.layer_indexes():
        info = ly.get_info(li)
        key = "%d/%d" % (info.layer, info.datatype)
        n = 0
        for s in c.shapes(li).each():
            n += 1
            if s.is_text():
                t["labels"].append({"text": s.text_string, "layer": key, "x_um": round(s.text_pos.x * ly.dbu, 4), "y_um": round(s.text_pos.y * ly.dbu, 4)})
        r = pya.Region(c.begin_shapes_rec(li))
        if not r.is_empty():
            b = r.bbox()
            t["layers"][key] = {"top_shapes": n, "bbox_um": [b.left * ly.dbu, b.bottom * ly.dbu, b.right * ly.dbu, b.top * ly.dbu], "area_um2": round(r.area() * ly.dbu * ly.dbu, 3)}
    t["instances"] = {}
    for i in c.each_inst():
        t["instances"][i.cell.name] = t["instances"].get(i.cell.name, 0) + i.size()
    res["tops"].append(t)
open(out, "w").write(json.dumps(res, indent=1))
'''


def cmd_info(a):
    d = scratch('info')
    open(os.path.join(d, 'info.py'), 'w').write(INFO_PY)
    out = os.path.join(d, 'info.json')
    p = subprocess.run(['klayout', '-b', '-r', os.path.join(d, 'info.py'), '-rd', 'gds=' + os.path.abspath(a.gds), '-rd', 'top=' + (a.top or ''), '-rd', 'out=' + out],
                       capture_output=True, text=True, stdin=subprocess.DEVNULL)
    if not os.path.exists(out):
        print(p.stdout + p.stderr)
        return 2
    print(open(out).read())
    return 0


def tool_versions():
    v = {}

    def one(cmd, pat=None, timeout=60):
        try:
            o = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout, stdin=subprocess.DEVNULL)
            t = (o.stdout + o.stderr).strip()
            if pat:
                m = re.search(pat, t)
                return m.group(1) if m else t.split('\n')[0][:80]
            return t.split('\n')[0][:80]
        except Exception as e:                                 # noqa
            return 'NOT FOUND (%s)' % type(e).__name__
    v['klayout'] = one(['klayout', '-v'], r'KLayout (\S+)')
    v['magic'] = one(['magic', '-dnull', '-noconsole', '--version'])
    v['ngspice'] = one(['ngspice', '--version'], r'ngspice-(\S+)')
    v['iverilog'] = one(['iverilog', '-V'], r'version (\S+)')
    v['yosys'] = one(['yosys', '-V'], r'Yosys (\S+)')
    v['openroad'] = one(['openroad', '-version'])
    v['librelane'] = one(['librelane', '--version'], r'LibreLane v?(\S+)', timeout=120)
    v['sta'] = one(['sta', '-version'])
    # netgen --version hangs (interactive): ask it in batch mode with a timeout
    try:
        o = subprocess.run(['netgen', '-batch', 'quit'], capture_output=True, text=True, timeout=60, stdin=subprocess.DEVNULL)
        m = re.search(r'Netgen (\S+) compiled', o.stdout + o.stderr)
        v['netgen'] = m.group(1) if m else (o.stdout + o.stderr).strip().split('\n')[0][:80]
    except Exception as e:                                     # noqa
        v['netgen'] = 'NOT FOUND (%s)' % type(e).__name__
    v['python'] = sys.version.split()[0]
    v['image'] = os.environ.get('IIC_OSIC_TOOLS_VERSION', 'unknown (IIC_OSIC_TOOLS_VERSION not set)')
    v['pdk'] = PDK
    return v


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sp = ap.add_subparsers(dest='cmd', required=True)
    for name in ('drc', 'ext', 'lvs', 'pex', 'info'):
        p = sp.add_parser(name)
        p.add_argument('--gds', required=True)
        p.add_argument('--top', required=(name != 'info'), default=None)
        p.add_argument('--out', default=OUT_DEFAULT)
        if name == 'drc':
            p.add_argument('--mode', default='flat', choices=('flat', 'deep'))
            p.add_argument('--thr', type=int, default=2)
            p.add_argument('--antenna', action='store_true')
            p.add_argument('--density', action='store_true')
            p.add_argument('--no-offgrid', dest='no_offgrid', action='store_true')
        if name in ('ext', 'lvs'):
            p.add_argument('--flatten', nargs='*', default=[])
        if name == 'lvs':
            p.add_argument('--ref', required=True)
            p.add_argument('--refcell', default=None)
            p.add_argument('--timeout', type=int, default=1800)
        if name == 'pex':
            p.add_argument('--mode', default='c', choices=('c', 'rc'))
            p.add_argument('--cthresh', type=float, default=0.01, help='fF: smaller capacitors are dropped')
            p.add_argument('--rthresh', type=float, default=1.0, help='ohm (rc mode)')
            p.add_argument('--rtol', type=float, default=10.0, help='extresist tolerance (rc mode)')
            p.add_argument('--lvsnet', default=None)
            p.add_argument('--no-mimfix', dest='no_mimfix', action='store_true', help='skip the MIM top-plate correction (evidence runs only)')
    sp.add_parser('versions')
    a = ap.parse_args()
    if getattr(a, 'out', None):
        a.out = os.path.abspath(a.out)                         # the tools run in a scratch directory
    if a.cmd == 'versions':
        print(json.dumps(tool_versions(), indent=1))
        return 0
    if a.cmd == 'ext':
        return 0 if cmd_ext(a)[0] else 2
    return {'drc': cmd_drc, 'lvs': cmd_lvs, 'pex': cmd_pex, 'info': cmd_info}[a.cmd](a)


if __name__ == '__main__':
    sys.exit(main())
