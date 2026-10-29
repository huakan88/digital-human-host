#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""把模型生成的一排人物图拆成单视图，再自己拼成标准七视图（4+3，纯白底，无文字）。

为什么自己拼：image-01 的 subject_reference 一张图里最多给 6 个稳定一致的全身像，
角度也听指挥（实测会丢角度、加编号、全变正面）。所以：
    1) 从最好的一排图里检测出每个人像的列区间（按前景像素的列投影切）
    2) 从另一排里补一个缺的角度
    3) 统一"人物高度"后拼成 7 格

用法：python sheet_build.py
"""
import subprocess
import sys
from pathlib import Path

import numpy as np
from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parent))
import backend as B  # noqa: E402

ASSETS = B.SKILL / "assets"
OUT_SHEET = ASSETS / "host_me_7view.jpg"
OUT_DIR = ASSETS / "host_me_views"
CELL_W, CELL_H = 432, 768
FIG_H = 700          # 统一后人物高度
N_TOP = 4


def foreground_mask(arr, tol=6):
    """tol 是每通道的百分比容差（6 ≈ 偏离背景 6% 以上算前景）"""
    bg = np.median(np.concatenate([
        arr[0:10, 0:10].reshape(-1, 3), arr[0:10, -10:].reshape(-1, 3),
        arr[-10:, 0:10].reshape(-1, 3), arr[-10:, -10:].reshape(-1, 3)]), axis=0)
    diff = np.abs(arr.astype(np.int16) - bg.astype(np.int16)).max(axis=2)
    return diff > (255 * tol / 100.0)


def column_runs(mask, min_gap=12, min_px=6):
    cols = (mask.sum(axis=0) > min_px).astype(np.int8)
    runs, start = [], None
    for i, v in enumerate(cols):
        if v and start is None:
            start = i
        elif not v and start is not None:
            runs.append((start, i))
            start = None
    if start is not None:
        runs.append((start, len(cols)))
    # 合并间隔过小的碎块
    merged = []
    for r in runs:
        if merged and r[0] - merged[-1][1] < min_gap:
            merged[-1] = (merged[-1][0], r[1])
        else:
            merged.append(r)
    return merged


def figure_bbox(sub_mask):
    ys, xs = np.where(sub_mask)
    if len(ys) == 0:
        return None
    return xs.min(), ys.min(), xs.max() + 1, ys.max() + 1


def cut_views(path, out_dir, prefix, tag=""):
    """从一排人物图里切出每个人像，返回 [(路径, 角度名)]"""
    im = Image.open(path).convert("RGB")
    arr = np.asarray(im)
    mask = foreground_mask(arr)
    runs = column_runs(mask)
    out_dir.mkdir(parents=True, exist_ok=True)
    outs = []
    for i, (x0, x1) in enumerate(runs, 1):
        sub = mask[:, x0:x1]
        bb = figure_bbox(sub)
        if bb is None:
            continue
        fx0, fy0, fx1, fy1 = bb
        pad = 6
        x0 = max(0, x0 + fx0 - pad); x1 = min(arr.shape[1], x0 + (fx1 - fx0) + 2 * pad)
        y0 = max(0, fy0 - pad); y1 = min(arr.shape[0], fy1 + pad)
        crop = im.crop((x0, y0, x1, y1))
        p = out_dir / f"{prefix}_{i}{tag}.jpg"
        crop.save(p, quality=94)
        outs.append((p, (fx1 - fx0) / max(1, (fy1 - fy0))))
    return outs


def normalize(path, out, fig_h=FIG_H):
    """把人物缩放到统一高度，贴到白底格子的底部居中"""
    im = Image.open(path).convert("RGB")
    arr = np.asarray(im)
    mask = foreground_mask(arr)
    bb = figure_bbox(mask)
    if bb is None:
        im.save(out)
        return out
    fx0, fy0, fx1, fy1 = bb
    person = im.crop((fx0, fy0, fx1, fy1))
    w, h = person.size
    scale = fig_h / h
    person = person.resize((max(1, int(w * scale)), fig_h), Image.LANCZOS)
    cell = Image.new("RGB", (CELL_W, CELL_H), (255, 255, 255))
    px = (CELL_W - person.size[0]) // 2
    cell.paste(person, (max(0, px), CELL_H - fig_h))
    cell.save(out, quality=94)
    return out


def stitch(cells, out):
    top = cells[:N_TOP]
    bot = cells[N_TOP:]
    tmp = Path(str(out) + ".parts")
    tmp.mkdir(exist_ok=True)
    args = []
    for p in top + bot:
        args += ["-i", str(p)]
    filt = ("[0][1][2][3]hstack=inputs=4[top];"
            f"[4][5][6]hstack=inputs=3,pad={CELL_W * 4}:{CELL_H}:(ow-iw)/2:0:white[bot];"
            "[top][bot]vstack=inputs=2[out]")
    cmd = ["ffmpeg", "-loglevel", "error", "-y"] + args + ["-filter_complex", filt, "-map", "[out]", "-q:v", "3", str(out)]
    subprocess.run(cmd, check=True)
    for p in tmp.glob("*"):
        p.unlink()
    tmp.rmdir()
    return out


def main():
    main_row = ASSETS / "host_me_7view_full.jpg"     # 6 格：正面 / 3-4 / 正面 / 侧 / 背 / 侧
    extra_row = ASSETS / "host_me_7view_row7_3.jpg"  # 里有干净的背面 3-4
    work = ASSETS / "_sheet_work"
    work.mkdir(exist_ok=True)

    views = cut_views(main_row, work, "m")
    print(f"主排切出 {len(views)} 个")
    extras = cut_views(extra_row, work, "x")
    print(f"备用排切出 {len(extras)} 个")

    picked = views[:6]
    if extras:
        # 备用排里取第 4 个（背面 3-4），补第 7 格
        back = extras[min(3, len(extras) - 1)]
        picked.append(back)
        print(f"第 7 格取自备用排：{back[0].name}")

    cells = []
    OUT_DIR.mkdir(exist_ok=True)
    for i, (p, _) in enumerate(picked, 1):
        cell = work / f"cell{i}.jpg"
        normalize(p, cell)
        cells.append(cell)
        Image.open(p).save(OUT_DIR / f"view_{i}.jpg", quality=94)
    stitch(cells, OUT_SHEET)
    print(f"✓ {OUT_SHEET.name}  {OUT_SHEET.stat().st_size} bytes")
    print(f"✓ 单视图 {OUT_DIR}/view_1..{len(cells)}.jpg")


if __name__ == "__main__":
    main()
