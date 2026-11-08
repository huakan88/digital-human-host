#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""口型人眼判读图（等价于技能里的 sync_pic）：上排嘴部逐帧，下排同帧配音能量。

用法：python img_sync_check.py <视频> <配音wav> <起始秒> [帧数] [输出png]

判读：嘴张得最大的那几帧，应该落在能量条最高的格上；能量接近零的帧，嘴应该闭着。
      对不上几格，就是差几帧。
"""
import subprocess
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont

FPS = 30
ROI_F = (0.296, 0.432, 0.704, 0.536)   # 嘴部框（按画面宽高的比例，适配任意分辨率）
CW, CH = 180, 110                # 每格缩放后尺寸
FONT = r"C:\Windows\Fonts\msyh.ttc"


def probe_wh(video: Path):
    r = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0",
                        "-show_entries", "stream=width,height", "-of", "csv=p=0", str(video)],
                       capture_output=True, text=True)
    w, h = r.stdout.strip().split(",")[:2]
    return int(w), int(h)


def grab(video: Path, t0: float, n: int):
    W0, H0 = probe_wh(video)
    fx0, fy0, fx1, fy1 = ROI_F
    x0, y0 = int(W0 * fx0), int(H0 * fy0)
    x1, y1 = int(W0 * fx1), int(H0 * fy1)
    r = subprocess.run(["ffmpeg", "-v", "error", "-ss", f"{t0:.3f}", "-i", str(video),
                        "-frames:v", str(n), "-vf",
                        f"crop={x1-x0}:{y1-y0}:{x0}:{y0},scale={CW}:{CH},format=rgb24",
                        "-f", "rawvideo", "-"], capture_output=True)
    buf = np.frombuffer(r.stdout, dtype=np.uint8)
    k = CW * CH * 3
    m = len(buf) // k
    return buf[:m * k].reshape(m, CH, CW, 3)


def energy(wav: Path, t0: float, n: int):
    r = subprocess.run(["ffmpeg", "-v", "error", "-ss", f"{t0-0.3:.3f}", "-i", str(wav),
                        "-ac", "1", "-ar", "16000", "-f", "f32le", "-"], capture_output=True)
    x = np.frombuffer(r.stdout, dtype=np.float32)
    hop = 16000 // FPS
    e = []
    off = int(0.3 * FPS)
    for i in range(off, off + n):
        seg = x[i * hop:(i + 1) * hop]
        e.append(float(np.sqrt(np.mean(seg ** 2) + 1e-12)) if len(seg) else 0.0)
    e = np.array(e)
    return e / (e.max() + 1e-9)


def main():
    video, wav, t0 = Path(sys.argv[1]), Path(sys.argv[2]), float(sys.argv[3])
    n = int(sys.argv[4]) if len(sys.argv) > 4 else 12
    out = Path(sys.argv[5]) if len(sys.argv) > 5 else Path("qc_sync.png")

    frames = grab(video, t0, n)
    en = energy(wav, t0, n)
    cols, pad = n, 6
    barh = 90
    W = cols * (CW + pad) + pad
    H = CH + barh + 60
    img = Image.new("RGB", (W, H), "#111")
    d = ImageDraw.Draw(img)
    f = ImageFont.truetype(FONT, 16)
    for i in range(len(frames)):
        x = pad + i * (CW + pad)
        img.paste(Image.fromarray(frames[i]), (x, 30))
        d.text((x + 2, 8), f"{t0 + i/FPS:.2f}s", font=f, fill="#888")
        # 能量条
        h = int(en[i] * barh)
        d.rectangle([x, 30 + CH + barh - h, x + CW, 30 + CH + barh],
                    fill="#3B7BFF" if en[i] > 0.35 else "#2a3a5a")
        d.text((x + 2, 30 + CH + 4), f"{en[i]:.2f}", font=f, fill="#9ab")
    d.text((pad, H - 20), "上：嘴部逐帧    下：同帧配音能量（越高越响）", font=f, fill="#ccc")
    img.save(out)
    print("✓", out, f"{len(frames)} 帧")


if __name__ == "__main__":
    sys.exit(main())
