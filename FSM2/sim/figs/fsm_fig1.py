#!/usr/bin/env python3
"""Figure 1: stacked waveform panel with state-region annotation.

Run from anywhere: python3 fsm_fig1.py
"""
import os

from fsm_common import (
    SIM_DIR, COLORS, STATE_COLORS, INK,
    load_wrdata, decode_state, state_segments, apply_poster_style, save_fig,
)
import matplotlib.pyplot as plt


def make_figure():
    d = load_wrdata(os.path.join(SIM_DIR, "fsm2_transitions_5v0_100k.txt"))
    t_us = d.t * 1e6
    dec = slice(None, None, 20)

    signals = [
        ("CLK", d.clk), ("MODE", d.mode), ("RSTn", d.rstn),
        ("S0", d.s0), ("REC_EN", d.rec_en), ("TREAT_EN", d.treat_en),
    ]
    state = decode_state(d.rec_en, d.s0, d.vdd)
    segs = state_segments(t_us, state)

    n = len(signals)
    fig = plt.figure(figsize=(14, 12))
    gs = fig.add_gridspec(n + 1, 1, height_ratios=[0.5] + [1] * n, hspace=0.12)
    ax_state = fig.add_subplot(gs[0])
    sig_axes = [fig.add_subplot(gs[i + 1], sharex=ax_state) for i in range(n)]

    span_thresh = t_us[-1] * 0.02
    for t0, t1, label in segs:
        color = STATE_COLORS.get(label, "#ffffff")
        ax_state.axvspan(t0, t1, color=color, alpha=0.35, lw=0)
        if t1 - t0 > span_thresh:
            ax_state.text((t0 + t1) / 2, 0.5, label, ha="center", va="center",
                          fontsize=13, fontweight="bold", color=INK)
    ax_state.set_ylim(0, 1)
    ax_state.set_yticks([])
    ax_state.set_ylabel("State", rotation=0, ha="right", va="center")
    ax_state.grid(False)
    for spine in ax_state.spines.values():
        spine.set_visible(False)
    plt.setp(ax_state.get_xticklabels(), visible=False)

    for ax, (name, sig) in zip(sig_axes, signals):
        for t0, t1, label in segs:
            color = STATE_COLORS.get(label, "#ffffff")
            ax.axvspan(t0, t1, color=color, alpha=0.10, lw=0)
        ax.plot(t_us[dec], sig[dec], color=COLORS[name], linewidth=2.0)
        ax.set_ylabel(name, rotation=0, ha="right", va="center")
        ax.set_ylim(-0.5, d.vdd * 1.3)
        ax.set_yticks([0, d.vdd])

    for ax in sig_axes[:-1]:
        plt.setp(ax.get_xticklabels(), visible=False)
    sig_axes[-1].set_xlabel("Time (µs)")

    fig.suptitle("FSM2 States (5.0V, 100kHz, postPEX)", y=0.995, fontsize=22)
    save_fig(fig, "01_stacked_waveforms")


def main():
    apply_poster_style()
    make_figure()


if __name__ == "__main__":
    main()
