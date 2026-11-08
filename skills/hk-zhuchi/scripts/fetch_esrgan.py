#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""下载 Real-ESRGAN ncnn 便携版到 <skill>/tools/esrgan/。

为什么需要它：出画超分要用 Real-ESRGAN（x4plus + tile=0）。
它是 Windows 专用的单文件二进制，**不入 Git 仓**（三套技能各 51MB 太肥，
而且对非 Windows 用户无用），所以换机器时跑一次这个脚本即可。

用法：
    python <skill>/scripts/fetch_esrgan.py            # 自动下载并解压
    python <skill>/scripts/fetch_esrgan.py --check    # 只检查是否已就位

下载源：官方 GitHub Release（境外直连）；直连不通时自动改用 gh-proxy 镜像。
"""
import argparse
import os
import pathlib
import shutil
import subprocess
import sys
import zipfile

SKILL = pathlib.Path(os.environ.get("HK_PRESET") or pathlib.Path(__file__).resolve().parent.parent).resolve()
DEST = SKILL / "tools" / "esrgan"
EXE = DEST / "realesrgan-ncnn-vulkan.exe"

FILENAME = "realesrgan-ncnn-vulkan-20220424-windows.zip"
UPSTREAM = "https://github.com/xinntao/Real-ESRGAN/releases/download/v0.2.5.0/" + FILENAME
MIRROR = "https://gh-proxy.com/" + UPSTREAM
FALLBACKS = [UPSTREAM, MIRROR]


def check():
    ok = EXE.exists()
    print(f"目标: {DEST}")
    print(f"可执行文件: {'✓ 已就位' if ok else '✗ 缺失'}")
    if ok:
        size = sum(f.stat().st_size for f in DEST.rglob("*") if f.is_file())
        print(f"目录体积: {size/1048576:.1f} MB")
    return 0 if ok else 1


def download(url, dest):
    print(f"下载 {url}")
    r = subprocess.run(["curl.exe", "-s", "-L", "--max-time", "300", "-o", str(dest), url,
                        "-w", "%{http_code}"])
    code = (r.stdout or "").strip()
    size = dest.stat().st_size if dest.exists() else 0
    print(f"  http={code} size={size/1048576:.1f} MB")
    return size > 5_000_000


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true", help="只检查，不下载")
    a = ap.parse_args()
    if a.check:
        return check()
    if EXE.exists():
        print("已就位，不用下载。")
        return 0

    DEST.parent.mkdir(parents=True, exist_ok=True)
    tmp = DEST.parent / FILENAME
    got = False
    for url in FALLBACKS:
        if download(url, tmp):
            got = True
            break
        print("  失败，换下一个源")
    if not got:
        print("下载失败。可手动去 https://github.com/xinntao/Real-ESRGAN/releases "
              f"下载 {FILENAME}，解压到 {DEST}")
        return 1

    print("解压…")
    with zipfile.ZipFile(tmp) as z:
        z.extractall(DEST)
    tmp.unlink(missing_ok=True)
    if not EXE.exists():
        print("解压后没找到 exe，检查压缩包结构")
        return 1
    print(f"✓ 完成：{EXE}")
    print(f"  模型目录: {DEST / 'models'}")
    print("  可用模型: realesrgan-x4plus（真人用）/ realesr-animevideov3（动画用，别用在真人脸上）")
    return 0


if __name__ == "__main__":
    sys.exit(main())
