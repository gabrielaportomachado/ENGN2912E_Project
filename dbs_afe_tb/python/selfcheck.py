"""Simulator-free checks of the Python side (frame helpers + analog model). Run: python3 -I selfcheck.py"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np  # noqa: E402

import afe_model as am  # noqa: E402
import spi  # noqa: E402

# --- frame helpers against the worked example of SPI_FRAME.md section 3
assert spi.config_word(1, 0, 1, 0xF) == 0xA00F
assert spi.status_word(0, 1, 0b0011) == 0xA4C0
assert spi.status_word(0, 1, 0xF) == 0xA7C0
assert spi.status_word() == 0xA000
w = spi.expected_frame(0, 1, 0b0011, [2018, 2032, 2048, 2008])
assert w == [0xA4C0, 0x07E2, 0x47F0, 0x8800, 0xC7D8], [hex(x) for x in w]
assert spi.bits_to_words(spi.words_to_bits(w)) == w
assert spi.decode(w)["codes"] == [2018, 2032, 2048, 2008]
print("spi helpers: OK")

# --- gain: 0.45 mV pk sine at 100 Hz should come out at ~0.45 V pk (60 dB)
t = np.arange(int(1.0 * am.FS_HI)) / am.FS_HI
y = am.amplifier(0.45e-3 * np.sin(2 * np.pi * 100 * t))
pk = (y[len(y) // 2:] - am.VCM_OUT).max()
assert abs(pk - 0.45) < 0.02, pk
print(f"gain @100 Hz: pk {pk * 1e3:.0f} mV for 0.45 mV in -> OK")

# --- rest level: no input -> code ~2018
y0 = am.amplifier(np.zeros(1000))
assert abs(int(am.v_to_code(y0)[500]) - 2018) <= 1
print("rest code 2018: OK")

# --- DC electrode offset is removed (AC coupling): 50 mV DC in, mean out ~ mid-scale
x, _ = am.neural_signal(2.0, seed=3, dc_mv=50.0)
assert abs(am.amplifier(x)[-1000:].mean() - am.VCM_OUT) < 0.1
print("DC offset removed: OK")

# --- spike detection at 4 kS/s through the front end
fe = am.FrontEnd(2.0, seed=1)
tot = [0, 0, 0]
for ch in range(4):
    codes = np.array([fe.codes(k, 0xF, 1, 0)[ch] for k in range(100, fe.n_frames)])
    truth = fe.truth[ch][fe.truth[ch] > 100 / am.FS_FRAME] - 100 / am.FS_FRAME
    h, m, f = am.match(am.detect_spikes(codes), truth)
    print(f"ch{ch}: truth {len(truth)} hits {h} miss {m} false {f}")
    tot = [a + b for a, b in zip(tot, (h, m, f))]
assert tot[0] >= 0.8 * (tot[0] + tot[1]) and tot[2] <= 0.1 * (tot[0] + tot[1]) + 1, tot
print("spike detection: OK", tot)

# --- gating

assert fe.codes(10, 0, 1, 0) == [2018] * 4 and fe.codes(10, 0xF, 0, 0) == [2018] * 4 and fe.codes(10, 0xF, 1, 1) == [2018] * 4
print("gating: OK")