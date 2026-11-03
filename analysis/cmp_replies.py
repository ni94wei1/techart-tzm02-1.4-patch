"""Compare camera reply templates of 1.4.0 (flash constants) with 1.3.0 (.data, located by searching the 1.3 image)."""

from pathlib import Path

B = 0x5000
d13 = Path("../TZM-02-VER-1-3-0.bin").read_bytes()
d14 = Path("../TZM-02-VER-1-4-0.bin").read_bytes()

# (description, 1.4 source address, length, 1.3 RAM source)
PAIRS = [
    ("cmd 0x02", 0x8a48, 8, 0x2000007c),
    ("cmd 0x07 first", 0x8a58, 14, 0x2000008c),
    ("cmd 0x07 again", 0x8a68, 14, 0x2000009c),
    ("cmd 0x0c / 0x09 / 0x19 (mode!=0x10 0x08)", 0x8af0, 6, 0x200000bc),
    ("0x08/0x09 6|e mode!=0x10", 0x8ae8, 6, 0x200000b4),
    ("0x08/0x09 6|e mode==0x10", 0x8af0, 6, 0x200000ac),
    ("cmd 0x00 ff", 0x8ae0, 6, 0x20000074),
    ("cmd 0x03 b4=3", 0x8a50, 6, 0x20000084),
    ("0x0001 b4=3", 0x8a40, 6, None),
    ("0x0001 b4 50/51/53/54/70/c3/0", 0x8a38, 6, 0x200000c8),
    ("0x0001 b4=54 (1.3)", 0x8a38, 6, 0x200000d0),
    ("0x0004", 0x8b88, 10, 0x200000d8),
    ("0x7001 b4=40", 0x8b94, 12, 0x200000e4),
    ("0x7001 e7/ea/d3/d1 / 0x7501", 0x8d14, 8, 0x2000006c),
    ("0x7401", 0x8a80, 8, 0x200002b0),
    ("0x7e01 b4=6 / 0x1301 b5=6", 0x8ba0, 14, 0x200001fc),
    ("0x7e01 b4=2", 0x8bb0, 16, 0x2000020c),
    ("0x7e01 b4=3", 0x8bc0, 18, 0x2000021c),
    ("0x1001", 0x8b54, 24, 0x2000024c),
    ("0x1001 b5=d", 0x8b6c, 28, 0x20000230),
    ("0x1101", 0x8b00, 74, 0x20000264),
    ("0x2001", 0x8bd4, 258, 0x200000f0),
    ("0xf301", 0x8ad8, 8, 0x200002b8),
    ("0x1501 <10", 0x8af8, 6, 0x200001f4),
    ("0x7601 <=4", 0x8a88, 12, 0x200002c8),
    ("0x7601 <=7", 0x8a94, 12, 0x200002d4),
    ("0x7601 <=a", 0x8aa0, 12, 0x200002e0),
    ("0x7601 b", 0x8aac, 12, 0x200002ec),
    ("0x0028 (1.4 only)", 0x8cdc, 46, None),
    ("0x5101 done", 0x8b50, 4, None),
]


def find_all(hay, needle):
    out, i = [], hay.find(needle)
    while i >= 0:
        out.append(i)
        i = hay.find(needle, i + 1)
    return out


for name, a14, n, r13 in PAIRS:
    t14 = d14[a14 - B:a14 - B + n]
    hits = find_all(d13, t14)
    tag = "SAME bytes found in 1.3" if hits else "DIFFERENT / not in 1.3"
    print(f"{name:42s} 1.4@0x{a14:x}: {t14.hex(' ')}")
    print(f"{'':42s} -> {tag} {[hex(h + B) for h in hits][:3]}")
