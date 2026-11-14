#!/bin/bash
# D2 supply runs (each step < 1800 s): split-supply grid (5 MHz, 1 MHz, digital ESTIMATE on), then the single-rail C x R sweep
ADC="$(cd "$(dirname "$0")/.." && pwd)"; cd "$ADC"; export OMP_NUM_THREADS=1; : > sim/d2_supply_err.log
python3 scripts/d2_supply.py split off 5 > /dev/null 2>> sim/d2_supply_err.log; echo split5 >> sim/d2_supply_done.txt
python3 scripts/d2_supply.py split dig 5 > /dev/null 2>> sim/d2_supply_err.log; echo split5dig >> sim/d2_supply_done.txt
python3 scripts/d2_supply.py sweep > /dev/null 2>> sim/d2_supply_err.log; echo sweep >> sim/d2_supply_done.txt
python3 scripts/d2_supply.py split off 1 > /dev/null 2>> sim/d2_supply_err.log; echo split1 >> sim/d2_supply_done.txt
