"""Download the newest firmware of every TECHART product in the official list into ./others/."""

import urllib.request
from pathlib import Path

lines = Path("../TECHART_LST.official.txt").read_text(encoding="utf-8").splitlines()
out = Path("others")
out.mkdir(exist_ok=True)
seen = set()
for line in lines:
    parts = line.split(";")
    if len(parts) < 6:
        continue
    name, ver, url = parts[0].replace("TECHART ", ""), parts[3].replace("VER ", ""), parts[5]
    if name in seen and name != "TZM-01":
        continue
    seen.add(name)
    dst = out / f"{name}_{ver}.bin"
    if not dst.exists():
        with urllib.request.urlopen(url, timeout=60) as r:
            dst.write_bytes(r.read())
    print(f"{dst.name:28s} {dst.stat().st_size}")
