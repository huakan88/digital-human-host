#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""本地口型修复：按「局部偏移曲线」把画面重新对齐到音轨。

思路
----
出画模型的问题不是"完全不理音频"（那样就该重出），而是两件事：
  1. 整段有一个固定偏移（实测 -333ms ~ +375ms，每段不同）
  2. 段内越往后越松（前 5 秒 corr 0.58，后 5 秒 0.34）

这两件本质上都是**时间轴错位**，不是嘴型画错。所以不需要重训/换模型，
只要把画面按测出来的偏移曲线重新切片对齐就行 —— 纯 ffmpeg，本地几秒钟一段。

做法
----
1. 分析：把片段缩到 160×160 灰度 + 抽音频包络（1/24 秒一格）
2. 在固定候选小块里找「和音频最相关」的那一块（那就是嘴）
3. 滑窗（1.5 秒窗、0.5 秒步）测每个窗的最优延迟，再中值平滑成偏移曲线
4. 修复：按 0.5 秒一段，从源片段的 t+lag(t) 处取画面，重新拼成同样长度

用法
----
python scripts/lipsync_repair.py --dir gen --out gen/fixed [--window 1.5] [--hop 0.5]
输出 gen/fixed/renoise-*.mp4；build_media 会自动优先用它们。
"""
import argparse
import json
import shutil
import subprocess
import tempfile
from pathlib import Path

import numpy as np

S = 160          # 分析分辨率
MAX_LAG = 8      # 搜索 ±8 帧（±333ms @24fps）


def sh(a):
    return subprocess.run(a, capture_output=True, check=False)


def video_fps(v, default=24.0):
    out = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0",
                          "-show_entries", "stream=r_frame_rate", "-of", "csv=p=0", str(v)],
                         capture_output=True, text=True).stdout.strip()
    try:
        a, b = out.split("/")
        return float(a) / float(b)
    except Exception:
        return default


def load(video, fps):
    with tempfile.TemporaryDirectory() as td:
        f = Path(td) / "f.raw"
        sh(["ffmpeg", "-v", "error", "-y", "-i", str(video),
            "-vf", f"scale={S}:{S},format=gray", "-f", "rawvideo", str(f)])
        b = f.read_bytes()
        a = Path(td) / "a.raw"
        sh(["ffmpeg", "-v", "error", "-y", "-i", str(video), "-vn", "-ac", "1", "-ar", "48000",
            "-f", "f32le", str(a)])
        x = np.frombuffer(a.read_bytes(), dtype=np.float32)
    n = len(b) // (S * S)
    if n < 8:
        return None, None
    fr = np.frombuffer(b[:n * S * S], dtype=np.uint8).reshape(n, S, S).astype(np.float32)
    per = int(48000 // fps)
    m = len(x) // per
    env = np.abs(x[:m * per].reshape(m, per)).mean(axis=1)
    if len(env) < n:
        env = np.pad(env, (0, n - len(env)))
    return fr, env[:n]


def corr_at(dark, env, lag):
    if lag >= 0:
        a, b = env[:len(env) - lag], dark[lag:]
    else:
        a, b = env[-lag:], dark[:len(dark) + lag]
    k = min(len(a), len(b))
    if k < 12:
        return -9
    a, b = a[:k] - a[:k].mean(), b[:k] - b[:k].mean()
    s = a.std() * b.std()
    return float((a * b).mean() / s) if s > 1e-9 else -9


def find_mouth(fr, env):
    """全片范围找「和音频最相关」的小块 = 嘴。"""
    n = len(fr)
    best = (0, -9, None)
    for bh in (0.12, 0.16, 0.20):
        for cy in np.arange(0.34, 0.78, 0.06):
            for cx in np.arange(0.34, 0.70, 0.08):
                bw = 0.28
                x0 = int((cx - bw / 2) * S); y0 = int((cy - bh / 2) * S)
                w0, h0 = int(bw * S), int(bh * S)
                if x0 < 0 or y0 < 0 or x0 + w0 > S or y0 + h0 > S:
                    continue
                reg = fr[:, y0:y0 + h0, x0:x0 + w0]
                dark = (reg <= np.percentile(reg, 20)).mean(axis=(1, 2))
                for lag in range(-MAX_LAG, MAX_LAG + 1):
                    c = corr_at(dark, env, lag)
                    if c > best[1]:
                        best = (lag, c, (x0, y0, w0, h0))
    return best


def lag_curve(fr, env, box, fps, window=1.5, hop=0.5):
    """滑窗测偏移，返回 [(t_start, lag_frames, corr)] + 中值平滑后的曲线。"""
    x0, y0, w0, h0 = box
    reg = fr[:, y0:y0 + h0, x0:x0 + w0]
    dark = (reg <= np.percentile(reg, 20)).mean(axis=(1, 2))
    W = max(12, int(round(window * fps)))
    H = max(4, int(round(hop * fps)))
    n = len(fr)
    raw = []
    t = 0
    while t + W <= n:
        best = (0, -9)
        for lag in range(-MAX_LAG, MAX_LAG + 1):
            c = corr_at(dark[t:t + W], env[t:t + W], lag)
            if c > best[1]:
                best = (lag, c)
        raw.append((t, best[0], best[1]))
        t += H
    if not raw:
        return [], []
    # 中值平滑（窗口 5），压掉单窗噪声
    lags = np.array([r[1] for r in raw], dtype=float)
    sm = lags.copy()
    for i in range(len(lags)):
        a, b = max(0, i - 2), min(len(lags), i + 3)
        sm[i] = np.median(lags[a:b])
    curve = [(raw[i][0], int(sm[i])) for i in range(len(raw))]
    return raw, curve


def score_clip(video):
    """给一个片段打「同步分」：整窗偏移 + 可信子窗最大偏移（越小越好）。
    可信 = 相关系数 ≥ 0.40 的子窗；说话少的小窗估计本身是噪声，不采信。"""
    fps = video_fps(video)
    fr, env = load(video, fps)
    if fr is None:
        return None
    lag0, c0, box = find_mouth(fr, env)
    raw, curve = lag_curve(fr, env, box, fps)
    trusted = [abs(r[1]) for r in raw if r[2] >= 0.40]
    sub_max = max(trusted) if trusted else 0
    return {"fps": fps, "lag": lag0, "corr": round(c0, 3),
            "sub_max": sub_max, "n_trusted": len(trusted), "n_sub": len(raw),
            "score": abs(lag0) + sub_max}


def repair(video, out, curve, fps, hop, crf=16):
    """按曲线重切：每条输出段从源 t+lag 处取 hop 秒。"""
    n_seg = len(curve)
    if n_seg == 0:
        sh(["ffmpeg", "-v", "error", "-y", "-i", str(video), "-c", "copy", str(out)])
        return
    with tempfile.TemporaryDirectory() as td:
        td = Path(td)
        parts = []
        for k, (t, lag) in enumerate(curve):
            dur = hop if k < n_seg - 1 else None
            start = max(0.0, t / fps + lag / fps)
            o = td / f"s{k:03d}.mp4"
            cmd = ["ffmpeg", "-v", "error", "-y", "-ss", f"{start:.6f}", "-i", str(video)]
            if dur is not None:
                cmd += ["-t", f"{dur:.6f}"]
            cmd += ["-vf", f"fps={fps},tpad=stop_mode=clone:stop_duration=1",
                    "-an", "-c:v", "libx264", "-crf", str(crf), "-preset", "medium", str(o)]
            sh(cmd)
            if o.exists() and o.stat().st_size > 1000:
                parts.append(o)
        if not parts:
            return
        lst = td / "l.txt"
        lst.write_text("".join(f"file '{p.as_posix()}'\n" for p in parts), encoding="utf-8")
        sh(["ffmpeg", "-v", "error", "-y", "-f", "concat", "-safe", "0", "-i", str(lst),
            "-c:v", "libx264", "-crf", str(crf), "-preset", "medium",
            "-pix_fmt", "yuv420p", "-r", str(fps), str(out)])
        # 把原音轨接回去（后续 build_media 只用画面，这里保留便于单独验收）
        if out.exists():
            tmp = out.with_suffix(".mux.mp4")
            sh(["ffmpeg", "-v", "error", "-y", "-i", str(out), "-i", str(video),
                "-map", "0:v:0", "-map", "1:a:0", "-c:v", "copy", "-c:a", "aac", "-shortest", str(tmp)])
            if tmp.exists():
                tmp.replace(out)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dir", default="gen")
    ap.add_argument("--out", default="gen/fixed")
    ap.add_argument("--window", type=float, default=1.5)
    ap.add_argument("--hop", type=float, default=0.5)
    ap.add_argument("--report", default="gen/repair.json")
    a = ap.parse_args()
    D, O = Path(a.dir), Path(a.out)
    O.mkdir(parents=True, exist_ok=True)
    clips = sorted(D.glob("renoise-*.mp4"))
    print(f"修复 {len(clips)} 段（窗 {a.window}s / 步 {a.hop}s）…")
    rep = {}
    for p in clips:
        fps = video_fps(p)
        fr, env = load(p, fps)
        if fr is None:
            continue
        lag0, c0, box = find_mouth(fr, env)
        raw, curve = lag_curve(fr, env, box, fps, a.window, a.hop)
        out = O / p.name
        base_score = score_clip(p)
        best_score, best_src, passes = base_score["score"], p, 0
        cur = p
        for it in range(2):                       # 最多两轮，每轮在上一轮结果上继续修
            fr_c, env_c = load(cur, fps)
            if fr_c is None:
                break
            lag_c, c_c, box_c = find_mouth(fr_c, env_c)
            raw_c, curve_c = lag_curve(fr_c, env_c, box_c, fps, a.window, a.hop)
            cand = Path(str(out) + f".p{it}.mp4")
            repair(cur, cand, curve_c, fps, a.hop)
            if not cand.exists():
                break
            sc = score_clip(cand)
            if sc and sc["score"] < best_score:
                best_score, best_src, passes = sc["score"], cand, it + 1
                cur = cand
            else:
                cand.unlink(missing_ok=True)
                break
        if best_src != p:
            shutil.copyfile(best_src, out)
            kept_original = False
            after = score_clip(out)
        else:
            shutil.copyfile(p, out)
            kept_original = True
            after = base_score
        for q in O.glob(p.name + ".p*.mp4"):
            q.unlink(missing_ok=True)
        lags = [c[1] for c in curve]
        rep[p.name] = {"kept_original": kept_original, "passes": passes, "fps": fps, "frames": len(fr),
                       "score_before": base_score["score"], "score_after": best_score,
                       "global_lag_before": lag0, "global_corr_before": round(c0, 3),
                       "global_lag_after": (after or {}).get("lag"),
                       "curve": [{"t": round(t / fps, 2), "lag": l} for t, l in curve],
                       "lag_min": min(lags) if lags else 0, "lag_max": max(lags) if lags else 0}
        print(f"  {p.name:24s} 分 {base_score['score']} → {best_score}（{passes} 轮，"
              f"{'保留原片' if kept_original else '已修'}）  整窗 lag {lag0:+d} → {(after or {}).get('lag')}")
    Path(a.report).write_text(json.dumps(rep, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"\n写入 {a.out}/ 与 {a.report}")
    sb = [v["score_before"] for v in rep.values()]
    sa = [v["score_after"] for v in rep.values()]
    if sb and sa:
        print(f"同步分均值：修前 {np.mean(sb):.2f} → 修后 {np.mean(sa):.2f}（越低越好）")


if __name__ == "__main__":
    main()
