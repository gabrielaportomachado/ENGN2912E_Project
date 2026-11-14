#!/usr/bin/env python3
"""Writes a PWL source file: one value per clock cycle (staircase), changing during the RESET half (clk low) so the input is stable at the evaluate edge.
usage: mkpwl.py <out.inc> <name> <TCYC> <rise> <v0,v1,...>   -> 'V<name> <name> 0 PWL(...)'  Value k holds from k*TCYC+toff.  usage: mkpwl.py out name TCYC rise values [toff]"""
import sys
out, name, tcyc, tr, vals = sys.argv[1], sys.argv[2], float(sys.argv[3]), float(sys.argv[4]), [float(x) for x in sys.argv[5].split(',')]
toff = float(sys.argv[6]) if len(sys.argv) > 6 else 0.25 * tcyc   # switch time inside the cycle (default 0.25*TCYC; for clk delayed 5 ns use TCYC-5n-10n.. see tb)
pts = []; prev = vals[0]
for k, v in enumerate(vals):
    t = k * tcyc + toff
    if k == 0: pts += [(0, v)]
    else: pts += [(t, prev), (t + tr, v)]
    prev = v
pts += [(len(vals) * tcyc + tcyc, prev)]
open(out, 'w').write(f'V{name} {name} 0 PWL(\n' + '\n'.join(f'+ {t:.6e} {v:.9g}' for t, v in pts) + ')\n')
