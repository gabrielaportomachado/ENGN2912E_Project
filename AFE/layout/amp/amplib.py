"""amplib.py (L2a): drawing helpers on top of AFE/layout/scripts/kpdk.py for the amplifier cell generators of AFE/layout/amp/.
Run only inside KLayout through   bash AFE/layout/scripts/kl.sh <script.py> ...   (the scripts import this file: kl_launch.py puts the script directory on sys.path).

Dev       a PDK transistor pcell (nfet / pfet / nfet_06v0_nvt) placed at a position; the terminal rectangles of the pcell (S/D Metal1 strips sorted by x, gate pads, bulk ties) are
          found from the pcell's own shapes (contact -> comp / poly -> implant), so no number of the PDK code is copied here.
mim       a MIM capacitor (cap_mim pcell, option B, Metal4 bottom / Metal5 top plate) with explicit plate shapes
All lengths in um; every coordinate is snapped to the 5 nm grid by kpdk.u().
"""
import os
import pya
import kpdk as k

GRID = 0.005
KNOB = dict(rg=2.5, gg=2.5, cg=3.0)          # L2a rework: ring gaps (um) of dev_block / group_block / compose, set by mk_amp_ch.py (rg= gg= cg=)


def snap(v):
    return round(v / GRID) * GRID


def L(ly, name):
    return k.li(ly, name)


_cache = {}
SNAP_LAYERS = ('metal1', 'metal2')          # FINDING (L2a): the PDK transistor pcells draw Metal1 gate pads with 1 nm coordinates (e.g. y = 2.289 um): DRC metal1_OFFGRID


MIM_NEAREST = ('fusetop', 'cap_mk', 'mim_l_mk', 'metal4', 'metal5')          # FINDING (L2a): the cap_mim pcell rounds sizes to 2 nm (44.595 -> 44.596) and places the Via4 sea on a 1 nm grid
MIM_SHIFT = ('via4',)


def mim_snapped_copy(ly, pc, name):
    g = int(round(GRID / ly.dbu))
    c = ly.create_cell('%s__%d' % (name, len(_cache)))
    near = {k.li(ly, n) for n in MIM_NEAREST}
    shift = {k.li(ly, n) for n in MIM_SHIFT}

    def rnd(v):
        return int(round(v / g)) * g
    for li in ly.layer_indexes():
        reg = pya.Region(pc.begin_shapes_rec(li))
        if reg.is_empty():
            continue
        if li in near or li in shift:
            out = pya.Region()
            for p in reg.merged().each() if li in near else reg.each():
                b = p.bbox()
                if li in near:
                    out.insert(pya.Box(rnd(b.left), rnd(b.bottom), rnd(b.right), rnd(b.top)))
                else:
                    out.insert(pya.Box(rnd(b.left), rnd(b.bottom), rnd(b.left) + b.width(), rnd(b.bottom) + b.height()))
            reg = out
        c.shapes(li).insert(reg)
    return c


def snapped_copy(ly, pc, name):
    """a plain cell with all shapes of the pcell cell (recursively flattened); the boxes of SNAP_LAYERS are grown outwards to the 5 nm grid (never shrunk)"""
    g = int(round(GRID / ly.dbu))
    c = ly.create_cell('%s__%d' % (name, len(_cache)))
    snap_idx = {k.li(ly, n) for n in SNAP_LAYERS}
    for li in ly.layer_indexes():
        reg = pya.Region(pc.begin_shapes_rec(li))
        if reg.is_empty():
            continue
        if li in snap_idx:
            out = pya.Region()
            for p in reg.merged().each():
                b = p.bbox()
                if p.is_box():
                    out.insert(pya.Box((b.left // g) * g, (b.bottom // g) * g, -((-b.right) // g) * g, -((-b.top) // g) * g))
                else:
                    out.insert(p.sized(0))
            reg = out.merged()
        c.shapes(li).insert(reg)
    return c


def region(ly, cell, layer):
    return pya.Region(cell.begin_shapes_rec(k.li(ly, layer)))


class PcellInfo:
    """terminal rectangles (local um coordinates) of one pcell variant"""

    def __init__(self, ly, name, params):
        self.name, self.params = name, params
        self.cell = snapped_copy(ly, k.pcell(ly, name, **params), name)
        c = self.cell
        dbu = ly.dbu
        m1 = region(ly, c, 'metal1').merged()
        poly = region(ly, c, 'poly2')
        comp = region(ly, c, 'comp')
        con = region(ly, c, 'contact')
        ppl, npl = region(ly, c, 'pplus'), region(ly, c, 'nplus')
        sd_imp = ppl if name == 'pfet' else npl
        tie_imp = npl if name == 'pfet' else ppl
        self.sd, self.g, self.tie = [], [], []
        for p in m1.each():
            r = pya.Region(p)
            cc = con & r
            if cc.is_empty():
                continue
            b = p.bbox()
            box = (b.left * dbu, b.bottom * dbu, b.right * dbu, b.top * dbu)
            if not (cc & poly).is_empty() and (cc & comp).is_empty():
                self.g.append(box)
            elif not (cc & comp).is_empty():
                # implant under the contacts decides: S/D or well / substrate tie
                if not (cc & sd_imp).is_empty() and (cc & tie_imp).is_empty():
                    self.sd.append(box)
                elif not (cc & tie_imp).is_empty():
                    self.tie.append(box)
                else:
                    self.sd.append(box)
        self.sd.sort()
        self.g.sort()
        self.tie.sort()
        bb = c.dbbox()
        self.bbox = (bb.left, bb.bottom, bb.right, bb.top)
        cb = comp.bbox()
        self.comp_bbox = (cb.left * dbu, cb.bottom * dbu, cb.right * dbu, cb.top * dbu)
        nb = region(ly, c, 'nwell').bbox()
        self.nw_bbox = None if region(ly, c, 'nwell').is_empty() else (nb.left * dbu, nb.bottom * dbu, nb.right * dbu, nb.top * dbu)


def info(ly, name, **params):
    key = (id(ly), name, tuple(sorted(params.items())))
    if key not in _cache:
        _cache[key] = PcellInfo(ly, name, params)
    return _cache[key]


class Dev:
    """a placed pcell. mirror = mirrored about the vertical axis through x (MY). Terminal lists are in absolute um."""

    def __init__(self, cell, name, x, y, mirror=False, **params):
        ly = cell.layout()
        self.ly = ly
        self.info = info(ly, name, **params)
        self.name, self.params, self.x, self.y, self.mirror = name, params, x, y, mirror
        # kpdk.put uses Trans(rot, mirror, x, y): mirror = mirror about the x axis (M0) then rotation; we want MY = R180 + M0
        t = pya.Trans(2 if mirror else 0, bool(mirror), k.u(x, ly), k.u(y, ly))
        self.trans = t
        cell.insert(pya.CellInstArray(self.info.cell.cell_index(), t))
        self.sd = [self._t(b) for b in self.info.sd]
        self.g = [self._t(b) for b in self.info.g]
        self.tie = [self._t(b) for b in self.info.tie]
        if mirror:
            self.sd.sort()
            self.g.sort()
            self.tie.sort()
        self.comp = self._t(self.info.comp_bbox)
        self.nw = self._t(self.info.nw_bbox) if self.info.nw_bbox else None
        bb = self.info.bbox
        self.bbox = self._t(bb)

    def _t(self, b):
        ly = self.ly
        bx = pya.Box(k.u(b[0], ly), k.u(b[1], ly), k.u(b[2], ly), k.u(b[3], ly))
        r = self.trans.trans(bx)
        return (r.left * ly.dbu, r.bottom * ly.dbu, r.right * ly.dbu, r.top * ly.dbu)


def cx(b):
    return (b[0] + b[2]) / 2.0


def cy(b):
    return (b[1] + b[3]) / 2.0


def m1(cell, b):
    k.rect(cell, 'metal1', *b)


def link(cell, layer, x1, y1, x2, y2, w, via_to=None):
    """L-shaped Manhattan wire of width w on `layer` from (x1,y1) to (x2,y2): first along x, then along y (corner square included)"""
    h = w / 2.0
    k.rect(cell, layer, min(x1, x2) - h, y1 - h, max(x1, x2) + h, y1 + h)
    k.rect(cell, layer, x2 - h, min(y1, y2) - h, x2 + h, max(y1, y2) + h)


def mim_cap(cell, x, y, w, l, top, bot, bot_label=None):
    """MIM option B (Metal4 bottom / Metal5 top) of w x l um, lower-left corner of the TOP plate at (x, y).  Returns dict of the plate rectangles.
    The pcell draws the capacitor with the top plate on Metal5 / FuseTop and the bottom plate on Metal4; both pcell shapes are used as they are."""
    ly = cell.layout()
    inf = info_mim(ly, w, l)
    k.put(cell, inf.cell, x - inf.tp[0], y - inf.tp[1])
    return dict(top=(x, y, x + w, y + l), bot=(x + inf.bp[0] - inf.tp[0], y + inf.bp[1] - inf.tp[1], x + inf.bp[2] - inf.tp[0], y + inf.bp[3] - inf.tp[1]))


class MimInfo:
    pass


def info_mim(ly, w, l):
    key = (id(ly), 'mim', w, l)
    if key not in _cache:
        m = MimInfo()
        m.cell = mim_snapped_copy(ly, k.pcell(ly, 'cap_mim', mim_option='MIM-B', metal_level='M5', wc=w, lc=l), 'cap_mim')
        dbu = ly.dbu
        ft = region(ly, m.cell, 'fusetop').bbox()
        m4 = region(ly, m.cell, 'metal4').bbox()
        m5 = region(ly, m.cell, 'metal5').bbox()
        m.tp = (ft.left * dbu, ft.bottom * dbu, ft.right * dbu, ft.top * dbu)
        m.bp = (m4.left * dbu, m4.bottom * dbu, m4.right * dbu, m4.top * dbu)
        m.m5 = (m5.left * dbu, m5.bottom * dbu, m5.right * dbu, m5.top * dbu)
        _cache[key] = m
    return _cache[key]


def cuts(cell, via, x1, y1, x2, y2, inset=0.1):
    """like kpdk.vias but tolerant of float noise (0.22 + 2 * 0.1 boxes) and snapped to the 5 nm grid; returns the number of cuts"""
    size, sp = k.CUT[via]
    w, h = x2 - x1 - 2 * inset + 1e-6, y2 - y1 - 2 * inset + 1e-6
    nx, ny = int((w + sp) // (size + sp)), int((h + sp) // (size + sp))
    if nx < 1 or ny < 1:
        raise RuntimeError('cuts: the box %.3f x %.3f um is too small for one %s cut' % (x2 - x1, y2 - y1, via))
    ox = snap(x1 + inset + (w - (nx * size + (nx - 1) * sp)) / 2.0)
    oy = snap(y1 + inset + (h - (ny * size + (ny - 1) * sp)) / 2.0)
    for i in range(nx):
        for j in range(ny):
            k.rect(cell, via, ox + i * (size + sp), oy + j * (size + sp), ox + i * (size + sp) + size, oy + j * (size + sp) + size)
    return nx * ny


def ring(cell, x1, y1, x2, y2, kind='p', w=0.42, lab=None, m1w=None):
    """substrate (kind 'p') or n-well (kind 'n') tie ring with the outer boundary x1..x2 / y1..y2: comp ring + implant + contacts + Metal1 ring.  The n-well is NOT drawn here."""
    imp = 'pplus' if kind == 'p' else 'nplus'
    sides = ((x1, y1, x1 + w, y2), (x2 - w, y1, x2, y2), (x1 + w, y1, x2 - w, y1 + w), (x1 + w, y2 - w, x2 - w, y2))
    for (ax1, ay1, ax2, ay2) in sides:
        k.rect(cell, 'comp', ax1, ay1, ax2, ay2)
        k.rect(cell, 'metal1', ax1, ay1, ax2, ay2)
        cuts(cell, 'contact', ax1, ay1, ax2, ay2, inset=(w - 0.22) / 2.0)
    e = 0.17
    k.rect(cell, imp, x1 - e, y1 - e, x2 + e, y1 + w + e)
    k.rect(cell, imp, x1 - e, y2 - w - e, x2 + e, y2 + e)
    k.rect(cell, imp, x1 - e, y1 - e, x1 + w + e, y2 + e)
    k.rect(cell, imp, x2 - w - e, y1 - e, x2 + e, y2 + e)
    if lab:
        k.label(cell, 'metal1', lab, x1 + w / 2, (y1 + y2) / 2)


# =====================================================================================================================================================================
# Blocks: a sub-cell with its own terminals (for the router) and fixed Metal2..4 shapes (obstacles)
# =====================================================================================================================================================================
def rint(v):
    return int(round(v))


class Block:
    """a sub-cell drawn at a local origin.  terms: (net, layer code, rect) for the router; fixed: (layer index 0..2, rect, net) Metal2..4 shapes; size = (w, h) of the outline
    (including its ring); lab: (layer, text, x, y) labels written only in debug mode"""

    def __init__(self, ly, name):
        self.ly = ly
        self.cell = ly.create_cell(name)
        self.name = name
        self.terms, self.fixed, self.lab = [], [], []
        self.bbox = [1e9, 1e9, -1e9, -1e9]

    def grow(self, x1, y1, x2, y2):
        b = self.bbox
        b[0], b[1], b[2], b[3] = min(b[0], x1), min(b[1], y1), max(b[2], x2), max(b[3], y2)

    def rect(self, layer, x1, y1, x2, y2):
        k.rect(self.cell, layer, x1, y1, x2, y2)
        self.grow(min(x1, x2), min(y1, y2), max(x1, x2), max(y1, y2))

    def term(self, net, code, rect):
        self.terms.append((net, code, tuple(rect)))

    def fixed_shape(self, layer_idx, rect, net, extra=0.0):
        self.fixed.append((layer_idx, tuple(rect), net, extra))


M2, M3, M4 = 0, 1, 2


def dev_block(ly, name, kind, w, l, nf, x_origin_hint=0.0, s_net='vss', d_nets=None, g_net=None, bulk_net=None, ring=True, dummies=False, params=None, ring_gap=None, wide_ring=False, multi=False):
    if ring_gap is None:
        ring_gap = KNOB['rg']
    """one multi-finger transistor array (nf >= 2) as a block.
    kind 'nfet' | 'pfet';  d_nets: a list with one net per drain strip (strips 1, 3, 5 ... of the pcell) or a single net name.  Sources = strips 0, 2, 4 ... all on s_net.
    Drawing: S rail Metal1 under the comp (strips extended down), gates joined by a Metal1 bus above the comp (landing pad at its left end), drains by Via1 + Metal2 stubs to ONE
    Metal2 rail above the bus (all drains must be the same net: the generator makes one block per drain net).  Ring: P+ (nfet) / N+ in an n-well (pfet) around everything,
    centre line on integer um so that its Metal1 (1 um wide) has a router node on it."""
    prm = dict(volt='3.3V', bulk='None', w_gate=w, l_gate=l, nf=nf, gate_con_pos='top')
    if params:
        prm.update(params)
    B = Block(ly, name)
    probe = info(ly, kind, **prm)
    # alignment: the gate-bus centre line on an integer y
    gy_c = (probe.g[0][1] + probe.g[0][3]) / 2.0
    oy = rint(gy_c) - gy_c + 0.0
    ox = 0.0
    D = Dev(B.cell, kind, ox, oy, **prm)
    sd, gp, comp = D.sd, D.g, D.comp
    cl, cb, cr, ct = comp
    S = sd[0::2]
    Dn = sd[1::2]
    nd = len(Dn)
    if isinstance(d_nets, str):
        d_nets = [d_nets] * nd
    # multi=True (L2a rework, tail-group merge): every drain strip may have its OWN net; each stub then ends in its own Metal2 pad on an integer x (no common rail)
    assert len(d_nets) == nd and (multi or len(set(d_nets)) == 1), 'dev_block: one drain net per block (multi=True for distinct nets)'
    dnet = d_nets[0]
    # S rail
    rail_y1, rail_y2 = cb - 2.0, cb - 0.5
    for s in S:
        B.rect('metal1', s[0], rail_y1, s[2], s[1] + 0.02)
    rx1, rx2 = min(S[0][0], (S[0][0] + S[-1][2]) / 2.0 - 1.0), max(S[-1][2], (S[0][0] + S[-1][2]) / 2.0 + 1.0)
    B.rect('metal1', rx1, rail_y1, rx2, rail_y2)
    B.term(s_net, 'metal1', (rx1, rail_y1, rx2, rail_y2))
    # gate bus
    gx1 = min(g[0] for g in gp)
    gx2 = max(g[2] for g in gp)
    gy1, gy2 = gp[0][1], gp[0][3]
    bc = rint((gy1 + gy2) / 2.0)
    B.rect('metal1', gx1, gy1, gx2, gy2)
    lx = rint(min(S[0][0], gx1) - 2.0)                    # landing pad centre x (integer)
    B.rect('metal1', lx - 0.5, bc - 0.5, lx + 0.5, bc + 0.5)
    B.rect('metal1', lx, gy1, gx1 + 0.01, gy2)
    B.term(g_net, 'metal1', (lx - 0.5, bc - 0.5, lx + 0.5, bc + 0.5))
    # drains: Via1 pad at the strip top, Metal2 stub up to the rail
    ry = bc + 1.0
    first = True
    for di, d in enumerate(Dn):
        xc = (d[0] + d[2]) / 2.0
        yv = d[3] - 0.45
        B.rect('metal1', xc - 0.25, yv - 0.25, xc + 0.25, yv + 0.25)
        k.rect(B.cell, 'via1', xc - 0.13, yv - 0.13, xc + 0.13, yv + 0.13)
        B.rect('metal2', xc - 0.25, yv - 0.25, xc + 0.25, ry + 0.25)
        B.fixed_shape(M2, (xc - 0.25, yv - 0.25, xc + 0.25, ry + 0.25), d_nets[di] if multi else dnet)
        if multi:
            xi = rint(xc)
            B.rect('metal2', min(xc, xi) - 0.25, ry - 0.25, max(xc, xi) + 0.25, ry + 0.25)
            B.fixed_shape(M2, (min(xc, xi) - 0.25, ry - 0.25, max(xc, xi) + 0.25, ry + 0.25), d_nets[di])
            B.term(d_nets[di], 'metal2', (xi - 0.25, ry - 0.25, xi + 0.25, ry + 0.25))
    if not multi:
        xa = (Dn[0][0] + Dn[0][2]) / 2.0 - 0.25
        xb = (Dn[-1][0] + Dn[-1][2]) / 2.0 + 0.25
        if xb - xa < 3.0:
            xm = (xa + xb) / 2.0
            xa, xb = xm - 1.5, xm + 1.5
        B.rect('metal2', xa, ry - 0.25, xb, ry + 0.25)
        B.fixed_shape(M2, (xa, ry - 0.25, xb, ry + 0.25), dnet)
        B.term(dnet, 'metal2', (xa, ry - 0.25, xb, ry + 0.25))
    else:
        xb = max(d[2] for d in Dn)
    # dummy poly lines at both ends (poly only, over field oxide: not devices)
    if dummies:
        pl = min(D.info.params.get('l_gate', l), 2.0)
        for side in (-1, 1):
            if side < 0:
                px2 = cl - 0.30
                px1 = px2 - pl
            else:
                px1 = cr + 0.30
                px2 = px1 + pl
            B.rect('poly2', snap(px1), snap(cb - 0.3), snap(px2), snap(ct + 0.3))
    # ring
    x_l = rint(min(lx, S[0][0]) - ring_gap)
    x_r = rint(max(cr, xb) + ring_gap)
    y_b = rint(rail_y1 - 1.5)
    y_t = rint(ry + 0.25 + 1.5 + 0.5)
    if ring:
        kind_r = 'p' if kind == 'nfet' else 'n'
        ring_cl(B, x_l, y_b, x_r, y_t, kind_r, bulk_net)
        if kind == 'pfet':
            B.rect('nwell', x_l - 0.5 - 0.8, y_b - 0.5 - 0.8, x_r + 0.5 + 0.8, y_t + 0.5 + 0.8)
    B.dev = D
    B.comp_box = D.comp
    B.size = (x_r - x_l, y_t - y_b)
    return B


def ring_cl(B, x1, y1, x2, y2, kind, net, w=0.42, mw=1.0):
    """tie ring whose centre lines are the integer rectangle x1..x2 / y1..y2: comp ring w wide, Metal1 ring mw wide (one router terminal piece per side), implant"""
    imp = 'pplus' if kind == 'p' else 'nplus'
    h = w / 2.0
    sides = ((x1 - h, y1 - h, x1 + h, y2 + h), (x2 - h, y1 - h, x2 + h, y2 + h), (x1 + h, y1 - h, x2 - h, y1 + h), (x1 + h, y2 - h, x2 - h, y2 + h))
    for (ax1, ay1, ax2, ay2) in sides:
        B.rect('comp', ax1, ay1, ax2, ay2)
    # contacts: along each centre line
    for (ax1, ay1, ax2, ay2) in ((x1 - h, y1, x1 + h, y2), (x2 - h, y1, x2 + h, y2)):
        cuts(B.cell, 'contact', ax1, ay1 + 0.15, ax2, ay2 - 0.15, inset=(w - 0.22) / 2.0)
    for (ax1, ay1, ax2, ay2) in ((x1, y1 - h, x2, y1 + h), (x1, y2 - h, x2, y2 + h)):
        cuts(B.cell, 'contact', ax1 + 0.15, ay1, ax2 - 0.15, ay2, inset=(w - 0.22) / 2.0)
    mh = mw / 2.0
    for (ax1, ay1, ax2, ay2) in ((x1 - mh, y1 - mh, x1 + mh, y2 + mh), (x2 - mh, y1 - mh, x2 + mh, y2 + mh), (x1 + mh, y1 - mh, x2 - mh, y1 + mh), (x1 + mh, y2 - mh, x2 - mh, y2 + mh)):
        B.rect('metal1', ax1, ay1, ax2, ay2)
    e = 0.16
    B.rect(imp, x1 - h - e, y1 - h - e, x2 + h + e, y1 + h + e)
    B.rect(imp, x1 - h - e, y2 - h - e, x2 + h + e, y2 + h + e)
    B.rect(imp, x1 - h - e, y1 - h - e, x1 + h + e, y2 + h + e)
    B.rect(imp, x2 - h - e, y1 - h - e, x2 + h + e, y2 + h + e)
    # terminal: the longest Metal1 side (the ring is one connected piece)
    if (x2 - x1) >= (y2 - y1):
        B.term(net, 'metal1', (x1, y1 - mh, x2, y1 + mh))
    else:
        B.term(net, 'metal1', (x1 - mh, y1, x1 + mh, y2))


# =====================================================================================================================================================================
# single-finger tiles, groups with a common ring, pseudo-resistor pairs, MIM blocks
# =====================================================================================================================================================================
import math


def pcname(kind):
    return 'nfet_06v0_nvt' if kind == 'nvt' else kind


def tile_params(kind, w, l):
    if kind == 'nvt':
        return dict(bulk='None', w_gate=w, l_gate=l, nf=1, gate_con_pos='top')
    return dict(volt='3.3V', bulk='None', w_gate=w, l_gate=l, nf=1, gate_con_pos='top')


def pad_rect(x, y, h=0.25):
    return (x - h, y - h, x + h, y + h)


def add_tile(B, kind, w, l, x, y, s, d, g, extra=None):
    """one single-finger transistor with its three Metal1 landing pads (0.5 um squares on integer coordinates) above it: source pad and drain pad in row 1, gate pad in row 2.
    The strips of the pcell (0.38 um wide) are extended by Metal1 stubs; terminals (s, d, g) are the pads."""
    prm = tile_params(kind, w, l)
    if extra:
        prm.update(extra)
    D = Dev(B.cell, pcname(kind), x, y, **prm)
    B.grow(*D.bbox)
    S, Dd = D.sd[0], D.sd[1]
    gp = max(D.g, key=lambda b: b[3])
    ry1 = math.ceil(max(gp[3], S[3], Dd[3]) + 0.5 - 1e-9)
    ry2 = ry1 + 1
    sc, dc = (S[0] + S[2]) / 2.0, (Dd[0] + Dd[2]) / 2.0
    xs = math.floor(sc - 0.3 - 1e-9)
    xd = math.ceil(dc + 0.3 - 1e-9)
    # source
    B.rect('metal1', S[0], S[3] - 0.02, S[2], ry1 + 0.25)
    B.rect('metal1', min(S[0], xs - 0.25), ry1 - 0.25, S[2], ry1 + 0.25)
    B.term(s, 'metal1', pad_rect(xs, ry1))
    # drain
    B.rect('metal1', Dd[0], Dd[3] - 0.02, Dd[2], ry1 + 0.25)
    B.rect('metal1', Dd[0], ry1 - 0.25, max(Dd[2], xd + 0.25), ry1 + 0.25)
    B.term(d, 'metal1', pad_rect(xd, ry1))
    # gate
    wide = (gp[2] - gp[0]) >= 1.3
    if wide:
        xg = math.ceil(gp[0] + 0.5 - 1e-9)
        B.rect('metal1', xg - 0.25, gp[3] - 0.02, xg + 0.25, ry2 + 0.25)
    else:
        xg = round((gp[0] + gp[2]) / 2.0)
        B.rect('metal1', gp[0], gp[3] - 0.02, gp[2], ry2 + 0.25)
        B.rect('metal1', min(gp[0], xg - 0.25), ry2 - 0.25, max(gp[2], xg + 0.25), ry2 + 0.25)
    B.term(g, 'metal1', pad_rect(xg, ry2))
    B.grow(xs - 0.25, y, xd + 0.25, ry2 + 0.25)
    return D


def group_block(ly, name, tiles, ring_kind=None, ring_net=None, gap=None, extra_blocks=None):
    if gap is None:
        gap = KNOB['gg']
    """tiles: list of dict(kind, w, l, x, y, s, d, g[, extra]); one ring (p for nfet / nvt, n for pfet) around all of them; for pfet an n-well around the ring"""
    B = Block(ly, name)
    for t in tiles:
        add_tile(B, **t)
    if ring_kind:
        x1, y1, x2, y2 = B.bbox
        xl, yb = math.floor(x1 - gap), math.floor(y1 - gap)
        xr, yt = math.ceil(x2 + gap), math.ceil(y2 + gap)
        ring_cl(B, xl, yb, xr, yt, ring_kind, ring_net)
        if ring_kind == 'n':
            B.rect('nwell', xl - 1.3, yb - 1.3, xr + 1.3, yt + 1.3)
        B.size = (xr - xl, yt - yb)
    else:
        B.size = (B.bbox[2] - B.bbox[0], B.bbox[3] - B.bbox[1])
    return B


def pr_block(ly, name, s1, s2, mnet, gnet):
    """two pseudo-resistor transistors in series (pfet_03v3 0.22u / 0.5u, drains on mnet, gates on gnet).  Each has its OWN n-well, tied to its source net (s1 / s2) by an N+ tie of
    the minimum size (0.42 x 0.5 um comp): the junction area on the summing node is the minimum the rules allow (SPEC.md 3.2 item 4); both drawn identically."""
    B = Block(ly, name)
    prm = dict(volt='3.3V', bulk='None', w_gate=0.22, l_gate=0.5, nf=1, con_bet_fin=0)
    for sn, x0 in ((s1, 0.0), (s2, 7.0)):
        probe = info(ly, 'pfet', **prm)
        yc0 = (probe.sd[0][1] + probe.sd[0][3]) / 2.0
        oy = 0.0
        D = Dev(B.cell, 'pfet', x0, oy, **prm)
        B.grow(*D.bbox)
        S, Dd = D.sd[0], D.sd[1]
        gb = min(D.g, key=lambda b: b[1])            # the bottom gate pad
        yc = (S[1] + S[3]) / 2.0
        # tie
        tx1, tx2 = x0 + 1.68, x0 + 2.10
        ty1, ty2 = snap(yc - 0.25), snap(yc + 0.25)
        B.rect('comp', tx1, ty1, tx2, ty2)
        B.rect('nplus', tx1 - 0.16, ty1 - 0.16, tx2 + 0.16, ty2 + 0.16)
        cuts(B.cell, 'contact', tx1, ty1, tx2, ty2, inset=0.1)
        B.rect('metal1', tx1, ty1, tx2, ty2)
        nw = D.nw
        B.rect('nwell', nw[0] + 0.8, nw[1], tx2 + 0.6, nw[3])
        # source -> link over the device -> tie
        ty = math.ceil(max(D.g[0][3], D.g[1][3]) + 0.5 + 0.25 - 1e-9)
        B.rect('metal1', S[0], S[3] - 0.02, S[2], ty + 0.25)
        B.rect('metal1', tx1, ty2 - 0.02, tx2, ty + 0.25)
        B.rect('metal1', S[0], ty - 0.25, tx2, ty + 0.25)
        B.term(sn, 'metal1', (S[0], ty - 0.25, tx2, ty + 0.25))
        # drain and gate pads below the device (row yd)
        yd = math.floor(gb[1] - 0.5 - 1e-9)
        B.rect('metal1', Dd[0], yd - 0.25, Dd[2], Dd[1] + 0.02)
        B.rect('metal1', Dd[0], yd - 0.25, x0 + 2.25, yd + 0.25)
        B.term(mnet, 'metal1', pad_rect(x0 + 2, yd))
        B.rect('metal1', gb[0], yd - 0.25, gb[2], gb[1] + 0.02)
        B.rect('metal1', x0 - 0.25, yd - 0.25, gb[2], yd + 0.25)
        B.term(gnet, 'metal1', pad_rect(x0, yd))
        B.grow(x0 - 0.25, yd - 0.25, x0 + 2.7, ty + 0.25)
    B.size = (B.bbox[2] - B.bbox[0], B.bbox[3] - B.bbox[1])
    return B


def mim_block(ly, name, w, top, bot, tab_y_top=None, tab_y_bot=None):
    """a MIM piece of w x w um at the local origin (top plate lower-left corner) with both plates brought out EAST: the top plate through a Metal5 extension + Via4 to a 2 x 2 um
    Metal4 pad 3 um from the plate (MIMTM.1: unrelated Metal4 >= 1.8 um from the top plate), the bottom plate through a Metal4 tab ending in a 2 x 2 um pad.
    Terminals are the two Metal4 pads (router layer Metal4)."""
    B = Block(ly, name)
    mc = mim_cap(B.cell, 0.0, 0.0, w, w, top, bot)
    B.grow(-0.6, -0.6, w + 0.6, w + 0.6)
    px = math.ceil(w + 2.3)
    yb = rint(min(1.0, w / 4.0)) if tab_y_bot is None else tab_y_bot
    yt = rint(max(w - 3.0, w * 0.6)) if tab_y_top is None else tab_y_top
    # bottom plate
    B.rect('metal4', w - 0.1, yb + 0.4, px + 1.0, yb + 1.6)
    B.rect('metal4', px, yb, px + 2.0, yb + 2.0)
    B.term(bot, 'metal4', (px, yb, px + 2.0, yb + 2.0))
    B.fixed_shape(M4, (w - 0.1, yb + 0.4, px + 1.0, yb + 1.6), bot, 1.0)                  # MIMTM.1: no other Metal4 within 1.2 um of the bottom plate metal (plate + tab + pad)
    B.fixed_shape(M4, (px, yb, px + 2.0, yb + 2.0), bot, 1.0)
    # top plate
    B.rect('metal5', w - 1.5, yt + 0.4, px + 1.0, yt + 1.6)
    B.rect('metal5', px, yt, px + 2.0, yt + 2.0)
    B.rect('metal4', px, yt, px + 2.0, yt + 2.0)
    cuts(B.cell, 'via4', px, yt, px + 2.0, yt + 2.0, inset=0.3)
    B.term(top, 'metal4', (px, yt, px + 2.0, yt + 2.0))
    B.fixed_shape(M4, (px, yt, px + 2.0, yt + 2.0), top, 0.0)
    B.mim = dict(w=w, plate=(-0.6, -0.6, w + 0.6, w + 0.6), top=(0.0, 0.0, w, w), bot=bot, topnet=top)
    B.size = (px + 2.0 + 0.6, w + 1.2)
    return B


# =====================================================================================================================================================================
# composition, standard cell block, Cin block
# =====================================================================================================================================================================
def compose(ly, name, parts, ring_kind=None, ring_net=None, gap=None, nwell=None, dummy_l=None, dummy_groups=None):
    if gap is None:
        gap = KNOB['cg']
    """parent block that instantiates `parts` = [(block, dx, dy)] (integer offsets); terminals / fixed shapes are copied with the offset; optional ring around all of them"""
    B = Block(ly, name)
    for (P, dx, dy) in parts:
        k.put(B.cell, P.cell, dx, dy)
        for (n, c, r) in P.terms:
            B.term(n, c, (r[0] + dx, r[1] + dy, r[2] + dx, r[3] + dy))
        for (l, r, n, ex) in P.fixed:
            B.fixed_shape(l, (r[0] + dx, r[1] + dy, r[2] + dx, r[3] + dy), n, ex)
        B.grow(P.bbox[0] + dx, P.bbox[1] + dy, P.bbox[2] + dx, P.bbox[3] + dy)
    if dummy_l:
        # poly-only dummy lines (not devices) at both outer ends of every group of parts (dummy_groups = list of lists of part indices; default: all parts)
        for grp in (dummy_groups or [list(range(len(parts)))]):
            cx1 = min(parts[i][0].comp_box[0] + parts[i][1] for i in grp)
            cx2 = max(parts[i][0].comp_box[2] + parts[i][1] for i in grp)
            cy1 = min(parts[i][0].comp_box[1] + parts[i][2] for i in grp)
            cy2 = max(parts[i][0].comp_box[3] + parts[i][2] for i in grp)
            B.rect('poly2', snap(cx1 - 0.30 - dummy_l), snap(cy1 - 0.3), snap(cx1 - 0.30), snap(cy2 + 0.3))
            B.rect('poly2', snap(cx2 + 0.30), snap(cy1 - 0.3), snap(cx2 + 0.30 + dummy_l), snap(cy2 + 0.3))
    if ring_kind:
        x1, y1, x2, y2 = B.bbox
        xl, yb = math.floor(x1 - gap), math.floor(y1 - gap)
        xr, yt = math.ceil(x2 + gap), math.ceil(y2 + gap)
        ring_cl(B, xl, yb, xr, yt, ring_kind, ring_net)
        if ring_kind == 'n':
            B.rect('nwell', xl - 1.3, yb - 1.3, xr + 1.3, yt + 1.3)
    B.size = (B.bbox[2] - B.bbox[0], B.bbox[3] - B.bbox[1])
    return B


STD_GDS = os.path.join(k.PDK_ROOT, k.PDK, 'libs.ref/gf180mcu_fd_sc_mcu7t5v0/gds/gf180mcu_fd_sc_mcu7t5v0.gds') if 'os' in globals() else None


def or2_block(ly, name, a1, a2, z, vdd, vss):
    """the 7t5v0 OR2 standard cell with one filltie abutted on the right (n-well + substrate tap).  Pins A1 (0.87, 1.6), A2 (1.96, 2.5), Z (3.75, 2.0) are Metal1 strips: Via1 + Metal2
    stubs go UP to pads on integer coordinates above the cell; VDD gets a Metal1 landing pad above the rail, VSS lands on the rail (cell origin on integer y)."""
    import os as _os
    std = _os.path.join(k.PDK_ROOT, k.PDK, 'libs.ref/gf180mcu_fd_sc_mcu7t5v0/gds/gf180mcu_fd_sc_mcu7t5v0.gds')
    B = Block(ly, name)
    c_or = k.import_gds(ly, std, 'gf180mcu_fd_sc_mcu7t5v0__or2_1')
    c_ft = k.import_gds(ly, std, 'gf180mcu_fd_sc_mcu7t5v0__filltie')
    for cc in (c_or, c_ft):                                   # labels of the library cells would become ports of amp_ch in Magic: remove them (pins are labelled once, at the top)
        for li in ly.layer_indexes():
            for sh in list(cc.shapes(li).each()):
                if sh.is_text():
                    cc.shapes(li).erase(sh)
    k.put(B.cell, c_or, 0, 0)
    k.put(B.cell, c_ft, 4.48, 0)
    B.grow(-0.43, -0.43, 4.48 + 1.55, 4.35)
    ry = 6                                                   # pad row (integer)
    pins = ((a1, 0.87, 1.6), (a2, 1.96, 2.5), (z, 3.8, 2.8))
    for i, (net, px, py) in enumerate(pins):
        xi = {0: 1, 1: 2, 2: 4}[i]
        k.rect(B.cell, 'via1', px - 0.13, py - 0.13, px + 0.13, py + 0.13)
        B.rect('metal2', px - 0.25, py - 0.25, px + 0.25, ry + 0.25)
        B.rect('metal2', min(px, xi) - 0.25, ry - 0.25, max(px, xi) + 0.25, ry + 0.25)
        B.fixed_shape(M2, (px - 0.25, py - 0.25, px + 0.25, ry + 0.25), net)
        B.fixed_shape(M2, (min(px, xi) - 0.25, ry - 0.25, max(px, xi) + 0.25, ry + 0.25), net)
        B.term(net, 'metal2', pad_rect(xi, ry))
    B.term(vss, 'metal1', (0.3, -0.3, 4.2, 0.3))
    # VDD: the filltie's rail at the top (y 3.92): Metal1 stub up to a landing pad on integer coordinates
    B.rect('metal1', 4.75, 3.9, 5.25, 8.25)
    B.term(vdd, 'metal1', pad_rect(5.0, 8.0))
    B.size = (B.bbox[2] - B.bbox[0], B.bbox[3] - B.bbox[1])
    return B
