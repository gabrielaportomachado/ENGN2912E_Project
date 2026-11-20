import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.environ["KL_SCRIPT"]), ".."))
import kpdk as k
import adclib as a
ly = k.new_layout()
for nf, w in ((2, 40.0), (4, 20.0), (5, 16.0), (8, 10.0), (10, 8.0)):
    b = a.dev_block(ly, 'pair%d' % nf, 'pfet', w, 0.5, nf, s_net='tl', d_nets='a', g_net='inx', bulk_net='vdd_cmp', ring=True)
    print(nf, w, [round(v, 1) for v in b.bbox], 'size', [round(v, 1) for v in b.size])
