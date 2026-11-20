#!/usr/bin/env python3
"""LP step 6 (audit issue M7): native-Vt fallback of the stage-2 follower.  Library for scripts/lp_rvt_*.py.

What it does: builds ngspice decks from the EXISTING testbenches of AFE/amp/tb (read only; include paths rewritten to absolute, corner / temperature / parameters set exactly as scripts/ngrun.sh does),
swaps the follower netlist (spice/ota2.spice) for a candidate, runs the jobs and parses the RESULT lines / CSV files.  The ORIGINAL netlist is always run by the same code in the same session.
Rules (AFE/prompts/layout_run.md common rules 4 and 8): one ngspice thread per job (job-local .spiceinit `set num_threads=1`), every ngspice through AFE/layout/scripts/slot.sh, at most NPAR = 2 of
this script's jobs at a time, PIDs are polled (no pgrep / pkill, no `timeout`), the ngspice output is never piped through `cut`: the whole log is read (carriage returns -> newlines) and searched for
the abort message; an aborted transient is re-run ONCE with a slightly different step cap.  Scratch: /tmp/lp_rvt (container disk).  Design netlists are only read.
Transients here use `.options abstol=1e-12 chgtol=1e-17 vntol=1e-7` (Decision 43a) for the original AND the variant; op / ac / noise keep the options of the A4c testbenches.
"""
import os, re, sys, subprocess, time, shutil, math, json
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
AMP = os.path.normpath(os.path.join(HERE, '..'))
AFE = os.path.normpath(os.path.join(AMP, '..'))
REPO = os.path.normpath(os.path.join(AFE, '..'))
ADC = os.path.join(AFE, 'adc')
SIM = os.path.join(AMP, 'sim')
SLOT = os.path.join(AFE, 'layout', 'scripts', 'slot.sh')
NG = '/foss/tools/bin/ngspice'
SCR = os.environ.get('LP_RVT_SCRATCH', '/tmp/lp_rvt')
NPAR = int(os.environ.get('LP_RVT_NPAR', '2'))
CORNERS = [('typical', 27), ('ff', 85), ('ss', -40)]
CKEY = {('typical', 27): 'typ', ('ff', 85): 'ff85', ('ss', -40): 'ss-40'}
# IDEAL RESISTOR (noise) values of Decision 8 = R0 of the A4c pseudo-R per corner (AFE/amp/sim/a4c_noise.log headers; the same numbers as AFE/review/scripts/freq_noise.py)
RFIX = {('typical', 27): (5.23534e12, 5.23572e12), ('ff', 85): (4.68481e12, 6.22437e12), ('ss', -40): (4.0999e12, 4.0999e12)}
NSVRS = {('typical', 27): 1.02771, ('ff', 85): 1.22173, ('ss', -40): 0.813879,         # start guess of the reset-level node (AFE/adc/scripts/x2lib.py, d5lib.py)
         ('typical', -40): 0.929467, ('typical', 85): 1.11139, ('ff', -40): 1.04386, ('ff', 27): 1.14011, ('ss', 27): 0.913448, ('ss', 85): 0.998332}
CORNERS9 = [(k, T) for k in ('typical', 'ff', 'ss') for T in (-40, 27, 85)]
for _k, _T in CORNERS9:
    CKEY.setdefault((_k, _T), '%s%+d' % ({'typical': 'typ', 'ff': 'ff', 'ss': 'ss'}[_k], _T))
LSB = 3.3 / 4096
TRAN_OPT = '.options gmin=1e-16 abstol=1e-12 reltol=1e-4 vntol=1e-7 chgtol=1e-17 itl1=500 itl4=500'

# ------------------------------------------------------------------ follower candidates (only the line Xmf of ota2.spice changes)
# name: (model, W, L, bulk node, m, text)
CAND = {
    'orig':     None,                                                                                   # spice/ota2.spice as it is: nfet_06v0_nvt 10u/2u, bulk vss
    'A_10_2':   ('nfet_03v3', '10u', '2u', 'out', 1, 'A: nfet_03v3 10u/2u in an isolated p-well (deep n-well), bulk = source'),
    'A_20_1':   ('nfet_03v3', '20u', '1u', 'out', 1, 'A: nfet_03v3 20u/1u, isolated p-well, bulk = source'),
    'A_40_0p5': ('nfet_03v3', '40u', '0.5u', 'out', 1, 'A: nfet_03v3 40u/0.5u, isolated p-well, bulk = source'),
    'A_40_1':   ('nfet_03v3', '40u', '1u', 'out', 1, 'A: nfet_03v3 40u/1u, isolated p-well, bulk = source'),
    'A_80_1':   ('nfet_03v3', '80u', '1u', 'out', 1, 'A: nfet_03v3 80u/1u, isolated p-well, bulk = source'),
    'A_100_0p5': ('nfet_03v3', '100u', '0.5u', 'out', 1, 'A: nfet_03v3 100u/0.5u, isolated p-well, bulk = source'),
    'B_10_2':   ('nfet_03v3', '10u', '2u', 'vss', 1, 'B: nfet_03v3 10u/2u, bulk vss (= the A4a follower)'),
    'B_40_0p5': ('nfet_03v3', '40u', '0.5u', 'vss', 1, 'B: nfet_03v3 40u/0.5u, bulk vss'),
    'B_100_0p5': ('nfet_03v3', '100u', '0.5u', 'vss', 1, 'B: nfet_03v3 100u/0.5u, bulk vss (weak inversion)'),
    'B_100_0p28': ('nfet_03v3', '100u', '0.28u', 'vss', 1, 'B: nfet_03v3 100u/0.28u, bulk vss (weak inversion, minimum L)'),
    'B_400_0p5': ('nfet_03v3', '100u', '0.5u', 'vss', 4, 'B: nfet_03v3 4 x 100u/0.5u, bulk vss (deep weak inversion)'),
    'B_100_0p3': ('nfet_03v3', '100u', '0.3u', 'vss', 1, 'B: nfet_03v3 100u/0.3u, bulk vss'),
    'B_100_0p35': ('nfet_03v3', '100u', '0.35u', 'vss', 1, 'B: nfet_03v3 100u/0.35u, bulk vss'),
    'B_100_0p4': ('nfet_03v3', '100u', '0.4u', 'vss', 1, 'B: nfet_03v3 100u/0.4u, bulk vss'),
    'B_200_0p28': ('nfet_03v3', '100u', '0.28u', 'vss', 2, 'B: nfet_03v3 2 x 100u/0.28u, bulk vss'),
    'B_400_0p28': ('nfet_03v3', '100u', '0.28u', 'vss', 4, 'B: nfet_03v3 4 x 100u/0.28u, bulk vss'),
    'B_40_0p28': ('nfet_03v3', '40u', '0.28u', 'vss', 1, 'B: nfet_03v3 40u/0.28u, bulk vss'),
    'A_80_0p5': ('nfet_03v3', '80u', '0.5u', 'out', 1, 'A: nfet_03v3 80u/0.5u, isolated p-well, bulk = source'),
    'A_40_0p28': ('nfet_03v3', '40u', '0.28u', 'out', 1, 'A: nfet_03v3 40u/0.28u, isolated p-well, bulk = source'),
    'A_40_2':   ('nfet_03v3', '40u', '2u', 'out', 1, 'A: nfet_03v3 40u/2u, isolated p-well, bulk = source'),
    'A_4x10_1': ('nfet_03v3', '10u', '1u', 'out', 4, 'A: nfet_03v3 4 x 10u/1u, isolated p-well, bulk = source'),
    'A_8x10_1': ('nfet_03v3', '10u', '1u', 'out', 8, 'A: nfet_03v3 8 x 10u/1u, isolated p-well (deep n-well on vdd), bulk = source  [= spice/ota2_rvt.spice]'),
    'A_10x10_0p5': ('nfet_03v3', '10u', '0.5u', 'out', 10, 'A: nfet_03v3 10 x 10u/0.5u, isolated p-well, bulk = source'),
    'B_10x10_0p28': ('nfet_03v3', '10u', '0.28u', 'vss', 10, 'B: nfet_03v3 10 x 10u/0.28u (minimum L), bulk vss, NO deep n-well'),
    'B_40x10_0p28': ('nfet_03v3', '10u', '0.28u', 'vss', 40, 'B: nfet_03v3 40 x 10u/0.28u (minimum L), bulk vss, NO deep n-well'),
    'C5_40_0p6': ('nfet_05v0', '40u', '0.6u', 'vss', 1, 'C: nfet_05v0 40u/0.6u, bulk vss'),
    'C6_40_0p7': ('nfet_06v0', '40u', '0.7u', 'vss', 1, 'C: nfet_06v0 40u/0.7u, bulk vss'),
    'C5i_40_0p6': ('nfet_05v0', '40u', '0.6u', 'out', 1, 'C: nfet_05v0 40u/0.6u, isolated p-well, bulk = source'),
}


def ota2_text(name):
    """ota2 netlist of a candidate: spice/ota2.spice with ONE changed line (Xmf)."""
    src = open(os.path.join(AMP, 'spice', 'ota2.spice')).read()
    if CAND[name] is None:
        return src
    model, w, l, bulk, m, txt = CAND[name]
    new = ('Xmf vdd o2 out %s %s L=%s W=%s nf=1 ad={DIFF*%s*0.18u} as={DIFF*%s*0.18u} pd={DIFF*2*(%s+0.18u)} ps={DIFF*2*(%s+0.18u)} nrd=0 nrs=0 sa=0 sb=0 sd=0 m={%d}'
           % (bulk, model, l, w, w, w, w, w, m))
    out, n = [], 0
    for ln in src.split('\n'):
        if ln.startswith('Xmf '):
            out.append('* lp_rvt candidate %s: %s' % (name, txt))
            out.append(new)
            n += 1
        else:
            out.append(ln)
    if n != 1:
        raise SystemExit('ota2.spice: expected exactly one Xmf line')
    return '\n'.join(out)


# WHAT-IF "<variant>+dio": the parasitic LVPWELL / DNWELL junction of the isolated follower, PDK model diode_pw2dw from the amplifier output (p-well = follower source) to vdd (deep n-well),
# added at TESTBENCH level across the pins out / vdd (it is not a device of the netlist).  Size = ESTIMATE of the isolated p-well of 8 x 10u/1u with its tap ring, upper bound: 20 x 20 um.
DIO_AREA, DIO_PJ = 400e-12, 80e-6
DIO_C0 = 0.00032124 * DIO_AREA + 5.4659e-10 * DIO_PJ        # zero-bias junction capacitance from the model card diode_pw2dw (cjo, cjp): 172 fF


def base(name):
    return name[:-4] if name.endswith('+dio') else name


def ota2_file(name, d=None):
    """path of the ota2 netlist to include for a candidate.  'orig' -> the design file; 'rvt' -> the committed variant spice/ota2_rvt.spice; else a generated file in the scratch."""
    name = base(name)
    if name == 'orig':
        return os.path.join(AMP, 'spice', 'ota2.spice')
    if name == 'rvt':
        return os.path.join(AMP, 'spice', 'ota2_rvt.spice')
    d = d or os.path.join(SCR, 'var')
    os.makedirs(d, exist_ok=True)
    fn = os.path.join(d, 'ota2_%s.spice' % name)
    open(fn, 'w').write(ota2_text(name))
    return fn


def chc_file(name):
    """afe_chc netlist: the committed variant file for 'rvt' (it must be used together with ota2_rvt.spice), the design file otherwise."""
    return os.path.join(AMP, 'spice', 'afe_chc_rvt.spice' if base(name) == 'rvt' else 'afe_chc.spice')


# ------------------------------------------------------------------ deck builder (same substitutions as scripts/ngrun.sh)
def deck(tb, corner, temp, var='orig', params=None, out=None, opt=None, extra=(), tbtext=None, control=None, dio_as_cap=False):
    """tb = file name in AFE/amp/tb (or tbtext = its text).  params: {NAME: value} (a `.param NAME=` line of the testbench is rewritten, otherwise a `.param` line is added after `.temp`).
    opt: replacement of the whole .options line (None = keep the testbench's).  extra: lines added before `.control` / `.tran`.  control: replacement of the .control block (list of lines)."""
    t = tbtext if tbtext is not None else open(os.path.join(AMP, 'tb', tb)).read()
    t = t.replace('../spice/models_typical.spice', '%s/spice/models_%s.spice' % (AMP, corner))
    t = t.replace('../spice/ota2.spice', ota2_file(var)).replace('../spice/afe_chc.spice', chc_file(var))
    t = t.replace('../spice/', AMP + '/spice/').replace('../../../TGATE/', REPO + '/TGATE/')
    t = re.sub(r'^\.temp .*$', '.temp %g' % temp, t, flags=re.M)
    if opt:
        t = re.sub(r'^\.options .*$', opt, t, count=1, flags=re.M)
    for k, v in (params or {}).items():
        v = v if isinstance(v, str) else '%.10g' % v
        if re.search(r'^\.param %s=' % re.escape(k), t, flags=re.M):
            t = re.sub(r'^(\.param %s=)\S*' % re.escape(k), lambda m: m.group(1) + v, t, flags=re.M)
        else:
            t = re.sub(r'^(\.temp .*)$', lambda m: m.group(1) + '\n.param %s=%s' % (k, v), t, count=1, flags=re.M)
    if out:
        t = t.replace('@OUT@', out)
    if var.endswith('+dio'):
        outs = [n for n in ('out1', 'out2') if re.search(r'\b%s\b' % n, t)] or ['out']
        if dio_as_cap:      # .noise returns NaN with the PDK level-3 diode card in ngspice-46 (a model / simulator problem of the what-if element): there the junction is its zero-bias capacitance
            extra = list(extra) + ['Cpwdw_%s %s vdd %g' % (n, n, DIO_C0) for n in outs]      # IDEAL C, upper bound (cjo x area + cjp x perimeter, typical); its fA shot noise is not modelled
        else:
            extra = list(extra) + ['Dpwdw_%s %s vdd diode_pw2dw area=%g pj=%g' % (n, n, DIO_AREA, DIO_PJ) for n in outs]
        t = re.sub(r'^(\.temp .*)$', lambda m: '.lib /foss/pdks/gf180mcuD/libs.tech/ngspice/sm141064.ngspice diode_%s\n' % corner + m.group(1), t, count=1, flags=re.M)   # the well-diode models
    if extra:
        i = t.index('.control') if '.control' in t else t.index('.end')
        j = t.rfind('\n.tran', 0, i)
        k = j + 1 if j >= 0 else i
        t = t[:k] + '\n'.join(extra) + '\n' + t[k:]
    if control is not None:
        i = t.index('.control')
        t = t[:i] + '\n'.join(['.control'] + list(control) + ['.endc', '.end']) + '\n'
    return t


# ------------------------------------------------------------------ job runner
def run_jobs(jobs, tag, npar=None, log=print, retry=None, wall=7200.0):
    """jobs: list of (name, deck text).  retry: optional function(name, text) -> new text for ONE re-run of an aborted job.  Returns {name: dict(ok, out, abort, wall, dir, tries)}."""
    npar = npar or NPAR
    d = os.path.join(SCR, tag)
    os.makedirs(d, exist_ok=True)
    open(os.path.join(d, '.spiceinit'), 'w').write('set num_threads=1\n')
    st = os.statvfs(SCR)
    if st.f_bavail * st.f_frsize / 2 ** 30 < 2.0:
        raise SystemExit('STOP: less than 2 GB free in the scratch disk')
    todo = [(n, t, 1) for n, t in jobs]
    run, res = [], {}
    while todo or run:
        while todo and len(run) < npar:
            name, net, tr = todo.pop(0)
            fn = os.path.join(d, name + '.spice')
            lg = os.path.join(d, name + '.log')
            open(fn, 'w').write(net)
            p = subprocess.Popen(['bash', SLOT, NG, '-b', fn], cwd=d, stdout=open(lg, 'w'), stderr=subprocess.STDOUT, env=dict(os.environ, OMP_NUM_THREADS='1'))
            run.append((p, name, lg, time.time(), net, tr))
        time.sleep(0.2)
        for r in list(run):
            p, name, lg, t0, net, tr = r
            if p.poll() is None:
                if time.time() - t0 > wall:
                    p.kill()
                    p.wait()
                else:
                    continue
            run.remove(r)
            txt = open(lg, errors='replace').read().replace('\r', '\n')
            ab = ' | '.join(l.strip()[:220] for l in txt.split('\n') if re.search(r'imestep too small|trouble with|ingular matrix|aborted|No convergence|doAnalyses|rror', l))[:700]
            fatal = bool(re.search(r'imestep too small|ingular matrix|aborted|No convergence|doAnalyses', txt))
            if fatal and retry and tr == 1:
                log('   job %s aborted (%s): one re-run with another step cap' % (name, ab[:160]))
                todo.append((name, retry(name, net), 2))
                continue
            res[name] = dict(ok=(p.returncode == 0 and not fatal), out=txt, abort=ab, wall=time.time() - t0, dir=d, tries=tr)
            log('   job %-34s pid %d exit %s wall %5.0f s try %d%s' % (name, p.pid, p.returncode, time.time() - t0, tr, (' MSG ' + ab) if ab else ''))
    return res


def retry_tmax(name, net):
    """the one re-run of an aborted transient: step cap x 0.9 (the 4th number of the .tran line; a parameter value if it is one)"""
    m = re.search(r'^\.param TMAXS=(\S+)', net, flags=re.M)
    if m:
        v = m.group(1)
        num = re.match(r'[-+0-9.eE]+', v).group(0)
        return re.sub(r'^(\.param TMAXS=)\S+', lambda mm: mm.group(1) + '%.6g' % (float(num) * 0.9) + v[len(num):], net, flags=re.M)
    return re.sub(r'^(\.tran\s+\S+\s+\S+\s+\S+\s+)(\S+)', lambda mm: mm.group(1) + '%.6g' % (float(mm.group(2)) * 0.9), net, flags=re.M)


def results(txt, key='RESULT'):
    out = []
    for ln in txt.split('\n'):
        if ln.startswith(key + ' '):
            dd = {}
            for kv in ln.split()[1:]:
                if '=' in kv:
                    k, v = kv.split('=', 1)
                    try:
                        dd[k] = float(v)
                    except ValueError:
                        dd[k] = v
            out.append(dd)
    return out


def keep_logs(res, tgz):
    """save the complete ngspice outputs of a stage (carriage returns as newlines) as one compressed archive next to the result log"""
    import tarfile, io
    with tarfile.open(tgz, 'w:gz') as tf:
        for name in sorted(res):
            b = res[name]['out'].encode()
            ti = tarfile.TarInfo(name + '.log')
            ti.size = len(b)
            ti.mtime = int(time.time())
            tf.addfile(ti, io.BytesIO(b))


class Log:
    def __init__(self, path, mode='w'):
        self.f = open(path, mode)
        self.path = path

    def __call__(self, *a):
        s = ' '.join(str(x) for x in a)
        print(s, flush=True)
        self.f.write(s + '\n')
        self.f.flush()


def load_csv(path):
    """ngspice wrdata with wr_singlescale + wr_vecnames -> (names, array)"""
    with open(path) as f:
        names = f.readline().split()
    return names, np.loadtxt(path, skiprows=1)


def harmonics(t, y, f, nper, nh=9, tend=None, ppc=400):
    """least-squares fit over the last nper periods (same method as scripts/a4c_lib.py): returns (fundamental amplitude, THD fraction, mean)"""
    if tend is None:
        tend = t[-1]
    T = 1.0 / f
    t0 = tend - nper * T
    tu = np.linspace(t0, tend, int(nper * ppc), endpoint=False)
    yu = np.interp(tu, t, y)
    tm = 0.5 * (t0 + tend)
    cols = [np.ones_like(tu), tu - tm]
    for k in range(1, nh + 1):
        cols += [np.cos(2 * np.pi * k * f * (tu - t0)), np.sin(2 * np.pi * k * f * (tu - t0))]
    A = np.array(cols).T
    c = np.linalg.lstsq(A, yu, rcond=None)[0]
    amps = [math.hypot(c[2 + 2 * (k - 1)], c[3 + 2 * (k - 1)]) for k in range(1, nh + 1)]
    return amps[0], math.sqrt(sum(a * a for a in amps[1:])) / amps[0], c[0]
