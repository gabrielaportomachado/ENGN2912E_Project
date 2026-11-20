#!/usr/bin/env python3
"""check_submission.py (LP kit, step 7): the organizer's submission checks that can be run here (the organizer publishes no checker script; these follow the template comments of
resources/info.yaml and lvs_config.json, copies in AFE/review/sim/organizer/).

  python3 AFE/layout/scripts/check_submission.py          final mode (L4): every item must PASS
  python3 AFE/layout/scripts/check_submission.py --pre    before the GDS exists (LP, L3a): items that only layout produces are PENDING (with the phase that produces them), not FAIL

Checks: info.yaml (template keys, 7 io_types, 24 pads, every pad's top-level ports exist in AFE/top/dbs_afe_top.v and every top port belongs to exactly one pad, export-control file,
lvs_config path, ready flags), lvs_config.json (template keys, TOP_SOURCE, every file after $UPRJ_ROOT / $TOP_SOURCE / $TOP_LAYOUT substitution, the SPICE top has subckt TOP_SOURCE with
exactly the top ports, the Verilog file defines afe_dig), the GDS (one top cell named TOP_LAYOUT, inside 1000 x 1000 um, DRC / LVS reports of flow.py on this very file), README.md
(no `<L4:` placeholder left).  Writes AFE/layout/sim/check_submission.log.  Exit 0 = no FAIL (and, without --pre, no PENDING)."""
import os, re, sys, json, hashlib, argparse
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from floorplan import verilog_ports, info_pads
LAY = os.path.normpath(os.path.join(HERE, '..'))
REPO = os.path.normpath(os.path.join(LAY, '..', '..'))
ORG = os.path.join(REPO, 'AFE', 'review', 'sim', 'organizer')
TOPV = os.path.join(REPO, 'AFE', 'top', 'dbs_afe_top.v')
IOTYPES = ('ground', 'power', 'input_cmos', 'input_schmitt', 'bidirectional', 'bidirectional_24ma', 'analog')
BIDI_CTL = ('PD', 'PU', 'CS', 'SL', 'IE', 'OE', 'PDRV0', 'PDRV1')
OUT, CNT = [], {'PASS': 0, 'FAIL': 0, 'PENDING': 0}


def R(st, what, todo=''):
    CNT[st] = CNT.get(st, 0) + 1
    OUT.append('%-7s %s' % (st, what) + (('\n        -> ' + todo) if todo and st != 'PASS' else ''))
    print(OUT[-1])


def ok(c, what, todo=''):
    R('PASS' if c else 'FAIL', what, todo)


def yaml_top_keys(path, section):
    keys, ins = [], False
    for ln in open(path):
        if re.match(r'^%s:' % section, ln):
            ins = True
            continue
        if ins:
            m = re.match(r'^\s{2}(\w+):', ln)
            if m:
                keys.append(m.group(1))
            elif re.match(r'^\S', ln):
                break
    return keys


def yaml_val(path, key):
    for ln in open(path):
        m = re.match(r'^\s+%s:\s*"?([^"#\n]*)"?' % key, ln)
        if m:
            return m.group(1).strip()
    return None


def pad_ports(name, typ):
    base, idx = re.match(r'([^\[]+)(\[\d+\])?', name).groups()
    idx = idx or ''
    if typ in ('analog', 'power', 'ground'):
        return [name]
    if typ in ('input_cmos', 'input_schmitt'):
        return [name, base + '_PU' + idx, base + '_PD' + idx]
    if typ == 'bidirectional':
        return [base + '_IN' + idx, base + '_OUT' + idx] + [base + '_' + c + idx for c in BIDI_CTL]
    return [base + '_IN' + idx, base + '_OUT' + idx] + [base + '_' + c + idx for c in ('PD', 'PU', 'CS', 'SL', 'IE', 'OE')]


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--pre', action='store_true')
    a = ap.parse_args()
    pend = lambda what, phase: R('PENDING' if a.pre else 'FAIL', what, 'produced by phase %s' % phase)
    info = os.path.join(REPO, 'info.yaml')
    print('check_submission.py%s  repo %s' % (' --pre' if a.pre else '', REPO))
    # ---------------- info.yaml
    tk, ik = yaml_top_keys(os.path.join(ORG, 'template_info.yaml'), 'project'), yaml_top_keys(info, 'project')
    ok(tk == ik, 'info.yaml project keys equal the template (%s)' % ' '.join(ik), 'template keys: ' + ' '.join(tk))
    pads = info_pads(info)
    bad = [p for p in pads if p[1] not in IOTYPES]
    ok(not bad, 'info.yaml: %d pads, io_type one of the 7 template types%s' % (len(pads), (' (BAD: %s)' % bad) if bad else ''))
    ok(len(pads) == 24 and len({p[0] for p in pads}) == 24, 'info.yaml has 24 distinct pads (Decision 45)')
    ports = verilog_ports(TOPV)
    want = [q for n, t in pads for q in pad_ports(n, t)]
    miss = [q for q in want if q not in ports]
    extra = [q for q in ports if q not in want]
    dup = sorted({q for q in want if want.count(q) > 1})
    ok(not miss and not extra and not dup, 'top ports of AFE/top/dbs_afe_top.v (%d) = the ports the 24 pads need (%d)%s' % (len(ports), len(want),
       ''.join(' %s: %s' % (k, v[:6]) for k, v in (('missing', miss), ('extra', extra), ('twice', dup)) if v)))
    ec = yaml_val(info, 'export_control')
    ok(ec and os.path.exists(os.path.join(REPO, ec)), 'export-control document %s exists' % ec)
    lc = yaml_val(info, 'lvs_config')
    ok(lc and os.path.exists(os.path.join(REPO, lc)), 'lvs_config %s exists' % lc)
    flags = {k: yaml_val(info, k) for k in ('gf_def_ready', 'ws_def_ready', 'drc_ready', 'lvs_ready')}
    if all(v == 'true' for v in flags.values()):
        R('PASS', 'info.yaml ready flags all true')
    else:
        pend('info.yaml ready flags %s (set to true when gate.py L4 passes)' % flags, 'L4')
    # ---------------- lvs_config.json
    lv = json.load(open(os.path.join(REPO, lc or 'lvs_config.json')))
    tl = json.load(open(os.path.join(ORG, 'template_lvs_config.json')))
    ok(sorted(lv) == sorted(tl), 'lvs_config.json keys equal the template')
    top = lv.get('TOP_SOURCE')
    ok(top == 'dbs_afe_top', 'TOP_SOURCE = %s (default name, ACCEPT.md section 5: rename here, in the GDS and in the SPICE top if the organizer assigns one)' % top)
    sub = lambda s: s.replace('$UPRJ_ROOT', REPO).replace('$TOP_SOURCE', top).replace('$TOP_LAYOUT', lv.get('TOP_LAYOUT', '').replace('$TOP_SOURCE', top))
    files = [sub(f) for k in ('LVS_SPICE_FILES', 'LVS_VERILOG_FILES') for f in lv.get(k, []) if f] + [sub(lv['LAYOUT_FILE'])]
    for f in files:
        if os.path.exists(f):
            R('PASS', 'lvs_config file %s exists' % os.path.relpath(f, REPO))
        else:
            pend('lvs_config file %s does not exist yet' % os.path.relpath(f, REPO), 'L4 (copies AFE/layout/lvs/dbs_afe_top.spice -> spice/, AFE/dig/final/afe_dig.pnl.v -> verilog/gl/afe_dig.v, the L3a GDS -> gds/)')
    sp = [f for f in files if f.endswith('.spice')]
    if sp and os.path.exists(sp[0]):
        txt = open(sp[0]).read()
        m = re.search(r'(?ims)^\.subckt\s+%s\s+(.*?)\n(?!\+)' % re.escape(top), txt)
        sp_ports = m.group(1).split() if m else []
        ok(sorted(sp_ports) == sorted(ports), 'SPICE top %s: subckt %s with exactly the %d top ports' % (os.path.relpath(sp[0], REPO), top, len(ports)))
    vf = [f for f in files if f.endswith('.v')]
    if vf and os.path.exists(vf[0]):
        ok(re.search(r'(?m)^\s*module\s+afe_dig\b', open(vf[0]).read()) is not None, 'Verilog %s defines module afe_dig' % os.path.relpath(vf[0], REPO))
    # ---------------- GDS
    g = sub(lv['LAYOUT_FILE'])
    if os.path.exists(g):
        try:
            import klayout.db as kdb
            ly = kdb.Layout()
            ly.read(g)
            tops = [c.name for c in ly.top_cells()]
            ok(tops == [top], 'GDS has one top cell %s (%s)' % (top, tops))
            bb = ly.top_cells()[0].bbox() if tops else None
            if bb:
                w, h = bb.width() * ly.dbu, bb.height() * ly.dbu
                ok(bb.left >= 0 and bb.bottom >= 0 and bb.right * ly.dbu <= 1000.0 + 1e-6 and bb.top * ly.dbu <= 1000.0 + 1e-6,
                   'GDS inside the 1000 x 1000 um outline: bbox %.3f x %.3f um at (%.3f, %.3f)' % (w, h, bb.left * ly.dbu, bb.bottom * ly.dbu), 'ACCEPT.md ladder A')
        except ImportError:
            R('FAIL', 'python module klayout.db missing (run inside the course container)')
        sha = hashlib.sha1(open(g, 'rb').read()).hexdigest()
        for kind, field, good in (('drc', 'total', 0), ('lvs', 'match', True)):
            jf = os.path.join(LAY, 'sim', 'flow', '%s.%s.json' % (top, kind))
            d = json.load(open(jf)) if os.path.exists(jf) else {}
            if d.get('gds_sha1') != sha and a.pre:
                pend('flow.py %s report of %s (today the file is the PR-boundary GDS of Decision 45)' % (kind, os.path.relpath(g, REPO)), 'L3a (DRC / LVS of the full chip), L4 (copies the GDS)')
                continue
            ok(d.get('gds_sha1') == sha and d.get(field) == good, 'flow.py %s report of THIS GDS: %s = %s' % (kind, field, d.get(field)),
               'run python3 AFE/layout/scripts/flow.py %s --gds %s --top %s%s' % (kind, os.path.relpath(g, REPO), top, ' --antenna' if kind == 'drc' else ' --ref AFE/layout/lvs/dbs_afe_top.spice'))
    else:
        pend('GDS %s does not exist yet' % os.path.relpath(g, REPO), 'L3a / L4')
    # ---------------- README
    rd = os.path.join(REPO, 'README.md')
    if not os.path.exists(rd):
        R('FAIL', 'README.md exists')
    else:
        txt = open(rd).read()
        need = ['## Block diagram', '## Pins', '## Host rules', '## Board needs', '## Test plan']
        ok(all(n in txt for n in need), 'README.md has the sections %s' % ', '.join(n[3:] for n in need))
        ph = re.findall(r'<L4:[^>]*>', txt)
        if ph:
            pend('README.md still has %d `<L4: ...>` placeholders' % len(ph), 'L4')
        else:
            R('PASS', 'README.md has no placeholder left')
    ea = os.path.join(REPO, 'documents', 'export_control_answers.md')
    ok(os.path.exists(ea), 'technical answers for the export-control form: documents/export_control_answers.md (the signer copies them into the .docx and signs)')
    v = 'FAIL' if CNT['FAIL'] or (CNT['PENDING'] and not a.pre) else 'PASS'
    s = 'RESULT check_submission%s: %s  (%d PASS, %d PENDING, %d FAIL)' % (' --pre' if a.pre else '', v, CNT['PASS'], CNT['PENDING'], CNT['FAIL'])
    print(s)
    OUT.append(s)
    os.makedirs(os.path.join(LAY, 'sim'), exist_ok=True)
    open(os.path.join(LAY, 'sim', 'check_submission%s.log' % ('_pre' if a.pre else '')), 'w').write('\n'.join(OUT) + '\n')
    return 0 if v == 'PASS' else 1


if __name__ == '__main__':
    sys.exit(main())
