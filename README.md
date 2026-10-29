# 数字人主持技能包（Digital Human Host Skills）

两个 DSH 技能，做「数字人口播 + 真实素材 + 花字包装」的竖版视频：

| 技能 | 形象 | 声音 |
|---|---|---|
| `hk-zhuchi`（hk主持） | 短发男生（用户本人形象） | 本机 VoxCPM2 克隆音色 `huakan` |
| `vivi-zhuchi`（vivi主持） | 白背心女性 | 豆包 Vivi 2.0 `zh_female_vv_uranus_bigtts` |

两者共用同一套引擎（`hk-zhuchi/scripts/`），`vivi-zhuchi` 通过 `HK_PRESET` 指回自己的
persona / 配置 / 素材，所以加第三个主持只要再开一个预设目录。

## 这套技能的核心规范（都是踩坑踩出来的）

1. **素材优先（硬指标）** —— 真实素材时长 ≥ 成片 50%，至少 8 段不同素材；
   不允许连续 2 拍以上是纯文字卡。纯 Remotion 只做数据卡 / 过渡 / 收尾。
2. **口型对齐（强制项）** —— 露脸段一段一次生成、每段 ≤6 秒；一个连续镜头只许一次生成
   （两次生成拼一起会出现景别/光线跳变）。出片前必须过 `sync_pic.py` 的嘴形+波形验收。
3. **口型验收与修正规范** —— 先用眼睛看，再用数字判。自动打分只用来抓大偏（≥150ms）。
4. **真实素材规范** —— B站（`yt-dlp`）与 Contra（Cloudinary 直链）实测可用；
   Dribbble 有 Cloudflare、X/YouTube 在本机不通。每条素材必须署名。
5. **时间轴用帧栅格** —— 千万别用配音原始时长算窗口，1/60 秒/段会累积成几百毫秒。

## 工作流

```bash
cd <工程目录>
export HK_PROJECT=$(pwd)

# 1) 稿子 script.json（一句一段，每段 ≤45 字 ≈ ≤6 秒）
# 2) 出画（配音 + 本机 MiniMax H3）
python <skill>/scripts/make_tasks.py
python <skill>/scripts/backend.py run tasks.json --merge 6 --only s1,s8,s11,s19
# 3) 拼旁白与主画面（露脸段用 gen/host_segs.json 指定）
python <skill>/scripts/build_media.py --full
# 4) 口型验收
python <skill>/scripts/sync_pic.py <片段或成片> <起始秒> 12 "0.28,0.36,0.72,0.56"
# 5) 接 koubo-video 做中期包装（真实片段 + 文字压画面）
python <skill>/scripts/make_host_wrap.py --project . --koubo <koubo工程> --host-segs s1,s8,s11,s19
python <skill>/scripts/patch_koubo_episode.py <koubo工程>
```

## 依赖

- 本机 ComfyUI + MiniMax H3（出画）、VoxCPM2（克隆音色）、豆包 TTS（云端）
- `koubo-video` 技能的 Remotion 模板（中期包装）
- `ffmpeg` / `ffprobe`、Python 3.11、Node 24

## 目录

```
skills/hk-zhuchi/     引擎 + 短发男生预设
skills/vivi-zhuchi/   白背心女性预设（共用引擎）
```
