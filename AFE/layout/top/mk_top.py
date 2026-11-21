"""mk_top.py (L3a): the chip dbs_afe_top, 605 x 1110 um, 4 channels, 20 pads (REC[3:0] back), from AFE/layout/floorplan.json.
Run:  bash AFE/layout/scripts/kl.sh AFE/layout/top/mk_top.py out=AFE/layout/top/dbs_afe_top.gds [stage=N] [decap=0|1]
Contents: 4 x afe_ch (mk_afe_ch.py: adc_ch + amp_ch + 2 TGATE + corridors), afe_dig (AFE/dig/final/afe_dig.gds), bias_genc (bias_genc.gds, mk_bias_genc.py),
the strap corridors (ADC-main VDD, ADC-DAC vdd_dac, vss on Metal5; control wires Metal2; jogs and the rst_amp trunk Metal3; rm3 strap resistor), the pin ring with the 37 pin bits,
the bias corridors (7 Metal2 lines between vss lines, analog vdd Metal4 strap), the east / west ring trunks and the decap (74 units on VDD, 30 on vdd_dac).
Every coordinate is on the 5 nm grid; all geometry comes from this script (common rule 2)."""
import os
import sys
import json
import re
import pya
sys.path.insert(0, os.path.dirname(os.environ['KL_SCRIPT']))
import kpdk as k
import toplib as T
import mk_afe_ch as A

HERE = os.path.dirname(os.path.abspath(os.environ['KL_SCRIPT']))
REPO = os.path.normpath(os.path.join(HERE, '..', '..', '..'))
FP = json.load(open(os.path.join(REPO, 'AFE/layout/floorplan.json')))
PINS_DIG = {q['name']: q for q in json.load(open(os.path.join(REPO, 'AFE/dig/final/afe_dig_pins.json')))['pins']}
STAGE = int(globals().get('stage', '99'))
DECAP = int(globals().get('decap', '1'))
outgds = globals().get('out', 'AFE/layout/top/dbs_afe_top.gds')

W, H = FP['outline'][2], FP['outline'][3]
PL = {q['inst']: q for q in FP['placements']}
DIG = PL['u_dig']
BIAS = PL['u_bias']
DX, DY, DW, DH = DIG['x'], DIG['y'], DIG['w'], DIG['h']
DUNIT = FP['params']['decap_unit']

ly = k.new_layout()
TOP = ly.create_cell('dbs_afe_top')
R = lambda layer, x1, y1, x2, y2: T.R(TOP, layer, x1, y1, x2, y2)
seg = lambda layer, x1, y1, x2, y2, w, cap=True: T.seg(TOP, layer, x1, y1, x2, y2, w, cap)
stk = lambda x, y, lo, hi, size=0.6, sx=None, sy=None: T.stk(TOP, x, y, lo, hi, size, sx, sy)
lab = lambda layer, t, x, y: T.lab(TOP, layer, t, x, y)
LOG = []


def log(*a):
    LOG.append(' '.join(str(x) for x in a))
    print(*a)


# ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------
# cells
# ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------
amp_c, adc_c, tg_c = A.load_cells(ly)
afe_c = A.build_afe_ch(ly, amp_c, adc_c, tg_c)
dig_c = k.import_gds(ly, os.path.join(REPO, 'AFE/dig/final/afe_dig.gds'), 'afe_dig')
bias_c = k.import_gds(ly, os.path.join(REPO, 'AFE/layout/top/bias_genc.gds'), 'bias_genc')
BB = bias_c.dbbox()
BX0, BY0 = 471.5, 497.5                         # bias_genc 107.25 x 115.10 um inside its region (471, 496.88, 579, 613.12)
k.put(TOP, dig_c, DX, DY)
k.put(TOP, bias_c, BX0, BY0)
SLOT = {}
for n in range(4):
    q = PL['ch%d' % n]
    SLOT[n] = q
    if q['orient'] == 'R0':
        k.put(TOP, afe_c, q['x'], q['y'])
    else:
        k.put(TOP, afe_c, q['x'], q['y'] + q['h'], mirror=True)       # MX: y -> q.y + h - y
log('placed: afe_dig at (%g, %g) %g x %g, bias_genc at (%g, %g) %.2f x %.2f, 4 x afe_ch' % (DX, DY, DW, DH, BX0, BY0, BB.width(), BB.height()))


def chy(n, ylocal):
    """absolute y of a slot-local y of channel n"""
    q = SLOT[n]
    return q['y'] + ylocal if q['orient'] == 'R0' else q['y'] + q['h'] - ylocal


def chx(n, xlocal):
    return SLOT[n]['x'] + xlocal


# ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------
# strap corridors: side s = +1 north (macro top edge DY + DH), -1 south (macro bottom edge DY); yc = distance from the macro edge
# ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------
SIDES = {1: dict(y0=DY + DH, chs=(0, 1)), -1: dict(y0=DY, chs=(2, 3))}
YC_VSS = (0.8, 6.3)
YC_VDD = (7.3, 15.3)
YC_DAC = (16.3, 21.3)
YC_JOG = {'sw_rec': 3.2, 'sw_rec_b': 4.6, 'sw_ipg': 6.0, 'sw_ipg_b': 7.4}
YC_RST = 10.5
YC_RM3 = (12.5, 14.5)
X_STRAP_W = 22.5
FORB_M2 = []          # (x1, x2) of Metal2 verticals in the strap corridors (all sides): for the decap stacks
FORB_M4 = []          # Metal4 stubs


def ya(s, yc):
    return SIDES[s]['y0'] + s * yc


def RC(s, layer, x1, yc1, x2, yc2):
    y1, y2 = ya(s, yc1), ya(s, yc2)
    R(layer, x1, min(y1, y2), x2, max(y1, y2))


def SC(s, layer, x1, yc1, x2, yc2, w, cap=True):
    seg(layer, x1, ya(s, yc1), x2, ya(s, yc2), w, cap)


def stkc(s, x, yc, lo, hi, size=0.6, sx=None, sy=None):
    stk(x, ya(s, yc), lo, hi, size, sx, sy)


def build_corridor(s):
    S = SIDES[s]
    y0 = S['y0']
    # --- straps (Metal5)
    RC(s, 'metal5', X_STRAP_W, YC_VSS[0], 458.5, YC_VSS[1])
    RC(s, 'metal5', 3.0, YC_VDD[0], 445.0, YC_VDD[1])
    RC(s, 'metal5', 30.0, YC_DAC[0], 465.0, YC_DAC[1])
    # VSS strap to the west ring vss trunk (Metal4): stub + via4 box
    RC(s, 'metal4', 19.0, 1.5, 25.0, 4.5)
    T.stkbox(TOP, 4, 5, 22.6, min(ya(s, 1.5), ya(s, 4.5)), 25.0, max(ya(s, 1.5), ya(s, 4.5)))
    # --- macro supply stripes -> straps
    for nm, strap in (('VDD', YC_VDD), ('VSS', YC_VSS)):
        for q in __import__('json').load(open(os.path.join(REPO, 'AFE/dig/final/afe_dig_pins.json')))['power'][nm]:
            if abs(q['y1_um'] - q['y0_um']) < 80.0:
                continue                                                   # the full-height stripe (the two edge stubs are 0.28 um tall)
            x1, x2 = DX + q['x0_um'], DX + q['x1_um']
            yc_t = (strap[0] + strap[1]) / 2.0 + (1.0 if nm == 'VDD' else 0.0)
            RC(s, 'metal4', x1, -0.3, x2, yc_t + 1.5)
            T.stkbox(TOP, 4, 5, x1, min(ya(s, yc_t - 1.5), ya(s, yc_t + 1.5)), x2, max(ya(s, yc_t - 1.5), ya(s, yc_t + 1.5)))
            FORB_M4.append((x1 - 0.7, x2 + 0.7, s))
    # --- channels of this side
    for n in S['chs']:
        sx = SLOT[n]['x']
        kk = n % 2
        # ADC control wires: macro pin -> adc pin stub of the slot (Metal2, 0.5 wide at the adc pin x)
        for nm in A.ADC_CTRL:
            m = re.match(r'(dac_g[pn])\[(\d+)\]', nm)
            mn = ('%s[%d]' % (m.group(1), 12 * n + int(m.group(2)))) if m else '%s[%d]' % (nm, n)
            xa = sx + A.adc_pin_x(nm)
            SC(s, 'metal2', xa, -1.0, xa, 25.5, 0.5, cap=False)
            FORB_M2.append((xa - 0.8, xa + 0.8))
        # sw jogs: macro pin (x_m) -> Metal3 west -> corridor line (slot x of A.CORR)
        for nm in ('sw_rec', 'sw_rec_b', 'sw_ipg', 'sw_ipg_b'):
            q = PINS_DIG['%s[%d]' % (nm, n)]
            xm = DX + 0.5 * (q['rect_um'][0] + q['rect_um'][2])
            xl = sx + A.CORR[nm]
            yj = YC_JOG[nm]
            SC(s, 'metal2', xm, -1.0, xm, yj, 0.5)
            stkc(s, xm, yj, 2, 3, size=0.5)
            SC(s, 'metal3', xm, yj, xl, yj, 0.5)
            stkc(s, xl, yj, 2, 3, size=0.5)
            SC(s, 'metal2', xl, yj, xl, 25.5, 0.5, cap=False)
            FORB_M2.append((min(xm, xl) - 0.8, min(xm, xl) + 0.8))
            FORB_M2.append((xm - 0.8, xm + 0.8))
            FORB_M2.append((xl - 0.8, xl + 0.8))
        # rst_amp: the Metal3 trunk meets the corridor line
        xr = sx + A.CORR['rst_amp']
        stkc(s, xr, YC_RST, 2, 3, size=0.5)
        SC(s, 'metal2', xr, YC_RST, xr, 25.5, 0.5, cap=False)
        FORB_M2.append((xr - 0.8, xr + 0.8))
        FORB_M2.append((sx + A.VSS_LINE_X - 0.8, sx + A.VSS_LINE_X + 0.8))
        # adc supply stubs (Metal4) down to the straps
        for (x1, x2, yc_from, yc_to, strap) in ((sx + 127.0, sx + 129.0, 25.5, 12.5, YC_VDD), (sx + 157.0, sx + 159.0, 25.5, 18.8, YC_DAC), (sx + 193.0, sx + 195.0, 26.5, 3.5, YC_VSS)):
            RC(s, 'metal4', x1, yc_to - 1.5, x2, yc_from)
            T.stkbox(TOP, 4, 5, x1, min(ya(s, yc_to - 1.5), ya(s, yc_to + 1.5)), x2, max(ya(s, yc_to - 1.5), ya(s, yc_to + 1.5)))
            FORB_M4.append((x1 - 0.7, x2 + 0.7, s))
    # rst_amp trunk Metal3: from the west ring to the last channel line
    xs = [SLOT[n]['x'] + A.CORR['rst_amp'] for n in S['chs']]
    SC(s, 'metal3', 22.9, YC_RST, max(xs), YC_RST, 0.5)
    stkc(s, 22.9, YC_RST, 2, 3, size=0.5)
    # strap resistor (north only): rm3 2 x 222.2 um
    if s == 1:
        xb, yb = 26.0, ya(s, YC_RM3[0])
        k.metal_res(TOP, 3, xb, yb, 222.2, 2.0, lead=2.0)
        stkc(s, 25.0, 13.5, 3, 5, size=1.6)                                 # west lead -> VDD-main strap
        xe = xb + 222.2 + 1.0
        seg('metal3', xe, ya(s, 13.5), xe, ya(s, 18.8), 1.2)
        stkc(s, xe, 18.8, 3, 5, size=1.6)                                   # east lead -> vdd_dac strap
        FORB_M4.append((24.0, 26.2, s))
        FORB_M4.append((xe - 1.2, xe + 1.2, s))


for s in (1, -1):
    build_corridor(s)
R('metal5', 460.0, ya(-1, YC_DAC[1]), 465.0, ya(1, YC_DAC[1]))              # vdd_dac: north strap <-> south strap (east of the macro)
log('strap corridors drawn')

# ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------
# decap unit (cap_nmos_03v3 20 x 20 um: pcell + a P+ tap strip below its S/D bar)
# ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------
DEC = k.pcell(ly, 'cap_nmos', volt='3.3V', lc=20.0, wc=20.0)
NDEC = {'VDD': 0, 'vdd_dac': 0}


def decap_unit(x, y, net):
    k.put(TOP, DEC, x, y)
    # tap strip (substrate, vss) below the unit: comp + P+ + contacts + Metal1 merged with the S/D bar
    R('comp', x + 1.0, y - 2.6, x + 19.9, y - 2.1)
    R('pplus', x + 0.7, y - 2.9, x + 20.2, y - 1.8)
    k.vias(TOP, 'contact', T.sn(x + 1.0), T.sn(y - 2.6), T.sn(x + 19.9), T.sn(y - 2.1), inset=0.14)
    R('metal1', x + 0.9, y - 2.8, x + 20.0, y - 1.9)
    NDEC[net] += 1


def gate_xy(x, y, forb2, forb4, ys=None, lo=0.8, hi=20.0):
    """a stack position inside the gate Metal1 pad of the unit at (x, y): first x (step 0.5) whose Metal2 / Metal4 pads clear the forbidden intervals"""
    cx = x + lo
    while cx <= x + hi:
        ok = all(not (a < cx + 0.2 and cx - 0.2 < b) for (a, b) in forb2) and all(not (a < cx + 0.2 and cx - 0.2 < b) for (a, b) in forb4)
        if ok:
            return cx
        cx += 0.1
    return None


# ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------
# corridor decap rows: 15 units on vdd_dac (x = 26 + 24 j, j = 0 .. 14) and 2 on VDD (j = 15, 16) in each corridor
# ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------
YU = 3.52             # distance of the unit origin (comp bottom) from the corridor edge on the adc side (north: from the macro edge + 3.44, see below)


def corridor_decap(s):
    for j in range(17):
        x = 26.0 + 24.0 * j
        net = 'vdd_dac' if j < 15 else 'VDD'
        y = ya(s, 3.44) if s == 1 else SIDES[-1]['y0'] - 25.0 + YU
        decap_unit(x, y, net)
        m4 = [(a, b) for (a, b, ss) in FORB_M4 if ss == s]
        xg = gate_xy(x, y, FORB_M2, m4)
        if xg is None:
            log('WARNING no free gate stack x for the corridor unit at', x, s)
            continue
        ygate = ya(s, 9.0 if net == 'VDD' else 19.0)
        T.stkbox(TOP, 1, 5, xg - 0.2, ygate - 0.2, xg + 0.2, ygate + 0.2)
        FORB_M4.append((xg - 0.7, xg + 0.7, s))
        # vss: Metal1 -> Metal5 vss strap on the left S/D vertical of the unit (x - 0.13)
        yv = ya(s, 1.85)
        T.stkbox(TOP, 1, 5, x - 0.33, yv - 0.2, x + 0.07, yv + 0.2)


if DECAP and STAGE >= 3:
    for s in (1, -1):
        corridor_decap(s)
log('corridor decap done: %s' % NDEC)

# ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------
# west ring: pins, VDD / VSS pads and trunks, rst_amp, decap bank
# ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------
PINW = [q for q in FP['pins'] if q['side'] == 'W']
PIN_WIRE_Y = []
for q in PINW:
    nm = q['name']
    if nm in ('VDD', 'VSS'):
        continue
    yp = q['y']
    if nm == 'DOUT_IN':
        R('metal3', 0.0, yp - 0.3, 2.0, yp + 0.3)
        lab('metal3', nm, 1.0, yp)
        continue
    mname = 'DOUT' if nm == 'DOUT_OUT' else nm
    qm = PINS_DIG[mname]
    ym = DY + 0.5 * (qm['rect_um'][1] + qm['rect_um'][3])
    seg('metal3', 0.0, yp, 20.0, yp, 0.56, cap=False)
    seg('metal3', 20.0, yp, 20.0, ym, 0.56)
    seg('metal3', 20.0, ym, DX + 1.0, ym, 0.56, cap=False)
    lab('metal3', nm, 1.0, yp)
    PIN_WIRE_Y += [yp, ym]
# rst_amp_o: macro west pin -> Metal3 west -> Metal2 vertical x = 22.9 to both corridor trunks
q = PINS_DIG['rst_amp_o']
y_rst = DY + 0.5 * (q['rect_um'][1] + q['rect_um'][3])
seg('metal3', 22.9, y_rst, DX + 1.0, y_rst, 0.5, cap=False)
stk(22.9, y_rst, 2, 3, size=0.5)
seg('metal2', 22.9, ya(-1, YC_RST), 22.9, ya(1, YC_RST), 0.5)
PIN_WIRE_Y.append(y_rst)
# VDD pad (Metal5) / VSS pad (Metal4) and the trunks
VDD_Y, VSS_Y = [q['y'] for q in PINW if q['name'] == 'VDD'][0], [q['y'] for q in PINW if q['name'] == 'VSS'][0]
R('metal5', 0.0, VDD_Y - 10.0, 21.0, VDD_Y + 10.0)
lab('metal5', 'VDD', 2.0, VDD_Y)
R('metal4', 0.0, VSS_Y - 10.0, 21.0, VSS_Y + 10.0)
lab('metal4', 'VSS', 2.0, VSS_Y)
YB0, YB1 = 44.0, 1010.0
R('metal5', 3.0, YB0, 11.0, YB1)                         # VDD-main trunk (decap bank, both strap corridors)
R('metal5', 13.0, 26.0, 21.0, 1084.0)                     # analog VDD trunk (to both bias corridors)
R('metal4', 12.5, 40.0, 20.5, 1070.0)                     # VSS trunk
FORB_W3 = [(y - 0.65, y + 0.65) for y in PIN_WIRE_Y]


def free_y(lo, hi, forb, step=0.1, half=0.2):
    y = lo
    while y <= hi:
        if all(not (a < y + half and y - half < b) for (a, b) in forb):
            return y
        y += step
    return None


NBANK = 0
bank_y = []
if DECAP and STAGE >= 3:
    js = [j for j in range(40) if j not in (18, 19)]
    for j in js:
        x, y = 4.0, 44.0 + 24.0 * j
        decap_unit(x, y, 'VDD')
        bank_y.append(y)
        yg = free_y(y + 0.5, y + 19.5, FORB_W3)
        if yg is None:
            log('WARNING bank unit at y=%g: no free y for the gate stack' % y)
            continue
        T.stkbox(TOP, 1, 5, 7.3, yg - 0.2, 7.7, yg + 0.2)                # gate Metal1 -> Metal5 VDD-main trunk (x 3 .. 11)
        ys = free_y(y - 1.7, y + 19.5, FORB_W3)
        if ys is None:
            log('WARNING bank unit at y=%g: no free y for the vss stack' % y)
            continue
        T.stkbox(TOP, 1, 4, 25.1, ys - 0.2, 25.5, ys + 0.2)               # S/D rail (Metal1) -> Metal4 stub to the vss trunk
        R('metal4', 20.0, ys - 0.25, 25.5, ys + 0.25)
    # Metal1 rail joining the S/D right verticals of the bank
    R('metal1', 24.9, min(bank_y) - 2.8, 25.7, max(bank_y) + 19.88)
log('west bank: %d units' % len(bank_y))

# ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------
# bias corridors (N: y 1072 .. 1084, S: 26 .. 38) and the east ring (VDD / VSS Metal5 trunks, 7 Metal3 bias lines)
# ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------
BSIG = ['vbn', 'vcm', 'vg1', 'vcmo', 'vg2', 'vrs', 'REF']
EV = {n: 598.25 + i for i, n in enumerate(BSIG)}             # x of the east ring Metal3 verticals
Y0N, Y0S = 1072.0, 38.0
XVSS_E = 594.0
R('metal5', 581.0, 26.0, 588.0, 1084.0)                        # analog VDD trunk (east)
R('metal5', 589.5, 26.0, 596.5, 1084.0)                        # VSS trunk (east)


def U(i):
    return 0.4 + 0.75 * i


for s, Y0, chs in ((1, Y0N, (0, 1)), (-1, Y0S, (2, 3))):
    def yl(u, s=s, Y0=Y0):
        return Y0 + s * u
    # analog vdd strap (Metal4) u 0.3 .. 8.8, tied to both trunks (Metal5) by via4 boxes
    R('metal4', 13.0, min(yl(0.3), yl(8.8)), 585.0, max(yl(0.3), yl(8.8)))
    T.stkbox(TOP, 4, 5, 14.0, min(yl(0.8), yl(8.3)), 20.0, max(yl(0.8), yl(8.3)))
    T.stkbox(TOP, 4, 5, 582.0, min(yl(0.8), yl(8.3)), 587.0, max(yl(0.8), yl(8.3)))
    # vss lines (even i), signal lines (odd i)
    for i in range(15):
        y = yl(U(i))
        if i % 2 == 0:
            seg('metal2', 22.8, y, XVSS_E, y, 0.4)
        else:
            n = BSIG[i // 2]
            xw = (chx(chs[0], 121.0) - 0.5) if n == 'REF' else (chx(chs[0], 9.0 + i // 2) - 0.5)
            seg('metal2', xw, y, EV[n], y, 0.4)
            stk(EV[n], y, 2, 3, size=0.46)
    for n in chs:
        for idx, nm in enumerate(BSIG[:6]):
            x = chx(n, 9.0 + idx)
            y = yl(U(2 * idx + 1))
            seg('metal3', x, yl(-0.3), x, y, 0.5)
            stk(x, y, 2, 3, size=0.46)
        # REF: Metal5 vertical + stack down to the Metal2 line
        xr = chx(n, 121.0)
        y = yl(U(13))
        R('metal5', xr - 0.6, min(yl(-0.3), y), xr + 0.6, max(yl(-0.3), y))
        stk(xr, y, 2, 5, size=0.6)
        # spur: analog vdd (Metal4) into the strap, vss (Metal3) up to the vss lines
        R('metal4', chx(n, 230.5), min(yl(-0.3), yl(8.5)), chx(n, 233.5), max(yl(-0.3), yl(8.5)))
        xs = chx(n, 235.4)
        seg('metal3', xs, yl(-0.3), xs, yl(U(14)), 1.0)
        for i in range(0, 15, 2):
            stk(xs, yl(U(i)), 2, 3, size=0.7)
    # west tie of the vss lines to the VSS trunk (Metal4, x 12.5 .. 20.5; it ends at y = 40 / 1070)
    seg('metal3', 22.8, yl(U(0)), 22.8, yl(U(14)), 0.5)
    for i in range(0, 15, 2):
        stk(22.8, yl(U(i)), 2, 3, size=0.5)
    ytie = 1069.8 if s == 1 else 40.2
    seg('metal3', 22.8, ytie, 22.8, yl(U(0)), 0.5)
    stk(22.8, ytie, 3, 4, size=0.5)
    R('metal4', 19.0, ytie - 0.3, 23.3, ytie + 0.3)
    # east tie: Metal3 bar x = 594 + via stack into the VSS trunk
    seg('metal3', XVSS_E, yl(U(0)), XVSS_E, yl(11.5), 0.5)
    for i in range(0, 15, 2):
        stk(XVSS_E, yl(U(i)), 2, 3, size=0.5)
    T.stkbox(TOP, 3, 5, XVSS_E - 0.5, min(yl(11.2), yl(11.9)), XVSS_E + 0.5, max(yl(11.2), yl(11.9)))
for n in BSIG:
    i = BSIG.index(n)
    seg('metal3', EV[n], Y0S - U(2 * i + 1) - 0.4, EV[n], Y0N + U(2 * i + 1) + 0.4, 0.5)
# bias_genc pins -> feeders (Metal4) to the Metal3 verticals / the Metal5 trunks
BPIN = {'vdd': 111.6, 'vss': 102.6, 'vcm_in': 90.6, 'vg1': 81.6, 'vbn': 69.6, 'vcm_out': 43.6, 'vg2': 18.6, 'vrs': 7.6}
BMAP = {'vbn': 'vbn', 'vcm_in': 'vcm', 'vg1': 'vg1', 'vcm_out': 'vcmo', 'vg2': 'vg2', 'vrs': 'vrs'}
for nm, yy in BPIN.items():
    xp, yp = BX0 + 106.25, BY0 + yy
    stk(xp, yp, 3, 4, size=1.2)
    if nm in BMAP:
        xe = EV[BMAP[nm]]
        seg('metal4', xp, yp, xe, yp, 0.5, cap=False)
        stk(xe, yp, 3, 4, size=0.5)
    elif nm == 'vdd':
        seg('metal4', xp, yp, 584.5, yp, 1.0, cap=False)
        T.stkbox(TOP, 4, 5, 583.5, yp - 0.5, 585.5, yp + 0.5)
    else:
        seg('metal4', xp, yp, 593.0, yp, 1.0, cap=False)
        T.stkbox(TOP, 4, 5, 592.0, yp - 0.5, 594.0, yp + 0.5)
# REF pad (east edge) -> Metal3 vertical of REF
R('metal5', 603.0, 554.0, 605.0, 556.0)
stk(EV['REF'], 555.0, 3, 5, size=0.6)
lab('metal5', 'REF', 604.0, 555.0)

# ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------
# pad wires of the channels (E, REC, IPG: Metal5, 2 um) and labels
# ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------
for n in range(4):
    for nm, xl in (('E', 70.0), ('REC', 118.0), ('IPG', 165.0)):
        x = chx(n, xl)
        if SLOT[n]['orient'] == 'R0':
            R('metal5', x - 1.0, Y0N - 0.5, x + 1.0, H)
            lab('metal5', '%s[%d]' % (nm, n), x, H - 1.0)
        else:
            R('metal5', x - 1.0, 0.0, x + 1.0, Y0S + 0.5)
            lab('metal5', '%s[%d]' % (nm, n), x, 1.0)
R('pr_bndry', 0.0, 0.0, W, H)

# ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------
# decap rows with Metal2 gate rails: 4 units under the Cref plate of every adc_ch (VDD via the analog spur) and 8 + 8 units in the two spare regions east of the channels (analog VDD trunk)
# ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------
def decap_row(xs, y, net_gate_exit, vss_exit, ngate_via=2):
    """units at origins (xs[i], y) in a row: bridge the S/D bars (Metal1), gate rail (Metal2, y + 10) to x = net_gate_exit[0] with a stack Metal2 .. net_gate_exit[1],
    S/D bar (Metal1) east to x = vss_exit[0] with a stack Metal1 .. vss_exit[1]"""
    for x in xs:
        decap_unit(x, y, 'VDD')
        for xv in (x + 6.0, x + 14.0):
            T.cuts(TOP, 'via1', xv - 0.13, y + 10.0 - 0.13, xv + 0.13, y + 10.0 + 0.13, inset=0.0)
            R('metal2', xv - 0.2, y + 9.8, xv + 0.2, y + 10.2)
            R('metal1', xv - 0.2, y + 9.8, xv + 0.2, y + 10.2)
    for a_, b_ in zip(xs, xs[1:]):
        R('metal1', a_ + 21.0, y - 1.9, b_ - 0.2, y - 1.0)
    seg('metal2', xs[0] + 6.0, y + 10.0, net_gate_exit[0], y + 10.0, 0.5, cap=False)
    stk(net_gate_exit[0], y + 10.0, 2, net_gate_exit[1], size=0.6)
    R('metal1', xs[-1] + 21.0, y - 1.9, vss_exit[0] + 0.6, y - 1.0)
    stk(vss_exit[0], y - 1.45, 1, vss_exit[1], size=0.9)


if DECAP and STAGE >= 3:
    # fusetop (75/0) polygon of the Cref plate in adc_ch (59.07 um square)
    reg = pya.Region(adc_c.begin_shapes_rec(ly.find_layer(75, 0))).merged()
    cp = [p.bbox() for p in reg.each() if abs(p.bbox().width() * ly.dbu - 59.07) < 0.2 and abs(p.bbox().height() * ly.dbu - 59.07) < 0.2]
    assert len(cp) == 1, 'Cref plate not found'
    px1, py1, px2, py2 = [v * ly.dbu for v in (cp[0].left, cp[0].bottom, cp[0].right, cp[0].top)]
    px1, px2 = px1 + A.ADC_ORG[0], px2 + A.ADC_ORG[0]
    log('Cref plate in the slot: x %.2f .. %.2f, y %.2f .. %.2f' % (px1, px2, py1, py2))
    for n in range(4):
        xa1, xa2 = sorted((chx(n, px1), chx(n, px2)))
        ya1, ya2 = sorted((chy(n, py1), chy(n, py2)))
        xu0 = round((xa1 + 0.63 + 5.6) / 0.005) * 0.005
        for r in range(2):
            y = round((ya1 + 2.95 + 5.0 + 26.0 * r) / 0.005) * 0.005
            decap_row([xu0, xu0 + 26.0], y, (chx(n, 232.0), 4), (chx(n, 235.4), 3))
    for (ys_, nrow) in ((640.0, (3, 3, 2)), (60.0, (3, 3, 2))):
        for r, nr in enumerate(nrow):
            y = ys_ + 26.0 * r
            xs = [503.0 + 26.0 * c for c in range(nr)]
            decap_row(xs, y, (583.5, 5), (591.5, 5))
log('decap units: %s' % NDEC)

#DECAP_REST2#

# ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------
# write
# ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------
k.write(ly, outgds, 'dbs_afe_top')
bb = TOP.dbbox()
log('wrote %s: %.3f x %.3f um (bbox %.3f %.3f %.3f %.3f); decap units %s' % (outgds, bb.width(), bb.height(), bb.left, bb.bottom, bb.right, bb.top, NDEC))
open(os.path.splitext(outgds)[0] + '.build.log', 'w').write('\n'.join(LOG) + '\n')
