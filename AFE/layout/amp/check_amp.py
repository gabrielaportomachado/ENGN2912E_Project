"""check_amp.py (L2a): facts about the generated amp_ch that DRC / LVS do not test.
  bash AFE/layout/scripts/kl.sh AFE/layout/amp/check_amp.py gds=AFE/layout/amp/amp_ch.gds build=AFE/layout/amp/amp_ch.build.json outjson=AFE/layout/amp/check_amp.json
  - W x H, area of the blocks (Cin block incl. lanes / input pair + tail / the rest) for the report
  - Decision 46c: nothing of comp / poly / contact / Metal1-3 / Via1-3 / wells / implants inside the four Cin plate footprints (Metal4 plate outline)
  - the pin labels of the top cell (name, layer, position)
"""
import json
import pya
import kpdk as k

g = globals()
ly = pya.Layout()
ly.read(g['gds'])
top = ly.cell('amp_ch')
b = json.load(open(g['build']))
bb = top.dbbox()
res = dict(W=round(bb.width(), 2), H=round(bb.height(), 2), area_um2=round(bb.width() * bb.height(), 1))
c = b['cin']
X0, Y0, T, P = c['X0'], c['Y0'], c['T'], c['P']
under = {}
for (nm, pos) in (('A1', (0, 0)), ('B1', (P, 0)), ('B2', (0, P)), ('A2', (P, P))):
    x1, y1 = X0 + pos[0] - 0.6, Y0 + pos[1] - 0.6
    win = pya.Region(pya.Box(int(x1 / ly.dbu), int(y1 / ly.dbu), int((x1 + T + 1.2) / ly.dbu), int((y1 + T + 1.2) / ly.dbu)))
    cnt = {}
    for layer in ('comp', 'poly2', 'contact', 'metal1', 'via1', 'metal2', 'via2', 'metal3', 'via3', 'nwell', 'pplus', 'nplus'):
        r = pya.Region(top.begin_shapes_rec(k.li(ly, layer))) & win
        if not r.is_empty():
            cnt[layer] = round(r.area() * ly.dbu ** 2, 3)
    under[nm] = cnt
res['under_cin_plates_um2'] = under
res['under_cin_clean'] = all(not v for v in under.values())
pins = []
for li in ly.layer_indexes():
    info = ly.get_info(li)
    for s in top.shapes(li).each():
        if s.is_text():
            pins.append(dict(name=s.text_string, layer='%d/%d' % (info.layer, info.datatype), x=round(s.text_pos.x * ly.dbu, 2), y=round(s.text_pos.y * ly.dbu, 2)))
res['pins'] = sorted(pins, key=lambda p: p['name'])
bl = b['blocks']
area = lambda n: bl[n][0] * bl[n][1]
cin_blk = bl['cin'][0] * bl['cin'][1]
mim_col = sum(area(n) for n in ('ct', 'cin2', 'cc2', 'cf2', 'cc1', 'cf1', 'cf1p'))
allb = sum(area(n) for n in bl)
res['areas_um2'] = dict(cin_block=round(cin_blk), ota_p_group_pair_and_tail=round(area('ota_p')), stage1_n_mirror_xm6=round(area('mir') + area('xm6')),
                        stage2_and_sinks=round(sum(area(n) for n in ('sink1', 'xms', 'fol', 's2p', 's2pair', 's2tail'))),
                        small_devices_pr_oneshot_or2=round(sum(area(n) for n in ('sn', 'sp', 'or2', 'pr1', 'pr2', 'pr3'))), mim_outside_cin=round(mim_col), sum_of_blocks=round(allb))
json.dump(res, open(g.get('outjson', 'check_amp.json'), 'w'), indent=1)
print(json.dumps({k_: v for k_, v in res.items() if k_ != 'pins'}))
print('pins:', ' '.join('%s@%s(%g,%g)' % (p['name'], p['layer'], p['x'], p['y']) for p in res['pins']))
