#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""给 koubo 横版模板加 MediaStat 卡：素材铺底 + 一个巨大的数字 + 说明。

用途：整片都是「素材 + 一句话」会显得平。插入 2-3 个数字钉子
（7 个兵种 / 0 安装 / 2 个引擎）能把节奏打断，也是短视频最常用的提神手法。

用法：python patch_koubo_wide_mediastat.py <wide 模板目录>
可重复执行。
"""
import sys
from pathlib import Path

CARD = '''
// 素材铺底 + 巨大数字（数字钉子）。用来打断「素材+一句话」的单调节奏
export const MediaStat:React.FC<{src:string;video?:boolean;from?:number;big:string;label:string;sub?:string;dim?:number}>=
({src,video=false,from=0,big,label,sub,dim=0.6})=>{
 const f=useCurrentFrame();
 const {durationInFrames}=useVideoConfig();
 const z=1+0.06*Math.min(1,f/Math.max(1,durationInFrames));
 const e=Math.min(1,f/10);
 const pop=1+(1-Math.min(1,f/9))*0.08;
 return (
 <AbsoluteFill>
  {video
   ? <OffthreadVideo src={staticFile(src)} startFrom={Math.round(from*30)} muted
       style={{position:'absolute',inset:0,width:'100%',height:'100%',objectFit:'cover',transform:`scale(${z})`}}/>
   : <Img src={staticFile(src)}
       style={{position:'absolute',inset:0,width:'100%',height:'100%',objectFit:'cover',transform:`scale(${z})`}}/>}
  <div style={{position:'absolute',inset:0,
    background:`linear-gradient(180deg,rgba(0,0,0,${(dim*0.7).toFixed(2)}),rgba(0,0,0,${dim.toFixed(2)}))`}}/>
  <div style={{position:'absolute',inset:0,display:'flex',flexDirection:'column',
    justifyContent:'center',alignItems:'center',opacity:e,transform:`scale(${pop})`}}>
    <div style={{fontFamily:F.sans,fontWeight:900,fontSize:300,lineHeight:1,color:'#fff',
      textShadow:'0 12px 60px rgba(0,0,0,.9)',letterSpacing:-6}}>{big}</div>
    <div style={{marginTop:18,fontFamily:F.sans,fontWeight:700,fontSize:46,color:'#fff',
      textShadow:'0 6px 32px rgba(0,0,0,.85)'}}>{label}</div>
    {sub?<div style={{marginTop:16,fontFamily:F.sans,fontSize:32,color:'rgba(255,255,255,.85)',
      textShadow:'0 4px 24px rgba(0,0,0,.8)'}}>{sub}</div>:null}
  </div>
 </AbsoluteFill>);
};
'''


def main():
    d = Path(sys.argv[1]).resolve()
    p = d / "src" / "components.tsx"
    t = p.read_text(encoding="utf-8")
    if "export const MediaStat" in t:
        print("· 已有 MediaStat")
        return
    p.write_text(t.rstrip() + "\n" + CARD, encoding="utf-8")
    print("✓ components.tsx 加了 MediaStat（大数字压素材）")


if __name__ == "__main__":
    main()
