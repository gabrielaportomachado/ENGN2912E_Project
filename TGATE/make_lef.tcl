# Regenerate TGATE.lef from TGATE.gds.
# Run from this directory:
#   magic -dnull -noconsole -rcfile $PDK_ROOT/$PDK/libs.tech/magic/gf180mcuD.magicrc make_lef.tcl

# Read the layout. Metal1 labels (GDS 34/10) become ports automatically.
gds read TGATE.gds
load TGATE

# "port" acts on the label under Magic's cursor box. With no window (-dnull)
# there is no box yet, so create one; findlabel then moves it onto each label.
# NOTE from human: the above explanation is wrong, but the script should still work fine
select top cell
box values 0 0 0 0

# Pin direction (LEF DIRECTION) and use (LEF USE)
proc setport {name class use} {
    findlabel $name
    port class $class
    port use   $use
}
setport IN   inout signal
setport OUT  inout signal
setport C    input signal
setport CBAR input signal
setport VDD  inout power
setport VSS  inout ground

# Cell placement properties (LEF CLASS / SITE / SYMMETRY).
# SIZE comes from the PR boundary (GDS 0/0), so no FIXED_BBOX is needed.
property LEFclass    CORE
property LEFsite     GF018hv5v_mcu_sc7
property LEFsymmetry "X Y"

lef write TGATE.lef
quit -noprompt
