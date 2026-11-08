#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""把这期（万圣节 横版）实测跑通的完整流程写进两个技能。"""
import pathlib

ADD = '''
### 横版完整流程（2026-10-29 实跑：万圣节这期，77 秒成片）

按这个顺序走，一条命令都不多余：

```bash
# 1) 稿子：每段 size 写 [1024, 576]，一段一句，≤45 字
python <skill>/scripts/make_tasks.py            # ratio 自动 16:9，提示词自动切 *_wide

# 2) 配音（豆包 Vivi，20 段约 1 分钟）
python voice_doubao.py

# 3) 出画：露脸段一段一次生成，用 gen/host_segs.json 指定
python <skill>/scripts/backend.py run tasks.json --backend local --only s1,s5,s16,s20

# 4) 主画面（1920×1080）+ 底版
python <skill>/scripts/make_backdrop.py "" 1920 1080
python <skill>/scripts/build_media.py --full --wide --no-asr

# 5) 横版包装工程
cp -r <koubo-video>/templates/wide ./koubo
python <skill>/scripts/patch_koubo_wide_host.py     ./koubo   # 数字人窗口层
python <skill>/scripts/patch_koubo_wide_mediatext.py ./koubo  # MediaText：素材铺底 + 大字
python <skill>/scripts/make_host_wrap.py --project . --koubo ./koubo --host-segs s1,s5,s16,s20 --wide
python <skill>/scripts/make_wide_beats.py ./koubo --tabs "现象|起源|结论"

# 6) 渲染
cd koubo && npx remotion render src/index.ts Wide out/wide.mp4 --props=public/beats.json
```

**两个新东西（这期加的）**

1. **`MediaText` 卡**（`patch_koubo_wide_mediatext.py`）
   横版模板原来只有白底排版卡，没有「文字压素材」。这个卡 = 素材铺满 + 压暗 + 大字居中，
   等价于竖版的 `cliptext`。参数：`{src, video?, from?, title, sub?, dim?}`。

2. **`make_wide_beats.py` 现在读 `public/timeline.json`**
   以前它自己按 `sec + 0.25` 逐段重算时长，结果数字人窗口和主画面对不上
   （实测 0-4.47s vs 主画面 0-4.23s，最后一段甚至超到 81.7s）。
   **帧栅格是唯一权威**，所有 beat 的 `from/dur` 都必须从 timeline.json 取。

### 拿「别人的科普片」当素材库（这期最省事的一招）

找到一条画面配得好的科普片（例：B站 `BV17e411R7nc`「5分钟介绍万圣节的来历」），
**按时间轴抽帧拆成十几个独立画面**，一格讲一个点，比自己找图快得多：

```bash
for t in 0 20 45 70 95 120 145 170 195 220 245 270 295; do
  ffmpeg -v error -y -ss $t -i ref.mp4 -frames:v 1 -vf "scale=300:-2" ex_$t.png
done
# 拼成对照图挑画面，再把选中的图复制进 koubo/public/clips/
```
署名写 `Bilibili · 作品名 · BV号`。**抽帧看清内容再配文案**，别凭时间猜。

'''

TARGETS = [
    pathlib.Path(r"E:\dsh-agents\skills\hk-zhuchi\SKILL.md"),
    pathlib.Path(r"E:\dsh-agents\skills\vivi-zhuchi\SKILL.md"),
]


def main():
    for p in TARGETS:
        t = p.read_text(encoding="utf-8")
        if "横版完整流程（2026-10-29" in t:
            print(f"· {p.parent.name} 已有")
            continue
        anchor = "## 工作流"
        block = ADD.strip() + "\n\n"
        if anchor in t:
            t = t.replace(anchor, block + anchor, 1)
        else:
            t = t.rstrip() + "\n\n" + block
        p.write_text(t, encoding="utf-8")
        print(f"✓ {p.parent.name}/SKILL.md 写入横版完整流程")


if __name__ == "__main__":
    main()
