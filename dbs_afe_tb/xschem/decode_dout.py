#!/usr/bin/env python3
"""Decode the ngspice result of tb_dbs_afe_top (tb_out.txt: time cs sclk din dout e0 e1 vdd) back into SPI frames.

    python3 decode_dout.py build/tb_out.txt build/stim_frames.json [--discard 6e-3]

Checks (host rules): sync nibble / IDs of every frame, status read-back of every committed config,
then reports per-channel statistics and the gain at the 200 Hz tone on channel 1 (E1 = 0.45 mV pk sine, expect ~60 dB).
Only frames later than --discard after the record command are used for the analog numbers (reset pulse ~3.6 ms, then settling).
"""
import argparse
import json
import os
import sys

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "python"))
import afe_model as am  # noqa: E402
import spi  # noqa: E402

TH = 1.65


def frames_from_waves(t, cs, sclk, dout):
    """-> list of (t_cs_fall, bits) ; DOUT sampled at the last point BEFORE each SCLK rising edge."""
    cs_lo, sc_hi = cs < TH, sclk >= TH
    rise = np.where(sc_hi[1:] & ~sc_hi[:-1])[0] + 1
    fall_cs = np.where(cs_lo[1:] & ~cs_lo[:-1])[0] + 1
    out = []
    for j, f in enumerate(fall_cs):
        end = fall_cs[j + 1] if j + 1 < len(fall_cs) else len(t)
        edges = [i for i in rise if f <= i < end and cs_lo[i]]
        out.append((t[f], [int(dout[i - 1] >= TH) for i in edges]))
    return out


def tone_fit(ts, y, f):
    A = np.c_[np.sin(2 * np.pi * f * ts), np.cos(2 * np.pi * f * ts), np.ones_like(ts)]
    c, *_ = np.linalg.lstsq(A, y, rcond=None)
    return float(np.hypot(c[0], c[1])), float(c[2])


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("out_txt")
    ap.add_argument("frames_json")
    ap.add_argument("--discard", type=float, default=6e-3)
    a = ap.parse_args(argv)
    info = json.load(open(a.frames_json))
    d = np.loadtxt(a.out_txt, skiprows=1)
    t, cs, sclk, din, dout = d[:, 0], d[:, 1], d[:, 2], d[:, 3], d[:, 4]
    rx = frames_from_waves(t, cs, sclk, dout)
    print(f"{len(rx)} frames decoded, {len(info['frames'])} scheduled")
    errors, held = 0, (0, 0, 0)
    decoded = []
    for n, ((tf, bits), sched) in enumerate(zip(rx, info["frames"])):
        if len(bits) != 80:
            print(f"frame {n}: {len(bits)} edges (expected 80)")
            errors += 1
            continue
        w = spi.bits_to_words(bits)
        try:
            r = spi.decode(w)
        except ValueError as e:
            print(f"frame {n} @ {tf * 1e3:.3f} ms: {e}")
            errors += 1
            continue
        exp = spi.status_word(*held)
        if w[0] != exp:
            print(f"frame {n}: status {w[0]:#06x}, expected {exp:#06x}")
            errors += 1
        cfg = sched["cfg"]
        if cfg >> 15:
            held = ((cfg >> 14) & 1, (cfg >> 13) & 1, cfg & 0xF)
        decoded.append((tf, r["codes"]))
    print("protocol:", "PASS" if errors == 0 else f"FAIL ({errors} problems)")

    sel = [(tf, c) for tf, c in decoded if tf > info["t_rec"] + a.discard]
    if len(sel) < 20:
        print("too few frames after the discard window for analog numbers (raise --tstop or lower --discard)")
        return 1 if errors else 0
    ts = np.array([x[0] for x in sel])
    codes = np.array([x[1] for x in sel], dtype=float)
    print(f"analog window: {len(sel)} frames from {ts[0] * 1e3:.2f} ms")
    for c in range(4):
        print(f"  ch{c}: mean {codes[:, c].mean():8.1f}  std {codes[:, c].std():6.2f} LSB")
    amp, off = tone_fit(ts, codes[:, 1], info["tone_hz"])
    gain = amp * am.LSB_V / info["tone_amp"]
    print(f"ch1 tone {info['tone_hz']:g} Hz: {amp:.1f} LSB pk -> gain {gain:.0f} V/V = {20 * np.log10(gain):.1f} dB (target 60 dB)")
    ok = errors == 0 and 20 * np.log10(gain) > 54
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())