#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""重试七视图：全身 4+3 两行（模型对"转体"更敏感），半身 21:9 一行七格。

用法：python make_7view.py [参考照路径] [尝试次数]
"""
import base64
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import backend as B  # noqa: E402
from make_avatar import gen  # noqa: E402

ASSETS = B.SKILL / "assets"

FULL = """Character turnaround sheet of ONE man, realistic photography, the identical person repeated SEVEN times. TWO ROWS on a plain white background: upper row FOUR full-body figures, lower row THREE full-body figures centred under it. Exactly seven figures, all the same size, same camera height, same lighting, evenly spaced.
Upper row, left to right: (1) front view facing camera; (2) body turned 45 degrees, facing right of frame; (3) full side profile, nose pointing right of frame; (4) seen from behind, showing the back of his head and shirt.
Lower row, left to right: (5) full side profile, nose pointing LEFT of frame; (6) body turned 45 degrees from the opposite side; (7) front view facing camera, arms slightly out.
East Asian man, about 170 cm tall, lean build, short black crew-cut hair, olive-green short-sleeve henley shirt with three-button placket, dark grey trousers, white sneakers, relaxed neutral standing pose, arms at sides, mouth closed, calm neutral expression.
Every figure fully visible from head to toe with empty space above the head and below the shoes.
Soft even studio light, subtle contact shadow under the shoes, sharp focus, plain white seamless background.
No text, no labels, no numbers, no watermark, no border."""

ROW7 = """Character turnaround sheet of ONE man, realistic photography. ONE single horizontal row of SEVEN full-body photographs of the SAME man standing, evenly spaced across the full width of the image, identical scale, identical camera height, identical soft lighting, plain pure white background.
The seven photographs show him at seven rotation angles, in this order: (1) his face square to the camera, full front view; (2) his face turned about 45 degrees to the left; (3) his face in full side profile pointing to the left; (4) his face about 135 degrees to the left, mostly the back of his head visible; (5) the complete back of him, no face visible at all; (6) his face about 135 degrees to the right, mostly the back of his head visible; (7) his face in full side profile pointing to the right.
IMPORTANT: the first figure must face the camera directly and the fifth figure must show his back.
East Asian man, about 170 cm tall, lean average build, short black crew-cut hair, olive-green short-sleeve henley shirt with a three-button placket, dark grey trousers, white sneakers, relaxed neutral standing pose, arms at his sides, mouth closed, calm neutral expression.
Every figure fully visible from head to toe with clear empty space above the head and below the shoes.
Soft even studio lighting, subtle contact shadow under the shoes, sharp focus, plain white seamless background.
No text, no labels, no numbers, no watermark, no border."""

GRID8 = """Character turnaround sheet of ONE man, realistic photography.
TWO ROWS on a plain white background: the UPPER row contains FOUR full-body figures side by side, the LOWER row contains FOUR full-body figures side by side directly under the upper row. Exactly EIGHT figures, all the same size, same camera height, same soft lighting, evenly spaced, plain pure white background.
Upper row, left to right: (1) facing the camera front view; (2) body turned 45 degrees, facing right of frame; (3) full side profile, nose pointing right of frame; (4) seen from behind, showing the back of his head and shirt.
Lower row, left to right: (5) full side profile, nose pointing LEFT of frame; (6) body turned 45 degrees from the opposite side; (7) facing the camera front view; (8) body turned 45 degrees, facing left of frame.
East Asian man, about 170 cm tall, lean average build, short black crew-cut hair, olive-green short-sleeve henley shirt with a three-button placket, dark grey trousers, white sneakers, relaxed neutral standing pose, arms at his sides, mouth closed, calm neutral expression.
Every figure fully visible from head to toe with empty space above the head and below the shoes.
Realistic photography, sharp focus, evenly lit, subtle contact shadow under the shoes, plain white seamless background.
No text, no labels, no numbers, no watermark, no border."""

BUST = """Character turnaround sheet of ONE single man, realistic photography, the identical person repeated SEVEN times.
Layout: ONE horizontal row spanning the full width of the image, SEVEN head-and-shoulders panels side by side, equal size, evenly spaced, small even gaps, same lighting, plain white background.
Left to right: (1) facing the camera front view; (2) head turned to face the LEFT of the frame, seen from a 45 degree angle; (3) full side profile with his nose pointing to the LEFT of the frame; (4) the back of his head, seen from behind; (5) full side profile with his nose pointing to the RIGHT of the frame; (6) head turned to face the RIGHT of the frame, seen from a 45 degree angle; (7) facing the camera front view again.
East Asian man, about 170 cm tall, lean build, short black crew-cut hair with trimmed sides, olive-green short-sleeve henley shirt, clean-shaven, natural skin texture, mouth closed, calm neutral expression, direct eye contact in the front-facing panels.
Chest-up framing in every panel with clear empty space above the head.
Soft even studio lighting, sharp focus on the eyes, plain pure white seamless background.
No text, no captions, no labels, no numbers, no letters, no arrows, no watermark, no border, no logo."""


def main():
    ref = Path(sys.argv[1]) if len(sys.argv) > 1 else ASSETS / "host_me_ref_1k.jpg"
    tries = int(sys.argv[2]) if len(sys.argv) > 2 else 3
    for i in range(tries):
        gen(ROW7, ASSETS / f"host_me_7view_strip_{i}.jpg", ref, width=2048, height=880, seed=20261141 + i * 11)


if __name__ == "__main__":
    main()
