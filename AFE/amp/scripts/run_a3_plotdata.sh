#!/bin/bash
# A3: Bode data for the figures, run SEQUENTIALLY (the testbenches write fixed file names; the parallel sweeps race on them).
# -> sim/a3_bode_<ol|loop|cl>_<corner>_<T>.csv   (columns from wrdata: f, dB, f, phase_deg [, ...])
AMP="$(cd "$(dirname "$0")/.." && pwd)"
for c in typical:27 ff:27 ss:27 typical:-40 typical:85; do k=${c%%:*}; T=${c##*:}
  bash "$AMP/scripts/ngrun.sh" tb_ota1_ol.spice $k $T > /dev/null 2>&1;   mv "$AMP/sim/a3_ota1_ol_bode.csv" "$AMP/sim/a3_bode_ol_${k}_$T.csv"
  bash "$AMP/scripts/ngrun.sh" tb_ota1_loop.spice $k $T > /dev/null 2>&1; mv "$AMP/sim/a3_loop_bode.csv" "$AMP/sim/a3_bode_loop_${k}_$T.csv"
  bash "$AMP/scripts/ngrun.sh" tb_st1_ac.spice $k $T > /dev/null 2>&1;    mv "$AMP/sim/a3_cl_bode.csv" "$AMP/sim/a3_bode_cl_${k}_$T.csv"
done
ls "$AMP"/sim/a3_bode_*.csv | wc -l
