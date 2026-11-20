#!/usr/bin/env python3
"""LP step 5: which standard-cell PAIR drives sw_rec / sw_rec_b (and sw_ipg / sw_ipg_b) from ONE node with the least skew (I0 mismatch 8)?
OpenSTA, liberty only (no wires): one input x, every candidate inverter (true output) and buffer (complement) on it, loads 0.05 / 0.1 / 0.2 pF, input slew 0.3 ns,
corners tt_025C_3v30 / ff_n40C_3v60 / ss_125C_3v00.  skew = |t(inverter) - t(buffer)| for x rising and x falling.
usage: python3 sw_pair_cells.py [out.log]   (default AFE/dig/reports/sw_pair_cells.log)"""
import subprocess, itertools, re, os, sys, tempfile
HERE = os.path.dirname(os.path.abspath(__file__))
OUT = sys.argv[1] if len(sys.argv) > 1 else os.path.normpath(os.path.join(HERE, '..', 'reports', 'sw_pair_cells.log'))
LIB = '/foss/pdks/gf180mcuD/libs.ref/gf180mcu_fd_sc_mcu7t5v0/lib/gf180mcu_fd_sc_mcu7t5v0__%s.lib'
INVS = ['inv_1', 'inv_2', 'inv_3', 'inv_4', 'clkinv_2', 'clkinv_4']
BUFS = ['buf_1', 'buf_2', 'buf_3', 'buf_4', 'buf_8', 'clkbuf_2', 'clkbuf_4', 'clkbuf_8']
CORN = ['tt_025C_3v30', 'ff_n40C_3v60', 'ss_125C_3v00']
LOADS = ['0.05', '0.1', '0.2']
d = tempfile.mkdtemp(prefix='swpair_')
v = 'module pair (input x' + ''.join(', output o_%s' % c for c in INVS + BUFS) + ');\n'
v += ''.join('  gf180mcu_fd_sc_mcu7t5v0__%s u_%s (.I(x), .ZN(o_%s));\n' % (c, c, c) for c in INVS)
v += ''.join('  gf180mcu_fd_sc_mcu7t5v0__%s u_%s (.I(x), .Z(o_%s));\n' % (c, c, c) for c in BUFS) + 'endmodule\n'
open(os.path.join(d, 'sw.v'), 'w').write(v)
open(os.path.join(d, 'sw.tcl'), 'w').write('''read_liberty $::env(LIBF)
read_verilog sw.v
link_design pair
set_input_transition 0.3 [get_ports x]
set_load $::env(LOADPF) [all_outputs]
foreach p [get_ports o_*] { foreach {t o} {R -rise_from F -fall_from} {
  set paths [find_timing_paths $o x -to $p -unconstrained -path_delay max]
  puts "D [get_full_name $p] $t [sta::time_sta_ui [[lindex $paths 0] data_arrival_time]]" } }
''')
res = {}
for c in CORN:
    for load in LOADS:
        out = subprocess.run(['sta', '-no_init', '-no_splash', '-exit', 'sw.tcl'], cwd=d, env=dict(os.environ, LIBF=LIB % c, LOADPF=load), capture_output=True, text=True).stdout
        for m in re.finditer(r'D o_(\S+) (\w) (\S+)', out):
            res[(c, load, m.group(1), m.group(2))] = float(m.group(3))
L = ['LP step 5: skew of the complementary output pair (true = inverter of x, complement = buffer of x), OpenSTA liberty delays, input slew 0.3 ns, no wires.',
     'x rising = the switch OPENS (x = dbs_ctrl sw_*_b), x falling = the switch CLOSES.  Columns: skew in ns for (x rise, x fall) at tt / ff_n40 / ss_125.',
     '%-9s %-9s | %-44s | %-44s | %-44s | worst' % ('inverter', 'buffer', 'load 0.05 pF', 'load 0.1 pF', 'load 0.2 pF')]
rows = []
for i, b in itertools.product(INVS, BUFS):
    sk = {ld: [abs(res[(c, ld, i, t)] - res[(c, ld, b, t)]) for c in CORN for t in 'RF'] for ld in LOADS}
    rows.append((max(max(s) for s in sk.values()), i, b, sk))
for w, i, b, sk in sorted(rows):
    L.append('%-9s %-9s | %s | %s | %s | %.3f' % (i, b, ' '.join('%.3f' % x for x in sk['0.05']), ' '.join('%.3f' % x for x in sk['0.1']), ' '.join('%.3f' % x for x in sk['0.2']), w))
w, i, b, sk = sorted(rows)[0]
L.append('PICK: %s + %s (smallest worst-case skew over 0.05-0.2 pF and the three corners: %.3f ns).  Absolute delays at 0.1 pF, tt: %s rise %.3f fall %.3f, %s rise %.3f fall %.3f ns (x edge).' % (
    i, b, w, i, res[('tt_025C_3v30', '0.1', i, 'R')], res[('tt_025C_3v30', '0.1', i, 'F')], b, res[('tt_025C_3v30', '0.1', b, 'R')], res[('tt_025C_3v30', '0.1', b, 'F')]))
open(OUT, 'w').write('\n'.join(L) + '\n')
print('\n'.join(L[:3] + L[3:9] + L[-1:]))
