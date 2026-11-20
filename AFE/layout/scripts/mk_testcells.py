"""mk_testcells.py (LP kit): the small generated cells that prove the flow and three Decision-46 facts.  Run:  bash AFE/layout/scripts/kl.sh AFE/layout/scripts/mk_testcells.py out=<dir>
Writes one GDS per cell + its LVS reference netlist <cell>.ref.spice into <dir>:
  lp_tgate_tap  the routing switch TGATE/TGATE.gds + one filltie standard cell (n-well and substrate taps).  2 devices: the netgen smoke test of check_env.sh, and the
                answer to the F1 note "the extracted TGATE has its PMOS bulk on an unnamed net": the cell needs a tap cell next to it (L3a places it like this).
  lp_mim        one 5 x 5 um MIM unit, top plate labelled TOPNET, bottom plate BOTNET: which Magic terminal is the top plate (Decision 46a).
  lp_rm3        the strap resistor rm3 2 um x 222.2 um (Decision 46e): is it an LVS-extractable device of variant D.
  lp_decap      one MOS decap unit cap_nmos_03v3 20 x 20 um: does it extract as a device.
  lp_cin_decap  Decision 46c, first area lever: one Cin piece (MIM 70.649 x 70.649 um, top plate = summing node `vn`, bottom plate = driven node `rec`) with 4 decap units,
                their Metal1 / Metal2 strapping and a Metal3 shield (on vss) UNDER the bottom plate: 2 units on vdd_cmp (ADC-main strap), 2 on vdd_dac (ADC-DAC strap).
"""
import os
import kpdk as k

out = globals().get('out', '.')
os.makedirs(out, exist_ok=True)
REPO = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(k.__file__)), '..', '..', '..'))
STD_GDS = os.path.join(k.PDK_ROOT, k.PDK, 'libs.ref/gf180mcu_fd_sc_mcu7t5v0/gds/gf180mcu_fd_sc_mcu7t5v0.gds')


def save(ly, top, ref):
    k.write(ly, os.path.join(out, top + '.gds'), top)
    open(os.path.join(out, top + '.ref.spice'), 'w').write('* LVS reference of the LP test cell %s (written by mk_testcells.py)\n' % top + ref)
    bb = ly.cell(top).dbbox()
    print('wrote %s.gds  %.2f x %.2f um' % (top, bb.width(), bb.height()))


# ---------------------------------------------------------------- lp_tgate_tap
ly = k.new_layout()
top = ly.create_cell('lp_tgate_tap')
tg = k.import_gds(ly, os.path.join(REPO, 'TGATE/TGATE.gds'), 'TGATE')
tie = k.import_gds(ly, STD_GDS, 'gf180mcu_fd_sc_mcu7t5v0__filltie')
k.put(top, tg, 0, 0)
k.put(top, tie, 3.36, 0)                       # abuts: the VDD / VSS rails and the wells join
for name, x, y in (('VDD', 1.68, 3.92), ('VSS', 1.68, 0.0), ('IN', 0.70, 2.0), ('OUT', 2.12, 2.0), ('C', 1.40, 1.39), ('CBAR', 1.40, 2.01)):
    k.label(top, 'metal1', name, x, y)
save(ly, 'lp_tgate_tap', '.subckt lp_tgate_tap OUT C CBAR IN VDD VSS\nXM1 OUT CBAR IN VDD pfet_05v0 L=0.6u W=1.22u\nXM2 OUT C IN VSS nfet_05v0 L=0.6u W=0.565u\n.ends\n')

# ---------------------------------------------------------------- lp_mim
ly = k.new_layout()
top = ly.create_cell('lp_mim')
k.put(top, k.pcell(ly, 'cap_mim', mim_option='MIM-B', metal_level='M5', wc=5.0, lc=5.0), 0, 0)
k.rect(top, 'metal5', 0.0, 0.0, 5.0, 5.0)      # top-plate metal (same shape as the pcell's): carries the label
k.rect(top, 'metal4', -4.0, 0.0, -0.6, 2.0)    # a Metal4 lead of the bottom plate (allowed: MIMTM.10 only forbids Via3 on the plate)
k.label(top, 'metal5', 'TOPNET', 2.5, 2.5)
k.label(top, 'metal4', 'BOTNET', -3.0, 1.0)
save(ly, 'lp_mim', '.subckt lp_mim TOPNET BOTNET\nX1 TOPNET BOTNET cap_mim_2f0_m4m5_noshield c_width=5u c_length=5u\n.ends\n')

# ---------------------------------------------------------------- lp_rm3
ly = k.new_layout()
top = ly.create_cell('lp_rm3')
(ax, ay), (bx, by) = k.metal_res(top, 3, 0.0, 0.0, 222.2, 2.0, lead=4.0)      # NOT the PDK pcell: see the FINDING in kpdk.metal_res
k.label(top, 'metal3', 'A', ax, ay)
k.label(top, 'metal3', 'B', bx, by)
save(ly, 'lp_rm3', '.subckt lp_rm3 A B\nX1 A B rm3 r_width=2u r_length=222.2u\n.ends\n')

# ---------------------------------------------------------------- lp_decap
ly = k.new_layout()
top = ly.create_cell('lp_decap')
k.put(top, k.pcell(ly, 'cap_nmos', volt='3.3V', lc=20.0, wc=20.0), 0, 0)
k.label(top, 'metal1', 'G', 10.44, 10.0)
k.label(top, 'metal1', 'SD', 10.45, -1.44)
save(ly, 'lp_decap', '.subckt lp_decap G SD\nX1 G SD cap_nmos_03v3 c_length=20u c_width=20u\n.ends\n')

# ---------------------------------------------------------------- lp_cin_decap
ly = k.new_layout()
top = ly.create_cell('lp_cin_decap')
W = 70.65                                                       # FINDING (LP): the F1 default 70.649 um is OFF the 5 nm grid (DRC *_OFFGRID); draw 70.65 and regenerate the
                                                                # reference with mk_lvs_netlists.py --cin 2,70.65,70.65 (20.0006 pF, +0.003 %)
k.put(top, k.pcell(ly, 'cap_mim', mim_option='MIM-B', metal_level='M5', wc=W, lc=W), 0, 0)
k.rect(top, 'metal5', 0.0, 0.0, W, W)
k.label(top, 'metal5', 'vn', W / 2, W / 2)                      # summing node = TOP plate (Decision 46a)
k.rect(top, 'metal4', -0.6, -8.0, 3.0, -0.6)                    # bottom-plate lead in Metal4
k.label(top, 'metal4', 'rec', 1.2, -6.0)
dec = k.pcell(ly, 'cap_nmos', volt='3.3V', lc=20.0, wc=20.0)   # pcell: comp (0,0)-(20.88,20), gate Metal1 (0.815,-0.47)-(20.065,20.47), S/D Metal1 bar (-0.63,-1.94)-(21.53,-0.94)
X0, Y0, PX, PY = 12.0, 12.0, 26.0, 26.0
for iy in range(2):
    y = Y0 + iy * PY
    for ix in range(2):
        x = X0 + ix * PX
        k.put(top, dec, x, y)
        k.vias(top, 'via1', x + 2.0, y + 8.5, x + 19.0, y + 11.5)       # gate Metal1 -> the Metal2 strap of the row
    net = 'vdd_cmp' if iy == 0 else 'vdd_dac'
    k.rect(top, 'metal2', -12.0, y + 8.5, X0 + PX + 21.0, y + 11.5)       # gate strap of the row, leaves the plate area to the west
    k.label(top, 'metal2', net, -10.0, y + 10.0)
    k.rect(top, 'metal1', 4.0, y - 1.94, X0 + PX + 21.53, y - 0.94)       # joins the S/D bars of the row and runs to the vss trunk
k.rect(top, 'metal1', 4.0, Y0 - 1.94, 7.0, Y0 + PY + 20.0)                # vss trunk (Metal1)
# substrate tap under the trunk: P+ COMP + contacts
k.rect(top, 'comp', 5.0, Y0, 6.0, Y0 + PY + 18.0)
k.rect(top, 'pplus', 4.7, Y0 - 0.3, 6.3, Y0 + PY + 18.3)
k.vias(top, 'contact', 5.0, Y0, 6.0, Y0 + PY + 18.0, inset=0.14)
# second tap column between the two unit columns (DF.14_LV: a substrate tap within 20 um of every NCOMP)
xt = X0 + PX - 2.8
k.rect(top, 'comp', xt, Y0, xt + 0.5, Y0 + PY + 18.0)
k.rect(top, 'pplus', xt - 0.3, Y0 - 0.3, xt + 0.8, Y0 + PY + 18.3)
k.vias(top, 'contact', xt, Y0, xt + 0.5, Y0 + PY + 18.0, inset=0.14)
k.rect(top, 'metal1', xt - 0.2, Y0 - 1.94, xt + 0.7, Y0 + PY + 18.0)
# Metal3 shield under the whole bottom plate, tied to vss west of the plate (no Via3 anywhere: MIMTM.10)
k.rect(top, 'metal3', -8.0, -2.0, W + 2.0, W + 2.0)
k.rect(top, 'metal1', -8.0, Y0 - 1.94, 4.0, Y0 - 0.94)                    # vss lead to the west
k.stack(top, 1, 3, -8.0, Y0 - 3.5, -5.0, Y0 - 0.5)                        # Metal1 -> Metal3 (the shield)
k.rect(top, 'metal1', -8.0, Y0 - 3.5, -5.0, Y0 - 0.94)
k.label(top, 'metal1', 'vss', -6.5, Y0 - 1.44)
save(ly, 'lp_cin_decap', '.subckt lp_cin_decap vn rec vdd_cmp vdd_dac vss\nX1 vn rec cap_mim_2f0_m4m5_noshield c_width=%.3fu c_length=%.3fu\n'
     'X2 vdd_cmp vss cap_nmos_03v3 c_length=20u c_width=20u m=2\nX3 vdd_dac vss cap_nmos_03v3 c_length=20u c_width=20u m=2\n.ends\n' % (W, W))
