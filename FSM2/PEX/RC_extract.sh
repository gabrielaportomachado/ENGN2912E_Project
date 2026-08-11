#!/bin/bash
# args:
# first arg = gds file to read
# second arg = name of top cell in gds file to read
magic -rcfile /foss/pdks/gf180mcuD/libs.tech/magic//gf180mcuD.magicrc -noconsole -dnull << EOF
gds read $1
load $2
select top cell
extract all
ext2spice lvs
ext2spice cthresh 0
ext2spice -o ${2}_pex.spice
Exit
EOF
