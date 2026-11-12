#!/usr/bin/env python3
"""Writes spice/ota2.spice (stage-2 OTA + follower) with the real-diffusion expressions.  Edit the table, rerun, commit the output."""
import os
HERE = os.path.dirname(os.path.abspath(__file__)); S = os.path.join(HERE, '..', 'spice')
def dev(name, kind, d, g, s, b, W, L, m='1'):
    P = 'pfet_03v3' if kind == 'p' else 'nfet_03v3'
    ex = f"ad={{DIFF*{W}*0.18u}} as={{DIFF*{W}*0.18u}} pd={{DIFF*2*({W}+0.18u)}} ps={{DIFF*2*({W}+0.18u)}} nrd=0 nrs=0 sa=0 sb=0 sd=0"
    return f"{name} {d} {g} {s} {b} {P} L={{{L}}} W={{{W}}} nf=1 {ex} m={{{m}}}"
ota2 = ['''* A4a stage-2 OTA: NMOS pair + PMOS mirror load (high-impedance node o2 loaded by CC2) + NMOS source FOLLOWER (buffer, inside the stage-2 loop).
* Pin order = the order xschem emits (inputs, outputs, inouts): inp inn vbn out vdd vss.
* Pins: inp (non-inverting = gate of M1, the DIODE side of the mirror: I1 up -> o2 up; = VOUT_CM), inn (inverting = gate of M2, output side; feedback node), out (buffered), vdd vss, vbn (NMOS mirror gate bias from bias_gen).
* Tail = mirror leg of the master (W/L = 1/20 vs master 4: ~1/80), pair at the same current density (W/L = 1/40 each), follower sink = KSF x master.
* Diffusion: same DIFF scheme as ota1.spice (nrd = nrs = 0).  Dominant pole: CC2 (MIM, o2 to vss).
.subckt ota2 inp inn vbn out vdd vss''',
dev('Xmt', 'n', 'tail', 'vbn', 'vss', 'vss', 'OTA2_WT', 'OTA2_LT'),
dev('Xm1', 'n', 'd1', 'inp', 'tail', 'vss', 'OTA2_WP', 'OTA2_LP'),
dev('Xm2', 'n', 'o2', 'inn', 'tail', 'vss', 'OTA2_WP', 'OTA2_LP'),
dev('Xm3', 'p', 'd1', 'd1', 'vdd', 'vdd', 'OTA2_WL', 'OTA2_LL'),
dev('Xm4', 'p', 'o2', 'd1', 'vdd', 'vdd', 'OTA2_WL', 'OTA2_LL'),
'* follower (drain on vdd, gate o2, source out) and its sink (master unit 16u/4u x BM_KSF)',
dev('Xmf', 'n', 'vdd', 'o2', 'out', 'vss', 'OTA2_WF', 'OTA2_LF'),
dev('Xms', 'n', 'out', 'vbn', 'vss', 'vss', '16u', '4u', 'BM_KSF').replace('W={16u}', 'W=16u').replace('L={4u}', 'L=4u').replace('{DIFF*16u*0.18u}', '{DIFF*16u*0.18u}'),
'Xcc o2 vss cap_mim_2f0_m2m3_noshield c_length={LCC2} c_width={LCC2}',
'.ends ota2']
open(os.path.join(S, 'ota2.spice'), 'w').write('\n'.join(ota2) + '\n')
print('wrote spice/ota2.spice')
