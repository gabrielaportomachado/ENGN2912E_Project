import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.environ["KL_SCRIPT"]), ".."))
import kpdk as k
import adclib as a
import dac_lib as D

out = globals().get('out', 'AFE/layout/adc/test/o')
os.makedirs(out, exist_ok=True)
ly = k.new_layout()
top = ly.create_cell('dactest')
d = D.build(top, 10.0, 9.8)
bb = top.dbbox()
print('array bbox %.2f x %.2f' % (bb.width(), bb.height()), 'rows y', [round(v, 2) for v in d.ys], 'channel centre', d.ych)
print('sites', len(d.sites))
nets = set()
for (net, half, r, xp, yp) in d.pads:
    if net == 'br':
        continue
    k.label(top, 'metal4', net, xp, yp)
    nets.add(net)
k.label(top, 'metal5', 't', d.xT_t, d.ys[3] + 3.5)
k.label(top, 'metal5', 'm', d.xT_m, d.ys[3] + 3.5)
nets |= {'t', 'm'}
ref = []
for i, (tag, nt, nb, x, y, w) in enumerate(d.sites):
    if tag.startswith('dummy'):
        continue
    ref.append('X%d %s %s cap_mim_2f0_m4m5_noshield c_length=5u c_width=%su' % (i, nt, nb, ('%.6g' % (5.082993 if tag == 'br' else 5.0))))
pins = sorted(nets)
open(os.path.join(out, 'dactest.ref.spice'), 'w').write('.subckt dactest %s\n%s\n.ends\n' % (' '.join(pins), '\n'.join(ref)))
k.write(ly, os.path.join(out, 'dactest.gds'), 'dactest')
