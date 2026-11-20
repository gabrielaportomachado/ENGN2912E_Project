"""R5 test: the three driver rows of adc_ch with a given ring gap / pitch (DRC only).  bash AFE/layout/scripts/kl.sh AFE/layout/adc/test/mk_drvtest.py gap=1.5 pitch=4 out=AFE/layout/adc/test/o"""
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.environ["KL_SCRIPT"]), ".."))
import kpdk as k
import adclib as a

out = globals().get('out', 'AFE/layout/adc/test/o')
gap = float(globals().get('gap', '2.5'))
PITCH = float(globals().get('pitch', '4'))
os.makedirs(out, exist_ok=True)
ly = k.new_layout()
ORDER = ['d'] + list(range(12))


def bnet(b):
    return 'bd' if b == 'd' else 'b%d' % b


ta, t1, t2 = [], [], []
x = 0
for b in ORDER:
    ta.append(dict(kind='nfet', w=1.0, l=0.28, x=x, y=0, s='vss', d=bnet(b), g=('dac_gdn' if b == 'd' else 'gn%s' % b), ring_s=True))
    x += PITCH
    ta.append(dict(kind='nfet', w=1.0, l=0.28, x=x, y=0, s='vin', d=bnet(b), g='tg_on'))
    x += PITCH
x = 0
for b in ORDER:
    t1.append(dict(kind='pfet', w=2.0, l=0.28, x=x, y=0, s='vdd_dac', d=bnet(b), g=('vdd_dac' if b == 'd' else 'gp%s' % b), ring_s=True, ring_g=(b == 'd')))
    t2.append(dict(kind='pfet', w=2.0, l=0.28, x=x, y=0, s='vin', d=bnet(b), g='samb'))
    x += PITCH
RA = a.group_block(ly, 'row_a', ta, ring_kind='p', ring_net='vss', gap=gap)
RB1 = a.group_block(ly, 'row_b1', t1, ring_kind='n', ring_net='vdd_dac', gap=gap)
RB2 = a.group_block(ly, 'row_b2', t2, ring_kind='n', ring_net='vdd', gap=gap)
print('row_a', [round(v, 2) for v in RA.bbox], RA.size)
print('row_b1', [round(v, 2) for v in RB1.bbox], RB1.size)
print('row_b2', [round(v, 2) for v in RB2.bbox], RB2.size)
top = ly.create_cell('drvtest')
x0 = 0
for blk in (RA, RB1, RB2):
    dx = int(round(x0 - blk.bbox[0]))
    k.put(top, blk.cell, dx, 0)
    x0 += blk.bbox[2] - blk.bbox[0] + 6
k.write(ly, os.path.join(out, 'drvtest.gds'), 'drvtest')
print('wrote', top.dbbox().width(), top.dbbox().height())
