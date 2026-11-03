"""Find the camera-command dispatcher (function using literals 0x7e01/0x5101) in sibling firmwares
and dump it to sib_<name>.txt so their 0x08/0x09/0x0c/0x19 handling can be compared."""

import struct
from pathlib import Path

import fwmap
from fwmap import Image, disasm_func


def try_base(d):
    rst = struct.unpack_from("<I", d, 4)[0]
    for base in (0x5000, 0x08005000, 0x08004000, 0x08003000, 0x4000, 0x6000):
        if rst & 1 and base <= rst < base + len(d):
            return base
    return None


for f in sorted(Path("others").glob("TZ*.bin")):
    d = f.read_bytes()
    base = try_base(d)
    fwmap.BASE = base
    img = Image(str(f))
    img.analyze()
    hits = []
    for fa, info in img.funcs.items():
        vals = {img.word(la) for la in info["lits"]}
        if 0x7E01 in vals or 0x5101 in vals or 0x7E01 in info["consts"]:
            hits.append(fa)
    out = Path(f"sib_{f.stem}.txt")
    with out.open("w", encoding="utf-8") as fh:
        for fa in sorted(hits):
            fh.write(f"===== FUNC 0x{fa:x}\n")
            disasm_func(img, fa, fh)
    print(f"{f.name}: base=0x{base:x} dispatch funcs={[hex(h) for h in sorted(hits)]}")
