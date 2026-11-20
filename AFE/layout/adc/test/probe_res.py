import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.environ["KL_SCRIPT"]), ".."))
import kpdk as k
import pya

ly = k.new_layout()
k.lib()
print([n for n in k.PCELLS if 'res' in n.lower() or 'poly' in n.lower()])
c = k.pcell(ly, 'ppolyf_u_high_Rs_resistor', l_res=12.5, w_res=1.0)
bb = c.dbbox()
print('bbox', bb.left, bb.bottom, bb.right, bb.top)
for li in ly.layer_indexes():
    info = ly.get_info(li)
    r = pya.Region(c.begin_shapes_rec(li))
    if r.is_empty():
        continue
    print('  layer', info.layer, info.datatype, [(round(p.bbox().left * ly.dbu, 3), round(p.bbox().bottom * ly.dbu, 3), round(p.bbox().right * ly.dbu, 3), round(p.bbox().top * ly.dbu, 3)) for p in r.merged().each()][:6])
print(c.pcell_parameters_by_name() if hasattr(c, 'pcell_parameters_by_name') else '')
