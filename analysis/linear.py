"""Usage: python linear.py <ver> <start_hex> <nbytes_hex>  - linear Thumb disassembly with literal values."""

import struct
import sys

from capstone import CS_ARCH_ARM, CS_MODE_THUMB, Cs

from fwmap import BASE, periph_name

ver, start, n = sys.argv[1], int(sys.argv[2], 16), int(sys.argv[3], 16)
d = open(f"../TZM-02-VER-{ver}.bin", "rb").read()
md = Cs(CS_ARCH_ARM, CS_MODE_THUMB)
md.skipdata = True


def word(a):
    o = a - BASE
    return struct.unpack_from("<I", d, o)[0] if 0 <= o <= len(d) - 4 else None


for ins in md.disasm(d[start - BASE:start - BASE + n], start):
    extra = ""
    if ins.mnemonic == "ldr" and "[pc" in ins.op_str:
        imm = int(ins.op_str.split("#")[-1].rstrip("]"), 0) if "#" in ins.op_str else 0
        val = word(((ins.address + 4) & ~3) + imm)
        if val is not None:
            p = periph_name(val)
            extra = f"   ; =0x{val:x}" + (f" [{p}]" if p else "")
    print(f"  0x{ins.address:x}: {ins.mnemonic:7s} {ins.op_str}{extra}")
