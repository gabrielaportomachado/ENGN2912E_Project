#!/usr/bin/env python3
"""mk_tables.py (REVIEW.md R13): merges the compare.py tables (compare.py --phase L2b --post <case dir>) of the pad cases with the reference without the pad
(AFE/layout/sim/post for the extracted netlist, AFE/layout/baseline for the schematic) -> AFE/layout/sim/recpad/recpad_table.md  (+ recpad_table.json).
Every row of AFE/layout/accept_limits.json that has a limit: value without the pad, value with the pad, delta, limit, margin to the limit with / without, status with the pad.
usage: python3 AFE/layout/sim/recpad/mk_tables.py [case ...]    (default: every case directory that has compare_L2b.json; run compare.py for it first: `--run`)"""
import os, sys, json, subprocess, re, shutil
HERE = os.path.dirname(os.path.abspath(__file__))
LAY = os.path.normpath(os.path.join(HERE, '..', '..'))
REPO = os.path.normpath(os.path.join(LAY, '..', '..'))
LIM = json.load(open(os.path.join(LAY, 'accept_limits.json')))
CASES = ['pex_open', 'pex_probe', 'sch_open', 'sch_probe']
WHATIF = ['pex_probe_100M', 'pex_probe_ac', 'pex_probe_rs100k', 'pex_leak_1n', 'pex_leak_10n', 'pex_ctl_1f', 'pex_check_nodiodes']      # `mk_tables.py --whatif`: tables of the what-if / control runs (only the checks that were run)


def key(r):
    return (r['check'], r['corner'], r['value'])


def margin(rule_txt, v):
    """margin to the limit text of compare.py (only simple '<= x', '>= x', 'a .. b'); positive = inside"""
    m = re.match(r'^<= ([-0-9.e+]+)$', rule_txt)
    if m:
        return float(m.group(1)) - v
    m = re.match(r'^>= ([-0-9.e+]+)$', rule_txt)
    if m:
        return v - float(m.group(1))
    m = re.match(r'^([-0-9.e+]+) \.\. ([-0-9.e+]+)$', rule_txt)
    if m:
        return min(v - float(m.group(1)), float(m.group(2)) - v)
    m = re.match(r'^\|x\| <= ([-0-9.e+]+)$', rule_txt)
    if m:
        return float(m.group(1)) - abs(v)
    return None


def load_rows(path):
    d = json.load(open(path))
    return d, {key(r): r for r in d['rows']}


def main():
    whatif = '--whatif' in sys.argv
    cases = [c for c in (sys.argv[1:] or (WHATIF if whatif else CASES)) if not c.startswith('--')]
    run = '--run' in sys.argv
    out, summary = [], []
    allj = {}
    for case in cases:
        d = os.path.join(HERE, case)
        if not os.path.isdir(d):
            continue
        if run or not os.path.exists(os.path.join(d, 'compare_L2b.json')):
            subprocess.run([sys.executable, os.path.join(LAY, 'tb', 'compare.py'), '--phase', 'L2b', '--post', d, '--quiet'], check=False)
        pj, prow = load_rows(os.path.join(d, 'compare_L2b.json'))
        ref = os.path.join(LAY, 'baseline') if case.startswith('sch') else os.path.join(LAY, 'sim', 'post')
        # the reference without the pad: compare.py on the committed results, run in a scratch copy (nothing under baseline / sim/post is rewritten)
        sch = case.startswith('sch')
        rd = os.path.join(HERE, '_ref_' + ('sch' if sch else 'pex'))
        rj = os.path.join(rd, 'compare_L2b%s.json' % ('_selftest' if sch else ''))
        if not os.path.exists(rj):
            os.makedirs(rd, exist_ok=True)
            if not sch:
                for f in os.listdir(os.path.join(LAY, 'sim', 'post')):
                    if f.endswith('.json') and not f.startswith('compare_'):
                        shutil.copy(os.path.join(LAY, 'sim', 'post', f), rd)
            subprocess.run([sys.executable, os.path.join(LAY, 'tb', 'compare.py'), '--phase', 'L2b', '--post', rd, '--quiet'] + (['--selftest'] if sch else []), check=False)
        rjd, rrow = load_rows(rj)
        rows = []
        for k, r in prow.items():
            if r['status'] == 'info' or not r['limit'] or not os.path.exists(os.path.join(d, k[0] + '.json')):
                continue
            q = rrow.get(k)
            v, v0 = r['post'], (q['post'] if q else None)
            dl = (v - v0) if isinstance(v, (int, float)) and isinstance(v0, (int, float)) else None
            rows.append(dict(check=k[0], corner=k[1], value=k[2], without=v0, with_pad=v, delta=dl, limit=r['limit'], status=r['status'], status_without=(q['status'] if q else '-'),
                             margin_with=(margin(r['limit'], v) if isinstance(v, (int, float)) else None), margin_without=(margin(r['limit'], v0) if isinstance(v0, (int, float)) else None)))
        nf = sum(1 for r in rows if r['status'] == 'FAIL')
        nw = sum(1 for r in rows if r['status'] == 'WARN')
        nf0 = sum(1 for r in rows if r['status_without'] == 'FAIL')
        summary.append('| %s | %d | %d PASS / %d WARN / %d FAIL | %d FAIL | %s |' % (case, len(rows), len(rows) - nf - nw, nw, nf, nf0, pj['verdict']))
        allj[case] = rows
        out += ['', '## %s' % case, '', '| check | corner | value | without pad | with pad | delta | limit | margin without | margin with | result |', '|---|---|---|---|---|---|---|---|---|---|']
        g = lambda x: ('%.5g' % x) if isinstance(x, (int, float)) and x == x else ('nan' if isinstance(x, float) else '-')
        for r in rows:
            out.append('| %s | %s | %s | %s | %s | %s | %s | %s | %s | %s |' % (r['check'], r['corner'], r['value'], g(r['without']), g(r['with_pad']), g(r['delta']), r['limit'], g(r['margin_without']),
                                                                              g(r['margin_with']), r['status']))
    md = ['# R13 recpad_table.md (written by mk_tables.py; limits = AFE/layout/accept_limits.json, Decision 51)', '', '| case | rows with a limit | with the pad | without the pad | compare.py verdict |', '|---|---|---|---|---|'] + summary + out
    open(os.path.join(HERE, 'recpad_whatif_table.md' if whatif else 'recpad_table.md'), 'w').write('\n'.join(md) + '\n')
    json.dump(allj, open(os.path.join(HERE, 'recpad_whatif_table.json' if whatif else 'recpad_table.json'), 'w'), indent=1)
    print('\n'.join(summary))


if __name__ == '__main__':
    main()
