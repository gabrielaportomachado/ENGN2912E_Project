"""cmp_lib.py (L1a): the comparator cmp_p (AFE/adc/spice/comparator.spice) as two mirror-image halves + a centre column.
side(ly, tag): one routed half (local nets inx, a, s, o, oo, bb, q + shared tl, clk, clkb, vdd_cmp, vss); the SAME cell is placed twice (second one mirrored about the axis), so the pair, the
preamp nodes a1 / a2, the MIM units Cxa and the latch halves are exactly mirror-symmetric.  centre(ly): mt1 (tail pfet) and the clock inverter ic."""
import math
import kpdk as k
import adclib as a
import rlib as R


GB = 3
MARG = 2
TP = 4


def side(ly, tag):
    pair = a.dev_block(ly, 'pair_' + tag, 'pfet', 16.0, 0.5, 5, s_net='tl', d_nets='a', g_net='inx', bulk_net='vdd_cmp', ring=True)
    nt = [dict(kind='nfet', w=2.0, l=0.28, x=0, y=0, s='vss', d='a', g='clkb', ring_s=True),                 # mr
          dict(kind='nfet', w=8.0, l=0.5, x=TP, y=0, s='vss', d='s', g='a', ring_s=True),                    # mc
          dict(kind='nfet', w=4.0, l=0.28, x=2 * TP, y=0, s='s', d='o', g='oo'),                                  # mn
          dict(kind='nfet', w=1.0, l=0.28, x=3 * TP, y=0, s='vss', d='bb', g='o', ring_s=True),                  # b_xn (first inverter)
          dict(kind='nfet', w=2.0, l=0.28, x=4 * TP, y=0, s='vss', d='q', g='bb', ring_s=True)]                  # b_xn (second inverter)
    N = a.group_block(ly, 'cn_' + tag, nt, ring_kind='p', ring_net='vss')
    pt = [dict(kind='pfet', w=4.0, l=0.28, x=0, y=0, s='vdd_cmp', d='o', g='oo', ring_s=True),            # mq
          dict(kind='pfet', w=2.0, l=0.28, x=TP, y=0, s='vdd_cmp', d='o', g='clk', ring_s=True),           # mp
          dict(kind='pfet', w=2.0, l=0.28, x=2 * TP, y=0, s='vdd_cmp', d='bb', g='o', ring_s=True),            # b_xp (first inverter)
          dict(kind='pfet', w=4.0, l=0.28, x=3 * TP, y=0, s='vdd_cmp', d='q', g='bb', ring_s=True)]           # b_xp (second inverter)
    P = a.group_block(ly, 'cp_' + tag, pt, ring_kind='n', ring_net='vdd_cmp')
    C = R.mim5_block(ly, 'cxa_' + tag, 'a', 'vss')
    return pair, N, P, C


def put_at(blk, x, y):
    """integer offsets (dx, dy) that place the lower-left corner of blk's bbox at (x, y) or just above / right of it"""
    return math.ceil(x - blk.bbox[0] - 1e-9), math.ceil(y - blk.bbox[1] - 1e-9)


def side_cell(ly, name='cmp_side'):
    """one routed half; local nets: inx a s o oo bb q (own) + tl clk clkb vdd_cmp vss (shared).  Returns the block (terms = exposure pads, Metal3)."""
    pair, N, P, C = side(ly, 'x')
    dxN, dyN = put_at(N, 0, 0)
    dxP, dyP = put_at(P, 0, dyN + N.bbox[3] + GB)
    dxQ, dyQ = put_at(pair, dxN + N.bbox[2] + GB, 0)
    dxC, dyC = put_at(C, dxQ + pair.bbox[0] + 2, dyQ + pair.bbox[3] + GB)
    parts = [(N, dxN, dyN), (P, dxP, dyP), (pair, dxQ, dyQ), (C, dxC, dyC)]
    xl = min(dxN + N.bbox[0], dxP + P.bbox[0]) - 2
    xr = max(dxQ + pair.bbox[2], dxC + C.bbox[2]) + 2
    yb = min(dyN + N.bbox[1], dyQ + pair.bbox[1])
    yt = max(dyP + P.bbox[3], dyC + C.bbox[3])
    ext = {}
    yy = int(yb) + 3
    for n in ('tl', 'clk', 'clkb', 'o', 'oo', 'vdd_cmp', 'vss'):
        ext[n] = (int(xl), yy)
        yy += 3
    ext['inx'] = (int(xr), int(yt) - 3)
    ext['q'] = (int(xr), int(yb) + 3)
    B = R.route_cell(ly, name, parts, ext, ['inx', 'a', 's', 'o', 'oo', 'bb', 'q', 'tl', 'clk', 'clkb'], margin=MARG, power_first=True)
    B.ext = ext
    B.parts = [(p[0].name, p[1], p[2]) for p in parts]
    return B
