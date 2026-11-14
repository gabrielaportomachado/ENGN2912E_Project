#!/usr/bin/env python3
"""D1 input-referred noise of the comparator by injected transient noise (probability vs Vin).
usage: d1_noise.py <corner> <tempC> [NAME=VALUE ...] [--ncyc N] [--span mV] [--na2] [--tag T] [--cm V]
 1. runs tb_cmp_gm (no noise) -> gm of the input pair averaged over the integration window (clk rise -> max(a1,a2) = 0.8 V)  [IDEAL-free: simulated]
 2. NA1 = sqrt(4 k T gamma gm / (2 NT)), gamma = 1 (conservative: strong inversion 2/3, weak ~0.5-0.65)
 3. noisy staircase run: one differential step per clock cycle, decisions fitted with a probit (ML) -> trip point mu and noise sigma (input-referred, rms)
Output: one line  'NOISE corner temp  gm=.. NA1=..  mu=.. uV  sigma=.. uV (+-..)  ncyc=..' appended to sim/d1_noise.log (and echoed)."""
import shutil, atexit, sys, os, subprocess, tempfile, math, numpy as np
from scipy.optimize import minimize
from scipy.stats import norm
sys.path.insert(0, os.path.dirname(__file__)); import dlib
ADC = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
args = [a for a in sys.argv[1:] if not a.startswith('--')]
opt = {a.split('=')[0]: a.split('=', 1)[1] if '=' in a else '1' for a in sys.argv[1:] if a.startswith('--')}
corner, T = args[0], float(args[1]); over = args[2:]
ncyc = int(opt.get('--ncyc', 600)); span = float(opt.get('--span', 0.6)) * 1e-3; cm = float(opt.get('--cm', 1.65)); tag = opt.get('--tag', '')
TCYC = 30e-9; TCLK0 = 5e-9; NT = 50e-12; kB = 1.380649e-23
tmp = tempfile.mkdtemp(prefix='d1n_', dir=os.path.join(ADC, 'sim', '.ptmp')); atexit.register(shutil.rmtree, tmp, True)
def run(tb, out, extra, env=None):
    e = dict(os.environ, OUT=out, **(env or {}))
    r = subprocess.run(['bash', f'{ADC}/scripts/dgrun.sh', tb, corner, str(T)] + over + extra, capture_output=True, text=True, env=e)
    open(f'{tmp}/last.log', 'w').write(r.stdout)
    if not os.path.exists(out): print([l[-250:] for l in r.stdout.splitlines() if 'too small' in l.lower() or 'singular' in l.lower() or 'rror' in l][:4]); raise SystemExit('run failed ' + tb)
# ---- 1. gm
run('tb_cmp_gm.spice', f'{tmp}/gm.csv', [f'CM={cm}', 'DVG=1m'])
t, d = dlib.load(f'{tmp}/gm.csv', ['clk', 'a1', 'a2', 'gm1', 'id1', 'itail', 'outp', 'outn', 'gmc1', 'gmc2', 'gmn2', 'o1', 'o2'])
tr = dlib.cross(t, d['clk'], 1.65, True, 30e-9, 60e-9)    # second clk rise (after power-up transient)
m = (t > tr + 0.2e-9) & (t < tr + 8e-9) & (np.maximum(d['a1'], d['a2']) < 0.8)
gm = np.trapezoid(d['gm1'][m], t[m]) / (t[m][-1] - t[m][0])
na1 = math.sqrt(4 * kB * (T + 273.15) * 1.0 * gm / (2 * NT))
# latch devices ACTUALLY on the regenerating side (o2 falls, Mc2 + Mn2): gm at the moment o2 crosses 1.65 V (middle of the regeneration) from the simulated operating point
tx = dlib.cross(t, d['o2'], 1.65, False, tr, tr + 8e-9)
gmc_, gmn_ = float(np.interp(tx, t, d['gmc2'])), float(np.interp(tx, t, d['gmn2']))
nvc = math.sqrt(4 * kB * (T + 273.15) * 1.0 / gmc_ / (2 * NT)); nvn = math.sqrt(4 * kB * (T + 273.15) * 1.0 / gmn_ / (2 * NT))
nzf = f'{tmp}/nz.spice'; subprocess.run(['python3', f'{ADC}/scripts/mk_noisy_cell.py', nzf, f'{na1:.6g}', f'{nvc:.6g}', f'{nvn:.6g}', str(NT)], check=True)
# ---- 3. noisy staircase
vd = np.linspace(-span, span, ncyc)
def mk(name, vals, path): subprocess.run(['python3', f'{ADC}/scripts/mkpwl.py', path, name, str(TCYC), '100e-12', ','.join(f'{v:.9g}' for v in vals), str(-TCLK0)], check=True)
mk('inp', cm + vd / 2, f'{tmp}/p.inc'); mk('inn', cm - vd / 2, f'{tmp}/n.inc')
sw = f'@PWLP@={tmp}/p.inc @PWLN@={tmp}/n.inc @NZFILE@={nzf}'
extra = [f'NCYC={ncyc + 2}', f'TCYC={TCYC}', f'TCLK0={TCLK0}']
run('tb_cmp_noise.spice', f'{tmp}/n.csv', extra, {'SWAPS': sw, 'CELL': 'cmp_p_nz'})
t, d = dlib.load(f'{tmp}/n.csv', ['outp', 'outn', 'clk', 'i_vdd'])
if t[-1] < TCLK0 + ncyc * TCYC:
    shutil.copy(f'{tmp}/last.log', os.path.join(ADC, 'sim', '.ptmp', 'last_debug.log')); print('SHORT RUN (aborted?): ', [l for l in open(f'{tmp}/last.log').read().splitlines() if l.strip()][-8:], [l for l in open(f'{tmp}/last.log').read().splitlines() if 'oo small' in l or 'ingular' in l or 'trouble' in l][:3]); raise SystemExit(1)
dec = []
for k in range(ncyc):
    ts = TCLK0 + k * TCYC + TCYC / 2 - 1e-9                     # end of the evaluate phase
    i = np.searchsorted(t, ts); dec.append(1 if d['outp'][i] - d['outn'][i] > 0 else 0)
dec = np.array(dec)
def nll(p):
    mu, ls = p; s = math.exp(ls); pr = np.clip(norm.cdf((vd - mu) / s), 1e-12, 1 - 1e-12)
    return -np.sum(dec * np.log(pr) + (1 - dec) * np.log(1 - pr))
r = minimize(nll, [0.0, math.log(span / 6)], method='Nelder-Mead', options={'xatol': 1e-9, 'fatol': 1e-6})
mu, s = r.x[0], math.exp(r.x[1])
# Fisher-style 1-sigma uncertainty of sigma from the bootstrap-free approximation: sigma/sqrt(2*Neff), Neff = number of cycles within +-2 sigma of the trip point
neff = max(1, int(np.sum(np.abs(vd - mu) < 2 * s))); ds = s / math.sqrt(2 * neff)
line = f'NOISE {corner} {T:g}C {tag} gm_pair={gm*1e6:.0f}uS gm_Mc2={gmc_*1e6:.0f}uS gm_Mn2={gmn_*1e6:.0f}uS(at o2=1.65V)  mu={mu*1e6:.1f}uV sigma={s*1e6:.1f}uV (+-{ds*1e6:.1f}) ncyc={ncyc} span=+-{span*1e3:.2f}mV decisions1={dec.sum()} ' + ' '.join(over)
print(line); open(f'{ADC}/sim/d1_noise.log', 'a').write(line + '\n')
