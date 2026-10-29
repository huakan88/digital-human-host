#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""把 koubo 模板顶栏的硬编码标题改成可配置（HUD_TITLE / HUD_SUB）。

模板里原本写死了「宠物快讯 · 宠物产业 · 兽医 · 干细胞 · 2026.10」和「N / 17」，
换一期就会露出上一期的字样。这个脚本把它改成常量 + PARTS.length，可重复执行。

用法：python patch_koubo_hud.py <koubo 工程或模板目录> ["主标题"] ["副标题"]
"""
import re
import sys
from pathlib import Path

DEFAULT_TITLE = "X 上的动效"
DEFAULT_SUB = "2026 年，卷的是可玩性"


def main():
    proj = Path(sys.argv[1]).resolve()
    title = sys.argv[2] if len(sys.argv) > 2 else DEFAULT_TITLE
    sub = sys.argv[3] if len(sys.argv) > 3 else DEFAULT_SUB
    p = proj / "src" / "Weekly.tsx"
    t = p.read_text(encoding="utf-8")

    # 1) 硬编码标题 → 常量
    m = re.search(r"(<div style=\{\{color: '#fff', fontWeight: 700, fontSize: 34[^>]*>)(.*?)(</div>)", t)
    if m and "HUD_TITLE" not in m.group(2):
        t = t.replace(m.group(0),
                      m.group(1).replace(">", ">") +
                      "{HUD_TITLE} <span style={{color: COLORS.textDim, fontWeight: 400, fontSize: 26, marginLeft: 18}}>{HUD_SUB}</span>"
                      + m.group(3), 1)
        print("✓ 顶栏标题改成 HUD_TITLE / HUD_SUB")
    elif "HUD_TITLE" in t:
        print("· 顶栏已经是常量")
    else:
        print("⚠ 没匹配到顶栏标题")

    # 2) 段数写死 → PARTS.length
    t2 = re.sub(r"\{String\(seg \+ 1\)\.padStart\(2, '0'\)\} / \d+",
                "{String(seg + 1).padStart(2, '0')} / {PARTS.length}", t)
    if t2 != t:
        print("✓ 段数改成 PARTS.length")
    t = t2

    # 3) 常量（不存在就加在 RAW 前面）
    if "const HUD_TITLE" not in t:
        t = t.replace("const RAW = [", f"// 顶栏标题（每期改这两行）\nconst HUD_TITLE = '{title}';\nconst HUD_SUB = '{sub}';\nconst RAW = [", 1)
        print(f"✓ 写入 HUD_TITLE={title}")
    else:
        t = re.sub(r"const HUD_TITLE = '[^']*';", f"const HUD_TITLE = '{title}';", t, count=1)
        t = re.sub(r"const HUD_SUB = '[^']*';", f"const HUD_SUB = '{sub}';", t, count=1)
        print(f"✓ 更新 HUD_TITLE={title}")

    p.write_text(t, encoding="utf-8")


if __name__ == "__main__":
    main()
