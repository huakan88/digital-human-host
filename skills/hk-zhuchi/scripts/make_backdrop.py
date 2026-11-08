#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""口播片的通用底版：深色影棚渐变 + 暖光 + 暗角 + 一个很淡的主题水印。

正文段没有专门卡片时用它当主画面，数字人缩在左下角继续讲，
花字卡片再叠上来——这是"资讯口播"最省事也最耐看的版式。
水印只是气氛，压到 6% 不抢字。
"""
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont

# 宽高可传：python make_backdrop.py "" 1920 1080
# 输出到工程目录（HK_PROJECT），没有就落到脚本旁边
import os
W, H = (int(sys.argv[2]), int(sys.argv[3])) if len(sys.argv) > 3 else (1080, 1920)
_proj = os.environ.get("HK_PROJECT")
OUT = (Path(_proj) / "backdrop.png") if _proj else (Path(__file__).resolve().parent / "backdrop.png")
FONT_B = r"C:\Windows\Fonts\msyhbd.ttc"
WMARK = sys.argv[1] if len(sys.argv) > 1 else "28"


def font(size):
    for p in (FONT_B, r"C:\Windows\Fonts\msyh.ttc"):
        if Path(p).exists():
            try:
                return ImageFont.truetype(p, size)
            except Exception:
                pass
    return ImageFont.load_default()


def main():
    # 竖向渐变：上深下略亮
    im = Image.new("RGB", (W, H), (10, 10, 14))
    d = ImageDraw.Draw(im)
    for y in range(H):
        t = y / H
        v = int(9 + 16 * t)
        d.line([(0, y), (W, y)], fill=(v, v, v + 4))

    # 暖光（右上），给纵深
    glow = Image.new("L", (W, H), 0)
    ImageDraw.Draw(glow).ellipse([W * 0.30, -H * 0.08, W * 1.25, H * 0.55], fill=180)
    glow = glow.filter(ImageFilter.GaussianBlur(190))
    im = Image.composite(Image.new("RGB", (W, H), (255, 122, 26)), im,
                         glow.point(lambda v: int(v * 0.16)))

    # 冷光（左下），和小窗错开
    glow2 = Image.new("L", (W, H), 0)
    ImageDraw.Draw(glow2).ellipse([-W * 0.35, H * 0.62, W * 0.75, H * 1.15], fill=150)
    glow2 = glow2.filter(ImageFilter.GaussianBlur(200))
    im = Image.composite(Image.new("RGB", (W, H), (90, 110, 255)), im,
                         glow2.point(lambda v: int(v * 0.10)))

    # 主题水印
    if WMARK:
        layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        ld = ImageDraw.Draw(layer)
        f = font(760)
        bb = ld.textbbox((0, 0), WMARK, font=f)
        ld.text(((W - (bb[2] - bb[0])) / 2, H * 0.10), WMARK, font=f, fill=(255, 255, 255, 9))
        im = Image.alpha_composite(im.convert("RGBA"), layer).convert("RGB")

    # 暗角
    vig = Image.new("L", (W, H), 0)
    ImageDraw.Draw(vig).ellipse([-W * 0.30, -H * 0.15, W * 1.30, H * 1.15], fill=255)
    vig = vig.filter(ImageFilter.GaussianBlur(230)).point(lambda v: 255 - v)
    im = Image.composite(Image.new("RGB", (W, H), (5, 5, 8)), im, vig.point(lambda v: int(v * 0.6)))

    im.save(OUT, quality=95)
    print("✓", OUT)


if __name__ == "__main__":
    main()

