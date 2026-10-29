#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""给 koubo-video 的 Remotion 模板加「数字人片头片尾」。

中间完全照旧用 koubo 自己的 11 种 beat 包装；只在片头/片尾把数字人铺满，
章节条和逐句字幕照常叠在最上层（所以数字人段也有字幕，不会"哑"）。

片头片尾的时长与素材由外部的数字人流水线产出（vivi主持 / hk主持）：
  <项目>/public/host/intro.mp4   覆盖旁白 0 ~ intro.sec 秒
  <项目>/public/host/outro.mp4   覆盖旁白最后 outro.sec 秒
  <项目>/public/host/host.json   {"intro":{"src":"host/intro.mp4","sec":12},
                                  "outro":{"src":"host/outro.mp4","sec":9}}
"""
import json
import pathlib
import sys

TPL = pathlib.Path(r"E:\dsh-agents\skills\koubo-video\remotion-template")
WEEKLY = TPL / "src" / "Weekly.tsx"
HOSTDIR = TPL / "public" / "host"

HOST_JSON = HOSTDIR / "host.json"
DEFAULT = {"intro": {"src": "host/intro.mp4", "sec": 0},
           "outro": {"src": "host/outro.mp4", "sec": 0}}


def ensure_host_json():
    HOSTDIR.mkdir(parents=True, exist_ok=True)
    if not HOST_JSON.exists():
        HOST_JSON.write_text(json.dumps(DEFAULT, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print("✓ 建了 public/host/host.json（默认不启用）")


def patch():
    t = WEEKLY.read_text(encoding="utf-8")
    if "HOST_CFG" in t:
        print("· 已经打过补丁，跳过")
        return

    # 1) import
    t = t.replace("import {COLORS, FONT_DISPLAY, FONT_UI} from './theme';",
                  "import {COLORS, FONT_DISPLAY, FONT_UI} from './theme';\n"
                  "// 数字人片头片尾配置（由 make_host_wrap.py 写；sec=0 表示不启用）\n"
                  "import HOST_CFG from '../public/host/host.json';", 1)

    # 2) Segment 支持「只留覆盖层」（数字人段不要 beats，只保留章节条和字幕）
    t = t.replace("const Segment: React.FC<{i: number}> = ({i}) => {",
                  "const Segment: React.FC<{i: number; onlyOverlay?: boolean}> = ({i, onlyOverlay}) => {", 1)
    t = t.replace("      {beats.map((b, k) => {",
                  "      {!onlyOverlay && beats.map((b, k) => {", 1)

    # 3) 主合成：数字人铺在 Bg 之上、内容之下；数字人时段内容只留覆盖层
    old = """export const PetHotspots: React.FC = () => {
  ensureFonts();
  return (
    <AbsoluteFill style={{background: COLORS.bg}}>
      <Bg />
      {PARTS.map((_, i) => ("""
    new = """export const PetHotspots: React.FC = () => {
  ensureFonts();
  const f = useCurrentFrame();
  const TOTAL_F = Math.round(PARTS.reduce((a, b) => a + b, 0) * FPS);
  const INTRO_F = Math.round((HOST_CFG.intro?.sec ?? 0) * FPS);
  const OUTRO_F = Math.round((HOST_CFG.outro?.sec ?? 0) * FPS);
  // 当前帧是不是落在数字人片头/片尾里
  const inHost = (INTRO_F > 0 && f < INTRO_F) || (OUTRO_F > 0 && f >= TOTAL_F - OUTRO_F);
  const hostStyle: React.CSSProperties = {position: 'absolute', inset: 0, width: '100%', height: '100%', objectFit: 'cover'};
  return (
    <AbsoluteFill style={{background: COLORS.bg}}>
      <Bg />
      {INTRO_F > 0 && (
        <Sequence from={0} durationInFrames={INTRO_F}>
          <OffthreadVideo src={staticFile(HOST_CFG.intro.src)} muted style={hostStyle} />
        </Sequence>
      )}
      {OUTRO_F > 0 && (
        <Sequence from={TOTAL_F - OUTRO_F} durationInFrames={OUTRO_F}>
          <OffthreadVideo src={staticFile(HOST_CFG.outro.src)} muted style={hostStyle} />
        </Sequence>
      )}
      {PARTS.map((_, i) => ("""
    if old not in t:
        raise SystemExit("主合成锚点没匹配，补丁中止")
    t = t.replace(old, new, 1)
    t = t.replace("<Segment i={i} /></Sequence>", "<Segment i={i} onlyOverlay={inHost} /></Sequence>", 1)

    WEEKLY.write_text(t, encoding="utf-8")
    print("✓ Weekly.tsx 已接上数字人片头片尾")


if __name__ == "__main__":
    ensure_host_json()
    patch()
    print("\n用法：把 host/intro.mp4、host/outro.mp4 放进 <项目>/public/host/，")
    print("      再把 host.json 的 sec 改成实际秒数，然后照常 npx remotion render。")
