#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""把 koubo 模板的「数字人片头片尾」升级成「任意多个露脸窗口」。

用法：python patch_koubo_windows.py <koubo 工程或模板目录>
可重复执行（幂等）。会重写 PetHotspots 整个函数（它在文件末尾）。
"""
import re
import sys
from pathlib import Path

PET = r'''export const PetHotspots: React.FC = () => {
  ensureFonts();
  const f = useCurrentFrame();
  const TOTAL_F = Math.round(PARTS.reduce((a, b) => a + b, 0) * FPS);
  // 露脸窗口：{src, from, to}，单位秒。也兼容老的 intro/outro 写法。
  // 注意：数字人画面不再用「每个窗口一个 video 元素」——Sequence 里晚出场的
  // OffthreadVideo 实测不渲染（只有第一个窗口有画面）。改成把带数字人的
  // main.mp4 铺满整条时间轴当底图，koubo 的 beat 盖在上面；
  // 数字人窗口内 beat 自动让位（onlyOverlay），只留章节条和字幕。
  const WINS: {src: string; from: number; to: number}[] =
    ((HOST_CFG as any).windows as {src: string; from: number; to: number}[]) ??
    [
      ...((HOST_CFG as any).intro?.sec ? [{src: (HOST_CFG as any).intro.src, from: 0, to: (HOST_CFG as any).intro.sec}] : []),
      ...((HOST_CFG as any).outro?.sec
        ? [{src: (HOST_CFG as any).outro.src, from: TOTAL_F / FPS - (HOST_CFG as any).outro.sec, to: TOTAL_F / FPS}]
        : []),
    ];
  const fw = WINS.map((w) => ({...w, a: Math.round(w.from * FPS), b: Math.round(w.to * FPS)}));
  const inHost = fw.some((w) => f >= w.a && f < w.b);
  const hostStyle: React.CSSProperties = {position: 'absolute', inset: 0, width: '100%', height: '100%', objectFit: 'cover'};
  return (
    <AbsoluteFill style={{background: COLORS.bg}}>
      <Bg />
      {fw.length > 0 ? <OffthreadVideo src={staticFile('main.mp4')} muted style={hostStyle} /> : null}
      {PARTS.map((_, i) => (
        <Sequence key={i} from={START[i]} durationInFrames={(START[i + 1] ?? TOTAL_F + 15) - START[i]}><Segment i={i} onlyOverlay={inHost} /></Sequence>
      ))}
      <Audio src={staticFile('narration.wav')} />
    </AbsoluteFill>
  );
};
'''


def main():
    proj = Path(sys.argv[1]).resolve()
    p = proj / "src" / "Weekly.tsx"
    t = p.read_text(encoding="utf-8")
    i = t.find("export const PetHotspots")
    if i < 0:
        raise SystemExit("找不到 PetHotspots，模板结构变了？")
    t = t[:i] + PET
    # 数字人层用 <Video>（OffthreadVideo 偶发 "Compositor error: No frame found"）
    if "Video," not in t.split("\n")[1]:
        t = t.replace("import {AbsoluteFill, Img, OffthreadVideo, Sequence,",
                      "import {AbsoluteFill, Img, OffthreadVideo, Video, Sequence,", 1)
    p.write_text(t, encoding="utf-8")
    print(f"✓ {p} 已升级为多窗口露脸")


if __name__ == "__main__":
    main()
