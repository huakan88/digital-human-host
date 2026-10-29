#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""把「口型对齐」写成两个主持技能的强制项（必须项），一次性写入、可重复执行。"""
import pathlib

BLOCK = '''
## 口型对齐（**强制项 · 不做就不算交付**）

> 适用于本技能的**所有**主持预设：白背心女性（vivi主持）、短发男生（hk主持），
> 以及以后新加的任何形象。**没有例外，不是可选项。**

出片前必须完整走完下面 5 条，缺一条都不算做完：

### 1. 出画阶段
- 必须用 `<Picture 1>` 绑定参考图、`<Audio 1>` 绑定配音；**台词不写进提示词**
- 提示词必须含 "lips resting closed during pauses"
- **露脸段必须单独出画**（一段一次 H3 调用），每段 ≤ 6 秒；超过就拆句。
  合并出画只允许用在"不露脸"的场合 —— 长片段内部口型会逐渐松掉（实测 10 秒片
  前 5 秒 corr 0.58、后 5 秒掉到 0.34）。
- **不要在同一个露脸窗口里拼两段独立出画**：两次生成的脸型、景别、光线会有细微差别，
  拼在一起就是一次可见的跳切（实测 2.1s → 2.35s 的脸突然变小、位置偏移）。
  一个连续镜头 = 一次生成。

### 2. 修复阶段（必跑）
```bash
python scripts/lipsync_repair.py --dir gen --out gen/fixed     # 两轮迭代 + 只采纳更好的
```
它会按 0.5 秒一段测出"嘴-音"局部偏移，重新对齐画面；修完不如原来会自动保留原片。

### 3. 装配阶段
- `build_media.py` 会自动优先用 `gen/fixed/`
- **绝对不要用配音原始时长去算时间窗口**，必须用 `public/timeline.json`（帧栅格时间轴）。
  两者差 1/60 秒/段，22 段就累积到 0.27 秒 —— 越靠后的露脸段画面越提前，这是
  "后面口型对不上"最常见的真凶。用 `make_host_wrap.py --host-segs` 按段 id 定窗口即可。

### 4. 验收阶段（必跑，出片前）
```bash
# 逐段量：整窗偏差 + 每 1.5 秒子窗偏差
E:\\AI\\envs\\voxcpm\\Scripts\\python.exe sync_report.py 成片.mp4 "起-止,起-止,..."
```
判据：**每段整窗 |lag| ≤ 2 帧（30fps 下 ≤ 67ms）**。

注意两点，否则会误判：
- 一定**逐段**量，别整窗量：一个窗口里拼了多段出画时，测量会取折中框，结果乱跳
- 测量要避开字幕区（`y > 0.62`）：字幕总是领先语音，否则会假报 -6 帧

### 5. 不达标怎么办（按顺序）
1. `gen/nudge.json` 定点平移：`{"s1": 7}` = 把该段画面往后推 7 帧（**确定有效**，s1 就是这么修好的）
2. 换种子重出这批：`HK_SEED=917733 ... backend.py run --force --only ...`，再用 `best_of.py` 择优
3. 还不行 → 该段改成版式卡（不露脸），别硬扛
4. 交付时**附上验收表**

> 已到能力边界：本机 H3 的口型在 ±100ms 以内我这套测量分辨不出（两批独立出画给出相同分数、
> 相邻子窗会 ±10 帧乱跳）。所以可承诺的是「全局 ≤2 帧」，做不到逐字级专业对白。
> 真要逐字级，只能上嘴型重生成模型（LatentSync / Wav2Lip），那是独立安装工程。

'''

TARGETS = [
    pathlib.Path(r"E:\dsh-agents\skills\hk-zhuchi\SKILL.md"),
    pathlib.Path(r"E:\dsh-agents\skills\vivi-zhuchi\SKILL.md"),
]


def main():
    for p in TARGETS:
        t = p.read_text(encoding="utf-8")
        if "口型对齐（**强制项" in t:
            print(f"· {p.parent.name} 已有强制项，跳过")
            continue
        # 插到「工作流」之前（靠前，显眼）
        anchor = "## 工作流"
        if anchor in t:
            t = t.replace(anchor, BLOCK.strip() + "\n\n" + anchor, 1)
        else:
            t = t.rstrip() + "\n" + BLOCK
        p.write_text(t, encoding="utf-8")
        print(f"✓ {p.parent.name}/SKILL.md 写入口型强制项")


if __name__ == "__main__":
    main()
