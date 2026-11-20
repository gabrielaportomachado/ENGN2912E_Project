"""mk_flowtest.py (L2a Step 1, FLOW-FIRST): the small cells that take every tool of the chain once.
Run:  bash AFE/layout/scripts/kl.sh AFE/layout/amp/mk_flowtest.py out=AFE/layout/amp/flowtest
Writes <cell>.gds + <cell>.ref.spice for
  lp_flow   two pseudo-R transistors (pfet_03v3 0.22u/0.5u, own n-well tied to the source: 'Bulk Tie'), one 5 x 5 um MIM unit with the plates labelled TOPNET (top plate, Metal5) and
            BOTNET (bottom plate, Metal4), one nfet_06v0_nvt 10u/2u with a P+ substrate ring, one nfet_03v3 2u/1u inside a P+ guard ring drawn by amplib.ring
  lp_dummy  an nfet_03v3 2 fingers (m=2 in the reference) next to a dummy transistor with gate = source = drain = bulk on one net: does netgen drop it, and does nf = m?
"""
import os
import kpdk as k
import amplib as a

out = globals().get('out', '.')
os.makedirs(out, exist_ok=True)


ring = a.ring


def save(ly, top, ref):
    k.write(ly, os.path.join(out, top + '.gds'), top)
    open(os.path.join(out, top + '.ref.spice'), 'w').write('* LVS reference of the L2a flow test cell %s (written by mk_flowtest.py)\n' % top + ref)
    bb = ly.cell(top).dbbox()
    print('wrote %s.gds  %.2f x %.2f um' % (top, bb.width(), bb.height()))


def lab_at(cell, b, text):
    k.label(cell, 'metal1', text, a.cx(b), a.cy(b))


# ------------------------------------------------------------------ lp_flow
ly = k.new_layout()
top = ly.create_cell('lp_flow')
for i, x0 in enumerate((0.0, 12.0)):
    d = a.Dev(top, 'pfet', x0, 0.0, volt='3.3V', bulk='None', w_gate=0.22, l_gate=0.5, nf=1, con_bet_fin=0)
    n = str(i + 1)
    print('pr', n, 'sd', d.sd, 'g', d.g, 'tie', d.tie, 'comp', d.comp, 'bbox', d.bbox)
    # n+ well tie of our own, right of the drain: comp 0.42 x 0.44 (contact 0.22), nplus, nwell extension, Metal1
    yc = a.cy(d.sd[1])
    tx1, ty1, tx2, ty2 = x0 + 1.68, a.snap(yc - 0.25), x0 + 2.10, a.snap(yc + 0.25)
    k.rect(top, 'comp', tx1, ty1, tx2, ty2)
    k.rect(top, 'nplus', tx1 - 0.16, ty1 - 0.16, tx2 + 0.16, ty2 + 0.16)
    k.rect(top, 'nwell', x0 + 1.0, d.bbox[1], tx2 + 0.5, d.bbox[3])
    a.cuts(top, 'contact', tx1, ty1, tx2, ty2, inset=0.1)
    k.rect(top, 'metal1', tx1, ty1, tx2, ty2)
    # source strip -> up, over the gate pad, down to the tie
    sx1, sx2 = d.sd[0][0], d.sd[0][2]
    k.rect(top, 'metal1', sx1, d.sd[0][1], sx2, 1.8)
    k.rect(top, 'metal1', sx1, 1.4, tx2, 1.8)
    k.rect(top, 'metal1', tx1, ty1, tx2, 1.8)
    lab_at(top, d.sd[0], 'S' + n)
    lab_at(top, d.sd[1], 'D' + n)
    lab_at(top, d.g[0], 'G' + n)
# MIM unit
mx, my = 30.0, 0.0
m = a.mim_cap(top, mx, my, 5.0, 5.0, 'TOPNET', 'BOTNET')
print('mim', m)
bp = m['bot']
k.rect(top, 'metal4', bp[0] - 3.4, bp[1], bp[0], bp[1] + 2.0)        # Metal4 lead of the bottom plate (allowed: MIMTM.10 forbids only Via3 on the plate)
k.label(top, 'metal4', 'BOTNET', bp[0] - 2.0, bp[1] + 1.0)
k.label(top, 'metal5', 'TOPNET', mx + 2.5, my + 2.5)
# native-Vt follower
nv = a.Dev(top, 'nfet_06v0_nvt', 55.0, 5.0, bulk='None', w_gate=10.0, l_gate=2.0, nf=1)
print('nvt sd', nv.sd, 'g', nv.g, 'bbox', nv.bbox)
lab_at(top, nv.sd[0], 'ND')
lab_at(top, nv.sd[1], 'NS')
lab_at(top, nv.g[0], 'NG')
ring(top, 55.0 - 6.0, 5.0 - 6.0, 55.0 + 8.0, 5.0 + 16.0, 'p', lab='VSS')
# 3.3 V nfet in a guard ring of our own
nf_ = a.Dev(top, 'nfet', 80.0, 5.0, volt='3.3V', bulk='None', w_gate=2.0, l_gate=1.0, nf=1, gate_con_pos='top')
print('nfet sd', nf_.sd, 'g', nf_.g)
lab_at(top, nf_.sd[0], 'DD')
lab_at(top, nf_.sd[1], 'GS')
lab_at(top, nf_.g[0], 'GG')
ring(top, 80.0 - 2.0, 5.0 - 2.0, 80.0 + 4.0, 5.0 + 5.5, 'p', lab='VSS')
save(ly, 'lp_flow', '.subckt lp_flow S1 D1 G1 S2 D2 G2 TOPNET BOTNET ND NG NS DD GG GS VSS\n'
     'X1 D1 G1 S1 S1 pfet_03v3 w=0.22u l=0.5u\nX2 D2 G2 S2 S2 pfet_03v3 w=0.22u l=0.5u\n'
     'X3 TOPNET BOTNET cap_mim_2f0_m4m5_noshield c_width=5u c_length=5u\n'
     'X4 ND NG NS VSS nfet_06v0_nvt w=10u l=2u\n'
     'X5 DD GG GS VSS nfet_03v3 w=2u l=1u\n.ends\n')

# ------------------------------------------------------------------ lp_dummy
ly = k.new_layout()
top = ly.create_cell('lp_dummy')
r = a.Dev(top, 'nfet', 0.0, 0.0, volt='3.3V', bulk='None', w_gate=2.0, l_gate=1.0, nf=2, gate_con_pos='top')
print('real nf=2', r.sd, r.g)
lab_at(top, r.sd[0], 'S')
lab_at(top, r.sd[1], 'D')
a.m1(top, (r.sd[0][0], r.g[0][3] + 0.5, r.sd[2][2], r.g[0][3] + 0.9))                    # bar joining the 3 strips needs vias: use S strips 0 and 2 only
k.rect(top, 'metal1', r.sd[0][0], r.sd[0][3], r.sd[0][2], r.g[0][3] + 0.9)
k.rect(top, 'metal1', r.sd[2][0], r.sd[2][3], r.sd[2][2], r.g[0][3] + 0.9)
g = r.g
k.rect(top, 'metal1', g[0][0], g[0][1], g[1][2], g[1][3])                               # joins the two gate pads
lab_at(top, (g[0][0], g[0][1], g[1][2], g[1][3]), 'G')
# dummies that are NOT devices (netgen does not drop a shorted dummy transistor: tested, it stays as an extra device): poly-only stripes on field oxide next to the end fingers, and a
# bare comp strip (n+ implant, no gate, no contact) next to the diffusion: neither extracts as a device
k.rect(top, 'poly2', -1.8, -0.3, -0.8, 2.3)
k.rect(top, 'poly2', 4.1, -0.3, 5.1, 2.3)
k.rect(top, 'comp', 6.0, 0.0, 7.0, 2.0)
k.rect(top, 'nplus', 5.8, -0.2, 7.2, 2.2)
ring(top, -3.0, -2.0, 9.0, 5.0, 'p', lab='VSS')
save(ly, 'lp_dummy', '.subckt lp_dummy S D G VSS\nX1 D G S VSS nfet_03v3 w=2u l=1u m=2\n.ends\n')
