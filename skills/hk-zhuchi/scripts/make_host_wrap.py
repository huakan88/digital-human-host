#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""把数字人工程的产物接进 koubo-video 的工程：片头片尾 + 旁白 + 分段表。

数字人工程（vivi主持 / hk主持）产出：
  public/main.mp4   全屏数字人视频（已逐段对齐口型）
  narration.wav     旁白总轨
  edit/src/tl.json  每段的起止时间

这里做的事：
  1. 从 main.mp4 切出 [0, intro] 和 [总长-outro, 总长] → <koubo>/public/host/{intro,outro}.mp4
  2. 拷 narration.wav → <koubo>/public/narration.wav
  3. 写 <koubo>/public/host/host.json（片头片尾秒数）
  4. 写 <koubo>/public/episode.json（分段表：起止 + 台词，给 beats 排布用）
  5. 顺带打印 Weekly.tsx 需要替换的 RAW / TEXT 两行常量

用法：
  python make_host_wrap.py --project <数字人工程> --koubo <koubo 工程> --intro 12 --outro 9
"""
import argparse
import json
import shutil
import subprocess
from pathlib import Path

W, H, FPS = 1080, 1920, 30


def dur(p):
    out = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                          "-of", "csv=p=0", str(p)], capture_output=True, text=True).stdout.strip()
    return float(out or 0)


def cut(src, out, start, length):
    out.parent.mkdir(parents=True, exist_ok=True)
    # -g 1：全关键帧。Remotion 的合成器按帧 seek，窗口片段如果是长 GOP，
    # 会偶发 "Compositor error: No frame found at position ..." 直接渲染失败。
    subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-ss", f"{start:.3f}", "-i", str(src),
                    "-t", f"{length:.3f}", "-vf", f"scale={W}:{H}:flags=lanczos,fps={FPS}",
                    "-an", "-c:v", "libx264", "-crf", "18", "-preset", "medium", "-g", "1",
                    "-pix_fmt", "yuv420p", str(out)], check=True)
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--project", required=True, help="数字人工程目录")
    ap.add_argument("--koubo", required=True, help="koubo-video 的 Remotion 工程目录")
    ap.add_argument("--intro", type=float, default=12)
    ap.add_argument("--outro", type=float, default=9)
    ap.add_argument("--windows", default="", help='多窗口："0-8.65,32.2-42.5"（给了就用它，忽略 intro/outro）')
    ap.add_argument("--host-segs", default="", help='按段 id 定窗口，如 "s1,s2,s8,s9,s15,s16"；'
                                                  '连续段自动并成一个窗口，时间取自 public/timeline.json（精确）')
    a = ap.parse_args()

    P = Path(a.project).resolve()
    K = Path(a.koubo).resolve()
    main_mp4 = P / "public" / "main.mp4"
    narr = P / "narration.wav"
    tl = P / "edit" / "src" / "tl.json"
    for f in (main_mp4, narr, tl):
        if not f.exists():
            raise SystemExit(f"缺文件：{f}")

    total = dur(narr)
    hostdir = K / "public" / "host"
    hostdir.mkdir(parents=True, exist_ok=True)

    intro_len = outro_len = 0.0
    wins = []
    if a.host_segs.strip():
        tl_file = P / "public" / "timeline.json"
        if not tl_file.exists():
            raise SystemExit("缺 public/timeline.json（先跑 build_media.py）")
        _rows = json.loads(tl_file.read_text(encoding="utf-8"))
        tlmap = {x["id"]: x for x in _rows}
        order = [x["id"] for x in _rows]
        want = [x.strip() for x in a.host_segs.split(",") if x.strip()]
        idx = sorted(order.index(w) for w in want if w in order)
        run = []
        for k, i in enumerate(idx):
            if run and i == run[-1] + 1:
                run.append(i)
            else:
                if run:
                    wins.append((tlmap[order[run[0]]]["start"], tlmap[order[run[-1]]]["end"]))
                run = [i]
        if run:
            wins.append((tlmap[order[run[0]]]["start"], tlmap[order[run[-1]]]["end"]))
        print(f"· 按段定窗口 {len(wins)} 个（取自 timeline.json 的帧栅格时间）")
    elif a.windows.strip():
        for part in a.windows.split(","):
            part = part.strip()
            if "-" not in part:
                continue
            x, y = part.split("-", 1)
            wins.append((float(x), float(y)))
    else:
        intro_len = min(a.intro, total * 0.5)
        outro_len = min(a.outro, total * 0.5)
        wins = [(0.0, intro_len), (total - outro_len, total)]
    win_objs = []
    for k, (st, en) in enumerate(wins, 1):
        name = f"w{k}.mp4"
        cut(main_mp4, hostdir / name, st, en - st)
        win_objs.append({"src": f"host/{name}", "from": round(st, 2), "to": round(en, 2)})
        print(f"✓ 窗口 {k}: {st:.2f}-{en:.2f}s → host/{name}")

    shutil.copy(narr, K / "public" / "narration.wav")
    print(f"✓ 旁白 → {K / 'public' / 'narration.wav'}（{total:.2f}s）")

    cfg = {"windows": win_objs}
    if not a.windows.strip():
        cfg["intro"] = {"src": "host/w1.mp4", "sec": round(wins[0][1], 2)}
        cfg["outro"] = {"src": "host/w2.mp4", "sec": round(wins[1][1] - wins[1][0], 2)}
    (hostdir / "host.json").write_text(json.dumps(cfg, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print("✓ host.json 已写")

    # 分段表：给 koubo 排 beats 用
    data = json.loads(tl.read_text(encoding="utf-8"))
    S = json.loads((P / "script.json").read_text(encoding="utf-8"))
    segs = []
    for i, seg in enumerate(data["segs"]):
        text = S[i]["t"] if i < len(S) else ""
        segs.append({"i": i, "id": S[i]["id"] if i < len(S) else f"s{i+1}",
                     "start": round(seg["start"], 3), "end": round(seg["end"], 3),
                     "sec": round(seg["end"] - seg["start"], 3), "text": text})
    (K / "public" / "episode.json").write_text(
        json.dumps({"total": round(total, 3), "intro": intro_len, "outro": outro_len,
                    "segs": segs}, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(f"✓ episode.json（{len(segs)} 段）")

    raw = ",".join(f"{s['sec']:.6f}" for s in segs)
    texts = ",".join(json.dumps(s["text"], ensure_ascii=False) for s in segs)
    print("\n把 Weekly.tsx 里这两行换成（RAW 用秒，PARTS 会自动 /1.04，所以这里已乘好）：")
    print(f"const RAW = [{', '.join(f'{s[chr(115)+chr(101)+chr(99)] * 1.04:.6f}' for s in segs)}];")
    print(f"const TEXT: string[] = [{texts}];")
    print(f"// 共 {len(segs)} 段，总长 {total:.2f}s；露脸窗口 {len(wins)} 个")


if __name__ == "__main__":
    main()
