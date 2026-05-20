v {xschem version=3.4.7 file_version=1.2}
G {}
K {}
V {}
S {}
E {}
C {ipin.sym} -110 -390 0 0 {name=p1 lab=D}
C {ipin.sym} 0 -320 0 0 {name=p2 lab=RN}
C {ipin.sym} 130 -260 0 0 {name=p3 lab=CLK}
C {opin.sym} 200 -220 0 0 {name=p4 lab=Q}
C {ipin.sym} 360 -160 0 0 {name=p5 lab=VDD}
C {ipin.sym} 460 -110 0 0 {name=p6 lab=VNW}
C {ipin.sym} 560 -70 0 0 {name=p7 lab=VPW}
C {ipin.sym} 690 0 0 0 {name=p8 lab=VSS}
C {code_shown.sym} -190 10 0 0 {name=s1 only_toplevel=false value="
.include /foss/designs/DBSchip/gf180mcu_fd_sc_mcu7t5v0__dffrnq_1.cdl
"}
