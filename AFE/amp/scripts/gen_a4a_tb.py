#!/usr/bin/env python3
"""Generates the A4a full-channel testbenches from one header: tb_afe_1ch_{op,noise,psrr}.spice (ac tb is hand-edited).
Rerun after changing the netlist hierarchy; outputs are committed."""
import os
T = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'tb')
head = ''.join(open(T + '/tb_afe_1ch_ac.spice').read().split('.control')[0])
head_op = head.replace('.ac: gain, -3 dB corners, phase; FSV=1 closes the fast-settle switches.', '.op: DC levels, supply current, region of every transistor.')
devs = [('xbias.xmp1', 'bias master PMOS mirror'), ('xbias.xmp2', 'bias master PMOS diode'), ('xbias.xmn1', 'bias master NMOS diode'), ('xbias.xmn2', 'bias master NMOS Rb side'),
        ('xch.xsink1', 'OTA1 bias sink'), ('xch.xs1.xota.xmb', 'OTA1 bias diode'), ('xch.xs1.xota.xmt', 'OTA1 tail'), ('xch.xs1.xota.xm1', 'OTA1 pair'),
        ('xch.xs1.xota.xm2', 'OTA1 pair'), ('xch.xs1.xota.xm3', 'OTA1 load diode'), ('xch.xs1.xota.xm4', 'OTA1 load'), ('xch.xs1.xota.xm6', 'OTA1 2nd stage'),
        ('xch.xs1.xota.xm7', 'OTA1 2nd-stage source'), ('xch.xs2.xota2.xmt', 'OTA2 tail'), ('xch.xs2.xota2.xm1', 'OTA2 pair'), ('xch.xs2.xota2.xm2', 'OTA2 pair'),
        ('xch.xs2.xota2.xm3', 'OTA2 load diode'), ('xch.xs2.xota2.xm4', 'OTA2 load'), ('xch.xs2.xota2.xmf', 'follower'), ('xch.xs2.xota2.xms', 'follower sink')]
L = ['.control', 'save all', 'op']
for d, desc in devs:
    n = d.replace('.', '_'); p = f'@m.{d}.m0'
    L += [f'let id_{n} = abs({p}[id])', f'let vds_{n} = abs({p}[vds])', f'let vdsat_{n} = abs({p}[vdsat])', f'let vgs_{n} = abs({p}[vgs])',
          f'let mg_{n} = vds_{n} - vdsat_{n}', f'let gmid_{n} = {p}[gm]/id_{n}',
          f'echo OPDEV {d} id_A=$&id_{n} vgs_V=$&vgs_{n} vds_V=$&vds_{n} vdsat_V=$&vdsat_{n} margin_V=$&mg_{n} gm_over_id=$&gmid_{n}']
L += ['let vo = v(out)', 'let itot = -i(Vdd)', 'let ibia = abs(@m.xch.xsink1.m0[id])', 'let verr = v(out) - v(vcmo)',
      'echo OPSUM vout_V=$&vo vout_err_V=$&verr vbn_V=$&v(vbn) vcm_V=$&v(vcm) vg1_V=$&v(vg1) vcmo_V=$&v(vcmo) vg2_V=$&v(vg2) i_supply_A=$&itot ibias1_A=$&ibia',
      'echo OPNODE v1_V=$&v(xch.v1) vn1_V=$&v(xch.xs1.vn) vp1_V=$&v(xch.xs1.vp) vn2_V=$&v(xch.xs2.vn2) o2_V=$&v(xch.xs2.xota2.o2)', 'quit', '.endc', '.end', '']
open(T + '/tb_afe_1ch_op.spice', 'w').write(head_op + '\n'.join(L))
# ---- noise
noise = head.replace('.ac: gain, -3 dB corners, phase; FSV=1 closes the fast-settle switches.',
                     '.noise: input-referred, integrated 0.5-300 Hz / midband gain.  Feedback elements are IDEAL RESISTORS (noise, Decision 8) = R0 of the pseudo-R.')
noise = noise.replace('.param FSV=0', '.param FSV=0\n.param FN=0\n.param fnoicor=FN\n.param RMODE=1\n.param RMODE2=1\n.param RFIX=5.2e12\n.param RFIX2=5.2e12\n.param RNOISY=1\n.param RNOISY2=1')
ctl = '''.control
ac dec 20 1e-3 1e6
let gdb = vdb(out)
let g1db = vdb(xch.v1)
meas ac g_mid find gdb at=12.25
meas ac g1_mid find g1db at=12.25
let gmid = 10^(g_mid/20)
let g1mid = 10^(g1_mid/20)
set gmid_lin = $&gmid
set g1mid_lin = $&g1mid
noise v(out) Vd dec 100 0.5 300
setplot noise2
let vo_b = onoise_total
let vi_b_mid = vo_b/$gmid_lin
let vi_b_ng = inoise_total
echo NOISE_B_0p5_300 vn_out_V=$&vo_b vn_in_mid_V=$&vi_b_mid vn_in_ngspice_V=$&vi_b_ng gmid_dB=$&g_mid
noise v(xch.v1) Vd dec 100 0.5 300
setplot noise4
let vo_s1 = onoise_total
let vi_s1 = vo_s1/$g1mid_lin
echo NOISE_S1_0p5_300 vn_in_stage1_V=$&vi_s1
noise v(out) Vd dec 50 0.5 2k
setplot noise6
let vo_c = onoise_total
let vi_c = vo_c/$gmid_lin
echo NOISE_C_0p5_2k vn_in_mid_V=$&vi_c
noise v(out) Vd dec 20 0.5 1Meg
setplot noise8
let vo_d = onoise_total
let vi_d = vo_d/$gmid_lin
echo NOISE_D_0p5_1M vn_in_mid_V=$&vi_d
quit
.endc
.end
'''
open(T + '/tb_afe_1ch_noise.spice', 'w').write(noise + ctl)
# ---- PSRR
psrr = head.replace('.ac: gain, -3 dB corners, phase; FSV=1 closes the fast-settle switches.',
                    '.ac with the AC source on VDD (Decision 17b): VDD -> out transfer.  Ideal ratiometric tracking of the ADC mid-scale would be 0.5 V/V.')
psrr = psrr.replace('Vdd vdd 0 {VSUP}', 'Vdd vdd 0 {VSUP} ac 1').replace('Vd vd 0 dc 0 ac 1', 'Vd vd 0 dc 0 ac 0')
ctl = '''.control
ac dec 10 1e-2 1e5
let a = mag(v(out))
meas ac a_dc find a at=0.05
meas ac a_50 find a at=50
meas ac a_60 find a at=60
meas ac a_300 find a at=300
meas ac a_1k find a at=1k
meas ac a_10k find a at=10k
echo RESULT vdd2out_dc=$&a_dc vdd2out_50Hz=$&a_50 vdd2out_60Hz=$&a_60 vdd2out_300Hz=$&a_300 vdd2out_1k=$&a_1k vdd2out_10k=$&a_10k
quit
.endc
.end
'''
open(T + '/tb_afe_1ch_psrr.spice', 'w').write(psrr + ctl)
print('wrote tb_afe_1ch_{op,noise,psrr}.spice')
