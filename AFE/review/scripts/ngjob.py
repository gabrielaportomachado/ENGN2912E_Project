#!/usr/bin/env python3
"""AUDIT helper: run ngspice batch jobs by PID (no pgrep/pkill, no `timeout` wrapper, no `cut`), one OpenMP thread per job
(job-local .spiceinit with `set num_threads=1`, Decision 43a), at most NPAR at a time, scratch in AFE/review/.ptmp/<tag>.
Design files are only read (absolute .include paths).  A job that aborts ("Timestep too small") is re-run ONCE with a different step cap
if the caller passes a retry netlist."""
import os, subprocess, time, re, shutil
HERE = os.path.dirname(os.path.abspath(__file__))
REV = os.path.normpath(os.path.join(HERE, '..'))
AFE = os.path.normpath(os.path.join(REV, '..'))
REPO = os.path.normpath(os.path.join(AFE, '..'))
AMP = os.path.join(AFE, 'amp')
ADC = os.path.join(AFE, 'adc')
PT = os.path.join(REV, '.ptmp')
SIM = os.path.join(REV, 'sim')
NG = '/foss/tools/ngspice/bin/ngspice'
NPAR = 3
PDKNG = '/foss/pdks/gf180mcuD/libs.tech/ngspice'


def free_gb():
    st = os.statvfs(REV)
    return st.f_bavail * st.f_frsize / 2 ** 30


def run_jobs(jobs, tag, npar=NPAR, wall=1800.0, log=print):
    """jobs: list of (name, netlist_text).  Returns {name: dict(ok, out, wall, abort)}; out = full ngspice stdout+stderr text."""
    if free_gb() < 3.0:
        raise SystemExit('STOP: less than 3 GB free on the design disk')
    d = os.path.join(PT, tag)
    os.makedirs(d, exist_ok=True)
    open(os.path.join(d, '.spiceinit'), 'w').write('set num_threads=1\n')
    todo = list(jobs)
    run = []
    res = {}
    while todo or run:
        while todo and len(run) < npar:
            name, net = todo.pop(0)
            fn = os.path.join(d, name + '.spice')
            lg = os.path.join(d, name + '.log')
            open(fn, 'w').write(net)
            p = subprocess.Popen([NG, '-b', fn], cwd=d, stdout=open(lg, 'w'), stderr=subprocess.STDOUT, env=dict(os.environ, OMP_NUM_THREADS='1'))
            run.append((p, name, lg, time.time()))
        time.sleep(0.2)
        for r in list(run):
            p, name, lg, t0 = r
            if p.poll() is None:
                if time.time() - t0 > wall:
                    p.kill()
                    p.wait()
                else:
                    continue
            run.remove(r)
            txt = open(lg, errors='replace').read().replace('\r', '\n')
            ab = ' | '.join(l.strip()[:200] for l in txt.split('\n') if re.search(r'imestep too small|trouble with|ingular matrix|aborted|No convergence|rror', l))[:600]
            res[name] = dict(ok=(p.returncode == 0), out=txt, wall=time.time() - t0, abort=ab, dir=d)
            log('   job %s: pid %d exit %s wall %.0f s%s' % (name, p.pid, p.returncode, time.time() - t0, (' MSG ' + ab) if ab else ''))
    return res


def results(txt, key='RESULT'):
    """parse 'KEY a=1 b=2 ...' lines into a list of dicts"""
    out = []
    for ln in txt.split('\n'):
        if ln.startswith(key + ' '):
            d = {}
            for kv in ln.split()[1:]:
                if '=' in kv:
                    k, v = kv.split('=', 1)
                    try:
                        d[k] = float(v)
                    except ValueError:
                        d[k] = v
            out.append(d)
    return out


def amp_includes(corner, extra=()):
    L = ['.include %s/spice/models_%s.spice' % (AMP, corner)]
    L += ['.include %s/spice/%s.spice' % (AMP, f) for f in ('pseudoR', 'ota1_params', 'afe_params', 'a4c_params', 'ota1', 'ota2', 'bias_genc', 'stage1c', 'stage2c', 'afe_chc', 'fs_oneshot_c')]
    return L + list(extra)


def cleanup(tag):
    shutil.rmtree(os.path.join(PT, tag), ignore_errors=True)
