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
# router: obstacles, terminals, pins
# =====================================================================================================================================================================
W = 232
H = int(math.ceil(H_DAC + 4.0))
rt = RT.Router(1.0, 1.0, float(W) - 1.0, float(H) - 1.0)
for (name, blk, dx, dy) in PLACED:
    for (l, r, n, ex) in blk.fixed:
        rt.obstacle(l, (r[0] + dx, r[1] + dy, r[2] + dx, r[3] + dy), n, extra=ex)
    for (n, c, r) in blk.terms:
        rt.terminal(n, c, (r[0] + dx, r[1] + dy, r[2] + dx, r[3] + dy))
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
    k.label(TOP, lay, n, px, py)
bb = TOP.dbbox()
print('wrote %s  %.2f x %.2f um' % (outgds, bb.width(), bb.height()))
k.write(ly, outgds, 'adc_ch')
