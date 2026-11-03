import struct
import sys

from capstone import CS_ARCH_ARM, CS_MODE_THUMB, Cs

BASE = 0x4000
md = Cs(CS_ARCH_ARM, CS_MODE_THUMB)


def lit(d, addr):
    off = addr - BASE
    return struct.unpack_from("<I", d, off)[0] if 0 <= off < len(d) - 3 else None


def dump(d, start, count, label):
    print(f"--- {label} @0x{start:x}")
    off = start - BASE
    for ins in md.disasm(d[off:off + count * 4], start):
        extra = ""
        if ins.mnemonic.startswith("ldr") and "[pc" in ins.op_str:
            imm = int(ins.op_str.split("#")[-1].rstrip("]"), 0) if "#" in ins.op_str else 0
            a = ((ins.address + 4) & ~3) + imm
            val = lit(d, a)
            extra = f"   ; =0x{val:x}" if val is not None else f"   ; =<0x{a:x} OUTSIDE IMAGE>"
        print(f"  0x{ins.address:x}: {ins.mnemonic:8s} {ins.op_str}{extra}")
        count -= 1
        if count <= 0:
            break


for v in sys.argv[1:] or ["1-3-0", "1-4-0"]:
    d = open(f"TZM-02-VER-{v}.bin", "rb").read()
    print(f"===== {v}  image 0x{BASE:x}..0x{BASE + len(d):x}")
    reset = lit(d, BASE + 4) & ~1
    dump(d, reset, 12, "Reset_Handler")
