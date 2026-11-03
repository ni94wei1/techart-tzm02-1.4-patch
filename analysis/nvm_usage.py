import collections
import struct

from capstone import CS_ARCH_ARM, CS_MODE_THUMB, Cs

BASE = 0x5000
md = Cs(CS_ARCH_ARM, CS_MODE_THUMB)
md.skipdata = True

# SAMD21 NVMCTRL CTRLA command = 0xA5 << 8 | cmd
NVM_CMDS = {0xA502: "ER (erase row)", 0xA504: "WP (write page)", 0xA544: "PBC (page buffer clear)",
            0xA505: "EAR", 0xA506: "WAP"}
EMPTY_VECTORS = [27, 28, 37, 38]  # SERCOM4, SERCOM5, TC6, TC7 (vector index incl. SP)

for v in ["1-2-0", "1-3-0", "1-4-0"]:
    d = open(f"../TZM-02-VER-{v}.bin", "rb").read()
    vec = [struct.unpack_from("<I", d, 4 * i)[0] for i in range(44)]
    print(f"===== {v}")
    print("  SERCOM4/SERCOM5/TC6/TC7 vectors:", ["0" if vec[i] == 0 else "set" for i in EMPTY_VECTORS])

    words = collections.Counter(struct.unpack_from("<I", d, i)[0] for i in range(0, len(d) - 3, 4))
    print("  NVMCTRL base 0x41004000 literal count:", words[0x41004000])
    found = []
    for ins in md.disasm(d, BASE):
        if ins.mnemonic in ("ldr", "movw", "movs", "adds") and "#" in ins.op_str:
            pass
        if ins.mnemonic == "ldr" and "[pc" in ins.op_str:
            imm = int(ins.op_str.split("#")[-1].rstrip("]"), 0)
            a = ((ins.address + 4) & ~3) + imm - BASE
            if 0 <= a <= len(d) - 4:
                val = struct.unpack_from("<I", d, a)[0]
                if val in NVM_CMDS:
                    found.append(f"0x{ins.address:x}:{NVM_CMDS[val]}")
    lits = {k: words[k] for k in NVM_CMDS if words[k]}
    print("  NVM command literals in image:", {NVM_CMDS[k]: n for k, n in lits.items()})
    print("  loaded by code at:", found[:10])
