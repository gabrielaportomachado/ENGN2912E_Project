import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.environ["KL_SCRIPT"]), ".."))
import kpdk as k
import adclib as a
import pya

ly = k.new_layout()
m = a.info_mim(ly, 59.07, 59.07)
r = a.region(ly, m.cell, 'via4')
print('via4 count', r.count(), 'bbox', r.bbox())
xs = sorted(set(round(p.bbox().left * ly.dbu, 3) for p in r.each()))
print(xs[:6], len(xs))
ft = a.region(ly, m.cell, 'fusetop').bbox()
print('fusetop', ft.left * ly.dbu, ft.right * ly.dbu)
