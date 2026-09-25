v {xschem version=3.4.7 file_version=1.2}
G {}
K {}
V {}
S {}
E {}
N -456.5625 -76.71875 -456.5625 -26.71875 {lab=vdd}
N -456.5625 33.28125 -456.5625 73.28125 {lab=GND}
N -386.5625 -76.71875 -386.5625 -26.71875 {lab=vss}
N -386.5625 33.28125 -386.5625 73.28125 {lab=GND}
N -326.5625 -76.71875 -326.5625 -26.71875 {lab=A1}
N -326.5625 33.28125 -326.5625 73.28125 {lab=GND}
N -266.5625 -76.71875 -266.5625 -26.71875 {lab=A2}
N -266.5625 33.28125 -266.5625 73.28125 {lab=GND}
N -206.5625 -76.71875 -206.5625 -26.71875 {lab=A3}
N -206.5625 33.28125 -206.5625 73.28125 {lab=GND}
N -90 -20 -60 -20 {lab=A1}
N -90 0 -60 0 {lab=A2}
N -90 20 -60 20 {lab=A3}
N 170 60 170 80 {lab=GND}
N 100 -0 170 -0 {lab=ZN}
N -30 100 -30 140 {lab=vss}
N -10 100 -10 140 {lab=vss}
N -30 -160 -30 -100 {lab=vdd}
N -10 -160 -10 -100 {lab=vdd}
C {vsource.sym} -456.5625 3.28125 0 0 {name=V1 value=3.3 savecurrent=false}
C {gnd.sym} -456.5625 73.28125 0 0 {name=l1 lab=GND}
C {lab_wire.sym} -456.5625 -66.71875 3 0 {name=p9 sig_type=std_logic lab=vdd}
C {vsource.sym} -386.5625 3.28125 0 0 {name=V2 value=0 savecurrent=false}
C {gnd.sym} -386.5625 73.28125 0 0 {name=l2 lab=GND}
C {lab_wire.sym} -386.5625 -66.71875 3 0 {name=p10 sig_type=std_logic lab=vss}
C {vsource.sym} -326.5625 3.28125 0 0 {name=V3 value=0 savecurrent=false}
C {gnd.sym} -326.5625 73.28125 0 0 {name=l5 lab=GND}
C {lab_wire.sym} -326.5625 -66.71875 3 0 {name=p11 sig_type=std_logic lab=A1}
C {vsource.sym} -266.5625 3.28125 0 0 {name=V4 value=0 savecurrent=false}
C {gnd.sym} -266.5625 73.28125 0 0 {name=l6 lab=GND}
C {lab_wire.sym} -266.5625 -66.71875 3 0 {name=p12 sig_type=std_logic lab=A2}
C {vsource.sym} -206.5625 3.28125 0 0 {name=V5 value=0 savecurrent=false}
C {gnd.sym} -206.5625 73.28125 0 0 {name=l7 lab=GND}
C {lab_wire.sym} -206.5625 -66.71875 3 0 {name=p13 sig_type=std_logic lab=A3}
C {lab_wire.sym} -30 -130 3 0 {name=p1 sig_type=std_logic lab=vdd}
C {lab_wire.sym} -10 -130 3 0 {name=p2 sig_type=std_logic lab=vdd}
C {lab_wire.sym} -30 130 1 0 {name=p4 sig_type=std_logic lab=vss}
C {lab_wire.sym} -10 130 1 0 {name=p3 sig_type=std_logic lab=vss}
C {lab_wire.sym} -90 -20 2 0 {name=p6 sig_type=std_logic lab=A1}
C {lab_wire.sym} -90 0 2 0 {name=p5 sig_type=std_logic lab=A2}
C {lab_wire.sym} -90 20 2 0 {name=p14 sig_type=std_logic lab=A3}
C {lab_wire.sym} 110 0 0 0 {name=p7 sig_type=std_logic lab=ZN}
C {devices/code_shown.sym} -455.46875 160.15625 0 0 {name=MODELS only_toplevel=true
format="tcleval( @value )"
value="
.include $::180MCU_MODELS/design.ngspice
.lib $::180MCU_MODELS/sm141064.ngspice typical
"}
C {code_shown.sym} -460 260 0 0 {name=INCLUDE
only_toplevel=false
value=".include /foss/designs/DBSchip/nand3/gf180mcu_fd_sc_mcu7t5v0__nand3_1.spice"}
C {code_shown.sym} 287.1875 -355.15625 0 0 {name=s1 only_toplevel=false value="
.control
save all
** eight equal segments, one per input combination, Gray ordered
** A1A2A3: 000 001 011 010 110 111 101 100
let fsig  = 1e3
let tper  = 1/fsig
let tstop = 8*tper
let tstep = 0.001*tper
let tfr   = 0.01*tper
let ts    = tstop/8
** A3 (V5): LSB, high on segments 1-2 and 5-6
let td_a3  = ts
let pw_a3  = 2*ts - 2*tfr
let per_a3 = 4*ts
** A2 (V4): middle bit, high on segments 2-5
let td_a2  = 2*ts
let pw_a2  = 4*ts - 2*tfr
let per_a2 = 2*tstop
** A1 (V3): MSB, high on segments 4-7
let td_a1  = 4*ts
let pw_a1  = 4*ts
let per_a1 = 2*tstop
** assign pulse sources
alter @v3[PULSE] = [ 0 3.3 $&td_a1 $&tfr $&tfr $&pw_a1 $&per_a1 0 ]
alter @v4[PULSE] = [ 0 3.3 $&td_a2 $&tfr $&tfr $&pw_a2 $&per_a2 0 ]
alter @v5[PULSE] = [ 0 3.3 $&td_a3 $&tfr $&tfr $&pw_a3 $&per_a3 0 ]
** run
op
tran $&tstep $&tstop
** plot
plot v(a1) v(a2)+5 v(a3)+10 v(zn)+15
write nand3_tb.raw
.endc
"}
C {capa.sym} 170 30 0 0 {name=C1
m=1
value=25f
footprint=1206
device="ceramic capacitor"}
C {gnd.sym} 170 80 0 0 {name=l3 lab=GND}
C {DBSchip/nand3/gf180mcu_fd_sc_mcu7t5v0__nand3_1.sym} 30 0 0 0 {name=x1}
