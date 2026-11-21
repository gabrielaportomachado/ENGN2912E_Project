#!/usr/bin/env python3
"""gate.py (LP kit, step 8): the end-of-phase gate.  A phase is finished only when this prints "GATE <phase>: PASS".

  python3 AFE/layout/scripts/gate.py <L2a|L1a|L1d|L2b|L1b|L3a|L3b|L4> [--gds FILE] [--run] [--no-findings]

It reads the reports that the kit commands wrote and judges them against AFE/layout/ACCEPT.md (accept_limits.json, through compare.py):
  every phase   ACCEPT.md (IN FORCE) limits table == accept_limits.json; the protected files unchanged since the last REVIEW.md commit (unless report section 9 names the REVIEW.md
                item that changed them); REVIEW.md not edited; every open REVIEW.md item for this or an earlier phase listed in section 9 of a phase report; this phase not named by
                BLOCKED.md; the phase report AFE/layout/reports/<phase>.md with its 10 sections (L1a onward; the first phase after L2a also converts NOTES_L2.md into reports/L2a.md);
                "<phase> findings" + a Results-log row (L2a: in AFE/layout/NOTES_L2.md; later phases: AFE/NOTES.md, and "L2a findings" merged there); floorplan.py check 0 FAIL
  L2a / L1a / L3a  DRC (flow.py drc, variant D) 0 violations and LVS (flow.py lvs) "Circuits match uniquely." for amp_ch / adc_ch / dbs_afe_top, both on the CURRENT GDS (sha1 in the report);
                L1a also the Cref keep-out (nothing below Metal4 inside the Cref bottom-plate footprint); L3a also antenna, decap >= 115 / 95 pF in the LVS reference, compare.py --phase L3a
  L1d           AFE/dig/final/{afe_dig.gds, afe_dig.pnl.v, afe_dig.lef, afe_dig_pins.json}, flow summary VERDICT PASS, KLayout DRC PASS on that GDS, the tap limits (a) (c) + slack, switch
                skew, gate-level testbench failures only the accepted ones, run_top_sim.sh dig EQUIV PASS, check_lvs_netlists.py PASS with the LVS top written from the final netlist
  L2b / L1b / L3b  PEX (flow.py pex) of the current GDS: census equal to the LVS extraction, MIM correction applied, no unknown model; compare.py --phase <phase> PASS on post-layout results
                that were simulated on a PEX netlist (not on the schematic)
  L4            AFE/layout/scripts/check_submission.py PASS
--gds FILE: the layout to judge (default: AFE/layout/<amp|adc|top>/<cell>.gds).  --run: run the missing / stale flow.py commands first (DRC, LVS, PEX; minutes to an hour for the top).
Writes AFE/layout/sim/gate_<phase>.log.  Exit 0 = PASS, 1 = FAIL (each FAIL line says what to do), 2 = usage error."""
import os, re, sys, json, glob, hashlib, argparse, subprocess

HERE = os.path.dirname(os.path.abspath(__file__))
LAY = os.path.normpath(os.path.join(HERE, '..'))
REPO = os.path.normpath(os.path.join(LAY, '..', '..'))
NOTES = os.path.join(REPO, 'AFE', 'NOTES.md')
FLOWD = os.path.join(LAY, 'sim', 'flow')
PHASES = ('L2a', 'L1a', 'L1d', 'L2b', 'L1b', 'L3a', 'L3b', 'L4')
CELL = {'L2a': 'amp_ch', 'L2b': 'amp_ch', 'L1a': 'adc_ch', 'L1b': 'adc_ch', 'L3a': 'dbs_afe_top', 'L3b': 'dbs_afe_top'}
GDS_DEFAULT = {'amp_ch': ['AFE/layout/amp/amp_ch.gds', 'AFE/layout/amp/gds/amp_ch.gds'], 'adc_ch': ['AFE/layout/adc/adc_ch.gds'], 'dbs_afe_top': ['AFE/layout/top/dbs_afe_top.gds', 'gds/dbs_afe_top.gds']}
REF = {'amp_ch': ['AFE/layout/amp/lvs/afe_chc.spice', 'AFE/layout/lvs/afe_chc.spice'], 'adc_ch': ['AFE/layout/adc/lvs/adc_ch.spice', 'AFE/layout/lvs/adc_ch.spice'],
       'dbs_afe_top': ['AFE/layout/lvs/dbs_afe_top.spice']}
PROTECTED = ['AFE/layout/accept_limits.json', 'AFE/layout/ACCEPT.md', 'AFE/amp/spice', 'AFE/adc/spice', 'rtl', 'AFE/adc/rtl', 'AFE/top/dbs_afe_top.v', 'TGATE/TGATE.spice']
DIG_ALLOWED = {'X1.contention', 'X5.word0', 'X5.after17d', 'T11.crowbar'}          # Decision 44f / AUDIT 4.4.6; MIXED corner also T2.settle
DECAP_PF = 1.593                                                                     # one cap_nmos_03v3 20 x 20 um unit at 3.3 V (SPEC.md section 4)
OUT = []
NF = [0]


def P(s=''):
    print(s, flush=True)
    OUT.append(s)


def R(ok, what, todo=''):
    if ok is None:
        P('INFO  ' + what)
        return
    P(('PASS  ' if ok else 'FAIL  ') + what)
    if not ok:
        NF[0] += 1
        if todo:
            P('      -> DO: ' + todo)


def rel(p):
    return os.path.relpath(p, REPO)


def sh(cmd, **kw):
    p = subprocess.run(cmd, cwd=REPO, capture_output=True, text=True, stdin=subprocess.DEVNULL, **kw)
    return p.returncode, p.stdout + p.stderr


def sha1(path):
    return hashlib.sha1(open(path, 'rb').read()).hexdigest()


def first(paths):
    for p in paths:
        if os.path.exists(os.path.join(REPO, p)):
            return os.path.join(REPO, p)
    return None


def jload(path):
    try:
        return json.load(open(path))
    except Exception:
        return None


# ------------------------------------------------------------------ common checks
SECTIONS = ['Summary and verdict', 'What was built', 'Commands run', 'Results', 'Gate output', 'Ladder decisions', 'Deviations', 'Open issues and risks', 'REVIEW.md items handled',
            'Files changed and commit']
REVIEW = os.path.join(LAY, 'REVIEW.md')
REPORTS = os.path.join(LAY, 'reports')


def report_sections(path):
    """{n: text} of the sections '## n. ...' of a phase report"""
    txt = open(path).read() if os.path.exists(path) else ''
    parts = re.split(r'(?m)^## (\d+)\.', txt)
    return {int(parts[k]): parts[k + 1] for k in range(1, len(parts) - 1, 2)}


def review_items():
    """[(id, target phase or 'all', status)] of AFE/layout/REVIEW.md: items are '### R<n> (<date>) to <phase|all>: <title>' followed by a line 'Status: open | closed'"""
    if not os.path.exists(REVIEW):
        return []
    txt = open(REVIEW).read()
    out = []
    for m in re.finditer(r'(?m)^### (R\d+)\b[^\n]*?\bto ([A-Za-z0-9, ]+?):([^\n]*)\n((?:(?!^### )[^\n]*\n?)*)', txt):
        st = re.search(r'(?im)^status:\s*(\w+)', m.group(4))
        out.append((m.group(1), [t.strip() for t in m.group(2).split(',')], (st.group(1).lower() if st else 'open')))
    return out


def base_commit():
    """the last commit that touched AFE/layout/REVIEW.md (written only by the user / monitoring session; LP created it with ACCEPT.md IN FORCE): protected files are compared against it"""
    rc, out = sh(['git', 'log', '-1', '--format=%H', '--', 'AFE/layout/REVIEW.md'])
    h = out.strip()
    return h if (rc == 0 and re.fullmatch(r'[0-9a-f]{40}', h)) else None


def common(phase, a):
    P('--- common')
    rc, out = sh([sys.executable, 'AFE/layout/tb/compare.py', '--check-accept'])
    R(rc == 0, 'ACCEPT.md limits table equals AFE/layout/accept_limits.json', 'nobody but a REVIEW.md item edits either file; restore them with git checkout <last REVIEW.md commit> -- <file>')
    rep = os.path.join(REPORTS, '%s.md' % phase)
    sec = report_sections(rep)
    rc, out = sh(['git', 'diff', '--name-only', 'HEAD', '--', 'AFE/layout/REVIEW.md'])
    R(not out.strip(), 'AFE/layout/REVIEW.md not edited by this phase', 'git checkout HEAD -- AFE/layout/REVIEW.md (only the user / monitoring session writes it)')
    b = base_commit()
    if b and phase != 'L2a':
        rc, out = sh(['git', 'diff', '--name-only', b, '--'] + PROTECTED)
        ch = [x for x in out.split('\n') if x.strip()]
        s9 = ' '.join(t for f in sorted(glob.glob(os.path.join(REPORTS, '*.md'))) for n, t in report_sections(f).items() if n == 9)
        unexplained = [x for x in ch if x not in s9 and os.path.basename(x) not in s9]
        R(not unexplained, 'protected files (limits, ACCEPT.md, design netlists, RTL) unchanged since the last REVIEW.md commit %s%s' % (b[:7], (': CHANGED ' + ' '.join(unexplained[:8])) if unexplained else ''),
          'a phase may not edit these (ACCEPT.md section 1) unless a REVIEW.md item asks for it and report section 9 names the item and the file; restore with git checkout %s -- <file>' % b[:7])
        if ch and not unexplained:
            P('WARN  protected files changed by REVIEW.md items (named in report section 9): ' + ' '.join(ch[:8]))
        rc, out = sh(['git', 'diff', '--name-only', b, '--', 'AFE/layout/baseline'])
        chb = [x for x in out.split('\n') if x.strip()]
        if chb:
            P('WARN  baselines changed since %s (%d files): allowed only by ladder N-2 (native-Vt swap) or a REVIEW.md item; say so in report section 6 / 9' % (b[:7], len(chb)))
    items = [it for it in review_items() if it[2] != 'closed' and any(t == 'all' or (t in PHASES and PHASES.index(t) <= PHASES.index(phase)) for t in it[1])]
    if items:
        done = ' '.join(t for f in sorted(glob.glob(os.path.join(REPORTS, '*.md'))) for n, t in report_sections(f).items() if n == 9)
        miss = [it[0] for it in items if not re.search(r'\b%s\b' % it[0], done)]
        R(not miss, 'open REVIEW.md items for %s or an earlier phase (%s) are listed as handled in section 9 of a phase report' % (phase, ' '.join(it[0] for it in items)),
          'apply %s BEFORE this phase\'s own work (redo and re-gate the earlier phase if the item is for it) and list them in section 9' % ' '.join(miss))
    else:
        P('INFO  no open REVIEW.md item for %s or an earlier phase' % phase)
    blk = os.path.join(LAY, 'BLOCKED.md')
    if os.path.exists(blk):
        head = open(blk).read()[:400]
        P('INFO  AFE/layout/BLOCKED.md exists: ' + head.split('\n')[0][:150])
        R(re.search(r'\b%s\b' % phase, head) is None, 'AFE/layout/BLOCKED.md does not block %s (its first lines do not name it)' % phase,
          'this phase is blocked: continue with a phase that does not depend on it (RUNBOOK.md "what blocks what"); the answer arrives through REVIEW.md')
    if not a.no_findings:
        if phase != 'L2a':
            miss = [n for n in range(1, 11) if n not in sec]
            R(os.path.exists(rep) and not miss, 'phase report %s with all 10 sections%s' % (rel(rep), (': MISSING sections ' + ' '.join(map(str, miss))) if (os.path.exists(rep) and miss) else ('' if os.path.exists(rep) else ': NOT FOUND')),
              'copy AFE/layout/reports/TEMPLATE.md to %s and fill it (sections 5 and 10 may say "after the gate" until the gate passes)' % rel(rep))
        nf = os.path.join(LAY, 'NOTES_L2.md') if phase == 'L2a' else NOTES
        txt = open(nf).read() if os.path.exists(nf) else ''
        R(re.search(r'(?m)^## %s findings' % phase, txt) is not None, '"## %s findings" section in %s' % (phase, rel(nf)), 'write it (common rule 7): what was done, numbers with their log paths')
        rows = [l for l in txt.split('\n') if re.match(r'^\|\s*20\d\d-\d\d-\d\d\s*\|\s*%s\b' % phase, l)]
        R(bool(rows), 'Results-log row for %s in %s' % (phase, rel(nf)), 'add one row "| date | %s ... | model / effort | | result with log paths |" to the Results log' % phase)
        if phase != 'L2a':
            l2 = os.path.join(LAY, 'NOTES_L2.md')
            if os.path.exists(l2) and '## L2a findings' in open(l2).read():
                R('## L2a findings' in open(NOTES).read(), 'L2a findings of AFE/layout/NOTES_L2.md are merged into AFE/NOTES.md',
                  'copy the "L2a findings" section and its Results-log row of AFE/layout/NOTES_L2.md into AFE/NOTES.md, unchanged (common rule 7)')
                s2 = report_sections(os.path.join(REPORTS, 'L2a.md'))
                R(all(n in s2 for n in range(1, 11)), 'L2a report AFE/layout/reports/L2a.md (converted from NOTES_L2.md) with all 10 sections',
                  'write it from AFE/layout/NOTES_L2.md, FLOW.md and the L2a logs with AFE/layout/reports/TEMPLATE.md (the first phase after L2a does this)')
    pt = os.path.join(LAY, '.ptmp')
    if os.path.isdir(pt) and os.listdir(pt):
        P('WARN  scratch AFE/layout/.ptmp is not empty: delete it at the end of the phase (common rule 4)')


def floorplan(gds_args, dig_pins):
    cmd = [sys.executable, 'AFE/layout/scripts/floorplan.py', 'check']
    if gds_args:
        cmd += ['--gds'] + gds_args
    if dig_pins:
        cmd += ['--dig-pins', dig_pins]
    rc, out = sh(cmd)
    last = [l for l in out.split('\n') if l.startswith('floorplan.py check')]
    fails = [l for l in out.split('\n') if l.startswith('FAIL')]
    R(rc == 0 and not fails, 'floorplan.py check %s: %s' % (' '.join(cmd[3:]), last[-1] if last else out[-200:]),
      'ACCEPT.md ladder A (area) or G-5 (pin side); failing lines: ' + ' | '.join(fails[:3]))


# ------------------------------------------------------------------ layout reports
def flow_report(cell, kind, gds, a, extra=()):
    """reads AFE/layout/sim/flow/<cell>.<kind>.json; with --run, (re)runs flow.py when it is missing or belongs to another GDS"""
    jf = os.path.join(FLOWD, '%s.%s.json' % (cell, kind))
    d = jload(jf)
    stale = d is None or d.get('gds_sha1') != sha1(gds)
    if stale and a.run:
        cmd = [sys.executable, 'AFE/layout/scripts/flow.py', kind, '--gds', gds, '--top', cell] + list(extra)
        P('RUN   ' + ' '.join(cmd))
        sh(cmd)
        d = jload(jf)
        stale = d is None or d.get('gds_sha1') != sha1(gds)
    return d, stale, jf


def drc_lvs(cell, gds, a, antenna=False):
    ref = first(REF[cell])
    d, stale, jf = flow_report(cell, 'drc', gds, a, ['--antenna'] if antenna else [])
    cmd = 'python3 AFE/layout/scripts/flow.py drc --gds %s --top %s%s' % (rel(gds), cell, ' --antenna' if antenna else '')
    if d is None:
        R(False, 'DRC report %s missing' % rel(jf), 'run: ' + cmd)
    else:
        R(not stale, 'DRC report belongs to the current GDS (sha1)', 'the GDS changed after the DRC: run ' + cmd)
        R(d.get('ran') and d.get('variant') == 'D', 'DRC ran with the official deck, variant %s' % d.get('variant'), 'run: ' + cmd)
        if antenna:
            R(bool(d.get('antenna')), 'DRC included the antenna rules', 'run: ' + cmd)
        R(d.get('total') == 0, 'DRC %s: %s violations%s' % (cell, d.get('total'), (' ' + json.dumps(dict(list((d.get('rules') or {}).items())[:6]))) if d.get('total') else ''),
          'ACCEPT.md ladder D')
    dl, stale, jf = flow_report(cell, 'lvs', gds, a, ['--ref', ref] if ref else [])
    cmd = 'python3 AFE/layout/scripts/flow.py lvs --gds %s --top %s --ref %s' % (rel(gds), cell, rel(ref) if ref else '?')
    if dl is None:
        R(False, 'LVS report %s missing' % rel(jf), 'run: ' + cmd)
    else:
        R(not stale, 'LVS report belongs to the current GDS (sha1)', 'the GDS changed after the LVS: run ' + cmd)
        okref = dl.get('ref') in REF[cell]
        R(okref, 'LVS reference %s is a generated reference of AFE/layout/lvs or the phase\'s own AFE/layout/<cell dir>/lvs' % dl.get('ref'),
          'LVS against the generated reference only (common rule 10)')
        R(bool(dl.get('match')), 'LVS %s: %s' % (cell, dl.get('final') or dl.get('why', '')), 'ACCEPT.md ladder L')
        if dl.get('ref') and os.path.exists(os.path.join(REPO, dl['ref'])):
            hdr = open(os.path.join(REPO, dl['ref'])).read(600)
            R('DO NOT EDIT' in hdr and 'mk_lvs_netlists.py' in hdr, 'the reference was written by mk_lvs_netlists.py (header)', 'regenerate it with mk_lvs_netlists.py; never edit it by hand')
    return d, dl


def cref_keepout(gds):
    """L1a: inside the bottom-plate footprint of the Cref plate (the one MIM top plate of 59.07 um) adc_ch has nothing below Metal4 (SPEC.md 3.3 rule 3)"""
    try:
        import klayout.db as kdb
    except ImportError:
        R(False, 'Cref keep-out: python module klayout.db missing', 'run inside the course container')
        return
    ly = kdb.Layout()
    ly.read(gds)
    top = ly.cell('adc_ch') or ly.top_cell()
    li = lambda l, d: ly.find_layer(l, d)
    ft = li(75, 0)
    if ft is None:
        R(False, 'Cref keep-out: no FuseTop (MIM top plate, 75/0) shapes in %s' % rel(gds), 'draw Cref as ONE MIM plate of 59.07 um (SPEC.md 3.3)')
        return
    reg = kdb.Region(top.begin_shapes_rec(ft)).merged()
    um = ly.dbu
    cands = [p for p in reg.each() if abs(p.bbox().width() * um - 59.07) < 0.2 and abs(p.bbox().height() * um - 59.07) < 0.2]
    R(len(cands) == 1, 'Cref plate found: %d MIM top plate(s) of 59.07 x 59.07 um in adc_ch' % len(cands), 'Cref must be ONE 59.07 um plate (Decision 44i, SPEC.md section 6)')
    if not cands:
        return
    box = cands[0].bbox().enlarged(int(round(0.6 / um)))
    hits = []
    for name, (l, d) in (('comp', (22, 0)), ('poly2', (30, 0)), ('contact', (33, 0)), ('metal1', (34, 0)), ('via1', (35, 0)), ('metal2', (36, 0)), ('via2', (38, 0)), ('metal3', (42, 0)), ('via3', (40, 0))):
        i = li(l, d)
        if i is None:
            continue
        r = kdb.Region(top.begin_shapes_rec_overlapping(i, box)) & kdb.Region(box)
        if not r.is_empty():
            hits.append('%s %.1f um2' % (name, r.area() * um * um))
    R(not hits, 'Cref keep-out: nothing below Metal4 inside the Cref bottom-plate footprint%s (L3a puts 4 decap units there)' % ((': FOUND ' + ', '.join(hits)) if hits else ''),
      'move those shapes out of the footprint (SPEC.md 3.3 rule 3)')


def pex_check(cell, gds, a):
    d, stale, jf = flow_report(cell, 'pex', gds, a)
    cmd = 'python3 AFE/layout/scripts/flow.py pex --gds %s --top %s' % (rel(gds), cell)
    if d is None:
        R(False, 'PEX report %s missing' % rel(jf), 'run: ' + cmd)
        return None
    R(not stale, 'PEX report belongs to the current GDS (sha1)', 'run: ' + cmd)
    R(bool(d.get('ran')), 'PEX ran (%s mode)' % d.get('mode'), 'ACCEPT.md ladder P-1')
    R(d.get('census_equal_lvs') is True, 'PEX device census equals the LVS extraction', 'ACCEPT.md ladder P (run flow.py lvs first, then pex; rc mode failing: P-1)')
    hasmim = any('cap_mim' in k for k in (d.get('devices') or {}))
    R((d.get('mim_fix') is not None) or not hasmim, 'MIM top-plate correction applied (moved %s)' % (', '.join('%s %.1f fF' % kv for kv in sorted(((d.get('mim_fix') or {}).get('moved_fF') or {}).items())[:4]) or '-'),
      'never use --no-mimfix for a gate (SPEC.md section 7 item 4)')
    R(not d.get('unknown_models'), 'no unknown device model in the PEX netlist %s' % (d.get('unknown_models') or ''), 'ACCEPT.md ladder L-3')
    return d


def compare(phase, pexnet=None):
    rc, out = sh([sys.executable, 'AFE/layout/tb/compare.py', '--phase', phase, '--quiet'])
    cj = jload(os.path.join(LAY, 'sim', 'post', 'compare_%s.json' % phase)) or {}
    R(rc == 0, 'compare.py --phase %s: %s (%s PASS, %s WARN, %s FAIL, %d missing)' % (phase, cj.get('verdict'), cj.get('n_pass'), cj.get('n_warn'), cj.get('n_fail'), len(cj.get('missing') or [])),
      'AFE/layout/sim/post/compare_%s.md lists every FAIL; apply the ACCEPT.md ladder entry of that check (R amplifier, Q ADC, S supply, X crosstalk)' % phase)
    for f in cj.get('missing') or []:
        P('      missing: ' + f)
    lim = jload(os.path.join(LAY, 'accept_limits.json')) or {}
    bad = []
    for chk, d in lim.items():
        if chk.startswith('_') or d.get('phase') != phase:
            continue
        pj = jload(os.path.join(LAY, 'sim', 'post', chk + '.json'))
        if pj and pj.get('netlist') == 'schematic' and not chk.startswith(('top_supply', 'bias_startup')):
            bad.append(chk)
    R(not bad, 'post-layout results were simulated on extracted netlists%s' % ((': SCHEMATIC in ' + ' '.join(bad)) if bad else ''),
      'run the tb_*.py scripts with --netlist AFE/layout/sim/flow/<cell>.pex.spice (RUNBOOK.md)')


# ------------------------------------------------------------------ phases
def phase_dig(a):
    F = os.path.join(REPO, 'AFE', 'dig', 'final')
    need = ['afe_dig.gds', 'afe_dig.pnl.v', 'afe_dig.lef', 'afe_dig_pins.json']
    miss = [n for n in need if not os.path.exists(os.path.join(F, n))]
    R(not miss, 'AFE/dig/final/ has %s' % ', '.join(need), 'copy them from the final run (RUNBOOK.md L1d step 4); missing: ' + ' '.join(miss))
    rp = os.path.join(REPO, 'AFE', 'dig', 'reports')
    fs = open(os.path.join(rp, 'flow_summary.rpt')).read() if os.path.exists(os.path.join(rp, 'flow_summary.rpt')) else ''
    R('VERDICT: structure PASS; timing / route / Magic DRC / LVS PASS; max-slew / max-cap PASS' in fs, 'AFE/dig/reports/flow_summary.rpt VERDICT all PASS',
      'see the lines of flow_summary.rpt; CTS problems: ladder C-1; congestion: C-3')
    m = re.search(r'DIE 0\.0 0\.0 ([\d.]+) ([\d.]+) um', fs)
    if m:
        # the slot of the macro = floorplan.json cells.afe_dig w x h (R14: 425 x dig_h for N = 4; it was 820 x 110 for N = 8)
        sw, sh = 820.0, 110.0
        try:
            slot = json.load(open(os.path.join(LAY, 'floorplan.json')))['cells']['afe_dig']
            sw, sh = float(slot['w']), float(slot['h'])
        except Exception:
            pass
        R(float(m.group(1)) <= sw + 1e-6 and float(m.group(2)) <= sh + 1e-6, 'die %s x %s um <= the slot %g x %g um of floorplan.json' % (m.group(1), m.group(2), sw, sh), 'ladder C-3 (then floorplan.py build --set dig_h=...)')
    kd = open(os.path.join(rp, 'klayout_drc.log')).read() if os.path.exists(os.path.join(rp, 'klayout_drc.log')) else ''
    gsz = os.path.getsize(os.path.join(F, 'afe_dig.gds')) if not miss else -1
    m = re.search(r'\((\d+) bytes\)', kd)
    R('RESULT KLayout DRC variant D: PASS' in kd and m is not None and int(m.group(1)) == gsz,
      'KLayout DRC variant D of afe_dig PASS on the GDS in AFE/dig/final (%s bytes in the log, %d committed)' % (m.group(1) if m else '?', gsz),
      'run: bash AFE/dig/scripts/drc_dig.sh AFE/dig/final/afe_dig.gds (ladder D on violations)')
    st = open(os.path.join(rp, 'sta_audit_dig.log')).read() if os.path.exists(os.path.join(rp, 'sta_audit_dig.log')) else ''
    m = re.search(r'L1D_LIMITS dac_cmp0_ff_n40=([\d.]+) window_pin_ss_125=([\d.]+) window_flop_ss_125=([\d.]+) cap_code_slack_3MHz_ss_125=([\d.]+)', st)
    if not m:
        R(False, 'AFE/dig/reports/sta_audit_dig.log has the L1D_LIMITS line', 'run python3 AFE/review/scripts/sta_audit.py with --dig (RUNBOOK.md L1d step 3)')
    else:
        a_, b_, c_, s_ = [float(x) for x in m.groups()]
        R(a_ >= 21.0, '(a) DAC edge -> comparator clock of ADC 0 at ff_n40: %.2f ns >= 21.0' % a_, 'ladder C-2')
        R(c_ >= 20.0, '(c) last window end -> next SCLK edge at the flop clock pins, ss_125: %.2f ns >= 20.0 (against the pin: %.2f ns, reported)' % (c_, b_), 'ladder C-2')
        R(s_ >= 10.0, 'captured decision -> code register slack at 3 MHz, ss_125: %.2f ns >= 10' % s_, 'ladder C-2')
    sk = [float(x) for x in re.findall(r'\|\s+([\d.]+) / ([\d.]+)\s+([\d.]+) / ([\d.]+)', st) for x in x]
    if sk:
        R(max(sk) <= 3.0, 'sw_rec / sw_ipg pair skew at the macro pins <= 3 ns: worst %.3f ns' % max(sk), 'a missing buffer on one side of the pair: check sw_pair cells in flow_summary.rpt')
    ts = os.path.join(REPO, 'AFE', 'dig', 'sim', 'tb_audit_dig_summary.log')
    bad = []
    for l in (open(ts).read().split('\n') if os.path.exists(ts) else []):
        if 'FAILS:' not in l:
            continue
        allowed = DIG_ALLOWED | ({'T2.settle'} if 'MIXED' in l else set())
        bad += [x for x in l.split('FAILS:')[1].split() if x not in allowed]
    R(os.path.exists(ts) and not bad, 'gate-level testbench on the hardened netlist: only accepted assertion failures%s' % ((': ALSO ' + ' '.join(sorted(set(bad)))) if bad else ''),
      'run: bash AFE/review/scripts/run_tb_audit.sh dig <final dir>; other failures: ladder C-4')
    td = os.path.join(REPO, 'AFE', 'dig', 'sim', 'top_dig.log')
    R(os.path.exists(td) and 'EQUIV PASS' in open(td).read(), 'run_top_sim.sh dig: EQUIV PASS (afe_dig equals the two RTL instances + ties)', 'run: (cd AFE/top && bash run_top_sim.sh dig)')
    cl = os.path.join(LAY, 'lvs', 'check_lvs_netlists.log')
    R(os.path.exists(cl) and 'SUMMARY: A PASS, B PASS, C PASS' in open(cl).read(), 'check_lvs_netlists.py SUMMARY A, B, C PASS', 'run: python3 AFE/layout/scripts/check_lvs_netlists.py')
    hdr = open(os.path.join(LAY, 'lvs', 'dbs_afe_top.spice')).read(800)
    R('--dig-netlist AFE/dig/final/afe_dig.pnl.v' in hdr, 'the LVS top was written from AFE/dig/final/afe_dig.pnl.v (header of AFE/layout/lvs/dbs_afe_top.spice)',
      'run: python3 AFE/layout/scripts/mk_lvs_netlists.py --decap-n 74,64 --dig-netlist AFE/dig/final/afe_dig.pnl.v (+ the other options in the current header)')
    floorplan([], os.path.join(F, 'afe_dig_pins.json') if not miss else None)


def lvs_decap():
    txt = open(os.path.join(LAY, 'lvs', 'dbs_afe_top.spice')).read()
    m1 = re.search(r'^Xu_dcm VDD VSS cap_nmos_03v3 c_length=20u c_width=20u m=(\d+)', txt, re.M)
    m2 = re.search(r'^Xu_dcd vdd_dac VSS cap_nmos_03v3 c_length=20u c_width=20u m=(\d+)', txt, re.M)
    if not (m1 and m2):
        R(False, 'decap devices Xu_dcm / Xu_dcd with 20 x 20 um units in AFE/layout/lvs/dbs_afe_top.spice', 'regenerate with --decap 20,20 --decap-n NMAIN,NDAC (SPEC.md section 4)')
        return
    cm, cd = int(m1.group(1)) * DECAP_PF, int(m2.group(1)) * DECAP_PF
    R(cm >= 115 and cd >= 95, 'decap in the LVS top (= drawn, LVS matched): ADC-main %d units = %.1f pF >= 115, ADC-DAC %d units = %.1f pF >= 95' % (int(m1.group(1)), cm, int(m2.group(1)), cd),
      'draw more units (SPEC.md section 4 reserve) and regenerate with --decap-n')


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('phase', choices=PHASES)
    ap.add_argument('--gds', default=None)
    ap.add_argument('--run', action='store_true')
    ap.add_argument('--no-findings', action='store_true', help='skip the findings / Results-log checks (to test the technical part before writing the findings)')
    a = ap.parse_args()
    ph = a.phase
    P('gate.py %s  (%s)' % (ph, ' '.join(sys.argv[1:])))
    common(ph, a)
    cell = CELL.get(ph)
    gds = None
    if cell:
        gds = os.path.abspath(a.gds) if a.gds else first(GDS_DEFAULT[cell])
        P('--- %s layout: %s' % (cell, rel(gds) if gds else 'NOT FOUND'))
        if not gds or not os.path.exists(gds):
            R(False, 'GDS of %s found' % cell, 'pass --gds <file> or write it to %s' % GDS_DEFAULT[cell][0])
    if ph == 'L1d':
        P('--- afe_dig')
        phase_dig(a)
    elif gds and os.path.exists(gds):
        if ph in ('L2a', 'L1a', 'L3a'):
            drc_lvs(cell, gds, a, antenna=(ph == 'L3a'))
            if ph == 'L1a':
                cref_keepout(gds)
            if ph == 'L3a':
                lvs_decap()
                compare('L3a')
                dp = os.path.join(REPO, 'AFE', 'dig', 'final', 'afe_dig_pins.json')
                floorplan(['dbs_afe_top=' + gds], dp if os.path.exists(dp) else None)
            else:
                floorplan(['%s=%s' % (cell, gds)], None)
        else:
            P('--- layout still clean (the PEX is of the layout that passed DRC / LVS)')
            drc_lvs(cell, gds, a, antenna=(ph == 'L3b'))
            P('--- PEX')
            pex_check(cell, gds, a)
            P('--- post-layout limits')
            compare(ph)
    if ph == 'L4':
        P('--- submission')
        rc, out = sh([sys.executable, 'AFE/layout/scripts/check_submission.py'])
        for l in out.strip().split('\n')[-30:]:
            P('      ' + l)
        R(rc == 0, 'check_submission.py: %s' % ('PASS' if rc == 0 else 'FAIL'), 'fix every FAIL line of check_submission.py')
    verdict = 'PASS' if NF[0] == 0 else 'FAIL'
    P('GATE %s: %s  (%d FAIL)' % (ph, verdict, NF[0]))
    os.makedirs(os.path.join(LAY, 'sim'), exist_ok=True)
    open(os.path.join(LAY, 'sim', 'gate_%s.log' % ph), 'w').write('\n'.join(OUT) + '\n')
    return 0 if verdict == 'PASS' else 1


if __name__ == '__main__':
    sys.exit(main())
