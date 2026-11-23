"""cocotb SPI master for dbs_afe_top (mode 0, 80 SCLK per frame)."""
import os
import sys

import cocotb
from cocotb.triggers import Timer

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "python"))
import spi  # noqa: E402

SCLK_HALF_NS = 250          # 2 MHz nominal
CS_LEAD_NS = 150            # CS falls >= 100 ns before the first SCLK edge


def pack_codes(codes):
    v = 0
    for i, c in enumerate(codes):
        v |= (c & 0xFFF) << (12 * i)
    return v


async def reset(dut, hold_ns=1000):
    dut.cs_n.value = 1
    dut.sclk.value = 0
    dut.din.value = 0
    dut.code_in.value = 0
    dut.rstn.value = 0
    await Timer(hold_ns, "ns")
    dut.rstn.value = 1          # released while CS is high (host rule)
    await Timer(hold_ns, "ns")


async def frame(dut, cfg=0x0000, codes=(2018, 2018, 2018, 2018), n_edges=spi.N_EDGES, half_ns=SCLK_HALF_NS):
    """One SPI frame. Returns the list of bits read from DOUT (one per rising edge).

    `codes` is what the analog side presents at the CS falling edge (written to code_in just before)."""
    dut.code_in.value = pack_codes(codes)
    await Timer(50, "ns")
    dut.cs_n.value = 0
    await Timer(CS_LEAD_NS, "ns")
    din_bits = spi.words_to_bits([cfg] + [0] * 4)
    rx = []
    for k in range(n_edges):
        dut.din.value = din_bits[k] if k < len(din_bits) else 0   # DIN changes while SCLK is low
        await Timer(half_ns, "ns")
        rx.append(int(dut.dout.value))                          # DOUT is stable here (changes on falling edges)
        dut.sclk.value = 1
        await Timer(half_ns, "ns")
        dut.sclk.value = 0
    await Timer(half_ns, "ns")
    dut.cs_n.value = 1
    await Timer(half_ns, "ns")
    return rx


async def frame_words(dut, **kw):
    bits = await frame(dut, **kw)
    return spi.bits_to_words(bits) if len(bits) == spi.N_EDGES else bits