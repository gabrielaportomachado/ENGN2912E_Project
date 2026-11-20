import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.environ["KL_SCRIPT"]), ".."))
import kpdk as k
import adclib as a

ly = k.new_layout()
PITCH = 4
tiles = []
x = 0
for b in list(range(11, -1, -1)) + ['d']:
    tiles.append(dict(kind='nfet', w=1.0, l=0.28, x=x, y=0, s='vss', d='b%s' % b, g='dac_gn%s' % b))
    x += PITCH
    tiles.append(dict(kind='nfet', w=1.0, l=0.28, x=x, y=0, s='vin', d='b%s' % b, g='tg_on'))
    x += PITCH
tA = a.group_block(ly, 'rowA', tiles, ring_kind='p', ring_net='vss')
print('rowA size', tA.size, 'bbox', [round(v, 2) for v in tA.bbox], 'nterm', len(tA.terms))
tiles = []
x = 0
for b in list(range(11, -1, -1)) + ['d']:
    tiles.append(dict(kind='pfet', w=2.0, l=0.28, x=x, y=0, s='vdd_dac', d='b%s' % b, g='dac_gp%s' % b))
    x += PITCH
tB = a.group_block(ly, 'rowB1', tiles, ring_kind='n', ring_net='vdd_dac')
print('rowB1 size', tB.size, 'bbox', [round(v, 2) for v in tB.bbox], 'nterm', len(tB.terms))
