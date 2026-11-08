#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""静音帧检验：在配音的静音处，嘴必须是闭的。这是唯一没有歧义的口型判据。

用法：python silence_check.py <配音 wav> <对应视频> [输出前缀]

做法：
  1. ffmpeg silencedetect 找出静音区间
  2. 在每段静音的正中间取一帧
  3. 把这些帧的嘴部裁切拼成一条，人眼一看就知道闭没闭
"""
import re
import subprocess
import sys
import tempfile
from pathlib import Path

BOX = "0.40,0.40,0.60,0.56"
CELL = 160


def main():
    wav = Path(sys.argv[1])
    video = Path(sys.argv[2])
    tag = sys.argv[3] if len(sys.argv) > 3 else "check"

    r = subprocess.run(["ffmpeg", "-v", "error", "-i", str(wav), "-af",
                        "silencedetect=n=-33dB:d=0.10", "-f", "null", "-"],
                       capture_output=True, text=True)
    starts = [float(x) for x in re.findall(r"silence_start: ([\d.]+)", r.stderr)]
    ends = [float(x) for x in re.findall(r"silence_end: ([\d.]+)", r.stderr)]
    mids = [(a + (b if i < len(ends) else a + 0.3)) / 2 for i, a in enumerate(starts)]

    if not mids:
        print("这条配音里没有明显静音（>100ms），换别的判据")
        return

    print(f"{wav.name}: 静音段 {len(mids)} 处 → 这些时刻嘴必须是闭的")
    print("  时刻：" + ", ".join(f"{m:.2f}s" for m in mids[:8]))

    with tempfile.TemporaryDirectory() as td:
        imgs = []
        for i, t in enumerate(mids[:8]):
            out = Path(td) / f"s{i}.png"
            subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", f"{t:.3f}", "-i", str(video),
                            "-frames:v", "1", "-vf",
                            f"scale=1920:1080,crop=iw*0.2:ih*0.16:iw*0.40:ih*0.40,scale={CELL}:{CELL}",
                            str(out)], capture_output=True)
            if out.exists():
                imgs.append((t, out))

    from PIL import Image, ImageDraw, ImageFont
    fnt = ImageFont.truetype(r"C:\Windows\Fonts\msyhbd.ttc", 20)
    W = len(imgs) * (CELL + 8)
    out = Image.new("RGB", (max(W, 600), CELL + 34), (16, 16, 20))
    d = ImageDraw.Draw(out)
    d.text((4, 2), f"{video.name} 静音时刻的嘴（应当闭合）", font=fnt, fill=(255, 220, 120))
    for i, (t, p) in enumerate(imgs):
        out.paste(Image.open(p).convert("RGB"), (i * (CELL + 8), 30))
        d.text((i * (CELL + 8) + 3, 30 + CELL), f"{t:.2f}s", font=fnt, fill=(190, 190, 200))
    out.save(f"silence_{tag}.png")
    print(f"→ silence_{tag}.png")


if __name__ == "__main__":
    main()
