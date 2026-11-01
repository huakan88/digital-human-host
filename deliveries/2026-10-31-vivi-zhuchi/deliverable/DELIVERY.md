# DELIVERY · vivi-zhuchi 竖版 · 选题 hypit（一天一个 GitHub）· 终稿（H3 真对口）

写于：2026-10-31 16:19 America/Adak (HDT)

## 状态：**终稿已交**

## Gofile
- **主链**：https://gofile.io/d/su4w6dwL
- **备链**：https://gofile.io/d/w9Be6rc3

## 本地成片
| 项 | 值 |
|----|----|
| 工程 | `/workspace/hypit-vertical-2026-10-31/` |
| 渲出原稿 | `/workspace/hypit-vertical-2026-10-31/out/hypit-vertical.mp4` |
| **主交付（loudnorm）** | `/workspace/hypit-vertical-2026-10-31/out/hypit-vertical.norm.mp4` |
| **仓库成片** | `deliveries/2026-10-31-vivi-zhuchi/deliverable/vivi-zhuchi-vertical.mp4` |
| 时长 | **93.50s**（约 **1:33.5**；timeline 93.411s） |
| 分辨率 | **1080×1920** · **30fps** · h264 + aac |
| 响度（norm） | **−16.1 LUFS** · Peak **−2.4 dBFS**（目标 −16 / ≤−2） |
| channelLabel | `AI 速递 · 一天一个 GitHub`（无「花花」） |
| 备注 | **H3 真对口 · hide 段静帧** |

## 数字人
- 引擎：本机 TX-HK MiniMax H3（vivi 定妆）+ lipsync_repair；nudge s2=-4 s5=-9（未再改音频偏移）
- **真对口已用**：s1, s2, s5, s6, s7, s10, s12, s13（MB 级 mp4）
- **hide 静帧占位**（画面不看 dh）：s3, s4, s8, s9, s11
- 详见 `H3_DONE.md` / `sync_report.txt`

## 布局自检
| beat | 期望 | QA |
|------|------|-----|
| s1 开场 | fullscreen 真对口 | `qa/final/f_0.5s_s1_open_fullscreen.jpg` |
| s2/s5 正文 | pip 真对口 | `f_5.5s_s2_pip_dh.jpg` / `f_30s_s5_pip_motion.jpg` |
| s3 GOAT | fullbleed 静镜 | `f_12s_s3_goat_fullbleed.jpg` |
| s4 成本 | fullbleed + 「约 $1.15」 | `f_20.5s_s4_cost_fullbleed.jpg` |
| s9 SVML | fullbleed gif 静镜 | `f_56s_s9_svml_fullbleed.jpg` |
| s11 社区 | fullbleed | `f_72s_s11_community_fullbleed.jpg` |
| s12/s13 收束 | fullscreen 真对口 | `f_82s_s12_end_fullscreen.jpg` / `f_90.5s_s13_end_fullscreen.jpg` |
| pip 真动 | s6 三连帧 | `motion_s6_36.0s.jpg` … `36.8s` |

## Remotion
```bash
cd remotion && npx remotion render src/index.ts Vertical ../out/hypit-vertical.mp4 --codec=h264 --concurrency=2
# → 2803/2803 Encoded · exit 0 · ~40.9 MB
```
loudnorm：`scripts/loudness_check.sh out/hypit-vertical.mp4 fix` → `out/hypit-vertical.norm.mp4`

## 禁项核对
- 外部视频生成 API / Grok i2v / token01 / MiniMax 云端 / Ref2VA：**未用**
- 「花花聊科学 / 讲科学」上屏：**无**（channelLabel 固定）
- Ken Burns 底板：**关**（仅 DH 层微动）

## 工程探针
- `out/loudness.txt` · `out/probe-norm.json` · `out/gofile1.txt` · `out/gofile2.txt` · `out/render.log`
