#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""逐片段口型对齐：量出每段出画相对自己音轨的偏移，写进 gen/align.json。

为什么要这一步：H3 每段出画的「嘴-音」相对偏移并不恒定（实测 0~±330ms），
有的整体偏前、有的整体偏后。全局时间轴再好也救不了单段的固定偏移。
所以每段单独量、单独补，装配时按这个偏移平移。

用法：python lipsync_align.py            # 量所有 gen/renoise-*.mp4
      python lipsync_align.py --max-seconds 6   # 只处理 ≤6 秒的（长的另外处理）
"""
import argparse
import json
import subprocess
import tempfile
from pathlib import Path

import numpy as np

FPS = 24
W = H = 128


def sh(a):
    return subprocess.run(a, capture_output=True, check=False)


def load(video):
    with tempfile.TemporaryDirectory() as td:
        f = Path(td) / "f.raw"
        sh(["ffmpeg", "-v", "error", "-y", "-i", str(video),
            "-vf", f"scale={W}:{H},format=gray", "-f", "rawvideo", str(f)])
        b = f.read_bytes()
        a = Path(td) / "a.raw"
        sh(["ffmpeg", "-v", "error", "-y", "-i", str(video), "-vn", "-ac", "1", "-ar", "48000",
            "-f", "f32le", str(a)])
        x = np.frombuffer(a.read_bytes(), dtype=np.float32)
    n = len(b) // (W * H)
    if n < 8:
        return None, None
    fr = np.frombuffer(b[:n * W * H], dtype=np.uint8).reshape(n, H, W).astype(np.float32)
    per = 48000 // FPS
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
    if k < 30:
        return -9
    a, b = a[:k] - a[:k].mean(), b[:k] - b[:k].mean()
    s = a.std() * b.std()
    return float((a * b).mean() / s) if s > 1e-9 else -9


def measure(video, max_lag=10):
    fr, env = load(video)
    if fr is None:
        return None
    n = len(fr)
    best = (0, -9, None)
    for bh in (0.12, 0.16, 0.20):
        for cy in np.arange(0.34, 0.78, 0.06):
            for cx in np.arange(0.34, 0.70, 0.08):
                bw = 0.28
                x0 = int((cx - bw / 2) * W); y0 = int((cy - bh / 2) * H)
                w0, h0 = int(bw * W), int(bh * H)
                if x0 < 0 or y0 < 0 or x0 + w0 > W or y0 + h0 > H:
                    continue
                reg = fr[:, y0:y0 + h0, x0:x0 + w0]
                dark = (reg <= np.percentile(reg, 20)).mean(axis=(1, 2))
                for lag in range(-max_lag, max_lag + 1):
                    c = corr_at(dark, env, lag)
                    if c > best[1]:
                        best = (lag, c, (x0, y0, w0, h0))
    lag, c, box = best
    # 前后半段各测一次，判断有没有"越走越偏"
    h = n // 2
    half = []
    for sl in (slice(0, h), slice(h, n)):
        b2 = (0, -9)
        for lag2 in range(-max_lag, max_lag + 1):
            c2 = corr_at(dark[sl], env[sl], lag2)
            if c2 > b2[1]:
                b2 = (lag2, c2)
        half.append(b2)
    return {"frames": n, "seconds": round(n / FPS, 2), "lag_frames": lag,
            "lag_ms": round(lag / FPS * 1000), "corr": round(c, 3),
            "corr_first_half": round(half[0][1], 3), "corr_second_half": round(half[1][1], 3),
            "lag_first_half": half[0][0], "lag_second_half": half[1][0]}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dir", default="gen")
    ap.add_argument("--out", default="gen/align.json")
    ap.add_argument("--max-lag", type=int, default=10)
    a = ap.parse_args()
    D = Path(a.dir)
    clips = sorted(D.glob("renoise-*.mp4"))
    res = {}
    print(f"量 {len(clips)} 段的口型偏移…")
    for p in clips:
        m = measure(p, a.max_lag)
        if not m:
            continue
        res[p.name] = m
        flag = ""
        if abs(m["lag_frames"]) >= 3:
            flag += " ⚠偏移大"
        if m["corr_second_half"] < m["corr_first_half"] - 0.12:
            flag += " ⚠后半脱钩"
        print(f"  {p.name:26s} {m['seconds']:5.1f}s  lag={m['lag_ms']:+5d}ms  "
              f"corr={m['corr']:.3f}  前半{m['corr_first_half']:.3f}/后半{m['corr_second_half']:.3f}{flag}")
    Path(a.out).write_text(json.dumps(res, ensure_ascii=False, indent=1), encoding="utf-8")
    bad = [k for k, v in res.items() if abs(v["lag_frames"]) >= 3 or v["corr_second_half"] < 0.25]
    print(f"\n写入 {a.out}；需要注意的 {len(bad)} 段：{bad}")


if __name__ == "__main__":
    main()
