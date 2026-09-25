#!/usr/bin/env python3
"""Figure 4: decoded state timeline (TREAT/BOTHOFF/REC) from S1S0 thresholding.

Run from anywhere: python3 fsm_fig4.py
"""
import os

from fsm_common import (
    SIM_DIR, STATE_COLORS, STATE_ORDER, INK,
    load_wrdata, decode_state, state_segments, apply_poster_style, save_fig,
)
import matplotlib.pyplot as plt
import numpy as np


def make_figure():
    d = load_wrdata(os.path.join(SIM_DIR, "fsm2_transitions_5v0_100k.txt"))
    t_us = d.t * 1e6
    state = decode_state(d.rec_en, d.s0, d.vdd)
    y_map = {s: i for i, s in enumerate(STATE_ORDER)}
    y = np.array([y_map.get(s, -1) for s in state], dtype=float)
    dec = slice(None, None, 20)

    segs = state_segments(t_us, state)
    fig, ax = plt.subplots(figsize=(14, 4))
    for t0, t1, label in segs:
        color = STATE_COLORS.get(label, "#ffffff")
        ax.axvspan(t0, t1, color=color, alpha=0.15, lw=0)

    ax.step(t_us[dec], y[dec], where="post", color=INK, linewidth=2.0)
    ax.set_yticks([y_map[s] for s in STATE_ORDER])
    ax.set_yticklabels(STATE_ORDER)
    ax.set_xlabel("Time (µs)")
    ax.set_ylabel("Decoded state")
    ax.set_ylim(-0.5, 2.5)
    fig.suptitle("Decoded FSM State — S1S0 thresholded at VDD/2 (5.0 V, 100 kHz)")
    fig.tight_layout()
    save_fig(fig, "04_decoded_state")


def main():
    apply_poster_style()
    make_figure()


if __name__ == "__main__":
    main()
