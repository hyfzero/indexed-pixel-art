# JSON Source Format

Version `1.0` supports `mode: "indexed"` and `encoding: "matrix"` only.

```json
{
  "version": "1.0",
  "name": "binary-heart",
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
  "pixels": ["0000000000000000"],
  "style": { "preset": "binary_icon" },
  "metadata": { "subject": "heart icon" }
}
```

`pixels` must contain exactly `canvas.height` strings. Every string contains exactly
`canvas.width` single-digit palette indexes. Indexes above `9`, RGB tuples, HEX values, spaces,
and comma-separated cells are unsupported.

When `allow_transparency` is true, add `transparent_index` and include that entry in the palette
and palette limit. Transparent black plus visible black plus visible white is three states, not
binary.

Optional `style` values are constrained by the JSON Schema. They guide design and warning checks
but cannot change dimensions or palette entries.

Patch files use:

```json
{
  "base_revision": 1,
  "set": [
    { "x": 7, "y": 4, "color": 1 }
  ]
}
```

Coordinates are zero-based from the top-left.
