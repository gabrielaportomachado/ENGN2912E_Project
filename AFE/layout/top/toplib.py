"""toplib.py (L3a): small drawing helpers for AFE/layout/top/mk_top.py on top of AFE/layout/scripts/kpdk.py.
Run only inside KLayout through   bash AFE/layout/scripts/kl.sh AFE/layout/top/mk_top.py ...   (kl_launch.py puts the script directory on sys.path).
Every coordinate is rounded to the 5 nm grid (common rule 2: nothing hand-drawn)."""
import os
import pya
import kpdk as k

G = 0.005


def sn(v):
    return round(round(v / G) * G, 4)


def R(cell, layer, x1, y1, x2, y2):
    k.rect(cell, layer, sn(x1), sn(y1), sn(x2), sn(y2))


def seg(cell, layer, x1, y1, x2, y2, w, cap=True):
    """Manhattan wire of width w between two points (one coordinate equal), square caps of w / 2"""
    h = w / 2.0 if cap else 0.0
    if abs(x1 - x2) < 1e-9:
        R(cell, layer, x1 - w / 2.0, min(y1, y2) - h, x1 + w / 2.0, max(y1, y2) + h)
    elif abs(y1 - y2) < 1e-9:
        R(cell, layer, min(x1, x2) - h, y1 - w / 2.0, max(x1, x2) + h, y1 + w / 2.0)
    else:
        raise ValueError('seg: not Manhattan %s' % ((x1, y1, x2, y2),))


def poly(cell, layer, pts, w):
    """polyline of Manhattan segments"""
    for (a, b) in zip(pts, pts[1:]):
        seg(cell, layer, a[0], a[1], b[0], b[1], w)


def cuts(cell, via, x1, y1, x2, y2, inset=0.07):
    """legal cut array inside the box (cut 0.26, spacing 0.36, inset >= 0.1 from the box edges; tolerant to float noise)"""
    size, sp = 0.26, 0.36
    w, h = x2 - x1 - 2 * inset, y2 - y1 - 2 * inset
    nx, ny = int((w + sp) / (size + sp) + 1e-6), int((h + sp) / (size + sp) + 1e-6)
    if nx < 1 or ny < 1:
        raise RuntimeError('cuts: box %.3f x %.3f too small for one %s cut' % (x2 - x1, y2 - y1, via))
    ox = x1 + (x2 - x1 - (nx * size + (nx - 1) * sp)) / 2.0
    oy = y1 + (y2 - y1 - (ny * size + (ny - 1) * sp)) / 2.0
    for i in range(nx):
        for j in range(ny):
            R(cell, via, ox + i * (size + sp), oy + j * (size + sp), ox + i * (size + sp) + size, oy + j * (size + sp) + size)
    return nx * ny


def stkbox(cell, lo, hi, x1, y1, x2, y2):
    """metal lo .. hi over the box with a legal cut array between each pair"""
    for m in range(lo, hi + 1):
        R(cell, k.METAL[m], x1, y1, x2, y2)
        if m < hi:
            cuts(cell, k.VIA[m], x1, y1, x2, y2)


def stk(cell, x, y, lo, hi, size=0.6, sx=None, sy=None):
    """metal lo .. hi with the vias between, square pad of `size` centred at (x, y) (sx / sy: different width / height)"""
    wx = size if sx is None else sx
    wy = size if sy is None else sy
    stkbox(cell, lo, hi, x - wx / 2.0, y - wy / 2.0, x + wx / 2.0, y + wy / 2.0)


def vias_box(cell, via, x1, y1, x2, y2, inset=0.07):
    return cuts(cell, via, x1, y1, x2, y2, inset)


def lab(cell, layer, text, x, y):
    k.label(cell, layer, text, sn(x), sn(y))


def flat_copy(ly, src, name):
    """a new cell `name` holding the flattened shapes of `src` (no sub-cell instances, no text)"""
    c = ly.create_cell(name)
    for li in ly.layer_indexes():
        reg = pya.Region(src.begin_shapes_rec(li))
        if not reg.is_empty():
            c.shapes(li).insert(reg)
    return c


def import_cells(ly, path, top):
    return k.import_gds(ly, path, top)
