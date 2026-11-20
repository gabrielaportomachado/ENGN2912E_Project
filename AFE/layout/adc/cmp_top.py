"""cmp_top.py (L1a): the whole comparator = two mirror-image halves (cmp_lib.side_cell, the SAME routed cell placed twice, the second one mirrored about x = 0) + the centre column (mt1, clock
inverter ic) + the routing of the shared / crossing nets tl, clk, clkb, o1, o2 and the supplies.  Terminals of the returned block: vref t cmp_q cmp_clk vdd_cmp vss (Metal3 pads)."""
import kpdk as k
import adclib as a
import rlib as R
import cmp_lib as CL


def renamer(side_no):
    if side_no == 1:
        m = {'inx': 'vref', 'tl': 'tl', 'clk': 'cmp_clk', 'clkb': 'clkb', 'o': 'o1', 'oo': 'o2', 'vdd_cmp': 'vdd_cmp', 'vss': 'vss', 'q': 'cmp_q'}
    else:
        m = {'inx': 't', 'tl': 'tl', 'clk': 'cmp_clk', 'clkb': 'clkb', 'o': 'o2', 'oo': 'o1', 'vdd_cmp': 'vdd_cmp', 'vss': 'vss'}
    return lambda n: m.get(n, 'c%d_%s' % (side_no, n))


def comparator(ly, name='cmp_blk'):
    S = CL.side_cell(ly)
    xi = 8                                                              # |x| of the inner exposure pads of the halves
    dx1 = xi - S.ext['tl'][0]
    ext1 = {n: (dx1 + x, y) for n, (x, y) in S.ext.items()}
    ext2 = {n: (-(x + dx1), y) for n, (x, y) in S.ext.items()}         # side 2 = mirror image about x = 0 (x -> -x)
    ct = [dict(kind='pfet', w=4.0, l=0.28, x=0, y=0, s='vdd_cmp', d='tl', g='clkb', ring_s=True),          # mt1
          dict(kind='pfet', w=2.0, l=0.28, x=4, y=0, s='vdd_cmp', d='clkb', g='cmp_clk', ring_s=True)]   # ic pfet
    CP = a.group_block(ly, 'cc_p', ct, ring_kind='n', ring_net='vdd_cmp')
    cn = [dict(kind='nfet', w=1.0, l=0.28, x=0, y=0, s='vss', d='clkb', g='cmp_clk', ring_s=True)]        # ic nfet
    CN = a.group_block(ly, 'cc_n', cn, ring_kind='p', ring_net='vss')
    yb = min(y for (x, y) in ext1.values())
    dxp, dyp = CL.put_at(CP, -CP.size[0] / 2.0, 6)
    dxn, dyn = CL.put_at(CN, -CN.size[0] / 2.0, dyp + CP.bbox[3] + 4)
    parts = [(S, dx1, 0, False, renamer(1)), (S, -dx1, 0, True, renamer(2)), (CP, dxp, dyp), (CN, dxn, dyn)]
    ext = {'vref': ext1['inx'], 't': ext2['inx'], 'cmp_q': ext1['q']}
    ext['cmp_clk'] = (0, int(yb) - 3)
    ext['vdd_cmp'] = (-4, int(yb) - 3)
    ext['vss'] = (4, int(yb) - 3)
    B = R.route_cell(ly, name, parts, ext, ['tl', 'clkb', 'cmp_clk', 'o1', 'o2'], margin=3, power_first=True)
    B.ext = ext
    return B
