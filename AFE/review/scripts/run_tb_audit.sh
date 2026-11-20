#!/bin/bash
# AUDIT step 4: build and run the assertion testbench AFE/review/tb/tb_audit.v.
#   RTL builds : adc8_top RTL + per-corner cell models (AFE/adc/tb/cells_sim.v) + STA-derived port delays (tb/audit_delays.vh), 5 corners + the MIXED corner, SCLK 2 and 3 MHz
#   GLS builds : delay-annotated copy of the hardened netlist AFE/adc/lg/runs/d3/final/nl/adc8_top.nl.v (gen_gl.py, SDF IOPATH delays, 5 corners + MIXED) + PDK functional cell models
# usage: bash run_tb_audit.sh [rtl|gls|all]      logs: AFE/review/sim/tb_audit_<build>_<corner>_<f>MHz_<scen>.log, summary: AFE/review/sim/tb_audit_summary.log
#   DIG builds (LP step 5 / L1d; nothing above changes): bash run_tb_audit.sh dig <LibreLane final dir of afe_dig>
#               the same testbench and scenarios on the hardened macro afe_dig (adc8_top + dbs_ctrl + clock buffer + switch pairs + tie cells): gen_gl.py on <final dir>/nl/afe_dig.nl.v
#               and its SDF, wrapper AFE/dig/top_ba_dig.v.  Logs: AFE/dig/sim/tb_audit_dig_<corner>_<f>MHz_<scen>.log, summary AFE/dig/sim/tb_audit_dig_summary.log (env DIG_OUT = another
#               log directory, DIG_TMP = scratch for the compiled files, default /tmp/lp_dig/tb).  The AFE/review/sim logs are not touched in this mode.
R="$(cd "$(dirname "$0")/.." && pwd)"; AFE="$R/.."; REPO="$AFE/.."
IV=/foss/tools/iverilog/bin; T="$R/.ptmp/tb"; mkdir -p "$T" "$R/sim"
PDKV=/foss/pdks/gf180mcuD/libs.ref/gf180mcu_fd_sc_mcu7t5v0/verilog
RUN="$AFE/adc/lg/runs/d3/final"
what=${1:-all}
LOGD="$R/sim"; SUM="$R/sim/tb_audit_summary.log"
if [ "$what" = dig ]; then
  DIGF="${2:-}"; [ -f "$DIGF/nl/afe_dig.nl.v" ] || { echo "usage: bash run_tb_audit.sh dig <LibreLane final dir of afe_dig> (no $DIGF/nl/afe_dig.nl.v)" >&2; exit 1; }
  LOGD="${DIG_OUT:-$AFE/dig/sim}"; SUM="$LOGD/tb_audit_dig_summary.log"; T="${DIG_TMP:-/tmp/lp_dig/tb}"; mkdir -p "$LOGD" "$T"
fi
: > "$SUM"
run() {  # tag, vvp file
  for per in 500.0 333.333; do
    f=$(python3 -c "print('%.0f' % (1000/$per))")
    for sc in main rstlate noreset; do
      log="$LOGD/tb_audit_${1}_${f}MHz_${sc}.log"
      $IV/vvp -n "$2" +PER=$per +SCEN=$sc > "$log" 2>&1
      printf "%-22s %s MHz %-8s  %s  FAILS: %s\n" "$1" "$f" "$sc" "$(grep '^SUMMARY' "$log" | sed 's/SUMMARY [a-z]* PER [0-9.]* ns: //')" "$(grep '^ASSERT' "$log" | grep FAIL | awk '{print $2}' | tr '\n' ' ')" >> "$SUM"
    done
  done
}
if [ "$what" = rtl ] || [ "$what" = all ]; then
  for c in FFN40 FF125 TT SSN40 SS125 FFN40_MIXED; do
    defs="-DCORNER_${c%_MIXED}"; [ "$c" = FFN40_MIXED ] && defs="$defs -DMIXED"; [ "$c" = TT ] && defs=""
    $IV/iverilog -g2005 -DSIM_STUBS $defs -I "$R/tb" -s tb_audit -o "$T/rtl_$c.vvp" "$R/tb/tb_audit.v" "$R/tb/top_ba.v" "$R/tb/stubs_audit.v" "$AFE/top/dbs_afe_top.v" \
        "$AFE"/adc/rtl/*.v "$AFE/adc/tb/cells_sim.v" "$REPO/rtl/dbs.v" "$REPO/TGATE/TGATE.v" 2>&1 | grep -v "^$" | head -20
    run "rtl_$c" "$T/rtl_$c.vvp"
  done
fi
if [ "$what" = gls ] || [ "$what" = all ]; then
  # gate level: delay-annotated copy of the hardened netlist (scripts/gen_gl.py: worst SDF IOPATH arc per cell output; Icarus cannot read this SDF), PDK functional cell models
  for c in ff_n40C_3v60:FFN40 ff_125C_3v60:FF125 tt_025C_3v30:TT ss_n40C_3v00:SSN40 ss_125C_3v00:SS125 ff_n40C_3v60:FFN40_MIXED; do
    lc=${c%%:*}; k=${c##*:}; defs="-DCORNER_${k%_MIXED}"; [ "$k" = FFN40_MIXED ] && defs="$defs -DMIXED"; [ "$k" = TT ] && defs=""
    python3 "$R/scripts/gen_gl.py" $lc "$T/gl_$lc.v" > /dev/null
    $IV/iverilog -g2005 -DSIM_STUBS -DGLS -DFUNCTIONAL $defs -I "$R/tb" -s tb_audit -o "$T/gls_$k.vvp" "$R/tb/tb_audit.v" "$R/tb/top_ba.v" "$R/tb/stubs_audit.v" \
        "$AFE/top/dbs_afe_top.v" "$T/gl_$lc.v" "$PDKV/primitives.v" "$PDKV/gf180mcu_fd_sc_mcu7t5v0.v" "$REPO/rtl/dbs.v" "$REPO/TGATE/TGATE.v" 2>&1 | grep -v "SDFFILE\|sdf_annotate" | head -20
    run "gls_$k" "$T/gls_$k.vvp"
  done
fi
if [ "$what" = dig ]; then
  # gate level of the macro afe_dig: mode_o / en_o are internal nets that the wrapper reads by name
  grep -q '^ wire mode_o;' "$DIGF/nl/afe_dig.nl.v" && grep -q '^ wire .en_o\[7\] ;' "$DIGF/nl/afe_dig.nl.v" || { echo "STOP: the netlist has no nets mode_o / en_o[7] (AFE/dig/top_ba_dig.v reads them)" >&2; exit 1; }
  for c in ff_n40C_3v60:FFN40 ff_125C_3v60:FF125 tt_025C_3v30:TT ss_n40C_3v00:SSN40 ss_125C_3v00:SS125 ff_n40C_3v60:FFN40_MIXED; do
    lc=${c%%:*}; k=${c##*:}; defs="-DCORNER_${k%_MIXED}"; [ "$k" = FFN40_MIXED ] && defs="$defs -DMIXED"; [ "$k" = TT ] && defs=""
    python3 "$R/scripts/gen_gl.py" $lc "$T/gl_dig_$lc.v" "$DIGF" afe_dig > /dev/null
    $IV/iverilog -g2005 -DSIM_STUBS -DGLS -DFUNCTIONAL $defs -I "$R/tb" -s tb_audit -o "$T/dig_$k.vvp" "$R/tb/tb_audit.v" "$AFE/dig/top_ba_dig.v" "$R/tb/stubs_audit.v" \
        "$AFE/top/dbs_afe_top.v" "$T/gl_dig_$lc.v" "$PDKV/primitives.v" "$PDKV/gf180mcu_fd_sc_mcu7t5v0.v" "$REPO/rtl/dbs.v" "$REPO/TGATE/TGATE.v" 2>&1 | grep -v "SDFFILE\|sdf_annotate" | head -20
    run "dig_$k" "$T/dig_$k.vvp"
  done
fi
cat "$SUM"
