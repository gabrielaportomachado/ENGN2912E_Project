#!/usr/bin/env python3
"""A1 plots + summary from sim/*.csv (no .raw). Run: python3 scripts/plots_a1.py"""
import os, glob, csv
import numpy as np
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
R = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
S, F = os.path.join(R, "sim"), os.path.join(R, "figs")
os.makedirs(F, exist_ok=True)

def gmid_fig(t):
    plt.figure(figsize=(5.5, 4))
    for L in ["0.5u", "1u", "2u", "4u"]:
        d = np.loadtxt(os.path.join(S, f"char_gmid_{t}_l{L}.csv"))
        idw, gm = d[:, 5], d[:, 3]          # wrdata: x y x y ...
        k = idw > 1e-9
        plt.loglog(idw[k], gm[k], label=f"L={L}")
    plt.xlabel("Id/(W/L) [A]"); plt.ylabel("gm/Id [1/V]"); plt.grid(True, which="both", alpha=.3)
    plt.title(f"{'nfet' if t=='n' else 'pfet'}_03v3, typ, 27C, |Vds|=0.5 V"); plt.legend()
    plt.tight_layout(); plt.savefig(os.path.join(F, f"gmid_{t}.png"), dpi=130); plt.close()
gmid_fig("n"); gmid_fig("p")

def rd(p):
    with open(p) as f:
        r = list(csv.reader(f, delimiter=" ", skipinitialspace=True))
    h = [x for x in r[0] if x]; rows = [[x for x in l if x] for l in r[1:]]
    return h, rows

# single-device noise vs W*L
plt.figure(figsize=(5.5, 4))
for t, mk in (("p", "o"), ("n", "s")):
    h, rows = rd(os.path.join(S, f"char_noise_{t}.csv"))
    for fn, ls in (("0", "-"), ("1", "--")):
        pts = [(float(r[1])*50e-6*float(r[2].replace("u", "e-6"))*1e12, float(r[-1])*1e6)
               for r in rows if r[0] == fn and r[3] == "10u"]
        a = np.array(pts)
        plt.loglog(a[:, 0], a[:, 1], mk+ls, label=f"{t}fet fnoicor={fn}")
plt.xlabel("W*L [um^2]"); plt.ylabel("input-referred noise 0.5-300 Hz [uV rms]")
plt.title("single device, Id=10 uA, typ 27C"); plt.grid(True, which="both", alpha=.3); plt.legend(fontsize=7)
plt.tight_layout(); plt.savefig(os.path.join(F, "noise_vs_area.png"), dpi=130); plt.close()

# recommended-pair spectrum
plt.figure(figsize=(5.5, 4))
for fn in (0, 1):
    d = np.loadtxt(os.path.join(S, f"char_ota5t_spectrum_fn{fn}.csv"))
    plt.loglog(d[:, 0], d[:, 1]*1e9, label=f"fnoicor={fn}")
plt.axvspan(0.5, 300, color="gray", alpha=.15)
plt.xlabel("f [Hz]"); plt.ylabel("input-referred [nV/rtHz]"); plt.grid(True, which="both", alpha=.3)
plt.title("5T OTA, pair 16x50u/2u, load 4x50u/8u, Id=10u/side"); plt.legend()
plt.tight_layout(); plt.savefig(os.path.join(F, "ota5t_spectrum.png"), dpi=130); plt.close()

# recommendation table: OTA noise incl. Cgg noise-gain factor (Cin=20 pF, Cf=0.2 pF: ESTIMATE inputs)
h, ota = rd(os.path.join(S, "char_ota5t_load.csv"))
h2, pn = rd(os.path.join(S, "char_noise_p.csv"))
cgg = {(r[1], r[2]): float(r[6]) for r in pn if r[0] == "0" and r[3] == "10u"}
out = ["pair(Mx50u/L) load(Mx50u/L)  area_um2  Cgg_pF  vn_typ  vn_fn1  vn_typ*(Cin+Cf+Cgg)/Cin  [uV rms, 0.5-300 Hz]"]
for r in ota:
    if r[0] != "0": continue
    pl, pm, ll, lm, v0 = r[1], r[2], r[3], r[4], float(r[5])
    v1 = [float(x[5]) for x in ota if x[0] == "1" and x[1:5] == r[1:5]][0]
    area = 2*float(pm)*50*float(pl[:-1]) + 2*float(lm)*50*float(ll[:-1])
    cg = cgg.get((pm, pl)); 
    if cg is None: continue
    f = (20e-12 + 0.2e-12 + cg)/20e-12
    out.append(f"{pm}x50u/{pl:<3} {lm}x50u/{ll:<4} {area:8.0f} {cg*1e12:6.2f} {v0*1e6:6.2f} {v1*1e6:6.2f} {v0*f*1e6:6.2f}")
open(os.path.join(S, "a1_summary.txt"), "w").write("\n".join(out)+"\n")
print("\n".join(out))
