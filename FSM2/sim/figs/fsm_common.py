"""Shared loader, style, and helpers for the FSM2 poster figures.

Imported by fsm_fig1.py .. fsm_fig4.py — not run directly.
"""
import os
import re

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

FIGS_DIR = os.path.dirname(os.path.abspath(__file__))
SIM_DIR = os.path.dirname(FIGS_DIR)

# Fixed categorical colors, one per signal, shared across every figure
# (dataviz skill's validated CVD-safe palette, used in its documented order).
COLORS = {
    "CLK": "#2a78d6",
    "MODE": "#eb6834",
    "RSTn": "#1baf7a",
    "S0": "#eda100",
    "REC_EN": "#e87ba4",
    "TREAT_EN": "#008300",
}

# Distinct from the signal colors, used only for state-region shading/labels.
STATE_COLORS = {
    "TREAT": "#4a3aa7",
    "BOTHOFF": "#c3c2b7",
    "REC": "#e34948",
    "STATE10": "#898781",
}
STATE_ORDER = ["TREAT", "BOTHOFF", "REC"]

INK = "#0b0b0b"
MUTED = "#52514e"


# ---------------------------------------------------------------------------
# Reusable loader
# ---------------------------------------------------------------------------

class WrData:
    """Parsed ngspice wrdata file: 12 columns = 6 (time, signal) pairs."""

    def __init__(self, t, clk, mode, rstn, s0, rec_en, treat_en, vdd, fclk, path):
        self.t = t
        self.clk = clk
        self.mode = mode
        self.rstn = rstn
        self.s0 = s0
        self.rec_en = rec_en
        self.treat_en = treat_en
        self.vdd = vdd
        self.fclk = fclk
        self.path = path


def _parse_vdd(filename):
    m = re.search(r"(\d)v(\d)", filename)
    if not m:
        raise ValueError(f"Cannot infer VDD from filename: {filename}")
    return float(f"{m.group(1)}.{m.group(2)}")


def _parse_fclk(filename):
    m = re.search(r"_(\d+)([kM])\.txt$", filename)
    if not m:
        return None
    val, unit = m.groups()
    mult = 1e3 if unit == "k" else 1e6
    return float(val) * mult


def load_wrdata(path):
    """Load an ngspice wrdata file with 6 vectors (12 columns: time,sig x6).

    Column order verified against the actual data: time,CLK,time,MODE,
    time,RSTn,time,S0,time,REC_EN,time,TREAT_EN.
    """
    data = np.loadtxt(path)
    assert data.shape[1] == 12, f"{path}: expected 12 columns, got {data.shape[1]}"
    time_cols = data[:, [0, 2, 4, 6, 8, 10]]
    assert np.allclose(time_cols, time_cols[:, [0]]), (
        f"{path}: the 6 time columns are not identical; column order assumption is wrong"
    )
    fname = os.path.basename(path)
    return WrData(
        t=data[:, 0],
        clk=data[:, 1],
        mode=data[:, 3],
        rstn=data[:, 5],
        s0=data[:, 7],
        rec_en=data[:, 9],
        treat_en=data[:, 11],
        vdd=_parse_vdd(fname),
        fclk=_parse_fclk(fname),
        path=path,
    )


# ---------------------------------------------------------------------------
# State decode + segment helpers
# ---------------------------------------------------------------------------

def decode_state(rec_en, s0, vdd):
    """Gray-decode S1S0 by thresholding at VDD/2. rec_en carries S1."""
    thresh = vdd / 2.0
    s1b = rec_en > thresh
    s0b = s0 > thresh
    state = np.empty(s1b.shape, dtype=object)
    state[(~s1b) & (~s0b)] = "TREAT"     # 00
    state[(~s1b) & (s0b)] = "BOTHOFF"    # 01
    state[(s1b) & (s0b)] = "REC"         # 11
    state[(s1b) & (~s0b)] = "STATE10"    # 10 (unused)
    return state


def state_segments(t, state):
    """Collapse a per-sample state array into contiguous (t0, t1, label) runs."""
    change = np.where(state[1:] != state[:-1])[0] + 1
    starts = np.concatenate(([0], change))
    ends = np.concatenate((change, [len(state)]))
    return [(t[s], t[e - 1], state[s]) for s, e in zip(starts, ends)]


# ---------------------------------------------------------------------------
# Style
# ---------------------------------------------------------------------------

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
    fig.savefig(os.path.join(FIGS_DIR, f"{name}.png"), dpi=300, bbox_inches="tight")
    fig.savefig(os.path.join(FIGS_DIR, f"{name}.pdf"), bbox_inches="tight")
    plt.close(fig)
    print(f"  wrote {name}.png / {name}.pdf")
