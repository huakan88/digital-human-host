#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""给 koubo 模板加一个 cliptext beat：真实片段当底 + 大字压在画面中间。

用户要的「把文字放在视频上」就是这个：视频铺满（压暗一点保证可读），
标题和副标题居中叠上去，比纯文字卡有动感得多。

用法：python patch_koubo_cliptext.py <koubo 工程或模板目录>
可重复执行。
"""
import sys
from pathlib import Path

TYPE_ADD = "  | {t: 'cliptext'; src: string; src_label: string; tag: string; title: string; sub?: string; from?: number; size?: number}\n"

CASE = '''  if (b.t === 'cliptext') {
    return (
      <Panel src_label={b.src_label} tag={b.tag} dur={dur}>
        <OffthreadVideo src={staticFile(b.src)} startFrom={Math.round((b.from ?? 0) * 30)} muted style={{position: 'absolute', inset: 0, width: '100%', height: '100%', objectFit: 'cover', filter: 'brightness(0.45) saturate(1.1)'}} />
        <div style={{position: 'absolute', inset: 0, display: 'flex', flexDirection: 'column', justifyContent: 'center', alignItems: 'center', padding: 64, background: 'linear-gradient(180deg, rgba(0,0,0,.35), rgba(0,0,0,.55))'}}>
          <div style={{fontFamily: FONT_DISPLAY, fontWeight: 900, fontSize: b.size ?? 96, color: '#fff', textAlign: 'center', lineHeight: 1.22, textShadow: '0 8px 48px rgba(0,0,0,.75)'}}>{b.title}</div>
          {b.sub ? <div style={{marginTop: 30, fontFamily: FONT_UI, fontSize: 38, color: 'rgba(255,255,255,.88)', textAlign: 'center', textShadow: '0 4px 24px rgba(0,0,0,.7)'}}>{b.sub}</div> : null}
        </div>
      </Panel>
    );
  }
'''


def main():
    proj = Path(sys.argv[1]).resolve()
    p = proj / "src" / "Weekly.tsx"
    t = p.read_text(encoding="utf-8")

    # 1) 类型里加 cliptext
    if "cliptext" not in t.split("const BEATS")[0]:
        anchor = "  | {t: 'clip'; src: string; src_label: string; tag: string; from?: number}\n"
        if anchor in t:
            t = t.replace(anchor, anchor + TYPE_ADD, 1)
            print("✓ 类型加了 cliptext")
        else:
            print("⚠ 没找到 clip 类型定义")
    else:
        print("· cliptext 类型已存在")

    # 2) 渲染分支加在 clip 分支之后
    if "if (b.t === 'cliptext')" not in t:
        anchor2 = "  if (b.t === 'web' || b.t === 'img') {"
        if anchor2 in t:
            t = t.replace(anchor2, CASE + anchor2, 1)
            print("✓ 渲染分支已插入")
        else:
            print("⚠ 没找到插入点")
    else:
        print("· 渲染分支已存在")

    p.write_text(t, encoding="utf-8")


if __name__ == "__main__":
    main()
