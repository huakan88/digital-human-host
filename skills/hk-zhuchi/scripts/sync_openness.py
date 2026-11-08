#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""口型同步（第三版，只用画面）：嘴部「张开度」 vs 配音能量，逐帧互相关。

为什么前两版不行：
  1) 拿片段自带音轨去和配音比 —— 相关性只有 0.2~0.4，那不是同一段声音，对齐结果是噪声。
  2) 用「嘴部帧间运动」当开口度 —— 头动、眨眼都会污染，相关也不稳。

这一版：在嘴部小框里数**暗像素占比**（张嘴时口腔是暗的），得到逐帧开口度；
再和配音 30fps 能量包络做互相关，只在 ±12 帧内找峰，并给出 corr。
corr 太低就判定「测不出来」，返回 0 不硬改。
"""
import subprocess
import sys
from pathlib import Path

import numpy as np

FPS = 30
# 嘴部框（按宽高比例）：只取嘴唇那条横带，避免下巴/脖子
ROI_F = (0.34, 0.445, 0.66, 0.515)


def probe_wh(p):
    r = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0",
                        "-show_entries", "stream=width,height", "-of", "csv=p=0", str(p)],
                       capture_output=True, text=True)
    w, h = r.stdout.strip().split(",")[:2]
    return int(w), int(h)


def mouth_openness(clip, dur):
    W0, H0 = probe_wh(clip)
    fx0, fy0, fx1, fy1 = ROI_F
    w, h = int(W0 * (fx1 - fx0)), int(H0 * (fy1 - fy0))
    x0, y0 = int(W0 * fx0), int(H0 * fy0)
    r = subprocess.run(
        ["ffmpeg", "-v", "error", "-i", str(clip), "-t", f"{dur:.3f}",
         "-vf", f"crop={w}:{h}:{x0}:{y0},format=gray", "-r", str(FPS), "-f", "rawvideo", "-"],
        capture_output=True)
    buf = np.frombuffer(r.stdout, dtype=np.uint8)
    n = len(buf) // (w * h)
    if n == 0:
        return np.zeros(1)
    f = buf[:n * w * h].reshape(n, h, w).astype(np.float32)
    # 暗像素占比：张嘴时口腔温度低（暗）
    dark = (f < np.percentile(f, 18, axis=(1, 2), keepdims=True)).mean(axis=(1, 2))
    return dark


def audio_env(wav, n):
    r = subprocess.run(["ffmpeg", "-v", "error", "-i", str(wav), "-ac", "1", "-ar", "16000",
                        "-f", "f32le", "-"], capture_output=True)
    x = np.frombuffer(r.stdout, dtype=np.float32)
    hop = max(1, len(x) // n)
    e = np.array([np.sqrt(np.mean(x[i * hop:(i + 1) * hop] ** 2) + 1e-12) for i in range(n)])
    if len(e) < n:
        e = np.pad(e, (0, n - len(e)), mode="edge")
    return e[:n]


def best_lag(aud, vis, max_lag=12):
    a = (aud - aud.mean()) / (aud.std() + 1e-9)
    b = (vis - vis.mean()) / (vis.std() + 1e-9)
    best = (0, -1.0)
    for lag in range(-max_lag, max_lag + 1):
        if lag >= 0:
            x, y = a[:len(a) - lag], b[lag:]
        else:
            x, y = a[-lag:], b[:len(b) + lag]
        m = min(len(x), len(y))
        if m < 20:
            continue
        c = float(np.corrcoef(x[:m], y[:m])[0, 1])
        if c > best[1]:
            best = (lag, c)
    return best


def main():
    clip = Path(sys.argv[1])
    wav = Path(sys.argv[2])
    dur = float(sys.argv[3]) if len(sys.argv) > 3 else 12.0
    vis = mouth_openness(clip, dur)
    aud = audio_env(wav, len(vis))
    lag, corr = best_lag(aud, vis)
    print(f"{clip.name}  {len(vis)} 帧  →  画面比配音 lag {lag:+d} 帧 ({lag/FPS*1000:+.0f}ms)  corr {corr:+.2f}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
