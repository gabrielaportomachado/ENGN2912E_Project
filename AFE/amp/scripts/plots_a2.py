import csv, collections
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
d = collections.defaultdict(list)
for r in list(csv.reader(open("../sim/char_pseudoR_iv.csv"), delimiter=" "))[1:]:
    d[(r[0], int(r[1]))].append((float(r[2]), float(r[3])))
fig, ax = plt.subplots(figsize=(6, 4))
for (c, T), v in d.items():
    ax.plot([x for x, _ in v], [abs(y) * 1e15 for _, y in v], label=f"{c} {T}C")
ax.set_yscale("log"); ax.set_xlabel("V across pseudo-R (mV)"); ax.set_ylabel("|I| (fA)")
ax.legend(fontsize=6, ncol=3); ax.grid(True, which="both", alpha=.3)
ax.set_title("pseudo_r 1u/2u, vt=0 (|I|; sign follows V)")
fig.tight_layout(); fig.savefig("../figs/pseudoR_iv.png", dpi=130)
# noise vs f_lo (ideal-R sweep)
fig, ax = plt.subplots(figsize=(6, 4))
rows = [r.split() for r in open("../sim/hpf_rsweep.csv")]
for cf in ("200f", "400f", "800f"):
    xs = [float(r[10]) for r in rows if r[3] == cf]; ys = [float(r[12]) * 1e6 for r in rows if r[3] == cf]
    ax.loglog(xs, ys, "o-", label=f"Cf={cf} (Cin=100 Cf)")
ax.axhline(1.37, color="k", ls="--", lw=.8); ax.text(0.015, 1.42, "budget 1.37 uV (OTA 1.46)", fontsize=7)
ax.set_xlabel("HPF -3 dB corner f_lo (Hz)"); ax.set_ylabel("input-ref. noise 0.5-300 Hz (uV)")
ax.grid(True, which="both", alpha=.3); ax.legend(fontsize=7)
fig.tight_layout(); fig.savefig("../figs/hpf_noise_vs_flo.png", dpi=130)
