v {xschem version=3.4.7 file_version=1.2}
G {}
K {}
V {}
S {}
E {}
N -170 -70 -110 -70 {lab=D}
N -180 -70 -170 -70 {lab=D}
N 0 80 0 140 {lab=RSTn}
N 0 140 0 150 {lab=RSTn}
N 0 -160 0 -100 {lab=CLK}
N 0 -170 0 -160 {lab=CLK}
N 110 40 170 40 {lab=vss}
N 170 40 180 40 {lab=vss}
N -170 40 -110 40 {lab=vdd}
N -180 40 -170 40 {lab=vdd}
N -626.5625 -96.71875 -626.5625 -46.71875 {lab=vdd}
N -626.5625 13.28125 -626.5625 53.28125 {lab=GND}
N -556.5625 -96.71875 -556.5625 -46.71875 {lab=vss}
N -556.5625 13.28125 -556.5625 53.28125 {lab=GND}
N -496.5625 -96.71875 -496.5625 -46.71875 {lab=D}
N -496.5625 13.28125 -496.5625 53.28125 {lab=GND}
N -436.5625 -96.71875 -436.5625 -46.71875 {lab=CLK}
N -436.5625 13.28125 -436.5625 53.28125 {lab=GND}
N -366.5625 -96.71875 -366.5625 -46.71875 {lab=RSTn}
N -366.5625 13.28125 -366.5625 53.28125 {lab=GND}
N 290 -10 290 10 {lab=GND}
N 110 -70 290 -70 {lab=Q}
N -170 0 -110 0 {lab=vdd}
N -180 0 -170 0 {lab=vdd}
N 110 0 170 0 {lab=vss}
N 170 0 180 0 {lab=vss}
C {lab_wire.sym} -150 -70 0 0 {name=p1 sig_type=std_logic lab=D}
C {lab_wire.sym} 0 120 3 0 {name=p3 sig_type=std_logic lab=RSTn}
C {lab_wire.sym} 0 -140 1 0 {name=p4 sig_type=std_logic lab=CLK}
C {lab_wire.sym} 150 40 2 0 {name=p7 sig_type=std_logic lab=vss}
C {lab_wire.sym} -150 40 0 0 {name=p8 sig_type=std_logic lab=vdd}
C {vsource.sym} -626.5625 -16.71875 0 0 {name=V1 value=3.3 savecurrent=false}
C {gnd.sym} -626.5625 53.28125 0 0 {name=l1 lab=GND}
C {lab_wire.sym} -626.5625 -86.71875 3 0 {name=p9 sig_type=std_logic lab=vdd}
C {vsource.sym} -556.5625 -16.71875 0 0 {name=V2 value=0 savecurrent=false}
C {gnd.sym} -556.5625 53.28125 0 0 {name=l2 lab=GND}
C {lab_wire.sym} -556.5625 -86.71875 3 0 {name=p10 sig_type=std_logic lab=vss}
C {vsource.sym} -496.5625 -16.71875 0 0 {name=V3 value=0 savecurrent=false}
C {gnd.sym} -496.5625 53.28125 0 0 {name=l5 lab=GND}
C {lab_wire.sym} -496.5625 -86.71875 3 0 {name=p11 sig_type=std_logic lab=D}
C {vsource.sym} -436.5625 -16.71875 0 0 {name=V4 value=3.3 savecurrent=false}
C {gnd.sym} -436.5625 53.28125 0 0 {name=l6 lab=GND}
C {lab_wire.sym} -436.5625 -86.71875 3 0 {name=p12 sig_type=std_logic lab=CLK}
C {vsource.sym} -366.5625 -16.71875 0 0 {name=V5 value=3.3 savecurrent=false}
C {gnd.sym} -366.5625 53.28125 0 0 {name=l7 lab=GND}
C {lab_wire.sym} -366.5625 -86.71875 3 0 {name=p13 sig_type=std_logic lab=RSTn}
C {capa.sym} 290 -40 0 0 {name=C1
m=1
value=25f
footprint=1206
device="ceramic capacitor"}
C {gnd.sym} 290 10 0 0 {name=l3 lab=GND}
C {lab_wire.sym} -150 0 0 0 {name=p2 sig_type=std_logic lab=vdd}
C {lab_wire.sym} 150 0 2 0 {name=p5 sig_type=std_logic lab=vss}
C {code_shown.sym} 377.1875 -495.15625 0 0 {name=s1 only_toplevel=false value="
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
C {devices/code_shown.sym} 384.53125 560.15625 0 0 {name=MODELS only_toplevel=true
format="tcleval( @value )"
value="
.include $::180MCU_MODELS/design.ngspice
.lib $::180MCU_MODELS/sm141064.ngspice typical
"}
C {lab_wire.sym} 190 -70 0 0 {name=p6 sig_type=std_logic lab=Q}
C {code_shown.sym} 1437.1875 -495.15625 0 0 {name=s2 only_toplevel=false value="
* NGSPICE file created from gf180mcu_fd_sc_mcu7t5v0__dffrnq_1.ext - technology: gf180mcuD

.subckt gf180mcu_fd_sc_mcu7t5v0__dffrnq_1 D Q RN VSS CLK VDD VNW VPW
X0 VSS.t2 CLK.t0 a_36_151# VPW.t2 nfet_05v0 ad=0.1053p pd=0.925u as=0.1782p ps=1.69u w=0.405u l=0.6u
X1 VSS.t1 RN.t0 a_1456_156# VPW.t1 nfet_05v0 ad=0.2016p pd=1.48u as=43.2f ps=0.6u w=0.36u l=0.6u
X2 Q.t1 a_2665_112# VDD.t4 VNW.t5 pfet_05v0 ad=0.5346p pd=3.31u as=0.5346p ps=3.31u w=1.215u l=0.5u
X3 a_796_472# D.t0 VSS.t6 VPW.t6 nfet_05v0 ad=93.59999f pd=0.88u as=0.1584p ps=1.6u w=0.36u l=0.6u
X4 VSS.t5 a_2665_112# a_2560_156# VPW.t0 nfet_05v0 ad=0.1224p pd=1.04u as=94.5f ps=0.885u w=0.36u l=0.6u
X5 a_2665_112# a_2248_156# a_3041_156# VPW.t5 nfet_05v0 ad=0.176p pd=1.68u as=0.134p ps=1.1u w=0.4u l=0.6u
X6 a_1000_472# a_448_472# a_796_472# VNW.t13 pfet_05v0 ad=0.2028p pd=1.3u as=0.2028p ps=1.3u w=0.78u l=0.5u
X7 a_2248_156# a_36_151# a_1308_423# VNW.t11 pfet_05v0 ad=0.25375p pd=1.51u as=0.2424p ps=1.465u w=0.505u l=0.5u
X8 a_2248_156# a_448_472# a_1308_423# VPW.t11 nfet_05v0 ad=0.2007p pd=1.475u as=0.2007p ps=1.475u w=0.36u l=0.6u
X9 VDD.t0 CLK.t1 a_36_151# VNW.t0 pfet_05v0 ad=0.2249p pd=1.385u as=0.3806p ps=2.61u w=0.865u l=0.5u
X10 a_1456_156# a_1308_423# a_1288_156# VPW.t7 nfet_05v0 ad=43.2f pd=0.6u as=43.2f ps=0.6u w=0.36u l=0.6u
X11 a_1308_423# a_1000_472# VSS.t3 VPW.t3 nfet_05v0 ad=0.2007p pd=1.475u as=0.2016p ps=1.48u w=0.36u l=0.6u
X12 Q.t0 a_2665_112# VSS.t4 VPW.t4 nfet_05v0 ad=0.3586p pd=2.51u as=0.3586p ps=2.51u w=0.815u l=0.6u
X13 a_448_472# a_36_151# VDD.t9 VNW.t10 pfet_05v0 ad=0.3806p pd=2.61u as=0.2249p ps=1.385u w=0.865u l=0.5u
X14 a_1204_472# a_36_151# a_1000_472# VNW.t9 pfet_05v0 ad=0.2028p pd=1.3u as=0.2028p ps=1.3u w=0.78u l=0.5u
X15 a_1204_472# RN.t1 VDD.t2 VNW.t3 pfet_05v0 ad=0.3432p pd=2.44u as=0.45p ps=2.02u w=0.78u l=0.5u
X16 a_2665_112# RN.t2 VDD.t3 VNW.t2 pfet_05v0 ad=0.26p pd=1.52u as=0.29465p ps=1.74u w=1u l=0.5u
X17 a_2560_156# a_36_151# a_2248_156# VPW.t0 nfet_05v0 ad=94.5f pd=0.885u as=0.2007p ps=1.475u w=0.36u l=0.6u
X18 VDD.t6 a_2248_156# a_2665_112# VNW.t6 pfet_05v0 ad=0.44p pd=2.88u as=0.26p ps=1.52u w=1u l=0.5u
X19 a_1288_156# a_448_472# a_1000_472# VPW.t10 nfet_05v0 ad=43.2f pd=0.6u as=93.59999f ps=0.88u w=0.36u l=0.6u
X20 VDD.t7 a_1308_423# a_1204_472# VNW.t7 pfet_05v0 ad=0.45p pd=2.02u as=0.2028p ps=1.3u w=0.78u l=0.5u
X21 a_2560_156# a_448_472# a_2248_156# VNW.t12 pfet_05v0 ad=0.1313p pd=1.025u as=0.25375p ps=1.51u w=0.505u l=0.5u
X22 a_448_472# a_36_151# VSS.t7 VPW.t9 nfet_05v0 ad=0.1782p pd=1.69u as=0.1053p ps=0.925u w=0.405u l=0.6u
X23 a_3041_156# RN.t3 VSS.t0 VPW.t0 nfet_05v0 ad=0.134p pd=1.1u as=0.1224p ps=1.04u w=0.36u l=0.6u
X24 VDD.t5 a_2665_112# a_2560_156# VNW.t4 pfet_05v0 ad=0.29465p pd=1.74u as=0.1313p ps=1.025u w=0.505u l=0.5u
X25 a_1308_423# a_1000_472# VDD.t1 VNW.t1 pfet_05v0 ad=0.2424p pd=1.465u as=0.2222p ps=1.89u w=0.505u l=0.5u
X26 a_1000_472# a_36_151# a_796_472# VPW.t8 nfet_05v0 ad=93.59999f pd=0.88u as=93.59999f ps=0.88u w=0.36u l=0.6u
X27 a_796_472# D.t1 VDD.t8 VNW.t8 pfet_05v0 ad=0.2028p pd=1.3u as=0.3432p ps=2.44u w=0.78u l=0.5u
R0 CLK.n0 CLK.t0 13.615
R1 CLK.n0 CLK.t1 12.3375
R2 CLK CLK.n0 8.01471
R3 VSS.n5 VSS.t6 11.0252
R4 VSS.n3 VSS.t4 8.92708
R5 VSS.n1 VSS.t3 8.4005
R6 VSS.n1 VSS.t1 8.4005
R7 VSS.n2 VSS.t0 7.3505
R8 VSS.n3 VSS.n2 6.55876
R9 VSS.n6 VSS.n0 6.46615
R10 VSS.n4 VSS.n1 6.43285
R11 VSS.n2 VSS.t5 4.5505
R12 VSS.n0 VSS.t7 4.04494
R13 VSS.n0 VSS.t2 4.04494
R14 VSS.n4 VSS.n3 0.83825
R15 VSS.n5 VSS.n4 0.7895
R16 VSS.n6 VSS.n5 0.2795
R17 VSS VSS.n6 0.0125
R18 VPW.t9 VPW.t6 2760.27
R19 VPW.t1 VPW.t3 2315.07
R20 VPW.t11 VPW.t0 2180.65
R21 VPW.t3 VPW.t11 2031.48
R22 VPW.t8 VPW.t10 1662.1
R23 VPW.t6 VPW.t8 1662.1
R24 VPW.t2 VPW.t9 1662.1
R25 VPW.t7 VPW.t1 1246.58
R26 VPW.t10 VPW.t7 1246.58
R27 VPW VPW.t2 860.731
R28 VPW.n0 VPW.t4 33.9274
R29 VPW.n0 VPW.t5 5.22563
R30 VPW.t0 VPW.n0 3.5722
R31 RN.t3 RN.t0 254.709
R32 RN.n0 RN.t2 31.4493
R33 RN.t0 RN.t1 23.7012
R34 RN RN.n0 8.14503
R35 RN.n0 RN.t3 6.79462
R36 VDD.n5 VDD.t1 9.06272
R37 VDD.n7 VDD.t8 7.70854
R38 VDD.n2 VDD.t5 7.20842
R39 VDD.n4 VDD.n2 5.89642
R40 VDD.n1 VDD.t2 5.38512
R41 VDD.n8 VDD.n0 5.36991
R42 VDD.n6 VDD.n1 5.33285
R43 VDD.n3 VDD.t6 4.66507
R44 VDD.n3 VDD.t4 4.45883
R45 VDD.n1 VDD.t7 4.30819
R46 VDD.n0 VDD.t9 2.10455
R47 VDD.n0 VDD.t0 2.10455
R48 VDD.n2 VDD.t3 1.39717
R49 VDD.n5 VDD.n4 0.78425
R50 VDD.n7 VDD.n6 0.6455
R51 VDD.n6 VDD.n5 0.3125
R52 VDD.n4 VDD.n3 0.3065
R53 VDD.n8 VDD.n7 0.2615
R54 VDD VDD.n8 0.0125
R55 Q Q.t0 8.55859
R56 Q Q.t1 4.30844
R57 VNW.t3 VNW.t1 682.644
R58 VNW.t6 VNW.t5 671.816
R59 VNW.t10 VNW.t8 671.816
R60 VNW.t7 VNW.t3 610.039
R61 VNW.t11 VNW.t12 601.145
R62 VNW.t1 VNW.t11 594.706
R63 VNW.t4 VNW.t2 478.764
R64 VNW.t2 VNW.t6 393.822
R65 VNW.t12 VNW.t4 393.822
R66 VNW.t9 VNW.t7 393.822
R67 VNW.t13 VNW.t9 393.822
R68 VNW.t8 VNW.t13 393.822
R69 VNW.t0 VNW.t10 393.822
R70 VNW VNW.t0 241.314
R71 D.n0 D.t0 13.5573
R72 D.n0 D.t1 11.0235
R73 D D.n0 8.00356
C0 a_2248_156# a_2665_112# 0.63332f
C1 VSS RN 0.44197f
C2 RN a_1308_423# 0.07929f
C3 VSS a_1000_472# 0.04356f
C4 VDD a_2560_156# 0.00217f
C5 a_1000_472# a_1308_423# 0.93419f
C6 RN a_2248_156# 0.09434f
C7 a_2248_156# a_1000_472# 0.00123f
C8 VDD D 0.00937f
C9 VNW a_1204_472# 0.01627f
C10 VDD a_2665_112# 0.10205f
C11 VDD RN 0.03498f
C12 VNW VSS 0.0106f
C13 a_3041_156# a_2665_112# 0.00177f
C14 VNW a_1308_423# 0.14901f
C15 VDD a_1000_472# 0.11921f
C16 VNW a_2248_156# 0.21243f
C17 CLK a_36_151# 0.6696f
C18 a_3041_156# RN 0.01068f
C19 Q VSS 0.1134f
C20 a_36_151# a_796_472# 0.01185f
C21 Q a_2248_156# 0.01436f
C22 VDD VNW 0.50356f
C23 a_1456_156# a_1000_472# 0
C24 a_1000_472# a_1288_156# 0
C25 Q VDD 0.14934f
C26 a_1204_472# a_448_472# 0.009f
C27 VSS a_448_472# 1.20207f
C28 a_448_472# a_1308_423# 0.8821f
C29 a_2248_156# a_448_472# 0.51037f
C30 D a_796_472# 0.08286f
C31 a_36_151# a_2560_156# 0.00367f
C32 VDD a_448_472# 0.45627f
C33 a_1204_472# a_1308_423# 0.02667f
C34 D a_36_151# 0.09411f
C35 a_796_472# a_1000_472# 0.04844f
C36 VSS a_1308_423# 0.01387f
C37 VSS a_2248_156# 0.03047f
C38 a_2248_156# a_1308_423# 0.05672f
C39 a_36_151# a_2665_112# 0.01904f
C40 VNW CLK 0.13704f
C41 RN a_36_151# 0.0801f
C42 a_36_151# a_1000_472# 0.08126f
C43 a_1456_156# a_448_472# 0.00227f
C44 VDD a_1204_472# 0.28263f
C45 VNW a_796_472# 0.01023f
C46 VDD VSS 0.01338f
C47 VDD a_1308_423# 0.09419f
C48 a_448_472# a_1288_156# 0.00207f
C49 VDD a_2248_156# 1.11667f
C50 VNW a_36_151# 1.28833f
C51 VSS a_1456_156# 0.0019f
C52 Q a_36_151# 0
C53 VSS a_1288_156# 0.0017f
C54 a_2665_112# a_2560_156# 0.11606f
C55 RN a_2560_156# 0.03878f
C56 CLK a_448_472# 0.00276f
C57 D a_1000_472# 0
C58 RN a_2665_112# 0.33647f
C59 a_796_472# a_448_472# 0.40164f
C60 RN a_1000_472# 0.0832f
C61 VNW a_2560_156# 0.02016f
C62 a_36_151# a_448_472# 0.53697f
C63 VNW D 0.12823f
C64 VSS CLK 0.02195f
C65 VNW a_2665_112# 0.35472f
C66 VNW RN 0.32949f
C67 VNW a_1000_472# 0.24136f
C68 VSS a_796_472# 0.05215f
C69 Q a_2665_112# 0.10944f
C70 a_36_151# a_1204_472# 0.007f
C71 Q RN 0
C72 VDD CLK 0.02303f
C73 VSS a_36_151# 0.29126f
C74 a_36_151# a_1308_423# 0.05539f
C75 a_2248_156# a_36_151# 0.0428f
C76 VDD a_796_472# 0
C77 Q VNW 0.03444f
C78 VDD a_36_151# 0.41709f
C79 a_448_472# a_2560_156# 0.27749f
C80 D a_448_472# 0.32879f
C81 a_2665_112# a_448_472# 0.02046f
C82 RN a_448_472# 0.07873f
C83 a_1000_472# a_448_472# 0.36196f
C84 VSS a_2560_156# 0.1285f
C85 a_2248_156# a_2560_156# 0.11969f
C86 VSS D 0.06462f
C87 VNW a_448_472# 0.34128f
C88 RN a_1204_472# 0.02104f
C89 a_1000_472# a_1204_472# 0.66083f
C90 VSS a_2665_112# 0.185f
C91 Q VPW 0.11476f
C92 VSS VPW 1.26186f
C93 RN VPW 1.36673f
C94 D VPW 0.25341f
C95 VDD VPW 0.79945f
C96 CLK VPW 0.29124f
C97 VNW VPW 6.1377f
C98 a_2560_156# VPW 0.01697f
C99 a_2665_112# VPW 0.62251f
C100 a_2248_156# VPW 0.37166f
C101 a_1204_472# VPW 0.01297f
C102 a_1000_472# VPW 0.29173f
C103 a_796_472# VPW 0.02321f
C104 a_1308_423# VPW 0.27904f
C105 a_448_472# VPW 0.68441f
C106 a_36_151# VPW 1.43589f
.ends

X1 D Q RSTn vss CLK vdd vdd vss gf180mcu_fd_sc_mcu7t5v0__dffrnq_1

"}
