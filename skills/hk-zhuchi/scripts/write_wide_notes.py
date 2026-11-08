#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""把横版实测结论补进两个技能（已验证的数据 + 踩到的坑）。"""
import pathlib

ADD = '''
### 横版实测结论（2026-10-29 首次跑通）

- **出画**：`size: [1024, 576]` → H3 正常出片，横构图、白底、手部动作都在画面里
- **成片**：`build_media.py --full --wide` → 1920×1080，帧栅格与竖版一致
- **嘴框（横版）**：`"0.34,0.28,0.66,0.58"`（半身、居中构图）；竖版那个 0.28/0.36/0.72/0.56 不适用
- **底版**：`python make_backdrop.py "" 1920 1080`（现在会写进 `HK_PROJECT` 目录）

**定妆照（重要）**：用**原始照片**当出画基准，比用二次生成的定妆照更像本人。
```bash
HK_LOOK=assets/host_me_photo.jpg python make_tasks.py
```
实测：拿原图当基准，脸型/鼻型/发际线都对得上；换成生成过的 `host_me_look` 会脸变圆、鼻子变大。

**本机 TTS 卡死时的兜底**：VoxCPM 服务偶发「加载完 9GB 但不响应」，`make_voice` 会一直挂着。
这时先用豆包云端把音出来，别等：
```bash
python voice_doubao.py            # 直接调 backend.tts_doubao，几秒出音
```
（豆包约 ¥0.59/2 分钟，出片后再换回克隆音色也可以）

**内存硬约束**：ComfyUI 开着 H3 权重时占 ~20GB，31GB 内存会只剩 0.9GB，
VoxCPM 直接换页卡死。**先出音再出画**，或者先 `POST http://127.0.0.1:8188/free`
（`{"unload_models":true,"free_memory":true}`）把 H3 权重卸掉。
'''

TARGETS = [
    pathlib.Path(r"E:\dsh-agents\skills\hk-zhuchi\SKILL.md"),
    pathlib.Path(r"E:\dsh-agents\skills\vivi-zhuchi\SKILL.md"),
]


def main():
    for p in TARGETS:
        t = p.read_text(encoding="utf-8")
        if "横版实测结论" in t:
            print(f"· {p.parent.name} 已有")
            continue
        anchor = "## 工作流"
        block = ADD.strip() + "\n\n"
        if anchor in t:
            t = t.replace(anchor, block + anchor, 1)
        else:
            t = t.rstrip() + "\n\n" + block
        p.write_text(t, encoding="utf-8")
        print(f"✓ {p.parent.name}/SKILL.md 写入横版实测结论")


if __name__ == "__main__":
    main()
