#!/usr/bin/env python3
"""16-channel demo figure from dbs_tb_16ch: what we ask for (inputs) vs what
each channel's switch does (outputs), across three short experiments.

usage: python3 plot_16ch.py   (after running dbs_tb_16ch)
"""
import os

import numpy as np

RTL_DIR = os.path.dirname(os.path.abspath(__file__))
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.colors import ListedColormap  # noqa: E402
from matplotlib.colors import to_rgb  # noqa: E402
from matplotlib.patches import Patch  # noqa: E402

DATA = os.path.join(RTL_DIR, "sim", "dbs_tb_16ch.txt")
OUT = os.path.join(RTL_DIR, "sim", "dbs_16ch_demo")
N = 16


# Switch-state shading. OVERLAP (both switches closed) must never appear.
SWITCH_COLORS = {
    "REC": "#e34948",
    "IPG": "#4a3aa7",
    "OFF": "#c3c2b7",
    "OVERLAP": "#0b0b0b",
}

INK = "#0b0b0b"
MUTED = "#52514e"


def apply_poster_style():
    plt.rcParams.update({
        "font.size": 16,
        "axes.titlesize": 22,
        "axes.labelsize": 18,
        "xtick.labelsize": 14,
        "ytick.labelsize": 14,
        "legend.fontsize": 14,
        "lines.linewidth": 2.0,
        "axes.spines.top": False,
        "axes.spines.right": False,
        "axes.grid": True,
        "grid.color": "#e1e0d9",
        "grid.linewidth": 0.8,
        "text.color": INK,
        "axes.labelcolor": INK,
        "axes.edgecolor": "#898781",
        "xtick.color": "#898781",
        "ytick.color": "#898781",
        "figure.facecolor": "white",
        "axes.facecolor": "white",
        "savefig.facecolor": "white",
    })


def tint(color, alpha=0.30):
    """Opaque version of color drawn at alpha over white."""
    return tuple(1 - alpha * (1 - c) for c in to_rgb(color))


# light REC / TREAT colors shared by the MODE band and the switch-state map
REC_LIGHT = tint(SWITCH_COLORS["REC"])
IPG_LIGHT = tint(SWITCH_COLORS["IPG"])
OFF = "#ffffff"
EN_ON = "#b4b2a9"   # mid grey so the dashed experiment dividers stay visible

# must match dbs_tb_16ch.v
C_A, SEG = 2, 16
EXPERIMENTS = [
    ("A", "All channels enabled"),
    ("B", "Even channels only"),
    ("C", "Channels 0–7 only"),
]


def load():
    rows = []
    with open(DATA) as f:
        for line in f:
            if line.startswith("#"):
                continue
            c, rstn, mode, ready, _rec_en, _treat_en, en, sw_rec, sw_ipg = line.split()
            if "x" in en + sw_rec + sw_ipg:
                continue
            rows.append((float(c), int(rstn), int(mode), int(ready),
                         int(en, 16), int(sw_rec, 16), int(sw_ipg, 16)))
    a = np.array(rows, dtype=object)
    t = a[:, 0].astype(float)
    bits = lambda col: np.array([[(v >> k) & 1 for v in a[:, col]] for k in range(N)])
    return t, a[:, 1].astype(int), a[:, 2].astype(int), a[:, 3].astype(int), \
        bits(4), bits(5), bits(6)


# 16:9 slide width, landscape, sized to sit under a slide title (no figure title);
# font sizes in pt
LAYOUT = dict(out=OUT, figsize=(13.33, 5.9), ratios=[0.5, 3, 3],
              hspace=0.42, top=0.90, bottom=0.17, left=0.07, right=0.99,
              banner=14, band=12, panel=13, chan=10, xlabel=13, xtick=11, legend=12,
              legend_y=0.0, chan_step=2)


def make(L):
    t, rstn, mode, ready, en, sw_rec, sw_ipg = load()
    assert not (sw_rec & sw_ipg).any(), "overlap in data"
    dt = t[1] - t[0]
    extent = [t[0] - dt / 2, t[-1] + dt / 2, N - 0.5, -0.5]
    t_end = C_A + 3 * SEG

    fig = plt.figure(figsize=L["figsize"])
    gs = fig.add_gridspec(3, 1, height_ratios=L["ratios"], hspace=L["hspace"],
                          top=L["top"], bottom=L["bottom"], left=L["left"], right=L["right"])
    ax_mode = fig.add_subplot(gs[0])
    ax_en = fig.add_subplot(gs[1], sharex=ax_mode)
    ax_sw = fig.add_subplot(gs[2], sharex=ax_mode)

    # experiment banners and dividers
    for i, (tag, desc) in enumerate(EXPERIMENTS):
        x0 = C_A + i * SEG
        ax_mode.text(x0 + SEG / 2, 1.25, f"{tag}  ·  {desc}", ha="center", va="bottom",
                     fontsize=L["banner"], fontweight="bold", color=INK, transform=ax_mode.transData,
                     clip_on=False)
        for ax in (ax_mode, ax_en, ax_sw):
            ax.axvline(x0, color=MUTED, lw=1.2, ls="--", zorder=5)
    for ax in (ax_mode, ax_en, ax_sw):
        ax.axvline(t_end, color=MUTED, lw=1.2, ls="--", zorder=5)
        ax.axvspan(extent[0], C_A, color="#e1e0d9", alpha=0.6, lw=0, zorder=0)
    ax_mode.text(C_A / 2, 0.5, "reset", ha="center", va="center", fontsize=L["band"] - 2, color=MUTED)

    # MODE as a labeled band
    edges = np.flatnonzero(np.diff(mode)) + 1
    starts = np.concatenate(([0], edges))
    ends = np.concatenate((edges, [len(t)]))
    for s, e in zip(starts, ends):
        x0, x1 = max(t[s] - dt / 2, C_A), t[e - 1] + dt / 2
        if x1 <= C_A:
            continue
        rec = mode[s] == 1
        ax_mode.axvspan(x0, x1, color=REC_LIGHT if rec else IPG_LIGHT, lw=0)
        ax_mode.text((x0 + x1) / 2, 0.5, "REC" if rec else "TREAT",
                     ha="center", va="center", fontsize=L["band"], fontweight="bold", color=INK)
    ax_mode.set_ylim(0, 1)
    ax_mode.set_yticks([])
    ax_mode.set_ylabel("MODE", rotation=0, ha="right", va="center", fontsize=L["panel"])
    ax_mode.grid(False)
    for sp in ax_mode.spines.values():
        sp.set_visible(False)

    # EN inputs
    ax_en.imshow(en, aspect="auto", interpolation="nearest", extent=extent,
                 cmap=ListedColormap([OFF, EN_ON]), vmin=0, vmax=1)
    ax_en.set_title("Inputs: EN[k], which channels we ask to connect",
                    loc="left", fontsize=L["panel"], color=INK, pad=6)

    # switch state per channel: 0 off, 1 REC, 2 IPG
    state = sw_rec + 2 * sw_ipg
    ax_sw.imshow(state, aspect="auto", interpolation="nearest", extent=extent,
                 cmap=ListedColormap([OFF, REC_LIGHT, IPG_LIGHT]),
                 vmin=0, vmax=2)
    ax_sw.set_title("Outputs: switch state of each channel",
                    loc="left", fontsize=L["panel"], color=INK, pad=6)

    for ax in (ax_en, ax_sw):
        ticks = range(0, N, L["chan_step"])
        ax.set_yticks(ticks)
        ax.set_yticklabels([str(k) for k in ticks], fontsize=L["chan"])
        ax.set_ylabel("Channel", fontsize=L["panel"])
        ax.set_yticks(np.arange(-0.5, N, 1), minor=True)
        ax.grid(False)
        ax.grid(which="minor", axis="y", color="#e1e0d9", lw=1.0)
        ax.tick_params(which="minor", length=0)

    for ax in (ax_mode, ax_en):
        plt.setp(ax.get_xticklabels(), visible=False)
    ax_sw.set_xlim(extent[0], t_end + 0.5)
    ax_sw.set_xlabel("Clock cycle (100 kHz)", fontsize=L["xlabel"])
    ax_sw.tick_params(axis="x", labelsize=L["xtick"])

    fig.legend(handles=[
        Patch(color=EN_ON, label="EN = 1 (channel enabled)"),
        Patch(color=REC_LIGHT, label="Recording switch closed"),
        Patch(color=IPG_LIGHT, label="Stimulation (IPG) switch closed"),
        Patch(facecolor=OFF, edgecolor="#c3c2b7", label="Both switches open"),
    ], loc="lower center", ncol=4, frameon=False, fontsize=L["legend"],
       bbox_to_anchor=(0.54, L["legend_y"]))

    fig.savefig(L["out"] + ".png", dpi=300)
    fig.savefig(L["out"] + ".pdf")
    plt.close(fig)
    print(f"wrote {L['out']}.png / .pdf")


def main():
    apply_poster_style()
    make(LAYOUT)


if __name__ == "__main__":
    main()
