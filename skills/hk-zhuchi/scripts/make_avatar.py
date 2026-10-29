#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""用一张正脸照做出数字人的七视图素材（MiniMax image-01 + subject_reference）。

产出（都在 skill 的 assets/ 下）：
    host_me_ref.jpg          原始正脸照（用户本人照片）
    host_me_7view_full.jpg   七视图·全身（看比例：约 170cm 男性）
    host_me_7view_bust.jpg   七视图·半身（看脸和发型一致性）
    host_me_look.jpg         9:16 定妆照（H3 的首帧/参考图：正脸、闭嘴、头顶留白）

用法：python make_avatar.py [参考照路径]
"""
import base64
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import backend as B  # noqa: E402

ASSETS = B.SKILL / "assets"

SHEET_FULL = """Character turnaround reference sheet of the SAME man shown in the reference photo, drawn as realistic photography.
One single image containing SEVEN separate full-body panels of the identical person, evenly spaced in a clean grid (four panels on the top row, three panels on the bottom row), every panel at the exact same scale, same camera height, same soft studio lighting, plain pure white seamless background, subtle contact shadow under the feet.
Panel order: 1) front view facing camera, 2) three-quarter view rotated 45 degrees to his left, 3) full left side profile, 4) back view, 5) full right side profile, 6) three-quarter view rotated 45 degrees to his right, 7) front view standing with arms slightly away from the body.
He is an East Asian man, about 170 cm tall, lean average build, short black crew-cut hair, olive-green short-sleeve henley shirt with a three-button placket, dark grey trousers, plain white sneakers, relaxed neutral standing pose, arms at his sides, mouth closed, calm neutral expression.
Head to toe fully visible in every panel with clear margin above the head and below the shoes. Realistic photography, sharp focus, evenly lit.
Absolutely no text, no captions, no labels, no numbers, no letters, no arrows, no watermark, no border, no logos."""

SHEET_BUST = """Character turnaround reference sheet of the SAME man shown in the reference photo, drawn as realistic photography.
One single image containing SEVEN separate head-and-shoulders panels of the identical person, evenly spaced in a clean grid (four panels on the top row, three panels on the bottom row), every panel at the exact same scale and camera height, same soft studio lighting, plain pure white seamless background.
Panel order: 1) front view facing camera, 2) three-quarter view rotated 45 degrees to his left, 3) full left side profile, 4) back of the head, 5) full right side profile, 6) three-quarter view rotated 45 degrees to his right, 7) front view, neutral relaxed expression.
He is an East Asian man about 170 cm tall, lean average build, short black crew-cut hair with trimmed sides, olive-green short-sleeve henley shirt, clean-shaven, natural skin texture, mouth closed, calm neutral expression, direct eye contact in the front panels.
Chest-up framing in every panel with generous empty space above the head. Realistic photography, sharp focus on the eyes, evenly lit.
Absolutely no text, no captions, no labels, no numbers, no letters, no arrows, no watermark, no border, no logos."""

LOOK_9X16 = """Realistic studio photograph of the SAME man shown in the reference photo.
Vertical 9:16 portrait, framed from the mid-chest up, he is centred in the frame with GENEROUS EMPTY HEADROOM above his hair (at least one quarter of the frame height is blank backdrop above the head).
He has short black crew-cut hair with the sides trimmed, a clean-shaven face, and wears the same olive-green short-sleeve henley shirt with a three-button placket.
He looks straight into the camera with a calm, friendly, neutral expression, mouth closed, relaxed shoulders, hands out of frame.
Plain pure white seamless studio backdrop, soft even studio lighting, natural skin texture, sharp focus on the eyes, realistic photography.
No text, no watermark, no logo, no border, no crop of the top of the head."""


def gen(prompt, out, ref, ratio=None, width=None, height=None, seed=None):
    b64 = base64.b64encode(Path(ref).read_bytes()).decode()
    data_url = f"data:image/jpeg;base64,{b64}"
    body = {"model": "image-01", "prompt": prompt, "n": 1,
            "response_format": "base64", "prompt_optimizer": False,
            "subject_reference": [{"type": "character", "image_file": data_url}]}
    if ratio:
        body["aspect_ratio"] = ratio
    if width and height:
        body["width"], body["height"] = width, height
    if seed is not None:
        body["seed"] = seed
    d = B.http_json(B.MM_BASE + "/image_generation", body, headers={"Authorization": "Bearer " + B.mm_key()})
    data = (d.get("data") or {}).get("image_base64") or []
    if not data:
        raise RuntimeError(f"生图失败：{json.dumps(d.get('base_resp'), ensure_ascii=False)}")
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_bytes(base64.b64decode(data[0]))
    print(f"✓ {out.name}  {out.stat().st_size} bytes", flush=True)
    return out


def main():
    ref = Path(sys.argv[1]) if len(sys.argv) > 1 else ASSETS / "host_me_ref_1k.jpg"
    gen(SHEET_FULL, ASSETS / "host_me_7view_full.jpg", ref, width=2048, height=1152, seed=20261027)
    gen(SHEET_BUST, ASSETS / "host_me_7view_bust.jpg", ref, width=2048, height=1152, seed=20261028)
    gen(LOOK_9X16, ASSETS / "host_me_look.jpg", ref, ratio="9:16", seed=20261029)


if __name__ == "__main__":
    main()
