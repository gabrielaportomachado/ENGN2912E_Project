v {xschem version=3.4.7 file_version=1.2}
G {}
K {}
V {}
S {}
E {}
C {symbols/pfet_03v3.sym} -600 -200 0 0 {name=mp2
L='4u'
W='40u'
nf=1
m='1'
ad='DIFF*40u*0.18u'
as='DIFF*40u*0.18u'
pd='DIFF*2*(40u+0.18u)'
ps='DIFF*2*(40u+0.18u)'
nrd=0
nrs=0
sa=0 sb=0 sd=0
model=pfet_03v3
spiceprefix=X}
C {lab_pin.sym} -580 -230 0 1 {name=p1 sig_type=std_logic lab=vdd}
C {lab_pin.sym} -580 -170 0 1 {name=p2 sig_type=std_logic lab=a}
C {lab_pin.sym} -620 -200 0 0 {name=p3 sig_type=std_logic lab=a}
C {lab_pin.sym} -580 -200 0 1 {name=p4 sig_type=std_logic lab=vdd}
C {symbols/pfet_03v3.sym} -420 -200 0 0 {name=mp1
L='4u'
W='40u'
nf=1
m='1'
ad='DIFF*40u*0.18u'
as='DIFF*40u*0.18u'
pd='DIFF*2*(40u+0.18u)'
ps='DIFF*2*(40u+0.18u)'
nrd=0
nrs=0
sa=0 sb=0 sd=0
model=pfet_03v3
spiceprefix=X}
C {lab_pin.sym} -400 -230 0 1 {name=p5 sig_type=std_logic lab=vdd}
C {lab_pin.sym} -400 -170 0 1 {name=p6 sig_type=std_logic lab=vbn}
C {lab_pin.sym} -440 -200 0 0 {name=p7 sig_type=std_logic lab=a}
C {lab_pin.sym} -400 -200 0 1 {name=p8 sig_type=std_logic lab=vdd}
C {symbols/nfet_03v3.sym} -420 -20 0 0 {name=mn1
L='4u'
W='16u'
nf=1
m='1'
ad='DIFF*16u*0.18u'
as='DIFF*16u*0.18u'
pd='DIFF*2*(16u+0.18u)'
ps='DIFF*2*(16u+0.18u)'
nrd=0
nrs=0
sa=0 sb=0 sd=0
model=nfet_03v3
spiceprefix=X}
C {lab_pin.sym} -400 -50 0 1 {name=p9 sig_type=std_logic lab=vbn}
C {lab_pin.sym} -400 10 0 1 {name=p10 sig_type=std_logic lab=vss}
C {lab_pin.sym} -440 -20 0 0 {name=p11 sig_type=std_logic lab=vbn}
C {lab_pin.sym} -400 -20 0 1 {name=p12 sig_type=std_logic lab=vss}
C {symbols/nfet_03v3.sym} -600 -20 0 0 {name=mn2
L='4u'
W='16u'
nf=1
m='4'
ad='DIFF*16u*0.18u'
as='DIFF*16u*0.18u'
pd='DIFF*2*(16u+0.18u)'
ps='DIFF*2*(16u+0.18u)'
nrd=0
nrs=0
sa=0 sb=0 sd=0
model=nfet_03v3
spiceprefix=X}
C {lab_pin.sym} -580 -50 0 1 {name=p13 sig_type=std_logic lab=a}
C {lab_pin.sym} -580 10 0 1 {name=p14 sig_type=std_logic lab=r1}
C {lab_pin.sym} -620 -20 0 0 {name=p15 sig_type=std_logic lab=vbn}
C {lab_pin.sym} -580 -20 0 1 {name=p16 sig_type=std_logic lab=vss}
C {symbols/ppolyf_u_1k.sym} -600 140 0 0 {name=rb
W='2u'
L='RB_L'
model=ppolyf_u_1k
spiceprefix=X
m=1}
C {lab_pin.sym} -600 110 3 0 {name=p17 sig_type=std_logic lab=r1}
C {lab_pin.sym} -600 170 1 0 {name=p18 sig_type=std_logic lab=}
C {lab_pin.sym} -620 140 0 0 {name=p19 sig_type=std_logic lab=vss}
C {lab_pin.sym} -600 170 1 0 {name=p20 sig_type=std_logic lab=vss}
C {symbols/pfet_03v3.sym} -240 -200 0 0 {name=s1
L='4u'
W='0.5u'
nf=1
m='1'
ad='DIFF*0.5u*0.18u'
as='DIFF*0.5u*0.18u'
pd='DIFF*2*(0.5u+0.18u)'
ps='DIFF*2*(0.5u+0.18u)'
nrd=0
nrs=0
sa=0 sb=0 sd=0
model=pfet_03v3
spiceprefix=X}
C {lab_pin.sym} -220 -230 0 1 {name=p21 sig_type=std_logic lab=vdd}
C {lab_pin.sym} -220 -170 0 1 {name=p22 sig_type=std_logic lab=s1}
C {lab_pin.sym} -260 -200 0 0 {name=p23 sig_type=std_logic lab=s1}
C {lab_pin.sym} -220 -200 0 1 {name=p24 sig_type=std_logic lab=vdd}
C {symbols/pfet_03v3.sym} -240 -100 0 0 {name=s2
L='4u'
W='0.5u'
nf=1
m='1'
ad='DIFF*0.5u*0.18u'
as='DIFF*0.5u*0.18u'
pd='DIFF*2*(0.5u+0.18u)'
ps='DIFF*2*(0.5u+0.18u)'
nrd=0
nrs=0
sa=0 sb=0 sd=0
model=pfet_03v3
spiceprefix=X}
C {lab_pin.sym} -220 -130 0 1 {name=p25 sig_type=std_logic lab=s1}
C {lab_pin.sym} -220 -70 0 1 {name=p26 sig_type=std_logic lab=s2}
C {lab_pin.sym} -260 -100 0 0 {name=p27 sig_type=std_logic lab=s2}
C {lab_pin.sym} -220 -100 0 1 {name=p28 sig_type=std_logic lab=vdd}
C {symbols/pfet_03v3.sym} -240 0 0 0 {name=s3
L='4u'
W='0.5u'
nf=1
m='1'
ad='DIFF*0.5u*0.18u'
as='DIFF*0.5u*0.18u'
pd='DIFF*2*(0.5u+0.18u)'
ps='DIFF*2*(0.5u+0.18u)'
nrd=0
nrs=0
sa=0 sb=0 sd=0
model=pfet_03v3
spiceprefix=X}
C {lab_pin.sym} -220 -30 0 1 {name=p29 sig_type=std_logic lab=s2}
C {lab_pin.sym} -220 30 0 1 {name=p30 sig_type=std_logic lab=vbn}
C {lab_pin.sym} -260 0 0 0 {name=p31 sig_type=std_logic lab=vbn}
C {lab_pin.sym} -220 0 0 1 {name=p32 sig_type=std_logic lab=vdd}
C {symbols/ppolyf_u_3k.sym} 0 100 0 0 {name=ra1
W='1u'
L='(VDDN-VCM_IN-VTT)/ILAD/3000*1u'
model=ppolyf_u_3k
spiceprefix=X
m=1}
C {lab_pin.sym} 0 70 3 0 {name=p33 sig_type=std_logic lab=vdd}
C {lab_pin.sym} 0 130 1 0 {name=p34 sig_type=std_logic lab=vg1}
C {lab_pin.sym} -20 100 0 0 {name=p35 sig_type=std_logic lab=vss}
C {symbols/ppolyf_u_3k.sym} 120 100 0 0 {name=ra2
W='1u'
L='VTT/ILAD/3000*1u'
model=ppolyf_u_3k
spiceprefix=X
m=1}
C {lab_pin.sym} 120 70 3 0 {name=p36 sig_type=std_logic lab=vg1}
C {lab_pin.sym} 120 130 1 0 {name=p37 sig_type=std_logic lab=vcm_in}
C {lab_pin.sym} 100 100 0 0 {name=p38 sig_type=std_logic lab=vss}
C {symbols/ppolyf_u_3k.sym} 240 100 0 0 {name=ra3
W='1u'
L='VCM_IN/ILAD/3000*1u'
model=ppolyf_u_3k
spiceprefix=X
m=1}
C {lab_pin.sym} 240 70 3 0 {name=p39 sig_type=std_logic lab=vcm_in}
C {lab_pin.sym} 240 130 1 0 {name=p40 sig_type=std_logic lab=vss}
C {lab_pin.sym} 220 100 0 0 {name=p41 sig_type=std_logic lab=vss}
C {symbols/ppolyf_u_3k.sym} 360 100 0 0 {name=rb1
W='1u'
L='(VDDN-VOCM-VTT)/ILAD/3000*1u'
model=ppolyf_u_3k
spiceprefix=X
m=1}
C {lab_pin.sym} 360 70 3 0 {name=p42 sig_type=std_logic lab=vdd}
C {lab_pin.sym} 360 130 1 0 {name=p43 sig_type=std_logic lab=vg2}
C {lab_pin.sym} 340 100 0 0 {name=p44 sig_type=std_logic lab=vss}
C {symbols/ppolyf_u_3k.sym} 480 100 0 0 {name=rb2
W='1u'
L='VTT/ILAD/3000*1u'
model=ppolyf_u_3k
spiceprefix=X
m=1}
C {lab_pin.sym} 480 70 3 0 {name=p45 sig_type=std_logic lab=vg2}
C {lab_pin.sym} 480 130 1 0 {name=p46 sig_type=std_logic lab=vcm_out}
C {lab_pin.sym} 460 100 0 0 {name=p47 sig_type=std_logic lab=vss}
C {symbols/ppolyf_u_3k.sym} 600 100 0 0 {name=rb3
W='1u'
L='VOCM/ILAD/3000*1u'
model=ppolyf_u_3k
spiceprefix=X
m=1}
C {lab_pin.sym} 600 70 3 0 {name=p48 sig_type=std_logic lab=vcm_out}
C {lab_pin.sym} 600 130 1 0 {name=p49 sig_type=std_logic lab=vss}
C {lab_pin.sym} 580 100 0 0 {name=p50 sig_type=std_logic lab=vss}
C {opin.sym} 700 -300 0 1 {name=io51 lab=vbn}
C {opin.sym} 700 -260 0 1 {name=io52 lab=vcm_in}
C {opin.sym} 700 -220 0 1 {name=io53 lab=vg1}
C {opin.sym} 700 -180 0 1 {name=io54 lab=vcm_out}
C {opin.sym} 700 -140 0 1 {name=io55 lab=vg2}
C {iopin.sym} -700 -100 0 0 {name=io56 lab=vdd}
C {iopin.sym} -700 -60 0 0 {name=io57 lab=vss}
T {A4a real bias: beta-multiplier master + start-up stack + two resistor ladders (generated by scripts/gen_a4a_sch.py).} -700 -360 0 0 0.3 0.3 {}
