"""rlib.py (L1a): helpers on top of adclib / router: a MIM unit block with separated pads and `route_cell` = place blocks, route the nets of ONE cell with its own router instance (local frame),
expose the external nets as Metal3 pads, and hand the result up as a block (terminals = the pads, fixed shapes = the routed wires, for the router of the next level).
Run only inside KLayout through kl.sh."""
import math
import kpdk as k
import adclib as a
import router as RT

LAYER_IDX = {'metal2': 0, 'metal3': 1, 'metal4': 2}


def mim5_block(ly, name, top, bot):
    """MIM unit 5 x 5 um (top plate lower-left corner at the origin).  Bottom plate: Metal4 tab east + pad centre (8, 1); top plate: Metal5 strap east to a Via4 + Metal4 pad centre (8, 4).
    Both pads are 1.2 um squares >= 2.26 um from the top plate edge (MIMTM.1, FLOW.md section 5) and 1.8 um from each other; terminals = the pads (router layer Metal4)."""
    B = a.Block(ly, name)
    a.mim_cap(B.cell, 0.0, 0.0, 5.0, 5.0, top, bot)
    B.grow(-0.6, -0.6, 5.6, 5.6)
    B.rect('metal4', 5.5, 0.5, 7.5, 1.5)
    B.rect('metal4', 7.4, 0.4, 8.6, 1.6)
    B.term(bot, 'metal4', (7.4, 0.4, 8.6, 1.6))
    B.fixed_shape(a.M4, (5.5, 0.5, 7.5, 1.5), bot, 1.0)
    B.fixed_shape(a.M4, (7.4, 0.4, 8.6, 1.6), bot, 1.0)
    B.rect('metal5', 4.99, 3.5, 8.6, 4.5)
    B.rect('metal4', 7.4, 3.4, 8.6, 4.6)
    a.cuts(B.cell, 'via4', 7.4, 3.4, 8.6, 4.6, inset=0.3)
    B.rect('metal5', 7.4, 3.4, 8.6, 4.6)
    B.term(top, 'metal4', (7.4, 3.4, 8.6, 4.6))
    B.fixed_shape(a.M4, (7.4, 3.4, 8.6, 4.6), top, 0.0)
    B.mim = dict(w=5.0, plate=(-0.6, -0.6, 5.6, 5.6), top=(0.0, 0.0, 5.0, 5.0), bot=bot, topnet=top)
    B.size = (9.2, 6.2)
    return B


def tr_rect(r, dx, dy, mirror):
    if mirror:
        return (dx - r[2], dy + r[1], dx - r[0], dy + r[3])
    return (r[0] + dx, r[1] + dy, r[2] + dx, r[3] + dy)


def emit(rt, cell):
    sh = rt.shapes()
    nw = 0
    for net, d in sh.items():
        for (lname, r) in d['wires']:
            k.rect(cell, lname, *r)
            nw += 1
        for (vname, r) in d['vias']:
            k.rect(cell, vname, *r)
    for (net, (x_, y_)) in rt.access_vias():
        k.rect(cell, 'metal1', x_ - 0.25, y_ - 0.25, x_ + 0.25, y_ + 0.25)
        k.rect(cell, 'via1', x_ - 0.13, y_ - 0.13, x_ + 0.13, y_ + 0.13)
    return nw


def add_part_to_router(rt, blk, dx, dy, mirror=False, rename=None):
    rn = (rename if callable(rename) else (lambda n: rename.get(n, n))) if rename else (lambda n: n)
    for (l, r, n, ex) in blk.fixed:
        rt.obstacle(l, tr_rect(r, dx, dy, mirror), rn(n), extra=ex)
    for (n, c, r) in blk.terms:
        rt.terminal(rn(n), c, tr_rect(r, dx, dy, mirror))
    if hasattr(blk, 'mim'):
        pl = tr_rect(blk.mim['plate'], dx, dy, mirror)
        rt.block_all(pl, layers=(0, 1))
        rt.obstacle(2, pl, None, extra=0.9)
    for pr in getattr(blk, 'plates', []):
        pl = tr_rect(pr, dx, dy, mirror)
        rt.block_all(pl, layers=(0, 1))
        rt.obstacle(2, pl, None, extra=0.9)


def route_cell(ly, name, parts, extern, order, margin=3, power=('vss', 'vdd_cmp'), pre=None, power_first=False):
    """parts: [(blk, dx, dy[, mirror[, rename]])] (integer offsets; mirror = about the vertical axis x = 0 of the block, i.e. x -> dx - x; rename: callable local net -> net of this cell).
    extern: {net: (x, y)} integer positions of the Metal3 exposure pads (each also a router terminal).  order: routing order (other nets after, power last).
    Returns the Block of the routed cell: terms = exposure pads (Metal3), fixed = the routed wires (layer index, rect, net).  `pre(rt)` may add obstacles."""
    B = a.Block(ly, name)
    P = []
    for t in parts:
        blk, dx, dy = t[0], t[1], t[2]
        mir = t[3] if len(t) > 3 else False
        ren = t[4] if len(t) > 4 else None
        P.append((blk, dx, dy, mir, ren))
        if mir:
            k.put(B.cell, blk.cell, dx, dy, rot=180, mirror=True)
        else:
            k.put(B.cell, blk.cell, dx, dy)
        bb = tr_rect(blk.bbox, dx, dy, mir)
        B.grow(*bb)
    for (n, (x, y)) in extern.items():
        B.grow(x - 1, y - 1, x + 1, y + 1)
    bx = B.bbox
    X0, Y0 = math.floor(bx[0]) - margin, math.floor(bx[1]) - margin
    X1, Y1 = math.ceil(bx[2]) + margin, math.ceil(bx[3]) + margin
    rt = RT.Router(float(X0), float(Y0), float(X1), float(Y1))
    for (blk, dx, dy, mir, ren) in P:
        add_part_to_router(rt, blk, dx, dy, mir, ren)
    for n, (x, y) in extern.items():
        rt.terminal(n, 'metal3', a.pad_rect(x, y, 0.5))
    if pre:
        pre(rt)
    rt.reserve()
    nets = list(rt.terms.keys())
    pw = [n for n in power if n in nets]
    seq = [n for n in order if n in nets] + [n for n in nets if n not in order and n not in pw] + pw
    if power_first:
        seq = pw + [n for n in seq if n not in pw]
    bad = []
    for n in seq:
        if not rt.route_net(n):
            bad.append(n)
    emit(rt, B.cell)
    for n, (x, y) in extern.items():
        B.rect('metal3', x - 0.25, y - 0.25, x + 0.25, y + 0.25)
        B.term(n, 'metal3', a.pad_rect(x, y, 0.5))
    sh = rt.shapes()
    for net, d in sh.items():
        for (lname, r) in d['wires']:
            B.fixed_shape(LAYER_IDX[lname], r, net, 0.0)
    B.plates = []
    for (blk, dx, dy, mir, ren) in P:                       # the fixed shapes (stubs, pads) and MIM plates of the parts stay obstacles for the next level
        for (l, r, n, ex) in blk.fixed:
            B.fixed_shape(l, tr_rect(r, dx, dy, mir), (ren(n) if ren else n), ex)
        if hasattr(blk, 'mim'):
            B.plates.append(blk.mim['plate'] if not (dx or dy or mir) else tr_rect(blk.mim['plate'], dx, dy, mir))
        for pr in getattr(blk, 'plates', []):
            B.plates.append(tr_rect(pr, dx, dy, mir))
    B.failed = bad
    B.nfail = rt.failed
    B.size = (B.bbox[2] - B.bbox[0], B.bbox[3] - B.bbox[1])
    B.rt = rt
    return B


def mim_unit_block(ly, name, w, top, bot, yb=1, yt=4):
    """MIM piece w x w um, top plate lower-left corner at the origin.  Bottom plate: Metal4 tab east + 1.2 um pad centred (px, yb); top plate: Metal5 strap east + Via4 + Metal4 pad centred (px, yt);
    px = ceil(w + 2.86) (pad >= 2.26 um from the top plate edge: MIMTM.1, FLOW.md section 5).  Terminals = the two Metal4 pads."""
    B = a.Block(ly, name)
    a.mim_cap(B.cell, 0.0, 0.0, w, w, top, bot)
    px = int(math.ceil(w + 2.86))
    B.grow(-0.6, -0.6, w + 0.6, w + 0.6)
    B.rect('metal4', w + 0.5, yb - 0.5, px + 0.1, yb + 0.5)
    B.rect('metal4', px - 0.6, yb - 0.6, px + 0.6, yb + 0.6)
    B.term(bot, 'metal4', (px - 0.6, yb - 0.6, px + 0.6, yb + 0.6))
    B.fixed_shape(a.M4, (w + 0.5, yb - 0.5, px + 0.1, yb + 0.5), bot, 1.0)
    B.fixed_shape(a.M4, (px - 0.6, yb - 0.6, px + 0.6, yb + 0.6), bot, 1.0)
    B.rect('metal5', w - 0.01, yt - 0.5, px + 0.6, yt + 0.5)
    B.rect('metal4', px - 0.6, yt - 0.6, px + 0.6, yt + 0.6)
    a.cuts(B.cell, 'via4', px - 0.6, yt - 0.6, px + 0.6, yt + 0.6, inset=0.3)
    B.rect('metal5', px - 0.6, yt - 0.6, px + 0.6, yt + 0.6)
    B.term(top, 'metal4', (px - 0.6, yt - 0.6, px + 0.6, yt + 0.6))
    B.fixed_shape(a.M4, (px - 0.6, yt - 0.6, px + 0.6, yt + 0.6), top, 0.0)
    B.mim = dict(w=w, plate=(-0.6, -0.6, w + 0.6, w + 0.6), top=(0.0, 0.0, w, w), bot=bot, topnet=top)
    B.px = px
    B.size = (px + 0.6 + 0.6, w + 1.2)
    return B
