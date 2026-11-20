#!/usr/bin/env python3
"""check_prompts.py (LP kit, step 8): every file, script and directory that the layout prompts mention must exist now, or be produced by a named phase / kit command.

  python3 AFE/layout/scripts/check_prompts.py [files ...]     default: AFE/prompts/layout_run.md AFE/layout/RUNBOOK.md AFE/layout/ACCEPT.md AFE/layout/SPEC.md
Paths are taken from the text (tokens starting with AFE/, gds/, spice/, verilog/, documents/, TGATE/, rtl/, or the root files info.yaml, lvs_config.json, README.md); `<...>` and `*`
are wildcards, `{a,b}` is expanded.  A path that does not exist passes only if it matches PRODUCED below (the phase that makes it).  Writes AFE/layout/sim/check_prompts.log; exit 1 on a miss."""
import os, re, sys, glob, fnmatch
HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.normpath(os.path.join(HERE, '..', '..', '..'))
DEFAULT = ['AFE/prompts/layout_run.md', 'AFE/layout/RUNBOOK.md', 'AFE/layout/ACCEPT.md', 'AFE/layout/SPEC.md']
PRODUCED = [   # (fnmatch pattern, who makes it)
    ('AFE/layout/amp*', 'L2a'), ('AFE/layout/FLOW.md', 'L2a'), ('AFE/layout/NOTES_L2.md', 'L2a'),
    ('AFE/layout/adc*', 'L1a (adc_ch generator, GDS, logs; adc/lvs only if L1a regenerates the reference)'),
    ('AFE/dig/final*', 'L1d (step 4)'),
    ('AFE/layout/top*', 'L3a'),
    ('AFE/layout/sim/flow*', 'flow.py (every phase)'), ('AFE/layout/sim/post*', 'tb_*.py / compare.py (L2b, L1b, L3a, L3b)'), ('AFE/layout/sim/gate_*', 'gate.py'),
    ('AFE/layout/reports/L*.md', 'each phase (common rule 7)'), ('AFE/layout/reports/<phase>.md', 'each phase'),
    ('AFE/layout/BLOCKED.md', 'a phase, only as the last resort (ACCEPT.md section 6)'),
    ('AFE/layout/organizer*', 'the phase that receives the organizer DEF (SPEC.md section 2)'),
    ('spice*', 'L4 (step 1)'), ('verilog*', 'L4 (step 1)'),
    ('AFE/dig/sim/tb_audit_dig_*', 'run_tb_audit.sh dig (L1d)'), ('AFE/layout/*/lvs', 'L2a / L1a, only when they regenerate a reference (ladder L-1)'),
]
TOK = re.compile(r'(?<![\w/.$-])((?:AFE|gds|spice|verilog|documents|TGATE|rtl)/[A-Za-z0-9_./<>{}*,\[\]-]*[A-Za-z0-9_>}*/]|info\.yaml|lvs_config\.json|README\.md)')


def expand(tok):
    m = re.search(r'\{([^{}]*)\}', tok)
    if not m:
        return [tok]
    return [x for alt in m.group(1).split(',') for x in expand(tok[:m.start()] + alt.strip() + tok[m.end():])]


def main():
    files = sys.argv[1:] or DEFAULT
    out, miss = [], 0
    seen = set()
    for f in files:
        txt = open(os.path.join(REPO, f)).read()
        txt = re.sub(r'<([^<>\n]{1,40})>', lambda m: '<' + m.group(1).replace(' ', '_') + '>', txt)          # <cell dir> -> one token
        txt = re.sub(r'\{([^{}\n]{1,200})\}', lambda m: '{' + m.group(1).replace(', ', ',') + '}', txt)          # {a, b} -> {a,b}
        txt = re.sub(r'\$\w+', '*', txt)                                                                          # tb_$t.py -> tb_*.py
        for m in TOK.finditer(txt):
            raw = re.sub(r'[.,*]+$', '', m.group(1)) if not m.group(1).endswith(('*.py', '/*')) else m.group(1)
            for p in expand(raw):
                p = p.rstrip('/').rstrip('.,')
                if p in seen or not p:
                    continue
                seen.add(p)
                pat = re.sub(r'<[^>]*>', '*', p)
                hit = glob.glob(os.path.join(REPO, pat)) if ('*' in pat or '[' in pat) else ([p] if os.path.exists(os.path.join(REPO, p)) else [])
                if '[' in pat and not hit and os.path.exists(os.path.join(REPO, p)):
                    hit = [p]
                if hit:
                    out.append('OK       %s  (%s)' % (p, f))
                    continue
                who = [w for pt, w in PRODUCED if fnmatch.fnmatch(p, pt) or fnmatch.fnmatch(pat, pt) or p.startswith(pt.rstrip('*'))]
                if who:
                    out.append('LATER    %s  -> made by %s  (%s)' % (p, who[0], f))
                else:
                    out.append('MISSING  %s  (%s)' % (p, f))
                    miss += 1
    s = 'RESULT check_prompts: %s  (%d paths, %d missing) in %s' % ('PASS' if not miss else 'FAIL', len(seen), miss, ' '.join(files))
    out.append(s)
    for l in out:
        if not l.startswith('OK'):
            print(l)
    os.makedirs(os.path.join(REPO, 'AFE', 'layout', 'sim'), exist_ok=True)
    open(os.path.join(REPO, 'AFE', 'layout', 'sim', 'check_prompts.log'), 'w').write('\n'.join(out) + '\n')
    return 1 if miss else 0


if __name__ == '__main__':
    sys.exit(main())
