#!/usr/bin/env python3
"""mk_dig_cfg.py (LP step 5 / L1d): writes the three LibreLane inputs of the digital macro afe_dig that depend on the floorplan:
  AFE/dig/config.json            the complete LibreLane 3 configuration (static part = table CFG below + die area, DEF template, clock-buffer placement)
  AFE/dig/afe_dig_template.def   die area + EXACT pin positions (LibreLane FP_DEF_TEMPLATE, step Odb.ApplyDEFTemplate)
  AFE/dig/pins_plan.json         the planned pin table [{name, layer, x_um, y_um, side}] (the as-built table is AFE/dig/trial/afe_dig_pins.json, written by scripts/collect_dig.py)

Floorplan input: AFE/layout/floorplan.json, key cells.afe_dig (written by LP step 2).  Keys used here (every other key is ignored):
  "w", "h"                     die size in um (also accepted: "w_um", "h_um"); w is rounded to 0.56 um sites, h to whole 3.92 um rows
  "pin_layers": {"N": "Metal2", "S": "Metal2", "W": "Metal3"}
  "pins": {"N": [{"name": "sw_rec[0]", "x": 8.0}, ...], "S": [...], "W": [{"name": "RSTN_PD", "y": 4.0}, ...]}     x from the west edge, y from the south edge of the macro, um
If the file or a key is missing the built-in default = the LP floorplan contract is used: north edge channels 0-3, south edge channels 4-7, group k' starts at x = 235 k' + 8 um,
33 pins per group at 3.0 um, order sw_rec sw_rec_b sw_ipg sw_ipg_b rst_sw tg_on dac_gdn cmp_clk cmp_q dac_gp[12k+11] dac_gn[12k+11] ... dac_gp[12k] dac_gn[12k]; west edge, south to
north, 4 um apart: RSTN_PD RSTN_PU RSTN SCLK_PD SCLK_PU SCLK DIN_PD DIN_PU DIN CS_PD CS_PU CS DOUT DOUT_OE DOUT_IE DOUT_PD DOUT_PU DOUT_CS DOUT_SL DOUT_PDRV0 DOUT_PDRV1 rst_amp_o.
The pin NAMES must be exactly the 286 signal pins of afe_dig (the script stops otherwise).
Every pin is SNAPPED to the routing-track grid of its layer (Metal1-4: offset 0.28 um, pitch 0.56 um): a pin moves by at most 0.28 um from the floorplan value.  The planned table
(pins_plan.json) and the as-built table (trial/afe_dig_pins.json) carry the real coordinates: use them, not the nominal ones.  A floorplan on the grid (x = 0.28 + n * 0.56) is built exactly.
HEIGHT: the LP trial needs h >= 105.84 um with routing up to Metal4 (Metal5 free for the top level), >= 94.08 um with --m5 (table MIN_H).  If floorplan.json asks for less, this script
uses the default 109.76 um, says so in capital letters, and the floorplan must be updated (--strict-h stops instead).
East edge: no signal pin.  Power: VDD / VSS = vertical Metal4 straps from the south to the north die edge (PDN_MULTILAYER false: no Metal5 inside the macro; routing stops at Metal4).

Clock options:  --clock buf (default) = Decision 44h: no CTS, ONE clkbuf_20 (ck.u_ckbuf, CLKBUF = 1) placed by MANUAL_GLOBAL_PLACEMENTS in the middle of the strip;
                --clock cts         = CLKBUF = 0 and OpenROAD.CTS runs (kept for experiments: TritonCTS puts the comparator delay chain on the root net, see AFE/dig/LP_STEP5.md).
usage: python3 mk_dig_cfg.py [--clock buf|cts] [--h H_um] [--strict-h] [--m5] [--no-chain-block] [--out DIR]"""
import os, re, sys, json, math, argparse
HERE = os.path.dirname(os.path.abspath(__file__))
AFE = os.path.normpath(os.path.join(HERE, '..'))
FP = os.path.join(AFE, 'layout', 'floorplan.json')
ROW = 3.92           # GF018hv5v_mcu_sc7 site height [libs.tech/librelane/gf180mcu_fd_sc_mcu7t5v0/config.tcl]
SITE = 0.56
TRK0, TRKP = 0.28, 0.56   # Metal1-4 tracks [tracks.info]
DBU = 2000           # DEF units per micron [libs.tech/librelane/config.tcl]
LIBDIR = '/foss/pdks/gf180mcuD/libs.ref/gf180mcu_fd_sc_mcu7t5v0/lib/gf180mcu_fd_sc_mcu7t5v0__%s.lib'
STDLEF = '/foss/pdks/gf180mcuD/libs.ref/gf180mcu_fd_sc_mcu7t5v0/lef/gf180mcu_fd_sc_mcu7t5v0.lef'
CORNERS = ['tt_025C_3v30', 'ss_125C_3v00', 'ss_n40C_3v00', 'ff_n40C_3v60', 'ff_125C_3v60']

# Smallest die heights that completed the flow in the LP trial (2026-11-20, 286 pins at the floorplan.json positions, settings of table CFG, delay chain as one block):
# routing up to Metal4 (Metal5 free for the top level): 105.84 um (101.92 um: global-routing overflow on Metal3, the only horizontal layer; without the chain block 98.00 um routed,
# but the comparator windows were 7 ns late); with --m5: 94.08 um.  Default 109.76 um = one more row pair of margin (Metal3 usage 58 %).
MIN_H = {'Metal4': 105.84, 'Metal5': 94.08}
DEFAULT = {'w': 820.0, 'h': 109.76, 'pin_layers': {'N': 'Metal2', 'S': 'Metal2', 'W': 'Metal3'},
           'north_channels': [0, 1, 2, 3], 'south_channels': [4, 5, 6, 7], 'group_x0': 8.0, 'group_pitch': 235.0, 'pin_pitch': 3.0, 'west_y0': 4.0, 'west_pitch': 4.0}
WEST = ['RSTN_PD', 'RSTN_PU', 'RSTN', 'SCLK_PD', 'SCLK_PU', 'SCLK', 'DIN_PD', 'DIN_PU', 'DIN', 'CS_PD', 'CS_PU', 'CS', 'DOUT', 'DOUT_OE',
        'DOUT_IE', 'DOUT_PD', 'DOUT_PU', 'DOUT_CS', 'DOUT_SL', 'DOUT_PDRV0', 'DOUT_PDRV1', 'rst_amp_o']
INPUTS = {'CS', 'SCLK', 'DIN', 'RSTN'}       # + cmp_q[*]
PIN_LEN = 2.0        # um, along the wire direction, from the die edge inwards
PIN_W = 0.56         # um (2 x the 0.28 um minimum width, as LibreLane's own pins)

CFG = {
    'DESIGN_NAME': 'afe_dig',
    'VERILOG_FILES': ['dir::afe_dig.v', 'dir::../adc/rtl/adc8_top.v', 'dir::../adc/rtl/adc_sar_ch.v', 'dir::../adc/rtl/adc_clkgen.v', 'dir::../adc/rtl/adc_dlychain.v', 'dir::../../rtl/dbs.v'],
    'EXTRA_VERILOG_MODELS': ['dir::../../TGATE/TGATE.v'],          # rtl/dbs.v also holds module dbs (16 TGATEs, not used by afe_dig): the black-box model keeps lint and yosys quiet
    'CLOCK_PORT': 'SCLK',
    'CLOCK_PERIOD': 500,
    'PNR_SDC_FILE': 'dir::afe_dig.sdc',
    'SIGNOFF_SDC_FILE': 'dir::afe_dig.sdc',
    'LIB': {'*_%s' % c: [LIBDIR % c] for c in CORNERS},
    'DEFAULT_CORNER': 'nom_tt_025C_3v30',
    'STA_CORNERS': ['nom_%s' % c for c in CORNERS],
    'TIMING_VIOLATION_CORNERS': ['*'],
    # never resized / buffered / removed: the comparator delay chain = its delay cells (instances ...ckg...<d|c|b|a>.u), the tapw inverters (...ckg.t[i].ui), its nets (taps ...ch.Z,
    # ...ch.w[k], ...wch.w[k], tapw_b[i], cap_clk = tapw[i]); the sampling-TG delay cells (utg); the clock buffer and its net; the switch output pairs (sw[i].*); the DOUT_OE inverter; the tie cells.
    # NOT in the list on purpose: the AND3 gates ...ckg.t[i].ug.  Their third input is drv_en, a net with 26 loads that the repair step has to buffer, and OpenROAD refuses to insert a
    # buffer in front of a dont-touch load (RSZ-3006, flow stops).  scripts/collect_dig.py checks that the 8 gates are still and3_1 after the flow.
    'RSZ_DONT_TOUCH_RX': 'ckg.*\\.(u|ui|Z)$|ckg.*\\.w\\[|tapw_b|cap_clk|utg|u_ckbuf|sclk_i|^sw\\[|u_tie_|^u_oe$',
    'DESIGN_REPAIR_BUFFER_OUTPUT_PORTS': False,
    'DESIGN_REPAIR_BUFFER_INPUT_PORTS': False,
    'FP_SIZING': 'absolute',
    'TOP_MARGIN_MULT': 1,
    'BOTTOM_MARGIN_MULT': 1,
    'LEFT_MARGIN_MULT': 12,
    'RIGHT_MARGIN_MULT': 12,
    'FP_DEF_TEMPLATE': 'dir::afe_dig_template.def',
    'FP_TEMPLATE_MATCH_MODE': 'strict',
    # power: vertical Metal4 straps only, promoted to pins, from die edge to die edge; no Metal5 in the macro (the top level runs its straps there)
    'PDN_MULTILAYER': False,
    'PDN_EXTEND_TO': 'boundary',
    'PDN_VPITCH': 117.6,
    'PDN_VOFFSET': 30.24,
    'RT_MAX_LAYER': 'Metal4',
    # no CTS in the default flow, so the post-CTS repair steps do not run: slew / cap repair and hold repair run after global routing instead
    'RUN_POST_GRT_DESIGN_REPAIR': True,
    'RUN_POST_GRT_RESIZER_TIMING': True,
    # slew / capacitance repair margins in % of the liberty limits (LibreLane defaults 20 / 20 after placement, 10 / 10 after global routing): wider, because the top-level wires
    # are not in these loads and the D3 macro left 16 / 3 violations at the slow corner
    # (tried 40 / 30 / 30 / 20: 7-18 slew and 2-3 cap violations were left on three long decode nets, because the extracted wires are heavier than the global-route estimate)
    'DESIGN_REPAIR_MAX_SLEW_PCT': 55,
    'DESIGN_REPAIR_MAX_CAP_PCT': 50,
    'GRT_DESIGN_REPAIR_MAX_SLEW_PCT': 50,
    'GRT_DESIGN_REPAIR_MAX_CAP_PCT': 45,
}


def die(msg):
    sys.exit('mk_dig_cfg: STOP: ' + msg)


def snap(v):
    return round(TRK0 + round((v - TRK0) / TRKP) * TRKP, 3)


def load_fp():
    """-> (W, H requested, layers, {side: [(name, coordinate)]}, list of notes)"""
    notes = []
    fp = {}
    if os.path.exists(FP):
        try:
            fp = json.load(open(FP)).get('cells', {}).get('afe_dig', {}) or {}
        except Exception as e:
            die('cannot read %s: %s' % (FP, e))
        if not fp:
            notes.append('AFE/layout/floorplan.json has no cells.afe_dig: built-in defaults')
    else:
        notes.append('AFE/layout/floorplan.json does not exist: built-in defaults (the LP floorplan contract)')
    g = lambda *ks: next((fp[k] for k in ks if k in fp), None)
    W = float(g('w', 'w_um') or DEFAULT['w'])
    H = g('h', 'h_um')
    notes.append('die size: w %s, h %s' % ('%.2f (floorplan.json)' % W if g('w', 'w_um') else '%.2f (default)' % W, '%.2f (floorplan.json)' % float(H) if H else '%.2f (default)' % DEFAULT['h']))
    H = float(H) if H else DEFAULT['h']
    layers = dict(DEFAULT['pin_layers'])
    layers.update(fp.get('pin_layers') or {})
    pl = fp.get('pins') or {}
    if all(isinstance(pl.get(sd), list) and pl.get(sd) for sd in ('N', 'S', 'W')):
        pins = {sd: [(q['name'], float(q['x' if sd in 'NS' else 'y'])) for q in pl[sd]] for sd in ('N', 'S', 'W')}
        notes.append('pin positions: floorplan.json cells.afe_dig.pins (N %d, S %d, W %d)' % (len(pins['N']), len(pins['S']), len(pins['W'])))
    else:
        pins = {'N': [], 'S': [], 'W': []}
        for sd, chans in (('N', DEFAULT['north_channels']), ('S', DEFAULT['south_channels'])):
            for kk, k in enumerate(chans):
                pins[sd] += [(name, DEFAULT['group_pitch'] * kk + DEFAULT['group_x0'] + n * DEFAULT['pin_pitch']) for n, name in enumerate(chan_order(k))]
        pins['W'] = [(name, DEFAULT['west_y0'] + n * DEFAULT['west_pitch']) for n, name in enumerate(WEST)]
        notes.append('pin positions: built-in default (cells.afe_dig.pins.N / .S / .W not in floorplan.json)')
    return W, H, layers, pins, notes


def chan_order(k):
    o = ['sw_rec[%d]' % k, 'sw_rec_b[%d]' % k, 'sw_ipg[%d]' % k, 'sw_ipg_b[%d]' % k, 'rst_sw[%d]' % k, 'tg_on[%d]' % k, 'dac_gdn[%d]' % k, 'cmp_clk[%d]' % k, 'cmp_q[%d]' % k]
    for b in range(11, -1, -1):
        o += ['dac_gp[%d]' % (12 * k + b), 'dac_gn[%d]' % (12 * k + b)]
    return o


def cell_width(master):
    txt = open(STDLEF).read()
    m = re.search(r'MACRO gf180mcu_fd_sc_mcu7t5v0__%s\b.*?SIZE\s+([\d.]+)\s+BY' % master, txt, flags=re.S)
    if not m:
        die('cell %s not found in %s' % (master, STDLEF))
    return float(m.group(1))


def chain_placement(W, core_y0, core_rows):
    """Global-placement seeds for the comparator delay chain (LP finding): the chain nets are dont-touch (no buffer may go in), so every um of wire on a tap net slows that tap AND all
    later ones.  Left to the placer, the chain is spread over the 820 um strip next to each ADC's pins: Delta grows by 4 % and the last window ends 7 ns later at ss 125 C than in the
    compact D3 macro (limit missed).  Here the chain is ONE compact block: the 41 + 2 main cells (T0, then 7 x DT) in serpentine rows, and for every tap i its side branch
    [W chain, tapw inverter ui, comparator-clock gate ug] in the row next to the tap.  Only the outputs cmp_clk[i] (driven by ug) travel to the pins.  The block sits near the
    pins of ADC 7 (south edge, east end): its window is the one that must end before the next SCLK edge.  Returns {instance: {location, orientation}}."""
    txt = re.sub(r'//[^\n]*', '', open(os.path.join(AFE, 'adc', 'rtl', 'adc_clkgen.v')).read())
    par = {k: int(v) for k, v in re.findall(r'\b(T0_[DCBA]|DT_[DCBA]|W_[DCBA])\s*=\s*(\d+)', txt)}
    if len(par) != 12:
        die('cannot read the 12 chain parameters from AFE/adc/rtl/adc_clkgen.v (found %s)' % sorted(par))
    wid = {k: cell_width(m) for k, m in (('d', 'dlyd_1'), ('c', 'dlyc_1'), ('b', 'dlyb_1'), ('a', 'dlya_1'), ('ui', 'inv_1'), ('ug', 'and3_1'))}
    sfx = {'d': 'd.u', 'c': 'genblk1.c.u', 'b': 'genblk1.genblk1.b.u', 'a': 'genblk1.genblk1.a.u'}

    def dly(prefix, key):
        kinds = 'd' * par[key + '_D'] + 'c' * par[key + '_C'] + 'b' * par[key + '_B'] + 'a' * par[key + '_A']
        return [('%s.g[%d].%s' % (prefix, k, sfx[kd]), wid[kd]) for k, kd in enumerate(kinds)]
    LROW = 200.0                                  # um of cells per main row
    x_hi = round(min(W - 60.0, 760.0), 2)         # block = [x_hi - LROW, x_hi]
    x_lo = x_hi - LROW
    need_rows = 2 * int(math.ceil((sum(w for _, w in dly('', 'T0')) + 7 * sum(w for _, w in dly('', 'DT'))) / (LROW - 20.0)))
    r_top = min(core_rows - 2, (core_rows + need_rows) // 2)   # top main row; the block is in the middle rows (the rows next to the pins stay free for each ADC's own logic) and grows downwards
    if r_top - need_rows + 1 < 0:
        die('the delay-chain block needs %d rows, the core has %d' % (need_rows, core_rows))
    place = {}
    state = {'row': r_top, 'dir': -1, 'x': x_hi}

    def put_main(name, w):
        st = state
        if (st['dir'] < 0 and st['x'] - w < x_lo) or (st['dir'] > 0 and st['x'] + w > x_hi):
            st['row'] -= 2
            st['dir'] = -st['dir']
            st['x'] = x_hi if st['dir'] < 0 else x_lo
        x = st['x'] - w if st['dir'] < 0 else st['x']
        place[name] = (x, st['row'])
        st['x'] += st['dir'] * w

    def put_branch(i):
        # the side branch of tap i, in the row below the main row, starting under the tap driver and running on in the direction of the chain
        st = state
        x, d, row = st['x'], st['dir'], st['row'] - 1
        for name, w in dly('u_adc.ckg.t[%d].wch' % i, 'W') + [('u_adc.ckg.t[%d].ui' % i, wid['ui']), ('u_adc.ckg.t[%d].ug' % i, wid['ug'])]:
            xx = min(max(x - w if d < 0 else x, x_lo - 30.0), x_hi + 30.0 - w)
            place[name] = (xx, row)
            x += d * w
    for name, w in dly('u_adc.ckg.t[0].first.ch', 'T0'):
        put_main(name, w)
    put_branch(0)
    for i in range(1, 8):
        for name, w in dly('u_adc.ckg.t[%d].nxt.ch' % i, 'DT'):
            put_main(name, w)
        put_branch(i)
    out = {}
    for name, (x, row) in place.items():
        out[name] = {'location': [round(round(x / SITE) * SITE, 2), round(core_y0 + row * ROW, 2)], 'orientation': 'N'}
    rows = sorted(set(r for _, r in place.values()))
    return out, 'delay chain: %d cells seeded in one block x %.0f..%.0f um, core rows %d..%d (y %.1f..%.1f um), parameters %s' % (
        len(out), x_lo, x_hi, rows[0], rows[-1], core_y0 + rows[0] * ROW, core_y0 + (rows[-1] + 1) * ROW, ' '.join('%s=%d' % kv for kv in sorted(par.items())))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--clock', choices=('buf', 'cts'), default='buf')
    ap.add_argument('--h', type=float, default=None, help='die height in um (overrides floorplan.json / the default)')
    ap.add_argument('--strict-h', action='store_true', help='stop if the floorplan height is below the smallest height that routes (default: use 109.76 um and warn)')
    ap.add_argument('--out', default=HERE)
    ap.add_argument('--no-chain-block', action='store_true', help='do not seed the delay chain as one compact block (experiment: the LP trial without it missed the window limit)')
    ap.add_argument('--m5', action='store_true', help='let the router use Metal5 inside the macro (RT_MAX_LAYER Metal5); default: Metal4, Metal5 stays free for the top level')
    opt = ap.parse_args()
    Wreq, Hreq, layers, plist, notes = load_fp()
    max_layer = 'Metal5' if opt.m5 else CFG['RT_MAX_LAYER']
    warn = []
    if opt.h:
        Hreq = opt.h
        notes.append('die height %.2f um from --h' % opt.h)
    W = round(math.floor(Wreq / SITE + 1e-6) * SITE, 3)
    nrow = int(round(Hreq / ROW))
    H = round(nrow * ROW, 3)
    if H < MIN_H[max_layer] - 1e-6:
        msg = ('THE FLOORPLAN HEIGHT %.2f um (%d rows = %.2f um) IS BELOW THE SMALLEST HEIGHT THAT ROUTES with routing up to %s (%.2f um; LP trial: Metal3 is the only horizontal layer '
               'and overflows).' % (Hreq, nrow, H, max_layer, MIN_H[max_layer]))
        if opt.strict_h:
            die(msg + '  Raise cells.afe_dig.h in AFE/layout/floorplan.json to >= %.2f (default 109.76), or use --m5 (>= %.2f um, Metal5 then used inside the macro).' % (MIN_H['Metal4'], MIN_H['Metal5']))
        if opt.h:
            warn.append(msg + '  Kept, because --h asks for it: expect GRT-0116 (congestion).')
        else:
            nrow = int(round(DEFAULT['h'] / ROW))
            H = round(nrow * ROW, 3)
            warn.append(msg + '  USING %.2f um INSTEAD: UPDATE cells.afe_dig.h (and the strip that holds the macro) IN AFE/layout/floorplan.json.' % H)
    if W > 820.0 + 1e-6:
        die('die width %.2f um exceeds the 820 um of the floorplan contract' % W)
    # ---- pins: snap to the track grid, check the name set
    want = set(WEST)
    for k in range(8):
        want |= set(chan_order(k))
    names = [n for sd in plist for n, _ in plist[sd]]
    if len(names) != len(set(names)) or set(names) != want:
        die('pin names: %d given, %d unique; missing %s; unknown %s' % (len(names), len(set(names)), sorted(want - set(names))[:6], sorted(set(names) - want)[:6]))
    pins = []
    dev = 0.0
    for sd in ('N', 'S', 'W'):
        seen = {}
        for name, v in plist[sd]:
            c = snap(v)
            dev = max(dev, abs(c - v))
            lim = W if sd in 'NS' else H
            if not (PIN_W < c < lim - PIN_W):
                die('pin %s at %.2f um is outside the %s edge (0 .. %.2f um)' % (name, c, sd, lim))
            for o, oc in seen.items():
                if abs(oc - c) < 2 * TRKP - 1e-6:
                    die('pins %s and %s are %.2f um apart on the %s edge after snapping (minimum 1.12 um)' % (o, name, abs(oc - c), sd))
            seen[name] = c
            pins.append({'name': name, 'layer': layers[sd], 'x_um': c if sd in 'NS' else 0.0, 'y_um': (H if sd == 'N' else 0.0) if sd in 'NS' else c, 'side': sd, 'floorplan_um': round(v, 3),
                         'dir': 'INPUT' if (name in INPUTS or name.startswith('cmp_q')) else 'OUTPUT'})
    # ---- DEF template
    u = lambda v: int(round(v * DBU))
    L = ['VERSION 5.8 ;', 'DIVIDERCHAR "/" ;', 'BUSBITCHARS "[]" ;', 'DESIGN afe_dig ;', 'UNITS DISTANCE MICRONS %d ;' % DBU,
         'DIEAREA ( 0 0 ) ( %d %d ) ;' % (u(W), u(H)), 'PINS %d ;' % len(pins)]
    for q in pins:
        hw, ln = u(PIN_W / 2), u(PIN_LEN)
        if q['side'] == 'N':
            box, org = '( %d %d ) ( %d 0 )' % (-hw, -ln, hw), (u(q['x_um']), u(H))
        elif q['side'] == 'S':
            box, org = '( %d 0 ) ( %d %d )' % (-hw, hw, ln), (u(q['x_um']), 0)
        else:
            box, org = '( 0 %d ) ( %d %d )' % (-hw, ln, hw), (0, u(q['y_um']))
        L += ['    - %s + NET %s + DIRECTION %s + USE SIGNAL' % (q['name'], q['name'], q['dir']), '      + PORT', '        + LAYER %s %s' % (q['layer'], box), '        + PLACED ( %d %d ) N ;' % org]
    L += ['END PINS', 'END DESIGN', '']
    os.makedirs(opt.out, exist_ok=True)
    open(os.path.join(opt.out, 'afe_dig_template.def'), 'w').write('\n'.join(L))
    json.dump({'_comment': 'PLANNED pin table of afe_dig, written by AFE/dig/mk_dig_cfg.py (the as-built table is trial/afe_dig_pins.json). x / y = pin centre on the die edge, um, origin = SW corner '
                           'of the macro; floorplan_um = the coordinate asked by AFE/layout/floorplan.json (or the default) before snapping to the 0.56 um track grid.',
               'die_w_um': W, 'die_h_um': H, 'max_snap_um': round(dev, 3), 'pin_len_um': PIN_LEN, 'pin_width_um': PIN_W,
               'pins': [{k: q[k] for k in ('name', 'layer', 'x_um', 'y_um', 'side', 'floorplan_um')} for q in pins]}, open(os.path.join(opt.out, 'pins_plan.json'), 'w'), indent=1)
    # ---- config
    cfg = {'//': 'GENERATED by AFE/dig/mk_dig_cfg.py (floorplan: AFE/layout/floorplan.json cells.afe_dig, or the built-in LP contract). Do not edit: change the script or floorplan.json and run it again. clock option: ' + opt.clock}
    cfg.update(CFG)
    cfg['DIE_AREA'] = [0, 0, W, H]
    if opt.m5:
        cfg['RT_MAX_LAYER'] = 'Metal5'
    core_rows = nrow - cfg['TOP_MARGIN_MULT'] - cfg['BOTTOM_MARGIN_MULT']
    core_w = W - (cfg['LEFT_MARGIN_MULT'] + cfg['RIGHT_MARGIN_MULT']) * SITE
    chain_note = 'delay chain: left to the placer (--no-chain-block)'
    cfg['MANUAL_GLOBAL_PLACEMENTS'] = {}
    if not opt.no_chain_block:
        cfg['MANUAL_GLOBAL_PLACEMENTS'], chain_note = chain_placement(W, cfg['BOTTOM_MARGIN_MULT'] * ROW, core_rows)
    if opt.clock == 'buf':
        cfg['SYNTH_PARAMETERS'] = ['CLKBUF=1']
        cfg['RUN_CTS'] = False
        cfg['RUN_POST_CTS_RESIZER_TIMING'] = False
        # the one clock buffer: global-placed in the middle of the strip (then legalised), so the unbuffered net sclk_i has the shortest reach to both ends
        cfg['MANUAL_GLOBAL_PLACEMENTS']['ck.u_ckbuf'] = {'location': [round(W / 2, 2), round(math.floor(nrow / 2) * ROW, 2)], 'orientation': 'N'}
    else:
        cfg['SYNTH_PARAMETERS'] = ['CLKBUF=0']
        cfg['RUN_CTS'] = True
        cfg['CTS_APPLY_NDR'] = 'none'          # with the default 'half' the detailed router finds no access point for a clock-buffer pin (DRT-0073)
    if not cfg['MANUAL_GLOBAL_PLACEMENTS']:
        del cfg['MANUAL_GLOBAL_PLACEMENTS']
    json.dump(cfg, open(os.path.join(opt.out, 'config.json'), 'w'), indent=2)
    for n in notes:
        print('mk_dig_cfg: ' + n)
    print('mk_dig_cfg: die %.2f x %.2f um (%d rows of %.2f), core %.2f x %.2f um = %.0f um2 (%d rows), clock: %s, routing up to %s' % (W, H, nrow, ROW, core_w, core_rows * ROW, core_w * core_rows * ROW, core_rows, opt.clock, cfg['RT_MAX_LAYER']))
    for sd in ('N', 'S', 'W'):
        q = [x for x in pins if x['side'] == sd]
        c = sorted(x['x_um'] if sd in 'NS' else x['y_um'] for x in q)
        print('mk_dig_cfg: %s edge: %d pins on %s, %.2f .. %.2f um, smallest pitch %.2f um' % (sd, len(q), layers[sd], c[0], c[-1], min(b - a for a, b in zip(c, c[1:]))))
    print('mk_dig_cfg: largest move of a pin from its floorplan coordinate to the track grid: %.3f um' % dev)
    print('mk_dig_cfg: ' + chain_note)
    for w in warn:
        print('mk_dig_cfg: WARNING: ' + w)
    print('mk_dig_cfg: wrote config.json, afe_dig_template.def, pins_plan.json in %s' % os.path.relpath(opt.out, os.path.join(AFE, '..')))


if __name__ == '__main__':
    main()
