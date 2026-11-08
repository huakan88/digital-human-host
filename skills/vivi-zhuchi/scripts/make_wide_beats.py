#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""把竖版那套 beat 定义转成 koubo 横版模板要的 beats.json。

横版模板（koubo-video/templates/wide）靠 `--props='beats.json'` 驱动：
  {beats:[{from,dur,card,props,crumb?,credit?,tab?,subs:[{from,text}]}], tabs?, narration, host?}

这个脚本读：
  - public/episode.json（make_host_wrap 产出：每段的 sec/text）
  - beats_wide.json（可选，按段 id 写 beat；没有就自动按 text 出一张 H1）
  - gen/host_segs.json（哪些段是数字人窗口）
产出：
  - koubo 横版工程 public/beats.json（含 host 窗口，帧为单位）

用法：python make_wide_beats.py <koubo 横版工程目录> [--tabs "甲|乙|丙"]
"""
import json
import sys
from pathlib import Path

FPS = 30

# 竖版 beat → 横版 card 的映射
MAP = {
    "stat": lambda b: ("Stat", {"big": b.get("big", ""), "title": b.get("title", ""),
                                "sub": b.get("sub", ""), "sub2": b.get("src_label", "")}),
    "bars": lambda b: ("BarChart", {"title": b.get("title", ""), "unit": (b.get("items") or [{}])[0].get("u", ""),
                                    "max": b.get("max"),
                                    "bars": [{"label": i.get("l", ""), "value": i.get("v", 0)} for i in (b.get("items") or [])],
                                    "src_label": b.get("src_label", "")}),
    "check": lambda b: ("Checklist", {"title": b.get("title", ""), "items": b.get("items", [])}),
    "rank": lambda b: ("NumberedList", {"items": b.get("items", []),
                                        "reveal": [10 + i * 20 for i in range(len(b.get("items", [])))]}),
    "clip": lambda b: ("MediaCard", {"src": b.get("src", ""), "video": True,
                                     "caption": b.get("src_label", ""), "fit": "contain"}),
    "cliptext": lambda b: ("MediaCard", {"src": b.get("src", ""), "video": True,
                                         "caption": b.get("src_label", ""), "fit": "contain"}),
    "h1": lambda b: ("H1", {"text": b.get("text", b.get("title", "")), "sub": b.get("sub", "")}),
    "end": lambda b: ("EndCard", {"title": b.get("title", ""), "line": b.get("sub", "")}),
}


def main():
    koubo = Path(sys.argv[1]).resolve()
    tabs = None
    if "--tabs" in sys.argv:
        tabs = sys.argv[sys.argv.index("--tabs") + 1].split("|")

    ep = json.loads((koubo / "public" / "episode.json").read_text(encoding="utf-8"))
    segs = ep["segs"]

    beats_src = {}
    bp = koubo / "beats_wide.json"
    if bp.exists():
        beats_src = json.loads(bp.read_text(encoding="utf-8"))

    host_segs = []
    hs = koubo.parent / "gen" / "host_segs.json"
    if hs.exists():
        host_segs = json.loads(hs.read_text(encoding="utf-8"))

    # 帧栅格是唯一权威：优先用 build_media 产出的 public/timeline.json，
    # 否则每段自己按 sec+0.25 重算会和主画面错开（踩过：窗口 4.47s vs 4.23s）
    tl = {}
    tp = koubo.parent / "public" / "timeline.json"
    if tp.exists():
        for x in json.loads(tp.read_text(encoding="utf-8")):
            tl[x["id"]] = (x["start"], x["end"])
    beats = []
    f = 0
    for i, s in enumerate(segs):
        if s["id"] in tl:
            a, b = tl[s["id"]]
            f = round(a * FPS)
            dur = max(1, round(b * FPS) - f)
        else:
            dur = max(1, round((s.get("sec") or 0) * FPS + 0.25 * FPS))
            if i == len(segs) - 1:
                dur = max(1, round((segs[i].get("sec") or 0) * FPS))
        spec = beats_src.get(s["id"])
        if spec:
            card = spec["card"]
            props = spec.get("props", {})
        else:
            card, props = "H1", {"text": s.get("text", "")}
        beats.append({"from": f, "dur": dur, "card": card, "props": props,
                      "credit": spec.get("credit") if spec else None,
                      "subs": [{"from": f, "text": s.get("text", "")}]})
        f += dur

    # 数字人窗口（帧）：连续的露脸段合成一个窗口
    wins = []
    cur = None
    for i, s in enumerate(segs):
        b = beats[i]
        if s["id"] in host_segs:
            if cur and cur["to"] == b["from"]:
                cur["to"] = b["from"] + b["dur"]
            else:
                cur = {"from": b["from"], "to": b["from"] + b["dur"]}
                wins.append(cur)
        else:
            cur = None

    out = {"beats": beats, "tabs": tabs, "narration": "narration.wav"}
    if wins:
        out["host"] = {"src": "main.mp4", "windows": wins}

    (koubo / "public" / "beats.json").write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"✓ beats.json：{len(beats)} 拍，{len(wins)} 个数字人窗口（帧）")
    for w in wins:
        print(f"   窗口 {w['from']/FPS:6.2f}-{w['to']/FPS:6.2f}s")


if __name__ == "__main__":
    main()
