# dbs_afe_top cocotb testbench (level 0 + 1)

```
make                 # cocotb + icarus: tb/test_frames.py (protocol) and tb/test_neural.py (neural signal)
make AFE_SECONDS=2   # longer recording
make selfcheck       # simulator-free check of the Python model / frame helpers (this one has been run)
```
Needs: `pip install cocotb numpy scipy`, Icarus Verilog.

## Levels
| level | what is simulated | status |
|---|---|---|
| 0 | `hdl/afe_frame_model.v`: spec-level SPI frame model (from SPI_FRAME.md), analog = `code_in` driven from Python | written, **not run** (no simulator in the authoring sandbox) |
| 1 | `python/afe_model.py`: neuron -> x1000 -> HP 0.27 Hz / LP 700 Hz -> ADC code; gating by held EN/MODE/RST_AMP | selfcheck passes |
| 2 | real RTL (`adc_top`/`afe_dig.pnl.v`) with a comparator model closing the SAR loop | TODO, needs `adc_sar_ch.v`, `adc_clkgen.v`, GF180 cell models |
| 3 | ngspice on `dbs_afe_top.spice` (`AFE_ANALOG=ngspice`) | TODO, placeholder raises NotImplementedError |

## Assumptions to confirm
* **Code mapping**: `code = v/3.3 V*4096 - 30`, so 1.65 V -> 2018 and 1 LSB = 0.806 mV (0.806 uV at the electrode). This matches the +-300 LSB = +-242 mV rule and the 26 uV = 32.6 LSB offset, but the docs also say "1.15-2.15 V" input range.
* Neuron model: biphasic 150 uV spikes at 15 Hz, 1.9 uV rms white noise, three LFP sinusoids (4/9/23 Hz). LP corner 700 Hz (design 0.42-1.0 kHz).
* Not modelled: reset-pulse/settling after record start, pseudo-resistor drift, crosstalk, INL/DNL, supply ripple, stimulation currents.
* `SPI_FRAME.md` section 3 hex for ch1-3 (0x17F0, 0x2800, 0x37D8) disagrees with its own binary and with `adc_top.v`; the tests use 0x47F0, 0x8800, 0xC7D8 (ID in bits 15:14).

## Next steps
1. Run `make` and fix whatever the simulator finds in level 0.
2. Send `adc_sar_ch.v` and `adc_clkgen.v` (and the GF180 `gf180mcu_fd_sc_mcu7t5v0` models for the gate-level netlist) to move to level 2.
3. Refine the analog model against the ngspice results in `AFE/layout/baseline/*.json`.