#!/usr/bin/env python3
"""AUDIT step 4: run scripts/sta_audit.tcl (OpenSTA) on AFE/adc/lg/runs/d3/final for 5 lib corners x 3 SPEF corners and print the digital -> analog
arrival table.  usage: python3 sta_audit.py [out.log]     Raw sta output is cached in AFE/review/.ptmp/sta (re-used if present; delete to re-run)."""
import subprocess, re, os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
REV = os.path.normpath(os.path.join(HERE, '..'))
RUN = os.path.normpath(os.path.join(REV, '..', 'adc', 'lg', 'runs', 'd3', 'final'))
TMP = os.path.join(REV, '.ptmp', 'sta')
CORN = ['ff_n40C_3v60', 'ff_125C_3v60', 'tt_025C_3v30', 'ss_n40C_3v00', 'ss_125C_3v00']
SPEFS = ['nom', 'min', 'max']


def run(c, sp):
    os.makedirs(TMP, exist_ok=True)
    f = os.path.join(TMP, 'sta_%s_%s.txt' % (c, sp))
    if not os.path.exists(f):
        env = dict(os.environ, CORNER=c, RUN=RUN, SPEF=sp)
        txt = subprocess.run(['sta', '-no_init', '-no_splash', '-exit', os.path.join(HERE, 'sta_audit.tcl')], env=env, capture_output=True, text=True).stdout
        open(f, 'w').write(txt)
    return open(f).read()


def parse(txt):
    d = {}
    cap = {}
    tag = None
    for ln in txt.splitlines():
        if ln.startswith('@@ '):
            tag = ln[3:].strip()
            continue
        if tag is None:
            continue
        m = re.match(r'\S+ \((?:output|gf180\S+)\)\s+(-?INF|[-\d.]+)\s+([-\d.]+)\s+(-?INF|[-\d.]+)', ln)
        if m and not tag.startswith('CAPPATH') and not tag.startswith('RECOVERY') and not tag.startswith('MINPULSE'):
            d.setdefault(tag, float(m.group(2)))
            continue
        if tag.startswith('RECOVERY'):
            m = re.match(r'(\S+)/RN \((\S+)\)\s+([-\d.]+)\s+([-\d.]+)\s+([-\d.]+)', ln)
            if m:
                d.setdefault(tag, []).append((m.group(2).split('__')[-1], float(m.group(3)), float(m.group(4)), float(m.group(5))))
            continue
        if tag.startswith('MINPULSE'):
            m = re.match(r'(\S+) \((low|high)\)\s+([-\d.]+)\s+([-\d.]+)\s+([-\d.]+)', ln)
            if m:
                d['MINPULSE'] = (m.group(1), m.group(2), float(m.group(3)), float(m.group(4)))
            continue
        if tag.startswith('CAPPATH'):
            mm = re.match(r'CAPPATH (\d) P=([\d.]+) flop=(\S+)', tag)
            i, P, f = int(mm.group(1)), mm.group(2), mm.group(3)
            m = re.match(r'\s+[-\d.]+\s+([-\d.]+) \^ ' + re.escape(f) + r'/CLK', ln)
            if m and (i, P, 'clk') not in cap:
                cap[(i, P, 'clk')] = float(m.group(1))
            m = re.search(r'(-?[\d.]+)\s+slack', ln)
            if m:
                cap[(i, P, 'slack')] = float(m.group(1))
    d['cap'] = cap
    return d


def table(d):
    r = {}
    r['rise'] = [d['CMPCLK %d RISE MAX' % i] for i in range(8)]
    r['rise_min'] = [d['CMPCLK %d RISE MIN' % i] for i in range(8)]
    r['fall'] = [d['CMPCLK %d FALL MAX' % i] for i in range(8)]
    r['fall_min'] = [d['CMPCLK %d FALL MIN' % i] for i in range(8)]
    r['cap'] = [d['cap'].get((i, '500', 'clk')) for i in range(8)]
    r['slack333'] = [d['cap'].get((i, '333.333', 'slack')) for i in range(8)]
    r['slack500'] = [d['cap'].get((i, '500', 'slack')) for i in range(8)]
    g = lambda pre, mm: [d['%s %d %s' % (pre, k, mm)] for k in range(96)]
    r['gpgn_max'] = max(g('GP', 'MAX') + g('GN', 'MAX'))
    r['gpgn_min'] = min(g('GP', 'MIN') + g('GN', 'MIN'))
    r['gpgn_ch_max'] = [max([d['GP %d MAX' % k] for k in range(12 * i, 12 * i + 12)] + [d['GN %d MAX' % k] for k in range(12 * i, 12 * i + 12)]) for i in range(8)]
    r['gpgn_cs_max'] = max(g('GPCS', 'MAX') + g('GNCS', 'MAX'))
    r['gpgn_cs_ch_max'] = [max([d['GPCS %d MAX' % k] for k in range(12 * i, 12 * i + 12)] + [d['GNCS %d MAX' % k] for k in range(12 * i, 12 * i + 12)]) for i in range(8)]
    for p in ('rst_sw', 'tg_on', 'dac_gdn'):
        for e in ('TRKF', 'TRKR', 'TRKC'):
            r['%s_%s_max' % (e, p)] = [d['%s %s %d MAX' % (e, p, i)] for i in range(8)]
            r['%s_%s_min' % (e, p)] = [d['%s %s %d MIN' % (e, p, i)] for i in range(8)]
    r['dout_max'] = d['DOUT MAX'] - 250.0
    r['dout_min'] = d['DOUT MIN'] - 250.0
    r['dout_cs'] = d['DOUTCS MAX']
    r['doutoe'] = d['DOUTOE MAX']
    r['cfg_max'] = max([d['RSTAMP MAX'], d['MODE MAX']] + [d['EN %d MAX' % i] for i in range(8)])
    r['rec_cs'] = d.get('RECOVERY CS', [])
    r['minpulse'] = d.get('MINPULSE')
    return r


if __name__ == '__main__':
    out = open(sys.argv[1], 'w') if len(sys.argv) > 1 else sys.stdout
    P = lambda *a: print(*a, file=out)
    T = {(c, sp): table(parse(run(c, sp))) for c in CORN for sp in SPEFS}
    P('AUDIT step 4: OpenSTA on the CURRENT hardened adc8_top netlist (AFE/adc/lg/runs/d3/final/nl, built 2026-11-14 15:59, I1; no CTS: SCLK = one net, ideal edge at the port, propagated through the SPEF).')
    P('All times in ns after the SCLK rising edge at the port (or after the CS edge at the port where stated).  nom SPEF unless stated; [min..max SPEF] in brackets.')
    P('Not in this netlist: dbs_ctrl (sw_rec / sw_ipg), the pad cells, the wires from the macro pins to the analog cells.\n')
    P('1. COMPARATOR CLOCK WINDOWS  (rise = evaluate start, end = evaluate end, cap = capture-flop clock (tapw) arrival)')
    for c in CORN:
        t = T[(c, 'nom')]
        P('  == %s' % c)
        P('  ADC   rise    end      W     cap   Delta   cap->code slack @333.3 / @500')
        for i in range(8):
            P('  %d   %7.2f %7.2f %5.2f %7.2f %6s   %8.2f / %8.2f' % (i, t['rise'][i], t['fall'][i], t['fall'][i] - t['rise'][i], t['cap'][i], ('%.2f' % (t['rise'][i] - t['rise'][i - 1])) if i else '-', t['slack333'][i], t['slack500'][i]))
    P('\n2. SUMMARY PER CORNER')
    hdr = '  %-14s' + ' %9s' * 11
    P(hdr % ('corner', 'T0', 'Delta', 'W', 'ADC7rise', 'lastend', 'm@3MHz', 'm@2MHz', 'gp/gn min', 'gp/gn max', 'DAC->cmp0', 'DAC->cmp7'))
    for c in CORN:
        t = T[(c, 'nom')]
        dl = (t['rise'][7] - t['rise'][0]) / 7
        P(('  %-14s' + ' %9.2f' * 11) % (c, t['rise'][0], dl, t['fall'][0] - t['rise'][0], t['rise'][7], t['fall'][7], 333.333 - t['fall'][7], 500 - t['fall'][7], t['gpgn_min'], t['gpgn_max'],
                                         t['rise'][0] - t['gpgn_ch_max'][0], t['rise'][7] - t['gpgn_ch_max'][7]))
    P('  (m@3MHz / m@2MHz = SCLK period minus the end of the last window; DAC->cmp_i = rise_i minus the LATEST gp/gn arrival of ADC i = the time the DAC has to settle before its comparator fires)')
    P('  SPEF spread [min .. max] of T0 / last end:')
    for c in CORN:
        P('  %-14s T0 %.2f .. %.2f   last end %.2f .. %.2f   gp/gn max %.2f .. %.2f' % (c, T[(c, 'min')]['rise'][0], T[(c, 'max')]['rise'][0], T[(c, 'min')]['fall'][7], T[(c, 'max')]['fall'][7], T[(c, 'min')]['gpgn_max'], T[(c, 'max')]['gpgn_max']))
    P('\n3. SAMPLING (CS falling at the port -> switch gates at the macro pins), min / max over the 8 ADCs')
    P('  %-14s %-18s %-18s %-18s %-22s' % ('corner', 'rst_sw fall', 'tg_on fall', 'dac_gdn rise', 'tg_on - rst_sw (worst = min tg - max rst)'))
    for c in CORN:
        t = T[(c, 'nom')]
        P('  %-14s %6.2f .. %-8.2f %6.2f .. %-8.2f %6.2f .. %-8.2f %6.2f' % (c, min(t['TRKF_rst_sw_min']), max(t['TRKF_rst_sw_max']), min(t['TRKF_tg_on_min']), max(t['TRKF_tg_on_max']),
                                                                         min(t['TRKF_dac_gdn_min']), max(t['TRKF_dac_gdn_max']), min(t['TRKF_tg_on_min']) - max(t['TRKF_rst_sw_max'])))
    P('  sampling skew between the 8 channels = spread of rst_sw fall (max - min):')
    for c in CORN:
        t = T[(c, 'nom')]
        P('  %-14s %.3f ns' % (c, max(t['TRKF_rst_sw_max']) - min(t['TRKF_rst_sw_min'])))
    P('\n4. RESUME OF TRACKING after the done flop (SCLK edge 14+i -> gates), and ABORT (CS rising in mid-conversion)')
    P('  %-14s %-20s %-20s | %-20s %-22s %-22s %s' % ('corner', 'rst_sw rise (SCLK)', 'tg_on rise (SCLK)', 'tg_on rise (CS^) min', 'gp/gn release (CS^) max', 'per-ADC worst overlap', 'CONTENTION = release - tg_on'))
    for c in CORN:
        t = T[(c, 'nom')]
        ov = [t['gpgn_cs_ch_max'][i] - t['TRKR_tg_on_min'][i] for i in range(8)]
        P('  %-14s %6.2f .. %-10.2f %6.2f .. %-10.2f | %-20.2f %-22.2f %-22.2f %s' % (c, min(t['TRKC_rst_sw_min']), max(t['TRKC_rst_sw_max']), min(t['TRKC_tg_on_min']), max(t['TRKC_tg_on_max']),
                                                                                 min(t['TRKR_tg_on_min']), t['gpgn_cs_max'], max(ov), 'YES %.2f ns' % max(ov) if max(ov) > 0 else 'no'))
    P('  (normal frame: the drivers are released one whole SCLK period before the done flop, so there is no contention; the abort case is CS rising while drv_en = 1)')
    P('\n5. SERIAL / CONFIG OUTPUTS')
    P('  %-14s %-22s %-14s %-12s %-14s' % ('corner', 'DOUT after SCLK fall', 'DOUT after CS^', 'DOUT_OE', 'cfg outputs (rst_amp/mode/en) after SCLK 33'))
    for c in CORN:
        t = T[(c, 'nom')]
        P('  %-14s %6.2f .. %-12.2f %-14.2f %-12.2f %-14.2f' % (c, t['dout_min'], t['dout_max'], t['dout_cs'], t['doutoe'], t['cfg_max']))
    P('\n6. CS FALLING -> FIRST SCLK RISING (recovery of the frame flops; required t = 500 - slack with input delay 0), and min pulse width')
    for c in CORN:
        t = T[(c, 'nom')]
        rr = [x for x in t['rec_cs'] if 'dffrnq' in x[0]]
        w = min(x[3] for x in rr) if rr else float('nan')
        arr = max(x[2] for x in rr) if rr else float('nan')
        P('  %-14s CS fall -> RN arrival %.2f ns, recovery slack %.2f -> CS must fall >= %.2f ns before the first SCLK rising edge;  min pulse %s' % (c, arr, w, 500 - w, t['minpulse']))
    if out is not sys.stdout:
        out.close()
