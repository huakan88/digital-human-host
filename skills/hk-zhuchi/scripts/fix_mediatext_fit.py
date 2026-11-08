import pathlib
import sys

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
};'''

d = pathlib.Path(sys.argv[1]).resolve()
p = d / "src" / "components.tsx"
t = p.read_text(encoding="utf-8")

start = t.find("// 真实素材铺底 + 大字压画面")
if start < 0:
    print("⚠ 没找到 MediaText 注释")
    sys.exit(0)
# MediaText 从头注释到它的 "};\n" 结束
end = t.find("\n};", start)
if end < 0:
    print("⚠ 没找到结束标记")
    sys.exit(0)
end += 3

if "fit?:'cover'|'contain'}>=\n({src,video=false" in t[start:end]:
    print("· MediaText 已支持 fit")
    sys.exit(0)

t = t[:start] + NEW + t[end:]
p.write_text(t, encoding="utf-8")
print("✓ MediaText 加了 fit=contain（模糊底衬）")
