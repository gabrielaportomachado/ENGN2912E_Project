#!/usr/bin/env python3
"""tb_top_supply.py (L3b item 3): the X2 S4 run (AFE/adc/scripts/x2_s4.py): N ADC cells (N = --nch, default 4; the n8 baseline: 8) converting with the staggered comparator clocks at SCLK 3 MHz on the MODELLED supply: one VDD and one
VSS pad (R + L each, 1 pF pad capacitance), main rail with its decap and ESR, DAC strap behind the strap resistor with its decap and ESR, digital charge of the macro as a current source.
--model FILE (JSON, written by L3b from the extracted straps): {"Rp": ohm per pad, "Lp": H per pad, "Cm": F, "Cd": F, "Rs": ohm, "Rd": ohm, "qdig_pC_per_cycle": pC of afe_dig per SCLK cycle}.
Default N = 4 (REVIEW R16): Rp 0.25 ohm, Lp 2 nH (ASSUMED), Rs 10 ohm and Rd 3 ohm (X2 S4 values, not re-derived: no extracted straps yet), decap Cm = 74 x 1.593 = 117.9 pF and Cd = 30 x 1.593 = 47.8 pF (the
LVS top AFE/layout/lvs/dbs_afe_top.spice), digital charge of the 4-channel macro afe_dig = 17.0 pC per SCLK cycle at tt 3.3 V, 19.1 pC at ff -40 C 3.6 V, 15.5 pC at ss 125 C 3.0 V (AFE/dig/reports/power_dig.log),
spread over the N ADCs as before (X2_QDIG = charge / N per converting ADC per edge).  N = 8 (--nch 8, needs --out): the X2 model of the n8 baseline (0.125 nF, 0.1 nF; 24 / 27 pC of D3).
Values (worst of the cases fs, mid, alt): dcode_max (code change against the same ADC alone on an ideal supply), dt_max_lsb (shift of the trial-12 transition level), dres_max_lsb (largest change of
the plate residue at any decision instant), droop_dac_mv, droop_main_mv, failed.   Pre-layout X2: <= 0.11 LSB at typ / ss 125; ff -40 C 3.6 V: residue 0.33-0.50 LSB, transition shift <= 0.25 LSB.
usage: python3 AFE/layout/tb/tb_top_supply.py [--netlist schematic|<adc_ch PEX>] [--corner typ|ff-40|ss125|all] [--model FILE] [--cases fs,mid,alt] [--nch 4] [--out DIR]"""
import os, sys, re
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lptb import *

# the supply model per channel count is SUPPLY_BY_N of lptb.py (4: layout of REVIEW R14; 8: the X2 / D3 values of the n8 baselines)


def run(netlist, corner, a, log):
    d = adc_env(netlist)
    m = json.load(open(a.model)) if a.model else {}
    n = N_CH['n']
    base = SUPPLY_BY_N.get(n)
    if base is None:
        raise TbError('no supply model for N = %d (SUPPLY_BY_N of lptb.py has %s): give --model FILE with Cm, Cd and qdig_pC_per_cycle' % (n, sorted(SUPPLY_BY_N)))
    q = m.get('qdig_pC_per_cycle', base['qdig_pC_per_cycle'].get(corner))
    if q is None:
        raise TbError('no digital charge for corner %s' % corner)
    env = {'X2_LOG_PREFIX': X2_PREFIX, 'X2_NADC': str(n), 'X2_QDIG': '%g' % (q / n * 1e-12)}
    for k, e in (('Cm', 'X2_CM'), ('Cd', 'X2_CD'), ('Lp', 'X2_LP'), ('Rd', 'X2_RD'), ('Rs', 'X2_RS'), ('Rp', 'X2_RP')):
        if k in m:
            env[e] = '%g' % m[k]            # (no override of the default model = no WHAT-IF label: x2_s4.py has the decap of N = 4 / 8 built in, equal to SUPPLY_BY_N of lptb.py)
    txt = run_script([os.path.join(ADC, 'scripts', 'x2_s4.py'), corner, a.cases, '3'], env, log)
    v = {'dcode_max': 0.0, 'dt_max_lsb': 0.0, 'dres_max_lsb': 0.0, 'droop_dac_mv': 0.0, 'droop_main_mv': 0.0}
    n = 0
    for ln in txt.split('\n'):
        mm = re.match(r'RESULT S4 \S+ (\S+) .*?max (\d+) LSB; max \|dT\| ([\d.]+) LSB; max per-trial residue change ([\d.na]+) LSB; worst decision-instant droop: DAC strap ([\d.]+) mV, main rail ([\d.]+) mV', ln)
        if mm:
            n += 1
            for k, x in zip(('dcode_max', 'dt_max_lsb', 'dres_max_lsb', 'droop_dac_mv', 'droop_main_mv'), mm.groups()[1:]):
                try:
                    v[k] = max(v[k], float(x))
                except ValueError:
                    pass
    x2_collect(out_dir(netlist, a.out), 'top_supply', corner)
    v['failed'] = float(len(a.cases.split(',')) - n)
    if n == 0:
        raise TbError('x2_s4.py gave no RESULT line: ' + txt[-400:])
    return v, {'model': m or 'X2 S4 default, decap / charge of N = %d (lptb.SUPPLY_BY_N)' % n, 'Cm_F': float(m.get('Cm', base['Cm'])), 'Cd_F': float(m.get('Cd', base['Cd'])), 'qdig_pC_per_cycle': q,
               'qdig_pC_per_ADC_per_edge': float(env['X2_QDIG']) * 1e12, 'warnings': d.warnings if d else []}


if __name__ == '__main__':
    def more(ap):
        ap.add_argument('--model', default=None)
        ap.add_argument('--cases', default='fs,mid,alt')
        add_nch(ap)
    sys.exit(cli('top_supply', __doc__, ('typ', 'ff-40'), run, more))
