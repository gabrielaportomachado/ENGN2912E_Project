v {xschem version=3.4.7 file_version=1.2}
G {}
K {}
V {}
S {}
E {}
N -50 -60 -50 -30 {lab=in}
N -50 -60 40 -60 {lab=in}
N 40 -60 130 -60 {lab=in}
N 130 -60 130 -30 {lab=in}
N -50 30 -50 60 {lab=out}
N -50 60 40 60 {lab=out}
N 40 60 130 60 {lab=out}
N 130 30 130 60 {lab=out}
N -120 -0 -90 0 {lab=cbar}
N 170 0 200 0 {lab=c}
N -50 -0 -30 -0 {lab=VDD}
N -30 -20 -30 -0 {lab=VDD}
N 90 0 130 -0 {lab=VSS}
N 90 0 90 30 {lab=VSS}
C {symbols/pfet_05v0.sym} -70 0 0 0 {name=M1
L=0.6u
W=1.22u
nf=1
m=1
ad="'int((nf+1)/2) * W/nf * 0.18u'"
pd="'2*int((nf+1)/2) * (W/nf + 0.18u)'"
as="'int((nf+2)/2) * W/nf * 0.18u'"
ps="'2*int((nf+2)/2) * (W/nf + 0.18u)'"
nrd="'0.18u / W'" nrs="'0.18u / W'"
sa=0 sb=0 sd=0
model=pfet_05v0
spiceprefix=X
}
C {symbols/nfet_05v0.sym} 150 0 2 0 {name=M2
L=0.6u
W=0.565u
nf=1
m=1
ad="'int((nf+1)/2) * W/nf * 0.18u'"
pd="'2*int((nf+1)/2) * (W/nf + 0.18u)'"
as="'int((nf+2)/2) * W/nf * 0.18u'"
ps="'2*int((nf+2)/2) * (W/nf + 0.18u)'"
nrd="'0.18u / W'" nrs="'0.18u / W'"
sa=0 sb=0 sd=0
model=nfet_05v0
spiceprefix=X
}
C {ipin.sym} 40 -60 1 0 {name=p1 lab=in}
C {opin.sym} 40 60 1 0 {name=p2 lab=out}
C {ipin.sym} -120 0 0 0 {name=p3 lab=cbar}
C {ipin.sym} 200 0 2 0 {name=p4 lab=c}
C {iopin.sym} -30 -20 3 0 {name=p5 lab=VDD}
C {iopin.sym} 90 30 1 0 {name=p6 lab=VSS}
