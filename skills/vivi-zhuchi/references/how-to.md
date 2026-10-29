# 用这个女性数字人做口播：三样东西 + 五步

## 三样东西

| 要素 | 在哪 | 换它做什么 |
|---|---|---|
| **形象** | `assets/host_look.jpg` | 换成你想要的女性正脸照（9:16、半身、头顶留白、手臂入画最好），再改 `persona/persona.json` 的 `look` 和外貌句 |
| **声音** | `references/local-backend.json` → `doubao_speaker` | 默认 `zh_female_vv_uranus_bigtts`（Vivi 2.0）；换 `zh_female_qingchezizi_uranus_bigtts`（清澈梓梓）等；`doubao_rate` 控语速 |
| **稿子** | 工程目录 `script.json` | 一句一段，**每段 ≤ 45 字**（约 7 秒） |

> 形象图很关键：H3 会**照抄参考图的构图**。参考图是贴脸自拍，出来就是大脸特写
> （不是不能看，但没留白、手臂进不来、手势也看不见）。
> 所以定妆照要「半身 + 头顶留白 + 手臂/手入画」——`make_look.py` 就是干这个的。

## 五步

```bash
cd <工程目录>
export HK_PROJECT=$(pwd)                    # 让引擎知道工程在哪

# 1) 出稿（自己写，或让 agent 按 ≤45 字/段拆）
#    script.json: [{"id":"s1","big":true,"size":[576,1024],"t":"第一句"}, ...]

# 2) 出画：豆包配音 + 本机 H3（最慢的一步）
python <skill>/scripts/make_tasks.py
python <skill>/scripts/backend.py quote tasks.json      # 先报价
python <skill>/scripts/backend.py run tasks.json --merge 15

# 3) 拼素材：旁白总轨 + 主画面 + 左下角小窗 + 逐字时间轴
python <skill>/scripts/build_media.py
python <scripts>/align.py script.json --out edit/src/tl.json

# 4) 写花字：edit/src/edit.json（标题、章节、关键词、卡片、结尾号召）

# 5) 渲染
python <skill>/scripts/check_edit.py edit/src
bash <skill>/scripts/render.sh edit 成片.mp4
```

## 主画面三种做法（按内容选）

1. **通用底版 + 小窗**（最省事，适合口播/评论）
   放一张 `backdrop.png` 在工程根目录，正文段自动用它当主画面，
   数字人在左下角讲，花字卡片叠在上面。
2. **证据版式**（适合科普/数据）
   在 `cards/<段id>.png` 放每段的 1080×1920 卡片（见 `hk-zhuchi/references/evidence-cards.md`）。
3. **素材**（适合有实拍/生成画面）
   在 `script.json` 里给 `cat` 字段，指向素材库的 `clip_<name>.mp4`。

优先级：`cards/<id>.png` → `script.json` 的 `card` → `backdrop.png` → 素材库。

## 出片长相

- 开场：数字人**全屏**（`"big": true`，只有第一段）
- 正文：数字人**缩到左下角**，直径 200px 圆形小窗，白边
- 字幕：逐字卡拉OK；顶栏胶囊标题；章节条；关键词放大变色
- 角标：左上角「内容由 AI 数字人演绎」

## 加速（2 分钟的片子从 50 分钟压到 ~30 分钟）

| 手段 | 省多少 | 怎么开 |
|---|---|---|
| 合并出画 | 每段省 ~100 秒固定开销 | `--merge 15`（连续短段合成 ≤15 秒的长片段） |
| 关掉 `--low-vram` | 每段 ~40 秒 | 配置里 `h3_low_vram: false`（默认已关） |
| 降步数 | 每段 ~40 秒 | 配置里 `h3_steps: 3`（4→3 肉眼看不出差别） |
| 批量 ASR | 每段 ~40 秒 | 默认已开（模型只加载一次） |
| 复用 ASR | 改卡片/字幕不重跑 | `build_media.py --no-asr` |
| 缩短稿子 | 线性 | 每减 10 秒成片 ≈ 省 3 分钟出画 |

真正的捷径是**云端 H3**（`--backend cloud-h3`，¥0.40/秒，30 秒出一段，比本机快约 10 倍），
但需要套餐支持 H3——Token Plan 免费档会返回 402 code 2068。
