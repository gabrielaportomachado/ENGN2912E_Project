v {xschem version=3.4.7 file_version=1.2}
G {}
K {}
V {}
S {}
E {}
N -850 -810 -780 -810 {lab=ENi}
N -670 -660 -670 -600 {lab=RSTn}
N -560 -810 -490 -810 {lab=ENi_q}
N -670 -900 -670 -840 {lab=CLK}
N -850 -700 -780 -700 {lab=VDD}
N -850 -740 -780 -740 {lab=VDD}
N -560 -700 -490 -700 {lab=VSS}
N -560 -740 -490 -740 {lab=VSS}
N -440 -810 -370 -810 {lab=ENi_q}
N -260 -660 -260 -600 {lab=RSTn}
N -150 -810 -80 -810 {lab=ENi_q2}
N -260 -900 -260 -840 {lab=CLK}
N -440 -700 -370 -700 {lab=VDD}
N -440 -740 -370 -740 {lab=VDD}
N -150 -700 -80 -700 {lab=VSS}
N -150 -740 -80 -740 {lab=VSS}
N -490 -810 -440 -810 {lab=ENi_q}
N -680 -530 -680 -460 {lab=VDD}
N -660 -530 -660 -460 {lab=VDD}
N -680 -260 -680 -190 {lab=VSS}
N -660 -260 -660 -190 {lab=VSS}
N -550 -360 -480 -360 {lab=SW_RECb}
N -400 -360 -310 -360 {lab=SW_REC}
N -450 -500 -450 -430 {lab=VDD}
N -430 -500 -430 -430 {lab=VDD}
N -450 -290 -450 -220 {lab=VSS}
N -430 -290 -430 -220 {lab=VSS}
N -800 -360 -710 -360 {lab=REC_EN}
N -780 -340 -710 -340 {lab=ENi_q2}
N -800 -340 -780 -340 {lab=ENi_q2}
N -800 -380 -710 -380 {lab=READY}
N -680 -140 -680 -70 {lab=VDD}
N -660 -140 -660 -70 {lab=VDD}
N -680 130 -680 200 {lab=VSS}
N -660 130 -660 200 {lab=VSS}
N -550 30 -480 30 {lab=SW_IPGb}
N -400 30 -310 30 {lab=SW_IPG}
N -450 -110 -450 -40 {lab=VDD}
N -430 -110 -430 -40 {lab=VDD}
N -450 100 -450 170 {lab=VSS}
N -430 100 -430 170 {lab=VSS}
N -800 30 -710 30 {lab=TREAT_EN}
N -780 50 -710 50 {lab=ENi_q2}
N -800 50 -780 50 {lab=ENi_q2}
N -800 10 -710 10 {lab=READY}
C {lab_wire.sym} -800 -810 0 0 {name=p1 sig_type=std_logic lab=ENi}
C {lab_wire.sym} -670 -620 0 0 {name=p2 sig_type=std_logic lab=RSTn
}
C {lab_wire.sym} -670 -850 1 0 {name=p5 sig_type=std_logic lab=CLK}
C {lab_wire.sym} -810 -700 0 0 {name=p8 sig_type=std_logic lab=VDD}
C {lab_wire.sym} -810 -740 0 0 {name=p9 sig_type=std_logic lab=VDD}
C {lab_wire.sym} -500 -700 0 0 {name=p11 sig_type=std_logic lab=VSS}
C {lab_wire.sym} -500 -740 0 0 {name=p12 sig_type=std_logic lab=VSS}
C {lab_wire.sym} -450 -810 0 0 {name=p19 sig_type=std_logic lab=ENi_q}
C {dffrnq/gf180mcu_fd_sc_mcu7t5v0__dffrnq_1.sym} -670 -750 0 0 {name=x2}
C {lab_wire.sym} -260 -620 0 0 {name=p21 sig_type=std_logic lab=RSTn
}
C {lab_wire.sym} -260 -850 1 0 {name=p22 sig_type=std_logic lab=CLK}
C {lab_wire.sym} -400 -700 0 0 {name=p23 sig_type=std_logic lab=VDD}
C {lab_wire.sym} -400 -740 0 0 {name=p24 sig_type=std_logic lab=VDD}
C {lab_wire.sym} -90 -700 0 0 {name=p25 sig_type=std_logic lab=VSS}
C {lab_wire.sym} -90 -740 0 0 {name=p26 sig_type=std_logic lab=VSS}
C {lab_wire.sym} -100 -810 0 0 {name=p27 sig_type=std_logic lab=ENi_q2}
C {dffrnq/gf180mcu_fd_sc_mcu7t5v0__dffrnq_1.sym} -260 -750 0 0 {name=x3}
C {nand3/gf180mcu_fd_sc_mcu7t5v0__nand3_1.sym} -620 -360 0 0 {name=x4}
C {lab_wire.sym} -680 -490 1 0 {name=p4 sig_type=std_logic lab=VDD}
C {lab_wire.sym} -660 -490 1 0 {name=p6 sig_type=std_logic lab=VDD}
C {lab_wire.sym} -680 -200 1 0 {name=p10 sig_type=std_logic lab=VSS}
C {lab_wire.sym} -660 -200 1 0 {name=p13 sig_type=std_logic lab=VSS}
C {lab_wire.sym} -490 -360 0 0 {name=p14 sig_type=std_logic lab=SW_RECb}
C {inv_1/gf180mcu_fd_sc_mcu7t5v0__inv_1.sym} -450 -360 0 0 {name=x5}
C {lab_wire.sym} -320 -360 0 0 {name=p15 sig_type=std_logic lab=SW_REC}
C {lab_wire.sym} -450 -460 1 0 {name=p16 sig_type=std_logic lab=VDD}
C {lab_wire.sym} -430 -460 1 0 {name=p17 sig_type=std_logic lab=VDD}
C {lab_wire.sym} -450 -230 1 0 {name=p18 sig_type=std_logic lab=VSS}
C {lab_wire.sym} -430 -230 1 0 {name=p20 sig_type=std_logic lab=VSS}
C {lab_wire.sym} -740 -360 0 0 {name=p30 sig_type=std_logic lab=REC_EN
}
C {lab_wire.sym} -740 -340 0 0 {name=p31 sig_type=std_logic lab=ENi_q2}
C {nand3/gf180mcu_fd_sc_mcu7t5v0__nand3_1.sym} -620 30 0 0 {name=x6}
C {lab_wire.sym} -680 -100 1 0 {name=p32 sig_type=std_logic lab=VDD}
C {lab_wire.sym} -660 -100 1 0 {name=p33 sig_type=std_logic lab=VDD}
C {lab_wire.sym} -680 190 1 0 {name=p34 sig_type=std_logic lab=VSS}
C {lab_wire.sym} -660 190 1 0 {name=p35 sig_type=std_logic lab=VSS}
C {lab_wire.sym} -490 30 0 0 {name=p36 sig_type=std_logic lab=SW_IPGb}
C {inv_1/gf180mcu_fd_sc_mcu7t5v0__inv_1.sym} -450 30 0 0 {name=x7}
C {lab_wire.sym} -320 30 0 0 {name=p37 sig_type=std_logic lab=SW_IPG}
C {lab_wire.sym} -450 -70 1 0 {name=p38 sig_type=std_logic lab=VDD}
C {lab_wire.sym} -430 -70 1 0 {name=p39 sig_type=std_logic lab=VDD}
C {lab_wire.sym} -450 160 1 0 {name=p40 sig_type=std_logic lab=VSS}
C {lab_wire.sym} -430 160 1 0 {name=p41 sig_type=std_logic lab=VSS}
C {lab_wire.sym} -740 30 0 0 {name=p42 sig_type=std_logic lab=TREAT_EN
}
C {lab_wire.sym} -740 50 0 0 {name=p43 sig_type=std_logic lab=ENi_q2}
C {lab_wire.sym} -740 10 0 0 {name=p64 sig_type=std_logic lab=READY}
C {lab_wire.sym} -740 -380 0 0 {name=p66 sig_type=std_logic lab=READY}
C {ipin.sym} -1100 -780 0 0 {name=p47 lab=MODE}
C {ipin.sym} -1100 -730 0 0 {name=p48 lab=RSTn}
C {ipin.sym} -1100 -680 0 0 {name=p49 lab=CLK}
C {iopin.sym} -1160 -630 0 0 {name=p50 lab=VDD}
C {iopin.sym} -1160 -580 0 0 {name=p51 lab=VSS}
C {opin.sym} -1170 -540 0 0 {name=p52 lab=SW_REC}
C {opin.sym} -1180 -500 0 0 {name=p53 lab=SW_IPG}
C {opin.sym} -1180 -460 0 0 {name=p54 lab=SW_RECb}
C {opin.sym} -1190 -420 0 0 {name=p55 lab=SW_IPGb}
C {ipin.sym} -1100 -820 0 0 {name=p65 lab=ENi}
C {ipin.sym} -1100 -860 0 0 {name=p56 lab=READY}
