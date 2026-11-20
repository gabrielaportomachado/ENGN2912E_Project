#!/usr/bin/env python3
"""lyrdb_count.py <dir or .lyrdb files...>: violation count per rule of KLayout report databases (the official gf180mcu DRC writes one .lyrdb per table).
Prints `<rule> <count>` for every rule with violations, then `TOTAL <n> violations in <k> rules, <m> rules checked, <f> files`.  Exit code 0 always (the caller decides)."""
import sys, os, glob, re
files = []
for a in sys.argv[1:]:
    files += sorted(glob.glob(os.path.join(a, '*.lyrdb'))) if os.path.isdir(a) else [a]
cnt, cats = {}, set()
for f in files:
    txt = open(f, errors='replace').read()
    cats |= set(re.findall(r'<category>\s*<name>([^<]+)</name>', txt))
    for m in re.finditer(r'<item>.*?<category>\'?([^<\']+)\'?</category>', txt, flags=re.S):
        cnt[m.group(1)] = cnt.get(m.group(1), 0) + 1
for k in sorted(cnt):
    print('%-28s %d' % (k, cnt[k]))
print('TOTAL %d violations in %d rules, %d rules checked, %d files' % (sum(cnt.values()), len(cnt), len(cats), len(files)))
