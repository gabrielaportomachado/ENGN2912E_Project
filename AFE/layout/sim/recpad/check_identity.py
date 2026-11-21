#!/usr/bin/env python3
"""check_identity.py (REVIEW.md R13): without --rec-load the modified AFE/layout/tb/lptb.py must produce byte-identical benches to the committed version of before R13.
usage: python3 AFE/layout/sim/recpad/check_identity.py        (the old version = `git show fb5b7bd:AFE/layout/tb/lptb.py`, written to the temporary file AFE/layout/tb/_lptb_old_r13.py, which is
deleted again: the include paths of a bench depend on where lptb.py sits; prints one line per bench and the verdict; exit 1 on a difference)"""
import sys, os, importlib.util, subprocess
HERE = os.path.dirname(os.path.abspath(__file__))
TB = os.path.normpath(os.path.join(HERE, '..', '..', 'tb'))
sys.path.insert(0, TB)


def load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


new = load(os.path.join(TB, 'lptb.py'), 'lptb_new')
OLD = os.path.join(TB, '_lptb_old_r13.py')
open(OLD, 'w').write(subprocess.run(['git', 'show', 'fb5b7bd:AFE/layout/tb/lptb.py'], capture_output=True, text=True, check=True, cwd=HERE).stdout)
try:
    old = load(OLD, 'lptb_old')
finally:
    os.remove(OLD)
PEX = os.path.normpath(os.path.join(HERE, '..', 'flow', 'amp_ch.pex.spice'))
n = bad = 0
for nl in ('schematic', PEX):
    for corner in ('typ', 'ff85', 'ss-40'):
        for mk in ('amp', 'ampch'):
            txt = []
            for m in (old, new):
                dut = (m.amp_dut if mk == 'amp' else m.ampch_dut)(nl)
                f = m.amp_bench if mk == 'amp' else m.ampch_bench
                L = f(corner, dut, 'identity', **({} if nl == 'schematic' or mk == 'ampch' else {'nodeset': ''}))
                L = L[0] if isinstance(L, tuple) else L
                txt.append(('\n'.join(L), dut.tag))
            n += 1
            same = txt[0] == txt[1]
            bad += (not same)
            print('%-9s %-5s %-6s bench + tag: %s' % (os.path.basename(nl), corner, mk, 'IDENTICAL' if same else 'DIFFERENT'))
print('IDENTITY %s (%d benches, %d different)' % ('PASS' if not bad else 'FAIL', n, bad))
sys.exit(1 if bad else 0)
