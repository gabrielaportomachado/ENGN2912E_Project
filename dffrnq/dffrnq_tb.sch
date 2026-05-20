v {xschem version=3.4.7 file_version=1.2}
G {}
K {}
V {}
S {}
E {}
N -170 -60 -110 -60 {lab=D}
N -180 -60 -170 -60 {lab=D}
N 0 90 0 150 {lab=RSTn}
N 0 150 0 160 {lab=RSTn}
N 0 -150 0 -90 {lab=CLK}
N 0 -160 0 -150 {lab=CLK}
N 110 50 170 50 {lab=vss}
N 170 50 180 50 {lab=vss}
N -170 50 -110 50 {lab=vdd}
N -180 50 -170 50 {lab=vdd}
N -626.5625 -86.71875 -626.5625 -36.71875 {lab=vdd}
N -626.5625 23.28125 -626.5625 63.28125 {lab=GND}
N -556.5625 -86.71875 -556.5625 -36.71875 {lab=vss}
N -556.5625 23.28125 -556.5625 63.28125 {lab=GND}
N -496.5625 -86.71875 -496.5625 -36.71875 {lab=D}
N -496.5625 23.28125 -496.5625 63.28125 {lab=GND}
N -436.5625 -86.71875 -436.5625 -36.71875 {lab=CLK}
N -436.5625 23.28125 -436.5625 63.28125 {lab=GND}
N -366.5625 -86.71875 -366.5625 -36.71875 {lab=RSTn}
N -366.5625 23.28125 -366.5625 63.28125 {lab=GND}
N 290 0 290 20 {lab=GND}
N 110 -60 290 -60 {lab=Q}
N -170 10 -110 10 {lab=vdd}
N -180 10 -170 10 {lab=vdd}
N 110 10 170 10 {lab=vss}
N 170 10 180 10 {lab=vss}
C {gf180mcu_fd_sc_mcu7t5v0__dffrnq_1.sym} 0 0 0 0 {name=x1}
C {lab_wire.sym} -150 -60 0 0 {name=p1 sig_type=std_logic lab=D}
C {lab_wire.sym} 0 130 3 0 {name=p3 sig_type=std_logic lab=RSTn}
C {lab_wire.sym} 0 -130 1 0 {name=p4 sig_type=std_logic lab=CLK}
C {lab_wire.sym} 150 50 2 0 {name=p7 sig_type=std_logic lab=vss}
C {lab_wire.sym} -150 50 0 0 {name=p8 sig_type=std_logic lab=vdd}
C {code_shown.sym} -510 -210 0 0 {name=INCLUDE
only_toplevel=false
value=".include /foss/designs/DBSchip/dffrnq/gf180mcu_fd_sc_mcu7t5v0__dffrnq_1.spice"}
C {vsource.sym} -626.5625 -6.71875 0 0 {name=V1 value=3.3 savecurrent=false}
C {gnd.sym} -626.5625 63.28125 0 0 {name=l1 lab=GND}
C {lab_wire.sym} -626.5625 -76.71875 3 0 {name=p9 sig_type=std_logic lab=vdd}
C {vsource.sym} -556.5625 -6.71875 0 0 {name=V2 value=0 savecurrent=false}
C {gnd.sym} -556.5625 63.28125 0 0 {name=l2 lab=GND}
C {lab_wire.sym} -556.5625 -76.71875 3 0 {name=p10 sig_type=std_logic lab=vss}
C {vsource.sym} -496.5625 -6.71875 0 0 {name=V3 value=0 savecurrent=false}
C {gnd.sym} -496.5625 63.28125 0 0 {name=l5 lab=GND}
C {lab_wire.sym} -496.5625 -76.71875 3 0 {name=p11 sig_type=std_logic lab=D}
C {vsource.sym} -436.5625 -6.71875 0 0 {name=V4 value=3.3 savecurrent=false}
C {gnd.sym} -436.5625 63.28125 0 0 {name=l6 lab=GND}
C {lab_wire.sym} -436.5625 -76.71875 3 0 {name=p12 sig_type=std_logic lab=CLK}
C {vsource.sym} -366.5625 -6.71875 0 0 {name=V5 value=3.3 savecurrent=false}
C {gnd.sym} -366.5625 63.28125 0 0 {name=l7 lab=GND}
C {lab_wire.sym} -366.5625 -76.71875 3 0 {name=p13 sig_type=std_logic lab=RSTn}
C {capa.sym} 290 -30 0 0 {name=C1
m=1
value=25f
footprint=1206
device="ceramic capacitor"}
C {gnd.sym} 290 20 0 0 {name=l3 lab=GND}
C {lab_wire.sym} -150 10 0 0 {name=p2 sig_type=std_logic lab=vdd}
C {lab_wire.sym} 150 10 2 0 {name=p5 sig_type=std_logic lab=vss}
C {code_shown.sym} 377.1875 -485.15625 0 0 {name=s1 only_toplevel=false value="
.control
save all

** Define input signals
let fsig = 1e3
let tper = 1/fsig
let tper2 = 0.95*tper
let tfr = 0.01*tper
let ton_clk = 0.5*tper - 2*tfr

** Define transient params
let tstop  = 2*tper
let tstep  = 0.001 * tper
let tstop3 = 8*tstop

** --- D waveform: high in 1st+3rd quarters, low in 2nd+4th ---
** Achieve this by making D a square wave whose PERIOD = tstop3/2
** Then it is high for tstop3/4, low for tstop3/4, repeating.
let tper_D = tstop3/2
let ton_D  = 0.5*tper_D - 2*tfr

** --- async reset waveform: high first half, low second half ---
** Make one high pulse that lasts tstop3/2, with a very long period so it doesn't repeat.
let tper_R = 2*tstop3
let ton_R  = 0.5*tstop3 - 2*tfr

** NEW: fast clock independent of fsig
let fclk     = 1e5
let tper_clk = 1/fclk
let tper2clk = 0.95*tper_clk
let tfr_clk  = 0.01*tper_clk
let ton_clk  = 0.5*tper_clk - 2*tfr_clk

** Clock on V4 (unchanged)
alter @v4[PULSE] = [ 0 3.3 0 $&tfr_clk $&tfr_clk $&ton_clk $&tper2clk 0 ]

** D on V3 (quarter pattern across full tstop3)
alter @v3[PULSE] = [ 0 3.3 0 $&tfr $&tfr $&ton_D  $&tper_D 0 ]

** Async reset on V5 (high first half, low second half)
alter @v5[PULSE] = [ 0 3.3 0 $&tfr $&tfr $&ton_R  $&tper_R 0 ]

** Simulation
op
tran $&tstep $&tstop3

plot v(clk) v(d)+5 v(rstn)+10 v(q)+15

** Save waveform
write dff_tb.raw
.endc



"}
C {devices/code_shown.sym} -125.46875 280.15625 0 0 {name=MODELS only_toplevel=true
format="tcleval( @value )"
value="
.include $::180MCU_MODELS/design.ngspice
.lib $::180MCU_MODELS/sm141064.ngspice typical
"}
C {lab_wire.sym} 190 -60 0 0 {name=p6 sig_type=std_logic lab=Q}
