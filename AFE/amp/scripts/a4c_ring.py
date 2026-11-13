import sys, glob; sys.path.insert(0,'scripts')
import a4c_lib as L, numpy as np
for f in sorted(glob.glob('/tmp/a4crun/ring/*.csv')):
    d=L.load(f); t=d['time']; v=d['v1']
    m=(t>199.9e-6)&(t<400e-6)
    tt=t[m]; vv=v[m]; v0=np.interp(199e-6,t,v); vend=np.interp(399e-6,t,v)
    dv=vv-v0; dd=np.diff(vv); big=np.abs(dd)>2e-4
    print(f.split('/')[-1], 'v0 %.4f'%v0, 'peak |dv| %.1f mV'%(1e3*np.max(np.abs(dv))), 'dv(399us) %.1f mV'%(1e3*(vend-v0)), 'sign changes of dv/dt %d'%np.sum(np.diff(np.sign(dd[np.abs(dd)>1e-5]))!=0), 'v1 min/max %.3f %.3f'%(vv.min(),vv.max()))
