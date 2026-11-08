#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""修 koubo 横版模板的章节条：1) 渲染顺序（原来被素材卡盖住）2) 深色底上的可读性。

原来 Wide.tsx 里 TabBar 在 Card 之前渲染，而 MediaText 是铺满画面的 AbsoluteFill，
章节条就被压在底下了。同时浅灰胶囊在深色战场上几乎看不见。

用法：python patch_koubo_wide_tabbar.py <wide 模板目录>
可重复执行。
"""
import sys
from pathlib import Path

OLD_ORDER = ("<K.Page crumb={b.crumb} credit={b.credit}>{tabs&&b.tab!==undefined&&<K.TabBar tabs={tabs} active={b.tab}/>}<Card {...b.props}/></K.Page>")
NEW_ORDER = ("<K.Page crumb={b.crumb} credit={b.credit}><Card {...b.props}/>{tabs&&b.tab!==undefined&&<K.TabBar tabs={tabs} active={b.tab}/>}</K.Page>")

OLD_TAB = """<div style={{position:'absolute',left:96,top:108,display:'flex',gap:12}}>{tabs.map((t,i)=>
   <div key={i} style={{padding:'8px 22px',borderRadius:999,fontSize:22,fontWeight:700,
   background:i===active?C.dark:'#F2F2F2',color:i===active?'#fff':C.grey}}>{t}</div>)}</div>);"""

NEW_TAB = """<div style={{position:'absolute',left:96,top:60,display:'flex',gap:10,alignItems:'center',
   padding:'10px 6px',borderRadius:999,background:'rgba(0,0,0,.34)',backdropFilter:'blur(6px)'}}>{tabs.map((t,i)=>
   <div key={i} style={{padding:'7px 20px',borderRadius:999,fontSize:22,fontWeight:700,
   background:i===active?'rgba(255,255,255,.92)':'transparent',
   color:i===active?'#101010':'rgba(255,255,255,.72)'}}>{t}</div>)}</div>);"""


def main():
    d = Path(sys.argv[1]).resolve()

    w = d / "src" / "Wide.tsx"
    t = w.read_text(encoding="utf-8")
    if OLD_ORDER in t:
        t = t.replace(OLD_ORDER, NEW_ORDER, 1)
        w.write_text(t, encoding="utf-8")
        print("✓ 章节条移到素材卡之后（不被盖住）")
    elif NEW_ORDER in t:
        print("· 渲染顺序已修")
    else:
        print("⚠ Wide.tsx 锚点没匹配")

    c = d / "src" / "components.tsx"
    t = c.read_text(encoding="utf-8")
    if OLD_TAB in t:
        t = t.replace(OLD_TAB, NEW_TAB, 1)
        c.write_text(t, encoding="utf-8")
        print("✓ 章节条改成半透明深底 + 白字（深色画面上可读）")
    elif NEW_TAB in t:
        print("· 配色已修")
    else:
        print("⚠ components.tsx 锚点没匹配")


if __name__ == "__main__":
    main()
