"""mk_afe_ch.py (L3a): the channel slot cell `afe_ch` (237 x 448.88 um, north-row orientation, origin = SW corner of the slot, y = 0 at the ADC end).
Imported by mk_top.py (function build_afe_ch); run alone for a cell test:
    bash AFE/layout/scripts/kl.sh AFE/layout/top/mk_afe_ch.py out=AFE/layout/top/afe_ch.gds
Content: adc_ch, amp_ch, the two routing TGATEs (flattened copy of TGATE/TGATE.gds + one filltie abutted each, SPEC.md 3.1), the control corridor (5 Metal2 lines + a vss line),
the analog spur corridor (vdd Metal4, vss Metal3), amp_out, the TGATE zone with its Metal3 control tracks and the Metal5 pad wires of E / REC / IPG.  LVS reference: subckt afe_ch of AFE/layout/lvs/dbs_afe_top.spice.
Pins of the cell = labels on the slot edge (names as the reference, lower case).
Deviation from SPEC.md 3.1 (report section 7): amp_ch is placed 15 um below the slot top (the slot has 63 um of free height), so the TGATE zone is 15 um high instead of 8 um."""
import os
import sys
import json
import pya
sys.path.insert(0, os.path.dirname(os.environ.get('KL_SCRIPT', __file__)))
import kpdk as k
import toplib as T

HERE = os.path.dirname(os.path.abspath(os.environ.get('KL_SCRIPT', __file__)))
REPO = os.path.normpath(os.path.join(HERE, '..', '..', '..'))
STD_GDS = os.path.join(k.PDK_ROOT, k.PDK, 'libs.ref/gf180mcu_fd_sc_mcu7t5v0/gds/gf180mcu_fd_sc_mcu7t5v0.gds')

SKIP = set((globals().get('skip', '') or '').split(','))
SLOT_W, SLOT_H = 237.0, 448.88
AT = 433.88                       # slot y of the amp_ch bbox top (the TGATE zone is above it)
AMP_BOX = (0.75, 1.75, 221.5, 275.0)
AMP_ORG = (8.0, AT - AMP_BOX[3])  # origin of the amp_ch cell in the slot
ADC_ORG = (8.0, 0.0)

# control corridor lines (Metal2, 0.5 wide) and the vss line
CORR = {'sw_rec': 1.0, 'sw_rec_b': 2.4, 'sw_ipg': 3.8, 'sw_ipg_b': 5.2, 'rst_amp': 6.6}
VSS_LINE_X = 7.6
# TGATE zone (z = y - AT)
ZT = SLOT_H - AT                  # 15.0
TZ0 = 5.0                         # z of the TGATE origin
TX_REC, TX_IPG = 76.78, 162.88    # x of the TGATE origins: OUT strip centre = tx + 2.12 = 78.9 (amp rec pin) / 165.0 (IPG pad)
TRACK = {'sw_rec': 2.0, 'sw_ipg': 3.3, 'sw_rec_b': 11.0, 'sw_ipg_b': 12.2}
Z_E = 13.4
SPUR_VDD = (230.5, 233.5)         # Metal4
SPUR_VSS = (234.0, 236.8)         # Metal3
ADC_CTRL = ['rst_sw', 'tg_on', 'dac_gdn', 'cmp_clk', 'cmp_q'] + ['dac_g%s[%d]' % (t, b) for b in range(11, -1, -1) for t in ('p', 'n')]


def adc_pin_x(name):
    """slot x of an adc_ch control pin (adc pins at 12, 15, 18, 21, 24, then 27 + 3 i)"""
    i = ADC_CTRL.index(name)
    return 8.0 + 12.0 + 3.0 * i


def make_tgate(ly, tg_src, tie_src, name='TGATE'):
    """flattened TGATE + filltie (abutted at x = 3.36) as ONE cell named like the reference subckt"""
    c = T.flat_copy(ly, tg_src, name)
    tie = T.flat_copy(ly, tie_src, name + '_tie')
    c.insert(pya.CellInstArray(tie.cell_index(), pya.Trans(0, False, T.k.u(3.36, ly), 0)))
    c.flatten(True)
    for nm, x, y in (('VDD', 1.68, 3.92), ('VSS', 1.68, 0.0), ('IN', 0.70, 2.0), ('OUT', 2.12, 2.0), ('C', 1.40, 1.39), ('CBAR', 1.40, 2.01)):
        k.label(c, 'metal1', nm, x, y)
    return c


def build_afe_ch(ly, amp_c, adc_c, tg_c, name='afe_ch'):
    C = ly.create_cell(name)
    k.put(C, adc_c, *ADC_ORG)
    k.put(C, amp_c, *AMP_ORG)
    ax, ay = AMP_ORG
    # ------------------------------------------------------------------ control corridor lines (Metal2)
    def ytr(z):
        return AT + z
    pin_y = {'sw_rec': ay + 263.0, 'sw_rec_b': ay + 255.0, 'rst_amp': ay + 247.0}         # amp_ch west-edge Metal2 pins (x = ax + 1.0)
    end_y = {'sw_rec': ytr(TRACK['sw_rec']), 'sw_ipg': ytr(TRACK['sw_ipg']), 'sw_rec_b': ytr(TRACK['sw_rec_b']), 'sw_ipg_b': ytr(TRACK['sw_ipg_b']), 'rst_amp': pin_y['rst_amp']}
    for n, x in CORR.items():
        T.seg(C, 'metal2', x, 0.25, x, end_y[n], 0.5)
        T.lab(C, 'metal2', n, x, 0.6)
    # pins of amp_ch: Metal3 stubs from the corridor lines
    for n in ('sw_rec', 'sw_rec_b', 'rst_amp'):
        y = pin_y[n]
        T.stk(C, CORR[n], y, 2, 3, size=0.6)
        T.seg(C, 'metal3', CORR[n], y, ax + 1.0, y, 0.5)
        T.stk(C, ax + 1.0, y, 2, 3, size=0.6)
    # ------------------------------------------------------------------ TGATE zone
    tgs = {'rec': TX_REC, 'ipg': TX_IPG}
    for nm, tx in tgs.items():
        T.k.put(C, tg_c, tx, ytr(TZ0))
    # Metal1 supply lines along the rails (VSS bottom rail, VDD top rail), VSS also west to the corridor vss line
    ys0, ys1 = ytr(TZ0 - 0.3), ytr(TZ0 + 0.3)
    yd0, yd1 = ytr(TZ0 + 3.62), ytr(TZ0 + 4.22)
    T.R(C, 'metal1', VSS_LINE_X - 0.35, ys0, SPUR_VSS[0] + 1.6, ys1)
    T.R(C, 'metal1', TX_REC, yd0, SPUR_VDD[0] + 1.6, yd1)
    T.stk(C, VSS_LINE_X, ytr(TZ0), 1, 2, size=0.6)
    T.seg(C, 'metal2', VSS_LINE_X, ytr(TZ0), VSS_LINE_X, 1.0, 0.5)
    T.lab(C, 'metal2', 'vss', VSS_LINE_X, 1.0)
    # TGATE pin positions (relative to the origin): IN strip centre x 0.705, OUT 2.12, C / CBAR Metal1 pads centred at x 1.40, y 1.39 / 2.01 (0.38 x 0.38 um), strips z 0.67 .. 3.35.
    # Via1 only (the TGATE pads are Metal1 already); the Metal2 pads are 0.38 wide, C extends downwards (z .. +1.54), CBAR upwards, so that they are 0.28 um apart.
    for nm, tx in tgs.items():
        xin, xout, xc = tx + 0.705, tx + 2.12, tx + 1.40
        zin = TZ0 + 3.0                                    # IN via at the upper part of the strip
        # E: IN strip -> Metal2 up to the E track
        T.stk(C, xin, ytr(zin), 1, 2, size=0.4)
        T.seg(C, 'metal2', xin, ytr(zin), xin, ytr(Z_E), 0.3)
        T.stk(C, xin, ytr(Z_E), 2, 3, size=0.4)
        # C: pad -> Metal2 down to the track below the row;  CBAR: pad -> Metal2 up to the track above the row
        cn = 'sw_rec' if nm == 'rec' else 'sw_ipg'
        bn = cn + '_b'
        T.cuts(C, 'via1', xc - 0.13, ytr(TZ0 + 1.39) - 0.13, xc + 0.13, ytr(TZ0 + 1.39) + 0.13, inset=0.0)
        T.R(C, 'metal2', xc - 0.19, ytr(TZ0 + 1.14), xc + 0.19, ytr(TZ0 + 1.53))
        T.seg(C, 'metal2', xc, ytr(TZ0 + 1.14), xc, ytr(TRACK[cn]), 0.3)
        T.stk(C, xc, ytr(TRACK[cn]), 2, 3, size=0.4)
        T.seg(C, 'metal3', CORR[cn], ytr(TRACK[cn]), xc, ytr(TRACK[cn]), 0.5)
        T.stk(C, CORR[cn], ytr(TRACK[cn]), 2, 3, size=0.5)
        T.cuts(C, 'via1', xc - 0.13, ytr(TZ0 + 2.01) - 0.13, xc + 0.13, ytr(TZ0 + 2.01) + 0.13, inset=0.0)
        T.R(C, 'metal2', xc - 0.19, ytr(TZ0 + 1.82), xc + 0.19, ytr(TZ0 + 2.21))
        T.seg(C, 'metal2', xc, ytr(TZ0 + 2.01), xc, ytr(TRACK[bn]), 0.3)
        T.stk(C, xc, ytr(TRACK[bn]), 2, 3, size=0.4)
        T.seg(C, 'metal3', CORR[bn], ytr(TRACK[bn]), xc, ytr(TRACK[bn]), 0.5)
        T.stk(C, CORR[bn], ytr(TRACK[bn]), 2, 3, size=0.5)
    # E track and the E pad wire
    xe_rec, xe_ipg = TX_REC + 0.705, TX_IPG + 0.705
    T.seg(C, 'metal3', 70.0, ytr(Z_E), xe_ipg, ytr(Z_E), 0.5)
    T.stk(C, 70.0, ytr(Z_E), 3, 5, size=1.0)
    T.seg(C, 'metal5', 70.0, ytr(Z_E), 70.0, SLOT_H, 2.0, cap=False)
    T.lab(C, 'metal5', 'e', 70.0, SLOT_H - 0.6)
    # REC: OUT strip -> Metal5 (via stack) -> Metal5 vertical to the amp rec pin, horizontal to x = 118, pad wire
    xo_rec = TX_REC + 2.12
    T.stk(C, xo_rec, ytr(TZ0 + 3.0), 1, 5, size=0.4)
    T.R(C, 'metal5', xo_rec - 0.6, AT - 1.0, xo_rec + 0.6, ytr(14.0) + 0.6)
    T.seg(C, 'metal5', xo_rec, ytr(14.0), 118.0, ytr(14.0), 1.2)
    T.seg(C, 'metal5', 118.0, ytr(14.0), 118.0, SLOT_H, 2.0, cap=False)
    T.lab(C, 'metal5', 'rec', 118.0, SLOT_H - 0.6)
    # IPG: OUT strip of the second TGATE -> Metal5 up to the slot edge
    xo_ipg = TX_IPG + 2.12
    T.stk(C, xo_ipg, ytr(TZ0 + 3.0), 1, 5, size=0.4)
    T.seg(C, 'metal5', xo_ipg, ytr(TZ0 + 3.0) - 0.5, xo_ipg, SLOT_H, 2.0, cap=False)
    T.lab(C, 'metal5', 'ipg', xo_ipg, SLOT_H - 0.6)
    # REF: amp_ch.ref pin (Metal5, x = ax + 113 +- 0.6) up to the slot edge
    xr = ax + 113.0
    T.R(C, 'metal5', xr - 0.6, AT - 1.0, xr + 0.6, SLOT_H)
    T.lab(C, 'metal5', 'ref', xr, SLOT_H - 0.6)
    # ------------------------------------------------------------------ bias pins: Metal2 verticals (they cross the Metal3 control tracks), Metal3 pad at the slot edge
    for i, n in enumerate(('vbn', 'vcm', 'vg1', 'vcmo', 'vg2', 'vrs') if 'bias' not in SKIP else ()):
        x = ax + 1.0 + i
        yp = ay + 273.6                                      # the pins end at y = 272.25; amp_ch has a Metal2 feeder at y 271.75 .. 272.25 (x >= 3.75): extend the Metal3 pin first
        T.R(C, 'metal3', x - 0.25, ay + 272.0, x + 0.25, yp + 0.23)
        T.stk(C, x, yp, 2, 3, size=0.46)
        T.seg(C, 'metal2', x, yp, x, SLOT_H - 1.4, 0.5)
        T.stk(C, x, SLOT_H - 1.4, 2, 3, size=0.46)
        T.R(C, 'metal3', x - 0.25, SLOT_H - 1.4, x + 0.25, SLOT_H)
        T.lab(C, 'metal3', n, x, SLOT_H - 0.5)
    # ------------------------------------------------------------------ spur corridor: vdd Metal4, vss Metal3
    T.R(C, 'metal4', SPUR_VDD[0], 0.0, SPUR_VDD[1], SLOT_H)
    T.R(C, 'metal3', SPUR_VSS[0], 0.0, SPUR_VSS[1], SLOT_H)
    T.lab(C, 'metal4', 'vdd', 232.0, SLOT_H - 0.6)
    T.lab(C, 'metal3', 'vss', 235.4, SLOT_H - 0.6)
    # TGATE rails to the spur
    if 'rails' not in SKIP:
        T.stk(C, 232.0, ytr(TZ0 + 3.92), 1, 4, size=1.2)
        T.stk(C, 235.4, ytr(TZ0), 1, 3, size=1.2)
    # amp_ch supply pins (Metal4, east edge): vdd -> spur Metal4;  vss -> via3 + Metal3 under the vdd spur
    if 'ampsup' not in SKIP:
        T.R(C, 'metal4', ax + 218.0, ay + 14.0 - 0.8, SPUR_VDD[0] + 0.5, ay + 14.0 + 0.8)
        T.stk(C, ax + 218.0, ay + 30.0, 4, 5, size=2.4)                       # amp vss pad (Metal4 3 x 3) -> Metal5 over the vdd spur -> vss spur (Metal3)
        T.R(C, 'metal5', ax + 217.0, ay + 30.0 - 0.6, 235.4 + 0.8, ay + 30.0 + 0.6)
        T.stk(C, 235.4, ay + 30.0, 3, 5, size=1.6)
    # adc_ch supply pins: vdd (east, bottom) -> spur;  vdd_cmp / vdd_dac -> stubs with labels (the top level continues them);  vss -> Metal5 line to the spur vss
    T.R(C, 'metal4', ADC_ORG[0] + 218.0, 1.0, SPUR_VDD[0] + 0.5, 3.0)
    T.R(C, 'metal4', ADC_ORG[0] + 120.0 + 5.0, 0.0, ADC_ORG[0] + 120.0 + 9.0, 3.0)
    T.lab(C, 'metal4', 'vdd_cmp', ADC_ORG[0] + 127.0, 1.5)
    T.R(C, 'metal4', ADC_ORG[0] + 150.0 + 5.0, 0.0, ADC_ORG[0] + 150.0 + 9.0, 3.0)
    T.lab(C, 'metal4', 'vdd_dac', ADC_ORG[0] + 157.0, 1.5)
    T.stkbox(C, 4, 5, ADC_ORG[0] + 190.0 - 6.0, 1.0, ADC_ORG[0] + 190.0 + 6.0, 3.0)
    T.R(C, 'metal5', ADC_ORG[0] + 190.0 - 6.0, 1.0, 235.4 + 0.8, 3.0)
    T.stk(C, 235.4, 2.0, 3, 5, size=1.6)
    # ------------------------------------------------------------------ ADC control pins: stubs with labels (the top level continues them)
    for n in ADC_CTRL:
        x = adc_pin_x(n)
        T.R(C, 'metal2', x - 0.25, 0.0, x + 0.25, 1.0)
        T.lab(C, 'metal2', n, x, 0.5)
    # ------------------------------------------------------------------ amp_out: amp_ch.out (Metal3 pin, bottom end) -> adc_ch.vin (Metal3 pin, top end)
    xo = ax + 148.0
    yo = ay + 1.75
    xv = ADC_ORG[0] + 4.0
    yv = ADC_ORG[1] + 103.25
    y_h = 128.0
    T.seg(C, 'metal3', xo, yo + 0.4, xo, y_h, 0.5)
    T.seg(C, 'metal3', xo, y_h, xv, y_h, 0.5)
    T.seg(C, 'metal3', xv, y_h, xv, yv - 0.3, 0.5)
    return C


def load_cells(ly):
    amp = k.import_gds(ly, os.path.join(REPO, 'AFE/layout/amp/amp_ch.gds'), 'amp_ch')
    adc = k.import_gds(ly, os.path.join(REPO, 'AFE/layout/adc/adc_ch.gds'), 'adc_ch')
    tg_src = k.import_gds(ly, os.path.join(REPO, 'TGATE/TGATE.gds'), 'TGATE')
    tie_src = k.import_gds(ly, STD_GDS, 'gf180mcu_fd_sc_mcu7t5v0__filltie')
    tg_src.name = 'TGATE_src'
    tgc = make_tgate(ly, tg_src, tie_src)
    return amp, adc, tgc


if __name__ == '__main__' or os.environ.get('KL_SCRIPT', '').endswith('mk_afe_ch.py'):
    out = globals().get('out', 'AFE/layout/top/afe_ch.gds')
    ly = k.new_layout()
    amp, adc, tgc = load_cells(ly)
    C = build_afe_ch(ly, amp, adc, tgc)
    k.write(ly, out, 'afe_ch')
    bb = C.dbbox()
    print('wrote %s  afe_ch %.2f x %.2f um  (bbox %.3f %.3f %.3f %.3f)' % (out, bb.width(), bb.height(), bb.left, bb.bottom, bb.right, bb.top))
