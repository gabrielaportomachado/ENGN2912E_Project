v {xschem version=3.4.7 file_version=1.2}
G {}
K {}
V {}
S {}
E {}
N -130 10 -60 10 {lab=ENi}
N 50 160 50 220 {lab=RSTn}
N 160 10 230 10 {lab=ENi_q}
N 50 -80 50 -20 {lab=CLK}
N -130 120 -60 120 {lab=VDD}
N -130 80 -60 80 {lab=VDD}
N 160 120 230 120 {lab=VSS}
N 160 80 230 80 {lab=VSS}
N 280 10 350 10 {lab=ENi_q}
N 460 160 460 220 {lab=RSTn}
N 570 10 640 10 {lab=ENi_q2}
N 460 -80 460 -20 {lab=CLK}
N 280 120 350 120 {lab=VDD}
N 280 80 350 80 {lab=VDD}
N 570 120 640 120 {lab=VSS}
N 570 80 640 80 {lab=VSS}
N 230 10 280 10 {lab=ENi_q}
N 130 -290 130 -220 {lab=VDD}
N 40 290 40 360 {lab=VDD}
N 60 290 60 360 {lab=VDD}
N 150 -290 150 -220 {lab=VSS}
N 40 560 40 630 {lab=VSS}
N 60 560 60 630 {lab=VSS}
N 170 460 240 460 {lab=SW_RECb}
N 320 460 410 460 {lab=SW_REC}
N 270 320 270 390 {lab=VDD}
N 290 320 290 390 {lab=VDD}
N 270 530 270 600 {lab=VSS}
N 290 530 290 600 {lab=VSS}
N 360 -170 450 -170 {lab=REC_EN}
N 360 -150 450 -150 {lab=TREAT_EN}
N -80 460 10 460 {lab=REC_EN}
N -60 480 10 480 {lab=ENi_q2}
N -80 480 -60 480 {lab=ENi_q2}
N -80 440 10 440 {lab=READY}
N 40 680 40 750 {lab=VDD}
N 60 680 60 750 {lab=VDD}
N 40 950 40 1020 {lab=VSS}
N 60 950 60 1020 {lab=VSS}
N 170 850 240 850 {lab=SW_IPGb}
N 320 850 410 850 {lab=SW_IPG}
N 270 710 270 780 {lab=VDD}
N 290 710 290 780 {lab=VDD}
N 270 920 270 990 {lab=VSS}
N 290 920 290 990 {lab=VSS}
N -80 850 10 850 {lab=TREAT_EN}
N -60 870 10 870 {lab=ENi_q2}
N -80 870 -60 870 {lab=ENi_q2}
N -80 830 10 830 {lab=READY}
N -180 -200 -120 -200 {lab=RSTn}
N -180 -160 -120 -160 {lab=MODE}
N -180 -110 -120 -110 {lab=CLK}
C {MODE+FSM/MODE+FSM.sym} 30 -110 0 0 {name=x1}
C {lab_wire.sym} -80 10 0 0 {name=p1 sig_type=std_logic lab=ENi}
C {lab_wire.sym} 50 200 0 0 {name=p2 sig_type=std_logic lab=RSTn
}
C {lab_wire.sym} 50 -30 1 0 {name=p5 sig_type=std_logic lab=CLK}
C {lab_wire.sym} -90 120 0 0 {name=p8 sig_type=std_logic lab=VDD}
C {lab_wire.sym} -90 80 0 0 {name=p9 sig_type=std_logic lab=VDD}
C {lab_wire.sym} 220 120 0 0 {name=p11 sig_type=std_logic lab=VSS}
C {lab_wire.sym} 220 80 0 0 {name=p12 sig_type=std_logic lab=VSS}
C {lab_wire.sym} 270 10 0 0 {name=p19 sig_type=std_logic lab=ENi_q}
C {dffrnq/gf180mcu_fd_sc_mcu7t5v0__dffrnq_1.sym} 50 70 0 0 {name=x2}
C {lab_wire.sym} 460 200 0 0 {name=p21 sig_type=std_logic lab=RSTn
}
C {lab_wire.sym} 460 -30 1 0 {name=p22 sig_type=std_logic lab=CLK}
C {lab_wire.sym} 320 120 0 0 {name=p23 sig_type=std_logic lab=VDD}
C {lab_wire.sym} 320 80 0 0 {name=p24 sig_type=std_logic lab=VDD}
C {lab_wire.sym} 630 120 0 0 {name=p25 sig_type=std_logic lab=VSS}
C {lab_wire.sym} 630 80 0 0 {name=p26 sig_type=std_logic lab=VSS}
C {lab_wire.sym} 620 10 0 0 {name=p27 sig_type=std_logic lab=ENi_q2}
C {dffrnq/gf180mcu_fd_sc_mcu7t5v0__dffrnq_1.sym} 460 70 0 0 {name=x3}
C {nand3/gf180mcu_fd_sc_mcu7t5v0__nand3_1.sym} 100 460 0 0 {name=x4}
C {lab_wire.sym} 130 -250 1 0 {name=p3 sig_type=std_logic lab=VDD}
C {lab_wire.sym} 40 330 1 0 {name=p4 sig_type=std_logic lab=VDD}
C {lab_wire.sym} 60 330 1 0 {name=p6 sig_type=std_logic lab=VDD}
C {lab_wire.sym} 150 -230 1 0 {name=p7 sig_type=std_logic lab=VSS}
C {lab_wire.sym} 40 620 1 0 {name=p10 sig_type=std_logic lab=VSS}
C {lab_wire.sym} 60 620 1 0 {name=p13 sig_type=std_logic lab=VSS}
C {lab_wire.sym} 230 460 0 0 {name=p14 sig_type=std_logic lab=SW_RECb}
C {inv_1/gf180mcu_fd_sc_mcu7t5v0__inv_1.sym} 270 460 0 0 {name=x5}
C {lab_wire.sym} 400 460 0 0 {name=p15 sig_type=std_logic lab=SW_REC}
C {lab_wire.sym} 270 360 1 0 {name=p16 sig_type=std_logic lab=VDD}
C {lab_wire.sym} 290 360 1 0 {name=p17 sig_type=std_logic lab=VDD}
C {lab_wire.sym} 270 590 1 0 {name=p18 sig_type=std_logic lab=VSS}
C {lab_wire.sym} 290 590 1 0 {name=p20 sig_type=std_logic lab=VSS}
C {lab_wire.sym} 440 -170 0 0 {name=p28 sig_type=std_logic lab=REC_EN
}
C {lab_wire.sym} 440 -150 0 0 {name=p29 sig_type=std_logic lab=TREAT_EN
}
C {lab_wire.sym} -20 460 0 0 {name=p30 sig_type=std_logic lab=REC_EN
}
C {lab_wire.sym} -20 480 0 0 {name=p31 sig_type=std_logic lab=ENi_q2}
C {nand3/gf180mcu_fd_sc_mcu7t5v0__nand3_1.sym} 100 850 0 0 {name=x6}
C {lab_wire.sym} 40 720 1 0 {name=p32 sig_type=std_logic lab=VDD}
C {lab_wire.sym} 60 720 1 0 {name=p33 sig_type=std_logic lab=VDD}
C {lab_wire.sym} 40 1010 1 0 {name=p34 sig_type=std_logic lab=VSS}
C {lab_wire.sym} 60 1010 1 0 {name=p35 sig_type=std_logic lab=VSS}
C {lab_wire.sym} 230 850 0 0 {name=p36 sig_type=std_logic lab=SW_IPGb}
C {inv_1/gf180mcu_fd_sc_mcu7t5v0__inv_1.sym} 270 850 0 0 {name=x7}
C {lab_wire.sym} 400 850 0 0 {name=p37 sig_type=std_logic lab=SW_IPG}
C {lab_wire.sym} 270 750 1 0 {name=p38 sig_type=std_logic lab=VDD}
C {lab_wire.sym} 290 750 1 0 {name=p39 sig_type=std_logic lab=VDD}
C {lab_wire.sym} 270 980 1 0 {name=p40 sig_type=std_logic lab=VSS}
C {lab_wire.sym} 290 980 1 0 {name=p41 sig_type=std_logic lab=VSS}
C {lab_wire.sym} -20 850 0 0 {name=p42 sig_type=std_logic lab=TREAT_EN
}
C {lab_wire.sym} -20 870 0 0 {name=p43 sig_type=std_logic lab=ENi_q2}
C {lab_wire.sym} -130 -200 0 0 {name=p44 sig_type=std_logic lab=RSTn
}
C {lab_wire.sym} -130 -160 0 0 {name=p45 sig_type=std_logic lab=MODE
}
C {lab_wire.sym} -130 -110 0 0 {name=p46 sig_type=std_logic lab=CLK
}
C {ipin.sym} -300 -200 0 0 {name=p47 lab=MODE}
C {ipin.sym} -300 -150 0 0 {name=p48 lab=RSTn}
C {ipin.sym} -300 -100 0 0 {name=p49 lab=CLK}
C {iopin.sym} -360 -50 0 0 {name=p50 lab=VDD}
C {iopin.sym} -360 0 0 0 {name=p51 lab=VSS}
C {opin.sym} -370 40 0 0 {name=p52 lab=SW_REC}
C {opin.sym} -380 80 0 0 {name=p53 lab=SW_IPG}
C {opin.sym} -380 120 0 0 {name=p54 lab=SW_RECb}
C {opin.sym} -390 160 0 0 {name=p55 lab=SW_IPGb}
C {lab_wire.sym} -20 830 0 0 {name=p64 sig_type=std_logic lab=READY}
C {ipin.sym} -300 -240 0 0 {name=p65 lab=ENi}
C {lab_wire.sym} -20 440 0 0 {name=p66 sig_type=std_logic lab=READY}
C {ipin.sym} -300 -280 0 0 {name=p56 lab=READY}
