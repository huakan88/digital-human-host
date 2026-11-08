#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""判 H3 是不是按我们的配音在说话：比对有效发声时长与停顿分布。

如果 H3 是在"复述"我们的话但自己重排了节奏，两边的
  · 有效发声总时长
  · 首次起声 / 末次收声
就会明显不同。这种差异是偏移补不回来的——嘴跟着它自己的节奏动。
"""
import json
import subprocess
import sys
from pathlib import Path

import numpy as np

SR = 16000


def decode(p):
    r = subprocess.run(["ffmpeg", "-v", "error", "-i", str(p), "-ac", "1", "-ar", str(SR),
                        "-f", "f32le", "-"], capture_output=True)
    return np.frombuffer(r.stdout, dtype=np.float32)


def env_db(x, hop=SR // 100):
    n = len(x) // hop
    e = np.array([np.sqrt(np.mean(x[i * hop:(i + 1) * hop] ** 2) + 1e-12) for i in range(n)])
    return 20 * np.log10(e / (e.max() + 1e-12) + 1e-9)


def stats(x):
    db = env_db(x)
    voiced = db > -30                       # -30dB 相对峰值
    # 最长连续发声段
    best = cur = 0
    for v in voiced:
        cur = cur + 1 if v else 0
        best = max(best, cur)
    idx = np.where(voiced)[0]
    return {
        "dur_s": round(len(x) / SR, 2),
        "voiced_s": round(voiced.sum() / 100, 2),
        "voiced_ratio": round(float(voiced.mean()), 2),
        "first_s": round(idx[0] / 100, 2) if len(idx) else None,
        "last_s": round(idx[-1] / 100, 2) if len(idx) else None,
        "longest_run_s": round(best / 100, 2),
        "bursts": int(np.sum(np.diff(voiced.astype(int)) == 1) + (1 if voiced[0] else 0)),
    }


def main():
    tasks = json.loads(Path("tasks.json").read_text(encoding="utf-8-sig"))
    only = set(sys.argv[1].split(",")) if len(sys.argv) > 1 else None
    print(f"{'段':5s} {'来源':10s} {'时长':>6s} {'发声':>6s} {'占比':>5s} {'起':>6s} {'收':>6s} {'最长':>6s} {'段数':>4s}")
    for t in tasks:
        sid = t["label"].split()[-1]
        if only and sid not in only:
            continue
        clip = Path("gen") / f"renoise-{sid}.mp4"
        pad = Path("voice") / f"{sid}_pad.wav"
        if not clip.exists() or not pad.exists():
            continue
        for label, path in (("配音(参考)", pad), ("H3 片段音轨", clip)):
            s = stats(decode(path))
            print(f"{sid if label.startswith('配音') else '':5s} {label:10s} {s['dur_s']:6.2f} "
                  f"{s['voiced_s']:6.2f} {s['voiced_ratio']:5.2f} {str(s['first_s']):>6s} "
                  f"{str(s['last_s']):>6s} {s['longest_run_s']:6.2f} {s['bursts']:4d}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
