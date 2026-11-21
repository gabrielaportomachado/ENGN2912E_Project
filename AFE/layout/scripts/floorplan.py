#!/usr/bin/env python3
"""floorplan.py (LP kit, step 2): builds and checks AFE/layout/floorplan.json, the single source of every position, size, pin and corridor of the chip floorplan.
All numbers are um, origin = SW corner of the outline_w x outline_h outline (gds/dbs_afe_top.gds, PR boundary 0/0, given to the organizer; never exceed it).
Decision 52: 605 x 1110 um, n_ch = 4 channels in two rows of n_ch / 2 (Decision 45 / 48: 1000 x 1000 um, 8 channels; restore with outline_w=1000 outline_h=1000 n_ch=8).

  python3 AFE/layout/scripts/floorplan.py build [--set key=value ...]   recompute floorplan.json from PARAMS below (+ overrides, which are stored in the file)
  python3 AFE/layout/scripts/floorplan.py check [--gds cell=file.gds ...] [--dig-pins file.json] [--pins-def file.def]
        1. floorplan.json equals what `build` gives for its stored params (not edited by hand)      2. everything inside the outline, no two blocks overlap
        3. every port bit of module dbs_afe_top (AFE/top/dbs_afe_top.v) is exactly one pin; every pad of info.yaml has exactly its ports (organizer template rules)
        4. area: block budgets vs the estimates of AFE/review/sim/f1_area.log, and the margin               5. as-built cells (--gds amp_ch=..., adc_ch=..., bias_genc=..., afe_dig=...,
           dbs_afe_top=...): bounding box <= budget / outline                                               6. the hardened macro's pin table (--dig-pins) against the contract
        prints PASS / FAIL per line; exit 0 only if nothing failed.
  bash AFE/layout/scripts/kl.sh AFE/layout/scripts/floorplan.py out=<file.gds>      a picture of the floorplan (boxes + labels) as GDS, for KLayout
The text of AFE/layout/SPEC.md explains every item; where SPEC.md and this file differ, floorplan.json wins and SPEC.md is wrong.
"""
import os, sys, json, re, math

HERE = os.path.dirname(os.path.abspath(__file__)) if '__file__' in globals() else os.environ.get('KL_KIT', '.')
LAY = os.path.normpath(os.path.join(HERE, '..'))
REPO = os.path.normpath(os.path.join(LAY, '..', '..'))
FP = os.path.join(LAY, 'floorplan.json')

PARAMS = {
    'outline_w': 1000.0, 'outline_h': 1000.0,   # outline (Decision 45: 1000 x 1000; Decision 52: 605 x 1110)
    'n_ch': 8,                  # channels, two rows of n_ch / 2 (Decision 52: 4)
    'ring': 30.0,               # pin ring on all four sides: pin escape wiring, supply trunks, the west decap bank
    'bias_corr': 14.0,          # corridor between the ring and the amplifier end of each channel row: 6 bias lines + REF + the analog supply strap
    'strap_corr': 26.0,         # corridor between the digital macro and the ADC end of each row: ADC-main / ADC-DAC / vss straps (Metal4/5), the DAC-strap decap row (Metal1), control crossings (Metal2)
    'dig_w': 820.0, 'dig_h': 110.0,         # afe_dig slot; the trial hardening of LP step 5 is 819.84 x 109.76 um (AFE/dig/trial/afe_dig_pins.json).  L1d may lower dig_h, never raise it
    'ch_pitch': 235.0,          # channel slot width (4 x 235 = 940 = outline - 2 x ring)
    'ctl_corr': 8.0,            # west side of every channel slot: sw_rec, sw_rec_b, sw_ipg, sw_ipg_b, rst_amp from the macro to the amplifier end (quasi-static lines, shielded)
    'spur_corr': 7.0,           # east side of every channel slot: analog vdd / vss spur from the bias corridor to adc_ch.vdd
    'adc_h': 104.0,             # adc_ch slot height (ADC end = next to the strap corridor)
    'tg_h': 8.0,                # routing-TGATE zone at the amplifier end (2 x TGATE + tap cells)
    'bias_gap': 20.0,           # gap between the macro's east end and the bias_genc region
    'bias_ys': 10.0,            # bias_genc region stays this far from the ADC ends of channels 3 and 7 (plus its own guard ring)
    'pin_pitch_dig': 3.0, 'pin_x0_dig': 8.0,     # macro pin group per channel: 33 pins from x0 at this pitch (measured from the west edge of the channel slot)
    'pin_pitch_w': 4.0, 'pin_y0_w': 4.0,     # west-edge pins of the macro (first pin 4 um above its south edge, as built in the trial) and of the chip (same y)
    'decap_unit': [20.0, 20.0],  # cap_nmos_03v3 unit (c_width, c_length), 3.983 fF/um2 at 3.3 V (PDK model, AUDIT m6)
    'decap_n_dac_corr': 32, 'decap_n_main_corr': 2, 'decap_n_main_ring': 38, 'decap_n_main_cref': 4,     # per corridor / per corridor / west ring / per ADC
    'decap_n_main_cin': 0,      # ADC-main decap units under the Cin pieces of each amp_ch (Decision 46c reserve, top-level overlap over a vss Metal3 shield)
    'decap_min_main_pF': 115.0, 'decap_min_dac_pF': 95.0,   # check 4c targets (Decision 44d: 0.125 / 0.1 nF less 8 %; Decision 52 sets the DAC target for 4 ADCs)
    'rstrap': ['rm3', 2.0, 222.2],
    'pin_source': 'DEFAULT (no organizer DEF yet): positions chosen by LP so that no pin wire crosses another; replace with `floorplan.py build --pins-def <organizer.def>` when the DEF arrives',
}
EST = {'amp_ch': 51626.0, 'adc_ch': 14911.0, 'bias_genc': 9966.0, 'afe_dig_cells': 33661.0, 'tgates': 199.0, 'decap_gate': 56533.0}
EST_SRC = ('AFE/review/sim/f1_area.log: afe_chc 49,312 + fs_oneshot_c 2,314 = 51,626 um2 (amp_ch); ADC analog part 14,911; bias_genc 9,966; digital cells 31,872 + dbs_ctrl 1,789 = 33,661; '
           '2 TGATE + OR2 + INV 199; decap 0.225 nF = 56,533 um2 of gate (all ESTIMATE, the layout model is at the top of that log)')
CH_DIG = ['sw_rec', 'sw_rec_b', 'sw_ipg', 'sw_ipg_b', 'rst_sw', 'tg_on', 'dac_gdn', 'cmp_clk', 'cmp_q'] + [x for b in range(11, -1, -1) for x in ('dac_gp%d' % b, 'dac_gn%d' % b)]
W_PINS = ['RSTN_PD', 'RSTN_PU', 'RSTN', 'SCLK_PD', 'SCLK_PU', 'SCLK', 'DIN_PD', 'DIN_PU', 'DIN', 'CS_PD', 'CS_PU', 'CS', 'DOUT', 'DOUT_OE', 'DOUT_IE', 'DOUT_PD', 'DOUT_PU', 'DOUT_CS',
          'DOUT_SL', 'DOUT_PDRV0', 'DOUT_PDRV1', 'rst_amp_o']           # macro west edge, south to north
PAD_TYPES = {'analog': [''], 'power': [''], 'ground': [''], 'input_cmos': ['', '_PU', '_PD'], 'input_schmitt': ['', '_PU', '_PD'],
             'bidirectional': ['_IN', '_OUT', '_PD', '_PU', '_CS', '_SL', '_IE', '_OE', '_PDRV0', '_PDRV1']}     # organizer template (AFE/review/sim/organizer/template_info.yaml lines 26-66)


def r3(v):
    return round(float(v), 3)


def build(p):
    W, H, R, N = p['outline_w'], p['outline_h'], p['ring'], int(p['n_ch'])
    NR = N // 2                                                        # channels per row
    O = H                                                              # y extent (the north edge)
    core0, core1, coreY1 = R, W - R, H - R
    dig_y0 = (H - p['dig_h']) / 2.0
    dig_y1 = dig_y0 + p['dig_h']
    sN0, sN1 = dig_y1, dig_y1 + p['strap_corr']                       # north strap corridor
    sS1, sS0 = dig_y0, dig_y0 - p['strap_corr']
    bN1, bN0 = coreY1, coreY1 - p['bias_corr']                        # north bias corridor
    bS0, bS1 = core0, core0 + p['bias_corr']
    ch_h = bN0 - sN1
    cell_w = p['ch_pitch'] - p['ctl_corr'] - p['spur_corr']
    amp_h = ch_h - p['adc_h'] - p['tg_h']
    fp = {'_about': 'Chip floorplan of dbs_afe_top. GENERATED by AFE/layout/scripts/floorplan.py build from "params"; do not edit by hand (floorplan.py check fails if you do). '
                    'Change a parameter with:  python3 AFE/layout/scripts/floorplan.py build --set key=value.  Units um, origin = SW corner of the outline. Explanations: AFE/layout/SPEC.md.',
          'params': p, 'outline': [0.0, 0.0, W, H], 'core': [core0, core0, core1, coreY1]}
    z = []

    def zone(name, x0, y0, x1, y1, what, layers):
        z.append({'name': name, 'rect': [r3(x0), r3(y0), r3(x1), r3(y1)], 'what': what, 'layers': layers})
    zone('ring_w', 0, 0, R, H, 'pin ring west: the 21 digital / pad-control pin wires straight to the macro, VDD / VSS entry = star point of the three straps, west decap bank (ADC-main)', 'pins Metal3; trunks Metal4/Metal5; decap comp/poly/Metal1')
    zone('ring_e', core1, 0, W, H, 'pin ring east: REF entry, bias trunk between the two bias corridors', 'Metal3-Metal5')
    zone('ring_n', R, bN1, core1, H, 'pin ring north: E / IPG pin escape of channels 0-%d (and any pin the organizer DEF puts here)' % (NR - 1), 'analog tracks Metal4/Metal5, digital only in the outer 12 um on Metal2/Metal3')
    zone('ring_s', R, 0, core1, bS0, 'pin ring south: E / IPG pin escape of channels %d-%d' % (NR, N - 1), 'as ring_n')
    zone('bias_corr_n', core0, bN0, core1, bN1, 'bias corridor north: vbn vcm vg1 vcmo vg2 vrs + REF (daisy chain from bias_genc, east to west) under the analog vdd / vss strap', 'lines Metal2/Metal3 (1 um wide, 1 um apart, vss between); strap Metal4 (vss) / Metal5 (vdd)')
    zone('bias_corr_s', core0, bS0, core1, bS1, 'bias corridor south (channels %d-%d), same as north' % (NR, N - 1), 'as bias_corr_n')
    xr = core0 + p['ch_pitch'] * NR                                     # east end of the channel rows
    if core1 - xr > 1e-6:
        zone('spare_ne', xr, sN1, core1, bN0, 'east of the north channel row: not assigned (REF / bias trunk widening, decap or wiring for L3a)', 'any')
        zone('spare_se', xr, bS1, core1, sS0, 'east of the south channel row: not assigned (as spare_ne)', 'any')
    zone('strap_corr_n', core0, sN0, core0 + p['dig_w'] + 10.0, sN1, 'strap corridor north: ADC-main strap (VDD), ADC-DAC strap (vdd_dac), vss; DAC-strap decap row; macro <-> adc_ch control wires cross it', 'straps Metal5 over vss Metal4; decap comp/poly/Metal1; crossings Metal2; rm3 strap resistor Metal3')
    zone('strap_corr_s', core0, sS0, core0 + p['dig_w'] + 10.0, sS1, 'strap corridor south, same as north (no strap resistor)', 'as strap_corr_n')
    bx0 = core0 + p['dig_w'] + p['bias_gap']
    by0, by1 = sS0 + p['bias_ys'], sN1 - p['bias_ys']
    fp['zones'] = z
    cells = {}
    cells['afe_dig'] = {'what': 'digital macro (LibreLane): dbs_ctrl N = 8 + adc8_top + 15 pad-control tie cells' + ('' if N == 8 else '; channels 0-%d brought out to pins, 4-7 tied off inside the wrapper (Decision 52)' % (N - 1)), 'w': p['dig_w'], 'h': p['dig_h'], 'x': core0, 'y': r3(dig_y0), 'orient': 'R0',
                        'rail': 'ADC-main strap (net VDD), vss', 'guard': 'P+ substrate ring on vss and N-well ring on VDD around the macro, inside the strap corridors (2 um each); >= 20 um to any analog device',
                        'pin_layers': {'N': 'Metal2', 'S': 'Metal2', 'W': 'Metal3'}, 'pins': {'N': [], 'S': [], 'W': []}}
    for edge, base in (('N', 0), ('S', NR)):
        for kk in range(NR):
            k = base + kk
            for i, nm in enumerate(CH_DIG):
                m = re.match(r'(dac_g[pn])(\d+)$', nm)
                name = '%s[%d]' % (m.group(1), 12 * k + int(m.group(2))) if m else '%s[%d]' % (nm, k)
                cells['afe_dig']['pins'][edge].append({'name': name, 'x': r3(p['ch_pitch'] * kk + p['pin_x0_dig'] + p['pin_pitch_dig'] * i), 'ch': k})
    y0w = p['pin_y0_w']
    for i, nm in enumerate(W_PINS):
        cells['afe_dig']['pins']['W'].append({'name': nm, 'y': r3(y0w + p['pin_pitch_w'] * i)})
    cells['afe_ch'] = {'what': 'one channel slot = control corridor | amp_ch + adc_ch + TGATE zone | analog spur corridor', 'w': p['ch_pitch'], 'h': r3(ch_h),
                       'sub': {'ctl_corr': [0.0, 0.0, p['ctl_corr'], r3(ch_h)], 'adc_ch': [p['ctl_corr'], 0.0, r3(p['ctl_corr'] + cell_w), p['adc_h']],
                               'amp_ch': [p['ctl_corr'], p['adc_h'], r3(p['ctl_corr'] + cell_w), r3(p['adc_h'] + amp_h)],
                               'tg_zone': [p['ctl_corr'], r3(p['adc_h'] + amp_h), r3(p['ctl_corr'] + cell_w), r3(ch_h)],
                               'spur_corr': [r3(p['ch_pitch'] - p['spur_corr']), 0.0, p['ch_pitch'], r3(ch_h)]},
                       'note': 'slot coordinates are those of a NORTH-row channel: y = 0 is the ADC end (next to the strap corridor), y = h the amplifier end. South-row channels are the same cell mirrored about the x axis (MX).'}
    cells['adc_ch'] = {'what': 'ADC analog part (L1a): dac_sw + cmp_p + vhalf + vrefs + INV', 'w_max': r3(cell_w), 'h_max': p['adc_h'], 'estimate_um2': EST['adc_ch'], 'ref': 'AFE/layout/lvs/adc_ch.spice subckt adc_ch'}
    cells['amp_ch'] = {'what': 'amplifier part (L2a): afe_chc + fs_oneshot_c + OR2', 'w_max': r3(cell_w), 'h_max': r3(amp_h), 'estimate_um2': EST['amp_ch'], 'ref': 'AFE/layout/lvs/afe_chc.spice subckt amp_ch',
                       'rotation': 'the cell may be placed R0 or R90 (all %d channels the same way) if its W x H fits only one way' % N}
    cells['bias_genc'] = {'what': 'shared bias (L3a): beta multiplier, start-up, ladders A / B in ppolyf_u_1k, reset-level replica, C_VRS', 'x': r3(bx0), 'y': r3(by0), 'w_max': r3(core1 - bx0), 'h_max': r3(by1 - by0),
                          'estimate_um2': EST['bias_genc'], 'ref': 'AFE/layout/lvs/bias_genc.spice', 'rail': 'analog strap', 'pins_side': 'E (towards the east ring): vbn vcm_in vg1 vcm_out vg2 vrs; vdd vss'}
    fp['cells'] = cells
    pl = [{'inst': 'u_dig', 'cell': 'afe_dig', 'x': core0, 'y': r3(dig_y0), 'w': p['dig_w'], 'h': p['dig_h'], 'orient': 'R0'},
          {'inst': 'u_bias', 'cell': 'bias_genc', 'x': r3(bx0), 'y': r3(by0), 'w': r3(core1 - bx0), 'h': r3(by1 - by0), 'orient': 'R0'}]
    for k in range(N):
        kk = k % NR
        north = k < NR
        pl.append({'inst': 'ch%d' % k, 'cell': 'afe_ch', 'x': r3(core0 + p['ch_pitch'] * kk), 'y': r3(sN1 if north else bS1), 'w': p['ch_pitch'], 'h': r3(ch_h), 'orient': 'R0' if north else 'MX',
                   'row': 'N' if north else 'S', 'adc_end_y': r3(sN1 if north else sS0), 'amp_end_y': r3(bN0 if north else bS1)})
    fp['placements'] = pl
    # ---- chip pins (41 port bits of dbs_afe_top).  DEFAULT positions: see params.pin_source
    pins = []
    for k in range(N):
        kk, north = k % NR, k < NR
        x0 = core0 + p['ch_pitch'] * kk
        y = O if north else 0.0
        pins.append({'name': 'E[%d]' % k, 'pad': 'E[%d]' % k, 'side': 'N' if north else 'S', 'x': r3(x0 + 70.0), 'y': y, 'layer': 'Metal5', 'w': 2.0, 'to': 'ch%d TGATE zone: IN of both TGATEs' % k})
        pins.append({'name': 'IPG[%d]' % k, 'pad': 'IPG[%d]' % k, 'side': 'N' if north else 'S', 'x': r3(x0 + 165.0), 'y': y, 'layer': 'Metal5', 'w': 2.0, 'to': 'ch%d TGATE zone: OUT of the IPG TGATE' % k})
    pins.append({'name': 'REF', 'pad': 'REF', 'side': 'E', 'x': W, 'y': r3(H / 2.0), 'layer': 'Metal5', 'w': 2.0, 'to': 'REF trunk: east ring -> both bias corridors -> amp_ch.ref of the %d channels (Metal5 / Metal3, never one Metal4 polygon: MIMTM.11)' % N})
    for i, nm in enumerate(W_PINS[:-1]):
        port = 'DOUT_OUT' if nm == 'DOUT' else nm
        pad = re.sub(r'_(PD|PU|OE|IE|CS|SL|PDRV0|PDRV1|OUT)$', '', port) if port not in ('CS',) else 'CS'
        pins.append({'name': port, 'pad': pad, 'side': 'W', 'x': 0.0, 'y': r3(dig_y0 + y0w + p['pin_pitch_w'] * i), 'layer': 'Metal3', 'w': 0.6, 'to': 'afe_dig.%s (straight wire across the west ring)' % nm})
    pins.append({'name': 'DOUT_IN', 'pad': 'DOUT', 'side': 'W', 'x': 0.0, 'y': r3(dig_y0 + y0w + p['pin_pitch_w'] * (len(W_PINS) - 1)), 'layer': 'Metal3', 'w': 0.6,
                 'to': 'not connected inside (the pad input buffer is off, DOUT_IE = 0); the pin exists because the organizer template requires it'})
    pins.append({'name': 'VDD', 'pad': 'VDD', 'side': 'W', 'x': 0.0, 'y': r3(dig_y1 + 14.0), 'layer': 'Metal5', 'w': 20.0, 'to': 'star point: ADC-main strap, analog strap, strap resistor -> ADC-DAC strap'})
    pins.append({'name': 'VSS', 'pad': 'VSS', 'side': 'W', 'x': 0.0, 'y': r3(dig_y0 - 14.0), 'layer': 'Metal4', 'w': 20.0, 'to': 'star point of the vss straps (one ground; the substrate is common)'})
    fp['pins'] = pins
    du = p['decap_unit']
    ff = du[0] * du[1] * 3.983
    n_main = 2 * p['decap_n_main_corr'] + p['decap_n_main_ring'] + N * p['decap_n_main_cref'] + N * p['decap_n_main_cin']
    n_dac = 2 * p['decap_n_dac_corr']
    fp['supply'] = {
        'straps': [
            {'name': 'analog', 'net': 'VDD', 'feeds': 'bias_genc, %d x amp_ch.vdd, %d x adc_ch.vdd (vhalf, Cref switch, samb inverter, sampling-TG wells), TGATE wells' % (N, N), 'route': 'star point -> west ring -> both bias corridors (Metal5 over vss Metal4) -> spur corridor of each channel -> adc_ch.vdd', 'decap': 'none required (AUDIT 4.9.2)'},
            {'name': 'ADC-main', 'net': 'VDD', 'feeds': '%d x adc_ch.vdd_cmp, afe_dig VDD' % N, 'route': 'star point -> both strap corridors (Metal5, 8 um, over vss Metal4)', 'decap': '%d units = %.1f pF: west ring bank %d + under each Cref %d x %d + under the Cin pieces %d x %d + corridor west ends %d x 2' % (n_main, n_main * ff / 1e3, p['decap_n_main_ring'], p['decap_n_main_cref'], N, p['decap_n_main_cin'], N, p['decap_n_main_corr'])},
            {'name': 'ADC-DAC', 'net': 'vdd_dac', 'feeds': '%d x adc_ch.vdd_dac' % N, 'route': 'star point -> strap resistor %s %g x %g um (10.0 ohm typ) in the north strap corridor -> both strap corridors (Metal5, 5 um)' % tuple(p['rstrap']), 'decap': '%d units = %.1f pF: one row of %d units in each strap corridor, under the straps' % (n_dac, n_dac * ff / 1e3, p['decap_n_dac_corr'])}],
        'decap_unit': {'device': 'cap_nmos_03v3', 'c_width': du[0], 'c_length': du[1], 'fF': r3(ff), 'pcell_footprint': [22.16, 22.41]},
        'decap_n_main': n_main, 'decap_n_dac': n_dac, 'decap_pF_main': r3(n_main * ff / 1e3), 'decap_pF_dac': r3(n_dac * ff / 1e3),
        'lvs_command': 'python3 AFE/layout/scripts/mk_lvs_netlists.py --decap %g,%g --decap-n %d,%d --rstrap %s,%g,%g --dig-netlist <powered afe_dig netlist>' % (du[0], du[1], n_main, n_dac, p['rstrap'][0], p['rstrap'][1], p['rstrap'][2]),
        'reserve': 'Decision 46c lever (proved on test cell lp_cin_decap): up to 16 more units per channel under the four Cin pieces (top-level overlap, Metal3 shield on vss), on the ADC-main strap through the spur corridor'}
    used = N * p['ch_pitch'] * ch_h + p['dig_w'] * p['dig_h'] + (core1 - bx0) * (by1 - by0)
    fp['area'] = {
        'outline_um2': W * H, 'core_um2': r3((core1 - core0) * (coreY1 - core0)),
        'slots_um2': {'amp_ch': r3(cell_w * amp_h), 'adc_ch': r3(cell_w * p['adc_h']), 'afe_ch': r3(p['ch_pitch'] * ch_h), 'bias_genc': r3((core1 - bx0) * (by1 - by0)), 'afe_dig': r3(p['dig_w'] * p['dig_h'])},
        'estimates_um2': EST, 'estimates_source': EST_SRC,
        'margin': {'amp_ch': r3(cell_w * amp_h / EST['amp_ch'] - 1), 'adc_ch': r3(cell_w * p['adc_h'] / EST['adc_ch'] - 1), 'bias_genc': r3((core1 - bx0) * (by1 - by0) / EST['bias_genc'] - 1),
                   'afe_dig_utilisation': r3(EST['afe_dig_cells'] / (p['dig_w'] * p['dig_h']))},
        'blocks_placed_um2': r3(used), 'overhead_um2': r3(W * H - used),
        'statement': 'slot / estimate - 1 (the estimates already contain block factors 1.5 / 2.5 on transistor groups and MIM spacing). Decap needs NO area of its own in this plan '
                     '(strap corridors, west ring, under Cref%s); the top-level factor that the outline allows on the F1 block sum without decap (618,660 um2 for 8 channels%s) is %.2f' % (', under Cin' if p['decap_n_main_cin'] else '', '' if N == 8 else '; scaled by %d / 8 for %d channels, ESTIMATE' % (N, N), W * H / (618660.0 * N / 8.0))}
    fp['rules'] = {
        'grid_um': 0.005,
        'keepout_digital_um': 20.0,
        'keepout_digital_nets': 'SCLK CS DIN DOUT cmp_clk dac_gp* dac_gn* dac_gdn rst_sw tg_on (and every net inside afe_dig)',
        'keepout_digital_nodes': 'summing nodes vn / vp / vn2, pseudo-resistor nodes, rec, the Cref node vref, the DAC top plates t and m',
        'keepout_exception': 'the last <= 10 um of a control net at the device it drives; the quasi-static nets sw_rec sw_rec_b sw_ipg sw_ipg_b rst_amp fs (they move only at a mode change)',
        'keepout_adc_supply_um': 5.0,
        'no_routing_over_cells': 'the top level routes only in the ring, the corridors and the two side corridors of each channel slot; nothing crosses amp_ch or adc_ch',
        'mim': 'MIMTM.10 no Via3 on a bottom plate; MIMTM.11 at most 10,000 um2 of MIM on one Metal4 polygon (REF, rec leave the plates through Via4 / Metal5)',
        'tgate': 'every TGATE instance has one gf180mcu_fd_sc_mcu7t5v0__filltie abutted (test cell lp_tgate_tap)'}
    return fp


# ----------------------------------------------------------------------------------------------- checks
def verilog_ports(path, mod='dbs_afe_top'):
    txt = re.sub(r'//[^\n]*', '', open(path).read())
    m = re.search(r'module\s+%s\s*\((.*?)\);' % mod, txt, flags=re.S)
    bits = []
    for decl in re.split(r',\s*(?=(?:input|output|inout)\b)', m.group(1)):
        mm = re.match(r'\s*(input|output|inout)\s*(?:wire\s*)?(\[\s*(\d+)\s*:\s*(\d+)\s*\])?\s*(.*)', decl, flags=re.S)
        if not mm:
            continue
        for nm in [x.strip() for x in mm.group(5).split(',') if x.strip()]:
            if mm.group(2):
                hi, lo = int(mm.group(3)), int(mm.group(4))
                bits += ['%s[%d]' % (nm, i) for i in range(min(hi, lo), max(hi, lo) + 1)]
            else:
                bits.append(nm)
    return bits


def info_pads(path):
    pads, name = [], None
    for ln in open(path):
        m = re.match(r'\s*-\s*name:\s*"?([^"#\n]+?)"?\s*(#.*)?$', ln)
        if m:
            name = m.group(1).strip()
        m = re.match(r'\s*io_type:\s*(\w+)', ln)
        if m and name:
            pads.append((name, m.group(1)))
            name = None
    return pads


def overlap(a, b):
    return min(a[2], b[2]) - max(a[0], b[0]) > 1e-6 and min(a[3], b[3]) - max(a[1], b[1]) > 1e-6


def check(args):
    res = []

    def R(ok, what, detail=''):
        res.append(ok)
        print('%s  %s%s' % ('PASS' if ok else 'FAIL', what, ('  ' + detail) if detail else ''))
    if not os.path.exists(FP):
        R(False, 'AFE/layout/floorplan.json exists', 'run: python3 AFE/layout/scripts/floorplan.py build')
        return 1
    fp = json.load(open(FP))
    ref = json.loads(json.dumps(build(fp['params'])))
    R(ref == fp, '1  floorplan.json is what floorplan.py builds from its stored params (not edited by hand)', '' if ref == fp else 'run `floorplan.py build --set ...` instead of editing the file')
    W, O = fp['outline'][2], fp['outline'][3]
    N = int(fp['params'].get('n_ch', 8))
    rects = [(q['inst'], [q['x'], q['y'], q['x'] + q['w'], q['y'] + q['h']]) for q in fp['placements']] + [(q['name'], q['rect']) for q in fp['zones']]
    bad = [n for n, r in rects if r[0] < -1e-6 or r[1] < -1e-6 or r[2] > W + 1e-6 or r[3] > O + 1e-6]
    R(not bad, '2a every block and corridor lies inside the %g x %g um outline' % (W, O), ', '.join(bad))
    ov = []
    names = [n for n, _ in rects]
    for i in range(len(rects)):
        for j in range(i + 1, len(rects)):
            a, b = rects[i], rects[j]
            ring_pair = a[0].startswith('ring') and b[0].startswith('ring')           # the four ring strips share the corners on purpose
            if overlap(a[1], b[1]) and not ring_pair:
                ov.append('%s/%s' % (a[0], b[0]))
    R(not ov, '2b no two blocks / corridors overlap (%d rectangles)' % len(rects), ', '.join(ov))
    sub = fp['cells']['afe_ch']['sub']
    sb = [(k, v) for k, v in sub.items()]
    ov2 = ['%s/%s' % (sb[i][0], sb[j][0]) for i in range(len(sb)) for j in range(i + 1, len(sb)) if overlap(sb[i][1], sb[j][1])]
    cov = sum((v[2] - v[0]) * (v[3] - v[1]) for v in sub.values())
    R(not ov2 and abs(cov - fp['cells']['afe_ch']['w'] * fp['cells']['afe_ch']['h']) < 1e-3, '2c the channel slot is exactly tiled by control corridor, adc_ch, amp_ch, TGATE zone and spur corridor', ', '.join(ov2))
    # pins against the Verilog top and info.yaml
    bits = verilog_ports(os.path.join(REPO, 'AFE/top/dbs_afe_top.v'))
    pn = [q['name'] for q in fp['pins']]
    miss, extra, dup = [b for b in bits if b not in pn], [x for x in pn if x not in bits], sorted(set(x for x in pn if pn.count(x) > 1))
    R(not miss and not extra and not dup, '3a every port bit of module dbs_afe_top is exactly one floorplan pin (%d bits, %d pins)' % (len(bits), len(pn)),
      ' '.join(['missing: %s' % miss] * bool(miss) + ['not a port: %s' % extra] * bool(extra) + ['twice: %s' % dup] * bool(dup)))
    pads = info_pads(os.path.join(REPO, 'info.yaml'))
    need, bad_t = [], []
    for name, typ in pads:
        if typ not in PAD_TYPES:
            bad_t.append('%s:%s' % (name, typ))
            continue
        need += [(name + s, name) for s in PAD_TYPES[typ]]
    nn = [a for a, _ in need]
    miss = [a for a in nn if a not in bits]
    extra = [b for b in bits if b not in nn]
    dup = sorted(set(a for a in nn if nn.count(a) > 1))
    R(not miss and not extra and not dup and not bad_t and len(pads) == 2 * N + 8, '3b info.yaml: %d pads (want 2 x n_ch + 8); each pad has exactly the ports the organizer template asks for its io_type, and no port is left over' % len(pads),
      ' '.join(['ports missing in the top: %s' % miss] * bool(miss) + ['top ports without a pad: %s' % extra] * bool(extra) + ['twice: %s' % dup] * bool(dup) + ['unknown io_type: %s' % bad_t] * bool(bad_t)))
    padof = dict(need)
    wrong = [q['name'] for q in fp['pins'] if padof.get(q['name']) != q['pad']]
    R(not wrong, '3c every floorplan pin names the pad of info.yaml it belongs to', ', '.join(wrong))
    onedge = [q['name'] for q in fp['pins'] if not ((q['side'] == 'W' and q['x'] == 0) or (q['side'] == 'E' and q['x'] == W) or (q['side'] == 'S' and q['y'] == 0) or (q['side'] == 'N' and q['y'] == O))]
    R(not onedge, '3d every pin is on the outline edge it names', ', '.join(onedge))
    close = []
    for s in 'NSEW':
        ps = sorted((q['x'] if s in 'NS' else q['y'], q['w'], q['name']) for q in fp['pins'] if q['side'] == s)
        close += ['%s/%s' % (a[2], b[2]) for a, b in zip(ps, ps[1:]) if b[0] - a[0] < (a[1] + b[1]) / 2.0 + 0.5]
    R(not close, '3e no two pins of one edge touch (>= 0.5 um between pin shapes)', ', '.join(close))
    # macro pins: every afe_dig signal exactly once
    dp = [q['name'] for e in 'NSW' for q in fp['cells']['afe_dig']['pins'][e]]
    want = ['CS', 'SCLK', 'DIN', 'RSTN', 'DOUT', 'DOUT_OE', 'rst_amp_o'] + ['%s[%d]' % (b, i) for b in ('sw_rec', 'sw_rec_b', 'sw_ipg', 'sw_ipg_b', 'cmp_q', 'cmp_clk', 'rst_sw', 'tg_on', 'dac_gdn') for i in range(N)] \
        + ['%s[%d]' % (b, i) for b in ('dac_gp', 'dac_gn') for i in range(12 * N)] + ['DOUT_IE', 'DOUT_PD', 'DOUT_PU', 'DOUT_CS', 'DOUT_SL', 'DOUT_PDRV0', 'DOUT_PDRV1', 'CS_PU', 'CS_PD', 'DIN_PU', 'DIN_PD', 'SCLK_PU', 'SCLK_PD', 'RSTN_PU', 'RSTN_PD']
    R(sorted(dp) == sorted(want), '3f the afe_dig contract lists every macro signal pin exactly once (%d pins + VDD / VSS)' % len(want),
      'missing %s, extra %s' % ([x for x in want if x not in dp][:6], [x for x in dp if x not in want][:6]) if sorted(dp) != sorted(want) else '')
    lastx = max(q['x'] for q in fp['cells']['afe_dig']['pins']['N'])
    R(lastx < fp['params']['dig_w'] - 2.0, '3g the last pin of the macro pin groups (x = %g um) is on the macro (width %g um)' % (lastx, fp['params']['dig_w']))
    # area
    mg = fp['area']['margin']
    R(mg['amp_ch'] >= 0.10 and mg['adc_ch'] >= 0.10 and mg['bias_genc'] >= 0.10, '4a slot / estimate - 1: amp_ch %+.0f %%, adc_ch %+.0f %%, bias_genc %+.0f %% (>= 10 %% each; estimates: AFE/review/sim/f1_area.log)' % (
        100 * mg['amp_ch'], 100 * mg['adc_ch'], 100 * mg['bias_genc']))
    R(0.30 <= mg['afe_dig_utilisation'] <= 0.60, '4b afe_dig: %.0f %% utilisation of %g x %g um with the estimated cell area (30-60 %%)' % (100 * mg['afe_dig_utilisation'], fp['params']['dig_w'], fp['params']['dig_h']))
    s = fp['supply']
    pp = fp['params']
    R(s['decap_pF_main'] >= pp.get('decap_min_main_pF', 115.0) and s['decap_pF_dac'] >= pp.get('decap_min_dac_pF', 95.0), '4c decap: ADC-main %.1f pF in %d units (>= %g), ADC-DAC %.1f pF in %d units (>= %g); Decision 44d (0.125 + 0.1 nF for 8 ADCs), Decision 52' % (
        s['decap_pF_main'], s['decap_n_main'], pp.get('decap_min_main_pF', 115.0), s['decap_pF_dac'], s['decap_n_dac'], pp.get('decap_min_dac_pF', 95.0)))
    p = fp['params']
    row = p['decap_n_dac_corr'] + p['decap_n_main_corr']
    R(row * 24.0 <= p['dig_w'] + 1e-6 and p['strap_corr'] >= 25.0, '4d one decap row of %d units (24 um pitch) fits the %g um strap corridor length and its %g um height (unit 22.16 x 22.41 um)' % (row, p['dig_w'], p['strap_corr']))
    R(p['decap_n_main_ring'] * 24.0 <= O - 2 * 40.0, '4e the west ring bank of %d units (24 um pitch) fits between y = 40 and %g' % (p['decap_n_main_ring'], O - 40.0))
    # as-built cells
    for kv in args.gds or []:
        cell, path = kv.split('=', 1)
        import subprocess
        o = subprocess.run([sys.executable, os.path.join(HERE, 'flow.py'), 'info', '--gds', path, '--top', cell], capture_output=True, text=True)
        try:
            t = json.loads(o.stdout)['tops'][0]
        except Exception:                                    # noqa
            R(False, '5  as-built %s: %s could not be read' % (cell, path), o.stdout[-200:] + o.stderr[-200:])
            continue
        w, h = t['w_um'], t['h_um']
        if cell == 'dbs_afe_top':
            R(w <= W + 1e-6 and h <= O + 1e-6, '5  as-built dbs_afe_top %.3f x %.3f um <= outline %g x %g' % (w, h, W, O))
            continue
        c = fp['cells'].get(cell)
        if c is None:
            R(False, '5  as-built %s: no such cell in floorplan.json' % cell)
            continue
        wm, hm = c.get('w_max', c.get('w')), c.get('h_max', c.get('h'))
        fits = (w <= wm + 1e-6 and h <= hm + 1e-6)
        rot = (h <= wm + 1e-6 and w <= hm + 1e-6)
        R(fits or rot, '5  as-built %s %.2f x %.2f um fits its slot %.2f x %.2f um%s' % (cell, w, h, wm, hm, '' if fits else (' ONLY ROTATED by 90 degrees' if rot else '')),
          '' if (fits or rot) else 'see AFE/layout/ACCEPT.md ladder "area"')
    if args.dig_pins:
        try:
            dj = json.load(open(args.dig_pins))
            got = {q['name']: q for q in (dj['pins'] if isinstance(dj, dict) else dj)}
            badp = []
            for e in 'NSW':
                for q in fp['cells']['afe_dig']['pins'][e]:
                    g = got.get(q['name'])
                    if g is None:
                        badp.append(q['name'] + ' missing')
                    elif str(g.get('side', e))[0].upper() != e:
                        badp.append('%s on side %s, contract %s' % (q['name'], g.get('side'), e))
                    elif e in 'NS' and abs(g['x_um'] - q['x']) > 1.5:
                        badp.append('%s x %.2f, contract %.2f' % (q['name'], g['x_um'], q['x']))
                    elif e == 'W' and abs(g['y_um'] - q['y']) > 2.5:
                        badp.append('%s y %.2f, contract %.2f' % (q['name'], g['y_um'], q['y']))
            R(not badp, '6  the hardened afe_dig pins (%s) are on the contract side, N / S pins within 1.5 um and W pins within 2.5 um of the contract position' % args.dig_pins, '; '.join(badp[:8]))
            if isinstance(dj, dict) and 'die_w_um' in dj:
                R(dj['die_w_um'] <= p['dig_w'] + 1e-6 and dj['die_h_um'] <= p['dig_h'] + 1e-6, '6  hardened afe_dig die %.2f x %.2f um <= the slot %g x %g' % (dj['die_w_um'], dj['die_h_um'], p['dig_w'], p['dig_h']))
        except Exception as e:                               # noqa
            R(False, '6  macro pin table %s' % args.dig_pins, repr(e))
    n = len(res) - sum(res)
    print('floorplan.py check: %d PASS, %d FAIL' % (sum(res), n))
    return 1 if n else 0


def main():
    import argparse
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('cmd', choices=('build', 'check'))
    ap.add_argument('--set', nargs='*', default=[])
    ap.add_argument('--gds', nargs='*', default=[])
    ap.add_argument('--dig-pins', default=None)
    a = ap.parse_args()
    if a.cmd == 'build':
        p = dict(PARAMS)
        if os.path.exists(FP):
            old = json.load(open(FP)).get('params', {})
            p.update({k: v for k, v in old.items() if k in p and k != 'pin_source' and old.get('_overrides', {}).get(k)})
            p['_overrides'] = dict(old.get('_overrides', {}))
        p.setdefault('_overrides', {})
        for kv in a.set:
            k, v = kv.split('=', 1)
            if k not in PARAMS:
                sys.exit('unknown parameter %s; known: %s' % (k, ', '.join(sorted(PARAMS))))
            p[k] = json.loads(v) if not isinstance(PARAMS[k], str) else v
            p['_overrides'][k] = True
        fp = build(p)
        json.dump(fp, open(FP, 'w'), indent=1)
        open(FP, 'a').write('\n')
        c = fp['cells']
        print('wrote %s: channel slot %g x %g um, amp_ch <= %g x %g, adc_ch <= %g x %g, bias_genc <= %g x %g, afe_dig %g x %g; margins amp %+.0f %%, adc %+.0f %%, bias %+.0f %%' % (
            os.path.relpath(FP, REPO), c['afe_ch']['w'], c['afe_ch']['h'], c['amp_ch']['w_max'], c['amp_ch']['h_max'], c['adc_ch']['w_max'], c['adc_ch']['h_max'], c['bias_genc']['w_max'], c['bias_genc']['h_max'],
            c['afe_dig']['w'], c['afe_dig']['h'], 100 * fp['area']['margin']['amp_ch'], 100 * fp['area']['margin']['adc_ch'], 100 * fp['area']['margin']['bias_genc']))
        return 0
    return check(a)


def picture(out):
    """floorplan boxes as GDS (run through kl.sh)"""
    import kpdk as k
    import pya
    fp = json.load(open(FP))
    ly = k.new_layout()
    top = ly.create_cell('floorplan_picture')
    W, O = fp['outline'][2], fp['outline'][3]
    k.rect(top, 'pr_bndry', 0, 0, W, O)

    def box(layer, r, text):
        top.shapes(ly.layer(*layer)).insert(pya.Box(*[k.u(v, ly) for v in r]))
        top.shapes(ly.layer(63, 0)).insert(pya.Text(text, pya.Trans(k.u(r[0] + 1, ly), k.u((r[1] + r[3]) / 2.0, ly))))
    for z in fp['zones']:
        box((200, 0), z['rect'], z['name'])
    for q in fp['placements']:
        if q['cell'] != 'afe_ch':
            box((201, 0), [q['x'], q['y'], q['x'] + q['w'], q['y'] + q['h']], q['inst'] + ' ' + q['cell'])
            continue
        for nm, r in fp['cells']['afe_ch']['sub'].items():
            y0, y1 = (q['y'] + r[1], q['y'] + r[3]) if q['orient'] == 'R0' else (q['y'] + q['h'] - r[3], q['y'] + q['h'] - r[1])
            box((202, 0), [q['x'] + r[0], y0, q['x'] + r[2], y1], '%s %s' % (q['inst'], nm))
    for q in fp['pins']:
        w = q['w'] / 2.0
        r = [q['x'] - w, q['y'] - 1, q['x'] + w, q['y'] + 1] if q['side'] in 'NS' else [q['x'] - 1, q['y'] - w, q['x'] + 1, q['y'] + w]
        box((203, 0), [max(0, r[0]), max(0, r[1]), min(W, r[2]), min(O, r[3])], q['name'])
    k.write(ly, out)
    print('wrote %s' % out)


if 'out' in globals() and os.environ.get('KL_SCRIPT'):
    picture(globals()['out'])
elif __name__ == '__main__':
    sys.exit(main())
