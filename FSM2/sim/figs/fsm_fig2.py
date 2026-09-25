#!/usr/bin/env python3
"""Figure 2: frequency independence overlay, normalized to clock periods.

Run from anywhere: python3 fsm_fig2.py
"""
import os

from fsm_common import (
    SIM_DIR, COLORS, MUTED, INK,
    load_wrdata, apply_poster_style, save_fig,
)
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from matplotlib.patches import ConnectionPatch
import numpy as np


def make_figure():
    files = [
        ("100 kHz", "fsm2_fmax_5v0_100k.txt", "-"),
        ("1 MHz", "fsm2_fmax_5v0_1M.txt", "--"),
        ("10 MHz", "fsm2_fmax_5v0_10M.txt", "-."),
        ("100 MHz", "fsm2_fmax_5v0_100M.txt", ":"),
    ]
    datasets = [(label, load_wrdata(os.path.join(SIM_DIR, fname)), ls)
                for label, fname, ls in files]
    dec = slice(None, None, 20)

    fig = plt.figure(figsize=(14, 11))
    gs = fig.add_gridspec(1, 1, top=0.88, bottom=0.42, left=0.09, right=0.97)
    ax = fig.add_subplot(gs[0])

    for label, d, ls in datasets:
        periods = d.t * d.fclk
        ax.plot(periods[dec], d.rec_en[dec] / d.vdd, color=COLORS["REC_EN"],
                linestyle=ls, linewidth=2.0, alpha=0.9)
        ax.plot(periods[dec], d.treat_en[dec] / d.vdd, color=COLORS["TREAT_EN"],
                linestyle=ls, linewidth=2.0, alpha=0.9)

    ax.set_xlabel("Clock periods (t × f$_{CLK}$)")
    ax.set_ylabel("Normalized output (V / VDD)")
    ax.set_xlim(0, 24)
    ax.set_ylim(-0.15, 1.3)

    signal_handles = [
        Line2D([0], [0], color=COLORS["REC_EN"], lw=2.5, label="REC_EN"),
        Line2D([0], [0], color=COLORS["TREAT_EN"], lw=2.5, label="TREAT_EN"),
    ]
    leg1 = ax.legend(handles=signal_handles, loc="center right", bbox_to_anchor=(1.0, 0.6), title="Signal", frameon=False)
    ax.add_artist(leg1)
    freq_handles = [Line2D([0], [0], color=MUTED, lw=2, linestyle=ls, label=label)
                     for label, _, ls in files]
    ax.legend(handles=freq_handles, loc="lower right", bbox_to_anchor=(1.0, 0.15),
              title="f$_{CLK}$", frameon=False)

    # Auto-detect the first REC_EN rising edge from the cleanest (100 kHz) trace.
    ref_label, ref_d, _ = datasets[0]
    ref_periods = ref_d.t * ref_d.fclk
    above = ref_d.rec_en > (ref_d.vdd / 2.0)
    rising = np.where(np.diff(above.astype(int)) == 1)[0] + 1
    rising = rising[ref_periods[rising] > 0.1]
    p_edge = ref_periods[rising[0]]

    # Rise time is set by drive strength (~1 ns, roughly fixed in absolute
    # time), so relative to a shrinking clock period it grows from
    # negligible at 100 kHz to ~10% of a period at 100 MHz. A wide window
    # would make every trace look like a vertical step; a narrow one
    # actually reveals that growing relative edge width.
    win = 0.5
    ax.axvspan(p_edge - win, p_edge + win, color=MUTED, alpha=0.10, lw=0)

    # Place the zoom box directly below the main plot, its left edge aligned
    # with the main plot's y-axis.
    y_bottom = ax.get_ylim()[0]
    ins_w, ins_h = 0.30, 0.28
    ins_left = ax.get_position().x0
    ins_bottom = 0.08
    axins = fig.add_axes([ins_left, ins_bottom, ins_w, ins_h])

    for label, d, ls in datasets:
        periods = d.t * d.fclk
        mask = (periods > p_edge - win) & (periods < p_edge + win)
        axins.plot(periods[mask], d.rec_en[mask] / d.vdd, color=COLORS["REC_EN"],
                   linestyle=ls, linewidth=2.0)
    axins.set_xlim(p_edge - win, p_edge + win)
    # Extra headroom above/below the 0/1 rails leaves clear space for the
    # title and axis-label text to sit inside the box, off the traces.
    axins.set_ylim(-0.35, 1.35)
    axins.set_yticks([])
    axins.set_xticks([])
    axins.text(0.5, 0.93, "REC$_{EN}$ edge, zoomed (full resolution)",
               transform=axins.transAxes, ha="center", va="top",
               fontsize=14, color=INK)
    axins.text(0.5, 0.05, "Clock periods →", transform=axins.transAxes,
               ha="center", va="bottom", fontsize=12, color=MUTED)
    for spine in axins.spines.values():
        spine.set_visible(True)
        spine.set_color(MUTED)
        spine.set_linewidth(1.2)

    # Diagonal callout lines from the shaded region's bottom corners (main
    # plot) down to the top corners of the zoom box below.
    for x_main, x_inset in [(p_edge - win, 0.0), (p_edge + win, 1.0)]:
        con = ConnectionPatch(
            xyA=(x_main, y_bottom), coordsA=ax.transData,
            xyB=(x_inset, 1.0), coordsB=axins.transAxes,
            color=MUTED, linewidth=1.2, linestyle="-",
        )
        fig.add_artist(con)

    fig.suptitle("Frequency Independence — REC_EN / TREAT_EN vs. Clock Period (5.0 V)")
    save_fig(fig, "02_freq_independence")


def main():
    apply_poster_style()
    make_figure()


if __name__ == "__main__":
    main()
