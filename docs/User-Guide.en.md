# Indexed Pixel Art User Guide

**Language:** [简体中文](用户手册.md) | [English](User-Guide.en.md)

This guide covers two ways to use the project:

1. Run the Python tools directly to validate, render, inspect, or modify pixel art.
2. Install the project as a Codex Skill and ask Codex to design pixel art in natural language.

## 1. Overview

`indexed-pixel-art` creates strict indexed-color pixel art, not normal images processed with a
pixel-art filter:

- Every pixel maps to an explicit palette index.
- The original image dimensions exactly match the declared canvas.
- No temporary colors may be added after the palette is frozen.
- No image generation model, anti-aliasing, automatic quantization, or raster downscaling is used.
- Every rendered PNG is reopened and checked for dimensions, indexes, colors, and transparency.
- Local changes use coordinate patches instead of redrawing the whole image.
- Binary images can be exported as C arrays for embedded devices.

## 2. Requirements

The project requires:

- Python 3.11 or newer
- Pillow
- jsonschema
- pytest
- PyYAML

Install dependencies from the project directory:

```powershell
python -m pip install -r requirements.txt
```

If `python` is unavailable on Windows, install Python and enable "Add Python to PATH" during
installation.

Verify the tools:

```powershell
python scripts/validate_pixel_art.py --help
python scripts/render_pixel_art.py --help
```

## 3. Quick Start

The project includes three examples:

| Example | Canvas | Palette |
|---|---:|---:|
| `binary-heart-16x16.json` | 16x16 | Black and white |
| `binary-cat-16x16.json` | 16x16 | Black and white |
| `four-color-slime-16x16.json` | 16x16 | Four colors |

Validate the heart example:

```powershell
python scripts/validate_pixel_art.py examples/binary-heart-16x16.json
```

A successful run prints `VALID`, canvas dimensions, palette count, and total pixel count.

Render the original and an 8x preview:

```powershell
python scripts/render_pixel_art.py examples/binary-heart-16x16.json `
  --output output/binary-heart.png `
  --preview-scale 8
```

On macOS or Linux, use backslashes for line continuation:

```bash
python scripts/render_pixel_art.py examples/binary-heart-16x16.json \
  --output output/binary-heart.png \
  --preview-scale 8
```

Output:

```text
output/binary-heart.png
output/binary-heart_preview_8x.png
```

The original remains 16x16. The preview is enlarged to 128x128 with nearest-neighbor scaling.

## 4. Command-Line Tools

### 4.1 Validate JSON

```powershell
python scripts/validate_pixel_art.py <source.json>
```

Add non-blocking style checks:

```powershell
python scripts/validate_pixel_art.py <source.json> --style-check
```

Hard errors return a nonzero exit code. Examples include:

- Incorrect row count or row width
- Discontinuous palette indexes
- Pixels referencing undeclared colors
- A palette exceeding `palette_limit`
- A missing declared transparency index

Style concerns only produce warnings by default. Examples include isolated pixels, a subject
touching the canvas edge, visible asymmetry, or unbalanced visual weight.

### 4.2 Render a PNG

```powershell
python scripts/render_pixel_art.py <source.json> `
  --output <original.png> `
  --preview-scale 8
```

Options:

- `--style-check`: print style warnings after rendering.
- `--silhouette-preview`: create an additional silhouette preview.
- `--preview-scale N`: set the preview scale from 1 to 64.

The renderer performs complete validation before writing. It then verifies the PNG pixel by
pixel. An invalid original is not kept.

### 4.3 Inspect a PNG

Whenever possible, provide the source JSON:

```powershell
python scripts/inspect_png.py output/binary-heart.png `
  --source examples/binary-heart-16x16.json
```

The command checks:

- Whether the PNG uses indexed `P` mode
- Actual image dimensions
- Used palette indexes and colors
- Unexpected extra colors
- Unexpected transparency
- Pixel-for-pixel consistency with the source matrix

### 4.4 Apply a Local Patch

Coordinates are zero-based from the top-left corner:

```text
(0,0) ---------> x
  |
  |
  v
  y
```

Create `patch.json`:

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

Apply it:

```powershell
python scripts/apply_patch.py examples/binary-heart-16x16.json patch.json `
  --output output/binary-heart-revision-2.json
```

The tool validates the base revision, coordinate range, and color indexes. If any operation is
invalid, the entire patch fails.

Render the updated source:

```powershell
python scripts/render_pixel_art.py output/binary-heart-revision-2.json `
  --output output/binary-heart-revision-2.png `
  --preview-scale 8
```

### 4.5 Export a C Array

Only strict binary sources are supported:

```powershell
python scripts/export_c_array.py examples/binary-heart-16x16.json `
  --output output/binary_heart.h
```

Bits are written row by row, left to right and top to bottom, MSB first. If a row does not end on
a full byte, zeros are appended only in the C array. The JSON and original PNG dimensions do not
change.

## 5. Create Your Own JSON

Copy an existing example as a starting point:

```json
{
  "version": "1.0",
  "name": "my-icon",
  "revision": 1,
  "mode": "indexed",
  "canvas": {
    "width": 16,
    "height": 16
  },
  "palette_limit": 2,
  "allow_transparency": false,
  "palette": [
    { "index": 0, "hex": "#FFFFFF", "name": "background" },
    { "index": 1, "hex": "#000000", "name": "foreground" }
  ],
  "encoding": "matrix",
  "pixels": [
    "0000000000000000"
  ],
  "style": {
    "preset": "binary_icon"
  }
}
```

The `pixels` array above only illustrates the structure. A 16x16 source must contain exactly 16
rows, and every row must contain exactly 16 index characters.

Version 1 supports indexes `0` through `9`. Matrix rows cannot contain HEX values, RGB tuples,
spaces, or commas.

## 6. Transparent Backgrounds

Transparency is disabled by default. To enable it, declare it explicitly:

```json
{
  "palette_limit": 2,
  "allow_transparency": true,
  "transparent_index": 0,
  "palette": [
    { "index": 0, "hex": "#FFFFFF", "name": "transparent" },
    { "index": 1, "hex": "#000000", "name": "foreground" }
  ]
}
```

This example still contains two states: transparent and black.

If transparent, black, and white are all required, use `palette_limit: 3`. Partial transparency
is not supported.

## 7. Install as a Codex Skill

Codex discovers Skills from these common locations:

- User scope: `$HOME/.agents/skills`
- Repository scope: `<target-repository>/.agents/skills`

This project contains `SKILL.md` at its root. A project in an arbitrary directory is not
automatically available as a global Skill. Copy or link the whole project into one of the
locations above.

### 7.1 Windows User Installation

Assume the project is located at:

```text
D:\LLM_Proj\indexed-pixel-art
```

A directory junction keeps the installed Skill synchronized with the working repository:

```powershell
New-Item -ItemType Directory -Force "$HOME\.agents\skills" | Out-Null
New-Item -ItemType Junction `
  -Path "$HOME\.agents\skills\indexed-pixel-art" `
  -Target "D:\LLM_Proj\indexed-pixel-art"
```

To copy instead:

```powershell
Copy-Item -Recurse -Force `
  "D:\LLM_Proj\indexed-pixel-art" `
  "$HOME\.agents\skills\indexed-pixel-art"
```

### 7.2 macOS/Linux User Installation

```bash
mkdir -p "$HOME/.agents/skills"
ln -s "/absolute/path/to/indexed-pixel-art" \
  "$HOME/.agents/skills/indexed-pixel-art"
```

### 7.3 Repository Installation

To make the Skill available only in one project, place the whole directory under:

```text
target-repository/
└── .agents/
    └── skills/
        └── indexed-pixel-art/
            ├── SKILL.md
            ├── scripts/
            ├── schemas/
            └── ...
```

Repository installation is useful for teams. Commit `.agents/skills/indexed-pixel-art` so other
contributors can use it when they start Codex in the repository.

Codex normally detects Skill changes automatically. If the Skill does not appear, restart Codex
or start a new thread.

## 8. Invoke the Skill in Codex

The Skill works in the Codex app, CLI, and IDE extension.

### 8.1 Confirm Discovery

In the Codex CLI or IDE extension, run:

```text
/skills
```

You can also type `$` in the prompt and look for:

```text
$indexed-pixel-art
```

### 8.2 Explicit Invocation

Put the Skill name at the beginning of the prompt:

```text
$indexed-pixel-art Create a 16x16 black-and-white rocket icon.
Do not use transparency. Output the JSON, original PNG, and 8x preview.
```

Codex reads `SKILL.md`, creates the complete index matrix, runs the validator and renderer, and
then inspects the PNG.

### 8.3 Implicit Invocation

You can also describe the task directly:

```text
Create a strict binary 16x16 OLED battery icon and export a C array.
```

Codex may select the Skill automatically when the task matches its description. Use
`$indexed-pixel-art` when you need to guarantee explicit invocation.

## 9. Recommended Prompts

### 9.1 Default Settings

```text
$indexed-pixel-art Create a coffee-cup pixel icon.
```

When unspecified, the Skill defaults to:

- A 16x16 source canvas
- Two colors
- No transparency
- White background and black foreground
- An 8x nearest-neighbor preview

### 9.2 Explicit Specifications

```text
$indexed-pixel-art Create a 24x24 four-color treasure-chest sprite.
Freeze the palette to #F4E8C1, #8C5A2B, #3B2414, and #FFD34E.
Disable transparency and use the retro_sprite preset.
Output the JSON source, original PNG, 8x preview, and run style-check.
```

### 9.3 OLED and C Array

```text
$indexed-pixel-art Create a strict binary 32x16 Wi-Fi icon for a monochrome OLED.
Avoid isolated pixels. Output the PNG, preview, and MSB-first C array.
```

### 9.4 Transparent Sprite

```text
$indexed-pixel-art Create a 16x16 black ghost silhouette.
Use two states: transparent background index 0 and black foreground index 1.
Output the JSON, original PNG, and 8x preview.
```

### 9.5 Local Edit

```text
$indexed-pixel-art Modify output/cat.json:
Move the top of the left ear up by one pixel and keep every other position unchanged.
Use a coordinate patch, increment the revision, validate, render, and inspect the PNG.
```

### 9.6 Style Cleanup

```text
$indexed-pixel-art Inspect the outline in examples/binary-cat-16x16.json.
Only fix unexplained isolated pixels and irregular edge steps.
Do not change the canvas or palette. Use a patch and list the changed coordinates.
```

## 10. Codex Workflow

After invoking the Skill, Codex should:

1. Understand the subject, intended use, and requested outputs.
2. Confirm canvas dimensions, palette size, and transparency policy.
3. Freeze the palette.
4. Design the silhouette, then add only necessary structure and negative space.
5. Write the complete indexed-matrix JSON.
6. Run strict validation.
7. Fix all hard errors and validate again.
8. Render the indexed original and nearest-neighbor preview.
9. Reopen the PNG and compare it pixel by pixel with the JSON source.
10. Return the JSON, original PNG, preview, and verification results.

For local changes, Codex should create a patch instead of redrawing the complete matrix.

## 11. Verify Correct Skill Usage

A completed task should include:

- A source JSON file
- An original PNG with the declared dimensions
- A scaled preview whose name contains `_preview_8x`
- Validator output containing `VALID`
- Renderer output containing `RENDERED`
- PNG inspection output containing `Constraint status: PASS`

A binary source should only use indexes `0, 1`. A four-color source must not contain a fifth
index. Default output must not contain transparency.

These behaviors indicate that the Skill was not followed:

- Returning only an image without a source matrix
- Enlarging the original PNG
- Adding gray anti-aliased edges
- Adding colors automatically
- Silently padding or cropping invalid input
- Changing unrelated pixels during a local edit

## 12. Troubleshooting

### Codex Cannot Find the Skill

Check for:

```text
$HOME/.agents/skills/indexed-pixel-art/SKILL.md
```

or:

```text
<repository-root>/.agents/skills/indexed-pixel-art/SKILL.md
```

Confirm that both the directory and the `name` in `SKILL.md` are `indexed-pixel-art`, then restart
Codex.

### Explicit Invocation Does Not Create Files

Require execution and provide an output directory:

```text
$indexed-pixel-art Generate the files under output/ in the current project.
Run the validation, rendering, and PNG inspection commands. Do not only provide a plan.
```

### Does a Style Warning Mean Failure?

No. Color, dimensions, transparency, and matrix validity are hard constraints. Isolated pixels,
edge rhythm, and visual weight are style concerns and only produce warnings by default.

### Can It Convert an Existing Photo?

Version 1 does not provide automatic image conversion and does not generate a normal image before
downscaling it. It begins with a discrete index matrix and designs every pixel explicitly.

### Can It Use More Than Ten Colors?

No. Version 1 uses single-character matrix indexes and therefore supports only `0` through `9`.

## 13. Further Reading

- [File format](../references/file-format.md)
- [Hard constraints](../references/pixel-art-rules.md)
- [Palette presets](../references/palette-presets.md)
- [Style presets](../references/style-presets.md)
- [JSON Schema](../schemas/pixel-art.schema.json)
- [Official Codex Agent Skills documentation](https://developers.openai.com/codex/skills)
