#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""数字人出画超分（标准工序：先渲染 576×1024 → 再超分 1152×2048）。

用法（在工程目录下）：
    python <skill>/scripts/upscale_segments.py s1 s7 s16
    python <skill>/scripts/upscale_segments.py --all          # 用 tasks.json 里所有露脸段
    python <skill>/scripts/upscale_segments.py s1 --fps 24 --tool "D:/tools/realesrgan-ncnn-vulkan.exe"

输出：gen_up/renoise-<id>.mp4（1080×1920，音轨已 mux，包装层 1:1 直接用）

⚠ 两个必须遵守的坑（2026-11-09 实测）：
  1. 必须 `-t 0`（不切 tile）。默认 128px 切块会把画面拼成错位碎块。
  2. 只用 `realesrgan-x4plus`。`realesr-animevideov3` 用在真人脸上会出描边感、睫毛结块。
  3. x4plus 会把毛孔磨掉一档，所以接 `cas=0.35` 极轻锐化找回质感；不要上强锐化（会蜡）。
"""
import argparse
import os
import pathlib
import shutil
import subprocess
import sys
import time

PROJ = pathlib.Path(os.environ.get("HK_PROJECT") or pathlib.Path.cwd()).resolve()
SKILL = pathlib.Path(os.environ.get("HK_PRESET") or pathlib.Path(__file__).resolve().parent.parent).resolve()

# Real-ESRGAN 可执行文件：环境变量 → 技能目录 tools → 工程 tools
CANDIDATES = [
    os.environ.get("HK_ESRGAN"),
    str(SKILL / "tools" / "esrgan" / "realesrgan-ncnn-vulkan.exe"),
    str(PROJ / "tools" / "esrgan" / "realesrgan-ncnn-vulkan.exe"),
    r"E:\dsh-agents\skills\vivi-zhuchi\tools\esrgan\realesrgan-ncnn-vulkan.exe",
]

SKIP = {"__pycache__"}


def find_esrgan(override=None):
    for c in ([override] if override else []) + CANDIDATES:
        if c and pathlib.Path(c).exists():
            return pathlib.Path(c)
    sys.exit(
        "找不到 realesrgan-ncnn-vulkan.exe。\n"
        "去 https://github.com/xinntao/Real-ESRGAN/releases 下 "
        "realesrgan-ncnn-vulkan-*-windows.zip，解压后设 HK_ESRGAN 指向 exe，\n"
        "或放进 <skill>/tools/esrgan/ 。"
    )


def run(cmd):
    r = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace")
    if r.returncode:
        print("  FAIL:", " ".join(str(c) for c in cmd[:3]))
        print("  ", (r.stderr or r.stdout)[-500:])
        raise SystemExit(1)
    return r


def probe(p, entries):
    return subprocess.run(["ffprobe", "-v", "error", "-show_entries", entries,
                           "-of", "csv=p=0", str(p)],
                          capture_output=True, text=True).stdout.strip()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("segs", nargs="*", help="段 id，如 s1 s7 s16")
    ap.add_argument("--all", action="store_true", help="用 tasks.json 里现有的全部出画段")
    ap.add_argument("--fps", type=int, default=24)
    ap.add_argument("--tool", default=None, help="realesrgan 可执行文件路径")
    ap.add_argument("--scale", type=int, default=4, help="模型放大倍数（默认 4，下采样到 1080x1920）")
    ap.add_argument("--sharp", type=float, default=0.35, help="cas 锐化强度（0.35 极轻）")
    ap.add_argument("--crf", type=int, default=16)
    ap.add_argument("--out-w", type=int, default=1080)
    ap.add_argument("--out-h", type=int, default=1920)
    a = ap.parse_args()

    GEN = PROJ / "gen"
    UP = PROJ / "gen_up"
    TMP = PROJ / "tmp_up"
    UP.mkdir(exist_ok=True)

    segs = a.segs
    if a.all or not segs:
        segs = sorted(p.stem.replace("renoise-", "") for p in GEN.glob("renoise-*.mp4"))
    if not segs:
        sys.exit("没有可超分的段（gen/renoise-*.mp4 不存在）")

    exe = find_esrgan(a.tool)
    print(f"Real-ESRGAN: {exe}")
    print(f"段: {', '.join(segs)}\n")

    done = []
    for seg in segs:
        src = GEN / f"renoise-{seg}.mp4"
        if not src.exists():
            print(f"[{seg}] 跳过：没有 {src.name}")
            continue
        out = UP / f"renoise-{seg}.mp4"
        fdir = TMP / seg
        if fdir.exists():
            shutil.rmtree(fdir)
        (fdir / "up").mkdir(parents=True)

        src_wh = probe(src, "stream=width,height")
        print(f"[{seg}] 原生 {src_wh} → 抽帧", flush=True)
        run(["ffmpeg", "-v", "error", "-y", "-i", str(src),
             "-vsync", "0", "-frame_pts", "1", str(fdir / "%05d.png")])
        frames = sorted(fdir.glob("*.png"))
        print(f"[{seg}] {len(frames)} 帧 → 超分 x{a.scale} (tile=0)", flush=True)

        t0 = time.time()
        for i, f in enumerate(frames, 1):
            run([str(exe), "-i", str(f), "-o", str(fdir / "up" / f.name),
                 "-n", "realesrgan-x4plus", "-s", str(a.scale), "-t", "0", "-f", "png"])
            if i % 40 == 0 or i == len(frames):
                print(f"  {i}/{len(frames)}  ({time.time()-t0:.0f}s)", flush=True)

        vf = (f"scale={a.out_w}:{a.out_h}:flags=lanczos"
              + (f",cas=strength={a.sharp}" if a.sharp > 0 else "")
              + ",format=yuv420p")
        print(f"[{seg}] → {a.out_w}×{a.out_h} + cas{a.sharp} + 编码", flush=True)
        run(["ffmpeg", "-v", "error", "-y",
             "-framerate", str(a.fps), "-i", str(fdir / "up" / "%05d.png"),
             "-i", str(src),
             "-map", "0:v:0", "-map", "1:a:0",
             "-vf", vf, "-c:v", "libx264", "-crf", str(a.crf), "-preset", "slow",
             "-c:a", "copy", "-shortest", "-movflags", "+faststart", str(out)])
        print(f"[{seg}] ✓ {out.name}  {out.stat().st_size/1048576:.2f} MB\n", flush=True)
        done.append(seg)

    print("=== 完成 ===")
    for seg in done:
        a_ = GEN / f"renoise-{seg}.mp4"
        b_ = UP / f"renoise-{seg}.mp4"
        print(f"  {seg}: {a_.stat().st_size/1048576:.2f} MB → {b_.stat().st_size/1048576:.2f} MB"
              f"   {probe(b_, 'stream=width,height')}")
    print(f"\n输出在 {UP}\n包装层用 gen_up/ 里的片，1:1 直接铺，不要再缩放。")


if __name__ == "__main__":
    main()
