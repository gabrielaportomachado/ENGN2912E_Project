"""Digital protocol tests (SPI_FRAME.md): status/ID words, commit rule, reset, short frames."""
import os
import sys

import cocotb
from cocotb.triggers import Timer

sys.path.insert(0, os.path.dirname(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "python"))
import spi  # noqa: E402
from afe_driver import frame, frame_words, reset  # noqa: E402


@cocotb.test()
async def reset_status_is_a000(dut):
    await reset(dut)
    w = await frame_words(dut)
    assert w[0] == 0xA000, f"status after reset {w[0]:#06x}"
    assert spi.decode(w)["codes"] == [2018] * 4


@cocotb.test()
async def worked_example(dut):
    """SPI_FRAME.md section 3: held EN=0011 record, host writes EN=1111, codes 2018/2032/2048/2008."""
    await reset(dut)
    await frame(dut, cfg=spi.config_word(1, 0, 1, 0b0011))                      # set up the held config
    w = await frame_words(dut, cfg=0xA00F, codes=(2018, 2032, 2048, 2008))
    exp = [0xA4C0, 0x07E2, 0x47F0, 0x8800, 0xC7D8]
    assert w == exp, [hex(x) for x in w]
    w2 = await frame_words(dut)                                                  # read-back of the commit
    assert w2[0] == 0xA7C0, f"read-back {w2[0]:#06x}"
    assert int(dut.en_o.value) == 0xF and int(dut.mode_o.value) == 1


@cocotb.test()
async def wr0_changes_nothing(dut):
    await reset(dut)
    await frame(dut, cfg=spi.config_word(1, 0, 1, 0b0101))
    await frame(dut, cfg=spi.config_word(0, 1, 0, 0b1010))                      # WR = 0: must be ignored
    w = await frame_words(dut)
    assert w[0] == spi.status_word(0, 1, 0b0101), hex(w[0])


@cocotb.test()
async def rst_amp_is_a_held_level(dut):
    await reset(dut)
    await frame(dut, cfg=0xC000)                                                 # RST_AMP = 1
    assert int(dut.rst_amp_o.value) == 1
    for _ in range(5):                                                           # WR = 0 frames do not clear it
        await frame(dut)
        assert int(dut.rst_amp_o.value) == 1
    await frame(dut, cfg=0x8000)
    assert int(dut.rst_amp_o.value) == 0


@cocotb.test()
async def ids_and_codes_for_many_values(dut):
    await reset(dut)
    for base in (0, 1, 0x555, 0xAAA, 0xFFF, 2018):
        codes = [(base + 17 * i) & 0xFFF for i in range(4)]
        d = spi.decode(await frame_words(dut, codes=codes))
        assert d["codes"] == codes


@cocotb.test()
async def short_frame_commits_nothing(dut):
    await reset(dut)
    await frame(dut, cfg=spi.config_word(1, 0, 1, 0xF), n_edges=16)              # < 17 edges
    assert int(dut.en_o.value) == 0
    assert (await frame_words(dut))[0] == 0xA000                                  # the DUT's own status agrees: nothing committed
    await frame(dut, cfg=spi.config_word(1, 0, 1, 0xF), n_edges=17)              # exactly 17 edges commits
    assert int(dut.en_o.value) == 0xF
    assert (await frame_words(dut))[0] == spi.status_word(0, 1, 0xF)


@cocotb.test()
async def edges_beyond_80_read_zero(dut):
    await reset(dut)
    bits = await frame(dut, n_edges=90)
    assert bits[80:] == [0] * 10, bits[80:]


@cocotb.test()
async def reset_clears_config(dut):
    await reset(dut)
    await frame(dut, cfg=spi.config_word(1, 1, 1, 0xF))
    await reset(dut)
    assert int(dut.en_o.value) == 0 and int(dut.mode_o.value) == 0 and int(dut.rst_amp_o.value) == 0
    assert (await frame_words(dut))[0] == 0xA000


@cocotb.test()
async def dout_oe_follows_cs(dut):
    await reset(dut)
    assert int(dut.dout_oe.value) == 0
    dut.cs_n.value = 0
    await Timer(10, "ns")
    assert int(dut.dout_oe.value) == 1
    dut.cs_n.value = 1