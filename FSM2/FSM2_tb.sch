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
C {vsource.sym} -556.5625 -6.71875 0 0 {name=V1 value=5 savecurrent=false}
C {gnd.sym} -556.5625 63.28125 0 0 {name=l1 lab=GND}
C {lab_wire.sym} -556.5625 -76.71875 3 0 {name=p9 sig_type=std_logic lab=vdd}
C {vsource.sym} -486.5625 -6.71875 0 0 {name=V2 value=0 savecurrent=false}
C {gnd.sym} -486.5625 63.28125 0 0 {name=l2 lab=GND}
C {lab_wire.sym} -486.5625 -76.71875 3 0 {name=p10 sig_type=std_logic lab=vss}
C {vsource.sym} -426.5625 -6.71875 0 0 {name=V3 value=0 savecurrent=false}
C {gnd.sym} -426.5625 63.28125 0 0 {name=l5 lab=GND}
C {lab_wire.sym} -426.5625 -86.71875 3 0 {name=p11 sig_type=std_logic lab=MODE}
C {vsource.sym} -366.5625 -6.71875 0 0 {name=V4 value=5 savecurrent=false}
C {gnd.sym} -366.5625 63.28125 0 0 {name=l6 lab=GND}
C {lab_wire.sym} -366.5625 -76.71875 3 0 {name=p12 sig_type=std_logic lab=CLK}
C {vsource.sym} -296.5625 -6.71875 0 0 {name=V5 value=5 savecurrent=false}
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
.include /foss/designs/DBSchip/and2/gf180mcu_fd_sc_mcu7t5v0__and2_1.spice
.include /foss/designs/DBSchip/or2/gf180mcu_fd_sc_mcu7t5v0__or2_1.spice
.include /foss/designs/DBSchip/nor2/gf180mcu_fd_sc_mcu7t5v0__nor2_1.spice
"}
C {code_shown.sym} 637.1875 -255.15625 0 0 {name=s1 only_toplevel=false value="
.control
save all
**
** ---- clock ----
let fclk     = 1e5
let tper_clk = 1/fclk
let tfr_clk  = 0.01*tper_clk
let ton_clk  = 0.5*tper_clk - 2*tfr_clk
let tper2clk = 0.95*tper_clk
**
** ---- resolution follows the fastest edge in the deck ----
let tmax  = tfr_clk/200
let tstep = tmax
**
** ---- 24 clock periods is enough to walk every transition ----
let tstop = 24*tper_clk
**
** ---- MODE: square wave, 8 clock periods per half ----
let tfr    = tfr_clk
let tper_D = 16*tper_clk
let ton_D  = 0.5*tper_D - 2*tfr
**
** ---- RSTn: low for the first 2 clock periods, then high ----
let td_R = 2*tper_clk
**
alter @v4[PULSE] = [ 0 5 0 $&tfr_clk $&tfr_clk $&ton_clk $&tper2clk 0 ]
alter @v3[PULSE] = [ 0 5 0 $&tfr $&tfr $&ton_D $&tper_D 0 ]
alter @v5[PULSE] = [ 0 5 $&td_R $&tfr $&tfr $&tstop $&tstop 0 ]
**
op

tran $&tstep $&tstop 0 $&tmax

**
plot v(clk) v(mode)+5 v(rstn)+10 v(rec_en)+15 v(treat_en)+20
write fsm_fast.raw
.endc



"}
C {lab_wire.sym} 250 -10 0 0 {name=p6 sig_type=std_logic lab=REC_EN}
C {lab_wire.sym} 150 10 2 0 {name=p7 sig_type=std_logic lab=TREAT_EN}
C {FSM2/FSM2.sym} 0 0 0 0 {name=x1}
