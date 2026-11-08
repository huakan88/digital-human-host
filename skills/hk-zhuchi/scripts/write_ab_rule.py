#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""把「A/B/C 人眼定标」写进两个技能。

自动相关性在 ±100ms 内不可靠（实测同一段能给出 ±460ms 且方向相反），
这时最靠谱的是：同一段做三个偏移版本，让人瞄一眼挑。
"""
import pathlib

ADD = '''
### 定不了的时候：A/B/C 人眼定标（2026-10-30 补充）

自动相关性在 ±100ms 内**不可靠**（实测同一段给出 −458ms 和 +458ms，方向相反）。
当长帧条看不出明显错位、但听感/观感就是不对时，别再纠结数字，让眼睛定标：

```bash
python scripts/ab_offsets.py <片段> <配音.wav> AB_对比.mp4 6
# 生成三段同一句：A 画面往前 0.2 秒 / B 原始 / C 画面往后 0.2 秒
```
放到最大看，只盯**嘴和音的先后**。选定哪个，就用 `gen/nudge.json` 按段调：

```json
{"s7": -6}     // 该段画面提前 6 帧；正数=画面往后
```

**这一招的价值**：把「我测不准」变成「用户能判断」，一次就问对，
比反复重出画省得多（每段重出约 4 分钟，改偏移只要重新渲染）。

**优先级顺序（最终版）**：
1. 拉 72 帧长帧条 → 嘴形几乎不变 → **重出**（换种子）
2. A/B/C 对比 → 人眼选偏移 → `nudge.json` 定点平移
3. 还不对 → 该段改成版式卡，不露脸
4. **永远不要**拿 `corr<0.4` 的 lag 数字直接去批量平移

'''

TARGETS = [
    pathlib.Path(r"E:\dsh-agents\skills\hk-zhuchi\SKILL.md"),
    pathlib.Path(r"E:\dsh-agents\skills\vivi-zhuchi\SKILL.md"),
]


def main():
    for p in TARGETS:
        t = p.read_text(encoding="utf-8")
        if "A/B/C 人眼定标" in t:
            print(f"· {p.parent.name} 已有")
            continue
        anchor = "## 口型验收与修正规范"
        block = ADD.strip() + "\n\n"
        if anchor in t:
            t = t.replace(anchor, block + anchor, 1)
        else:
            t = t.rstrip() + "\n\n" + block
        p.write_text(t, encoding="utf-8")
        print(f"✓ {p.parent.name}/SKILL.md 写入 A/B/C 定标")


if __name__ == "__main__":
    main()
