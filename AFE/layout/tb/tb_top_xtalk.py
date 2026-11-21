#!/usr/bin/env python3
"""tb_top_xtalk.py (L3b item 4): the X2 S5 run (AFE/adc/scripts/x2_s5.py): TWO complete channels (amplifier + ADC cell each) on ONE bias cell, the shared REF electrode and the modelled supply;
channel 0 = aggressor (electrode step to an output of 2.15 V and 1.15 V, its ADC converts), channel 1 = victim (quiet electrode).  A = both ADCs convert, B = the aggressor ADC idle.
Values: victim_conv_lsb = what the aggressor's conversions add to the victim output at the victim's sampling instants: (A - B) at frames 1 and 2 MINUS (A - B) at frame 0, which is taken before any
        aggressor conversion.  The raw A - B that x2_s5.py prints contains floor_lsb = the difference of the DC operating points of two separate runs (TOhm nodes at reltol 1e-4: 0.02 LSB in the
        X2 run, 0.28 LSB in the LP baseline run): it is a numerical floor, not crosstalk.  dcode_conv = change of the victim code difference after frame 0, victim_peak_mv (victim output right
        after the aggressor's resume, shorter than 0.5 us), kick_mv (aggressor's own output spike).   Pre-layout X2: conversion-induced part <= 1.5 uV = 0.002 LSB (limit 0.5), 0.87 mV, 330 mV.   --amp / --netlist: schematic or the PEX netlist of amp_ch; --adc: schematic or the PEX netlist of adc_ch.
REVIEW R16: the two channels are the same for any chip; the channel count N (--nch, default 4) only selects the decap of the modelled supply (N = 4: Cm 117.9 pF, Cd 47.8 pF of the LVS top; N = 8: the X2 model of the n8 baseline).
usage: python3 AFE/layout/tb/tb_top_xtalk.py [--netlist schematic|<amp_ch PEX>] [--adc schematic|<adc_ch PEX>] [--corner typ] [--nch 4] [--out DIR]"""
import os, sys, re
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lptb import *


def run(netlist, corner, a, log):
    d1 = amp_x2_env(netlist, corner, log)
    d2 = adc_env(a.adc)
    env = {'X2_LOG_PREFIX': X2_PREFIX, 'X2_NADC': str(N_CH['n'])}          # N selects the decap of the modelled supply in x2_s4.MODEL (117.9 / 47.8 pF for N = 4; 125 / 100 pF for the n8 baseline)
    if a.adc != 'schematic':                                # predictor calibration of the EXTRACTED ADC: the file of tb_top_e2e.py with the same netlists if it is there, else x2_s5.py calibrates
        env['X2_CAL_NPZ'] = os.path.join(out_dir(netlist, a.out), 'top_e2e_x2_s1_%s.npz' % corner)
    txt = run_script([os.path.join(ADC, 'scripts', 'x2_s5.py'), corner], env, log)
    x2_collect(out_dir(netlist, a.out), 'top_xtalk', corner)
    m = re.search(r'RESULT S5 \S+: aggressor kick spike on its own output up to ([\d.]+) mV; on the victim output \(A - B\) peak ([\d.]+) mV', txt)
    fr = {}
    for ln in txt.split('\n'):
        q = re.match(r'S5 \S+ L=([\d.]+) frame (\d): aggressor out .*?A - B ([-+][\d.]+) uV .*?victim code A (\d+) / B (\d+)', ln)
        if q:
            fr.setdefault(q.group(1), {})[int(q.group(2))] = (float(q.group(3)), int(q.group(4)) - int(q.group(5)))
    if not m or not fr or any(0 not in f for f in fr.values()):
        raise TbError('x2_s5.py gave no usable result: ' + txt[-400:])
    lsb = CORNERS[corner][2] / 4096 * 1e6
    conv = max(abs(f[k][0] - f[0][0]) for f in fr.values() for k in f if k > 0)
    floor = max(abs(f[0][0]) for f in fr.values())
    dcode = max(abs(f[k][1] - f[0][1]) for f in fr.values() for k in f if k > 0)
    return ({'victim_conv_lsb': conv / lsb, 'victim_conv_uv': conv, 'floor_lsb': floor / lsb, 'dcode_conv': float(dcode), 'kick_mv': float(m.group(1)), 'victim_peak_mv': float(m.group(2))},
            {'amp': netlist, 'adc': a.adc, 'warnings': (d1.warnings if d1 else []) + (d2.warnings if d2 else [])})


if __name__ == '__main__':
    sys.exit(cli('top_xtalk', __doc__, ('typ',), run, lambda ap: (ap.add_argument('--adc', default='schematic'), add_nch(ap))))
