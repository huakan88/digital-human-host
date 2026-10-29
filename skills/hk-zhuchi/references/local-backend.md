# 本机后端（Renoise MCP 的替代实现）

这台机器上 `digital-human-koubo` / `finance-explainer` **不连 Renoise**，生成这一层换成了
「本机 MiniMax H3 + 本机克隆音色 + MiniMax 生图」。上游的 `build_tasks.py` → `assemble.py` →
`align.py` → Remotion **一行都不用改**。

```
script.json
   │ scripts/local/build_tasks.py        （和上游同构，只是读本机 persona）
   ▼
tasks.json
   │ scripts/local/backend.py run         ← 这一步替换了 create_tasks / wait_tasks / download_results
   │   ├─ 配音    本机 VoxCPM2（自己的 huakan 音色）
   │   ├─ 出画    本机 MiniMax H3（ComfyUI:8188，guide-audio 硬锚定口型）
   │   └─ 产物    gen/renoise-<taskId>.mp4 + ids.json   ← 上游约定的文件名，assemble.py 直接吃
   ▼
assemble.py（whisper-cli → 本机 FunASR 兼容层）→ cut/qa.json + cut/<id>.json
   ▼
align.py → tl.json
   ▼
Remotion（templates/huazi-916）→ 成片
```

---

## 1. 依赖清单

| 组件 | 位置 | 状态 |
|---|---|---|
| MiniMax H3（视频，65.7GB 权重） | `E:\minimax H3\ComfyUI` + `E:\minimax H3\models` | ✅ 已装，ComfyUI 0.35.0 |
| H3 命令行封装 | `E:\minimax H3\tools\h3gen.py` | ✅ 能自动拉起服务 |
| VoxCPM2（音色克隆 TTS） | `E:\AI\models\VoxCPM2` + `E:\AI\voxcpm-tools\tts_server.py` | ✅ 常驻 `127.0.0.1:8808` |
| FunASR（中文转写） | `E:\AI\envs\voxcpm`（funasr 1.4.16） | ✅ 模型已在 `E:\AI\caches\modelscope` |
| ffmpeg / ffprobe | `C:\ProgramData\chocolatey\bin\ffmpeg.exe` | ✅ 8.1 |
| Node + pnpm | `E:\AI\node24\node.exe` | ✅ v24.21.0 |
| **文生图模型** | — | ❌ **没有**。`ComfyUI\models\checkpoints` 是空的，全盘没有 FLUX / SDXL 权重 |
| whisper.cpp | — | ❌ 没有（用 FunASR 兼容层顶替） |

> 因为没有本地生图模型，**定妆照和场景图走云端 `image-01`**（¥0.025/张），其余全在本机。

---

## 2. 四个本机适配点

### 2.1 `scripts/local/backend.py` —— 顶替 Renoise 的 MCP 工具面

上游的生成动作全是 agent 调 MCP 工具（`create_tasks` / `wait_tasks` / `download_results` /
`estimate_cost` / `get_account` / `upload_files`），脚本本身不发 HTTP。所以要换的是**工具面**，
不是某个 Python 函数。本文件把这六个工具用本机能力实现出来，并且**沿用上游的产物命名约定**
（`gen/renoise-<taskId>.mp4`、`ids.json`），于是下游脚本零改动。

```bash
python scripts/local/backend.py account              # 自检：H3 / VoxCPM / MiniMax 通没通
python scripts/local/backend.py quote  tasks.json     # 报价：段数 · 秒数 · 预估 ¥
python scripts/local/backend.py run    tasks.json    # 配音 → H3 出画 → gen/*.mp4 + ids.json
python scripts/local/backend.py tts    --text "台词" --out voice/s1.wav
python scripts/local/backend.py image  --prompt "场景描述" --out stills/scene.jpg [--ref 定妆照]
```

配置在 `references/local-backend.json`（分辨率、步数、配音引擎、音色都能改）。

### 2.2 `bin\whisper-cli.exe` —— whisper.cpp 兼容层

上游 `assemble.py` / `align.py` 调的是 whisper.cpp 的命令行，并读它的 JSON：

```
whisper-cli -m <model> -l zh [--prompt "..."] [-ml 1] -oj -of cut/s1 -f cut/s1.wav
→ cut/s1.json  {"transcription":[{"text":"你","offsets":{"from":0,"to":320}}]}
```

本机没有 whisper.cpp，但有 FunASR。`scripts/local/asr_funasr.py` 用 FunASR 做同样的事，
输出同样的 JSON；`scripts/local/whisper-cli.cs` 用 `csc.exe` 编成真的 `whisper-cli.exe`
（`.cmd` 不行：Windows 的无扩展名查找不会命中 `.cmd`，而上游是用 `subprocess.run(['whisper-cli', …])` 调的）。

用的时候把 skill 的 `bin` 加进 PATH：

```bash
export PATH="<skill>/bin:$PATH"      # Git Bash
set PATH=<skill>\bin;%PATH%          # cmd
```

> 改 `whisper-cli.cs` 后重新编译：
> `csc /nologo /target:exe /out:bin\whisper-cli.exe scripts\local\whisper-cli.cs`

### 2.3 Remotion 的 TEMP 坑（本机最隐蔽的一个）

Remotion 把中间文件写进 `%TEMP%\react-motion-render*\pre-encode.mp4`。本机系统 TEMP
（`C:\Users\huaka\AppData\Local\Temp`）对子进程是**拒绝写入**的，于是：

```
Error opening output …\pre-encode.mp4: Permission denied
→ ffmpeg 退出 → Node 端只剩一句 "Error: write EOF"
```

看起来像 Remotion 版本问题、显卡问题、pipe 问题，全都不是。**把 TEMP/TMP 指到工程目录就行**，
`scripts/local/render.sh` 已经代劳：

```bash
export TEMP="<工程目录>/../.tmp"; export TMP="$TEMP"
npx remotion render src/index.ts Huazi out/raw.mp4 --concurrency=3
```

### 2.4 Remotion 版本

上游模板钉的是 `4.0.408`。本机用 **`4.0.534` + React `19.2.3`** 渲染（本机其它工程都是这组），
`4.0.408` 也能跑但要先把 TEMP 改掉。改法：`edit/package.json` 里把所有 `@remotion/*` 和
`remotion` 换成 `4.0.534`，`react`/`react-dom` 换 `19.2.3`，补 `@remotion/media`、
`@remotion/media-utils`，再 `npm install`。

---

## 3. 形象与声音

- **形象**：`scripts/local/persona.local.json` → **短发男生**。定妆照
  `assets/host_me_look.jpg`（用户本人正脸照 → MiniMax image-01 + subject_reference 生成）。
  换成用户自己的正面照：把 `renoise.reference_material` 指到那张图即可。
  定妆照要**正脸、闭嘴、头顶留白**——留白不够，成片会顶到脸。
- **声音**：本机 VoxCPM2 克隆音色 `huakan`（就是用户自己的声音）。
  `tts_speed` 默认 0.85（≈5.3 字/秒，口播更稳）；`speed` 是服务端 ffmpeg atempo 倍率。
- 语速实测：原速 6.25 字/秒 → 0.85 倍速 ≈ 5.3 字/秒。

### 3.1 七视图（做新形象时走这条）

```bash
# 1) 把用户自己的正脸照放到 assets/host_me_ref.jpg（2048 级、正脸、闭嘴、光线均匀）
ffmpeg -y -i assets/host_me_ref.jpg -vf scale=1024:1024 assets/host_me_ref_1k.jpg
# 2) 生成七视图素材（3 次生图，约 ¥0.08）
python scripts/local/make_avatar.py      # 七视图全身 + 七视图半身 + 9:16 定妆照
python scripts/local/make_7view.py       # 多种版式的候选，挑一版
# 3) 拆图 + 自己拼成标准七视图（4+3，纯白底，无文字）
"E:\minimax H3\venv\Scripts\python.exe" scripts/local/sheet_build.py
```

产出：
| 文件 | 用途 |
|---|---|
| `assets/host_me_ref.jpg` | 用户本人原照（只用作参考，别直接当出画图） |
| `assets/host_me_look.jpg` | 9:16 定妆照 → **H3 的 ref/guide 图**（正脸、闭嘴、留白） |
| `assets/host_me_7view.jpg` | 七视图总表（4+3） |
| `assets/host_me_views/view_1..7.jpg` | 七张单视图（换角度出场景图时用） |

**image-01 的两个坑（实测）**
1. `subject_reference` 的 `image_file` 要写成 **data URL 字符串**，不是数组；
   数组会被判 `invalid params`。
2. **它不会听话地"转角度"**：让它一张图里出七个角度，它会丢角度、把自己加的编号也画上去、
   或者八个全变正面。所以别指望一张图出七视图——**一次生成一排（自带一致性），
   再用 `sheet_build.py` 自己切、自己拼**，角度和版式才可控。
3. 提示词超过 1500 字符会被拒（`prompt length must be less than 1500`）。

---

## 4. H3 出片的硬约束

| 项 | 值 |
|---|---|
| 单段时长 | ≤ 10 秒（帧数落在 `17k+5` 网格，24fps） |
| 分辨率 | 宽高都必须是 32 的倍数。9:16 → `576x1024`；16:9 → `704x384` |
| 显存 | 8GB 卡上 576x1024 + VoxCPM 常驻（约占 5.7GB）能跑，但会慢；紧张时用 `448x672` |
| 速度 | 576x1024 / 124 帧 / 4 步 turbo ≈ 3–5 分钟一段 |
| 口型 | `--guide-audio` 把音频 latent 硬锚定（`AUDIO_COND_TIMESTEP=1.0`）→ 口型逐字跟配音 |
| 画面 | H3 出的是 video-only，`backend.py` 会把配音轨 mux 回段视频，上游照常取音轨 |

`backend.py` 内部做的事：

1. `h3gen.py --ref-image 定妆照 --guide-image 定妆照 --guide-audio 配音.wav --video-only`
2. 轮询 `GET /history/<prompt_id>` 拿输出 mp4
3. `ffmpeg` 把配音 mux 回段视频 → `gen/renoise-<taskId>.mp4`

---

## 5. 口型（这一关最容易翻车）

**结论：本机 H3 能做出真口型，但提示词必须用 `<Picture 1>` / `<Audio 1>` 绑定参考图和配音。**

踩过的坑（按影响排序）：

| 坑 | 症状 | 解法 |
|---|---|---|
| **没写 `<Picture 1>` / `<Audio 1>`** | 嘴在动，但和声音完全对不上（相关性 ~0.09，嘴部曲线是缓慢漂移） | 提示词里写 `Use the exact same adult Chinese man in <Picture 1>` 和 `Speak Mandarin Chinese precisely synchronized to <Audio 1>`。这是 h3gen 自己的约定（`h3gen.py:685`：「prompt 里必须用 `<Picture 1>` <Picture 2> … 按接线顺序引用参考图」） |
| **台词写进了提示词** | 模型自己再编一遍台词，和配音对不上 | 台词只由 `<Audio 1>` 提供，提示词里不写台词，只写「no additional words」 |
| **用了 `--ref-audio` 代替 `--guide-audio`** | 只有音色像，口型不跟 | `--guide-audio` 是硬锚定实际口播；`--ref-audio` 只软参考音色/节奏 |
| **提示词没要求闭嘴** | 停顿时嘴还张着 | 写「natural mouth and jaw movement during speech, **lips resting closed during pauses**, no additional words or music」 |
| **音频比视频短** | 尾部几秒嘴在无锚定乱动 | H3 帧数有 124 帧下限（≈5.17s），音频短就用静音补齐（`backend.py` 已自动做） |
| **出画时 TTS 服务还在跑** | ComfyUI 直接 `CUDA error: out of memory`，卡 20 分钟 | 出画前停掉本机 TTS（占 ~5.7GB 显存），出完再拉起来（`backend.py` 已自动做） |

**自检工具**（判断口型合不合格，别靠肉眼瞎猜）：

```bash
python scripts/local/lipsync_eval.py <段视频.mp4> [--plot 对照图.png] [--sheet 嘴部帧条.png]
```
- `corr` 越高越同步；`best_lag` 接近 0 才算没整体延迟
- `--plot` 画出「音频能量 vs 嘴部开合」两条曲线，峰值对得上才算真同步
- `--sheet` 输出嘴部帧条（连续帧），能直接看出有没有闭嘴、露齿、圆唇

> 指标只是代理，**最终以抽帧看为准**：连续帧里要能看到「张嘴→露齿→闭嘴」的节奏变化。

**云端备选**：MiniMax H3 v2（`/v2/video_generation`，reference_image + reference_audio）能生成原生口播音频，
口型天生对齐——但本机 Token Plan 套餐等级不支持（HTTP 402 / 2068），要用得先升级套餐。
`backend.py --backend cloud-h3` 的代码已就绪。

---

## 6. 报价（生成前一定要先报给用户）

| 项 | 单价 | 本机一次 3 段 15 秒的量 |
|---|---|---|
| H3 出画（本机） | ¥0 | ¥0 |
| 定妆照 / 场景图（`image-01`） | ¥0.025 / 张 | ¥0.075 |
| 配音（本机 VoxCPM2） | ¥0 | ¥0 |
| MiniMax H3 云端备用 | 768P ¥0.40/s，2K ¥0.80/s | 需要时才用 |

`backend.py quote tasks.json` 会直接打印「段数 · 秒数 · 预估 ¥」。

---

## 7. 故障排查

| 现象 | 原因 | 处理 |
|---|---|---|
| Remotion 报 `Error: write EOF` | 子进程写不了系统 TEMP | 把 `TEMP`/`TMP` 指到工程目录（见 2.3） |
| `assemble.py` 报找不到 `whisper-cli` | skill 的 `bin` 不在 PATH | `export PATH="<skill>/bin:$PATH"` |
| H3 提交后一直不返回 | ComfyUI 没起来 | `E:\minimax H3\start_h3.bat`；`h3gen.py` 也会自动拉起 |
| H3 显存不足 | VoxCPM 常驻吃了 ~5.7GB | 渲染期间停掉 TTS 服务，或把分辨率降到 448x672 |
| 口型对不上 | `--guide-audio` 的音频被裁短 | 段音频必须是**完整台词**，不能截中间 |
| `image-01` 返回 `response_format not 'url' or 'base64'` | 只能用 `base64` | 用 `response_format: "base64"`，取 `data.image_base64[0]` |
| image-01 的签名 URL 403 | OSS 签名 URL 经代理/重编码失效 | 同上，用 base64 直取 |
| 「文字在人身后」抠像用不了 | `cutout_video.py` 依赖 macOS Vision | 本机没有等价实现，这个包装组件暂不可用 |

---

## 8. 上游没改动的部分

`scripts/assemble.py`、`scripts/align.py`、`scripts/check_edit.py`、`scripts/voicefx/unify.py`、
`scripts/make_assets.py`、`templates/*` 全部保持上游原样。只有 `SKILL.md` 顶部加了一段
「本机后端覆盖」的说明，`scripts/local/` 和 `bin/`、`references/local-backend.json`、
`references/local-backend.md` 是新增的。
