"""vhalf_lib.py (L1a): vhalf = two 250 um x 1 um ppolyf_u_1k resistors (Xru vdd -> vcmd, Xrd vcmd -> vss) drawn as ONE interdigitated serpentine of 2 x 10 segments of 25 um, rows A B A B ... (equal
segments, same orientation, plain poly dummy lines at both ends), plus the 22.18 um MIM decap (vcmd to vss).  netgen adds series segments of equal width (SPEC.md section 6), so the
reference (one 250 um resistor each) matches.
The segments are the PDK pcell ppolyf_u_high_Rs_resistor (l_res = 25, w_res = 1) WITHOUT its substrate-tie contact on the left (clipped: it would sit under the jumper lanes).
Chain A (rows 0, 2, .. 18): vdd -> A0 .. A9 -> out.  Chain B (rows 19, 17, .. 1): out -> B0 .. B9 -> vss.  Jumpers: Metal2 lanes at the heads (chain A) and Metal1 strip + Metal2 lane 1 um
further out (chain B), alternating right / left, so that A and B never share a lane."""
import math
import pya
import kpdk as k
import adclib as a

LSEG = 25.0
PITCH = 3.0
NSEG = 10


def res_cell(ly):
    pc = k.pcell(ly, 'ppolyf_u_high_Rs_resistor', l_res=LSEG, w_res=1.0)
    c = ly.create_cell('vh_seg')
    clip = pya.Region(pya.Box(k.u(-3.0, ly), k.u(-1.0, ly), k.u(-1.0, ly), k.u(2.0, ly)))        # the substrate tie on the left (x < -1.0)
    for li in ly.layer_indexes():
        reg = pya.Region(pc.begin_shapes_rec(li))
        if reg.is_empty():
            continue
        if ly.get_info(li).layer in (22, 31, 33, 34):
            reg = reg - clip
        c.shapes(li).insert(reg)
    return c


def build(ly, name='vhalf_res'):
    """block with terminals vdd, vcmd, vss (Metal2 pads on integer coordinates west of the serpentine)"""
    B = a.Block(ly, name)
    seg = res_cell(ly)
    HL, HR = -0.46, LSEG + 0.46                                             # x of the poly-contact pads (pcell geometry)
    ROWS = 2 * NSEG
    for r in range(ROWS):
        k.put(B.cell, seg, 0.0, r * PITCH)
        B.grow(-1.0, r * PITCH - 0.4, LSEG + 1.0, r * PITCH + 1.4)
    # plain poly dummy lines (no res_mk, no contacts) one row beyond each end
    for r in (-1, ROWS):
        B.rect('poly2', -0.64, r * PITCH, LSEG + 0.64, r * PITCH + 1.0)
    yc = lambda r: r * PITCH + 0.5

    def m1pad(x, y):
        B.rect('metal1', x - 0.25, y - 0.25, x + 0.25, y + 0.25)

    def via1(x, y):
        k.rect(B.cell, 'via1', x - 0.13, y - 0.13, x + 0.13, y + 0.13)

    def lane(x, r1, r2):
        B.rect('metal2', x - 0.25, yc(min(r1, r2)) - 0.25, x + 0.25, yc(max(r1, r2)) + 0.25)

    def head(r, side, chain):
        """Metal1 pad on the head; chain B: Metal1 strip 1 um outward; returns the x of the lane"""
        x0 = HL if side == 'L' else HR
        m1pad(x0, yc(r))
        if chain == 'A':
            via1(x0, yc(r))
            return x0
        sx = x0 - 1.0 if side == 'L' else x0 + 1.0
        B.rect('metal1', min(x0, sx) - 0.25, yc(r) - 0.25, max(x0, sx) + 0.25, yc(r) + 0.25)
        via1(sx, yc(r))
        return sx

    A_rows = [2 * j for j in range(NSEG)]
    B_rows = [ROWS - 1 - 2 * j for j in range(NSEG)]
    for chain, rows in (('A', A_rows), ('B', B_rows)):
        for j in range(NSEG - 1):
            side = 'R' if j % 2 == 0 else 'L'
            x1 = head(rows[j], side, chain)
            x2 = head(rows[j + 1], side, chain)
            lane(x1, rows[j], rows[j + 1])
    # free heads: A0.L = vdd, A9.L = out, B0.L = out, B9.L = vss; Metal1 strips west to the terminal columns, Metal2 stubs to integer pads
    ends = {}
    for (net, r, xcol) in (('vdd', A_rows[0], -3.0), ('vcmd', A_rows[-1], -3.0), ('vcmd', B_rows[0], -3.0), ('vss', B_rows[-1], -5.0)):
        x0 = HL
        m1pad(x0, yc(r))
        B.rect('metal1', xcol - 0.25, yc(r) - 0.25, x0 + 0.25, yc(r) + 0.25)
        via1(xcol, yc(r))
        ends.setdefault(net, []).append((xcol, r))
    # vcmd: the two ends are joined by a Metal2 lane at x = -3 (rows 18 .. 19)
    B.rect('metal2', -3.25, yc(A_rows[-1]) - 0.25, -2.75, yc(B_rows[0]) + 0.25)
    B.fixed_shape(a.M2, (-3.25, yc(A_rows[-1]) - 0.25, -2.75, yc(B_rows[0]) + 0.25), 'vcmd')
    # terminals: Metal2 pads at integer coordinates
    for net, lst in ends.items():
        xcol, r = lst[0]
        ty = int(round(yc(r)))
        tx = int(round(xcol))
        B.rect('metal2', xcol - 0.25, min(yc(r), ty) - 0.25, xcol + 0.25, max(yc(r), ty) + 0.25)
        B.rect('metal2', tx - 0.25, ty - 0.25, tx + 0.25, ty + 0.25)
        B.term(net, 'metal2', a.pad_rect(tx, ty, 0.25))
        B.fixed_shape(a.M2, (xcol - 0.25, min(yc(r), ty) - 0.25, xcol + 0.25, max(yc(r), ty) + 0.25), net)
    B.grow(-6.0, -1.0, LSEG + 3.0, ROWS * PITCH + 1.0)
    B.plates = [(-2.2, -1.5, LSEG + 2.5, ROWS * PITCH + 1.5)]
    B.size = (B.bbox[2] - B.bbox[0], B.bbox[3] - B.bbox[1])
    return B
