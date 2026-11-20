v {xschem version=3.4.7 file_version=1.2}
G {}
K {}
V {}
S {}
E {}
C {symbols/pfet_03v3.sym} -400 -200 0 0 {name=mt1
L='CMP_LT'
W='CMP_WT'
nf=1
m=1
ad='CMP_WT*0.18u'
as='CMP_WT*0.18u'
pd='2*(CMP_WT+0.18u)'
ps='2*(CMP_WT+0.18u)'
nrd=0
nrs=0
sa=0 sb=0 sd=0
model=pfet_03v3
spiceprefix=X}
C {lab_pin.sym} -380 -230 0 1 {name=p1 sig_type=std_logic lab=vdd_cmp}
C {lab_pin.sym} -380 -170 0 1 {name=p2 sig_type=std_logic lab=tl}
C {lab_pin.sym} -420 -200 0 0 {name=p3 sig_type=std_logic lab=clkb}
C {lab_pin.sym} -380 -200 0 1 {name=p4 sig_type=std_logic lab=vdd_cmp}
C {symbols/pfet_03v3.sym} -520 -80 0 0 {name=m1
L='CMP_LP'
W='CMP_WP'
nf=1
m=1
ad='CMP_WP*0.18u'
as='CMP_WP*0.18u'
pd='2*(CMP_WP+0.18u)'
ps='2*(CMP_WP+0.18u)'
nrd=0
nrs=0
sa=0 sb=0 sd=0
model=pfet_03v3
spiceprefix=X}
C {lab_pin.sym} -500 -110 0 1 {name=p5 sig_type=std_logic lab=tl}
C {lab_pin.sym} -500 -50 0 1 {name=p6 sig_type=std_logic lab=a1}
C {lab_pin.sym} -540 -80 0 0 {name=p7 sig_type=std_logic lab=inp}
C {lab_pin.sym} -500 -80 0 1 {name=p8 sig_type=std_logic lab=vdd_cmp}
C {symbols/pfet_03v3.sym} -280 -80 0 0 {name=m2
L='CMP_LP'
W='CMP_WP'
nf=1
m=1
ad='CMP_WP*0.18u'
as='CMP_WP*0.18u'
pd='2*(CMP_WP+0.18u)'
ps='2*(CMP_WP+0.18u)'
nrd=0
nrs=0
sa=0 sb=0 sd=0
model=pfet_03v3
spiceprefix=X}
C {lab_pin.sym} -260 -110 0 1 {name=p9 sig_type=std_logic lab=tl}
C {lab_pin.sym} -260 -50 0 1 {name=p10 sig_type=std_logic lab=a2}
C {lab_pin.sym} -300 -80 0 0 {name=p11 sig_type=std_logic lab=inn}
C {lab_pin.sym} -260 -80 0 1 {name=p12 sig_type=std_logic lab=vdd_cmp}
C {symbols/nfet_03v3.sym} -520 60 0 0 {name=mr1
L='CMP_LR'
W='CMP_WR'
nf=1
m=1
ad='CMP_WR*0.18u'
as='CMP_WR*0.18u'
pd='2*(CMP_WR+0.18u)'
ps='2*(CMP_WR+0.18u)'
nrd=0
nrs=0
sa=0 sb=0 sd=0
model=nfet_03v3
spiceprefix=X}
C {lab_pin.sym} -500 30 0 1 {name=p13 sig_type=std_logic lab=a1}
C {lab_pin.sym} -500 90 0 1 {name=p14 sig_type=std_logic lab=vss}
C {lab_pin.sym} -540 60 0 0 {name=p15 sig_type=std_logic lab=clkb}
C {lab_pin.sym} -500 60 0 1 {name=p16 sig_type=std_logic lab=vss}
C {symbols/nfet_03v3.sym} -280 60 0 0 {name=mr2
L='CMP_LR'
W='CMP_WR'
nf=1
m=1
ad='CMP_WR*0.18u'
as='CMP_WR*0.18u'
pd='2*(CMP_WR+0.18u)'
ps='2*(CMP_WR+0.18u)'
nrd=0
nrs=0
sa=0 sb=0 sd=0
model=nfet_03v3
spiceprefix=X}
C {lab_pin.sym} -260 30 0 1 {name=p17 sig_type=std_logic lab=a2}
C {lab_pin.sym} -260 90 0 1 {name=p18 sig_type=std_logic lab=vss}
C {lab_pin.sym} -300 60 0 0 {name=p19 sig_type=std_logic lab=clkb}
C {lab_pin.sym} -260 60 0 1 {name=p20 sig_type=std_logic lab=vss}
C {capa.sym} -620 60 0 0 {name=cxa1 m=1 value='CMP_CA' footprint=1206 device="ceramic capacitor"}
C {lab_pin.sym} -620 30 3 0 {name=p21 sig_type=std_logic lab=a1}
C {lab_pin.sym} -620 90 1 0 {name=p22 sig_type=std_logic lab=vss}
C {capa.sym} -180 60 0 0 {name=cxa2 m=1 value='CMP_CA' footprint=1206 device="ceramic capacitor"}
C {lab_pin.sym} -180 30 3 0 {name=p23 sig_type=std_logic lab=a2}
C {lab_pin.sym} -180 90 1 0 {name=p24 sig_type=std_logic lab=vss}
C {symbols/nfet_03v3.sym} -80 140 0 0 {name=mc1
L='CMP_LC'
W='CMP_WC'
nf=1
m=1
ad='CMP_WC*0.18u'
as='CMP_WC*0.18u'
pd='2*(CMP_WC+0.18u)'
ps='2*(CMP_WC+0.18u)'
nrd=0
nrs=0
sa=0 sb=0 sd=0
model=nfet_03v3
spiceprefix=X}
C {lab_pin.sym} -60 110 0 1 {name=p25 sig_type=std_logic lab=s1}
C {lab_pin.sym} -60 170 0 1 {name=p26 sig_type=std_logic lab=vss}
C {lab_pin.sym} -100 140 0 0 {name=p27 sig_type=std_logic lab=a1}
C {lab_pin.sym} -60 140 0 1 {name=p28 sig_type=std_logic lab=vss}
C {symbols/nfet_03v3.sym} 160 140 0 0 {name=mc2
L='CMP_LC'
W='CMP_WC'
nf=1
m=1
ad='CMP_WC*0.18u'
as='CMP_WC*0.18u'
pd='2*(CMP_WC+0.18u)'
ps='2*(CMP_WC+0.18u)'
nrd=0
nrs=0
sa=0 sb=0 sd=0
model=nfet_03v3
spiceprefix=X}
C {lab_pin.sym} 180 110 0 1 {name=p29 sig_type=std_logic lab=s2}
C {lab_pin.sym} 180 170 0 1 {name=p30 sig_type=std_logic lab=vss}
C {lab_pin.sym} 140 140 0 0 {name=p31 sig_type=std_logic lab=a2}
C {lab_pin.sym} 180 140 0 1 {name=p32 sig_type=std_logic lab=vss}
C {symbols/nfet_03v3.sym} -80 20 0 0 {name=mn1
L='CMP_LN'
W='CMP_WN'
nf=1
m=1
ad='CMP_WN*0.18u'
as='CMP_WN*0.18u'
pd='2*(CMP_WN+0.18u)'
ps='2*(CMP_WN+0.18u)'
nrd=0
nrs=0
sa=0 sb=0 sd=0
model=nfet_03v3
spiceprefix=X}
C {lab_pin.sym} -60 -10 0 1 {name=p33 sig_type=std_logic lab=o1}
C {lab_pin.sym} -60 50 0 1 {name=p34 sig_type=std_logic lab=s1}
C {lab_pin.sym} -100 20 0 0 {name=p35 sig_type=std_logic lab=o2}
C {lab_pin.sym} -60 20 0 1 {name=p36 sig_type=std_logic lab=vss}
C {symbols/nfet_03v3.sym} 160 20 0 0 {name=mn2
L='CMP_LN'
W='CMP_WN'
nf=1
m=1
ad='CMP_WN*0.18u'
as='CMP_WN*0.18u'
pd='2*(CMP_WN+0.18u)'
ps='2*(CMP_WN+0.18u)'
nrd=0
nrs=0
sa=0 sb=0 sd=0
model=nfet_03v3
spiceprefix=X}
C {lab_pin.sym} 180 -10 0 1 {name=p37 sig_type=std_logic lab=o2}
C {lab_pin.sym} 180 50 0 1 {name=p38 sig_type=std_logic lab=s2}
C {lab_pin.sym} 140 20 0 0 {name=p39 sig_type=std_logic lab=o1}
C {lab_pin.sym} 180 20 0 1 {name=p40 sig_type=std_logic lab=vss}
C {symbols/pfet_03v3.sym} -80 -100 0 0 {name=mq1
L='CMP_LQ'
W='CMP_WQ'
nf=1
m=1
ad='CMP_WQ*0.18u'
as='CMP_WQ*0.18u'
pd='2*(CMP_WQ+0.18u)'
ps='2*(CMP_WQ+0.18u)'
nrd=0
nrs=0
sa=0 sb=0 sd=0
model=pfet_03v3
spiceprefix=X}
C {lab_pin.sym} -60 -130 0 1 {name=p41 sig_type=std_logic lab=vdd_cmp}
C {lab_pin.sym} -60 -70 0 1 {name=p42 sig_type=std_logic lab=o1}
C {lab_pin.sym} -100 -100 0 0 {name=p43 sig_type=std_logic lab=o2}
C {lab_pin.sym} -60 -100 0 1 {name=p44 sig_type=std_logic lab=vdd_cmp}
C {symbols/pfet_03v3.sym} 160 -100 0 0 {name=mq2
L='CMP_LQ'
W='CMP_WQ'
nf=1
m=1
ad='CMP_WQ*0.18u'
as='CMP_WQ*0.18u'
pd='2*(CMP_WQ+0.18u)'
ps='2*(CMP_WQ+0.18u)'
nrd=0
nrs=0
sa=0 sb=0 sd=0
model=pfet_03v3
spiceprefix=X}
C {lab_pin.sym} 180 -130 0 1 {name=p45 sig_type=std_logic lab=vdd_cmp}
C {lab_pin.sym} 180 -70 0 1 {name=p46 sig_type=std_logic lab=o2}
C {lab_pin.sym} 140 -100 0 0 {name=p47 sig_type=std_logic lab=o1}
C {lab_pin.sym} 180 -100 0 1 {name=p48 sig_type=std_logic lab=vdd_cmp}
C {symbols/pfet_03v3.sym} -80 -220 0 0 {name=mp1
L='CMP_LS'
W='CMP_WS'
nf=1
m=1
ad='CMP_WS*0.18u'
as='CMP_WS*0.18u'
pd='2*(CMP_WS+0.18u)'
ps='2*(CMP_WS+0.18u)'
nrd=0
nrs=0
sa=0 sb=0 sd=0
model=pfet_03v3
spiceprefix=X}
C {lab_pin.sym} -60 -250 0 1 {name=p49 sig_type=std_logic lab=vdd_cmp}
C {lab_pin.sym} -60 -190 0 1 {name=p50 sig_type=std_logic lab=o1}
C {lab_pin.sym} -100 -220 0 0 {name=p51 sig_type=std_logic lab=clk}
C {lab_pin.sym} -60 -220 0 1 {name=p52 sig_type=std_logic lab=vdd_cmp}
C {symbols/pfet_03v3.sym} 160 -220 0 0 {name=mp2
L='CMP_LS'
W='CMP_WS'
nf=1
m=1
ad='CMP_WS*0.18u'
as='CMP_WS*0.18u'
pd='2*(CMP_WS+0.18u)'
ps='2*(CMP_WS+0.18u)'
nrd=0
nrs=0
sa=0 sb=0 sd=0
model=pfet_03v3
spiceprefix=X}
C {lab_pin.sym} 180 -250 0 1 {name=p53 sig_type=std_logic lab=vdd_cmp}
C {lab_pin.sym} 180 -190 0 1 {name=p54 sig_type=std_logic lab=o2}
C {lab_pin.sym} 140 -220 0 0 {name=p55 sig_type=std_logic lab=clk}
C {lab_pin.sym} 180 -220 0 1 {name=p56 sig_type=std_logic lab=vdd_cmp}
C {cmp_inv.sym} 340 -240 0 0 {name=Xic
WN='CMP_WI'
WP='2*CMP_WI'}
C {lab_pin.sym} 260 -260 0 0 {name=p57 sig_type=std_logic lab=clk}
C {lab_pin.sym} 420 -260 0 1 {name=p58 sig_type=std_logic lab=clkb}
C {lab_pin.sym} 320 -320 3 0 {name=p59 sig_type=std_logic lab=vdd_cmp}
C {lab_pin.sym} 360 -160 1 0 {name=p60 sig_type=std_logic lab=vss}
C {cmp_inv.sym} 340 -120 0 0 {name=Xb1
WN='CMP_WI'
WP='2*CMP_WI'}
C {lab_pin.sym} 260 -140 0 0 {name=p61 sig_type=std_logic lab=o1}
C {lab_pin.sym} 420 -140 0 1 {name=p62 sig_type=std_logic lab=b1}
C {lab_pin.sym} 320 -200 3 0 {name=p63 sig_type=std_logic lab=vdd_cmp}
C {lab_pin.sym} 360 -40 1 0 {name=p64 sig_type=std_logic lab=vss}
C {cmp_inv.sym} 560 -120 0 0 {name=Xb2
WN='CMP_WB'
WP='2*CMP_WB'}
C {lab_pin.sym} 480 -140 0 0 {name=p65 sig_type=std_logic lab=b1}
C {lab_pin.sym} 640 -140 0 1 {name=p66 sig_type=std_logic lab=outp}
C {lab_pin.sym} 540 -200 3 0 {name=p67 sig_type=std_logic lab=vdd_cmp}
C {lab_pin.sym} 580 -40 1 0 {name=p68 sig_type=std_logic lab=vss}
C {cmp_inv.sym} 340 0 0 0 {name=Xb3
WN='CMP_WI'
WP='2*CMP_WI'}
C {lab_pin.sym} 260 -20 0 0 {name=p69 sig_type=std_logic lab=o2}
C {lab_pin.sym} 420 -20 0 1 {name=p70 sig_type=std_logic lab=b2}
C {lab_pin.sym} 320 -80 3 0 {name=p71 sig_type=std_logic lab=vdd_cmp}
C {lab_pin.sym} 360 80 1 0 {name=p72 sig_type=std_logic lab=vss}
C {cmp_inv.sym} 560 0 0 0 {name=Xb4
WN='CMP_WB'
WP='2*CMP_WB'}
C {lab_pin.sym} 480 -20 0 0 {name=p73 sig_type=std_logic lab=b2}
C {lab_pin.sym} 640 -20 0 1 {name=p74 sig_type=std_logic lab=outn}
C {lab_pin.sym} 540 -80 3 0 {name=p75 sig_type=std_logic lab=vdd_cmp}
C {lab_pin.sym} 580 80 1 0 {name=p76 sig_type=std_logic lab=vss}
C {ipin.sym} -700 -300 0 0 {name=io77 lab=inp}
C {ipin.sym} -700 -260 0 0 {name=io78 lab=inn}
C {ipin.sym} -700 -220 0 0 {name=io79 lab=clk}
C {opin.sym} 700 -180 0 1 {name=io80 lab=outp}
C {opin.sym} 700 -140 0 1 {name=io81 lab=outn}
C {iopin.sym} -700 -100 0 0 {name=io82 lab=vdd_cmp}
C {iopin.sym} -700 -60 0 0 {name=io83 lab=vss}
T {D1 dynamic comparator (PMOS-input double-tail, cell cmp_p; generated by scripts/gen_cmp_sch.py).  Sizes = spice/comparator_params.spice.  The trnoise injection sources of the hand netlist are simulation-only and not drawn.} -700 -360 0 0 0.3 0.3 {}
