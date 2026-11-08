#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""在 koubo 横版模板（templates/wide）里接入数字人窗口层。

横版模板是靠 `--props='beats.json'` 驱动的（Wide.tsx 读 beats[]，card 名对应 components.tsx
里的组件）。这个补丁加一个可选的 `host` prop：

    { "host": { "src": "main.mp4", "windows": [{"from": 0, "to": 87}, ...] } }

- `src`：带数字人窗口的整条主画面（build_media.py --wide 产出）
- `windows`：帧为单位；这些区间里**只保留字幕和章节条，卡片让位**

用法：python patch_koubo_wide_host.py <wide 模板目录>
可重复执行。
"""
import sys
from pathlib import Path

OLD = """export const Wide:React.FC<{beats:Beat[];tabs?:string[];narration:string;bgm?:string;bgmVol?:number}>=({beats,tabs,narration,bgm,bgmVol=0.12})=>(
 <AbsoluteFill style={{background:C.bg}}>
  {beats.map((b,i)=>{const Card=(K as any)[b.card];return <Sequence key={i} from={b.from} durationInFrames={b.dur}>
   <K.Page crumb={b.crumb} credit={b.credit}>{tabs&&b.tab!==undefined&&<K.TabBar tabs={tabs} active={b.tab}/>}<Card {...b.props}/></K.Page>
"""

NEW = """// 数字人窗口：{src, windows:[{from,to}]}（帧）。命中的区间里卡片让位，只留字幕/章节条。
export type HostWin={src:string;windows:{from:number;to:number}[]};
export const Wide:React.FC<{beats:Beat[];tabs?:string[];narration:string;bgm?:string;bgmVol?:number;host?:HostWin}>=({beats,tabs,narration,bgm,bgmVol=0.12,host})=>{
 const inHost=(f:number)=>!!host&&host.windows.some((w)=>f>=w.from&&f<w.to);
 return (
 <AbsoluteFill style={{background:C.bg}}>
  {host&&<OffthreadVideo src={staticFile(host.src)} muted style={{position:'absolute',inset:0,width:'100%',height:'100%',objectFit:'cover'}}/>}
  {beats.map((b,i)=>{const Card=(K as any)[b.card];const ov=inHost(b.from);return <Sequence key={i} from={b.from} durationInFrames={b.dur}>
   {!ov&&<K.Page crumb={b.crumb} credit={b.credit}>{tabs&&b.tab!==undefined&&<K.TabBar tabs={tabs} active={b.tab}/>}<Card {...b.props}/></K.Page>}
"""

TAIL_OLD = """  </Sequence>;})}
  <Audio src={staticFile(narration)}/>{bgm&&<Audio src={staticFile(bgm)} volume={bgmVol}/>}
 </AbsoluteFill>);"""

TAIL_NEW = """  </Sequence>;})}
  <Audio src={staticFile(narration)}/>{bgm&&<Audio src={staticFile(bgm)} volume={bgmVol}/>}
 </AbsoluteFill>);};"""


def main():
    d = Path(sys.argv[1]).resolve()
    p = d / "src" / "Wide.tsx"
    t = p.read_text(encoding="utf-8")

    if "HostWin" in t:
        print("· 已接入数字人窗口层")
        return

    if OLD not in t:
        raise SystemExit("没匹配到 Wide 组件签名 —— 模板结构可能变了，手动接")

    t = t.replace(OLD, NEW, 1)
    t = t.replace(TAIL_OLD, TAIL_NEW, 1)

    # 需要 OffthreadVideo
    if "OffthreadVideo" not in t.split("\n")[2]:
        t = t.replace("import {Sequence,Audio,staticFile,AbsoluteFill} from 'remotion';",
                      "import {Sequence,Audio,staticFile,AbsoluteFill,OffthreadVideo} from 'remotion';", 1)
    p.write_text(t, encoding="utf-8")
    print("✓ Wide.tsx 已接入数字人窗口层（host prop）")


if __name__ == "__main__":
    main()
