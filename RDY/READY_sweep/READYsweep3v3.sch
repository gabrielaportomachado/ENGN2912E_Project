v {xschem version=3.4.7 file_version=1.2}
G {}
K {}
V {}
S {}
E {}
N -130 10 -60 10 {lab=VDD}
N 160 10 230 10 {lab=RDY1}
N 50 -80 50 -20 {lab=CLK}
N 50 160 50 220 {lab=RSTn}
N -130 80 -60 80 {lab=VDD}
N -130 120 -60 120 {lab=VDD}
N 160 80 230 80 {lab=VSS}
N 160 120 230 120 {lab=VSS}
N 280 10 350 10 {lab=RDY1}
N 570 10 640 10 {lab=RDY2}
N 460 -80 460 -20 {lab=CLK}
N 460 160 460 220 {lab=RSTn}
N 280 80 350 80 {lab=VDD}
N 280 120 350 120 {lab=VDD}
N 570 80 640 80 {lab=VSS}
N 570 120 640 120 {lab=VSS}
N 690 10 760 10 {lab=RDY2}
N 980 10 1050 10 {lab=RDY3}
N 870 -80 870 -20 {lab=CLK}
N 870 160 870 220 {lab=RSTn}
N 690 80 760 80 {lab=VDD}
N 690 120 760 120 {lab=VDD}
N 980 80 1050 80 {lab=VSS}
N 980 120 1050 120 {lab=VSS}
N 1100 10 1170 10 {lab=RDY3}
N 1390 10 1460 10 {lab=RDY4}
N 1280 -80 1280 -20 {lab=CLK}
N 1280 160 1280 220 {lab=RSTn}
N 1100 80 1170 80 {lab=VDD}
N 1100 120 1170 120 {lab=VDD}
N 1390 80 1460 80 {lab=VSS}
N 1390 120 1460 120 {lab=VSS}
N -1200 -180 -1200 -130 {lab=VDD}
N -1200 -70 -1200 -30 {lab=GND}
N -1100 -180 -1100 -130 {lab=VSS}
N -1100 -70 -1100 -30 {lab=GND}
N -1000 -180 -1000 -130 {lab=MODE}
N -1000 -70 -1000 -30 {lab=GND}
N -900 -180 -900 -130 {lab=CLK}
N -900 -70 -900 -30 {lab=GND}
N -800 -180 -800 -130 {lab=RSTn}
N -800 -70 -800 -30 {lab=GND}
N -700 -180 -700 -130 {lab=ENi}
N -700 -70 -700 -30 {lab=GND}
C {dffrnq/gf180mcu_fd_sc_mcu7t5v0__dffrnq_1.sym} 50 70 0 0 {name=x1}
C {dffrnq/gf180mcu_fd_sc_mcu7t5v0__dffrnq_1.sym} 460 70 0 0 {name=x2}
C {dffrnq/gf180mcu_fd_sc_mcu7t5v0__dffrnq_1.sym} 870 70 0 0 {name=x3}
C {dffrnq/gf180mcu_fd_sc_mcu7t5v0__dffrnq_1.sym} 1280 70 0 0 {name=x4}
C {lab_wire.sym} -80 10 0 0 {name=p1 sig_type=std_logic lab=VDD}
C {lab_wire.sym} 220 10 0 0 {name=p2 sig_type=std_logic lab=RDY1}
C {lab_wire.sym} 50 -30 1 0 {name=p3 sig_type=std_logic lab=CLK}
C {lab_wire.sym} 50 200 0 0 {name=p4 sig_type=std_logic lab=RSTn}
C {lab_wire.sym} -90 80 0 0 {name=p5 sig_type=std_logic lab=VDD}
C {lab_wire.sym} -90 120 0 0 {name=p6 sig_type=std_logic lab=VDD}
C {lab_wire.sym} 220 80 0 0 {name=p7 sig_type=std_logic lab=VSS}
C {lab_wire.sym} 220 120 0 0 {name=p8 sig_type=std_logic lab=VSS}
C {lab_wire.sym} 330 10 0 0 {name=p9 sig_type=std_logic lab=RDY1}
C {lab_wire.sym} 630 10 0 0 {name=p10 sig_type=std_logic lab=RDY2}
C {lab_wire.sym} 460 -30 1 0 {name=p11 sig_type=std_logic lab=CLK}
C {lab_wire.sym} 460 200 0 0 {name=p12 sig_type=std_logic lab=RSTn}
C {lab_wire.sym} 300 80 0 0 {name=p13 sig_type=std_logic lab=VDD}
C {lab_wire.sym} 300 120 0 0 {name=p14 sig_type=std_logic lab=VDD}
C {lab_wire.sym} 630 80 0 0 {name=p15 sig_type=std_logic lab=VSS}
C {lab_wire.sym} 630 120 0 0 {name=p16 sig_type=std_logic lab=VSS}
C {lab_wire.sym} 740 10 0 0 {name=p17 sig_type=std_logic lab=RDY2}
C {lab_wire.sym} 1040 10 0 0 {name=p18 sig_type=std_logic lab=RDY3}
C {lab_wire.sym} 870 -30 1 0 {name=p19 sig_type=std_logic lab=CLK}
C {lab_wire.sym} 870 200 0 0 {name=p20 sig_type=std_logic lab=RSTn}
C {lab_wire.sym} 710 80 0 0 {name=p21 sig_type=std_logic lab=VDD}
C {lab_wire.sym} 710 120 0 0 {name=p22 sig_type=std_logic lab=VDD}
C {lab_wire.sym} 1040 80 0 0 {name=p23 sig_type=std_logic lab=VSS}
C {lab_wire.sym} 1040 120 0 0 {name=p24 sig_type=std_logic lab=VSS}
C {lab_wire.sym} 1150 10 0 0 {name=p25 sig_type=std_logic lab=RDY3}
C {lab_wire.sym} 1450 10 0 0 {name=p26 sig_type=std_logic lab=RDY4}
C {lab_wire.sym} 1280 -30 1 0 {name=p27 sig_type=std_logic lab=CLK}
C {lab_wire.sym} 1280 200 0 0 {name=p28 sig_type=std_logic lab=RSTn}
C {lab_wire.sym} 1120 80 0 0 {name=p29 sig_type=std_logic lab=VDD}
C {lab_wire.sym} 1120 120 0 0 {name=p30 sig_type=std_logic lab=VDD}
C {lab_wire.sym} 1450 80 0 0 {name=p31 sig_type=std_logic lab=VSS}
C {lab_wire.sym} 1450 120 0 0 {name=p32 sig_type=std_logic lab=VSS}
C {vsource.sym} -1200 -100 0 0 {name=V1 value=3.3 savecurrent=false}
C {gnd.sym} -1200 -30 0 0 {name=l1 lab=GND}
C {lab_wire.sym} -1200 -170 3 0 {name=p33 sig_type=std_logic lab=VDD}
C {vsource.sym} -1100 -100 0 0 {name=V2 value=0 savecurrent=false}
C {gnd.sym} -1100 -30 0 0 {name=l2 lab=GND}
C {lab_wire.sym} -1100 -170 3 0 {name=p34 sig_type=std_logic lab=VSS}
C {vsource.sym} -1000 -100 0 0 {name=V3 value=0 savecurrent=false}
C {gnd.sym} -1000 -30 0 0 {name=l3 lab=GND}
C {lab_wire.sym} -1000 -170 3 0 {name=p35 sig_type=std_logic lab=MODE}
C {vsource.sym} -900 -100 0 0 {name=V4 value=0 savecurrent=false}
C {gnd.sym} -900 -30 0 0 {name=l4 lab=GND}
C {lab_wire.sym} -900 -170 3 0 {name=p36 sig_type=std_logic lab=CLK}
C {vsource.sym} -800 -100 0 0 {name=V5 value=0 savecurrent=false}
C {gnd.sym} -800 -30 0 0 {name=l5 lab=GND}
C {lab_wire.sym} -800 -170 3 0 {name=p37 sig_type=std_logic lab=RSTn}
C {vsource.sym} -700 -100 0 0 {name=V6 value=3.3 savecurrent=false}
C {gnd.sym} -700 -30 0 0 {name=l6 lab=GND}
C {lab_wire.sym} -700 -170 3 0 {name=p38 sig_type=std_logic lab=ENi}
C {devices/code_shown.sym} -1200 400 0 0 {name=MODELS only_toplevel=true
format="tcleval( @value )"
value="
.include $::180MCU_MODELS/design.ngspice
.lib $::180MCU_MODELS/sm141064.ngspice typical
"}
C {code_shown.sym} -1200 560 0 0 {name=INCLUDE
only_toplevel=false
value="
.include /foss/designs/DBSchip/dffsnq/gf180mcu_fd_sc_mcu7t5v0__dffsnq_1.spice
.include /foss/designs/DBSchip/dffrnq/gf180mcu_fd_sc_mcu7t5v0__dffrnq_1.spice
.include /foss/designs/DBSchip/and2/gf180mcu_fd_sc_mcu7t5v0__and2_1.spice
.include /foss/designs/DBSchip/or2/gf180mcu_fd_sc_mcu7t5v0__or2_1.spice
.include /foss/designs/DBSchip/nor2/gf180mcu_fd_sc_mcu7t5v0__nor2_1.spice
.include /foss/designs/DBSchip/nand3/gf180mcu_fd_sc_mcu7t5v0__nand3_1.spice
.include /foss/designs/DBSchip/inv_1/gf180mcu_fd_sc_mcu7t5v0__inv_1.spice
.include /foss/designs/DBSchip/ROW/READY_sweep/CHANNEL_sub.spice
"}
C {code_shown.sym} -1200 900 0 0 {name=DUTS
only_toplevel=false
value="
* port order confirmed from **.subckt line of CHANNEL.spice
.subckt chan ENi MODE RSTn CLK READY SW_REC SW_IPG SW_RECb SW_IPGb VDD VSS
XD MODE RSTn CLK VDD VSS SW_REC SW_IPG SW_RECb SW_IPGb ENi READY CHANNEL
.ends
XU1 ENi MODE RSTn CLK RDY1 SW_REC1 SW_IPG1 SW_RECB1 SW_IPGB1 VDD VSS chan
XU2 ENi MODE RSTn CLK RDY2 SW_REC2 SW_IPG2 SW_RECB2 SW_IPGB2 VDD VSS chan
XU3 ENi MODE RSTn CLK RDY3 SW_REC3 SW_IPG3 SW_RECB3 SW_IPGB3 VDD VSS chan
XU4 ENi MODE RSTn CLK RDY4 SW_REC4 SW_IPG4 SW_RECB4 SW_IPGB4 VDD VSS chan
CI1 SW_IPG1 0 25f
CI2 SW_IPG2 0 25f
CI3 SW_IPG3 0 25f
CI4 SW_IPG4 0 25f
CR1 SW_REC1 0 25f
CR2 SW_REC2 0 25f
CR3 SW_REC3 0 25f
CR4 SW_REC4 0 25f"}
C {code_shown.sym} 600 400 0 0 {name=s1 only_toplevel=false value="
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
alter @v4[PULSE] = [ 0 3.3 0 $&tfr_clk $&tfr_clk $&ton_clk $&tper2clk 0 ]
alter @v3[PULSE] = [ 0 3.3 0 $&tfr $&tfr $&ton_D $&tper_D 0 ]
alter @v5[PULSE] = [ 0 3.3 $&td_R $&tfr $&tfr $&tstop $&tstop 0 ]
**
op

tran $&tstep $&tstop 0 $&tmax

**
** ---- the N sweep ----
plot v(sw_ipg1) v(sw_ipg2)+6 v(sw_ipg3)+12 v(sw_ipg4)+18
**
** ---- READY against its own output, N=1 and N=4 ----
plot v(clk) v(rstn)+6 v(rdy1)+12 v(sw_ipg1)+18 v(rdy4)+24 v(sw_ipg4)+30
**
** ---- worst-case output excursion while READY is still low ----
** If maximum() is not recognised, try vecmax().
let pre1 = v(sw_ipg1) * (v(rdy1) < 2.5)
let pre2 = v(sw_ipg2) * (v(rdy2) < 2.5)
let pre3 = v(sw_ipg3) * (v(rdy3) < 2.5)
let pre4 = v(sw_ipg4) * (v(rdy4) < 2.5)
print maximum(pre1)
print maximum(pre2)
print maximum(pre3)
print maximum(pre4)
**
wrdata channel_ready_3v3_100k.txt v(clk) v(rstn) v(rdy1) v(rdy2) v(rdy3) v(rdy4)
wrdata channel_swipg_3v3_100k.txt v(clk) v(rstn) v(sw_ipg1) v(sw_ipg2) v(sw_ipg3) v(sw_ipg4)
wrdata channel_swrec_3v3_100k.txt v(clk) v(rstn) v(sw_rec1) v(sw_rec2) v(sw_rec3) v(sw_rec4)
**
write channel_ready_sweep_3v3_100k.raw
.endc

"}
