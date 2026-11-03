# TECHART TZM-02 非官方补丁固件 / Unofficial Patched Firmware

> **⚠️ 免责声明 / Disclaimer**
>
> 本项目是个人逆向分析后制作的**非官方**补丁固件，与 TECHART（天工）及其代理商无任何关系，未经厂商认可。补丁只在作者自己的一套设备上做过有限测试，**很可能还有尚未发现的 bug**。刷写固件存在使转接环工作异常甚至无法使用的风险，也可能影响保修。**是否刷写请自行判断，一切后果由使用者自行承担。**
>
> This is an **unofficial** firmware patch made by reverse engineering. It is not affiliated with or endorsed by TECHART or its distributors. It has only been tested briefly on the author's own equipment and **very likely contains bugs that have not been found yet**. Flashing firmware may cause the adapter to malfunction or stop working, and may void your warranty. **Flash at your own risk; you alone are responsible for any consequences.**

---

## 这是什么 / What is this

TECHART TZM-02 是徕卡 M 口镜头转尼康 Z 卡口的自动对焦转接环。官方 1.4.0 固件已在服务器上发布，但官方更新工具的固件清单里没有它；而且刷上 1.4.0 后我发现两个相对 1.3.0 的退步：

1. **关机后转接环不再自动收回**（1.3.0 会收回）。
2. **视频模式下无法自动对焦**：AF-F 不动，AF-C 半按快门也没有反应（1.3.0 虽然不准，但能动）。

本仓库提供在官方 1.4.0 基础上修复这两点的补丁固件，以及一个能把这些固件加进官方更新工具列表的启动器。

The TECHART TZM-02 is an autofocus adapter for Leica M lenses on Nikon Z cameras. Official firmware 1.4.0 is on TECHART's server but missing from the official updater's list. After flashing it, I found two regressions compared with 1.3.0:

1. **The adapter no longer retracts when the camera powers off** (1.3.0 did).
2. **No autofocus in video**: AF-F does nothing and half-pressing the shutter in AF-C has no effect (1.3.0 was inaccurate but did move).

This repository provides patched firmware based on official 1.4.0 that fixes both, plus a launcher that adds these files to the official updater's list.

## 固件版本 / Firmware versions

"1.4.1" 只是为了能在更新工具里显示而起的名字，**不是官方版本**。 / "1.4.1" is only a label so the updater can list it; **it is not an official release.**

| 列表中显示 / Listed as | 文件 / File | 内容 / Contents |
|---|---|---|
| **VER 1.4.1（非官方 / unofficial）** | `TZM-02-VER-1-4-1-unofficial.bin` | 官方 1.4.0 + 关机收回 + 恢复 1.3.0 的镜头身份应答和对焦指令处理 / Official 1.4.0 + power-off retract + 1.3.0 lens identity replies and focus-command handling |
| VER 1.4.0 | `TZM-02-VER-1-4-0.bin` | 官方原版 1.4.0 / Official 1.4.0, unmodified |

作者实测（单台机身）：1.4.1 关机能收回，视频对焦“勉强可用”（和 1.3.0 类似，AF-F 会来回拉）。

Author's test (one camera body): with 1.4.1 the adapter retracts on power-off, and video AF is "barely usable" (similar to 1.3.0; AF-F hunts back and forth).

如果 TECHART 以后发布官方 1.4.1，官方清单里出现同名版本时启动器不会再添加本补丁版。 / If TECHART ever publishes an official 1.4.1, the launcher stops adding this patch once that version appears in the official list.

## 使用方法 / How to use

需要 Windows 和 [Python 3](https://www.python.org/downloads/)（安装时勾选 “Add python.exe to PATH”）。

Requires Windows and [Python 3](https://www.python.org/downloads/) (tick "Add python.exe to PATH" when installing).

1. 下载本仓库（绿色 **Code** 按钮 → **Download ZIP**）并解压。 / Download this repository (green **Code** button → **Download ZIP**) and unzip it.
2. 用 USB 连接转接环（方法同官方更新）。 / Connect the adapter by USB, as for an official update.
3. 双击 `启动TZM-02_1.4更新器.cmd`。它会在本机 `127.0.0.1:47123` 起一个临时服务，然后打开更新工具。 / Double-click `启动TZM-02_1.4更新器.cmd`. It starts a temporary local server on `127.0.0.1:47123` and opens the updater.
4. 在列表中选择 **VER 1.4.1**，点击更新。刷写过程中不要断开。 / Select **VER 1.4.1** in the list and click Update. Do not disconnect during flashing.
5. 关闭更新工具后，命令行窗口里的本地服务也会停止。 / Closing the updater also stops the local server.

**回退 / Rollback**：同一个列表里有官方 **VER 1.3.0** 和 **VER 1.4.0**，选中后刷写即可回到官方固件。补丁不修改引导程序（bootloader），刷写方式和官方升级完全相同。 / The same list contains the official **VER 1.3.0** and **VER 1.4.0**; flash either one to return to official firmware. The patches do not touch the bootloader, and flashing works exactly like an official update.

## 是怎么做出来的 / How it was made

### 1. 让更新工具显示 1.4.0 / Getting 1.4.0 into the updater

官方更新工具 `TECHART_Updater(USB).exe` 从 `http://www.techart-logic.com/product/TECHART_LST.txt` 读取固件清单，清单里没有 TZM-02 1.4.0 这一行，但 `.bin` 文件本身在服务器上。

`TECHART_Updater_1.4.exe` 是官方工具的副本，只把这个清单地址替换成等长的本地地址（共 39 个字节，见 `patch_updater.py`）。`run_updater_1.4.py` 取回官方清单，在前面加上本仓库的固件，校验 SHA-256 后由本地服务提供；USB 检测和刷写都还是官方程序自己完成的。

The official updater `TECHART_Updater(USB).exe` reads its list from `http://www.techart-logic.com/product/TECHART_LST.txt`. That list lacks a TZM-02 1.4.0 line, although the `.bin` exists on the server.

`TECHART_Updater_1.4.exe` is a copy of the official updater in which only that URL is replaced by a same-length local URL (39 bytes, see `patch_updater.py`). `run_updater_1.4.py` fetches the official list, prepends this repository's firmware after checking their SHA-256, and serves them locally. USB detection and flashing are still done by the official program.

### 2. 关机收回 / Power-off retract

固件运行在 Microchip SAMD21（Cortex-M0+）上，程序从 flash 0x5000 开始。用 Capstone 反汇编 1.3.0 和 1.4.0 并对比相机消息的分发函数：

- 相机关机时会反复发送消息 `0x5101`。1.3.0 前 50 次回答“忙”，并在第 2 次时把镜头开到收回位置，之后才回答“完成”。
- 1.4.0 的这段处理还在，但决定是否回答“忙”的函数是个永远返回 0 的空壳，所以第一次就回答“完成”，电机也不动。

补丁在固件末尾加了一个小函数，按 1.3.0 的方式计数并驱动电机，计数器用开机时清零的一块未使用内存（`analysis/make_patch.py`）。

The firmware runs on a Microchip SAMD21 (Cortex-M0+), with the application at flash 0x5000. I disassembled 1.3.0 and 1.4.0 with Capstone and compared their camera-message dispatchers:

- While shutting down, the camera repeatedly sends message `0x5101`. 1.3.0 answers "busy" for the first 50 polls, drives the lens to the retracted position on the 2nd, and then answers "done".
- 1.4.0 still has this handler, but the function that decides whether to answer "busy" is a stub that always returns 0. It answers "done" at once and never moves the motor.

The patch appends a small function that counts polls and drives the motor the way 1.3.0 does, using an unused word of RAM that is zeroed at boot (`analysis/make_patch.py`).

### 3. 视频对焦 / Video AF

对比两版发给相机的应答和对焦指令处理，1.4.0 有以下变化（`analysis/make_patch_video.py`）：

- **镜头身份**：1.3.0 向相机自报为尼康 “Mount Adapter FTZ / NIKON”，1.4.0 改为 “TZM-02 / TECHART”。镜头信息里有一个能力字节从 `0x30` 改成了 `0x40`。一个新查询 `0x0028` 被回答成 46 字节全零（1.3.0 不回答）。另一个状态查询的两个子项回答被对调。半按快门完全没反应，说明是相机自己没有发起对焦，很可能就是相机根据这些应答判断这只“镜头”不支持视频对焦。
- **对焦指令**：1.3.0 中指令 `0x19` 和 `0x09` 走同一套处理，都会驱动电机。1.4.0 对 `0x19` 只回应不动，对部分 `0x09` 也不动，并且在非标准模式下不再驱动电机。

1.4.1 两者都恢复。（开发过程中也试过只恢复镜头身份的版本，可用 `make_patch_video.py` 生成为 `vidA`。）

Comparing the replies sent to the camera and the focus-command handling, 1.4.0 changed the following (`analysis/make_patch_video.py`):

- **Lens identity**: 1.3.0 identifies itself to the camera as Nikon "Mount Adapter FTZ / NIKON", while 1.4.0 says "TZM-02 / TECHART". A capability byte in the lens info changed from `0x30` to `0x40`. A new query `0x0028` is answered with 46 zero bytes (1.3.0 does not answer it). Two sub-answers of another status query are swapped. Since half-pressing the shutter does nothing at all, the camera itself is not starting AF. Most likely it decides from these replies that the "lens" cannot autofocus in video.
- **Focus commands**: in 1.3.0, commands `0x19` and `0x09` share one handler and both drive the motor. 1.4.0 only acknowledges `0x19` without moving, also ignores some `0x09` cases, and no longer drives the motor in non-standard modes.

1.4.1 restores both. (An intermediate build restoring only the lens identity is also produced by `make_patch_video.py` as `vidA`.)

### 已知局限 / Known limitations

- 1.4.1 恢复了 1.3.0 的“FTZ”身份，官方 1.4.0 宣称的“改善 ZR 兼容性”可能因此失效，在尼康 ZR 上可能有问题；暗光对焦的改进是否保留也未验证。 / 1.4.1 restores the 1.3.0 "FTZ" identity, so the "improved ZR compatibility" claimed for official 1.4.0 may be lost and the Nikon ZR may have problems. Whether the low-light AF improvement survives is untested.
- 视频对焦只是恢复到 1.3.0 的水平，并不精确，AF-F 会来回拉。 / Video AF is only restored to the 1.3.0 level: not accurate, and AF-F hunts.
- 关机收回时不像 1.3.0 那样保存设置，也不检查“关闭收回”的设置项。 / The power-off retract does not save settings and does not check a "no retract" setting, unlike 1.3.0.
- 只在一台机身、少量镜头上测试过。 / Tested on one camera body with only a few lenses.

## 文件说明 / Files

| 文件 / File | 说明 / Description |
|---|---|
| `启动TZM-02_1.4更新器.cmd` | 双击启动 / Double-click to start |
| `run_updater_1.4.py` | 本地清单服务 + 启动更新工具 / Local list server + updater launcher |
| `TECHART_Updater_1.4.exe` | 改过清单地址的官方更新工具 / Official updater with the list URL changed |
| `patch_updater.py` | 由官方 exe 生成上面的文件 / Generates the file above from the official exe |
| `TECHART_LST.official.txt` | 官方清单的缓存（联网失败时使用） / Cached official list, used when offline |
| `TZM-02-VER-1-4-1-unofficial.bin` | 补丁固件 / Patched firmware |
| `TZM-02-VER-1-4-0.bin` | 官方 1.4.0 / Official 1.4.0 |
| `TZM-02-VER-1-3-0.bin` | 官方 1.3.0，用于对比分析 / Official 1.3.0, used for comparison |
| `analysis/` | 反汇编与补丁生成脚本（需 `pip install capstone`） / Disassembly and patch-building scripts (need `pip install capstone`) |

### 自己重新生成补丁 / Rebuilding the patches yourself

```
pip install capstone
cd analysis
python make_patch.py          # 1.4.0 -> TZM-02-VER-1-4-0-retract.bin（只加关机收回 / retract only）
python make_patch_video.py    # retract -> TZM-02-VER-1-4-1-unofficial.bin（以及中间版 / and intermediate vidA）
```

脚本会先校验源固件的 SHA-256，生成的文件应与仓库中的完全一致。 / The scripts check the source firmware's SHA-256 first, and the output should match the files in this repository byte for byte.

| 文件 / File | SHA-256 |
|---|---|
| `TZM-02-VER-1-4-0.bin`（官方 / official） | `f3580a0ffe627f4422710dc6655be52f513a78a6ba5ff3d14806f3d3b0521f9f` |
| `TZM-02-VER-1-4-1-unofficial.bin` | `c15ae49f2090964e35b1be07be0f98b39c374260beee0759684dc0931c728e22` |

## 版权 / Copyright

官方固件和更新工具的版权归 TECHART 所有，此处仅为方便用户修复上述问题而提供。如权利人要求，将立即删除相关文件。本仓库中的脚本可自由使用。

The official firmware and updater are copyright TECHART and are included only to help users fix the issues above. They will be removed promptly on request from the rights holder. The scripts in this repository are free to use.
