#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""用豆包云端音色给横版试片配音（本机 VoxCPM 卡死时的备选路径）。

用法：python voice_doubao.py [--speaker zh_female_vv_uranus_bigtts]
"""
import json
import os
import sys
from pathlib import Path

sys.path.insert(0, r"E:\dsh-agents\skills\hk-zhuchi\scripts")
import backend as B  # noqa: E402

PROJ = Path(os.environ["HK_PROJECT"]).resolve()
SPEAKER = "zh_female_vv_uranus_bigtts"
if "--speaker" in sys.argv:
    SPEAKER = sys.argv[sys.argv.index("--speaker") + 1]

S = json.loads((PROJ / "script.json").read_text(encoding="utf-8"))
(PROJ / "voice").mkdir(exist_ok=True)
for s in S:
    out = PROJ / "voice" / f"{s['id']}.wav"
    if out.exists() and out.stat().st_size > 1000:
        print(f"[{s['id']}] 已有，跳过")
        continue
    print(f"[{s['id']}] 豆包配音 {len(s['t'])} 字 …", flush=True)
    B.tts_doubao(s["t"], out, speaker=SPEAKER)
    print(f"[{s['id']}] ✓ {out.stat().st_size // 1024} KB", flush=True)
print("✓ 完成")
