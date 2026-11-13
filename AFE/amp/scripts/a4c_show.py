"""quick look: python3 a4c_show.py csv [t_ref] -> out/v1 vs time (mV from rest)"""
import sys, numpy as np
sys.path.insert(0, __file__.rsplit('/',1)[0]); import a4c_lib as L
d = L.load(sys.argv[1]); t = d['time']
rest = {k: np.interp(float(sys.argv[2]) if len(sys.argv)>2 else t[0], t, d[k]) for k in ['out','v1','vn1','vn2']}
pts = [float(x) for x in sys.argv[3:]] or [0.0999, 0.1, 0.10002, 0.1001, 0.101, 0.11, 0.2, 0.5, 1, 2]
print('rest', {k: round(v,5) for k,v in rest.items()}, 'tmax', t[-1], 'npts', len(t))
for p in pts:
    if p>t[-1]: break
    print('t=%-9g out-rest %9.3f mV  v1 %9.3f mV  vn1 %9.3f mV  vn2 %9.3f mV  fs %.2f vrs %.3f gm1 %.3f' % (p, 1e3*(np.interp(p,t,d['out'])-rest['out']), 1e3*(np.interp(p,t,d['v1'])-rest['v1']), 1e3*(np.interp(p,t,d['vn1'])-rest['vn1']), 1e3*(np.interp(p,t,d['vn2'])-rest['vn2']), np.interp(p,t,d['fs']), np.interp(p,t,d['vrs']), np.interp(p,t,d['gm1'])))
