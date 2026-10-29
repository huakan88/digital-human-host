#!/bin/bash
# hk主持 · 渲染 + 出片（Git Bash）
# 用法：bash render.sh <工程目录> [输出文件名]
#   例：bash render.sh edit 成片.mp4
#
# ⚠ TEMP 必须指到工程目录下面：Remotion 的合成器把中间文件写在 %TEMP%，
#   本机系统 TEMP 对子进程拒绝写入，会报 "Error: write EOF"（看着像版本/显卡问题，其实是权限）。
set -e
DST="${1:-edit}"
NAME="${2:-成片.mp4}"
NODE_DIR="${DHK_NODE_DIR:-/e/AI/node24}"
export PATH="$PATH:$NODE_DIR"

cd "$DST" || { echo "没有工程目录 $DST"; exit 1; }
export TEMP="$(cd .. && pwd)/.tmp"
export TMP="$TEMP"
mkdir -p "$TEMP"

echo "=== render ==="
npx remotion render src/index.ts Huazi out/raw.mp4 --concurrency=3

echo "=== 成片（-16 LUFS）==="
ffmpeg -loglevel error -y -i out/raw.mp4 \
  -af loudnorm=I=-16:TP=-1.5:LRA=11 \
  -c:v libx264 -crf 20 -preset medium -pix_fmt yuv420p \
  -c:a aac -b:a 192k -movflags +faststart "$NAME"
ffprobe -v error -show_entries format=duration,size -of default=nw=1 "$NAME"
echo "✓ $DST/$NAME"
