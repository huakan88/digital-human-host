#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""逐帧并列打印「嘴部开合」与「音频音量」，人眼直接读偏移。

用法：python frame_pairs.py <视频> <起始秒> [帧数]
输出：每帧一行，左边嘴张开度柱，右边音频音量柱。
        再给出「音量最高那一帧」与「嘴最张那一帧」相差多少帧。
"""
import subprocess
import sys
import tempfile
from pathlib import Path

import numpy as np

BOX = (0.40, 0.40, 0.60, 0.56)


def main():
    video = Path(sys.argv[1])
    start = float(sys.argv[2])
    n = int(sys.argv[3]) if len(sys.argv) > 3 else 60
    fps = 24.0
    out = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0",
                          "-show_entries", "stream=r_frame_rate", "-of", "csv=p=0", str(video)],
                         capture_output=True, text=True).stdout.strip().split(",")[0]
    a, b = out.split("/")
    fps = float(a) / float(b)

    with tempfile.TemporaryDirectory() as td:
        f = Path(td) / "v.raw"
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", f"{start:.3f}", "-i", str(video),
                        "-frames:v", str(n), "-vf", "scale=480:-2,format=gray",
                        "-f", "rawvideo", str(f)], capture_output=True)
        raw = f.read_bytes()
        w = 480
        h = len(raw) // max(1, n) // w
        arr = np.frombuffer(raw, dtype=np.uint8)[: n * h * w].reshape(n, h, w).astype(np.float32)

        fa = Path(td) / "a.raw"
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", f"{start:.3f}", "-t", f"{n/fps:.3f}",
                        "-i", str(video), "-vn", "-ac", "1", "-ar", "16000", "-f", "f32le", str(fa)],
                       capture_output=True)
        x = np.frombuffer(fa.read_bytes(), dtype=np.float32)

    x0, y0 = int(BOX[0] * w), int(BOX[1] * h)
    x1, y1 = int(BOX[2] * w), int(BOX[3] * h)
    lip = arr[:, y0:y1, x0:x1]
    # 张嘴 → 唇间暗区变大 → 暗像素占比升高
    open_ = (lip <= np.percentile(lip, 25)).mean(axis=(1, 2))

    per = max(1, int(16000 // fps))
    n = min(n, len(open_), max(1, len(x) // per))
    rms = np.array([np.sqrt((x[i * per:(i + 1) * per] ** 2).mean()) if (i + 1) * per <= len(x) else 0.0
                    for i in range(n)])

    sig = open_[:n]
    o = (sig - sig.min()) / (np.max(sig) - np.min(sig) + 1e-9)
    r = (rms - rms.min()) / (np.max(rms) - np.min(rms) + 1e-9)

    print(f"{video.name}  t={start:.2f}s  {n} 帧 @ {fps:.0f}fps")
    print("帧  嘴张开 音量")
    for i in range(n):
        print(f"{i:3d}  {'█' * int(o[i] * 22):22s} | {'▓' * int(r[i] * 22)}")
    top_o = [i for i in range(n) if o[i] > 0.75]
    top_r = [i for i in range(n) if r[i] > 0.75]
    print(f"\n嘴最张的帧: {top_o}")
    print(f"音量最高的帧: {top_r}")


if __name__ == "__main__":
    main()
