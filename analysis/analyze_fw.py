import struct
import sys

versions = sys.argv[1:] or ["1-2-0", "1-3-0", "1-4-0"]

for v in versions:
    d = open(f"TZM-02-VER-{v}.bin", "rb").read()
    w = [struct.unpack_from("<I", d, i)[0] for i in range(0, len(d) - 3, 4)]

    n = 1
    for x in w[1:200]:
        if x == 0 or (x & 1 and x < 0x10000):
            n += 1
        else:
            break
    vt = [x for x in w[1:n] if x]
    lo, hi = min(vt), max(vt)
    print(f"===== {v} len=0x{len(d):x} vector_entries={n} handlers=0x{lo:x}..0x{hi:x} sp=0x{w[0]:x}")

    cands = [b for b in range(0, 0x10000, 0x400) if all(b <= x - 1 < b + len(d) for x in vt)]
    print("  candidate bases:", [hex(c) for c in cands])

    for i in range(0, len(d) - 15, 4):
        a, b, c, f = struct.unpack_from("<IIII", d, i)
        if 0x20000000 <= b < 0x20004000 and c < 0x4000 and f & 1 and f < 0x10000 and 0x1000 <= a < 0x10000:
            print(f"  region @0x{i:x}: load=0x{a:x} exec=0x{b:x} size=0x{c:x} fn=0x{f:x}")
