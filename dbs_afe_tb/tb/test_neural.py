"""System test: synthetic neural signal -> behavioral amplifier/ADC -> SPI frames -> host-side analysis.

Analog backend is selected with AFE_ANALOG (default 'behavioral'). 'ngspice' is a placeholder, see README.
Length: AFE_SECONDS (default 0.5 s = 2000 frames).  Spikes: 15 Hz firing, 150 uV, 1.9 uV rms noise, per channel.
"""
import os
import sys

import cocotb
import numpy as np
from cocotb.triggers import Timer

sys.path.insert(0, os.path.dirname(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "python"))
import afe_model as am  # noqa: E402
import spi  # noqa: E402
from afe_driver import frame_words, reset  # noqa: E402

SECONDS = float(os.environ.get("AFE_SECONDS", "0.5"))
FRAME_PERIOD_NS = 250_000
BACKEND = os.environ.get("AFE_ANALOG", "behavioral")


def make_frontend(seconds, **kw):
    if BACKEND == "behavioral":
        return am.FrontEnd(seconds, **kw)
    raise NotImplementedError("AFE_ANALOG=%s: only 'behavioral' exists so far (see README, analog levels)" % BACKEND)


async def acquire(dut, fe, n_frames, expect_connected):
    """Run n_frames at 4 kS/s. The 'analog' codes come from the front end given the DUT's HELD config."""
    rec = [[] for _ in range(4)]
    for k in range(n_frames):
        en, mode, rst = int(dut.en_o.value), int(dut.mode_o.value), int(dut.rst_amp_o.value)
        codes = fe.codes(k, en, mode, rst)
        w = await frame_words(dut, codes=codes)
        d = spi.decode(w)                               # raises on sync/ID errors (host rule 4)
        assert d["codes"] == codes, "SPI readback != analog codes"
        assert (d["en"], d["mode"], d["rst_amp"]) == (en, mode, rst)
        for c in range(4):
            rec[c].append(d["codes"][c])
        await Timer(FRAME_PERIOD_NS - 45_000, "ns")     # frame is ~40 us + overhead; pad to 250 us
    return [np.array(r) for r in rec]


@cocotb.test()
async def record_spikes_all_channels(dut):
    await reset(dut)
    fe = make_frontend(SECONDS + 0.1)
    n = int(SECONDS * am.FS_FRAME)
    await frame_words(dut, cfg=0xC000)                  # RST_AMP = 1, then 0 (power-up rule; shortened in sim)
    await Timer(1_000_000, "ns")
    await frame_words(dut, cfg=0x8000)
    await frame_words(dut, cfg=spi.config_word(1, 0, 1, 0xF))   # record on all four channels
    rec = await acquire(dut, fe, n, expect_connected=True)
    for c in range(4):
        sig = rec[c][50:]                                # skip the first frames (settling)
        mean = sig.mean()
        assert abs(mean - 2018) < 300, f"ch{c} mean {mean:.0f} outside +-300 LSB of 2018 (host offset rule)"
        times = am.detect_spikes(sig, k=5.0)
        truth = fe.truth[c][fe.truth[c] < (n - 50) / am.FS_FRAME] - 50 / am.FS_FRAME
        hits, miss, fa = am.match(times, truth)
        dut._log.info(f"ch{c}: truth {len(truth)} hits {hits} miss {miss} false {fa}")
        assert hits >= 0.8 * len(truth), f"ch{c}: only {hits}/{len(truth)} spikes found"
        assert fa <= max(1, 0.1 * len(truth)), f"ch{c}: {fa} false alarms"


@cocotb.test()
async def disabled_channels_stay_parked(dut):
    await reset(dut)
    fe = make_frontend(0.2)
    await frame_words(dut, cfg=spi.config_word(1, 0, 1, 0b0001))   # only channel 0 recording
    rec = await acquire(dut, fe, 300, expect_connected=False)
    assert rec[0].std() > 5, "enabled channel shows no signal"
    for c in (1, 2, 3):
        assert np.all(rec[c] == rec[c][0]), f"ch{c} not parked"
        assert abs(rec[c][0] - 2018) <= 1


@cocotb.test()
async def stimulate_mode_disconnects_amplifiers(dut):
    await reset(dut)
    fe = make_frontend(0.2)
    await frame_words(dut, cfg=spi.config_word(1, 0, 0, 0xF))      # MODE = 0 (stimulate): E -> IPG, amps parked
    rec = await acquire(dut, fe, 200, expect_connected=False)
    for c in range(4):
        assert np.all(rec[c] == rec[c][0])


@cocotb.test()
async def rst_amp_forces_midscale(dut):
    await reset(dut)
    fe = make_frontend(0.2)
    await frame_words(dut, cfg=spi.config_word(1, 1, 1, 0xF))      # record + RST_AMP held
    rec = await acquire(dut, fe, 100, expect_connected=False)
    for c in range(4):
        assert np.all(rec[c] == rec[c][0])