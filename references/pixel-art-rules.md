# Indexed Pixel Art Rules

## Priority

1. Exact canvas dimensions
2. Frozen palette and palette limit
3. Explicit transparency policy
4. Valid indexed matrix
5. Subject recognition
6. Style guidance
7. Decoration

Never relax a higher-priority rule to improve a lower-priority result.

## Hard Invariants

- The matrix has exactly `height` rows and each row has exactly `width` indexes.
- Palette indexes start at `0`, are continuous, unique, and limited to single digits in v1.
- Every matrix character references a declared palette entry.
- Palette colors are unique `#RRGGBB` values.
- The original PNG is an indexed `P` image at the declared source size.
- No anti-aliasing, interpolation, quantization, automatic repair, crop, or padding is allowed.
- Transparency is disabled by default. When enabled, `transparent_index` is required and counts
  toward `palette_limit`. Partial alpha is unsupported.
- Preview images use nearest-neighbor scaling and never redefine the source canvas.

## Style Guidance

Design the silhouette before internal detail. Use deliberate edge steps, clear negative space,
compact clusters, and limited decoration. Style checks are warnings unless a style setting
contradicts a hard requirement, such as dithering in binary mode or a non-binary terminal OLED
preset.

Local changes should use coordinate patches. Preserve dimensions, palette, transparency, and all
unrelated pixels.
