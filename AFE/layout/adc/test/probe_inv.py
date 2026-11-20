import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.environ["KL_SCRIPT"]), ".."))
import kpdk as k
import pya

ly = k.new_layout()
std = os.path.join(k.PDK_ROOT, k.PDK, 'libs.ref/gf180mcu_fd_sc_mcu7t5v0/gds/gf180mcu_fd_sc_mcu7t5v0.gds')
for nm in ('gf180mcu_fd_sc_mcu7t5v0__inv_1', 'gf180mcu_fd_sc_mcu7t5v0__filltie'):
    c = k.import_gds(ly, std, nm)
    bb = c.dbbox()
    print(nm, 'bbox', bb.left, bb.bottom, bb.right, bb.top)
    for li in ly.layer_indexes():
        info = ly.get_info(li)
        r = pya.Region(c.begin_shapes_rec(li))
        if r.is_empty():
            continue
        print('  layer', info.layer, info.datatype, [(round(p.bbox().left * ly.dbu, 3), round(p.bbox().bottom * ly.dbu, 3), round(p.bbox().right * ly.dbu, 3), round(p.bbox().top * ly.dbu, 3)) for p in r.merged().each()][:8])
        for sh in c.shapes(li).each():
            if sh.is_text():
                print('    text', sh.text.string, sh.text.x * ly.dbu, sh.text.y * ly.dbu)
