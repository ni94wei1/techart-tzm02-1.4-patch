"""Build two video-AF test variants on top of TZM-02-VER-1-4-0-retract.bin.

1.4.0 changed several camera-visible replies compared with 1.3.0:
  * 0x1001 lens info: byte 5 = 0x40 (1.3.0: 0x30)
  * 0x1101 lens name: "TZM-02" / "TECHART" (1.3.0: "Mount Adapter FTZ" / "NIKON")
  * 0x0028 query: answered with 46 zero bytes (1.3.0: not answered)
  * 0x0001 sub 0x03 / 0x54: replies "55 00 05" / "55 00 04" (1.3.0: swapped)
and it narrowed which focus commands move the motor:
  * cmd 0x19 never moves (1.3.0: same handler as 0x09)
  * cmd 0x09 with byte1 not 6/0x0e never moves (1.3.0: same as 0x0c)
  * 0x6bf8 only acts in mode 0x10 with a 16-byte frame or mode 0x12 with an 18-byte
    frame (1.3.0: mode 0x10 -> absolute target from bytes 5..6, any other mode ->
    drive toward the farther end)

Variant A (vidA): restore the 1.3.0 replies.
Variant B (published as "1.4.1"): A + restore the 1.3.0 focus-command routing via a wrapper around 0x6bf8.
"""

import hashlib
import struct
import sys
from pathlib import Path

from capstone import CS_ARCH_ARM, CS_MODE_THUMB, Cs

BASE = 0x5000
SRC = Path("../TZM-02-VER-1-4-0-retract.bin")
SRC_SHA = "9ab990de61014ad08cfd4d623cd4209d89eeadca23461ae1dae8b2b95ebaa14e"
REF13 = Path("../TZM-02-VER-1-3-0.bin")
OUT_A = Path("../TZM-02-VER-1-4-0-vidA.bin")
OUT_B = Path("../TZM-02-VER-1-4-1-unofficial.bin")

INFO24, INFO28 = 0x8B54, 0x8B6C      # 0x1001 replies (24 / 28 bytes)
NAME, NAME13 = 0x8B00, 0x9A68        # 0x1101 reply (74 bytes) in 1.4 / 1.3
B_0028 = 0x701E                      # "b 0x7210" (send 0x0028 reply)
RET = 0x7070                         # dispatcher epilogue (default reply stays set)
SUB3_BEQ, SUB54_BEQ = 0x7380, 0x739A
REPLY04, REPLY05 = 0x73A8, 0x73B2    # paths sending "55 00 04 .." / "55 00 05 .."

H19 = 0x7206                         # cmd 0x19 handler
H09, H09_OTHER = 0x71C8, 0x71FC      # cmd 0x09 handler / its byte1-not-6/e branch
H0C = 0x70B4                         # cmd 0x0c handler
FOCUS_CALLS = (0x70C4, 0x71B2, 0x71EC)
FOCUS = 0x6BF8
SET_TARGET = 0x6BE0
MODE = 0x20000A4A
POS = 0x20000B7E                     # current position, quarter steps
MID = 0xD00                          # (32 + 1632) / 2 * 4
POS_MIN, POS_MAX = 32, 1632


def h(v):
    return struct.pack("<H", v)


def bl(src, dst):
    off = (dst - (src + 4)) >> 1
    assert -(1 << 21) <= off < (1 << 21)
    off &= (1 << 22) - 1
    return struct.pack("<HH", 0xF000 | (off >> 11), 0xF800 | (off & 0x7FF))


def b(src, dst):
    off = (dst - (src + 4)) >> 1
    assert -1024 <= off < 1024
    return h(0xE000 | (off & 0x7FF))


def bcond(cond, src, dst):
    off = (dst - (src + 4)) >> 1
    assert -128 <= off < 128
    return h(0xD000 | (cond << 8) | (off & 0xFF))


def put(data, addr, new, old):
    o = addr - BASE
    assert bytes(data[o:o + len(old)]) == old, f"unexpected bytes at 0x{addr:x}"
    data[o:o + len(new)] = new


def fix_sum(data, addr, n):
    o = addr - BASE
    data[o + n - 1] = (-sum(data[o:o + n - 1])) & 0xFF


def variant_a(data):
    d13 = REF13.read_bytes()
    for addr, n in ((INFO24, 24), (INFO28, 28)):
        put(data, addr + 5, b"\x30", b"\x40")
        fix_sum(data, addr, n)
    name13 = d13[NAME13 - BASE:NAME13 - BASE + 74]
    assert name13[1:18] == b"Mount Adapter FTZ" and sum(name13) & 0xFF == 0
    put(data, NAME, name13, b"\x55TZM-02")
    put(data, B_0028, b(B_0028, RET), b(B_0028, 0x7210))
    put(data, SUB3_BEQ, bcond(0x0, SUB3_BEQ, REPLY04), bcond(0x0, SUB3_BEQ, REPLY05))
    put(data, SUB54_BEQ, bcond(0x0, SUB54_BEQ, REPLY05), bcond(0x0, SUB54_BEQ, REPLY04))


def variant_b(data):
    f = BASE + len(data)
    assert f % 4 == 0
    code = bytearray()

    def at():
        return f + len(code)

    labels, fix = {}, []

    def br(kind, label):
        fix.append((at(), kind, label))
        code.extend(b"\0\0" if kind != "bl" else b"\0\0\0\0")

    code += h(0xB510)                       # push {r4, lr}
    br("ldr3", "lit_mode")                  # ldr r3, =MODE
    code += h(0x781B)                       # ldrb r3, [r3]
    code += h(0x2B10)                       # cmp r3, #0x10
    br("bne", "not10")
    code += h(0x2910)                       # cmp r1, #0x10
    br("beq", "tail")
    code += h(0x7943)                       # ldrb r3, [r0, #5]
    code += h(0x7980)                       # ldrb r0, [r0, #6]
    code += h(0x0200)                       # lsls r0, r0, #8
    code += h(0x4318)                       # orrs r0, r3
    code += h(0xB200)                       # sxth r0, r0
    br("b", "move")
    labels["not10"] = at()
    code += h(0x2B12)                       # cmp r3, #0x12
    br("bne", "sweep")
    code += h(0x2912)                       # cmp r1, #0x12
    br("beq", "tail")
    labels["sweep"] = at()
    br("ldr3", "lit_pos")                   # ldr r3, =POS
    code += h(0x881B)                       # ldrh r3, [r3]
    code += h(0x2000 | (MID >> 4))          # movs r0, #0xd0
    code += h(0x0100)                       # lsls r0, r0, #4
    code += h(0x2400 | POS_MIN)             # movs r4, #32
    code += h(0x4283)                       # cmp r3, r0
    br("bhi", "set")
    code += h(0x2400 | (POS_MAX >> 3))      # movs r4, #0xcc
    code += h(0x00E4)                       # lsls r4, r4, #3
    labels["set"] = at()
    code += h(0x0020)                       # movs r0, r4
    labels["move"] = at()
    code += h(0x0011)                       # movs r1, r2
    fix.append((at(), "blx", SET_TARGET)); code += b"\0\0\0\0"
    code += h(0xBD10)                       # pop {r4, pc}
    labels["tail"] = at()
    fix.append((at(), "blx", FOCUS)); code += b"\0\0\0\0"
    code += h(0xBD10)                       # pop {r4, pc}
    while at() % 4:
        code += h(0x46C0)
    labels["lit_mode"] = at(); code += struct.pack("<I", MODE)
    labels["lit_pos"] = at(); code += struct.pack("<I", POS)

    conds = {"beq": 0x0, "bne": 0x1, "bhi": 0x8}
    for src, kind, tgt in fix:
        o = src - f
        if kind == "blx":
            code[o:o + 4] = bl(src, tgt)
        elif kind == "ldr3":
            lit = labels[tgt]
            code[o:o + 2] = h(0x4B00 | ((lit - ((src + 4) & ~3)) // 4))
        elif kind == "b":
            code[o:o + 2] = b(src, labels[tgt])
        else:
            code[o:o + 2] = bcond(conds[kind], src, labels[tgt])
    data += code

    for site in FOCUS_CALLS:
        put(data, site, bl(site, f), bl(site, FOCUS))
    put(data, H19, b(H19, H09), h(0x2106))
    put(data, H09_OTHER, b(H09_OTHER, H0C), h(0x2106))
    return f, code


def show(data, start, n):
    md = Cs(CS_ARCH_ARM, CS_MODE_THUMB)
    for ins in md.disasm(bytes(data[start - BASE:start - BASE + n]), start):
        print(f"  0x{ins.address:x}: {ins.mnemonic} {ins.op_str}")


def main():
    src = SRC.read_bytes()
    if hashlib.sha256(src).hexdigest() != SRC_SHA:
        raise SystemExit("source firmware hash mismatch")

    a = bytearray(src)
    variant_a(a)
    OUT_A.write_bytes(a)
    print(f"wrote {OUT_A} size {len(a)} sha256 {hashlib.sha256(a).hexdigest()}")

    bb = bytearray(a)
    f, code = variant_b(bb)
    OUT_B.write_bytes(bb)
    print(f"wrote {OUT_B} size {len(bb)} sha256 {hashlib.sha256(bb).hexdigest()}")

    print("--- wrapper")
    show(bb, f, len(code) - 8)
    for site in (B_0028, SUB3_BEQ, SUB54_BEQ, H19, H09_OTHER) + FOCUS_CALLS:
        print(f"--- 0x{site:x}")
        show(bb, site, 4)


if __name__ == "__main__":
    sys.exit(main())
