"""asciimap.py: ASCII occupancy map of the block bounding boxes of an amp_ch build (reads amp_ch.build.json; a debugging aid for the packing).
usage: python3 AFE/layout/amp/asciimap.py <amp_ch.build.json> [row_um=3] [col_um=2]"""
import json
import sys

d = json.load(open(sys.argv[1]))
R = float(sys.argv[2]) if len(sys.argv) > 2 else 3.0
Cc = float(sys.argv[3]) if len(sys.argv) > 3 else 2.0
bb = d['bboxes']
sym = {'cc1': 'c', 'mir': 'M', 'xms': 'x', 'fol': 'f', 's2p': 'p', 'sink1': 'k', 'xm6': '6', 'ota_p': 'O', 's2tail': 't', 'cf1': '1', 'cf1p': '1', 'sp': 'P', 'or2': 'o', 'pr1': 'r', 'pr2': 'r',
       's2pair': 'S', 'sn': 'N', 'cin2': 'I', 'cf2': 'F', 'pr3': 'r', 'cc2': 'C', 'ct': 'T', 'sn_a': 'N', 'sp_a': 'P', 'sn_os': 'n', 'sp_os': 'q'}
H = d['bbox'][3]
W = d['bbox'][2]
cx, cy = d['cin']['X0'], d['cin']['Y0']
P, T = d['cin']['P'], d['cin']['T']
y = H
while y >= 0:
    line = ''
    x = 0.0
    while x < W + 1:
        ch = '.'
        for n, b in bb.items():
            if n == 'cin':
                if cx <= x <= cx + P + T and cy <= y <= cy + P + T:
                    ch = '#'
                elif b[0] <= x <= b[2] and b[1] <= y <= b[3] and ch == '.':
                    ch = ':'
                continue
            if b[0] <= x <= b[2] and b[1] <= y <= b[3]:
                ch = sym.get(n, '?')
        line += ch
        x += Cc
    print('%5.0f %s' % (y, line))
    y -= R
