#!/usr/bin/env python3
"""X2: size of the transfer step at a 512-code boundary (ADC alone, ideal source, closed-loop replay, second frame), for the design and for TESTBENCH-ONLY what-if overrides (PROPOSAL evidence).
Inputs: 2 x NP values on a 5-code pitch just below and just above code boundary B (default 1536, where bit 9 goes 0 -> 1).  e = code + 0.5 - Vin/LSB (code centre minus input).
step = mean(e | code >= B) - mean(e | code < B): 0 for a linear ADC (each mean carries +-0.5/sqrt(12 NP) LSB of quantisation scatter).
usage: x2_inl_step.py <corner> <label> [B=1536] [NP=8]      with X2_EXTRA='.param ...' for a what-if   -> sim/x2_inl_step.log (append)"""
import sys, os, time, numpy as np
H = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, H)
import x2lib as X, x2_adc as A
OFF = {'typ': 30.3, 'ff85': 40.5, 'ss-40': 22.1}       # code offset of the design (X2 S1), only used to place the inputs
ck, label = sys.argv[1], sys.argv[2]; B = int(sys.argv[3]) if len(sys.argv) > 3 else 1536; NP = int(sys.argv[4]) if len(sys.argv) > 4 else 8
lsb = X.COR[ck][2] / 4096; off = float(os.environ.get('X2_OFF', OFF[ck])); k = np.arange(-NP, NP)
vins = list((B + off + 5 * k + 2.5 + 0.31 * np.sin(1.3 * k)) * lsb); out = []
def P(s): print(s, flush=True); out.append(s)
t0 = time.time(); cal, rows, _ = A.static(ck, vins, log=lambda s: None, tag=f'step_{ck}')
r = np.array([(a[0], a[1]) for a in rows]); v, c = r[:, 0], r[:, 1]; e = c + 0.5 - v / lsb; lo = c < B
P(f'INLSTEP {ck} "{label}" extra "{os.environ.get("X2_EXTRA", "")}": boundary {B}: {lo.sum()} codes below ({int(c[lo].min())}..{int(c[lo].max())}), {(~lo).sum()} above ({int(c[~lo].min())}..{int(c[~lo].max())}) | code offset e mean {e.mean():+.2f} LSB | '
  f'e below {e[lo].mean():+.2f} (+-{e[lo].std()/np.sqrt(lo.sum()):.2f}), above {e[~lo].mean():+.2f} (+-{e[~lo].std()/np.sqrt((~lo).sum()):.2f}) -> STEP {e[~lo].mean()-e[lo].mean():+.2f} LSB | predictor: {cal.fitinfo[:230]} | wall {time.time()-t0:.0f} s')
open(f'{X.ADC}/sim/x2_inl_step.log', 'a').write('\n'.join(out) + '\n')
