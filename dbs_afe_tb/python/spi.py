"""SPI frame helpers for dbs_afe_top (AFE/adc/SPI_FRAME.md): 80 SCLK = 5 x 16-bit words, mode 0."""

N_EDGES = 80


def config_word(wr=0, rst_amp=0, mode=0, en=0):
    """Word 0 on DIN: {WR, RST_AMP, MODE, 9 x 0, EN[3:0]}"""
    return (wr & 1) << 15 | (rst_amp & 1) << 14 | (mode & 1) << 13 | (en & 0xF)


def status_word(rst_amp=0, mode=0, en=0):
    """Word 0 on DOUT: {1010, RST_AMP, MODE, EN[3:0], 000000}"""
    return 0xA << 12 | (rst_amp & 1) << 11 | (mode & 1) << 10 | (en & 0xF) << 6


def channel_word(ch, code):
    return (ch & 3) << 14 | (code & 0xFFF)


def expected_frame(held_rst, held_mode, held_en, codes):
    return [status_word(held_rst, held_mode, held_en)] + [channel_word(i, c) for i, c in enumerate(codes)]


def bits_to_words(bits):
    """80 bits (MSB first) -> five 16-bit words"""
    assert len(bits) == N_EDGES
    return [int("".join(str(b) for b in bits[16 * i:16 * i + 16]), 2) for i in range(5)]


def words_to_bits(words):
    return [(w >> (15 - j)) & 1 for w in words for j in range(16)]


def decode(words):
    """Decode a received frame -> dict; raises on sync/ID errors (host rule 4)."""
    st = words[0]
    if st >> 12 != 0xA:
        raise ValueError(f"bad sync nibble {st >> 12:#x}")
    codes = []
    for i, w in enumerate(words[1:]):
        if w >> 14 != i or (w >> 12) & 3:
            raise ValueError(f"bad ID/flags in word {i + 1}: {w:#06x}")
        codes.append(w & 0xFFF)
    return dict(rst_amp=(st >> 11) & 1, mode=(st >> 10) & 1, en=(st >> 6) & 0xF, codes=codes)