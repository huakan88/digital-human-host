# 样例：《全世界家猫只有一个祖先》

一期完整跑通的例子，可直接照抄改。

| 项 | 值 |
|---|---|
| 选题 | 猫的起源（研究素材来自本机 E:\minimax H3\002_全世界家猫只有一个祖先_跳跳项目） |
| 稿子 | 7 句 · 74.7 秒 |
| 旁白 | 本机克隆音色 huakan（7 段逐句合成，段间 0.25 秒停顿） |
| 数字人 | 开场 576x1024 全屏；其余 6 段 384x576 → 左下角 200px 圆窗 |
| 画面 | 猫素材 16:9 → 竖版化（模糊底 + 完整画面） |
| 回听 | 98 / 88 / 94 / 96 / 98 / 80 / 85 %（ASR 同音字，非发音错误） |
| 渲染 | Remotion 4.0.534 + React 19.2.3，2278 帧，-16 LUFS |

## 改稿重跑

``bash
cd <新工程目录>
cp <skill>/examples/cat/script.json .
cp <skill>/examples/cat/edit/src/edit.json edit/src/
python <skill>/scripts/make_tasks.py
python <skill>/scripts/backend.py run tasks.json
python <skill>/scripts/build_media.py
python <skill>/scripts/check_edit.py edit/src
bash <skill>/scripts/render.sh edit 成片.mp4
``

改 script.json 的 \	\ 换台词；改 \cat\ 字段换配图；改 \edit.json\ 换花字与卡片。
