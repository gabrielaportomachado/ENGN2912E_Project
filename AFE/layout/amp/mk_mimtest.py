"""mk_mimtest.py (L2a): DRC experiments on MIM spacing / bottom-plate tab / Via4 rules.  bash AFE/layout/scripts/kl.sh AFE/layout/amp/mk_mimtest.py out=DIR
mimsp_<gap>: two 10 x 10 um MIM pieces, top plates `gap` um apart, unrelated bottom plates; each with a Metal4 tab + Via4 + Metal5 pad on the outer side.
mimst_<d>:   two pieces 6 um apart (top plates), an unrelated Metal4 strap 1 um wide between them at distance d from the left top plate."""
import os
import kpdk as k
import amplib as a

out = globals().get('out', '.')
os.makedirs(out, exist_ok=True)
ly = k.new_layout()
cells = []
for gap in (1.8, 2.4, 2.9, 3.5, 4.5):
    c = ly.create_cell('mimsp_%d' % int(gap * 10))
    m1 = a.mim_cap(c, 0.0, 0.0, 10.0, 10.0, 't1', 'b1')
    m2 = a.mim_cap(c, 10.0 + gap, 0.0, 10.0, 10.0, 't2', 'b2')
    for (bp, sgn) in ((m1['bot'], -1), (m2['bot'], 1)):
        yc = 5.0
        if sgn < 0:
            x1, x2 = bp[0] - 3.0, bp[0]
        else:
            x1, x2 = bp[2], bp[2] + 3.0
        k.rect(c, 'metal4', x1, yc - 0.6, x2, yc + 0.6)
        vx1, vx2 = (x1, x1 + 1.2) if sgn < 0 else (x2 - 1.2, x2)
        k.rect(c, 'metal5', vx1, yc - 0.6, vx2, yc + 0.6)
        a.cuts(c, 'via4', vx1, yc - 0.6, vx2, yc + 0.6, inset=0.2)
    cells.append(c)
for d in (1.5, 1.8, 2.0, 2.3, 2.6, 3.0):
    c = ly.create_cell('mimst_%d' % int(d * 10))
    a.mim_cap(c, 0.0, 0.0, 10.0, 10.0, 't1', 'b1')
    a.mim_cap(c, 16.0, 0.0, 10.0, 10.0, 't2', 'b2')
    k.rect(c, 'metal4', 10.0 + d, -3.0, 11.0 + d, 13.0)
    cells.append(c)
top = ly.create_cell('mimtest')
for i, c in enumerate(cells):
    k.put(top, c, 0.0, i * 30.0)
    k.write(ly, os.path.join(out, c.name + '.gds'), c.name)
print('ok')
