import collections
import struct

from capstone import CS_ARCH_ARM, CS_MODE_THUMB, Cs

md = Cs(CS_ARCH_ARM, CS_MODE_THUMB)

for v in ["1-2-0", "1-3-0", "1-4-0"]:
    d = open(f"TZM-02-VER-{v}.bin", "rb").read()
    vec = [struct.unpack_from("<I", d, i)[0] for i in range(4, 4 * 48, 4)]
    default = collections.Counter(x for x in vec if x).most_common(1)[0][0] & ~1
    reset = vec[0] & ~1
    print(f"===== {v} default_handler=0x{default:x} reset=0x{reset:x}")
    for off in range(0, len(d) - 1, 2):
        if d[off:off + 2] == b"\xfe\xe7":
            base = default - off
            if base < 0 or base % 0x100:
                continue
            roff = reset - base
            if not 0 <= roff < len(d):
                continue
            ins = list(md.disasm(d[roff:roff + 24], reset))
            text = "; ".join(f"{i.mnemonic} {i.op_str}" for i in ins[:6])
            print(f"  base 0x{base:x}: reset -> {text}")
