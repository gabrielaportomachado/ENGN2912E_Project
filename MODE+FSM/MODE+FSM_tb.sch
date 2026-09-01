v {xschem version=3.4.7 file_version=1.2}
G {}
K {}
V {}
S {}
E {}
N -650 -170 -580 -170 {lab=MODE}
N -470 -20 -470 40 {lab=RSTn}
N -360 -170 -290 -170 {lab=MODE_q}
N 400 -180 490 -180 {lab=REC_EN}
N 400 -160 490 -160 {lab=TREAT_EN}
N -470 -260 -470 -200 {lab=CLK}
N 250 -290 250 -230 {lab=CLK}
N 270 -290 270 -230 {lab=RSTn}
N -650 -60 -580 -60 {lab=VDD}
N -650 -100 -580 -100 {lab=VDD}
N 180 -290 180 -230 {lab=VDD}
N -360 -60 -290 -60 {lab=VSS}
N -360 -100 -290 -100 {lab=VSS}
N 340 -290 340 -230 {lab=VSS}
N -1176.5625 -176.71875 -1176.5625 -126.71875 {lab=VDD}
N -1176.5625 -66.71875 -1176.5625 -26.71875 {lab=GND}
N -1106.5625 -176.71875 -1106.5625 -126.71875 {lab=VSS}
N -1106.5625 -66.71875 -1106.5625 -26.71875 {lab=GND}
N -1046.5625 -176.71875 -1046.5625 -126.71875 {lab=MODE}
N -1046.5625 -66.71875 -1046.5625 -26.71875 {lab=GND}
N -986.5625 -176.71875 -986.5625 -126.71875 {lab=CLK}
N -986.5625 -66.71875 -986.5625 -26.71875 {lab=GND}
N -916.5625 -176.71875 -916.5625 -126.71875 {lab=RSTn}
N -916.5625 -66.71875 -916.5625 -26.71875 {lab=GND}
N 570 -120 570 -100 {lab=GND}
N 490 -100 490 -80 {lab=GND}
N 490 -180 570 -180 {lab=REC_EN}
N -240 -170 -170 -170 {lab=MODE_q}
N -60 -20 -60 40 {lab=RSTn}
N 50 -170 120 -170 {lab=MODE_q2}
N -60 -260 -60 -200 {lab=CLK}
N -240 -60 -170 -60 {lab=VDD}
N -240 -100 -170 -100 {lab=VDD}
N 50 -60 120 -60 {lab=VSS}
N 50 -100 120 -100 {lab=VSS}
N -290 -170 -240 -170 {lab=MODE_q}
C {lab_wire.sym} -600 -170 0 0 {name=p1 sig_type=std_logic lab=MODE}
C {lab_wire.sym} -470 20 0 0 {name=p2 sig_type=std_logic lab=RSTn
}
C {lab_wire.sym} 480 -180 0 0 {name=p3 sig_type=std_logic lab=REC_EN
}
C {lab_wire.sym} 480 -160 0 0 {name=p4 sig_type=std_logic lab=TREAT_EN
}
C {lab_wire.sym} -470 -210 1 0 {name=p5 sig_type=std_logic lab=CLK}
C {lab_wire.sym} 250 -240 1 0 {name=p6 sig_type=std_logic lab=CLK}
C {lab_wire.sym} 270 -240 1 0 {name=p7 sig_type=std_logic lab=RSTn
}
C {lab_wire.sym} -610 -60 0 0 {name=p8 sig_type=std_logic lab=VDD}
C {lab_wire.sym} -610 -100 0 0 {name=p9 sig_type=std_logic lab=VDD}
C {lab_wire.sym} 180 -240 1 0 {name=p10 sig_type=std_logic lab=VDD}
C {lab_wire.sym} -300 -60 0 0 {name=p11 sig_type=std_logic lab=VSS}
C {lab_wire.sym} -300 -100 0 0 {name=p12 sig_type=std_logic lab=VSS}
C {lab_wire.sym} 340 -240 1 0 {name=p13 sig_type=std_logic lab=VSS}
C {FSM2/FSM2.sym} 260 -170 0 0 {name=x2}
C {vsource.sym} -1176.5625 -96.71875 0 0 {name=V1 value=5 savecurrent=false}
C {gnd.sym} -1176.5625 -26.71875 0 0 {name=l1 lab=GND}
C {lab_wire.sym} -1176.5625 -166.71875 3 0 {name=p14 sig_type=std_logic lab=VDD}
C {vsource.sym} -1106.5625 -96.71875 0 0 {name=V2 value=0 savecurrent=false}
C {gnd.sym} -1106.5625 -26.71875 0 0 {name=l2 lab=GND}
C {lab_wire.sym} -1106.5625 -166.71875 3 0 {name=p15 sig_type=std_logic lab=VSS}
C {vsource.sym} -1046.5625 -96.71875 0 0 {name=V3 value=0 savecurrent=false}
C {gnd.sym} -1046.5625 -26.71875 0 0 {name=l5 lab=GND}
C {lab_wire.sym} -1046.5625 -176.71875 3 0 {name=p16 sig_type=std_logic lab=MODE}
C {vsource.sym} -986.5625 -96.71875 0 0 {name=V4 value=3.3 savecurrent=false}
C {gnd.sym} -986.5625 -26.71875 0 0 {name=l6 lab=GND}
C {lab_wire.sym} -986.5625 -166.71875 3 0 {name=p17 sig_type=std_logic lab=CLK}
C {vsource.sym} -916.5625 -96.71875 0 0 {name=V5 value=3.3 savecurrent=false}
C {gnd.sym} -916.5625 -26.71875 0 0 {name=l7 lab=GND}
C {lab_wire.sym} -916.5625 -166.71875 3 0 {name=p18 sig_type=std_logic lab=RSTn}
C {devices/code_shown.sym} -185.46875 150.15625 0 0 {name=MODELS only_toplevel=true
format="tcleval( @value )"
value="
.include $::180MCU_MODELS/design.ngspice
.lib $::180MCU_MODELS/sm141064.ngspice typical
"}
C {code_shown.sym} -180 280 0 0 {name=INCLUDE
only_toplevel=false
value="
.include /foss/designs/DBSchip/dffsnq/gf180mcu_fd_sc_mcu7t5v0__dffsnq_1.spice
.include /foss/designs/DBSchip/dffrnq/gf180mcu_fd_sc_mcu7t5v0__dffrnq_1.spice
.include /foss/designs/DBSchip/and2/gf180mcu_fd_sc_mcu7t5v0__and2_1.spice
.include /foss/designs/DBSchip/or2/gf180mcu_fd_sc_mcu7t5v0__or2_1.spice
.include /foss/designs/DBSchip/nor2/gf180mcu_fd_sc_mcu7t5v0__nor2_1.spice
"}
C {capa.sym} 570 -150 0 0 {name=C1
m=1
value=25f
footprint=1206
device="ceramic capacitor"}
C {gnd.sym} 570 -100 0 0 {name=l3 lab=GND}
C {capa.sym} 490 -130 0 0 {name=C2
m=1
value=25f
footprint=1206
device="ceramic capacitor"}
C {gnd.sym} 490 -80 0 0 {name=l4 lab=GND}
C {code_shown.sym} 717.1875 -375.15625 0 0 {name=s1 only_toplevel=false value="
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
plot v(clk) v(mode)+6 v(mode_q2)+12 v(rstn)+18 v(rec_en)+24 v(treat_en)+30
write fsm_fast.raw
.endc



"}
C {lab_wire.sym} -250 -170 0 0 {name=p19 sig_type=std_logic lab=MODE_q}
C {dffrnq/gf180mcu_fd_sc_mcu7t5v0__dffrnq_1.sym} -470 -110 0 0 {name=x1}
C {lab_wire.sym} -60 20 0 0 {name=p21 sig_type=std_logic lab=RSTn
}
C {lab_wire.sym} -60 -210 1 0 {name=p22 sig_type=std_logic lab=CLK}
C {lab_wire.sym} -200 -60 0 0 {name=p23 sig_type=std_logic lab=VDD}
C {lab_wire.sym} -200 -100 0 0 {name=p24 sig_type=std_logic lab=VDD}
C {lab_wire.sym} 110 -60 0 0 {name=p25 sig_type=std_logic lab=VSS}
C {lab_wire.sym} 110 -100 0 0 {name=p26 sig_type=std_logic lab=VSS}
C {lab_wire.sym} 100 -170 0 0 {name=p27 sig_type=std_logic lab=MODE_q2}
C {dffrnq/gf180mcu_fd_sc_mcu7t5v0__dffrnq_1.sym} -60 -110 0 0 {name=x3}
