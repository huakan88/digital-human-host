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
| 定妆照 | `assets/host_look.jpg`（**三代脸锁见 `assets/ASSETS-LOCK.json`**；与花花主持同源） |
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

## 定妆资产（锁定 · 2026-11-08）

**别手工覆盖 `assets/host_look.jpg`**，一切走 `assets/ASSETS-LOCK.json`（人读版 `assets/资产锁定.md`）：

```bash
python scripts/set_face_lock.py --check    # 校验现场图与 default 是否一致
python scripts/set_face_lock.py            # 列出三代锁
python scripts/set_face_lock.py locked     # 切到 GitHub HEAD 权威锁 67c56496
python scripts/set_face_lock.py in_use      # 切回旧锁 44385332
```

| 锁 | md5 | 尺寸 | 说明 |
|---|---|---|---|
| `locked` | `67c56496…` | 864×1152 | **GitHub HEAD 权威**（`huahua-zhuchi-skill` 11-04 晚批重锁，短款背心、领口更低） |
| `in_use` | `44385332…` | 864×1152 | 11-04 早批 preferred（花花仓已归档；留作回滚） |
| `canonical` | `4ac65eac…` | 720×1280 | 历史脸锁（自拍构图、手臂入画） |

- **多视图**：`assets/looks/look-01-white-tank/7view-sheet.jpg`（七视新批，来自花花仓 HEAD）
- **换装**：花花的 8 套定妆在 `huahua-zhuchi-skill/assets/looks/<look>/host_look.jpg`，直接当参考图用。
  本机 `assets/host_look_car_icd.jpg` 就是借它的 `look-04-blazer`（md5 一致）。
  **别用文字描述换装** —— 文字换装会改脸，这是花花系列反复踩过的坑。
- 切换脚本先校验源文件 md5 再动手，换下来的图自动进 `assets/_archive/`，不删文件、可回滚。
- 硬锁：同一张脸（禁换脸另造）、露胸口必留左胸小痣（观众右）、头大小与胸量对齐 preferred、七视下装按 look 走。

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

### 「嘴部静止」这个失败模式（2026-10-30 补充）

自动相关性低（<0.4）时**不要**把它当成"偏移多少帧"，它多半是这一条素材
**嘴根本没在动** —— 嘴一直是半张状态，和音频没有任何关系。平移救不了，只能重出。

**判定方法（唯一可信）**：拉 72 帧（≈2.4 秒）的长帧条，看嘴形有没有变化。

```bash
python scripts/lipsync_long.py <成片或片段> <起始秒> 72      # 默认嘴框就是横版唇部
# 输出：最佳滞后 ±N 帧 + corr + 一张 72 格的长帧条
```

- **72 帧里嘴形几乎不变** → 这条素材废了，重出（换种子），别调时间轴
- 嘴形在变、但整体错开 → 才用 `gen/nudge.json` 定点平移
- `corr < 0.4` 时**不要采信那个 lag 数字**：实测同一段能给出 ±500ms 且方向相反

**重出的具体做法**（一次试两个种子，挑好的）：

```bash
for seed in 1201 9931; do
  HK_SEED=$seed python scripts/backend.py run tasks.json --backend local --force --only s7
  cp gen/renoise-s7.mp4 gen/s7_seed$seed.mp4
done
# 然后每条都拉长帧条看，挑嘴形变化最明显的那个
```

**为什么会随机出现**：口型一致性对种子敏感。同一句台词、同一张定妆照，
有的种子嘴跟得很紧，有的种子嘴几乎不动。这不是参数没调好，是抽样问题。

**验收顺序（更新）**：
1. 拉长帧条看**嘴形有没有变化**（这是第一道门，不过就重出）
2. 过了再量滞后，`|lag| ≤ 2 帧` 才放行
3. 只有 1~3 帧的小偏差才用 nudge 平移

### 定不了的时候：A/B/C 人眼定标（2026-10-30 补充）

自动相关性在 ±100ms 内**不可靠**（实测同一段给出 −458ms 和 +458ms，方向相反）。
当长帧条看不出明显错位、但听感/观感就是不对时，别再纠结数字，让眼睛定标：

```bash
python scripts/ab_offsets.py <片段> <配音.wav> AB_对比.mp4 6
# 生成三段同一句：A 画面往前 0.2 秒 / B 原始 / C 画面往后 0.2 秒
```
放到最大看，只盯**嘴和音的先后**。选定哪个，就用 `gen/nudge.json` 按段调：

```json
{"s7": -6}     // 该段画面提前 6 帧；正数=画面往后
```

**这一招的价值**：把「我测不准」变成「用户能判断」，一次就问对，
比反复重出画省得多（每段重出约 4 分钟，改偏移只要重新渲染）。

**优先级顺序（最终版）**：
1. 拉 72 帧长帧条 → 嘴形几乎不变 → **重出**（换种子）
2. A/B/C 对比 → 人眼选偏移 → `nudge.json` 定点平移
3. 还不对 → 该段改成版式卡，不露脸
4. **永远不要**拿 `corr<0.4` 的 lag 数字直接去批量平移

### 出画还有个「构图漂移」要查（2026-10-30 补）

H3 偶尔会在生成过程中**把镜头怼到脸上**——开头还是正常头肩中景，两秒后只剩半张脸，
看起来像"半个截图"。这不属于口型问题，但一样废片段。

**验收时除了看嘴，还要看构图**：抽片段的首帧、中间、末帧三张，
如果人物大小明显变化（尤其突然拉近到只剩五官），**换种子重出**，
挑一个全程稳定的（实测换两次种子就能拿到稳定的）。

```bash
for t in 0.3 1.6 3.2 4.6; do ffmpeg -v error -y -ss $t -i clip.mp4 -frames:v 1 chk_$t.png; done
# 拼成一张对比图，人物大小应当基本一致
```

### nudge 的符号别再搞反（2026-10-30 踩坑）

`gen/nudge.json` 的值会进到 `seg_clip` 的 `-ss (off + lag)`：

- **正数 = 画面提前**（从片段更靠后的位置开始切，内容显得更早）
- **负数 = 画面延后**（从更靠前的位置切，内容显得更晚）

要判断该用哪个，看逐帧表（`frame_pairs.py`）：
**嘴比音频早闭嘴 → 画面要延后 → 用负数。**

这次万圣节开场：嘴在第 20 帧闭嘴、音频第 29 帧才停 → 嘴早 10 帧 → 应该
`{"s1": -10}`。我第一次写成 +10，结果更糟（嘴更早了），重渲一次才发现。

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

## 横版 16:9（**约束与竖版完全一致**）

竖版 9:16 和横版 16:9 是同一套规范，只是画幅不同。**素材优先、口型强制项、验收流程一条都不减。**

### 出画与装配（本仓库已支持 --wide）

```bash
# 1) 稿子里每段用横版分辨率（1024×576 是 32 的倍数，H3 能出）
#    script.json: "size": [1024, 576]
python scripts/make_tasks.py            # ratio 自动跟 size 走（16:9），
                                       # 提示词自动切 persona 的 prompt_template_wide

# 2) 主画面（1920×1080）
python scripts/build_media.py --full --wide

# 3) 口型验收（同竖版，嘴框按横版构图调）
python scripts/sync_pic.py <片段> <起始秒> 12 "0.30,0.30,0.70,0.55"

# 4) 切数字人窗口也用 --wide
python scripts/make_host_wrap.py --project . --koubo <横版工程> --host-segs s1,s8 --wide
```

横版提示词已经写进两个 persona（`prompt_template_wide` / `prompt_big_wide`），
要点：**中景、腰部以上、人物居中留两侧空地、头顶留白**，不要手机自拍构图。

### 中期包装换成 koubo 横版模板

```bash
cp -r <koubo-video>/templates/wide ./koubo          # 横版模板
python scripts/patch_koubo_wide_host.py ./koubo     # 接入数字人窗口层（host prop）
python scripts/make_wide_beats.py ./koubo --tabs "现象|证据|规律|结论"
cd koubo && npx remotion render src/index.ts Wide out/wide.mp4 --props='public/beats.json'
```

横版模板的卡片库很全（`components.tsx`）：`H1` / `Stat` / `BarChart` / `Checklist` /
`NumberedList` / `MediaCard`（放真实片段）/ `Timeline` / `Compare` / `QuoteCard` / `EndCard` …
`make_wide_beats.py` 已经把竖版那套 beat（stat/bars/check/rank/clip/cliptext）映射过去了；
想用别的卡片就在 `beats_wide.json` 里按段 id 直接写 `{card, props}`。

**数字人窗口**用 `beats.json` 里的 `host` 字段：
```json
"host": {"src": "main.mp4", "windows": [{"from": 0, "to": 87}]}
```
窗口内的拍会**只留字幕、卡片让位**，露出下面的数字人主画面 —— 和竖版同一个思路。

### 横竖版差异（只有这些）

| 项 | 竖版 9:16 | 横版 16:9 |
|---|---|---|
| 出画尺寸 | 576×1024（或 1080p） | 1024×576 |
| 成片尺寸 | 1080×1920 | 1920×1080 |
| 构图提示词 | 手机自拍、手臂伸向镜头 | 中景、腰以上、两侧留空、头顶留白 |
| 包装模板 | `koubo-video/remotion-template` | `koubo-video/templates/wide` |
| beat 定义 | `patch_koubo_episode.py` 写进 Weekly.tsx | `beats_wide.json` + `make_wide_beats.py` |
| 露脸位置 | 可全屏，也可缩成左下角圆形小窗 | 一般全屏出镜，卡片让位 |

**素材密度、单镜头一次生成、口型验收、署名——全部照旧。**

### 横版实测结论（2026-10-29 首次跑通）

- **出画**：`size: [1024, 576]` → H3 正常出片，横构图、白底、手部动作都在画面里
- **成片**：`build_media.py --full --wide` → 1920×1080，帧栅格与竖版一致
- **嘴框（横版）**：`"0.34,0.28,0.66,0.58"`（半身、居中构图）；竖版那个 0.28/0.36/0.72/0.56 不适用
- **底版**：`python make_backdrop.py "" 1920 1080`（现在会写进 `HK_PROJECT` 目录）

**定妆照（重要）**：用**原始照片**当出画基准，比用二次生成的定妆照更像本人。
```bash
HK_LOOK=assets/host_me_photo.jpg python make_tasks.py
```
实测：拿原图当基准，脸型/鼻型/发际线都对得上；换成生成过的 `host_me_look` 会脸变圆、鼻子变大。

**本机 TTS 卡死时的兜底**：VoxCPM 服务偶发「加载完 9GB 但不响应」，`make_voice` 会一直挂着。
这时先用豆包云端把音出来，别等：
```bash
python voice_doubao.py            # 直接调 backend.tts_doubao，几秒出音
```
（豆包约 ¥0.59/2 分钟，出片后再换回克隆音色也可以）

**内存硬约束**：ComfyUI 开着 H3 权重时占 ~20GB，31GB 内存会只剩 0.9GB，
VoxCPM 直接换页卡死。**先出音再出画**，或者先 `POST http://127.0.0.1:8188/free`
（`{"unload_models":true,"free_memory":true}`）把 H3 权重卸掉。

### 横版完整流程（2026-10-29 实跑：万圣节这期，77 秒成片）

按这个顺序走，一条命令都不多余：

```bash
# 1) 稿子：每段 size 写 [1024, 576]，一段一句，≤45 字
python <skill>/scripts/make_tasks.py            # ratio 自动 16:9，提示词自动切 *_wide

# 2) 配音（豆包 Vivi，20 段约 1 分钟）
python voice_doubao.py

# 3) 出画：露脸段一段一次生成，用 gen/host_segs.json 指定
python <skill>/scripts/backend.py run tasks.json --backend local --only s1,s5,s16,s20

# 4) 主画面（1920×1080）+ 底版
python <skill>/scripts/make_backdrop.py "" 1920 1080
python <skill>/scripts/build_media.py --full --wide --no-asr

# 5) 横版包装工程
cp -r <koubo-video>/templates/wide ./koubo
python <skill>/scripts/patch_koubo_wide_host.py     ./koubo   # 数字人窗口层
python <skill>/scripts/patch_koubo_wide_mediatext.py ./koubo  # MediaText：素材铺底 + 大字
python <skill>/scripts/make_host_wrap.py --project . --koubo ./koubo --host-segs s1,s5,s16,s20 --wide
python <skill>/scripts/make_wide_beats.py ./koubo --tabs "现象|起源|结论"

# 6) 渲染
cd koubo && npx remotion render src/index.ts Wide out/wide.mp4 --props=public/beats.json
```

**两个新东西（这期加的）**

1. **`MediaText` 卡**（`patch_koubo_wide_mediatext.py`）
   横版模板原来只有白底排版卡，没有「文字压素材」。这个卡 = 素材铺满 + 压暗 + 大字居中，
   等价于竖版的 `cliptext`。参数：`{src, video?, from?, title, sub?, dim?}`。

2. **`make_wide_beats.py` 现在读 `public/timeline.json`**
   以前它自己按 `sec + 0.25` 逐段重算时长，结果数字人窗口和主画面对不上
   （实测 0-4.47s vs 主画面 0-4.23s，最后一段甚至超到 81.7s）。
   **帧栅格是唯一权威**，所有 beat 的 `from/dur` 都必须从 timeline.json 取。

### 拿「别人的科普片」当素材库（这期最省事的一招）

找到一条画面配得好的科普片（例：B站 `BV17e411R7nc`「5分钟介绍万圣节的来历」），
**按时间轴抽帧拆成十几个独立画面**，一格讲一个点，比自己找图快得多：

```bash
for t in 0 20 45 70 95 120 145 170 195 220 245 270 295; do
  ffmpeg -v error -y -ss $t -i ref.mp4 -frames:v 1 -vf "scale=300:-2" ex_$t.png
done
# 拼成对照图挑画面，再把选中的图复制进 koubo/public/clips/
```
署名写 `Bilibili · 作品名 · BV号`。**抽帧看清内容再配文案**，别凭时间猜。

### 横版两个必踩的 UI 坑（2026-10-30 补）

**1. 章节条被素材卡盖住**
`Wide.tsx` 里 `TabBar` 原本渲染在 `Card` 之前，而 `MediaText` 是铺满画面的
`AbsoluteFill`，章节条就被压在底下了。必须把 TabBar 放到 Card **之后**：
```tsx
<K.Page ...><Card {...b.props}/>{tabs&&b.tab!==undefined&&<K.TabBar tabs={tabs} active={b.tab}/>}</K.Page>
```
（`patch_koubo_wide_tabbar.py`）

**2. 章节条的默认配色在素材上不可读**
模板默认是浅灰胶囊（#F2F2F2）+ 灰字，放在深色战场画面上几乎看不见。
改成半透明深底 + 白字、当前项反白（`fix_tabbar_style.py`）。

**3. 静态图连播会像 PPT**
`MediaText` 原来是静止图 + 静止大字。加了极慢推近（1.0→1.06）+ 前 12 帧文字淡入上移
（`patch_koubo_wide_motion.py`）。注意：加了推镜后每帧都在变，同样 CRF 下体积会翻倍，
交付时把 CRF 调到 24 左右（78 秒 / 1080p ≈ 16MB）。

### groups.json 会被「--only 单段」覆盖（2026-10-30 补）

`backend.py run --only s3` 只跑一段时，它写出的 `groups.json` **只有这一段**。
之后跑 `build_media.py`，其他段的 `seg_src` 就找不到，**静默退回底版**——
表现是「某几个数字人窗口里没有人，只有背景」，非常难查。

现在 `build_media.py` 会在读完 groups.json 后再**扫一遍 `gen/renoise-<id>.mp4`**，
文件在就算有出画，并打印「groups.json 补了 N 段」。

**排查口诀**：窗口里没数字人 → 先看 `main.mp4` 对应时间点有没有人 →
没有人就查 `gen/renoise-<id>.mp4` 在不在、`groups.json` 里有没有这一段。

**另一个教训**：改完稿子（旁白时长变了）要重跑 `build_media`，
不然帧栅格还是旧的；但重跑前先确认 `gen/` 里的片段是给**新稿**出的。

### 境外站点全线不通时，用 gh-proxy 取 GitHub（2026-10-30 实测）

本机 `github.com` / `api.github.com` / `raw.githubusercontent.com` / `video.twimg.com`
**全部 000**（连本地 Clash 也不通），但这两个 GitHub 代理**可达**：

```
https://gh-proxy.com/https://api.github.com/repos/<owner>/<repo>       # 元数据
https://gh-proxy.com/https://github.com/<owner>/<repo>/archive/refs/heads/<branch>.zip
```

实测用它把 `tsonglew/chess-cn`（45.8MB）整包拉下来了，里面的 `media/`
**自带项目官方演示视频**（`demo.mp4` 竖屏实机录屏、`general-cinematic.mp4` 横屏特写）——
比任何 AI 概念图都强，直接进片。

**两条经验**：
1. 开源项目的 `media/` 目录常放官方 demo 视频，优先用它们，别自己生成
2. `api.github.com` 的返回里能读到默认分支（不一定叫 main）、许可证、homepage（在线 demo 地址）

**竖屏素材放进横版**：`objectFit: contain` 会变成中间一条窄带，很难看。
正确做法是用 ffmpeg 裁成 16:9 再 cover：
```bash
ffmpeg -i demo.mp4 -vf "crop=592:333:0:260,scale=1280:720:flags=lanczos" -an out.mp4
```
`y=260`、`333` 高是按该片实测选的（避开顶部 UI 和底部提示条）。

## 工作流

```bash
cd <工程目录>
# 0) 环境自检
powershell -NoProfile -ExecutionPolicy Bypass -File <skill>\scripts\doctor.ps1
# 1) 写稿 script.json（每句 ≤ 10 秒 ≈ ≤53 字）
# 2) 出画（Vivi 配音 + 本机 H3）
python <skill>\scripts\make_tasks.py
python <skill>\scripts\backend.py quote tasks.json     # 先报价
python <skill>\scripts\backend.py run   tasks.json     # 默认本地 H3 → gen/renoise-<id>.mp4 + ids.json
#    ⚠ 出画前先问用户选通道（默认本地，不要替他选贵的）：
#      local = 本机 H3（¥0，慢，主力）
# 3) 组装素材
python <skill>\scripts\build_media.py                 # → public/{main,pip,voice}.* + cut/ + tl.json
# 4) 花字配置 edit/src/edit.json
# 5) 校验 + 渲染
python <skill>\scripts\check_edit.py edit/src
bash <skill>\scripts/render.sh edit 成片.mp4
```

## 交付档默认（2026-11-09 更新：**先渲染 → 再超分**）

> **标准工序变了。** 以前硬顶 704×1280 求原生清晰度，但 8GB 卡在 7 秒以上的片段会 OOM，
> 而且 704×1280 的原生片码率也只有 ~1.8–2.7 Mbps。现在改成：
> **出画统一 576×1024，再用 Real-ESRGAN 超分到 1152×2048**，质量更稳、也不怕 OOM。

| 项 | 交付默认 | 只许用于草稿 |
|---|---|---|
| **出画分辨率** | **576×1024**（全部段统一，不再顶 704×1280） | — |
| **超分** | **Real-ESRGAN `x4plus` + `-t 0` → 1152×2048**（见下一节） | — |
| 步数 / 模式 | **`mode=standard`（不挂 turbo LoRA）**、`h3_steps` **≥8** | turbo 4 步 |
| 成片 | 1080×1920 / 30fps / **CBR ≥4 Mbps**（本机实测 6.0 Mbps） | ABR/CRF（静态图形下实测只吃到 3.4 Mbps） |

为什么不再用 704×1280 出画：
- 576×1024 + standard + steps≥8 → 超分后实测（2026-11-09 Anatomy 这期）睫毛、发丝、皮肤纹理
  都不比 704×1280 原生差，肉眼 1:1 抽帧确认过（`dhk-anatomy/qc/esr_pipeline.png`）。
- 704×1280 在 7 秒以上片段会 **torch OOM**（8GB 卡实测），576×1024 没有这个问题。
- 576×1024 每步比 704×1280 快约 4 成，总排期更短。

## 超分工序（**交付必做，不是可选**）

出画完 → **必须超分**，再进 Remotion。三段/多段露脸片一律照此执行：

```bash
# 1) 抽帧
ffmpeg -v error -y -i gen/renoise-s1.mp4 -vsync 0 -frame_pts 1 tmp_up/s1/%05d.png

# 2) 超分（x4plus + tile=0！见下方两个坑）
realesrgan-ncnn-vulkan.exe -i tmp_up/s1/%05d.png -o tmp_up/s1/up/%05d.png \
  -n realesrgan-x4plus -s 4 -t 0 -f png

# 3) 下采样到成片尺寸 + 极轻锐化 + 带音轨重编码
ffmpeg -v error -y -framerate 24 -i tmp_up/s1/up/%05d.png -i gen/renoise-s1.mp4 \
  -map 0:v:0 -map 1:a:0 \
  -vf "scale=1080:1920:flags=lanczos,cas=strength=0.35,format=yuv420p" \
  -c:v libx264 -crf 16 -preset slow -c:a copy -shortest -movflags +faststart gen_up/renoise-s1.mp4
```

脚本模板：`dhk-anatomy/upscale_segments.py`（三段批量跑，可改 SEGS 列表直接用）。

### 超分的两个坑（2026-11-09 实测，踩过）

| 坑 | 症状 | 修法 |
|---|---|---|
| **默认 tile 切块** | 输出图**拼成错位碎块**（脸被切成几块拼歪） | 必须加 **`-t 0`**（不切 tile） |
| **模型选错** | `realesr-animevideov3` 用在真人脸上出**描边感、睫毛结块**（那是给二次元做的） | 只用 **`realesrgan-x4plus`** |
| **x4plus 会磨皮** | 毛孔被抹掉一档，轻微美化 → 撞「禁磨皮/禁蜡感」 | 接 **`cas=strength=0.35`** 极轻锐化找回质感；**不要上强锐化**（强了会蜡） |

### 超分后包装层不许再缩放

`gen_up/` 里的片已经是 **1080×1920**，Remotion 里 **1:1 直接铺**，不要再 `objectFit:cover` 放大——
二次缩放会糊掉刚找回来的细节。prep 脚本要能区分「有超分版」和「无超分版」，
无超分版才走放大通道并打印警告。

## 构图漂移：出画怼脸怎么办（2026-11-08 实测）

新脸锁是**近景自拍构图**，H3 照着它复刻，出来就是**怼脸大特写**
（头被裁、眯眼笑）——看着像废片。修法三件套：

1. 造一张 9:16 拉版参考图（脸锁不变，上下留白 + 肩胸入画），当 `<Picture 1>` 喂；
2. 提示词追加 FRAMING LOCK：中景腰以上、整颗头在画内、头顶留 15% 空、
   全程不推拉、表情平静睁眼不笑、嘴闭时保持闭合；
3. **换种子重出**（同段不同种子表现差异很大）。

```bash
# 9:16 拉版参考图（示例脚本见工程 dhk-sitc/assets/make_ref.py）
python -c "from PIL import Image; im=Image.open('assets/host_look.jpg').convert('RGB'); W,H=704,1280; s=W/im.width; im=im.resize((W,int(im.height*s))); bg=im.getpixel((5,5)); c=Image.new('RGB',(W,H),bg); c.paste(im,(0,170)); c.save('assets/host_look_9x16.jpg')"
```

### 口型验收：`sync_pic.py` 的嘴框要按新构图重调

新构图脸在画面上半部，嘴框不再是 `0.28,0.36,0.72,0.56`，要用
`"0.36,0.38,0.64,0.48"`（自拍/中景构图实测）。框落错会得到完全无意义的结果。
**超分后要重跑一次 `sync_pic.py`**——确认超分没把口型弄糊。
- Real-ESRGAN 本机已装在 `tools/esrgan/`（**不入 Git 仓**）；换机器时跑 `python <skill>/scripts/fetch_esrgan.py` 自动下载（直连不通会自动走 gh-proxy 镜像）。

**口型铁律**（写错就前功尽弃）：
- 提示词必须用 `<Picture 1>` 绑定参考图、`<Audio 1>` 绑定配音
- **台词不要写进提示词**（台词由 `<Audio 1>` 提供）
- 必须要求 "lips resting closed during pauses"、手部动作、锁五官（鼻型）
- 出画分辨率统一 **576×1024**，交给超分补足（不要靠降分辨率省时间，也不要顶 704 硬扛 OOM）

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

## vivi 的服装（2026-10-31 加）

- 服装表在 `persona.json` 的 `outfits`（比 hk 那套更露一点、仍是可发布的日常穿着）
- 挑衣服的逻辑、`gen/outfit.json` 固定机制、全局计数器都**在 `hk-zhuchi/SKILL.md`
  的「服装：每个话题换一套」一节**，引擎共用，照那节执行
- 口型强制流程同 `hk-zhuchi/SKILL.md` 的「口型强制流程」一节，vivi 没有例外
