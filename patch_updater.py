"""Make TECHART_Updater_1.4.exe: a copy of the official updater whose firmware
list URL points at the local server started by run_updater_1.4.py."""

import shutil
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
src = Path(sys.argv[1]) if len(sys.argv) > 1 else Path.home() / "Downloads/TECHART_Update-win/TECHART_Updater(USB).exe"
dst = HERE / "TECHART_Updater_1.4.exe"

old = "http://www.techart-logic.com/product/TECHART_LST.txt"
new = "http://127.0.0.1:47123/product/TECHART_LST-v1400.txt"
assert len(old) == len(new), (len(old), len(new))

data = src.read_bytes()
o, n = old.encode("utf-16le"), new.encode("utf-16le")
if data.count(o) != 1:
    raise SystemExit(f"在 {src} 中找到 {data.count(o)} 处清单地址，预期 1 处")
shutil.copyfile(src, dst)
dst.write_bytes(data.replace(o, n))
print(f"已生成 {dst}")
