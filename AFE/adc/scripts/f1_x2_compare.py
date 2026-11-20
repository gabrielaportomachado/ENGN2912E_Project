#!/usr/bin/env python3
"""F1 (Decision 44a / 44d): compare the ADC-alone closed-loop replays made after the F1 netlist changes (sim/f1_x2_adc.log, written by
`X2_ADC_LOG=sim/f1_x2_adc.log python3 scripts/x2_adc.py ...`) with the X2 baseline blocks of sim/x2_adc.log (same corner, same reference variant, same inputs, no testbench override).
Per input: the code of the last frame, the code of the first conversion from the DC operating point, and the transition offset T [LSB].  PASS = every code identical.
usage: python3 f1_x2_compare.py [out.log]     (default sim/f1_x2_compare.log)"""
import os, re, sys
H = os.path.dirname(os.path.abspath(__file__)); ADC = os.path.abspath(os.path.join(H, '..'))


def blocks(path):
    """list of dict(title, head, rows={vin: (code, code0, T, T0)}, summary) in file order; title = the '# =====' line before the block, if any"""
    out = []; cur = None; title = ''
    for ln in open(path):
        ln = ln.rstrip('\n')
        if ln.startswith('# ====='):
            title = ln[7:].strip(); continue
        if ln.startswith('# X2 ADC alone'):
            m = re.search(r'corner (\S+) .*reference variant (\w+)', ln)
            cur = dict(title=title, head=ln, corner=m.group(1), ref=m.group(2), override=('OVERRIDE' in ln), rows={}, summary='')
            out.append(cur); title = ''; continue
        m = re.match(r'ADC (\S+) (\w+) vin ([\d.]+) code (\d+) ideal \d+ diff \S+ \| T (\S+) LSB \| x12 \S+ LSB \| first conversion from the DC op: code (\d+), T (\S+) \|', ln)
        if m and cur is not None:
            cur['rows'][m.group(3)] = (int(m.group(4)), int(m.group(6)), float(m.group(5)), float(m.group(7)))
        if ln.startswith('SUMMARY') and cur is not None:
            cur['summary'] = ln
    return out


if __name__ == '__main__':
    path = sys.argv[1] if len(sys.argv) > 1 else f'{ADC}/sim/f1_x2_compare.log'
    out = open(path, 'w')
    P = lambda *a: (print(*a), print(*a, file=out))
    base = [b for b in blocks(f'{ADC}/sim/x2_adc.log') if not b['override']]
    new = blocks(f'{ADC}/sim/f1_x2_adc.log')
    P('F1: ADC alone, closed-loop replay (scripts/x2_adc.py), after the F1 netlist changes, against the X2 baseline sim/x2_adc.log.  Codes are the circuit\'s own decisions.')
    allok = bool(new)
    for nb in new:
        cand = [b for b in base if b['corner'] == nb['corner'] and b['ref'] == nb['ref'] and set(b['rows']) == set(nb['rows'])]
        P('\nRUN: %s' % (nb['title'] or nb['head'][:120]))
        if not cand:
            P('  no baseline block with the same corner / reference / inputs: NOT COMPARED'); allok = False; continue
        b = cand[0]
        P('  %-9s | %-11s %-11s | %-11s %-11s | %-9s %-9s %-8s | %s' % ('Vin [V]', 'code X2', 'code F1', 'first X2', 'first F1', 'T X2', 'T F1', 'dT [LSB]', 'codes'))
        nd = 0; dtm = 0.0
        for v in sorted(nb['rows'], key=float):
            c1, f1, t1, _ = b['rows'][v]; c2, f2, t2, _ = nb['rows'][v]
            same = (c1 == c2 and f1 == f2); nd += (not same); dtm = max(dtm, abs(t2 - t1))
            P('  %-9s | %-11d %-11d | %-11d %-11d | %+9.3f %+9.3f %+8.3f | %s' % (v, c1, c2, f1, f2, t1, t2, t2 - t1, 'same' if same else 'DIFFERENT'))
        g = lambda s, pat: (re.search(pat, s).group(1) if re.search(pat, s) else '?')
        P('  code - ideal code, mean: X2 %s, F1 %s;  transition offset T mean: X2 %s LSB, F1 %s LSB;  theta: X2 %s, F1 %s LSB' % (
            g(b['summary'], r'code - ideal code: mean (\S+),'), g(nb['summary'], r'code - ideal code: mean (\S+),'),
            g(b['summary'], r'transition offset T: mean (\S+) LSB'), g(nb['summary'], r'transition offset T: mean (\S+) LSB'),
            g(b['summary'], r'theta (\S+) LSB'), g(nb['summary'], r'theta (\S+) LSB')))
        ok = nd == 0
        allok = allok and ok
        P('  %d inputs x 2 frames: %d code differences, max |dT| %.3f LSB  -> %s' % (len(nb['rows']), nd, dtm, 'PASS (identical codes)' if ok else 'FAIL'))
    P('\nRESULT F1 ADC-alone replay: %s' % ('PASS: identical codes in every run' if allok else 'FAIL'))
    out.close()
    sys.exit(0 if allok else 1)
