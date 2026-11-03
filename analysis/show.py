"""Usage: python show.py <ver> <func_addr_hex> [...]   - disassemble functions
          python show.py <ver> --periph NAME          - list per-function register offsets for a peripheral"""

import sys

from fwmap import Image

ver = sys.argv[1]
img = Image(f"../TZM-02-VER-{ver}.bin")
img.analyze()
callers = img.callers()

if sys.argv[2] == "--periph":
    name = sys.argv[3]
    for f in sorted(img.funcs):
        hits = {p: n for p, n in img.funcs[f]["periph"].items() if p.split("+")[0] == name}
        if hits:
            print(f"0x{f:x} (callers {[hex(c) for c in sorted(callers[f])]}): {hits}")
else:
    for a in sys.argv[2:]:
        f = int(a, 16)
        info = img.funcs.get(f)
        print(f"===== {ver} FUNC 0x{f:x} callers={[hex(c) for c in sorted(callers[f])]}"
              + ("" if info else "  (not a discovered function start)"))
        from fwmap import disasm_func
        disasm_func(img, f)
