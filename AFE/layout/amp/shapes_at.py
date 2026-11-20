"""shapes_at.py (L2a debug): list the shapes of a GDS inside a window.  bash AFE/layout/scripts/kl.sh AFE/layout/amp/shapes_at.py gds=F cell=amp_ch box=x1,y1,x2,y2 [layers=metal4,metal5]"""
import pya
import kpdk as k

g = globals()
ly = pya.Layout()
ly.read(g['gds'])
cell = ly.cell(g.get('cell', 'amp_ch'))
x1, y1, x2, y2 = [float(v) for v in g['box'].split(',')]
win = pya.Box(int(x1 / ly.dbu), int(y1 / ly.dbu), int(x2 / ly.dbu), int(y2 / ly.dbu))
names = g.get('layers', 'metal1,metal2,metal3,metal4,metal5,via4,fusetop,cap_mk').split(',')
for nm in names:
    li = ly.find_layer(*k.LAYERS[nm])
    if li is None:
        continue
    r = pya.Region(cell.begin_shapes_rec(li)) & pya.Region(win)
    r = pya.Region(cell.begin_shapes_rec(li)).merged().interacting(pya.Region(win))
    for p in r.each():
        b = p.bbox()
        print(nm, 'box' if p.is_box() else 'poly%d' % p.num_points(), [round(v * ly.dbu, 3) for v in (b.left, b.bottom, b.right, b.top)])
