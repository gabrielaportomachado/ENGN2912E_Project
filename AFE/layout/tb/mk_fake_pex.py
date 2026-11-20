#!/usr/bin/env python3
"""mk_fake_pex.py (LP kit): writes a STAND-IN for a Magic PEX netlist of a layout cell, made from the LVS reference of that cell (AFE/layout/lvs/), so that the PEX path of every golden
testbench can be exercised before the layout exists and re-tested on any machine (tb_selftest.sh).  It is NOT a layout result: never use it as a post-layout number.
What it imitates of `flow.py pex` output: ONE flat subckt with the cell name; ports in another order than the reference; internal nodes with Magic-style names (a_<x>_<y>#); devices
called X0, X1, ...; every m = N device as N separate devices; MIM sizes rounded to the 5 nm grid; ad / as / pd / ps on the MOS devices (the DIFF = 1 formula of the simulation netlists);
parasitic capacitors: --cpar fF from every internal node to vss (default 2) and --ccpl fF between consecutive internal nodes (default 0.2).
usage: python3 AFE/layout/tb/mk_fake_pex.py <amp_ch|adc_ch|bias_genc|afe_ch|tgate> <out.spice> [--cpar fF] [--ccpl fF] [--seed N] [--no-shuffle]"""
import os, sys, re, random, argparse
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lptb import subckts, LAY, REPO, um

REF = {'amp_ch': ('afe_chc.spice', 'amp_ch'), 'adc_ch': ('adc_ch.spice', 'adc_ch'), 'bias_genc': ('bias_genc.spice', 'bias_genc'), 'afe_ch': ('dbs_afe_top.spice', 'afe_ch'), 'tgate': ('dbs_afe_top.spice', 'TGATE')}
MOS = ('nfet_03v3', 'pfet_03v3', 'nfet_06v0_nvt', 'nfet_05v0', 'pfet_05v0', 'nfet_06v0', 'pfet_06v0')


def flatten(subs, name, prefix='', netmap=None):
    nm, ports, elems = subs[name.lower()]
    netmap = netmap or {p.lower(): p.lower() for p in ports}
    out = []
    for e in elems:
        t = e.split()
        nodes = [x for x in t[1:] if '=' not in x]
        par = [x for x in t[1:] if '=' in x]
        model = nodes.pop().lower()
        nn = [netmap.get(n.lower(), prefix + n.lower()) for n in nodes]
        if model in subs:
            cports = subs[model][1]
            if len(cports) != len(nn):
                sys.exit('%s: %d nodes for %d pins of %s' % (t[0], len(nn), len(cports), model))
            out += flatten(subs, model, prefix + t[0].lower() + '/', {p.lower(): n for p, n in zip(cports, nn)})
        else:
            out.append((nn, model, dict(x.lower().split('=') for x in par)))
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('cell', choices=sorted(REF))
    ap.add_argument('out')
    ap.add_argument('--cpar', type=float, default=2.0)
    ap.add_argument('--ccpl', type=float, default=0.2)
    ap.add_argument('--seed', type=int, default=1)
    ap.add_argument('--no-shuffle', action='store_true')
    ap.add_argument('--ref', default=None, help='another reference file (default AFE/layout/lvs/<file of the cell>)')
    a = ap.parse_args()
    rnd = random.Random(a.seed)
    fn, top = REF[a.cell]
    path = a.ref or os.path.join(LAY, 'lvs', fn)
    subs = subckts(path)
    ports = [p.lower() for p in subs[top.lower()][1]]
    devs = flatten(subs, top)
    internal = []
    for nn, _, _ in devs:
        for n in nn:
            if n not in ports and n not in internal:
                internal.append(n)
    ren = {n: 'a_%d_%d#' % (rnd.randint(-9000, 90000), rnd.randint(-9000, 90000)) for n in internal}
    L = ['* STAND-IN for a Magic PEX netlist of %s (mk_fake_pex.py from %s; NOT a layout result)' % (a.cell, os.path.relpath(path, REPO)), '']
    pp = list(subs[top.lower()][1])
    if not a.no_shuffle:
        rnd.shuffle(pp)
    L.append('.subckt %s %s' % (subs[top.lower()][0], ' '.join(pp)))
    k = 0
    grid = lambda v: round(round(v / 0.005) * 0.005, 3)
    for nn, model, par in devs:
        nodes = ' '.join(ren.get(n, n) for n in nn)
        m = int(par.pop('m', '1'))
        if model in MOS:
            w, l = um(par['w']), um(par['l'])
            geo = 'ad=%gp pd=%gu as=%gp ps=%gu w=%gu l=%gu' % (w * 0.18, 2 * (w + 0.18), w * 0.18, 2 * (w + 0.18), w, l)
        elif 'c_width' in par:
            geo = 'c_width=%gu c_length=%gu' % (grid(um(par['c_width'])), grid(um(par['c_length'])))
        elif 'r_width' in par:
            geo = 'r_width=%gu r_length=%gu' % (um(par['r_width']), um(par['r_length']))
        else:
            sys.exit('device %s: parameters %s' % (model, par))
        for _ in range(m):
            L.append('X%d %s %s %s' % (k, nodes, model, geo))
            k += 1
    c = 0
    gnd = 'vss' if 'vss' in ports else ports[-1]
    for i, n in enumerate(internal):
        if a.cpar > 0:
            L.append('C%d %s %s %gf' % (c, ren[n], gnd, a.cpar * (0.5 + rnd.random())))
            c += 1
        if a.ccpl > 0 and i:
            L.append('C%d %s %s %gf' % (c, ren[n], ren[internal[i - 1]], a.ccpl * (0.5 + rnd.random())))
            c += 1
    L += ['.ends', '']
    open(a.out, 'w').write('\n'.join(L))
    print('wrote %s: %d devices, %d parasitic capacitors, %d internal nodes, ports %s' % (a.out, k, c, len(internal), ' '.join(pp)))


if __name__ == '__main__':
    main()
