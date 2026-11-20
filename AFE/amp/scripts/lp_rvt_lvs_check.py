#!/usr/bin/env python3
"""LP step 6: does the LVS-reference generator accept the native-Vt-free variant?  AFE/layout/scripts/mk_lvs_netlists.py is NOT edited (another session owns it): it is loaded in memory, its list
SIM_FILES gets the two substitutions  AFE/amp/spice/ota2.spice -> ota2_rvt.spice  and  AFE/amp/spice/afe_chc.spice -> afe_chc_rvt.spice, and it writes to /tmp/lp_rvt/lvs_rvt (nothing under
AFE/layout is touched).  The result is compared with a default run in /tmp/lp_rvt/lvs_orig and with the committed AFE/layout/lvs/.   usage: python3 lp_rvt_lvs_check.py -> AFE/amp/sim/lp_rvt_lvs_check.log"""
import sys, os, io, re, contextlib, importlib.util, difflib
HERE = os.path.dirname(os.path.abspath(__file__)); AMP = os.path.normpath(os.path.join(HERE, '..')); AFE = os.path.normpath(os.path.join(AMP, '..'))
S = os.path.join(AFE, 'layout', 'scripts', 'mk_lvs_netlists.py'); OUT = '/tmp/lp_rvt'
SUB = [('AFE/amp/spice/ota2.spice', 'AFE/amp/spice/ota2_rvt.spice'), ('AFE/amp/spice/afe_chc.spice', 'AFE/amp/spice/afe_chc_rvt.spice')]


def run(out, swap):
    spec = importlib.util.spec_from_file_location('mk', S); m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
    if swap:
        n = 0
        for a, b in SUB:
            n += m.SIM_FILES.count(a); m.SIM_FILES = [b if f == a else f for f in m.SIM_FILES]
        if n != len(SUB): return False, 'SIM_FILES does not list %s' % [a for a, _ in SUB]
    os.makedirs(out, exist_ok=True); sys.argv = ['mk_lvs_netlists.py', '--out', out]; buf = io.StringIO()
    try:
        with contextlib.redirect_stdout(buf): m.main()
        return True, buf.getvalue()
    except SystemExit as e:
        return False, str(e)


body = lambda p: [l for l in open(p).read().split('\n') if not l.startswith('* ')]
L = []
P = lambda s: (print(s), L.append(s))
P(__doc__.split('usage')[0].strip())
ok0, t0 = run(OUT + '/lvs_orig', False); ok1, t1 = run(OUT + '/lvs_rvt', True)
P('default run: %s;  run with SIM_FILES substituted (%s): %s' % ('OK' if ok0 else 'STOP ' + t0[:200], ', '.join('%s -> %s' % (os.path.basename(a), os.path.basename(b)) for a, b in SUB), 'OK' if ok1 else 'STOP ' + t1[:300]))
res = ok0 and ok1
if res:
    for f in ('afe_chc.spice', 'adc_ch.spice', 'bias_genc.spice', 'dbs_afe_top.spice'):
        a, b = body(OUT + '/lvs_orig/' + f), body(OUT + '/lvs_rvt/' + f)
        d = [l for l in difflib.unified_diff(a, b, lineterm='', n=0) if l[:1] in '+-' and l[:3] not in ('+++', '---')]
        P('%-18s default vs variant: %d changed lines' % (f, len(d) // 2))
        for l in d: P('     ' + l[:200])
        c = os.path.join(AFE, 'layout', 'lvs', f)
        if os.path.exists(c):
            same = body(c) == a
            P('%-18s default run in memory == committed AFE/layout/lvs/%s: %s%s' % ('', f, same, '' if same else '  (the committed file was written with other options or by a newer script: compare the variant against a fresh default run, as above)'))
    exp = (len([1 for f in ('afe_chc.spice', 'dbs_afe_top.spice') for l in difflib.unified_diff(body(OUT + '/lvs_orig/' + f), body(OUT + '/lvs_rvt/' + f), lineterm='', n=0) if l.startswith('+X')]) == 2
           and body(OUT + '/lvs_orig/adc_ch.spice') == body(OUT + '/lvs_rvt/adc_ch.spice') and body(OUT + '/lvs_orig/bias_genc.spice') == body(OUT + '/lvs_rvt/bias_genc.spice'))
    res = exp
    P('RESULT: %s (expected: exactly ONE device line changes, the follower Xs2_xota2_xmf, in afe_chc.spice and in the copy of that cell in dbs_afe_top.spice; adc_ch and bias_genc unchanged)' % ('PASS' if exp else 'FAIL'))
open(os.path.join(AMP, 'sim', 'lp_rvt_lvs_check.log'), 'w').write('\n'.join(L) + '\n')
sys.exit(0 if res else 1)
