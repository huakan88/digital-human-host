#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""whisper-cli 兼容层：用本机 FunASR 做转写，输出 whisper.cpp 的 JSON 格式。

上游 scripts/assemble.py 和 scripts/align.py 调的是 whisper.cpp 的命令行：
    whisper-cli -m <model> -l zh [--prompt "..."] [-ml 1] -oj -of <prefix> -f <wav>
然后读 <prefix>.json，形如
    {"transcription":[{"text":"你好","offsets":{"from":0,"to":320}}]}
本机没有 whisper.cpp（也没有 ggml 模型），但装了 FunASR（paraformer + punc + VAD）。
这里做一个同名包装，让上游脚本一行不用改就能跑。

模型（已在本机缓存，离线可用）：
    iic/speech_seaco_paraformer_large_asr_nat-zh-cn-16k-common-vocab8404-pytorch
    iic/speech_fsmn_vad_zh-cn-16k-common-pytorch
    iic/speech_punc_ct-transformer_cn-en-common-vocab471067-large
"""
import argparse
import json
import os
import sys
from pathlib import Path

ASR_MODEL = os.environ.get("DHK_ASR_MODEL", "paraformer-zh")
VAD_MODEL = os.environ.get("DHK_VAD_MODEL", "fsmn-vad")
PUNC_MODEL = os.environ.get("DHK_PUNC_MODEL", "ct-punc")
CACHE = os.environ.get("MODELSCOPE_CACHE", r"E:\AI\caches\modelscope")


def _to_16k(src, dst):
    import subprocess
    subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-i", str(src), "-ar", "16000", "-ac", "1", str(dst)], check=True)
    return str(dst)


def _load_model():
    os.environ.setdefault("MODELSCOPE_CACHE", CACHE)
    from funasr import AutoModel
    return AutoModel(model=ASR_MODEL, vad_model=VAD_MODEL, punc_model=PUNC_MODEL,
                     disable_update=True, device="cpu")


def transcribe(wav, model=None):
    """返回 whisper.cpp 风格的 token 列表 [{'text':..., 'offsets':{'from':ms,'to':ms}}]"""
    import tempfile
    model = model or _load_model()
    with tempfile.TemporaryDirectory() as td:
        wav16 = _to_16k(wav, Path(td) / "in16k.wav")
        res = model.generate(input=wav16, batch_size_s=300)
    if not res:
        return []
    r = res[0]
    text = (r.get("text") or "").strip()
    ts = r.get("timestamp") or []
    if not text:
        return []
    tokens = []
    if ts and len(ts) == len(text):
        for ch, (a, b) in zip(text, ts):
            tokens.append({"text": ch, "offsets": {"from": int(a), "to": int(b)}})
    elif ts:
        # 时间戳个数和字符数对不上（英文按词、标点被剥离等情况）：按比例摊开
        n = len(text)
        for i, ch in enumerate(text):
            j = min(len(ts) - 1, int(i * len(ts) / n))
            a, b = ts[j]
            tokens.append({"text": ch, "offsets": {"from": int(a), "to": int(b)}})
    else:
        tokens.append({"text": text, "offsets": {"from": 0, "to": 0}})
    return tokens


def main():
    ap = argparse.ArgumentParser(add_help=False)
    ap.add_argument("-m", "--model")
    ap.add_argument("-l", "--language", default="zh")
    ap.add_argument("--prompt")
    ap.add_argument("-ml", "--max-len")
    ap.add_argument("-oj", "--output-json", action="store_true")
    ap.add_argument("-of", "--output-file")
    ap.add_argument("-f", "--file")
    ap.add_argument("-nt", "--no-timestamps", action="store_true")
    ap.add_argument("--batch", default=None, help="批量模式：OUTDIR，后面跟若干 wav（模型只加载一次）")
    ap.add_argument("-h", "--help", action="store_true")
    a, rest = ap.parse_known_args()

    if a.help:
        print(__doc__)
        return

    # 批量模式：模型只加载一次。单段加载模型要 ~40 秒，十段就是七八分钟。
    if a.batch:
        outdir = Path(a.batch)
        outdir.mkdir(parents=True, exist_ok=True)
        model = _load_model()
        for w in rest:
            w = w.strip().strip('"')
            if not w or not Path(w).exists():
                continue
            tokens = transcribe(w, model)
            out = outdir / (Path(w).stem + ".json")
            out.write_text(json.dumps({"transcription": tokens}, ensure_ascii=False, indent=1), encoding="utf-8")
            print(f"{out}  {len(tokens)} tokens")
        return

    if not a.file:
        print(__doc__)
        return
    tokens = transcribe(a.file)
    payload = {"transcription": tokens}
    if a.output_file:
        out = Path(a.output_file)
        if out.suffix != ".json":
            out = out.with_suffix(".json")
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(payload, ensure_ascii=False, indent=1), encoding="utf-8")
        print(f"{out}  {len(tokens)} tokens")
    else:
        print(json.dumps(payload, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
