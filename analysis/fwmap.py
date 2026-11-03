"""Recursive-descent function map for TZM-02 firmware images (SAMD21, Thumb, base 0x5000)."""

import struct
import sys
from collections import defaultdict

from capstone import CS_ARCH_ARM, CS_MODE_THUMB, Cs
from capstone.arm import ARM_OP_IMM

BASE = 0x5000

PERIPH = [
    (0x40000000, 0x400, "PAC0"), (0x40000400, 0x400, "PM"), (0x40000800, 0x400, "SYSCTRL"),
    (0x40000C00, 0x400, "GCLK"), (0x40001000, 0x400, "WDT"), (0x40001400, 0x400, "RTC"),
    (0x40001800, 0x400, "EIC"), (0x41000000, 0x400, "PAC1"), (0x41002000, 0x2000, "DSU"),
    (0x41004000, 0x400, "NVMCTRL"), (0x41004400, 0x400, "PORT"), (0x41004800, 0x400, "DMAC"),
    (0x41005000, 0x1000, "USB"), (0x41006000, 0x1000, "MTB"), (0x41007000, 0x1000, "SBMATRIX"),
    (0x42000000, 0x400, "PAC2"), (0x42000400, 0x400, "EVSYS"),
    (0x42000800, 0x400, "SERCOM0"), (0x42000C00, 0x400, "SERCOM1"), (0x42001000, 0x400, "SERCOM2"),
    (0x42001400, 0x400, "SERCOM3"), (0x42001800, 0x400, "SERCOM4"), (0x42001C00, 0x400, "SERCOM5"),
    (0x42002000, 0x400, "TCC0"), (0x42002400, 0x400, "TCC1"), (0x42002800, 0x400, "TCC2"),
    (0x42002C00, 0x400, "TC3"), (0x42003000, 0x400, "TC4"), (0x42003400, 0x400, "TC5"),
    (0x42003800, 0x400, "TC6"), (0x42003C00, 0x400, "TC7"), (0x42004000, 0x400, "ADC"),
    (0x42004400, 0x400, "AC"), (0x42004800, 0x400, "DAC"), (0x42004C00, 0x400, "PTC"),
    (0x60000000, 0x400, "PORT_IOBUS"), (0xE000E000, 0x1000, "SCS"),
]


def periph_name(v):
    for base, size, name in PERIPH:
        if base <= v < base + size:
            return name if v == base else f"{name}+0x{v - base:x}"
    return None


class Image:
    def __init__(self, path):
        self.d = open(path, "rb").read()
        self.end = BASE + len(self.d)
        self.md = Cs(CS_ARCH_ARM, CS_MODE_THUMB)
        self.md.detail = True
        self.funcs = {}
        self.insns = {}

    def word(self, a):
        o = a - BASE
        return struct.unpack_from("<I", self.d, o)[0] if 0 <= o <= len(self.d) - 4 else None

    def in_code(self, a):
        return BASE <= a < self.end

    def decode_at(self, a):
        if a in self.insns:
            return self.insns[a]
        o = a - BASE
        for ins in self.md.disasm(self.d[o:o + 4], a, count=1):
            self.insns[a] = ins
            return ins
        self.insns[a] = None
        return None

    def analyze(self):
        vec = [self.word(BASE + 4 * i) for i in range(48)]
        roots = {v & ~1 for v in vec[1:] if v and v & 1 and self.in_code(v)}
        todo = list(roots)
        while todo:
            f = todo.pop()
            if f in self.funcs or not self.in_code(f):
                continue
            info = self.walk(f)
            self.funcs[f] = info
            todo.extend(c for c in info["calls"] if c not in self.funcs)
        return vec

    def walk(self, start):
        seen, blocks = set(), [start]
        calls, periph, ram, consts, lits = set(), defaultdict(int), set(), set(), set()
        while blocks:
            a = blocks.pop()
            while a not in seen and self.in_code(a):
                seen.add(a)
                ins = self.decode_at(a)
                if ins is None:
                    break
                m, ops = ins.mnemonic, ins.op_str
                nxt = a + ins.size
                if m == "ldr" and "[pc" in ops:
                    imm = int(ops.split("#")[-1].rstrip("]"), 0) if "#" in ops else 0
                    la = ((a + 4) & ~3) + imm
                    lits.add(la)
                    val = self.word(la)
                    if val is not None:
                        p = periph_name(val)
                        if p:
                            periph[p] += 1
                        elif 0x20000000 <= val < 0x20008000:
                            ram.add(val)
                        elif val & 1 and self.in_code(val):
                            calls.add(val & ~1)
                        else:
                            consts.add(val)
                for op in ins.operands:
                    if op.type == ARM_OP_IMM and m not in ("b", "bl") and not m.startswith("b"):
                        if op.imm > 8:
                            consts.add(op.imm)
                if m == "bl":
                    calls.add(ins.operands[0].imm)
                elif m == "b" or (m.startswith("b") and m[1:] in (
                        "eq", "ne", "cs", "hs", "cc", "lo", "mi", "pl", "vs", "vc",
                        "hi", "ls", "ge", "lt", "gt", "le")):
                    t = ins.operands[0].imm
                    blocks.append(t)
                    if m == "b":
                        break
                elif m in ("cbz", "cbnz"):
                    blocks.append(ins.operands[1].imm)
                elif m == "bx" or (m == "pop" and "pc" in ops) or (m.startswith("ldr") and ops.startswith("pc")):
                    break
                elif m == "mov" and ops.startswith("pc"):
                    break
                a = nxt
        return {"start": start, "size": (max(seen) - start + 2) if seen else 0, "addrs": seen,
                "calls": calls, "periph": dict(periph), "ram": ram, "consts": consts, "lits": lits}

    def callers(self):
        r = defaultdict(set)
        for f, info in self.funcs.items():
            for c in info["calls"]:
                r[c].add(f)
        return r


def dump(img, out, names=None):
    callers = img.callers()
    with open(out, "w", encoding="utf-8") as fh:
        for f in sorted(img.funcs):
            info = img.funcs[f]
            fh.write(f"FUNC 0x{f:x} size~{info['size']} callers={sorted(hex(c) for c in callers[f])}\n")
            if info["periph"]:
                fh.write(f"  periph: {info['periph']}\n")
            if info["calls"]:
                fh.write(f"  calls: {sorted(hex(c) for c in info['calls'])}\n")
            if info["ram"]:
                fh.write(f"  ram: {sorted(hex(c) for c in info['ram'])}\n")
            big = sorted(c for c in info["consts"] if c > 0xff)
            if big:
                fh.write(f"  consts: {[hex(c) for c in big][:20]}\n")


def disasm_func(img, f, out=sys.stdout):
    info = img.funcs.get(f) or img.walk(f)
    for a in sorted(info["addrs"]):
        ins = img.decode_at(a)
        if ins is None:
            continue
        extra = ""
        if ins.mnemonic == "ldr" and "[pc" in ins.op_str:
            imm = int(ins.op_str.split("#")[-1].rstrip("]"), 0) if "#" in ins.op_str else 0
            val = img.word(((a + 4) & ~3) + imm)
            if val is not None:
                p = periph_name(val)
                extra = f"   ; =0x{val:x}" + (f" [{p}]" if p else "")
        out.write(f"  0x{a:x}: {ins.mnemonic:7s} {ins.op_str}{extra}\n")


if __name__ == "__main__":
    for v in ["1-3-0", "1-4-0"]:
        img = Image(f"../TZM-02-VER-{v}.bin")
        img.analyze()
        dump(img, f"map_{v}.txt")
        print(v, "functions:", len(img.funcs))
