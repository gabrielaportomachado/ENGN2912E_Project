v {xschem version=3.4.8RC file_version=1.3}
G {}
K {}
V {}
S {}
F {}
E {}
N -285 -80 -285 -30 {lab=VDD}
N -285 30 -285 70 {lab=GND}
N -185 -80 -185 -30 {lab=cnode}
N -185 30 -185 70 {lab=GND}
N -85 -80 -85 -30 {lab=cbarnode}
N -85 30 -85 70 {lab=GND}
N 15 -80 15 -30 {lab=innode}
N 15 30 15 70 {lab=GND}
N 115 -80 115 -30 {lab=biasnode}
N 115 30 115 70 {lab=GND}
N 210 190 230 190 {lab=innode}
N 310 190 330 190 {lab=outnode}
N 260 210 260 250 {lab=cnode}
N 260 130 260 160 {lab=cbarnode}
N 330 190 370 190 {lab=outnode}
C {vsource.sym} -285 0 0 0 {name=V_vdd value=5 savecurrent=false}
C {gnd.sym} -285 70 0 0 {name=l1 lab=GND}
C {lab_wire.sym} -285 -70 3 0 {name=p1 sig_type=std_logic lab=VDD}
C {vsource.sym} -185 0 0 0 {name=V_c value=0 savecurrent=false}
C {gnd.sym} -185 70 0 0 {name=l2 lab=GND}
C {lab_wire.sym} -185 -70 3 0 {name=p2 sig_type=std_logic lab=cnode}
C {vsource.sym} -85 0 0 0 {name=V_cbar value=5 savecurrent=false}
C {gnd.sym} -85 70 0 0 {name=l3 lab=GND}
C {lab_wire.sym} -85 -70 3 0 {name=p3 sig_type=std_logic lab=cbarnode}
C {vsource.sym} 15 0 0 0 {name=V_in value=0 savecurrent=true}
C {gnd.sym} 15 70 0 0 {name=l4 lab=GND}
C {lab_wire.sym} 15 -70 3 0 {name=p4 sig_type=std_logic lab=innode}
C {vsource.sym} 115 0 0 0 {name=V_bias value=2.5 savecurrent=false}
C {gnd.sym} 115 70 0 0 {name=l5 lab=GND}
C {lab_wire.sym} 115 -70 3 0 {name=p5 sig_type=std_logic lab=biasnode}
C {lab_wire.sym} 210 190 0 0 {name=p6 sig_type=std_logic lab=innode}
C {lab_wire.sym} 370 190 0 0 {name=p7 sig_type=std_logic lab=outnode}
C {lab_wire.sym} 260 250 1 0 {name=p8 sig_type=std_logic lab=cnode}
C {lab_wire.sym} 260 130 0 0 {name=p9 sig_type=std_logic lab=cbarnode}
C {res.sym} 400 200 0 0 {name=R_bias
value=100Meg
footprint=1206
device=resistor
m=1}
C {lab_wire.sym} 400 170 3 0 {name=p10 sig_type=std_logic lab=outnode}
C {lab_wire.sym} 400 230 1 0 {name=p11 sig_type=std_logic lab=biasnode}
C {devices/code_shown.sym} -200 500 0 0 {name=MODELS only_toplevel=true
format="tcleval( @value )"
value="
.include $::180MCU_MODELS/design.ngspice
.lib $::180MCU_MODELS/sm141064.ngspice typical
"}
C {code_shown.sym} 200 500 0 0 {name=s1 only_toplevel=false value="
.control
save all
* ===== Test 1: off-state leakage (c=0, cbar=VDD -> switch open) =====
dc V_in 0 5.0 0.05
let ileak = abs(i(V_in))
let imax  = vecmax(ileak)
echo TGATE off-state max leakage = $&imax A
if $&imax > 1e-9
  echo FAIL_TGATE_HIZ leakage exceeds 1nA threshold
else
  echo PASS_TGATE_HIZ leakage below 1nA
end
write tb_tgate_hiz.raw
* ===== Test 2: on-resistance (c=VDD, cbar=0 -> switch closed) =====
* out is held at V_bias through R_bias (reduced to 1 ohm). For each level vcm,
* V_in is stepped from vcm-10mV to vcm+10mV, so RON = 20mV / change in i(V_in) - 1 ohm.
* Pass/fail only covers the signal range 0..ron_vmax. ron_max is a placeholder: set it from your spec.
alter V_c dc=5
alter V_cbar dc=0
alter R_bias 1
set ron_max = 10e3
set ron_vmax = 0.5
set ron_fail = 0
foreach vcm 0 0.05 0.1 0.2 0.3 0.5 1 2 2.5 3 4 5
  alter V_bias dc=$vcm
  let lo = $vcm - 0.01
  let hi = $vcm + 0.01
  dc V_in $&lo $&hi 0.02
  let ron = 0.02 / abs(i(V_in)[1] - i(V_in)[0]) - 1
  echo TGATE on-resistance at $vcm V = $&ron ohm
  if $vcm <= $ron_vmax
    if ron > $ron_max
      set ron_fail = 1
    end
  end
end
if $ron_fail > 0
  echo FAIL_TGATE_RON above $ron_max ohm somewhere in 0 to $ron_vmax V
else
  echo PASS_TGATE_RON below $ron_max ohm over 0 to $ron_vmax V
end
.endc
"}
C {TGATE.sym} 300 200 0 0 {name=x1}
C {lab_pin.sym} 310 160 0 1 {name=p12 sig_type=std_logic lab=VDD}
C {lab_pin.sym} 310 210 0 1 {name=p13 sig_type=std_logic lab=GND}
