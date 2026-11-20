#!/usr/bin/env python3
"""LP step 6, screening of the follower candidates (lp_rvt_lib.CAND): stage-2 OTA + follower + sink in an INVERTING gain -1 loop made of two IDEAL 100 MOhm resistors (screening scaffold only),
non-inverting input on the REAL vcm_out tap of bias_genc (1.65 V, as in the channel, so the pair's tail sits where it sits in the channel), DC sweep of the source: out = 2 vcm_out - Vx.
For every candidate and corner: the output range in which the stage still follows (|d out / d Vx| >= 0.99 and >= 0.9), the node o2 and the follower Vgs / Vth at out = 1.15 / 1.65 / 2.15 V,
the follower current.  The stage-2 loop of the channel has the same DC limits (o2 cannot go above VDD - Vdsat of the PMOS mirror nor below the pair's tail + Vdsat), so this finds the swing of a
candidate in seconds; the candidates that pass are then run in the full channel (lp_rvt_swing.py).
usage: python3 lp_rvt_screen.py [all | cand,cand,...] [VDD list, default 3.3] [suffix]     -> sim/lp_rvt_screen[_suffix].log + .json + _nglogs.tgz
"""
import sys
from lp_rvt_lib import *


# LP_RVT_VOCM=<V> (candidate E): the reference input of the stage is an IDEAL source of that value instead of the vcm_out tap (1.65 V) of bias_genc: what a LOWER output common mode would allow.
VOCM = float(os.environ.get('LP_RVT_VOCM', '0'))
REF = 'vcmx' if VOCM else 'vcmo'


def net(name, corner, temp, vdd, csv):
    L = ['* lp_rvt screen: ota2 (candidate %s) unity-gain buffer, DC sweep  (%s %g C, VDD %g V)' % (name, corner, temp, vdd),
         '.include %s/spice/models_%s.spice' % (AMP, corner)]
    L += ['.include %s/spice/%s.spice' % (AMP, f) for f in ('ota1_params', 'afe_params', 'a4c_params')]
    L += ['.include %s' % ota2_file(name), '.include %s/spice/bias_genc.spice' % AMP,
          '.options gmin=1e-16 abstol=1e-20 reltol=1e-4 itl1=500 itl4=500', '.temp %g' % temp,
          'Vdd vdd 0 %g' % vdd, 'Xbias vbn vcm vg1 vcmo vg2 vrs vdd 0 bias_genc', 'Vin inp 0 %g' % (VOCM if VOCM else vdd / 2),
          'R1 inp inn 100meg', 'R2 inn out 100meg', 'Xota %s inn vbn out vdd 0 ota2' % REF, 'Cl out 0 20f',
          '.nodeset v(vrs)=%g v(vbn)=0.65 v(xbias.a)=2.4 v(vcm)=1.65 v(vg1)=1.85 v(vcmo)=1.65 v(vg2)=2.55 v(out)=1.65 v(inn)=1.65 v(xota.d1)=2.6 v(xota.tail)=1.0' % NSVRS[(corner, temp)],
          ] + (['Vvocm vcmx 0 %g' % VOCM] if VOCM else []) + [
          '.control', 'set wr_singlescale', 'set wr_vecnames',
          'save v(out) v(inp) v(inn) v(vcmo) v(%s)' % REF + ' v(xota.o2) v(xota.tail) v(xota.d1) @m.xota.xmf.m0[id] @m.xota.xmf.m0[vgs] @m.xota.xmf.m0[vth] @m.xota.xmf.m0[gm] @m.xota.xmf.m0[vdsat] @m.xota.xmf.m0[vbs]',
          'dc Vin %g %g 0.005' % (0.1, vdd - 0.1),
          'wrdata %s v(out) v(xota.o2) v(xota.tail) v(%s) @m.xota.xmf.m0[id] @m.xota.xmf.m0[vgs] @m.xota.xmf.m0[vth] @m.xota.xmf.m0[gm] @m.xota.xmf.m0[vbs]' % (csv, REF),
          'echo DONE', 'quit', '.endc', '.end']
    return '\n'.join(L) + '\n'


def analyse(csv):
    names, a = load_csv(csv)
    vin, out, o2, tail, vcmo, idf, vgs, vth, gm, vbs = [a[:, i] for i in range(10)]
    o = np.argsort(out)                                    # out falls while Vx rises: sort by the output
    vin, out, o2, tail, vcmo, idf, vgs, vth, gm, vbs = [x[o] for x in (vin, out, o2, tail, vcmo, idf, vgs, vth, gm, vbs)]
    slope = -np.gradient(out, vin)
    mid = float(np.median(vcmo))
    i0 = int(np.argmin(np.abs(out - mid)))

    def rng(lim):
        lo = i0
        while lo > 0 and slope[lo - 1] >= lim:
            lo -= 1
        hi = i0
        while hi < len(vin) - 1 and slope[hi + 1] >= lim:
            hi += 1
        return out[lo], out[hi]
    r99, r90 = rng(0.99), rng(0.90)
    at = lambda v, y: float(np.interp(v, out, y)) if out[0] <= v <= out.max() else float('nan')
    pts = (mid - 0.5, mid, mid + 0.5)
    return dict(lo99=r99[0], hi99=r99[1], lo90=r90[0], hi90=r90[1], outmax=float(out.max()), outmin=float(out.min()), mid=mid, tail=at(mid, tail),
                o2=[at(v, o2) for v in pts], vgs=[at(v, vgs) for v in pts], vth=[at(v, vth) for v in pts],
                idf=at(mid, idf), gm=at(mid, gm), err=[(2 * mid - at(v, vin) - v) * 1e3 for v in pts])


if __name__ == '__main__':
    cands = sys.argv[1].split(',') if len(sys.argv) > 1 and sys.argv[1] != 'all' else ['orig', 'rvt'] + [c for c in CAND if c != 'orig']
    vdds = [float(x) for x in sys.argv[2].split(',')] if len(sys.argv) > 2 else [3.3]
    sfx = '' if len(sys.argv) < 4 else '_' + sys.argv[3]
    if os.environ.get('LP_RVT_PVT9'):          # all 9 PVT instead of typ 27 / ff 85 / ss -40
        CORNERS[:] = CORNERS9
    tag = 'screen' + sfx
    P = Log(os.path.join(SIM, 'lp_rvt_screen%s.log' % sfx))
    P(__doc__.split('usage')[0].strip())
    P('Columns: follow99 / follow90 = output range [V] around mid = vcm_out where |d out / d Vx| >= 0.99 / 0.90; tail = source node of the pair; o2, Vgs, Vth of the follower at out = mid - 0.5 /')
    P('         mid / mid + 0.5 V; Id, gm of the follower at mid (all fingers); err = ideal - actual output [mV] at those three outputs (finite loop gain).  Needed range: mid +- 0.5 V = 1.15 ..')
    P('         2.15 V at 3.3 V (Decision 17; +-0.5 mV x 1000); mid = VDD / 2 (ratiometric), so at another VDD the needed range moves with it.  nan = that output is not reached.')
    desc = lambda c: ('spice/ota2.spice as designed (nfet_06v0_nvt 10u/2u, bulk vss)' if c == 'orig' else 'spice/ota2_rvt.spice, the delivered variant (nfet_03v3 8 x 10u/1u, isolated p-well, bulk = source)' if c == 'rvt' else CAND[c][5])
    jobs = []
    for c in cands:
        for (k, T) in CORNERS:
            for v in vdds:
                n = 'scr_%s_%s_%g_%g' % (c, k, T, v)
                jobs.append((n, net(c, k, T, v, os.path.join(SCR, tag, n + '.csv'))))
    res = run_jobs(jobs, tag, log=lambda s: None)
    J = {}
    P('\n%-12s %-8s %4s %4s | %-13s %-13s | %5s | %-20s | %-20s | %-20s | %7s %7s | %-22s' % ('candidate', 'corner', 'T', 'VDD', 'follow99 [V]', 'follow90 [V]', 'tail', 'o2 @mid-.5/mid/mid+.5', 'Vgs @ same', 'Vth @ same', 'Id uA', 'gm uS', 'err mV @ same'))
    for c in cands:
        P('# %s: %s' % (c, desc(c)))
        for (k, T) in CORNERS:
            for v in vdds:
                n = 'scr_%s_%s_%g_%g' % (c, k, T, v)
                f = os.path.join(SCR, tag, n + '.csv')
                if not os.path.exists(f) or 'DONE' not in res[n]['out']:
                    P('%-12s %-8s %4g %4g | FAILED %s' % (c, k, T, v, res[n]['abort'][:200]))
                    continue
                r = analyse(f)
                f3 = lambda x: ' '.join('%6.3f' % y for y in x)
                need = (r['mid'] - 0.5, r['mid'] + 0.5)
                r['margin_bottom_mv'] = (need[0] - r['lo99']) * 1e3
                r['margin_top_mv'] = (r['hi99'] - need[1]) * 1e3
                r['pass'] = bool(r['lo99'] <= need[0] and r['hi99'] >= need[1])
                ok = ('PASS (margin bottom %.0f mV, top %.0f mV)' % (r['margin_bottom_mv'], r['margin_top_mv'])) if r['pass'] else ('FAIL top %.3f < %.3f' % (r['hi99'], need[1]) if r['hi99'] < need[1] else 'FAIL bottom %.3f > %.3f' % (r['lo99'], need[0]))
                J.setdefault(c, {}).setdefault('%g' % v, {})[CKEY[(k, T)]] = {kk: (vv if not isinstance(vv, float) or vv == vv else None) for kk, vv in r.items() if not isinstance(vv, list)}
                P('%-12s %-8s %4g %4g | %5.3f - %5.3f %5.3f - %5.3f | %5.3f | %-20s | %-20s | %-20s | %7.3f %7.1f | %-22s %s' % (
                    c, k, T, v, r['lo99'], r['hi99'], r['lo90'], r['hi90'], r['tail'], f3(r['o2']), f3(r['vgs']), f3(r['vth']), r['idf'] * 1e6, r['gm'] * 1e6, ' '.join('%6.2f' % y for y in r['err']), ok))
    json.dump(dict(desc={c: desc(c) for c in cands}, res=J), open(P.path.replace('.log', '.json'), 'w'), indent=1)
    keep_logs(res, P.path.replace('.log', '_nglogs.tgz'))
    P('\ncomplete ngspice outputs: %s' % os.path.basename(P.path.replace('.log', '_nglogs.tgz')))
