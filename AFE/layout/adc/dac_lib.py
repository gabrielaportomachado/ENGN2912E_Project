"""dac_lib.py (L1a): the split 6+6 charge-redistribution DAC array of adc_ch (127 units 5 x 5 um + bridge 5.085 x 5 um + dummy rows), generated, nothing drawn by hand.

Geometry (all numbers measured with the official deck, FLOW.md section 5 and AFE/layout/adc/FLOW_ADC.md):
  unit = cap_mim pcell (top plate 5 x 5 um on Metal5 / FuseTop, bottom plate Metal4 = top plate + 0.6 um on every side).
  neighbours of the SAME net: pitch 6.0 um (top plates 1.0 um apart, MIMTM.6 >= 0.6), their Metal4 plates overlap -> ONE bottom-plate polygon, the Metal5 plates are joined by a strap.
  neighbours of DIFFERENT nets: pitch 7.4 um (top plates 2.4 um apart = bottom plates 1.2 um apart, MIMTM.1).
  a bottom-plate pad (Metal4 polygon that is part of the plate) must be >= 2.26 um from the top plate edge of its own unit (FLOW.md section 5): tabs run to pads there, the router starts from the pads.
Array (LSB half west, MSB half east, 8 rows each, see SPEC.md 3.3 rule 1; every bit is placed in point-symmetric pairs about the centre of its half):
  rows 0, 1 and 6, 7 = the largest bit (b5 / b11), rows 2 and 5 = the next one (b4 / b10), rows 3 and 4 = the small bits (4 + 4 + 2 + 2 + 1 + 1 + bridge / dummy bd): row 4 is the point reflection of row 3.
  between row 3 and row 4 a 6 um channel (pads and Metal2 / Metal3 wires of the trapped runs), one dummy row (both plates on vss) south and north of the 8 rows.
"""
import kpdk as k
import adclib as a

U = 5.0                      # unit top plate
PS = 6.0                     # pitch inside a run (same net)
GAP_D = 2.4                  # top plate gap between different nets
GAP_S = 1.0                  # top plate gap between same-net neighbours
CHAN = 6.0                   # channel between row 3 and row 4 (top plate to top plate)
BR_W = 5.085                 # bridge unit width (5.082993 in the reference, 5 nm grid)
PAD = 1.2                    # Metal4 pad
M5W = 1.0                    # Metal5 strap width (top plate bars)

# runs per row, west -> east, per half.  ('bd' = the dummy unit of the LSB array, 'br' = the bridge)
LSB_ROWS = {0: [('b5', 8)], 1: [('b5', 8)], 2: [('b4', 8)], 3: [('bd', 1), ('b1', 1), ('b2', 2), ('b3', 4)], 4: [('b3', 4), ('b2', 2), ('b1', 1), ('b0', 1)],
            5: [('b4', 8)], 6: [('b5', 8)], 7: [('b5', 8)]}
MSB_ROWS = {0: [('b11', 8)], 1: [('b11', 8)], 2: [('b10', 8)], 3: [('b9', 4), ('b8', 2), ('b7', 1), ('b6', 1)], 4: [('br', 1), ('b7', 1), ('b8', 2), ('b9', 4)],
            5: [('b10', 8)], 6: [('b11', 8)], 7: [('b11', 8)]}


def run_w(n, w=U):
    return n * w + (n - 1) * GAP_S


def row_w(runs):
    return sum(run_w(n, BR_W if net == 'br' else U) for net, n in runs) + GAP_D * (len(runs) - 1)


def row_ys():
    """y of the lower edge of the top plates: dummy south, rows 0..7, dummy north"""
    gaps = [GAP_D, GAP_S, GAP_D, GAP_D, CHAN, GAP_D, GAP_D, GAP_S, GAP_D]          # between consecutive of: dS, r0 .. r7, dN
    ys = [0.0]
    for g in gaps:
        ys.append(ys[-1] + U + g)
    return ys                                                                         # 10 values: dS, r0, .. r7, dN


class Dac:
    pass


def build(cell, x0=0.0, y0=0.0, pad_x_w=None, pad_x_e=None, dummies=True):
    """draws the array into `cell` (a block cell) with its lower-left top plate corner at (x0, y0).  Returns a Dac object: sites, terminals (net, 'metal4', rect), fixed Metal4 shapes,
    keep-out boxes, plate polygons, Metal5 trunk positions."""
    D = Dac()
    D.sites, D.terms, D.fixed, D.m4_polys, D.m5 = [], [], [], [], []
    ys = row_ys()
    D.ys = [y0 + v for v in ys]
    wl = max(row_w(r) for r in LSB_ROWS.values())
    wm = max(row_w(r) for r in MSB_ROWS.values())
    gb = GAP_D                                                                    # boundary between the halves (top plate to top plate)
    xl0 = x0
    xm0 = a.snap(x0 + wl + gb)
    D.xl0, D.xl1, D.xm0, D.xm1 = xl0, xl0 + wl, xm0, xm0 + wm
    D.x_all = (xl0, xm0 + wm)
    ly = cell.layout()

    def unit(x, y, net_t, net_b, w=U, tag=''):
        a.mim_cap(cell, x, y, w, U, net_t, net_b)
        D.sites.append((tag, net_t, net_b, round(x, 3), round(y, 3), w))

    def strap(x1, x2, yc, tag=None):
        k.rect(cell, 'metal5', x1, yc - M5W / 2.0, x2, yc + M5W / 2.0)

    D.row_ext = {}                                                                # (half, row) -> (x_first_left, x_last_right) of the top plates
    D.run_pos = {}                                                                # (half, row, net) -> list of unit x
    for half, rows, xo, wmax, topnet in (('L', LSB_ROWS, xl0, wl, 'm'), ('M', MSB_ROWS, xm0, wm, 't')):
        for r in range(8):
            y = D.ys[r + 1]
            runs = rows[r]
            x = a.snap(xo + (wmax - row_w(runs)) / 2.0)
            first = x
            for net, n in runs:
                for i in range(n):
                    w = BR_W if net == 'br' else U
                    if net == 'br':
                        unit(x, y, 't', 'm', w, 'br')                             # bridge: top plate t, bottom plate m
                    elif net == 'bd':
                        unit(x, y, topnet, 'bd', w, 'bd')
                    else:
                        unit(x, y, topnet, net, w, net)
                    D.run_pos.setdefault((half, r, net), []).append(x)
                    x = a.snap(x + w + (GAP_S if i < n - 1 else 0.0))
                x = a.snap(x + GAP_D)
            last = a.snap(x - GAP_D)
            D.row_ext[(half, r)] = (first, last)
            strap(first, last, y + U / 2.0)
    # dummy rows (both plates vss): one merged bottom plate, one Metal5 bar
    xa, xb = D.x_all
    nd = int((xb - xa + GAP_S) // PS)
    D.dummy = []
    D.dummies = dummies
    for idx, r in ((0, 'S'), (9, 'N')):
        if not dummies:                                                           # R5: no dummy bars (plain metal only, no matching value for the MIM): the rows are not drawn
            continue
        y = D.ys[idx]
        xs = [xa + i * PS for i in range(nd)]
        # FINDING (L1a): a dummy MIM with both plates on vss is extracted by Magic as a shorted cap_mim device that netgen does not drop (the reference has none): the dummy
        # row is drawn as plain Metal4 (6.2 um) / Metal5 (5 um) bars of the unit footprint, no FuseTop / CAP_MK, so that the metal pattern around the array is regular.
        k.rect(cell, 'metal4', xs[0] - 0.6, y - 0.6, xs[-1] + U + 0.6, y + U + 0.6)
        k.rect(cell, 'metal5', xs[0], y, xs[-1] + U, y + U)
        D.sites.append(('dummy' + r, 'vss', 'vss', round(xs[0], 3), round(y, 3), round(xs[-1] + U - xs[0], 3)))
        D.dummy.append((r, y, xs[0], xs[-1] + U))
    D.top = (D.ys[9] if dummies else D.ys[8]) + U
    D.ylo = D.ys[0] if dummies else D.ys[1]
    exits(cell, D)
    return D


TRIM_NET = 'b11'
TRIM_LEN = 100.0
TRIM_W = float(__import__('os').environ.get('TRIM_W', '1.6'))


def m4(cell, x1, y1, x2, y2):
    k.rect(cell, 'metal4', x1, y1, x2, y2)


def m5(cell, x1, y1, x2, y2):
    k.rect(cell, 'metal5', x1, y1, x2, y2)


def pad(cell, D, net, xc, yc, via4=False):
    """Metal4 pad 1.2 x 1.2 um on integer-friendly centre (xc, yc) = router terminal; optional Via4 + Metal5 pad (0.8 um)"""
    h = PAD / 2.0
    m4(cell, xc - h, yc - h, xc + h, yc + h)
    D.terms.append((net, 'metal4', (xc - h, yc - h, xc + h, yc + h)))
    if via4:
        a.cuts(cell, 'via4', xc - 0.4, yc - 0.4, xc + 0.4, yc + 0.4, inset=0.27)
        m5(cell, xc - 0.4, yc - 0.4, xc + 0.4, yc + 0.4)


def exits(cell, D):
    """tabs, pads and Metal5 trunks.  West = LSB half (trunk m, pads at xl0 - 5), east = MSB half (trunk t, pads at xm1 + 5).  Pads of pure rows sit at the end of a Metal4 tab
    running OUTWARD under the trunk; the trapped runs of rows 3 / 4 take a tab into the channel and a pad at its centre line (both rows are allowed there at different x)."""
    import math
    D.pads = []
    D.tabs = []
    D.xT_m = D.xl0 - 1.8
    D.xT_t = D.xm1 + 1.8
    D.xp_m = D.xl0 - 5.0
    D.xp_t = math.ceil(D.xm1 + 4.6)
    yc_ch = D.ys[4] + U + CHAN / 2.0                                  # centre line of the channel (between row 3 and row 4)
    D.ych = yc_ch
    D.tr_m = [None, None]
    D.tr_t = [None, None]

    def ypad(y):
        return math.ceil(y + 1.0 - 1e-9)

    for half, rows, topnet, xT, xp, sgn in (('L', LSB_ROWS, 'm', D.xT_m, D.xp_m, -1), ('M', MSB_ROWS, 't', D.xT_t, D.xp_t, +1)):
        for r in range(8):
            y = D.ys[r + 1]
            first, last = D.row_ext[(half, r)]
            runs = rows[r]
            # strap from the bar to the trunk (Metal5)
            ys5 = y + 3.5
            if sgn > 0:
                m5(cell, last - 0.01, ys5 - 0.5, xT + 0.5, ys5 + 0.5)
            else:
                m5(cell, xT - 0.5, ys5 - 0.5, first + 0.01, ys5 + 0.5)
            if len(runs) == 1:
                net = runs[0][0]
                if r in (1, 6):
                    continue                                          # merged with row 0 / row 7 (same net, gap 1 um): one polygon, one tab
                yp = ypad(y)
                if sgn > 0:
                    m4(cell, last + 0.55, yp - 0.5, xp + 0.1, yp + 0.5)
                    D.tabs.append((net, (last + 0.55, yp - 0.5, xp + 0.1, yp + 0.5)))
                else:
                    m4(cell, xp - 0.1, yp - 0.5, first - 0.55, yp + 0.5)
                    D.tabs.append((net, (xp - 0.1, yp - 0.5, first - 0.55, yp + 0.5)))
                pad(cell, D, net, xp, yp)
                D.pads.append((net, half, r, xp, yp))
            else:
                for (net, n) in runs:
                    xs = D.run_pos[(half, r, net)]
                    wd = BR_W if net == 'br' else U
                    # pick the unit nearest the run centre and an integer x inside it (>= 1 um from the unit edges)
                    xm = sum(xs) / len(xs) + wd / 2.0
                    xu = min(xs, key=lambda v: abs(v + wd / 2.0 - xm))
                    cand = [i for i in range(int(math.ceil(xu + 1.0)), int(math.floor(xu + wd - 1.0)) + 1)]
                    xi = min(cand, key=lambda v: abs(v - (xu + wd / 2.0)))
                    if r == 3:
                        m4(cell, xi - 0.5, y + U + 0.55, xi + 0.5, yc_ch)
                        D.tabs.append((net if net != 'br' else 'm', (xi - 0.5, y + U + 0.55, xi + 0.5, yc_ch)))
                    else:
                        m4(cell, xi - 0.5, yc_ch, xi + 0.5, y - 0.55)
                        D.tabs.append((net if net != 'br' else 'm', (xi - 0.5, yc_ch, xi + 0.5, y - 0.55)))
                    pad(cell, D, net if net != 'br' else 'm', xi, yc_ch, via4=(net == 'br'))
                    D.pads.append((net, half, r, xi, yc_ch))
    # trunks
    ylo = D.ys[1] + 3.0
    yhi = D.ys[8] + 4.0
    m5(cell, D.xT_m - 0.5, ylo, D.xT_m + 0.5, yhi)
    m5(cell, D.xT_t - 0.5, ylo, D.xT_t + 0.5, yhi)
    D.tr_m = (D.xT_m, ylo, yhi)
    D.tr_t = (D.xT_t, ylo, yhi)
    # L1b trim (module variable TRIM_NET / TRIM_LEN): Metal4 strips of one bit net under the t trunk, grown from its tabs, to compensate the
    # bit-dependent coupling of the bottom-plate wiring to the top plate (the weights of the MSB half are not binary after PEX)
    if TRIM_LEN > 0:
        xs, xe = D.xT_t - TRIM_W / 2.0, D.xT_t + TRIM_W / 2.0
        cross = sorted((r[1], r[3]) for (n, r) in D.tabs if r[0] < xe and r[2] > xs)
        for (n, r) in list(D.tabs):
            if n != TRIM_NET or not (r[0] < xe and r[2] > xs):
                continue
            for sgn in (+1, -1):
                y0 = r[3] if sgn > 0 else r[1]
                lim = yhi - 0.5 if sgn > 0 else ylo + 0.5
                for (c0, c1) in cross:
                    if (c0, c1) == (r[1], r[3]):
                        continue
                    if sgn > 0 and c0 - 0.8 > y0 - 1e-9:
                        lim = min(lim, c0 - 0.8)
                    if sgn < 0 and c1 + 0.8 < y0 + 1e-9:
                        lim = max(lim, c1 + 0.8)
                y1 = y0 + sgn * TRIM_LEN
                y1 = min(y1, lim) if sgn > 0 else max(y1, lim)
                ya, yb = min(r[3] if sgn > 0 else r[1], y1), max(r[3] if sgn > 0 else r[1], y1)
                if yb - ya > 0.5:
                    m4(cell, xs, ya, xe, yb)
                    D.tabs.append((TRIM_NET, (xs, ya, xe, yb)))
    # bridge: its bottom plate (net m) goes through its Via4 pad in the channel to a Metal5 strap to the east end of the LSB row 4 bar
    br = [p for p in D.pads if p[0] == 'br'][0]
    xb, yb = br[3], br[4]
    lf, ll = D.row_ext[('L', 4)]
    xt = ll - U / 2.0
    m5(cell, xt - 0.5, yb - 0.5, xb + 0.4, yb + 0.5)
    m5(cell, xt - 0.5, yb - 0.5, xt + 0.5, D.ys[5] + 0.01)
    # dummy rows: one bottom-plate polygon + one top-plate bar, tied together (both vss) through a Metal4 pad outside the plate: tab, Via4, Metal5 strap
    for (r, y, xa, xz) in D.dummy:
        if r == 'S':
            xi = int(math.ceil(xa + 6.0))
            yp = math.floor(y - 3.2)
            m4(cell, xi - 0.5, yp, xi + 0.5, y - 0.55)
            m5(cell, xi - 0.5, yp - 0.4, xi + 0.5, y + 0.01)
            D.tabs.append(('vss', (xi - 0.5, yp, xi + 0.5, y - 0.55)))
        else:
            xi = D.xp_t
            yp = math.ceil(y + 2.0)
            m4(cell, xz + 0.55, yp - 0.5, xi + 0.1, yp + 0.5)
            m5(cell, xz - 0.01, yp - 0.5, xi + 0.4, yp + 0.5)
            D.tabs.append(('vss', (xz + 0.55, yp - 0.5, xi + 0.1, yp + 0.5)))
        pad(cell, D, 'vss', xi, yp, via4=True)
        D.pads.append(('vss', r, 0, xi, yp))
