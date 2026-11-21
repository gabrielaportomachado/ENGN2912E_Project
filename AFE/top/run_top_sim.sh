#!/bin/bash
# I0 whole-digital-part simulation (Icarus).  usage: bash run_top_sim.sh   (from anywhere) -> sim/i0_top.log
#   bash run_top_sim.sh dig   (LP step 5 / L1d): the SAME testbench on the variant top with ONE afe_dig macro instance (AFE/dig/afe_dig.v) in place of adc_top #(4) + dbs_ctrl #(4) + the 15
#                             pad-control ties.  The variant top AFE/dig/dbs_afe_top_dig.v is generated from dbs_afe_top.v by AFE/dig/mk_top_dig.py.  Log: AFE/dig/sim/top_dig.log
#                             (sim/i0_top.log is NOT touched); the two logs are compared line by line (only the `$finish` line may differ) and all 15 pad-control constants are checked.
T="$(cd "$(dirname "$0")" && pwd)"; R="$T/../.."; cd "$T"
if [ "${1:-}" = dig ]; then
  D="$T/../dig"; mkdir -p "$D/sim"
  python3 "$D/mk_top_dig.py" || exit 1
  iverilog -g2005 -DSIM_STUBS -s tb_top -s tb_padctl -o /tmp/top_dig.vvp tb_top.v "$D/tb_padctl.v" "$D/dbs_afe_top_dig.v" "$D/afe_dig.v" "$D/cells_dig_sim.v" stubs_analog.v ../adc/rtl/*.v ../adc/tb/cells_sim.v "$R/rtl/dbs.v" "$R/TGATE/TGATE.v" 2>&1 | head -30
  vvp /tmp/top_dig.vvp > "$D/sim/top_dig.log" 2>&1; rm -f /tmp/top_dig.vvp
  grep '^PADCTL' "$D/sim/top_dig.log"; tail -3 "$D/sim/top_dig.log"
  nd=$(diff <(grep -v '\$finish' sim/i0_top.log) <(grep -v '\$finish\|^PADCTL' "$D/sim/top_dig.log") | grep -c '^[<>]')
  res=$(grep -c '^RESULT PASS errors 0' "$D/sim/top_dig.log"); pad=$(grep -c '^PADCTL PASS' "$D/sim/top_dig.log"); padf=$(grep -c '^PADCTL FAIL' "$D/sim/top_dig.log")
  echo "EQUIVALENCE afe_dig vs reference top: RESULT PASS lines $res (want 1), PADCTL PASS / FAIL lines $pad / $padf (want 1 / 0), log lines that differ from sim/i0_top.log (the \$finish line excluded): $nd (want 0)" | tee -a "$D/sim/top_dig.log"
  if [ "$res" = 1 ] && [ "$pad" = 1 ] && [ "$padf" = 0 ] && [ "$nd" = 0 ]; then echo "EQUIV PASS" | tee -a "$D/sim/top_dig.log"; exit 0; fi
  echo "EQUIV FAIL" | tee -a "$D/sim/top_dig.log"; exit 1
fi
iverilog -g2005 -DSIM_STUBS -s tb_top -o /tmp/i0_top.vvp tb_top.v dbs_afe_top.v stubs_analog.v ../adc/rtl/*.v ../adc/tb/cells_sim.v "$R/rtl/dbs.v" "$R/TGATE/TGATE.v" 2>&1 | head -30
vvp /tmp/i0_top.vvp > sim/i0_top.log 2>&1; head -80 sim/i0_top.log; rm -f /tmp/i0_top.vvp
