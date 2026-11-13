"""A4c figures: (1) R_reset vs gate level, 3 corners (ladder tap rejected); (2) reset recovery waveforms (100 mV offset step, 3/10 ms pulse), typical/ff 85/ss -40."""
import sys, os, glob, numpy as np
sys.path.insert(0, os.path.dirname(__file__)); import a4c_lib as L
import matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt
AMP = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
fig, ax = plt.subplots(1, 2, figsize=(11, 4))
d = {}
for l in open(AMP + '/sim/a4c_prst.log'):
    if l.startswith('#'): continue
    p = l.split(); d.setdefault((p[0], p[1]), []).append((float(p[2]), float(p[3])))
for (c, T), v in d.items():
    v = np.array(sorted(v)); ax[0].semilogy(v[:, 0], v[:, 1], label=f'{c} {T} C')
ax[0].axhspan(2e7, 1e9, color='g', alpha=0.1); ax[0].set_xlabel('pseudo-R gate level (V), nodes at 1.65 V'); ax[0].set_ylabel('R pair (Ohm)'); ax[0].legend(); ax[0].set_title('R_reset vs gate level: 100x spread over PVT (ladder tap rejected)')
for c, T in [('typical', '27'), ('ff', '85'), ('ss', '-40')]:
    f = f'/tmp/a4crun/rec/{c}_{T}_os100m_w10m.csv'
    if not os.path.exists(f): continue
    r = L.load(f); t = r['time']; m = (t > 0.09) & (t < 0.16)
    ax[1].plot(1e3 * (t[m] - 0.1), 1e3 * (r['out'][m] - np.interp(0.09, t, r['out'])), label=f'out {c} {T} C')
ax[1].set_xlabel('ms from the 100 mV REC step (reset pulse 10 ms)'); ax[1].set_ylabel('output - rest (mV)'); ax[1].set_title('Recovery with the gate-switched reset'); ax[1].legend()
plt.tight_layout(); plt.savefig(AMP + '/figs/a4c_reset.png', dpi=110); print('wrote figs/a4c_reset.png')
