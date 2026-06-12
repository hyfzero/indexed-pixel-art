# indexed-pixel-art

**Language:** [简体中文](README.md) | [English](README.en.md)

For complete installation, CLI, and Codex usage instructions, see the
[Indexed Pixel Art User Guide](docs/User-Guide.en.md).

This repository provides a runnable Codex Skill for creating true pixel art from a limited
palette and a discrete palette-index matrix. The LLM designs every pixel, while deterministic
Python tools validate the source, render it pixel by pixel, inspect the PNG, apply local edits,
and export binary C arrays.

This is not conventional image generation with a pixel-art filter. It does not call an image
generation model, shrink a normal raster image, apply filters, quantize colors, diffuse errors,
anti-alias edges, or approximate colors. Every output pixel is an explicit palette index.

## Core Constraints

- The source canvas size is immutable.
- The palette is frozen.
- Invalid input must fail.
- A scaled preview does not change the source dimensions.
- Transparency must be counted as an explicit palette state.

The matrix row count must exactly match the canvas height, and every row length must exactly
match the canvas width. Palette indexes are continuous from `0`. Version 1 supports up to ten
colors and single-character indexes `0..9`.

Transparency is disabled by default. When enabled, `transparent_index` is required and counts
toward `palette_limit`. Transparent, black, and white are three states, not binary mode.

## Installation

Python 3.11 or newer is recommended:

```bash
python -m pip install -r requirements.txt
```

## Validate and Render

```bash
python scripts/validate_pixel_art.py examples/binary-heart-16x16.json
python scripts/validate_pixel_art.py examples/binary-cat-16x16.json --style-check

python scripts/render_pixel_art.py examples/binary-heart-16x16.json \
  --output output/binary-heart.png \
  --preview-scale 8
```

The validator reports as many errors as possible in one run. It never silently pads rows,
crops pixels, changes colors, or repairs the matrix. The original PNG is written pixel by pixel
in indexed `P` mode. Previews use nearest-neighbor scaling only.

Generate a silhouette preview and run style checks:

```bash
python scripts/render_pixel_art.py examples/binary-cat-16x16.json \
  --output output/binary-cat.png \
  --preview-scale 8 \
  --silhouette-preview \
  --style-check
```

## Inspect a PNG

```bash
python scripts/inspect_png.py output/binary-heart.png \
  --source examples/binary-heart-16x16.json
```

This checks the actual dimensions, image mode, pixel indexes, colors, transparency, and
pixel-for-pixel consistency with the source matrix.

## Apply a Patch

Patch coordinates use the top-left corner as the origin:

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

If any coordinate, color, or revision is invalid, the entire patch fails and no partial output
is written.

## Export a C Array

Export is limited to sources with `palette_limit=2` and exactly two palette entries:

```bash
python scripts/export_c_array.py examples/binary-heart-16x16.json \
  --output output/binary_heart.h
```

Bits are stored row by row, left to right and top to bottom, MSB first. Rows that do not end on
a full byte are padded only in C storage; the source dimensions remain unchanged.

## JSON Source Format

See [references/file-format.md](references/file-format.md) for the complete format.
[schemas/pixel-art.schema.json](schemas/pixel-art.schema.json) validates the base structure,
while the Python validator enforces semantic rules.

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
  "pixels": ["complete matrix"]
}
```

## Style Guidance vs. Hard Constraints

Color count, transparency, canvas dimensions, and matrix validity are hard constraints. Invalid
input is rejected. Silhouette quality, edge rhythm, isolated pixels, holes, symmetry, and visual
weight are style concerns and produce warnings by default.

Style guidance never overrides hard constraints. Do not add gray to soften edges or enlarge the
canvas to fit more detail. See [references/style-presets.md](references/style-presets.md).

## Common Errors

- The row count or row width does not match `canvas`.
- Pixels reference undeclared indexes.
- Palette indexes are discontinuous, colors are duplicated, or `palette_limit` is exceeded.
- Binary mode contains index `2`, gray, dithering, or partial transparency.
- `transparent_index` is declared while transparency is disabled.
- The 8x preview is mistaken for the original image.
- A local edit redraws the whole matrix and changes unrelated pixels.

## Add an Example

1. Copy the closest `examples/*.json` source.
2. Update the name, canvas, frozen palette, and complete matrix.
3. Run the validator and renderer.
4. Run `inspect_png.py --source` to verify the output.
5. Store the original and nearest-neighbor preview in `output/`.

## Use with Codex

```text
Use $indexed-pixel-art to create a 16x16 black-and-white sitting cat icon.
Output the JSON source, original PNG, and 8x preview.
```

You can also request OLED patterns, limited-palette sprites, Game Boy-style assets, C bitmap
arrays, or coordinate-level local edits.

## Tests

```bash
python -m pytest -q
```
