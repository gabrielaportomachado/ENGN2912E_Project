#!/usr/bin/env python3
"""AUDIT step 3: scripted connectivity / interface consistency check (nothing is checked by eye).
Parses AFE/top/dbs_afe_top.v + stubs_analog.v, AFE/adc/rtl/*.v, rtl/dbs.v, TGATE/*, every SPICE subckt used on the chip, info.yaml, lvs_config.json,
AFE/layout/PLAN.md section 9 and the organizer's info.yaml template (copy fetched 2026-11-20: AFE/review/sim/organizer/template_info.yaml).
Prints one row per check: [OK | MISMATCH | NOTE]  id  what  detail.   usage: python3 xcheck.py [out.log]
F1 (2026-11-20, Decision 44 / 45): rows that close an audit issue carry its id in brackets ([B1] [B2] [M2] [M3] [m7]) and are summarised at the end; the LVS reference netlists of
AFE/layout/lvs (mk_lvs_netlists.py) are parsed with THIS file's SPICE reader and compared device by device with the simulation netlists; 24 pads, no REC ports."""
import re, os, sys, json
HERE = os.path.dirname(os.path.abspath(__file__))
REV = os.path.normpath(os.path.join(HERE, '..'))
AFE = os.path.normpath(os.path.join(REV, '..'))
REPO = os.path.normpath(os.path.join(AFE, '..'))
rows = []


def R(st, cid, what, detail=''):
    rows.append((st, cid, what, detail))


# ------------------------------------------------------------------ SPICE
MOS = {'nfet_03v3': 'n', 'pfet_03v3': 'p', 'nfet_06v0_nvt': 'n', 'nfet_05v0': 'n', 'pfet_05v0': 'p', 'nfet_06v0': 'n', 'pfet_06v0': 'p'}
PARAMS = {'looptest': 0, 'rmode': 0, 'rmode2': 0}


def spice_lines(path):
    raw = open(path).read().split('\n')
    out = []
    for ln in raw:
        ln = ln.split('$')[0].rstrip()
        if ln.startswith('+') and out:
            out[-1] += ' ' + ln[1:]
        else:
            out.append(ln)
    return out


class Sub:
    def __init__(self, name, ports, file):
        self.name, self.ports, self.file = name, ports, file
        self.inst = []      # (iname, nodes, model)
        self.ideal = []     # primitive R/C/V/I/B/E lines


def parse_spice(path, subs):
    cur = None
    stack = []   # conditional stack: True/False = branch active, plus 'done' flag
    for ln in spice_lines(path):
        s = ln.strip()
        if not s or s.startswith('*'):
            continue
        low = s.lower()
        if low.startswith('.subckt'):
            tk = s.split()
            ports = []
            for t in tk[2:]:
                if '=' in t or t.lower() == 'params:':
                    break
                ports.append(t.lower())
            cur = Sub(tk[1].lower(), ports, os.path.relpath(path, REPO))
            subs[cur.name] = cur
            continue
        if low.startswith('.ends'):
            cur = None
            continue
        m = re.match(r'\.(if|elseif)\s*\(\s*(\w+)\s*==\s*(\d+)\s*\)', low)
        if m:
            val = PARAMS.get(m.group(2), 0) == int(m.group(3))
            if m.group(1) == 'if':
                stack.append([val, val])
            else:
                stack[-1][0] = (not stack[-1][1]) and val
                stack[-1][1] = stack[-1][1] or val
            continue
        if low.startswith('.else'):
            stack[-1][0] = not stack[-1][1]
            continue
        if low.startswith('.endif'):
            stack.pop()
            continue
        if stack and not all(x[0] for x in stack):
            continue
        if cur is None or low.startswith('.'):
            continue
        tk = s.split()
        c = tk[0][0].lower()
        if c == 'x':
            nodes = []
            for t in tk[1:]:
                if '=' in t:
                    break
                nodes.append(t.lower())
            cur.inst.append((tk[0].lower(), nodes[:-1], nodes[-1], s))
        elif c in 'rcvibe':
            cur.ideal.append((tk[0], tk[1].lower(), tk[2].lower(), ' '.join(tk[3:])))


def flatten(subs, name, portmap=None, prefix='', acc=None):
    """returns list of (device_path, model, [(net, role)]) with nets renamed to the top level; roles d g s b / p n / a b sub / t1 t2"""
    sub = subs[name]
    if acc is None:
        acc = []
    if portmap is None:
        portmap = {p: p for p in sub.ports}

    def net(n):
        if n in portmap:
            return portmap[n]
        if n == '0':
            return '0'
        return prefix + n
    for iname, nodes, model, _ in sub.inst:
        if model in subs:
            child = subs[model]
            pm = {p: net(n) for p, n in zip(child.ports, nodes)}
            flatten(subs, model, pm, prefix + iname + '.', acc)
        elif model in MOS:
            acc.append((prefix + iname, model, list(zip([net(n) for n in nodes], ['d', 'g', 's', 'b']))))
        elif model.startswith('cap_mim'):
            acc.append((prefix + iname, model, list(zip([net(n) for n in nodes], ['p', 'n']))))
        elif model.startswith('ppolyf') or model.startswith('npolyf'):
            acc.append((prefix + iname, model, list(zip([net(n) for n in nodes], ['a', 'b', 'sub']))))
        else:
            acc.append((prefix + iname, model, [(net(n), '?') for n in nodes]))
    for nm, a, b, rest in sub.ideal:
        acc.append((prefix + nm.lower(), 'IDEAL_' + nm[0].upper(), [(net(a), 't1'), (net(b), 't2')]))
    return acc


def port_class(subs, name):
    """per port: 'gate' (touches only MOS gates: needs an external driver), 'bulk', 'io' (touches a channel / passive terminal), with the gate device types"""
    flat = flatten(subs, name)
    cls = {}
    for p in subs[name].ports:
        roles = [(dev, model, r) for dev, model, tl in flat for (n, r) in tl if n == p]
        kinds = set(r for _, _, r in roles)
        gtypes = sorted(set(MOS[m] for _, m, r in roles if r == 'g' and m in MOS))
        if not roles:
            c = 'unconnected'
        elif kinds <= {'g'}:
            c = 'gate'
        elif kinds <= {'b', 'sub'}:
            c = 'bulk'
        else:
            c = 'io'
        cls[p] = (c, gtypes, len(roles))
    return cls, flat


# ------------------------------------------------------------------ Verilog (limited parser, enough for these files)
def vstrip(txt, defines=()):
    txt = re.sub(r'/\*.*?\*/', '', txt, flags=re.S)
    txt = re.sub(r'//[^\n]*', '', txt)
    out = []
    stack = []
    for ln in txt.split('\n'):
        s = ln.strip()
        m = re.match(r'`ifdef\s+(\w+)', s)
        if m:
            v = m.group(1) in defines
            stack.append([v, v])
            continue
        if s.startswith('`else'):
            stack[-1][0] = not stack[-1][1]
            continue
        if s.startswith('`endif'):
            stack.pop()
            continue
        if s.startswith('`'):
            continue
        if stack and not all(x[0] for x in stack):
            continue
        out.append(ln)
    return '\n'.join(out)


def split_top(s, sep=','):
    out, d, cur = [], 0, ''
    for ch in s:
        if ch in '([{':
            d += 1
        elif ch in ')]}':
            d -= 1
        if ch == sep and d == 0:
            out.append(cur)
            cur = ''
        else:
            cur += ch
    if cur.strip():
        out.append(cur)
    return out


class Mod:
    def __init__(self, name):
        self.name = name
        self.ports = []     # (name, dir, width)
        self.inst = []      # (type, iname, {pin: expr}, loopvar_or_None, loopN)
        self.assign = {}
        self.body = ''


def width(rng):
    if not rng:
        return 1
    m = re.match(r'\[\s*(\d+)\s*:\s*(\d+)\s*\]', rng)
    return abs(int(m.group(1)) - int(m.group(2))) + 1 if m else None


def parse_verilog(txt, mods):
    for m in re.finditer(r'\bmodule\s+(\w+)\s*(#\s*\((?:[^()]|\([^()]*\))*\))?\s*\((.*?)\)\s*;(.*?)\bendmodule', txt, flags=re.S):
        mod = Mod(m.group(1))
        plist, body = m.group(3), m.group(4)
        mod.body = body
        cur_dir, cur_w = None, 1
        for item in split_top(plist):
            it = item.strip()
            mm = re.match(r'(input|output|inout)\s*(reg|wire)?\s*(\[[^\]]+\])?\s*(\w+)$', it)
            if mm:
                cur_dir, cur_w = mm.group(1), width(mm.group(3))
                mod.ports.append((mm.group(4), cur_dir, cur_w))
            elif re.match(r'\w+$', it):
                mod.ports.append((it, cur_dir, cur_w))
        if any(d is None for _, d, _ in mod.ports):      # non-ANSI: read the declarations in the body
            decl = {}
            for mm in re.finditer(r'\b(input|output|inout)\s*(reg|wire)?\s*(\[[^\]]+\])?\s*([^;]+);', body):
                for n in mm.group(4).split(','):
                    decl[n.strip().split()[0]] = (mm.group(1), width(mm.group(3)))
            mod.ports = [(n, decl.get(n, (None, 1))[0], decl.get(n, (None, 1))[1]) for n, _, _ in mod.ports]
        for mm in re.finditer(r'\bassign\s+(#[\d.]+\s+)?([\w\[\]:+* ]+?)\s*=\s*([^;]+);', body):
            mod.assign[mm.group(2).strip()] = mm.group(3).strip()
        # generate-for loops (one level): remember the span
        loops = [(g.start(), g.end(), g.group(1), int(g.group(2))) for g in re.finditer(r'generate\s+for\s*\(\s*(\w+)\s*=\s*0\s*;\s*\w+\s*<\s*(\d+)\s*;[^)]*\)\s*begin.*?endgenerate', body, flags=re.S)]
        for mm in re.finditer(r'(?:\(\*[^)]*\*\)\s*)?\b(\w+)\s*(#\s*\((?:[^()]|\([^()]*\))*\))?\s+(\w+)\s*\(\s*(\.(?:[^;]|\n)*?)\)\s*;', body):
            typ, iname, conns = mm.group(1), mm.group(3), mm.group(4)
            if typ in ('module', 'assign', 'always', 'if', 'else', 'for', 'begin', 'generate', 'wire', 'reg'):
                continue
            pins = {}
            for c in split_top(conns):
                cm = re.match(r'\s*\.(\w+)\s*\((.*)\)\s*$', c.strip(), flags=re.S)
                if cm:
                    pins[cm.group(1)] = cm.group(2).strip()
            lv = None
            for (a, b, v, n) in loops:
                if a <= mm.start() < b:
                    lv = (v, n)
            mod.inst.append((typ, iname, pins, lv))
        mods[mod.name] = mod


# ------------------------------------------------------------------ F1: the LVS reference netlists (AFE/layout/lvs, written by AFE/layout/scripts/mk_lvs_netlists.py)
LVS_DIR = os.path.join(AFE, 'layout', 'lvs')
REMOVED = r'rbrk|rt|rmm|cpm|cpb\d+|cpbd'            # ideal elements that AUDIT 4.9.3 rule 2 removes
JOINED = {'xs1_vng': 'xs1_vn', 'xs2_vng2': 'xs2_vn2'}   # nets joined when Rbrk is removed
MIM_SIM, MIM_LVS = 'cap_mim_2f0_m2m3_noshield', 'cap_mim_2f0_m4m5_noshield'


def lvs_equiv(simsubs, lvssubs, cell):
    """device-by-device comparison of the LVS reference cell with the flattened simulation cell under the rules of AUDIT 4.9.3.  -> (number of devices compared, list of differences)"""
    us = lambda s: s.replace('.', '_')
    net = lambda n: JOINED.get(us(n), us(n))
    got = {d: (m, [(nn, r) for nn, r in tl]) for d, m, tl in flatten(lvssubs, cell)}
    exp = {}
    for d, m, tl in flatten(simsubs, cell):
        base = d.split('.')[-1]
        nets = [net(nn) for nn, r in tl]
        if m.startswith('IDEAL_'):
            if re.fullmatch(REMOVED, base):
                continue
            if re.fullmatch(r'cxa[12]', base):
                exp['x' + us(d)] = (MIM_LVS, list(zip(nets, ['p', 'n'])))        # rule 3: one MIM unit, same two nets, first net = top plate
                continue
            exp[us(d)] = ('UNHANDLED ' + m, [])
            continue
        if m == MIM_SIM and re.fullmatch(r'xcin[12]', base):
            pieces = sorted(k for k in got if re.fullmatch(re.escape(us(d)) + r'_\d+', k))
            for k in pieces or [us(d) + '_1']:
                exp[k] = (MIM_LVS, list(zip(nets, ['p', 'n'])))                 # rule 4: N pieces in parallel, same plates
            continue
        exp[us(d)] = (MIM_LVS if m == MIM_SIM else m, list(zip(nets, [r for nn, r in tl])))
    diff = []
    for k in sorted(set(exp) | set(got)):
        if exp.get(k) != got.get(k):
            diff.append('%s: expected %s, LVS has %s' % (k, exp.get(k), got.get(k)))
    return len(exp), diff


def lvs_sizes(path, cell):
    """{device name: (model, {param: value in um})} of one flat cell of an LVS reference file (numbers as written)"""
    out, cur = {}, False
    for ln in spice_lines(path):
        tk = ln.split()
        if not tk:
            continue
        if tk[0].lower() == '.subckt':
            cur = tk[1].lower() == cell
            continue
        if tk[0].lower().startswith('.ends'):
            cur = False
            continue
        if cur and tk[0][0].lower() == 'x':
            par = {a.split('=')[0].lower(): a.split('=')[1] for a in tk if '=' in a}
            model = [a for a in tk[1:] if '=' not in a][-1].lower()
            out[tk[0].lower()] = (model, {k: (float(v[:-1]) if v.endswith('u') else float(v)) for k, v in par.items()})
    return out


def main():
    out = open(sys.argv[1], 'w') if len(sys.argv) > 1 else sys.stdout
    subs = {}
    for f in ['AFE/amp/spice/afe_chc.spice', 'AFE/amp/spice/stage1c.spice', 'AFE/amp/spice/stage2c.spice', 'AFE/amp/spice/ota1.spice', 'AFE/amp/spice/ota2.spice', 'AFE/amp/spice/pseudoR.spice',
              'AFE/amp/spice/bias_genc.spice', 'AFE/amp/spice/fs_oneshot_c.spice', 'AFE/adc/spice/dac_sw.spice', 'AFE/adc/spice/dac_units.spice', 'AFE/adc/spice/comparator.spice', 'AFE/adc/spice/vhalf.spice',
              'TGATE/TGATE.spice']:
        parse_spice(os.path.join(REPO, f), subs)
    mods = {}
    for f, d in [('AFE/top/dbs_afe_top.v', ()), ('AFE/top/stubs_analog.v', ()), ('AFE/adc/rtl/adc8_top.v', ()), ('AFE/adc/rtl/adc_sar_ch.v', ()), ('AFE/adc/rtl/adc_clkgen.v', ()),
                 ('AFE/adc/rtl/adc_dlychain.v', ()), ('rtl/dbs.v', ()), ('TGATE/TGATE.v', ())]:
        parse_verilog(vstrip(open(os.path.join(REPO, f)).read(), d), mods)
    ANA = ['afe_chc', 'fs_oneshot_c', 'bias_genc', 'dac_sw', 'cmp_p', 'vhalf', 'vrefs']

    # ---- C1: stub ports == SPICE ports (names and order)
    for c in ANA:
        vp = [p for p, _, _ in mods[c].ports]
        sp = subs[c].ports
        if vp == sp:
            R('OK', 'C1', 'stub %s ports = SPICE subckt ports (order too)' % c, '%d pins: %s' % (len(sp), ' '.join(sp)))
        else:
            R('MISMATCH', 'C1', 'stub %s ports != SPICE subckt' % c, 'verilog: %s | spice (%s): %s' % (' '.join(vp), subs[c].file, ' '.join(sp)))
    # ---- C2: TGATE views
    tv = [p for p, _, _ in mods['TGATE'].ports]
    ts = subs['tgate'].ports
    lef = re.findall(r'^\s*PIN (\w+)', open(os.path.join(REPO, 'TGATE/TGATE.lef')).read(), flags=re.M)
    ext = re.search(r'\.SUBCKT TGATE (.*)', open(os.path.join(REPO, 'TGATE/TGATE_extracted.cir')).read()).group(1).split()
    sig = lambda l: sorted(x.lower() for x in l if x.lower() not in ('vdd', 'vss', 'sub'))
    R('OK' if sig(tv) == sig(ts) == sig(lef) == sig(ext) else 'MISMATCH', 'C2', 'TGATE signal pins agree in .v / .spice / .lef / extracted .cir', 'v: %s | spice: %s | lef: %s | cir: %s' % (' '.join(tv), ' '.join(ts), ' '.join(lef), ' '.join(ext)))
    R('NOTE', 'C2', 'TGATE power pins', 'SPICE and LEF have VDD / VSS (PMOS bulk = VDD, NMOS bulk = VSS); TGATE.v has none and afe_ch connects none: the 5 V-device macro relies on implicit power in LVS; '
      'extracted .cir has only SUB (PMOS bulk is the unnamed net $8): the macro LVS view is not pin-compatible with TGATE.spice')
    r = re.findall(r'(pfet_\w+|nfet_\w+) L=(\S+) W=(\S+)', open(os.path.join(REPO, 'TGATE/TGATE.spice')).read())
    R('NOTE', 'C2', 'TGATE devices', '; '.join('%s W=%s L=%s' % (a, w, l) for a, l, w in r) + ' (5 V devices on the single 3.3 V supply, Decision 30)')

    # ---- port classes of the analog cells from the flattened SPICE
    PC = {}
    FL = {}
    for c in ANA + ['tgate']:
        PC[c], FL[c] = port_class(subs, c)
    STD = {'gf180mcu_fd_sc_mcu7t5v0__or2_1': {'A1': 'gate', 'A2': 'gate', 'Z': 'drv'}, 'gf180mcu_fd_sc_mcu7t5v0__inv_1': {'I': 'gate', 'ZN': 'drv'}}

    # ---- C3 / C4: afe_ch instances and net census
    ch = mods['afe_ch']
    chports = {p: d for p, d, _ in ch.ports}
    nets = {}
    for typ, iname, pins, lv in ch.inst:
        key = typ.lower()
        if key in subs:
            sp = subs[key].ports
            vp = [p.lower() for p in pins]
            miss = [p for p in sp if p not in vp and p not in ('vdd', 'vss')]
            extra = [p for p in vp if p not in sp]
            if miss or extra:
                R('MISMATCH', 'C3', 'afe_ch.%s (%s) pin connections' % (iname, typ), 'unconnected SPICE pins: %s; pins not in the SPICE subckt: %s' % (miss or '-', extra or '-'))
            else:
                nopow = [p for p in ('vdd', 'vss') if p in sp and p not in vp]
                R('OK', 'C3', 'afe_ch.%s (%s): every SPICE pin connected by name' % (iname, typ), ('%d pins' % len(sp)) + ((' (power pins %s implicit)' % nopow) if nopow else ''))
            for p, e in pins.items():
                c, gt, n = PC[key].get(p.lower(), ('?', [], 0))
                nets.setdefault(e, []).append(('%s.%s' % (iname, p), {'gate': 'gate', 'io': 'io', 'bulk': 'bulk', 'unconnected': 'nc'}.get(c, '?'), ''.join(gt)))
        elif typ in STD:
            for p, e in pins.items():
                nets.setdefault(e, []).append(('%s.%s' % (iname, p), STD[typ][p], ''))
        else:
            R('MISMATCH', 'C3', 'afe_ch.%s: unknown cell type %s' % (iname, typ))
    chw = {p: w for p, _, w in ch.ports}
    for n, d in chports.items():
        role = {'input': 'drv', 'output': 'load', 'inout': 'io'}[d]
        if chw[n] > 1:                                   # vector port: one net per bit (the instances connect bit-selects)
            for k in range(chw[n]):
                nets.setdefault('%s[%d]' % (n, k), []).append(('port:%s[%d]' % (n, k), role, ''))
        else:
            nets.setdefault(n, []).append(('port:' + n, role, ''))
    P = []
    for n in sorted(nets):
        con = nets[n]
        drv = [c for c, k, _ in con if k == 'drv']
        io = [c for c, k, _ in con if k == 'io']
        gate = [c + ('(%s)' % g if g else '') for c, k, g in con if k == 'gate']
        load = [c for c, k, _ in con if k == 'load']
        st = 'OK'
        why = ''
        if not drv and not io:
            st, why = 'MISMATCH', 'FLOATING: only gates on this net'
        elif len(drv) > 1:
            st, why = 'MISMATCH', 'more than one digital driver'
        elif len(con) == 1:
            st, why = 'NOTE', 'single connection (open)'
        P.append((st, n, drv, io, gate, load, why))
        if st != 'OK':
            R(st, 'C4', 'afe_ch net %s' % n, '%s: %s' % (why, ' '.join(c for c, _, _ in con)))
    R('OK' if all(p[0] != 'MISMATCH' for p in P) else 'MISMATCH', 'C4', 'afe_ch: %d nets, every gate-only pin has a driver or a DC path, no net has two digital drivers' % len(P), 'net table below')

    # ---- C5: top-level buses and per-channel slices
    top = mods['dbs_afe_top']
    adc = {p: (d, w) for p, d, w in mods['adc8_top'].ports}
    u = [i for i in top.inst if i[0] == 'afe_ch'][0]
    lv, n = u[3]
    seen = {}
    bad = []
    for i in range(n):
        for pin, e in u[2].items():
            m = re.match(r'(\w+)\[(.+)\]$', e)
            if not m:
                seen.setdefault(e, set()).add('all')
                continue
            base, idx = m.group(1), m.group(2)
            if '+:' in idx:
                a, b = idx.split('+:')
                lo = eval(a.replace(lv, str(i)))
                bits = range(lo, lo + int(b))
            else:
                bits = [eval(idx.replace(lv, str(i)))]
            for b_ in bits:
                if b_ in seen.setdefault(base, set()):
                    bad.append('%s[%d] used twice' % (base, b_))
                seen[base].add(b_)
    exp_w = {'E': 8, 'IPG': 8, 'sw_rec': 8, 'sw_rec_b': 8, 'sw_ipg': 8, 'sw_ipg_b': 8, 'rst_sw': 8, 'tg_on': 8, 'cmp_clk': 8, 'dac_gdn': 8, 'cmp_q': 8, 'dac_gp': 96, 'dac_gn': 96}
    for b_, w in exp_w.items():
        got = seen.get(b_, set())
        if got != set(range(w)):
            bad.append('%s: bits used %d of %d' % (b_, len(got), w))
    R('OK' if not bad else 'MISMATCH', 'C5', 'dbs_afe_top generate loop (N = %d): every bit of the 13 per-channel buses is used exactly once' % n, '; '.join(bad) if bad else ', '.join('%s[%d]' % (k, v) for k, v in exp_w.items()))
    ua = [i for i in top.inst if i[0] == 'adc8_top'][0]
    wb = []
    for pin, e in ua[2].items():
        dw = adc[pin][1]
        mm = re.search(r'\bwire\s*(\[[^\]]+\])?\s*([^;]*\b%s\b[^;]*);' % re.escape(e), top.body)
        ew = width(mm.group(1)) if mm else (1 if e in [p for p, _, _ in top.ports] else None)
        if e in [p for p, _, _ in top.ports]:
            ew = [w for p, _, w in top.ports if p == e][0]
        if ew != dw:
            wb.append('%s(%s): port %s wide, net %s' % (pin, e, dw, ew))
    R('OK' if not wb else 'MISMATCH', 'C5', 'adc8_top instance: net widths = port widths (%d ports, all connected: %s)' % (len(ua[2]), 'yes' if set(ua[2]) == set(adc) else 'NO: ' + str(set(adc) ^ set(ua[2]))), '; '.join(wb))
    ud = [i for i in top.inst if i[0] == 'dbs_ctrl'][0]
    dports = {p: (d, w) for p, d, w in mods['dbs_ctrl'].ports}
    R('OK' if set(ud[2]) == set(dports) else 'MISMATCH', 'C11', 'dbs_ctrl #(8): all ports connected; exports sw_rec sw_rec_b sw_ipg sw_ipg_b', 'clk = %s, rstn = %s, mode = %s, en = %s, ready = %s' % tuple(ud[2][k] for k in ('clk', 'rstn', 'mode', 'en', 'ready')))
    used = set(re.findall(r'\.(sw_rec|sw_rec_b|sw_ipg|sw_ipg_b)\(', ''.join('.%s(' % p for p in u[2])))
    cons = {s: [c for c, _, _ in nets.get(s, []) if not c.startswith('port:')] for s in ('sw_rec', 'sw_rec_b', 'sw_ipg', 'sw_ipg_b')}
    R('OK' if all(cons.values()) else 'MISMATCH', 'C11', 'consumers of the dbs_ctrl outputs inside afe_ch', '; '.join('%s -> %s' % (k, ' '.join(v)) for k, v in cons.items()))

    # ---- C6: control polarity from the device types (SPICE) against the RTL expressions
    def gates(cell, pin):
        return sorted(set('%s:%s' % (MOS[m], d.split('.')[-1]) for d, m, tl in FL[cell] for (nn, r) in tl if nn == pin and r == 'g' and m in MOS))
    sar = mods['adc_sar_ch']
    a8 = mods['adc8_top']
    db = open(os.path.join(REPO, 'rtl/dbs.v')).read()
    rtl = {'gp': sar.assign.get('gp'), 'gn': sar.assign.get('gn'), 'rst_sw': a8.assign.get('rst_sw[i]'), 'dac_gdn': a8.assign.get('dac_gdn[i]'), 'dout_oe': a8.assign.get('dout_oe'),
           'sw_rec_b': re.search(r'sw_rec_b\[i\]\s*=\s*([^;]+);', db).group(1), 'sw_rec': re.search(r'sw_rec\[i\]\s*=\s*([^;]+);', db).group(1),
           'trk': re.search(r'wire\s+trk\s*=\s*([^;]+);', a8.body).group(1), 'tg_on': 'dlyd_1(trk)' if re.search(r'dlyd_1\s+utg\s*\(\.I\(trk\),\s*\.Z\(tg_on\[i\]\)\)', a8.body) else None}
    POL = [  # cell, pin, net in afe_ch, expected device(s), meaning, rtl
        ('tgate', 'c', 'sw_rec / sw_ipg', ['n'], 'NMOS gate: switch closed when HIGH', 'sw_rec = ' + rtl['sw_rec'] + '  (= ready & rec_en & en_reg_2)'),
        ('tgate', 'cbar', 'sw_rec_b / sw_ipg_b', ['p'], 'PMOS gate: switch closed when LOW', 'sw_rec_b = ' + rtl['sw_rec_b']),
        ('afe_chc', 'pkc', 'sw_rec_b', ['n'], 'park NMOS on when HIGH = routing switch open', ''),
        ('afe_chc', 'pkcb', 'sw_rec', ['p'], 'park PMOS on when LOW = routing switch open', ''),
        ('afe_chc', 'fs', 'fs (OR2 of fs_os, rst_amp)', ['n', 'p'], 'PMOS = normal tap when LOW, NMOS = reset level when HIGH: reset active HIGH', ''),
        ('fs_oneshot_c', 'trig', 'sw_rec', ['n', 'p'], 'PMOS Xpu holds the timer node while LOW; NAND input: pulse starts on the RISING edge', ''),
        ('dac_sw', 'rst', 'rst_sw', ['n'], 'plate reset NMOS closed when HIGH (tracking)', 'rst_sw = trk = ' + rtl['trk']),
        ('dac_sw', 'rstm', 'rst_sw', ['n'], 'M-node reset NMOS closed when HIGH (same net as rst: I0 mismatch 4)', ''),
        ('dac_sw', 'sam', 'tg_on', ['n'], 'sampling TG NMOS on when HIGH', 'tg_on = ' + str(rtl['tg_on'])),
        ('dac_sw', 'samb', 'samb = inv_1(tg_on)', ['p'], 'sampling TG PMOS on when LOW', ''),
        ('dac_sw', 'gp11', 'dac_gp[11]', ['p'], 'driver PMOS: bottom to VDD when LOW', 'gp = ' + rtl['gp']),
        ('dac_sw', 'gn11', 'dac_gn[11]', ['n'], 'driver NMOS: bottom to VSS when HIGH', 'gn = ' + rtl['gn']),
        ('dac_sw', 'gdp', 'vdd_dac', ['p'], 'dummy driver PMOS: tied HIGH (to its own source rail vdd_dac) = always off', ''),
        ('dac_sw', 'gdn', 'dac_gdn', ['n'], 'dummy bottom grounded when HIGH', 'dac_gdn = ' + rtl['dac_gdn']),
        ('vrefs', 'c', 'tg_on', ['n'], 'Cref TG NMOS on when HIGH (tracking)', ''),
        ('vrefs', 'cb', 'samb', ['p'], 'Cref TG PMOS on when LOW', ''),
        ('cmp_p', 'clk', 'cmp_clk', ['n', 'p'], 'precharge PMOS on when LOW, evaluate when HIGH (clkb inverter inside)', ''),
    ]
    for cell, pin, netn, expd, mean, rt in POL:
        g = gates(cell, pin)
        types = sorted(set(x.split(':')[0] for x in g))
        # the actual net on that pin in afe_ch
        act = [e for typ, iname, pins, _ in ch.inst if typ.lower() == cell for p, e in pins.items() if p.lower() == pin]
        R('OK' if types == sorted(expd) else 'MISMATCH', 'C6', 'polarity %s.%s <- %s' % (cell, pin, ' / '.join(sorted(set(act))) or netn), 'gate of %s | %s%s' % (' '.join(g), mean, (' | RTL: ' + rt) if rt else ''))
    R('OK' if rtl['gp'] and rtl['gn'] else 'MISMATCH', 'C6', 'crowbar by construction', 'gp = %s, gn = %s: gp LOW and gn HIGH cannot both be true for one bit (en & code vs en & ~code); skew between the two gates is not in the RTL' % (rtl['gp'], rtl['gn']))
    cmpi = [pins for typ, iname, pins, _ in ch.inst if typ == 'cmp_p'][0]
    R('OK' if cmpi['inp'] == 'vref' and cmpi['inn'] == 't' and cmpi['outp'] == 'cmp_q' else 'MISMATCH', 'C6', 'comparator sense', 'inp = %s (reference), inn = %s (plate), outp -> %s: cmp_q = 1 when reference > plate = Vin >= trial (adc_sar_ch convention); outn -> %s (open)' % (cmpi['inp'], cmpi['inn'], cmpi['outp'], cmpi['outn']))

    # ---- C7 / C8: REF and vhalf
    refs = [e for pin, e in u[2].items() if pin == 'ref']
    amp_ref = [pins['ref'] for typ, iname, pins, _ in ch.inst if typ == 'afe_chc']
    R('OK' if refs == ['REF'] and amp_ref == ['ref'] and n == 8 else 'MISMATCH', 'C7', 'REF pad reaches afe_chc.ref of all 8 channels', 'dbs_afe_top: afe_ch.ref <- %s in the generate loop (N = %d); afe_ch: afe_chc.ref <- %s' % (refs, n, amp_ref))
    vh = [c for c, _, _ in nets.get('vcmd', [])]
    R('OK' if sorted(vh) == ['u_dac.vcm', 'u_vh.out', 'u_vr.in'] else 'MISMATCH', 'C8', 'one vhalf per ADC (inside afe_ch), its node is local', 'net vcmd: %s; not a port of afe_ch: %s' % (' '.join(sorted(vh)), 'vcmd' not in chports))
    R('NOTE', 'C8', 'bias_genc.vcm_out no longer feeds the ADC', 'vcmo consumers in afe_ch: %s' % ' '.join(c for c, _, _ in nets.get('vcmo', [])))

    # ---- C9: info.yaml against the top-level ports and the organizer template
    y = open(os.path.join(REPO, 'info.yaml')).read()
    pins = re.findall(r'-\s*name:\s*(\S+)\s*\n\s*io_type:\s*(\S+)', y)
    tports = {p: (d, w) for p, d, w in top.ports}
    R('OK' if len(pins) == 24 else 'MISMATCH', 'C9', 'info.yaml pin count = 24 (Decision 45: 17 analog + 5 digital + VDD + VSS)', '%d pins: %s' % (len(pins), ', '.join('%s x%d' % (t, sum(1 for _, tt in pins if tt == t)) for t in sorted(set(t for _, t in pins)))))
    need = {'input_cmos': ['_PD', '_PU'], 'input_schmitt': ['_PD', '_PU'], 'bidirectional': ['_PD', '_PU', '_CS', '_SL', '_IE', '_OE', '_PDRV0', '_PDRV1'], 'bidirectional_24ma': ['_PD', '_PU', '_CS', '_SL', '_IE', '_OE']}
    tmpl = open(os.path.join(REV, 'sim', 'organizer', 'template_info.yaml')).read() if os.path.exists(os.path.join(REV, 'sim', 'organizer', 'template_info.yaml')) else ''
    for nme, t in pins:
        base = re.sub(r'\[\d+\]$', '', nme)
        idx = re.search(r'\[(\d+)\]$', nme)
        if t == 'analog':
            ok = base in tports and tports[base][0] == 'inout' and (not idx or int(idx.group(1)) < tports[base][1])
            if not ok:
                R('MISMATCH', 'C9', 'pad %s (analog)' % nme, 'no matching inout port')
        elif t in ('power', 'ground'):
            if not (base in tports and tports[base][0] == 'inout'):
                R('MISMATCH', 'C9', 'pad %s (%s)' % (nme, t), 'no matching inout port')
        elif t.startswith('input'):
            miss = [base + s for s in need[t] if base + s not in tports or tports[base + s][0] != 'output']
            undr = [base + s for s in need[t] if base + s not in top.assign]
            ok = base in tports and tports[base][0] == 'input' and not miss and not undr
            R('OK' if ok else 'MISMATCH', 'C9', 'pad %s (%s): input port + _PU / _PD driven' % (nme, t), ', '.join('%s%s = %s' % (base, s, top.assign.get(base + s)) for s in need[t]) + ('; missing ' + str(miss) if miss else ''))
        elif t.startswith('bidirectional'):
            miss = [base + s for s in need[t] if base + s not in tports]
            R('OK' if not miss else 'MISMATCH', 'C9', 'pad %s (%s): 8 control pins exist and are driven' % (nme, t), ', '.join('%s%s = %s' % (base, s, top.assign.get(base + s)) for s in need[t]))
            io_ok = (base + '_OUT') in tports and (base + '_IN') in tports
            io_ok = io_ok and tports[base + '_OUT'][0] == 'output' and tports[base + '_IN'][0] == 'input' and base not in tports
            R('OK' if io_ok else 'MISMATCH', 'C9', '[B2] pad %s (%s): organizer template wants <name>_OUT (-> A) and <name>_IN (<- Y)' % (nme, t),
              'port %s: %s; %s_OUT: %s, %s_IN: %s  [template_info.yaml lines 42-45]' % (base, tports.get(base, ('absent',))[0], base, tports.get(base + '_OUT', ('ABSENT',))[0], base, tports.get(base + '_IN', ('ABSENT',))[0]))
            drv = [i for i in top.inst if any(e == base + '_OUT' for e in i[2].values())]
            use = [i for i in top.inst if any(re.search(r'\b%s_IN\b' % base, e) for e in i[2].values())] + [k for k, v in top.assign.items() if re.search(r'\b%s_IN\b' % base, v)]
            R('OK' if len(drv) == 1 and not use else 'MISMATCH', 'C9', '[B2] %s_OUT has one driver, %s_IN is unused' % (base, base),
              '%s_OUT <- %s; %s_IN loads: %s (the pad input buffer is off: %s_IE = %s)' % (base, ', '.join('%s.%s' % (i[1], [p for p, e in i[2].items() if e == base + '_OUT'][0]) for i in drv) or 'NONE', base, use or 'none', base, top.assign.get(base + '_IE')))
    allpad = set(re.sub(r'\[\d+\]$', '', nme) for nme, _ in pins)
    ctl = set(base + s for nme, t in pins if t in need for base in [re.sub(r'\[\d+\]$', '', nme)] for s in need[t])
    bid = set(base + s for nme, t in pins if t.startswith('bidirectional') for base in [re.sub(r'\[\d+\]$', '', nme)] for s in ('_OUT', '_IN'))
    allpad = (allpad - set(b[:-4] for b in bid if b.endswith('_OUT'))) | bid          # a bidirectional pad <name> appears on the top as <name>_OUT and <name>_IN
    extra = [p for p in tports if p not in allpad and p not in ctl]
    R('OK' if 'REC' not in tports and 'rec' not in chports and not any(nme.startswith('REC') for nme, _ in pins) else 'MISMATCH', 'C9', 'no REC pad / port (Decision 45): rec is an internal net of afe_ch',
      'top port REC: %s; afe_ch port rec: %s; info.yaml REC entries: %d; net rec inside afe_ch: %s' % ('present' if 'REC' in tports else 'absent', 'present' if 'rec' in chports else 'absent',
                                                                                                   sum(1 for nme, _ in pins if nme.startswith('REC')), ' '.join(c for c, _, _ in nets.get('rec', [])) or 'ABSENT'))
    R('OK' if not extra else 'MISMATCH', 'C9', 'top-level ports that are neither a pad nor a pad-control pin', ' '.join(extra) or 'none')
    R('OK' if top.assign.get('DOUT_OE') == 'dout_oe' and rtl['dout_oe'] == '~cs_n' else 'MISMATCH', 'C9', 'DOUT_OE = ~CS', 'dbs_afe_top: DOUT_OE = %s; adc8_top: dout_oe = %s' % (top.assign.get('DOUT_OE'), rtl['dout_oe']))
    R('OK' if top.assign.get('RSTN_PD') == "1'b1" and top.assign.get('RSTN_PU') == "1'b0" else 'MISMATCH', 'C9', 'RSTN pull-down on', 'RSTN_PD = %s, RSTN_PU = %s' % (top.assign.get('RSTN_PD'), top.assign.get('RSTN_PU')))
    st = [i + 1 for i, l in enumerate(y.split('\n')) if 'DOUT_OE=1' in l]
    R('MISMATCH' if st else 'OK', 'C9', '[m1] stale comment in info.yaml', ('line %s says "tie DOUT_OE=1"; the design has DOUT_OE = ~CS (Decision 41d)' % st) if st else 'none')
    R('NOTE', 'C9', 'bracketed pad names', 'info.yaml uses E[0] .. IPG[7]; the organizer template uses plain identifiers (vss, reset_n, gpio0 ...): whether bus-bit names are accepted is an organizer question')
    R('NOTE', 'C9', 'pad-control values', 'DOUT: PDRV1:0 = 00 (4 mA per the template), SL = 0 (fast), CS = 0 (CMOS), IE = 0 (input off): match the template meanings; values still to be confirmed (Decision 41d)')
    ec = re.search(r'export_control:\s*"([^"]+)"', y).group(1)
    R('OK' if os.path.exists(os.path.join(REPO, ec)) else 'MISMATCH', 'C9', 'export-control document named in info.yaml exists', ec)
    for k in ('gf_def_ready', 'ws_def_ready', 'drc_ready', 'lvs_ready'):
        v = re.search(r'%s:\s*(\w+)' % k, y)
        R('NOTE', 'C9', 'info.yaml %s' % k, v.group(1) if v else 'absent')

    # ---- C10: lvs_config.json
    j = json.load(open(os.path.join(REPO, 'lvs_config.json')))
    tsrc = j['TOP_SOURCE']

    def ex(s):
        return s.replace('$TOP_SOURCE', tsrc).replace('$TOP_LAYOUT', j['TOP_LAYOUT'].replace('$TOP_SOURCE', tsrc)).replace('$UPRJ_ROOT', REPO)
    R('OK' if tsrc in mods else 'MISMATCH', 'C10', 'lvs_config TOP_SOURCE is a module that exists', '%s (defined in AFE/top/dbs_afe_top.v); organizer template uses the macro name they assign (A01_topcell style): name still open' % tsrc)
    for k in ('LVS_SPICE_FILES', 'LVS_VERILOG_FILES'):
        for f in j[k]:
            R('OK' if os.path.exists(ex(f)) else 'MISMATCH', 'C10', 'lvs_config %s' % k, '%s -> %s' % (f, 'exists' if os.path.exists(ex(f)) else 'DOES NOT EXIST (no spice/, verilog/gl/ directory in the repo yet)'))
    gds = ex(j['LAYOUT_FILE'])
    R('OK' if os.path.exists(gds) else 'MISMATCH', 'C10', 'lvs_config LAYOUT_FILE', '%s -> %s' % (j['LAYOUT_FILE'], ('exists (%d bytes%s)' % (os.path.getsize(gds), ': the 1000 x 1000 um PR-boundary placeholder of Decision 45, replaced by the layout in L3a' if os.path.getsize(gds) < 2000 else '')) if os.path.exists(gds) else 'DOES NOT EXIST'))
    L = {}                                   # the LVS reference files, read with this file's SPICE parser
    for f in ('afe_chc.spice', 'adc_ch.spice', 'bias_genc.spice', 'dbs_afe_top.spice'):
        if os.path.exists(os.path.join(LVS_DIR, f)):
            L[f] = {}
            parse_spice(os.path.join(LVS_DIR, f), L[f])
    tsub = L.get('dbs_afe_top.spice', {}).get('dbs_afe_top')
    tcls = {}
    for i_, nd_, m_, r_ in (tsub.inst if tsub else []):
        tcls[m_] = tcls.get(m_, 0) + 1
    R('OK' if tsub and tcls.get('afe_dig') == 1 and tcls.get('afe_ch') == 8 and tcls.get('bias_genc') == 1 else 'MISMATCH', 'C10', '[M3] LVS source structure: a SPICE top reference with the digital macro as a black box',
      ('AFE/layout/lvs/dbs_afe_top.spice: ' + ', '.join('%s x%d' % kv for kv in sorted(tcls.items())) + '; afe_dig is an empty .subckt until L1d delivers its powered netlist (mk_lvs_netlists.py --dig-netlist); '
       'lvs_config.json still names spice/<top>.spice and verilog/gl/<top>.v: filled in L4') if tsub else 'AFE/layout/lvs/dbs_afe_top.spice not found: run AFE/layout/scripts/mk_lvs_netlists.py')
    R('OK' if 'afe_dig' in mods else 'MISMATCH', 'C10', 'module afe_dig (L1d macro) exists in the repo', 'not yet: AFE/dig/ is created by L1d')

    # ---- C12: ideal elements and device names: simulation netlists (information) and the LVS reference written from them (F1, AUDIT 4.9.3)
    HOME = {'afe_chc': 'afe_chc.spice', 'fs_oneshot_c': 'afe_chc.spice', 'bias_genc': 'bias_genc.spice', 'dac_sw': 'adc_ch.spice', 'cmp_p': 'adc_ch.spice', 'vhalf': 'adc_ch.spice', 'vrefs': 'adc_ch.spice'}
    for c in ANA:
        idl = [(d, m) for d, m, tl in FL[c] if m.startswith('IDEAL_')]
        cnt = {}
        for d, m, tl in FL[c]:
            cnt[m] = cnt.get(m, 0) + 1
        R('NOTE', 'C12', 'device census %s (simulation netlist)' % c, ', '.join('%s x%d' % (k, v) for k, v in sorted(cnt.items())))
        if c in ('bias_genc', 'vhalf') or cnt.get('ppolyf_u_3k'):
            R('MISMATCH' if cnt.get('ppolyf_u_3k') else 'OK', 'C12', '[B1] %s: the high-resistance poly is ppolyf_u_1k (the only HRES device of gf180mcuD)' % c,
              'ppolyf_u_3k x%d, ppolyf_u_1k x%d (KLayout LVS variant D sets poly_res = 1k; netgen setup and the Magic tech know only ppolyf_u_1k; organizer table "Resistor HRES 1k")' % (cnt.get('ppolyf_u_3k', 0), cnt.get('ppolyf_u_1k', 0)))
        f = HOME[c]
        simid = ', '.join(sorted(set(d.split('.')[-1] + ('' if len(d.split('.')) == 1 else ' (in %s)' % '.'.join(d.split('.')[:-1])) for d, m in idl)))[:300]
        if f not in L or c not in L[f]:
            R('MISMATCH', 'C12', '[M3] LVS reference of %s' % c, 'AFE/layout/lvs/%s not found (run AFE/layout/scripts/mk_lvs_netlists.py); ideal elements of the simulation netlist: %s' % (f, simid or 'none'))
            continue
        lf = flatten(L[f], c)
        lid = [d for d, m, tl in lf if m.startswith('IDEAL_')]
        lm23 = sum(1 for d, m, tl in lf if m == MIM_SIM)
        n_, diff = lvs_equiv(subs, L[f], c)
        same_top = ('dbs_afe_top.spice' in L and c in L['dbs_afe_top.spice'] and flatten(L['dbs_afe_top.spice'], c) == lf)
        ok_ = not lid and not lm23 and not diff and same_top
        R('OK' if ok_ else 'MISMATCH', 'C12', '[M3] LVS reference of %s: no ideal element, m4m5 MIM, equal to the simulation netlist under the AUDIT 4.9.3 rules' % c,
          'AFE/layout/lvs/%s: %d devices compared terminal by terminal with the flattened simulation netlist, %d differences%s; ideal elements left: %d; m2m3 MIM left: %d; same cell text in dbs_afe_top.spice: %s; '
          'simulation netlist has %s' % (f, n_, len(diff), (' (' + '; '.join(diff[:2])[:300] + ')') if diff else '', len(lid), lm23, 'yes' if same_top else 'NO',
                                         ('the ideal elements ' + simid + ' (removed or replaced by the script)') if simid else 'no ideal element'))
    # ---- m7: Cref one plate, Cin in pieces
    pa = dict(re.findall(r'(CAPK_A|CAPK_P|CF1V|CIN_RATIO)=(\S+)', open(os.path.join(AFE, 'amp', 'spice', 'afe_params.spice')).read()))
    ka, kp = float(pa['CAPK_A']) * 1e3, float(pa['CAPK_P']) * 1e9            # fF/um2, fF/um
    cmim = lambda w, l: ka * w * l + kp * 2 * (w + l)                       # fF, um
    if 'adc_ch.spice' in L:
        sz = lvs_sizes(os.path.join(LVS_DIR, 'adc_ch.spice'), 'vrefs')
        mim = [(k, v) for k, (m, v) in sz.items() if m == MIM_LVS]
        ok_ = len(mim) == 1 and abs(mim[0][1]['c_length'] - 59.07) < 0.01 and abs(mim[0][1]['c_width'] - 59.07) < 0.01
        R('OK' if ok_ else 'MISMATCH', 'C12', '[m7] Cref is ONE MIM plate of 59.07 um side (Decision 44i), not 128 units',
          '; '.join('%s %.3f x %.3f um = %.1f um2, %.2f fF' % (k, v['c_width'], v['c_length'], v['c_width'] * v['c_length'], cmim(v['c_width'], v['c_length'])) for k, v in mim) or 'no MIM in vrefs')
    if 'afe_chc.spice' in L:
        sz = lvs_sizes(os.path.join(LVS_DIR, 'afe_chc.spice'), 'afe_chc')
        grp = {}
        for k, (m, v) in sz.items():
            mm = re.fullmatch(r'(xs1_xcin[12])_\d+', k)
            if mm and m == MIM_LVS:
                grp.setdefault(mm.group(1), []).append(v)
        ctar = float(pa['CIN_RATIO']) * float(pa['CF1V'].rstrip('f'))        # fF
        ctot = {g: sum(cmim(v['c_width'], v['c_length']) for v in lst) for g, lst in grp.items()}
        amax = max([v['c_width'] * v['c_length'] for lst in grp.values() for v in lst] or [1e9])
        ok_ = sorted(grp) == ['xs1_xcin1', 'xs1_xcin2'] and all(len(l) >= 2 for l in grp.values()) and amax <= 10000.0 and all(abs(c_ / ctar - 1) <= 1e-3 for c_ in ctot.values())
        R('OK' if ok_ else 'MISMATCH', 'C12', '[m7] each Cin is built from >= 2 MIM pieces <= 10,000 um2 with the simulated capacitance (within 0.1 %)',
          '; '.join('%s: %d x %.3f x %.3f um = %.1f um2 each, %.4f pF (simulated %.4f pF, %+.3f %%)' % (g, len(l), l[0]['c_width'], l[0]['c_length'], l[0]['c_width'] * l[0]['c_length'], ctot[g] / 1e3, ctar / 1e3, (ctot[g] / ctar - 1) * 100)
                    for g, l in sorted(grp.items())) or 'no Cin pieces found')
    # ---- M2: supply pins and the rail table of AUDIT 4.9.2 (Decision 44d)
    R('OK' if all(p_ in chports for p_ in ('vdd', 'vdd_cmp', 'vdd_dac', 'vss')) else 'MISMATCH', 'M2', '[M2] afe_ch has the supply pins vdd, vdd_cmp, vdd_dac, vss', 'supply ports of afe_ch: ' + ' '.join(p_ for p_ in chports if p_.startswith('vdd') or p_ == 'vss'))
    on = lambda cell, pin: sorted('%s:%s' % (d, r) for d, m, tl in FL[cell] for (nn, r) in tl if nn == pin)
    dd, dv = on('dac_sw', 'vdd_dac'), on('dac_sw', 'vdd')
    drv_ok = len(dd) == 26 and all(re.fullmatch(r'xdv\w+\.xp:[sb]', x) for x in dd)
    tg_ok = len(dv) == 13 and all(re.fullmatch(r'xt\w+\.xp:b', x) for x in dv)
    R('OK' if drv_ok and tg_ok else 'MISMATCH', 'M2', '[M2] dac_sw: vdd_dac = source and n-well of the 13 bottom-plate driver PMOS only; vdd = n-well of the 13 sampling-TG PMOS only',
      'vdd_dac: %d terminals (%s ...); vdd: %d terminals (%s ...)' % (len(dd), ' '.join(dd[:2]), len(dv), ' '.join(dv[:2])))
    cv = on('cmp_p', 'vdd_cmp')
    R('OK' if 'vdd_cmp' in subs['cmp_p'].ports and 'vdd' not in subs['cmp_p'].ports and len(cv) >= 10 else 'MISMATCH', 'M2', '[M2] cmp_p: its supply pin is vdd_cmp',
      'pins: %s; %d device terminals on vdd_cmp (sources / n-wells of the tail, latch, precharge and inverter PMOS)' % (' '.join(subs['cmp_p'].ports), len(cv)))
    wires = {(iname, pn.lower()): e for typ, iname, pins_, lv_ in ch.inst for pn, e in pins_.items()}
    expw = [(('u_amp', 'vdd'), 'vdd'), (('u_os', 'vdd'), 'vdd'), (('u_vh', 'vdd'), 'vdd'), (('u_vr', 'vdd'), 'vdd'), (('u_dac', 'vdd'), 'vdd'), (('u_cmp', 'vdd_cmp'), 'vdd_cmp'), (('u_dac', 'vdd_dac'), 'vdd_dac'), (('u_dac', 'gdp'), 'vdd_dac')]
    badw = ['%s.%s = %s (expected %s)' % (k[0], k[1], wires.get(k), v) for k, v in expw if wires.get(k) != v]
    R('OK' if not badw else 'MISMATCH', 'M2', '[M2] afe_ch wiring = rail table of AUDIT 4.9.2: analog strap vdd; ADC-main strap vdd_cmp (cmp_p); ADC-DAC strap vdd_dac (drivers, gdp)',
      '; '.join(badw) or ', '.join('%s.%s <- %s' % (k[0], k[1], v) for k, v in expw))
    rs = [i for i in top.inst if i[0] == 'afe_rstrap']
    dc = [i for i in top.inst if i[0] == 'afe_decap']
    tok = (u[2].get('vdd') == 'VDD' and u[2].get('vdd_cmp') == 'VDD' and u[2].get('vdd_dac') == 'vdd_dac' and len(rs) == 1 and sorted([rs[0][2].get('a'), rs[0][2].get('b')]) == ['VDD', 'vdd_dac']
           and sorted(i[2].get('p') for i in dc) == ['VDD', 'vdd_dac'] and all(i[2].get('n') == 'VSS' for i in dc))
    R('OK' if tok else 'MISMATCH', 'M2', '[M2] top netlist: afe_ch.vdd and .vdd_cmp on VDD, .vdd_dac on the net vdd_dac behind ONE strap resistor; one decap cell on each of the two ADC straps',
      'afe_ch: vdd <- %s, vdd_cmp <- %s, vdd_dac <- %s; afe_rstrap: %s; afe_decap: %s' % (u[2].get('vdd'), u[2].get('vdd_cmp'), u[2].get('vdd_dac'), ', '.join('%s (%s - %s)' % (i[1], i[2].get('a'), i[2].get('b')) for i in rs) or 'NONE',
                                                                                       ', '.join('%s (%s - %s)' % (i[1], i[2].get('p'), i[2].get('n')) for i in dc) or 'NONE'))
    if tsub:
        sz = lvs_sizes(os.path.join(LVS_DIR, 'dbs_afe_top.spice'), 'dbs_afe_top')
        RSHT = {'rm1': 0.09, 'rm2': 0.09, 'rm3': 0.09, 'rm4': 0.09, 'ppolyf_s': 7.3, 'npolyf_s': 6.8, 'ppolyf_u': 350.0, 'npolyf_u': 310.0}
        strap, cap = [], {}
        for i_, nd_, m_, r_ in tsub.inst:
            if m_ in RSHT:
                strap.append((i_, sorted(nd_[:2]), m_, RSHT[m_] * sz[i_][1]['r_length'] / sz[i_][1]['r_width']))
            if m_ == 'cap_nmos_03v3':
                cap[tuple(nd_)] = cap.get(tuple(nd_), 0.0) + sz[i_][1].get('m', 1.0) * sz[i_][1]['c_length'] * sz[i_][1]['c_width'] * 3.983 / 1e3      # pF at 3.98 fF/um2 (PDK model, 3.3 V)
        lok = (len(strap) == 1 and strap[0][1] == ['vdd', 'vdd_dac'] and 8.0 <= strap[0][3] <= 12.0 and cap.get(('vdd', 'vss'), 0) >= 125.0 and cap.get(('vdd_dac', 'vss'), 0) >= 100.0)
        R('OK' if lok else 'MISMATCH', 'M2', '[M2] LVS top reference: the 10 ohm strap resistor and the MOS decap (0.125 nF main strap, 0.1 nF DAC strap) are devices',
          'strap: %s; cap_nmos_03v3 at 3.98 fF/um2: %s' % (', '.join('%s %s between %s and %s = %.2f ohm (typical)' % (i_, m_, n_[0], n_[1], r_) for i_, n_, m_, r_ in strap) or 'NONE',
                                                          ', '.join('%s-%s %.1f pF' % (k[0], k[1], v) for k, v in sorted(cap.items())) or 'NONE'))
        # ---- afe_ch of the LVS top against afe_ch of the Verilog, net by net (independent of mk_lvs_netlists.py: this file's two parsers)
        S = L['dbs_afe_top.spice']
        cen, imp = {}, []
        POWERPINS = {'tgate': ('vdd', 'vss'), 'gf180mcu_fd_sc_mcu7t5v0__or2_1': ('vdd', 'vnw', 'vpw', 'vss'), 'gf180mcu_fd_sc_mcu7t5v0__inv_1': ('vdd', 'vnw', 'vpw', 'vss')}

        def add(iname, nodes, model, nm):
            for pn, nd in zip(S[model].ports, nodes):
                if pn in POWERPINS.get(model, ()):
                    imp.append((iname[1:], pn, nm(nd)))
                else:
                    cen.setdefault(nm(nd), set()).add('%s.%s' % (iname[1:], pn))
        for i_, nd_, m_, r_ in S['afe_ch'].inst:
            if m_ in ('amp_ch', 'adc_ch'):
                pm = dict(zip(S[m_].ports, nd_))
                for i2, n2, m2, r2 in S[m_].inst:
                    add(i2, n2, m2, lambda x: pm.get(x, x))
            else:
                add(i_, nd_, m_, lambda x: x)
        vcen = {}
        for nn, con in nets.items():
            s_ = set(c_.lower() for c_, k_, g_ in con if not c_.startswith('port:'))
            if s_:
                vcen[nn.lower()] = s_
        dnet = sorted(k for k in set(cen) | set(vcen) if cen.get(k) != vcen.get(k))
        badimp = [x for x in imp if x[2] != {'vdd': 'vdd', 'vnw': 'vdd', 'vpw': 'vss', 'vss': 'vss'}[x[1]]]
        R('OK' if not dnet and not badimp else 'MISMATCH', 'C3', '[M3] afe_ch of the LVS top (through amp_ch / adc_ch) = module afe_ch of the Verilog, net by net; TGATE and standard-cell power on the analog strap',
          '%d nets, %d pin connections compared, differing nets: %s; %d implicit power pins (TGATE VDD / VSS, std-cell VDD / VNW / VPW / VSS), wrong: %s' % (
              len(vcen), sum(len(v) for v in vcen.values()), ' '.join(dnet[:6]) or 'none', len(imp), badimp or 'none'))
        # ---- the 8 channel instances and the macro of the LVS top against the Verilog top
        badc = []
        for i_, nd_, m_, r_ in tsub.inst:
            if m_ != 'afe_ch':
                continue
            k = int(re.search(r'(\d+)$', i_).group(1))
            got_ = dict(zip(S['afe_ch'].ports, nd_))
            for pin, e in u[2].items():
                mm = re.match(r'(\w+)\[(.+)\]$', e)
                if not mm:
                    exp_ = {pin.lower(): e.lower()}
                elif '+:' in mm.group(2):
                    a_, b_ = mm.group(2).split('+:')
                    lo_ = eval(a_.replace(lv, str(k)))
                    exp_ = {'%s[%d]' % (pin.lower(), j): '%s[%d]' % (mm.group(1).lower(), lo_ + j) for j in range(int(b_))}
                else:
                    exp_ = {pin.lower(): '%s[%d]' % (mm.group(1).lower(), eval(mm.group(2).replace(lv, str(k))))}
                for a_, b_ in exp_.items():
                    if got_.get(a_) != b_:
                        badc.append('ch%d.%s = %s (Verilog: %s)' % (k, a_, got_.get(a_), b_))
        dg = [(i_, nd_) for i_, nd_, m_, r_ in tsub.inst if m_ == 'afe_dig']
        badd = [] if dg else ['no afe_dig instance']
        for pn, nd in (zip(S['afe_dig'].ports, dg[0][1]) if dg else []):
            if nd != {'dout': 'dout_out'}.get(pn, pn):
                badd.append('afe_dig.%s = %s' % (pn, nd))
        ties = sorted((a_, b_) for nm_, a_, b_, r_ in tsub.ideal)
        expt = sorted((k.lower(), 'vdd' if v == "1'b1" else 'vss') for k, v in top.assign.items() if v in ("1'b0", "1'b1"))
        R('OK' if not badc and not badd and ties == expt else 'MISMATCH', 'C5', '[M3] LVS top = Verilog top: the 8 afe_ch instances pin by pin, the afe_dig black box, the pad-control ties',
          '8 x %d channel pins: %s; afe_dig %d pins (DOUT -> DOUT_OUT, DOUT_OE -> DOUT_OE, every other pin on the net of its own name): %s; %d ties (0-ohm resistors) = the %d constant assigns of the Verilog: %s' % (
              len(S['afe_ch'].ports), '; '.join(badc[:4]) or 'equal', len(S['afe_dig'].ports), '; '.join(badd[:4]) or 'equal', len(ties), len(expt), 'equal' if ties == expt else 'DIFFERENT'))
    # floating internal nets of each analog cell: nets that touch only gates, or a single terminal
    for c in ANA:
        tn = {}
        for d, m, tl in FL[c]:
            for (nn, r) in tl:
                tn.setdefault(nn, []).append((d, m, r))
        fl = []
        for nn, l in tn.items():
            if nn in subs[c].ports or nn == '0':
                continue
            kinds = set(r for _, _, r in l)
            if kinds <= {'g'} or len(l) == 1:
                fl.append('%s (%s)' % (nn, ','.join(sorted(kinds))))
            elif kinds <= {'g', 'p', 'n'}:
                fl.append('%s (gates + capacitor plates only: no DC path in the netlist)' % nn)
        R('OK' if not fl else 'NOTE', 'C13', '%s internal nets with no DC path / single terminal' % c, '; '.join(fl) or 'none')

    # ---- C14: PLAN.md section 9 pin table against afe_ch
    plan = open(os.path.join(AFE, 'layout', 'PLAN.md')).read()
    sec = plan[plan.index('## 9.'):]
    tb = re.findall(r'^\|\s*([a-z_0-9,\[\]: ]+?)\s*\|\s*(in|out|inout)\s*\|', sec, flags=re.M)
    pl = []
    for names, d in tb:
        for nme in names.split(','):
            pl.append(re.sub(r'\[.*\]', '', nme).strip())
    vp = [p for p, _, _ in ch.ports]
    R('OK' if sorted(pl) == sorted(vp) else 'MISMATCH', 'C14', 'AFE/layout/PLAN.md section 9 pin table = afe_ch module ports', 'only in PLAN: %s; only in afe_ch: %s; order in afe_ch: %s' % (sorted(set(pl) - set(vp)) or '-', sorted(set(vp) - set(pl)) or '-', ' '.join(vp)))
    m = re.search(r'Total = 8 x \((\d+) \+ (\d+) \+ (\d+)\) \+ 1 = (\d+)', sec)
    dig_in = [p for p, d, w in ch.ports if d == 'input' and p not in ('vbn', 'vcm', 'vg1', 'vcmo', 'vg2', 'vrs', 'vdd', 'vdd_cmp', 'vdd_dac', 'vss')]
    nd = sum(w for p, d, w in ch.ports if p in dig_in)
    R('OK' if m and nd - 1 == int(m.group(1)) else 'MISMATCH', 'C14', 'crossing-net count of PLAN.md section 9', 'afe_ch digital inputs: %d bits incl. rst_amp (PLAN: %s per channel + rst_amp), 1 digital output cmp_q; PLAN total %s' % (nd, m.group(1) if m else '?', m.group(4) if m else '?'))
    # ---- C15: std cells instantiated by hand exist in the library
    libv = '/foss/pdks/gf180mcuD/libs.ref/gf180mcu_fd_sc_mcu7t5v0/verilog/gf180mcu_fd_sc_mcu7t5v0.v'
    lt = open(libv).read() if os.path.exists(libv) else ''
    for cname in ['or2_1', 'inv_1', 'dlya_1', 'dlyc_1', 'dlyd_1', 'and3_1']:
        mm = re.search(r'module gf180mcu_fd_sc_mcu7t5v0__%s\s*\(([^)]*)\)' % cname, lt)
        R('OK' if mm else 'MISMATCH', 'C15', 'std cell gf180mcu_fd_sc_mcu7t5v0__%s exists' % cname, ('pins: ' + ' '.join(mm.group(1).replace(',', ' ').split())) if mm else 'not found in ' + libv)

    Pr = lambda *a: print(*a, file=out)
    Pr(__doc__.split('usage')[0].strip())
    nm = sum(1 for r in rows if r[0] == 'MISMATCH')
    Pr('\nSUMMARY: %d checks, %d OK, %d MISMATCH, %d NOTE' % (len(rows), sum(1 for r in rows if r[0] == 'OK'), nm, sum(1 for r in rows if r[0] == 'NOTE')))
    Pr('ISSUE ROWS (AUDIT section 2; a row belongs to an issue when its text starts with the id in brackets):')
    for tag in ('B1', 'B2', 'M2', 'M3', 'm7', 'm1'):
        rr = [r for r in rows if r[2].startswith('[%s]' % tag)]
        Pr('  %-3s %-8s %d rows: %d OK, %d MISMATCH' % (tag, 'OK' if rr and all(r[0] == 'OK' for r in rr) else 'MISMATCH', len(rr), sum(1 for r in rr if r[0] == 'OK'), sum(1 for r in rr if r[0] == 'MISMATCH')))
    Pr('')
    for st, cid, what, detail in rows:
        Pr('%-8s %-4s %s%s' % (st, cid, what, (' :: ' + detail) if detail else ''))
    Pr('\nNET TABLE of afe_ch (drv = digital driver or input port, io = channel / passive terminal, gate = MOS gate only (n / p), load = output port)')
    for st, n_, drv, io, gate, load, why in P:
        Pr('  %-10s %-8s drv[%s] io[%s] gate[%s] load[%s] %s' % (n_, st, ' '.join(drv), ' '.join(io), ' '.join(gate), ' '.join(load), why))
    Pr('\nPORT CLASSES from the flattened SPICE (gate = only MOS gates: needs a driver; types of the gated devices)')
    for c in ANA + ['tgate']:
        Pr('  %-13s %s' % (c, '  '.join('%s:%s%s' % (p, PC[c][p][0], ('(' + ''.join(PC[c][p][1]) + ')') if PC[c][p][1] else '') for p in subs[c].ports)))
    if out is not sys.stdout:
        out.close()
    return nm


if __name__ == '__main__':
    main()
