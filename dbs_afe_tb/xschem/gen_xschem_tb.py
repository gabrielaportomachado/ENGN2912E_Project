#!/usr/bin/env python3
"""Generate an xschem + ngspice testbench for dbs_afe_top from the real netlist.

    python3 gen_xschem_tb.py --netlist /path/to/AFE/layout/lvs/dbs_afe_top.spice [--out build] [--pdk-root $PDK_ROOT]

The port ORDER is read from the `.subckt dbs_afe_top ...` line of the netlist, so the symbol pins and the X-instance
always match it. Port names are mapped by name: E[0]/E0 -> net e0, IPG*, REC*, REF, CS, SCLK, DIN, RSTN, DOUT, VDD, VSS.

Writes into --out:
    dbs_afe_top.sym            xschem symbol (pins in .subckt order)
    tb_dbs_afe_top.sch         xschem testbench (open with xschem, netlist with 'n', simulate with 's')
    tb_dbs_afe_top.spice       the same testbench as a stand-alone deck:  cd <out>; ngspice -b tb_dbs_afe_top.spice
    stim.inc                   neural signal + SPI waveforms (PWL), included by both
    stim_frames.json           frame schedule, read by decode_dout.py

Time is SHORTENED against the host rules (5 s bias wait skipped, RST_AMP held 5 ms instead of >= 100 ms):
a transistor-level run cannot cover seconds. Results are only meaningful once the bias has started (see README).
"""
import argparse
import json
import os
import re
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "python"))
import afe_model as am  # noqa: E402
import spi  # noqa: E402

V = 3.3
T_SCLK = 500e-9            # 2 MHz
FRAME_PERIOD = 250e-6      # 4 kS/s
VALID_NETS = {f"{p}{i}" for p in ("e", "ipg", "rec") for i in range(4)} | {"ref", "cs", "sclk", "din", "rstn", "dout", "vdd", "vss"}


# ----------------------------------------------------------------------------------------------------------- netlist
def read_ports(path, name="dbs_afe_top"):
    if not os.path.isfile(path):
        d = os.path.dirname(path) or "."
        near = sorted(os.listdir(d))[:20] if os.path.isdir(d) else []
        raise SystemExit(f"netlist not found: {path}" + (f"\nfiles in {d}: {', '.join(near)}" if near else f"\n(directory {d} does not exist)"))
    text = re.sub(r"\n\+", " ", open(path).read())
    for line in text.splitlines():
        t = line.split()
        if len(t) >= 2 and t[0].lower() == ".subckt" and t[1].lower() == name.lower():
            return t[1], [p for p in t[2:] if "=" not in p]
    raise SystemExit(f"no '.subckt {name}' found in {path}")


ALIASES = {"dout_out": "dout", "dout_o": "dout", "doutpad": "dout", "miso": "dout", "dout_pad": "dout",
           "csn": "cs", "cs_n": "cs", "sclk_in": "sclk", "din_in": "din", "mosi": "din", "rst_n": "rstn",
           "gnd": "vss", "vssa": "vss", "vssd": "vss", "avss": "vss", "dvss": "vss",
           "vdda": "vdd", "vddd": "vdd", "avdd": "vdd", "dvdd": "vdd", "vdd3v3": "vdd"}
USER_MAP = {}      # from --map PORT=net
UNKNOWN = []


def net_of(port):
    n = re.sub(r"[\[\]<>]", "", port).lower()
    n = USER_MAP.get(n, USER_MAP.get(port.lower(), n))
    n = ALIASES.get(n, n)
    if n in ("0", "gnd"):
        return "0"
    if n not in VALID_NETS:
        if port not in UNKNOWN:
            UNKNOWN.append(port)
        return n                       # left as its own net: no source, no load
    return "0" if n == "vss" else n


# ----------------------------------------------------------------------------------------------------------- stimulus
class Pwl:
    def __init__(self, v0):
        self.p, self.v = [(0.0, v0)], v0

    def set(self, t, v, tr=1e-9):
        if v == self.v:
            return
        t = max(t, self.p[-1][0] + 1e-12)
        self.p.append((t, self.v))
        self.p.append((t + tr, v))
        self.v = v

    def card(self, name, node):
        pts = [f"{t:.10g} {v:.6g}" for t, v in self.p]
        lines = [f"V{name} {node} 0 pwl("] + ["+ " + " ".join(pts[i:i + 6]) for i in range(0, len(pts), 6)] + ["+ )"]
        return "\n".join(lines)


def build_stimulus(tstop, rst_hold, t_start=50e-6, seed=1, rate_hz=40.0, tone_hz=200.0, tone_amp=0.45e-3):
    cs, sclk, din, rstn = Pwl(0.0), Pwl(0.0), Pwl(0.0), Pwl(0.0)
    frames = []

    def frame(t, cfg):
        frames.append(dict(t=t, cfg=cfg))
        cs.set(t, 0.0)
        bits = spi.words_to_bits([cfg, 0, 0, 0, 0])
        tr0 = t + 150e-9                                       # CS falls >= 100 ns before the first SCLK edge
        for k in range(80):
            tr = tr0 + k * T_SCLK
            din.set(tr - T_SCLK / 2 if k else t + 50e-9, V * bits[k])
            sclk.set(tr, V)
            sclk.set(tr + T_SCLK / 2, 0.0)
        tend = tr0 + 79 * T_SCLK + T_SCLK
        cs.set(tend, V)
        din.set(tend, 0.0)
        return tend + T_SCLK

    cs.set(2e-6, V)                                            # CS high once VDD is up
    rstn.set(20e-6, V)                                         # RSTN released while CS is high
    t = frame(t_start, 0x0000)                                 # pure read: status must be 0xA000
    t = frame(t + 20e-6, spi.config_word(1, 1, 0, 0))          # RST_AMP = 1 (level held in the chip)
    t = frame(t + rst_hold, spi.config_word(1, 0, 0, 0))       # RST_AMP = 0
    t = frame(t + 20e-6, spi.config_word(1, 0, 1, 0xF))        # record on all four channels
    t_rec = frames[-1]["t"]
    k = 1
    while t_rec + k * FRAME_PERIOD < tstop - 60e-6:
        frame(t_rec + k * FRAME_PERIOD, 0x0000)
        k += 1
    # electrode signals: all within 0..VDD, centred on REF = 1.65 V
    x, truth = am.neural_signal(tstop, seed=seed, rate_hz=rate_hz)
    n = len(x)
    ts = np.arange(n) / am.FS_HI
    e0 = Pwl(1.65)
    e0.p = [(float(a), float(1.65 + b)) for a, b in zip(ts, x)]
    cards = [cs.card("cs", "cs"), sclk.card("sclk", "sclk"), din.card("din", "din"), rstn.card("rstn", "rstn"), e0.card("e0", "e0"),
             f"Ve1 e1 0 sin(1.65 {tone_amp:g} {tone_hz:g} 0 0)", "Ve2 e2 0 1.65", "Ve3 e3 0 1.65", "Vref ref 0 1.65"]
    info = dict(frames=frames, t_rec=t_rec, tone_hz=tone_hz, tone_amp=tone_amp, tstop=tstop, spike_times_ch0=[float(a) for a in truth])
    return cards, info, dict(cs=cs, sclk=sclk, din=din, rstn=rstn)


# ----------------------------------------------------------------------------------------------------------- spice deck
EXTRA_INCLUDES = []
LIB_SECTIONS = ["typical"]


def spice_body(subckt, ports, tstop, pdk_root, netlist_path, with_pdk):
    inst = f"Xdut {' '.join(net_of(p) for p in ports)} {subckt}"
    lines = ["* dbs_afe_top testbench (generated by gen_xschem_tb.py)"]
    if with_pdk:
        lines += [f".lib {pdk_root}/gf180mcuD/libs.tech/ngspice/sm141064.ngspice {sec}" for sec in LIB_SECTIONS]
        lines += [f".include {pdk_root}/gf180mcuD/libs.tech/ngspice/design.ngspice"]
    lines += [f".include {os.path.abspath(f)}" for f in EXTRA_INCLUDES]
    lines += [f".include {netlist_path}", ".include stim.inc"]
    return lines, inst


def control(tstop):
    return "\n".join([
        ".options abstol=1e-12 reltol=1e-3 method=gear",
        ".temp 27",
        ".save v(cs) v(sclk) v(din) v(dout) v(e0) v(e1) v(vdd)",     # keep only what decode_dout.py needs (full chip = huge)
        f".tran 50n {tstop:g} 0 200n",
        ".control",
        "set num_threads=1",
        "set wr_singlescale",
        "set wr_vecnames",
        "run",
        "wrdata tb_out.txt v(cs) v(sclk) v(din) v(dout) v(e0) v(e1) v(vdd)",
        ".endc",
    ])


LOADS = ["Cdout dout 0 15p",
         "Ripg0 ipg0 ref 1g", "Ripg1 ipg1 ref 1g", "Ripg2 ipg2 ref 1g", "Ripg3 ipg3 ref 1g",
         "Rrec0 rec0 0 1e13", "Rrec1 rec1 0 1e13", "Rrec2 rec2 0 1e13", "Rrec3 rec3 0 1e13"]
VDD_CARD = "Vdd vdd 0 pwl(0 0 2u 3.3)"


# ----------------------------------------------------------------------------------------------------------- xschem
def esc(s):
    return s.replace("\\", "\\\\").replace("{", "\\{").replace("}", "\\}")


def write_sym(path, ports):
    left = [p for p in ports if net_of(p) not in ("dout", "vdd", "vss")]
    right = [p for p in ports if net_of(p) == "dout"]
    top = [p for p in ports if net_of(p) == "vdd"]
    bot = [p for p in ports if net_of(p) == "vss"]
    h = max(len(left), 1) * 20 + 40
    yt, yb = -h // 2, h // 2
    out = ["v {xschem version=3.4.5 file_version=1.2}", "G {}", "K {type=subcircuit", 'format="@name @pinlist @symname"',
           'template="name=x1"', "}", "V {}", "S {}", "E {}",
           f"L 4 -130 {yt} 130 {yt} {{}}", f"L 4 130 {yt} 130 {yb} {{}}", f"L 4 130 {yb} -130 {yb} {{}}", f"L 4 -130 {yb} -130 {yt} {{}}",
           f"T {{@symname}} -120 {yt + 8} 0 0 0.3 0.3 {{}}", f"T {{@name}} 20 {yb - 24} 0 0 0.3 0.3 {{}}"]
    pins = {}
    for i, p in enumerate(left):
        y = yt + 30 + 20 * i
        pins[p] = (-150, y)
        out += [f"L 4 -150 {y} -130 {y} {{}}", f"B 5 -152.5 {y - 2.5} -147.5 {y + 2.5} {{name={p} dir=in}}", f"T {{{p}}} -125 {y - 4} 0 0 0.2 0.2 {{}}"]
    for p in right:
        pins[p] = (150, 0)
        out += [f"L 4 130 0 150 0 {{}}", f"B 5 147.5 -2.5 152.5 2.5 {{name={p} dir=out}}", f"T {{{p}}} 125 -4 0 1 0.2 0.2 {{}}"]
    for p in top:
        pins[p] = (0, yt - 20)
        out += [f"L 4 0 {yt - 20} 0 {yt} {{}}", f"B 5 -2.5 {yt - 22.5} 2.5 {yt - 17.5} {{name={p} dir=inout}}"]
    for p in bot:
        pins[p] = (0, yb + 20)
        out += [f"L 4 0 {yb} 0 {yb + 20} {{}}", f"B 5 -2.5 {yb + 17.5} 2.5 {yb + 22.5} {{name={p} dir=inout}}"]
    # xschem builds @pinlist in the order of the B 5 lines: keep the .subckt order
    order = {p: i for i, p in enumerate(ports)}
    pin_lines = sorted([l for l in out if l.startswith("B 5")], key=lambda l: order[re.search(r"name=(\S+)", l).group(1)])
    rest = [l for l in out if not l.startswith("B 5")]
    open(path, "w").write("\n".join(rest + pin_lines) + "\n")
    return pins


def write_sch(path, ports, pins, code_blocks):
    out = ["v {xschem version=3.4.5 file_version=1.2}", "G {}", "K {}", "V {}", "S {}", "E {}",
           "C {dbs_afe_top.sym} 0 0 0 0 {name=Xdut}"]
    n = 0
    for p in ports:
        x, y = pins[p]
        net = net_of(p)
        n += 1
        if net == "0":
            out.append(f"C {{devices/gnd.sym}} {x} {y} 0 0 {{name=l{n} lab=GND}}")
            continue
        dx, dy = (-40, 0) if x < 0 else (40, 0) if x > 0 else (0, -40)
        x2, y2 = x + dx, y + dy
        out.append(f"N {x} {y} {x2} {y2} {{lab={net}}}")
        out.append(f"C {{devices/lab_pin.sym}} {x2} {y2} 0 {0 if x <= 0 else 1} {{name=p{n} sig_type=std_logic lab={net}}}")
    out += ["C {devices/vsource.sym} -400 -300 0 0 {name=Vdd value=\"pwl(0 0 2u 3.3)\" savecurrent=false}",
            "C {devices/lab_pin.sym} -400 -330 0 0 {name=pvdd sig_type=std_logic lab=vdd}",
            "C {devices/gnd.sym} -400 -270 0 0 {name=lg0 lab=GND}"]
    for i, (nm, txt) in enumerate(code_blocks):
        out.append(f"C {{devices/code_shown.sym}} {-700 + 350 * i} 400 0 0 {{name={nm} only_toplevel=false value=\"{esc(txt)}\"}}")
    out.append("T {Sources E0-E3, REF, SPI pins and the electrode PWL are in stim.inc (included below). Check with decode_dout.py after the run.} -700 300 0 0 0.3 0.3 {}")
    open(path, "w").write("\n".join(out) + "\n")


# ----------------------------------------------------------------------------------------------------------- main
def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--netlist", required=True)
    ap.add_argument("--out", default="build")
    ap.add_argument("--pdk-root", default=os.environ.get("PDK_ROOT", "$PDK_ROOT"))
    ap.add_argument("--no-pdk", action="store_true", help="do not add .lib/.include of the PDK (netlist already has models)")
    ap.add_argument("--map", action="append", default=[], metavar="PORT=NET",
                    help="map a netlist port to a testbench net (e0-3, ipg0-3, rec0-3, ref, cs, sclk, din, rstn, dout, vdd, vss/0); repeatable")
    ap.add_argument("--include", action="append", default=[], metavar="FILE",
                    help="extra SPICE file to .include BEFORE the DUT netlist (e.g. afe_dig netlist, std-cell library); repeatable")
    ap.add_argument("--lib-section", action="append", default=[], metavar="SEC",
                    help="section of sm141064.ngspice to load (default: typical). Repeat for more, e.g. --lib-section typical --lib-section res_typical")
    ap.add_argument("--tstop", type=float, default=30e-3)
    ap.add_argument("--rst-hold", type=float, default=5e-3, help="RST_AMP hold time (host rule: >= 100 ms, too long to simulate)")
    a = ap.parse_args(argv)
    os.makedirs(a.out, exist_ok=True)
    for m in a.map:
        k, _, v = m.partition("=")
        USER_MAP[k.strip().lower()] = v.strip().lower()
    EXTRA_INCLUDES.extend(a.include)
    if a.lib_section:
        LIB_SECTIONS[:] = a.lib_section
    subckt, ports = read_ports(a.netlist)
    print(f"{subckt} ports (netlist name -> testbench net):")
    for p in ports:
        print(f"  {p:14s} -> {net_of(p)}")
    if UNKNOWN:
        print("\nWARNING: unrecognised ports, left on their own undriven nets: " + ", ".join(UNKNOWN) +
              "\n  each gets a 1 Gohm pull-down so nothing floats (inputs among them read 0); override with e.g.  --map " + UNKNOWN[0] + "=vdd")
        for p in UNKNOWN:
            n = net_of(p)
            LOADS.append(f"Rfl_{re.sub(r'[^a-z0-9]', '_', n)} {n} 0 1g")
    cards, info, _ = build_stimulus(a.tstop, a.rst_hold)
    open(os.path.join(a.out, "stim.inc"), "w").write("* generated stimulus\n" + "\n".join(cards) + "\n")
    json.dump(info, open(os.path.join(a.out, "stim_frames.json"), "w"), indent=1)
    head, inst = spice_body(subckt, ports, a.tstop, a.pdk_root, os.path.abspath(a.netlist), not a.no_pdk)
    deck = head + [VDD_CARD, inst] + LOADS + [control(a.tstop), ".end"]
    open(os.path.join(a.out, "tb_dbs_afe_top.spice"), "w").write("\n".join(deck) + "\n")
    pins = write_sym(os.path.join(a.out, "dbs_afe_top.sym"), ports)
    models = "\n".join(h for h in head[1:] if not h.startswith(".include stim"))
    write_sch(os.path.join(a.out, "tb_dbs_afe_top.sch"), ports, pins,
              [("MODELS", models), ("STIM", ".include stim.inc\n" + "\n".join(LOADS)), ("SIM", control(a.tstop))])
    print(f"wrote {a.out}/ (sym, sch, spice, stim.inc, stim_frames.json); {len(info['frames'])} SPI frames")


if __name__ == "__main__":
    main()