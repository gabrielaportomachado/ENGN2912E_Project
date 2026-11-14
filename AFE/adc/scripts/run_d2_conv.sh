#!/bin/bash
# D2 transistor-level runs, one core per job -> sim/d2_settle.log, sim/d2_samp.log ; also sim/d2_idd_<corner>_<T>.npz (supply-current waveforms for scripts/d2_supply.py)
ADC="$(cd "$(dirname "$0")/.." && pwd)"; cd "$ADC"; export OMP_NUM_THREADS=1
V=0.05,0.4,1.2345,1.65,2.3,2.9,3.25; CORN="typical:27 ff:85 ss:-40"
{ for c in $CORN; do k=${c%%:*}; t=${c##*:}; echo "python3 scripts/d2_conv.py settle $k $t 200 $V ${k}_200"; echo "python3 scripts/d2_conv.py settle $k $t 1000 0.4,1.2345,2.9 ${k}_1000"
   echo "python3 scripts/d2_conv.py samp $k $t top_first"; echo "python3 scripts/d2_conv.py samp $k $t bottom_first"; done; } | bash scripts/pj.sh > sim/d2_conv_raw.log 2>&1
grep "^SETTLE" sim/d2_conv_raw.log | sort > sim/d2_settle.log; grep "^SAMP" sim/d2_conv_raw.log | sort > sim/d2_samp.log; grep -v "^SETTLE\|^SAMP" sim/d2_conv_raw.log | head -20
wc -l sim/d2_settle.log sim/d2_samp.log
