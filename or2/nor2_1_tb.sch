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
N -50 -130 -50 -100 {lab=vdd}
N -30 -130 -30 -100 {lab=vdd}
N -30 100 -30 130 {lab=vss}
N -50 100 -50 130 {lab=vss}
N -90 20 -60 20 {lab=A2}
N -90 -20 -60 -20 {lab=A1}
N 80 0 110 0 {lab=Z}
N 170 60 170 80 {lab=GND}
N 110 0 170 -0 {lab=Z}
N 60 -0 80 -0 {lab=Z}
C {vsource.sym} -456.5625 3.28125 0 0 {name=V1 value=3.3 savecurrent=false}
C {gnd.sym} -456.5625 73.28125 0 0 {name=l1 lab=GND}
C {lab_wire.sym} -456.5625 -66.71875 3 0 {name=p9 sig_type=std_logic lab=vdd}
C {vsource.sym} -386.5625 3.28125 0 0 {name=V2 value=0 savecurrent=false}
C {gnd.sym} -386.5625 73.28125 0 0 {name=l2 lab=GND}
C {lab_wire.sym} -386.5625 -66.71875 3 0 {name=p10 sig_type=std_logic lab=vss}
C {vsource.sym} -326.5625 3.28125 0 0 {name=V3 value=0 savecurrent=false}
C {gnd.sym} -326.5625 73.28125 0 0 {name=l5 lab=GND}
C {lab_wire.sym} -326.5625 -66.71875 3 0 {name=p11 sig_type=std_logic lab=A1}
C {vsource.sym} -266.5625 3.28125 0 0 {name=V4 value=3.3 savecurrent=false}
C {gnd.sym} -266.5625 73.28125 0 0 {name=l6 lab=GND}
C {lab_wire.sym} -266.5625 -66.71875 3 0 {name=p12 sig_type=std_logic lab=A2}
C {lab_wire.sym} -50 -130 3 0 {name=p1 sig_type=std_logic lab=vdd}
C {lab_wire.sym} -30 -130 3 0 {name=p2 sig_type=std_logic lab=vdd}
C {lab_wire.sym} -50 130 1 0 {name=p4 sig_type=std_logic lab=vss}
C {lab_wire.sym} -30 130 1 0 {name=p3 sig_type=std_logic lab=vss}
C {lab_wire.sym} -90 20 2 0 {name=p5 sig_type=std_logic lab=A2}
C {lab_wire.sym} -90 -20 2 0 {name=p6 sig_type=std_logic lab=A1}
C {lab_wire.sym} 110 0 0 0 {name=p7 sig_type=std_logic lab=Z}
C {devices/code_shown.sym} -455.46875 160.15625 0 0 {name=MODELS only_toplevel=true
format="tcleval( @value )"
value="
.include $::180MCU_MODELS/design.ngspice
.lib $::180MCU_MODELS/sm141064.ngspice typical
"}
C {code_shown.sym} -460 260 0 0 {name=INCLUDE
only_toplevel=false
value=".include /foss/designs/DBSchip/or2/gf180mcu_fd_sc_mcu7t5v0__or2_1.spice"}
C {code_shown.sym} 287.1875 -355.15625 0 0 {name=s1 only_toplevel=false value="

.control
save all

** four equal segments, one per input combination
let fsig  = 1e3
let tper  = 1/fsig
let tstop = 4*tper
let tstep = 0.001*tper
let tfr   = 0.01*tper
let tq    = tstop/4

** A2 (V4): fast bit, high in 2nd and 4th quarters
let td_a2  = tq
let pw_a2  = tq - 2*tfr
let per_a2 = 2*tq

** A1 (V3): slow bit, high in 2nd half only
let td_a1  = 2*tq
let pw_a1  = 2*tq
let per_a1 = 2*tstop

** assign pulse sources
alter @v3[PULSE] = [ 0 3.3 $&td_a1 $&tfr $&tfr $&pw_a1 $&per_a1 0 ]
alter @v4[PULSE] = [ 0 3.3 $&td_a2 $&tfr $&tfr $&pw_a2 $&per_a2 0 ]

** run
op
tran $&tstep $&tstop

** plot
plot v(a1) v(a2)+5 v(z)+10

write nor2_tb.raw
.endc
"}
C {capa.sym} 170 30 0 0 {name=C1
m=1
value=25f
footprint=1206
device="ceramic capacitor"}
C {gnd.sym} 170 80 0 0 {name=l3 lab=GND}
C {DBSchip/or2/gf180mcu_fd_sc_mcu7t5v0__or2_1.sym} 0 0 0 0 {name=x1}
