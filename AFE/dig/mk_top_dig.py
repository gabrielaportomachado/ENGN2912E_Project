#!/usr/bin/env python3
"""mk_top_dig.py (LP step 5 / L1d): writes AFE/dig/dbs_afe_top_dig.v = AFE/top/dbs_afe_top.v with the digital part replaced by ONE instance of the macro afe_dig.

AFE/top/dbs_afe_top.v is only READ (it stays the reference: it shows what is inside the macro).  In module dbs_afe_top this script
  - removes the instances u_adc (adc8_top) and u_dbs (dbs_ctrl) and the 15 constant pad-control assigns (`assign X = 1'b0 / 1'b1;`),
  - inserts `afe_dig u_dig (...)`: every connection is taken from the removed instances through the table DIG_PINS of AFE/layout/scripts/mk_lvs_netlists.py
    (the same table that builds the LVS top), the 15 tie pins connect to the top ports of the same name: nothing is typed twice,
  - adds two simulation aliases (mode_o, en_o: the testbenches read them hierarchically; they are internal nets of afe_dig).
Everything else (ports, bias, straps, the 8 channels, module afe_ch) is copied verbatim.
It STOPS if: the instances / the table do not match, u_dbs is not wired as the macro assumes (clk = the SCLK net of u_adc, rstn, mode_o, en_o, ready = 1'b1),
or the tie values of AFE/dig/afe_dig.v (tiel = 0, tieh = 1) differ from the constants assigned in AFE/top/dbs_afe_top.v.
usage: python3 mk_top_dig.py [out.v]        (default AFE/dig/dbs_afe_top_dig.v)"""
import os, re, sys, importlib.util
HERE = os.path.dirname(os.path.abspath(__file__))
AFE = os.path.normpath(os.path.join(HERE, '..'))
SRC = os.path.join(AFE, 'top', 'dbs_afe_top.v')
DIG = os.path.join(HERE, 'afe_dig.v')
OUT = sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, 'dbs_afe_top_dig.v')


def die(msg):
    sys.exit('mk_top_dig: STOP: ' + msg)


def load_tables():
    spec = importlib.util.spec_from_file_location('mk_lvs_netlists', os.path.join(AFE, 'layout', 'scripts', 'mk_lvs_netlists.py'))
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m.DIG_PINS, m.DIG_INTERNAL


def conns(stmt):
    """{port: expression} of one instance statement"""
    body = stmt[stmt.index('(', stmt.index(re.search(r'\bu_\w+\s*\(', stmt).group(0))):]
    return {m.group(1): m.group(2).strip() for m in re.finditer(r'\.(\w+)\s*\(([^()]*)\)', body)}


def tie_table_dig():
    t = {}
    for m in re.finditer(r'gf180mcu_fd_sc_mcu7t5v0__tie([hl])\s+u_tie_(\w+)\s*\(\s*\.(\w+)\s*\(\s*(\w+)\s*\)\s*\)', open(DIG).read()):
        hl, name, pin, net = m.groups()
        if net != name or pin != ('Z' if hl == 'h' else 'ZN'):
            die('afe_dig.v: tie cell u_tie_%s drives %s through pin %s' % (name, net, pin))
        t[name] = '1' if hl == 'h' else '0'
    return t


def main():
    DIG_PINS, DIG_INTERNAL = load_tables()
    txt = open(SRC).read()
    m = re.search(r'^module dbs_afe_top\b.*?^endmodule', txt, flags=re.S | re.M)
    if not m:
        die('module dbs_afe_top not found in ' + SRC)
    top = m.group(0)
    inst = {}
    for typ, name in (('adc8_top', 'u_adc'), ('dbs_ctrl', 'u_dbs')):
        mm = list(re.finditer(r'^[ \t]*%s\b[^;]*?\b%s\s*\(.*?\);[ \t]*\n' % (typ, name), top, flags=re.S | re.M))
        if len(mm) != 1:
            die('expected exactly one instance %s %s, found %d' % (typ, name, len(mm)))
        inst[name] = (mm[0].group(0), conns(mm[0].group(0)))
    # the macro's assumptions about what is inside
    for i1, p1, i2, p2 in DIG_INTERNAL:
        if inst[i1][1].get(p1) != inst[i2][1].get(p2):
            die('%s.%s (%s) and %s.%s (%s) are not the same net' % (i1, p1, inst[i1][1].get(p1), i2, p2, inst[i2][1].get(p2)))
    if inst['u_dbs'][1].get('ready') != "1'b1":
        die("u_dbs.ready is expected to be 1'b1")
    handled = set((i, p) for _, i, p in DIG_PINS) | set((a, b) for a, b, _, _ in DIG_INTERNAL) | set((c, d) for _, _, c, d in DIG_INTERNAL) | {('u_dbs', 'ready')}
    left = [(i, p) for i in inst for p in inst[i][1] if (i, p) not in handled]
    if left:
        die('connections %s are not in the table DIG_PINS' % left)
    # constant pad-control assigns
    ties = {mm.group(1): mm.group(2) for mm in re.finditer(r"assign\s+(\w+)\s*=\s*1'b([01])\s*;", top)}
    tdig = tie_table_dig()
    if ties != tdig:
        die('pad-control constants differ: dbs_afe_top.v %s, afe_dig.v tie cells %s' % (sorted(ties.items()), sorted(tdig.items())))
    # afe_dig drives DOUT_OE from its own inverter on CS: only valid while adc8_top defines dout_oe as ~cs_n
    adc_v = re.sub(r'//[^\n]*', '', open(os.path.join(AFE, 'adc', 'rtl', 'adc8_top.v')).read())
    if not re.search(r'assign\s+dout_oe\s*=\s*~\s*cs_n\s*;', adc_v):
        die('AFE/adc/rtl/adc8_top.v no longer says `assign dout_oe = ~cs_n;`: the DOUT_OE inverter u_oe of AFE/dig/afe_dig.v must be reviewed')
    if not re.search(r'clkinv_20\s+u_oe\s*\(\s*\.I\(CS\)\s*,\s*\.ZN\(DOUT_OE\)\s*\)', open(DIG).read()):
        die('AFE/dig/afe_dig.v: the DOUT_OE driver u_oe (clkinv_20 from CS) was not found')
    ports = re.search(r'^module afe_dig\b.*?^\);', re.sub(r'//[^\n]*', '', open(DIG).read()), flags=re.S | re.M).group(0)
    for pin, _, _ in DIG_PINS:
        if not re.search(r'\b%s\b' % pin, ports):
            die('afe_dig.v has no port %s' % pin)
    # ---- the afe_dig instance
    sig = ['.%s(%s)' % (pin, inst[i][1][p]) for pin, i, p in DIG_PINS]
    tie = ['.%s(%s)' % (n, n) for n in ties]
    lines, cur = [], '    afe_dig u_dig ('
    for c in sig + tie:
        if len(cur) + len(c) > 190:
            lines.append(cur.rstrip())
            cur = '                   '
        cur += c + ', '
    lines.append(cur.rstrip(', ') + ');')
    new_inst = ('    // ---- the digital macro afe_dig (AFE/dig/afe_dig.v) = adc8_top + dbs_ctrl #(8) + clock buffer + switch output pairs + the 15 pad-control tie cells ----\n'
                + '\n'.join(lines) + '\n'
                '    // simulation aliases: the testbenches read dut.mode_o / dut.en_o; in the chip they are internal nets of afe_dig\n'
                '    assign mode_o = u_dig.mode_o;\n    assign en_o = u_dig.en_o;\n')
    # the macro instance takes the place of the LATER of the two removed instances (every net it uses is declared above it)
    first, last = sorted(('u_adc', 'u_dbs'), key=lambda k: top.index(inst[k][0]))
    new = top.replace(inst[first][0], '').replace(inst[last][0], new_inst)
    n_removed = 0
    for n, v in ties.items():
        new, k = re.subn(r"assign\s+%s\s*=\s*1'b%s\s*;[ \t]*" % (n, v), '', new)
        n_removed += k
    if n_removed != len(ties):
        die('removed %d tie assigns, expected %d' % (n_removed, len(ties)))
    hdr = ('// GENERATED by AFE/dig/mk_top_dig.py from AFE/top/dbs_afe_top.v: DO NOT EDIT (edit the source or the script and run the script again).\n'
           '// Variant of the top with ONE afe_dig instance in place of u_adc (adc8_top) + u_dbs (dbs_ctrl) + the %d constant pad-control assigns (now tie cells inside afe_dig, Decision 46e).\n'
           '// Used by `bash AFE/top/run_top_sim.sh dig` (equivalence with the reference top) and as the picture of the layout hierarchy; the LVS top is AFE/layout/lvs/dbs_afe_top.spice.\n' % len(ties))
    out = hdr + txt.replace(top, new)
    open(OUT, 'w').write(out)
    print('mk_top_dig: %s written: afe_dig u_dig with %d signal connections (%d bits of table DIG_PINS) + %d tie pins (%s); u_adc, u_dbs and %d constant assigns removed' % (
        os.path.relpath(OUT, os.path.join(AFE, '..')), len(sig), len(DIG_PINS), len(tie), ' '.join('%s=%s' % kv for kv in ties.items()), n_removed))


if __name__ == '__main__':
    main()
