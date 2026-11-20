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

LAY = int(globals().get('lay', '3'))             # 1 = packing of the first L2a pass (commit 1b3076a), 2 = packing "A-3" (rework step 1), 3 = tail group merged + pair and xm6 in one row (rework step 2, default)
_KD = dict(rg=2.5, gg=2.5, cg=3.0) if LAY == 1 else dict(rg=1.5, gg=1.5, cg=1.5)       # ring gaps (um) of dev_block / group_block / compose
for _n in ('rg', 'gg', 'cg'):
    a.KNOB[_n] = float(globals().get(_n, _KD[_n]))
a.KNOB['tm'] = int(globals().get('tm', '1' if LAY >= 3 else '0'))          # 1 = tail group xmb / xmt / xm7 as one 6-finger block (L2a rework step 2)
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


GX = float(globals().get('gx', '2.0' if LAY == 1 else '1.5'))          # gap between blocks of a row (um)
GY = float(globals().get('gy', '2.0' if LAY == 1 else '1.0'))          # gap between rows
CAP = float(globals().get('capt', '8.0' if LAY == 1 else '2.0'))       # margin above the Cin block lanes (pins) up to the cell top
if LAY == 1:
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
elif LAY == 4:
    # ---- "A-3, step 3": like lay=3, but mir is ROTATED by 90 degrees and stands in the east column (it may reach 5 um under the Metal5 lanes of the Cin block: nothing but Metal5 / the Metal4 ref tab is there);
    #      the capacitors C_T and Cin2 move to the bottom row, next to the column of xms / fol / Cc1 / s2p / sink1.
    B['mir'] = a.rotate_block(ly, B['mir'], 'mir_r')
    XR = float(globals().get('xr', '1.0'))
    x, top2 = XR, 3.0
    for n in ('xms', 'fol', 'cc1', 's2p'):
        xe, ye = put(n, B[n], x, 3.0)
        x = xe + GX
        top2 = max(top2, ye)
    xe, ye = put('sink1', B['sink1'], XR, top2 + GY)
    xb_ = max(xe, x - GX) + GX
    xe, y_ct = put('ct', B['ct'], xb_, 3.0)
    xe, y_ci = put('cin2', B['cin2'], xe + GX, 3.0)
    yt = max(ye, y_ct, y_ci) + GY
    xo, tt = row(['ota_p', 'xm6'], yt, x0=XR, gap=GX)
    t5 = tt
    STRIP = float(globals().get('strip', '24.0'))
    Y0 = math.ceil(t5 + GY + STRIP + 0.6)
    X0 = float(globals().get('x0', '7.0'))
    k.put(TOP, cin.cell, X0, Y0)
    PLACED.append(('cin', cin, X0, Y0))
    ys = Y0 - STRIP
    put('or2', B['or2'], 9.0, ys + 3.0)
    put('pr1', B['pr1'], X0 + 22.0, ys + 3.0)
    put('cf1', B['cf1'], X0 + 39.0, ys)
    xe, y1 = put('sp', B['sp'], X0 + 58.0, ys)
    put('sn', B['sn'], X0 + 58.0, y1 + GY)
    put('cf1p', B['cf1p'], X0 + 115.0, ys)
    put('pr2', B['pr2'], X0 + 135.0, ys + 3.0)
    xc = X0 + cin.bbox[2] + 2.0
    xmr = float(globals().get('xmr', '160.0'))                     # west edge of the rotated mir
    xe, yc = put('mir', B['mir'], xmr, ys)
    yc += GY
    xe, yc = put('s2tail', B['s2tail'], xc, yc)
    yc += GY
    xe, yc = put('s2pair', B['s2pair'], xc, yc)
    yc += GY
    xe, ye = put('cf2', B['cf2'], xc, yc)
    put('pr3', B['pr3'], xe + GX, yc)
    yc = ye + GY
    for n in ('cc2',):
        xe, ye = put(n, B[n], xc, yc)
        yc = ye + GY
elif LAY == 3:
    # ---- packing "A-3, step 2": tail group merged (tm=1) so that the input pair and xm6 share ONE row; bottom row = mirror + (sink1 over xms / fol / Cc1 / s2p);
    #      the Cf1 strip (taller) also holds the OR2, pseudo-R 1 / 2 and the sp / sn gate-mux stack; the east column starts with s2tail + s2pair
    XR = float(globals().get('xr', '1.0'))
    xm_, tmir = put('mir', B['mir'], XR, 3.0)
    xc0 = xm_ + GX
    x, top2 = xc0, 3.0
    for n in ('xms', 'fol', 'cc1', 's2p'):
        xe, ye = put(n, B[n], x, 3.0)
        x = xe + GX
        top2 = max(top2, ye)
    xe, ye = put('sink1', B['sink1'], xc0, top2 + GY)
    yt = max(ye, tmir) + GY
    xo, tt = row(['ota_p', 'xm6'], yt, x0=XR, gap=GX)
    t5 = tt
    STRIP = float(globals().get('strip', '24.0'))
    Y0 = math.ceil(t5 + GY + STRIP + 0.6)
    X0 = float(globals().get('x0', '7.0'))
    k.put(TOP, cin.cell, X0, Y0)
    PLACED.append(('cin', cin, X0, Y0))
    ys = Y0 - STRIP
    put('or2', B['or2'], 9.0, ys + 3.0)
    put('pr1', B['pr1'], X0 + 22.0, ys + 3.0)
    put('cf1', B['cf1'], X0 + 39.0, ys)
    xe, y1 = put('sp', B['sp'], X0 + 58.0, ys)
    put('sn', B['sn'], X0 + 58.0, y1 + GY)
    put('cf1p', B['cf1p'], X0 + 115.0, ys)
    put('pr2', B['pr2'], X0 + 135.0, ys + 3.0)
    xc = X0 + cin.bbox[2] + 2.0
    yc = ys
    xe, yc = put('s2tail', B['s2tail'], xc, yc)
    yc += GY
    xe, yc = put('s2pair', B['s2pair'], xc, yc)
    yc += GY
    xe, ye = put('cf2', B['cf2'], xc, yc)
    put('pr3', B['pr3'], xe + GX, yc)
    yc = ye + GY
    for n in ('cin2', 'cc2', 'ct'):
        xe, ye = put(n, B[n], xc, yc)
        yc = ye + GY
else:
    # ---- packing "A-3" (L2a rework): rows below the Cin block (ota_p on top, directly under the descenders), stage-2 + one-shot MIM column east of the Cin block
    XR = float(globals().get('xr', '4.0'))                 # west start of the device rows
    S2P_UP = int(globals().get('s2p_up', '1'))                                       # 1: s2p in the pocket east of ota_p (above s2tail) instead of the bottom row
    x, tb = row(['sink1', 'xms', 'fol'] + ([] if S2P_UP else ['s2p']), 3.0, x0=XR, gap=GX)      # bottom row: the out pin (fol) at the inner edge
    ym = tb + GY
    x, tm = row(['mir', 'xm6'], ym, x0=XR, gap=GX)                                  # stage-1 load mirror + xm6
    _pl = {nm: (dx, dy, blk) for (nm, blk, dx, dy) in PLACED}
    xe, _ = put('cc1', B['cc1'], x + GX, ym)
    yt = tm + GY
    xo, tt = row(['ota_p'], yt, x0=XR, gap=GX)                                      # input pair + tail group: the row next to the Cf1 strip
    xp = xo                                                                         # pocket east of ota_p: gate-mux / park / one-shot devices, OR2
    _, y1 = put('sp', B['sp'], xp, yt)
    _, y2 = put('sn', B['sn'], xp, y1 + GY)
    put('or2', B['or2'], xp + B['sn'].bbox[2] - B['sn'].bbox[0] + GX, y1 + GY)
    _, y3 = put('s2tail', B['s2tail'], xp, y2 + GY)
    if S2P_UP:
        _, y3 = put('s2p', B['s2p'], xp, y3 + GY)
    t5 = max(tt, y3)
    STRIP = float(globals().get('strip', '15.0'))
    Y0 = math.ceil(t5 + GY + STRIP + 0.6)                  # origin of the Cin block: the strip of the two Cf1 pieces lies below it
    X0 = float(globals().get('x0', '7.0'))
    k.put(TOP, cin.cell, X0, Y0)
    PLACED.append(('cin', cin, X0, Y0))
    put('cf1', B['cf1'], X0 + 39.0, Y0 - STRIP)                  # right of the vn descender (x = 35), same orientation as the Cin pieces
    put('pr1', B['pr1'], X0 + 39.0 + 20.0, Y0 - STRIP + 3.0)
    put('cf1p', B['cf1p'], X0 + 115.0, Y0 - STRIP)               # right of the vp descender (x = 111)
    put('pr2', B['pr2'], X0 + 115.0 + 20.0, Y0 - STRIP + 3.0)
    # east column: stage-2 diff pair, Cf2 + pseudo-R 3, Cin2, Cc2, C_T
    xc = X0 + cin.bbox[2] + 2.0
    yc = Y0 - STRIP
    xe, yc = put('s2pair', B['s2pair'], xc, yc)
    yc += GY
    xe, ye = put('cf2', B['cf2'], xc, yc)
    put('pr3', B['pr3'], xe + GX, yc)
    yc = ye + GY
    for n in ('cin2', 'cc2', 'ct'):
        xe, ye = put(n, B[n], xc, yc)
        yc = ye + GY
H = math.ceil(Y0 + cin.pins['ytop'] + CAP)
W = max(EAST, math.ceil(max(dx + blk.bbox[2] for (_, blk, dx, dy) in PLACED)) + 0.0)
print('placed: W = %.1f  H = %.1f  Y0 = %d  row top t5 = %.1f' % (W, H, Y0, t5))

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
if LAY in (3, 4):
    PINS.append(('vdd', 'metal4', W - 4.0, 14.0))                 # east edge, bottom (inner) half: free of blocks
    PINS.append(('vss', 'metal4', W - 4.0, 30.0))
else:
    PINS.append(('vdd', 'metal4', W - 6.0, H - (6.0 if LAY == 1 else 5.0)))
    PINS.append(('vss', 'metal4', W - (6.0 if LAY == 1 else 16.0), H - (14.0 if LAY == 1 else 5.0)))
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
