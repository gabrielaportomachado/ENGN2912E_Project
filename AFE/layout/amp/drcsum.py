"""drcsum.py (L2a): print the violations of a flow.py drc run (rule, location) grouped by rule.  usage: python3 AFE/layout/amp/drcsum.py <drc_dir> [max per rule]"""
import sys, glob, re
import xml.etree.ElementTree as ET

d = sys.argv[1]
mx = int(sys.argv[2]) if len(sys.argv) > 2 else 6
seen = {}
for f in glob.glob(d + '/*.lyrdb'):
    for ev, el in ET.iterparse(f, events=('end',)):
        if el.tag != 'item':
            continue
        cat = el.find('category').text.strip("'")
        vals = [x.text for x in el.find('values').iter('value')] if el.find('values') is not None else []
        seen.setdefault(cat, []).append(' | '.join(vals))
        el.clear()
for cat, v in sorted(seen.items()):
    print('%-18s %6d' % (cat, len(v)))
    for t in v[:mx]:
        print('     ', t[:200])
