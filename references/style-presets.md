# Style Presets

## `binary_icon`

High-priority silhouette, no outline layer, no shading or dithering, approximate vertical
symmetry, minimal detail, clear negative space, and no unexplained isolated pixels.

## `clean_icon`

High-priority silhouette, selective outline, flat palette-defined shading, low detail, intentional
edge steps, and clear negative space.

## `retro_sprite`

Solid outline, flat shading, medium detail, approximate symmetry, clustered forms, and limited
isolated decorative pixels.

## `gameboy`

Use the four-color Game Boy palette with solid outline, clustered shading, optional regular sparse
checkerboard dithering, and medium detail.

## `terminal_oled`

Strictly binary, no shading or dithering, minimal detail, strong silhouette, clear negative space,
and robust connected structures suitable for C-array export.

## `pixel_avatar`

Use selective outlines, clustered palette-defined shading, medium detail, and recognizable hair,
face direction, and clothing shapes. Prefer 32x32 or larger.

The complete field enums are defined in `schemas/pixel-art.schema.json`. Presets guide composition;
they never authorize new colors, alpha levels, or canvas changes.
