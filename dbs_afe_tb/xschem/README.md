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

## Level 3: xschem / ngspice testbench (`xschem/`)
```
python3 xschem/gen_xschem_tb.py --netlist <AFE>/layout/lvs/dbs_afe_top.spice --out build --pdk-root $PDK_ROOT
cd build && ngspice -b tb_dbs_afe_top.spice           # or open tb_dbs_afe_top.sch in xschem: 'n' netlist, 's' simulate
python3 ../xschem/decode_dout.py tb_out.txt stim_frames.json
```
* The port order comes from the `.subckt dbs_afe_top` line, so the generated symbol and the X-instance cannot disagree with your netlist.
* Stimulus: SPI frames at 2 MHz / 4 kS/s (read, RST_AMP pulse, record on all channels, then read frames), E0 = the neural signal from `afe_model.py` around 1.65 V, E1 = 0.45 mV pk 200 Hz tone, E2/E3/REF = 1.65 V.
* `decode_dout.py` turns the DOUT wave back into frames (sync, IDs, status read-back) and reports per-channel mean/std and the gain at 200 Hz (expect ~60 dB).
* Status: generator and decoder were exercised in the sandbox only against a dummy netlist and a synthetic ideal DOUT. **ngspice and xschem were not available, so the deck, `.sym` and `.sch` have not been loaded by either tool.**
* Assumptions to check: PDK path/corner in the `.lib` line (`gf180mcuD/libs.tech/ngspice/sm141064.ngspice typical`), the load values, RSTN/CS idle levels, and the time compression (RST_AMP held 5 ms, not >= 100 ms; the 5 s bias wait is skipped), so early frames may be unsettled. Use `--no-pdk` if your netlist already includes models.