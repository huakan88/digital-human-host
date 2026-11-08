#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""给 MediaText 卡加「慢推 + 文字入场」，让静态图不显死板。

原来 MediaText 是一张静止图片 + 静止大字，连着 78 秒会觉得像 PPT。
这个补丁加两件小事（都很克制）：
  1. 画面极慢推近（Ken Burns），1.0 → 1.06
  2. 标题/副标题在前 12 帧淡入 + 轻微上移

用法：python patch_koubo_wide_motion.py <wide 模板目录>
可重复执行。
"""
import re
import sys
from pathlib import Path

NEW = '''// 真实素材铺底 + 大字压画面（横版版 cliptext）
// 加了极慢推近（1.0→1.06）+ 文字淡入上移，避免长片看起来像 PPT
export const MediaText:React.FC<{src:string;video?:boolean;from?:number;title:string;sub?:string;dim?:number}>=
({src,video=false,from=0,title,sub,dim=0.55})=>{
 const f=useCurrentFrame();
 const {durationInFrames}=useVideoConfig();
 const z=1+0.06*Math.min(1,f/Math.max(1,durationInFrames));
 const e=Math.min(1,f/12);
 const rise=(1-e)*18;
 return (
 <AbsoluteFill>
  {video
   ? <OffthreadVideo src={staticFile(src)} startFrom={Math.round(from*30)} muted
       style={{position:'absolute',inset:0,width:'100%',height:'100%',objectFit:'cover',transform:`scale(${z})`}}/>
   : <Img src={staticFile(src)}
       style={{position:'absolute',inset:0,width:'100%',height:'100%',objectFit:'cover',transform:`scale(${z})`}}/>}
  <div style={{position:'absolute',inset:0,
    background:`linear-gradient(180deg,rgba(0,0,0,${(dim*0.65).toFixed(2)}),rgba(0,0,0,${dim.toFixed(2)}))`}}/>
  <div style={{position:'absolute',inset:0,display:'flex',flexDirection:'column',
    justifyContent:'center',alignItems:'center',padding:'0 140px',textAlign:'center',
    opacity:e,transform:`translateY(${rise}px)`}}>
    <div style={{fontFamily:F.sans,fontWeight:900,fontSize:96,color:'#fff',lineHeight:1.22,
      textShadow:'0 8px 48px rgba(0,0,0,.85)'}}>{title}</div>
    {sub?<div style={{marginTop:30,fontFamily:F.sans,fontSize:38,color:'rgba(255,255,255,.92)',
      textShadow:'0 4px 24px rgba(0,0,0,.75)'}}>{sub}</div>:null}
  </div>
 </AbsoluteFill>);
};
'''


def main():
    d = Path(sys.argv[1]).resolve()
    p = d / "src" / "components.tsx"
    t = p.read_text(encoding="utf-8")
    if "1+0.06*Math.min" in t:
        print("· 已有慢推效果")
        return
    i = t.find("// 真实素材铺底 + 大字压画面")
    if i < 0:
        raise SystemExit("没找到 MediaText 注释锚点")
    # 从注释到文件末尾整体替换（MediaText 是文件最后一个组件）
    t = t[:i] + NEW
    p.write_text(t, encoding="utf-8")
    print("✓ MediaText 加了慢推 + 文字入场")


if __name__ == "__main__":
    main()
