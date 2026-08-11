v {xschem version=3.4.7 file_version=1.2}
G {}
K {}
V {}
S {}
E {}
N -160 -510 -160 -460 {lab=vdd}
N -140 -510 -140 -460 {lab=vdd}
N 100 -150 100 -100 {lab=vdd}
N 120 -150 120 -100 {lab=vdd}
N 250 70 300 70 {lab=vdd}
N 250 110 300 110 {lab=vdd}
N 250 110 300 110 {lab=vdd}
N 290 510 340 510 {lab=vdd}
N 290 550 340 550 {lab=vdd}
N 290 550 340 550 {lab=vdd}
N 520 70 570 70 {lab=vss}
N 520 110 570 110 {lab=vss}
N 520 110 570 110 {lab=vss}
N 560 510 610 510 {lab=vss}
N 560 550 610 550 {lab=vss}
N 560 550 610 550 {lab=vss}
N -160 -260 -160 -210 {lab=vss}
N -140 -260 -140 -210 {lab=vss}
N 100 100 100 150 {lab=vss}
N 120 100 120 150 {lab=vss}
N 410 150 410 210 {lab=RSTn}
N 410 210 410 220 {lab=RSTn}
N 410 -90 410 -30 {lab=CLK}
N 410 -100 410 -90 {lab=CLK}
N 450 590 450 650 {lab=RSTn}
N 450 650 450 660 {lab=RSTn}
N 450 350 450 410 {lab=CLK}
N 450 340 450 350 {lab=CLK}
N -280 -380 -170 -380 {lab=#net1}
N -280 -340 -170 -340 {lab=REC_EN}
N -20 20 90 20 {lab=MODE}
N -110 -20 90 -20 {lab=S0}
N -30 -360 80 -360 {lab=TREAT_EN}
N 200 440 340 440 {lab=#net2}
N 520 0 600 0 {lab=REC_EN}
N 560 440 660 440 {lab=S0}
N 90 290 90 340 {lab=vdd}
N 110 290 110 340 {lab=vdd}
N 90 540 90 590 {lab=vss}
N 110 540 110 590 {lab=vss}
N -30 420 80 420 {lab=REC_EN}
N -30 460 80 460 {lab=MODE}
N 210 -0 300 -0 {lab=#net3}
C {nor2/gf180mcu_fd_sc_mcu7t5v0__nor2_1.sym} -110 -360 0 0 {name=x1}
C {dffrnq/gf180mcu_fd_sc_mcu7t5v0__dffrnq_1.sym} 410 60 0 0 {name=x5}
C {dffsnq/gf180mcu_fd_sc_mcu7t5v0__dffsnq_1.sym} 450 500 0 0 {name=x6}
C {lab_wire.sym} -160 -500 3 0 {name=p1 sig_type=std_logic lab=vdd}
C {lab_wire.sym} -140 -500 3 0 {name=p2 sig_type=std_logic lab=vdd}
C {lab_wire.sym} 100 -140 3 0 {name=p5 sig_type=std_logic lab=vdd}
C {lab_wire.sym} 120 -140 3 0 {name=p6 sig_type=std_logic lab=vdd}
C {lab_wire.sym} 290 70 0 0 {name=p9 sig_type=std_logic lab=vdd}
C {lab_wire.sym} 290 110 0 0 {name=p10 sig_type=std_logic lab=vdd}
C {lab_wire.sym} 330 510 0 0 {name=p11 sig_type=std_logic lab=vdd}
C {lab_wire.sym} 330 550 0 0 {name=p12 sig_type=std_logic lab=vdd}
C {lab_wire.sym} 560 70 0 0 {name=p13 sig_type=std_logic lab=vss}
C {lab_wire.sym} 560 110 0 0 {name=p14 sig_type=std_logic lab=vss}
C {lab_wire.sym} 600 510 0 0 {name=p15 sig_type=std_logic lab=vss}
C {lab_wire.sym} 600 550 0 0 {name=p16 sig_type=std_logic lab=vss}
C {lab_wire.sym} -160 -250 3 0 {name=p17 sig_type=std_logic lab=vss}
C {lab_wire.sym} -140 -250 3 0 {name=p18 sig_type=std_logic lab=vss}
C {lab_wire.sym} 100 110 3 0 {name=p21 sig_type=std_logic lab=vss}
C {lab_wire.sym} 120 110 3 0 {name=p22 sig_type=std_logic lab=vss}
C {lab_wire.sym} 410 190 3 0 {name=p23 sig_type=std_logic lab=RSTn}
C {lab_wire.sym} 410 -70 1 0 {name=p24 sig_type=std_logic lab=CLK}
C {lab_wire.sym} 450 630 3 0 {name=p25 sig_type=std_logic lab=RSTn}
C {lab_wire.sym} 450 370 1 0 {name=p26 sig_type=std_logic lab=CLK}
C {lab_wire.sym} -200 -340 0 0 {name=p27 sig_type=std_logic lab=REC_EN}
C {lab_wire.sym} -240 -380 0 0 {name=p28 sig_type=std_logic lab=S0}
C {lab_wire.sym} 10 20 0 0 {name=p30 sig_type=std_logic lab=MODE}
C {lab_wire.sym} 70 -360 0 0 {name=p31 sig_type=std_logic lab=TREAT_EN}
C {opin.sym} 880 -180 0 0 {name=p34 lab=REC_EN}
C {ipin.sym} -540 -130 0 0 {name=p35 lab=MODE}
C {ipin.sym} -540 -80 0 0 {name=p36 lab=RSTn}
C {ipin.sym} -540 -30 0 0 {name=p37 lab=CLK}
C {opin.sym} 870 -140 0 0 {name=p38 lab=TREAT_EN}
C {iopin.sym} -600 20 0 0 {name=p39 lab=vdd}
C {iopin.sym} -600 70 0 0 {name=p40 lab=vss}
C {lab_wire.sym} 570 0 0 0 {name=p41 sig_type=std_logic lab=REC_EN}
C {lab_wire.sym} 610 440 0 0 {name=p42 sig_type=std_logic lab=S0}
C {code_shown.sym} -240 700 0 0 {name=INCLUDE
only_toplevel=false
value="
.include /foss/designs/DBSchip/dffsnq/gf180mcu_fd_sc_mcu7t5v0__dffsnq_1.spice
.include /foss/designs/DBSchip/dffrnq/gf180mcu_fd_sc_mcu7t5v0__dffrnq_1.spice
.include /foss/designs/DBSchip/inv_1/gf180mcu_fd_sc_mcu7t5v0__inv_1.spice
.include /foss/designs/DBSchip/or2/gf180mcu_fd_sc_mcu7t5v0__or2_1.spice
.include /foss/designs/DBSchip/nor2/gf180mcu_fd_sc_mcu7t5v0__nor2_1.spice
.include /foss/designs/DBSchip/and2/gf180mcu_fd_sc_mcu7t5v0__and2_1.spice
"}
C {lab_wire.sym} -20 -20 0 0 {name=p3 sig_type=std_logic lab=S0}
C {and2/gf180mcu_fd_sc_mcu7t5v0__and2_1.sym} 150 0 0 0 {name=x2}
C {lab_wire.sym} 90 300 3 0 {name=p4 sig_type=std_logic lab=vdd}
C {lab_wire.sym} 110 300 3 0 {name=p7 sig_type=std_logic lab=vdd}
C {lab_wire.sym} 90 550 3 0 {name=p8 sig_type=std_logic lab=vss}
C {lab_wire.sym} 110 550 3 0 {name=p19 sig_type=std_logic lab=vss}
C {lab_wire.sym} 50 460 0 0 {name=p32 sig_type=std_logic lab=MODE}
C {lab_wire.sym} 40 420 0 0 {name=p20 sig_type=std_logic lab=REC_EN}
C {or2/gf180mcu_fd_sc_mcu7t5v0__or2_1.sym} 140 440 0 0 {name=x3}
