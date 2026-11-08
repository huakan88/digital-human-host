#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""把「横版 16:9」写进两个主持技能，约束与竖版完全一致。"""
import pathlib

SECTION = '''
## 横版 16:9（**约束与竖版完全一致**）

竖版 9:16 和横版 16:9 是同一套规范，只是画幅不同。**素材优先、口型强制项、验收流程一条都不减。**

### 出画与装配（本仓库已支持 --wide）

```bash
# 1) 稿子里每段用横版分辨率（1024×576 是 32 的倍数，H3 能出）
#    script.json: "size": [1024, 576]
python scripts/make_tasks.py            # ratio 自动跟 size 走（16:9），
                                       # 提示词自动切 persona 的 prompt_template_wide

# 2) 主画面（1920×1080）
python scripts/build_media.py --full --wide

# 3) 口型验收（同竖版，嘴框按横版构图调）
python scripts/sync_pic.py <片段> <起始秒> 12 "0.30,0.30,0.70,0.55"

# 4) 切数字人窗口也用 --wide
python scripts/make_host_wrap.py --project . --koubo <横版工程> --host-segs s1,s8 --wide
```

横版提示词已经写进两个 persona（`prompt_template_wide` / `prompt_big_wide`），
要点：**中景、腰部以上、人物居中留两侧空地、头顶留白**，不要手机自拍构图。

### 中期包装换成 koubo 横版模板

```bash
cp -r <koubo-video>/templates/wide ./koubo          # 横版模板
python scripts/patch_koubo_wide_host.py ./koubo     # 接入数字人窗口层（host prop）
python scripts/make_wide_beats.py ./koubo --tabs "现象|证据|规律|结论"
cd koubo && npx remotion render src/index.ts Wide out/wide.mp4 --props='public/beats.json'
```

横版模板的卡片库很全（`components.tsx`）：`H1` / `Stat` / `BarChart` / `Checklist` /
`NumberedList` / `MediaCard`（放真实片段）/ `Timeline` / `Compare` / `QuoteCard` / `EndCard` …
`make_wide_beats.py` 已经把竖版那套 beat（stat/bars/check/rank/clip/cliptext）映射过去了；
想用别的卡片就在 `beats_wide.json` 里按段 id 直接写 `{card, props}`。

**数字人窗口**用 `beats.json` 里的 `host` 字段：
```json
"host": {"src": "main.mp4", "windows": [{"from": 0, "to": 87}]}
```
窗口内的拍会**只留字幕、卡片让位**，露出下面的数字人主画面 —— 和竖版同一个思路。

### 横竖版差异（只有这些）

| 项 | 竖版 9:16 | 横版 16:9 |
|---|---|---|
| 出画尺寸 | 576×1024（或 1080p） | 1024×576 |
| 成片尺寸 | 1080×1920 | 1920×1080 |
| 构图提示词 | 手机自拍、手臂伸向镜头 | 中景、腰以上、两侧留空、头顶留白 |
| 包装模板 | `koubo-video/remotion-template` | `koubo-video/templates/wide` |
| beat 定义 | `patch_koubo_episode.py` 写进 Weekly.tsx | `beats_wide.json` + `make_wide_beats.py` |
| 露脸位置 | 可全屏，也可缩成左下角圆形小窗 | 一般全屏出镜，卡片让位 |

**素材密度、单镜头一次生成、口型验收、署名——全部照旧。**

'''

TARGETS = [
    pathlib.Path(r"E:\dsh-agents\skills\hk-zhuchi\SKILL.md"),
    pathlib.Path(r"E:\dsh-agents\skills\vivi-zhuchi\SKILL.md"),
]


def main():
    for p in TARGETS:
        t = p.read_text(encoding="utf-8")
        if "## 横版 16:9" in t:
            print(f"· {p.parent.name} 已有横版章节")
            continue
        anchor = "## 工作流"
        block = SECTION.strip() + "\n\n"
        if anchor in t:
            t = t.replace(anchor, block + anchor, 1)
        else:
            t = t.rstrip() + "\n\n" + block
        p.write_text(t, encoding="utf-8")
        print(f"✓ {p.parent.name}/SKILL.md 写入横版章节")


if __name__ == "__main__":
    main()
