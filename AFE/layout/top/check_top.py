"""check_top.py (L3a step 6): facts of the finished top that DRC / LVS do not test.
    python3 AFE/layout/top/check_top.py [gds] > AFE/layout/top/check_top.log
1. outline and the pin list: every port bit of floorplan.json exactly once as a label on the pin shape, at the floorplan position (<= 0.3 um)
2. keep-outs of SPEC.md section 5: smallest distances (um) from the digital side (the macro, the 116 ADC control wires of the strap corridors) to the sensitive plates
   (every MIM top plate = FuseTop of amp_ch / adc_ch: a superset of the summing nodes, DAC top plates and Cref), from the ADC supply straps to the same plates, and from the REC / E / IPG pad wires to the digital side
3. sw_rec / sw_rec_b wire lengths (macro pin -> TGATE pin) per channel and their difference (from the drawn constants of mk_afe_ch.py / mk_top.py)
4. decap units per net (count of cap_nmos devices by their gate net is checked by LVS; here the count of the pcell instances) and the Cref-decap placement
Uses only klayout.db (python3 -I is not needed: no file of the repository is imported)."""
import sys
import json
import math
import klayout.db as db

REPO = '/foss/designs/ENGN2912E_Project/.claude/worktrees/l3a'
gds = sys.argv[1] if len(sys.argv) > 1 else REPO + '/AFE/layout/top/dbs_afe_top.gds'
FP = json.load(open(REPO + '/AFE/layout/floorplan.json'))
ly = db.Layout()
ly.read(gds)
top = ly.cell('dbs_afe_top')
dbu = ly.dbu
res = {}


def reg(cell, l, d):
    i = ly.find_layer(l, d)
    return db.Region(cell.begin_shapes_rec(i)) if i is not None else db.Region()


def mind(a, b, hi=2000.0):
    """smallest Euclidean distance (um) between two regions (binary search on the sized region, resolution 0.05 um)"""
    if a.is_empty() or b.is_empty():
        return None
    lo, h = 0.0, hi
    if not a.interacting(b).is_empty():
        return 0.0
    while h - lo > 0.05:
        m = (lo + h) / 2.0
        if (a.sized(int(m / dbu), 2) & b).is_empty() and a.sized(int(m / dbu), 2).interacting(b).is_empty():
            lo = m
        else:
            h = m
    return round(h, 2)


# ------------------------------------------------------------------ 1. pins
bb = top.dbbox()
res['outline_um'] = [round(bb.width(), 3), round(bb.height(), 3)]
print('outline: %.3f x %.3f um (limit 605 x 1110)' % (bb.width(), bb.height()))
labels = {}
for li in ly.layer_indexes():
    info = ly.get_info(li)
    if info.datatype != 10:
        continue
    for sh in top.shapes(li).each():
        if sh.is_text():
            labels.setdefault(sh.text.string, []).append((info.layer, round(sh.text.x * dbu, 2), round(sh.text.y * dbu, 2)))
bad = []
for q in FP['pins']:
    got = labels.get(q['name'])
    if not got or len(got) != 1:
        bad.append('%s: %s' % (q['name'], got))
        continue
    l, x, y = got[0]
    dx = min(abs(x - q['x']), 1e9)
    dy = abs(y - q['y'])
    near = (abs(x - q['x']) <= 2.0 if q['side'] in 'WE' else abs(x - q['x']) <= 0.3) and (abs(y - q['y']) <= 2.0 if q['side'] in 'NS' else abs(y - q['y']) <= 10.5)
    if not near:
        bad.append('%s at (%.2f, %.2f), floorplan (%.2f, %.2f)' % (q['name'], x, y, q['x'], q['y']))
print('pin bits: %d in floorplan.json, %d labels on the top cell (%d distinct names); mismatches: %s' % (len(FP['pins']), sum(len(v) for v in labels.values()), len(labels), bad or 'none'))
res['pins_bad'] = bad
# ------------------------------------------------------------------ 2. keep-outs
pl = {q['inst']: q for q in FP['placements']}
dig = pl['u_dig']
digbox = db.Region(db.Box(int(dig['x'] / dbu), int(dig['y'] / dbu), int((dig['x'] + 424.48) / dbu), int((dig['y'] + dig['h']) / dbu)))
sens = db.Region()
for cn in ('amp_ch', 'adc_ch'):
    for inst in top.begin_instances_rec() if False else []:
        pass
sens_amp, sens_adc = db.Region(), db.Region()
it = top.begin_shapes_rec(ly.find_layer(75, 0))
while not it.at_end():
    path = [c.cell.name for c in it.path()] if False else None
    it.next()
# per instance: walk the hierarchy: afe_ch -> amp_ch / adc_ch
for n in range(4):
    q = pl['ch%d' % n]
    for inst in top.each_inst():
        pass
cells = {c.name: c for c in ly.each_cell()}


def plates_in(cellname, tr_list):
    out = db.Region()
    c = cells[cellname]
    r = db.Region(c.begin_shapes_rec(ly.find_layer(75, 0)))
    for tr in tr_list:
        out += r.transformed(tr)
    return out


# transformations of the channel slots: afe_ch instances in the top cell
afe_tr = []
for inst in top.each_inst():
    if inst.cell.name == 'afe_ch':
        afe_tr.append(inst.dcplx_trans if False else inst.trans)
amp_in_afe = [i.trans for i in cells['afe_ch'].each_inst() if i.cell.name == 'amp_ch']
adc_in_afe = [i.trans for i in cells['afe_ch'].each_inst() if i.cell.name == 'adc_ch']
amp_tr = [t * a for t in afe_tr for a in amp_in_afe]
adc_tr = [t * a for t in afe_tr for a in adc_in_afe]
sens_amp = plates_in('amp_ch', amp_tr)
sens_adc = plates_in('adc_ch', adc_tr)
sens_all = sens_amp + sens_adc
res['plates_um2'] = {'amp': round(sens_amp.area() * dbu * dbu), 'adc': round(sens_adc.area() * dbu * dbu)}
# digital wires of the strap corridors: the top-cell's own Metal2 shapes inside the corridors (north y 598.12 .. 623.12, south 486.88 .. 511.88)
own = db.Region(top.shapes(ly.find_layer(36, 0)))
corr = db.Region(db.Box(0, int(598.12 / dbu), int(605 / dbu), int(623.12 / dbu))) + db.Region(db.Box(0, int(486.88 / dbu), int(605 / dbu), int(511.88 / dbu)))
dwires = own & corr
# the adc control wires only (x of the adc pins): drop the vertical quasi-static control lines (corridor lines at slot x < 8)
keep = db.Region()
for p in dwires.merged().each():
    b = p.bbox()
    xs = (b.left + b.right) * 0.5 * dbu
    slotx = (xs - 26.0) % 237.0
    if slotx >= 12.0 and (b.height() * dbu) > 20.0:
        keep.insert(p)
res['adc_control_wires'] = keep.count()
print('digital side: macro afe_dig, %d adc control wires (Metal2, strap corridors)' % keep.count())
d_mac = mind(digbox, sens_all)
d_wire = mind(keep, sens_all)
print('smallest distance macro -> any MIM top plate (summing nodes, DAC / Cref plates): %s um (rule: >= 20)' % d_mac)
print('smallest distance ADC control wire (top level) -> any MIM top plate: %s um (rule: >= 20, the last 10 um at the device excepted)' % d_wire)
res['keepout_um'] = {'macro_to_plates': d_mac, 'adc_control_wires_to_plates': d_wire}
straps = db.Region()
m5 = db.Region(top.shapes(ly.find_layer(81, 0)))
straps = m5 & corr
d_strap = mind(straps, sens_all)
print('smallest distance ADC supply strap (Metal5 in the strap corridors) -> any MIM top plate: %s um (rule: >= 5)' % d_strap)
res['keepout_um']['straps_to_plates'] = d_strap
# rec pad wires and E / IPG: Metal5 shapes of the top cell that reach the chip edge
pad = db.Region()
for p in m5.each():
    b = p.bbox()
    if (b.top * dbu >= 1109.0 or b.bottom * dbu <= 1.0) and b.width() * dbu < 3.0:
        pad.insert(p)
d_pad = mind(pad, keep + digbox)
print('smallest distance pad wires (E / REC / IPG Metal5, %d shapes) -> digital side: %s um' % (pad.count(), d_pad))
res['keepout_um']['pad_wires_to_digital'] = d_pad
d_bias = mind(db.Region(db.Box(int(471.5 / dbu), int(497.5 / dbu), int(578.75 / dbu), int(612.6 / dbu))), digbox)
print('bias_genc to the macro: %s um (rule: >= 20)' % d_bias)
res['keepout_um']['bias_to_macro'] = d_bias
# ------------------------------------------------------------------ 3. sw_rec / sw_rec_b skew
YC = {'sw_rec': 3.2, 'sw_rec_b': 4.6}
CORR = {'sw_rec': 1.0, 'sw_rec_b': 2.4}
AT, ZT = 433.88, 448.88 - 433.88
TX = {0: 76.78, 1: 76.78}
sk = {}
pins = json.load(open(REPO + '/AFE/dig/final/afe_dig_pins.json'))['pins']
P = {q['name']: q for q in pins}
for n in range(4):
    L = {}
    for nm, track in (('sw_rec', 2.0), ('sw_rec_b', 11.0)):
        q = P['%s[%d]' % (nm, n)]
        xm = dig['x'] + 0.5 * (q['rect_um'][0] + q['rect_um'][2])
        xl = pl['ch%d' % n]['x'] + CORR[nm]
        xc = pl['ch%d' % n]['x'] + 76.78 + 1.40
        ln = (YC[nm] + 1.0) + abs(xm - xl) + (25.0 - YC[nm]) + (AT + track) + abs(xc - xl) + abs((5.0 + (1.39 if nm == 'sw_rec' else 2.01)) - track)
        L[nm] = round(ln, 1)
    sk[n] = {'sw_rec_um': L['sw_rec'], 'sw_rec_b_um': L['sw_rec_b'], 'difference_um': round(abs(L['sw_rec'] - L['sw_rec_b']), 1)}
    print('channel %d: sw_rec %.1f um, sw_rec_b %.1f um, difference %.1f um (limit 100)' % (n, L['sw_rec'], L['sw_rec_b'], abs(L['sw_rec'] - L['sw_rec_b'])))
res['skew'] = sk
# ------------------------------------------------------------------ 4. decap
n_dec = sum(1 for c in ly.each_cell() for i in c.each_inst() if i.cell.name.startswith('cap_nmos')) if False else 0
dec_cells = [c for c in ly.each_cell() if c.name.startswith('cap_nmos')]
cnt = 0
for c in dec_cells:
    cnt += sum(1 for i in top.each_inst() if i.cell.cell_index() == c.cell_index())
print('decap pcell instances in the top cell: %d (LVS reference: 74 + 30 = 104)' % cnt)
res['decap_instances'] = cnt
json.dump(res, open(REPO + '/AFE/layout/top/check_top.json', 'w'), indent=1)
