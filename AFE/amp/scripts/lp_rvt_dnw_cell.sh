#!/bin/bash
# LP step 6, bonus check for the native-Vt-free follower (spice/ota2_rvt.spice): does a regular nfet_03v3 in an isolated p-well (LVPWELL inside DNWELL) come out of the PDK tools as
# `nfet_03v3` with its own bulk net, and how large is it?   usage: bash AFE/amp/scripts/lp_rvt_dnw_cell.sh   -> AFE/amp/sim/lp_rvt_dnw_cell.log   (GDS and extraction only in /tmp/lp_rvt/lay)
# Steps: (1) the PDK KLayout pcell `nfet` (gf180mcu library; it needs the environment variable USER, which this container does not set) draws 8 x 10u/1u, 3.3 V, with deepnwell = 1,
#        pcmpgr = 1 (P+ ring around the DNWELL) and a P+ tap ring in the LVPWELL; the original follower (nfet_06v0_nvt 10u/2u) and the runner-up (nfet_03v3 10 x 10u/0.28u, no DNWELL) are
#        drawn for the size comparison; (2) Magic extracts the flattened cell (ext2spice lvs); (3) the KLayout sign-off DRC deck, variant D, runs on it.
# Nothing here is a layout deliverable: the amplifier cell is drawn by the layout phases.
AMP="$(cd "$(dirname "$0")/.." && pwd)"; SLOT="$AMP/../layout/scripts/slot.sh"; T=/tmp/lp_rvt/lay; LOG="$AMP/sim/lp_rvt_dnw_cell.log"; PDKT=/foss/pdks/gf180mcuD/libs.tech
mkdir -p $T; cd $T || exit 1
cat > gen.py <<'EOF'
import sys, pya
sys.path.insert(0, '/foss/pdks/gf180mcuD/libs.tech/klayout/tech/pymacros')
import cells
lib = cells.gf180mcu(); lib.register("gf180mcu")
ly = pya.Layout(); ly.dbu = 0.001
top = ly.create_cell("fol_rvt")
pc = ly.create_cell("nfet", "gf180mcu", dict(deepnwell=True, pcmpgr=True, volt="3.3V", bulk="Guard Ring", w_gate=10.0, l_gate=1.0, nf=8, con_bet_fin=1, gate_con_pos="alternating"))
b = pc.dbbox(); print("SIZE variant   nfet_03v3 8 x 10u/1u, LVPWELL tap ring + DNWELL + P+ ring : %.2f x %.2f um = %.1f um2" % (b.width(), b.height(), b.width() * b.height()))
names = {'12/0': 'DNWELL', '204/0': 'LVPWELL', '22/0': 'COMP', '30/0': 'Poly2', '31/0': 'Pplus', '32/0': 'Nplus', '33/0': 'Contact', '34/0': 'Metal1', '21/0': 'Nwell'}
for li in ly.layer_indexes():
    r = pya.Region(pc.begin_shapes_rec(li))
    if not r.is_empty():
        k = str(ly.get_info(li)); bb = r.bbox()
        print("LAYER %-8s %-8s %4d shapes, bbox %.2f x %.2f um" % (k, names.get(k, ''), r.count(), bb.width() * ly.dbu, bb.height() * ly.dbu))
o = ly.create_cell("nfet_06v0_nvt", "gf180mcu", dict(bulk="Guard Ring", w_gate=10.0, l_gate=2.0, nf=1))
b = o.dbbox(); print("SIZE original  nfet_06v0_nvt 10u/2u with its P+ ring                          : %.2f x %.2f um = %.1f um2" % (b.width(), b.height(), b.width() * b.height()))
r = ly.create_cell("nfet", "gf180mcu", dict(deepnwell=False, pcmpgr=False, volt="3.3V", bulk="Guard Ring", w_gate=10.0, l_gate=0.28, nf=10, con_bet_fin=1))
b = r.dbbox(); print("SIZE runner-up nfet_03v3 10 x 10u/0.28u with its P+ ring, no DNWELL            : %.2f x %.2f um = %.1f um2" % (b.width(), b.height(), b.width() * b.height()))
top.insert(pya.DCellInstArray(pc.cell_index(), pya.DTrans())); top.flatten(True)
for c in list(ly.each_cell()):
    if c.cell_index() != top.cell_index(): ly.delete_cell(c.cell_index())
ly.write("fol_rvt.gds")
EOF
cat > ext.tcl <<'EOF'
gds read fol_rvt.gds
load fol_rvt
select top cell
extract all
ext2spice lvs
ext2spice -o fol_rvt_ext.spice
quit -noprompt
EOF
{
echo "# LP step 6: isolated-p-well follower drawn by the PDK pcell, extracted by Magic, checked by the KLayout DRC deck (variant D).  $(date '+%F %T')"
echo "# tools: $(klayout -v 2>&1 | head -1), magic $(magic -dnull -noconsole --version 2>/dev/null | head -1)"
echo "## 1. PDK pcell (klayout -b, USER set)"
USER=designer bash "$SLOT" klayout -b -r gen.py 2>&1 | grep -E "^(SIZE|LAYER)"
echo "## 2. Magic extraction of the flattened cell (magic -dnull -noconsole, extract all, ext2spice lvs)"
bash "$SLOT" magic -dnull -noconsole -rcfile $PDKT/magic/gf180mcuD.magicrc ext.tcl > ext.log 2>&1 < /dev/null
grep -E "^(X|\.subckt|\.ends)" fol_rvt_ext.spice
echo "   devices: $(grep -c '^X' fol_rvt_ext.spice) x $(grep '^X' fol_rvt_ext.spice | awk '{print $6}' | sort -u | tr '\n' ' '); bulk nets: $(grep '^X' fol_rvt_ext.spice | awk '{print $5}' | sort -u | tr '\n' ' ')(a well net of its own, not the substrate net of the cell)"
echo "## 3. KLayout DRC, sign-off deck, variant D (run_drc.py --variant=D)"
rm -rf drc; mkdir -p drc
bash "$SLOT" python3 $PDKT/klayout/tech/drc/run_drc.py --path=fol_rvt.gds --variant=D --topcell=fol_rvt --run_dir=$T/drc --run_mode=flat --no_offgrid > drc.log 2>&1
python3 - <<'EOF'
import glob, re, collections
tot = collections.Counter()
for f in glob.glob('/tmp/lp_rvt/lay/drc/*.lyrdb'):
    t = open(f).read()
    for m in re.finditer(r"<item>.*?<category>'?([^<']+)'?</category>", t, flags=re.S):
        tot[m.group(1)] += 1
print("   result files: %d; violations: %d %s" % (len(glob.glob('/tmp/lp_rvt/lay/drc/*.lyrdb')), sum(tot.values()), dict(tot) if tot else ''))
well = [k for k in tot if k.split('.')[0] in ('DN', 'LPW', 'NW', 'DF', 'PL', 'NP', 'PP', 'COMP')]
print("   well / diffusion / poly / implant rules violated (DN.*, LPW.*, NW.*, DF.*, PL.*, NP.*, PP.*): %s" % (well or 'none'))
if set(tot) == {'CO.6'}:
    print("   -> the ONLY violations are CO.6 (Metal1 overlap of contact >= 0.005 um): the pcell draws the contacts of its two rings (P+ tap ring in the LVPWELL, P+ ring around the DNWELL)")
    print("      without Metal1; the layout adds the Metal1 rings that wire them (p-well ring -> out, outer ring -> vss).  The pcell also draws NO N+ tap for the DNWELL (Nplus has one shape,")
    print("      the device): the layout must add one N+ / COMP tap inside the DNWELL outside the LVPWELL (the 2.5 um LPW.3 band) and wire it to vdd.")
EOF
grep -E "rror|RROR" drc.log | tail -3
echo "## 4. What this shows: (a) the isolated-p-well follower can be drawn with the PDK generator; its footprint with both rings is the SIZE line above (ESTIMATE of the layout cost: variant minus"
echo "   original); (b) Magic extracts 8 x nfet_03v3 w=10u l=1u whose bulk is a well net of its own (the LVPWELL), i.e. spice/ota2_rvt.spice with bulk = source is LVS-able; (c) no well-rule violation."
echo "   NOT shown: netgen LVS of the wired cell (the pcell leaves gates / sources / drains unconnected), the DNWELL tap, the complete amplifier cell (layout phases)."
} > "$LOG" 2>&1
cat "$LOG"
