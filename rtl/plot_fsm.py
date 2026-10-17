#!/usr/bin/env python3
"""FSM states from fsm_tb (RTL), same layout as FSM2/sim/figs/fsm_fig1.py.

usage: python3 plot_fsm.py   (after running fsm_tb, from anywhere)
"""
from plot_common import (
    STATE_COLORS, load_txt, decode_fsm, state_segments, stacked, apply_poster_style,
)


def main():
    apply_poster_style()
    t_us, d = load_txt("fsm_tb_transitions.txt")
    segs = state_segments(t_us, decode_fsm(d["s0"], d["s1"]))
    panels = [
        ("CLK", d["clk"]), ("MODE", d["mode"]), ("RSTn", d["rstn"]),
        ("S0", d["s0"]), ("REC_EN", d["rec_en"]), ("TREAT_EN", d["treat_en"]),
    ]
    stacked(t_us, segs, STATE_COLORS, "State", panels,
            "FSM States (RTL, dbs.v, 100kHz)", "rtl_fsm_waveforms", figsize=(14, 12))


if __name__ == "__main__":
    main()
