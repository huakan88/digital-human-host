#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""把 gen/renoise-*.mp4 的「起手延迟」裁掉，治口型固定偏移。

原理：中转 H3 出片时，开头常有一小段还没开口的准备时间（测出来 0.3~0.7 秒不等）。
画面和它自带音轨是同一条时间线，所以把这**整段**前移同样的秒数，
画面里第一次开口那一帧就正好落在旁白的第一个字上。

做法：用片段自带音轨算起声点（能量首次越过阈值），然后 `-ss 起声点` 重切。
只处理露脸段；素材段不动。
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


def onset_s(p):
    x = decode(p)
    if len(x) == 0:
        return 0.0
    hop = SR // 100
    n = len(x) // hop
    e = np.array([np.sqrt(np.mean(x[i * hop:(i + 1) * hop] ** 2) + 1e-12) for i in range(n)])
    thr = e.max() * 0.12
    idx = np.argmax(e > thr)
    return round(idx / 100, 3)


def main():
    script = json.loads(Path("script.json").read_text(encoding="utf-8-sig"))
    hosts = [s["id"] for s in script if not any(k in s for k in ("cat", "card"))]
    for sid in hosts:
        f = Path("gen") / f"renoise-{sid}.mp4"
        if not f.exists():
            print(f"{sid}: 无片段，跳过")
            continue
        off = onset_s(f)
        if off < 0.08:
            print(f"{sid}: 起手延迟 {off:.2f}s，不用裁")
            continue
        tmp = Path("gen") / f"_trim_{sid}.mp4"
        r = subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-ss", f"{off:.3f}", "-i", str(f),
                            "-c:v", "libx264", "-crf", "18", "-preset", "medium",
                            "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "128k", str(tmp)],
                           capture_output=True, text=True, encoding="utf-8", errors="replace")
        if r.returncode:
            print(f"{sid}: 裁失败 {(r.stderr or r.stdout)[-200:]}")
            continue
        tmp.replace(f)
        print(f"{sid}: 裁掉起手 {off:.2f}s → {Path('gen').joinpath(f'renoise-{sid}.mp4').stat().st_size//1024}KB")


if __name__ == "__main__":
    sys.exit(main())
