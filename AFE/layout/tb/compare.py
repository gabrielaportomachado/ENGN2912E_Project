#!/usr/bin/env python3
"""compare.py (LP kit, step 3): baseline (schematic) versus post-layout results of the golden testbenches -> change table with PASS / WARN / FAIL against AFE/layout/accept_limits.json
(the machine-readable copy of the limits of AFE/layout/ACCEPT.md).

  python3 AFE/layout/tb/compare.py --phase L2b            every check of the phase: AFE/layout/baseline/<check>.json against AFE/layout/sim/post/<check>.json
  python3 AFE/layout/tb/compare.py --checks amp_ac,amp_noise [--post DIR] [--base DIR]
  python3 AFE/layout/tb/compare.py --phase L2b --selftest baseline against itself: shows that the pre-layout design meets the limits (and that the script works)
  python3 AFE/layout/tb/compare.py --limits-md             the limits as a Markdown table;  --write-accept puts it into ACCEPT.md section 3,  --check-accept tests that the two agree (gate.py does)
Writes <post>/compare_<phase>.md and .json; exit code 0 = no FAIL (WARN does not fail), 1 = at least one FAIL, 2 = a result file is missing or a check ended with an error.
A check that the phase needs but that was not run counts as a FAIL (use --allow-missing only while debugging).
Derived values: amp_ac.hf_dev_db = largest |change| of the hf_ values (stand-in for the loop margin); amp_noise.noise_d8_post_uv = baseline noise_d8_uv x post / pre of noise_real_uv
(the Decision-8 noise figure cannot be simulated on an extracted netlist, the real-device figure can)."""
import os, sys, json, argparse, math

HERE = os.path.dirname(os.path.abspath(__file__))
LAY = os.path.normpath(os.path.join(HERE, '..'))
REPO = os.path.normpath(os.path.join(LAY, '..', '..'))
LIM = os.path.join(LAY, 'accept_limits.json')
BASE = os.path.join(LAY, 'baseline')
POST = os.path.join(LAY, 'sim', 'post')


def num(x):
    return isinstance(x, (int, float)) and not isinstance(x, bool) and x == x


def lim_of(rule, corner):
    l = rule.get('limit')
    if isinstance(l, dict):
        return l.get(corner)
    return l


def derived(check, corner, post, base):
    """adds the derived values to the post dict (in place)"""
    if check.startswith('amp_ac') and base:
        d = [abs(post[k] - base[k]) for k in post if k.startswith('hf_') and k != 'hf_dev_db' and num(post.get(k)) and num(base.get(k))]
        if d:
            post['hf_dev_db'] = max(d)
    if check == 'amp_noise' and base and num(post.get('noise_real_uv')) and num(base.get('noise_real_uv')) and num(base.get('noise_d8_uv')):
        post['noise_d8_post_uv'] = base['noise_d8_uv'] * post['noise_real_uv'] / base['noise_real_uv']


def judge(rule, v, b, corner):
    """-> (status, text of the limit)"""
    k = rule['kind']
    L = lim_of(rule, corner)
    if k == 'report' or L is None:
        return 'info', ''
    if not num(v):
        return ('PASS', 'nan allowed') if rule.get('nan_ok') else ('FAIL', 'no value')
    ok, txt = True, ''
    if k == 'max':
        ok, txt = v <= L, '<= %g' % L
    elif k == 'min':
        ok, txt = v >= L, '>= %g' % L
    elif k == 'range':
        ok, txt = L[0] <= v <= L[1], '%g .. %g' % (L[0], L[1])
    elif k == 'absmax':
        ok, txt = abs(v) <= L, '|x| <= %g' % L
    elif k in ('dmax', 'dinc', 'rrange'):
        if not num(b):
            return 'FAIL', 'no baseline value'
        if k == 'dmax':
            ok, txt = abs(v - b) <= L, '|change| <= %g' % L
        elif k == 'dinc':
            ok, txt = (v - b) <= L, 'change <= %+g' % L
        else:
            r = v / b if b else float('inf')
            ok, txt = L[0] <= r <= L[1], 'x / baseline %g .. %g' % (L[0], L[1])
    else:
        return 'FAIL', 'unknown kind %s' % k
    if ok:
        return 'PASS', txt
    return ('WARN' if rule.get('soft') else 'FAIL'), txt


def f(x):
    if not num(x):
        return 'nan' if isinstance(x, float) else ('-' if x is None else str(x)[:14])
    return '%.5g' % x


def limits_md(lim):
    out = ['| check | phase | value | corners | limit | soft | why |', '|---|---|---|---|---|---|---|']
    for chk, d in lim.items():
        if chk.startswith('_'):
            continue
        for m, rules in d['metrics'].items():
            for r in rules:
                if r['kind'] == 'report':
                    continue
                L = r['limit']
                if isinstance(L, dict):
                    cs = ' / '.join(L)
                    lt = ' / '.join(judge(dict(r, limit=L[c]), 0.0, 1.0, c)[1] for c in L)
                else:
                    cs, lt = 'all', judge(r, 0.0, 1.0, 'x')[1]
                out.append('| %s | %s | %s | %s | %s | %s | %s |' % (chk, d.get('phase', ''), m, cs, lt, 'WARN only' if r.get('soft') else '', r.get('why', '')))
    return '\n'.join(out)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--phase', default=None)
    ap.add_argument('--checks', default=None)
    ap.add_argument('--base', default=BASE)
    ap.add_argument('--post', default=POST)
    ap.add_argument('--selftest', action='store_true')
    ap.add_argument('--allow-missing', action='store_true')
    ap.add_argument('--limits-md', action='store_true')
    ap.add_argument('--write-accept', action='store_true', help='write the limits table into AFE/layout/ACCEPT.md (between its LIMITS markers)')
    ap.add_argument('--check-accept', action='store_true', help='exit 0 if the table in ACCEPT.md equals accept_limits.json')
    ap.add_argument('--quiet', action='store_true')
    a = ap.parse_args()
    lim = json.load(open(LIM))
    if a.limits_md or a.write_accept or a.check_accept:
        md = limits_md(lim)
        acc = os.path.join(LAY, 'ACCEPT.md')
        if a.limits_md:
            print(md)
            return 0
        txt = open(acc).read()
        b0, b1 = '<!-- LIMITS BEGIN (written by compare.py --write-accept from accept_limits.json; do not edit by hand) -->', '<!-- LIMITS END -->'
        if b0 not in txt or b1 not in txt:
            print('ACCEPT.md has no LIMITS block')
            return 2
        cur = txt[txt.index(b0) + len(b0):txt.index(b1)].strip()
        if a.check_accept:
            ok = (cur == md.strip())
            print('ACCEPT.md limits table %s accept_limits.json' % ('equals' if ok else 'DIFFERS from'))
            return 0 if ok else 1
        open(acc, 'w').write(txt[:txt.index(b0) + len(b0)] + '\n' + md + '\n' + txt[txt.index(b1):])
        print('ACCEPT.md limits table written (%d rows)' % (md.count('\n') - 1))
        return 0
    checks = [c for c in lim if not c.startswith('_') and ((a.checks and c in a.checks.split(',')) or (a.phase and lim[c].get('phase') == a.phase))]
    if not checks:
        ap.error('no check selected: --phase L2b | L1b | L3a | L3b or --checks a,b (known: %s)' % ' '.join(c for c in lim if not c.startswith('_')))
    post_dir = a.base if a.selftest else a.post
    rows, missing, nf, nw, npass = [], [], 0, 0, 0
    for chk in checks:
        pj, bj = os.path.join(post_dir, chk + '.json'), os.path.join(a.base, chk + '.json')
        if not os.path.exists(pj):
            missing.append('%s: %s does not exist (run AFE/layout/tb/tb_%s.py --netlist <PEX> --corner all%s)' % (chk, os.path.relpath(pj, REPO), chk.replace('_junction', '').replace('_host', ''),
                                                                                                            ' --junction' if chk.endswith('_junction') else ''))
            continue
        post = json.load(open(pj))
        base = json.load(open(bj)) if os.path.exists(bj) else {'corners': {}}
        if not base['corners'] and not a.selftest:
            missing.append('%s: no baseline %s' % (chk, os.path.relpath(bj, REPO)))
        for corner, ent in post['corners'].items():
            pv = dict(ent['values'])
            bv = base['corners'].get(corner, {}).get('values', {})
            if 'error' in pv:
                missing.append('%s %s: the check ended with an error: %s' % (chk, corner, str(pv['error'])[:160]))
                continue
            derived(chk, corner, pv, bv)
            if a.selftest and chk == 'amp_noise' and num(pv.get('noise_d8_uv')):
                pv['noise_d8_post_uv'] = pv['noise_d8_uv']
            for m, rules in lim[chk]['metrics'].items():
                for r in rules:
                    st, txt = judge(r, pv.get(m), bv.get(m), corner)
                    if st == 'info' and m not in pv:
                        continue
                    if st == 'FAIL':
                        nf += 1
                    elif st == 'WARN':
                        nw += 1
                    elif st == 'PASS':
                        npass += 1
                    ch = (pv.get(m) - bv.get(m)) if (num(pv.get(m)) and num(bv.get(m))) else None
                    rows.append(dict(check=chk, corner=corner, value=m, baseline=bv.get(m), post=pv.get(m), change=ch, limit=txt, status=st, why=r.get('why', '')))
    title = '%s: %s against %s' % (a.phase or a.checks, 'baseline (selftest)' if a.selftest else os.path.relpath(post_dir, REPO), os.path.relpath(a.base, REPO))
    md = ['# compare.py ' + title, '', '| check | corner | value | baseline | post-layout | change | limit | result |', '|---|---|---|---|---|---|---|---|']
    for r in rows:
        md.append('| %s | %s | %s | %s | %s | %s | %s | %s |' % (r['check'], r['corner'], r['value'], f(r['baseline']), f(r['post']), ('%+.4g' % r['change']) if r['change'] is not None else '', r['limit'],
                                                               '' if r['status'] == 'info' else r['status']))
    md += [''] + ['MISSING: ' + m for m in missing]
    verdict = 'FAIL' if (nf or (missing and not a.allow_missing)) else 'PASS'
    md.append('RESULT compare %s: %s  (%d PASS, %d WARN, %d FAIL, %d missing)' % (a.phase or a.checks, verdict, npass, nw, nf, len(missing)))
    tag = (a.phase or 'sel') + ('_selftest' if a.selftest else '')
    os.makedirs(a.post, exist_ok=True)
    open(os.path.join(a.post, 'compare_%s.md' % tag), 'w').write('\n'.join(md) + '\n')
    json.dump(dict(title=title, verdict=verdict, n_pass=npass, n_warn=nw, n_fail=nf, missing=missing, rows=rows, limits_file='AFE/layout/accept_limits.json'), open(os.path.join(a.post, 'compare_%s.json' % tag), 'w'), indent=1)
    if not a.quiet:
        for r in rows:
            if r['status'] in ('FAIL', 'WARN'):
                print('%-4s %s %s %s: baseline %s, post %s, limit %s  (%s)' % (r['status'], r['check'], r['corner'], r['value'], f(r['baseline']), f(r['post']), r['limit'], r['why'][:110]))
        for m in missing:
            print('MISSING ' + m)
        print(md[-1] + '   -> ' + os.path.relpath(os.path.join(a.post, 'compare_%s.md' % tag), REPO))
    return 0 if verdict == 'PASS' else (2 if missing and not nf else 1)


if __name__ == '__main__':
    sys.exit(main())
