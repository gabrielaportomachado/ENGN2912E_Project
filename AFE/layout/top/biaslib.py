"""biaslib.py (L3a): helpers of the bias_genc generator (mk_bias_genc.py).  Run only inside KLayout through   bash AFE/layout/scripts/kl.sh AFE/layout/top/mk_bias_genc.py ...
It uses the proven helpers of AFE/layout/adc/ (adclib: Block, dev_block, group_block, ring_cl, mim_cap; router; rlib: route_cell) without changing them.

ladder   : the 1 um wide ppolyf_u_1k ladders A and B as ONE serpentine each: rows of 3 units of 25 um (the PDK pcell ppolyf_u_high_Rs_resistor WITHOUT its left substrate tie, as in
           adc/vhalf_lib.py), units of one row joined head to head on Metal1, rows alternately of chain E (even rows) and chain O (odd rows), Metal2 jumper lanes at the row ends
           (chain E: Via1 on the head, chain O: Metal1 strip 1 um outward + Via1, so that the lanes of the two chains never share an x), plain poly dummy rows at both ends.
rbres    : Rb = 120 um x 2 um as NR rows of equal segments (series segments of equal width = one resistor for netgen)
"""
import math
import pya
import kpdk as k
import adclib as a

k.LAYERS.setdefault('resistor', (62, 0))        # the RESISTOR marker of the PDK pcell (HRES.1)
UL = 25.0                     # unit length (um)
GAP = 2.0                      # distance between the bodies of two units of one row (even, so that the junction centre is on an integer x when XO is an integer)
PITCH = 2.0                    # row pitch of the ladders (um)
NU = 3                         # units per row
NROW = 22                      # rows per ladder (11 of chain E, 11 of chain O)
DUMMIES = True

_seg_cache = {}


def res_seg(ly, w, l):
    """the ppolyf_u_1k pcell of w x l um without the substrate tie on its left (clipped), as a plain cell"""
    key = (id(ly), w, l)
    if key not in _seg_cache:
        pc = k.pcell(ly, 'ppolyf_u_high_Rs_resistor', l_res=l, w_res=w)
        c = ly.create_cell('bg_res_%g_%g' % (w, l))
        clip = pya.Region(pya.Box(k.u(-3.0, ly), k.u(-1.0, ly), k.u(-1.0, ly), k.u(w + 3.0, ly)))        # the tie is at x = -1.78 .. -1.32
        for li in ly.layer_indexes():
            reg = pya.Region(pc.begin_shapes_rec(li))
            if reg.is_empty():
                continue
            if ly.get_info(li).layer in (22, 31, 33, 34):
                reg = reg - clip
            c.shapes(li).insert(reg)
        _seg_cache[key] = c
    return _seg_cache[key]


def ladder(ly, name, n_e1, tap_net, mid_net, tap_inrow, XO=6):
    """ladder block.  Chain E (even rows 0, 2 .. 20) = n_e1 units + (33 - n_e1) units, the tap `tap_net` after unit n_e1, the end of chain E = node mid_net; chain O (odd rows, from row 21 down to row 1)
    = 33 units from mid_net to vss.  Start of chain E (row 0, left head) = vdd, end of chain O (row 1, left head) = vss.
    tap_inrow: True if the tap is a junction INSIDE a row (n_e1 % 3 != 0), False if it is the row end (the head of the last unit of the tap row, joined to the lane).
    Terminals (Metal1 pads on integer coordinates): vdd, vss (x = XO - 3), mid_net and tap_net.  Metal2 lanes are fixed shapes (obstacles for the router) with the net names
    'mid' / 'tap' for the two named ones and unique internal names for the rest."""
    B = a.Block(ly, name)
    seg = res_seg(ly, 1.0, UL)
    UP = UL + GAP
    HL = XO - 0.46
    HR = XO + (NU - 1) * UP + UL + 0.46
    yc = lambda r: r * PITCH                                    # row centre line (integer for PITCH = 2)
    nE = NROW // 2
    for r in range(NROW):
        for u in range(NU):
            k.put(B.cell, seg, XO + u * UP, yc(r) - 0.5)
        B.grow(XO - 1.0, yc(r) - 0.9, XO + (NU - 1) * UP + UL + 1.0, yc(r) + 0.9)
        for u in range(NU - 1):                                  # head-to-head joints on Metal1
            B.rect('metal1', XO + u * UP + UL + 0.46 - 0.25, yc(r) - 0.25, XO + (u + 1) * UP - 0.46 + 0.25, yc(r) + 0.25)
            # PP.2: the P+ of two facing heads is 0.36 um apart (< 0.4): merge them (field oxide only)
            B.rect('pplus', XO + u * UP + UL, yc(r) - 0.68, XO + (u + 1) * UP, yc(r) + 0.68)
        if r < NROW - 1 and PITCH < 2.2:                         # HRES.1: resistor marker spacing 0.4 um, "merge if less": fill the gap between two rows
            B.rect('resistor', XO - 1.04, yc(r) + 0.9 - 0.01, XO + (NU - 1) * UP + UL + 1.04, yc(r + 1) - 0.9 + 0.01)
    if DUMMIES:
        for r in (-1, NROW):
            for u in range(NU):
                B.rect('poly2', XO + u * UP - 0.64, yc(r) - 0.5, XO + u * UP + UL + 0.64, yc(r) + 0.5)

    def m1pad(x, y):
        B.rect('metal1', x - 0.25, y - 0.25, x + 0.25, y + 0.25)

    def via1(x, y):
        k.rect(B.cell, 'via1', x - 0.13, y - 0.13, x + 0.13, y + 0.13)

    cnt = [0]

    def lane(x, r1, r2, net=None):
        if net is None:
            cnt[0] += 1
            net = '%s_lane%d' % (name, cnt[0])
        r = (x - 0.25, yc(min(r1, r2)) - 0.25, x + 0.25, yc(max(r1, r2)) + 0.25)
        B.rect('metal2', *r)
        B.fixed_shape(a.M2, r, net)

    def head(r, side, chain):
        x0 = HL if side == 'L' else HR
        m1pad(x0, yc(r))
        if chain == 'E':
            via1(x0, yc(r))
            return x0
        sx = x0 - 1.0 if side == 'L' else x0 + 1.0
        B.rect('metal1', min(x0, sx) - 0.25, yc(r) - 0.25, max(x0, sx) + 0.25, yc(r) + 0.25)
        via1(sx, yc(r))
        return sx

    E_rows = [2 * j for j in range(nE)]
    O_rows = [NROW - 1 - 2 * j for j in range(nE)]
    j_tap = (n_e1 - 1) // NU                                    # E row that holds unit n_e1 (0-based j)
    for j in range(nE - 1):
        sE = 'R' if j % 2 == 0 else 'L'
        sO = 'L' if j % 2 == 0 else 'R'
        x1 = head(E_rows[j], sE, 'E')
        x2 = head(E_rows[j + 1], sE, 'E')
        lane(x1, E_rows[j], E_rows[j + 1], 'tap' if (not tap_inrow and j == j_tap) else None)
        x1 = head(O_rows[j], sO, 'O')
        x2 = head(O_rows[j + 1], sO, 'O')
        lane(x1, O_rows[j], O_rows[j + 1])
    # free ends
    xw = XO - 3
    for (net, r) in (('vdd', E_rows[0]), ('vss', O_rows[-1])):
        m1pad(HL, yc(r))
        B.rect('metal1', xw - 0.25, yc(r) - 0.25, HL + 0.25, yc(r) + 0.25)
        B.term(net, 'metal1', a.pad_rect(xw, yc(r)))
    # mid node: E row 20 and O row 21, right heads, one Metal2 lane at x = HR
    for r in (E_rows[-1], O_rows[0]):
        m1pad(HR, yc(r))
        via1(HR, yc(r))
    lane(HR, E_rows[-1], O_rows[0], 'mid')
    xe = int(XO + (NU - 1) * UP + UL + 3)                       # east pad column (integer)
    B.rect('metal1', HR - 0.25, yc(E_rows[-1]) - 0.25, xe + 0.25, yc(E_rows[-1]) + 0.25)
    B.term(mid_net, 'metal1', a.pad_rect(xe, yc(E_rows[-1])))
    # tap
    if tap_inrow:
        o = (n_e1 - 1) % NU                                      # order of unit n_e1 inside its row (0 = first traversed)
        u_a = o if j_tap % 2 == 0 else (NU - 1 - o) - 1          # the junction is between the positions u_a and u_a + 1
        xj = XO + u_a * UP + UL + GAP / 2.0
        yt = yc(E_rows[j_tap])
        B.term(tap_net, 'metal1', a.pad_rect(xj, yt))
        assert abs(xj - round(xj)) < 1e-9
    else:
        yt = yc(E_rows[j_tap])
        assert j_tap % 2 == 0, 'row-end tap on the right side only'
        B.rect('metal1', HR - 0.25, yt - 0.25, xe + 0.25, yt + 0.25)
        B.term(tap_net, 'metal1', a.pad_rect(xe, yt))
    B.grow(xw - 0.5, yc(-1) - 0.6, xe + 0.5, yc(NROW) + 0.6)
    B.size = (B.bbox[2] - B.bbox[0], B.bbox[3] - B.bbox[1])
    B.xe, B.xw, B.yc = xe, xw, yc
    return B


def rbres(ly, name, nrow=2, pitch=3.0, XO=4):
    """Rb: 120 um x 2 um as nrow rows of 120 / nrow um, rows joined alternately on the right and the left (Metal1 strips); terminals r1 (row 0, left) and vss (last row)"""
    assert nrow % 2 == 0
    B = a.Block(ly, name)
    L = 120.0 / nrow
    seg = res_seg(ly, 2.0, L)
    yc = lambda r: r * pitch + 1.0
    for r in range(nrow):
        k.put(B.cell, seg, XO, r * pitch)
        B.grow(XO - 1.0, r * pitch - 0.5, XO + L + 1.0, r * pitch + 2.5)
        if r < nrow - 1 and pitch < 3.2:                          # HRES.1 (marker spacing 0.4): merge the markers of two rows
            B.rect('resistor', XO - 1.04, r * pitch + 2.4 - 0.01, XO + L + 1.04, (r + 1) * pitch - 0.4 + 0.01)
    for r in range(nrow - 1):
        if r % 2 == 0:
            xh = XO + L + 0.46
        else:
            xh = XO - 0.46
        B.rect('metal1', xh - 0.19, yc(r) - 0.7, xh + 0.19, yc(r + 1) + 0.7)
    xw = XO - 3
    for net, r in (('r1', 0), ('vss', nrow - 1)):
        xh = XO - 0.46
        B.rect('metal1', xw - 0.25, yc(r) - 0.25, xh + 0.19, yc(r) + 0.25)
        B.term(net, 'metal1', a.pad_rect(xw, yc(r)))
    B.grow(xw - 0.5, -0.5, XO + L + 1.5, (nrow - 1) * pitch + 2.5)
    B.size = (B.bbox[2] - B.bbox[0], B.bbox[3] - B.bbox[1])
    return B


# =====================================================================================================================================================================
# transistor blocks
# =====================================================================================================================================================================
def dev_block_m(ly, name, kind, w, l, nf, s_net, d_nets, g_net, bulk_net, ring_gap=1.5, params=None):
    """adclib.dev_block with the `multi` option of amp/amplib.py: every drain strip may carry its own net (d_nets = list, one entry per drain strip), each ends in its own Metal2 pad on an integer x"""
    prm = dict(volt='3.3V', bulk='None', w_gate=w, l_gate=l, nf=nf, gate_con_pos='top')
    if params:
        prm.update(params)
    B = a.Block(ly, name)
    probe = a.info(ly, kind, **prm)
    gy_c = (probe.g[0][1] + probe.g[0][3]) / 2.0
    oy = a.rint(gy_c) - gy_c
    D = a.Dev(B.cell, kind, 0.0, oy, **prm)
    sd, gp, comp = D.sd, D.g, D.comp
    cl, cb, cr, ct = comp
    S = sd[0::2]
    Dn = sd[1::2]
    assert len(d_nets) == len(Dn), (len(d_nets), len(Dn))
    rail_y1, rail_y2 = cb - 2.0, cb - 0.5
    for s in S:
        B.rect('metal1', s[0], rail_y1, s[2], s[1] + 0.02)
    rx1, rx2 = min(S[0][0], (S[0][0] + S[-1][2]) / 2.0 - 1.0), max(S[-1][2], (S[0][0] + S[-1][2]) / 2.0 + 1.0)
    B.rect('metal1', rx1, rail_y1, rx2, rail_y2)
    B.term(s_net, 'metal1', (rx1, rail_y1, rx2, rail_y2))
    gx1 = min(g[0] for g in gp)
    gx2 = max(g[2] for g in gp)
    gy1, gy2 = gp[0][1], gp[0][3]
    bc = a.rint((gy1 + gy2) / 2.0)
    B.rect('metal1', gx1, gy1, gx2, gy2)
    lx = a.rint(min(S[0][0], gx1) - 2.0)
    B.rect('metal1', lx - 0.5, bc - 0.5, lx + 0.5, bc + 0.5)
    B.rect('metal1', lx, gy1, gx1 + 0.01, gy2)
    B.term(g_net, 'metal1', (lx - 0.5, bc - 0.5, lx + 0.5, bc + 0.5))
    ry = bc + 1.0
    for di, d in enumerate(Dn):
        xc = (d[0] + d[2]) / 2.0
        yv = d[3] - 0.45
        B.rect('metal1', xc - 0.25, yv - 0.25, xc + 0.25, yv + 0.25)
        k.rect(B.cell, 'via1', xc - 0.13, yv - 0.13, xc + 0.13, yv + 0.13)
        B.rect('metal2', xc - 0.25, yv - 0.25, xc + 0.25, ry + 0.25)
        B.fixed_shape(a.M2, (xc - 0.25, yv - 0.25, xc + 0.25, ry + 0.25), d_nets[di])
        xi = a.rint(xc)
        B.rect('metal2', min(xc, xi) - 0.25, ry - 0.25, max(xc, xi) + 0.25, ry + 0.25)
        B.fixed_shape(a.M2, (min(xc, xi) - 0.25, ry - 0.25, max(xc, xi) + 0.25, ry + 0.25), d_nets[di])
        B.term(d_nets[di], 'metal2', (xi - 0.25, ry - 0.25, xi + 0.25, ry + 0.25))
    xb = max(d[2] for d in Dn)
    x_l = a.rint(min(lx, S[0][0]) - ring_gap)
    x_r = a.rint(max(cr, xb) + ring_gap)
    y_b = a.rint(rail_y1 - 1.5)
    y_t = a.rint(ry + 0.25 + 1.5 + 0.5)
    a.ring_cl(B, x_l, y_b, x_r, y_t, 'p' if kind == 'nfet' else 'n', bulk_net)
    if kind == 'pfet':
        B.rect('nwell', x_l - 0.5 - 0.8, y_b - 0.5 - 0.8, x_r + 0.5 + 0.8, y_t + 0.5 + 0.8)
    B.dev = D
    B.comp_box = D.comp
    B.size = (x_r - x_l, y_t - y_b)
    return B


def pr1_block(ly, name, sn, mnet, gnet):
    """ONE pseudo-resistor-like pfet 0.22u / 0.5u (adclib.pr_block draws two of them): own n-well, N+ tie of the minimum size tied to the source net sn; drain net mnet, gate net gnet"""
    B = a.Block(ly, name)
    prm = dict(volt='3.3V', bulk='None', w_gate=0.22, l_gate=0.5, nf=1, con_bet_fin=0)
    x0 = 0.0
    D = a.Dev(B.cell, 'pfet', x0, 0.0, **prm)
    B.grow(*D.bbox)
    S, Dd = D.sd[0], D.sd[1]
    gb = min(D.g, key=lambda b: b[1])
    yc = (S[1] + S[3]) / 2.0
    tx1, tx2 = x0 + 1.68, x0 + 2.10
    ty1, ty2 = a.snap(yc - 0.25), a.snap(yc + 0.25)
    B.rect('comp', tx1, ty1, tx2, ty2)
    B.rect('nplus', tx1 - 0.16, ty1 - 0.16, tx2 + 0.16, ty2 + 0.16)
    a.cuts(B.cell, 'contact', tx1, ty1, tx2, ty2, inset=0.1)
    B.rect('metal1', tx1, ty1, tx2, ty2)
    nw = D.nw
    B.rect('nwell', nw[0] + 0.8, nw[1], tx2 + 0.6, nw[3])
    ty = math.ceil(max(D.g[0][3], D.g[1][3]) + 0.5 + 0.25 - 1e-9)
    B.rect('metal1', S[0], S[3] - 0.02, S[2], ty + 0.25)
    B.rect('metal1', tx1, ty2 - 0.02, tx2, ty + 0.25)
    B.rect('metal1', S[0], ty - 0.25, tx2, ty + 0.25)
    B.term(sn, 'metal1', (S[0], ty - 0.25, tx2, ty + 0.25))
    yd = math.floor(gb[1] - 0.5 - 1e-9)
    B.rect('metal1', Dd[0], yd - 0.25, Dd[2], Dd[1] + 0.02)
    B.rect('metal1', Dd[0], yd - 0.25, x0 + 2.25, yd + 0.25)
    B.term(mnet, 'metal1', a.pad_rect(x0 + 2, yd))
    B.rect('metal1', gb[0], yd - 0.25, gb[2], gb[1] + 0.02)
    B.rect('metal1', x0 - 0.25, yd - 0.25, gb[2], yd + 0.25)
    B.term(gnet, 'metal1', a.pad_rect(x0, yd))
    B.grow(x0 - 0.25, yd - 0.25, x0 + 2.7, ty + 0.25)
    B.size = (B.bbox[2] - B.bbox[0], B.bbox[3] - B.bbox[1])
    return B


def rotate_block(ly, B, name):
    """B rotated by 90 degrees counter-clockwise ((x, y) -> (-y, x)); terminals, fixed shapes, plates and bbox are transformed (integer pad coordinates stay integer)"""
    R = a.Block(ly, name)
    k.put(R.cell, B.cell, 0, 0, rot=90)
    tr = lambda r: (-r[3], r[0], -r[1], r[2])
    R.terms = [(n, c, tr(r)) for (n, c, r) in B.terms]
    R.fixed = [(l, tr(r), n, ex) for (l, r, n, ex) in B.fixed]
    R.bbox = list(tr(B.bbox))
    R.size = (B.size[1], B.size[0]) if hasattr(B, 'size') else None
    return R
