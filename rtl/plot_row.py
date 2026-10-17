#!/usr/bin/env python3
"""ROW switch control from dbs_tb (RTL, channel 0), same layout as the ROW
poster figure (row_fig1.py).

usage: python3 plot_row.py   (after running dbs_tb, from anywhere)
"""
from plot_common import (
    SWITCH_COLORS, load_txt, decode_switch, state_segments, stacked, apply_poster_style,
)


def main():
    apply_poster_style()
    t_us, d = load_txt("dbs_tb_transitions.txt")
    segs = state_segments(t_us, decode_switch(d["sw_rec"], d["sw_ipg"]))
    panels = [
        ("CLK", d["clk"]), ("MODE", d["mode"]), ("RSTn", d["rstn"]), ("ENi", d["eni_q2"]),
        ("REC_EN", d["rec_en"]), ("TREAT_EN", d["treat_en"]),
        ("SW_REC", d["sw_rec"]), ("SW_IPG", d["sw_ipg"]),
    ]
    stacked(t_us, segs, SWITCH_COLORS, "Switch", panels,
            "ROW Switch Control (RTL, dbs.v, channel 0, 100kHz)", "rtl_row_waveforms",
            figsize=(14, 15))


if __name__ == "__main__":
    main()
