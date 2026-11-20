"""blocks_amp.py (L2a): the blocks of amp_ch (one function per functional group).  Net names are the FLATTENED names of AFE/layout/lvs/afe_chc.spice subckt amp_ch (afe_chc internal nets
keep their names, fs_oneshot_c: t nd mm, OR2: pins only).  Used by mk_amp_ch.py."""
import math
import kpdk as k
import amplib as a

# ---- net names (as in the reference)
VN, VP, V1, VN2 = 'xs1_vn', 'xs1_vp', 'v1', 'xs2_vn2'
TAIL1, D1, O1 = 'xs1_xota_tail', 'xs1_xota_d1', 'xs1_xota_o1'
TAIL2, D2, O2 = 'xs2_xota2_tail', 'xs2_xota2_d1', 'xs2_xota2_o2'
IB1 = 'ibias1'
GM1, GM2 = 'gm1', 'gm2'
M1R, M2R, M3R = 'xs1_xr1_m', 'xs1_xr2_m', 'xs2_xr_m'
FS, FSOS = 'fs', 'fs_os'
VDD, VSS = 'vdd', 'vss'


def blocks(ly):
    B = {}
    # ------------------------------------------------------------------ stage 1 P side: input pair ABBA + tail group in one n-well
    pr = dict(volt='3.3V')
    pa = lambda nm, g, d: a.dev_block(ly, nm, 'pfet', 50.0, 2.0, 8, s_net=TAIL1, d_nets=d, g_net=g, bulk_net=VDD, ring=False)
    A1, B1, B2, A2 = pa('pair_a1', VN, D1), pa('pair_b1', VP, O1), pa('pair_b2', VP, O1), pa('pair_a2', VN, D1)
    tl = lambda nm, d: a.dev_block(ly, nm, 'pfet', 50.0, 4.0, 2, s_net=VDD, d_nets=d, g_net=IB1, bulk_net=VDD, ring=False)
    parts = []
    x = 0
    for blk in (A1, B1, B2, A2):
        w = blk.bbox[2] - blk.bbox[0]
        parts.append((blk, math.ceil(x - blk.bbox[0]), 0))
        x = x + w + 1.5
    x += 5
    if a.KNOB.get('tm', 0):
        # tail-group merge (L2a rework): xmb / xmt / xm7 (2 fingers each, common gate ibias1 and source vdd) as ONE 6-finger array: strips S D S D S D S, drains ibias1 / tail1 / v1
        T6 = a.dev_block(ly, 'tail6', 'pfet', 50.0, 4.0, 6, s_net=VDD, d_nets=[IB1, TAIL1, V1], g_net=IB1, bulk_net=VDD, ring=False, multi=True)
        parts.append((T6, math.ceil(x - T6.bbox[0]), 0))
        groups = [[0, 1, 2, 3], [4]]
    else:
        T_mb, T_mt, T_m7 = tl('tail_mb', IB1), tl('tail_mt', TAIL1), tl('tail_m7', V1)
        for blk in (T_mb, T_mt, T_m7):
            w = blk.bbox[2] - blk.bbox[0]
            parts.append((blk, math.ceil(x - blk.bbox[0]), 0))
            x = x + w + 1.5
        groups = [[0, 1, 2, 3], [4, 5, 6]]
    B['ota_p'] = a.compose(ly, 'ota_p', parts, ring_kind='n', ring_net=VDD, dummy_l=2.0, dummy_groups=groups)
    # ------------------------------------------------------------------ stage 1 N side: mirror xm3 / xm4 (ABBA), xm6
    na = lambda nm, g, d, nf=1, w=50.0: a.dev_block(ly, nm, 'nfet', w, 16.0, nf, s_net=VSS, d_nets=d, g_net=g, bulk_net=VSS, ring=False)
    m3a, m4a, m4b, m3b = na('m3a', D1, D1), na('m4a', D1, O1), na('m4b', D1, O1), na('m3b', D1, D1)
    parts = []
    x = 0
    for blk in (m3a, m4a, m4b, m3b):
        w = blk.bbox[2] - blk.bbox[0]
        parts.append((blk, math.ceil(x - blk.bbox[0]), 0))
        x = x + w + 1.5
    B['mir'] = a.compose(ly, 'mir', parts, ring_kind='p', ring_net=VSS, dummy_l=2.0)
    B['xm6'] = a.dev_block(ly, 'xm6', 'nfet', 50.0, 16.0, 4, s_net=VSS, d_nets=V1, g_net=O1, bulk_net=VSS, ring=True)
    B['sink1'] = a.dev_block(ly, 'sink1', 'nfet', 16.0, 4.0, 24, s_net=VSS, d_nets=IB1, g_net='vbn', bulk_net=VSS, ring=True)
    B['xms'] = a.dev_block(ly, 'xms', 'nfet', 16.0, 4.0, 6, s_net=VSS, d_nets='out', g_net='vbn', bulk_net=VSS, ring=True)
    # ------------------------------------------------------------------ stage 2
    def col(name, spec):
        tiles = []
        y = 0
        for sp in spec:
            (w, l, s_, d_, g_) = sp[:5]
            tiles.append(dict(kind='nfet', w=w, l=l, x=0.0, y=float(y), s=s_, d=d_, g=g_, extra=(sp[5] if len(sp) > 5 else None)))
            y += 7
        return a.group_block(ly, name, tiles, ring_kind='p', ring_net=VSS)
    B['s2pair'] = col('s2pair', ((0.5, 40.0, TAIL2, D2, 'vcmo'), (0.5, 40.0, TAIL2, O2, VN2), (0.5, 40.0, TAIL2, O2, VN2), (0.5, 40.0, TAIL2, D2, 'vcmo')))
    B['s2tail'] = col('s2tail', ((1.0, 20.0, VSS, TAIL2, 'vbn'), (0.28, 40.0, VSS, 't', 'vbn', dict(con_bet_fin=0))))
    B['s2p'] = a.group_block(ly, 's2p', [dict(kind='pfet', w=1.0, l=20.0, x=0.0, y=0.0, s=VDD, d=D2, g=D2), dict(kind='pfet', w=1.0, l=20.0, x=0.0, y=7.0, s=VDD, d=O2, g=D2)],
                             ring_kind='n', ring_net=VDD)
    B['fol'] = a.group_block(ly, 'fol', [dict(kind='nvt', w=10.0, l=2.0, x=0.0, y=0.0, s='out', d=VDD, g=O2)], ring_kind='p', ring_net=VSS, gap=4.0)
    # ------------------------------------------------------------------ small devices: muxes, park, one-shot
    nt = [dict(kind='nfet', w=0.5, l=0.5, x=0.0, y=0.0, s='vrs', d=GM1, g=FS),
          dict(kind='nfet', w=0.5, l=0.5, x=7.0, y=0.0, s='vrs', d=GM2, g=FS),
          dict(kind='nfet', w=1.0, l=0.5, x=14.0, y=0.0, s='vcm', d='rec', g='sw_rec_b'),
          dict(kind='nfet', w=1.0, l=0.5, x=21.0, y=0.0, s='mm', d='nd', g='sw_rec'),
          dict(kind='nfet', w=1.0, l=0.5, x=28.0, y=0.0, s=VSS, d='mm', g='t'),
          dict(kind='nfet', w=1.0, l=0.5, x=35.0, y=0.0, s=VSS, d=FSOS, g='nd')]
    B['sn'] = a.group_block(ly, 'sn', nt, ring_kind='p', ring_net=VSS)
    pt = [dict(kind='pfet', w=0.5, l=0.5, x=0.0, y=0.0, s='vg1', d=GM1, g=FS),
          dict(kind='pfet', w=0.5, l=0.5, x=7.0, y=0.0, s='vg2', d=GM2, g=FS),
          dict(kind='pfet', w=2.0, l=0.5, x=14.0, y=0.0, s='vcm', d='rec', g='sw_rec'),
          dict(kind='pfet', w=1.0, l=0.5, x=21.0, y=0.0, s=VDD, d='t', g='sw_rec'),
          dict(kind='pfet', w=1.0, l=0.5, x=28.0, y=0.0, s=VDD, d='nd', g='sw_rec'),
          dict(kind='pfet', w=1.0, l=0.5, x=35.0, y=0.0, s=VDD, d='nd', g='t'),
          dict(kind='pfet', w=2.0, l=0.5, x=42.0, y=0.0, s=VDD, d=FSOS, g='nd')]
    B['sp'] = a.group_block(ly, 'sp', pt, ring_kind='n', ring_net=VDD)
    B['or2'] = a.or2_block(ly, 'or2', FSOS, 'rst_amp', FS, VDD, VSS)
    # ------------------------------------------------------------------ pseudo resistors
    B['pr1'] = a.pr_block(ly, 'pr1', VN, V1, M1R, GM1)
    B['pr2'] = a.pr_block(ly, 'pr2', VP, 'vcm', M2R, GM1)
    B['pr3'] = a.pr_block(ly, 'pr3', VN2, 'out', M3R, GM2)
    # ------------------------------------------------------------------ MIM capacitors outside the Cin block
    B['cc1'] = a.mim_block(ly, 'cc1', 22.0, O1, V1)
    B['cf1'] = a.mim_block(ly, 'cf1', 8.45, VN, V1)
    B['cf1p'] = a.mim_block(ly, 'cf1p', 8.45, VP, 'vcm')
    B['cin2'] = a.mim_block(ly, 'cin2', 38.59, VN2, V1)
    B['cc2'] = a.mim_block(ly, 'cc2', 31.465, O2, VSS)
    B['cf2'] = a.mim_block(ly, 'cf2', 11.92, VN2, 'out')
    B['ct'] = a.mim_block(ly, 'ct', 44.595, 't', VSS)
    return B
