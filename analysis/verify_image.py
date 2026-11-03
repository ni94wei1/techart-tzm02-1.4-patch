import struct

from capstone import CS_ARCH_ARM, CS_MODE_THUMB, Cs

BASE = 0x5000
md = Cs(CS_ARCH_ARM, CS_MODE_THUMB)


def word(d, addr):
    off = addr - BASE
    return struct.unpack_from("<I", d, off)[0] if 0 <= off <= len(d) - 4 else None


for v in ["1-2-0", "1-3-0", "1-4-0"]:
    d = open(f"TZM-02-VER-{v}.bin", "rb").read()
    end = BASE + len(d)
    reset = word(d, BASE + 4) & ~1
    print(f"===== {v} image 0x{BASE:x}..0x{end:x}")
    lits = []
    off = reset - BASE
    for ins in md.disasm(d[off:off + 0xA0], reset):
        extra = ""
        if ins.mnemonic == "ldr" and "[pc" in ins.op_str:
            imm = int(ins.op_str.split("#")[-1].rstrip("]"), 0)
            a = ((ins.address + 4) & ~3) + imm
            val = word(d, a)
            lits.append(val)
            extra = f"   ; =0x{val:x}" if val is not None else "   ; =<OUTSIDE IMAGE>"
        print(f"  0x{ins.address:x}: {ins.mnemonic:6s} {ins.op_str}{extra}")
        if ins.mnemonic in ("bx", "pop") or (ins.mnemonic == "b" and ins.address > reset + 0x60):
            break
    flash = sorted({x for x in lits if x and BASE <= x < 0x10000})
    print("  flash literals:", [hex(x) for x in flash], " (image end 0x%x)" % end)
    print("  max code pointer in vectors: 0x%x" % max(word(d, BASE + i) or 0 for i in range(4, 0xC0, 4)))
