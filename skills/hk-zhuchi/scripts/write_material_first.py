#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""把「素材优先」写成硬指标，进两个主持技能。这是用户 2026-10 明确指定的第一原则。"""
import pathlib

SECTION = '''
## 第一原则：素材优先（**硬指标，用户明确要求**）

> 2026-10 用户原话：「需要特别多的素材，里面一定要是用素材填充的，
> 而不是干巴巴的都是 Remotion 的内容」。
> **这条优先于其它一切包装规则。**

### 硬指标（出片前逐条打勾）

- [ ] **真实素材时长 ≥ 成片的 50%**（拿 `ffprobe` 算一下，别凭感觉）
- [ ] **至少 8 段不同素材**；一期 60~90 秒的片子，素材段越多越好
- [ ] **不允许连续 2 拍以上都是纯文字卡**。纯 Remotion 卡只用于三类：数据卡（数字/条形/表格）、
      过渡/章节、结尾收束
- [ ] 每条素材画面上都有署名（平台 · 作品名 · 作者 · 编号）
- [ ] 能用「文字压在素材上」就不要做纯文字卡 —— 用 `cliptext` beat
- [ ] 用户自己的作品**必须用**，并且文案里点名"这是我自己做的"

### 反面例子（别这么做）

一期 70 秒里有 55 秒是深色底 + 文字卡 = 干巴巴。
正确做法：每一拍先问「这一拍能不能用一段真实画面」，能就上素材，文字叠上去。

### 素材密度怎么保证

1. 先按脚本的**每一拍**列一张表：这一拍讲什么 → 配哪段素材（没有合适的就去找）
2. 素材不够就去抓（见下一节「真实素材：从哪来」）
3. 把「数据卡」压缩到最少：一期里 3~4 张足够，其余全用画面
4. 同一段素材可以复用在不同位置，但 `from` 要错开，避免观众看出重复

### 自检命令

```bash
# 估算素材占比：把 BEATS 里所有 clip / cliptext 的段落时长加起来 ÷ 总时长
# 简单办法：看成片，纯色底/纯文字卡超过一半就是不合格
```

'''

TARGETS = [
    pathlib.Path(r"E:\dsh-agents\skills\hk-zhuchi\SKILL.md"),
    pathlib.Path(r"E:\dsh-agents\skills\vivi-zhuchi\SKILL.md"),
]


def main():
    for p in TARGETS:
        t = p.read_text(encoding="utf-8")
        if "第一原则：素材优先" in t:
            print(f"· {p.parent.name} 已有")
            continue
        # 放在「成品长什么样」之后，最显眼的位置
        anchor = "## 口型对齐（**强制项"
        block = SECTION.strip() + "\n\n"
        if anchor in t:
            t = t.replace(anchor, block + anchor, 1)
        else:
            t = t.rstrip() + "\n\n" + block
        p.write_text(t, encoding="utf-8")
        print(f"✓ {p.parent.name}/SKILL.md 写入「素材优先」硬指标")


if __name__ == "__main__":
    main()
