#!/usr/bin/env python3
"""X2 / S2: reproduce the D5 long-run abort with the UNTRUNCATED ngspice output.
The D5 driver ran ngspice through scripts/dgrun.sh, which pipes the output through `cut -c1-300`; ngspice prints its progress
("Reference value : t") on ONE line separated by carriage returns, and the abort message follows on that same line, so the
log kept only the first ~10 progress values after TSAVE (28 ms) and lost the abort time and the node name.
This script builds exactly the D5 testbench (d5lib.build / controls, same options, same .tran), runs ngspice by PID with the
full output in sim/.ptmp, and prints the last progress value, the abort message and the number of saved rows.
usage: x2_s2_repro.py <corner> <tempC> <tag> <amp_V_out_pk> <M> <N> <TPRE> <TMAXS> [TSAVE] [extra option text, e.g. "method=gear"] [WALL s]
"""
import sys, os, re, subprocess, time, shutil, atexit
H = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, H)
import numpy as np, d5lib as L
from x2lib import SPICEINIT as X_SPICEINIT
ADC = L.ADC; PT = f'{ADC}/sim/.ptmp'
corner, temp, tag, apk, M, N, tpre, tmaxs = sys.argv[1], int(sys.argv[2]), sys.argv[3], float(sys.argv[4]), int(sys.argv[5]), int(sys.argv[6]), float(sys.argv[7]), float(sys.argv[8])
tsave = float(sys.argv[9]) if len(sys.argv) > 9 and sys.argv[9] not in ('', '-') else tpre - 2e-3
extra = sys.argv[10] if len(sys.argv) > 10 else ''
wall = float(sys.argv[11]) if len(sys.argv) > 11 else 3000.0
if os.environ.get('X2_TR'): L.TR = float(os.environ['X2_TR'])      # PWL edge time of the scripted SAR controls (d5lib default 100 ps)
savespec = os.environ.get('X2_SAVE', '')      # e.g. "all" -> wrdata of every node for the saved window (only use with a short window)
f = M * 4000.0 / N; ts = tpre + np.arange(N + 1) * L.TFRAME
codes = np.clip(np.round((1.6502 + apk * np.sin(2 * np.pi * f * ts)) / L.LSB), 0, 4095).astype(int)
ctrl, tread = L.controls([(float(a), int(c)) for a, c in zip(ts, codes)])
tb = L.build(vd=apk / 1000.0, fsig=f, tdsig=0.0, phase=0.0, tstop=float(ts[-1] + L.TFRAME * 0.2), tsave=tsave, tstep=1e-7, tmaxs=tmaxs, reltol=1e-4)
d = f'{PT}/x2_s2_{tag}_{corner}_{os.getpid()}'; os.makedirs(d, exist_ok=True)
if not os.environ.get('X2_KEEP'): atexit.register(shutil.rmtree, d, True)
open(f'{d}/c.inc', 'w').write(ctrl)
# the dgrun.sh transformations, done here: corner, temperature, NSVRS, output file, control include
tb = tb.replace('models_typical', f'models_{corner}').replace('c.inc', f'{d}/c.inc')
tb = re.sub(r'^\.temp .*$', f'.temp {temp}', tb, flags=re.M)
tb = re.sub(r'^(\.param NSVRS=)\S+', lambda m: m.group(1) + str(L.NSVRS[(corner, temp)]), tb, flags=re.M)
if extra:
    ol = re.search(r'^\.options .*$', tb, flags=re.M).group(0); nl = ol
    for kv in extra.split():
        k = kv.split('=')[0]
        nl = re.sub(rf'\b{k}=\S+', kv, nl) if re.search(rf'\b{k}=', nl) else nl + ' ' + kv
    tb = tb.replace(ol, nl)
# testbench-only variants used to locate the mechanism (X2_VARIANT): nocmp = comparator replaced by its 70 fF input capacitance; keep<R> = comparator copy with keeper resistors R
# on the nodes that an ON switch parks at a rail in reset (o1 o2 outp outn clkb -> vss side, a1 a2 b1 b2 -> vdd side), so that Vds of the parking switch cannot cross 0
var = os.environ.get('X2_VARIANT', '')
if var == 'nocmp':
    tb = tb.replace('Xc vcmd t ck outp outn vdd 0 cmp_p', 'Ccmpin t 0 70f\nRoutp outp 0 1k\nRoutn outn 0 1k')
elif var.startswith('keep'):
    R = var[4:]; ct = open(f'{ADC}/spice/comparator.spice').read()
    k = '\n'.join([f'Rk_{n} {n} vss {R}' for n in ('o1', 'o2', 'outp', 'outn', 'clkb')] + [f'Rk_{n} {n} vdd {R}' for n in ('a1', 'a2', 'b1', 'b2')])
    ct = ct.replace('.ends cmp_p', k + '\n.ends cmp_p', 1); open(f'{d}/cmp_keep.spice', 'w').write(ct)
    tb = tb.replace('.include ../spice/comparator.spice', f'.include {d}/cmp_keep.spice')
if savespec == 'all':
    tb = tb.replace('wrdata @OUT@ v(out) v(outu) v(t) v(m)', 'wrdata @OUT@ all')
elif N > 64:      # the D5 testbench keeps EVERY node in memory (no .save): a 512-frame run then dies with 'memory required' (seen at frame 395); keep only the 4 vectors it writes
    tb = tb.replace('.control', '.save v(out) v(outu) v(t) v(m)\n.control', 1)
if os.environ.get('X2_NUMDGT'): tb = tb.replace('set wr_singlescale', 'set numdgt=' + os.environ['X2_NUMDGT'] + '\nset wr_singlescale')
tb = tb.replace('@OUT@', f'{d}/o.csv')
OLD = bool(os.environ.get('X2_OLDSTYLE'))        # as D5 ran it: working directory tb/, relative includes, start-up file ~/.spiceinit
if not OLD: tb = tb.replace('.include ../', f'.include {ADC}/tb/../')        # absolute includes: ngspice runs in the scratch directory (its .spiceinit sets ONE thread unless X2_THREADS is given)
if not OLD: open(f'{d}/.spiceinit', 'w').write(X_SPICEINIT.replace('num_threads=1', 'num_threads=' + os.environ.get('X2_THREADS', '1')))
open(f'{d}/tb.spice', 'w').write(tb)
import x2lib as X                      # only for the machine-wide 3-job slot limit
slot = None
while slot is None:
    slot = X._slot_take()
    if slot is None: time.sleep(1)
X._slots.append(slot)
log = f'{d}/ng.log'; t0 = time.time()
p = subprocess.Popen(['ngspice', '-b', f'{d}/tb.spice'], cwd=f'{ADC}/tb' if OLD else d, stdout=open(log, 'w'), stderr=subprocess.STDOUT, env=dict(os.environ, OMP_NUM_THREADS='1'))
print(f'S2REPRO start pid {p.pid} {tag} {corner} {temp}C N={N} tpre={tpre} tmaxs={tmaxs} tsave={tsave} extra="{extra}" dir {d}', flush=True)
while p.poll() is None:
    if time.time() - t0 > wall: p.kill(); p.wait(); print(f'S2REPRO KILLED by wall-clock {wall:.0f} s (pid {p.pid})', flush=True); break
    time.sleep(2)
X._slot_free(slot); X._slots.remove(slot)
txt = open(log, errors='replace').read().replace('\r', '\n')
ref = re.findall(r'Reference value :\s+(\S+)', txt); rows = re.findall(r'No. of Data Rows : (\d+)', txt)
msg = [l.strip() for l in txt.split('\n') if re.search(r'imestep too small|trouble with|singular|aborted|Error|error', l)]
acct = ' '.join(re.findall(r'(?:Accepted timepoints|Rejected timepoints|Total iterations|Transient iterations) = \d+', txt))
res = f'S2REPRO {tag} {corner} {temp}C N={N} tpre={tpre} tmaxs={tmaxs} TR={L.TR:g} extra="{extra}" variant="{os.environ.get('X2_VARIANT','')}" threads={'as D5 (directory tb/, container start-up files: 8 threads, no compatibility mode)' if os.environ.get('X2_OLDSTYLE') else os.environ.get('X2_THREADS','1')} [{acct}]: wall {time.time()-t0:.0f} s, exit {p.returncode}, last progress t = {ref[-1] if ref else "none"} s (tstop {ts[-1] + L.TFRAME * 0.2:.5f}), rows {rows[-1] if rows else "?"} | ' + ' || '.join(m[:400] for m in msg[:6])
print(res, flush=True)
keep = os.environ.get('X2_LOGOUT')
if keep:
    open(keep, 'a').write(res + '\n')
    tail = txt[-3000:] if len(txt) > 3000 else txt
    open(keep, 'a').write('   --- last lines of the untruncated ngspice output ---\n' + '\n'.join('   ' + l[:500] for l in tail.split('\n')[-25:] if l.strip()) + '\n')
if savespec == 'all' and os.path.exists(f'{d}/o.csv'):
    dst = os.environ.get('X2_CSV', f'{PT}/x2_s2_{tag}_{corner}_all.csv'); shutil.copy(f'{d}/o.csv', dst); print('saved', dst, os.path.getsize(dst))
