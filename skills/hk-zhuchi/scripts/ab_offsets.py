#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""A/B/C 对比片：把同一段口播按 -6 帧 / 0 / +6 帧三个偏移并排做出来给人眼挑。

自动相关性分辨不出 ±100ms，与其猜，不如让用户看三条选一条。

用法：python ab_offsets.py <片段> <配音wav> <输出mp4> [偏移帧数,默认6]
"""
import subprocess
import sys
from pathlib import Path

SKILL = Path(__file__).resolve().parent


def run(args):
    subprocess.run(args, check=True, capture_output=True)


def main():
    clip = Path(sys.argv[1])
    wav = Path(sys.argv[2])
    out = Path(sys.argv[3])
    k = int(sys.argv[4]) if len(sys.argv) > 4 else 6

    dur = float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                                "-of", "csv=p=0", str(clip)], capture_output=True, text=True).stdout.strip())
    parts = []
    variants = [
        ("A  画面往前 0.2 秒（嘴更早）", +k, (250, 200, 60)),
        ("B  原始（不偏移）", 0, (140, 255, 160)),
        ("C  画面往后 0.2 秒（嘴更晚）", -k, (120, 200, 255)),
    ]
    tmp = Path("_ab")
    tmp.mkdir(exist_ok=True)

    for i, (label, shift, color) in enumerate(variants):
        # shift>0：画面提前（先播后面几帧）
        # shift<0：画面延后
        vf = "scale=1920:1080:flags=lanczos,fps=30"
        src_v = clip
        off = 0.0
        if shift > 0:
            keep = dur - shift / 30.0
            vf += f",trim=start_frame={shift},setpts=PTS-STARTPTS"
            src = [str(clip)]
        else:
            off = -shift / 30.0
            src = [str(clip)]

        seg = tmp / f"v{i}.mp4"
        chain = f"[0:v]fps=30,scale=1920:1080:flags=lanczos"
        if shift > 0:
            chain += f",trim=start_frame={shift},setpts=PTS-STARTPTS"
        chain += f",trim=duration={dur:.3f},setpts=PTS-STARTPTS"
        if off > 0:
            chain += f",tpad=start_duration={off:.3f}:start_mode=clone,trim=duration={dur:.3f}"
        chain += ",drawtext=fontfile='C\\:/Windows/Fonts/msyhbd.ttc':text='" + label + "':fontcolor=white:fontsize=40:x=(w-text_w)/2:y=h-110:box=1:boxcolor=black@0.65:boxborderw=14"
        chain += "[v]"
        achain = f"[1:a]atrim=duration={dur:.3f},asetpts=PTS-STARTPTS[a]"
        run(["ffmpeg", "-v", "error", "-y", "-i", str(clip), "-i", str(wav),
             "-filter_complex", f"{chain};{achain}", "-map", "[v]", "-map", "[a]",
             "-c:v", "libx264", "-crf", "20", "-pix_fmt", "yuv420p", "-c:a", "aac", str(seg)])
        parts.append(seg)

    lst = tmp / "list.txt"
    lst.write_text("".join(f"file '{p.resolve().as_posix()}'\n" for p in parts), encoding="utf-8")
    run(["ffmpeg", "-v", "error", "-y", "-f", "concat", "-safe", "0", "-i", str(lst),
         "-c:v", "libx264", "-crf", "20", "-pix_fmt", "yuv420p", "-c:a", "aac", str(out)])
    print(f"✓ {out}  （{dur:.1f}×3 = {dur*3:.1f}s，三段同一句，只看嘴和音的先后）")


if __name__ == "__main__":
    main()
