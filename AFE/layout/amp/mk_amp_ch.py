"""mk_amp_ch.py (L2a): the amplifier channel amp_ch = afe_chc + fs_oneshot_c + OR2 (LVS reference: subckt amp_ch of AFE/layout/lvs/afe_chc.spice).
Run:  bash AFE/layout/scripts/kl.sh AFE/layout/amp/mk_amp_ch.py out=AFE/layout/amp [dbg=1] [plan=1]
  plan=1  only build the blocks and print their sizes
  dbg=1   label every internal net (for the debug LVS reference of mk_dbg_ref.py); the committed GDS is written WITHOUT dbg
Everything is generated; nothing is drawn by hand.  Geometry rules of this cell are in AFE/layout/FLOW.md and in the docstrings of amplib.py / router.py.
"""
import os
import sys
import math
import json
import kpdk as k
import amplib as a
import blocks_amp as BA
import router as RT

out = globals().get('out', 'AFE/layout/amp')
dbg = int(globals().get('dbg', '0'))
plan = int(globals().get('plan', '0'))
gdsname = globals().get('gds', 'amp_ch.gds')
os.makedirs(out, exist_ok=True)

ly = k.new_layout()
TOP = ly.create_cell('amp_ch')
B = BA.blocks(ly)
VN, VP, V1 = BA.VN, BA.VP, BA.V1

T, P = 70.65, 76.15                       # Cin piece (top plate) and the pitch of the 2 x 2 block (5.5 um corridors: MIMTM.1 needs 2.26 um from a top plate to a Metal4 strap that is part of the plate polygon)


def cin_block():
    """the 2 x 2 checkerboard of the four Cin pieces (A = Cin1: vn on the top plate / rec bottom; B = Cin2: vp / ref), all top-plate and bottom-plate wiring on Metal5 / Metal4 OUTSIDE the
    plate footprints or in the 5 um corridors.  Local origin = lower left corner of piece A1; A1 (0,0) A2 (P,P)  B1 (P,0) B2 (0,P).
    vn: A1 - A2 through the centre of the corridors (Metal5).  rec: Metal4 strap in the vertical corridor from A1 to A2, down to a pad below the block and up to the pin.
    vp: B1 - B2 around the east and north sides (inner lanes, Metal5).  ref: Metal4 tabs on the east / west edges, Metal5 lanes around (outer lanes)."""
    C = a.Block(ly, 'cin_blk')
    for (x, y, top, bot) in ((0.0, 0.0, VN, 'rec'), (P, 0.0, VP, 'ref'), (0.0, P, VP, 'ref'), (P, P, VN, 'rec')):
        a.mim_cap(C.cell, x, y, T, T, top, bot)
    C.grow(-0.6, -0.6, P + T + 0.6, P + T + 0.6)
    m5 = lambda x1, y1, x2, y2: C.rect('metal5', x1, y1, x2, y2)
    m4 = lambda x1, y1, x2, y2: C.rect('metal4', x1, y1, x2, y2)

    def via4(x1, y1, x2, y2):
        a.cuts(C.cell, 'via4', x1, y1, x2, y2, inset=0.2)
    top_edge = P + T                                                   # 146.3
    # vn: through the centre of the corridors
    xcc = T + (P - T) / 2.0
    m5(66.0, 67.0, xcc + 0.5, 68.0)
    m5(xcc - 0.5, 67.0, xcc + 0.5, 79.0)
    m5(xcc - 0.5, 78.0, P + 4.35, 79.0)
    # vn / vp descenders to the OTA (Metal5 down, Via4 to a Metal4 pad below the block = router terminal)
    for (xc, net) in ((35.0, VN), (111.0, VP)):
        m5(xc - 0.5, -7.0, xc + 0.5, 2.0)
        m5(xc - 1.0, -7.0, xc + 1.0, -5.0)
        m4(xc - 1.0, -7.0, xc + 1.0, -5.0)
        via4(xc - 1.0, -7.0, xc + 1.0, -5.0)
        C.term(net, 'metal4', (xc - 1.0, -7.0, xc + 1.0, -5.0))
        C.fixed_shape(a.M4, (xc - 1.0, -7.0, xc + 1.0, -5.0), net)
    # vp: east lane (inner) and north lane (inner)
    ex = top_edge + 4.5
    m5(140.0, 30.0, ex + 0.5, 31.0)
    m5(ex - 0.5, 30.0, ex + 0.5, ex + 0.5)
    m5(34.5, ex - 0.5, ex + 0.5, ex + 0.5)
    m5(34.5, top_edge - 1.3, 35.5, ex + 0.5)
    # ref: Metal4 tabs east (B1) and west (B2), Via4 to Metal5 pads, outer lanes
    ex2 = top_edge + 11.3
    ty = top_edge + 9.5
    m4(top_edge - 0.3, 10.0, ex2 + 0.6, 11.2)
    m5(ex2 - 0.6, 10.0, ex2 + 0.6, 11.2)
    via4(ex2 - 0.6, 10.0, ex2 + 0.6, 11.2)
    m5(ex2 - 0.6, 10.0, ex2 + 0.6, ty + 0.6)
    m5(-6.0, ty - 0.6, ex2 + 0.6, ty + 0.6)
    m4(-6.0, 110.0, 0.0, 111.2)
    m5(-6.0, 110.0, -4.8, 111.2)
    via4(-6.0, 110.0, -4.8, 111.2)
    m5(-6.0, 110.0, -4.8, ty + 0.6)
    # rec: Metal4 strap (0.9 um) through the vertical corridor, stubs to the plates, pad below the block, via to Metal5 above the lanes
    m4(T + 0.5, 34.5, xcc + 0.45, 35.5)
    m4(xcc + 0.45 - 0.1, 110.0, P - 0.5, 111.0)
    ytop = ty + 4.0
    m4(xcc - 0.45, -7.0, xcc + 0.45, ytop)
    m4(xcc - 1.0, -7.0, xcc + 1.0, -5.0)
    C.term('rec', 'metal4', (xcc - 1.0, -7.0, xcc + 1.0, -5.0))
    m5(xcc - 0.6, ytop - 1.5, xcc + 0.6, ytop)
    via4(xcc - 0.45, ytop - 1.4, xcc + 0.45, ytop - 0.1)
    for r in ((xcc - 0.45, -7.0, xcc + 0.45, ytop), (xcc - 1.0, -7.0, xcc + 1.0, -5.0), (T + 0.5, 34.5, xcc + 0.45, 35.5), (xcc + 0.35, 110.0, P - 0.5, 111.0)):
        C.fixed_shape(a.M4, r, 'rec')
    for r in ((146.0, 10.0, ex2 + 0.6, 11.2), (-6.0, 110.0, 0.0, 111.2)):
        C.fixed_shape(a.M4, r, 'ref')
    C.size = (P + T + 0.6 + 6.0 + 12.0, ytop + 7.0)
    C.pins = dict(rec_x=xcc, ref_x=125.0, ytop=ytop, ty=ty)
    C.keepout = (-1.0, -1.0, P + T + 1.0, P + T + 1.0)
    C.plates = [(x, y) for (x, y) in ((0.0, 0.0), (P, 0.0), (0.0, P), (P, P))]
    return C


cin = cin_block()

if plan:
    for n, blk in sorted(B.items()):
        print('%-8s %6.1f x %6.1f  bbox %s  terms %d' % (n, blk.bbox[2] - blk.bbox[0], blk.bbox[3] - blk.bbox[1], [round(v, 1) for v in blk.bbox], len(blk.terms)))
    print('cin      %6.1f x %6.1f' % (cin.bbox[2] - cin.bbox[0], cin.bbox[3] - cin.bbox[1]))
    sys.exit(0)

# =====================================================================================================================================================================
# placement (explicit rows; coordinates are integers, so every router node of a block terminal is also a node of the global grid)
# =====================================================================================================================================================================
PLACED = []                                  # (name, block, dx, dy)
WEST, EAST = 9.0, 220.0


def put(name, blk, x, y):
    """place the block so that the lower left corner of its bbox is at (x, y) or beyond (integer offset); returns the new top-right corner"""
    dx = math.ceil(x - blk.bbox[0] - 1e-9)
    dy = math.ceil(y - blk.bbox[1] - 1e-9)
    k.put(TOP, blk.cell, dx, dy)
    PLACED.append((name, blk, dx, dy))
    return dx + blk.bbox[2], dy + blk.bbox[3]


def row(names, y, x0=WEST, gap=3.0):
    x = x0
    top = y
    for n in names:
        xe, ye = put(n, B[n], x, y)
        x = xe + gap
        top = max(top, ye)
    return x, top


GAP_Y = 3.0
x, t1 = row(['sink1', 'xms', 'fol', 's2p'], 3.0, x0=8.0, gap=2.0)
x, t2 = row(['s2pair', 's2tail', 'sn', 'sp'], t1 + GAP_Y, x0=8.0, gap=2.0)
for n in ('sn', 'sp'):
    pass
_pl = {nm: (dx, dy, blk) for (nm, blk, dx, dy) in PLACED}
# small blocks above the short ones of row 2: pseudo-resistors above sn, OR2 above sp
yy = _pl['sn'][1] + _pl['sn'][2].bbox[3] + 3.0
xx = _pl['sn'][0] + _pl['sn'][2].bbox[0]
for n in ('pr1', 'pr2', 'pr3'):
    xe, ye = put(n, B[n], xx, yy)
    xx = xe + 2.0
put('or2', B['or2'], _pl['sp'][0] + _pl['sp'][2].bbox[0], _pl['sp'][1] + _pl['sp'][2].bbox[3] + 3.0)
x, t3 = row(['mir', 'xm6', 'cc1'], t2 + GAP_Y, x0=8.0, gap=2.0)
x, t4 = row(['ota_p'], t3 + GAP_Y, x0=8.0, gap=2.0)
t5 = t4
Y0 = math.ceil(t5 + GAP_Y + 19.0 + 0.6)                  # origin of the Cin block: the strip of the two Cf1 pieces (SPEC.md 3.2 item 1: next to the Cin block) lies below it, its descender pads 7 um below it
X0 = 9.0
k.put(TOP, cin.cell, X0, Y0)
PLACED.append(('cin', cin, X0, Y0))
put('cf1', B['cf1'], X0 + 39.0, Y0 - 19.0)                  # right of the vn descender (x = 35), same orientation as the Cin pieces
put('cf1p', B['cf1p'], X0 + 115.0, Y0 - 19.0)               # right of the vp descender (x = 111)
# column of the stage-2 / one-shot capacitors east of the Cin block
xc = X0 + cin.bbox[2] + 2.5
yc = Y0 + 1.0
for n in ('ct', 'cin2', 'cc2', 'cf2'):
    xe, ye = put(n, B[n], xc, yc)
    yc = ye + 3.0
H = math.ceil(Y0 + cin.pins['ytop'] + 8.0)
W = max(EAST, math.ceil(max(dx + blk.bbox[2] for (_, blk, dx, dy) in PLACED)) + 0.0)
print('placed: W = %.1f  H = %.1f  rows tops %s' % (W, H, [round(v, 1) for v in (t1, t2, t3, t4, t5)]))

# =====================================================================================================================================================================
# router: obstacles, terminals, pins
# =====================================================================================================================================================================
rt = RT.Router(1.0, 1.0, float(W) - 1.0, float(H) - 1.0)
for (name, blk, dx, dy) in PLACED:
    for (l, r, n, ex) in blk.fixed:
        rt.obstacle(l, (r[0] + dx, r[1] + dy, r[2] + dx, r[3] + dy), n, extra=ex)
    for (n, c, r) in blk.terms:
        rt.terminal(n, c, (r[0] + dx, r[1] + dy, r[2] + dx, r[3] + dy))
    if hasattr(blk, 'mim'):
        m = blk.mim
        pl = m['plate']
        rt.block_all((pl[0] + dx, pl[1] + dy, pl[2] + dx, pl[3] + dy), layers=(0, 1))
        rt.obstacle(2, (pl[0] + dx, pl[1] + dy, pl[2] + dx, pl[3] + dy), None, extra=0.9)
kx = cin.keepout
rt.block_all((kx[0] + X0, kx[1] + Y0, kx[2] + X0, kx[3] + Y0))
rt.obstacle(2, (kx[0] + X0, kx[1] + Y0, kx[2] + X0, kx[3] + Y0), None, extra=0.9)
# the area above the Cin block lanes is not used by the router at all

# ---- pins (label, layer, position)
PINS = []
ytop_pin = H - 3.0
for i, n in enumerate(('vbn', 'vcm', 'vg1', 'vcmo', 'vg2', 'vrs')):
    PINS.append((n, 'metal3', 1.0 + i, ytop_pin))
for i, n in enumerate(('sw_rec', 'sw_rec_b', 'rst_amp')):
    PINS.append((n, 'metal2', 1.0, H - 12.0 - 8.0 * i))
PINS.append(('vdd', 'metal4', W - 6.0, H - 6.0))
PINS.append(('vss', 'metal4', W - 6.0, H - 14.0))
xo = None
for (name, blk, dx, dy) in PLACED:
    if name == 'fol':
        xo = dx + 8.0
PINS.append(('out', 'metal3', math.floor(xo), 2.0))
for (n, lay, px, py) in PINS:
    if lay == 'metal4':
        rt.terminal(n, 'metal4', (px - 1.5, py - 1.5, px + 1.5, py + 1.5))
        rt.obstacle(2, (px - 1.5, py - 1.5, px + 1.5, py + 1.5), n)
    elif lay == 'metal3':
        rt.terminal(n, 'metal3', a.pad_rect(px, py, 0.5))
    else:
        rt.terminal(n, 'metal2', a.pad_rect(px, py, 0.5))

HALO_NETS = [BA.VN, BA.VP, BA.VN2, BA.M1R, BA.M2R, BA.M3R, 'rec']   # routed wires of the summing nodes / pseudo-resistor nodes / rec: a SOFT clearance of ~2 um to other nets (SPEC.md 3.2 item 5); the ends sit inside device blocks
HALO = float(globals().get('halo', '1.95'))
HEND = int(globals().get('hend', '8'))
rt.reserve()
# ---- routing order: sensitive / short nets first, power last
SENS = [BA.VN, BA.VP, BA.VN2, BA.M1R, BA.M2R, BA.M3R, 'rec', BA.O1, BA.O2]
nets = list(rt.terms.keys())
rest = [n for n in nets if n not in SENS and n not in (BA.VDD, BA.VSS)]
rest.sort(key=lambda n: len(rt.terms[n]))
ORDER = [n for n in SENS if n in rt.terms] + rest + [BA.VDD, BA.VSS]
bad = []
for n in ORDER:
    ok = rt.route_net(n)
    if not ok:
        bad.append(n)
    if n in HALO_NETS and ok:
        for path in rt.paths.get(n, []):
            for idx, (l, i, j) in enumerate(path):
                if idx < HEND or idx > len(path) - 1 - HEND:         # the ends sit inside the device blocks: no halo there
                    continue
                x, y = rt.xy(i, j)
                rt.add_halo(l, (x - 0.25, y - 0.25, x + 0.25, y + 0.25), n, HALO)
print('routing: %d nets, %d failed: %s' % (len(ORDER), len(bad), bad))
for f in rt.failed:
    print('  FAILED', f)


# ---- achieved clearance of the sensitive nets (routed wires only): edge-to-edge distance to the nearest wire of another net on the same layer
CLEAR = {}
for n in HALO_NETS:
    nid = rt.nid(n)
    worst, tot, near = 99.0, 0, 0
    for path in rt.paths.get(n, []):
        for idx, (l, i, j) in enumerate(path):
            if idx < HEND or idx > len(path) - 1 - HEND:
                continue
            tot += 1
            best = 99.0
            for di in range(-3, 4):
                for dj in range(-3, 4):
                    ii, jj = i + di, j + dj
                    if 0 <= ii < rt.nx and 0 <= jj < rt.ny:
                        o = rt.occ[l, ii, jj]
                        if o not in (0, nid):
                            best = min(best, max(abs(di), abs(dj)) * 1.0 - 0.5)
            worst = min(worst, best)
            if best < 2.0:
                near += 1
    CLEAR[n] = dict(nodes=tot, nodes_closer_than_2um=near, min_clearance_um=round(worst, 2))
print('clearance of the sensitive nets (edge to edge, same layer):', json.dumps(CLEAR))

# =====================================================================================================================================================================
# emit router shapes
# =====================================================================================================================================================================
sh = rt.shapes()
nw = nv = 0
for net, d in sh.items():
    for (lname, r) in d['wires']:
        k.rect(TOP, lname, *r)
        nw += 1
    for (vname, r) in d['vias']:
        k.rect(TOP, vname, *r)
        nv += 1
for (net, (x_, y_)) in rt.access_vias():
    k.rect(TOP, 'metal1', x_ - 0.25, y_ - 0.25, x_ + 0.25, y_ + 0.25)
    k.rect(TOP, 'via1', x_ - 0.13, y_ - 0.13, x_ + 0.13, y_ + 0.13)
    nv += 1
print('router shapes: %d wires, %d vias' % (nw, nv))

# ---- the M5 pin lanes of rec and ref and the pin labels
yt = Y0 + cin.pins['ytop']
k.rect(TOP, 'metal5', X0 + cin.pins['rec_x'] - 0.6, yt - 1.5, X0 + cin.pins['rec_x'] + 0.6, H)
tyg = Y0 + cin.pins['ty']
k.rect(TOP, 'metal5', X0 + cin.pins['ref_x'] - 0.6, tyg - 0.6, X0 + cin.pins['ref_x'] + 0.6, H)
k.label(TOP, 'metal5', 'rec', X0 + cin.pins['rec_x'], H - 1.0)
k.label(TOP, 'metal5', 'ref', X0 + cin.pins['ref_x'], H - 1.0)
for (n, lay, px, py) in PINS:
    if lay == 'metal4':
        k.rect(TOP, 'metal4', px - 1.5, py - 1.5, px + 1.5, py + 1.5)
    k.label(TOP, lay, n, px, py)
    if lay == 'metal3':
        k.rect(TOP, 'metal3', px - 0.25, py - 0.25, px + 0.25, py + 0.25)
    if lay == 'metal2':
        k.rect(TOP, 'metal2', px - 0.25, py - 0.25, px + 0.25, py + 0.25)

bb = TOP.dbbox()
info = dict(W=round(bb.width(), 3), H=round(bb.height(), 3), bbox=[round(v, 3) for v in (bb.left, bb.bottom, bb.right, bb.top)], slot=[220, 263], dbg=dbg,
            blocks={n: [round(blk.bbox[2] - blk.bbox[0], 2), round(blk.bbox[3] - blk.bbox[1], 2), dx, dy] for (n, blk, dx, dy) in PLACED}, failed=bad, clearance=CLEAR, cin=dict(X0=X0, Y0=Y0, T=T, P=P), halo=dict(extra_um=HALO, end_nodes=HEND),
            wire_um={n: round(sum(len(p) for p in rt.paths.get(n, [])) * 1.0, 1) for n in rt.paths})
json.dump(info, open(os.path.join(out, 'amp_ch.build.json' if not dbg else 'amp_ch_dbg.build.json'), 'w'), indent=1)
k.write(ly, os.path.join(out, gdsname), 'amp_ch')
print('wrote %s  %.2f x %.2f um' % (gdsname, bb.width(), bb.height()))
