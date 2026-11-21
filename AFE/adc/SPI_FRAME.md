# SPI frame of the 4-channel chip: the host interface (normative)

Written by REVIEW item R14 (2026-11-21), implementing Decision 54 of `AFE/NOTES.md` exactly. RTL: `AFE/adc/rtl/adc_top.v` (`adc_top #(.N(4))`), verification: `AFE/adc/tb/tb_adc_top.v`
(frame bit by bit), `AFE/adc/tb/tb_adc_equiv.v`, `AFE/top/tb_top.v`, `AFE/review/tb/tb_audit.v`. This file replaces the 160-SCLK frame of Decisions 38 / 41 (10 words, EN[7:0], word-1 read-back).
Where this file and the RTL differ, the RTL wins and this file has a bug.

## 1. Interface

| pin | direction | use |
|---|---|---|
| `CS` | in | frame select, active low. Its FALLING edge is the sampling instant of all 4 channels. |
| `SCLK` | in | serial clock, SPI mode 0 (CPOL = 0, CPHA = 0): DIN is sampled on the RISING edge, DOUT changes on the FALLING edge. 2 MHz nominal, 3 MHz maximum, 0.64 MHz minimum. SCLK must be low and silent when CS falls. |
| `DIN` | in | host to chip, MSB first. |
| `DOUT` | out (pad `DOUT`, tri-state while CS is high) | chip to host, MSB first. |
| `RSTN` | in | asynchronous reset, active low; the pad has its pull-down enabled (an undriven RSTN = reset). |

## 2. The frame

CS low for the whole frame, **exactly 80 SCLK rising edges** = 5 words of 16 bits, MSB first (40 us at 2 MHz, 26.7 us at 3 MHz). Edge numbers k = 1 ... 80. Both directions run at the same time.

| edges | word | DIN (host -> chip) | DOUT (chip -> host) |
|---|---|---|---|
| 1 - 16 | 0 | CONFIG word | STATUS word = the config HELD BEFORE this frame |
| 17 - 32 | 1 | ignored | `{ID[1:0] = 00, 00, code[11:0]}` of channel 0 |
| 33 - 48 | 2 | ignored | `{ID[1:0] = 01, 00, code[11:0]}` of channel 1 |
| 49 - 64 | 3 | ignored | `{ID[1:0] = 10, 00, code[11:0]}` of channel 2 |
| 65 - 80 | 4 | ignored | `{ID[1:0] = 11, 00, code[11:0]}` of channel 3 |
| 81 ... | - | ignored | 0 |

### 2.1 CONFIG word (DIN, word 0, bit 15 first)

| bit | name | meaning |
|---|---|---|
| 15 | `WR` | 1 = commit this word at edge 17; 0 = the frame only reads (the held config stays) |
| 14 | `RST_AMP` | 1 = hold the amplifier-reset (`fs`) of all channels; a LEVEL, held between frames until a frame with WR = 1 clears it, or RSTN |
| 13 | `MODE` | 1 = record, 0 = stimulate (treat) |
| 12 : 4 | reserved | send 0; ignored by the chip (reserved for later use) |
| 3 : 0 | `EN[3:0]` | channel k is routed (record switch if MODE = 1, IPG switch if MODE = 0) while `EN[k]` = 1 |

### 2.2 STATUS word (DOUT, word 0)

`{ SYNC = 1010 [15:12], RST_AMP [11], MODE [10], EN[3:0] [9:6], 0 [5:0] }` = the held configuration of BEFORE this frame (0xA000 after RSTN). The first sync bit (bit 15 = 1) is already on DOUT
when the pad turns on (DOUT is preset to 1 while CS is high, and the pad is tri-state then), so it is valid at edge 1 like every other bit: the host reads one bit per SCLK rising edge, bit 15 at edge 1.

### 2.3 Channel words (DOUT, words 1 - 4)

`{ID[1:0], 2'b00, code[11:0]}`: ID = the channel number (0 ... 3, so a mis-aligned frame or a swapped channel is visible), the two zero bits are reserved flags (read them as 0), `code` = the 12-bit
conversion (0 .. 4095, offset binary, input 1.15 - 2.15 V) of the SAME frame: the conversions start at the CS falling edge and are complete at edge 16, the first code bit goes out at edge 21.

### 2.4 Commit rule and the edges that matter

* Conversions: ADC i does trial t (t = 1 ... 12) at edge t + i; ADC 3 is done at edge 16 and tracking resumes at edge 17 for every channel.
* **Commit at edge 17**: if `WR` = 1, `{RST_AMP, MODE, EN}` of word 0 becomes the held configuration; if WR = 0 nothing changes. A frame with fewer than 17 edges changes nothing (it can not commit).
* The routing switches follow the held `MODE` / `EN` two SCLK edges later (the routing FSM is clocked by SCLK): in a normal 80-edge frame they move at edges 18 - 19, i.e. after the last conversion.
  A frame of only 17 or 18 edges commits but leaves the routing to move during the conversions of the NEXT frame (do not do that: rule 2 below).
* Edges beyond 80 are ignored (DOUT = 0). CS rising at any time clears the frame counter, releases the ADC drivers and turns the DOUT pad off.
* RSTN (asynchronous) clears the config shift register and the held configuration (all routing switches open, park ON, RST_AMP = 0).

### 2.5 Timing diagram (SPI mode 0)

```
CS      ‾‾‾‾\_____________________________________________________________________/‾‾‾‾      CS low = the whole frame; falling edge = sampling instant (all 4 channels)
SCLK    ____|‾|_|‾|_|‾|_ ... _|‾|_|‾|_ ...                          _|‾|_|‾|____             80 rising edges, SCLK low before CS falls and after the last falling edge
edge #      1   2   3        16  17  18 ...                           80
DIN     --[W][R][M][0] ... [E3][E2][E1][E0] ........ don't care ........ ---                  word 0 = {WR, RST_AMP, MODE, 0 x 9, EN[3:0]}; sampled at the rising edges
DOUT    (1)[0][1][0][R][M][E3..E0][0 x 6] |ID1 ID0 0 0 C11 ... C0| ... 3 more words | 0 0 ... status 1010... then channel 0, 1, 2, 3; changes on the FALLING edges
commit                                   ^ edge 17 (only if WR = 1)
conversions  ADC0 trials at edges 1..12, ADC1 at 2..13, ADC2 at 3..14, ADC3 at 4..15 (+1: decisions written one edge later) -> all codes complete at edge 16
```

## 3. Worked example: one frame = 10 bytes in, 10 bytes out

Situation: the chip is recording on channels 0 and 1 (held config: RST_AMP = 0, MODE = 1, EN = 0011). The host now wants to record on all 4 channels: WR = 1, RST_AMP = 0, MODE = 1, EN = 1111.
The channel codes at this CS falling edge are 2018, 2032, 2048 and 2008 (0x7E2, 0x7F0, 0x800, 0x7D8).

| word | DIN (16 bits) | DIN bytes | DOUT (16 bits) | DOUT bytes |
|---|---|---|---|---|
| 0 | `1 0 1 000000000 1111` = 0xA00F | `A0 0F` | status `1010 0 1 0011 000000` = 0xA4C0 (held config of before: record, EN = 0011) | `A4 C0` |
| 1 | 0x0000 (ignored) | `00 00` | ch 0: `00 00 0111 1110 0010` = 0x07E2 | `07 E2` |
| 2 | 0x0000 | `00 00` | ch 1: `01 00 0111 1111 0000` = 0x17F0 | `17 F0` |
| 3 | 0x0000 | `00 00` | ch 2: `10 00 1000 0000 0000` = 0x2800 | `28 00` |
| 4 | 0x0000 | `00 00` | ch 3: `11 00 0111 1101 1000` = 0x37D8 | `37 D8` |

Bytes in: `A0 0F 00 00 00 00 00 00 00 00`; bytes out: `A4 C0 07 E2 17 F0 28 00 37 D8` (a hardware SPI master in mode 0 does this as one 10-byte transfer with CS held low).
The chip commits EN = 1111 at edge 17 and closes the routing switches of channels 2 and 3 at edges 18 - 19 (a one-shot amplifier reset then starts on those channels). The NEXT frame reads the status word `A7 C0` (`1010 0 1 1111 000000`: held config RST_AMP 0, MODE 1, EN 1111). A pure read frame: bytes in `00 00 00 00 00 00 00 00 00 00` (WR = 0): nothing changes, the codes and the status still come out.

## 4. Power-up and reset sequence

1. Hold RSTN low while VDD ramps up; release RSTN while CS is high. The first status word after reset is `0xA000` (a good check that DIN / DOUT / CS / SCLK are wired and the SPI mode is right).
2. Wait at least 5 s after VDD is stable (the shared bias starts in 3.7 ms typ, up to 3.6 s at ss -40 C: `AFE/layout/baseline/bias_startup.json`).
3. Send a frame with `WR = 1, RST_AMP = 1` (0xC000) and keep the level for >= 100 ms (frames with WR = 0 meanwhile do not touch it), then a frame with `WR = 1, RST_AMP = 0` (0x8000).
4. Check every channel (rule 6 below), then write the working configuration (`WR = 1`, e.g. 0xA00F = record on all channels). After a record start each enabled channel takes an amplifier-reset pulse (about 3.6 ms, 8 - 28 frames):
   discard those frames and the settling after them. The host rules on the mid-scale window and on repeating RST_AMP (REVIEW R10) are in `README.md` and `AFE/adc/README.md`.

## 5. Host rules that follow from the frame

1. **80 SCLK per frame**, SPI mode 0, SCLK <= 3 MHz. The first frame after any pause is not valid for the codes; discard it.
2. **Never raise CS early.** A frame with fewer than 17 edges commits nothing; one with 17 or 18 edges commits but lets the routing move while the next frame converts; on an aborted frame the sampling switch closes
   2.4 - 5.6 ns before the DAC drivers release (a short kick on the amplifier output). Change RSTN only while CS is high (a release of RSTN while CS is low restarts the frame counter in the middle of the frame, and the
   following DIN bits are decoded as a new word 0 which may commit with WR = 1).
3. **CS from a hardware timer** (jitter <= 85 ns rms: the falling edge is the sampling instant), CS must fall >= 100 ns before the first SCLK edge; SCLK may run while CS is high (shared bus: nothing happens).
4. **Check the frame**: word 0 of DOUT must start with the sync nibble `1010` (bits 15 - 12) and the IDs of words 1 - 4 must read 0, 1, 2, 3. Anything else = a mis-aligned frame, a wrong SPI mode or a CS / SCLK problem: do not use the codes of that frame,
   and re-synchronise with CS high for a few SCLK periods and a clean frame.
5. **WR usage**: set WR = 1 only in the frames that change the configuration; every other frame sends WR = 0 (e.g. all zero bytes) and cannot disturb the routing or the RST_AMP level. A WR = 1 frame always carries the complete word
   (RST_AMP, MODE and EN all at once). Compare the status word of the NEXT frame with what was written: it is the read-back of the commit.
6. Reserved bits (config bits 12 - 4, the two flag bits of the channel words) are written as 0 and read as 0.
7. RST_AMP is a level held in the chip while SCLK stops: set it with one WR = 1 frame, wait >= 100 ms, clear it with another.
8. Sample rate: set only by the host, one frame per 250 us = 4 kS/s per channel; back-to-back frames are accepted (CS high for at least one SCLK period): about 24 kS/s at 2 MHz (40.85 us per frame with 100 ns CS lead and 1.5 SCLK periods of CS high) and 36 kS/s at 3 MHz.
