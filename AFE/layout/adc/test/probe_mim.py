import sys
sys.path.insert(0, 'AFE/layout/amp')
import kpdk as k, amplib as a
ly = k.new_layout()
for w, l in ((5.0, 5.0), (5.085, 5.0), (59.07, 59.07), (22.18, 22.18)):
    m = a.info_mim(ly, w, l)
    print(w, l, 'tp', m.tp, 'bp', m.bp, 'm5', m.m5)
    c = m.cell
    for ln in ('via4', 'via3', 'metal4', 'metal5', 'fusetop', 'cap_mk', 'mim_l_mk'):
        r = a.region(ly, c, ln)
        b = r.bbox()
        print('  ', ln, r.count(), (b.left * ly.dbu, b.bottom * ly.dbu, b.right * ly.dbu, b.top * ly.dbu))
