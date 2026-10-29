# 医学科普的「证据版式」做法

严肃医疗内容不能拍脑袋，每一拍都要有真材料、每个数字都要有出处、不能夸大。
`hk主持` 的主画面用**证据版式卡**（1080×1920 PNG）承担这件事，数字人缩到左下角继续主持。

## 卡片结构（`scripts/make_cards.py` 那套）

```
眉标（40px 灰）      全球临床试验格局
大数字（190px 橙）    471
标题（62px 白）      项细胞外囊泡相关临床试验在注册（截至 2024）
要点（42px）        · I 期与 II 期合计超过六成
                    · III 期不到 5% —— 确证性试验几乎空白
—— 分隔线 ——
来源（28px 灰）      来源：公开临床试验注册统计（截至 2024 年）
```

底色 `#0E0E12`，强调色跟模板一致用橙 `#FF7A1A`（特殊数字可用紫 `#A78BFA`）。

## 硬规矩（来自 koubo-video 的医学规范）

1. **不许说「治愈」「已实现逆转」「根治」**；讲清样本量、开放标签、有无对照、主要终点、随访长短、是否获批。
2. **数字必须带出处**：论文就写「作者 · 期刊 · 年份 · Fig N」，监管就写「CDE / 中检院 / FDA · 日期」。
3. **图上的数字、旁白说的数字、屏幕上的大数字必须同源**（同一篇论文 / 同一个页面）。
4. **严肃医疗不加评论区互动 CTA**；结尾改成「行动建议」+「免责声明」。
5. **AI 生成的假报告站数据一律弃用**：同一细分出现多个互相矛盾的市场规模数字 → 全部不引用。
6. **不出现客户名/内部项目名**（公开版）。
7. 图片许可：CC BY 可裁可标、NC-ND 只能整图非商用；图注写清许可；裁切/标注过要写明。
8. **片头先交代系列与本期主题**（例如标题胶囊写「外泌体成药第一课」）。

## 流程

```bash
# 1) 稿子（每句 ≤ 10 秒 ≈ ≤53 字，因为 H3 单段上限 10 秒）
#    script.json: [{"id":"s3","card":"s3","size":[576,1024],"t":"…"}]
# 2) 出画
python scripts/make_tasks.py && python scripts/backend.py run tasks.json
# 3) 做证据版式卡（每段一张，1080x1920）
python make_cards.py            # 输出到 cards/<id>.png
# 4) 组装（build_media 会自动优先用 cards/<id>.png 作为该段主画面）
python scripts/build_media.py
# 5) 花字配置 + 渲染
python scripts/check_edit.py edit/src && bash scripts/render.sh edit 成片.mp4
```

`build_media.py` 的画面来源优先级：
1. `cards/<id>.png` —— 证据版式（本来就是 1080×1920，直接铺满）
2. `clip_<cat>.mp4` —— 素材库里的 16:9 素材（模糊底 + 完整画面竖版化）

## 本机现成的素材库

| 项目 | 路径 | 能拿什么 |
|---|---|---|
| 外泌体成药（公开科普） | `E:\Users\huaka\Documents\deepseek-harness\default-workspace\ev-ind-course-2026-10-23` | `script/口播稿_上集.md`、`script/口播稿_下集.md`、`assets/evidence/figs.json`（7 张论文图，带 PMID/PMCID/DOI/图注）、`audio/narration_final_L1.wav` |
| ED / 干细胞客户决策片 | `...\ed-ded-ind-timeline-2026-10-23` | `script/narration_v7.md`（27 拍，**含客户信息，公开版要脱敏**）、`web_ind/`（30 张论文图）、`web/`（45 张监管页/新闻截图） |
| 猫（AI 生成角色） | `E:\minimax H3\002_全世界家猫只有一个祖先_跳跳项目\video\final\clip_s*.mp4` | 12 段跳跳猫画面（自带口型与爪子动作） |

`assets/evidence/figs.json` 里每张图都有 `pmid` / `pmcid` / `doi` / `label` / `caption` / `title`，
图注可以直接从这生成，不用另查。

## 一个必须自己核的点

`figs.json` 里**没有许可字段**。引用前要自己确认那篇的许可（NC-ND 的只能整图、不许裁）。
不确定就在图注只写「作者·期刊·年份·Fig N」，不要写没核实的许可。
