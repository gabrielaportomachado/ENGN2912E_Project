v {xschem version=3.4.7 file_version=1.2}
G {}
K {}
V {}
S {}
E {}
N -556.5625 -86.71875 -556.5625 -36.71875 {lab=vdd}
N -556.5625 23.28125 -556.5625 63.28125 {lab=GND}
N -486.5625 -86.71875 -486.5625 -36.71875 {lab=vss}
N -486.5625 23.28125 -486.5625 63.28125 {lab=GND}
N -426.5625 -86.71875 -426.5625 -36.71875 {lab=MODE}
N -426.5625 23.28125 -426.5625 63.28125 {lab=GND}
N -366.5625 -86.71875 -366.5625 -36.71875 {lab=CLK}
N -366.5625 23.28125 -366.5625 63.28125 {lab=GND}
N -296.5625 -86.71875 -296.5625 -36.71875 {lab=RSTn}
N -296.5625 23.28125 -296.5625 63.28125 {lab=GND}
N 310 50 310 70 {lab=GND}
N 230 70 230 90 {lab=GND}
N -190 -0 -140 -0 {lab=MODE}
N -80 -100 -80 -60 {lab=vdd}
N -10 -100 -10 -60 {lab=CLK}
N 10 -100 10 -60 {lab=RSTn}
N 80 -100 80 -60 {lab=vss}
N 140 -10 310 -10 {lab=REC_EN}
N 140 10 230 10 {lab=TREAT_EN}
C {FSM.sym} 0 0 0 0 {name=x1}
C {vsource.sym} -556.5625 -6.71875 0 0 {name=V1 value=3.3 savecurrent=false}
C {gnd.sym} -556.5625 63.28125 0 0 {name=l1 lab=GND}
C {lab_wire.sym} -556.5625 -76.71875 3 0 {name=p9 sig_type=std_logic lab=vdd}
C {vsource.sym} -486.5625 -6.71875 0 0 {name=V2 value=0 savecurrent=false}
C {gnd.sym} -486.5625 63.28125 0 0 {name=l2 lab=GND}
C {lab_wire.sym} -486.5625 -76.71875 3 0 {name=p10 sig_type=std_logic lab=vss}
C {vsource.sym} -426.5625 -6.71875 0 0 {name=V3 value=0 savecurrent=false}
C {gnd.sym} -426.5625 63.28125 0 0 {name=l5 lab=GND}
C {lab_wire.sym} -426.5625 -86.71875 3 0 {name=p11 sig_type=std_logic lab=MODE}
C {vsource.sym} -366.5625 -6.71875 0 0 {name=V4 value=3.3 savecurrent=false}
C {gnd.sym} -366.5625 63.28125 0 0 {name=l6 lab=GND}
C {lab_wire.sym} -366.5625 -76.71875 3 0 {name=p12 sig_type=std_logic lab=CLK}
C {vsource.sym} -296.5625 -6.71875 0 0 {name=V5 value=3.3 savecurrent=false}
C {gnd.sym} -296.5625 63.28125 0 0 {name=l7 lab=GND}
C {lab_wire.sym} -296.5625 -76.71875 3 0 {name=p13 sig_type=std_logic lab=RSTn}
C {capa.sym} 310 20 0 0 {name=C1
m=1
value=25f
footprint=1206
device="ceramic capacitor"}
C {gnd.sym} 310 70 0 0 {name=l3 lab=GND}
C {capa.sym} 230 40 0 0 {name=C2
m=1
value=25f
footprint=1206
device="ceramic capacitor"}
C {gnd.sym} 230 90 0 0 {name=l4 lab=GND}
C {lab_wire.sym} -160 0 0 0 {name=p1 sig_type=std_logic lab=MODE}
C {lab_wire.sym} -80 -70 1 0 {name=p2 sig_type=std_logic lab=vdd}
C {lab_wire.sym} -10 -70 1 0 {name=p3 sig_type=std_logic lab=CLK}
C {lab_wire.sym} 10 -70 1 0 {name=p4 sig_type=std_logic lab=RSTn}
C {lab_wire.sym} 80 -70 1 0 {name=p5 sig_type=std_logic lab=vss}
C {devices/code_shown.sym} -205.46875 150.15625 0 0 {name=MODELS only_toplevel=true
format="tcleval( @value )"
value="
.include $::180MCU_MODELS/design.ngspice
.lib $::180MCU_MODELS/sm141064.ngspice typical
"}
C {code_shown.sym} -200 280 0 0 {name=INCLUDE
only_toplevel=false
value="
.include /foss/designs/DBSchip/dffsnq/gf180mcu_fd_sc_mcu7t5v0__dffsnq_1.spice
.include /foss/designs/DBSchip/dffrnq/gf180mcu_fd_sc_mcu7t5v0__dffrnq_1.spice
.include /foss/designs/DBSchip/inv_1/gf180mcu_fd_sc_mcu7t5v0__inv_1.spice
.include /foss/designs/DBSchip/mux2_1/gf180mcu_fd_sc_mcu7t5v0__mux2_1.spice
.include /foss/designs/DBSchip/nor2/gf180mcu_fd_sc_mcu7t5v0__nor2_1.spice
"}
C {code_shown.sym} 687.1875 -505.15625 0 0 {name=s1 only_toplevel=false value="
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

plot v(clk) v(mode)+5 v(rstn)+10 v(rec_en)+15 v(treat_en)+20

** Save waveform
write dff_tb.raw
.endc



"}
C {lab_wire.sym} 250 -10 0 0 {name=p6 sig_type=std_logic lab=REC_EN}
C {lab_wire.sym} 150 10 2 0 {name=p7 sig_type=std_logic lab=TREAT_EN}
