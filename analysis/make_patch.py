"""Build TZM-02 1.4.0 with the 1.3.0 power-off retract restored.

1.3.0, on message 0x5101 (sent by the camera while shutting down), counts polls:
replies "busy" (55 81 00 2a) for the first 50, starts moving to min+32 (= 64) on
the 2nd, then replies "done" (55 01 00 aa). 1.4.0 calls a stub at 0x6b70 that
always returns 0, so it replies "done" at once and never retracts.

Patch:
  * 0x7330  bl 0x6b70  ->  bl poll5101 (new code appended after the image)
  * .data copy end 0x20000064 -> 0x20000068, with 4 zero bytes appended, so the
    poll counter at 0x20000064 (unused RAM) is zeroed on every boot
"""

import hashlib
import struct
import sys
from pathlib import Path

from capstone import CS_ARCH_ARM, CS_MODE_THUMB, Cs

BASE = 0x5000
SRC = Path("../TZM-02-VER-1-4-0.bin")
DST = Path("../TZM-02-VER-1-4-0-retract.bin")
SRC_SHA = "f3580a0ffe627f4422710dc6655be52f513a78a6ba5ff3d14806f3d3b0521f9f"

CALL_SITE = 0x7330
STUB = 0x6B70
SET_TARGET = 0x6BE0          # queue motor target: r0 = position, r1 = mode flag
DATA_END_LITERAL = 0x5198    # literal used by Reset_Handler's .data copy loop
COUNTER = 0x20000064
RETRACT_POS = 64             # 1.3.0: min (32) + 32
BUSY_POLLS = 49              # 1.3.0: busy while count <= 0x31


def bl(src, dst):
    off = (dst - (src + 4)) >> 1
    assert -(1 << 21) <= off < (1 << 21)
    off &= (1 << 22) - 1
    hi = 0xF000 | (off >> 11)
    lo = 0xF800 | (off & 0x7FF)
    return struct.pack("<HH", hi, lo)


def bcond(cond, src, dst):
    off = (dst - (src + 4)) >> 1
    assert -128 <= off < 128
    return struct.pack("<H", 0xD000 | (cond << 8) | (off & 0xFF))


def h(v):
    return struct.pack("<H", v)


def main():
    data = bytearray(SRC.read_bytes())
    if hashlib.sha256(data).hexdigest() != SRC_SHA:
        raise SystemExit("source firmware hash mismatch")
    end = BASE + len(data)
    assert end == 0x8DE0

    # sanity: the call site really calls the stub, and the stub is "movs r0,#0; bx lr"
    assert bytes(data[CALL_SITE - BASE:CALL_SITE - BASE + 4]) == bl(CALL_SITE, STUB)
    assert bytes(data[STUB - BASE:STUB - BASE + 4]) == h(0x2000) + h(0x4770)
    assert struct.unpack_from("<I", data, DATA_END_LITERAL - BASE)[0] == 0x20000064

    # 1) extend .data by one zeroed word to hold the counter
    struct.pack_into("<I", data, DATA_END_LITERAL - BASE, COUNTER + 4)
    data += b"\x00\x00\x00\x00"

    # 2) new function at 0x8de4
    f = BASE + len(data)
    assert f == 0x8DE4
    code = bytearray()

    def at():
        return f + len(code)

    code += h(0xB500)                                   # push {lr}
    ldr_at = at(); code += h(0)                         # ldr r3, =COUNTER (fixed below)
    code += h(0x7818)                                   # ldrb r0, [r3]
    code += h(0x2800 | BUSY_POLLS)                      # cmp r0, #49
    bhi_at = at(); code += h(0)                         # bhi done
    code += h(0x3001)                                   # adds r0, #1
    code += h(0x7018)                                   # strb r0, [r3]
    code += h(0x2802)                                   # cmp r0, #2
    bne_at = at(); code += h(0)                         # bne busy
    code += h(0x2000 | RETRACT_POS)                     # movs r0, #64
    code += h(0x2100)                                   # movs r1, #0
    code += bl(at(), SET_TARGET)                        # bl set_target
    busy = at()
    code += h(0x2001)                                   # movs r0, #1
    code += h(0xBD00)                                   # pop {pc}
    done = at()
    code += h(0x2000)                                   # movs r0, #0
    code += h(0xBD00)                                   # pop {pc}
    while at() % 4:
        code += h(0x46C0)                               # nop
    lit = at()
    code += struct.pack("<I", COUNTER)

    struct.pack_into("<H", code, ldr_at - f, 0x4B00 | ((lit - ((ldr_at + 4) & ~3)) // 4))
    code[bhi_at - f:bhi_at - f + 2] = bcond(0x8, bhi_at, done)
    code[bne_at - f:bne_at - f + 2] = bcond(0x1, bne_at, busy)
    data += code

    # 3) redirect the call
    data[CALL_SITE - BASE:CALL_SITE - BASE + 4] = bl(CALL_SITE, f)

    DST.write_bytes(data)
    print(f"wrote {DST} size {len(data)} sha256 {hashlib.sha256(data).hexdigest()}")

    md = Cs(CS_ARCH_ARM, CS_MODE_THUMB)
    print("--- call site")
    for ins in md.disasm(bytes(data[CALL_SITE - BASE - 4:CALL_SITE - BASE + 8]), CALL_SITE - 4):
        print(f"  0x{ins.address:x}: {ins.mnemonic} {ins.op_str}")
    print("--- new function")
    for ins in md.disasm(bytes(code[:lit - f]), f):
        print(f"  0x{ins.address:x}: {ins.mnemonic} {ins.op_str}")
    print(f"  0x{lit:x}: .word 0x{struct.unpack_from('<I', code, lit - f)[0]:x}")


if __name__ == "__main__":
    sys.exit(main())
