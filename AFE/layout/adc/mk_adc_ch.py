"""mk_adc_ch.py (L1a): the ADC analog cell adc_ch (LVS reference: subckt adc_ch of AFE/layout/lvs/adc_ch.spice = dac_sw + cmp_p + vhalf + vrefs + INV).
Run:  bash AFE/layout/scripts/kl.sh AFE/layout/adc/mk_adc_ch.py out=AFE/layout/adc/adc_ch.gds [plan=1] [stage=N]
Everything is generated; nothing is drawn by hand.  Geometry rules of the DAC array are in dac_lib.py, the flow notes in AFE/layout/FLOW.md and AFE/layout/adc/FLOW_ADC.md.
"""
import os
import sys
import math
import json
sys.path.insert(0, os.path.dirname(os.environ['KL_SCRIPT']))
import kpdk as k
import adclib as a
import router as RT
import dac_lib as DL
import rlib as R
import cmp_top as CT
import vhalf_lib as VH

outgds = globals().get('out', 'AFE/layout/adc/adc_ch.gds')
outdir = os.path.dirname(outgds) or '.'
plan = int(globals().get('plan', '0'))
stage = int(globals().get('stage', '99'))
os.makedirs(outdir, exist_ok=True)

ly = k.new_layout()
TOP = ly.create_cell('adc_ch')
PLACED = []                                  # (name, block, dx, dy, mirror)
FIXED = []                                   # extra explicit router obstacles / terminals are added to the router below
BITS = list(range(12))


def bnet(b):
    return 'bd' if b == 'd' else 'b%d' % b


def gp(b):
    return 'dac_gp[%d]' % b


def gn(b):
    return 'dac_gn[%d]' % b


def put(name, blk, x, y):
    """place the block so that the lower left corner of its bbox is at (x, y) or beyond (integer offsets)"""
    dx = math.ceil(x - blk.bbox[0] - 1e-9)
    dy = math.ceil(y - blk.bbox[1] - 1e-9)
    k.put(TOP, blk.cell, dx, dy)
    PLACED.append((name, blk, dx, dy))
    return dx + blk.bbox[2], dy + blk.bbox[3]


# =====================================================================================================================================================================
# blocks: driver rows
# =====================================================================================================================================================================
PITCH = 4
ORDER = ['d'] + list(range(12))                                       # west -> east: bd, b0 .. b11  (LSB drivers west, MSB drivers east, like the array)


def row_a():
    t = []
    x = 0
    for b in ORDER:
        t.append(dict(kind='nfet', w=1.0, l=0.28, x=x, y=0, s='vss', d=bnet(b), g=('dac_gdn' if b == 'd' else gn(b)), ring_s=True))
        x += PITCH
        t.append(dict(kind='nfet', w=1.0, l=0.28, x=x, y=0, s='vin', d=bnet(b), g='tg_on'))
        x += PITCH
    return a.group_block(ly, 'row_a', t, ring_kind='p', ring_net='vss')


def row_b1():
    t = []
    x = 0
    for b in ORDER:
        t.append(dict(kind='pfet', w=2.0, l=0.28, x=x, y=0, s='vdd_dac', d=bnet(b), g=('vdd_dac' if b == 'd' else gp(b)), ring_s=True, ring_g=(b == 'd')))
        x += PITCH
    return a.group_block(ly, 'row_b1', t, ring_kind='n', ring_net='vdd_dac')


def row_b2():
    t = []
    x = 0
    for b in ORDER:
        t.append(dict(kind='pfet', w=2.0, l=0.28, x=x, y=0, s='vin', d=bnet(b), g='samb'))
        x += PITCH
    return a.group_block(ly, 'row_b2', t, ring_kind='n', ring_net='vdd')


RA, RB1, RB2 = row_a(), row_b1(), row_b2()
if plan:
    for n, b in (('row_a', RA), ('row_b1', RB1), ('row_b2', RB2)):
        print(n, [round(v, 1) for v in b.bbox], 'terms', len(b.terms))

# =====================================================================================================================================================================
# placement
# =====================================================================================================================================================================
X_A = 12.0
Y_A = 4.0
xe, ye = put('row_a', RA, X_A, Y_A)
xe2, ye2 = put('row_b1', RB1, X_A, ye + 4.0)
xe3, ye3 = put('row_b2', RB2, xe2 + 3.0, ye + 4.0)
Y_DRV_TOP = max(ye2, ye3)
print('driver zone top y = %.1f, row_a x end %.1f, row_b2 x end %.1f' % (Y_DRV_TOP, xe, xe3))

# DAC array: lower left of the S dummy plate row at (X0L, YS); the channel centre must be an integer y
X0L = 20.0
YS_MIN = Y_DRV_TOP + 20.0 - DL.U - DL.GAP_D + 0.6 + 1.0
YS = math.ceil(YS_MIN - 0.8) + 0.8                                    # y0 = n + 0.8  ->  channel centre y = y0 + 36.2 integer
cellD = ly.create_cell('dac')
D = DL.build(cellD, X0L, YS)
k.put(TOP, cellD, 0, 0)
print('DAC: x %.1f .. %.1f  y %.1f .. %.1f  channel centre %.1f' % (D.xl0, D.xm1, D.ys[0], D.top, D.ych))
H_DAC = D.top + 0.6
if plan:
    sys.exit(0)

# =====================================================================================================================================================================
# the rest of the cell: comparator, Cref (+ switch, inverter), vhalf (+ capacitor), reset switches
# =====================================================================================================================================================================
EXPLICIT = []                                 # (layer index 0..2, rect, net, extra): shapes drawn by hand below (stacks of t / vref / m): obstacles for the router
# ---- comparator (two mirror-image halves + centre column)
CMP = CT.comparator(ly)
XC, YC = 205, 6                               # axis x of the comparator, y offset
k.put(TOP, CMP.cell, XC, YC)
PLACED.append(('cmp', CMP, XC, YC))
vref_pad = (CMP.ext['vref'][0] + XC, CMP.ext['vref'][1] + YC)
t_pad = (CMP.ext['t'][0] + XC, CMP.ext['t'][1] + YC)
print('comparator: %.1f x %.1f  x %.1f .. %.1f  y %.1f .. %.1f  vref pad %s  t pad %s  failed %s' % (CMP.size[0], CMP.size[1], CMP.bbox[0] + XC, CMP.bbox[2] + XC, CMP.bbox[1] + YC, CMP.bbox[3] + YC, vref_pad, t_pad, CMP.failed))


def stack_up(cell, x, y, lo, hi, w5=0.8):
    """via stack at (x, y) from metal `lo` to metal `hi` (1..5): 0.5 um pads (Metal5: w5), one cut per via; returns the list of (router layer idx, rect) for Metal2..4"""
    out = []
    for m in range(lo, hi + 1):
        w = w5 if m == 5 else 0.5
        k.rect(cell, k.METAL[m], x - w / 2, y - w / 2, x + w / 2, y + w / 2)
        if 2 <= m <= 4:
            out.append((m - 2, (x - w / 2, y - w / 2, x + w / 2, y + w / 2)))
        if m < hi:
            c = {1: 'via1', 2: 'via2', 3: 'via3', 4: 'via4'}[m]
            k.rect(cell, c, x - 0.13, y - 0.13, x + 0.13, y + 0.13)
    return out


# ---- Cref switch (vrefs: nfet 1/0.28 gate tg_on, pfet 2/0.28 gate samb, in = vcmd, out = vref) and the inverter samb = not tg_on (5 V devices of inv_1)
SWN = a.group_block(ly, 'sw_n', [dict(kind='nfet', w=1.0, l=0.28, x=0, y=0, s='vcmd', d='vref', g='tg_on')], ring_kind='p', ring_net='vss')
SWP = a.group_block(ly, 'sw_p', [dict(kind='pfet', w=2.0, l=0.28, x=0, y=0, s='vcmd', d='vref', g='samb')], ring_kind='n', ring_net='vdd')
IVN = a.group_block(ly, 'iv_n', [dict(kind='nfet5', w=0.82, l=0.6, x=0, y=0, s='vss', d='samb', g='tg_on', ring_s=True)], ring_kind='p', ring_net='vss')
IVP = a.group_block(ly, 'iv_p', [dict(kind='pfet5', w=1.22, l=0.5, x=0, y=0, s='vdd', d='samb', g='tg_on', ring_s=True)], ring_kind='n', ring_net='vdd')
ysw = math.ceil(YC + CMP.bbox[3] + 2)
xe = XC + CMP.bbox[2] - 2
for nm, blk in (('sw_n', SWN), ('sw_p', SWP), ('iv_n', IVN), ('iv_p', IVP)):
    xw = blk.bbox[2] - blk.bbox[0]
    put(nm, blk, xe - xw, ysw)
    xe = xe - xw - 3
print('switch / inverter blocks at y %d' % ysw)

HSW = max(blk.bbox[3] - blk.bbox[1] for blk in (SWN, SWP, IVN, IVP))
# ---- Cref: ONE 59.07 um MIM plate, top plate = vref, bottom plate = vss; nothing below Metal4 in its footprint
CREF_W = 59.07
cref = R.mim_unit_block(ly, 'cref', CREF_W, 'vref', 'vss', yb=1, yt=4)
cref.terms = [t for t in cref.terms if t[0] != 'vref']
cx0 = math.ceil(vref_pad[0] + 3.0 - CREF_W)
cy0 = int(math.ceil(ysw + HSW + 3))
dxr, dyr = cx0, cy0
k.put(TOP, cref.cell, dxr, dyr)
PLACED.append(('cref', cref, dxr, dyr))
# vref: Metal5 strap from the plate to the comparator pad (Metal3 pad -> Via3 -> Metal4 -> Via4 -> Metal5)
vx, vy = vref_pad
EXPLICIT += [(l, r, 'vref', 0.0) for (l, r) in stack_up(TOP, vx, vy, 3, 5, w5=1.0)]
k.rect(TOP, 'metal5', vx - 0.5, vy - 0.5, vx + 0.5, dyr + 0.01)
print('Cref: x %.1f .. %.1f  y %.1f .. %.1f' % (dxr, dxr + CREF_W, dyr, dyr + CREF_W))

# ---- vhalf: serpentine + 22.18 um capacitor (vcmd to vss)
VHR = VH.build(ly)
vx0, vy0 = 140, math.ceil(max(D.ys[1], YC + CMP.bbox[3] + 8))
put('vhalf', VHR, 171, vy0)
VHC = R.mim_unit_block(ly, 'vh_cap', 22.18, 'vcmd', 'vss', yb=1, yt=4)
put('vh_cap', VHC, 142, vy0 + 1)

# ---- reset switches (t / m to vcmd, gate rst_sw) next to the lower ends of the trunks
XR0 = a.group_block(ly, 'xr0', [dict(kind='nfet', w=0.5, l=0.28, x=0, y=0, s='vcmd', d='t', g='rst_sw')], ring_kind='p', ring_net='vss')
XR1 = a.group_block(ly, 'xr1', [dict(kind='nfet', w=0.5, l=0.28, x=0, y=0, s='vcmd', d='m', g='rst_sw')], ring_kind='p', ring_net='vss')
y_tstrap = math.ceil(D.ys[0]) - 8
put('xr0', XR0, D.xp_t + 3, y_tstrap - 4)
put('xr1', XR1, D.xl0 - 12, y_tstrap - 4)

# =====================================================================================================================================================================
# router: obstacles, terminals, pins
# =====================================================================================================================================================================
W_CELL = max(dx + blk.bbox[2] for (_, blk, dx, dy) in PLACED)
H_CELL = max(H_DAC, max(dy + blk.bbox[3] for (_, blk, dx, dy) in PLACED))
W = int(math.ceil(W_CELL)) + 4
H = int(math.ceil(H_CELL)) + 3
print('placed extent: W = %.1f  H = %.1f' % (W_CELL, H_CELL))
rt = RT.Router(1.0, 1.0, float(W) - 1.0, float(H) - 1.0)
for (name, blk, dx, dy) in PLACED:
    for (l, r, n, ex) in blk.fixed:
        rt.obstacle(l, (r[0] + dx, r[1] + dy, r[2] + dx, r[3] + dy), n, extra=ex)
    for (n, c, r) in blk.terms:
        rt.terminal(n, c, (r[0] + dx, r[1] + dy, r[2] + dx, r[3] + dy))
    if hasattr(blk, 'mim'):
        pl = blk.mim['plate']
        pl = (pl[0] + dx, pl[1] + dy, pl[2] + dx, pl[3] + dy)
        rt.block_all(pl, layers=(0, 1))
        rt.obstacle(2, pl, None, extra=0.9)
    for pl in getattr(blk, 'plates', []):
        pl = (pl[0] + dx, pl[1] + dy, pl[2] + dx, pl[3] + dy)
        rt.block_all(pl, layers=(0, 1))
        rt.obstacle(2, pl, None, extra=0.9)
# DAC: nothing of Metal2 / Metal3 under the plate area except the channel strip; Metal4 keeps 1.2 um (MIMTM.1) from every plate polygon
ych = D.ych
body_x1, body_x2 = D.xl0 - 0.6, D.xm1 + 0.6
rt.block_all((body_x1, D.ys[0] - 0.6, body_x2, ych - 3.0), layers=(0, 1))
rt.block_all((body_x1, ych + 3.0, body_x2, D.top + 0.6), layers=(0, 1))
for half, rows in (('L', DL.LSB_ROWS), ('M', DL.MSB_ROWS)):
    for r in range(8):
        f, l = D.row_ext[(half, r)]
        y = D.ys[r + 1]
        rt.obstacle(2, (f - 0.6, y - 0.6, l + 0.6, y + DL.U + 0.6), None, extra=1.2)
for (r, y, xa, xz) in D.dummy:
    rt.obstacle(2, (xa - 0.6, y - 0.6, xz + 0.6, y + DL.U + 0.6), None, extra=1.2)
for (n, c, r) in D.terms:
    rt.terminal(n, c, r)
    rt.obstacle(2, r, n)
for (n, r) in D.tabs:
    rt.obstacle(2, r, n, extra=0.5)
# trunks: nothing of Metal3 / Metal4 under them (they carry t / m)
for (xT, ylo, yhi) in (D.tr_m, D.tr_t):
    rt.block_all((xT - 1.5, ylo - 1.0, xT + 1.5, yhi + 1.0), layers=(1, 2))

# ---- the t / m / vref connections drawn explicitly (Metal5): trunks -> reset switch drains and -> the comparator pads
def placed(name):
    for (n, blk, dx, dy) in PLACED:
        if n == name:
            return blk, dx, dy


def term_xy(name, net, code='metal1'):
    blk, dx, dy = placed(name)
    for (n, c, r) in blk.terms:
        if n == net and c == code:
            return ((r[0] + r[2]) / 2.0 + dx, (r[1] + r[3]) / 2.0 + dy)


for (nm, net, trunk, rt_x) in (('xr0', 't', D.tr_t, D.xT_t), ('xr1', 'm', D.tr_m, D.xT_m)):
    xd, yd = term_xy(nm, net)
    EXPLICIT += [(l, r, net, 0.0) for (l, r) in stack_up(TOP, xd, yd, 1, 5, w5=0.8)]
    k.rect(TOP, 'metal5', min(xd, rt_x) - 0.5, yd - 0.5, max(xd, rt_x) + 0.5, yd + 0.5)       # strap to the trunk column
    k.rect(TOP, 'metal5', rt_x - 0.5, yd - 0.5, rt_x + 0.5, trunk[1] + 0.01)                  # the trunk is extended down to the switch
tx, ty = t_pad
EXPLICIT += [(l, r, 't', 0.0) for (l, r) in stack_up(TOP, tx, ty, 3, 5, w5=1.0)]
k.rect(TOP, 'metal5', D.xT_t - 0.5, ty - 0.5, tx + 0.5, ty + 0.5)
k.rect(TOP, 'metal5', D.xT_t - 0.5, min(ty, term_xy('xr0', 't')[1]) - 0.5, D.xT_t + 0.5, max(ty, term_xy('xr0', 't')[1]) + 0.5)
for (l, r, n, ex) in EXPLICIT:
    rt.obstacle(l, r, n, extra=ex)
for net in ('t', 'm'):
    rt.terms.pop(net, None)                                                  # drawn explicitly: no router terminal
bridge_pads = [i for i, (n, c, r) in enumerate(D.terms) if n == 'm']

# ---- pins
PINS = []
PIN_X = {'rst_sw': 12, 'tg_on': 15, 'dac_gdn': 18, 'cmp_clk': 21, 'cmp_q': 24}
for i, b in enumerate(range(11, -1, -1)):
    PIN_X[gp(b)] = 27 + 6 * i
    PIN_X[gn(b)] = 30 + 6 * i
for n, x in PIN_X.items():
    PINS.append((n, 'metal2', x, 0.75))
    rt.terminal(n, 'metal2', (x - 0.25, 0.0, x + 0.25, 1.25))
    rt.obstacle(0, (x - 0.25, 0.0, x + 0.25, 1.25), n)
PINS.append(('vin', 'metal3', 4.0, H - 2.0))
rt.terminal('vin', 'metal3', a.pad_rect(4.0, H - 2.0, 0.5))
PIN_RECT = {'vdd_cmp': (110.0, 0.0, 130.0, 4.0), 'vdd_dac': (140.0, 0.0, 160.0, 4.0), 'vss': (170.0, 0.0, 210.0, 4.0),
            'vdd': (math.floor(W_CELL) - 6.0, 48.0, math.floor(W_CELL) - 0.0, 54.0)}
for n, r in PIN_RECT.items():
    PINS.append((n, 'metal4', (r[0] + r[2]) / 2.0, (r[1] + r[3]) / 2.0))
    rt.terminal(n, 'metal4', r)
    rt.obstacle(2, r, n)
rt.reserve()
for (n, c, r) in D.terms:                                              # the stack above a DAC pad (Via3 -> Metal3 -> Via2 -> Metal2) is reserved for its net: long Metal3 tracks of other nets must not wall the pad in
    nid = rt.nid(n)
    i = int(round(((r[0] + r[2]) / 2.0 - rt.x0) / rt.p))
    j = int(round(((r[1] + r[3]) / 2.0 - rt.y0) / rt.p))
    for l in (1, 0):
        if rt.occ[l, i, j] == 0:
            rt.occ[l, i, j] = nid
    for dj in (-1, 1):
        if rt.occ[0, i, j + dj] == 0 and rt.blk[0, i, j + dj] == 0:
            rt.occ[0, i, j + dj] = nid
nets = list(rt.terms.keys())
SENS = [bnet(b) for b in ['d'] + BITS]
POWER = ['vss', 'vdd', 'vdd_dac', 'vdd_cmp']
rest = [n for n in nets if n not in SENS and n not in POWER]
rest.sort(key=lambda n: len(rt.terms[n]))
FIRST = [n for n in ('vin', 'tg_on', 'samb') if n in rt.terms]
ORDER_R = FIRST + [n for n in SENS if n in rt.terms] + [n for n in rest if n not in FIRST] + [n for n in POWER if n in rt.terms]
if int(globals().get('dbg', '0')):
    print('vdd_dac terms', [(c, [round(v, 2) for v in r]) for (c, r) in rt.terms['vdd_dac']])
bad = []
for n in ORDER_R:
    if not rt.route_net(n):
        bad.append(n)
print('routing: %d nets, %d failed: %s' % (len(ORDER_R), len(bad), bad))
for f in rt.failed:
    print('  FAILED', str(f)[:300])
    if f[1].startswith('terminal without') and int(globals().get('dbg', '0')):
        (c, r) = f[2]
        for (l, rr, nn) in rt.fixed:
            if rr[0] < r[2] + 3 and rr[2] > r[0] - 3 and rr[1] < r[3] + 3 and rr[3] > r[1] - 3:
                print('      near fixed: layer', l, [round(v, 2) for v in rr], nn)
    if f[1] == 'no path' and int(globals().get('dbg', '0')):
        (c, r) = f[2]
        cx, cy = (r[0] + r[2]) / 2.0, (r[1] + r[3]) / 2.0
        i0 = int(round((cx - rt.x0) / rt.p))
        j0 = int(round((cy - rt.y0) / rt.p))
        for l in range(3):
            print('   layer', l, 'blk/occ around the pad (rows j0+3 .. j0-3, cols i0-3 .. i0+3)')
            for j in range(j0 + 3, j0 - 4, -1):
                print('    ', ' '.join('%3d/%-3d' % (rt.blk[l, i, j], rt.occ[l, i, j]) for i in range(i0 - 3, i0 + 4)))
sh = rt.shapes()
for net, d in sh.items():
    for (lname, r) in d['wires']:
        k.rect(TOP, lname, *r)
    for (vname, r) in d['vias']:
        k.rect(TOP, vname, *r)
for (net, (x_, y_)) in rt.access_vias():
    k.rect(TOP, 'metal1', x_ - 0.25, y_ - 0.25, x_ + 0.25, y_ + 0.25)
    k.rect(TOP, 'via1', x_ - 0.13, y_ - 0.13, x_ + 0.13, y_ + 0.13)
for (n, lay, px, py) in PINS:
    if lay == 'metal3':
        k.rect(TOP, 'metal3', px - 0.25, py - 0.25, px + 0.25, py + 0.25)
    if lay == 'metal2':
        k.rect(TOP, 'metal2', px - 0.25, 0.0, px + 0.25, 1.25)
    if lay == 'metal4':
        k.rect(TOP, 'metal4', *PIN_RECT[n])
    k.label(TOP, lay, n, px, py)
bb = TOP.dbbox()
print('wrote %s  %.2f x %.2f um' % (outgds, bb.width(), bb.height()))
k.write(ly, outgds, 'adc_ch')
