---
name: hk-zhuchi
description: hk主持 —— 数字人主持的口播视频工作流。短发男生主持人（本机 MiniMax H3 出画，口型逐字跟配音）+ 本机克隆音色配音 + koubo-video 竖版花字包装；数字人先全屏开场、再缩成左下角约十分之一大小的圆形小窗继续主持，全程本机、几乎零成本。触发：hk主持、用 hk 主持做一期、做一期数字人口播、让这个数字人讲这段、做个数字人主持的视频、开场大图然后缩到左下角。适合：科普/冷知识/工具讲解/产品口播。不用于：真人出镜、纯横版无数字人（用 koubo-video）、需要严格人脸复刻（先用 face-swap）。
---

# hk主持

一条**固定主持人**的数字人口播视频流水线：写稿 → 配音 → 出画 → 配画面 → 花字包装 → 成片。
主持人是**短发男生**，声音是**你自己的克隆音色**（本机 VoxCPM2 `huakan`），画面是**本机 MiniMax H3** 生成。
成本几乎为零：只有换形象时需要云端生图（¥0.025/张），其余全在本机。

## 成品长什么样

- **开场**：数字人**全屏**（1080×1920 竖屏），带手部和身体动作，字幕逐字卡拉OK跳动
- **正文**：数字人**缩到左下角圆形小窗**（直径 200px，约页面十分之一），白边描边，不挡字幕；
  主画面交给内容素材（16:9 素材用「模糊底 + 完整画面」竖版化）
- **包装**：顶栏胶囊标题、章节目录条、关键词变色放大、动态表情、数字卡/标签卡/砸屏大字、弹幕、结尾号召
- **角标**：左上角常驻「内容由 AI 数字人演绎」

## 第一原则：素材优先（**硬指标，用户明确要求**）

> 2026-10 用户原话：「需要特别多的素材，里面一定要是用素材填充的，
> 而不是干巴巴的都是 Remotion 的内容」。
> **这条优先于其它一切包装规则。**

### 硬指标（出片前逐条打勾）

- [ ] **真实素材时长 ≥ 成片的 50%**（拿 `ffprobe` 算一下，别凭感觉）
- [ ] **至少 8 段不同素材**；一期 60~90 秒的片子，素材段越多越好
- [ ] **不允许连续 2 拍以上都是纯文字卡**。纯 Remotion 卡只用于三类：数据卡（数字/条形/表格）、
      过渡/章节、结尾收束
- [ ] 每条素材画面上都有署名（平台 · 作品名 · 作者 · 编号）
- [ ] 能用「文字压在素材上」就不要做纯文字卡 —— 用 `cliptext` beat
- [ ] 用户自己的作品**必须用**，并且文案里点名"这是我自己做的"

### 反面例子（别这么做）

一期 70 秒里有 55 秒是深色底 + 文字卡 = 干巴巴。
正确做法：每一拍先问「这一拍能不能用一段真实画面」，能就上素材，文字叠上去。

### 素材密度怎么保证

1. 先按脚本的**每一拍**列一张表：这一拍讲什么 → 配哪段素材（没有合适的就去找）
2. 素材不够就去抓（见下一节「真实素材：从哪来」）
3. 把「数据卡」压缩到最少：一期里 3~4 张足够，其余全用画面
4. 同一段素材可以复用在不同位置，但 `from` 要错开，避免观众看出重复

### 自检命令

```bash
# 估算素材占比：把 BEATS 里所有 clip / cliptext 的段落时长加起来 ÷ 总时长
# 简单办法：看成片，纯色底/纯文字卡超过一半就是不合格
```

## 口型对齐（**强制项 · 不做就不算交付**）

> 适用于本技能的**所有**主持预设：白背心女性（vivi主持）、短发男生（hk主持），
> 以及以后新加的任何形象。**没有例外，不是可选项。**

出片前必须完整走完下面 5 条，缺一条都不算做完：

### 1. 出画阶段
- 必须用 `<Picture 1>` 绑定参考图、`<Audio 1>` 绑定配音；**台词不写进提示词**
- 提示词必须含 "lips resting closed during pauses"
- **露脸段必须单独出画**（一段一次 H3 调用），每段 ≤ 6 秒；超过就拆句。
  合并出画只允许用在"不露脸"的场合 —— 长片段内部口型会逐渐松掉（实测 10 秒片
  前 5 秒 corr 0.58、后 5 秒掉到 0.34）。
- **不要在同一个露脸窗口里拼两段独立出画**：两次生成的脸型、景别、光线会有细微差别，
  拼在一起就是一次可见的跳切（实测 2.1s → 2.35s 的脸突然变小、位置偏移）。
  一个连续镜头 = 一次生成。

### 2. 修复阶段（必跑）
```bash
python scripts/lipsync_repair.py --dir gen --out gen/fixed     # 两轮迭代 + 只采纳更好的
```
它会按 0.5 秒一段测出"嘴-音"局部偏移，重新对齐画面；修完不如原来会自动保留原片。

### 3. 装配阶段
- `build_media.py` 会自动优先用 `gen/fixed/`
- **绝对不要用配音原始时长去算时间窗口**，必须用 `public/timeline.json`（帧栅格时间轴）。
  两者差 1/60 秒/段，22 段就累积到 0.27 秒 —— 越靠后的露脸段画面越提前，这是
  "后面口型对不上"最常见的真凶。用 `make_host_wrap.py --host-segs` 按段 id 定窗口即可。

### 4. 验收阶段（必跑，出片前）
```bash
# 逐段量：整窗偏差 + 每 1.5 秒子窗偏差
E:\AI\envs\voxcpm\Scripts\python.exe sync_report.py 成片.mp4 "起-止,起-止,..."
```
判据：**每段整窗 |lag| ≤ 2 帧（30fps 下 ≤ 67ms）**。

注意两点，否则会误判：
- 一定**逐段**量，别整窗量：一个窗口里拼了多段出画时，测量会取折中框，结果乱跳
- 测量要避开字幕区（`y > 0.62`）：字幕总是领先语音，否则会假报 -6 帧

### 5. 不达标怎么办（按顺序）
1. `gen/nudge.json` 定点平移：`{"s1": 7}` = 把该段画面往后推 7 帧（**确定有效**，s1 就是这么修好的）
2. 换种子重出这批：`HK_SEED=917733 ... backend.py run --force --only ...`，再用 `best_of.py` 择优
3. 还不行 → 该段改成版式卡（不露脸），别硬扛
4. 交付时**附上验收表**

> 已到能力边界：本机 H3 的口型在 ±100ms 以内我这套测量分辨不出（两批独立出画给出相同分数、
> 相邻子窗会 ±10 帧乱跳）。所以可承诺的是「全局 ≤2 帧」，做不到逐字级专业对白。
> 真要逐字级，只能上嘴型重生成模型（LatentSync / Wav2Lip），那是独立安装工程。

## 口型验收与修正规范（2026-10 血泪版）

### 一句话原则
**先用眼睛看，再用数字判。** 自动打分的嘴框一旦偏了，会把对的判成错的，
然后按错的数据去"修"，把本来是对的画面推歪 —— 这次就是这么把一条片子修坏的。

### 用这个工具看（唯一可信的验收方式）
```bash
python scripts/sync_pic.py <片段或成片> <起始秒> 12 "0.28,0.36,0.72,0.56"
# → 上方是逐帧嘴部裁切，下方是同帧的音频能量条
```
**判读**：嘴张得最大的那几帧要落在蓝色高条上；音频是暗条（静音）时嘴必须闭上。
对不上多少格，就是差多少帧。

> 嘴框按形象调：白背心女性 / 短发男生这种自拍构图，嘴在 **y 0.42~0.52、x 0.30~0.70**。
> 框放错（比如落到脖子/锁骨上）会得到完全无意义的结果 —— 这是最隐蔽的坑。

### 自动打分只用来抓大偏
```bash
python scripts/sync_report.py <成片> "起-止,起-止"    # 逐段整窗 lag + 子窗 lag
```
- 只在**单段**（一次生成）上用；把几段拼在一个窗口里量，会取折中框然后乱跳
- 判据：整窗 |lag| ≤ 2 帧（30fps 下 ≤67ms）
- 它分辨不出 ±100ms 以内（实测同一段内容连测两次能给出 -4 和 -9）

### 已确认的坑（症状 → 真因 → 修法）

| 症状 | 真因 | 修法 |
|---|---|---|
| 「只有前几秒口型对」 | 合并出画时按"组"拼主画面，每组少一个段间间隔，累计 +3 秒 | 按**段**切；窗口边界用 `public/timeline.json`，**不要用配音原始时长**（差 1/60 秒/段会累积） |
| 越靠后的露脸段画面越提前 | 同上，用原始时长算窗口 | `make_host_wrap.py --host-segs` 按段 id 吸附 |
| 某个窗口数字人根本不出现 | ① `groups.json` 写错目录（要在**工程根**）② 逐段判定用了残留变量（要 `S[i]["id"]`）③ `<OffthreadVideo>` 放在晚出场的 `<Sequence>` 里不渲染 | 数字人统一铺一条 `main.mp4` 当底图；beat 用 `onlyOverlay` 让位 |
| 我以为画面错了，其实没错 | `ffmpeg -ss T -i x.mp4` 是**关键帧跳转**，抽到的是几秒前的帧 | 一律 `ffmpeg -i x.mp4 -ss T`（输出侧 seek） |
| 修完更不对 | 按错框的自动打分做平移 | 回退，只用原始出画；确认要看 `sync_pic.py` |
| 一段里嘴巴/身体/词三者都对不上 | 出画模型这一段本身就没跟住音频（不是时间轴问题） | **这一段重出**（换种子），或者改成版式卡。平移救不了 |

### 出画阶段的硬规定
1. 露脸段**一段一次生成**，每段 ≤6 秒；超过就拆句
2. **一个连续镜头只能一次生成**：两次生成拼在一个窗口里，脸的大小/位置/光线会变，观众读作"跳切"
3. 提示词必须含 `<Picture 1>` + `<Audio 1>` + "lips resting closed during pauses"

### 还是不对怎么办（按这个顺序）
1. 先用 `sync_pic.py` 确认**到底错多少帧**（别猜）
2. 差 1~3 帧：`gen/nudge.json = {"s9": 2}` 定点平移（确定有效，别整段大改）
3. 差得多或"身体也不对"：**这一段重出**（`HK_SEED=<别的值> --force --only <段>`），
   再用 `best_of.py` 和旧版比分数择优
4. 还不行：这一段改成版式卡（不露脸），别硬扛
5. 交付时附上 `sync_pic.py` 的截图作为证据

### 不要做的事
- ❌ 不要凭自动打分的单次结果去批量平移所有片段
- ❌ 不要为了"修口型"去缩短句子、砍字（会改稿，而且不解决根本问题）
- ❌ 不要把两段独立出画拼进同一个露脸窗口
- ❌ 不要在没跑 `sync_pic.py` 的情况下声称"口型已对齐"

## 真实素材：从哪来、怎么嵌、怎么标（2026-10 实测）

图文卡撑得住信息，但**没有真实片段会显得空**。这一节是实测能走通的路子。

### 本机能通 / 不通（先看这张表，别浪费时间）

| 站点 | 可达 | 说明 |
|---|---|---|
| **Bilibili** | ✅ 200 | `yt-dlp` 直接下，最可靠。**28 集的动态设计合集这种＝一堆独立作品** |
| **Contra** | ✅ 200 | 作品页里有 `media.contra.com/...mp4`（Cloudinary 直链），curl 就能拿 |
| Vimeo / TikTok / 抖音 | ✅ 200 | 未深测，`yt-dlp` 大概率可用 |
| Dribbble | ⚠️ 202 | Cloudflare 挑战，页面拿不到 |
| Rive 社区 | ❌ 000 | 不通 |
| **X / Twitter** | ❌ 000 | 官方、fxtwitter、syndication 全不通；`yt-dlp` 也需要先能连上 |
| YouTube | ❌ 000 | 不通 |

> X 上的作品，去**作者自己的作品页**（Contra / 个人站 / Dribbble）拿原始 mp4，
> 往往比从 X 转存质量更好。（例：Owl Loading 在 contra.com 就有 1600px 原片）

### 抓素材的最小命令

```bash
# B站（最省事）
yt-dlp -f "bv*[height<=720]+ba/b[height<=720]" --max-filesize 80M -o "clips/%(id)s.%(ext)s" "https://www.bilibili.com/video/BVxxxx"

# Contra 这类作品页：先抓 html 再抠直链
curl.exe -s -A "Mozilla/5.0" "https://contra.com/p/xxxx" -o page.html
# 然后 grep media.contra.com/video/upload/...mp4，挑 w_1600 那档
```
> PowerShell 里 `curl` 是 `Invoke-WebRequest` 的别名，**必须写 `curl.exe`**。

### 嵌进片子

| 需求 | 用什么 beat |
|---|---|
| 单纯展示作品（带信源角标） | `clip` |
| **文字压在画面上** | `cliptext`（本仓库补丁 `patch_koubo_cliptext.py` 已加：视频铺满压暗 + 大字居中 + 副标题） |

```bash
python patch_koubo_cliptext.py <koubo 工程>    # 模板与工程各跑一次
```

### 挑 `from` 起始秒（最容易白干的一步）

同一个素材里，有的时间点是大片留白/黑场/转场。**必须先抽帧看，再写 from**：

```bash
for t in 2 8 14 22 30 38; do ffmpeg -v error -y -ss $t -i clip.mp4 -frames:v 1 -vf scale=300:-2 probe_$t.png; done
```
拼成对照图挑一帧有内容的，再把它的时间写进 beats。

> ⚠️ **改 `from` 不要用字符串替换。** 本仓库踩过：把 `"from": 1` 去替换，
> 命中了 `"from": 18` 的**前缀**，结果变成 `"from": 308`（超出片长）→ 画面全灰，
> 查了半天。改数值一律**整行重写**，或者用 JSON 结构化编辑。

### 署名（硬性）
每条真实片段都要在画面上带：
- `tag`：`真实作品` / `我的作品`
- `src_label`：**平台 · 作品名 · 作者 · 编号**（如 `Bilibili · Ravie 动态设计合集 · BV1wC4y1M7y6`）

### 自有素材
用户自己的作品直接进 `public/clips/`，`tag` 写 `我的作品`，`src_label` 写清项目名。
用户自己的片子放进片子里是**最强的可信度**，别只当素材，要在文案里点名"这是我自己做的"。

## 工作流（照着走）

### Step 0 · 环境自检（第一次做，或换机器后）

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File <skill>\doctor.ps1
```

要绿的有：ffmpeg、Node 24、Remotion 4.0.534、本机 H3（ComfyUI:8188）、本机 TTS（:8808）、FunASR。
缺 Remotion 依赖就 `npm install --registry=https://registry.npmjs.org --proxy=null --https-proxy=null`。

### Step 1 · 选题与调研

- 内容方法论、素材抓取、信源规范 → **交给 `koubo-video`**（它有成体系的调研/素材/信源/自检清单）
- 猫、科普、工具拆解这类题材，本机已有素材库（`E:\minimax H3\0*_...项目\video\final\clip_s*.mp4`）可直接复用

### Step 2 · 写稿（≤ 8 句，60–100 秒）

`script.json`：

```json
[{ "id": "s1", "card": "s1", "size": [576, 1024], "big": true, "t": "这一句要念的台词" },
 { "id": "s2", "card": "s2", "size": [576, 1024], "t": "第二句" }]
```

- `t` = 台词（配音和字幕都用它）
- `big: true` = 这段数字人**全屏**（只有第一段用）
- `size` = **统一 `[576, 1024]`**，不要为了省时间改小（见下面的「分辨率铁律」）
- `card` = 可选：这句配哪张证据版式（工程目录 `cards/<id>.png`）；没有就配素材库的 `clip_<cat>.mp4`
- **默认一口气出片**；用户说「先看稿」才停下来发稿等确认

> ⚠ **分辨率铁律**：出画分辨率不能降。本机实测 384×576 会让**鼻头变大、脸变形、口型发糊**，
> 576×1024 同一个提示词出来的脸才正常。省时间要用别的办法（减段数、减句长），不要降分辨率。

### Step 3 · 出画（本机 H3）

```bash
python <skill>\scripts\make_tasks.py                 # script.json → tasks.json
python <skill>\scripts\backend.py quote tasks.json   # 先报价：段数 · 秒数 · 预估花费
python <skill>\scripts\backend.py run   tasks.json   # 配音 → H3 出画 → gen\renoise-<id>.mp4 + ids.json
```

**口型的铁律**（写错就前功尽弃）：

- 提示词必须用 `<Picture 1>` 绑定参考图、`<Audio 1>` 绑定配音（h3gen 的约定）
- **台词不要写进提示词**，台词由 `<Audio 1>` 提供，提示词里写 "no additional words"
- 提示词里必须要求 "lips resting closed during pauses"（停顿要闭嘴）
- 必须要求手部/身体动作，否则出来是木头人
- 必须锁五官：「identical face shape, identical nose shape and nose width … no beautification, no distortion」
  —— 不写这句，低分辨率下模型会把鼻子越生成越大（`scripts/make_tasks.py` 的 `LOOK` 里已经内置）

### Step 4 · 组装素材

```bash
python <skill>\scripts\build_media.py     # 旁白总轨 + 主画面 + 小窗轨 + 逐字时间轴
```

产出 `public/main.mp4`（开场大图 + 正文素材）、`public/pip.mp4`（小窗数字人）、`public/voice.wav`（旁白）、
`cut/qa.json`（回听质量）、`edit/src/tl.json`（逐字时间轴）。

### Step 5 · 花字配置

改 `edit/src/edit.json`：标题、章节、关键词、表情、卡片、砸屏大字、结尾号召。
时间写法：`"3:"` 第 3 段开头 · `"3:关键词"` 该词开始 · 数字 = 绝对秒。

**小窗参数**：`"pipFrom": 9.85`（开场大图结束的那一秒）、`"pipSize": 200`、`"pipMargin": 36`。

### Step 6 · 校验 + 渲染

```bash
python <skill>\scripts\check_edit.py edit\src      # 时间引用对不上就别渲
cd edit && npx remotion render src/index.ts Huazi out\raw.mp4 --concurrency=3
ffmpeg -i out\raw.mp4 -af loudnorm=I=-16:TP=-1.5:LRA=11 -c:v libx264 -crf 20 成片.mp4
```

> ⚠ **TEMP 坑**：Remotion 把中间文件写在 `%TEMP%`，本机系统 TEMP 对子进程拒绝写入，
> 会报一句没头没尾的 `Error: write EOF`。**渲染前把 `TEMP`/`TMP` 指到工程目录**：
>
> ```bash
> export TEMP="$(cd .. && pwd)/.tmp"; export TMP="$TEMP"; mkdir -p "$TEMP"
> ```
>
> `scripts\render.sh` 已经代劳。

### Step 7 · 自检（出片前必看）

抽帧看 4 个点：**开场第 3 秒**（大图+手势）、**正文第 15 秒**（小窗位置+字幕不挡）、**每个卡片出现时**、**最后 3 秒**（号召）。
再跑 `python <skill>\scripts\lipsync_eval.py <段视频.mp4> --plot 对照.png` 看口型对不对得上。
清单见 `references/qc.md`。

## 形象

| 项 | 值 |
|---|---|
| 主持人 | 短发男生，黑色短寸（两侧推短），橄榄绿亨利领短袖（三颗扣），无胡须，约 170cm |
| 定妆照（喂 H3） | `assets/host_me_look.jpg`（9:16，正脸、闭嘴、头顶留白） |
| 七视图 | `assets/host_me_7view.jpg` + `assets/host_me_views/view_1..7.jpg` |
| 原始正脸照 | `assets/host_me_ref.jpg` |
| 声音 | 本机 VoxCPM2 克隆音色 `huakan`（自己的声音），语速 0.85 倍 ≈ 5.3 字/秒 |
| 人物设定全文 | `persona/persona.json` |

**换人**：把新的正脸照放成 `assets/host_me_ref.jpg`，跑 `python scripts/make_avatar.py` 生成新的定妆照与七视图，
再改 `persona/persona.json` 的 `look` 与提示词。

**换衣服/发型**：改 `persona/persona.json` 的 `prompt_template`，重新生成定妆照。

## 和其它 skill 的分工

| 环节 | 用哪个 |
|---|---|
| 数字人形象 / 口型 / 花字包装组件 | **本 skill**（hk主持） |
| 调研 / 抓素材 / 信源规范 / 通用方法论 | `koubo-video` |
| 另一条数字人风格（白背心数字人、小林说式财经） | `digital-human-koubo` |
| 3D 空镜 | `diorama-video` |
| 外部 BGM / 音效 / 图片 | `media-use` |
| 科普视觉语言选型 | `kepu-video-styles` |

## 目录

```
SKILL.md                      本文件
persona/persona.json          人物设定（形象/声音/提示词模板/服装）
assets/                       定妆照、七视图、原始正脸照
templates/huazi-916/          Remotion 工程模板（含 HostPip 左下角小窗层）
scripts/
  make_tasks.py               script.json → tasks.json
  backend.py                  本机后端：配音 / 生图 / H3 出画 / 报价 / 自检
  build_media.py              旁白总轨 + 主画面 + 小窗轨 + 逐字时间轴
  asr_funasr.py               whisper.cpp 兼容层（本机 FunASR）
  whisper-cli.cs              编译成 bin\whisper-cli.exe
  lipsync_eval.py             口型同步度评估（相关性 + 对照图 + 嘴部帧条）
  render.sh                   渲染 + 成片（TEMP 已处理）
  doctor.ps1                  环境自检
references/
  local-backend.md            本机后端全部踩坑（口型/显存/Remotion/下载签名）
  host-pip.md                 「大→小」小窗规格与模板改法
  qc.md                       出片自检清单
bin/whisper-cli.exe           whisper.cpp 兼容层（编译产物）
examples/cat/                 一期完整样例（工程目录）
```

## 出画速度：先看这张表再调参

本机 RTX 5060 Laptop（8GB 显存）实测，**576×1024、turbo、576 帧上限内**：

| 片段长度 | 帧数 | 每步耗时 | 每段总耗时 | 结论 |
|---|---|---|---|---|
| 5.2 秒 | 124 | 30 秒 | ~192 秒 | 正常 |
| 10 秒 | 240 | 48.5 秒 | ~234 秒 | **每秒成本最低** |
| 15 秒 | 360 | **901 秒** | ~45 分钟 | ❌ 爆显存，疯狂换页 |

**超过约 300 帧（12.5 秒）会掉进显存悬崖**：注意力矩阵装不下 8GB，
单步耗时从 30 秒涨到 900 秒。所以 `--merge` 最多给到 10，别贪长。

其它省时间的（都已在引擎里默认打开）：
- **批量 ASR**：FunASR 模型只加载一次（单段加载 ~40 秒 × N 段）
- **配音缓存**：`voice/<id>.wav` 已存在就跳过，重跑不重花配音钱
- **断点续跑**：片段按段 id 命名（`gen/renoise-<组内第一段>.mp4`），崩了接着跑
- **自动重启重试**：ComfyUI 连跑十来段会报 `hostbuf_file_reader_read failed`，
  引擎会杀进程重开再试（最多 3 次）
- **`build_media.py --no-asr`**：只改卡片/字幕时复用已有时间轴
- 别开 `--low-vram`：它强制权重异步换出，每段多花 ~40 秒

真正的捷径是云端 H3（`--backend cloud-h3`，¥0.40/秒，约快 10 倍），
但 Token Plan 免费档会返回 402 code 2068。

## 花字卡片：必须写 `until`

模板里卡片的默认结束时间是**本段结束**（`min(seg.end, 下一张卡, at+4.5)`）。
如果关键词在句子末尾，卡片就只亮 1 秒，几乎看不见 —— 这是最容易白忙一场的坑。

```json
{ "type": "number", "at": "4:二十八天", "until": "6:交付物", "value": 28, "unit": " 天" }
```

写完一定抽帧验：`ffmpeg -ss <卡片中点> -i 成片.mp4 -frames:v 1 x.png`。

## 全程放大模式（小窗口型的保险方案）

如果小窗那段的口型/画质怎么调都不满意，**直接不要小窗**：

```bash
python build_media.py --full      # 主画面 = 数字人全程全屏
```
```json
// edit.json
{ "pipOff": true }                 // 关掉小窗（不写 pipFrom 不会关，会从 0 秒就显示）
```

原理：小窗之所以"看起来口型不对"，多半是那几段用了低分辨率出画（384×576 会让脸崩、嘴糊）。
`--full` 让所有段都当主画面用同一个 576×1024 出画，花字卡片由模板叠在人物上面 ——
口型问题从结构上绕开，不用赌。

代价：画面只有人物，需要"展示东西"的内容（截图、图表、作品）得靠 `image` / `showcase` 卡片叠上去。

## 口型对不上的头号原因：时间轴漂移（不是分辨率！）

「只有前几秒口型对得上，越往后越不对」—— 几乎都是**累积漂移**，跟分辨率无关。

三个必踩的坑，都已经在 `build_media.py` 里修好，别改回去：

1. **合并出画时按「组」拼主画面** → 每组只贡献一个段间间隔，被合并掉的段各少 0.25 秒。
   29 段合 17 组 → 少 12 个间隔 = **+3.00 秒**，画面就越走越偏。
   ✅ 正确做法：**按段切**。每段从所在组里取 `[offset, offset+slot]`，offset 是组内该段的起点。

2. **切片按秒不按帧** → 每段多出 1~2 帧，29 段累计 +1.7 秒。
   ✅ 正确做法：**帧栅格是唯一真相**。先算 `frames_i = round((durs_i + GAP) * FPS)`，
   再用 `slot_i = frames_i / FPS` 反过来截旁白（`apad,atrim=0:slot_i`），画面用 `-frames:v frames_i`。
   这样旁白总长 == 主画面总长，一个字节都不差。

3. **源片段没有尾部的段间静音** → 切 `[0, slot]` 会短一个 GAP。
   ✅ 正确做法：切片时加 `tpad=stop_mode=clone:stop_duration=1`，把最后一帧冻住补满。

**自检命令**（每次出片前跑一下，两边必须相等）：

```bash
ffprobe -v error -show_entries format=duration -of csv=p=0 public/main.mp4
ffprobe -v error -show_entries format=duration -of csv=p=0 narration.wav
# 例：131.500 vs 131.500 ✅   133.233 vs 131.533 ❌ 差 1.7 秒，画面会越走越偏
```

再抽几段嘴部帧条看：`ffmpeg -ss <靠后的时间> -i 成片.mp4 -vf "crop=...,select='between(n,0,11)',tile=6x2"`，
每 10 秒一段都该有开合变化；连续十几帧都闭着嘴而旁白还在响，就是漂了。

## 露脸策略：出画模型的同步能力有上限，别硬扛

实测（本机 H3 / 576×1024 / turbo）：

| 现象 | 数据 |
|---|---|
| 同一段出画，前 5 秒 vs 后 5 秒 | corr 0.58 → 0.34（**越往后越松**） |
| 不同片段之间的固定偏移 | **-333ms ~ +375ms**（四种缩放测都一致，不是噪声） |
| 5 秒左右的片段 | 前后半 corr 都在 0.42~0.47，可以接受 |

结论：**露出脸的时长越短、片段越短，口型越可信。**

所以给了三档，按内容选：

| 模式 | 命令 | 露脸 | 适用 |
|---|---|---|---|
| 混合（推荐） | `HK_HOST_INTRO=10 HK_HOST_OUTRO=8 build_media.py --full` | 只在开场+结尾 | 长视频、要露出很多信息的 |
| 全程全屏 | `build_media.py --full` + `pipOff` | 全程 | 短口播（≤30 秒）、脸要一直在的 |
| 卡片+小窗 | `build_media.py` + `pipFrom` | 小窗 | 画面以图表为主、人只是串场 |

**逐片段口型对齐**（可选，改善但不万能）：

```bash
python scripts/lipsync_align.py      # 量每段的嘴-音偏移 → gen/align.json
python build_media.py --full         # 装配时按偏移平移
```

它能把「某段整体偏 1/3 秒」这种情况拉回来，但**修不了同一段内部的逐渐走松**——
后者只能靠缩短露脸时长解决。

## 口型本地修复（**有条件**：先用 sync_pic 确认，再决定修不修）

> ⚠️ **不要盲修。** 2026-10 那次就是没先看图、只信自动打分，结果把本来是对的画面整体推歪，
> 越修越不对。现在这条的启用条件：
> 1. 先用 `scripts/sync_pic.py` 看「嘴部帧条 + 音频波形」，确认**确实存在系统性偏移**
> 2. 偏移 ≤3 帧用 `gen/nudge.json` 定点平移，别整段重切
> 3. 偏移大 / 连带身体也不对 → 那一段**重出**，不是修
>
> 详细判读方式见上面「口型验收与修正规范」。


不用下模型、不用缩短露脸：`scripts/lipsync_repair.py` 把画面按测出来的偏移曲线重新对齐。

```bash
# 1) 修复所有片段（输出 gen/fixed/，同时写 gen/repair.json）
& "E:\AI\envs\voxcpm\Scripts\python.exe" scripts\lipsync_repair.py --dir gen --out gen/fixed
# 2) 正常装配（build_media 会自动优先用 gen/fixed/，且不再叠加 align.json 的偏移）
python scripts/build_media.py --full
```

原理：出画的毛病是**时间轴错位**（每段有 -333~+375ms 的固定偏移，段内还会慢慢松），
不是嘴型画错。所以按 0.5 秒一段测出「嘴-音」局部偏移，再从源片段 t+lag 处取画面重拼，
长度不变、内容对齐。纯 ffmpeg，17 段约 4 分钟。

实测（同一条 133 秒片子，17 段）：

| | 修复前 | 修复后 |
|---|---|---|
| 每段全局偏移 \|lag\| 均值 | 3.12 帧（±130ms） | **0.53 帧（±22ms）** |
| 归零的段 | — | 16 / 17 |

注意两点：
- 修复后**不要**再叠 `gen/align.json` 的整段偏移（会双重校正），build_media 已自动处理
- 人眼容差大约 ±80–100ms，修到 ±22ms 就基本看不出来了；剩下那 1 段（曲线跨度大）会差一点

短窗（2~6 秒）上的相关测量噪声很大，验收要看**整段**的口径，别拿 2 秒窗的相关系数下结论。

## 图文填充模式（推荐：露脸短 + 中间有内容）

中间不露脸不等于中间是空底版。每一拍都要有画面，做法是给**每一段**生成一张 1080×1920 版式卡：

```bash
python make_cards.py          # 项目里带 5 种版式轮换的卡片生成器 → cards/<id>.png
HK_HOST_INTRO=12 HK_HOST_OUTRO=9 build_media.py --full --no-asr
```

- 版式用到 5 种轮换：`hero`（大字）/ `number`（大数字）/ `quote`（引语+署名）/ `list`（要点）/ `compare`（两栏对照）
- **卡片里不要再画页眉**：标题胶囊和章节条是 Remotion 那层的，卡片再画一套会叠在一起打架
- 叠层卡片（edit.json 的 cards）只留"补刀"的印章，否则和版式卡内容重复
- 结束后 Remotion 渲染，动效（章节条滚动、关键词放大、逐字字幕、印章弹入）都在这一层

这一档是现在的主力：露脸只占头尾十几秒（口型最稳），中间靠图文撑,
信息密度和观感都不输纯口播。

## 交给 koubo-video 做中期（分工）

长片子更好的分工：**数字人管头尾，中间交给 koubo 的 11 种 beat 包装**（clip / web / img / bars /
table / check / rank / stat / paper / chat / beforeafter）。

```bash
python scripts/make_host_wrap.py --project <本工程> --koubo <koubo 工程> --intro 12 --outro 9
```

产出的东西：
- `<koubo>/public/host/{intro,outro}.mp4`（1080×1920，口型已对齐）
- `<koubo>/public/narration.wav`（同一条旁白，所以两边天然同步）
- `<koubo>/public/episode.json`（分段表：起止 + 台词，给 beat 排布用）
- 终端直接打印 `RAW` / `TEXT` 两行，粘进 koubo 的 `Weekly.tsx` 即可

前提：本工程要先用 `--full` 出过 `public/main.mp4`（全屏数字人），并且过了 `lipsync_repair.py`。
