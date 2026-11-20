import os, sys, math
sys.path.insert(0, os.path.join(os.path.dirname(os.environ["KL_SCRIPT"]), ".."))
import kpdk as k
import adclib as a
import rlib as R
import cmp_lib as CL
import cmp_top as CT

out = globals().get('out', 'AFE/layout/adc/test/o')
os.makedirs(out, exist_ok=True)
ly = k.new_layout()
S = CT.comparator(ly)
print('comparator bbox', [round(v, 1) for v in S.bbox], 'size', [round(v, 1) for v in S.size], 'failed', S.failed)
for f in S.nfail:
    print('  FAILED', str(f)[:200])
top = ly.create_cell('cmptest')
k.put(top, S.cell, 0, 0)
for n, (x, y) in S.ext.items():
    k.label(top, 'metal3', n, x, y)
k.write(ly, os.path.join(out, 'cmptest.gds'), 'cmptest')
bb = top.dbbox()
print('wrote', bb.width(), bb.height())
