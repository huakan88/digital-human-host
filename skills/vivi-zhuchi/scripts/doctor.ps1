# hk主持 · 环境自检
# 用法：powershell -NoProfile -ExecutionPolicy Bypass -File doctor.ps1
# 注意：本文件必须存成 UTF-8 with BOM，否则 Windows PowerShell 5.1 会按 GBK 读，中文全乱码。
$ErrorActionPreference = "Continue"

function Probe($block) {
    try { $v = & $block 2>$null; if ($v) { return "$v" } } catch { }
    return $null
}

$script:miss = 0
function Check($name, $block, $hint) {
    $r = Probe $block
    if ($r) { Write-Host ("  [OK]   {0}  -> {1}" -f $name, $r) -ForegroundColor Green }
    else { Write-Host ("  [缺]   {0}  -> {1}" -f $name, $hint) -ForegroundColor Yellow; $script:miss++ }
}

Write-Host ""
Write-Host "=== hk主持 环境自检 ===" -ForegroundColor Cyan
Write-Host ""

Write-Host "基础工具" -ForegroundColor Cyan
Check "ffmpeg" { (ffmpeg -version 2>&1 | Select-Object -First 1) } "winget install Gyan.FFmpeg"
Check "node"   { (node -v 2>&1) } "装 Node 24（E:\AI\node24）"
Check "python" { (python -V 2>&1) } "装 Python 3.11+"

Write-Host ""
Write-Host "本机模型" -ForegroundColor Cyan
Check "H3 权重"     { if (Test-Path 'E:\minimax H3\models\diffusion_models\minimax_h3_fl2va_pruned_int8_convrot.safetensors') { 'minimax_h3_fl2va int8' } } "见 E:\minimax H3\部署说明.md"
Check "H3 脚本"     { if (Test-Path 'E:\minimax H3\tools\h3gen.py') { 'h3gen.py' } } "缺了就重装 H3 套件"
Check "VoxCPM 模型" { if (Test-Path 'E:\AI\models\VoxCPM2\model.safetensors') { 'VoxCPM2' } } "本机 TTS 权重"
Check "Huakan 音色" { if (Test-Path 'E:\AI\voices') { 'voices/' } } "录音参考"

Write-Host ""
Write-Host "运行中的服务" -ForegroundColor Cyan
Check "TTS :8808" {
    try { (Invoke-WebRequest 'http://127.0.0.1:8808/health' -UseBasicParsing -TimeoutSec 5).Content } catch { $null }
} "没起：python E:\AI\voxcpm-tools\tts_server.py --port 8808 --preload --model E:\AI\models\VoxCPM2"
Check "ComfyUI :8188" {
    try { "v" + (Invoke-WebRequest 'http://127.0.0.1:8188/system_stats' -UseBasicParsing -TimeoutSec 5).Content.Length } catch { $null }
} "没起：E:\minimax H3\start_h3.bat（出画前必须起，h3gen 会自动拉）"

Write-Host ""
Write-Host "本 skill 自带" -ForegroundColor Cyan
$root = Split-Path $PSScriptRoot -Parent
Check "whisper-cli.exe" { if (Test-Path "$root\bin\whisper-cli.exe") { "$((Get-Item "$root\bin\whisper-cli.exe").Length) bytes" } } "编译：csc /target:exe /out:bin\whisper-cli.exe scripts\whisper-cli.cs"
Check "Remotion 模板"  { if (Test-Path "$root\templates\huazi-916\src\Huazi.tsx") { "huazi-916" } } "模板缺失"
Check "定妆照"         { if (Test-Path "$root\assets\host_me_look.jpg") { "host_me_look.jpg" } } "换人：先放 host_me_ref.jpg 再跑 make_avatar.py"
Check "七视图"         { if (Test-Path "$root\assets\host_me_7view.jpg") { "host_me_7view.jpg" } } "换人：跑 make_avatar.py"

Write-Host ""
Write-Host "(Remotion 工程依赖在第一次建工程时装：npm install --registry=https://registry.npmjs.org --proxy=null --https-proxy=null)" -ForegroundColor DarkGray
Write-Host ""
if ($script:miss -eq 0) { Write-Host "环境 OK" -ForegroundColor Green }
else { Write-Host ("有 {0} 项缺失，按提示补" -f $script:miss) -ForegroundColor Yellow }
Write-Host ""
