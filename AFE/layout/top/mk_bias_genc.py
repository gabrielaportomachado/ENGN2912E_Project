"""mk_bias_genc.py (L3a): the shared bias cell bias_genc (LVS reference: subckt bias_genc of AFE/layout/lvs/bias_genc.spice).
Run:  bash AFE/layout/scripts/kl.sh AFE/layout/top/mk_bias_genc.py out=AFE/layout/top/bias_genc.gds
Writes bias_genc.gds, bias_genc.build.json and mk_bias_genc.log next to it.  Everything is generated; nothing is drawn by hand.
Blocks (helpers in biaslib.py and in AFE/layout/adc/): ladders A and B (1 um ppolyf_u_1k serpentines), Rb, the beta-multiplier MOS groups, the start-up chain, the reset-level replica,
the reset-level switch, C_VRS (MIM over ladder B) and a grid router (Metal2 .. Metal4) for all connections; the 8 pins are Metal3 pads on the east edge.
"""
import os
import sys
import math
import json
import pya
sys.path.insert(0, os.path.dirname(os.environ['KL_SCRIPT']))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.environ['KL_SCRIPT'])), 'adc'))
import kpdk as k
import adclib as a
import router as RT
import rlib as R
import biaslib as bl

outgds = globals().get('out', 'AFE/layout/top/bias_genc.gds')
outdir = os.path.dirname(outgds) or '.'
os.makedirs(outdir, exist_ok=True)
G = globals()
LOG = []


def log(s):
    print(s)
    LOG.append(s)


def P(name, default):
    return type(default)(G.get(name, default))


ly = k.new_layout()
TOP = ly.create_cell('bias_genc')
PLACED = []                                  # (name, block, dx, dy)
bl.PITCH = P('pitch', 2.0)
bl.GAP = P('gap', 2.0)

# =====================================================================================================================================================================
# blocks
# =====================================================================================================================================================================
LA = bl.ladder(ly, 'lad_a', 29, 'vg1', 'vcm_in', True)           # ra1 = units 1..29, tap vg1, ra2 = units 30..33 (chain E), ra3 = 33 units (chain O)
LB = bl.ladder(ly, 'lad_b', 15, 'vg2', 'vcm_out', False)         # rb1 = 15 units, tap vg2, rb2 = 18 units (chain E), rb3 = 33 units (chain O)
RB = bl.rbres(ly, 'rb_res', nrow=2)
PG = bl.dev_block_m(ly, 'pg', 'pfet', 10.0, 4.0, 8, 'vdd', ['a', 'vbn', 'vbn', 'a'], 'a', 'vdd')            # mp2 (D = a) 4 fingers + mp1 (D = vbn) 4 fingers, ABBA, 8 x 10 um = 2 x 40 um
N2 = a.dev_block(ly, 'n2', 'nfet', P('n2w', 12.8), 4.0, P('n2nf', 5), s_net='r1', d_nets='a', g_net='vbn', bulk_net='vss', ring_gap=1.5)      # mn2: 64 um / 4 um
N1 = a.dev_block(ly, 'n1', 'nfet', 8.0, 4.0, 2, s_net='vss', d_nets='vbn', g_net='vbn', bulk_net='vss', ring_gap=1.5)                         # mn1: 16 um / 4 um (2 x 8 um)
tl = []
x = 0
for (s_, d_, g_, rs) in (('vdd', 's1', 's1', True), ('s1', 's2', 's2', False), ('s2', 'vbn', 'vbn', False)):
    tl.append(dict(kind='pfet', w=0.5, l=4.0, x=x, y=0, s=s_, d=d_, g=g_, ring_s=rs))
    x += P('sup', 7)
SU = a.group_block(ly, 'su', tl, ring_kind='n', ring_net='vdd')                                                                                 # Xs1 .. Xs3
REP = bl.pr1_block(ly, 'rep', 'vcm_in', 'vrs', 'vrs')                                                                                         # Xrep
XSR = a.group_block(ly, 'xsr', [dict(kind='nfet', w=0.28, l=40.0, x=0, y=0, s='vss', d='vrs', g='vbn', extra=dict(con_bet_fin=0), ring_s=True)], ring_kind='p', ring_net='vss')
CV = R.mim_unit_block(ly, 'cvrs', 49.885, 'vrs', 'vss', yb=1, yt=4)
for n, b in (('LA', LA), ('LB', LB), ('RB', RB), ('PG', PG), ('N2', N2), ('N1', N1), ('SU', SU), ('REP', REP), ('XSR', XSR), ('CV', CV)):
    log('block %-3s bbox %s size %s' % (n, [round(v, 2) for v in b.bbox], [round(v, 2) for v in b.size]))
RBR = bl.rotate_block(ly, RB, 'rb_rot')
XSRR = bl.rotate_block(ly, XSR, 'xsr_rot')
SUR = bl.rotate_block(ly, SU, 'su_rot')
REPR = bl.rotate_block(ly, REP, 'rep_rot')


def put(name, blk, x, y):
    """the lower left corner of the bbox of blk at (x, y) or beyond (integer offsets)"""
    dx = math.ceil(x - blk.bbox[0] - 1e-9)
    dy = math.ceil(y - blk.bbox[1] - 1e-9)
    k.put(TOP, blk.cell, dx, dy)
    PLACED.append((name, blk, dx, dy))
    return (dx + blk.bbox[0], dy + blk.bbox[1], dx + blk.bbox[2], dy + blk.bbox[3])


def put_at(name, blk, dx, dy):
    k.put(TOP, blk.cell, dx, dy)
    PLACED.append((name, blk, dx, dy))
    return (dx + blk.bbox[0], dy + blk.bbox[1], dx + blk.bbox[2], dy + blk.bbox[3])


# =====================================================================================================================================================================
# placement
# =====================================================================================================================================================================
W = P('W', 108)
H = P('H', 116)
yB = P('yB', 3)
bb = {}
bb['LB'] = put_at('LB', LB, -1, yB)
bb['LA'] = put_at('LA', LA, -1, yB + 2 * bl.NROW + 2)
CVX, CVY = P('cvx', 32), P('cvy', 1)
bb['CV'] = put_at('CV', CV, CVX, CVY)
ytop = bb['LA'][3]
YB0 = math.ceil(ytop + P("ygap", 0.0))
bb['PG'] = put('PG', PG, 1.0, YB0)
bb['N2'] = put('N2', N2, bb['PG'][2] + 1.5, YB0)
bb['N1'] = put('N1', N1, bb['N2'][2] + 1.5, YB0)
XE = math.ceil(bb['LB'][2]) + 2
bb['XSR'] = put('XSR', XSRR, XE, 1.0)
bb['SU'] = put('SU', SUR, XE, bb['XSR'][3] + 1.5)
bb['RB'] = put('RB', RBR, bb['XSR'][2] + 2.0, 1.0)
bb['REP'] = put('REP', REPR, bb['RB'][0], bb['RB'][3] + 1.5)
for n, b in bb.items():
    log('placed %-3s x %.1f .. %.1f  y %.1f .. %.1f' % (n, b[0], b[2], b[1], b[3]))

# =====================================================================================================================================================================
# router: obstacles, terminals, pins
# =====================================================================================================================================================================
PIN_X = 107
PINS = [('vdd', P('y_vdd', 112)), ('vss', P('y_vss', 103)), ('vcm_in', P('y_vcm_in', 91)), ('vg1', P('y_vg1', 82)), ('vbn', P('y_vbn', 70)),
        ('vcm_out', P('y_vcm_out', 44)), ('vg2', P('y_vg2', 19)), ('vrs', P('y_vrs', 8))]
rt = RT.Router(1.0, 1.0, float(PIN_X), float(H - 1))
for (name, blk, dx, dy) in PLACED:
    for (l, r, n, ex) in blk.fixed:
        rt.obstacle(l, (r[0] + dx, r[1] + dy, r[2] + dx, r[3] + dy), n, extra=ex)
    for (n, c, r) in blk.terms:
        rt.terminal(n, c, (r[0] + dx, r[1] + dy, r[2] + dx, r[3] + dy))
    if hasattr(blk, 'mim'):
        pl = blk.mim['plate']
        pl = (pl[0] + dx, pl[1] + dy, pl[2] + dx, pl[3] + dy)
        rt.block_all(pl, layers=(1,))                    # no Metal3 under the plate; Metal2 (ladder lanes, taps) is allowed
        rt.obstacle(2, pl, None, extra=0.9)              # Metal4 keeps MIMTM.1 clearance
for (n, y) in PINS:
    rt.terminal(n, 'metal3', a.pad_rect(PIN_X, y, 0.5))
    rt.obstacle(1, (PIN_X - 1.0, y - 1.0, PIN_X + 1.0, y + 1.0), n, extra=0.3)
rt.reserve()
nets = list(rt.terms.keys())
log('nets: ' + ', '.join('%s(%d)' % (n, len(rt.terms[n])) for n in nets))
FIRST = ['vrs', 'vbn', 'a', 'r1', 'vcm_in', 'vg1', 'vg2', 'vcm_out', 's1', 's2']
POWER = ['vss', 'vdd']
order = [n for n in FIRST if n in rt.terms] + [n for n in nets if n not in FIRST and n not in POWER] + [n for n in POWER if n in rt.terms]
bad = []
for n in order:
    if not rt.route_net(n):
        bad.append(n)
log('routing: %d nets, %d failed: %s' % (len(order), len(bad), bad))
for f in rt.failed:
    log('  FAILED ' + str(f)[:400])
sh = rt.shapes()
for net, d in sh.items():
    for (lname, r) in d['wires']:
        k.rect(TOP, lname, *r)
    for (vname, r) in d['vias']:
        k.rect(TOP, vname, *r)
for (net, (x_, y_)) in rt.access_vias():
    k.rect(TOP, 'metal1', x_ - 0.25, y_ - 0.25, x_ + 0.25, y_ + 0.25)
    k.rect(TOP, 'via1', x_ - 0.13, y_ - 0.13, x_ + 0.13, y_ + 0.13)
for (n, y) in PINS:
    k.rect(TOP, 'metal3', PIN_X - 1.0, y - 1.0, PIN_X + 1.0, y + 1.0)
    k.label(TOP, 'metal3', n, PIN_X, y)

# =====================================================================================================================================================================
# finish: cell names get the prefix bg_ (no clash when the cell is merged into afe_ch), the cell is moved to the origin (5 nm grid), build summary and log
# =====================================================================================================================================================================
for c in ly.each_cell():
    if c.cell_index() != TOP.cell_index() and not c.name.startswith('bg_'):
        c.name = 'bg_' + c.name
cb = TOP.dbbox()
sx, sy = round(cb.left / 0.005) * 0.005, round(cb.bottom / 0.005) * 0.005
TOP.transform(pya.Trans(-k.u(sx, ly), -k.u(sy, ly)))
cb = TOP.dbbox()
Wc, Hc = cb.width(), cb.height()
log('cell bbox %.3f .. %.3f x %.3f .. %.3f  =  %.3f x %.3f um (limit 108 x 116.24)  area %.1f um2' % (cb.left, cb.right, cb.bottom, cb.top, Wc, Hc, Wc * Hc))
assert Wc <= 108.0 and Hc <= 116.24, 'cell too large'
labs = []
for sh_ in TOP.shapes(k.li(ly, 'metal3_label')).each():
    if sh_.is_text():
        labs.append((sh_.text_string, round(sh_.text_dpos.x, 3), round(sh_.text_dpos.y, 3)))
log('labels on the top cell: %s' % labs)
k.write(ly, outgds, 'bias_genc')

blocks = {}
AREA = {}
for (name, blk, dx, dy) in PLACED:
    x1, y1, x2, y2 = dx + blk.bbox[0] - sx, dy + blk.bbox[1] - sy, dx + blk.bbox[2] - sx, dy + blk.bbox[3] - sy
    area = (x2 - x1) * (y2 - y1)
    ring = 0.0
    if name in ('PG', 'N2', 'N1', 'SU', 'XSR'):
        w_, h_ = blk.size if name not in ('SU', 'XSR') else (blk.size if blk.size[0] > blk.size[1] else (blk.size[1], blk.size[0]))
        ring = 2 * (w_ + h_) * 0.42
    blocks[name] = dict(bbox=[round(v, 3) for v in (x1, y1, x2, y2)], W=round(x2 - x1, 3), H=round(y2 - y1, 3), area_um2=round(area, 1), tie_ring_comp_um2=round(ring, 1))
log('block areas (bbox, um2): ' + ', '.join('%s %.0f' % (n, v['area_um2']) for n, v in blocks.items()))
log('tie rings (comp 0.42 um wide, centre-line perimeter): ' + ', '.join('%s %.1f' % (n, v['tie_ring_comp_um2']) for n, v in blocks.items() if v['tie_ring_comp_um2']) + ' um2, total %.1f' % sum(v['tie_ring_comp_um2'] for v in blocks.values()))
pins = {n: dict(label_xy=[round(PIN_X - sx, 3), round(y - sy, 3)], pad_m3=[round(PIN_X - 1.0 - sx, 3), round(y - 1.0 - sy, 3), round(PIN_X + 1.0 - sx, 3), round(y + 1.0 - sy, 3)]) for (n, y) in PINS}
wire = {n: round(sum(len(p) for p in rt.paths.get(n, [])) * 1.0, 1) for n in rt.paths}
info = dict(cell='bias_genc', W=round(Wc, 3), H=round(Hc, 3), area_um2=round(Wc * Hc, 1), limit=[108, 116.24], bbox=[round(v, 3) for v in (cb.left, cb.bottom, cb.right, cb.top)],
            shift_applied=[round(-sx, 3), round(-sy, 3)], blocks=blocks, pins=pins, failed=bad, wire_um=wire,
            ladders=dict(unit_um=bl.UL, units_per_row=bl.NU, rows=bl.NROW, pitch_um=bl.PITCH, unit_gap_um=bl.GAP, A=dict(ra1=29, ra2=4, ra3=33), B=dict(rb1=15, rb2=18, rb3=33), Rb='2 rows of 60 um x 2 um'),
            mim=dict(w=49.885, top='vrs', bottom='vss', over='ladder B'))
json.dump(info, open(os.path.join(outdir, 'bias_genc.build.json'), 'w'), indent=1)
open(os.path.join(outdir, 'mk_bias_genc.log'), 'w').write('\n'.join(LOG) + '\n')
