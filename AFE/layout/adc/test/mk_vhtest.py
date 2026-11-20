"""R5 test: vhalf serpentine with given nseg / lseg / pitch (DRC / LVS later).  kl.sh ... nseg=3 lseg=83.33 pitch=2.2"""
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.environ["KL_SCRIPT"]), ".."))
import kpdk as k
import vhalf_lib as VH
out = globals().get('out', 'AFE/layout/adc/test/o')
VH.NSEG = int(globals().get('nseg', '3'))
VH.LSEG = float(globals().get('lseg', '83.33'))
VH.PITCH = float(globals().get('pitch', '2.2'))
VH.DUMMIES = False
os.makedirs(out, exist_ok=True)
ly = k.new_layout()
B = VH.build(ly)
print('vhalf bbox', [round(v, 2) for v in B.bbox], 'size', [round(v, 2) for v in B.size], 'terms', [(n, [round(v, 2) for v in r]) for (n, c, r) in B.terms])
top = ly.create_cell('vhtest')
k.put(top, B.cell, 10, 10)
for (n, c, r) in B.terms:
    k.label(top, 'metal2', n, 10 + (r[0] + r[2]) / 2, 10 + (r[1] + r[3]) / 2)
k.write(ly, os.path.join(out, 'vhtest.gds'), 'vhtest')
