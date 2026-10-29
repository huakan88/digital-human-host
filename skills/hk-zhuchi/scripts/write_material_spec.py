#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""把「真实素材从哪来 / 怎么嵌 / 怎么标」写成规范，进两个主持技能。"""
import pathlib

SECTION = '''
## 真实素材：从哪来、怎么嵌、怎么标（2026-10 实测）

图文卡撑得住信息，但**没有真实片段会显得空**。这一节是实测能走通的路子。

### 本机能通 / 不通（先看这张表，别浪费时间）

| 站点 | 可达 | 说明 |
|---|---|---|
| **Bilibili** | ✅ 200 | `yt-dlp` 直接下，最可靠。**28 集的动态设计合集这种＝一堆独立作品** |
| **Contra** | ✅ 200 | 作品页里有 `media.contra.com/...mp4`（Cloudinary 直链），curl 就能拿 |
| Vimeo / TikTok / 抖音 | ✅ 200 | 未深测，`yt-dlp` 大概率可用 |
| Dribbble | ⚠️ 202 | Cloudflare 挑战，页面拿不到 |
| Rive 社区 | ❌ 000 | 不通 |
| **X / Twitter** | ❌ 000 | 官方、fxtwitter、syndication 全不通；`yt-dlp` 也需要先能连上 |
| YouTube | ❌ 000 | 不通 |

> X 上的作品，去**作者自己的作品页**（Contra / 个人站 / Dribbble）拿原始 mp4，
> 往往比从 X 转存质量更好。（例：Owl Loading 在 contra.com 就有 1600px 原片）

### 抓素材的最小命令

```bash
# B站（最省事）
yt-dlp -f "bv*[height<=720]+ba/b[height<=720]" --max-filesize 80M -o "clips/%(id)s.%(ext)s" "https://www.bilibili.com/video/BVxxxx"

# Contra 这类作品页：先抓 html 再抠直链
curl.exe -s -A "Mozilla/5.0" "https://contra.com/p/xxxx" -o page.html
# 然后 grep media.contra.com/video/upload/...mp4，挑 w_1600 那档
```
> PowerShell 里 `curl` 是 `Invoke-WebRequest` 的别名，**必须写 `curl.exe`**。

### 嵌进片子

| 需求 | 用什么 beat |
|---|---|
| 单纯展示作品（带信源角标） | `clip` |
| **文字压在画面上** | `cliptext`（本仓库补丁 `patch_koubo_cliptext.py` 已加：视频铺满压暗 + 大字居中 + 副标题） |

```bash
python patch_koubo_cliptext.py <koubo 工程>    # 模板与工程各跑一次
```

### 挑 `from` 起始秒（最容易白干的一步）

同一个素材里，有的时间点是大片留白/黑场/转场。**必须先抽帧看，再写 from**：

```bash
for t in 2 8 14 22 30 38; do ffmpeg -v error -y -ss $t -i clip.mp4 -frames:v 1 -vf scale=300:-2 probe_$t.png; done
```
拼成对照图挑一帧有内容的，再把它的时间写进 beats。

> ⚠️ **改 `from` 不要用字符串替换。** 本仓库踩过：把 `"from": 1` 去替换，
> 命中了 `"from": 18` 的**前缀**，结果变成 `"from": 308`（超出片长）→ 画面全灰，
> 查了半天。改数值一律**整行重写**，或者用 JSON 结构化编辑。

### 署名（硬性）
每条真实片段都要在画面上带：
- `tag`：`真实作品` / `我的作品`
- `src_label`：**平台 · 作品名 · 作者 · 编号**（如 `Bilibili · Ravie 动态设计合集 · BV1wC4y1M7y6`）

### 自有素材
用户自己的作品直接进 `public/clips/`，`tag` 写 `我的作品`，`src_label` 写清项目名。
用户自己的片子放进片子里是**最强的可信度**，别只当素材，要在文案里点名"这是我自己做的"。

'''

TARGETS = [
    pathlib.Path(r"E:\dsh-agents\skills\hk-zhuchi\SKILL.md"),
    pathlib.Path(r"E:\dsh-agents\skills\vivi-zhuchi\SKILL.md"),
]


def main():
    for p in TARGETS:
        t = p.read_text(encoding="utf-8")
        if "真实素材：从哪来" in t:
            print(f"· {p.parent.name} 已有")
            continue
        anchor = "## 工作流"
        block = SECTION.strip() + "\n\n"
        if anchor in t:
            t = t.replace(anchor, block + anchor, 1)
        else:
            t = t.rstrip() + "\n\n" + block
        p.write_text(t, encoding="utf-8")
        print(f"✓ {p.parent.name}/SKILL.md 写入真实素材规范")


if __name__ == "__main__":
    main()
