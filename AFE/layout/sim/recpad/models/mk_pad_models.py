#!/usr/bin/env python3
"""mk_pad_models.py (REVIEW.md R13): writes the REC pad models pad_<end>[_rs<R>].spice next to this script.
  end   open  = external end of the bond wire open (the board rule 'high-impedance probe only')
        probe = 10 pF / 10 MOhm scope probe at the external end
  _rs10k / _rs100k = the what-if of R13 item 4: a series resistor between the amplifier input rec and the pad (not part of any design)
Every file defines `.subckt recpad rec vdd vss` (rec = amplifier input, vdd / vss = the chip rails = pad DVDD / DVSS)."""
import os

HDR = '''* REC pad model for REVIEW.md R13 / Decision 53 (AFE/layout/sim/recpad/models/mk_pad_models.py writes this file; do not edit by hand).
* The cell of the PDK IO library on a REC pad: gf180mcu_fd_io__asig_5p0 (gf180mcu_fd_io.spice, copied verbatim below): ESD diodes ASIG5V -> DVDD (diode_pd2nw_06v0, m=4 x 150 um2),
* DVSS -> ASIG5V (diode_nd2ps_06v0, m=4 x 150 um2), a power clamp diode DVDD / DVSS (D0) and the supply decap cap_nmos_06v0 (X1, 36 x 15 x 15 um). It has NO series resistor.
* Pad supplies DVDD = chip VDD, DVSS = VSS (the chip rails; the core pins VDD / VSS of the cell are unused inside the cell).
* Outside the cell: bond wire 2 nH + 0.25 ohm, package / board 2 pF on the board side, external end {END}.
{RS_NOTE}.SUBCKT gf180mcu_fd_io__asig_5p0 ASIG5V DVDD DVSS VDD VSS
D0 DVSS DVDD diode_nd2ps_06v0 m=4.0 area=40e-12 pj=82e-6
X1 DVDD DVSS cap_nmos_06v0 m=36.0 c_length=15e-6 c_width=15e-6
D2 DVSS ASIG5V diode_nd2ps_06v0 m=4.0 area=150e-12 pj=106e-6
D3 ASIG5V DVDD diode_pd2nw_06v0 m=4.0 area=150e-12 pj=106e-6
.ENDS

.subckt recpad rec vdd vss
{RS}Xasig pad vdd vss vdd vss gf180mcu_fd_io__asig_5p0
Lbond pad pw 2n
Rbond pw pb 0.25
Cpkg pb 0 2p
{PROBE}.ends
'''
ENDS = {'open': ('OPEN (high-impedance probe only)', ''), 'probe': ('a 10 pF / 10 MOhm scope probe', 'Cprobe pb 0 10p\nRprobe pb 0 10Meg\n')}

here = os.path.dirname(os.path.abspath(__file__))
for k, (end, probe) in ENDS.items():
    for rs in (None, '10k', '100k'):
        t = HDR.replace('{END}', end).replace('{PROBE}', probe)
        if rs:
            t = t.replace('{RS_NOTE}', '* WHAT-IF (R13 item 4): series resistor %s ohm (high-resistance poly) between the amplifier input rec and the pad; not part of any design.\n' % rs)
            t = t.replace('{RS}', 'Rser rec pad %s\n' % rs)
        else:
            t = t.replace('{RS_NOTE}', '').replace('{RS}', 'Rser rec pad 1m\n')
        open(os.path.join(here, 'pad_%s%s.spice' % (k, '' if rs is None else '_rs' + rs)), 'w').write(t)

# validation model (not a pad): the same wiring without the PDK cell, only the 2 pF + 2.9 pF-equivalent capacitor; used to check lptb.rec_patch's own noise integral against ngspice's onoise_total
open(os.path.join(here, 'pad_check_nodiodes.spice'), 'w').write('* VALIDATION model of R13 (no diodes): 2.87 pF to ground on rec; see AFE/layout/sim/recpad/noise_check.md\n.subckt recpad rec vdd vss\nCcheck rec 0 2.87p\n.ends\n')

# CONTROL models for the reset family (R13 report section 4): a 1 fF capacitor (numerical-sensitivity floor of the long reset transients) and the capacitance of the pad without diodes
open(os.path.join(here, 'pad_ctl_1f.spice'), 'w').write('* CONTROL model of R13: 1 fF on rec = the smallest possible change of the circuit (how much do the long reset transients move by themselves)\n.subckt recpad rec vdd vss\nCctl rec 0 1f\n.ends\n')

# WHAT-IF models for the 10 MOhm probe finding (R13 item 4): a higher-impedance DC probe, an AC-coupled probe (100 nF in series with the 10 MOhm / 10 pF)
for name, probe, note in (('pad_probe_100M', 'Cprobe pb 0 10p\nRprobe pb 0 100Meg\n', 'probe 10 pF / 100 MOhm'), ('pad_probe_1G', 'Cprobe pb 0 10p\nRprobe pb 0 1G\n', 'probe 10 pF / 1 GOhm'),
                          ('pad_probe_ac', 'Cac pb pq 100n\nCprobe pq 0 10p\nRprobe pq 0 10Meg\n', 'AC-coupled probe: 100 nF in series with 10 pF / 10 MOhm')):
    t = open(os.path.join(here, 'pad_open.spice')).read().replace('external end OPEN (high-impedance probe only)', 'external end: ' + note).replace('.ends\n', probe + '.ends\n')
    open(os.path.join(here, name + '.spice'), 'w').write(t)

# WHAT-IF DC leakage (the PDK model leaks only ~1-2 pA at ff 85 C; a real pad / board / ESD structure can leak much more): a constant current from VDD into rec (the direction of the P+/Nwell reverse leakage)
for n in ('1n', '10n'):
    t = open(os.path.join(here, 'pad_open.spice')).read().replace('.ends\n', 'Ileak vdd rec DC %s\n.ends\n' % n)
    open(os.path.join(here, 'pad_leak_%s.spice' % n), 'w').write(t.replace('Outside the cell:', 'WHAT-IF %s DC leakage from VDD into rec added below. Outside the cell:' % n))
