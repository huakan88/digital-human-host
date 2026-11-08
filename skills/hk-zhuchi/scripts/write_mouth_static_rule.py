#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""把「嘴部静止」这个失败模式和长帧条验收写进两个技能。

这一轮发现：H3 偶尔会生成**嘴基本不动**的片段——嘴一直半张，随音频毫无变化。
这种情况自动相关性只有 0.2~0.3，看不出偏移，人一耳朵就听出来对不上。
以前技能里没有这条，导致我拿 ±500ms 的假数据去修，越修越乱。
"""
import pathlib

ADD = '''
### 「嘴部静止」这个失败模式（2026-10-30 补充）

自动相关性低（<0.4）时**不要**把它当成"偏移多少帧"，它多半是这一条素材
**嘴根本没在动** —— 嘴一直是半张状态，和音频没有任何关系。平移救不了，只能重出。

**判定方法（唯一可信）**：拉 72 帧（≈2.4 秒）的长帧条，看嘴形有没有变化。

```bash
python scripts/lipsync_long.py <成片或片段> <起始秒> 72      # 默认嘴框就是横版唇部
# 输出：最佳滞后 ±N 帧 + corr + 一张 72 格的长帧条
```

- **72 帧里嘴形几乎不变** → 这条素材废了，重出（换种子），别调时间轴
- 嘴形在变、但整体错开 → 才用 `gen/nudge.json` 定点平移
- `corr < 0.4` 时**不要采信那个 lag 数字**：实测同一段能给出 ±500ms 且方向相反

**重出的具体做法**（一次试两个种子，挑好的）：

```bash
for seed in 1201 9931; do
  HK_SEED=$seed python scripts/backend.py run tasks.json --backend local --force --only s7
  cp gen/renoise-s7.mp4 gen/s7_seed$seed.mp4
done
# 然后每条都拉长帧条看，挑嘴形变化最明显的那个
```

**为什么会随机出现**：口型一致性对种子敏感。同一句台词、同一张定妆照，
有的种子嘴跟得很紧，有的种子嘴几乎不动。这不是参数没调好，是抽样问题。

**验收顺序（更新）**：
1. 拉长帧条看**嘴形有没有变化**（这是第一道门，不过就重出）
2. 过了再量滞后，`|lag| ≤ 2 帧` 才放行
3. 只有 1~3 帧的小偏差才用 nudge 平移

'''

TARGETS = [
    pathlib.Path(r"E:\dsh-agents\skills\hk-zhuchi\SKILL.md"),
    pathlib.Path(r"E:\dsh-agents\skills\vivi-zhuchi\SKILL.md"),
]


def main():
    for p in TARGETS:
        t = p.read_text(encoding="utf-8")
        if "嘴部静止" in t:
            print(f"· {p.parent.name} 已有")
            continue
        anchor = "## 口型验收与修正规范"
        block = ADD.strip() + "\n\n"
        if anchor in t:
            t = t.replace(anchor, block + anchor, 1)
        else:
            t = t.rstrip() + "\n\n" + block
        p.write_text(t, encoding="utf-8")
        print(f"✓ {p.parent.name}/SKILL.md 写入「嘴部静止」")


if __name__ == "__main__":
    main()
