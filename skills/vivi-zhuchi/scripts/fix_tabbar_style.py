import pathlib
import sys

NEW = """export const TabBar:React.FC<{tabs:string[];active:number}>=({tabs,active})=>(
 <div style={{position:'absolute',left:96,top:56,display:'flex',gap:10,alignItems:'center',
  padding:'10px 8px',borderRadius:999,background:'rgba(0,0,0,.36)'}}>{tabs.map((t,i)=>
  <div key={i} style={{padding:'7px 20px',borderRadius:999,fontSize:22,fontWeight:700,
   background:i===active?'rgba(255,255,255,.94)':'transparent',
   color:i===active?'#101010':'rgba(255,255,255,.75)'}}>{t}</div>)}</div>);"""

d = pathlib.Path(sys.argv[1]).resolve()
p = d / "src" / "components.tsx"
lines = p.read_text(encoding="utf-8").split("\n")

start = next((i for i, ln in enumerate(lines) if ln.startswith("export const TabBar")), -1)
if start < 0:
    print("⚠ 没找到 TabBar")
    sys.exit(0)
end = start
while end < len(lines) and "</div>);" not in lines[end]:
    end += 1
if end >= len(lines):
    print("⚠ TabBar 结束标记没找到")
    sys.exit(0)

if "rgba(255,255,255,.94)" in "\n".join(lines[start:end + 1]):
    print("· 已改过")
else:
    lines[start:end + 1] = NEW.split("\n")
    p.write_text("\n".join(lines), encoding="utf-8")
    print("✓ TabBar 改为半透明深底 + 白字")
