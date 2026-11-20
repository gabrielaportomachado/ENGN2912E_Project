"""kpdk.py (LP kit): KLayout-Python helpers for the generated layouts of AFE/layout (common rule 2: no hand-drawn GDS).
Import it from a script that is run by   bash AFE/layout/scripts/kl.sh <script.py> [-rd name=value ...]   (kl.sh sets USER, which the PDK pcell code needs).

What it gives
  lib()                      the GF180MCU pcell library of the PDK (libs.tech/klayout/tech/pymacros), registered once.  FINDING (LP): the pcells DO work in batch mode
                             once the environment variable USER exists (draw_efuse.py reads os.environ["USER"]); AFE/layout/PLAN.md section 2 said gdsfactory fails here.
  pcell(ly, name, **p)       a pcell variant, e.g. pcell(ly, 'cap_mim', mim_option='MIM-B', metal_level='M5', wc=5.0, lc=5.0)
                             names: nfet pfet nfet_06v0_nvt cap_mim cap_nmos metal_resistor ppolyf_u_high_Rs_resistor via_dev ... (PCELLS below lists them at run time)
  put(cell, child, x, y, rot=0, mirror=False)      place an instance (um)
  rect(cell, layer, x1, y1, x2, y2)                a box on a layer of LAYERS (um)
  label(cell, layer, text, x, y)                   a net label on the label datatype of a metal (this is what Magic turns into a pin / port of the cell)
  vias(cell, via, x1, y1, x2, y2)                  fills the box with a legal array of contact / via1..via4 cuts (cut size, spacing and 0.1 um inset from the box edges)
  stack(cell, lo, hi, x1, y1, x2, y2)              metal + via stack from metal `lo` to metal `hi` (1..5) over the box
  write(ly, path)
Layer numbers = libs.tech/klayout/tech/pymacros/cells/layers_def.py (gf180mcuD, 5 metals, MIM option B between Metal4 and Metal5).
Rules worth knowing before drawing (KLayout deck mim_b.drc + the design manual 10.4.2, read 2026-11-20):
  MIMTM.10  no Via3 may touch the MIM bottom plate (Metal4 under FuseTop); the bottom plate is contacted ONLY from above (Via4 -> Metal5) or by a Metal4 wire.
  MIMTM.11  MIM pieces may share one bottom-plate polygon only up to 10,000 um2 of MIM in total: a net that joins more MIM area (REF: 16 pieces) must leave each plate through Via4 / Metal5.
  MIMTM.1   bottom plate to other Metal4 1.2 um;  MIMTM.3 bottom plate overlaps the top plate by 0.6 um;  MIMTM.6 top plates 0.6 um apart;  MIMTM.8a/b 25 .. 10,000 um2 per top plate.
  Guideline "There cannot be any sensitive matching analog circuitry underneath MIM": decap and plain wiring are allowed there.
"""
import os, sys
import pya

PDK_ROOT = os.environ.get('PDK_ROOT', '/foss/pdks')
PDK = os.environ.get('PDK', 'gf180mcuD')
PYMACROS = os.path.join(PDK_ROOT, PDK, 'libs.tech/klayout/tech/pymacros')

LAYERS = {
    'comp': (22, 0), 'dnwell': (12, 0), 'nwell': (21, 0), 'lvpwell': (204, 0), 'dualgate': (55, 0), 'poly2': (30, 0), 'nplus': (32, 0), 'pplus': (31, 0), 'sab': (49, 0),
    'contact': (33, 0), 'metal1': (34, 0), 'via1': (35, 0), 'metal2': (36, 0), 'via2': (38, 0), 'metal3': (42, 0), 'via3': (40, 0), 'metal4': (46, 0), 'via4': (41, 0), 'metal5': (81, 0),
    'fusetop': (75, 0), 'cap_mk': (117, 5), 'mim_l_mk': (117, 10), 'res_mk': (110, 5), 'mos_cap_mk': (166, 5), 'v5_xtor': (112, 1), 'fhres': (227, 0), 'nat': (5, 0),
    'pr_bndry': (0, 0), 'guard_ring_mk': (167, 5),
    'metal1_label': (34, 10), 'metal2_label': (36, 10), 'metal3_label': (42, 10), 'metal4_label': (46, 10), 'metal5_label': (81, 10), 'poly2_label': (30, 10), 'comp_label': (22, 10),
}
METAL = {1: 'metal1', 2: 'metal2', 3: 'metal3', 4: 'metal4', 5: 'metal5'}
VIA = {1: 'via1', 2: 'via2', 3: 'via3', 4: 'via4'}          # VIA[n] joins metal n and metal n+1
CUT = {'contact': (0.22, 0.28), 'via1': (0.26, 0.36), 'via2': (0.26, 0.36), 'via3': (0.26, 0.36), 'via4': (0.26, 0.36)}       # (cut size, spacing used) um; spacing is above the minimum on purpose
_lib = None
PCELLS = []


def lib():
    global _lib, PCELLS
    if _lib is None:
        os.environ.setdefault('USER', 'designer')
        if PYMACROS not in sys.path:
            sys.path.insert(0, PYMACROS)
        L = pya.Library.library_by_name('gf180mcu')
        if L is None:
            import cells                      # noqa: the PDK's pcell package (needs gdsfactory, shipped in the image)
            cells.gf180mcu().register('gf180mcu')
            L = pya.Library.library_by_name('gf180mcu')
        _lib = L
        PCELLS = list(L.layout().pcell_names())
    return _lib


def new_layout():
    ly = pya.Layout()
    ly.dbu = 0.001
    return ly


def li(ly, name):
    l, d = LAYERS[name]
    return ly.layer(l, d)


def pcell(ly, name, **params):
    lib()
    c = ly.create_cell(name, 'gf180mcu', params)
    if c is None:
        raise RuntimeError('pcell %s not found; available: %s' % (name, PCELLS))
    return c


def u(v, ly):
    return int(round(v / ly.dbu))


def put(cell, child, x=0.0, y=0.0, rot=0, mirror=False):
    ly = cell.layout()
    t = pya.Trans(rot // 90, mirror, u(x, ly), u(y, ly))
    return cell.insert(pya.CellInstArray(child.cell_index(), t))


def rect(cell, layer, x1, y1, x2, y2):
    ly = cell.layout()
    cell.shapes(li(ly, layer)).insert(pya.Box(u(min(x1, x2), ly), u(min(y1, y2), ly), u(max(x1, x2), ly), u(max(y1, y2), ly)))


def label(cell, layer, text, x, y):
    """net label; layer = metal1..metal5 (or its *_label name)"""
    ly = cell.layout()
    name = layer if layer.endswith('_label') else layer + '_label'
    cell.shapes(li(ly, name)).insert(pya.Text(text, pya.Trans(u(x, ly), u(y, ly))))


def vias(cell, via, x1, y1, x2, y2, inset=0.1):
    """a legal cut array inside the box (x1,y1)-(x2,y2); returns the number of cuts"""
    size, sp = CUT[via]
    w, h = x2 - x1 - 2 * inset, y2 - y1 - 2 * inset
    nx, ny = int((w + sp) // (size + sp)), int((h + sp) // (size + sp))
    if nx < 1 or ny < 1:
        raise RuntimeError('vias: the box %.2f x %.2f um is too small for one %s cut' % (x2 - x1, y2 - y1, via))
    ox = x1 + inset + (w - (nx * size + (nx - 1) * sp)) / 2.0
    oy = y1 + inset + (h - (ny * size + (ny - 1) * sp)) / 2.0
    for i in range(nx):
        for j in range(ny):
            rect(cell, via, ox + i * (size + sp), oy + j * (size + sp), ox + i * (size + sp) + size, oy + j * (size + sp) + size)
    return nx * ny


def stack(cell, lo, hi, x1, y1, x2, y2):
    """metal lo .. metal hi with all vias between them over the box"""
    for m in range(lo, hi + 1):
        rect(cell, METAL[m], x1, y1, x2, y2)
        if m < hi:
            vias(cell, VIA[m], x1, y1, x2, y2)


def metal_res(cell, m, x, y, length, width, lead=2.0):
    """metal resistor rm<m> (m = 1..3; the strap resistor of Decision 46e is rm3 2 x 222.2 um) drawn in `cell` itself, body from (x, y) to (x + length, y + width), with a
    metal lead of `lead` um at each end.  Returns the two lead centres.
    FINDING (LP): Magic's GDS import builds the device layer as  MET<m> AND RESDEF (110/5) AND MET<m>RES (110/1<m>)  inside ONE cell.  The PDK pcell `metal_resistor` draws only
    110/1<m>, so its Magic extraction is two open metal stubs and NO device.  This helper draws all three shapes in the same cell (KLayout DRC variant D: clean; check_env.sh)."""
    ly = cell.layout()
    rect(cell, METAL[m], x - lead, y, x + length + lead, y + width)
    cell.shapes(ly.layer(110, 10 + m)).insert(pya.Box(u(x, ly), u(y, ly), u(x + length, ly), u(y + width, ly)))
    rect(cell, 'res_mk', x, y, x + length, y + width)
    return (x - lead / 2.0, y + width / 2.0), (x + length + lead / 2.0, y + width / 2.0)


def import_gds(ly, path, cellname):
    """reads another GDS into the layout and returns the cell `cellname` (e.g. TGATE/TGATE.gds, a standard cell of the PDK)"""
    opt = pya.LoadLayoutOptions()
    opt.cell_conflict_resolution = pya.LoadLayoutOptions.CellConflictResolution.RenameCell
    ly.read(path, opt)
    c = ly.cell(cellname)
    if c is None:
        raise RuntimeError('%s has no cell %s' % (path, cellname))
    return c


def write(ly, path, top=None):
    opt = pya.SaveLayoutOptions()
    if top is not None:
        opt.clear_cells()
        opt.add_cell(ly.cell(top).cell_index())
    ly.write(path, opt)
