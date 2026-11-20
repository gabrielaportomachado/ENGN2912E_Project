"""R5 debug: metal-only connectivity of a GDS with KLayout (Metal1..5 + vias + contact on comp is ignored); prints the labels that share one net.
run: klayout -b -r AFE/layout/adc/test/probe_short.py -rd gds=... -rd top=adc_ch"""
import pya

gds = globals().get('gds')
top = globals().get('top', 'adc_ch')
ly = pya.Layout()
ly.read(gds)
cell = ly.cell(top)
L = {}
tmp = ly.layer(900, 0)
v4 = pya.Region(cell.begin_shapes_rec(ly.layer(41, 0))) - pya.Region(cell.begin_shapes_rec(ly.layer(117, 5)))
cell.shapes(tmp).insert(v4)
l2n = pya.LayoutToNetlist(pya.RecursiveShapeIterator(ly, cell, []))
for name, (l, d) in dict(m1=(34, 0), v1=(35, 0), m2=(36, 0), v2=(38, 0), m3=(42, 0), v3=(40, 0), m4=(46, 0), m5=(81, 0)).items():
    L[name] = l2n.make_layer(ly.layer(l, d), name)
# Via4 inside CAP_MK joins FuseTop to Metal5, NOT Metal4: only the Via4 outside CAP_MK connect Metal4 and Metal5
L['v4'] = l2n.make_layer(tmp, 'v4')
for a, v, b in (('m1', 'v1', 'm2'), ('m2', 'v2', 'm3'), ('m3', 'v3', 'm4'), ('m4', 'v4', 'm5')):
    l2n.connect(L[a])
    l2n.connect(L[v])
    l2n.connect(L[b])
    l2n.connect(L[a], L[v])
    l2n.connect(L[v], L[b])
labs = {34: 'm1', 36: 'm2', 42: 'm3', 46: 'm4', 81: 'm5'}
l2n.extract_netlist()
nl = l2n.netlist()
c = nl.circuit_by_name(top)
# labels: take texts on the label datatype of each metal
texts = []
for (l, d) in ((34, 10), (36, 10), (42, 10), (46, 10), (81, 10)):
    li = ly.find_layer(l, d)
    if li is None:
        continue
    for sh in cell.begin_shapes_rec(li) if False else []:
        pass
it = cell.begin_shapes_rec(ly.layer(34, 10))
res = {}
for (l, d, mname) in ((34, 10, 'm1'), (36, 10, 'm2'), (42, 10, 'm3'), (46, 10, 'm4'), (81, 10, 'm5')):
    li = ly.layer(l, d)
    it = cell.begin_shapes_rec(li)
    while not it.at_end():
        sh = it.shape()
        if sh.is_text():
            t = sh.text.transformed(it.trans())
            texts.append((t.string, mname, t.x * ly.dbu, t.y * ly.dbu))
        it.next()
for (s, m, x, y) in texts:
    pt = pya.Point(int(round(x / ly.dbu)), int(round(y / ly.dbu)))
    n = l2n.probe_net(L[m], pt)
    if n is None:
        print('label', s, 'no net at', x, y)
        continue
    res.setdefault(n.cluster_id, []).append(s)
for cid, names in res.items():
    if len(set(names)) > 1:
        print('SHORT: labels on one net:', sorted(set(names)))
print('labels', len(texts), 'nets with labels', len(res))

# dump the polygons of the shorted net on Metal4 and Metal3 inside a window
win = pya.Box(int(100 / ly.dbu), 0, int(230 / ly.dbu), int(12 / ly.dbu))
for (s, m, x, y) in texts:
    if s == 'vdd_dac':
        n = l2n.probe_net(L[m], pya.Point(int(round(x / ly.dbu)), int(round(y / ly.dbu))))
        for nm in ('m4', 'm3', 'm5', 'm2'):
            r = l2n.shapes_of_net(n, L[nm], True)
            rr = r & pya.Region(win)
            for p in rr.each():
                b = p.bbox()
                print(nm, 'piece', round(b.left * ly.dbu, 2), round(b.bottom * ly.dbu, 2), round(b.right * ly.dbu, 2), round(b.top * ly.dbu, 2))
        break
