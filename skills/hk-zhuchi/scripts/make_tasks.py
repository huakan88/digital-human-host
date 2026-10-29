#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""生成本期任务表：数字人（人类主播）逐段任务 + 猫画面素材对应关系。

提示词照抄本机 H3 的约定：<Picture 1> 绑参考图、<Audio 1> 绑配音，台词不写进提示词。
每段可以单独指定分辨率（开场大图 9:16，小窗 2:3）和手部/身体动作要求。
"""
import json
import math
import os
import re
import sys
from pathlib import Path

PROJ = Path(os.environ.get("HK_PROJECT", Path.cwd())).resolve()
SKILL = Path(os.environ.get("HK_PRESET", Path(__file__).resolve().parent.parent)).resolve()
P = json.loads((SKILL / "persona" / "persona.json").read_text(encoding="utf-8"))
REF = P["renoise"]["reference_material"]

# 提示词模板全部来自 persona.json（主持预设的唯一真相）。
# 以前把主持外貌写死在这里，导致换预设时 H3 跟着「文字」而不是「参考图」生成，
# 出来的还是原来那个人。下面只保留没被 persona 覆盖的通用部分。
LOOK = ""


def build_prompt(P, big):
    """用 persona 的 prompt_template / prompt_big 组装 H3 提示词。"""
    base = (P.get("prompt_big") if big else None) or P["prompt_template"]
    acts = P.get("acts", {})
    return base.format(purpose="explaining clearly", act=acts.get("full", "warm eye contact"))


def main():
    S = json.loads((PROJ / "script.json").read_text(encoding="utf-8"))
    cps = float(P["voice"]["speed_cps"])          # 本机克隆音色的实测语速（字/秒）
    max_sec = int(P["model"]["max_seconds"])
    tasks = []
    for i, s in enumerate(S):
        n = len(re.sub(r"[\s，。、：；！？,.:;!?“”]", "", s["t"]))
        dur = max(4, min(max_sec, math.ceil(n / cps + 1.0)))
        if dur > max_sec:
            print(f"! {s['id']} 约 {n/cps+1:.0f} 秒，超过 H3 单段上限 {max_sec} 秒，拆成两段")
        tasks.append({
            "model": P["model"]["name"], "kind": "video", "ratio": "9:16",
            "resolution": "720p", "duration": dur, "label": f"口播 {s['id']}",
            "idempotencyKey": f"dh-cat-{s['id']}-v1",
            "references": [{"ref": REF, "role": "reference_image"}],
            "prompt": build_prompt(P, bool(s.get("big"))),
            "prompt_override": build_prompt(P, bool(s.get("big"))),
            # 出画分辨率：统一 576x1024。低分辨率（384x576）会让脸崩、鼻头变大、口型发糊。
            "size": s.get("size") or [576, 1024],
            "line": s["t"], "cat": s.get("cat", ""), "card": s.get("card", ""),
        })
    out = PROJ / "tasks.json"
    out.write_text(json.dumps(tasks, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"✓ {out}  {len(tasks)} 段")


if __name__ == "__main__":
    main()
