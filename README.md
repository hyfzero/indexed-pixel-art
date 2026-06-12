# indexed-pixel-art

完整安装、命令行操作和 Codex 调用说明见
[《Indexed Pixel Art 用户手册》](docs/用户手册.md)。

这是一个可运行的 Codex Skill，用有限调色板和离散索引矩阵生成真正的像素画。LLM
负责设计每一个像素，Python 工具负责严格校验、逐像素渲染、PNG 复检、局部修改和
二值 C 数组导出。

它不是“像素风生图”：不调用图片生成模型，不先生成普通图片再缩小，不使用滤镜、
自动量化、误差扩散、抗锯齿或颜色近似。每一个最终像素都是明确的调色板索引。

## 核心约束

- 原图尺寸是不可变的。
- 颜色集合是冻结的。
- 所有违规输入都必须失败。
- 放大预览不等于改变原图尺寸。
- 透明色必须被显式计入状态数量。

矩阵行数必须严格等于画布高度，每行长度必须严格等于画布宽度。调色板索引从 `0`
开始连续排列，第一版最多支持十种颜色，矩阵只能使用单字符索引 `0..9`。

默认禁止透明背景。启用透明时必须声明 `transparent_index`，并把它计入
`palette_limit`。“透明 + 黑色 + 白色”是三种状态，不是二值模式。

## 安装

建议使用 Python 3.11 或更高版本：

```bash
python -m pip install -r requirements.txt
```

## 校验与渲染

```bash
python scripts/validate_pixel_art.py examples/binary-heart-16x16.json
python scripts/validate_pixel_art.py examples/binary-cat-16x16.json --style-check

python scripts/render_pixel_art.py examples/binary-heart-16x16.json \
  --output output/binary-heart.png \
  --preview-scale 8
```

校验器尽可能一次列出全部错误，不会自动补行、裁剪、改色或修复矩阵。原图使用 PNG
索引色 `P` 模式逐像素写入，预览只使用最近邻放大。

可同时生成剪影预览并执行风格检查：

```bash
python scripts/render_pixel_art.py examples/binary-cat-16x16.json \
  --output output/binary-cat.png \
  --preview-scale 8 \
  --silhouette-preview \
  --style-check
```

## PNG 检查

```bash
python scripts/inspect_png.py output/binary-heart.png \
  --source examples/binary-heart-16x16.json
```

检查实际尺寸、模式、像素索引、颜色、透明度以及与源矩阵的逐像素一致性。

## Patch 修改

Patch 坐标以左上角为原点：

```json
{
  "base_revision": 1,
  "set": [
    { "x": 7, "y": 4, "color": 1 },
    { "x": 8, "y": 4, "color": 1 }
  ]
}
```

```bash
python scripts/apply_patch.py source.json patch.json --output updated.json
```

任一坐标、颜色或版本非法时，整个 Patch 失败，不会产生部分修改。

## C 数组导出

仅支持 `palette_limit=2` 且恰好有两个调色板条目的作品：

```bash
python scripts/export_c_array.py examples/binary-heart-16x16.json \
  --output output/binary_heart.h
```

位图按逐行、从左到右、从上到下、MSB first 排列。每行不足整字节时仅在 C 存储中
尾部补零，不改变源尺寸。

## JSON 文件格式

完整格式见 [references/file-format.md](references/file-format.md)，基础结构由
[schemas/pixel-art.schema.json](schemas/pixel-art.schema.json) 校验。复杂规则由 Python
校验器负责。

```json
{
  "version": "1.0",
  "name": "example",
  "revision": 1,
  "mode": "indexed",
  "canvas": { "width": 16, "height": 16 },
  "palette_limit": 2,
  "allow_transparency": false,
  "palette": [
    { "index": 0, "hex": "#FFFFFF", "name": "background" },
    { "index": 1, "hex": "#000000", "name": "foreground" }
  ],
  "encoding": "matrix",
  "pixels": ["完整矩阵"]
}
```

## 风格化与硬性约束的区别

颜色数量、透明度、画布尺寸和矩阵合法性属于硬性约束，违规输入会被拒绝。
剪影质量、轮廓节奏、孤立像素、孔洞、对称性和视觉重心属于风格建议，默认只产生警告。

风格化不能覆盖硬性约束。不能为了柔化边缘增加灰色，也不能为了容纳细节放大画布。
预设说明见 [references/style-presets.md](references/style-presets.md)。

## 常见错误

- 行数或行宽与 `canvas` 不一致。
- 像素引用未声明索引。
- 调色板索引不连续、颜色重复或超过 `palette_limit`。
- 二值模式中出现索引 `2`、灰色、抖动或半透明。
- 禁止透明时仍声明 `transparent_index`。
- 把 8 倍预览误认为原图尺寸。
- 修改局部像素时整张重画，意外改变无关区域。

## 添加示例

1. 复制最接近的 `examples/*.json`。
2. 修改名称、画布、冻结调色板和完整矩阵。
3. 运行校验器和渲染器。
4. 使用 `inspect_png.py --source` 完成输出复检。
5. 将原图和最近邻预览保存在 `output/`。

## 在 Codex 中使用

```text
使用 $indexed-pixel-art 画一个 16x16 黑白坐姿猫图标，并输出 JSON、原图和 8 倍预览。
```

也可请求 OLED 图案、有限调色板 Sprite、Game Boy 风格素材、C 位图数组或坐标级局部修改。

## 测试

```bash
python -m pytest -q
```
