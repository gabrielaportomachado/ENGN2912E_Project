#!/bin/bash
# check_env.sh (LP kit, step 1): run this FIRST on the machine that will run the layout phases.   usage:  bash AFE/layout/scripts/check_env.sh [logfile]
# It prints one PASS / WARN / FAIL line per check, what to do on a FAIL, and exits 0 only if nothing FAILED.  Takes about 1-2 minutes.
# Log: AFE/layout/sim/check_env.log (the reference run of the LP machine is AFE/layout/sim/check_env_ref.log: compare yours with it).
# What it checks: A environment (image, tools, PDK variant D decks, one-thread ngspice, git-lfs, disk, RAM)  B a 1-minute smoke test of every tool
#                 C three device facts that the layout depends on (Decision 46): rm3 strap resistor, cap_nmos_03v3 decap, which Magic terminal is the MIM top plate,
#                   and the MIM correction of the kit's PEX command.
ROOT="$(cd "$(dirname "$0")/../../.." && pwd)"; cd "$ROOT" || exit 2
S=AFE/layout/scripts
LOG="${1:-AFE/layout/sim/check_env.log}"; mkdir -p "$(dirname "$LOG")"
exec > >(tee "$LOG") 2>&1
export AFE_SCRATCH="${AFE_SCRATCH:-$ROOT/AFE/layout/.ptmp}"
W="$AFE_SCRATCH/env"; rm -rf "$W"; mkdir -p "$W/o"
np=0; nw=0; nf=0
pass(){ np=$((np+1)); echo "PASS  $1"; }
warn(){ nw=$((nw+1)); echo "WARN  $1"; [ -n "$2" ] && echo "      -> $2"; }
fail(){ nf=$((nf+1)); echo "FAIL  $1"; [ -n "$2" ] && echo "      -> DO: $2"; }
jget(){ python3 -c "import json,sys; d=json.load(open(sys.argv[1])); print(eval(sys.argv[2], {'d': d}))" "$1" "$2" 2>/dev/null; }

# ---- reference values of the LP machine (2026-11-20, AFE/layout/sim/check_env_ref.log)
REF_IMAGE=2026.04
declare -A REF=( [klayout]=0.30.8 [magic]=8.3.636 [netgen]=1.5.318 [ngspice]=46 [iverilog]=14.0 [yosys]=0.64 [openroad]=26Q2-254-g61932e897 [librelane]=3.0.2 [sta]=3.1.0 )
# Disk / RAM minimum for ALL remaining phases. Measured on the LP machine: afe_dig LibreLane run directory 183 MB, peak 549 MB RSS (AFE/dig/reports/flow_summary.rpt); KLayout DRC of
# the macro 645 MB RSS, 1 MB run directory (AFE/dig/reports/klayout_drc.log); kit smoke test (section B/C) < 200 MB of scratch. ESTIMATE for the full chip (not measured): GDS < 100 MB, flat
# DRC < 3 GB RSS, PEX netlists < 1 GB.  The repository file system holds only committed outputs (MIN_REPO_GB); simulation / extraction scratch goes to $AFE_SCRATCH (MIN_DISK_GB; the D1
# phase once leaked 13 GB of simulation scratch, so that limit has margin, and every phase deletes its scratch at the end).
MIN_REPO_GB=3; MIN_DISK_GB=10; WARN_DISK_GB=20; MIN_RAM_GB=7; MIN_AVAIL_GB=3

echo "check_env.sh  $(date '+%Y-%m-%d %H:%M')  host $(hostname)  $(uname -m)  repo $ROOT  commit $(git rev-parse --short HEAD 2>/dev/null)"
echo "--- A. environment"
if [ "$IIC_OSIC_TOOLS_VERSION" = "$REF_IMAGE" ]; then pass "A1 image IIC-OSIC-TOOLS $IIC_OSIC_TOOLS_VERSION (hpretl/iic-osic-tools:chipathon26)"
else warn "A1 image version is '${IIC_OSIC_TOOLS_VERSION:-not set}', the kit was tested in $REF_IMAGE" "start the course container (image hpretl/iic-osic-tools:chipathon26); other versions may work if every line below passes"; fi
python3 $S/flow.py versions > "$W/versions.json" 2>"$W/versions.err"
for t in klayout magic netgen ngspice iverilog yosys openroad librelane sta; do
  v="$(jget "$W/versions.json" "d['$t']")"
  if [ -z "$v" ] || [[ "$v" == NOT\ FOUND* ]]; then fail "A2 $t not found ($v)" "run inside the IIC-OSIC-TOOLS container; $t must be on PATH"
  elif [ "$v" = "${REF[$t]}" ]; then pass "A2 $t $v"
  else warn "A2 $t $v (reference ${REF[$t]})" "not the tested version: continue only if section B and C pass"; fi
done
if python3 -c "import numpy, json, re" 2>/dev/null; then pass "A3 python3 $(python3 -c 'import sys,numpy;print(sys.version.split()[0], "numpy", numpy.__version__)')"; else fail "A3 python3 with numpy" "pip install numpy (the testbench scripts need it)"; fi
P="${PDK_ROOT:-/foss/pdks}/${PDK:-gf180mcuD}"; T="$P/libs.tech"
if [ "${PDK:-}" = gf180mcuD ] && [ -d "$P" ]; then pass "A4 PDK=$PDK at $P"; else fail "A4 PDK gf180mcuD (PDK='${PDK:-}', PDK_ROOT='${PDK_ROOT:-}')" "export PDK=gf180mcuD PDK_ROOT=/foss/pdks (the container sets both)"; fi
miss=""; for f in klayout/tech/drc/run_drc.py klayout/tech/drc/rule_decks/mim_b.drc klayout/tech/lvs/run_lvs.py magic/gf180mcuD.magicrc magic/gf180mcuD.tech netgen/gf180mcuD_setup.tcl \
          ngspice/sm141064.ngspice ngspice/sm141064_mim.ngspice ngspice/design.ngspice klayout/tech/pymacros/cells/__init__.py; do [ -f "$T/$f" ] || miss="$miss $f"; done
for f in libs.ref/gf180mcu_fd_sc_mcu7t5v0/gds/gf180mcu_fd_sc_mcu7t5v0.gds libs.ref/gf180mcu_fd_sc_mcu7t5v0/spice/gf180mcu_fd_sc_mcu7t5v0.spice libs.ref/gf180mcu_fd_sc_mcu7t5v0/lib; do [ -e "$P/$f" ] || miss="$miss $f"; done
if [ -z "$miss" ]; then pass "A4 PDK files: KLayout DRC + LVS decks, Magic tech, netgen setup, ngspice models, pcells, 7t5v0 library"; else fail "A4 PDK files missing:$miss" "the PDK install is incomplete: use the course container"; fi
if python3 "$T/klayout/tech/drc/run_drc.py" --help 2>/dev/null | grep -q "variant=D: Select  metal_top=11K  mim_option=B  metal_level=5LM"; then pass "A4 KLayout DRC deck knows variant D = 11K top metal, MIM option B, 5 metals (common rule 9)"
else fail "A4 KLayout DRC deck has no variant D" "wrong PDK version: use the course container"; fi
if grep -q "ppolyf_u_1k" "$T/netgen/gf180mcuD_setup.tcl" && ! grep -q "ppolyf_u_3k" "$T/netgen/gf180mcuD_setup.tcl" && grep -q "cap_mim_2f0_m4m5_noshield" "$T/netgen/gf180mcuD_setup.tcl" && grep -q "lappend devices rm3" "$T/netgen/gf180mcuD_setup.tcl"; then
  pass "A4 netgen setup: ppolyf_u_1k yes, ppolyf_u_3k no (Decision 44a), cap_mim_2f0_m4m5_noshield, rm3"; else fail "A4 netgen setup does not have the expected device list" "wrong PDK version: use the course container"; fi
# one ngspice thread per job (common rule 8)
mkdir -p "$W/ng"; echo "set num_threads=1" > "$W/ng/.spiceinit"
cat > "$W/ng/t.spice" <<EOF
* check_env smoke: PDK models and the device / parameter names of a Magic PEX netlist
.include $T/ngspice/design.ngspice
.lib $T/ngspice/sm141064.ngspice typical
.lib $T/ngspice/sm141064.ngspice mimcap_typical
.lib $T/ngspice/sm141064.ngspice res_typical
.lib $T/ngspice/sm141064.ngspice moscap_typical
Vdd vdd 0 3.3
X0 d d 0 0 nfet_03v3 ad=0.5p pd=3u as=0.5p ps=3u w=2u l=0.28u
X1 vdd d 0 ppolyf_u_1k r_width=1u r_length=100u
X2 vdd a rm3 r_width=2u r_length=0.2222m
X3 a 0 cap_nmos_03v3 c_width=20u c_length=20u
X4 a b cap_mim_2f0_m4m5_noshield c_width=5u c_length=5u
X5 b b 0 0 nfet_06v0_nvt ad=5p pd=12u as=5p ps=12u w=10u l=2u
R1 b 0 1meg
.control
op
echo THREADS \$num_threads
print v(d) i(Vdd)
echo DONE
quit
.endc
.end
EOF
(cd "$W/ng" && ngspice -b t.spice > t.log 2>&1 < /dev/null)
th="$(grep '^THREADS' "$W/ng/t.log" | awk '{print $2}')"
if [ "$th" = 1 ]; then pass "A5 ngspice runs ONE thread with a job-local .spiceinit (set num_threads=1); the kit's runners write it into every job directory"
else fail "A5 ngspice thread count with a job-local .spiceinit is '$th'" "ngspice must read .spiceinit from the working directory: check SPICE_USERINIT_DIR and the ngspice build"; fi
mkdir -p "$W/ng0"; cp "$W/ng/t.spice" "$W/ng0/"; (cd "$W/ng0" && ngspice -b t.spice > t0.log 2>&1 < /dev/null); th0="$(grep '^THREADS' "$W/ng0/t0.log" | awk '{print $2}')"
echo "INFO  A5 without it this machine would use ${th0:-?} threads per job (5-35x slower for these netlists); SPICE_USERINIT_DIR=${SPICE_USERINIT_DIR:-unset}"
if git lfs version >/dev/null 2>&1; then pass "A6 $(git lfs version | cut -d' ' -f1)"; else warn "A6 git-lfs not found" "FSM2/sim/** is stored with git-lfs; AFE/ does not use it, but install git-lfs before you push"; fi
if git rev-parse --is-inside-work-tree >/dev/null 2>&1; then echo "INFO  A6 branch $(git rev-parse --abbrev-ref HEAD), origin $(git remote get-url origin 2>/dev/null)"; else fail "A6 not a git work tree" "clone the repository and run from it"; fi
fg=$(df -Pk "$ROOT" | awk 'NR==2{printf "%d", $4/1048576}'); sg=$(df -Pk "$AFE_SCRATCH" | awk 'NR==2{printf "%d", $4/1048576}')
same=0; [ "$(df -P "$ROOT" | awk 'NR==2{print $1}')" = "$(df -P "$AFE_SCRATCH" | awk 'NR==2{print $1}')" ] && same=1
if [ "$fg" -lt "$MIN_REPO_GB" ]; then fail "A7 free disk on the repository file system $fg GB, less than $MIN_REPO_GB GB" "free space on the disk of the repository"
else pass "A7 free disk on the repository file system: $fg GB (minimum $MIN_REPO_GB GB for the committed outputs)"; fi
if [ "$sg" -lt "$MIN_DISK_GB" ]; then fail "A7 scratch AFE_SCRATCH=$AFE_SCRATCH has $sg GB free, less than $MIN_DISK_GB GB" "export AFE_SCRATCH=<directory on a disk with >= $MIN_DISK_GB GB> (e.g. /tmp/afe_scratch inside the container) before every phase"
elif [ "$sg" -lt "$WARN_DISK_GB" ]; then warn "A7 scratch $AFE_SCRATCH: $sg GB free (minimum $MIN_DISK_GB, comfortable $WARN_DISK_GB)" "delete the scratch and old LibreLane run directories after every phase"
else pass "A7 scratch $AFE_SCRATCH: $sg GB free (minimum $MIN_DISK_GB GB)$([ $same = 1 ] && echo ', same file system as the repository')"; fi
mt=$(awk '/MemTotal/{printf "%.1f", $2/1048576}' /proc/meminfo); ma=$(awk '/MemAvailable/{printf "%.1f", $2/1048576}' /proc/meminfo)
if awk "BEGIN{exit !($mt >= $MIN_RAM_GB)}"; then pass "A8 RAM $mt GB total (minimum $MIN_RAM_GB), $(nproc) cores"; else fail "A8 RAM $mt GB total, minimum $MIN_RAM_GB GB" "give the container at least 8 GB (Docker Desktop: Settings > Resources)"; fi
if awk "BEGIN{exit !($ma >= $MIN_AVAIL_GB)}"; then pass "A8 RAM available now $ma GB (need >= $MIN_AVAIL_GB)"; else warn "A8 only $ma GB of RAM available now" "close other programs; the slot wrapper limits heavy jobs to 3 (AFE_SLOTS=2 on a loaded machine)"; fi

echo "--- B. smoke test"
bash $S/kl.sh $S/mk_testcells.py out="$W" > "$W/gen.log" 2>&1
n=$(ls "$W"/lp_*.gds 2>/dev/null | wc -l)
if [ "$n" -ge 5 ]; then pass "B1 KLayout batch + the PDK pcell library generate the $n test cells (bash $S/kl.sh; needs USER, which kl.sh sets)"
else fail "B1 test-cell generation ($n of 5 GDS; see $W/gen.log)" "KLayout cannot load the PDK pcells: check 'bash $S/kl.sh $S/mk_testcells.py out=/tmp/x' by hand; gdsfactory must be importable in KLayout (KLAYOUT_PYTHONPATH)"; fi
F="python3 $S/flow.py"
$F drc --gds "$W/lp_tgate_tap.gds" --top lp_tgate_tap --out "$W/o" > "$W/o/b2.txt" 2>&1; rc=$?
if [ $rc = 0 ]; then pass "B2 KLayout DRC --variant=D on lp_tgate_tap (TGATE + tap cell): 0 violations, $(jget "$W/o/lp_tgate_tap.drc.json" "'%s s, %s MB' % (d['wall_s'], d['maxrss_mb'])")"
else fail "B2 KLayout DRC variant D on lp_tgate_tap: $(tail -1 "$W/o/b2.txt")" "see $W/o/lp_tgate_tap.drc.log; the official deck must run (python3 $T/klayout/tech/drc/run_drc.py)"; fi
$F lvs --gds "$W/lp_tgate_tap.gds" --top lp_tgate_tap --ref "$W/lp_tgate_tap.ref.spice" --out "$W/o" > "$W/o/b3.txt" 2>&1; rc=$?
if [ $rc = 0 ]; then pass "B3 Magic extraction + netgen -batch LVS on the two-device cell lp_tgate_tap: $(jget "$W/o/lp_tgate_tap.lvs.json" "d['final']")"
else fail "B3 netgen LVS on lp_tgate_tap: $(tail -1 "$W/o/b3.txt")" "see $W/o/lp_tgate_tap.lvs.out and .ext.log"; fi
if grep -q '^DONE' "$W/ng/t.log" && grep -q 'v(d) = 8.3' "$W/ng/t.log"; then pass "B4 ngspice .op with the PDK models (nfet_03v3, nfet_06v0_nvt, ppolyf_u_1k, rm3, cap_nmos_03v3, cap_mim_2f0_m4m5_noshield): $(grep 'v(d)' "$W/ng/t.log")"
else fail "B4 ngspice .op with the PDK models" "see $W/ng/t.log"; fi
if librelane --help > "$W/ll.txt" 2>&1 < /dev/null; then pass "B5 librelane --help"; else fail "B5 librelane --help" "LibreLane must start: see $W/ll.txt"; fi
printf 'module t; initial begin $display("IVL_OK"); $finish; end endmodule\n' > "$W/t.v"
if iverilog -o "$W/t.vvp" "$W/t.v" 2>/dev/null && vvp "$W/t.vvp" 2>/dev/null | grep -q IVL_OK; then pass "B6 iverilog + vvp"; else fail "B6 iverilog + vvp" "Icarus Verilog must run"; fi

echo "--- C. device facts (Decision 46) and the PEX path"
$F drc --gds "$W/lp_rm3.gds" --top lp_rm3 --out "$W/o" > "$W/o/c1d.txt" 2>&1; r1=$?
$F lvs --gds "$W/lp_rm3.gds" --top lp_rm3 --ref "$W/lp_rm3.ref.spice" --out "$W/o" > "$W/o/c1l.txt" 2>&1; r2=$?
line="$(grep -i ' rm3 ' "$W/o/lp_rm3.lvs.spice" 2>/dev/null | head -1)"
if [ $r1 = 0 ] && [ $r2 = 0 ] && [ -n "$line" ]; then pass "C1 rm3 (Metal3 resistor 2 x 222.2 um, the strap resistor of Decision 46e) IS an LVS-extractable device of variant D: DRC 0, LVS match, extracted '$line'"
  echo "INFO  C1 it must be drawn with kpdk.metal_res (Metal3 + 110/13 + RES_MK 110/5 in ONE cell): the PDK pcell metal_resistor draws only 110/13 and Magic then extracts NO device"
else fail "C1 rm3 does not extract / match (DRC rc $r1, LVS rc $r2)" "use the salicided poly resistor instead: mk_lvs_netlists.py --rstrap ppolyf_s,W,L (ACCEPT.md ladder L3a-R); see $W/o/lp_rm3.lvs.out"; fi
$F drc --gds "$W/lp_cin_decap.gds" --top lp_cin_decap --out "$W/o" > "$W/o/c2d.txt" 2>&1; r1=$?
$F lvs --gds "$W/lp_cin_decap.gds" --top lp_cin_decap --ref "$W/lp_cin_decap.ref.spice" --out "$W/o" > "$W/o/c2l.txt" 2>&1; r2=$?
nd="$(jget "$W/o/lp_cin_decap.lvs.json" "d['devices_layout']")"
if [ $r1 = 0 ] && [ $r2 = 0 ]; then pass "C2 cap_nmos_03v3 extracts as a device, also UNDER a MIM plate (Decision 46c test cell lp_cin_decap: one 70.65 um Cin piece over 4 decap units + Metal3 shield): DRC 0, LVS match"
else fail "C2 decap under the MIM plate (DRC rc $r1: $(tail -1 "$W/o/c2d.txt"); LVS rc $r2: $(tail -1 "$W/o/c2l.txt"))" "do not put decap under the Cin plates: place it in the centre strip (ACCEPT.md ladder, area lever 1 off)"; fi
$F drc --gds "$W/lp_mim.gds" --top lp_mim --out "$W/o" > "$W/o/c3d.txt" 2>&1
$F lvs --gds "$W/lp_mim.gds" --top lp_mim --ref "$W/lp_mim.ref.spice" --out "$W/o" > "$W/o/c3a.txt" 2>&1; ra=$?
sed 's/^X1 TOPNET BOTNET /X1 BOTNET TOPNET /' "$W/lp_mim.ref.spice" > "$W/lp_mim.swapped.spice"
mkdir -p "$W/o2"; $F lvs --gds "$W/lp_mim.gds" --top lp_mim --ref "$W/lp_mim.swapped.spice" --out "$W/o2" > "$W/o/c3b.txt" 2>&1; rb=$?
if [ $ra = 0 ] && [ $rb = 1 ]; then pass "C3 MIM terminal order (Decision 46a): terminal 1 of cap_mim_2f0_m4m5_noshield = TOP plate (FuseTop / Metal5 side).  5 x 5 um unit with the plates labelled TOPNET / BOTNET: LVS MATCHES 'X1 TOPNET BOTNET' and does NOT match the swapped 'X1 BOTNET TOPNET' (netgen does not permute MIM terminals)"
  echo "INFO  C3 so the references of AFE/layout/lvs (mk_lvs_netlists.py --cin-top sum: summing nodes listed first) put the summing nodes physically on the top plates"
elif [ $ra = 1 ] && [ $rb = 0 ]; then fail "C3 MIM terminal order: terminal 1 is the BOTTOM plate on this machine (the reference assumes top)" "regenerate the references with: python3 $S/mk_lvs_netlists.py --cin-top rec  and report it at the top of the phase summary (ACCEPT.md ladder G-3)"
else fail "C3 MIM terminal test inconclusive (LVS rc $ra as drawn, $rb swapped)" "see $W/o/lp_mim.lvs.out"; fi
if [ -f AFE/layout/FLOW.md ]; then
  fl="$(grep -i -E 'terminal *1|top plate' AFE/layout/FLOW.md | head -5)"
  if echo "$fl" | grep -qi -E 'terminal *1[^.;]*bottom'; then fail "C3 AFE/layout/FLOW.md (L2a) says terminal 1 = BOTTOM plate, this check says TOP" "stop: re-run L2a's MIM unit check; one of the two is wrong.  FLOW.md lines: $fl"
  elif echo "$fl" | grep -qi -E 'terminal *1[^.;]*top'; then pass "C3 AFE/layout/FLOW.md (L2a) agrees: terminal 1 = top plate"
  else warn "C3 AFE/layout/FLOW.md exists but states no terminal order that this script can read" "L2a must have recorded it: search FLOW.md / NOTES_L2.md for the MIM terminal check"; fi
else echo "INFO  C3 AFE/layout/FLOW.md (L2a) is not in the work tree yet: nothing to compare with"; fi
$F pex --gds "$W/lp_cin_decap.gds" --top lp_cin_decap --out "$W/o" > "$W/o/c4.txt" 2>&1; rc=$?
mv="$(jget "$W/o/lp_cin_decap.pex.json" "d['mim_fix']['moved_fF']['vn']")"
cs="$(grep -i -E '^C[0-9]+ +(vn vss|vss vn) ' "$W/o/lp_cin_decap.pex_stock.spice" 2>/dev/null | awk '{print $4}')"; cf="$(grep -i -E '^C[0-9]+ +(vn vss|vss vn) ' "$W/o/lp_cin_decap.pex.spice" 2>/dev/null | awk '{print $4}')"
if [ $rc = 0 ] && [ -n "$mv" ] && awk "BEGIN{exit !($mv > 100)}"; then pass "C4 PEX (flow.py pex) with the MIM correction: stock Magic puts $cs between the TOP plate (summing node vn) and the shield below, the corrected netlist $cf ($mv fF moved to the bottom plate rec)"
  echo "INFO  C4 Magic attaches the capacitor-to-below capacitance to MIM terminal 1 (top plate); in silicon the bottom plate shields it.  Always use flow.py pex (never a raw ext2spice) for post-layout runs"
else fail "C4 PEX / MIM correction on lp_cin_decap: $(tail -1 "$W/o/c4.txt")" "see $W/o/lp_cin_decap.pex.log; post-layout numbers of nodes on MIM top plates are not trustworthy without the correction"; fi
$F pex --gds "$W/lp_tgate_tap.gds" --top lp_tgate_tap --out "$W/o" > "$W/o/c5.txt" 2>&1
cat > "$W/ng/p.spice" <<EOF
* check_env: a Magic PEX netlist (own port order) loads and simulates
.include $T/ngspice/design.ngspice
.lib $T/ngspice/sm141064.ngspice typical
.include $W/o/lp_tgate_tap.pex.spice
Vdd vdd 0 3.3
Vin in 0 1.65
Bo out 0 V = V(in) - 0.01
Xdut vdd 0 in out vdd 0 lp_tgate_tap
.control
op
let ron = 0.01/abs(i(Vin))
print ron
echo DONE
quit
.endc
.end
EOF
(cd "$W/ng" && ngspice -b p.spice > p.log 2>&1 < /dev/null)
ports="$(jget "$W/o/lp_tgate_tap.pex.json" "' '.join(d['ports'])")"
if grep -q '^DONE' "$W/ng/p.log" && [ "$ports" = "VDD VSS IN OUT C CBAR" ]; then pass "C5 the Magic PEX netlist of lp_tgate_tap (ports '$ports') simulates in ngspice: $(grep '^ron' "$W/ng/p.log")"
else fail "C5 PEX netlist into ngspice (ports '$ports')" "see $W/ng/p.log"; fi

echo "--- summary: $np PASS, $nw WARN, $nf FAIL"
[ $nf = 0 ] && echo "RESULT: OK, this machine can run the layout phases (next: AFE/layout/RUNBOOK.md)" || echo "RESULT: NOT OK, fix every FAIL line above and run again"
rm -rf "$W"
[ $nf = 0 ]
