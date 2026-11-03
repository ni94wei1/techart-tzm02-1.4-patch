from collections import defaultdict

from fwmap import Image

imgs = {}
for v in ["1-3-0", "1-4-0"]:
    img = Image(f"../TZM-02-VER-{v}.bin")
    img.analyze()
    imgs[v] = img

for v, img in imgs.items():
    by = defaultdict(list)
    for f, info in img.funcs.items():
        for p in info["periph"]:
            by[p.split("+")[0]].append(f)
    print(f"===== {v}")
    for p in sorted(by):
        print(f"  {p:10s} {len(by[p]):3d} funcs: {', '.join(hex(f) for f in sorted(set(by[p])))[:150]}")
