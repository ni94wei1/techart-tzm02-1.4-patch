"""Usage: python xref_ram.py <ver> <ram_hex> [...]  - functions whose literal pool references the RAM address."""

import sys

from fwmap import Image

ver = sys.argv[1]
img = Image(f"../TZM-02-VER-{ver}.bin")
img.analyze()
callers = img.callers()
for a in sys.argv[2:]:
    addr = int(a, 16)
    hits = sorted(f for f, info in img.funcs.items() if addr in info["ram"])
    print(f"0x{addr:x}: " + ", ".join(f"0x{f:x}(<-{','.join(hex(c) for c in sorted(callers[f])) or 'isr/ptr'})" for f in hits))
