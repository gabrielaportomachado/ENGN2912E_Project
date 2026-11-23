#!/usr/bin/env python3
"""Convert a gate-level Verilog netlist (afe_dig.pnl.v) into a SPICE subcircuit that instantiates std cells.

    python3 pnl2spice.py ../AFE/dig/final/afe_dig.pnl.v \
        --lib $PDK_ROOT/gf180mcuD/libs.ref/gf180mcu_fd_sc_mcu7t5v0/spice/gf180mcu_fd_sc_mcu7t5v0.spice \
        --order-from ../AFE/layout/lvs/dbs_afe_top.spice --out build/afe_dig.spice

* Cell pin order comes from the `.subckt` lines of --lib, so connections are made by pin NAME.
* The port order of the generated `.subckt afe_dig` is taken from the line in --order-from that instantiates `afe_dig`
  (net names there are matched to the Verilog port names, case-insensitive). Supplies: net `vdd` -> VDD, net `0` -> VSS.
  If names do not match the script stops and lists both sides; `--order header` uses the Verilog header order instead
  (only do that if you know it equals the order in which dbs_afe_top.spice calls afe_dig).
* Handles: bus ports, escaped identifiers, `assign` between nets, constants 1'b0/1'b1, multi-line instances, comments.
"""
import argparse
import re
import sys

SUPPLY = {"vdd", "vss", "vnw", "vpw"}


def strip_comments(t):
    t = re.sub(r"/\*.*?\*/", " ", t, flags=re.S)
    t = re.sub(r"\(\*.*?\*\)", " ", t, flags=re.S)
    return re.sub(r"//[^\n]*", " ", t)


def norm(n):
    n = n.strip()
    if n.startswith("\\"):
        n = n[1:]
    return re.sub(r"\s+", "", n).lower()


def read_lib(path, wanted=None):
    text = re.sub(r"\n\s*\+", " ", open(path).read())
    cells = {}
    for line in text.splitlines():
        t = line.split()
        if len(t) >= 2 and t[0].lower() == ".subckt":
            cells[t[1].lower()] = [p.lower() for p in t[2:] if "=" not in p]
    return cells


def parse_verilog(path):
    stm = [s.strip() for s in strip_comments(open(path).read()).split(";")]
    mods = [s for s in stm if s.startswith("module")]
    if not mods:
        sys.exit("no module found")
    m = re.match(r"module\s+(\S+?)\s*\((.*)\)\s*$", mods[0], re.S)
    name, header = m.group(1), [norm(x) for x in m.group(2).split(",") if x.strip()]
    ports, insts, assigns = {}, [], []
    started = False
    for s in stm:
        if s.startswith("module"):
            started = True
            continue
        if not started or not s or s.startswith("endmodule"):
            continue
        k = s.split(None, 1)[0]
        if k in ("input", "output", "inout"):
            r = re.match(r"(input|output|inout)\s*(?:\[\s*(\d+)\s*:\s*(\d+)\s*\])?\s*(.*)$", s, re.S)
            hi, lo = (int(r.group(2)), int(r.group(3))) if r.group(2) else (None, None)
            for nm in r.group(4).split(","):
                nm = norm(nm)
                if not nm:
                    continue
                if hi is None:
                    ports[nm] = k
                else:
                    for b in range(hi, lo - 1, -1) if hi >= lo else range(hi, lo + 1):
                        ports[f"{nm}[{b}]"] = k
        elif k in ("wire", "tri", "supply0", "supply1", "reg"):
            continue
        elif k == "assign":
            for a in re.split(r",(?![^{]*})", s[len("assign"):]):
                l, _, r = a.partition("=")
                assigns.append((norm(l), norm(r)))
        else:
            r = re.match(r"(\S+)\s+(\S+(?:\s*\[[^\]]*\])?)\s*\((.*)\)\s*$", s, re.S)
            if not r:
                sys.exit(f"cannot parse statement: {s[:120]}")
            insts.append((r.group(1).lower(), norm(r.group(2)), parse_conns(r.group(3), s)))
    return name, header, ports, insts, assigns


def parse_conns(body, ctx):
    out, i = {}, 0
    while True:
        i = body.find(".", i)
        if i < 0:
            break
        j = body.index("(", i)
        pin = body[i + 1:j].strip().lower()
        d, k = 1, j + 1
        while d:
            d += {"(": 1, ")": -1}.get(body[k], 0)
            k += 1
        out[pin] = body[j + 1:k - 1].strip()
        i = k
    return out


def order_from_call(path, child):
    text = re.sub(r"\n\s*\+", " ", open(path).read())
    for line in text.splitlines():
        t = line.split()
        if len(t) > 2 and t[0][0] in "xX":
            tt = [x for x in t if "=" not in x]
            if tt[-1].lower() == child.lower():
                return tt[1:-1]
    sys.exit(f"no X line instantiating {child} found in {path}")


def wrap(prefix, items, width=110):
    lines, cur = [], prefix
    for it in items:
        if len(cur) + len(it) + 1 > width:
            lines.append(cur)
            cur = "+"
        cur += " " + it
    lines.append(cur)
    return lines


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("pnl")
    ap.add_argument("--lib", required=True, help="std-cell SPICE library (gf180mcu_fd_sc_mcu7t5v0.spice)")
    ap.add_argument("--order-from", help="dbs_afe_top.spice (reads the line that instantiates the module)")
    ap.add_argument("--order", choices=["call", "header"], default="call")
    ap.add_argument("--map", action="append", default=[], metavar="CALLNET=VERILOGPORT",
                    help="pair a net name in the call with a differently named Verilog port, e.g. --map DOUT_OUT=dout; repeatable")
    ap.add_argument("--out", required=True)
    a = ap.parse_args(argv)

    pmap = {}
    for m in a.map:
        k_, _, v_ = m.partition("=")
        pmap[k_.strip().lower()] = v_.strip().lower()
    cells = read_lib(a.lib)
    name, header, ports, insts, assigns = parse_verilog(a.pnl)
    sig = [p for p in ports if p not in SUPPLY]
    sig_h = [p for p in header if p not in SUPPLY]

    # port order -----------------------------------------------------------------------------------
    if a.order == "header" or not a.order_from:
        if not a.order_from and a.order == "call":
            print("note: no --order-from, using the Verilog header order (+ vdd vss at the end)", file=sys.stderr)
        expanded = []
        for h in sig_h:
            expanded += [p for p in sig if p == h or p.startswith(h + "[")] or [h]
        order = expanded + ["vdd", "vss"]
    else:
        call = order_from_call(a.order_from, name)
        order, bad = [], []
        for n in call:
            nl = n.lower()
            nl = nl.rsplit(".", 1)[-1] if "." in nl else nl
            nl = pmap.get(nl, nl)
            if nl in ("0", "gnd", "vss"):
                order.append("vss")
            elif nl == "vdd":
                order.append("vdd")
            elif nl in sig:
                order.append(nl)
            else:
                bad.append(n)
        missing = [p for p in sig if p not in order]
        if bad or missing:
            print(f"ERROR: the call of {name} in {a.order_from} does not match the ports of {a.pnl} by name.", file=sys.stderr)
            print(f"  nets in the call with no such port ({len(bad)}): {' '.join(bad)}", file=sys.stderr)
            print(f"  Verilog ports not found in the call ({len(missing)}): {' '.join(missing)}", file=sys.stderr)
            if len(bad) == 1 and len(missing) == 1:
                print(f"  if these are the same signal, rerun with:  --map {bad[0]}={missing[0]}", file=sys.stderr)
            sys.exit("fix the names with --map, or use --order header if you know the orders are the same")
        if len(order) != len(set(order)):
            sys.exit("a port appears twice in the call")

    # body ------------------------------------------------------------------------------------------
    body, used, nc, k = [], {}, 0, 0
    pw = {"vdd": "vdd", "vnw": "vdd", "vss": "vss", "vpw": "vss"}

    def net(expr):
        nonlocal k
        e = expr.strip()
        c = re.fullmatch(r"\d*'[bBhHdD]([01])", e)
        if c:
            k += 1
            tie = f"tie{k}"
            body.append(f"Vtie{k} {tie} {'vdd' if c.group(1) == '1' else 'vss'} 0")
            return tie
        if e.startswith("{"):
            sys.exit(f"concatenation in a connection is not supported: {e}")
        n = norm(e)
        return pw.get(n, n)

    for cell, inst, conns in insts:
        if cell not in cells:
            sys.exit(f"cell {cell} (instance {inst}) not found in {a.lib}")
        pins = cells[cell]
        extra = [p for p in conns if p not in pins]
        if extra:
            sys.exit(f"instance {inst}: cell {cell} has no pin(s) {extra}; its pins are {pins}")
        nets = []
        for p in pins:
            if p in conns and conns[p].strip():
                nets.append(net(conns[p]))
            elif p in pw:
                nets.append(pw[p])
            else:
                nc += 1
                nets.append(f"nc{nc}")
        base = re.sub(r"[^a-z0-9_]", "_", inst)
        used[base] = used.get(base, 0) + 1
        iname = "X" + base + (f"_{used[base]}" if used[base] > 1 else "")
        body += wrap(iname, nets + [cell])
    for i, (l, r) in enumerate(assigns):
        L, R = net(l), net(r)
        if L != R:
            body.append(f"Rassign{i} {L} {R} 1m")

    out = [f"* {name}: converted from {a.pnl} by pnl2spice.py ({len(insts)} cell instances)"]
    out += wrap(f".subckt {name}", order)
    out += body
    out.append(f".ends {name}")
    open(a.out, "w").write("\n".join(out) + "\n")
    print(f"wrote {a.out}: {len(insts)} instances, {len(order)} ports ({len(order) - 2} signals + vdd/vss), {len(assigns)} assigns, {nc} unconnected pins")


if __name__ == "__main__":
    main()