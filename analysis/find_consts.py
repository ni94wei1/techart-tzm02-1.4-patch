"""Usage: python find_consts.py <ver> <const_hex> [...] - rank functions by how many of the immediates they use."""

import sys

from fwmap import Image

ver = sys.argv[1]
wanted = {int(c, 16) for c in sys.argv[2:]}
img = Image(f"../TZM-02-VER-{ver}.bin")
img.analyze()
callers = img.callers()
rows = []
for f, info in img.funcs.items():
    imms = set()
    for a in info["addrs"]:
        ins = img.decode_at(a)
        if ins is not None and ins.mnemonic == "cmp" and "#" in ins.op_str:
            imms.add(int(ins.op_str.split("#")[-1], 0))
    hit = wanted & imms
    if hit:
        rows.append((len(hit), f, sorted(hit), info["size"]))
for n, f, hit, size in sorted(rows, reverse=True)[:15]:
    print(f"0x{f:x} size~{size} callers={[hex(c) for c in sorted(callers[f])]} matches={[hex(h) for h in hit]}")
