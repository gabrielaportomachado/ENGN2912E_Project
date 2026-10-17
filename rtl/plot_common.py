"""Shared loader, style, and stacked-waveform layout for the RTL figures.

Same look as FSM2/sim/figs (fsm_common.py) and the ROW poster figures:
a labeled state band on top, one panel per signal underneath, every panel
shaded by the state. RTL signals are logic levels, so panels run 0..1.

Imported by plot_fsm.py and plot_row.py — not run directly.
"""
import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

RTL_DIR = os.path.dirname(os.path.abspath(__file__))
SIM_DIR = os.path.join(RTL_DIR, "sim")
FIGS_DIR = os.path.join(SIM_DIR, "figs")

# one color per signal, same as the FSM2 / ROW figures
COLORS = {
    "CLK": "#2a78d6",
    "MODE": "#eb6834",
    "RSTn": "#1baf7a",
    "S0": "#eda100",
    "ENi": "#eda100",
    "READY": "#eda100",
    "REC_EN": "#e87ba4",
    "TREAT_EN": "#008300",
    "SW_REC": "#e34948",
    "SW_IPG": "#4a3aa7",
}

# FSM state shading (fsm_common.py)
STATE_COLORS = {
    "TREAT": "#4a3aa7",
    "BOTHOFF": "#c3c2b7",
    "REC": "#e34948",
    "STATE10": "#898781",
}

# switch-state shading (row_common.py). OVERLAP must never appear.
SWITCH_COLORS = {
    "REC": "#e34948",
    "IPG": "#4a3aa7",
    "OFF": "#c3c2b7",
    "OVERLAP": "#0b0b0b",
}

INK = "#0b0b0b"
MUTED = "#52514e"


def load_txt(name, hex_cols=()):
    """Load a testbench dump: first column time (s), then 0/1 or hex columns.

    Returns (t_us, {column name: int array}); names come from the '#' header.
    """
    path = os.path.join(SIM_DIR, name)
    if not os.path.exists(path):
        raise FileNotFoundError(f"{path} not found — run the testbench first")
    with open(path) as f:
        header = f.readline().lstrip("#").split()
        rows = [line.split() for line in f if line.strip() and not line.startswith("#")]
    cols = header[:len(rows[0])]
    t_us = np.array([float(r[0]) for r in rows]) * 1e6
    data = {}
    for i, c in enumerate(cols[1:], start=1):
        base = 16 if c in hex_cols else 2
        # x/z (before reset settles) read as 0
        data[c] = np.array([int(r[i], base) if not set(r[i]) & set("xzXZ") else 0 for r in rows])
    return t_us, data


def decode_fsm(s0, s1):
    """{S1,S0}: 11 REC, 01 BOTHOFF, 00 TREAT, 10 unused (as in fsm_common.decode_state)."""
    state = np.empty(s0.shape, dtype=object)
    state[(s1 == 0) & (s0 == 0)] = "TREAT"
    state[(s1 == 0) & (s0 == 1)] = "BOTHOFF"
    state[(s1 == 1) & (s0 == 1)] = "REC"
    state[(s1 == 1) & (s0 == 0)] = "STATE10"
    return state


def decode_switch(sw_rec, sw_ipg):
    state = np.empty(sw_rec.shape, dtype=object)
    state[(sw_rec == 0) & (sw_ipg == 0)] = "OFF"
    state[(sw_rec == 1) & (sw_ipg == 0)] = "REC"
    state[(sw_rec == 0) & (sw_ipg == 1)] = "IPG"
    state[(sw_rec == 1) & (sw_ipg == 1)] = "OVERLAP"
    return state


def state_segments(t, state):
    """Collapse a per-sample state array into contiguous (t0, t1, label) runs."""
    change = np.where(state[1:] != state[:-1])[0] + 1
    starts = np.concatenate(([0], change))
    ends = np.concatenate((change, [len(state)]))
    return [(t[s], t[e] if e < len(t) else t[-1], state[s]) for s, e in zip(starts, ends)]


def draw_band(ax, segs, colors, label, fontsize=13):
    """Labeled state band on top of the stack."""
    span_thresh = (segs[-1][1] - segs[0][0]) * 0.02
    for t0, t1, s in segs:
        ax.axvspan(t0, t1, color=colors.get(s, "#ffffff"), alpha=0.35, lw=0)
        if t1 - t0 > span_thresh:
            ax.text((t0 + t1) / 2, 0.5, s, ha="center", va="center",
                    fontsize=fontsize, fontweight="bold", color=INK)
    ax.set_ylim(0, 1)
    ax.set_yticks([])
    ax.set_ylabel(label, rotation=0, ha="right", va="center")
    ax.grid(False)
    for spine in ax.spines.values():
        spine.set_visible(False)
    plt.setp(ax.get_xticklabels(), visible=False)


def draw_signal(ax, t_us, sig, color, label, segs, colors, ylabel_size=None):
    """One logic-level panel, shaded by the state underneath."""
    for t0, t1, s in segs:
        ax.axvspan(t0, t1, color=colors.get(s, "#ffffff"), alpha=0.10, lw=0)
    ax.step(t_us, sig, where="post", color=color, linewidth=2.0)
    ax.set_ylabel(label, rotation=0, ha="right", va="center", fontsize=ylabel_size)
    ax.set_ylim(-0.15, 1.3)
    ax.set_yticks([0, 1])


def stacked(t_us, segs, colors, band_label, panels, title, name, figsize, hspace=0.12):
    """Band + one panel per (label, signal). Returns nothing; saves the figure."""
    n = len(panels)
    fig = plt.figure(figsize=figsize)
    gs = fig.add_gridspec(n + 1, 1, height_ratios=[0.5] + [1] * n, hspace=hspace, top=0.95)
    ax_band = fig.add_subplot(gs[0])
    axes = [fig.add_subplot(gs[i + 1], sharex=ax_band) for i in range(n)]
    draw_band(ax_band, segs, colors, band_label)
    for ax, (label, sig) in zip(axes, panels):
        draw_signal(ax, t_us, sig, COLORS[label], label, segs, colors)
    for ax in axes[:-1]:
        plt.setp(ax.get_xticklabels(), visible=False)
    axes[-1].set_xlabel("Time (µs)")
    fig.suptitle(title, y=0.995, fontsize=22)
    save_fig(fig, name)


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


def save_fig(fig, name):
    os.makedirs(FIGS_DIR, exist_ok=True)
    fig.savefig(os.path.join(FIGS_DIR, f"{name}.png"), dpi=300, bbox_inches="tight")
    fig.savefig(os.path.join(FIGS_DIR, f"{name}.pdf"), bbox_inches="tight")
    plt.close(fig)
    print(f"  wrote figs/{name}.png / .pdf")
