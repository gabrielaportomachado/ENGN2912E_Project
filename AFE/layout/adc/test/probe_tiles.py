import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.environ["KL_SCRIPT"]), ".."))
import kpdk as k
import adclib as a

ly = k.new_layout()
for (kind, w, l) in (('nfet', 1.0, 0.28), ('pfet', 2.0, 0.28), ('nfet', 0.5, 0.28), ('nfet', 8.0, 0.5), ('pfet', 4.0, 0.28), ('pfet', 80.0, 0.5), ('nfet', 4.0, 0.28), ('nfet', 2.0, 0.28)):
    B = a.Block(ly, 'p_%s_%g_%g' % (kind, w, l))
    D = a.add_tile(B, kind, w, l, 0.0, 0.0, 's', 'd', 'g')
    print(kind, w, l, 'bbox', [round(v, 3) for v in B.bbox], 'comp', [round(v, 3) for v in D.comp], 'sd', [[round(v, 2) for v in s] for s in D.sd], 'g', [[round(v, 2) for v in g] for g in D.g])
    print('    terms', [(n, c, [round(v, 2) for v in r]) for (n, c, r) in B.terms])
