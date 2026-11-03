"""Run the official TECHART updater with extra TZM-02 firmware added to its list.

The patched updater fetches its firmware list from this local server instead of
www.techart-logic.com. The list served is the live official list with extra
TZM-02 lines (official 1.4.0, and "1.4.1" = unofficial patch of 1.4.0 built by
analysis/make_patch.py + analysis/make_patch_video.py), whose .bin files are served from this folder after a
SHA-256 check. Everything else (USB detection, flashing) is the official app.
"""

import hashlib
import http.server
import subprocess
import sys
import threading
import urllib.request
from pathlib import Path

HERE = Path(__file__).resolve().parent
PORT = 47123
LIST_PATH = "/product/TECHART_LST-v1400.txt"
OFFICIAL_LIST_URL = "http://www.techart-logic.com/product/TECHART_LST.txt"
CACHED_LIST = HERE / "TECHART_LST.official.txt"
UPDATER = HERE / "TECHART_Updater_1.4.exe"

BASE_URL = f"http://127.0.0.1:{PORT}"

# (list version, file name, sha256, notes); listed in this order above the official entries
EXTRA_FIRMWARE = [
    ("VER 1.4.1", "TZM-02-VER-1-4-1-unofficial.bin",
     "c15ae49f2090964e35b1be07be0f98b39c374260beee0759684dc0931c728e22",
     "非官方补丁版（基于官方1.4.0）：恢复关机自动收回；恢复1.3.0的镜头身份与对焦指令处理，"
     "视频可自动对焦。可能有未发现的bug，刷写风险自负。"),
    ("VER 1.4.0", "TZM-02-VER-1-4-0.bin",
     "f3580a0ffe627f4422710dc6655be52f513a78a6ba5ff3d14806f3d3b0521f9f",
     "提高了暗光的对焦，改善了ZR兼容性"),
]


def extra_line(ver: str, name: str) -> str:
    stem = name.rsplit(".", 1)[0]
    return (f"TECHART TZM-02;0483;5710;{ver};Copyright TECHART Inc.;"
            f"{BASE_URL}/fw/{stem}.bin;{BASE_URL}/fw/{stem}.txt")


def load_official_list() -> bytes:
    try:
        with urllib.request.urlopen(OFFICIAL_LIST_URL, timeout=20) as r:
            data = r.read()
        CACHED_LIST.write_bytes(data)
        print("已获取官方固件清单")
        return data
    except Exception as e:
        if CACHED_LIST.exists():
            print(f"官方清单获取失败（{e}），使用本地缓存")
            return CACHED_LIST.read_bytes()
        raise SystemExit(f"无法获取官方固件清单：{e}")


def build_list(official: bytes) -> bytes:
    text = official.decode("utf-8")
    newline = "\r\n" if "\r\n" in text else "\n"
    lines = []
    for ver, name, _, _ in EXTRA_FIRMWARE:
        if f"TZM-02;0483;5710;{ver};" in text:
            print(f"官方清单已经包含 TZM-02 {ver}，不再额外添加")
            continue
        lines.append(extra_line(ver, name))
    return "".join(line + newline for line in lines).encode("utf-8") + official


def main() -> None:
    if not UPDATER.exists():
        raise SystemExit(f"找不到 {UPDATER.name}")

    routes = {LIST_PATH: build_list(load_official_list())}
    for _, name, sha, notes in EXTRA_FIRMWARE:
        fw = (HERE / name).read_bytes()
        if hashlib.sha256(fw).hexdigest() != sha:
            raise SystemExit(f"{name} 校验失败，已停止")
        stem = name.rsplit(".", 1)[0]
        routes[f"/fw/{stem}.bin"] = fw
        routes[f"/fw/{stem}.txt"] = notes.encode("gbk")  # the updater decodes notes as GBK

    class Handler(http.server.BaseHTTPRequestHandler):
        def do_GET(self):
            body = routes.get(self.path.split("?")[0])
            if body is None:
                self.send_error(404)
                return
            self.send_response(200)
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Content-Type", "application/octet-stream")
            self.end_headers()
            self.wfile.write(body)

        def log_message(self, fmt, *args):
            print("[本地服务]", self.path)

    server = http.server.ThreadingHTTPServer(("127.0.0.1", PORT), Handler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    print(f"本地服务已启动：{BASE_URL}，正在打开更新器……")

    proc = subprocess.Popen([str(UPDATER)], cwd=str(HERE))
    proc.wait()
    server.shutdown()
    print("更新器已关闭")


if __name__ == "__main__":
    sys.exit(main())
