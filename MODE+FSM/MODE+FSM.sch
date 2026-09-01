v {xschem version=3.4.7 file_version=1.2}
G {}
K {}
V {}
S {}
E {}
N -630 -50 -560 -50 {lab=MODE}
N -450 100 -450 160 {lab=RSTn}
N -340 -50 -270 -50 {lab=MODE_q}
N 420 -60 510 -60 {lab=REC_EN}
N 420 -40 510 -40 {lab=TREAT_EN}
N -450 -140 -450 -80 {lab=CLK}
N 270 -170 270 -110 {lab=CLK}
N 290 -170 290 -110 {lab=RSTn}
N -630 60 -560 60 {lab=VDD}
N -630 20 -560 20 {lab=VDD}
N 200 -170 200 -110 {lab=VDD}
N -340 60 -270 60 {lab=VSS}
N -340 20 -270 20 {lab=VSS}
N 360 -170 360 -110 {lab=VSS}
N -220 -50 -150 -50 {lab=MODE_q}
N -40 100 -40 160 {lab=RSTn}
N 70 -50 140 -50 {lab=MODE_q2}
N -40 -140 -40 -80 {lab=CLK}
N -220 60 -150 60 {lab=VDD}
N -220 20 -150 20 {lab=VDD}
N 70 60 140 60 {lab=VSS}
N 70 20 140 20 {lab=VSS}
N -270 -50 -220 -50 {lab=MODE_q}
C {lab_wire.sym} -580 -50 0 0 {name=p1 sig_type=std_logic lab=MODE}
C {lab_wire.sym} -450 140 0 0 {name=p2 sig_type=std_logic lab=RSTn
}
C {lab_wire.sym} 500 -60 0 0 {name=p3 sig_type=std_logic lab=REC_EN
}
C {lab_wire.sym} 500 -40 0 0 {name=p4 sig_type=std_logic lab=TREAT_EN
}
C {lab_wire.sym} -450 -90 1 0 {name=p5 sig_type=std_logic lab=CLK}
C {lab_wire.sym} 270 -120 1 0 {name=p6 sig_type=std_logic lab=CLK}
C {lab_wire.sym} 290 -120 1 0 {name=p7 sig_type=std_logic lab=RSTn
}
C {lab_wire.sym} -590 60 0 0 {name=p8 sig_type=std_logic lab=VDD}
C {lab_wire.sym} -590 20 0 0 {name=p9 sig_type=std_logic lab=VDD}
C {lab_wire.sym} 200 -120 1 0 {name=p10 sig_type=std_logic lab=VDD}
C {lab_wire.sym} -280 60 0 0 {name=p11 sig_type=std_logic lab=VSS}
C {lab_wire.sym} -280 20 0 0 {name=p12 sig_type=std_logic lab=VSS}
C {lab_wire.sym} 360 -120 1 0 {name=p13 sig_type=std_logic lab=VSS}
C {FSM2/FSM2.sym} 280 -50 0 0 {name=x2}
C {lab_wire.sym} -230 -50 0 0 {name=p19 sig_type=std_logic lab=MODE_q}
C {dffrnq/gf180mcu_fd_sc_mcu7t5v0__dffrnq_1.sym} -450 10 0 0 {name=x1}
C {lab_wire.sym} -40 140 0 0 {name=p21 sig_type=std_logic lab=RSTn
}
C {lab_wire.sym} -40 -90 1 0 {name=p22 sig_type=std_logic lab=CLK}
C {lab_wire.sym} -180 60 0 0 {name=p23 sig_type=std_logic lab=VDD}
C {lab_wire.sym} -180 20 0 0 {name=p24 sig_type=std_logic lab=VDD}
C {lab_wire.sym} 130 60 0 0 {name=p25 sig_type=std_logic lab=VSS}
C {lab_wire.sym} 130 20 0 0 {name=p26 sig_type=std_logic lab=VSS}
C {lab_wire.sym} 120 -50 0 0 {name=p27 sig_type=std_logic lab=MODE_q2}
C {dffrnq/gf180mcu_fd_sc_mcu7t5v0__dffrnq_1.sym} -40 10 0 0 {name=x3}
C {ipin.sym} -780 -100 0 0 {name=p35 lab=MODE}
C {ipin.sym} -780 -50 0 0 {name=p36 lab=RSTn}
C {ipin.sym} -780 0 0 0 {name=p37 lab=CLK}
C {iopin.sym} -840 50 0 0 {name=p39 lab=VDD}
C {iopin.sym} -840 100 0 0 {name=p40 lab=VSS}
C {opin.sym} -850 140 0 0 {name=p34 lab=REC_EN}
C {opin.sym} -860 180 0 0 {name=p38 lab=TREAT_EN}
