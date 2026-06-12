---
name: indexed-pixel-art
description: Create, validate, render, inspect, patch, and export true indexed-color pixel art from discrete palette-index matrices. Use when Codex needs to draw pixel art, binary icons, bitmap glyphs, limited-palette sprites, OLED/LCD patterns, Game Boy-style art, C bitmap arrays, or make local pixel-coordinate edits while preserving exact canvas dimensions and a frozen palette.
---

# Indexed Pixel Art

Create pixel art by designing every source pixel as an explicit palette index. Use the bundled
Python tools to reject malformed work, render an indexed PNG, and inspect the file after writing.

## Non-Negotiable Rules

1. Never call an image-generation model.
2. Never generate a conventional raster image and then reduce its size.
3. Never introduce colors outside the frozen palette.
4. Never change the declared canvas dimensions.
5. Represent every final pixel with a palette index.
6. Validate before rendering.
7. Re-open and inspect the PNG after rendering.
8. Reject malformed data instead of silently repairing it.
9. Use nearest-neighbor scaling only for preview images.
10. Prefer coordinate patches for local edits.

Hard constraints outrank recognition, style, and decoration. Do not add gray, alpha, dithering,
anti-aliasing, padding, cropping, or scaling to make a design fit.

## Workflow

1. Parse the user's subject and intended use.
2. Confirm the original canvas size, palette limit, and transparency policy.
3. Use these defaults when omitted: `16x16`, two colors, no transparency, white background
   `#FFFFFF`, black foreground `#000000`, and preview scale `8`.
4. Freeze a continuous palette indexed from `0`. Count transparency as a palette state.
5. Select a style preset from [style-presets.md](references/style-presets.md) when useful.
6. Build the silhouette first, then add only necessary internal structure and negative space.
7. Emit the complete JSON matrix described in [file-format.md](references/file-format.md).
8. Run `scripts/validate_pixel_art.py SOURCE --style-check`.
9. Correct every hard error without changing the requested dimensions or frozen palette.
10. Run `scripts/render_pixel_art.py SOURCE --output OUTPUT --preview-scale 8 --style-check`.
11. Run `scripts/inspect_png.py OUTPUT --source SOURCE`.
12. Return the JSON source, original PNG, and nearest-neighbor preview PNG.

For a binary icon, use exactly two states and do not add grayscale or partial transparency.
For local edits, create a coordinate patch and run `scripts/apply_patch.py`; do not redraw the
whole matrix unless the requested change genuinely affects the whole composition.

## Commands

```bash
python scripts/validate_pixel_art.py examples/binary-heart-16x16.json --style-check
python scripts/render_pixel_art.py examples/binary-heart-16x16.json --output output/binary-heart.png --preview-scale 8
python scripts/inspect_png.py output/binary-heart.png --source examples/binary-heart-16x16.json
python scripts/apply_patch.py SOURCE PATCH --output UPDATED_SOURCE
python scripts/export_c_array.py SOURCE --output BITMAP_HEADER
```

Read [pixel-art-rules.md](references/pixel-art-rules.md) for invariants and style priority.
Read [palette-presets.md](references/palette-presets.md) before choosing a standard palette.

## Style Guidance

Treat style findings as warnings unless the underlying dimensions, palette, matrix, transparency,
or preset requirements are invalid. Prefer recognizable silhouettes, intentional edge steps,
clear negative space, compact color clusters, and explainable isolated pixels. Disable dithering
for binary work. Never let a style preference override a hard constraint.
