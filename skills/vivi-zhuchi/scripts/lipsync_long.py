#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""长窗口口型检查：把 2-4 秒的嘴部帧条 + 音频能量一起铺开，再用互相关算整体滞后。

之前的 sync_pic 只抽 12 帧（0.5 秒），看不出「整段晚 150ms」这种系统偏差。
这个工具做两件事：
  1. 铺一条长帧条（默认 72 帧 ≈ 3 秒），人眼能看出节奏
  2. 算嘴部开合曲线与音频能量的互相关峰，直接给出"差几帧"

用法：
  python lipsync_long.py <视频> <起始秒> [帧数] ["嘴框"]
"""
import subprocess
import sys
import tempfile
from pathlib import Path

import numpy as np

BOX_DEFAULT = "0.40,0.42,0.60,0.55"   # 横版半身构图，只框嘴唇
S = 240            # 分析基准宽
CELL = 84          # 帧条每格大小


def fps_of(v):
    out = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0",
                          "-show_entries", "stream=r_frame_rate", "-of", "csv=p=0", str(v)],
                         capture_output=True, text=True).stdout.strip()
    out = out.split(",")[0].strip()          # csv 有时会多带一个逗号
    a, b = out.split("/")
    return float(a) / float(b)


def main():
    video = Path(sys.argv[1])
    start = float(sys.argv[2])
    n = int(sys.argv[3]) if len(sys.argv) > 3 else 72
    box = sys.argv[4] if len(sys.argv) > 4 else BOX_DEFAULT
    fps = fps_of(video)

    with tempfile.TemporaryDirectory() as td:
        # 一帧拿到尺寸
        f0 = Path(td) / "one.raw"
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", f"{start:.3f}", "-i", str(video),
                        "-frames:v", "1", "-vf", f"scale={S}:-2,format=gray", "-f", "rawvideo", str(f0)],
                       capture_output=True)
        b0 = f0.read_bytes()
        hh = len(b0) // S
        xa, ya, xb, yb = (float(v) for v in box.split(","))
        x0, y0 = int(xa * S), int(ya * hh)
        w0, h0 = int((xb - xa) * S), int((yb - ya) * hh)

        # 嘴部帧
        fm = Path(td) / "m.raw"
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", f"{start:.3f}", "-i", str(video),
                        "-frames:v", str(n), "-vf",
                        f"scale={S}:{hh},crop={w0}:{h0}:{x0}:{y0},scale={CELL}:{CELL},format=gray",
                        "-f", "rawvideo", str(fm)], capture_output=True)
        mb = fm.read_bytes()

        # 音频
        fa = Path(td) / "a.raw"
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", f"{start:.3f}", "-t", f"{n / fps:.3f}",
                        "-i", str(video), "-vn", "-ac", "1", "-ar", "16000", "-f", "f32le", str(fa)],
                       capture_output=True)
        x = np.frombuffer(fa.read_bytes(), dtype=np.float32)

    frames = np.frombuffer(mb, dtype=np.uint8)[: n * CELL * CELL].reshape(n, CELL, CELL).astype(np.float32)
    n = len(frames)

    # 嘴张开度：暗像素占比（张嘴=口腔区域变暗）
    dark = (frames <= np.percentile(frames, 22, axis=(1, 2), keepdims=True)).mean(axis=(1, 2))

    per = max(1, int(16000 // fps))
    env = np.array([np.abs(x[i * per:(i + 1) * per]).mean() for i in range(n)])

    a = (dark - dark.mean()) / (dark.std() + 1e-9)
    b = (env - env.mean()) / (env.std() + 1e-9)

    best = (-9, 0)
    allc = []
    for lag in range(-20, 21):
        if lag < 0:
            aa, bb = a[-lag:], b[:n + lag]
        elif lag > 0:
            aa, bb = a[:n - lag], b[lag:]
        else:
            aa, bb = a, b
        if len(aa) < 8:
            continue
        c = float(np.corrcoef(aa, bb)[0, 1])
        allc.append((lag, c))
        if c > best[1]:
            best = (lag, c)
    allc.sort(key=lambda t: -t[1])

    print(f"{video.name}  t={start:.2f}s  {n} 帧 @ {fps:.0f}fps  嘴框 {box}")
    print(f"最佳滞后 {best[0]:+d} 帧（{best[0] / fps * 1000:+.0f} ms）  corr={best[1]:.2f}")
    print("前 3 名：" + "  ".join(f"{l:+d}帧/{c:.2f}" for l, c in allc[:3]))

    # 长帧条
    from PIL import Image, ImageDraw, ImageFont
    fnt = ImageFont.truetype(r"C:\Windows\Fonts\msyhbd.ttc", 18)
    pad = 4
    per_row = 36
    rows = (n + per_row - 1) // per_row
    Wd = per_row * (CELL + pad)
    rowH = CELL + 56
    out = Image.new("RGB", (Wd, 26 + rows * rowH), (16, 16, 20))
    d = ImageDraw.Draw(out)
    d.text((4, 2), f"{video.name} t={start:.2f}s  lag={best[0]:+d}帧 ({best[0]/fps*1000:+.0f}ms) corr={best[1]:.2f}",
           font=fnt, fill=(255, 220, 120))
    for i in range(n):
        r, c = i // per_row, i % per_row
        x = c * (CELL + pad)
        y = 26 + r * rowH
        out.paste(Image.fromarray(frames[i].astype(np.uint8)).convert("RGB"), (x, y))
        bh = int(max(0, min(1, env[i] / (env.max() + 1e-9))) * 44)
        d.rectangle([x, y + CELL + 44 - bh, x + CELL, y + CELL + 44],
                    fill=(120, 200, 255) if env[i] > env.mean() else (70, 70, 90))
        if i % 6 == 0:
            d.text((x + 1, y + CELL + 44), str(i), font=fnt, fill=(190, 190, 200))
    out.save("lipsync_long.png")
    print("→ lipsync_long.png")


if __name__ == "__main__":
    main()
