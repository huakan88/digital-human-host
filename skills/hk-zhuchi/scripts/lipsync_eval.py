#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""口型同步度评估：把视频里"嘴张开程度"和音频能量按帧对齐，算相关性。

用法：
    python lipsync_eval.py <video.mp4> <audio.wav> [--box x0,y0,x1,y1] [--sheet out.png]

原理（够用就好，不追求学术精度）：
  嘴张开时口腔是画面里最暗的一块，所以用「下半脸区域里极暗像素的比例」当开口度代理。
  再算音频每帧的 RMS 包络，两者做归一化互相关：
    corr 越接近 1 → 口型和声音越同步；best_lag 接近 0 → 没有整体延迟。
"""
import argparse
import subprocess
import sys
from pathlib import Path

import numpy as np


def read_audio(wav, sr=16000):
    p = subprocess.run(["ffmpeg", "-loglevel", "error", "-i", str(wav), "-f", "s16le", "-ac", "1", "-ar", str(sr), "-"],
                       capture_output=True)
    return np.frombuffer(p.stdout, dtype=np.int16).astype(np.float32) / 32768.0, sr


def read_frames(video, box=None, max_side=640):
    """抽帧并裁出下半脸区域"""
    cmd = ["ffmpeg", "-loglevel", "error", "-i", str(video), "-vf", f"scale={max_side}:-2", "-f", "rawvideo", "-pix_fmt", "gray", "-"]
    raw = subprocess.run(cmd, capture_output=True).stdout
    # 探测原始帧尺寸
    probe = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0",
                            "-show_entries", "stream=width,height", "-of", "csv=p=0", str(video)],
                           capture_output=True, text=True).stdout.strip().split(",")
    ow, oh = int(probe[0]), int(probe[1])
    nw = max_side
    nh = int(round(oh * nw / ow / 2)) * 2
    frames = np.frombuffer(raw, dtype=np.uint8).reshape(-1, nh, nw)
    if box is None:
        # 默认取下半脸中间一块（嘴在下半脸）
        x0, x1 = int(nw * 0.33), int(nw * 0.67)
        y0, y1 = int(nh * 0.46), int(nh * 0.62)
    else:
        x0, y0, x1, y1 = [int(v) for v in box.split(",")]
    crops = frames[:, y0:y1, x0:x1].astype(np.float32)
    return crops, len(frames), (nw, nh), frames


def auto_mouth_box(frames):
    """自动定位嘴部：在下半脸区域里找"时间上最活跃"的那块。

    不要用"最暗的地方"——脖子阴影比嘴更暗，会定位错。
    嘴是说话时变化最剧烈的区域（眼睛会眨，但被限制在下半脸范围内），
    所以找时间标准差最大的窗口。
    """
    n = len(frames)
    h, w = frames.shape[1], frames.shape[2]
    y0, y1 = int(h * 0.38), int(h * 0.60)
    x0, x1 = int(w * 0.25), int(w * 0.75)
    roi = frames[:, y0:y1, x0:x1].astype(np.float32)
    std = roi.std(axis=0)
    kw, kh = int(w * 0.16), int(h * 0.07)
    best, bxy = -1, (0, 0)
    for yy in range(0, max(1, std.shape[0] - kh), max(1, kh // 3)):
        for xx in range(0, max(1, std.shape[1] - kw), max(1, kw // 3)):
            v = std[yy:yy + kh, xx:xx + kw].sum()
            if v > best:
                best, bxy = v, (xx, yy)
    return (x0 + bxy[0], y0 + bxy[1], x0 + bxy[0] + kw, y0 + bxy[1] + kh)


def openness(crops):
    """每帧的"嘴张开程度"代理。

    不要用"暗像素比例"：嘴张开露牙时，牙是亮的，暗像素反而变少，会把张开算成闭合。
    正确做法是看"这一帧和静止状态差多少"：
      闭嘴 → 整块都是皮肤色，偏离小；
      张嘴（露口腔 或 露牙）→ 偏离大。
    """
    med = np.median(crops, axis=0)                      # 时间中位 ≈ 静止的嘴
    dev = np.abs(crops - med)
    thr = max(16.0, float(dev.std()) * 2.0)
    return (dev > thr).reshape(len(crops), -1).mean(axis=1)


def envelope(audio, sr, n_frames, fps):
    per = max(1, int(sr / fps))
    usable = (len(audio) // per) * per
    e = audio[:usable].reshape(-1, per)
    rms = np.sqrt((e ** 2).mean(axis=1))
    if len(rms) < n_frames:
        rms = np.pad(rms, (0, n_frames - len(rms)))
    return rms[:n_frames]


def corr_at_lag(a, b, lag):
    if lag >= 0:
        x, y = a[lag:], b[:len(b) - lag]
    else:
        x, y = a[:len(a) + lag], b[-lag:]
    n = min(len(x), len(y))
    if n < 10:
        return 0.0
    x, y = x[:n], y[:n]
    x = x - x.mean(); y = y - y.mean()
    d = (np.linalg.norm(x) * np.linalg.norm(y))
    return float((x * y).sum() / d) if d > 1e-9 else 0.0


def scan_best_box(crops, env, fps, grid=5):
    """在下半脸范围里扫一遍框子，挑相关性最高的（避免框错位置导致误判）"""
    h, w = crops.shape[1], crops.shape[2]
    best = None
    for yi in range(3):
        for xi in range(4):
            x0 = int(w * (0.22 + 0.13 * xi)); x1 = int(w * (0.22 + 0.13 * xi + 0.26))
            y0 = int(h * (0.34 + 0.10 * yi)); y1 = int(h * (0.34 + 0.10 * yi + 0.16))
            if x1 > w or y1 > h:
                continue
            m = openness(crops[:, y0:y1, x0:x1])
            voiced = env > (env.max() * 0.12)
            if not voiced.any():
                continue
            c = max(corr_at_lag(m[voiced], env[voiced], l) for l in range(-10, 11))
            if best is None or c > best[0]:
                best = (c, (x0, y0, x1, y1))
    return best


def plot_alignment(mouth, env, fps, out):
    """画一张对照图：上=音频能量，下=嘴部开合，横轴都是时间。
    两条曲线峰值对得上 → 口型跟得上；错开 → 就是有延迟/没同步。"""
    from PIL import Image, ImageDraw
    W, H = 1000, 460
    im = Image.new("RGB", (W, H), (255, 255, 255))
    d = ImageDraw.Draw(im)
    n = len(mouth)
    pad_l, pad_r, pad_t = 40, 12, 14
    plot_w = W - pad_l - pad_r
    half = (H - pad_t * 3) // 2

    def curve(vals, top, height, color, fill):
        mx = max(1e-6, float(np.max(vals)))
        pts = [(pad_l + i * plot_w / max(1, len(vals) - 1), top + height - (v / mx) * height)
               for i, v in enumerate(vals)]
        if fill:
            d.polygon(pts + [(pad_l + plot_w, top + height), (pad_l, top + height)], fill=fill)
        d.line(pts, fill=color, width=2)

    curve(env, pad_t, half, (30, 90, 220), (170, 200, 250))
    curve(mouth, pad_t * 2 + half, half, (230, 90, 20), (250, 200, 180))
    d.rectangle([pad_l, pad_t, pad_l + plot_w, pad_t + half], outline=(120, 120, 120))
    d.rectangle([pad_l, pad_t * 2 + half, pad_l + plot_w, pad_t * 2 + half * 2], outline=(120, 120, 120))
    d.text((6, pad_t + half // 2 - 6), "音频", fill=(30, 90, 220))
    d.text((6, pad_t * 2 + half + half // 2 - 6), "嘴部开合", fill=(230, 90, 20))
    step = max(1, n // 10)
    for i in range(0, n, step):
        x = pad_l + i * plot_w / max(1, n - 1)
        d.line([x, pad_t + half, x, pad_t + half + 4], fill=(120, 120, 120))
        d.text((x - 6, pad_t + half + 6), f"{i/fps:.1f}", fill=(90, 90, 90))
    im.save(out)
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("video")
    ap.add_argument("audio", nargs="?", default=None, help="不给就抽视频自带音轨")
    ap.add_argument("--box", default=None, help="嘴部区域 x0,y0,x1,y1（基于缩放后帧）")
    ap.add_argument("--sheet", default=None, help="顺便输出嘴部帧条")
    ap.add_argument("--plot", default=None, help="输出音频 vs 嘴部开合 对照图")
    ap.add_argument("--scan", action="store_true", help="自动扫框，取相关性最高的位置")
    ap.add_argument("--auto", action="store_true", default=True, help="自动定位嘴部（默认开）")
    ap.add_argument("--no-auto", dest="auto", action="store_false")
    ap.add_argument("--fps", type=float, default=30.0)
    a = ap.parse_args()

    crops, n_frames, dims, frames = read_frames(a.video, a.box)
    if a.audio:
        audio, sr = read_audio(a.audio)
    else:
        audio, sr = read_audio(a.video)   # 用视频自带音轨（云端 H3 原生口播就是这种）
    if not a.box and a.auto:
        mb = auto_mouth_box(frames)
        if mb:
            x0, y0, x1, y1 = mb
            crops = frames[:, y0:y1, x0:x1].astype(np.float32)
            print(f"自动定位嘴部：{mb}（在 {dims} 帧里）")
    mouth = openness(crops)
    env = envelope(audio, sr, n_frames, a.fps)

    # 只在有声区间里评估
    voiced = env > (env.max() * 0.12)
    lags = range(-24, 25)
    scores = {l: corr_at_lag(mouth[voiced], env[voiced], l) for l in lags}
    best_lag = max(scores, key=scores.get)
    best = scores[best_lag]
    zero = scores[0]

    # 静音时嘴应该闭合：算静音段的开口度 vs 有声段
    quiet = env <= (env.max() * 0.08)
    m_open = float(mouth[voiced].mean()) if voiced.any() else 0.0
    q_open = float(mouth[quiet].mean()) if quiet.any() else 0.0

    print(f"帧数 {n_frames}  采样 {dims}")
    print(f"口型-音频 相关性：best_lag={best_lag} 帧 ({best_lag / a.fps * 1000:+.0f} ms)  corr={best:.3f}   lag0 corr={zero:.3f}")
    print(f"开口度：有声段 {m_open:.4f}   静音段 {q_open:.4f}   （差值 {m_open - q_open:+.4f}，越大越像在说话）")
    if a.scan:
        sc = scan_best_box(crops, env, a.fps)
        if sc:
            print(f"自动扫框最佳：box={sc[1]}  corr={sc[0]:.3f}")
    if a.plot:
        plot_alignment(mouth, env, a.fps, a.plot)
        print(f"对齐对照图 → {a.plot}")
    if a.sheet:
        from PIL import Image
        k = min(len(crops), 24)
        idx = np.linspace(0, len(crops) - 1, k).astype(int)
        h, w = crops.shape[1], crops.shape[2]
        sheet = np.concatenate([crops[i] for i in idx], axis=1).astype(np.uint8)
        Image.fromarray(sheet).save(a.sheet)
        print(f"嘴部帧条 → {a.sheet}（{k} 帧，每 {1/a.fps:.3f}s）")


if __name__ == "__main__":
    main()
