#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""把「嘴部帧条」和「音频波形」画在同一张图上，人眼直接判断是否一一对应。

上方：逐帧的嘴部裁切
下方：同样逐帧的音频能量条
如果嘴张得最大的那几帧，正好落在音量的高峰上 → 对齐；
如果错开，错开多少格就是多少帧。

用法：python sync_pic.py <video> <起始秒> [帧数]
"""
import subprocess
import sys
import tempfile
from pathlib import Path

import numpy as np

S = 200          # 分析/裁切的基准尺寸
CELL = 96        # 每格输出尺寸


def video_fps(v):
    out = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0",
                          "-show_entries", "stream=r_frame_rate", "-of", "csv=p=0", str(v)],
                         capture_output=True, text=True).stdout.strip()
    try:
        a, b = out.split("/")
        return float(a) / float(b)
    except Exception:
        return 24.0


def find_mouth_box(video, fps, start, n):
    """用一小段找嘴：和音频最相关的那块。"""
    with tempfile.TemporaryDirectory() as td:
        f = Path(td) / "f.raw"
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", f"{start:.2f}", "-i", str(video),
                        "-frames:v", str(n), "-vf", f"scale={S}:-2,format=gray", "-f", "rawvideo", str(f)],
                       capture_output=True)
        b = f.read_bytes()
    h = len(b) // max(1, n) // S
    fr = np.frombuffer(b, dtype=np.uint8)[: n * h * S].reshape(n, h, S).astype(np.float32)
    best = (-1, None)
    for bh in (0.10, 0.14, 0.18):
        for cy in np.arange(0.30, 0.60, 0.05):
            for cx in np.arange(0.34, 0.70, 0.08):
                bw = 0.30
                x0 = int((cx - bw / 2) * S); y0 = int((cy - bh / 2) * h)
                w0, h0 = int(bw * S), int(bh * h)
                if x0 < 0 or y0 < 0 or x0 + w0 > S or y0 + h0 > h:
                    continue
                reg = fr[:, y0:y0 + h0, x0:x0 + w0]
                dark = (reg <= np.percentile(reg, 20)).mean(axis=(1, 2))
                v = dark.std()
                if v > best[0]:
                    best = (v, (x0, y0, w0, h0, h, S))
    return best[1] or (int(S * 0.35), int(h * 0.35), int(S * 0.3), int(h * 0.15), h, S)


def main():
    video = Path(sys.argv[1])
    start = float(sys.argv[2])
    n = int(sys.argv[3]) if len(sys.argv) > 3 else 36
    fps = video_fps(video)
    # 支持手动指定归一化框："x0,y0,x1,y1"（这几个形象的嘴实测在 y 0.42~0.52）
    manual = sys.argv[4] if len(sys.argv) > 4 else ""
    with tempfile.TemporaryDirectory() as td:
        f0 = Path(td) / "one.raw"
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", f"{start:.3f}", "-i", str(video),
                        "-frames:v", "1", "-vf", f"scale={S}:-2,format=gray", "-f", "rawvideo", str(f0)],
                       capture_output=True)
        b0 = f0.read_bytes()
    hh = len(b0) // S
    WW = S
    if manual:
        xa, ya, xb, yb = (float(v) for v in manual.split(","))
        x0, y0 = int(xa * WW), int(ya * hh)
        w0, h0 = int((xb - xa) * WW), int((yb - ya) * hh)
    else:
        x0, y0, w0, h0, hh, WW = find_mouth_box(video, fps, start, n)
    with tempfile.TemporaryDirectory() as td:
        # 原始分辨率的嘴部裁切
        f = Path(td) / "m.raw"
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", f"{start:.3f}", "-i", str(video),
                        "-frames:v", str(n), "-vf",
                        f"scale={WW}:{hh},crop={w0}:{h0}:{x0}:{y0},scale={CELL}:{CELL},format=gray",
                        "-f", "rawvideo", str(f)], capture_output=True)
        mb = f.read_bytes()
        a = Path(td) / "a.raw"
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", f"{start:.3f}", "-t", f"{n / fps:.3f}",
                        "-i", str(video), "-vn", "-ac", "1", "-ar", "16000", "-f", "f32le", str(a)],
                       capture_output=True)
        x = np.frombuffer(a.read_bytes(), dtype=np.float32)
    frames = np.frombuffer(mb, dtype=np.uint8)[: n * CELL * CELL].reshape(n, CELL, CELL)
    per = int(16000 // fps)
    env = np.array([np.abs(x[i * per:(i + 1) * per]).mean() for i in range(n)])
    env = env / (env.max() + 1e-9)

    from PIL import Image, ImageDraw, ImageFont
    fnt = ImageFont.truetype(r"C:\Windows\Fonts\msyhbd.ttc", 20)
    pad = 6
    Wd = n * (CELL + pad)
    Hd = CELL + 170
    out = Image.new("RGB", (Wd, Hd), (16, 16, 20))
    d = ImageDraw.Draw(out)
    for i in range(n):
        im = Image.fromarray(frames[i]).convert("RGB")
        out.paste(im, (i * (CELL + pad), 26))
        # 音量条
        bh = int(env[i] * 90)
        d.rectangle([i * (CELL + pad), 150 + 90 - bh, i * (CELL + pad) + CELL, 240],
                    fill=(120, 200, 255) if env[i] > 0.5 else (90, 90, 110))
        if i % 6 == 0:
            d.text((i * (CELL + pad) + 2, 246), f"{i}", font=fnt, fill=(200, 200, 210))
    d.text((4, 2), f"{video.name}  t={start:.2f}s  {n} 帧 @ {fps:.0f}fps", font=fnt, fill=(255, 220, 120))
    out.save(Path("sync_pic.png"))
    print(f"✓ sync_pic.png  {Wd}x{Hd}  嘴框 x={x0} y={y0}")


if __name__ == "__main__":
    main()
