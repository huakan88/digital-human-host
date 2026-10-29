---
name: vivi-zhuchi
description: vivi主持 —— 用「白背心数字人」形象 + 豆包 Vivi 2.0 声音做数字人口播视频。数字人先全屏开场、再缩成左下角约十分之一大小的圆形小窗继续主持；出画走本机 MiniMax H3，配音走豆包 Vivi，全流程本地。触发：vivi主持、用 vivi 做一期、白背心数字人讲这段、用豆包 vivi 的声音做数字人、女数字人口播。不用于：自己的克隆音色（用 hk主持）、真人出镜、纯横版无数字人（用 koubo-video）。
---

# vivi主持

「白背心数字人」主��的口播视频流水线。形象取自 `digital-human-koubo` 上游项目自带的
**白背心数字人**定妆照（`assets/avatar_ref.jpg`），声音用**豆包 Vivi 2.0**
（`zh_female_vv_uranus_bigtts`），出画走本机 MiniMax H3。

和 `hk主持` 同一套引擎，只换「主持预设」：形象、声音、素材、文案。

## 成品长什么样

- **开场**：白背心数字人**全屏**，手臂入画、有手部动作，字幕逐字跳动
- **正文**：数字人**缩到左下角圆形小窗**（直径 200px，约页面十分之一），白边，不挡字幕
- **包装**：顶栏胶囊标题、章节目录条、关键词变色放大、结尾号召、逐字卡拉OK字幕
- **角标**：左上角常驻「内容由 AI 数字人演绎」

## 主持预设

| 项 | 值 |
|---|---|
| 形象 | 年轻东亚女性，黑色长发带脸侧碎发，**白色罗纹背心**，手机自拍构图，约 165cm |
| 定妆照 | `assets/host_look.jpg`（来自上游 `digital-human-koubo` 的 `avatar_ref.jpg`） |
| 声音 | 豆包 **Vivi 2.0** `zh_female_vv_uranus_bigtts`（`seed-tts-2.0` 资源） |
| 语速 | `doubao_rate` 默认 20（koubo-video 横版实测约 6.5 字/秒） |
| 人物设定全文 | `persona/persona.json` |

**换声音**：改 `references/local-backend.json` 的 `doubao_speaker`
（备选 `zh_female_qingchezizi_uranus_bigtts` 清澈梓梓、`zh_female_yue_uranus_bigtts` 等），
不用改代码。

**换形象**：把新正脸照放成 `assets/host_look.jpg`，改 `persona/persona.json` 的 `look` 与 `prompt_template`。

**换成本机自己的克隆音色**：把 `references/local-backend.json` 的 `tts_backend` 改成 `voxcpm`（用 `hk主持` 那套），
或者直接用 `hk-zhuchi` 这个技能。

详细的「怎么做一期口播」见 `references/how-to.md`（三样东西 + 五步 + 主画面三种做法 + 加速表）。

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

## 工作流

```bash
cd <工程目录>
# 0) 环境自检
powershell -NoProfile -ExecutionPolicy Bypass -File <skill>\scripts\doctor.ps1
# 1) 写稿 script.json（每句 ≤ 10 秒 ≈ ≤53 字）
# 2) 出画（Vivi 配音 + 本机 H3）
python <skill>\scripts\make_tasks.py
python <skill>\scripts\backend.py quote tasks.json     # 先报价
python <skill>\scripts\backend.py run   tasks.json     # → gen/renoise-<id>.mp4 + ids.json
# 3) 组装素材
python <skill>\scripts\build_media.py                 # → public/{main,pip,voice}.* + cut/ + tl.json
# 4) 花字配置 edit/src/edit.json
# 5) 校验 + 渲染
python <skill>\scripts\check_edit.py edit/src
bash <skill>\scripts/render.sh edit 成片.mp4
```

**口型铁律**（写错就前功尽弃）：
- 提示词必须用 `<Picture 1>` 绑定参考图、`<Audio 1>` 绑定配音
- **台词不要写进提示词**（台词由 `<Audio 1>` 提供）
- 必须要求 "lips resting closed during pauses"、手部动作、锁五官（鼻型）
- 出画分辨率统一 **576×1024**，不要降（降了脸会崩、鼻头大、口型发糊）

## 小窗参数

```json
{ "pipVideo": "pip.mp4", "pipFrom": 6.65, "pipSize": 200, "pipMargin": 36 }
```
`pipFrom` 用时间轴算：`tl.segs[0].end`（开场大图结束的那一刻）。详见 `references/host-pip.md`。

## 和其它 skill 的关系

| | |
|---|---|
| **本 skill** | vivi主持：白背心形象 + 豆包 Vivi 声音 |
| `hk主持` | 同一套引擎，短发男生形象 + 本机克隆音色 huakan |
| `digital-human-koubo` | 上游技能（白背心数字人 / 小林说式财经），提供形象与花字组件 |
| `koubo-video` | 调研 / 素材 / 信源 / 通用方法论；豆包配音脚本在这 |

> 引擎只有一份，在 `hk-zhuchi/scripts`；本技能通过 `HK_PRESET` 指回自己的目录。
> 加第三个主持只要再开一个预设目录（persona + 配置 + 素材）。

## 目录

```
SKILL.md
persona/persona.json          形象 / 声音 / 提示词模板
assets/host_look.jpg          定妆照（白背心数字人）
references/
  local-backend.json          本机后端配置（音色、分辨率、出画参数）
  host-pip.md                 「大→小」小窗规格
  qc.md                       出片自检清单
scripts/                      薄封装（指向 hk-zhuchi 的引擎）
examples/                     样例
```
