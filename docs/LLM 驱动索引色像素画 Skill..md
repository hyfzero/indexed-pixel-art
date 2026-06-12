你需要在当前项目中实现一个可实际运行的 Codex Skill，名称为：

```text
indexed-pixel-art
```

该 Skill 用于生成真正的像素画。不要调用任何图片生成模型，不要使用扩散模型，不要先生成图片再缩小，也不要通过滤镜将普通图片伪装成像素画。

系统的基本原理是：

1. LLM 根据用户的自然语言描述设计像素画。
2. LLM 输出有限调色板和离散像素矩阵。
3. 每一个最终像素必须引用调色板中的一个索引值。
4. Python 脚本负责严格校验矩阵。
5. 校验通过后，脚本逐像素渲染 PNG。
6. 任何约束不满足时，必须报错，不得静默修复、自动裁剪、自动缩放或引入额外颜色。

---

# 一、最重要的硬性约束

系统必须将以下两个约束视为不可违反的 invariant。

## 约束 1：颜色数量必须严格受控

所有像素只能使用用户声明或配置文件中冻结的调色板。

例如，二值模式：

```json
{
  "palette": [
    { "index": 0, "hex": "#FFFFFF", "name": "background" },
    { "index": 1, "hex": "#000000", "name": "foreground" }
  ]
}
```

像素矩阵中只能出现：

```text
0
1
```

禁止出现：

```text
2
灰色
透明度渐变
抗锯齿像素
自动插值产生的新颜色
未经声明的临时颜色
```

实现规则：

1. `palette_limit` 是强约束，不是建议。
2. 调色板一旦冻结，后续绘制和局部修改都不得增加新颜色。
3. 二值模式下，只允许两个调色板索引。
4. 四色模式下，只允许四个调色板索引。
5. 每个像素保存的必须是索引，不允许直接在像素矩阵中写 RGB 或 HEX。
6. PNG 导出后，必须再次读取文件，验证实际存在的索引和颜色数量。
7. 不得使用自动量化、抖动、颜色近似或抗锯齿。
8. 如果存在透明背景，透明必须被视为一种明确的状态，不得隐式加入。

透明度规则：

* 默认不允许透明背景。
* `allow_transparency=false` 时，输出 PNG 不得包含 alpha 通道或透明索引。
* `allow_transparency=true` 时，必须显式声明 `transparent_index`。
* “透明 + 黑色 + 白色”不是二值模式，而是三种状态，必须设置 `palette_limit=3`。
* 二值模式允许“透明 + 黑色”，但此时只有一个可见颜色和一个透明索引。

## 约束 2：画布尺寸必须严格受控

原始图像尺寸必须与用户声明的尺寸完全一致。

例如：

```json
{
  "canvas": {
    "width": 16,
    "height": 16
  }
}
```

则必须满足：

1. 像素矩阵必须恰好包含 16 行。
2. 每一行必须恰好包含 16 个像素索引。
3. 原始 PNG 必须恰好为 16 × 16 像素。
4. 不允许缺行。
5. 不允许多行。
6. 不允许行长度不一致。
7. 不允许自动补齐背景色。
8. 不允许自动裁剪。
9. 不允许为了适应尺寸而缩放原始图像。
10. 不允许输出尺寸与声明尺寸不一致的图片。

可以额外输出放大预览图，例如 8 倍预览：

```text
16 × 16 原图
128 × 128 预览图
```

但预览图只能使用最近邻放大，不得使用双线性、双三次或其他会产生新颜色的插值算法。

原始 PNG 永远保持用户指定的尺寸。

---

# 二、创建目录结构

在当前项目下创建：

```text
indexed-pixel-art/
├── SKILL.md
├── README.md
├── requirements.txt
├── schemas/
│   └── pixel-art.schema.json
├── scripts/
│   ├── validate_pixel_art.py
│   ├── render_pixel_art.py
│   ├── apply_patch.py
│   ├── inspect_png.py
│   └── export_c_array.py
├── references/
│   ├── pixel-art-rules.md
│   ├── file-format.md
│   └── palette-presets.md
├── examples/
│   ├── binary-heart-16x16.json
│   ├── binary-cat-16x16.json
│   └── four-color-slime-16x16.json
├── tests/
│   ├── test_validation.py
│   ├── test_rendering.py
│   ├── test_patch.py
│   └── test_export_c_array.py
└── output/
```

优先使用 Python 3.11 或更高版本。

使用 Pillow 渲染 PNG。

不要引入不必要的复杂依赖。

---

# 三、设计 JSON 源文件格式

实现一个明确、可校验、可版本化的 JSON 格式。

基础示例：

```json
{
  "version": "1.0",
  "name": "binary-heart",
  "revision": 1,
  "mode": "indexed",
  "canvas": {
    "width": 16,
    "height": 16
  },
  "palette_limit": 2,
  "allow_transparency": false,
  "palette": [
    {
      "index": 0,
      "hex": "#FFFFFF",
      "name": "background"
    },
    {
      "index": 1,
      "hex": "#000000",
      "name": "foreground"
    }
  ],
  "encoding": "matrix",
  "pixels": [
    "0000000000000000",
    "0001100000011000",
    "0011110000111100",
    "0111111001111110",
    "0111111111111110",
    "0111111111111110",
    "0011111111111100",
    "0001111111111000",
    "0000111111110000",
    "0000011111100000",
    "0000001111000000",
    "0000000110000000",
    "0000000000000000",
    "0000000000000000",
    "0000000000000000",
    "0000000000000000"
  ],
  "metadata": {
    "subject": "heart icon",
    "notes": "strict binary pixel art"
  }
}
```

第一版只需要完整支持：

```text
encoding = matrix
```

矩阵中的每一个字符代表一个调色板索引。

第一版调色板最多支持 10 个颜色，因此索引使用单个数字字符：

```text
0 至 9
```

当索引超过 9 时，校验器应明确报错，并提示当前版本暂不支持，而不是错误解析。

---

# 四、实现严格校验器

创建：

```text
scripts/validate_pixel_art.py
```

命令行接口：

```bash
python scripts/validate_pixel_art.py examples/binary-heart-16x16.json
```

成功时输出：

```text
VALID
Canvas: 16x16
Palette entries: 2
Palette limit: 2
Transparency: disabled
Rows: 16
Pixels per row: 16
Total pixels: 256
```

失败时：

1. 返回非零退出码。
2. 给出精确错误位置。
3. 不允许自动修复。
4. 如果存在多个错误，尽可能一次列出全部错误。

至少校验：

## 文件结构

* JSON 能否解析。
* 必填字段是否存在。
* `version` 是否支持。
* `encoding` 是否为 `matrix`。
* 宽高是否为正整数。
* 宽高是否处于合理范围，例如 `1..256`。

## 尺寸约束

* `pixels` 是否为数组。
* 行数是否严格等于 `canvas.height`。
* 每行是否为字符串。
* 每行字符数是否严格等于 `canvas.width`。
* 总像素数是否严格等于 `width * height`。

## 颜色约束

* `palette_limit` 是否为正整数。
* `palette` 条目数量是否小于或等于 `palette_limit`。
* 二值模式下，`palette_limit=2` 时不得存在第三种索引。
* 调色板索引必须从 `0` 开始连续排列。
* 调色板索引不得重复。
* `hex` 必须是合法的 `#RRGGBB` 格式。
* 调色板 HEX 值不得重复。
* 每一个像素索引都必须存在于调色板中。
* 不得存在调色板以外的索引。
* 不得存在空格、逗号或其他非法字符。

## 透明度约束

* 默认不允许透明。
* 如果允许透明，必须存在 `transparent_index`。
* `transparent_index` 必须出现在调色板中。
* 不得存在未声明的半透明 alpha。
* 输出只允许完全透明或完全不透明，不支持中间 alpha 值。

错误信息示例：

```text
INVALID
- Row count mismatch: expected 16 rows, received 15.
- Row 7 width mismatch: expected 16 pixels, received 15.
- Invalid palette index "2" at x=8, y=11. Allowed indexes: 0, 1.
```

---

# 五、实现逐像素 PNG 渲染器

创建：

```text
scripts/render_pixel_art.py
```

命令行接口：

```bash
python scripts/render_pixel_art.py \
  examples/binary-heart-16x16.json \
  --output output/binary-heart.png \
  --preview-scale 8
```

必须遵循以下规则：

1. 渲染前必须调用与 `validate_pixel_art.py` 相同的校验逻辑。
2. 校验失败时，不输出 PNG。
3. 原图必须逐像素写入。
4. 原图必须使用索引色模式，即 Pillow 的 `P` 模式。
5. 每一个像素只能写入声明的调色板索引。
6. 不允许使用自动绘图函数产生抗锯齿。
7. 不允许自动缩放原图。
8. 预览图只能使用 `Image.Resampling.NEAREST`。
9. 输出后重新读取 PNG，执行二次验证。
10. 二次验证失败时，删除错误输出文件并返回非零退出码。

输出：

```text
output/binary-heart.png
output/binary-heart_preview_8x.png
```

输出后打印：

```text
RENDERED
Source canvas: 16x16
Original PNG: output/binary-heart.png
Original PNG size: 16x16
Preview PNG: output/binary-heart_preview_8x.png
Preview scale: 8
Verified palette entries: 2
Verified unique pixel indexes: 0, 1
```

---

# 六、实现 PNG 检查工具

创建：

```text
scripts/inspect_png.py
```

命令行接口：

```bash
python scripts/inspect_png.py output/binary-heart.png
```

输出：

```text
PNG INSPECTION
Mode: P
Size: 16x16
Declared palette entries: 2
Used palette indexes: 0, 1
Used visible colors:
- 0: #FFFFFF
- 1: #000000
Transparency: disabled
Constraint status: PASS
```

该工具需要验证：

1. 实际 PNG 尺寸。
2. 实际 PNG 模式。
3. 实际使用的像素索引。
4. 实际可见颜色数量。
5. 是否存在透明度。
6. 是否存在未声明颜色。
7. 是否存在非预期 alpha。
8. PNG 是否符合源 JSON 声明。

可以通过参数指定源文件：

```bash
python scripts/inspect_png.py \
  output/binary-heart.png \
  --source examples/binary-heart-16x16.json
```

---

# 七、实现坐标 Patch 修改功能

创建：

```text
scripts/apply_patch.py
```

Patch 文件示例：

```json
{
  "base_revision": 1,
  "set": [
    { "x": 7, "y": 4, "color": 1 },
    { "x": 8, "y": 4, "color": 1 },
    { "x": 9, "y": 4, "color": 0 }
  ]
}
```

命令行接口：

```bash
python scripts/apply_patch.py \
  examples/binary-heart-16x16.json \
  patch.json \
  --output output/binary-heart-revision-2.json
```

约束：

1. 不得改变画布尺寸。
2. 不得添加新调色板条目。
3. 不得使用不存在的颜色索引。
4. 坐标必须在画布范围内。
5. 必须校验 `base_revision` 是否与源文件一致。
6. Patch 后自动增加 `revision`。
7. Patch 后再次执行完整校验。
8. 如果任意坐标非法，整个 Patch 必须失败，不允许只执行其中一部分。

错误示例：

```text
PATCH REJECTED
- Coordinate out of bounds: x=16, y=4. Canvas is 16x16.
- Invalid color index: 2. Allowed indexes: 0, 1.
```

---

# 八、实现 C 数组导出

创建：

```text
scripts/export_c_array.py
```

第一版支持将严格二值图导出为 C 语言位图数组。

命令行接口：

```bash
python scripts/export_c_array.py \
  examples/binary-heart-16x16.json \
  --output output/binary_heart.h
```

要求：

1. 仅允许 `palette_limit=2` 的作品导出为单色 bit array。
2. 明确说明每一位与像素坐标的对应关系。
3. 默认使用逐行、从左到右、从上到下、MSB first。
4. 如果宽度不是 8 的整数倍，明确执行逐行尾部补零。
5. 补零仅用于 C 数组存储，不得改变源 PNG 尺寸。
6. 输出中包含宽度、高度和数组长度宏。

输出示例：

```c
#ifndef BINARY_HEART_H
#define BINARY_HEART_H

#include <stdint.h>

#define BINARY_HEART_WIDTH 16
#define BINARY_HEART_HEIGHT 16
#define BINARY_HEART_DATA_LENGTH 32

static const uint8_t binary_heart_data[BINARY_HEART_DATA_LENGTH] = {
    0x00, 0x00,
    0x18, 0x18
};

#endif
```

---

# 九、编写 JSON Schema

创建：

```text
schemas/pixel-art.schema.json
```

使用 JSON Schema 对源文件做基础结构校验。

注意：

JSON Schema 只能验证基础结构。以下复杂规则仍然必须由 Python 校验器负责：

* 每行长度必须等于画布宽度。
* 行数必须等于画布高度。
* 像素索引必须存在于调色板。
* 调色板条目不得超过限制。
* PNG 输出后颜色数量必须再次检查。

---

# 十、编写 SKILL.md

创建：

```text
SKILL.md
```

内容需要使 Codex 在用户要求绘制像素画、点阵图、二值图标、有限调色板 Sprite、OLED 图案或局部像素修改时，自动采用本 Skill。

SKILL.md 必须明确写出以下规则：

```text
1. Never call an image-generation model.
2. Never generate a conventional raster image and then reduce its size.
3. Never introduce colors outside the frozen palette.
4. Never change the declared canvas dimensions.
5. Every final pixel must be represented by a palette index.
6. Validate before rendering.
7. Re-open and inspect the PNG after rendering.
8. Reject malformed data instead of silently repairing it.
9. Use nearest-neighbor scaling only for preview images.
10. Prefer coordinate patches for local edits.
```

还要包含 LLM 绘图流程：

```text
1. 解析用户描述。
2. 确认原始画布尺寸。
3. 确认调色板数量。
4. 确认是否允许透明。
5. 冻结调色板。
6. 先构建轮廓。
7. 再补充内部细节。
8. 输出完整像素矩阵。
9. 调用校验器。
10. 修复所有错误后再次校验。
11. 调用渲染器。
12. 检查最终 PNG。
13. 返回 JSON、原始 PNG 和最近邻放大预览 PNG。
```

当用户没有指定参数时，默认使用：

```text
canvas: 16x16
palette_limit: 2
allow_transparency: false
background: #FFFFFF
foreground: #000000
preview_scale: 8
```

当用户只说“画一个二值图标”时，必须使用两个颜色，不得生成灰度和半透明像素。

---

# 十一、编写 README.md

README 需要使用中文，包含：

1. 项目用途。
2. 为什么这是真正的像素画，而不是像素风生图。
3. 颜色约束。
4. 尺寸约束。
5. 安装命令。
6. 校验命令。
7. 渲染命令。
8. PNG 检查命令。
9. Patch 修改命令。
10. C 数组导出命令。
11. JSON 文件格式。
12. 常见错误。
13. 二值模式与透明背景之间的区别。
14. 如何添加新的示例。
15. 如何在 Codex 中使用该 Skill。

README 中需要特别强调：

```text
原图尺寸是不可变的。
颜色集合是冻结的。
所有违规输入都必须失败。
放大预览不等于改变原图尺寸。
透明色必须被显式计入状态数量。
```

---

# 十二、准备示例文件

至少创建三个合法示例：

```text
examples/binary-heart-16x16.json
examples/binary-cat-16x16.json
examples/four-color-slime-16x16.json
```

要求：

1. `binary-heart-16x16.json`：16 × 16，严格黑白二值。
2. `binary-cat-16x16.json`：16 × 16，严格黑白二值。
3. `four-color-slime-16x16.json`：16 × 16，严格四种颜色。

运行脚本，为每个示例生成：

```text
output/*.png
output/*_preview_8x.png
```

---

# 十三、编写自动化测试

使用 `pytest`。

至少覆盖以下测试。

## 合法输入

* 合法的 16 × 16 二值图可以通过校验。
* 合法的四色图可以通过校验。
* 渲染后的原始 PNG 尺寸完全正确。
* 预览图尺寸正确。
* 预览图使用最近邻缩放后，没有产生新颜色。
* 二值 PNG 实际只包含两个索引。
* 四色 PNG 实际最多只包含四个索引。
* 合法 Patch 可以修改指定像素。
* Patch 后尺寸不变。
* Patch 后调色板不变。

## 非法尺寸

* 少一行时必须失败。
* 多一行时必须失败。
* 某一行少一个像素时必须失败。
* 某一行多一个像素时必须失败。
* 宽度为零时必须失败。
* 高度为负数时必须失败。
* Patch 坐标越界时必须失败。

## 非法颜色

* 二值图中出现索引 `2` 时必须失败。
* 像素引用不存在的索引时必须失败。
* 调色板索引重复时必须失败。
* 调色板颜色重复时必须失败。
* HEX 格式错误时必须失败。
* 调色板条目超过 `palette_limit` 时必须失败。
* 默认模式下出现透明度时必须失败。
* 未声明透明索引时必须失败。

## 渲染后验证

* 原始 PNG 尺寸错误时必须失败。
* PNG 出现额外颜色时必须失败。
* 二值 PNG 混入灰色时必须失败。
* 二值 PNG 混入半透明像素时必须失败。

---

# 十四、执行与验收

完成编码后，不要只汇报文件列表。必须实际执行以下步骤：

```bash
python -m pip install -r requirements.txt
python -m pytest -q
python scripts/validate_pixel_art.py examples/binary-heart-16x16.json
python scripts/render_pixel_art.py examples/binary-heart-16x16.json --output output/binary-heart.png --preview-scale 8
python scripts/inspect_png.py output/binary-heart.png --source examples/binary-heart-16x16.json
python scripts/export_c_array.py examples/binary-heart-16x16.json --output output/binary_heart.h
```

然后对另外两个示例执行校验和渲染。

最终汇报：

1. 实际创建的文件。
2. 测试运行结果。
3. 三个示例的原始尺寸。
4. 三个示例实际使用的颜色数量。
5. 是否存在透明像素。
6. 输出文件路径。
7. 如果存在尚未完成的功能，明确列出。
8. 不要声称测试通过，除非已经实际执行测试。

---

# 十五、实现原则

优先完成一个稳定、容易理解、可以运行的 MVP。

不要过度设计 GUI。

第一版不需要实现：

```text
Web 界面
动画编辑器
图层系统
复杂 RLE
超过 10 种颜色的索引编码
自动图片转像素画
生图模型接入
```

但代码结构需要为后续增加以下功能预留清晰扩展点：

```text
RLE 编码
Sprite Sheet
动画帧
Godot 导出
SVG 导出
更多调色板预设
孤立像素检测
对称性辅助
交互式局部修改
```

现在开始实现。先检查当前目录，再创建文件、运行测试并输出最终结果。不要停留在方案说明阶段。
