# 「大 → 小」小窗规格（数字人先全屏，再缩到左下角）

## 效果

| 时间 | 画面 |
|---|---|
| 0 ~ 9.85 秒 | 数字人**全屏**（1080×1920），带手部动作，字幕逐字跳动 |
| 9.85 秒之后 | 数字人**缩到左下角圆形小窗**（直径 200px，白边），主画面切成内容素材 |

200px ≈ 页面高度的 1/9.6、宽度的 1/5.4 —— 就是「十分之一」那个量级。

## 三个参数（写在 `edit/src/edit.json`）

```json
{
  "video": "main.mp4",      // 主画面：开场大图 + 正文素材（已经是拼好的整片）
  "pipVideo": "pip.mp4",    // 小窗：数字人第 2 段起的连续小窗素材
  "pipFrom": 9.85,          // 小窗出现的时刻（= 第 1 段结束 = tl.json 里 segs[0].end）
  "pipSize": 200,           // 小窗直径 px
  "pipMargin": 36           // 离画布边缘 px
}
```

`pipFrom` **不要手填**，用时间轴算：

```python
import json
tl = json.load(open("edit/src/tl.json", encoding="utf-8"))
d["pipFrom"] = tl["segs"][0]["end"]
```

## 模板改动（已内置在 `templates/huazi-916/src/Huazi.tsx`）

新增一个 `HostPip` 层，挂在 `<Host />` 后面：

```tsx
const HostPip: React.FC = () => {
  const f = useCurrentFrame();
  const at = ED.pipFrom ?? 0;
  const size = ED.pipSize ?? 200;
  const margin = ED.pipMargin ?? 36;
  const appear = interpolate(f, [F(at), F(at) + 14], [0, 1], { ...clamp, easing: Easing.out(Easing.cubic) });
  if (appear <= 0.001) return null;
  return (
    <div style={{ position: "absolute", left: margin, bottom: margin, width: size, height: size,
      borderRadius: size / 2, overflow: "hidden", transform: `scale(${appear})`, transformOrigin: "0% 100%",
      boxShadow: "0 0 0 5px #fff, 0 16px 44px rgba(0,0,0,.45)", zIndex: 40 }}>
      <OffthreadVideo src={staticFile(ED.pipVideo ?? "pip.mp4")} muted
        style={{ width: "100%", height: "100%", objectFit: "cover", objectPosition: "50% 32%" }} />
    </div>
  );
};
```

要点：

- **圆形**：`borderRadius: size/2` + `overflow:hidden`
- **出场动画**：从 `scale(0)` 弹到 `scale(1)`，14 帧，`transformOrigin: "0% 100%"`（从左下角长出来）
- **人脸要留在窗里**：源素材是 2:3 或 9:16 竖屏，裁成方形会切掉脸，所以 `objectPosition: "50% 32%"` 往上偏
- **静音**：小窗不出声，口播走 `voice.wav` 旁白轨（否则叠两遍人声）
- `zIndex: 40` 保证压过主画面和字幕底板

> ⚠ 模板自带的 `Host` 组件里也有一套缩放（`showcase` 触发时缩到**右下角 330×586**）。
> 那是「作品展示」用的，和本 skill 的左下角小窗是两套机制，别混用：
> 用 hk主持 就把 `showcase` 留空，用 `pip*` 参数。

## 素材怎么拼（小窗轨）

`scripts/build_media.py` 自动做：

1. 取每段数字人视频（`gen/renoise-<id>.mp4`），按该段旁白时长裁剪
2. 静音，串成一条 `public/pip.mp4`
3. 时长 = 第 2 段开始到全片结束，所以 `pipFrom` 要等于第 1 段结束时间

## 如果想让小窗不是圆的

把 `borderRadius` 改成 `size / 6`（圆角矩形），或者干脆 `0`（直角方窗），
再把 `objectPosition` 调成 `"50% 30%"` 保住脸。

## 位置对照

| 需求 | 参数 |
|---|---|
| 左下角（本 skill 默认） | `pipMargin: 36`，`left/bottom` |
| 右下角 | 组件里把 `left: margin` 换成 `right: margin` |
| 左上 / 右上 | 同理换 `bottom` / `left` |
