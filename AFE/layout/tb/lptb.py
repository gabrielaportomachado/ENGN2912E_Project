#!/usr/bin/env python3
"""lptb.py (LP kit, step 3): library of the golden post-layout testbenches AFE/layout/tb/tb_*.py.

Every check script takes   --netlist schematic | <path to a Magic PEX netlist written by flow.py pex>   --corner typ|ff85|ss-40|all   [--out DIR]
runs ngspice by the rules of common rule 8 (one thread per job through a job-local .spiceinit, abstol 1e-12 in transients with switching, whole logs kept, one re-run of an aborted
job with another step cap, machine-wide job slots) and writes   <out>/<check>.json  (machine readable, all corners merged)  +  <out>/<check>_<corner>.log.
Default <out>: AFE/layout/baseline for the schematic (the committed pre-layout baselines), AFE/layout/sim/post for an extracted netlist.  compare.py puts the two side by side.

THE ADAPTER (how a PEX netlist gets into testbenches that were written for the simulation netlists)
  * A PEX netlist is ONE flat subckt (the layout cell: amp_ch, adc_ch, bias_genc, TGATE ...) with Magic's own port order and node names.  The adapter reads its .subckt line and connects
    every port BY NAME (case-insensitive) to the pin of the same name of the layout cell (pin lists = AFE/layout/lvs/mk_lvs_netlists.log); a missing or an unknown port is an error.
    amp_ch is wrapped as the simulation cell afe_chc (fs = rst_amp, pkc = sw_rec_b, pkcb = sw_rec: the wiring of module afe_ch), so the testbench text is the same for both netlists.
  * Internal nodes that a check needs (summing nodes, v1, the DAC plate, the Cref node ...) are found from ANCHOR devices: MIM capacitors of a unique size (table ANCHORS).  The MIM
    terminal order is top plate first (Decision 46a, check_env.sh C3).
  * The operating point of an extracted amplifier cannot use the node guesses of the simulation testbenches (other node names; stage 1 is bistable).  `settle()` simulates the host
    sequence instead (supply ramp from 0 V, RST_AMP held, release, wait), writes every node voltage with `wrnodev` and feeds them back as .nodeset.  The schematic uses the same method
    when --settle is given; the baselines record that both methods give the same numbers.
  * `VSUBS` (Magic's name for a substrate that the cell does not tie to vss) is tied to ground and reported as a warning.
"""
import os, sys, re, json, time, hashlib, subprocess, shutil, argparse, math

HERE = os.path.dirname(os.path.abspath(__file__))
LAY = os.path.normpath(os.path.join(HERE, '..'))
AFE = os.path.normpath(os.path.join(LAY, '..'))
REPO = os.path.normpath(os.path.join(AFE, '..'))
AMP, ADC, REV = os.path.join(AFE, 'amp'), os.path.join(AFE, 'adc'), os.path.join(AFE, 'review')
sys.path.insert(0, os.path.join(LAY, 'scripts'))
from flow import Slot, SCRATCH                                           # noqa: the same job slots and scratch directory as flow.py

PDKNG = os.path.join(os.environ.get('PDK_ROOT', '/foss/pdks'), os.environ.get('PDK', 'gf180mcuD'), 'libs.tech/ngspice')
BASE = os.path.join(LAY, 'baseline')
POST = os.path.join(LAY, 'sim', 'post')
NG = shutil.which('ngspice') or '/foss/tools/ngspice/bin/ngspice'
# corner name -> (model file suffix, temperature C, VDD).  Amplifier corners = typ / ff85 / ss-40 (common rule 5); ADC D-phase corners = typ / ff-40 (3.6 V) / ss125 (3.0 V)
CORNERS = {'typ': ('typical', 27, 3.3), 'ff85': ('ff', 85, 3.3), 'ss-40': ('ss', -40, 3.3), 'ff-40': ('ff', -40, 3.6), 'ss125': ('ss', 125, 3.0),
           'ss-40x': ('ss', -40, 3.6)}        # ss-40x = the MIXED corner of the audit (M4): slow 3.3 V devices at -40 C / 3.6 V with the fastest standard-cell timing (ff_n40)
AMP_CORNERS = ('typ', 'ff85', 'ss-40')
ADC_CORNERS = ('typ', 'ff-40', 'ss125')
RFIX = {'typ': (5.23534e12, 5.23572e12), 'ff85': (4.68481e12, 6.22437e12), 'ss-40': (4.0999e12, 4.0999e12)}       # Decision 8 resistors (AFE/amp/sim/a4c_noise.log headers)
NSVRS = {'typ': 1.02771, 'ff85': 1.22173, 'ss-40': 0.813879}                                                     # start guess of the reset level (AFE/adc/scripts/x2lib.py NSVRS)
AMP_PINS = ['ref', 'sw_rec', 'sw_rec_b', 'rst_amp', 'vbn', 'vcm', 'vg1', 'vcmo', 'vg2', 'vrs', 'rec', 'out', 'vdd', 'vss']          # layout cell amp_ch (mk_lvs_netlists.log)
AFE_CHC_PINS = ['rec', 'ref', 'out', 'vdd', 'vss', 'vbn', 'vcm', 'vg1', 'vcmo', 'vg2', 'vrs', 'fs', 'pkc', 'pkcb']                  # simulation cell afe_chc
AMP_MAP = {'ref': 'ref', 'sw_rec': 'pkcb', 'sw_rec_b': 'pkc', 'rst_amp': 'fs', 'vbn': 'vbn', 'vcm': 'vcm', 'vg1': 'vg1', 'vcmo': 'vcmo', 'vg2': 'vg2', 'vrs': 'vrs', 'rec': 'rec', 'out': 'out',
           'vdd': 'vdd', 'vss': 'vss'}
ADC_PINS = (['rst_sw', 'tg_on', 'cmp_clk', 'dac_gdn'] + ['dac_gp[%d]' % i for i in range(11, -1, -1)] + ['dac_gn[%d]' % i for i in range(11, -1, -1)] + ['cmp_q', 'vin', 'vdd', 'vdd_cmp', 'vdd_dac', 'vss'])
BIAS_PINS = ['vbn', 'vcm_in', 'vg1', 'vcm_out', 'vg2', 'vrs', 'vdd', 'vss']
TGATE_PINS = ['out', 'c', 'cbar', 'in', 'vdd', 'vss']
MIM = 'cap_mim_2f0_m4m5_noshield'
# anchor = (probe name, MIM side um (drawn on the 5 nm grid; 1 % tolerance), which terminal [0 = top plate, 1 = bottom plate], optional condition on the OTHER terminal)
ANCHORS = {
    'amp_ch': [('vn', 61.15, 0, 'rec'), ('vp', 61.15, 0, 'ref'), ('vn2', 38.59, 0, None), ('v1', 38.59, 1, None), ('o1', 22.0, 0, None), ('o2', 31.465, 0, None), ('ct', 44.595, 0, None)],
    'adc_ch': [('t', (5.085, 5.0), 0, None), ('m', (5.085, 5.0), 1, None), ('vref', 59.07, 0, None), ('vcmd', 22.18, 0, None)],
    'bias_genc': [],
    'tgate': [],
}
SIM_PROBE = {'vn': 'xs1.vn', 'vp': 'xs1.vp', 'vn2': 'xs2.vn2', 'v1': 'v1', 'o1': 'xs1.xota.o1', 'o2': 'xs2.xota2.o2'}        # the same nodes inside the simulation cell afe_chc


class TbError(Exception):
    pass


# ------------------------------------------------------------------------------------------------ REC pad load (REVIEW.md R13, Decision 53)
REC_LOAD = {'file': None}        # --rec-load <spice file>: subckt `recpad rec vdd vss` that hangs on the amplifier input node `rec`; None (default) = nothing is added, every netlist is unchanged


def set_rec_load(path):
    """--rec-load: the pad model on the `rec` node of the amplifier benches (amp_bench, ampch_bench, tb_amp_loop).  Default none = unchanged behaviour (baselines and gates byte-identical)."""
    if not path:
        REC_LOAD['file'] = None
        return
    f = os.path.abspath(path)
    if not os.path.isfile(f) or not re.search(r'(?im)^\.subckt\s+recpad\s', open(f, errors='replace').read()):
        raise TbError('--rec-load %s: no such file or it does not define `.subckt recpad rec vdd vss`' % path)
    REC_LOAD['file'] = f


def rec_models(corner):
    """model lines of the pad (PDK diodes of the corner, MOS-capacitor corner) + the include of the pad file; [] without --rec-load"""
    if not REC_LOAD['file']:
        return []
    c = CORNERS[corner][0]
    return ['.lib %s/sm141064.ngspice diode_%s' % (PDKNG, c), '.lib %s/sm141064.ngspice moscap_%s' % (PDKNG, c), '.include %s' % REC_LOAD['file']]


def rec_inst(node='rec', inst='Xrecpad', vdd='vdd'):
    """the pad on the amplifier input: chip VDD / VSS (= 0) as pad supplies; [] without --rec-load"""
    return ['%s %s %s 0 recpad' % (inst, node, vdd)] if REC_LOAD['file'] else []


def rec_patch(net):
    """tb_amp_loop.py builds its own bench (two channel copies, rec1 / rec2): with --rec-load both copies get the pad.  Any other netlist is returned unchanged."""
    if REC_LOAD['file'] and 'vo=$&onoise_total' in net:
        # ngspice 46 returns onoise_total = nan as soon as a PDK diode is in the circuit (its spectrum is finite: checked); integrate the spectrum instead (log trapezoid, 100 points per
        # decade as in `noise ... dec 100`; vo_ng keeps the simulator's own total, finite without diodes: AFE/layout/sim/recpad/noise_check.md)
        net = net.replace('setplot noise2\necho RESULT gm_db=$&ac1.gm vo=$&onoise_total',
                          'setplot noise1\nlet s2 = onoise_spectrum*onoise_spectrum*frequency\nlet n2 = length(s2)\n'
                          'let vint = sqrt((mean(s2)*n2 - 0.5*(s2[0] + s2[n2-1]))*ln(10)/100)\necho RESULT gm_db=$&ac1.gm vo=$&vint vo_ng=$&noise2.onoise_total')
        return net
    if not REC_LOAD['file'] or 'stage-1 loop gain' not in net.split('\n', 1)[0] or 'Xrecpad' in net:
        return net
    corner = re.search(r'\[(typ|ff85|ss-40)\]', net.split('\n', 1)[0]).group(1)
    out = []
    for ln in net.split('\n'):
        out.append(ln)
        if ln.startswith('Xch2 '):
            out += rec_inst('rec1', 'Xrecpad') + rec_inst('rec2', 'Xrecpad_2')
        if ln.startswith('* LP golden testbench') and 'sm141064.ngspice diode_' not in net:        # the schematic loop bench gets the models through amp_includes already
            out += rec_models(corner)
    return '\n'.join(out)


def rec_tag():
    return ('_rl' + sha(REC_LOAD['file'])[:6]) if REC_LOAD['file'] else ''


# ------------------------------------------------------------------------------------------------ SPICE text helpers
def logical(path):
    out, cur = [], ''
    for ln in open(path, errors='replace'):
        ln = ln.rstrip('\n')
        if ln.startswith('+'):
            cur += ' ' + ln[1:]
        else:
            out.append(cur)
            cur = ln
    out.append(cur)
    return [x for x in out if x.strip()]


def um(tok):
    m = re.match(r'^([-+]?[0-9.]+(?:e[-+]?\d+)?)([a-z]?)', tok.lower())
    return float(m.group(1)) * {'u': 1.0, 'm': 1e3, 'n': 1e-3, 'p': 1e-6, '': 1e6}[m.group(2)]


def subckts(path):
    """{name lower: (name, ports, [element lines])} of a netlist file"""
    res, name = {}, None
    for ln in logical(path):
        s = ln.strip()
        lo = s.lower()
        if lo.startswith('.subckt'):
            t = s.split()
            name = t[1].lower()
            res[name] = (t[1], [x for x in t[2:] if '=' not in x and x.lower() != 'params:'], [])
        elif lo.startswith('.ends'):
            name = None
        elif name and s[0] not in '*.':
            res[name][2].append(s)
    return res


def sha(path):
    h = hashlib.sha1()
    h.update(open(path, 'rb').read())
    return h.hexdigest()[:12]


class Dut:
    """one cell under test: the simulation netlists (`schematic`) or a PEX netlist"""

    def __init__(self, cell, netlist, pins, as_cell=None, pinmap=None):
        self.cell, self.netlist, self.pins = cell, netlist, pins
        self.pex = (netlist != 'schematic')
        self.warnings = []
        self.probes = {}                    # probe name -> node name INSIDE the PEX subckt
        self.as_cell = as_cell or cell      # name of the subckt that the testbench instantiates
        self.pinmap = pinmap or {p: p for p in pins}
        self.tag = 'sch'
        self.models = set()
        if self.pex:
            if not os.path.isfile(netlist):
                raise TbError('netlist %s does not exist' % netlist)
            self.netlist = os.path.abspath(netlist)
            self.tag = 'pex' + sha(self.netlist)
            subs = subckts(self.netlist)
            cand = [k for k in subs if k == cell.lower()] or ([k for k in subs] if len(subs) == 1 else [])
            if not cand:
                raise TbError('%s defines the subckts %s: none is %s (the PEX netlist must come from `flow.py pex --top %s`)' % (netlist, sorted(subs), cell, cell))
            self.subname, self.ports, self.elems = subs[cand[0]]
            low = [p.lower() for p in self.ports]
            miss = [p for p in pins if p.lower() not in low]
            extra = [p for p in self.ports if p.lower() not in [q.lower() for q in pins]]
            if miss or extra:
                raise TbError('%s subckt %s: ports %s; missing %s; not pins of %s: %s' % (netlist, self.subname, ' '.join(self.ports), miss, cell, extra))
            self._anchors()
            body = ' '.join(self.elems)
            self.models = set(x.lower() for x in re.findall(r'\b(cap_nmos_03v3|rm[1-4]|ppolyf_u_1k|nfet_06v0_nvt|%s)\b' % MIM, body, flags=re.I))
            self.vsubs = bool(re.search(r'\bVSUBS\b', body)) and 'vsubs' not in low
            if self.vsubs:
                self.warnings.append('the substrate node VSUBS is not tied to vss inside %s (no substrate tap on vss?): tied to ground in the testbench' % cell)

    def _anchors(self):
        mims = []
        for s in self.elems:
            t = s.split()
            nodes = [x for x in t[1:] if '=' not in x]
            if nodes[-1].lower() != MIM:
                continue
            par = dict(x.lower().split('=') for x in t if '=' in x)
            mims.append((nodes[0], nodes[1], um(par['c_width']), um(par['c_length'])))
        for name, size, term, other in ANCHORS.get(self.cell, []):
            w, l = size if isinstance(size, tuple) else (size, size)
            hit = [m for m in mims if (abs(m[2] - w) <= 0.01 * w and abs(m[3] - l) <= 0.01 * l) or (abs(m[2] - l) <= 0.01 * l and abs(m[3] - w) <= 0.01 * w and w != l)]
            if other:
                hit = [m for m in hit if m[1 - term].lower() == other]
            nets = sorted(set(m[term] for m in hit))
            if len(nets) == 1:
                self.probes[name] = nets[0]
            else:
                self.warnings.append('anchor for node %s (MIM %g x %g um%s) is %s: probe not available' % (name, w, l, ', other plate on %s' % other if other else '',
                                                                                                           'missing' if not nets else 'not unique (%s)' % nets))

    def wrapper(self):
        """SPICE text: include of the PEX netlist + the subckt `as_cell` with the simulation pin order around it"""
        if not self.pex:
            return []
        conn = dict((p.lower(), self.pinmap[q]) for q in self.pins for p in self.ports if p.lower() == q.lower())
        inc, sub = self.netlist, self.subname
        if self.as_cell.lower() == self.subname.lower():           # the layout cell has the name of the simulation cell: use a copy with the subckt renamed
            sub = self.subname + '__pex'
            inc = os.path.join(SCRATCH, 'tb', 'ren_%s_%s.spice' % (self.cell, self.tag))
            os.makedirs(os.path.dirname(inc), exist_ok=True)
            txt = open(self.netlist, errors='replace').read()
            txt = re.sub(r'(?im)^(\.subckt\s+)%s\b' % re.escape(self.subname), r'\g<1>' + sub, txt)
            txt = re.sub(r'(?im)^(\.ends)\s+%s\b' % re.escape(self.subname), r'\g<1> ' + sub, txt)
            open(inc, 'w').write(txt)
        L = ['* ---- device under test: PEX netlist %s (subckt %s, ports by name)' % (self.netlist, self.subname), '.include %s' % inc]
        L += ['.subckt %s %s' % (self.as_cell, ' '.join(self.sim_pins)), 'Xpex %s %s' % (' '.join(conn[p.lower()] for p in self.ports), sub), '.ends %s' % self.as_cell]
        if self.vsubs:
            L += ['.global VSUBS', 'Rvsubs VSUBS 0 1m']
        return L

    def taps(self, names, inst='xch'):
        """-> (netlist lines, {probe: clean top-level node}).  Each available probe is copied to the node p_<probe> by an ideal unity VCVS, because Magic node names (a_12_34#) cannot be
        used in ngspice control-language expressions."""
        L, m = [], {}
        for n in names:
            h = self.node(n, inst)
            if h:
                L.append('Ep_%s p_%s 0 %s 0 1' % (n, n, h))
                m[n] = 'p_%s' % n
        return L, m

    def node(self, probe, inst='xch'):
        """hierarchical node name of a probe for an instance called `inst`"""
        if self.pex:
            if probe not in self.probes:
                return None
            return ('%s.xpex.%s' % (inst, self.probes[probe])).lower()
        return ('%s.%s' % (inst, SIM_PROBE[probe])).lower() if probe in SIM_PROBE else None


def amp_dut(netlist, prdiff=False):
    """prdiff (schematic only): the design netlists with junction area / perimeter on the six pseudo-resistor devices (AFE/amp/spice/pseudoR.spice gives them none; every extracted netlist
    has them).  A what-if copy in the scratch directory, the design file is not touched."""
    d = Dut('amp_ch', strip_pr(netlist, prdiff), AMP_PINS, as_cell='afe_chc', pinmap=AMP_MAP)
    d.sim_pins = AFE_CHC_PINS
    d.prdiff = bool(prdiff) and not d.pex
    d.convention = 'junction' if prdiff else 'design'
    if d.prdiff:
        d.tag = 'schprdiff'
    d.tag += rec_tag()
    return d


PR_SIZE = (0.22, 0.5)          # W, L um of the pseudo-resistor transistors (PR1W / PR1L, PR2W / PR2L of AFE/amp/spice/a4c_params.spice); no other device of amp_ch has this size


def strip_pr(netlist, junction):
    """PEX netlist in the DESIGN convention: a copy (scratch) in which the pseudo-resistor transistors (pfet_03v3 0.22u / 0.5u) have no ad / as / pd / ps, as in the design netlists.
    WHY (LP finding, AFE/layout/sim/lp_prdiff_study.log): with junction area on these six devices the simulated pseudo-resistance rises far above the leakage resistance of the MIM capacitors,
    the 0.2 Hz corner disappears and an electrode offset of 10 mV rails the output at typ and -40 C.  Both are model floors.  Every approved number was made without the area, so the gates
    of ACCEPT.md use this convention and the junction convention (`--junction`) is reported next to it."""
    if netlist == 'schematic' or junction:
        return netlist
    src = os.path.abspath(netlist)
    out = os.path.join(SCRATCH, 'tb', 'prstrip_%s.spice' % sha(src))
    os.makedirs(os.path.dirname(out), exist_ok=True)
    n, L = 0, []
    for ln in logical(src):
        t = ln.split()
        if t and t[0][0] in 'xX' and 'pfet_03v3' in [x.lower() for x in t]:
            par = dict(x.lower().split('=') for x in t if '=' in x)
            if 'w' in par and abs(um(par['w']) - PR_SIZE[0]) < 0.006 and abs(um(par['l']) - PR_SIZE[1]) < 0.006:
                t = [x for x in t if x.lower().split('=')[0] not in ('ad', 'as', 'pd', 'ps')]
                n += 1
        L.append(' '.join(t) if n and t and t[0][0] in 'xX' else ln)
    open(out, 'w').write('* DESIGN-convention copy of %s: %d pseudo-resistor transistors without junction area (lptb.strip_pr)\n' % (src, n) + '\n'.join(L) + '\n')
    strip_pr.count = n
    return out


def pseudo_r_with_diffusion():
    src = open(os.path.join(AMP, 'spice', 'pseudoR.spice')).read()
    a = src.index('.subckt pseudo_r_fg')
    b = src.index('.ends', a)
    blk = re.sub(r'(?m)^(Xm[12] .*pfet_03v3 W=\{W\} L=\{L\} nf=1)[ \t]*$', r'\1 ad={W*0.18u} as={W*0.18u} pd={2*(W+0.18u)} ps={2*(W+0.18u)}', src[a:b])
    if blk.count('ad={W*0.18u}') != 2:
        raise TbError('pseudoR.spice: the two devices of pseudo_r_fg were not found')
    fn = os.path.join(SCRATCH, 'tb', 'pseudoR_prdiff.spice')
    os.makedirs(os.path.dirname(fn), exist_ok=True)
    open(fn, 'w').write('* WHAT-IF copy of AFE/amp/spice/pseudoR.spice (lptb.py): pseudo_r_fg with junction area W x 0.18 um and perimeter 2 (W + 0.18 um), the DIFF = 1 formula of the other devices\n' + src[:a] + blk + src[b:])
    return fn


def bias_dut(netlist):
    d = Dut('bias_genc', netlist, BIAS_PINS, as_cell='bias_genc')
    d.sim_pins = BIAS_PINS
    return d


def tgate_dut(netlist):
    d = Dut('TGATE', netlist, TGATE_PINS, as_cell='TGATE')
    d.sim_pins = TGATE_PINS
    return d


def adc_env(netlist):
    """environment for AFE/adc/scripts/x2lib.py (set BEFORE importing it).  schematic: the four design cells (nothing set).  PEX: a wrapper file around the extracted adc_ch with the DAC plate
    and the Cref node (found through their MIM anchors) exported as two extra pins, X2_ADC_INC = that file, X2_ADC_CELL = the wrapper."""
    if netlist == 'schematic':
        os.environ.pop('X2_ADC_INC', None)
        os.environ.pop('X2_ADC_CELL', None)
        return None
    d = Dut('adc_ch', netlist, ADC_PINS)
    miss = [n for n in ('t', 'vref') if n not in d.probes]
    if miss:
        raise TbError('%s: the anchor capacitors of %s were not found (%s); the closed-loop replay needs the DAC plate and the Cref node' % (netlist, miss, '; '.join(d.warnings)))
    f = os.path.join(SCRATCH, 'tb', 'adc_x2_%s.spice' % d.tag)
    os.makedirs(os.path.dirname(f), exist_ok=True)
    txt = open(d.netlist, errors='replace').read()
    sub = d.subname + '__pex'
    txt, n1 = re.subn(r'(?im)^(\.subckt\s+)%s\b([^\n]*)$' % re.escape(d.subname), lambda m: '%s%s%s %s %s' % (m.group(1), sub, m.group(2), d.probes['t'], d.probes['vref']), txt)
    txt = re.sub(r'(?im)^(\.ends)\s+%s\b' % re.escape(d.subname), r'\g<1> ' + sub, txt)
    if n1 != 1 or re.search(r'(?im)^\.subckt[^\n]*\n\+', txt):
        raise TbError('%s: unexpected .subckt line (continuation line or several subckts)' % netlist)
    names = ['rst_sw', 'tg_on', 'cmp_clk', 'dac_gdn'] + ['gp%d' % i for i in range(11, -1, -1)] + ['gn%d' % i for i in range(11, -1, -1)] + ['cmp_q', 'vin', 'vdd', 'vdd_cmp', 'vdd_dac', 'vss']
    conn = {p.lower(): q for p, q in zip(ADC_PINS, names)}
    L = ['* wrapper of lptb.py around the extracted ADC cell %s for the X2 closed-loop replay (ports by name; plate %s and Cref node %s exported)' % (d.netlist, d.probes['t'], d.probes['vref']), txt,
         '.subckt adc_ch_x2 %s t vref' % ' '.join(names), 'Xpex %s t vref %s' % (' '.join(conn[p.lower()] for p in d.ports), sub), '.ends adc_ch_x2']
    if d.vsubs:
        L += ['.global VSUBS', 'Rvsubs VSUBS 0 1m']
    open(f, 'w').write('\n'.join(L) + '\n')
    os.environ['X2_ADC_INC'] = f
    os.environ['X2_ADC_CELL'] = 'adc_ch_x2'
    return d


def amp_x2_env(netlist, corner, log=None):
    """environment for x2lib.py when the amplifier is an extracted amp_ch (design convention): a wrapper file defining afe_chc_pex (X2_AMP_INC, X2_AMP_SUBCKT) and the node guesses of a
    power-up run (X2_AMP_NODESET).  schematic: the three variables are removed."""
    for k in ('X2_AMP_INC', 'X2_AMP_SUBCKT', 'X2_AMP_NODESET'):
        os.environ.pop(k, None)
    if netlist == 'schematic':
        if AMP_VARIANT != 'native':
            os.environ['X2_AMP_INC'] = ':'.join(os.path.join(AMP, 'spice', amp_file(f) + '.spice') for f in ('ota1', 'ota2', 'stage1c', 'stage2c', 'afe_chc'))
        return None
    d = Dut('amp_ch', strip_pr(netlist, False), AMP_PINS, as_cell='afe_chc_pex', pinmap=AMP_MAP)
    d.sim_pins = AFE_CHC_PINS
    f = os.path.join(SCRATCH, 'tb', 'amp_x2_%s.spice' % d.tag)
    os.makedirs(os.path.dirname(f), exist_ok=True)
    open(f, 'w').write('\n'.join(d.wrapper()) + '\n')
    d2 = amp_dut(netlist)                               # same netlist as afe_chc for the power-up run
    ns = settle(corner, d2, log)
    nf = os.path.join(SCRATCH, 'tb', 'amp_x2_%s_%s.ns' % (d.tag, corner))
    open(nf, 'w').write('\n'.join(l.replace('v(xch.', 'v({x}.') for l in ns.split('\n') if l.startswith('.nodeset v(xch.')) + '\n')
    os.environ.update(X2_AMP_INC=f, X2_AMP_SUBCKT='afe_chc_pex', X2_AMP_NODESET=nf)
    return d


def run_script(argv, env_extra=None, log=None):
    """runs one of the existing analysis scripts as a child process (its ngspice jobs follow its own slot rules) -> stdout text"""
    env = dict(os.environ)
    env.update(env_extra or {})
    p = subprocess.run([sys.executable] + argv, capture_output=True, text=True, env=env, stdin=subprocess.DEVNULL)
    if log:
        for ln in (p.stdout + p.stderr).split('\n'):
            if ln.startswith(('RESULT', 'S1REPORT', 'S4 ', 'S5 ', '#')) or 'FAILED' in ln or 'Traceback' in ln or 'Error' in ln:
                log(ln[:1500])
    return p.stdout + p.stderr


X2_PREFIX = 'lp_top'                                    # X2_LOG_PREFIX of the wrappers: the x2_*.py scripts then write sim/lp_top_* and leave the X2 / F1 evidence logs alone


def x2_collect(dest, check, corner):
    """moves the logs that an x2_*.py child wrote under AFE/adc/sim/lp_top_* into dest as <check>_x2_<rest> and removes its bookkeeping files"""
    sim = os.path.join(ADC, 'sim')
    for f in sorted(os.listdir(sim)):
        if not f.startswith(X2_PREFIX + '_'):
            continue
        src = os.path.join(sim, f)
        if f.endswith(('_done.txt', '_summary.log')):
            os.remove(src)
        elif ('_%s' % corner) in f:
            os.replace(src, os.path.join(dest, '%s_x2_%s' % (check, f[len(X2_PREFIX) + 1:])))


def model_lines(corner, extra=()):
    c = CORNERS[corner][0]
    L = ['.include %s/spice/models_%s.spice' % (AMP, c)]
    if 'cap_nmos_03v3' in extra:
        L.append('.lib %s/sm141064.ngspice moscap_%s' % (PDKNG, c))
    return L


AMP_VARIANT = os.environ.get('AFE_AMP_VARIANT', 'native')      # native | rvt | nodnw: the follower of ACCEPT.md ladder N (LP step 6); only the SCHEMATIC files change, a PEX netlist has its own devices
VARIANT_FILES = {'native': {}, 'rvt': {'ota2': 'ota2_rvt', 'afe_chc': 'afe_chc_rvt'}, 'nodnw': {'ota2': 'ota2_rvt_nodnw', 'afe_chc': 'afe_chc_rvt'}}[AMP_VARIANT]
if AMP_VARIANT != 'native':
    os.environ['X2_AMP_INC'] = ':'.join(os.path.join(AMP, 'spice', VARIANT_FILES.get(f, f) + '.spice') for f in ('ota1', 'ota2', 'stage1c', 'stage2c', 'afe_chc'))


def amp_file(f):
    return VARIANT_FILES.get(f, f)


def amp_includes(corner, dut, more=()):
    files = [amp_file(f) for f in ['pseudoR', 'ota1_params', 'afe_params', 'a4c_params', 'ota1', 'ota2', 'bias_genc', 'stage1c', 'stage2c', 'afe_chc', 'fs_oneshot_c', 'src_randles']] + list(more)
    if dut.pex:
        files = [f for f in files if f not in ('afe_chc', 'afe_chc_rvt')]
    L = model_lines(corner, dut.models) + ['.include %s/spice/%s.spice' % (AMP, f) for f in files]
    if getattr(dut, 'prdiff', False):
        L = [('.include ' + pseudo_r_with_diffusion()) if x.endswith('/pseudoR.spice') else x for x in L]
    return L + rec_models(corner) + dut.wrapper()


STD_SPICE = os.path.join(os.environ.get('PDK_ROOT', '/foss/pdks'), os.environ.get('PDK', 'gf180mcuD'), 'libs.ref/gf180mcu_fd_sc_mcu7t5v0/spice/gf180mcu_fd_sc_mcu7t5v0.spice')


def std_cell(name):
    """the .SUBCKT block of one standard cell of the PDK library (pins: ... VDD VNW VPW VSS)"""
    txt = open(STD_SPICE, errors='replace').read()
    m = re.search(r'(?ims)^\.subckt %s .*?^\.ends[^\n]*$' % re.escape(name), txt)
    if not m:
        raise TbError('standard cell %s not found in %s' % (name, STD_SPICE))
    return m.group(0).split('\n')


def ampch_dut(netlist, prdiff=False):
    """the layout cell amp_ch itself (pins of AFE/layout/lvs: ref sw_rec sw_rec_b rst_amp vbn vcm vg1 vcmo vg2 vrs rec out vdd vss) as subckt amp_ch_tb.
    schematic = afe_chc + fs_oneshot_c + the OR2 standard cell wired as in module afe_ch of AFE/top/dbs_afe_top.v."""
    d = Dut('amp_ch', strip_pr(netlist, prdiff), AMP_PINS, as_cell='amp_ch_tb')
    d.sim_pins = AMP_PINS
    d.prdiff = bool(prdiff) and not d.pex
    d.convention = 'junction' if prdiff else 'design'
    d.level = 'amp_ch'
    if d.prdiff:
        d.tag = 'schprdiff'
    d.tag += rec_tag()
    return d


def ampch_includes(corner, dut, more=()):
    L = amp_includes(corner, dut, more)
    if not dut.pex:
        L += std_cell('gf180mcu_fd_sc_mcu7t5v0__or2_1')
        L += ['.subckt amp_ch_tb ' + ' '.join(AMP_PINS), 'Xos sw_rec fs_os vbn vdd vss fs_oneshot_c', 'Xor fs_os rst_amp fs vdd vdd vss vss gf180mcu_fd_sc_mcu7t5v0__or2_1',
              'Xamp rec ref out vdd vss vbn vcm vg1 vcmo vg2 vrs fs sw_rec_b sw_rec afe_chc', '.ends amp_ch_tb']
    return L


def ampch_node(dut, probe, inst='xch'):
    if dut.pex:
        return dut.node(probe, inst)
    if probe == 'ct':
        return '%s.xos.t' % inst
    return ('%s.xamp.%s' % (inst, SIM_PROBE[probe])) if probe in SIM_PROBE else None


def ampch_bench(corner, dut, title, vdd='Vdd vdd 0 {VSUP}', rst='Vrst rst_amp 0 0', sw=('Vsw sw_rec 0 {VSUP}', 'Vswb sw_rec_b 0 0'), vd='Vd vd 0 dc 0', vos=('Vosr vosr 0 0', 'Vosf vosf 0 0'),
                load='CADC out 0 20f', opts='abstol=1e-12 chgtol=1e-17', extra=(), params=None, probes=()):
    """bench around the layout cell: real bias cell, Randles electrode pair on the 1.65 V tissue node, record switch state given by sw_rec / sw_rec_b (HIGH / LOW = record, park off)."""
    cname, T, vsup = CORNERS[corner]
    p = {'VSUP': vsup, 'LOOPTEST': 0}
    p.update(params or {})
    L = ['* LP golden testbench (amp_ch level): %s  [%s, %s]' % (title, corner, 'schematic' if not dut.pex else dut.netlist)] + ampch_includes(corner, dut)
    L += ['.options gmin=1e-16 %s reltol=1e-4 itl1=500 itl4=500' % opts, '.temp %g' % T] + ['.param %s=%s' % kv for kv in p.items()]
    L += [vdd, 'Xbias vbn vcm vg1 vcmo vg2 vrs vdd 0 bias_genc', rst, sw[0], sw[1], 'Vtis tis 0 1.65', vd, vos[0], vos[1], 'Xsrc vd tis rec ref vosr vosf src_randles',
          'Xch ref sw_rec sw_rec_b rst_amp vbn vcm vg1 vcmo vg2 vrs rec out vdd 0 amp_ch_tb', load] + rec_inst() + list(extra)
    tp = {}
    for n in probes:
        h = ampch_node(dut, n)
        if h:
            L.append('Ep_%s p_%s 0 %s 0 1' % (n, n, h))
            tp[n] = 'p_%s' % n
    return L, tp


def read_wr(path):
    """ngspice wrdata file (pairs of x, y columns) -> (x, [y columns])"""
    import numpy as np
    a = np.loadtxt(path)
    return a[:, 0], [a[:, i] for i in range(1, a.shape[1], 2)]


NATIVE_NS = ('.nodeset v(rec)=1.65 v(vrs)={NSVRS} v(xch.gm1)=1.85 v(xch.gm2)=2.55 v(vbn)=0.65 v(xbias.a)=2.4 v(vcm)=1.65 v(vg1)=1.85 v(vcmo)=1.65 v(vg2)=2.55\n'
             '.nodeset v(xch.xs1.vn)=1.65 v(xch.xs1.vp)=1.65 v(xch.xs1.vng)=1.65 v(xch.v1)=1.65 v(xch.xs1.xota.o1)=0.78 v(xch.xs1.xota.d1)=0.78 v(xch.xs1.xota.tail)=2.55 v(xch.ibias1)=2.4\n'
             '.nodeset v(xch.xs1.xr1.m)=1.65 v(xch.xs1.xr2.m)=1.65 v(xch.xs2.xr.m)=1.65 v(xch.xs2.vn2)=1.65 v(xch.xs2.vng2)=1.65 v(out)=1.65 v(xch.xs2.xota2.o2)=2.45 v(xch.xs2.xota2.d1)=2.6 '
             'v(xch.xs2.xota2.tail)=1.0')              # the node guesses of AFE/amp/tb/tb_a4c_*.spice


def amp_bench(corner, dut, title, params=None, vdd=None, fs='Vfs fs 0 0', vd='Vd vd 0 dc 0 ac 1', vos=('Vosr vosr 0 0', 'Vosf vosf 0 0'), park=None, load='CADC out 0 20f',
              opts='abstol=1e-20', extra=(), nodeset='native', more_inc=(), temp=None):
    """the bench of AFE/amp/tb/tb_a4c_ac.spice (supply, real bias cell, Randles electrode pair on a 1.65 V tissue node, park off, 20 fF load), element for element"""
    cname, T, vsup = CORNERS[corner]
    p = {'VSUP': vsup, 'NSVRS': NSVRS.get(corner, 1.0), 'LOOPTEST': 0}
    p.update(params or {})
    L = ['* LP golden testbench: %s  [%s, %s]' % (title, corner, 'schematic' if not dut.pex else dut.netlist)] + amp_includes(corner, dut, more_inc)
    L += ['.options gmin=1e-16 %s reltol=1e-4 itl1=500 itl4=500' % opts, '.temp %g' % (T if temp is None else temp)] + ['.param %s=%s' % kv for kv in p.items()]
    L += [vdd or 'Vdd vdd 0 {VSUP}', 'Xbias vbn vcm vg1 vcmo vg2 vrs vdd 0 bias_genc', fs, 'Vtis tis 0 1.65', vd, vos[0], vos[1], 'Xsrc vd tis rec ref vosr vosf src_randles']
    L += list(park or ['Vpkc pkc 0 0', 'Vpkcb pkcb 0 {VSUP}'])
    L += ['Xch rec ref out vdd 0 vbn vcm vg1 vcmo vg2 vrs fs pkc pkcb afe_chc', load] + rec_inst() + list(extra)
    if nodeset == 'native':
        if dut.pex:
            raise TbError('the native node guesses only exist for the schematic')
        L.append(NATIVE_NS)
    elif nodeset:
        L.append(nodeset)
    return L


# ------------------------------------------------------------------------------------------------ job runner
def run_ng(jobs, tag, npar=3, wall=7200.0, retry=None, log=None):
    """jobs: [(name, netlist text)] -> {name: dict(ok, out, wall, abort, dir)}.  One thread per job (job-local .spiceinit), machine-wide slots, waited by PID, whole log kept.
    retry: optional function(name, text) -> new text; an aborted job is re-run ONCE with it (common rule 8)."""
    d = os.path.join(SCRATCH, 'tb', tag)
    os.makedirs(d, exist_ok=True)
    open(os.path.join(d, '.spiceinit'), 'w').write('set num_threads=1\n')
    todo, run, res = list(jobs), [], {}
    tried = set()
    while todo or run:
        while todo and len(run) < npar:
            name, net = todo.pop(0)
            fn, lg = os.path.join(d, name + '.spice'), os.path.join(d, name + '.log')
            net = rec_patch(net)
            open(fn, 'w').write(net)
            sl = Slot()
            sl.__enter__()
            p = subprocess.Popen([NG, '-b', fn], cwd=d, stdout=open(lg, 'w'), stderr=subprocess.STDOUT, stdin=subprocess.DEVNULL, env=dict(os.environ, OMP_NUM_THREADS='1'))
            run.append((p, name, lg, time.time(), sl, net))
        time.sleep(0.2)
        for r in list(run):
            p, name, lg, t0, sl, net = r
            if p.poll() is None:
                if time.time() - t0 < wall:
                    continue
                p.kill()
                p.wait()
            run.remove(r)
            sl.__exit__()
            txt = open(lg, errors='replace').read().replace('\r', '\n')
            ab = ' | '.join(l.strip()[:200] for l in txt.split('\n') if re.search(r'imestep too small|trouble with|ingular matrix|aborted|No convergence|rror', l))[:600]
            ok = (p.returncode == 0) and 'imestep too small' not in txt
            if not ok and retry and name not in tried:
                tried.add(name)
                todo.append((name, retry(name, net)))
                if log:
                    log('   job %s aborted (%s): re-run once with another step cap' % (name, ab[:120]))
                continue
            res[name] = dict(ok=ok, out=txt, wall=time.time() - t0, abort=ab, dir=d, retried=name in tried)
            if log:
                log('   job %s: exit %s, %.0f s%s' % (name, p.returncode, time.time() - t0, (' MSG ' + ab[:200]) if ab else ''))
    return res


def results(txt, key='RESULT'):
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


def scale_tmax(net, f=0.9):
    """re-run rule: another maximum time step (the 4th number of the .tran line / tmax=... tokens)"""
    def rep(m):
        t = m.group(0).split()
        if len(t) >= 5:
            mm = re.match(r'^([0-9.eE+-]+)([a-zA-Z]*)$', t[4])
            if mm:
                t[4] = '%.4g%s' % (float(mm.group(1)) * f, mm.group(2))
        return ' '.join(t)
    return re.sub(r'(?im)^\s*\.?tran .*$', rep, net)


# ------------------------------------------------------------------------------------------------ operating point of the amplifier
SETTLE_T = {'typ': (0.05, 0.6), 'ff85': (0.05, 0.6), 'ss-40': (1.2, 0.8)}        # (time the bias needs before RST_AMP counts, settling time after the release) [s]; ss -40: bias start-up 0.6 s with one channel


def settle(corner, dut, log=None, extra=(), load='CADC out 0 20f', key=''):
    """host power-up sequence -> .nodeset text for the instance names of amp_bench (xch, xbias, xsrc).  Cached in the scratch directory."""
    tb0, tset = SETTLE_T.get(corner, (1.2, 0.8))
    cache = os.path.join(SCRATCH, 'tb', 'settle_%s_%s_%s.ns' % (dut.tag, corner, hashlib.sha1((key + load + ''.join(extra) + rec_tag()).encode()).hexdigest()[:8]))
    if os.path.exists(cache):
        return open(cache).read()
    trel = tb0 + 0.1
    tstop = trel + tset
    nv = os.path.join(SCRATCH, 'tb', 'settle', '%s_%s.nodev' % (dut.tag, corner))
    os.makedirs(os.path.dirname(nv), exist_ok=True)
    L = amp_bench(corner, dut, 'power-up sequence: VDD ramp 1 ms, RST_AMP held until %.2f s, release, settle until %.2f s' % (trel, tstop), opts='abstol=1e-12 chgtol=1e-17',
                  vdd='Vdd vdd 0 PWL(0 0 1m {VSUP})', fs='Vfs fs 0 PWL(0 0 1m {VSUP} %g {VSUP} %g 0)' % (trel, trel + 1e-6), vd='Vd vd 0 dc 0', nodeset=None, extra=extra, load=load)
    L += ['.control', 'tran 1m %g 0 1m uic' % tstop, 'wrnodev %s' % nv, 'print v(out)[length(v(out))-1]', 'echo SETTLE_DONE', 'quit', '.endc', '.end']
    r = run_ng([('settle_%s_%s' % (dut.tag, corner), '\n'.join(L) + '\n')], 'settle', retry=lambda n, t: t.replace('tran 1m ', 'tran 0.7m ').replace(' 0 1m uic', ' 0 0.7m uic'), log=log)
    r = list(r.values())[0]
    if 'SETTLE_DONE' not in r['out'] or not os.path.exists(nv):
        raise TbError('the power-up run did not finish (%s): %s' % (corner, r['abort'] or r['out'][-300:]))
    ns = []
    for ln in open(nv):
        m = re.match(r'\s*\.ic\s+v\(([^)]+)\)\s*=\s*([-+0-9.eE]+)', ln)
        if m and not m.group(1).lower().endswith('#branch'):
            ns.append('.nodeset v(%s)=%s' % (m.group(1), m.group(2)))
    if len(ns) < 10:
        raise TbError('wrnodev wrote %d node voltages' % len(ns))
    txt = '\n'.join(ns)
    open(cache, 'w').write(txt)
    return txt


# ------------------------------------------------------------------------------------------------ results
def out_dir(netlist, out=None):
    d = out or (BASE if netlist == 'schematic' else POST)
    os.makedirs(d, exist_ok=True)
    return d


def save(check, netlist, corner, values, logtext, out=None, info=None, limits_note=None):
    """merge one corner into <out>/<check>.json and write <out>/<check>_<corner>.log"""
    d = out_dir(netlist, out)
    jf = os.path.join(d, check + '.json')
    doc = {'check': check, 'corners': {}}
    if os.path.exists(jf):
        try:
            doc = json.load(open(jf))
        except ValueError:
            pass
    nl = 'schematic' if netlist == 'schematic' else os.path.relpath(os.path.abspath(netlist), REPO)
    rl = os.path.relpath(REC_LOAD['file'], REPO) if REC_LOAD['file'] else None
    if doc.get('netlist') not in (None, nl) or doc.get('rec_load') != rl:
        doc['corners'] = {}                                # another netlist (or another REC pad load): start over
    doc.update(check=check, netlist=nl, netlist_sha1=(None if netlist == 'schematic' else sha(netlist)), written_by='AFE/layout/tb/tb_%s.py' % check)
    if rl:
        doc['rec_load'] = rl
    else:
        doc.pop('rec_load', None)
    lf = os.path.join(d, '%s_%s.log' % (check, corner))
    open(lf, 'w').write(logtext)
    ent = {'values': values, 'log': os.path.relpath(lf, REPO), 'date': time.strftime('%Y-%m-%d %H:%M')}
    if info:
        ent['info'] = info
    doc['corners'][corner] = ent
    json.dump(doc, open(jf, 'w'), indent=1, sort_keys=True)
    open(jf, 'a').write('\n')
    return jf


def fmt(v):
    if isinstance(v, float):
        return '%.6g' % v
    return str(v)


def cli(check, doc, corners_default, run, extra_args=None):
    """common command line of the tb_*.py scripts.  run(netlist, corner, args, log) -> (values dict, info dict or None)"""
    ap = argparse.ArgumentParser(description=doc, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--netlist', default='schematic', help='schematic | path to the PEX netlist of the cell (flow.py pex)')
    ap.add_argument('--corner', action='append', default=None, help='typ | ff85 | ss-40 | ff-40 | ss125 | all (repeatable); default: %s' % ' '.join(corners_default))
    ap.add_argument('--out', default=None, help='directory of the JSON + logs (default: AFE/layout/baseline for the schematic, AFE/layout/sim/post otherwise)')
    ap.add_argument('--junction', dest='prdiff', action='store_true',
                    help='amplifier checks: the JUNCTION convention for the six pseudo-resistor transistors (area / perimeter present: added to the schematic, kept as extracted in a PEX '
                         'netlist).  Default = the DESIGN convention (none, as AFE/amp/spice/pseudoR.spice: stripped from a PEX netlist).  Results go to <check>_junction.json')
    ap.add_argument('--rec-load', dest='rec_load', default=None,
                    help='amplifier checks (REVIEW.md R13): SPICE file defining `.subckt recpad rec vdd vss` = the pad model that hangs on the amplifier input node rec (AFE/layout/sim/recpad/pad_*.spice). '
                         'Default none = nothing added, results identical to before.  Use --out with it: results must not go to baseline / sim/post')
    if extra_args:
        extra_args(ap)
    a = ap.parse_args()
    if a.rec_load:
        if not a.out:
            ap.error('--rec-load needs --out DIR (outside AFE/layout/baseline and AFE/layout/sim/post)')
        set_rec_load(a.rec_load)
    if a.prdiff:
        check = check + '_junction'
    cs = []
    for c in (a.corner or ['all']):
        cs += list(corners_default) if c == 'all' else [c]
    bad = [c for c in cs if c not in CORNERS]
    if bad:
        ap.error('unknown corner %s (known: %s)' % (bad, ' '.join(CORNERS)))
    rc = 0
    for c in cs:
        lines = []

        def log(*x):
            s = ' '.join(str(q) for q in x)
            lines.append(s)
            print(s, flush=True)
        log('== %s  netlist %s  corner %s (%s, %g C, %g V)  %s' % (check, a.netlist, c, CORNERS[c][0], CORNERS[c][1], CORNERS[c][2], time.strftime('%Y-%m-%d %H:%M')) +
            (('  REC pad load %s' % os.path.relpath(REC_LOAD['file'], REPO)) if REC_LOAD['file'] else ''))
        try:
            vals, info = run(a.netlist, c, a, log)
        except TbError as e:
            log('ERROR %s' % e)
            save(check, a.netlist, c, {'error': str(e)}, '\n'.join(lines) + '\n', a.out)
            rc = 2
            continue
        log('RESULT %s %s: ' % (check, c) + '  '.join('%s=%s' % (k, fmt(v)) for k, v in vals.items()))
        jf = save(check, a.netlist, c, vals, '\n'.join(lines) + '\n', a.out, info)
        print('   -> %s' % os.path.relpath(jf, REPO))
    return rc
