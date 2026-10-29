#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""组装本期素材：
  narration.wav  旁白总轨（各段 huakan 配音 + 0.25s 停顿）
  cut/sN.wav     各段旁白（给回听/逐字时间轴用）
  cut/sN.json    各段 FunASR 逐字（whisper-cli 兼容层产出）
  cut/qa.json    回听质量（给上游 align.py 用）
  main.mp4       主画面：开场数字人全屏 → 跳跳猫素材（竖版，模糊底 + 完整画面）
  pip.mp4        左下角小窗：数字人 PiP 段（静音）
  之后用上游 align.py 生成 tl.json
"""
import json
import os
import re
import subprocess
import sys
from pathlib import Path

PROJ = Path(os.environ.get("HK_PROJECT", Path.cwd())).resolve()
SKILL = Path(os.environ.get("HK_PRESET", Path(__file__).resolve().parent.parent)).resolve()
CAT = Path(os.environ.get("HK_CAT_CLIPS", r"E:\minimax H3\002_全世界家猫只有一个祖先_跳跳项目\video\final"))
W, H, FPS = 1080, 1920, 30
GAP = 0.25
# --full：全程放大（主画面就是数字人全屏，花字叠在上面）。小窗口型的保险方案。
FULL_SCREEN = "--full" in sys.argv


def run(cmd, **kw):
    r = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace", **kw)
    if r.returncode:
        raise RuntimeError(f"{cmd[:3]} 失败：{(r.stderr or r.stdout)[-400:]}")
    return r.stdout


def dur(p):
    return float(run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(p)]).strip())


CN_NUM = {"零": "0", "一": "1", "二": "2", "两": "2", "三": "3", "四": "4",
           "五": "5", "六": "6", "七": "7", "八": "8", "九": "9"}
UNITS = {"十": 10, "百": 100, "千": 1000}
BIG = {"万": 10000, "亿": 100000000}


def _cn_int(s):
    """中文数字串 → 阿拉伯数字（最多到亿），失败返回 None"""
    total = section = num = 0
    for ch in s:
        if ch in CN_NUM:
            num = int(CN_NUM[ch])
        elif ch in UNITS:
            section += (num or 1) * UNITS[ch]
            num = 0
        elif ch in BIG:
            section = (section + num) * BIG[ch]
            total += section
            section = num = 0
        else:
            return None
    v = total + section + num
    return v if v else None


def cn_to_digits(text):
    """把 ASR 里的中文数字还原成阿拉伯数字，好让逐字对齐能对上稿子。
    （ASR 写「九百七十九」，稿子写「979」——发音一样，字不一样。）"""
    out, i = [], 0
    while i < len(text):
        if text[i] in CN_NUM or text[i] in UNITS or text[i] in BIG:
            j = i
            while j < len(text) and (text[j] in CN_NUM or text[j] in UNITS or text[j] in BIG):
                j += 1
            seg = text[i:j]
            whole = _cn_int(seg)
            if whole is not None:
                out.append(str(whole))
            else:                      # 带小数：十三点一
                if "点" in seg:
                    a, _, b = seg.partition("点")
                    w = _cn_int(a) if a else 0
                    frac = "".join(CN_NUM.get(c, c) for c in b)
                    if w is not None and frac.isdigit():
                        out.append(f"{w}.{frac}")
                    else:
                        out.append(seg)
                else:
                    out.append(seg)
            i = j
        else:
            out.append(text[i])
            i += 1
    return "".join(out)


def convert_word(w):
    """单个中文词 → 阿拉伯数字。只在「确实是数字」时才转：
    一/两 单独成词（一个/一条/一只）不是数字，不能转；「十三万」要转成「13万」而不是 130000。"""
    if not re.fullmatch(r"[零一二两三四五六七八九十百千万亿点]+", w):
        return w
    m = re.fullmatch(r"([零一二两三四五六七八九十百千]+)(万|亿)", w)
    if m:
        v = _cn_int(m.group(1))
        return f"{v}{m.group(2)}" if v else w
    if "点" in w:
        a, _, b = w.partition("点")
        whole = _cn_int(a) if a else 0
        frac = "".join(CN_NUM.get(c, "") for c in b)
        if whole is not None and frac.isdigit() and len(b) == len(frac):
            return f"{whole}.{frac}"
        return w
    v = _cn_int(w)
    if v is None or v < 10:      # 一个 / 一条 / 一只 —— 不转
        return w
    return str(v)


def normalize_tokens(tokens):
    """把逐字 ASR token 里「中文数字串」还原成阿拉伯数字，时间按新字数摊开。
    （ASR 写「九百七十九」，稿子写「979」——读音一样，字不一样，逐字对齐要对上才行。）"""
    NUMCH = set(CN_NUM) | set(UNITS) | set(BIG) | {"点"}
    out = []
    numrun = ["", None, None]      # [text, from, to]

    def emit_run():
        if not numrun[0]:
            return
        w, wf, wt = numrun
        conv = convert_word(w)
        span = max(0, wt - wf)
        if len(conv) == len(w) and len(w) > 1:
            for i, ch in enumerate(conv):
                out.append({"text": ch, "offsets": {"from": int(wf + span * i / len(conv)),
                                                    "to": int(wf + span * (i + 1) / len(conv))}})
        else:
            out.append({"text": conv, "offsets": {"from": int(wf), "to": int(wt)}})
        numrun[0], numrun[1], numrun[2] = "", None, None

    for tk in tokens:
        t = tk["text"]
        if not t.strip():
            continue
        f, to = tk["offsets"]["from"], tk["offsets"]["to"]
        if len(t) == 1 and t in NUMCH:
            numrun[0] += t
            numrun[1] = f if numrun[1] is None else numrun[1]
            numrun[2] = to
            continue
        emit_run()
        out.append({"text": t, "offsets": {"from": int(f), "to": int(to)}})
    emit_run()
    return out


ALIASES = {}
ALIGN = {}
NUDGE = {}          # gen/nudge.json：{段id: 帧数}，人工微调（正=画面往后推）


def load_nudge():
    f = Path(os.environ.get("HK_PROJECT", Path.cwd())) / "gen" / "nudge.json"
    if f.exists():
        try:
            NUDGE.update(json.loads(f.read_text(encoding="utf-8")))
            print(f"· 手动微调 {len(NUDGE)} 段：{NUDGE}")
        except Exception as e:
            print("! nudge.json 读取失败：", e)
    return NUDGE


def load_align():
    """gen/align.json：每段出画相对自己音轨的偏移（由 scripts/lipsync_align.py 量出）。
    不同段偏移能差到 ±1/3 秒，不补的话就是"有的段对得上、有的段对不上"。"""
    f = Path(os.environ.get("HK_PROJECT", Path.cwd())) / "gen" / "align.json"
    if f.exists():
        try:
            ALIGN.update(json.loads(f.read_text(encoding="utf-8")))
            print(f"· 已加载逐段口型偏移 {len(ALIGN)} 条")
        except Exception as e:
            print("! align.json 读取失败：", e)
    return ALIGN


def load_aliases():
    """项目目录下的 aliases.json：把 ASR 的写法映射回稿子的写法。

    ASR 会把数字和术语写成读音（471→四七一、ExoFlo→XOflow、III 期→LI一七、百分之→100分之），
    读音一样但字不一样，逐字对齐就匹配不上。用别名表把它们换回来，
    字幕时间轴才会落在正确的字上。
    """
    f = PROJ / "aliases.json"
    if f.exists():
        try:
            ALIASES.update(json.loads(f.read_text(encoding="utf-8")))
        except Exception as e:
            print("! aliases.json 读取失败：", e)
    return ALIASES


def apply_aliases(text):
    if not ALIASES:
        return text
    for a, b in ALIASES.items():
        text = text.replace(a, b)
    return text


def apply_aliases_to_tokens(tokens):
    """把别名表作用到整段文本上，再按 difflib 把新字符对回原来的时间轴。

    token 是逐字的，别名又是多字的（XOflow→ExoFlo、100分之→百分之），
    所以必须先展平成「字符 + 时间」，替换后再用 difflib 回填时间；
    替换掉的部分用邻居插值。
    """
    if not ALIASES:
        return tokens
    import difflib
    chars, times = [], []
    for tk in tokens:
        t = tk["text"]
        if not t.strip():
            continue
        f, to = tk["offsets"]["from"], tk["offsets"]["to"]
        span = (to - f) / max(1, len(t))
        for i, ch in enumerate(t):
            chars.append(ch)
            times.append((f + span * i, f + span * (i + 1)))
    old = "".join(chars)
    new = apply_aliases(old)
    if new == old:
        return tokens
    nt = [None] * len(new)
    for a, b, size in difflib.SequenceMatcher(None, old, new, autojunk=False).get_matching_blocks():
        for k in range(size):
            nt[b + k] = times[a + k]
    known = [i for i, v in enumerate(nt) if v]
    for i in range(len(nt)):
        if nt[i] is not None:
            continue
        lo = max([j for j in known if j < i], default=None)
        hi = min([j for j in known if j > i], default=None)
        if lo is None and hi is None:
            nt[i] = (0, 0)
        elif lo is None:
            nt[i] = nt[hi]
        elif hi is None:
            nt[i] = nt[lo]
        else:
            w = (i - lo) / (hi - lo)
            nt[i] = (nt[lo][0] + (nt[hi][0] - nt[lo][0]) * w, nt[lo][1] + (nt[hi][1] - nt[lo][1]) * w)
    return [{"text": ch, "offsets": {"from": int(a), "to": int(b)}} for ch, (a, b) in zip(new, nt)]


def main():
    global FULL_SCREEN
    load_aliases()
    load_align()
    load_nudge()
    S = json.loads((PROJ / "script.json").read_text(encoding="utf-8"))
    ids = json.loads((PROJ / "ids.json").read_text(encoding="utf-8"))  # 段 id → taskId
    cut = PROJ / "cut"; cut.mkdir(exist_ok=True)
    (PROJ / "public").mkdir(exist_ok=True)

    # ① 各段旁白 + 时长
    durs = []
    for s in S:
        w = PROJ / "voice" / f"{s['id']}.wav"
        durs.append(dur(w))

    # 把每段的时长**吸附到帧栅格**：slot_i = frames_i / FPS。
    # 画面只能整帧切，旁白却能精确到采样；两边不共用同一套栅格的话，
    # 每段都会多出 1~2 帧，几十段累计下来画面就慢慢追不上旁白
    # （表现就是「只有前几秒口型对得上」）。所以以帧为准，拿它反过来截旁白。
    frames = [max(1, int(round((d + GAP) * FPS))) for d in durs]
    slots = [f / FPS for f in frames]
    offs = [sum(slots[:i]) for i in range(len(slots))]

    # ①.5 把「装配真正使用的时间轴」写出来（帧栅格）。外部切窗口必须用这个，
    #     不能用配音原始时长 —— 每段 ±1/60 秒的取整会累积成几百毫秒。
    (PROJ / "public").mkdir(exist_ok=True)
    (PROJ / "public" / "timeline.json").write_text(json.dumps(
        [{"id": s["id"], "start": round(offs[i], 6), "end": round(offs[i] + slots[i], 6)}
         for i, s in enumerate(S)], ensure_ascii=False, indent=1), encoding="utf-8")

    # ② 旁白总轨（每段精确截到 slot_i，段间静音含在里面）
    inputs, parts, labels = [], [], []
    for i, s in enumerate(S):
        inputs += ["-i", str(PROJ / "voice" / f"{s['id']}.wav")]
        parts.append(f"[{i}:a]aresample=48000,aformat=sample_fmts=s16:channel_layouts=mono,"
                     f"apad,atrim=0:{slots[i]:.6f},asetpts=N/SR/TB[a{i}]")
        labels.append(f"[a{i}]")
    chain = ";".join(parts) + ";" + "".join(labels) + f"concat=n={len(S)}:v=0:a=1[out]"
    cmd = ["ffmpeg", "-loglevel", "error", "-y"] + inputs + ["-filter_complex", chain,
         "-map", "[out]", "-c:a", "pcm_s16le", str(PROJ / "narration.wav")]
    run(cmd)
    narr_d = dur(PROJ / "narration.wav")
    print(f"✓ narration.wav {narr_d:.2f}s（帧栅格总长 {sum(slots):.2f}s）")

    # ③ 切出每段 wav（与总轨对齐）+ ASR 逐字
    qa = []
    reuse = "--no-asr" in sys.argv and (cut / "qa.json").exists()
    if reuse:
        qa = json.loads((cut / "qa.json").read_text(encoding="utf-8"))
        print("· 复用已有 cut/（--no-asr），跳过 ASR")
    # ③ 切出每段 wav（与总轨对齐）+ 批量 ASR 逐字
    off = 0.0
    qa = []
    reuse = "--no-asr" in sys.argv and (cut / "qa.json").exists()
    if reuse:
        qa = json.loads((cut / "qa.json").read_text(encoding="utf-8"))
        print("· 复用已有 cut/（--no-asr），跳过 ASR")
    segs = []
    for i, s in enumerate(S):
        sid = s["id"]
        seg = cut / f"{sid}.wav"
        run(["ffmpeg", "-loglevel", "error", "-y", "-i", str(PROJ / "narration.wav"),
             "-ss", f"{offs[i]:.3f}", "-t", f"{slots[i]:.3f}", "-ac", "1", "-ar", "16000", str(seg)])
        segs.append(seg)

    if not reuse:
        # 一次跑完全部段：FunASR 模型只加载一次（单段要 ~40 秒，十段就是七八分钟）
        ENGINE = Path(__file__).resolve().parent
        ASR_PY = r"E:\AI\envs\voxcpm\Scripts\python.exe"
        if Path(ASR_PY).exists():
            run([ASR_PY, str(ENGINE / "asr_funasr.py"), "--batch", str(cut)] + [str(x) for x in segs])
        else:
            # 兜底：逐段调用 whisper-cli 兼容层
            shim = SKILL / "bin" / "whisper-cli.exe"
            if not shim.exists():
                shim = Path(__file__).resolve().parent.parent / "bin" / "whisper-cli.exe"
            for seg in segs:
                run([str(shim), "-m", "any", "-l", "zh", "--prompt", "以下是普通话的句子。", "-oj",
                     "-of", str(seg.with_suffix("")), "-f", str(seg)])
        import difflib
        clean = lambda x: "".join(ch for ch in x if ch.strip() and ch not in "，。、：；！？,.:;!?“”")
        for i, s in enumerate(S):
            sid = s["id"]
            jf = cut / f"{sid}.json"
            jd = json.loads(jf.read_text(encoding="utf-8"))
            jd["transcription"] = apply_aliases_to_tokens(normalize_tokens(jd["transcription"]))
            jf.write_text(json.dumps(jd, ensure_ascii=False, indent=1), encoding="utf-8")
            heard = "".join(t["text"] for t in jd["transcription"] if t["text"].strip())
            acc = difflib.SequenceMatcher(None, clean(s["t"]), clean(heard)).ratio()
            qa.append({"id": sid, "acc": round(acc, 3), "speech": [0.0, round(durs[i], 2)],
                        "keep": round(slots[i], 3), "src_dur": round(slots[i], 3), "heard": heard})
            print(f"  {sid} {durs[i]:.2f}s acc={acc:.0%} :: {heard}")
    (cut / "qa.json").write_text(json.dumps(qa, ensure_ascii=False, indent=1), encoding="utf-8")

    # ④ 主画面：开场数字人全屏（第一段）+ 正文画面
    #    正文画面有两种来源：
    #      card/<id>.png  证据版式（医学科普常用：数字 + 要点 + 来源行）
    #      素材库 clip_<cat>.mp4  实拍/生成素材（16:9 → 模糊底 + 完整画面竖版化）
    # 每个「段」对应到哪个片段、以及片段内的偏移秒。
    # 合并出画时一个片段盖住好几段，如果按「组」拼主画面，每组只贡献一个段间间隔，
    # 被合并掉的段就各少 0.25 秒 —— 累计到最后画面就追不上旁白（表现：只有前几秒口型对）。
    # 所以一律**按段切**：每段从组里取 [offset, offset+dur+GAP]，时间轴和旁白逐段对齐。
    _gfile = PROJ / "groups.json"
    _groups = json.loads(_gfile.read_text(encoding="utf-8")) if _gfile.exists() else None
    FIXED = PROJ / "gen" / "fixed"          # lipsync_repair.py 的产物：已按偏移曲线对齐

    def _pick(rel):
        """有修复版就用修复版（它已经对齐好了，不能再叠偏移）。"""
        p0 = PROJ / rel
        fx = FIXED / p0.name
        return (fx, True) if fx.exists() else (p0, False)

    seg_src = {}
    if _groups:
        for g in _groups:
            off = 0.0
            for sid in g["ids"]:
                k = next(k for k, s in enumerate(S) if s["id"] == sid)
                srcp, done = _pick(g["file"])
                seg_src[sid] = (srcp, off, done)
                off += slots[k]
    else:
        for s in S:
            srcp, done = _pick(f"gen/renoise-{ids[s['id']]}.mp4")
            seg_src[s["id"]] = (srcp, 0.0, done)
    nfix = sum(1 for v in seg_src.values() if v[2])
    if nfix:
        print(f"· 用上口型修复版片段 {nfix} 段")

    def seg_clip(i, tag):
        """从所在组里精确切出第 i 段，时长 = 该段旁白 + 一个间隔。
        这段没有出画素材（只生成了数字人那几段）时，退回画面卡。"""
        s = S[i]
        if s["id"] not in seg_src:
            return visual_clip(i)
        srcf, off, done = seg_src[s["id"]]
        out = PROJ / "tmp" / f"{tag}_{s['id']}.mp4"
        out.parent.mkdir(exist_ok=True)
        # tpad 冻最后一帧，把该段结尾的 0.25s 静音补满（源片段只到人声结束）
        # 该片段的实测嘴-音偏移（lag>0 = 嘴比声音晚 → 画面要提前取）
        lag_f = 0 if done else (ALIGN.get(srcf.name, {}).get("lag_frames", 0) or 0)
        lag_f += NUDGE.get(s["id"], 0)
        start = max(0.0, off + lag_f / FPS)
        lead = max(0.0, -(off + lag_f / FPS))      # 需要往前补的空档
        vf = f"scale={W}:{H}:flags=lanczos,tpad=stop_mode=clone:stop_duration=1,fps={FPS}"
        if lead > 0.001:
            vf = f"tpad=start_mode=clone:start_duration={lead:.3f}," + vf
        run(["ffmpeg", "-loglevel", "error", "-y", "-ss", f"{start:.6f}", "-i", str(srcf),
             "-frames:v", str(frames[i]), "-an", "-vf", vf,
             "-c:v", "libx264", "-crf", "18", "-preset", "medium", str(out)])
        return str(out)

    def visual_clip(i):
        """第 i 段的非数字人画面：证据卡 / 通用底版 / 素材，长度严格 = frames[i]。"""
        s = S[i]
        card = PROJ / "cards" / f"{s['id']}.png"
        if not card.exists() and s.get("card"):
            card = PROJ / f"{s['card']}.png"
        if not card.exists():
            card = PROJ / "backdrop.png"      # 通用底版：没有专门卡片时用
        out = PROJ / "tmp" / f"vis_{s['id']}.mp4"
        out.parent.mkdir(exist_ok=True)
        if card.exists():
            # 证据版式：原图已经是 1080x1920，铺满 + 极慢推近（避免整段死板）
            nf = frames[i]
            # zoompan 的裁切位置会被量化成整数像素，慢推近在文字卡上就是「走几帧不动、跳 1 像素」的抖。
            # 3 倍超采样后再缩放回来，抖动从 0.9px 压到 0.05px（实测）。
            SS = 3
            vf = (f"scale={W * SS}:{H * SS}:flags=lanczos,"
                  f"zoompan=z='min(zoom+{0.00022 / SS:.7f},1.03)':d={nf}:"
                  f"x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':s={W * SS}x{H * SS}:fps={FPS},"
                  f"scale={W}:{H}:flags=lanczos,format=yuv420p")
            run(["ffmpeg", "-loglevel", "error", "-y", "-loop", "1", "-i", str(card),
                 "-vf", vf, "-frames:v", str(nf), "-an",
                 "-c:v", "libx264", "-crf", "18", "-preset", "medium", str(out)])
        else:
            cat = CAT / f"clip_{s['cat']}.mp4"
            # 竖版：模糊底铺满 + 完整 16:9 画面居中偏上
            vf = (f"split[a][b];[a]scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H},"
                  f"gblur=sigma=26,eq=brightness=-0.05:saturation=0.92[bg];"
                  f"[b]scale={W}:-2[fg];[bg][fg]overlay=(W-w)/2:520:shortest=1,"
                  f"format=yuv420p,trim=duration={slots[i]:.3f},setpts=PTS-STARTPTS")
            run(["ffmpeg", "-loglevel", "error", "-y", "-i", str(cat), "-filter_complex", vf,
                 "-an", "-r", str(FPS), "-c:v", "libx264", "-crf", "18", "-preset", "medium", str(out)])
        return str(out)


    intro = PROJ / "gen" / f"renoise-{ids[S[0]['id']]}.mp4"
    total = sum(slots)
    host_intro = float(os.environ.get("HK_HOST_INTRO", "0") or 0)
    host_outro = float(os.environ.get("HK_HOST_OUTRO", "0") or 0)
    win_raw = (os.environ.get("HK_HOST_WINDOWS", "") or "").strip()
    host_windows = []
    for part in win_raw.split(","):
        part = part.strip()
        if "-" in part:
            a, b = part.split("-", 1)
            try:
                host_windows.append((float(a), float(b)))
            except ValueError:
                pass
    host_segs = set()
    _hs = PROJ / "gen" / "host_segs.json"
    if _hs.exists():
        try:
            host_segs = set(json.loads(_hs.read_text(encoding="utf-8")))
            print(f"· 露脸段（按 id）：{sorted(host_segs)}")
        except Exception as e:
            print("! host_segs.json 读取失败：", e)
    HYBRID = (host_intro > 0 or host_outro > 0 or bool(host_windows) or bool(host_segs))
    if HYBRID and not FULL_SCREEN:
        FULL_SCREEN = True          # 混合模式不要小窗
    parts = [] if FULL_SCREEN else [str(intro)]
    if FULL_SCREEN:
        # 数字人全屏：每段按段切，时间轴严丝合缝。
        # 配了 HK_HOST_INTRO / HK_HOST_OUTRO 时就只留开头结尾，中间换 Remotion 画面
        # （出画模型在长片段里口型会漂，露脸越久越容易看出来；中间用画面讲反而更稳）
        for i in range(len(S)):
            st, en = offs[i], offs[i] + slots[i]
            if host_segs:
                # 只按段 id 判定：时间范围比大小容易和帧栅格错开（实测踩过）
                use_host = S[i]["id"] in host_segs   # 注意：这里必须用 S[i]，不能用上一轮残留的 s
            elif host_windows:
                use_host = any(st < b and en > a for a, b in host_windows)
            else:
                use_host = (not HYBRID) or (st < host_intro) or (en > total - host_outro)
            parts.append(seg_clip(i, "full") if use_host else visual_clip(i))
        if HYBRID:
            print(f"· 混合模式：数字人 0~{host_intro:.0f}s 和 {total - host_outro:.0f}s~ 露脸，中间走画面")
    # 首段只取到旁白结束
    intro_trim = PROJ / "tmp" / "intro.mp4"
    run(["ffmpeg", "-loglevel", "error", "-y", "-i", str(intro), "-frames:v", str(frames[0]),
         "-an", "-vf", f"scale={W}:{H},fps={FPS}", "-c:v", "libx264", "-crf", "18", "-preset", "medium", str(intro_trim)])
    if not FULL_SCREEN:
        parts[0] = str(intro_trim)
    lst = PROJ / "tmp" / "main.txt"
    lst.write_text("".join(f"file '{p.replace(chr(92), '/')}'\n" for p in parts), encoding="utf-8")
    run(["ffmpeg", "-loglevel", "error", "-y", "-f", "concat", "-safe", "0", "-i", str(lst),
         "-c:v", "libx264", "-crf", "18", "-preset", "medium", "-pix_fmt", "yuv420p", "-r", str(FPS),
         str(PROJ / "public" / "main.mp4")])
    print(f"✓ public/main.mp4 {dur(PROJ / 'public' / 'main.mp4'):.2f}s")

    # ⑤ PiP 小窗：数字人第 2..N 段，静音（全程放大模式下不需要）
    pip_parts = []
    if FULL_SCREEN:
        print("· 全程放大模式：跳过小窗轨（edit.json 里配 pipOff: true）")
        run(["ffmpeg", "-loglevel", "error", "-y", "-i", str(PROJ / "narration.wav"),
             "-ac", "2", "-ar", "48000", str(PROJ / "public" / "voice.wav")])
        print("✓ public/voice.wav")
        return
    # PiP 也用「按段切」，同样避免合并带来的累积漂移
    for i in range(1, len(S)):
        pip_parts.append(seg_clip(i, "pip"))
    plst = PROJ / "tmp" / "pip.txt"
    plst.write_text("".join(f"file '{p.replace(chr(92), '/')}'\n" for p in pip_parts), encoding="utf-8")
    run(["ffmpeg", "-loglevel", "error", "-y", "-f", "concat", "-safe", "0", "-i", str(plst),
         "-c:v", "libx264", "-crf", "18", "-preset", "medium", "-pix_fmt", "yuv420p", "-r", str(FPS),
         str(PROJ / "public" / "pip.mp4")])
    print(f"✓ public/pip.mp4 {dur(PROJ / 'public' / 'pip.mp4'):.2f}s")
    # 旁白轨也放进 public 供 Remotion 用
    run(["ffmpeg", "-loglevel", "error", "-y", "-i", str(PROJ / "narration.wav"),
         "-ac", "2", "-ar", "48000", str(PROJ / "public" / "voice.wav")])
    print("✓ public/voice.wav")


if __name__ == "__main__":
    main()

