import struct

BASE = 0x4000

for v in ["1-2-0", "1-3-0", "1-4-0"]:
    d = open(f"TZM-02-VER-{v}.bin", "rb").read()
    end = BASE + len(d)
    print(f"===== {v} image 0x{BASE:x}..0x{end:x}")
    for i in range(0, len(d) - 11, 4):
        a, b, c = struct.unpack_from("<III", d, i)
        if 0x20000000 <= b < 0x20004000 and c < 0x4000 and BASE <= a <= end + 0x100:
            tag = "OK" if a + c <= end or c == 0 else "PAST-END?"
            print(f"  @0x{i:x}: load=0x{a:x} exec=0x{b:x} size=0x{c:x} next=0x{struct.unpack_from('<I', d, i + 12)[0]:x} {tag}")

    refs = [struct.unpack_from("<I", d, i)[0] for i in range(0, len(d) - 3, 4)]
    beyond = sorted({r for r in refs if end <= r < end + 0x4000 and r & 0xFFFF0000 == 0})
    print(f"  words pointing just past image end: {[hex(x) for x in beyond[:20]]}")
