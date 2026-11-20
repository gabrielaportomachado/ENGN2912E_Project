#!/usr/bin/env python3
"""mk_lvs_netlists.py (F1, Decision 44e): writes the LVS REFERENCE netlists from the SIMULATION netlists.  The simulation netlists are only read; never edit them for LVS.

Sources (read only)
  SPICE   AFE/amp/spice/{ota1_params,afe_params,a4c_params,pseudoR,ota1,ota2,bias_genc,stage1c,stage2c,afe_chc,fs_oneshot_c}.spice
          AFE/adc/spice/{dac_units,dac_sw,comparator_params,comparator,vhalf}.spice,  TGATE/TGATE.spice,
          the two standard cells used by hand in afe_ch (PDK gf180mcu_fd_sc_mcu7t5v0.spice: or2_1, inv_1)
  Verilog AFE/top/dbs_afe_top.v (modules dbs_afe_top and afe_ch: every connection of the LVS top and of the channel cell is taken from this file, nothing is typed twice)

Rules = AFE/review/AUDIT.md 4.9.3 (P-A5), the table RULES below.  The script STOPS if a rule does not find exactly the elements it expects, if an ideal R / C / V / I / B / E element is left,
or if a device is not in the list of gf180mcuD LVS devices.
  1. cap_mim_2f0_m2m3_noshield -> cap_mim_2f0_m4m5_noshield (same model parameters; MIM option B of the 5-metal stack).  Terminal order is kept: 1 = top plate, 2 = bottom plate
     (Magic: `device csubcircuit cap_mim_2f0_m4m5_noshield *mimcap *m4`; the netgen setup does NOT permute MIM terminals).
  2. Rbrk removed, its two nets joined (stage1c: vng = vn; stage2c: vng2 = vn2).  Rt, Rmm (fs_oneshot_c) and Cpm, Cpb0-11, Cpbd (dac_sw) removed.
  3. Cxa1, Cxa2 of cmp_p (ideal 40 fF) -> one 5 x 5 um MIM unit each (54.5 fF; 40 fF is below the 25 um2 minimum).
  4. Cin (stage1c Xcin1, Xcin2; one 100.01 um plate = 10,002 um2 > the 10,000 um2 limit) -> N pieces (default 2 squares sized for C/N each, so the capacitance and the ratio Cin : Cf1 = 100
     stay as simulated).  --cin N,W,L sets what the layout draws.
  5. Cref (vrefs) stays ONE plate (59.07 um, P-A10).   6. Resistors: ppolyf_u_1k as in the netlists (F1 item 1); ppolyf_u_3k is refused.
  7. Top: SPICE top = 8 x afe_ch + bias_genc + the supply devices (strap resistor, MOS decap) + the digital macro afe_dig as a BLACK BOX.  The 15 constant pad-control pins of the top
     (`assign X = 1'b0 / 1'b1` in AFE/top/dbs_afe_top.v) are OUTPUT PINS of afe_dig, driven there by tie cells (Decision 46e, LP step 5; AFE/dig/afe_dig.v, whose tie values are
     checked against the Verilog top here): each such top pin is simply a net between the pad and the macro pin of the same name.  `--ties resistor` writes the F1 form instead
     (a 0-ohm resistor from the pin to VDD / VSS and no tie pins on afe_dig).
  8. Routing TGATE: TGATE/TGATE.spice with VDD / VSS on the analog strap; the two standard cells get VDD / VNW on the analog strap and VSS / VPW on vss.
Every device parameter is evaluated to a number (netgen does not evaluate ngspice .param expressions); the simulation-only instance parameters (ad as pd ps nrd nrs sa sb sd, nf = 1) are dropped.
Analog cells are written FLAT (one .subckt per cell, device names = the hierarchical simulation names with `_` for `.`), so the reference does not depend on the layout hierarchy:
netgen flattens layout sub-cells that have no namesake.

Output (default AFE/layout/lvs/), one file per cell, each self-contained:
  afe_chc.spice      afe_chc, fs_oneshot_c, the OR2 standard cell, and amp_ch = afe_chc + fs_oneshot_c + OR2 (the amplifier part of a channel, L2)
  adc_ch.spice       dac_sw, cmp_p, vhalf, vrefs, the INV standard cell, and adc_ch = the ADC analog part of a channel (L1)
  bias_genc.spice    bias_genc (L3)
  dbs_afe_top.spice  everything above + TGATE + afe_ch + dbs_afe_top (L3); afe_dig is a black box (an empty .subckt with the L1d pin list, or the port order of --dig-netlist)
  mk_lvs_netlists.log   what was removed / replaced, device census, MIM and resistor tables, pin lists

usage: python3 mk_lvs_netlists.py [--out DIR] [--cin N[,W_um,L_um]] [--cin-top sum|rec] [--decap W_um,L_um] [--decap-n NMAIN,NDAC] [--rstrap MODEL,W_um,L_um]
                                  [--ties dig|resistor] [--dig-netlist afe_dig.pnl.v]
  --decap-n NMAIN,NDAC   explicit numbers of decap units on the ADC-main strap (net VDD) and on the ADC-DAC strap (net vdd_dac), e.g. 80,64 for 8 x 10 and 8 x 8 units under the Cin
                         plates (Decision 46c).  Default: the smallest number of units that reaches the capacitance asked in the Verilog top (0.125 nF / 0.1 nF).
  --dig-netlist FILE     powered gate-level netlist of afe_dig (LP trial: AFE/dig/trial/afe_dig.pnl.v; L1d: the final one): the black-box instance follows ITS port order.
"""
import os, re, sys, math, argparse

HERE = os.path.dirname(os.path.abspath(__file__))
LAY = os.path.normpath(os.path.join(HERE, '..'))
AFE = os.path.normpath(os.path.join(LAY, '..'))
REPO = os.path.normpath(os.path.join(AFE, '..'))
PDK_STD = '/foss/pdks/gf180mcuD/libs.ref/gf180mcu_fd_sc_mcu7t5v0/spice/gf180mcu_fd_sc_mcu7t5v0.spice'
SIM_FILES = ['AFE/amp/spice/ota1_params.spice', 'AFE/amp/spice/afe_params.spice', 'AFE/amp/spice/a4c_params.spice', 'AFE/amp/spice/pseudoR.spice', 'AFE/amp/spice/ota1.spice',
             'AFE/amp/spice/ota2.spice', 'AFE/amp/spice/bias_genc.spice', 'AFE/amp/spice/stage1c.spice', 'AFE/amp/spice/stage2c.spice', 'AFE/amp/spice/afe_chc.spice',
             'AFE/amp/spice/fs_oneshot_c.spice', 'AFE/adc/spice/dac_units.spice', 'AFE/adc/spice/dac_sw.spice', 'AFE/adc/spice/comparator_params.spice', 'AFE/adc/spice/comparator.spice',
             'AFE/adc/spice/vhalf.spice', 'TGATE/TGATE.spice']
TOP_V = 'AFE/top/dbs_afe_top.v'

MIM_SIM, MIM_LVS = 'cap_mim_2f0_m2m3_noshield', 'cap_mim_2f0_m4m5_noshield'
MOS = ('nfet_03v3', 'pfet_03v3', 'nfet_06v0_nvt', 'nfet_05v0', 'pfet_05v0')
RES3 = ('ppolyf_u_1k', 'ppolyf_s', 'ppolyf_u', 'npolyf_s', 'npolyf_u')            # 3-terminal resistors (a b substrate)
RES2 = ('rm1', 'rm2', 'rm3', 'rm4')                                              # 2-terminal metal resistors
MOSCAP = ('cap_nmos_03v3',)
LVS_DEVICES = MOS + (MIM_LVS, 'ppolyf_u_1k') + MOSCAP + RES2 + ('ppolyf_s', 'ppolyf_u', 'npolyf_s', 'npolyf_u')
RSH = {'rm1': 0.09, 'rm2': 0.09, 'rm3': 0.09, 'rm4': 0.09, 'ppolyf_s': 7.3, 'npolyf_s': 6.8, 'ppolyf_u': 350.0, 'npolyf_u': 310.0, 'ppolyf_u_1k': 1000.0}   # typical ohm/sq (sm141064.ngspice)
MOSCAP_FF_UM2 = 3.983          # cap_nmos_03v3 at 3.3 V: (cvar1 + cvar2) = 0.002003 + 0.00198 F/m2 (sm141064.ngspice, .LIB moscap)

# ---- the rules of AUDIT 4.9.3 on single elements: (cell, action, element-name regex, number of elements that must match)
RULES = [
    ('stage1c',      'short',    r'rbrk',             1),     # remove, join its two nets (vng -> vn)
    ('stage2c',      'short',    r'rbrk',             1),     # remove, join its two nets (vng2 -> vn2)
    ('fs_oneshot_c', 'drop',     r'rt|rmm',           2),     # 10 TOhm numerical keepers
    ('dac_sw',       'drop',     r'cpm|cpb\d+|cpbd',  14),    # ASSUMED 2 fF wiring parasitics
    ('cmp_p',        'mim_unit', r'cxa[12]',          2),     # ideal 40 fF -> one 5 x 5 um MIM unit
    ('stage1c',      'cin',      r'xcin[12]',         2),     # one 10,002 um2 plate -> N pieces
]
# ---- which afe_ch instance belongs to which layout cell (everything else of afe_ch stays in afe_ch itself: the two routing TGATEs)
GROUPS = {'amp_ch': ['u_os', 'u_or', 'u_amp'], 'adc_ch': ['u_vh', 'u_samb', 'u_dac', 'u_vr', 'u_cmp']}
GROUP_PIN_NAME = {('amp_ch', 'amp_out'): 'out', ('adc_ch', 'amp_out'): 'vin'}      # the net amp_out of afe_ch is called out (= afe_chc.out) / vin (= dac_sw.vin) at the pins of the two cells
SUPPLY_NETS = ('vdd', 'vdd_cmp', 'vdd_dac', 'vss')
# ---- power pins that the Verilog instances do not connect (AUDIT 4.9.3 rule 8): SPICE pin -> net of afe_ch
IMPLICIT_POWER = {'tgate': {'vdd': 'vdd', 'vss': 'vss'},
                  'gf180mcu_fd_sc_mcu7t5v0__or2_1': {'vdd': 'vdd', 'vnw': 'vdd', 'vpw': 'vss', 'vss': 'vss'},
                  'gf180mcu_fd_sc_mcu7t5v0__inv_1': {'vdd': 'vdd', 'vnw': 'vdd', 'vpw': 'vss', 'vss': 'vss'}}
# ---- the digital macro afe_dig (AFE/prompts/layout_run.md L1d): macro pin <- (instance of dbs_afe_top, its port).  mode_o / en_o stay inside the macro, ready is tied high inside.
DIG_PINS = [('CS', 'u_adc', 'cs_n'), ('SCLK', 'u_adc', 'sclk'), ('DIN', 'u_adc', 'din'), ('RSTN', 'u_adc', 'rstn'), ('DOUT', 'u_adc', 'dout'), ('DOUT_OE', 'u_adc', 'dout_oe'),
            ('rst_amp_o', 'u_adc', 'rst_amp_o'), ('sw_rec', 'u_dbs', 'sw_rec'), ('sw_rec_b', 'u_dbs', 'sw_rec_b'), ('sw_ipg', 'u_dbs', 'sw_ipg'), ('sw_ipg_b', 'u_dbs', 'sw_ipg_b'),
            ('cmp_q', 'u_adc', 'cmp_q'), ('cmp_clk', 'u_adc', 'cmp_clk'), ('rst_sw', 'u_adc', 'rst_sw'), ('tg_on', 'u_adc', 'tg_on'), ('dac_gp', 'u_adc', 'dac_gp'),
            ('dac_gn', 'u_adc', 'dac_gn'), ('dac_gdn', 'u_adc', 'dac_gdn')]
DIG_POWER = [('VDD', 'VDD'), ('VSS', 'VSS')]            # macro power pin -> net of the top (the macro sits on the ADC-main strap = net VDD)
DIG_INTERNAL = [('u_dbs', 'clk', 'u_adc', 'sclk'), ('u_dbs', 'rstn', 'u_adc', 'rstn'), ('u_dbs', 'mode', 'u_adc', 'mode_o'), ('u_dbs', 'en', 'u_adc', 'en_o')]   # nets that must be common

LOG = []


def P(*a):
    LOG.append(' '.join(str(x) for x in a))


def die(msg):
    sys.exit('mk_lvs_netlists: STOP: ' + msg)


# =========================================================================================== SPICE reader
SUF = {'t': 1e12, 'g': 1e9, 'meg': 1e6, 'k': 1e3, 'm': 1e-3, 'u': 1e-6, 'n': 1e-9, 'p': 1e-12, 'f': 1e-15}
_NUM = re.compile(r'^([-+]?(?:\d+\.?\d*|\.\d+)(?:e[-+]?\d+)?)(meg|[tgkmunpf])?[a-z]*$', re.I)


def num(s):
    m = _NUM.match(s.strip())
    if not m:
        raise ValueError(s)
    return float(m.group(1)) * SUF.get((m.group(2) or '').lower(), 1.0)


def ev(expr, env):
    """value of an ngspice parameter expression ('...', {...} or plain) with the parameters of env (lower-case names)"""
    e = expr.strip()
    if e and e[0] in "'{":
        e = e[1:-1]
    try:
        return num(e)
    except ValueError:
        pass
    e = re.sub(r'(?<![\w.])((?:\d+\.?\d*|\.\d+)(?:e[-+]?\d+)?)(meg|[tgkmunpf])(?![\w.])', lambda m: repr(float(m.group(1)) * SUF[m.group(2).lower()]), e, flags=re.I)
    e = re.sub(r'[A-Za-z_]\w*', lambda m: m.group(0).lower(), e)
    try:
        return float(eval(e, {'__builtins__': {}}, dict(env, sqrt=math.sqrt, int=int, abs=abs, min=min, max=max)))
    except Exception as ex:
        raise ValueError('cannot evaluate %r: %s' % (expr, ex))


def logical_lines(path):
    out = []
    for raw in open(path).read().split('\n'):
        ln = raw.split('$')[0].rstrip()
        if ln.startswith('+') and out:
            out[-1] += ' ' + ln[1:]
        else:
            out.append(ln)
    return out


def toks(s):
    """split on blanks outside '...' and {...}; `a = b` is glued to a=b"""
    out, cur, q, depth = [], '', None, 0
    for ch in s:
        if q:
            cur += ch
            if ch == q:
                q = None
        elif ch == "'":
            q = ch
            cur += ch
        elif ch == '{':
            depth += 1
            cur += ch
        elif ch == '}':
            depth -= 1
            cur += ch
        elif ch.isspace() and depth == 0:
            if cur:
                out.append(cur)
                cur = ''
        else:
            cur += ch
    if cur:
        out.append(cur)
    glued = []
    i = 0
    while i < len(out):
        t = out[i]
        if t == '=' and glued and i + 1 < len(out):
            glued[-1] += '=' + out[i + 1]
            i += 2
            continue
        if t.endswith('=') and i + 1 < len(out):
            glued.append(t + out[i + 1])
            i += 2
            continue
        if t.startswith('=') and glued:
            glued[-1] += t
            i += 1
            continue
        glued.append(t)
        i += 1
    return glued


class Elem:
    def __init__(self, name, nodes, model, params, kind):
        self.name, self.nodes, self.model, self.params, self.kind = name, nodes, model, params, kind      # kind 'x' = subckt / PDK device instance, else the SPICE letter of an ideal element

    def copy(self):
        return Elem(self.name, list(self.nodes), self.model, dict(self.params), self.kind)


class Sub:
    def __init__(self, name, ports, defaults, file):
        self.name, self.ports, self.defaults, self.file, self.elems = name, ports, defaults, file, []


def read_spice(files):
    """-> (subckts {lower name: Sub}, global parameters {lower name: value}).  .if / .elseif / .else are resolved with the parameter values of the files (LOOPTEST = 0, RMODE = 0, RMODE2 = 0)."""
    subs, genv = {}, {}
    for f in files:
        cur, stack = None, []
        for ln in logical_lines(os.path.join(REPO, f)):
            s = ln.strip()
            if not s or s.startswith('*'):
                continue
            low = s.lower()
            m = re.match(r'\.(if|elseif)\s*\(\s*(\w+)\s*==\s*([-\d.e]+)\s*\)', low)
            if m:
                if m.group(2) not in genv:
                    die('%s: condition on the unknown parameter %s' % (f, m.group(2)))
                v = abs(genv[m.group(2)] - float(m.group(3))) < 1e-12
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
            tk = toks(s)
            if low.startswith('.param'):
                if cur is not None:
                    die('%s: .param inside .subckt %s is not supported' % (f, cur.name))
                for t in tk[1:]:
                    if '=' not in t:
                        die('%s: cannot read %r' % (f, s))
                    k, v = t.split('=', 1)
                    genv[k.lower()] = ev(v, genv)
                continue
            if low.startswith('.subckt'):
                ports, defaults = [], {}
                for t in tk[2:]:
                    if t.lower() == 'params:':
                        continue
                    if '=' in t:
                        k, v = t.split('=', 1)
                        defaults[k.lower()] = v
                    else:
                        ports.append(t)
                cur = Sub(tk[1], ports, defaults, f)
                subs[cur.name.lower()] = cur
                continue
            if low.startswith('.ends'):
                cur = None
                continue
            if low.startswith('.') or cur is None:
                continue
            c = tk[0][0].lower()
            if c == 'x':
                nodes = []
                params = {}
                for t in tk[1:]:
                    if '=' in t:
                        k, v = t.split('=', 1)
                        params[k.lower()] = v
                    elif params:
                        die('%s: node after a parameter in %r' % (f, s))
                    else:
                        nodes.append(t)
                cur.elems.append(Elem(tk[0], nodes[:-1], nodes[-1], params, 'x'))
            else:
                cur.elems.append(Elem(tk[0], tk[1:3], None, {'value': ' '.join(tk[3:])}, c))
    return subs, genv


# =========================================================================================== rules + flattening
def mim_c(w, l, genv):
    """PDK cap_mim_2f0 formula with the constants the netlists use (afe_params.spice): C = A W L + P 2 (W + L)   [F, m]"""
    return genv['capk_a'] * w * l + genv['capk_p'] * 2 * (w + l)


def mim_side(c, genv):
    a, p = genv['capk_a'], genv['capk_p']
    return (-4 * p + math.sqrt(16 * p * p + 4 * a * c)) / (2 * a)


def apply_rules(subs, genv, opt, notes):
    """returns a copy of the subckt table with the element rules applied (still hierarchical, parameters not yet evaluated)"""
    out = {}
    for k, s in subs.items():
        n = Sub(s.name, list(s.ports), dict(s.defaults), s.file)
        n.elems = [e.copy() for e in s.elems]
        out[k] = n
    for cell, action, rx, count in RULES:
        s = out[cell]
        hit = [e for e in s.elems if re.fullmatch(rx, e.name.lower())]
        if len(hit) != count:
            die('rule (%s, %s, %s): %d elements found, %d expected: the simulation netlist changed, update RULES' % (cell, action, rx, len(hit), count))
        for e in hit:
            if action == 'drop':
                if e.kind == 'x':
                    die('rule drop on a device: %s.%s' % (cell, e.name))
                s.elems.remove(e)
                notes.append('%-13s removed  %-6s %s %s  (%s)' % (cell, e.name, ' '.join(e.nodes), e.params['value'], 'ideal element, no layout device'))
            elif action == 'short':
                a, b = e.nodes
                s.elems.remove(e)
                for o in s.elems:
                    o.nodes = [b if x.lower() == a.lower() else x for x in o.nodes]
                if a.lower() in [p.lower() for p in s.ports]:
                    die('rule short would rename a port of %s' % cell)
                notes.append('%-13s removed  %-6s %s %s %s; net %s joined with %s' % (cell, e.name, a, b, e.params['value'], a, b))
            elif action == 'mim_unit':
                old = '%s %s %s' % (e.name, ' '.join(e.nodes), e.params['value'])
                e.kind, e.model, e.name, e.params = 'x', MIM_SIM, 'X' + e.name, {'c_length': '5u', 'c_width': '5u'}
                notes.append('%-13s replaced %s (= %.1f fF ideal)  by  %s %s %s c_length=5u c_width=5u (%.2f fF, the smallest legal MIM)' % (
                    cell, old, ev(old.split()[-1], genv) * 1e15, e.name, ' '.join(e.nodes), MIM_LVS, mim_c(5e-6, 5e-6, genv) * 1e15))
            elif action == 'cin':
                w0, l0 = ev(e.params['c_width'], genv), ev(e.params['c_length'], genv)
                c0 = mim_c(w0, l0, genv)
                n = opt.cin_n
                if opt.cin_w:
                    w, l = opt.cin_w * 1e-6, opt.cin_l * 1e-6
                else:
                    w = l = mim_side(c0 / n, genv)
                c1 = n * mim_c(w, l, genv)
                idx = s.elems.index(e)
                s.elems.remove(e)
                nodes = list(e.nodes) if opt.cin_top == 'rec' else list(reversed(e.nodes))
                for k in range(n):
                    s.elems.insert(idx + k, Elem('%s_%d' % (e.name, k + 1), nodes, MIM_SIM, {'c_length': repr(l), 'c_width': repr(w)}, 'x'))
                notes.append('%-13s split    %s %s: one plate %.3f x %.3f um = %.1f um2 (> 10,000), %.4f pF  ->  %d pieces %.3f x %.3f um = %.1f um2 each, %.4f pF in total (%+.3f %%); top plate on %s' % (
                    cell, e.name, ' '.join(e.nodes), w0 * 1e6, l0 * 1e6, w0 * l0 * 1e12, c0 * 1e12, n, w * 1e6, l * 1e6, w * l * 1e12, c1 * 1e12, (c1 / c0 - 1) * 100, nodes[0]))
                if w * l * 1e12 > 10000.0 + 1e-6:
                    die('Cin piece area %.1f um2 is above the 10,000 um2 limit (MIMTM.8b): use more pieces' % (w * l * 1e12))
                if abs(c1 / c0 - 1) > 1e-3:
                    notes.append('              WARNING: the Cin pieces differ from the simulated capacitance by more than 0.1 % (AUDIT 4.9.3 rule 4)')
    if opt.cin_top == 'sum':
        s = out['stage2c']
        hit = [e for e in s.elems if e.name.lower() == 'xcin']
        if len(hit) != 1:
            die('stage2c: Xcin not found for --cin-top sum')
        hit[0].nodes = list(reversed(hit[0].nodes))
        notes.append('%-13s swapped  the plates of Xcin: top plate on %s (--cin-top sum)' % ('stage2c', hit[0].nodes[0]))
    return out


def fmt_um(v):
    s = '%.6f' % (v * 1e6)
    s = s.rstrip('0').rstrip('.')
    return s + 'u'


def flatten(subs, genv, name, keep=()):
    """-> (ports, [device lines as (name, nodes, model, {param: value})]) of subckt `name`, flat down to PDK devices (sub-cells listed in `keep` stay instances).
    Flat names: instance path joined with `_` (xs1.xota.xm1 -> Xs1_xota_xm1); internal nets likewise (xs1.vn -> xs1_vn)."""
    top = subs[name.lower()]
    devs = []

    def walk(sub, env, prefix, netmap):
        loc = dict(genv)
        for k, v in sub.defaults.items():
            loc[k] = ev(v, loc)
        loc.update(env)
        for e in sub.elems:
            nodes = [netmap.get(n.lower(), n if n == '0' else prefix + n.lower()) for n in e.nodes]
            nm = prefix + e.name.lower()
            if e.kind != 'x':
                die('ideal element left in %s: %s %s (add a rule)' % (sub.name, e.name, ' '.join(e.nodes)))
            model = e.model.lower()
            if model in subs and model not in keep:
                child = subs[model]
                if len(child.ports) != len(nodes):
                    die('%s.%s: %d nodes for %d pins of %s' % (sub.name, e.name, len(nodes), len(child.ports), child.name))
                cenv = {k: ev(v, loc) for k, v in e.params.items()}
                walk(child, cenv, nm + '_', {p.lower(): n for p, n in zip(child.ports, nodes)})
                continue
            if model in keep:
                devs.append((nm, nodes, subs[model].name, {}))
                continue
            par = {}
            g = lambda k, d=None: (ev(e.params[k], loc) if k in e.params else d)
            if model == MIM_SIM:
                model = MIM_LVS
            if model in MOS:
                if g('nf', 1.0) != 1.0:
                    die('%s: nf != 1 is not supported (nf does not scale W in these models)' % nm)
                par = {'w': fmt_um(g('w')), 'l': fmt_um(g('l'))}
            elif model == MIM_LVS or model in MOSCAP:
                par = {'c_length': fmt_um(g('c_length')), 'c_width': fmt_um(g('c_width'))}
            elif model in RES3 or model in RES2:
                par = {'r_length': fmt_um(g('r_length')), 'r_width': fmt_um(g('r_width'))}
            elif model == 'ppolyf_u_3k':
                die('%s uses ppolyf_u_3k: not a gf180mcuD device (Decision 44a)' % nm)
            else:
                die('%s: unknown device or subckt %s' % (nm, e.model))
            mult = g('m', 1.0)
            if abs(mult - round(mult)) > 1e-9 or mult < 1:
                die('%s: m = %r' % (nm, mult))
            if round(mult) != 1:
                par['m'] = '%d' % round(mult)
            if model not in LVS_DEVICES:
                die('%s: %s is not in the LVS device list' % (nm, model))
            devs.append((nm, nodes, model, par))

    walk(top, {}, '', {p.lower(): p.lower() for p in top.ports})
    names = [d[0] for d in devs]
    if len(set(names)) != len(names):
        die('flat device names of %s are not unique' % name)
    return [p.lower() for p in top.ports], devs


def census(devs):
    c = {}
    for _, _, m, par in devs:
        c[m] = c.get(m, 0) + 1
    return c


def sim_census(subs, name):
    """devices and ideal elements of the SIMULATION netlist (flat count)"""
    c = {}

    def walk(sub):
        for e in sub.elems:
            if e.kind != 'x':
                k = 'ideal ' + e.kind.upper()
                c[k] = c.get(k, 0) + 1
            elif e.model.lower() in subs:
                walk(subs[e.model.lower()])
            else:
                c[e.model.lower()] = c.get(e.model.lower(), 0) + 1
    walk(subs[name.lower()])
    return c


# =========================================================================================== Verilog reader (enough for AFE/top/dbs_afe_top.v)
class Mod:
    def __init__(self, name):
        self.name, self.ports, self.width, self.assign, self.inst = name, [], {}, [], []     # ports [(name, dir)], width {net: (msb, lsb) or None}, inst [(type, params, name, {pin: expr}, loop)]


def vstrip(txt):
    txt = re.sub(r'/\*.*?\*/', '', txt, flags=re.S)
    txt = re.sub(r'//[^\n]*', '', txt)
    out, stack = [], []
    for ln in txt.split('\n'):
        s = ln.strip()
        if re.match(r'`ifdef\s+\w+', s):
            stack.append([False, False])           # no macro is defined (SIM_STUBS, SYNTHESIS, GLS ... are simulation switches)
            continue
        if re.match(r'`ifndef\s+\w+', s):
            stack.append([True, True])
            continue
        if s.startswith('`else'):
            stack[-1][0] = not stack[-1][1]
            continue
        if s.startswith('`endif'):
            stack.pop()
            continue
        if s.startswith('`'):
            continue
        if stack and not all(x[0] for x in stack):
            continue
        out.append(ln)
    return re.sub(r'\(\*.*?\*\)', '', '\n'.join(out), flags=re.S)


def split0(s, sep=','):
    out, d, cur = [], 0, ''
    for ch in s:
        if ch in '([{':
            d += 1
        elif ch in ')]}':
            d -= 1
        if ch == sep and d == 0:
            out.append(cur)
            cur = ''
        else:
            cur += ch
    if cur.strip():
        out.append(cur)
    return out


def rng(s):
    if not s:
        return None
    m = re.match(r'\[\s*(\d+)\s*:\s*(\d+)\s*\]', s)
    if not m:
        die('cannot read the range %s' % s)
    return (int(m.group(1)), int(m.group(2)))


def read_verilog(path):
    mods = {}
    txt = vstrip(open(path).read())
    for m in re.finditer(r'\bmodule\s+(\w+)\s*\((.*?)\)\s*;(.*?)\bendmodule', txt, flags=re.S):
        mod = Mod(m.group(1))
        cur_dir, cur_r = None, None
        for item in split0(m.group(2)):
            mm = re.match(r'\s*(input|output|inout)?\s*(?:wire|reg)?\s*(\[[^\]]+\])?\s*(\w+)\s*$', item, flags=re.S)
            if not mm:
                die('%s: cannot read the port %r' % (mod.name, item.strip()))
            if mm.group(1):
                cur_dir, cur_r = mm.group(1), rng(mm.group(2))
            mod.ports.append((mm.group(3), cur_dir))
            mod.width[mm.group(3)] = cur_r
        body = m.group(3)
        for mm in re.finditer(r'\bwire\s*(\[[^\]]+\])?\s*([^;=]+);', body):
            for n in mm.group(2).split(','):
                mod.width[n.strip()] = rng(mm.group(1))
        for mm in re.finditer(r'\bassign\s+(\w+)\s*=\s*([^;]+);', body):
            mod.assign.append((mm.group(1), mm.group(2).strip()))
        loops = [(g.start(), g.end(), g.group(1), int(g.group(2)), g.group(3)) for g in
                 re.finditer(r'generate\s+for\s*\(\s*(\w+)\s*=\s*0\s*;\s*\w+\s*<\s*(\d+)\s*;[^)]*\)\s*begin\s*:\s*(\w+).*?endgenerate', body, flags=re.S)]
        for mm in re.finditer(r'\b(\w+)\s*(#\s*\((?:[^()]|\([^()]*\))*\))?\s+(\w+)\s*\(\s*(\.[^;]*?)\)\s*;', body, flags=re.S):
            typ = mm.group(1)
            if typ in ('module', 'assign', 'always', 'if', 'else', 'for', 'begin', 'generate', 'wire', 'reg', 'genvar'):
                continue
            pins = {}
            for c in split0(mm.group(4)):
                cm = re.match(r'\s*\.(\w+)\s*\((.*)\)\s*$', c.strip(), flags=re.S)
                if not cm:
                    die('%s.%s: cannot read the connection %r' % (mod.name, mm.group(3), c.strip()))
                pins[cm.group(1)] = cm.group(2).strip()
            par = dict(re.findall(r'\.(\w+)\s*\(\s*([^()]*?)\s*\)', mm.group(2) or ''))
            loop = None
            for a, b, v, n, lab in loops:
                if a <= mm.start() < b:
                    loop = (v, n, lab)
            mod.inst.append((typ, par, mm.group(3), pins, loop))
        mods[mod.name] = mod
    return mods


def read_module_ports(path, name):
    """port bits (declaration order, MSB first) of ONE module of a gate-level netlist.  Only the header and the input / output / inout declarations are read (ANSI or not),
    so escaped identifiers and thousands of cell instances in the body do not matter."""
    txt = re.sub(r'/\*.*?\*/', '', open(path).read(), flags=re.S)
    txt = re.sub(r'//[^\n]*', '', txt)
    m = re.search(r'\bmodule\s+%s\s*\((.*?)\)\s*;(.*?)\bendmodule' % re.escape(name), txt, flags=re.S)
    if not m:
        return None
    order, width = [], {}
    cur_r = None
    for item in split0(m.group(1)):
        mm = re.match(r'\s*(input|output|inout)?\s*(?:wire|reg)?\s*(\[[^\]]+\])?\s*(\w+)\s*$', item, flags=re.S)
        if not mm:
            die('%s: cannot read the port %r of %s' % (path, item.strip(), name))
        if mm.group(1):
            cur_r = rng(mm.group(2))
        order.append(mm.group(3))
        width[mm.group(3)] = cur_r
    for mm in re.finditer(r'\b(?:input|output|inout)\s*(?:wire|reg)?\s*(\[[^\]]+\])?\s*([\w\s,]+);', m.group(2)):
        for n in mm.group(2).split(','):
            if n.strip() in width:
                width[n.strip()] = rng(mm.group(1))
    out = []
    for n in order:
        out += bits_of(n, width[n])
    return out


def bits_of(name, r):
    if r is None:
        return [name]
    step = -1 if r[0] >= r[1] else 1
    return ['%s[%d]' % (name, k) for k in range(r[0], r[1] + step, step)]


def expand(expr, mod, lv=None, i=None):
    """bits of a connection expression, MSB first.  Constants come back as "1'b0" / "1'b1"."""
    e = expr.strip()
    if e in ("1'b0", "1'b1"):
        return [e]
    sub = lambda s: int(eval(re.sub(r'\b%s\b' % lv, str(i), s), {'__builtins__': {}}, {})) if lv else int(eval(s, {'__builtins__': {}}, {}))
    m = re.fullmatch(r'(\w+)', e)
    if m:
        if e not in mod.width:
            die('%s: net %s is not declared' % (mod.name, e))
        return bits_of(e, mod.width[e])
    m = re.fullmatch(r'(\w+)\s*\[\s*([^:\]]+?)\s*\+:\s*(\d+)\s*\]', e)
    if m:
        lo = sub(m.group(2))
        return ['%s[%d]' % (m.group(1), k) for k in range(lo + int(m.group(3)) - 1, lo - 1, -1)]
    m = re.fullmatch(r'(\w+)\s*\[\s*([^:\]]+)\s*:\s*([^:\]]+)\s*\]', e)
    if m:
        return bits_of(m.group(1), (sub(m.group(2)), sub(m.group(3))))
    m = re.fullmatch(r'(\w+)\s*\[\s*([^:\]]+)\s*\]', e)
    if m:
        return ['%s[%d]' % (m.group(1), sub(m.group(2)))]
    die('%s: cannot read the connection expression %r' % (mod.name, expr))


def port_bits(mod):
    out = []
    for n, _ in mod.ports:
        out += bits_of(n, mod.width[n])
    return out


# =========================================================================================== writers
def wrap(s, width=150):
    if len(s) <= width:
        return s
    out, cur = [], ''
    for t in s.split(' '):
        if cur and len(cur) + 1 + len(t) > width:
            out.append(cur)
            cur = '+ ' + t
        else:
            cur = (cur + ' ' + t) if cur else t
    out.append(cur)
    return '\n'.join(out)


def dev_line(d):
    nm, nodes, model, par = d
    order = [k for k in ('w', 'l', 'c_length', 'c_width', 'r_length', 'r_width', 'm') if k in par]
    return wrap('X%s %s %s%s' % (nm[1:] if nm[0] in 'xX' else nm, ' '.join(nodes), model, ''.join(' %s=%s' % (k, par[k]) for k in order)))


def subckt_text(name, ports, devs, comment=''):
    L = []
    if comment:
        L += ['* ' + c for c in comment.split('\n')]
    L.append(wrap('.subckt %s %s' % (name, ' '.join(ports))))
    L += [dev_line(d) for d in devs]
    L.append('.ends %s' % name)
    return '\n'.join(L) + '\n'


def std_cell_text(name):
    txt = open(PDK_STD).read()
    m = re.search(r'^\.SUBCKT %s .*?^\.ENDS' % re.escape(name), txt, flags=re.S | re.M)
    if not m:
        die('standard cell %s not found in %s' % (name, PDK_STD))
    ports = m.group(0).split('\n')[0].split()[2:]
    return ports, '* standard cell, copied unchanged from the PDK (%s)\n%s\n' % (os.path.relpath(PDK_STD, '/foss/pdks'), m.group(0))


# =========================================================================================== main
def main():
    ap = argparse.ArgumentParser(description='LVS reference netlists from the simulation netlists (AUDIT 4.9.3)')
    ap.add_argument('--out', default=os.path.join(LAY, 'lvs'))
    ap.add_argument('--cin', default='2', help='N or N,W_um,L_um: pieces of each stage-1 input capacitor (default 2 squares sized for C/N each)')
    ap.add_argument('--cin-top', default='sum', choices=('rec', 'sum'), help='which net the TOP plate of the input capacitors (stage 1 Cin, stage 2 Cin2) is on: rec = as in the simulation netlists '
                    '(electrode / driven side on top, summing node on the bottom plate); sum = summing node on the top plate')
    ap.add_argument('--decap', default='20,20', help='W_um,L_um of ONE cap_nmos_03v3 decap unit (c_width, c_length)')
    ap.add_argument('--rstrap', default='rm3,2,222.2', help='MODEL,W_um,L_um of the 10 ohm strap resistor')
    ap.add_argument('--decap-n', default=None, help='NMAIN,NDAC: explicit numbers of decap units on the ADC-main strap (VDD) and on the ADC-DAC strap (vdd_dac); default: computed from the capacitance')
    ap.add_argument('--ties', default='dig', choices=('dig', 'resistor'), help='the 15 constant pad-control pins: dig = output pins of afe_dig driven by its tie cells (Decision 46e, default); '
                    'resistor = 0-ohm resistors to VDD / VSS in the top (the F1 form)')
    ap.add_argument('--dig-netlist', default=None, help='powered gate-level netlist of afe_dig (L1d): its port order is used for the black-box instance')
    ap.add_argument('--follower', default='native', choices=('native', 'rvt', 'nodnw'), help='output follower of stage 2: native = nfet_06v0_nvt (design netlists, default); rvt / nodnw = '
                    'the pre-approved fallbacks of ACCEPT.md ladder N (AFE/amp/spice/ota2_rvt.spice + afe_chc_rvt.spice, or ota2_rvt_nodnw.spice + afe_chc_rvt.spice; LP step 6)')
    opt = ap.parse_args()
    if opt.follower != 'native':
        sub = {'AFE/amp/spice/ota2.spice': 'AFE/amp/spice/ota2_rvt.spice' if opt.follower == 'rvt' else 'AFE/amp/spice/ota2_rvt_nodnw.spice',
               'AFE/amp/spice/afe_chc.spice': 'AFE/amp/spice/afe_chc_rvt.spice'}
        SIM_FILES[:] = [sub.get(f, f) for f in SIM_FILES]
    c = opt.cin.split(',')
    opt.cin_n, opt.cin_w, opt.cin_l = int(c[0]), (float(c[1]) if len(c) == 3 else None), (float(c[2]) if len(c) == 3 else None)
    dw, dl = [float(x) for x in opt.decap.split(',')]
    rs_model, rs_w, rs_l = opt.rstrap.split(',')[0], float(opt.rstrap.split(',')[1]), float(opt.rstrap.split(',')[2])
    decap_n = None
    if opt.decap_n:
        try:
            decap_n = {'main': int(opt.decap_n.split(',')[0]), 'dac': int(opt.decap_n.split(',')[1])}
        except Exception:
            die('--decap-n expects NMAIN,NDAC (two integers), got %r' % opt.decap_n)
        if min(decap_n.values()) < 1:
            die('--decap-n: the numbers of units must be >= 1')
    if rs_model not in RES2 + RES3:
        die('--rstrap: unknown resistor model %s' % rs_model)
    os.makedirs(opt.out, exist_ok=True)

    sim, genv = read_spice(SIM_FILES)
    notes = []
    lvs = apply_rules(sim, genv, opt, notes)
    mods = read_verilog(os.path.join(REPO, TOP_V))
    for need in ('dbs_afe_top', 'afe_ch'):
        if need not in mods:
            die('module %s not found in %s' % (need, TOP_V))

    # options as given on the command line, per file: the cell files (afe_chc / adc_ch / bias_genc) only depend on the Cin options, so their text does not change when the top is
    # regenerated for another digital netlist, decap count or strap resistor (LP step 5)
    argl, k = [], 1
    while k < len(sys.argv):
        a = sys.argv[k]
        if a.startswith('--') and '=' not in a and k + 1 < len(sys.argv):
            argl.append((a, a + ' ' + sys.argv[k + 1]))
            k += 2
        else:
            argl.append((a.split('=')[0], a))
            k += 1
    opt_cells = ' '.join(t for f, t in argl if f in ('--cin', '--cin-top')) or '(defaults)'
    opt_top = ' '.join(t for f, t in argl if f != '--out') or '(defaults)'
    HDR0 = ('* LVS REFERENCE netlist, written by AFE/layout/scripts/mk_lvs_netlists.py from the simulation netlists (AFE/review/AUDIT.md 4.9.3, Decision 44e).\n'
            '* DO NOT EDIT: change the simulation netlist or the script and run the script again.  Options of this run: %s\n'
            '* MIM = cap_mim_2f0_m4m5_noshield (terminal 1 = top plate, 2 = bottom plate, NOT interchangeable in LVS); all sizes are numbers; no ideal element.\n')
    HDR, HDR_TOP = HDR0 % opt_cells, HDR0 % opt_top

    # ---------------- flat analog cells
    flat = {}
    for cell in ('afe_chc', 'fs_oneshot_c', 'bias_genc', 'dac_sw', 'cmp_p', 'vhalf', 'vrefs', 'tgate'):
        flat[cell] = flatten(lvs, genv, cell)
    P('mk_lvs_netlists.py  options: %s' % (' '.join(sys.argv[1:]) or '(defaults)'))
    P('Sources: %d simulation netlists + %s; rules of AFE/review/AUDIT.md 4.9.3.  Output: %s' % (len(SIM_FILES), TOP_V, os.path.relpath(opt.out, REPO)))
    P('\nELEMENT RULES APPLIED (simulation netlist -> LVS reference)')
    for n in notes:
        P('  ' + n)
    P('  every cell      %s -> %s (same model parameters; the 5-metal stack has the MIM between Metal4 and Metal5)' % (MIM_SIM, MIM_LVS))
    P('\nDEVICE CENSUS per analog cell:  simulation netlist  ->  LVS reference')
    for cell in ('afe_chc', 'fs_oneshot_c', 'bias_genc', 'dac_sw', 'cmp_p', 'vhalf', 'vrefs', 'tgate'):
        a, b = sim_census(sim, cell), census(flat[cell][1])
        P('  %-13s sim: %s' % (cell, ', '.join('%s x%d' % (k, v) for k, v in sorted(a.items()))))
        P('  %-13s LVS: %s   (%d devices; pins: %s)' % ('', ', '.join('%s x%d' % (k, v) for k, v in sorted(b.items())), len(flat[cell][1]), ' '.join(flat[cell][0])))

    # ---------------- MIM / resistor tables
    P('\nMIM CAPACITORS of the LVS reference (C from the netlists\' formula C = %.4g W L + %.4g x 2 (W + L); rule check 25 um2 <= area <= 10,000 um2)' % (genv['capk_a'], genv['capk_p']))
    bad_mim = 0
    for cell in ('afe_chc', 'fs_oneshot_c', 'bias_genc', 'dac_sw', 'cmp_p', 'vhalf', 'vrefs'):
        seen = {}
        for nm, nodes, model, par in flat[cell][1]:
            if model != MIM_LVS:
                continue
            w, l = num(par['c_width']), num(par['c_length'])
            key = (par['c_width'], par['c_length'])
            seen.setdefault(key, []).append((nm, nodes))
            if not (25.0 - 1e-6 <= w * l * 1e12 <= 10000.0 + 1e-6):
                bad_mim += 1
        for (ws, ls), lst in sorted(seen.items(), key=lambda kv: -num(kv[0][0]) * num(kv[0][1])):
            w, l = num(ws), num(ls)
            ex = lst[0]
            P('  %-13s %3d x  %9s x %-9s = %9.1f um2  %10.2f fF each   %s  e.g. X%s (top %s, bottom %s)' % (
                cell, len(lst), ws, ls, w * l * 1e12, mim_c(w, l, genv) * 1e15, 'ok' if 25.0 - 1e-6 <= w * l * 1e12 <= 10000.0 + 1e-6 else 'RULE VIOLATION', ex[0][1:], ex[1][0], ex[1][1]))
    if bad_mim:
        die('%d MIM capacitors violate the area rules' % bad_mim)
    P('\nPOLY RESISTORS of the LVS reference (nominal R = 1000 ohm/sq x length / width, PDK typical rsh)')
    for cell in ('bias_genc', 'vhalf'):
        for nm, nodes, model, par in flat[cell][1]:
            if model in RES3:
                w, l = num(par['r_width']), num(par['r_length'])
                P('  %-13s X%-6s %-12s %s  width %s length %s = %.1f squares = %.1f kOhm nominal' % (cell, nm[1:], model, ' '.join(nodes), par['r_width'], par['r_length'], l / w, RSH[model] * l / w / 1e3))

    # ---------------- afe_ch from the Verilog: groups amp_ch / adc_ch
    ch = mods['afe_ch']
    chbits = port_bits(ch)
    insts = {}
    for typ, par, iname, pins, loop in ch.inst:
        if loop:
            die('afe_ch: generate loops are not expected here')
        insts[iname] = (typ, pins)
    grouped = [i for g in GROUPS.values() for i in g]
    for i in grouped:
        if i not in insts:
            die('afe_ch: instance %s (table GROUPS) not found' % i)
    rest = [i for i in insts if i not in grouped]
    for i in rest:
        if insts[i][0] != 'TGATE':
            die('afe_ch: instance %s (%s) is in no group of the table GROUPS' % (i, insts[i][0]))
    std_ports = {}
    std_text = {}

    def cell_pins(typ):
        """SPICE pin order of a cell instantiated in afe_ch / dbs_afe_top"""
        k = typ.lower()
        if k in flat:
            return flat[k][0], (sim[k].name if k in sim else typ)
        if k.startswith('gf180mcu_fd_sc_'):
            if k not in std_ports:
                std_ports[k], std_text[k] = std_cell_text(typ)
            return [p.lower() for p in std_ports[k]], typ
        die('no SPICE view for the cell %s' % typ)

    def xline(mod, iname, typ, pins, lv=None, i=None, xname=None):
        spins, sname = cell_pins(typ)
        vp = {p.lower(): e for p, e in pins.items()}
        nodes = []
        imp = IMPLICIT_POWER.get(typ.lower(), {})
        for sp in spins:
            if sp in vp:
                b = expand(vp[sp], mod, lv, i)
                if len(b) != 1 or b[0].startswith("1'b"):
                    die('%s.%s pin %s: expected one net, got %s' % (mod.name, iname, sp, b))
                nodes.append(b[0])
            elif sp in imp:
                nodes.append(imp[sp])
            else:
                die('%s.%s (%s): SPICE pin %s is not connected in the Verilog and has no implicit-power rule' % (mod.name, iname, typ, sp))
        extra = [p for p in vp if p not in spins]
        if extra:
            die('%s.%s (%s): Verilog pins %s do not exist in the SPICE cell' % (mod.name, iname, typ, extra))
        return ((xname or iname), nodes, sname, {})

    ch_lines = {i: xline(ch, i, insts[i][0], insts[i][1]) for i in insts}
    used = {}          # net -> set of instance names
    for i, (nm, nodes, sname, _) in ch_lines.items():
        for n in nodes:
            used.setdefault(n, set()).add(i)
    group_text, group_ports, group_inst = {}, {}, {}
    for g, members in GROUPS.items():
        nets = []
        for i in members:
            for n in ch_lines[i][1]:
                if n not in nets:
                    nets.append(n)
        ext = [n for n in nets if n in chbits or (used[n] - set(members))]
        sig = [n for n in chbits if n in ext and n not in SUPPLY_NETS] + [n for n in ext if n not in chbits and n not in SUPPLY_NETS]
        pins_g = sig + [n for n in SUPPLY_NETS if n in ext]
        ren = {n: GROUP_PIN_NAME.get((g, n), n) for n in pins_g}
        if len(set(ren.values())) != len(ren):
            die('%s: pin names are not unique after renaming' % g)
        body = []
        for i in members:
            nm, nodes, sname, par = ch_lines[i]
            body.append((nm, [ren.get(n, n) for n in nodes], sname, par))
        group_ports[g] = [ren[n] for n in pins_g]
        group_inst[g] = ('x' + g, pins_g, g, {})
        group_text[g] = body
    P('\nCHANNEL CELLS from module afe_ch of %s' % TOP_V)
    P('  amp_ch (L2) = %s;  pins: %s' % (' + '.join('%s (%s)' % (i, insts[i][0]) for i in GROUPS['amp_ch']), ' '.join(group_ports['amp_ch'])))
    P('  adc_ch (L1) = %s;  pins: %s' % (' + '.join('%s (%s)' % (i, insts[i][0]) for i in GROUPS['adc_ch']), ' '.join(group_ports['adc_ch'])))
    P('  afe_ch (L3) = %s + amp_ch + adc_ch;  pins: %s' % (' + '.join('%s (%s)' % (i, insts[i][0]) for i in rest), ' '.join(chbits)))
    internal = sorted(n for n in used if n not in chbits)
    P('  internal nets of afe_ch: %s' % ' '.join('%s[%s]' % (n, ','.join(sorted(used[n]))) for n in internal))
    P('  implicit power (not in the Verilog): TGATE VDD / VSS -> vdd / vss (analog strap); standard cells VDD, VNW -> vdd, VSS, VPW -> vss')
    P('  supply pins of adc_ch: vdd = %s;  vdd_cmp = %s;  vdd_dac = %s' % tuple(
        ', '.join(sorted('%s.%s' % (i, p) for i in GROUPS['adc_ch'] for p, n in zip(cell_pins(insts[i][0])[0], ch_lines[i][1]) if n == s)) for s in ('vdd', 'vdd_cmp', 'vdd_dac')))

    # ---------------- top from the Verilog
    top = mods['dbs_afe_top']
    topbits = port_bits(top)
    alias = {}        # internal net -> port it is assigned to
    ties = []         # (port, 'VDD' | 'VSS')
    for lhs, rhs in top.assign:
        if rhs == "1'b0":
            ties.append((lhs, 'VSS'))
        elif rhs == "1'b1":
            ties.append((lhs, 'VDD'))
        elif re.fullmatch(r'\w+', rhs):
            alias[rhs] = lhs
        else:
            die('dbs_afe_top: assign %s = %s is not a tie or an alias' % (lhs, rhs))
    A = lambda n: alias.get(n, n)
    top_lines = []
    dig = {}
    supply_devs = []
    for typ, par, iname, pins, loop in top.inst:
        if typ in ('adc8_top', 'dbs_ctrl'):
            dig[iname] = pins
        elif typ == 'afe_ch':
            if not loop:
                die('dbs_afe_top: afe_ch is expected in a generate loop')
            lv, n, lab = loop
            for i in range(n):
                nodes = []
                for pn, _ in ch.ports:
                    if pn not in pins:
                        die('dbs_afe_top: afe_ch pin %s is not connected' % pn)
                    b = expand(pins[pn], top, lv, i)
                    if len(b) != len(bits_of(pn, ch.width[pn])):
                        die('dbs_afe_top: width mismatch on afe_ch.%s' % pn)
                    nodes += [A(x) for x in b]
                top_lines.append(('x%s%d' % (lab, i), nodes, 'afe_ch', {}))
            extra = [p for p in pins if p not in [q for q, _ in ch.ports]]
            if extra:
                die('dbs_afe_top: afe_ch has no pins %s' % extra)
        elif typ == 'afe_rstrap':
            a, b, s = (A(expand(pins[k], top)[0]) for k in ('a', 'b', 'vss'))
            nodes = [a, b] + ([s] if rs_model in RES3 else [])
            supply_devs.append(('x' + iname, nodes, rs_model, {'r_length': fmt_um(rs_l * 1e-6), 'r_width': fmt_um(rs_w * 1e-6)}))
            P('\nSUPPLY DEVICES of the top (Decision 44d, AUDIT 4.9.2)')
            P('  strap resistor  X%s %s %s: %s  width %g um length %g um = %.1f squares x %.3g ohm/sq (typical) = %.2f ohm  (target 10 ohm, X2 S4)' % (
                iname, a, b, rs_model, rs_w, rs_l, rs_l / rs_w, RSH[rs_model], RSH[rs_model] * rs_l / rs_w))
        elif typ == 'afe_decap':
            p_, n_ = A(expand(pins['p'], top)[0]), A(expand(pins['n'], top)[0])
            cn = float(par['C_NF'])
            unit = dw * dl * MOSCAP_FF_UM2 * 1e-6      # nF per unit
            m = int(math.ceil(cn / unit - 1e-9))
            how = 'smallest number of units that reaches the capacitance asked'
            if decap_n:
                strap = 'dac' if p_ == 'vdd_dac' else 'main'       # the ADC-DAC strap is the net vdd_dac; the ADC-main strap is the net VDD
                how = '--decap-n: %d units as placed on the ADC-%s strap (the capacitance alone would need %d)' % (decap_n[strap], strap, m)
                m = decap_n[strap]
            supply_devs.append(('x' + iname, [p_, n_], 'cap_nmos_03v3', {'c_length': fmt_um(dl * 1e-6), 'c_width': fmt_um(dw * 1e-6), 'm': '%d' % m}))
            P('  decap           X%s %s %s: cap_nmos_03v3  %d units of %g x %g um (c_width x c_length) = %.0f um2, %.2f fF/um2 at 3.3 V -> %.2f pF  (asked: %.1f pF; %s)%s' % (
                iname, p_, n_, m, dw, dl, m * dw * dl, MOSCAP_FF_UM2, m * unit * 1e3, cn * 1e3, how, '' if m * unit >= cn - 1e-12 else '   WARNING: LESS THAN ASKED'))
        else:
            top_lines.append(xline(top, iname, typ, pins))
            top_lines[-1] = (top_lines[-1][0], [A(x) for x in top_lines[-1][1]], top_lines[-1][2], {})
    if sorted(dig) != ['u_adc', 'u_dbs']:
        die('dbs_afe_top: expected the digital instances u_adc and u_dbs, found %s' % sorted(dig))
    for (i1, p1, i2, p2) in DIG_INTERNAL:
        if [A(x) for x in expand(dig[i1][p1], top)] != [A(x) for x in expand(dig[i2][p2], top)]:
            die('digital macro: %s.%s and %s.%s are not on the same net' % (i1, p1, i2, p2))
    if dig['u_dbs'].get('ready') != "1'b1":
        die('digital macro: dbs_ctrl.ready is expected to be tied high')
    handled = set((i, p) for _, i, p in DIG_PINS) | set((a, b) for a, b, _, _ in DIG_INTERNAL) | set((c, d) for _, _, c, d in DIG_INTERNAL) | {('u_dbs', 'ready')}
    left = [(i, p) for i in dig for p in dig[i] if (i, p) not in handled]
    if left:
        die('digital macro: connections %s are not in the table DIG_PINS' % left)
    dig_map = {}       # macro pin bit -> top net
    dig_w = {}
    for pin, inst_, port in DIG_PINS:
        b = [A(x) for x in expand(dig[inst_][port], top)]
        dig_w[pin] = len(b)
        if len(b) == 1:
            dig_map[pin] = b[0]
        else:
            for k, n in enumerate(b):
                dig_map['%s[%d]' % (pin, len(b) - 1 - k)] = n
    for pin, net in DIG_POWER:
        dig_map[pin] = net
    # pad-control constants (Decision 46e): tie cells inside afe_dig, one macro output pin per constant-tied top pin, same name
    tie_pins = []
    if opt.ties == 'dig':
        dig_v = os.path.join(AFE, 'dig', 'afe_dig.v')
        if not os.path.exists(dig_v):
            die('--ties dig needs AFE/dig/afe_dig.v (the wrapper with the tie cells); use --ties resistor for the F1 form')
        cells = {}
        for mm in re.finditer(r'gf180mcu_fd_sc_mcu7t5v0__tie([hl])\s+\w+\s*\(\s*\.\w+\s*\(\s*(\w+)\s*\)\s*\)', re.sub(r'//[^\n]*', '', open(dig_v).read())):
            cells[mm.group(2)] = 'VDD' if mm.group(1) == 'h' else 'VSS'
        if cells != dict(ties):
            die('pad-control constants: AFE/top/dbs_afe_top.v assigns %s, the tie cells of AFE/dig/afe_dig.v drive %s' % (sorted(ties), sorted(cells.items())))
        for port, rail in ties:
            if port in dig_map:
                die('tie pin %s clashes with a signal pin of afe_dig' % port)
            dig_map[port] = port
            tie_pins.append(port)
    for i1, p1, _, _ in DIG_INTERNAL[2:]:
        for n in expand(dig[i1][p1], top):
            users = [x for x in top_lines if n in x[1]]
            if users or n in topbits:
                die('net %s must stay inside the digital macro' % n)
    if opt.dig_netlist:
        dbits = read_module_ports(opt.dig_netlist, 'afe_dig')
        if dbits is None:
            die('%s has no module afe_dig' % opt.dig_netlist)
        miss = [b for b in dbits if b not in dig_map]
        if miss:
            die('afe_dig pins without a net in the top: %s' % miss[:10])
        unused = [b for b in dig_map if b not in dbits]
        if unused:
            die('pins expected on afe_dig but missing in %s: %s' % (opt.dig_netlist, unused[:10]))
        dig_order = dbits
        dig_def = '* afe_dig: the digital macro (dbs_ctrl N = 8 + adc8_top).  Its definition is the powered gate-level netlist %s (LVS_VERILOG_FILES);\n* the instance below lists the nets in the port order of that file.\n' % os.path.relpath(opt.dig_netlist, REPO)
    else:
        dig_order = [p for p, _ in DIG_POWER]
        for pin, _, _ in DIG_PINS:
            dig_order += [pin] if dig_w[pin] == 1 else ['%s[%d]' % (pin, k) for k in range(dig_w[pin] - 1, -1, -1)]
        dig_order += tie_pins
        dig_def = ('* afe_dig: the digital macro (dbs_ctrl N = 8 + adc8_top, hardened in L1d) as a BLACK BOX.  PROVISIONAL pin list = the L1d prompt (AFE/prompts/layout_run.md) with VDD VSS first'
                   + (' and the %d pad-control tie pins last' % len(tie_pins) if tie_pins else '') + '.\n'
                   '* When the powered gate-level netlist exists, run this script with --dig-netlist <file>: the instance then follows the port order of that file and this empty definition is not written\n'
                   '* (the netlist itself goes into LVS_VERILOG_FILES, as in the organizer\'s mixed-signal example).\n' + wrap('.subckt afe_dig ' + ' '.join(dig_order)) + '\n.ends afe_dig\n')
    top_lines.insert(0, ('xdig', [dig_map[b] for b in dig_order], 'afe_dig', {}))
    tie_lines = ['Rtie_%s %s %s 0' % (p, p, r) for p, r in ties] if opt.ties == 'resistor' else []
    nets_top = set(n for l in top_lines + supply_devs for n in l[1])
    open_ports = [b for b in topbits if b not in nets_top and b not in [p for p, _ in ties]]
    if open_ports != ['DOUT_IN']:
        die('top ports without a connection: %s (only DOUT_IN is expected: the pad input is not used)' % open_ports)
    low = {}
    for n in list(nets_top) + topbits:
        if low.setdefault(n.lower(), n) != n:
            die('top nets %s and %s differ only in case' % (low[n.lower()], n))
    P('\nTOP dbs_afe_top from %s' % TOP_V)
    P('  %d pins: %s' % (len(topbits), ' '.join(topbits)))
    cnt = {}
    for l in top_lines:
        cnt[l[2]] = cnt.get(l[2], 0) + 1
    P('  instances: %s + %d supply devices + %d pad-control ties (%s: %s)' % (', '.join('%d x %s' % (v, k) for k, v in cnt.items()), len(supply_devs), len(ties),
                                                                              'output pins of afe_dig, driven by its tie cells (Decision 46e); pin-constant' if opt.ties == 'dig' else '0-ohm resistors',
                                                                              ', '.join('%s-%s' % t for t in ties)))
    P('  pad pins that are plain nets of the macro: %s;  top port without a connection inside: %s (the pad input is not used, DOUT_IE = 0)' % (
        ', '.join('%s = afe_dig.%s' % (dig_map[p], p) for p in ('DOUT', 'DOUT_OE')), ' '.join(open_ports)))
    P('  net census: VDD on %d channel pins (vdd, vdd_cmp) + bias_genc + afe_dig + decap + strap; vdd_dac on %d channel pins + decap + strap' % (
        sum(l[1].count('VDD') for l in top_lines if l[2] == 'afe_ch'), sum(l[1].count('vdd_dac') for l in top_lines if l[2] == 'afe_ch')))
    P('  digital macro afe_dig: %d pins, %s' % (len(dig_order), 'port order of ' + opt.dig_netlist if opt.dig_netlist else 'PROVISIONAL black box (L1d pin list, VDD VSS first)'))
    P('    afe_dig pin -> net of the top: ' + ', '.join('%s -> %s' % (pin, (dig_map[pin] if dig_w.get(pin, 1) == 1 else '%s[%d:0]' % (re.sub(r'\[\d+\]$', '', dig_map['%s[0]' % pin]), dig_w[pin] - 1)))
                                                     for pin in [p for p, _ in DIG_POWER] + [p for p, _, _ in DIG_PINS]))

    # ---------------- files
    def cell(c):
        return subckt_text(sim[c].name if c in sim else c, flat[c][0], flat[c][1])

    amp_file = (HDR + '* File afe_chc.spice: the amplifier part of one channel (L2).  Cells: afe_chc (stage 1 + stage 2 + follower + gate muxes + REC park), fs_oneshot_c, the OR2 standard cell,\n'
                '* and amp_ch = afe_chc + fs_oneshot_c + OR2 wired as in module afe_ch of AFE/top/dbs_afe_top.v (out = the net amp_out of afe_ch).\n\n'
                + cell('afe_chc') + '\n' + cell('fs_oneshot_c') + '\n' + ''.join(std_text[k] for k in sorted(std_text) if 'or2' in k) + '\n'
                + subckt_text('amp_ch', group_ports['amp_ch'], group_text['amp_ch']))
    adc_file = (HDR + '* File adc_ch.spice: the ADC analog part of one channel (L1).  Cells: dac_sw (split 6+6 MIM DAC, 13 drivers on vdd_dac, 13 sampling TGs, 2 reset switches), cmp_p (on vdd_cmp),\n'
                '* vhalf, vrefs (Cref switch + Cref), the INV standard cell (samb), and adc_ch = their wiring in module afe_ch of AFE/top/dbs_afe_top.v (vin = the net amp_out of afe_ch).\n'
                '* Supply pins of adc_ch (AUDIT 4.9.2): vdd = analog strap (vhalf, Cref switch, inverter, sampling-TG n-wells); vdd_cmp = ADC-main strap; vdd_dac = ADC-DAC strap; one vss.\n\n'
                + cell('dac_sw') + '\n' + cell('cmp_p') + '\n' + cell('vhalf') + '\n' + cell('vrefs') + '\n' + ''.join(std_text[k] for k in sorted(std_text) if 'inv' in k) + '\n'
                + subckt_text('adc_ch', group_ports['adc_ch'], group_text['adc_ch']))
    bias_file = HDR + '* File bias_genc.spice: the shared bias cell (one per chip, L3): beta-multiplier master, start-up, ladders A and B in ppolyf_u_1k, reset-level replica, C_VRS.\n\n' + cell('bias_genc')
    ch_body = [ch_lines[i] for i in rest] + [group_inst['amp_ch'], group_inst['adc_ch']]
    top_text = wrap('.subckt dbs_afe_top ' + ' '.join(topbits)) + '\n'
    top_text += '* digital macro\n' + dev_line(top_lines[0]) + '\n* shared bias and the 8 channels\n' + '\n'.join(dev_line(l) for l in top_lines[1:]) + '\n'
    top_text += '* supply network (Decision 44d): ADC-main strap decap and ADC-DAC strap decap (MOS capacitors, gate on the rail), the strap resistor between the two straps\n' + '\n'.join(dev_line(l) for l in supply_devs) + '\n'
    if opt.ties == 'resistor':
        top_text += ('* pad-control ties (Decision 41d / 44b): a top pin shorted to VDD or VSS, written as a 0-ohm resistor so that the pin keeps its own name.  Magic writes the same element from a layout\n'
                     '* short with `ext2spice short resistor` (F1 form; the default since Decision 46e is tie cells inside afe_dig).\n' + '\n'.join(tie_lines) + '\n.ends dbs_afe_top\n')
    else:
        top_text += ('* pad-control ties (Decisions 41d / 44b / 46e): the %d constant pad-control pins (%s)\n'
                     '* are driven by tie cells INSIDE afe_dig (gf180mcu_fd_sc_mcu7t5v0__tiel / __tieh) and reach the top pins as plain nets: there is no device for them at this level.\n'
                     '.ends dbs_afe_top\n' % (len(ties), wrap(' '.join('%s = %s' % (p, '1' if r == 'VDD' else '0') for p, r in ties), 190).replace('\n+ ', '\n*   ')))
    top_file = (HDR_TOP + '* File dbs_afe_top.spice: the LVS top (L3), self-contained.  dbs_afe_top = afe_dig (black box) + bias_genc + 8 x afe_ch + supply devices%s;\n'
                % (' + pad-control ties' if opt.ties == 'resistor' else '; the 15 pad-control constants are pins of afe_dig')
                + '* afe_ch = 2 routing TGATEs (TGATE/TGATE.spice, wells on the analog strap) + amp_ch + adc_ch.  The cell definitions are the same text as in afe_chc.spice, adc_ch.spice, bias_genc.spice.\n\n'
                + '* ---------------- amplifier part\n' + cell('afe_chc') + '\n' + cell('fs_oneshot_c') + '\n' + ''.join(std_text[k] for k in sorted(std_text) if 'or2' in k) + '\n'
                + subckt_text('amp_ch', group_ports['amp_ch'], group_text['amp_ch'])
                + '\n* ---------------- ADC analog part\n' + cell('dac_sw') + '\n' + cell('cmp_p') + '\n' + cell('vhalf') + '\n' + cell('vrefs') + '\n' + ''.join(std_text[k] for k in sorted(std_text) if 'inv' in k) + '\n'
                + subckt_text('adc_ch', group_ports['adc_ch'], group_text['adc_ch'])
                + '\n* ---------------- routing switch (5 V devices), from TGATE/TGATE.spice\n' + cell('tgate')
                + '\n* ---------------- one channel\n' + subckt_text('afe_ch', chbits, ch_body)
                + '\n* ---------------- shared bias\n' + cell('bias_genc')
                + '\n* ---------------- digital macro\n' + dig_def
                + '\n* ---------------- top\n' + top_text)
    files = {'afe_chc.spice': amp_file, 'adc_ch.spice': adc_file, 'bias_genc.spice': bias_file, 'dbs_afe_top.spice': top_file}
    P('\nFILES written to %s' % os.path.relpath(opt.out, REPO))
    for fn, txt in files.items():
        ideal = [l for l in txt.split('\n') if re.match(r'[RCVIBE]', l, flags=re.I) and not (fn == 'dbs_afe_top.spice' and l.startswith('Rtie_'))]
        if ideal:
            die('%s contains ideal elements: %s' % (fn, ideal[:3]))
        if MIM_SIM in txt or 'ppolyf_u_3k' in txt:
            die('%s contains a device that is not an LVS device' % fn)
        open(os.path.join(opt.out, fn), 'w').write(txt)
        nd = len(re.findall(r'^X', txt, flags=re.M))
        P('  %-18s %6d lines, %5d X lines, subckts: %s' % (fn, txt.count('\n'), nd, ' '.join(re.findall(r'^\.subckt (\S+)', txt, flags=re.M | re.I))))
    # flat device total of the chip (for the layout device count)
    per = {c: len(flat[c][1]) for c in flat}
    std_n = {k: len(re.findall(r'^X', t, flags=re.M)) for k, t in std_text.items()}
    amp_n = per['afe_chc'] + per['fs_oneshot_c'] + sum(v for k, v in std_n.items() if 'or2' in k)
    adc_n = per['dac_sw'] + per['cmp_p'] + per['vhalf'] + per['vrefs'] + sum(v for k, v in std_n.items() if 'inv' in k)
    chn = amp_n + adc_n + 2 * per['tgate']
    P('\nFLAT DEVICE COUNT (device lines; m > 1 counted once): amp_ch %d, adc_ch %d, afe_ch %d, bias_genc %d; chip without the digital macro: 8 x %d + %d + %d supply devices = %d (+ %d tie %s)' % (
        amp_n, adc_n, chn, per['bias_genc'], chn, per['bias_genc'], len(supply_devs), 8 * chn + per['bias_genc'] + len(supply_devs), len(ties),
        'resistors' if opt.ties == 'resistor' else 'pins of afe_dig, no device in the top'))
    open(os.path.join(opt.out, 'mk_lvs_netlists.log'), 'w').write('\n'.join(LOG) + '\n')
    print('\n'.join(LOG))


if __name__ == '__main__':
    main()
