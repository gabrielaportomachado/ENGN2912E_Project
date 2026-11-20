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
PITCH = 3.5
ORDER = ['d'] + list(range(12))                                       # west -> east: bd, b0 .. b11  (LSB drivers west, MSB drivers east, like the array)


def row_a():
    t = []
    x = 0
    for b in ORDER:
        t.append(dict(kind='nfet', w=1.0, l=0.28, x=x, y=0, s='vss', d=bnet(b), g=('dac_gdn' if b == 'd' else gn(b)), ring_s=True))
        x += 4                                                     # the pull-down tile has no source terminal (ring_s): 3 pad columns for the TG tile after it
        t.append(dict(kind='nfet', w=1.0, l=0.28, x=x, y=0, s='vin', d=bnet(b), g='tg_on'))
        x += 3
    return a.group_block(ly, 'row_a', t, ring_kind='p', ring_net='vss')


def row_b1():
    t = []
    x = 0
    for b in ORDER:
        t.append(dict(kind='pfet', w=2.0, l=0.28, x=x, y=0, s='vdd_dac', d=bnet(b), g=('vdd_dac' if b == 'd' else gp(b)), ring_s=True, ring_g=(b == 'd')))
        x += 3                                                     # no source terminal (ring_s): 2 pad columns per tile
    return a.group_block(ly, 'row_b1', t, ring_kind='n', ring_net='vdd_dac')


def row_b2():
    t = []
    x = 0
    for b in ORDER:
        t.append(dict(kind='pfet', w=2.0, l=0.28, x=x, y=0, s='vin', d=bnet(b), g='samb'))
        x += 4
    return a.group_block(ly, 'row_b2', t, ring_kind='n', ring_net='vdd')


RA, RB1, RB2 = row_a(), row_b1(), row_b2()
if plan:
    for n, b in (('row_a', RA), ('row_b1', RB1), ('row_b2', RB2)):
        print(n, [round(v, 1) for v in b.bbox], 'terms', len(b.terms))

# =====================================================================================================================================================================
# placement (R5: drivers bottom-left, DAC above them WITHOUT dummy rows, vhalf in the keep-out band, comparator bottom-right under Cref, switches + capacitor beside Cref)
# =====================================================================================================================================================================
H_MAX = 104.0
KO = 20.3                                   # control wire -> top plate, SPEC.md 3.3 rule 6 (20 um + half a wire)
X_A = 6.0
Y_A = 2.5
xe, ye = put('row_a', RA, X_A, Y_A)
xe2, ye2 = put('row_b1', RB1, X_A, ye + 2.5)
xe3, ye3 = put('row_b2', RB2, xe2 + 2.0, ye + 2.5)
Y_DRV_TOP = max(ye2, ye3)
# highest control gate pad of the driver rows
WIRE_TOP = 0.0
for (nm, blk, dx, dy) in PLACED:
    for (n, c, r) in blk.terms:
        if n.startswith('dac_g') or n in ('tg_on', 'samb'):
            WIRE_TOP = max(WIRE_TOP, r[3] + dy)
print('driver zone top y = %.1f, highest control gate pad %.2f, row_a x end %.1f, row_b2 x end %.1f' % (Y_DRV_TOP, WIRE_TOP, xe, xe3))

# DAC array (no dummy rows): lower left of the (virtual) S dummy plate row at (X0L, YS); the channel centre must be an integer y
X0L = 13.0
YS_MIN = WIRE_TOP + KO - DL.U - DL.GAP_D
YS = math.ceil(YS_MIN - 0.8) + 0.8                                    # y0 = n + 0.8  ->  channel centre y = y0 + 36.2 integer
cellD = ly.create_cell('dac')
D = DL.build(cellD, X0L, YS, dummies=False)
k.put(TOP, cellD, 0, 0)
print('DAC: x %.1f .. %.1f  y %.1f .. %.1f  channel centre %.1f' % (D.xl0, D.xm1, D.ylo, D.top, D.ych))
H_DAC = D.top + 0.6
if plan:
    sys.exit(0)

# =====================================================================================================================================================================
# the rest of the cell: comparator, Cref (+ switch, inverter), vhalf (+ capacitor), reset switches
# =====================================================================================================================================================================
EXPLICIT = []                                 # (layer index 0..2, rect, net, extra): shapes drawn by hand below (stacks of t / vref / m): obstacles for the router
CREF_W = 59.07
# ---- comparator (two mirror-image halves + centre column), bottom right; its east pad vref sits under the Cref plate
CMP = CT.comparator(ly)
YC = int(math.ceil(4.5 - CMP.bbox[1]))
CREF_X0 = 161.0                                # lower left of the Cref plate; the plate ends at 220.07, its Metal4 at 220.67, the bottom-plate pad is on the west side
XC = int(CREF_X0 + 55.0 - CMP.ext['vref'][0])
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
# ---- the column between the DAC and Cref (bottom to top): Cref switch, capacitor of vhalf, inverter
cx0 = int(CREF_X0)
cy0 = int(math.ceil(YC + CMP.bbox[3] + 1.5))
dxr, dyr = cx0, cy0
XCOL = math.ceil(D.xp_t + 6.0)
VHC = R.mim_unit_block(ly, 'vh_cap', 22.18, 'vcmd', 'vss', yb=1, yt=4)
y_sw = dyr
yx = put('sw_n', SWN, XCOL, y_sw)
yx2 = put('sw_p', SWP, yx[0] + 3, y_sw)
y_iv = max(yx[1], yx2[1]) + 2.5
yv2 = put('iv_n', IVN, XCOL, y_iv)
yv3 = put('iv_p', IVP, yv2[0] + 3, y_iv)
y_cap = max(yv2[1], yv3[1]) + 2.5
ycp = put('vh_cap', VHC, XCOL, y_cap)
cap_dy = [dy for (n_, b_, dx_, dy) in PLACED if n_ == 'vh_cap'][0]
print('column x %d: switches y %.1f, inverter y %.1f, cap y %.1f .. %.1f' % (XCOL, y_sw, y_iv, y_cap, ycp[1]))
# ---- Cref: ONE 59.07 um MIM plate, top plate = vref, bottom plate = vss; nothing below Metal4 in its footprint; its vss pad is level with the vss pad of the capacitor
cref = R.mim_bw_block(ly, 'cref', CREF_W, 'vref', 'vss', yb=57)
k.put(TOP, cref.cell, dxr, dyr)
PLACED.append(('cref', cref, dxr, dyr))
# vref: Metal5 strap from the plate to the comparator pad (Metal3 pad -> Via3 -> Metal4 -> Via4 -> Metal5)
vx, vy = vref_pad
EXPLICIT += [(l, r, 'vref', 0.0) for (l, r) in stack_up(TOP, vx, vy, 3, 5, w5=1.0)]
k.rect(TOP, 'metal5', vx - 0.5, vy - 0.5, vx + 0.5, dyr + 0.01)
print('Cref: x %.1f .. %.1f  y %.1f .. %.1f' % (dxr, dxr + CREF_W, dyr, dyr + CREF_W))

# ---- vhalf: serpentine in the keep-out band under the DAC
VH.NSEG, VH.LSEG, VH.PITCH, VH.DUMMIES = 4, 62.5, 2.2, False
VHR = VH.build(ly)
put('vhalf', VHR, 24.0, Y_DRV_TOP + 1.2)

# ---- reset switches (t / m to vcmd, gate rst_sw) next to the lower ends of the trunks
XR0 = a.group_block(ly, 'xr0', [dict(kind='nfet', w=0.5, l=0.28, x=0, y=0, s='vcmd', d='t', g='rst_sw')], ring_kind='p', ring_net='vss')
XR1 = a.group_block(ly, 'xr1', [dict(kind='nfet', w=0.5, l=0.28, x=0, y=0, s='vcmd', d='m', g='rst_sw')], ring_kind='p', ring_net='vss')
y_tstrap = math.ceil(D.ylo) - 8
XR0X = D.xp_t - 20
put('xr0', XR0, XR0X, y_tstrap - 4)
put('xr1', XR1, D.xl0 - 12, y_tstrap - 4)

# =====================================================================================================================================================================
# router: obstacles, terminals, pins
# =====================================================================================================================================================================
W_CELL = max(dx + blk.bbox[2] for (_, blk, dx, dy) in PLACED)
H_CELL = max(H_DAC, max(dy + blk.bbox[3] for (_, blk, dx, dy) in PLACED))
W = int(math.ceil(W_CELL)) + 4
H = int(math.ceil(H_CELL)) + 1
print('placed extent: W = %.1f  H = %.1f' % (W_CELL, H_CELL))
rt = RT.Router(1.0, 1.0, float(W) - 1.0, float(H) - 1.0)
BAN_NETS = ['dac_gdn', 'cmp_clk', 'tg_on', 'samb', 'rst_sw'] + ['dac_gp[%d]' % b_ for b_ in range(12)] + ['dac_gn[%d]' % b_ for b_ in range(12)]
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
rt.block_all((body_x1, D.ylo - 0.6, body_x2, ych - 3.0), layers=(0, 1))
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


Y_T = CMP.bbox[3] + YC + 1.6                                                 # the t strap runs ABOVE the comparator (between its top edge and the first plate row)
for (nm, net, trunk, rt_x) in (('xr0', 't', D.tr_t, D.xT_t), ('xr1', 'm', D.tr_m, D.xT_m)):
    xd, yd = term_xy(nm, net)
    EXPLICIT += [(l, r, net, 0.0) for (l, r) in stack_up(TOP, xd, yd, 1, 5, w5=0.8)]
    if net == 't':
        k.rect(TOP, 'metal5', xd - 0.5, yd - 0.5, xd + 0.5, Y_T + 0.5)
        k.rect(TOP, 'metal5', min(xd, rt_x) - 0.5, Y_T - 0.5, max(xd, rt_x) + 0.5, Y_T + 0.5)
        k.rect(TOP, 'metal5', rt_x - 0.5, Y_T - 0.5, rt_x + 0.5, trunk[1] + 0.01)
    else:
        k.rect(TOP, 'metal5', min(xd, rt_x) - 0.5, yd - 0.5, max(xd, rt_x) + 0.5, yd + 0.5)       # strap to the trunk column
        k.rect(TOP, 'metal5', rt_x - 0.5, yd - 0.5, rt_x + 0.5, trunk[1] + 0.01)                  # the trunk is extended down to the switch
tx, ty = t_pad
EXPLICIT += [(l, r, 't', 0.0) for (l, r) in stack_up(TOP, tx, ty, 3, 5, w5=1.0)]
k.rect(TOP, 'metal5', tx - 0.5, ty - 0.5, tx + 0.5, Y_T + 0.5)
k.rect(TOP, 'metal5', min(tx, D.xT_t) - 0.5, Y_T - 0.5, max(tx, D.xT_t) + 0.5, Y_T + 0.5)
for nm in ('sw_n', 'sw_p'):                                                  # the Cref switch drains: Metal5 strap to the west edge of the Cref plate (the plate is the vref node)
    xd, yd = term_xy(nm, 'vref')
    EXPLICIT += [(l, r, 'vref', 0.0) for (l, r) in stack_up(TOP, xd, yd, 1, 5, w5=0.8)]
    k.rect(TOP, 'metal5', xd - 0.5, yd - 0.5, dxr + 0.01, yd + 0.5)
for (l, r, n, ex) in EXPLICIT:
    rt.obstacle(l, r, n, extra=ex)
for net in ('t', 'm', 'vref'):
    rt.terms.pop(net, None)                                                  # drawn explicitly: no router terminal
bridge_pads = [i for i, (n, c, r) in enumerate(D.terms) if n == 'm']
# keep-out of the control nets: the band between the driver rows and the first plate row (SPEC.md 3.3 rule 6), except the 12 um at the reset switch xr0 / xr1
rt.ban(BAN_NETS, (D.xl0 - 2.0, D.ylo - 20.6, XR0X - 0.5, D.ylo - 0.7))
rt.ban(BAN_NETS, (XR0X + 9.0, D.ylo - 20.6, D.xm1 + 6.0, D.ylo - 0.7))

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
            'vdd': (215.0, 0.0, 221.0, 4.0)}
for n, r in PIN_RECT.items():
    PINS.append((n, 'metal4', (r[0] + r[2]) / 2.0, (r[1] + r[3]) / 2.0))
    rt.terminal(n, 'metal4', r)
    rt.obstacle(2, r, n, extra=0.8)
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
        print('   net ids', {i: n for i, n in rt.names.items() if i in (43, 21, 25, 23, 27, 29, 61, 29)})
        (c, r) = f[2]
        cx, cy = (r[0] + r[2]) / 2.0, (r[1] + r[3]) / 2.0
        i0 = int(round((cx - rt.x0) / rt.p))
        j0 = int(round((cy - rt.y0) / rt.p))
        for l in range(3):
            print('   layer', l, 'blk/occ around the pad (rows j0+3 .. j0-3, cols i0-3 .. i0+3)')
            for j in range(j0 + 3, j0 - 4, -1):
                print('    ', ' '.join('%3d/%-3d' % (rt.blk[l, i, j], rt.occ[l, i, j]) for i in range(i0 - 3, i0 + 4)))
sh = rt.shapes()
SKIP = [x for x in globals().get('skip', '').split(',') if x]
if int(globals().get('dbg', '0')):
    for nn in ('vdd_cmp',):
        print('WIRES', nn, [(l, [round(v, 2) for v in r]) for (l, r) in sh[nn]['wires'] if r[1] < 8][:20])
for net, d in sh.items():
    if net in SKIP:
        continue
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
if int(globals().get('lab', '0')):                                     # debug: label the DAC bottom-plate pads so that test/probe_short.py sees the bit nets (NEVER in a deliverable GDS)
    for (n, c, r) in D.terms:
        k.label(TOP, 'metal4', n, (r[0] + r[2]) / 2.0, (r[1] + r[3]) / 2.0)
bb = TOP.dbbox()
print('wrote %s  %.2f x %.2f um' % (outgds, bb.width(), bb.height()))
k.write(ly, outgds, 'adc_ch')

# =====================================================================================================================================================================
# facts that DRC / LVS do not test: DAC site map + centroids, block sizes, keep-out distances, wire lengths of the sensitive nets  -> dac_sites.log, adc_ch.build.json, keepout.log
# =====================================================================================================================================================================
LOG = []
LOG.append('# dac_sites.log (mk_adc_ch.py, L1a): site of every DAC unit.  Coordinates: lower-left corner of the 5 x 5 um top plate (FuseTop / Metal5) in the adc_ch frame, um.')
LOG.append('# half L = LSB array (node m), half M = MSB array (node t); row 0 = lowest of the 8 rows of a half, col = index inside the run order of that row (west -> east).')
LOG.append('# unit  half  row  col  bit  top_plate  bottom_plate  x  y  w')
cnt = {}
unit_list = []
rowcol = {}
for i, (tag, nt, nb, x, y, w) in enumerate(D.sites):
    if tag.startswith('dummy'):
        LOG.append('dummy  -     -    -    %-4s %-9s %-12s %8.3f %8.3f  bar (plain Metal4 / Metal5, no FuseTop)  length %.3f' % ('-', nt, nb, x, y, w))
        continue
    half = 'L' if nt == 'm' and tag != 'br' else 'M'
    if tag == 'br':
        half = 'M'
    rr = min(range(8), key=lambda r: abs(D.ys[r + 1] - y))
    c = rowcol.get((half, rr), 0)
    rowcol[(half, rr)] = c + 1
    LOG.append('u%03d   %-5s %-4d %-4d %-4s %-9s %-12s %8.3f %8.3f  %.3f' % (len(unit_list), half, rr, c, tag, nt, nb, x, y, w))
    unit_list.append((half, rr, tag, x, y, w))
    cnt[tag] = cnt.get(tag, 0) + 1
LOG.append('# units per bit: ' + ' '.join('%s=%d' % (b, cnt.get(b, 0)) for b in ['b11', 'b10', 'b9', 'b8', 'b7', 'b6', 'br', 'b5', 'b4', 'b3', 'b2', 'b1', 'b0', 'bd']) + '   total %d' % sum(cnt.values()))
wl = D.xl1 - D.xl0
wm = D.xm1 - D.xm0
y_c = (D.ys[1] + D.ys[8] + DL.U) / 2.0
LOG.append('# centroids relative to the centre of the half array (um; the units of a bit sit in point-symmetric pairs, a non-zero value is the odd unit):')
for half, xc0 in (('L', D.xl0 + wl / 2.0), ('M', D.xm0 + wm / 2.0)):
    for b in (['b11', 'b10', 'b9', 'b8', 'b7', 'b6', 'br'] if half == 'M' else ['b5', 'b4', 'b3', 'b2', 'b1', 'b0', 'bd']):
        us = [(x + w / 2.0, y + DL.U / 2.0) for (h, r, t, x, y, w) in unit_list if h == half and t == b]
        if us:
            LOG.append('#   %-4s n=%-3d  dx = %+6.2f  dy = %+6.2f' % (b, len(us), sum(u[0] for u in us) / len(us) - xc0, sum(u[1] for u in us) / len(us) - y_c))
open(os.path.join(outdir, 'dac_sites.log'), 'w').write('\n'.join(LOG) + '\n')

# block sizes
BLK = {}
for (name, blk, dx, dy) in PLACED:
    BLK[name] = [round(blk.bbox[0] + dx, 2), round(blk.bbox[1] + dy, 2), round(blk.bbox[2] + dx, 2), round(blk.bbox[3] + dy, 2)]
BLK['dac'] = [round(D.xl0 - 5.6, 2), round(D.ylo - 0.6, 2), round(D.xp_t + 0.6, 2), round(D.top + 0.6, 2)]
# keep-out distances (SPEC.md 3.3 rule 6, section 5 rule 1)
plates = [(x, y, x + w, y + DL.U) for (tag, nt, nb, x, y, w) in D.sites if nt in ('t', 'm') or tag == 'br']
plates += [(dxr, dyr, dxr + CREF_W, dyr + CREF_W), (vx - 0.5, vy - 0.5, vx + 0.5, dyr)]
CTRL = ['cmp_clk', 'dac_gdn', 'rst_sw', 'tg_on'] + [gp(b) for b in BITS] + [gn(b) for b in BITS]
KO = {}
KN = {}
KB = {}
for n in CTRL:
    best, where = 1e9, None
    near = set()
    for path in rt.paths.get(n, []):
        for (l, i, j) in path:
            x, y = rt.xy(i, j)
            dmin = 1e9
            for (a1, b1, a2, b2) in plates:
                ddx = max(a1 - x, 0.0, x - a2)
                ddy = max(b1 - y, 0.0, y - b2)
                dd = math.hypot(ddx, ddy) - 0.25
                dmin = min(dmin, dd)
                if dd < best:
                    best, where = dd, (round(x, 1), round(y, 1))
            if dmin < 20.0:
                near.add((l, i, j))
    KO[n] = (round(best, 1), where)
    KN[n] = len(near)
    if near:
        xs_ = [rt.xy(i, j)[0] for (l, i, j) in near]
        ys_ = [rt.xy(i, j)[1] for (l, i, j) in near]
        KB[n] = (min(xs_), min(ys_), max(xs_), max(ys_))
klog = ['# keepout.log (mk_adc_ch.py, L1a): smallest edge distance between a wire of the control nets and a DAC top plate (t / m / bridge) or the Cref plate / vref strap, um.  Limit 20 um (SPEC.md 3.3 rule 6),',
        '# exception: the last 10 um of a net at the device it drives (cmp_clk at the comparator; rst_sw at the reset switches next to the trunks).']
for n, (dd, wh) in sorted(KO.items(), key=lambda kv: kv[1][0]):
    klog.append('%-12s %6.1f um  at %s  %s  (%d grid nodes of 1 um within 20 um of a plate)' % (n, dd, wh, 'OK' if dd >= 20.0 else 'BELOW 20 um', KN[n]) + ('  box %s' % (KB[n],) if n in KB else ''))
open(os.path.join(outdir, 'keepout.log'), 'w').write('\n'.join(klog) + '\n')
wire = {n: round(sum(len(p) for p in rt.paths.get(n, [])) * 1.0, 1) for n in rt.paths}
info = dict(W=round(bb.width(), 3), H=round(bb.height(), 3), bbox=[round(v, 3) for v in (bb.left, bb.bottom, bb.right, bb.top)], slot=[222, 104], blocks=BLK, failed=bad, keepout={n: v[0] for n, v in KO.items()},
            wire_um=wire, dac=dict(x0=D.xl0, y0=D.ys[0], rows_y=[round(v, 3) for v in D.ys], ych=D.ych, xT_t=D.xT_t, xT_m=D.xT_m, units=sum(cnt.values())), cref=[dxr, dyr, CREF_W],
            comparator_xy=[XC, YC], cmp_failed=CMP.failed)
info['comparator_wire_um'] = {n: round(sum(len(p) for p in CMP.rt.paths.get(n, [])) * 1.0, 1) for n in CMP.rt.paths}
yx0 = term_xy('xr0', 't')[1]
yx1 = term_xy('xr1', 'm')[1]
info['t_metal5_um'] = round((D.tr_t[2] - min(yx0, ty)) + (tx - D.xT_t) + 8 * 3.0, 1)
info['m_metal5_um'] = round((D.tr_m[2] - yx1) + 8 * 3.0, 1)
info['vref_strap_um'] = round(dyr - (vy - 0.5), 1)
json.dump(info, open(os.path.join(outdir, 'adc_ch.build.json'), 'w'), indent=1)
print('keep-out: %d control nets, %d below 20 um: %s' % (len(KO), sum(1 for v in KO.values() if v[0] < 20.0), sorted([(n, v[0]) for n, v in KO.items() if v[0] < 20.0], key=lambda t: t[1])[:6]))
