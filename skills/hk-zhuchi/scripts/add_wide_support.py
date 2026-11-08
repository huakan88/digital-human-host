#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""给两个主持技能加横版 16:9 支持（约束完全一致）。

改四处：
  1. build_media.py   加 --wide → W,H = 1920×1080
  2. make_backdrop.py 支持传宽高
  3. make_tasks.py    ratio 跟着 size 走；有 prompt_template_wide 就用横版提示词
  4. make_host_wrap.py 加 --wide → 切窗口时用 1920×1080
可重复执行。
"""
import pathlib
import re

BASE = pathlib.Path(r"E:\dsh-agents\skills\hk-zhuchi\scripts")


def patch_build_media():
    p = BASE / "build_media.py"
    t = p.read_text(encoding="utf-8")
    old = "W, H, FPS = 1080, 1920, 30"
    if "WIDE = " in t:
        print("· build_media 已有 --wide")
        return
    t = t.replace(old,
                  "# --wide：横版 16:9（1920×1080）。其它约束（素材优先/口型验收）完全一样。\n"
                  "WIDE = \"--wide\" in sys.argv\n"
                  "W, H, FPS = (1920, 1080, 30) if WIDE else (1080, 1920, 30)", 1)
    p.write_text(t, encoding="utf-8")
    print("✓ build_media.py 支持 --wide")


def patch_backdrop():
    p = BASE / "make_backdrop.py"
    t = p.read_text(encoding="utf-8")
    if "sys.argv[2]" in t and "W, H = " in t and "WIDE" in t:
        print("· make_backdrop 已支持宽高")
        return
    t = t.replace("W, H = 1080, 1920", "W, H = (int(sys.argv[2]), int(sys.argv[3])) if len(sys.argv) > 3 else (1080, 1920)", 1)
    p.write_text(t, encoding="utf-8")
    print("✓ make_backdrop.py 支持传宽高（python make_backdrop.py \"\" 1920 1080）")


def patch_make_tasks():
    p = BASE / "make_tasks.py"
    t = p.read_text(encoding="utf-8")
    if "prompt_template_wide" in t:
        print("· make_tasks 已支持横版提示词")
        return
    # ratio 跟着 size
    t = t.replace('"model": P["model"]["name"], "kind": "video", "ratio": "9:16",',
                  '"model": P["model"]["name"], "kind": "video",\n'
                  '            "ratio": "16:9" if (s.get("size") or [576, 1024])[0] > (s.get("size") or [576, 1024])[1] else "9:16",', 1)
    # 横版提示词
    t = t.replace('''def build_prompt(P, big):
    """用 persona 的 prompt_template / prompt_big 组装 H3 提示词。"""
    base = (P.get("prompt_big") if big else None) or P["prompt_template"]''',
'''def build_prompt(P, big, size=None):
    """用 persona 的 prompt_template / prompt_big 组装 H3 提示词。
    横版（宽>高）优先用 *_wide 那套模板。"""
    wide = bool(size) and size[0] > size[1]
    base = None
    if wide:
        base = (P.get("prompt_big_wide") if big else None) or P.get("prompt_template_wide")
    if not base:
        base = (P.get("prompt_big") if big else None) or P["prompt_template"]''', 1)
    t = t.replace('"prompt": build_prompt(P, bool(s.get("big"))),',
                  '"prompt": build_prompt(P, bool(s.get("big")), s.get("size")),', 1)
    t = t.replace('"prompt_override": build_prompt(P, bool(s.get("big"))),',
                  '"prompt_override": build_prompt(P, bool(s.get("big")), s.get("size")),', 1)
    p.write_text(t, encoding="utf-8")
    print("✓ make_tasks.py 支持横版 ratio 与提示词")


def patch_host_wrap():
    p = BASE / "make_host_wrap.py"
    t = p.read_text(encoding="utf-8")
    if "--wide" in t:
        print("· make_host_wrap 已支持 --wide")
        return
    t = t.replace("W, H, FPS = 1080, 1920, 30",
                  "WIDE = \"--wide\" in sys.argv\n"
                  "# --wide：切横版窗口用 1920×1080（build_media 也要用 --wide 出主画面）\n"
                  "W, H, FPS = (1920, 1080, 30) if WIDE else (1080, 1920, 30)", 1)
    p.write_text(t, encoding="utf-8")
    print("✓ make_host_wrap.py 支持 --wide")


if __name__ == "__main__":
    patch_build_media()
    patch_backdrop()
    patch_make_tasks()
    patch_host_wrap()
    for f in ("build_media.py", "make_backdrop.py", "make_tasks.py", "make_host_wrap.py"):
        import ast
        ast.parse((BASE / f).read_text(encoding="utf-8"))
    print("✓ 四个脚本语法检查通过")
