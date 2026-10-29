#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""digital-human-koubo · 本机后端适配器（替代 Renoise MCP 这一层工具面）。

上游 skill 的生成动作全部由 agent 通过 MCP 工具完成，脚本本身只负责造 payload 和下载：
    get_account / create_tasks / wait_tasks / download_results / estimate_cost / upload_files
本文件把这一层映射到本机已有的能力，**产物命名沿用上游约定**，所以 assemble.py / align.py
一个都不用改：

    gen/renoise-<taskId>.mp4   ← assemble.py 直接读
    ids.json                   ← {段 id: taskId}

能力映射：
    配音   → MiniMax speech-2.8-hd（云，默认）或本机 VoxCPM2 http://127.0.0.1:8808（本地克隆音色）
    定妆照 → MiniMax image-01（云）。本机没有文生图模型：ComfyUI\models\checkpoints 是空的。
    口播   → 本机 MiniMax H3（ComfyUI:8188，--guide-audio 硬锚定，口型跟配音逐字对齐）
             或云端 MiniMax-H3（/v2/video_generation，参考音频免费）

用法：
    python backend.py account
    python backend.py quote  tasks.json
    python backend.py tts    --text "台词" --out voice/s1.wav [--voice female-shaonv|huakan]
    python backend.py image  --prompt "场景描述" --out stills/x.jpg [--ref assets/avatar_ref.jpg] [--ratio 9:16]
    python backend.py run    tasks.json [--out ids.json] [--backend local|cloud] [--only s1,s2] [--dry-run]
"""
import argparse
import binascii
import json
import math
import os
import re
import shutil
import subprocess
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

HERE = Path(__file__).resolve().parent
# HK_PRESET 让多个「主持」预设共用这一套引擎：各自只带 persona/配置/素材
SKILL = Path(os.environ.get("HK_PRESET", HERE.parent)).resolve()
WORKSPACE = SKILL

# ------------------------------------------------------------------ 配置

def _cfg():
    """local-backend.json 覆盖默认值；环境变量再覆盖。"""
    cfg = {}
    f = SKILL / "references" / "local-backend.json"
    if f.exists():
        cfg.update(json.loads(f.read_text(encoding="utf-8")))
    for k, v in (("h3_root", "DHK_H3_ROOT"), ("width", "DHK_W"), ("height", "DHK_H"),
                 ("steps", "DHK_STEPS"), ("tts_voice", "DHK_VOICE")):
        if os.environ.get(v):
            cfg[k] = int(os.environ[v]) if k in ("width", "height", "steps") else os.environ[v]
    return cfg

CFG = _cfg()

H3_ROOT = Path(CFG.get("h3_root", "E:/minimax H3"))
H3_PY = H3_ROOT / "venv" / "Scripts" / "python.exe"
H3_CLI = H3_ROOT / "tools" / "h3gen.py"
H3_OUT = H3_ROOT / "ComfyUI" / "output"
COMFY = "http://127.0.0.1:8188"

MM_BASE = CFG.get("minimax_base", "https://api.minimaxi.com/v1")
MM_IMAGE_MODEL = CFG.get("image_model", "image-01")
MM_TTS_MODEL = CFG.get("tts_model", "speech-2.8-hd")
VOXCPM_BASE = CFG.get("voxcpm_base", os.environ.get("VOXCPM_BASE", "http://127.0.0.1:8808/v1"))
VOXCPM_VOICE = CFG.get("voxcpm_voice", os.environ.get("VOXCPM_VOICE", "huakan"))

# 视频定价（元/秒），来源 platform.minimax.cn 定价概览（2026-10）
H3_PRICE = {"MiniMax-H3-Highspeed": 0.40, "MiniMax-H3-Lite": 0.26, "MiniMax-H3": 0.50}
IMAGE_PRICE = 0.025          # 元/张
TTS_PRICE_PER_10K = 3.50     # 元/万字符（汉字算 2 字符）


def _opener():
    # 本机设了系统代理，直连 127.0.0.1 必须绕过，否则会拿到 502
    return urllib.request.build_opener(urllib.request.ProxyHandler({}))


def mm_key():
    """从 DSH 凭据文件或环境变量取 MiniMax key，不落到命令行里。"""
    k = os.environ.get("MINIMAX_CN_API_KEY") or os.environ.get("MINIMAX_API_KEY")
    if k:
        return k
    f = Path(os.environ.get("DSH_HOME", "E:/dsh-home")) / ".credentials.yaml"
    if f.exists():
        m = re.search(r"MINIMAX_CN_API_KEY:\s*(\S+)", f.read_text(encoding="utf-8"))
        if m:
            return m.group(1)
    sys.exit("找不到 MiniMax API key（设 MINIMAX_CN_API_KEY 环境变量）")


def http_json(url, payload=None, method="POST", headers=None, timeout=120, raw=False):
    data = json.dumps(payload).encode("utf-8") if payload is not None else None
    h = {"Content-Type": "application/json"}
    h.update(headers or {})
    req = urllib.request.Request(url, data=data, method=method, headers=h)
    op = _opener()
    try:
        r = op.open(req, timeout=timeout)
        body = r.read()
        return body if raw else json.loads(body.decode("utf-8", "replace"))
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", "replace")
        raise RuntimeError(f"HTTP {e.code} {url}\n{body[:400]}") from None


# ------------------------------------------------------------------ 报价

def estimate(tasks):
    """段数 · 秒数 · 预估花费。本机后端只有生图要花钱；视频和配音都在本地跑。
    images_this_run 默认 0：定妆照/场景图是单独用 image 命令生成的，
    正常出片流程不再额外生图，所以不该按段数收钱。"""
    secs = sum(t["duration"] for t in tasks)
    n_img = int(CFG.get("images_this_run", 0))
    chars = sum(len(t.get("line", "") or t.get("prompt", "")) for t in tasks) * 2
    local_video = CFG.get("video_backend", "local") == "local"
    local_tts = CFG.get("tts_backend", "voxcpm") == "voxcpm"
    video = 0.0 if local_video else secs * H3_PRICE.get(CFG.get("cloud_video_model", "MiniMax-H3-Highspeed"), 0.40)
    img = n_img * IMAGE_PRICE
    tts = 0.0 if local_tts else chars / 10000 * TTS_PRICE_PER_10K
    return {"segments": len(tasks), "seconds": round(secs, 1),
            "video_backend": "本机 H3（免费）" if local_video else CFG.get("cloud_video_model"),
            "tts_backend": ("本机 VoxCPM2（免费）" if local_tts else
                            (f"豆包 {CFG.get('doubao_speaker')}" if CFG.get("tts_backend") == "doubao"
                             else CFG.get("tts_model"))),
            "images": n_img,
            "video_cny": round(video, 3), "image_cny": round(img, 3), "tts_cny": round(tts, 3),
            "total_cny": round(video + img + tts, 3)}


# ------------------------------------------------------------------ 配音

def tts_minimax(text, out_path, voice=None):
    voice = voice or CFG.get("tts_voice", "female-shaonv")
    body = {
        "model": MM_TTS_MODEL, "text": text, "stream": False,
        "voice_setting": {"voice_id": voice, "speed": CFG.get("tts_speed", 1.0), "vol": 1.0,
                          "pitch": 0, "emotion": "happy", "language_boost": "Chinese"},
        "audio_setting": {"sample_rate": 32000, "bitrate": 128000, "format": "wav", "channel": 1},
    }
    d = http_json(MM_BASE + "/t2a_v2", body, headers={"Authorization": "Bearer " + mm_key()})
    hexed = (d.get("data") or {}).get("audio") or ""
    if not hexed:
        raise RuntimeError(f"TTS 没有返回音频：{json.dumps(d, ensure_ascii=False)[:300]}")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_bytes(binascii.unhexlify(hexed))
    return out_path


HUAKAN_CLI = Path(r"E:\dsh-agents\skills\huakan-tts\bin\huakan.cmd")

# ------------------------------------------------------------------ 豆包 TTS（Vivi 2.0 / 清澈梓梓 等）
DOUBAO_URL = "https://openspeech.bytedance.com/api/v3/tts/unidirectional"
DOUBAO_KEY_PATHS = [Path(r"E:\工作用\.config\secrets\doubao_speech_api_key"),
                    Path.home() / ".config/secrets/doubao_speech_api_key"]


def doubao_key():
    k = os.environ.get("DOUBAO_API_KEY")
    if k:
        return k.strip()
    f = os.environ.get("DOUBAO_KEY_FILE")
    for p in ([Path(f)] if f else []) + DOUBAO_KEY_PATHS:
        if p.exists():
            return p.read_text(encoding="utf-8").strip()
    raise RuntimeError("找不到豆包 API key（设 DOUBAO_API_KEY 或 DOUBAO_KEY_FILE）")


def tts_doubao(text, out_path, speaker=None, resource="seed-tts-2.0", rate=None):
    """豆包合成：speaker 默认取配置里的 vivi（zh_female_vv_uranus_bigtts）。"""
    import base64, uuid
    speaker = speaker or CFG.get("doubao_speaker", "zh_female_vv_uranus_bigtts")
    resource = CFG.get("doubao_resource", resource)
    rate = int(CFG.get("doubao_rate", 20) if rate is None else rate)
    payload = {"user": {"uid": "hk-zhuchi"},
               "req_params": {"text": text, "speaker": speaker,
                              "audio_params": {"format": "wav", "sample_rate": 48000, "speech_rate": rate}}}
    req = urllib.request.Request(DOUBAO_URL, data=json.dumps(payload).encode("utf-8"), method="POST",
                                 headers={"X-Api-Key": doubao_key(), "X-Api-Resource-Id": resource,
                                          "X-Api-Request-Id": str(uuid.uuid4()), "Content-Type": "application/json"})
    audio, err = b"", None
    with _opener().open(req, timeout=180) as r:
        for raw in r:
            line = raw.decode("utf-8", "replace").strip()
            if not line:
                continue
            try:
                obj = json.loads(line)
            except Exception:
                continue
            code, data = obj.get("code"), obj.get("data")
            if code not in (None, 0, 20000000):
                err = (code, obj.get("message"))
            if isinstance(data, str) and data:
                audio += base64.b64decode(data)
            if code == 20000000:
                break
    if len(audio) < 1000:
        raise RuntimeError(f"豆包 TTS 失败：{err}")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_bytes(audio)
    return out_path



def tts_voxcpm(text, out_path):
    """配音：优先走 huakan-tts 技能的命令行（带完整的文本规范化/术语纠音/人声打磨/响度归一），
    走不通再退回裸 HTTP API。

    为什么要走技能：huakan-tts 内置了数字→中文、多音字锁音、专有名词表（PD-1→P D one、
    CD105→C D一百零五…）、>48 字自动切段、句首吞字防护。这些直接决定**配音和文稿是否一致**，
    不一致的话口型再准也会对不上稿子。
    """
    if HUAKAN_CLI.exists():
        tmp = Path(str(out_path).rsplit(".", 1)[0] + ".mp3")
        r = subprocess.run([str(HUAKAN_CLI), text, "-o", str(tmp), "--lufs", "-16"],
                           capture_output=True, text=True, encoding="utf-8", errors="replace")
        if r.returncode == 0 and tmp.exists() and tmp.stat().st_size > 0:
            subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-i", str(tmp),
                            "-ar", "48000", "-ac", "1", "-c:a", "pcm_s16le", str(out_path)], check=True)
            tmp.unlink(missing_ok=True)
            return out_path
        print(f"· huakan-tts 调用失败，退回裸 API：{(r.stdout + r.stderr)[-200:]}", flush=True)

    if not ensure_voxcpm():
        raise RuntimeError("本机 TTS 服务起不来（:8808），配音做不了")
    key = os.environ.get("VOXCPM_API_KEY")
    if not key:
        f = Path(os.environ.get("USERPROFILE", ".")) / ".config" / "ai-teardown" / "voxcpm.env"
        if f.exists():
            m = re.search(r"VOXCPM_API_KEY\s*=\s*(\S+)", f.read_text(encoding="utf-8"))
            key = m.group(1) if m else None
    key = key or "sk-voxcpm-c6fbce3f533bb1e5c0637b47"
    body = {"model": "voxcpm2", "input": text, "voice": VOXCPM_VOICE, "response_format": "wav",
            "speed": float(CFG.get("tts_speed", 1.0))}
    raw = http_json(VOXCPM_BASE + "/audio/speech", body, method="POST",
                    headers={"Authorization": "Bearer " + key}, timeout=300, raw=True)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_bytes(raw)
    return out_path


def make_voice(text, out_path, backend=None):
    backend = backend or CFG.get("tts_backend", "voxcpm")
    if backend == "doubao":
        return tts_doubao(text, out_path)
    if backend == "voxcpm":
        return tts_voxcpm(text, out_path)
    return tts_minimax(text, out_path)


# ------------------------------------------------------------------ 定妆照

def image_generate(prompt, out_path, ref=None, ratio="9:16"):
    import base64
    # 用 b64_json 拿，避免 OSS 签名 URL 的 403（签名 URL 被代理/重编码会失效）
    body = {"model": MM_IMAGE_MODEL, "prompt": prompt, "aspect_ratio": ratio, "n": 1,
            "response_format": "base64", "prompt_optimizer": True}
    if ref:
        b64 = base64_data_url(ref)
        body["subject_reference"] = [{"type": "character", "image_file": b64}]
    d = http_json(MM_BASE + "/image_generation", body, headers={"Authorization": "Bearer " + mm_key()})
    data = d.get("data") or {}
    b64s = data.get("image_base64") or []
    if b64s:
        raw = base64.b64decode(b64s[0])
    else:
        urls = data.get("image_urls") or []
        if not urls:
            raise RuntimeError(f"生图失败：{json.dumps(d, ensure_ascii=False)[:300]}")
        raw = http_json(urls[0], None, method="GET", timeout=300, raw=True)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_bytes(raw)
    return out_path


def base64_data_url(path):
    import base64
    data = base64.b64encode(Path(path).read_bytes()).decode()
    ext = Path(path).suffix.lower().lstrip(".") or "jpeg"
    if ext == "jpg":
        ext = "jpeg"
    return f"data:image/{ext};base64,{data}"


# ------------------------------------------------------------------ 素材解析

def resolve_material(ref, materials):
    """把上游的 material:<id> / task:<id> 解析成本机文件路径。"""
    if ref.startswith(("http://", "https://", "data:")):
        return ref
    direct = Path(ref)
    if not direct.is_absolute():
        direct = (SKILL / direct).resolve()
    if direct.exists():
        return str(direct)
    m = materials.get(ref)
    if not m:
        raise RuntimeError(f"persona 里的 {ref} 没有本机对应文件。"
                           f"请在 references/local-backend.json 的 materials 里补一条，"
                           f"或先按 references/new-avatar.md 做一张定妆照。")
    p = Path(m["file"])
    if not p.is_absolute():
        p = (SKILL / p).resolve()
    if not p.exists():
        raise RuntimeError(f"{ref} 指向的文件不存在：{p}")
    return str(p)


def to_h3_prompt(grok_prompt):
    """本地 H3 的提示词规范：
      - 必须用 <Picture 1> 绑定参考图、<Audio 1> 绑定配音（h3gen 自己就是这么约定的，
        见 h3gen.py:685「prompt 里必须用 <Picture 1> <Picture 2> 按接线顺序引用参考图」）
      - 台词不写进提示词：台词由 <Audio 1> 提供，写进提示词模型会自己再编一遍台词
    这里只做兜底清理：去掉引号里的台词、去掉 Sound: 行、去掉 @xxx。
    """
    p = grok_prompt
    p = re.sub(r"\n?[“\"].+?[”\"]", "", p, flags=re.S)
    p = re.sub(r"\n?Sound:.*", "", p, flags=re.S)
    p = re.sub(r"[ \t]+", " ", p).strip()
    p = re.sub(r"\s*@\S+", " ", p).strip()
    return p


# ------------------------------------------------------------------ 显存腾挪
# H3 出画时必须把本机 TTS 服务停掉：VoxCPM 常驻占 ~5.7GB 显存，H3 的 20GB 权重
# 要靠"显存不够就从内存换"才塞得下，两者同时在 → ComfyUI 直接 CUDA out of memory。
# 出完片再把 TTS 服务拉回来。

VOXCPM_SERVER = r"E:\AI\voxcpm-tools\tts_server.py"
VOXCPM_PY = r"E:\AI\envs\voxcpm\Scripts\python.exe"
VOXCPM_MODEL = r"E:\AI\models\VoxCPM2"


def _python_pids(match):
    ps = subprocess.run(["powershell", "-NoProfile", "-Command",
                         "Get-CimInstance Win32_Process -Filter \"Name='python.exe'\" | "
                         "ForEach-Object { \"$($_.ProcessId)|$($_.CommandLine)\" }"],
                        capture_output=True, text=True, encoding="utf-8", errors="replace")
    pids = []
    for line in ps.stdout.splitlines():
        pid, _, cmd = line.partition("|")
        if match in cmd and pid.strip().isdigit():
            pids.append(int(pid.strip()))
    return pids


def stop_voxcpm():
    pids = _python_pids("tts_server.py")
    for p in pids:
        subprocess.run(["taskkill", "/F", "/PID", str(p)], capture_output=True)
    if pids:
        time.sleep(4)
        print(f"· 已停本机 TTS 服务（PID {pids}），把显存让给 H3", flush=True)
    return pids


def start_voxcpm():
    if not Path(VOXCPM_SERVER).exists():
        return False
    subprocess.Popen([VOXCPM_PY, "-u", VOXCPM_SERVER, "--port", "8808", "--preload", "--model", VOXCPM_MODEL],
                     stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                     creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
    print("· 本机 TTS 服务已重新拉起（:8808，加载约 80 秒）", flush=True)
    return True


def ensure_voxcpm(wait=240):
    """确保本机 TTS 服务在线可用。
    服务带 --preload，起��来要 ~80 秒；没好之前调用会直接 ConnectionRefused。"""
    op = _opener()
    for _ in range(3):
        try:
            op.open("http://127.0.0.1:8808/health", timeout=6).read()
            return True
        except Exception:
            pass
        start_voxcpm()
        t0 = time.time()
        while time.time() - t0 < wait:
            time.sleep(6)
            try:
                op.open("http://127.0.0.1:8808/health", timeout=6).read()
                print("· 本机 TTS 服务就绪", flush=True)
                return True
            except Exception:
                continue
    return False


def h3_frames(duration_s, fps=24):
    """H3 要求帧数落在 17k+5 网格上。"""
    n = max(124, math.ceil(duration_s * fps))
    return 5 + 17 * max(1, math.ceil((n - 5) / 17))


# ------------------------------------------------------------------ 本机 H3 出片

def h3_generate(image_path, audio_path, prompt, width, height, frames, seed, prefix):
    """调本机 h3gen.py 提交一个 guide-audio 锚定的 H3 任务，返回 ComfyUI prompt_id。"""
    if not H3_PY.exists():
        raise RuntimeError(f"找不到本机 H3 解释器：{H3_PY}")
    if not H3_CLI.exists():
        raise RuntimeError(f"找不到本机 H3 脚本：{H3_CLI}")
    prompt_file = Path(prefix).with_suffix(".prompt.txt")
    prompt_file.parent.mkdir(parents=True, exist_ok=True)
    prompt_file.write_text(prompt, encoding="utf-8")
    cmd = [str(H3_PY), "-E", str(H3_CLI),
           "--prompt-file", str(prompt_file),
           "--ref-image", str(image_path),
           "--guide-image", str(image_path),
           "--guide-audio", str(audio_path),
           "--width", str(width), "--height", str(height),
           "--frames", str(frames), "--steps", str(CFG.get("h3_steps", 4)),
           "--mode", CFG.get("mode", "turbo"),
           "--seed", str(seed), "--prefix", str(prefix), "--no-wait"]
    # --low-vram 会强制「权重异步换出」，每个任务都要把 20GB 模型从内存搬到显存，
    # 实测每段多花 ~40 秒。显存够的时候关掉它。
    if CFG.get("h3_low_vram", False):
        cmd.append("--low-vram")
    cmd.append("--video-only")
    r = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace")
    (prompt_file.with_suffix(".submit.log")).write_text(r.stdout + r.stderr, encoding="utf-8")
    if r.returncode:
        raise RuntimeError(f"H3 提交失败：{(r.stdout + r.stderr)[-600:]}")
    m = re.search(r"prompt_id=([a-f0-9-]{36})", r.stdout)
    if not m:
        raise RuntimeError(f"H3 没返回 prompt_id：{(r.stdout + r.stderr)[-600:]}")
    return m.group(1)


def h3_wait(prompt_id, timeout=3600):
    op = _opener()
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        try:
            rec = http_json(f"{COMFY}/history/{prompt_id}", None, method="GET", timeout=20).get(prompt_id)
        except Exception:
            rec = None
        if rec:
            st = rec.get("status", {})
            if st.get("status_str") == "error":
                raise RuntimeError(f"H3 任务失败：{json.dumps(st.get('messages'), ensure_ascii=False)[:400]}")
            if st.get("completed"):
                for out in (rec.get("outputs") or {}).values():
                    for item in (out.get("images") or []) + (out.get("videos") or []):
                        if item.get("type") == "output" and item.get("filename", "").endswith(".mp4"):
                            return H3_OUT / item.get("subfolder", "") / item["filename"]
                raise RuntimeError("H3 任务完成但没找到视频输出")
        time.sleep(5)
    raise TimeoutError("H3 任务超时")


# ------------------------------------------------------------------ 云端 H3 出片

def download(url, dst):
    """下载带签名的 OSS 链接。urllib 会把 %2F / %3D 这类转义重新编码，导致签名对不上 → 403，
    所以优先用 curl（原样发 URL），失败再退回 urllib。"""
    dst = Path(dst)
    dst.parent.mkdir(parents=True, exist_ok=True)
    exe = shutil.which("curl") or shutil.which("curl.exe")
    if exe:
        r = subprocess.run([exe, "-sSL", "--max-time", "900", "-o", str(dst), url], capture_output=True)
        if r.returncode == 0 and dst.exists() and dst.stat().st_size > 0:
            return dst
        raise RuntimeError(f"curl 下载失败 rc={r.returncode}: {r.stderr[:200]}")
    raw = http_json(url, None, method="GET", timeout=600, raw=True)
    dst.write_bytes(raw)
    return dst


def cloud_video(image_path, audio_path, prompt, model=None, duration=6):
    model = model or CFG.get("cloud_video_model", "MiniMax-H3-Highspeed")
    body = {"model": model, "prompt": prompt, "duration": duration,
            "first_frame_image": base64_data_url(image_path),
            "reference_audio": base64_data_url(audio_path).replace("data:image/", "data:audio/")}
    d = http_json("https://api.minimaxi.com/v2/video_generation", body,
                  headers={"Authorization": "Bearer " + mm_key()})
    return d


# ------------------------------------------------------------------ 云端 H3 v2（r2va：图 + 音 → 带原生口播的视频）

H3_V2_URL = "https://api.minimaxi.com/v2/video_generation"
H3_V2_QUERY = "https://api.minimaxi.com/v2/query/video_generation"
# 云端 H3 时长下限 4 秒、每段参考音 2–15 秒
H3_MIN_DUR = 4
VOICE_GAP = 0.25          # 段间静音，和 build_media.py 的 GAP 必须一致


def to_r2va_prompt(grok_prompt, line=None):
    """云端 H3 v2 的 r2va 说法：台词写在提示词里，声音交给参考音频。"""
    p = grok_prompt
    m = re.search(r"(She|He) speaks .*?:\s*\n?[“\"](.+?)[”\"]", p, flags=re.S)
    if not line and m:
        line = m.group(2)
    if m:
        p = p[:m.start()] + p[m.end():]
    p = re.sub(r"\n?Sound:.*", "", p, flags=re.S)
    p = re.sub(r"[ \t]+", " ", p).strip()
    p = re.sub(r"\s*@\S+", " ", p).strip()
    p = re.sub(r"<Picture 1>|<Audio 1>", "", p).strip()
    if line:
        p += f' Character speaks: "{line}". Voice timbre follows reference audio 1.'
    return p


def _data_url(path, mime):
    import base64
    return f"data:{mime};base64," + base64.b64encode(Path(path).read_bytes()).decode()


def h3_v2_create(image_path, audio_path, prompt, model, duration, resolution, ratio):
    content = [
        {"type": "text", "text": prompt},
        {"type": "image_url", "role": "reference_image",
         "image_url": {"url": _data_url(image_path, "image/jpeg")}},
        {"type": "audio_url", "role": "reference_audio",
         "audio_url": {"url": _data_url(audio_path, "audio/wav")}},
    ]
    body = {"model": model, "content": content, "resolution": resolution,
            "duration": int(duration), "ratio": ratio}
    d = http_json(H3_V2_URL, body, headers={"Authorization": "Bearer " + mm_key()})
    tid = d.get("task_id") or (d.get("task") or {}).get("id")
    if not tid:
        raise RuntimeError(f"H3 v2 没返回 task_id：{json.dumps(d, ensure_ascii=False)[:300]}")
    return tid


def h3_v2_wait(task_id, timeout=1800):
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        d = http_json(f"{H3_V2_QUERY}?task_id={task_id}", None, method="GET",
                      headers={"Authorization": "Bearer " + mm_key()}, timeout=30)
        task = d.get("task") or {}
        status = task.get("status") or d.get("status")
        if status in ("succeeded", "success", "Success"):
            url = (task.get("content") or {}).get("url") or d.get("url")
            if not url:
                raise RuntimeError(f"H3 v2 成功但没有下载地址：{json.dumps(d, ensure_ascii=False)[:300]}")
            return url
        if status in ("failed", "cancelled", "Failed"):
            raise RuntimeError(f"H3 v2 失败：{json.dumps(d, ensure_ascii=False)[:400]}")
        time.sleep(8)
    raise TimeoutError("H3 v2 超时")


def pad_audio_to(src, dst, seconds):
    """把音频补/截到指定秒数（云端 H3 时长下限 4 秒）"""
    subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-i", str(src),
                    "-af", f"apad,atrim=0:{seconds}", "-ar", "44100", "-ac", "1",
                    "-c:a", "pcm_s16le", str(dst)], check=True)
    return dst


# ------------------------------------------------------------------ 主流程

def restart_comfyui(wait_s=20):
    """ComfyUI 跑十来段后会出 hostbuf_file_reader_read failed（显存/句柄累积）。
    杀掉重开一次就恢复；h3gen 下一次提交会自动把它拉起来。"""
    import subprocess
    try:
        out = subprocess.run(["wmic", "process", "where", "name='python.exe'", "get", "ProcessId,CommandLine"],
                             capture_output=True, text=True, encoding="utf-8", errors="replace").stdout
    except Exception:
        out = ""
    killed = 0
    for line in out.splitlines():
        if "main.py" in line and "8188" in line:
            m = re.search(r"(\d+)\s*$", line.strip())
            if m:
                os.system(f"taskkill /F /PID {m.group(1)} >nul 2>&1")
                killed += 1
    print(f"· 重启 ComfyUI（杀掉 {killed} 个进程），等 {wait_s} 秒…", flush=True)
    time.sleep(wait_s)

def run(tasks, out_ids="ids.json", backend="local", only=None, dry_run=False, seed_base=None, merge=0, force=False):
    seed_base = int(seed_base if seed_base is not None else os.environ.get("HK_SEED", "4201"))
    materials = CFG.get("materials", {})
    q = estimate(tasks)
    print(f"报价：{q['segments']} 段 · {q['seconds']} 秒 · 预估 ¥{q['total_cny']}"
          f"（视频 ¥{q['video_cny']} + 图 ¥{q['image_cny']} + 配音 ¥{q['tts_cny']}）", flush=True)
    if dry_run:
        return q
    gen = Path("gen"); gen.mkdir(exist_ok=True)
    ids = {}
    if Path(out_ids).exists():
        ids = json.loads(Path(out_ids).read_text(encoding="utf-8"))
    todo = [(i, t) for i, t in enumerate(tasks)
            if not only or (t["label"].split()[-1] if t.get("label") else f"s{i+1}") in only]

    # ① 先把配音全做完（这步需要本机 TTS 服务在跑）
    voices = {}
    for i, t in todo:
        sid = t["label"].split()[-1] if t.get("label") else f"s{i+1}"
        voice = Path("voice") / f"{sid}.wav"
        line = extract_line(t)
        if voice.exists() and voice.stat().st_size > 1000:
            print(f"[{sid}] 配音已存在，跳过", flush=True)
        else:
            print(f"[{sid}] 配音 {len(line)} 字 …", flush=True)
            make_voice(line, voice)
        voices[sid] = voice

    # ② 分组：每段单独出一次片要付一次 ~100 秒的固定开销（模型 20GB 从内存换到显存）。
    #    把连续的短段合并成一个长片段（≤merge 秒），固定开销只付一次。
    #    第一段保持独立（它是全屏开场）。
    groups = []
    if merge and merge > 0 and len(todo) > 1:
        # 整片跑的时候第一段单独成组（它是全屏开场）；
        # 但用 --only 挑段跑（数字人穿插）时不拆，照常按 merge 合并。
        start_idx = 0 if only else 1
        if start_idx == 1:
            groups.append([todo[0]])
        cur, acc, prev_i = [], 0.0, None
        for it in todo[start_idx:]:
            sid = it[1]["label"].split()[-1]
            d = float(probe_duration(voices[sid]))
            # 只能合并「时间上相邻」的段：--only 挑段跑时，中间跳过的段不能拼进来
            adjacent = (prev_i is None) or (it[0] == prev_i + 1)
            if cur and (acc + d > merge or not adjacent):
                groups.append(cur); cur, acc = [], 0.0
            cur.append(it); acc += d; prev_i = it[0]
        if cur:
            groups.append(cur)
        print(f"· 合并出画：{len(todo)} 段 → {len(groups)} 次 H3 调用（每组 ≤ {merge:.0f}s）", flush=True)
    else:
        groups = [[it] for it in todo]

    # ③ 本机出画前把 TTS 服务停掉，把显存让给 H3（否则 CUDA OOM）
    stopped_tts = False
    if backend == "local" and CFG.get("free_vram_for_h3", True):
        stopped_tts = bool(stop_voxcpm())
    groups_meta = []
    try:
        for gi, grp in enumerate(groups):
            i, t = grp[0]
            sids = [x[1]["label"].split()[-1] for x in grp]
            sid = sids[0]
            # 文件名用「组内第一段的 id」，同一份稿子重跑时文件名不变，可以断点续跑
            task_id = sid
            for s in sids:
                ids[s] = task_id
            out_mp4 = gen / f"renoise-{task_id}.mp4"
            voice = voices[sid]
            ref = resolve_material(t["references"][0]["ref"], materials)

            # 组内音频：各段配音 + 段间 0.25s 静音（和总轨一致，口型才对得上）
            if len(grp) > 1:
                voice = Path("voice") / f"grp_{sid}.wav"
                ins, parts, labels = [], [], []
                for k, s in enumerate(sids):
                    ins += ["-i", str(voices[s])]
                    parts.append(f"[{k}:a]aresample=48000,apad=pad_dur={VOICE_GAP}[a{k}]")
                    labels.append(f"[a{k}]")
                chain = ";".join(parts) + ";" + "".join(labels) + f"concat=n={len(sids)}:v=0:a=1[out]"
                subprocess.run(["ffmpeg", "-loglevel", "error", "-y"] + ins +
                               ["-filter_complex", chain, "-map", "[out]", "-c:a", "pcm_s16le", str(voice)], check=True)
            dur = float(probe_duration(voice))
            if out_mp4.exists() and out_mp4.stat().st_size > 10000 and not force:
                print(f"[{sid}] 已有成片，跳过（{sids}）", flush=True)
                groups_meta.append({"ids": sids, "taskId": task_id, "dur": round(dur, 3),
                                    "file": f"gen/renoise-{task_id}.mp4"})
                Path(out_ids).write_text(json.dumps(ids, ensure_ascii=False, indent=1), encoding="utf-8")
                Path("groups.json").write_text(json.dumps(groups_meta, ensure_ascii=False, indent=1), encoding="utf-8")
                continue
            prompt = t.get("prompt_override") or to_h3_prompt(t["prompt"])

            if backend == "cloud-h3":
                # 云端 H3 v2：图 + 音频参考 → 视频自带原生口播，口型天生对齐
                model = CFG.get("cloud_h3_model", "MiniMax-H3-Highspeed")
                resolution = CFG.get("cloud_h3_resolution", "768P")
                ratio = CFG.get("cloud_h3_ratio", "9:16")
                want = max(H3_MIN_DUR, int(math.ceil(dur)))
                wav2 = Path("voice") / f"{sid}_pad.wav"
                pad_audio_to(voice, wav2, want)
                r2va = to_r2va_prompt(t["prompt"], extract_line(t))
                print(f"[{sid}] 云端 H3 v2 {model}/{resolution} {want}s（参考音频=本段配音）…", flush=True)
                tid = h3_v2_create(ref, wav2, r2va, model, want, resolution, ratio)
                print(f"[{sid}] task_id={tid}，等待出片…", flush=True)
                url = h3_v2_wait(tid)
                download(url, out_mp4)
                print(f"[{sid}] 完成 → {out_mp4}（云端自带口播音轨）", flush=True)
                continue

            frames = h3_frames(dur)
            sz = t.get("size") or [CFG.get("width", 448), CFG.get("height", 672)]
            w, h = int(sz[0]), int(sz[1])
            prefix = f"video/dhk/{sid}"
            print(f"[{sid}] 本机 H3 出片 {w}x{h} {frames}帧 ≈ {frames/24:.1f}s（可能要几分钟）…", flush=True)
            # 本机 H3 的帧数有 124 帧下限，音频比视频短时用静音补齐，
            # 否则尾部那几秒的嘴是"无锚定乱动"，口型会明显跑偏。
            audio_for_h3 = voice
            if frames / 24 > dur + 0.05:
                audio_for_h3 = Path("voice") / f"{sid}_pad.wav"
                pad_audio_to(voice, audio_for_h3, frames / 24)
            src = None
            for attempt in range(3):
                try:
                    pid = h3_generate(ref, audio_for_h3, prompt, w, h, frames, seed_base + i, prefix)
                    print(f"[{sid}] H3 prompt_id={pid}，等待出片…", flush=True)
                    src = h3_wait(pid)
                    break
                except Exception as e:
                    print(f"[{sid}] 出画失败（第 {attempt + 1}/3 次）：{str(e)[:160]}", flush=True)
                    if attempt == 2:
                        raise
                    restart_comfyui()
                    try:
                        os.remove(out_mp4)
                    except Exception:
                        pass
            # H3 出的是 video-only，把配音轨 mux 回去（上游 assemble.py 直接从段视频里取音轨）
            subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-i", str(src), "-i", str(voice),
                            "-map", "0:v:0", "-map", "1:a:0", "-c:v", "copy", "-c:a", "aac", "-b:a", "192k",
                            "-shortest", "-movflags", "+faststart", str(out_mp4)], check=True)
            print(f"[{sid}] 完成 → {out_mp4}", flush=True)
            groups_meta.append({"ids": sids, "taskId": task_id, "dur": round(dur, 3),
                                "file": f"gen/renoise-{task_id}.mp4"})
            Path(out_ids).write_text(json.dumps(ids, ensure_ascii=False, indent=1), encoding="utf-8")
            Path("groups.json").write_text(json.dumps(groups_meta, ensure_ascii=False, indent=1), encoding="utf-8")
    finally:
        if stopped_tts:
            start_voxcpm()
    Path(out_ids).write_text(json.dumps(ids, ensure_ascii=False, indent=1), encoding="utf-8")
    try:
        Path("groups.json").write_text(json.dumps(groups_meta, ensure_ascii=False, indent=1), encoding="utf-8")
    except Exception:
        pass
    return q


def extract_line(task_or_prompt):
    """台词：优先取任务里的 line 字段（H3 提示词里不再写台词），否则从提示词里抠引号内容"""
    if isinstance(task_or_prompt, dict):
        if task_or_prompt.get("line"):
            return str(task_or_prompt["line"]).strip()
        prompt = task_or_prompt.get("prompt", "")
    else:
        prompt = task_or_prompt
    m = re.search(r"[“\"](.+?)[”\"]", prompt, flags=re.S)
    if m:
        return m.group(1).strip()
    return prompt.strip().splitlines()[-1].strip()


def probe_duration(path):
    out = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                          "-of", "csv=p=0", str(path)], capture_output=True, text=True).stdout.strip()
    return float(out or 1.0)


def main():
    ap = argparse.ArgumentParser(description="digital-human-koubo 本机后端")
    ap.add_argument("cmd", choices=["account", "quote", "tts", "image", "run", "doctor"])
    ap.add_argument("arg", nargs="?")
    ap.add_argument("--text")
    ap.add_argument("--out")
    ap.add_argument("--voice")
    ap.add_argument("--prompt")
    ap.add_argument("--ref")
    ap.add_argument("--ratio", default="9:16")
    ap.add_argument("--backend", default="local", choices=["local", "cloud-h3"])
    ap.add_argument("--only")
    ap.add_argument("--merge", type=float, default=float(CFG.get("merge_seconds", 0)),
                    help="把连续短段合并成 ≤N 秒的长片段出画（省每段 ~100 秒固定开销）")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--force", action="store_true", help="忽略已有片段，全部重出")
    a = ap.parse_args()

    if a.cmd == "account":
        try:
            d = http_json(MM_BASE + "/chat/completions",
                          {"model": "MiniMax-M3.1-Flash", "messages": [{"role": "user", "content": "1"}],
                           "max_completion_tokens": 1},
                          headers={"Authorization": "Bearer " + mm_key()}, timeout=30)
            print("MiniMax 云端：可用（模型 %s）" % d.get("model", "MiniMax-M3.1-Flash"))
        except Exception as e:
            print("MiniMax 云端：不可用 →", e)
        try:
            h = http_json("http://127.0.0.1:8808/health", None, method="GET", timeout=8)
            print("VoxCPM 本机 TTS：可用 →", json.dumps(h, ensure_ascii=False)[:160])
        except Exception as e:
            print("VoxCPM 本机 TTS：不可用 →", e)
        try:
            s = http_json(f"{COMFY}/system_stats", None, method="GET", timeout=8)
            print("本机 H3 ComfyUI：可用 →", s.get("system", {}).get("comfyui_version", "?"))
        except Exception as e:
            print("本机 H3 ComfyUI：未启动 →", e, "（用 E:\\minimax H3\\start_h3.bat 起）")
        return
    if a.cmd == "doctor":
        print(json.dumps(CFG, ensure_ascii=False, indent=2))
        return
    if a.cmd == "quote":
        tasks = json.loads(Path(a.arg).read_text(encoding="utf-8"))
        print(json.dumps(estimate(tasks), ensure_ascii=False, indent=1))
        return
    if a.cmd == "tts":
        out = Path(a.out or "voice/out.wav")
        make_voice(a.text, out, backend="voxcpm" if (a.voice or "").lower() == "huakan" else None)
        print(out, f"{probe_duration(out):.2f}s")
        return
    if a.cmd == "image":
        out = Path(a.out or "stills/out.jpg")
        image_generate(a.prompt, out, ref=a.ref, ratio=a.ratio)
        print(out)
        return
    if a.cmd == "run":
        tasks = json.loads(Path(a.arg).read_text(encoding="utf-8"))
        only = set(a.only.split(",")) if a.only else None
        run(tasks, out_ids=a.out or "ids.json", backend=a.backend, only=only, dry_run=a.dry_run, merge=a.merge, force=a.force)
        return


if __name__ == "__main__":
    main()
