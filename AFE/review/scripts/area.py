#!/usr/bin/env python3
"""AUDIT step 5: bottom-up area from the netlists (every size is evaluated from the SPICE parameters; nothing typed by hand).
Blocks: afe_chc (stage 1, stage 2, follower, muxes, park), fs_oneshot_c, bias_genc, dac_sw (+ dac_units), cmp_p, vhalf, vrefs, the 2 routing TGATEs, the digital macro
(LibreLane run AFE/adc/lg/runs/d3 + dbs_ctrl estimate), decap (Decision 40e), then per channel / per ADC / chip totals, MIM rule checks (25 um2 <= area <= 10,000 um2) and a floorplan.
LAYOUT MODEL (ESTIMATE, stated so every number can be redone):
  MOS footprint      = m * (W + 0.8 um) * (L + 1.0 um)        contacted source/drain 0.5 um per side, poly end caps 0.4 um per side (3.3 V devices; x1.2 for 5 V / 6 V devices)
  MIM footprint      = (side + 2 * 0.6 um bottom-plate overlap + 0.6 um spacing)^2 per piece  (MIMTM.3 / MIMTM.6, AFE/layout/PLAN.md section 1)
  HRES poly resistor = length * (width + 0.4 um spacing) * 1.2   (serpentine, HRES spacing 0.4 um, heads / contacts 20 %)
  block factor       = 1.5 for blocks of large analog devices (wells, guard ring, dummies, local wiring), 2.5 for blocks of small devices (comparator, switches, one-shot, muxes)
  top-level factor   = x1.30 on the sum of all blocks (channel-to-channel routing, the vcm / bias daisy chain, supply straps, pin access); the digital macro is taken as hardened.
usage: python3 area.py [out.log]"""
import re, os, sys, math, json
HERE = os.path.dirname(os.path.abspath(__file__))
REV = os.path.normpath(os.path.join(HERE, '..'))
AFE = os.path.normpath(os.path.join(REV, '..'))
REPO = os.path.normpath(os.path.join(AFE, '..'))
SUF = {'t': 1e12, 'g': 1e9, 'meg': 1e6, 'k': 1e3, 'm': 1e-3, 'u': 1e-6, 'n': 1e-9, 'p': 1e-12, 'f': 1e-15}
MOS = {'nfet_03v3': 1.0, 'pfet_03v3': 1.0, 'nfet_06v0_nvt': 1.2, 'nfet_05v0': 1.2, 'pfet_05v0': 1.2}
CAPK_A, CAPK_P = 1.99e-3, 2.383e-10          # F/m2, F/m (PDK cap_mim_2f0: sm141064_mim.ngspice)


def num(s):
    m = re.match(r'^([-+]?\d*\.?\d+(?:e[-+]?\d+)?)(meg|[tgkmunpf])?[a-z]*$', s.strip().lower())
    if not m:
        raise ValueError(s)
    return float(m.group(1)) * SUF.get(m.group(2), 1.0)


def ev(expr, env):
    e = expr.strip().strip("'{}")
    try:
        return num(e)
    except ValueError:
        pass
    e2 = re.sub(r'(?<![\w.])(\d*\.?\d+(?:e[-+]?\d+)?)(meg|[tgkmunpf])(?![\w.])', lambda m: repr(float(m.group(1)) * SUF[m.group(2)]), e, flags=re.I)
    names = {k: v for k, v in env.items()}
    names.update(sqrt=math.sqrt)
    return float(eval(re.sub(r'\b([A-Za-z_]\w*)\b', lambda m: m.group(1).lower(), e2), {'__builtins__': {}}, names))


def lines(path):
    out = []
    for ln in open(path).read().split('\n'):
        ln = ln.split('$')[0].rstrip()
        if ln.startswith('+') and out:
            out[-1] += ' ' + ln[1:]
        else:
            out.append(ln)
    return out


class Sub:
    def __init__(self, name, ports, defaults):
        self.name, self.ports, self.defaults, self.inst, self.prim = name, ports, defaults, [], []


def kv(tokens):
    d = {}
    for t in tokens:
        if '=' in t:
            k, v = t.split('=', 1)
            d[k.lower()] = v
    return d


def load(files, genv, cond):
    subs = {}
    for f in files:
        cur = None
        stack = []
        for ln in lines(os.path.join(REPO, f)):
            s = ln.strip()
            if not s or s.startswith('*'):
                continue
            low = s.lower()
            m = re.match(r'\.(if|elseif)\s*\(\s*(\w+)\s*==\s*(\d+)\s*\)', low)
            if m:
                v = cond.get(m.group(2), 0) == int(m.group(3))
                if m.group(1) == 'if':
                    stack.append([v, v])
                else:
                    stack[-1][0] = (not stack[-1][1]) and v
                    stack[-1][1] = stack[-1][1] or v
                continue
            if low.startswith('.else'):
                stack[-1][0] = not stack[-1][1]
                continue
            if low.startswith('.endif'):
                stack.pop()
                continue
            if stack and not all(x[0] for x in stack):
                continue
            if low.startswith('.param'):
                for k, v in kv(re.sub(r"\s*=\s*", '=', s[6:]).replace("' ", "'|").split() if "'" not in s else [re.sub(r'\s+', '', x) for x in re.findall(r"\w+\s*=\s*'[^']*'|\w+\s*=\s*\S+", s[6:])]).items():
                    try:
                        (genv if cur is None else cur.defaults)[k] = ev(v, genv)
                    except Exception as ex:
                        print('param', k, v, ex, file=sys.stderr)
                continue
            if low.startswith('.subckt'):
                tk = s.split()
                ports = []
                rest = []
                for i, t in enumerate(tk[2:]):
                    if '=' in t or t.lower() == 'params:':
                        rest = tk[2 + i:]
                        break
                    ports.append(t.lower())
                cur = Sub(tk[1].lower(), ports, {})
                for k, v in kv(rest).items():
                    cur.defaults[k] = v
                subs[cur.name] = cur
                continue
            if low.startswith('.ends'):
                cur = None
                continue
            if cur is None or low.startswith('.'):
                continue
            tk = s.split()
            if tk[0][0].lower() == 'x':
                nodes = [t for t in tk[1:] if '=' not in t]
                cur.inst.append((tk[0].lower(), nodes[-1].lower(), kv(tk[1:])))
            else:
                cur.prim.append((tk[0], ' '.join(tk[1:])))
    return subs


def flat(subs, name, env, genv, path='', out=None):
    """list of (path, model, params{w,l,m ...} evaluated)"""
    if out is None:
        out = []
    sub = subs[name]
    loc = dict(genv)
    for k, v in sub.defaults.items():
        loc[k] = ev(v, loc) if isinstance(v, str) else v
    loc.update(env)
    for iname, model, p in sub.inst:
        pe = {}
        for k, v in p.items():
            try:
                pe[k] = ev(v, loc)
            except Exception:
                pe[k] = None
        if model in subs:
            flat(subs, model, pe, genv, path + iname + '.', out)
        else:
            out.append((path + iname, model, pe))
    for nm, rest in sub.prim:
        out.append((path + nm.lower(), 'IDEAL', {'text': rest}))
    return out


def mim_c(w, l):
    return CAPK_A * w * l + CAPK_P * 2 * (w + l)


def block(devs, P, title, bf_big=1.5, bf_small=2.5, pieces=None):
    """returns dict with gate area, MOS footprint, MIM drawn / footprint, resistor area, estimate; prints the device table"""
    g = mos_fp = mim_d = mim_fp = res_a = 0.0
    viol = []
    nm = 0
    small = big = 0.0
    P('  -- %s' % title)
    agg = {}
    for path, model, p in devs:
        if model in MOS:
            w, l, m = p.get('w') * 1e6, p.get('l') * 1e6, (p.get('m') or 1)
            ga = w * l * m
            fp = m * (w + 0.8) * (l + 1.0) * MOS[model]
            g += ga
            mos_fp += fp
            if l >= 1.0 and w >= 5.0:
                big += fp
            else:
                small += fp
            k = (model, round(w, 3), round(l, 3))
            agg.setdefault(k, [0, 0.0, 0.0])
            agg[k][0] += m
            agg[k][1] += ga
            agg[k][2] += fp
        elif model.startswith('cap_mim'):
            w, l = p['c_width'] * 1e6, p['c_length'] * 1e6
            a = w * l
            npc = 1
            if a > 10000.0:
                npc = (pieces or {}).get(path.split('.')[-1], 2)
                viol.append('%s %.1f x %.1f um = %.0f um2 > 10,000 (MIMTM.8b): %d pieces assumed' % (path, w, l, a, npc))
            if a < 25.0:
                viol.append('%s %.2f x %.2f um = %.1f um2 < 25 (MIMTM.8a)' % (path, w, l, a))
            side = math.sqrt(a / npc)
            fp = npc * (side + 1.8) ** 2
            mim_d += a
            mim_fp += fp
            nm += 1
            k = ('MIM', round(w, 2), round(l, 2))
            agg.setdefault(k, [0, 0.0, 0.0])
            agg[k][0] += 1
            agg[k][1] += a
            agg[k][2] += fp
        elif model.startswith('ppolyf'):
            w, l = p['r_width'] * 1e6, p['r_length'] * 1e6
            a = l * (w + 0.4) * 1.2
            res_a += a
            k = (model, round(w, 2), round(l, 1))
            agg.setdefault(k, [0, 0.0, 0.0])
            agg[k][0] += 1
            agg[k][1] += l * w
            agg[k][2] += a
    for k in sorted(agg, key=lambda x: -agg[x][2])[:14]:
        n, a, fp = agg[k]
        if k[0] == 'MIM':
            P('     %-26s %4d x  %7.2f x %7.2f um   drawn %9.0f um2  C %8.3f pF  footprint %9.0f' % ('cap_mim_2f0 (W x L)', n, k[1], k[2], a, n * mim_c(k[1] * 1e-6, k[2] * 1e-6) * 1e12, fp))
        elif k[0].startswith('ppolyf'):
            P('     %-26s %4d x  W %5.2f L %8.1f um   drawn %9.0f um2                 footprint %9.0f' % (k[0], n, k[1], k[2], a, fp))
        else:
            P('     %-26s m %4d  W %6.2f L %6.2f um   gate  %9.1f um2                 footprint %9.0f' % (k[0], n, k[1], k[2], a, fp))
    if len(agg) > 14:
        P('     ... %d more device groups' % (len(agg) - 14))
    est = big * bf_big + small * bf_small + mim_fp + res_a
    P('     gate area %.0f um2, MOS footprint %.0f (large %.0f x%.1f, small %.0f x%.1f), MIM drawn %.0f / footprint %.0f (%d caps), poly R %.0f  ->  ESTIMATE %.0f um2' % (g, mos_fp, big, bf_big, small, bf_small, mim_d, mim_fp, nm, res_a, est))
    for v in viol:
        P('     MIM RULE: ' + v)
    return dict(gate=g, mos=mos_fp, mimd=mim_d, mimfp=mim_fp, res=res_a, est=est, viol=viol)


if __name__ == '__main__':
    out = open(sys.argv[1], 'w') if len(sys.argv) > 1 else sys.stdout
    P = lambda *a: print(*a, file=out)
    P(__doc__.split('usage')[0].strip())
    genv = {}
    files = ['AFE/amp/spice/afe_params.spice', 'AFE/amp/spice/a4c_params.spice', 'AFE/amp/spice/ota1_params.spice', 'AFE/adc/spice/comparator_params.spice',
             'AFE/amp/spice/pseudoR.spice', 'AFE/amp/spice/ota1.spice', 'AFE/amp/spice/ota2.spice', 'AFE/amp/spice/bias_genc.spice', 'AFE/amp/spice/stage1c.spice', 'AFE/amp/spice/stage2c.spice',
             'AFE/amp/spice/afe_chc.spice', 'AFE/amp/spice/fs_oneshot_c.spice', 'AFE/adc/spice/dac_units.spice', 'AFE/adc/spice/dac_sw.spice', 'AFE/adc/spice/comparator.spice', 'AFE/adc/spice/vhalf.spice',
             'TGATE/TGATE.spice']
    subs = load(files, genv, {'looptest': 0, 'rmode': 0, 'rmode2': 0})
    P('\n1. BLOCKS (device groups sorted by footprint; sizes evaluated from the netlist parameters)')
    B = {}
    B['afe_chc'] = block(flat(subs, 'afe_chc', {}, genv), P, 'afe_chc = stage 1 (OTA1, Cin x2, Cf x2, pseudo-R) + stage 2 (OTA2, follower) + gate muxes + REC park', pieces={'xcin1': 2, 'xcin2': 2})
    B['oneshot'] = block(flat(subs, 'fs_oneshot_c', {}, genv), P, 'fs_oneshot_c (C_T 4 pF)')
    B['bias'] = block(flat(subs, 'bias_genc', {}, genv), P, 'bias_genc (one per chip; ladders are ppolyf_u_3k as frozen)')
    B['dac'] = block(flat(subs, 'dac_sw', {}, genv), P, 'dac_sw = 128 MIM units + bridge + 13 drivers + 13 sampling TGs + 2 reset switches')
    B['cmp'] = block(flat(subs, 'cmp_p', {}, genv), P, 'cmp_p (the two 40 fF preamp capacitors are IDEAL in the netlist: not counted; one legal 5x5 um MIM each would add 2 x 46 um2)')
    B['vhalf'] = block(flat(subs, 'vhalf', {}, genv), P, 'vhalf (2 x 250 kOhm ppolyf_u_3k + 1 pF)')
    B['vrefs'] = block(flat(subs, 'vrefs', {}, genv), P, 'vrefs (TG + Cref 7 pF: ONE MIM in the netlist; Decision 42 / L1a say 128 x 5x5 um units)')
    # unit-array view of the DAC and of Cref (5 x 5 um units on a 6.8 um pitch = 5 + 2 x 0.6 overlap + 0.6 space, one dummy ring)
    pitch = 6.8
    dac_arr = (12 + 2) * (11 + 2) * pitch ** 2        # 129 units + dummy -> 12 x 11 sites + ring
    cref_units = 128 * pitch ** 2
    P('  -- unit-array view: DAC 129 units as 12 x 11 sites + one dummy ring on a %.1f um pitch = %.0f um2 (the per-piece footprint above gives %.0f); Cref as 128 units %.0f um2 vs one plate %.0f um2' % (pitch, dac_arr, B['dac']['mimfp'], cref_units, B['vrefs']['mimfp']))
    tg = re.search(r'SIZE ([\d.]+) BY ([\d.]+)', open(os.path.join(REPO, 'TGATE/TGATE.lef')).read())
    tga = float(tg.group(1)) * float(tg.group(2))
    P('  -- TGATE macro (TGATE/TGATE.lef SIZE): %.2f x %.2f um = %.1f um2 each, 2 per channel (std-cell row height: needs VDD / VSS rails and well taps: x3 assumed) = %.0f um2 per channel' % (float(tg.group(1)), float(tg.group(2)), tga, 2 * tga * 3))
    # HRES what-if
    for var, fac in (('ppolyf_u_1k, same resistance (3x the squares)', 3.0), ('ppolyf_u_1k, same squares (R / 3)', 1.0)):
        P('  -- HRES option of gf180mcuD (%s): bias ladders %.0f um2, vhalf pair %.0f um2 per ADC' % (var, sum(1 for _ in [0]) * (B['bias']['res'] - 120 * 2.4 * 1.2) * fac + 120 * 2.4 * 1.2, B['vhalf']['res'] * fac))

    P('\n2. DIGITAL MACRO (LibreLane run AFE/adc/lg/runs/d3/final/metrics.json = adc8_top only, I1 RTL, no CTS)')
    m = json.load(open(os.path.join(AFE, 'adc', 'lg', 'runs', 'd3', 'final', 'metrics.json')))
    bb = [float(x) for x in str(m['design__die__bbox']).split()]
    P('     die %.2f x %.2f um = %.0f um2, core %.0f um2, std cells %.0f um2 (%d cells), utilization %.1f %%, sequential %.0f um2 (%d flops)' % (bb[2], bb[3], m['design__die__area'], m['design__core__area'], m['design__instance__area__stdcell'], m['design__instance__count__stdcell'], 100 * m['design__instance__utilization'], m['design__instance__area__class:sequential_cell'], m['design__instance__count__class:sequential_cell']))
    flop = m['design__instance__area__class:sequential_cell'] / m['design__instance__count__class:sequential_cell']
    dbs = 18 * flop + 16 * 2 * 12.0 + 6 * 12.0
    P('     dbs_ctrl (not hardened yet; ESTIMATE): 18 flops x %.1f um2 + 32 NAND3 / INV + FSM gates = %.0f um2 of std cells' % (flop, dbs))
    dig_std = m['design__instance__area__stdcell'] + dbs
    for u in (0.39, 0.50, 0.60):
        P('     afe_dig at %2.0f %% utilization: %.0f um2 (%.0f x %.0f um square)' % (100 * u, dig_std / u, math.sqrt(dig_std / u), math.sqrt(dig_std / u)))
    dig = dig_std / 0.45

    P('\n3. DECAP (Decision 40e / 43f: 0.125 nF main rail + 0.1 nF DAC strap = 0.225 nF; MOS cap density from the PDK model cap_nmos_03v3: 3.98 fF/um2 at 3.3 V)')
    dec_mos = 0.225e-9 / 3.98e-15 * 1.25
    dec_mim = 0.225e-9 / 2.0e-15 * 1.15
    P('     as MOS capacitors: %.0f um2 drawn x1.25 = %.0f um2 (D2 assumed 4.6 fF/um2: 0.049 mm2); as MIM 2 fF/um2: %.0f um2.  Under the Cin MIM plates (8 x 2 x 10,000 um2 available) it costs no area.' % (0.225e-9 / 3.98e-15, dec_mos, dec_mim))

    P('\n4. TOTALS')
    amp = B['afe_chc']['est'] + B['oneshot']['est'] + 2 * tga * 3 + 2 * 60.0
    adc = B['dac']['est'] - B['dac']['mimfp'] + dac_arr + B['cmp']['est'] + 2 * 46.2 + B['vhalf']['est'] + B['vrefs']['est']
    P('     amplifier part of a channel (afe_chc + one-shot + 2 TGATE + OR2 / INV): %.0f um2   [gate %.0f, MIM drawn %.0f]' % (amp, B['afe_chc']['gate'] + B['oneshot']['gate'], B['afe_chc']['mimd'] + B['oneshot']['mimd']))
    P('     ADC analog part of a channel (dac_sw with the unit array + cmp_p + vhalf + vrefs): %.0f um2   [MIM drawn %.0f]' % (adc, B['dac']['mimd'] + B['vhalf']['mimd'] + B['vrefs']['mimd']))
    chn = amp + adc
    P('     one channel cell afe_ch: %.0f um2 (e.g. %.0f x %.0f um)' % (chn, math.sqrt(chn / 1.6), 1.6 * math.sqrt(chn / 1.6)))
    blocks = 8 * chn + B['bias']['est'] + dig + dec_mos
    P('     chip blocks: 8 channels %.0f + bias %.0f + digital macro at 45 %% %.0f + decap (MOS, not under MIM) %.0f = %.0f um2 = %.3f mm2' % (8 * chn, B['bias']['est'], dig, dec_mos, blocks, blocks / 1e6))
    for tf, lab in ((1.30, 'x1.30 top-level factor (planning value)'), (1.50, 'x1.50 (pessimistic: first-time generated layout)')):
        tot = (blocks - dig) * tf + dig
        for slot, sl in ((1110.0 ** 2, '1110 x 1110 um slot (ASSUMED, TAPEOUT.md)'), (2040.0 ** 2 / 3, 'one third of the 2040 x 2040 um area (organizer Integration README)'), (2235.0 ** 2 / 3, 'one third of 2235 x 2235 um (TAPEOUT.md planning frame)')):
            P('     %-50s total %.3f mm2 = %4.0f x %4.0f um | %-66s %.3f mm2 -> utilization %3.0f %%, margin %3.0f %%' % (lab, tot / 1e6, math.sqrt(tot), math.sqrt(tot), sl, slot / 1e6, 100 * tot / slot, 100 * (1 - tot / slot)))
    P('     decap under the Cin MIM instead: blocks %.3f mm2 -> x1.30 total %.3f mm2' % ((blocks - dec_mos) / 1e6, ((blocks - dec_mos - dig) * 1.3 + dig) / 1e6))
    P('     8 amplifier parts %.3f mm2 (earlier estimate 0.40-0.45 mm2), 8 ADC analog parts %.3f mm2 + digital %.3f mm2 = %.3f mm2 (earlier 0.08-0.12 mm2 / D0b 0.136 mm2), block total earlier 0.8-1.0 mm2' % (8 * amp / 1e6, 8 * adc / 1e6, dig / 1e6, (8 * adc + dig) / 1e6))
    P('\n5. LEVERS if the slot is smaller (area saved, from the numbers above)')
    cin = 2 * (math.sqrt(10002.4 / 2) + 1.8) ** 2 * 2
    P('     decap under the Cin MIM: -%.3f mm2 (x1.3: -%.3f)' % (dec_mos / 1e6, 1.3 * dec_mos / 1e6))
    P('     Cin 20 -> 10 pF (noise +: kT/C and OTA noise gain; gain ratio kept with Cf 100 fF): -%.3f mm2 for 8 channels' % (8 * cin / 2 / 1e6))
    P('     Cref as ONE plate (netlist) instead of 128 units (Decision text): -%.3f mm2 for 8' % (8 * (cref_units - B['vrefs']['mimfp']) / 1e6))
    P('     N = 4 channels: -%.3f mm2 of blocks' % (4 * chn / 1e6))
    P('     11-bit DAC (6+5): -32 units per ADC: -%.3f mm2 for 8 (not worth it)' % (8 * 32 * pitch ** 2 / 1e6))
    if out is not sys.stdout:
        out.close()
