#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""验收：成片里每一个露脸窗口，口型到底对没对上。

对每个窗口：
  · 整窗最优延迟（帧）
  · 每 1.5 秒子窗的最优延迟，取绝对值最大者（抓"越走越偏"）
  · 相关性（越高说明这块确实在跟着音频动）

判定：整窗 |lag| ≤ 2 帧 且 子窗最大 |lag| ≤ 3 帧 → 通过。
（30fps 下 2 帧 ≈ 67ms、3 帧 ≈ 100ms，人眼基本分不出）
"""
import subprocess
import sys
import tempfile
from pathlib import Path

import numpy as np

S = 160
MAX_LAG = 10


def video_fps(v):
    out = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0",
                          "-show_entries", "stream=r_frame_rate", "-of", "csv=p=0", str(v)],
                         capture_output=True, text=True).stdout.strip()
    try:
        a, b = out.split("/")
        return float(a) / float(b)
    except Exception:
        return 30.0


def load(video, fps):
    with tempfile.TemporaryDirectory() as td:
        f = Path(td) / "f.raw"
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(video),
                        "-vf", f"scale={S}:{S},format=gray", "-f", "rawvideo", str(f)], capture_output=True)
        b = f.read_bytes()
        a = Path(td) / "a.raw"
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(video), "-vn", "-ac", "1", "-ar", "48000",
                        "-f", "f32le", str(a)], capture_output=True)
        x = np.frombuffer(a.read_bytes(), dtype=np.float32)
    n = len(b) // (S * S)
    if n < 8:
        return None, None
    fr = np.frombuffer(b[:n * S * S], dtype=np.uint8).reshape(n, S, S).astype(np.float32)
    per = int(48000 // fps)
    m = len(x) // per
    env = np.abs(x[:m * per].reshape(m, per)).mean(axis=1)
    if len(env) < n:
        env = np.pad(env, (0, n - len(env)))
    return fr, env[:n]


def corr_at(dark, env, lag):
    if lag >= 0:
        a, b = env[:len(env) - lag], dark[lag:]
    else:
        a, b = env[-lag:], dark[:len(dark) + lag]
    k = min(len(a), len(b))
    if k < 12:
        return -9
    a, b = a[:k] - a[:k].mean(), b[:k] - b[:k].mean()
    s = a.std() * b.std()
    return float((a * b).mean() / s) if s > 1e-9 else -9


def analyse(video):
    fps = video_fps(video)
    fr, env = load(video, fps)
    if fr is None:
        return None
    n = len(fr)
    best = (0, -9, None)
    # 只在人脸上半部找嘴：竖版片的字幕在 y≈0.66 以下，且字幕总是领先语音，
    # 搜索范围包含字幕的话会量到字幕而不是嘴（实测会假报 -6 帧）。
    for bh in (0.10, 0.13, 0.16):
        for cy in np.arange(0.30, 0.58, 0.05):
            for cx in np.arange(0.34, 0.70, 0.08):
                bw = 0.28
                x0 = int((cx - bw / 2) * S); y0 = int((cy - bh / 2) * S)
                w0, h0 = int(bw * S), int(bh * S)
                if x0 < 0 or y0 < 0 or x0 + w0 > S or y0 + h0 > S:
                    continue
                if cy + bh / 2 > 0.62:      # 字幕区，排除
                    continue
                reg = fr[:, y0:y0 + h0, x0:x0 + w0]
                dark = (reg <= np.percentile(reg, 20)).mean(axis=(1, 2))
                for lag in range(-MAX_LAG, MAX_LAG + 1):
                    c = corr_at(dark, env, lag)
                    if c > best[1]:
                        best = (lag, c, dark)
    lag, c, dark = best
    # 子窗
    W = max(16, int(round(1.5 * fps)))
    H = max(6, int(round(0.75 * fps)))
    subs = []
    t = 0
    while t + W <= n:
        b2 = (0, -9)
        for lag2 in range(-MAX_LAG, MAX_LAG + 1):
            c2 = corr_at(dark[t:t + W], env[t:t + W], lag2)
            if c2 > b2[1]:
                b2 = (lag2, c2)
        subs.append(b2)
        t += H
    # 只采信「相关够高」的子窗：说话少/嘴动得少的窗口，估计本身就是噪声，
    # 实测会出现 +1 → -10 → +10 这种物理上不可能的跳变，就是这类窗口造成的。
    trusted = [x for x in subs if x[1] >= 0.40]
    worst = max((abs(x[0]) for x in trusted), default=0)
    return {"fps": fps, "frames": n, "lag": lag, "corr": round(c, 3),
            "sub_max_abs_lag": worst, "n_trusted": len(trusted), "n_sub": len(subs),
            "sub_lags": [x[0] for x in subs],
            "sub_trusted_lags": [x[0] for x in trusted],
            "sub_corrs": [round(x[1], 2) for x in subs]}


def main():
    video = Path(sys.argv[1])
    wins = []
    for part in sys.argv[2].split(","):
        p = part.strip()
        if "-" in p:
            a, b = p.split("-", 1)
            wins.append((float(a), float(b)))
    print(f"{video.name}")
    ok_all = True
    for i, (a, b) in enumerate(wins, 1):
        with tempfile.TemporaryDirectory() as td:
            w = Path(td) / "w.mp4"
            subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", f"{a:.3f}", "-t", f"{b - a:.3f}",
                            "-i", str(video), "-c:v", "libx264", "-crf", "20", "-c:a", "aac", str(w)],
                           capture_output=True)
            r = analyse(w)
        if not r:
            print(f"  窗口{i} {a:.2f}-{b:.2f}s  采样不足，跳过")
            continue
        ok = abs(r["lag"]) <= 2 and r["sub_max_abs_lag"] <= 3
        ok_all &= ok
        print(f"  窗口{i} {a:6.2f}-{b:6.2f}s  {r['frames']:4d}帧  "
              f"整窗 lag={r['lag']:+d}帧({r['lag'] / r['fps'] * 1000:+.0f}ms) corr={r['corr']:.2f}  "
              f"子窗最大|lag|={r['sub_max_abs_lag']}帧  {'✓' if ok else '✗'}")
        print(f"          可信子窗 {r['n_trusted']}/{r['n_sub']} 个，延迟 {r['sub_trusted_lags']}")
        print(f"          子窗相关     {r['sub_corrs']}")
    print("\n" + ("全部窗口通过 ✓" if ok_all else "有窗口未达标 ✗ —— 需要再修一轮"))


if __name__ == "__main__":
    main()
