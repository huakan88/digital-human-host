# 竖版口播稿 v2 · 一天一个 GitHub · hypit

> 系列定位：每天拆一个有意思的 GitHub——先开场亮点，再教怎么用。  
> 本集项目：hypit-ai/hypit  
> 成片意向：竖版 9:16 · Vivi 定妆真全屏开场/收束 · 正文左下 pip · 中段 **真视频 FullBleed**（官方 clone 对比 / SVML·安装界面）· 禁 Ken Burns · 禁外部视频生成 API  
> **状态：v2 等侃华过眼，未配音未渲染**  
> 星数核验：GitHub API **27113**（2026-10-31 15:12:31 America/Adak · HDT；口播仍说「两万七千多星」）  
> v1→v2 硬改：中段必须播真实 demo mp4；口播「先看结果」再讲成本；标明「官方示例」

---

## 角标 / 系列名
- channelLabel：**AI 速递 · 一天一个 GitHub**
- 片头小字：今日项目 · hypit
- 禁：「花花聊科学 / 讲科学」及旧频道品牌字

---

## 口播正文（约 75–95 秒 · 可微调）

今天继续「一天一个 GitHub」。

打开仓库 hypit-ai 的 hypit——两万七千多星，给 Claude Code、Codex 这类 Agent，装一套做视频的语言和系统。

先看结果。这是官方示例：足球 Tier List「GOAT DEBATE」——同一套结构，三条 clone 变体，换主持、换排名，都能再出一条。

官方写总成本大约一块一毛五美金——约一点一五美元。播客「DAILY CREATINE」、街头采访「NICE RIDE」，README 里也都有官方示例成片。

它不是「丢提示词就出片」的黑盒。它把画面、字幕、B-roll、特效锚定在「词」上，而不是死盯第几秒。你可以丢参考片复刻成完整 workflow；也可以从模板起步，或直接描述让 Agent 从零写。生成模型可选——字幕、动效、代码渲，不调生成接口也能成片。

怎么用？三步就够。

第一步，跑 npx skills add hypit-ai/hypit -g，把 Skill 装进 Coding Agent。

第二步，丢参考片或说清需求——比如「按这条排名片的结构，换成我的产品」。左侧 SVML 源文件，右侧实时预览，就是官方示例里的 Studio 观感。

第三步，让 Agent 对齐、组素材、交出可再跑的工程；改一句台词，时间轴跟着词重排。

社区也有人做过：书单带货、产品广告换角色换场景——hypit.io/examples 能点开真片。不是空口「你可以试试」，是别人已经交过卷。

仓库 github.com/hypit-ai/hypit，落地页 hypit.ai。想看 Agent 怎么按「词」剪片，去 Star 一份自己玩。

明天同一个点，再拆下一个有意思的 GitHub。你想看哪一类，评论区丢给我。

---

## 分镜 beat（给制作 · 秒数为估，配音后重算）

| Beat | 口播锚点 | 布局 (handraw v4) | 画面（**静镜播放** · ken=false · **禁 Ken Burns**） | 素材文件 |
|------|----------|-------------------|------------------------------------------------------|----------|
| B0 | 今天继续「一天一个 GitHub」 | **真全屏** dh | 定妆 host_look；角标 channelLabel | host_look（成片再备） |
| B1 | hypit · 两万七千多星 · Agent 语言/系统 | 左下 pip + 证据卡 | 仓库页静帧 / NumberCard 27113 | GitHub 现网截帧 |
| **B2** | **先看结果 · 官方示例 GOAT DEBATE 三 clone** | **FullBleed**（**broll-mid** · 真视频） | **官方示例** mp4 静镜连播或三格快切：clone-a→b→c（可先闪 1–2s ref） | `assets/demo/goat-clone-a.mp4` 等 |
| **B3** | **成本 ~$1.15 / 一块一毛五** · 另有播客/街头官方示例 | FullBleed 续 / 叠字卡 | 成本角标叠在 demo 上；可选短切 podcast / street 官方示例 | goat + 可选 podcast/street |
| B4 | 不是黑盒 / 是词锚定 | 左下 pip | 文案卡「词 ≠ 秒」；落地页句 | hypit.ai 截帧 |
| B5 | 参考片/模板/描述 · 模型可选 | pip | 概念卡 | — |
| **B6** | 第一步装 Skill | **FullBleed**（**broll-mid** · 真界面） | 终端 `npx skills add hypit-ai/hypit -g` 真命令屏 | 终端录屏/静帧（成片抓；URL 见 assets） |
| **B7** | 第二步丢参考 · SVML/Studio 观感 | **FullBleed**（**broll-mid** · 真界面动图） | **官方** SVML 左源右预览 gif **静镜播完**（禁 Ken Burns） | `assets/demo/svml-preview.gif` |
| B8 | 第三步可再跑 · 改词重排 | 左下 pip | workflow 概念卡（勿假造 UI 数据） | — |
| **B9** | 社区书单 / 产品复刻（可选一句） | **FullBleed** 或画中画短切 | 社区真片：书单带货 / 产品广告变体；字幕标作者与链接 | `assets/demo/community/*.mp4` |
| B10 | CTA：github + hypit.ai | **真全屏** dh | 链接轻叠 | — |
| B11 | 明天再拆 · 评论区 | **真全屏** dh | 系列预告 | — |

### FullBleed 硬要求（侃华）
1. **至少两处真片/真界面**：① **B2** 官方 clone 对比 mp4；② **B6 或 B7** 安装命令或 Studio/SVML 真界面（本稿两处都写，成片至少落地两处）。
2. B2/B3/B7/B9：**播放真实文件**，禁止只靠文字卡说「有 demo」。
3. 口播凡出官方片，叠字或口播标明 **「官方示例」**；社区片标明作者与 hypit.io/examples 链。

---

## 硬规则备忘
- 星数口播用「**两万七千多星**」（现网 27113 @ 15:12:31 HDT；勿编造）
- 示例成本只引用 README「大约一块一毛五 / 约 $1.15」——勿改价
- Demo 版权：官方 README user-attachments = 官方示例·证据镜；社区 = 作者署名 + 案例页链接
- 禁「花花」；channelLabel 固定
- 竖版中段真视频 FullBleed；静镜底板；**本集停在交稿 v2**
