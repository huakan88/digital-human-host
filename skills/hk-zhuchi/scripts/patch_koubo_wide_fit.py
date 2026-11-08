#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""给 MediaText 加 fit 参数（cover / contain），contain 时用模糊底衬。

竖屏素材（如 592×1280 的实机录屏）放进 16:9 会被裁掉一大半；
contain + 模糊底能完整显示，和竖版模板的 clip 手法一致。

用法：python patch_koubo_wide_fit.py <wide 模板目录>
可重复执行。
"""
import sys
from pathlib import Path

NEW = '''// 真实素材铺底 + 大字压画面（横版版 cliptext）
// fit="contain" 时用模糊底衬完整显示（竖屏录屏不裁切）
export const MediaText:React.FC<{src:string;video?:boolean;from?:number;title:string;sub?:string;dim?:number;fit?:'cover'|'contain'}>=
({src,video=false,from=0,title,sub,dim=0.55,fit='cover'})=>{
 const f=useCurrentFrame();
 const {durationInFrames}=useVideoConfig();
 const z=1+0.06*Math.min(1,f/Math.max(1,durationInFrames));
 const e=Math.min(1,f/12);
 const rise=(1-e)*18;
 const Media=({style}:{style:React.CSSProperties})=> video
   ? <OffthreadVideo src={staticFile(src)} startFrom={Math.round(from*30)} muted style={style}/>
   : <Img src={staticFile(src)} style={style}/>;
 return (
 <AbsoluteFill>
  {fit==='contain' && (
   <Media style={{position:'absolute',inset:0,width:'100%',height:'100%',objectFit:'cover',
     filter:'blur(26px) brightness(.45)',transform:`scale(${z})`}}/>
  )}
  <Media style={{position:'absolute',inset:0,width:'100%',height:'100%',
    objectFit:fit==='contain'?'contain':'cover',transform:`scale(${z})`}}/>
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
    if "fit?:'cover'|'contain'" in t:
        print("· 已有 fit 参数")
        return
    i = t.find("// 真实素材铺底 + 大字压画面")
    if i < 0:
        raise SystemExit("没找到 MediaText 注释锚点")
    # MediaText 是文件最后一个组件，从注释到末尾整体替换；
    # 但如果后面还有 MediaStat，要保留它
    j = t.find("// 素材铺底 + 巨大数字")
    tail = ""
    if j > i:
        end = t.find("\n};", j)
        tail = "\n" + t[j:end + 3] if end > 0 else ""
    p.write_text(t[:i] + NEW + tail, encoding="utf-8")
    print("✓ MediaText 支持 fit=contain（模糊底衬）")


if __name__ == "__main__":
    main()
