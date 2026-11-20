import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.environ["KL_SCRIPT"]), ".."))
import kpdk as k
import adclib as a
import cmp_lib as CL
ly = k.new_layout()
pair, N, P, C = CL.side(ly, 'x')
for n, b in (('pair', pair), ('N', N), ('P', P), ('C', C)):
    print(n, [round(v, 1) for v in b.bbox], 'size', [round(v, 1) for v in b.size])
S = CL.side_cell(ly)
print('side', [round(v, 1) for v in S.bbox], S.parts, S.failed)
