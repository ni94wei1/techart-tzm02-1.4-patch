"""Compare TZM-02 1.4.0 against every other TECHART firmware.

Code is position-dependent, so compare sets of 8-byte instruction windows with
pc-relative/branch noise reduced: hash 2-byte-aligned 8-byte chunks.
Also report vector-table shape and reset-handler prologue for each image."""

import struct
from pathlib import Path


def grams(d, n=8):
    return {d[i:i + n] for i in range(0, len(d) - n, 2) if d[i:i + n].count(0) < n // 2}


def shape(d):
    vec = [struct.unpack_from("<I", d, 4 * i)[0] for i in range(48)]
    present = "".join("." if v == 0 else "x" for v in vec[16:44])
    return f"sp=0x{vec[0]:x} irq[{present}]"


target = Path("../TZM-02-VER-1-4-0.bin").read_bytes()
tg = grams(target)
files = sorted(Path("others").glob("*.bin")) + [Path("../TZM-02-VER-1-2-0.bin")]
print(f"{'TZM-02_1.4.0 (target)':28s} {len(target):6d}  {shape(target)}")
rows = []
for f in files:
    d = f.read_bytes()
    g = grams(d)
    jacc = len(tg & g) / len(tg | g)
    cover = len(tg & g) / len(tg)
    rows.append((cover, f.name, len(d), jacc, shape(d)))
for cover, name, size, jacc, sh in sorted(rows, reverse=True):
    print(f"{name:28s} {size:6d}  cover={cover:5.1%} jaccard={jacc:5.1%}  {sh}")
