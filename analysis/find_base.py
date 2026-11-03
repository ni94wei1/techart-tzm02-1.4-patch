import re
import struct

for v in ["1-2-0", "1-3-0", "1-4-0"]:
    d = open(f"TZM-02-VER-{v}.bin", "rb").read()
    reset = struct.unpack_from("<I", d, 4)[0] & ~1
    print(f"===== {v} reset vector=0x{reset:x} len=0x{len(d):x}")
    # Keil/CMSIS startup: LDR R0,=SystemInit; BLX R0; LDR R0,=__main; BX R0
    for m in re.finditer(rb"[\x00-\xff]\x48\x80\x47[\x00-\xff]\x48\x00\x47", d):
        off = m.start()
        base = reset - off
        print(f"  startup pattern at file offset 0x{off:x} -> base 0x{base:x}")
    # GCC startup often: ldr sp,=_estack  (0d 48 85 46 = ldr r0,..; mov sp,r0)
    for m in re.finditer(rb"[\x00-\xff]\x48\x85\x46", d):
        off = m.start()
        print(f"  'ldr r0; mov sp,r0' at file offset 0x{off:x} -> base 0x{reset - off:x}")
