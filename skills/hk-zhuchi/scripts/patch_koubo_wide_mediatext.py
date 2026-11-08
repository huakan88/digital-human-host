#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""给 koubo 横版模板加一个 MediaText 卡：真实素材铺底 + 大字压画面。

横版模板的卡片都是白底排版卡，没有「文字压在视频上」这种。用户明确要求
文字要压在素材上，所以补这一个（等价于竖版的 cliptext）。

用法：python patch_koubo_wide_mediatext.py <wide 模板目录>
可重复执行。
"""
import sys
from pathlib import Path

CARD = '''

// 真实素材铺底 + 大字压画面（横版版 cliptext）
export const MediaText:React.FC<{src:string;video?:boolean;from?:number;title:string;sub?:string;dim?:number}>=
({src,video=false,from=0,title,sub,dim=0.55})=>(
 <AbsoluteFill>
  {video
   ? <OffthreadVideo src={staticFile(src)} startFrom={Math.round(from*30)} muted
       style={{position:'absolute',inset:0,width:'100%',height:'100%',objectFit:'cover'}}/>
   : <Img src={staticFile(src)}
       style={{position:'absolute',inset:0,width:'100%',height:'100%',objectFit:'cover'}}/>}
  <div style={{position:'absolute',inset:0,
    background:`linear-gradient(180deg,rgba(0,0,0,${(dim*0.65).toFixed(2)}),rgba(0,0,0,${dim.toFixed(2)}))`}}/>
  <div style={{position:'absolute',inset:0,display:'flex',flexDirection:'column',
    justifyContent:'center',alignItems:'center',padding:'0 140px',textAlign:'center'}}>
    <div style={{fontFamily:F.sans,fontWeight:900,fontSize:96,color:'#fff',lineHeight:1.22,
      textShadow:'0 8px 48px rgba(0,0,0,.85)'}}>{title}</div>
    {sub?<div style={{marginTop:30,fontFamily:F.sans,fontSize:38,color:'rgba(255,255,255,.92)',
      textShadow:'0 4px 24px rgba(0,0,0,.75)'}}>{sub}</div>:null}
  </div>
 </AbsoluteFill>);
'''


def main():
    d = Path(sys.argv[1]).resolve()
    p = d / "src" / "components.tsx"
    t = p.read_text(encoding="utf-8")
    if "export const MediaText" in t:
        print("· 已有 MediaText")
        return
    p.write_text(t.rstrip() + "\n" + CARD, encoding="utf-8")
    print("✓ components.tsx 加了 MediaText（素材铺底 + 大字压画面）")


if __name__ == "__main__":
    main()
