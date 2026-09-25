#!/usr/bin/env python3
"""Figure 3: state10 recovery, mode0 vs mode1 side by side.

Run from anywhere: python3 fsm_fig3.py
"""
import os

from fsm_common import (
    SIM_DIR, COLORS, STATE_COLORS, MUTED,
    load_wrdata, apply_poster_style, save_fig,
)
import matplotlib.pyplot as plt
import numpy as np


def make_figure():
    files = [
        ("MODE = 0 → TREAT", "fsm2_state10_5v0_mode0.txt"),
        ("MODE = 1 → REC", "fsm2_state10_5v0_mode1.txt"),
    ]
    fig, axes = plt.subplots(1, 2, figsize=(14, 6), sharey=True)
    for ax, (title, fname) in zip(axes, files):
        d = load_wrdata(os.path.join(SIM_DIR, fname))
        t_us = d.t * 1e6

        ax.plot(t_us, d.s0, color=COLORS["S0"], label="S0")
        ax.plot(t_us, d.rec_en, color=COLORS["REC_EN"], label="REC_EN [S1]")
        ax.plot(t_us, d.treat_en, color=COLORS["TREAT_EN"], label="TREAT_EN [(S0+S1)b]")

        ax.axvline(0, color=STATE_COLORS["STATE10"], linestyle=":", linewidth=1.5)
        ax.text(0.5, d.vdd * 1.16, "S1S0=10\n(forced IC)", fontsize=12,
                color=STATE_COLORS["STATE10"])

        above = d.clk > (d.vdd / 2.0)
        edge_idx = np.where(np.diff(above.astype(int)) == 1)[0]
        if len(edge_idx):
            t_edge = t_us[edge_idx[0] + 1]
            ax.axvline(t_edge, color=MUTED, linestyle="--", linewidth=1.5)
            ax.text(t_edge, d.vdd * 1.16, "1st CLK edge", fontsize=12, color=MUTED, ha="left")

        ax.set_title(title)
        ax.set_xlabel("Time (µs)")
        ax.set_ylim(-0.5, d.vdd * 1.35)

    axes[0].set_ylabel("Voltage (V)")
    axes[0].legend(loc="center right", frameon=False)
    fig.suptitle("Recovery from \"Don't Care\" State S1S0=10 (5.0 V)")
    fig.tight_layout()
    save_fig(fig, "03_state10_recovery")


def main():
    apply_poster_style()
    make_figure()


if __name__ == "__main__":
    main()
